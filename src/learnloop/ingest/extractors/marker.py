"""Marker adapter (spec_source_ingestion_v2 §2.3/§2.8/§2.9).

Marker is GPL-3.0 with separately licensed model weights; it is an **optional**
provider from day one, held behind this adapter boundary. Downstream code must
never import marker classes.

The chunks renderer returns ``FlatBlockOutput`` items plus document metadata. We
map them directly into the IR — ids/types/html/page/polygon/bbox/section hierarchy
into DocumentBlocks, ``table_of_contents`` into DocumentUnits, ``page_stats`` into
ExtractionHealth. We do NOT re-derive structure from rendered markdown.

``chunk_output_to_ir`` is a pure function over plain dicts so adapter tests can
hand-build FlatBlockOutput-shaped data without invoking marker inference.
"""

from __future__ import annotations

import hashlib
import importlib.util
import re
from pathlib import Path
from typing import Any

from learnloop.ingest.block_roles import classify_block_role
from learnloop.ingest.extractors.base import ExtractionContext
from learnloop.ingest.hashing import semantic_hash
from learnloop.ingest.ir import (
    IR_SCHEMA_VERSION,
    DocumentAsset,
    DocumentBlock,
    DocumentIR,
    DocumentUnit,
    ExtractionHealth,
    PageHealth,
    block_content_hash,
)

EXTRACTOR_NAME = "marker"

_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")
_VERBATIM_TYPES = {"equation", "equationnumber", "math", "inlinemath", "table", "tablegroup", "code", "codeblock"}


class MarkerUnavailableError(RuntimeError):
    """Raised when marker is requested but not importable (§2.9 explicit fallback)."""


def marker_available() -> bool:
    return importlib.util.find_spec("marker") is not None


def marker_package_version() -> str:
    try:
        from importlib.metadata import version

        return version("marker-pdf")
    except Exception:  # pragma: no cover - best effort per §2.2
        return "unknown"


def _as_dict(block: Any) -> dict[str, Any]:
    if isinstance(block, dict):
        return block
    # pydantic FlatBlockOutput or any object with the same attributes.
    return {
        "id": getattr(block, "id", None),
        "block_type": getattr(block, "block_type", ""),
        "html": getattr(block, "html", ""),
        "page": getattr(block, "page", None),
        "polygon": getattr(block, "polygon", None),
        "bbox": getattr(block, "bbox", None),
        "section_hierarchy": getattr(block, "section_hierarchy", None),
        "images": getattr(block, "images", None),
    }


_BLOCK_ID_PAGE = re.compile(r"^/page/(\d+)(?:/|$)")


def _block_page(block: dict[str, Any]) -> int | None:
    """Page index for a chunk block.

    The block id (``/page/3/Text/7``) is marker's canonical page identity.
    ``FlatBlockOutput.page`` is preferred only when no id is present: on real
    PDFs (observed with pypdf-sliced files) marker can emit internal page ids
    (108, 358, ...) in ``page`` while the block id keeps the true 0-based
    index — trusting ``page`` there breaks ToC unit assignment.
    """

    block_id = block.get("id")
    if block_id is not None:
        match = _BLOCK_ID_PAGE.match(str(block_id))
        if match:
            return int(match.group(1))
    page = block.get("page")
    return int(page) if page is not None else None


def _section_path(section_hierarchy: dict | None) -> list[str]:
    if not section_hierarchy:
        return []
    ordered_levels = sorted(int(level) for level in section_hierarchy)
    return [str(section_hierarchy[level]).strip() for level in ordered_levels if str(section_hierarchy[level]).strip()]


def _block_text(block_type: str, html: str) -> str:
    normalized_type = (block_type or "").replace(" ", "").lower()
    unescaped = _unescape(_TAG_RE.sub(" ", html or ""))
    if normalized_type in _VERBATIM_TYPES:
        return unescaped.strip()
    return _WS_RE.sub(" ", unescaped).strip()


def _unescape(text: str) -> str:
    return (
        text.replace("&amp;", "&")
        .replace("&lt;", "<")
        .replace("&gt;", ">")
        .replace("&#39;", "'")
        .replace("&quot;", '"')
        .replace("&nbsp;", " ")
    )


