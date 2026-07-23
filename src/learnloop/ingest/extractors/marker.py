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
from learnloop.ingest.extractors.base import ExtractionContext, units_from_toc_entries
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

# Marker loads its CUDA models before PdfProvider asks pdftext to extract native
# PDF text.  pdftext's default ProcessPoolExecutor uses ``fork`` on Linux, so
# its workers inherit an already-initialized CUDA/PyTorch process and can hang
# forever waiting on inherited locks.  Keep that CPU-only pre-pass in-process;
# Marker/Surya's model inference remains GPU-batched.  Advanced callers may
# explicitly override this through marker_options when they run in a process
# topology where spawning pdftext workers is known to be safe.
_SAFE_PDFTEXT_WORKERS = 1

_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")
_VERBATIM_TYPES = {"equation", "equationnumber", "math", "inlinemath", "table", "tablegroup", "code", "codeblock"}


def _marker_runtime_options(config: dict[str, Any]) -> dict[str, Any]:
    options: dict[str, Any] = {"output_format": "chunks", **config}
    options.setdefault("pdftext_workers", _SAFE_PDFTEXT_WORKERS)
    return options


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
    values = [section_hierarchy.get(level, section_hierarchy.get(str(level))) for level in ordered_levels]
    return [str(value).strip() for value in values if value is not None and str(value).strip()]


_MATH_TAG_RE = re.compile(r"<math\b([^>]*)>(.*?)</math>", re.IGNORECASE | re.DOTALL)
_MATH_DISPLAY_BLOCK_RE = re.compile(r"""display\s*=\s*["']block["']""", re.IGNORECASE)


def _math_to_delimited(html: str) -> str:
    """Marker encodes math as ``<math display='inline|block'>LaTeX</math>``. Rewrite to
    $/$$ delimiters BEFORE tag stripping — stripping the tag bare leaves undelimited
    LaTeX that no downstream renderer can recognize as math."""

    def _sub(match: re.Match[str]) -> str:
        body = match.group(2).strip()
        if not body:
            return " "
        if _MATH_DISPLAY_BLOCK_RE.search(match.group(1) or ""):
            return f"$${body}$$"
        return f"${body}$"

    return _MATH_TAG_RE.sub(_sub, html)


def _block_text(block_type: str, html: str) -> str:
    normalized_type = (block_type or "").replace(" ", "").lower()
    unescaped = _unescape(_TAG_RE.sub(" ", _math_to_delimited(html or "")))
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
    embedded_outline: list[dict[str, Any]] | None = None,
) -> DocumentIR:
    """Pure marker ``ChunkOutput`` → :class:`DocumentIR` mapping (§2.3).

    ``embedded_outline`` (ToC-shaped entries from the PDF's bookmark tree) takes
    precedence over marker's detected table of contents for unit derivation."""

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
        embedded_outline=embedded_outline,
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
    embedded_outline: list[dict[str, Any]] | None = None,
) -> list[DocumentUnit]:
    """Units from the best available section source.

    The PDF's embedded outline (bookmarks) is author-curated — exact titles with
    real destination pages — so it beats marker's layout-detected ToC whenever it
    carries at least two entries (a lone "Cover" bookmark is no structure).
    Fallback order: embedded outline → marker ToC → whole document."""

    if embedded_outline and len(embedded_outline) >= 2:
        units = units_from_toc_entries(
            embedded_outline, blocks, document_title=document_title,
            locator_scheme="pdf_outline", drop_empty=True,
        )
        if units:
            return units

    entries: list[dict[str, Any]] = []
    for raw in toc or []:
        entry = raw if isinstance(raw, dict) else {
            "title": getattr(raw, "title", ""),
            "heading_level": getattr(raw, "heading_level", 1),
            "page_id": getattr(raw, "page_id", None),
        }
        entries.append(entry)
    return units_from_toc_entries(
        entries, blocks, document_title=document_title, locator_scheme="toc"
    )


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

    # Our chunk→IR mapping is part of the extraction contract: bumping this
    # changes extraction_request_hash so cached runs from an older mapping
    # (e.g. pre-math-delimiter _block_text) are not silently reused.
    # 3: units prefer the PDF's embedded outline over the detected ToC.
    CHUNK_MAP_VERSION = 3

    def __init__(self, *, config: dict[str, Any] | None = None) -> None:
        self._config = dict(config or {})

    def version(self) -> str:
        return f"{marker_package_version()}+map{self.CHUNK_MAP_VERSION}"

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
        from learnloop.ingest.extractors.pypdf import read_embedded_outline

        chunk_output = self._run_marker(raw_bytes, context)
        return chunk_output_to_ir(
            blocks=list(getattr(chunk_output, "blocks", [])),
            metadata=dict(getattr(chunk_output, "metadata", {}) or {}),
            page_info=dict(getattr(chunk_output, "page_info", {}) or {}),
            extractor_version=self.version(),
            embedded_outline=read_embedded_outline(raw_bytes),
        )

    def _run_marker(self, raw_bytes: bytes, context: ExtractionContext) -> Any:  # pragma: no cover - needs marker
        import os
        import tempfile

        from marker.config.parser import ConfigParser
        from marker.converters.pdf import PdfConverter
        from marker.models import create_model_dict

        options = _marker_runtime_options(self._config)
        if context.page_selection is not None:
            options["page_range"] = ",".join(str(page) for page in context.page_selection)
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
