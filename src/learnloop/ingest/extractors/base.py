"""The versioned extractor-provider boundary (spec_source_ingestion_v2 §2.9).

``DocumentExtractor`` is the single interface every provider implements; it returns
the LearnLoop IR. Downstream services never import marker/pypdf classes — they hold
a ``DocumentExtractor`` and consume :class:`~learnloop.ingest.ir.DocumentIR`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from learnloop.ingest.hashing import semantic_hash
from learnloop.ingest.ir import DocumentBlock, DocumentUnit


@dataclass(frozen=True)
class ExtractionContext:
    """Everything a run needs beyond the raw bytes (feeds the request hash)."""

    revision_id: str
    config: dict[str, Any] = field(default_factory=dict)
    page_selection: tuple[int, ...] | None = None
    cache_dir: Path | None = None
    parent_extraction_id: str | None = None


@runtime_checkable
class DocumentExtractor(Protocol):
    """A provider that turns raw bytes into the LearnLoop Document IR."""

    name: str

    def version(self) -> str:
        """Provider/package version — participates in the request hash (§2.2)."""

    def model_versions(self) -> dict[str, str]:
        """Best-effort model-artifact versions (may be empty)."""

    def extract(self, raw_bytes: bytes, context: ExtractionContext):  # -> DocumentIR
        """Return a :class:`DocumentIR` for ``raw_bytes``."""


def assign_span_semantic_hash(blocks: list[DocumentBlock]) -> str:
    """Convenience wrapper so extractors compute unit hashes consistently."""

    return semantic_hash(blocks)


def units_from_toc_entries(
    entries: list[dict[str, Any]],
    blocks: list[DocumentBlock],
    *,
    document_title: str | None = None,
    locator_scheme: str = "toc",
    drop_empty: bool = False,
) -> list[DocumentUnit]:
    """Hierarchical units from ordered ToC-shaped entries (§2.3).

    Each entry is ``{"title", "heading_level", "page_id"}`` — the common shape of
    marker's detected table of contents AND a PDF's embedded outline (bookmarks).
    A unit spans from its entry's page to the page before the next entry; nesting
    follows ``heading_level`` via a parent stack. No entries → one honest
    whole-document unit. ``drop_empty`` removes units whose page range holds no
    extracted blocks (an embedded outline can cover pages outside the import's
    page selection)."""

    paged = [block for block in blocks if block.page is not None]
    max_page = max((block.page for block in paged), default=None)

    if not entries:
        label = document_title or "Document"
        return [
            DocumentUnit(
                unit_id="u1",
                parent_unit_id=None,
                label=label,
                ordinal=1,
                locator={"scheme": "whole_document"},
                semantic_hash=semantic_hash(blocks),
                page_start=min((block.page for block in paged), default=None),
                page_end=max_page,
                span_ids=[block.span_id for block in blocks],
            )
        ]

    ordered = sorted(
        entries, key=lambda item: (item.get("page_id") if item.get("page_id") is not None else 0)
    )
    units: list[DocumentUnit] = []
    parent_stack: list[tuple[int, str]] = []  # (heading_level, unit_id)
    for position, entry in enumerate(ordered, start=1):
        unit_id = f"u{position}"
        level = int(entry.get("heading_level") or 1)
        page_start = entry.get("page_id")
        next_start = ordered[position].get("page_id") if position < len(ordered) else None
        if page_start is None:
            page_end = None
        elif next_start is None:
            page_end = max_page if max_page is not None else page_start
        else:
            page_end = max(page_start, int(next_start) - 1)

        while parent_stack and parent_stack[-1][0] >= level:
            parent_stack.pop()
        parent_unit_id = parent_stack[-1][1] if parent_stack else None
        parent_stack.append((level, unit_id))

        unit_blocks = [
            block
            for block in blocks
            if page_start is not None
            and block.page is not None
            and page_start <= block.page <= (page_end if page_end is not None else page_start)
        ]
        units.append(
            DocumentUnit(
                unit_id=unit_id,
                parent_unit_id=parent_unit_id,
                label=str(entry.get("title") or unit_id).strip() or unit_id,
                ordinal=position,
                locator={"scheme": locator_scheme, "page": page_start, "heading_level": level},
                semantic_hash=semantic_hash(unit_blocks),
                page_start=page_start,
                page_end=page_end,
                span_ids=[block.span_id for block in unit_blocks],
            )
        )

    if drop_empty:
        empty_parents = {unit.unit_id: unit.parent_unit_id for unit in units if not unit.span_ids}

        def _live_parent(parent_id: str | None) -> str | None:
            while parent_id in empty_parents:
                parent_id = empty_parents[parent_id]
            return parent_id

        units = [unit for unit in units if unit.span_ids]
        for ordinal, unit in enumerate(units, start=1):
            unit.ordinal = ordinal
            unit.parent_unit_id = _live_parent(unit.parent_unit_id)
    return units


def single_unit_from_blocks(
    blocks: list[DocumentBlock],
    *,
    label: str,
    unit_id: str = "u1",
    locator: dict | None = None,
) -> DocumentUnit:
    """Build one whole-document unit — the honest trivial case for non-paged
    or ToC-less sources (§2.3)."""

    pages = [block.page for block in blocks if block.page is not None]
    return DocumentUnit(
        unit_id=unit_id,
        parent_unit_id=None,
        label=label,
        ordinal=1,
        locator=locator or {"scheme": "whole_document"},
        semantic_hash=semantic_hash(blocks),
        page_start=min(pages) if pages else None,
        page_end=max(pages) if pages else None,
        span_ids=[block.span_id for block in blocks],
    )