def chunk_output_to_ir(
    *,
    blocks: list[Any],
    metadata: dict[str, Any] | None = None,
    page_info: dict[Any, Any] | None = None,
    extractor_version: str,
    document_title: str | None = None,
) -> DocumentIR:
    """Pure marker ``ChunkOutput`` → :class:`DocumentIR` mapping (§2.3)."""

    metadata = metadata or {}
    document_blocks: list[DocumentBlock] = []
    assets: list[DocumentAsset] = []

    for index, raw in enumerate(blocks, start=1):
        block = _as_dict(raw)
        span_id = f"s{index}"
        block["page"] = _block_page(block)
        block_type = str(block.get("block_type") or "Text")
        section_path = _section_path(block.get("section_hierarchy"))
        text = _block_text(block_type, str(block.get("html") or ""))
        images = block.get("images") or {}
        # marker keys images by BlockId objects, not strings — coerce before
        # they reach pydantic ids or the persisted asset_ids_json.
        image_items = (
            [(str(key), value) for key, value in images.items()] if isinstance(images, dict) else []
        )
        asset_ids = [key for key, _ in image_items]
        for asset_key, image_value in image_items:
            payload = str(image_value)
            assets.append(
                DocumentAsset(
                    id=asset_key,
                    media_type="image/png",
                    content_hash="sha256:" + hashlib.sha256(payload.encode("utf-8")).hexdigest(),
                    path=None,
                    caption=None,
                    page=block.get("page"),
                    geometry={"bbox": block.get("bbox"), "polygon": block.get("polygon")},
                    neighboring_span_ids=[span_id],
                )
            )
        document_blocks.append(
            DocumentBlock(
                span_id=span_id,
                extractor_block_id=(str(block["id"]) if block.get("id") is not None else None),
                block_type=block_type,
                role_hint=classify_block_role(block_type, section_path, text),
                page=block.get("page"),
                bbox=block.get("bbox"),
                polygon=block.get("polygon"),
                section_path=section_path,
                text=text,
                content_hash=block_content_hash(text),
                asset_ids=asset_ids,
                ordinal=index,
            )
        )

    units = _units_from_toc(
        metadata.get("table_of_contents"),
        document_blocks,
        document_title=document_title,
    )
    health = _health_from_page_stats(metadata.get("page_stats"), document_blocks)

    return DocumentIR(
        ir_schema_version=IR_SCHEMA_VERSION,
        extractor=EXTRACTOR_NAME,
        extractor_version=extractor_version,
        blocks=document_blocks,
        units=units,
        assets=assets,
        health=health,
    )


def _units_from_toc(
    toc: list[Any] | None,
    blocks: list[DocumentBlock],
    *,
    document_title: str | None,
) -> list[DocumentUnit]:
    paged = [block for block in blocks if block.page is not None]
    max_page = max((block.page for block in paged), default=None)

    if not toc:
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

    entries: list[dict[str, Any]] = []
    for raw in toc:
        entry = raw if isinstance(raw, dict) else {
            "title": getattr(raw, "title", ""),
            "heading_level": getattr(raw, "heading_level", 1),
            "page_id": getattr(raw, "page_id", None),
        }
        entries.append(entry)
    entries.sort(key=lambda item: (item.get("page_id") if item.get("page_id") is not None else 0))

    units: list[DocumentUnit] = []
    parent_stack: list[tuple[int, str]] = []  # (heading_level, unit_id)
    for ordinal, entry in enumerate(entries, start=1):
        unit_id = f"u{ordinal}"
        level = int(entry.get("heading_level") or 1)
        page_start = entry.get("page_id")
        next_start = entries[ordinal].get("page_id") if ordinal < len(entries) else None
        if page_start is None:
            page_end = None
        elif next_start is None:
            page_end = max_page if max_page is not None else page_start
        else:
            page_end = max(page_start, int(next_start) - 1)

        while parent_stack and parent_stack[-1][0] >= level:
            parent_stack.pop()
        parent_unit_id = parent_stack[-1][1] if parent_stack else None

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
                ordinal=ordinal,
                locator={"scheme": "toc", "page": page_start, "heading_level": level},
                semantic_hash=semantic_hash(unit_blocks),
                page_start=page_start,
                page_end=page_end,
                span_ids=[block.span_id for block in unit_blocks],
            )
        )
        parent_stack.append((level, unit_id))
    return units


