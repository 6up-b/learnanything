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