def _health_from_page_stats(
    page_stats: list[Any] | None,
    blocks: list[DocumentBlock],
) -> ExtractionHealth:
    if not page_stats:
        return ExtractionHealth()
    pages: list[PageHealth] = []
    methods: dict[int, str | None] = {}
    for raw in page_stats:
        stat = raw if isinstance(raw, dict) else {
            "page_id": getattr(raw, "page_id", None),
            "text_extraction_method": getattr(raw, "text_extraction_method", None),
            "block_counts": getattr(raw, "block_counts", None),
        }
        page_id = stat.get("page_id")
        method = stat.get("text_extraction_method")
        counts = _normalize_counts(stat.get("block_counts"))
        methods[page_id] = method
        pages.append(
            PageHealth(
                page=int(page_id) if page_id is not None else 0,
                text_extraction_method=method,
                block_counts=counts,
                flags=_page_flags(counts, blocks, page_id),
            )
        )

    # Flag pages whose extraction method differs from BOTH neighbors (§2.5).
    ordered = sorted(methods)
    for position, page_id in enumerate(ordered):
        method = methods[page_id]
        prev_method = methods[ordered[position - 1]] if position > 0 else None
        next_method = methods[ordered[position + 1]] if position + 1 < len(ordered) else None
        neighbors = [m for m in (prev_method, next_method) if m is not None]
        if method is not None and neighbors and all(method != m for m in neighbors):
            for page in pages:
                if page.page == page_id and "method_differs_from_neighbors" not in page.flags:
                    page.flags.append("method_differs_from_neighbors")

    doc_flags = sorted({flag for page in pages for flag in page.flags})
    return ExtractionHealth(pages=pages, flags=doc_flags)


def _normalize_counts(block_counts: Any) -> dict[str, int]:
    if isinstance(block_counts, dict):
        return {str(key): int(value) for key, value in block_counts.items()}
    counts: dict[str, int] = {}
    if isinstance(block_counts, (list, tuple)):
        for item in block_counts:
            if isinstance(item, (list, tuple)) and len(item) == 2:
                counts[str(item[0])] = int(item[1])
    return counts


def _page_flags(counts: dict[str, int], blocks: list[DocumentBlock], page_id: Any) -> list[str]:
    flags: list[str] = []
    total = sum(counts.values())
    image_like = sum(value for key, value in counts.items() if key.lower() in {"picture", "figure", "image"})
    text_like = sum(value for key, value in counts.items() if key.lower() in {"text", "textinlinemath", "listitem", "sectionheader"})
    if total > 0 and image_like > 0 and text_like == 0:
        flags.append("image_only_page")
    if total <= 1:
        flags.append("near_empty_page")
    page_text = "".join(block.text for block in blocks if block.page == page_id)
    if "�" in page_text:
        flags.append("replacement_characters")
    return flags


class MarkerDocumentExtractor:
    """High-fidelity local OCR/layout/math/table/figure extractor (§2.9).

    Import-guarded: constructing it when marker is absent is fine; ``extract``
    raises :class:`MarkerUnavailableError` so callers degrade explicitly to the
    approved fallback (§2.9 / §14 "missing Marker degrades explicitly").
    """

    name = EXTRACTOR_NAME

    def __init__(self, *, config: dict[str, Any] | None = None) -> None:
        self._config = dict(config or {})

    def version(self) -> str:
        return marker_package_version()

    def model_versions(self) -> dict[str, str]:
        # Best-effort; surya model weights carry no stable programmatic version.
        versions: dict[str, str] = {}
        for package in ("surya-ocr", "texify"):
            try:
                from importlib.metadata import version

                versions[package] = version(package)
            except Exception:
                continue
        return versions

    def extract(self, raw_bytes: bytes, context: ExtractionContext) -> DocumentIR:
        if not marker_available():
            raise MarkerUnavailableError(
                "marker-pdf is not installed; use the pypdf fallback or install learnloop[pdf]"
            )
        chunk_output = self._run_marker(raw_bytes, context)
        return chunk_output_to_ir(
            blocks=list(getattr(chunk_output, "blocks", [])),
            metadata=dict(getattr(chunk_output, "metadata", {}) or {}),
            page_info=dict(getattr(chunk_output, "page_info", {}) or {}),
            extractor_version=self.version(),
        )

    def _run_marker(self, raw_bytes: bytes, context: ExtractionContext) -> Any:  # pragma: no cover - needs marker
        import os
        import tempfile

        from marker.config.parser import ConfigParser
        from marker.converters.pdf import PdfConverter
        from marker.models import create_model_dict

        options: dict[str, Any] = {"output_format": "chunks", **self._config}
        torch_device = options.pop("torch_device", None)
        if torch_device:
            os.environ["TORCH_DEVICE"] = str(torch_device)
        parser = ConfigParser(options)
        converter = PdfConverter(
            config=parser.generate_config_dict(),
            artifact_dict=create_model_dict(),
            processor_list=parser.get_processors(),
            renderer=parser.get_renderer(),
            llm_service=parser.get_llm_service(),
        )
        with tempfile.TemporaryDirectory(prefix="learnloop-marker-") as tmp:
            pdf_path = Path(tmp) / "source.pdf"
            pdf_path.write_bytes(raw_bytes)
            return converter(str(pdf_path))
