"""Open-in-source span view (spec_source_ingestion_v2 §9.2).

Resolves a ``block_span_v1`` locator (``extraction_id`` + ``span_id``) to the
geometry and text the read-only viewer renders, and records a
``source_exposure`` event on EVERY view (§14). The viewer is minimal by design:

* PDF spans carry a page + bbox/polygon. When the pinned original is a readable
  local PDF, its requested page is rendered on demand (never persisted) and the
  frontend overlays the source geometry. Remote or unavailable originals use the
  labelled ``pdf_text`` fallback.
* HTML / plaintext spans have no page geometry; ``viewer_mode`` is
  ``text_anchor`` and the frontend scrolls to the block anchor and highlights it.

Neighboring spans (ordinal-adjacent blocks) are returned so prev/next paging and
multi-span page context work without a second round-trip.
"""

from __future__ import annotations

import base64
import io
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from learnloop.clock import Clock
from learnloop.db.repositories import Repository

# How many ordinal-adjacent blocks to return on each side for prev/next paging.
_NEIGHBOR_RADIUS = 3
# Neighbor previews are truncated; the focused span returns full text.
_NEIGHBOR_CHAR_CAP = 240

_VALID_CONTEXTS = {
    "provenance",
    "gate_diagnostic",
    "registry_review",
    "library",
    "other",
    # ING M8 (§9.2, §11): tutor-citation click-through, provenance-panel open, and
    # conflict-review span open all record exposure with their own discriminator.
    "tutor_citation",
    "provenance_panel",
    "conflict_review",
    "remediation",
    # P3 reader (§3, §11): render-view open + post-cold reader restoration.
    "reader",
    "reader_restoration",
    # Coldness receipts v2 (migration 150): a prescribed remediation passage's
    # text was DELIVERED to the surface that renders it inline. Weaker than
    # `remediation`, which means the learner opened the span deliberately.
    "remediation_delivery",
}


class SpanViewError(ValueError):
    """Typed failure for the get_span_view RPC."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def _neighbor(block: Any) -> dict[str, Any]:
    text = block.text or ""
    truncated = text[:_NEIGHBOR_CHAR_CAP]
    return {
        "span_id": block.span_id,
        "block_type": block.block_type,
        "page": block.page,
        "ordinal": block.ordinal,
        "text": truncated,
        "truncated": len(truncated) < len(text),
    }


def build_span_view(
    repo: Repository,
    extraction_id: str,
    span_id: str,
    *,
    context: str = "other",
    entity_type: str | None = None,
    entity_id: str | None = None,
    record: bool = True,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """Resolve a span to viewer geometry + text and record a source_exposure event."""

    if context not in _VALID_CONTEXTS:
        context = "other"

    ir = repo.load_document_ir(extraction_id)
    if ir is None:
        raise SpanViewError("extraction_not_found", f"No extraction IR for '{extraction_id}'.")
    block = ir.block_by_span(span_id)
    if block is None:
        raise SpanViewError("span_not_found", f"Span '{span_id}' not found in extraction '{extraction_id}'.")

    # Resolve the source chain for chrome + external-open fallback.
    run = repo.get_extraction_run(extraction_id)
    revision_id = run.get("revision_id") if run else None
    revision = repo.get_source_revision(revision_id) if revision_id else None
    source_id = revision.get("source_id") if revision else None
    original_uri = revision.get("original_uri") if revision else None
    artifact = repo.get_source_artifact(source_id) if source_id else None
    acquisition_kind = artifact.get("acquisition_kind") if artifact else None
    canonical_uri = artifact.get("canonical_uri") if artifact else None

    ordered = sorted(ir.blocks, key=lambda candidate: candidate.ordinal)
    index = next((i for i, candidate in enumerate(ordered) if candidate.span_id == span_id), None)
    previous_blocks: list[dict[str, Any]] = []
    next_blocks: list[dict[str, Any]] = []
    if index is not None:
        previous_blocks = [_neighbor(b) for b in ordered[max(0, index - _NEIGHBOR_RADIUS):index]]
        next_blocks = [_neighbor(b) for b in ordered[index + 1:index + 1 + _NEIGHBOR_RADIUS]]

    has_geometry = block.page is not None and bool(block.bbox)
    pdf_path = _original_pdf_path(repo, revision, original_uri or canonical_uri)
    page_render, page_render_size = _local_pdf_page_render(pdf_path, block.page)
    viewer_mode = "pdf_page" if page_render else ("pdf_text" if has_geometry else "text_anchor")
    # Every span on the focused page (multi-span highlight on one page).
    same_page_spans: list[dict[str, Any]] = []
    if block.page is not None:
        same_page_spans = [
            {"span_id": b.span_id, "bbox": b.bbox, "polygon": b.polygon}
            for b in ordered
            if b.page == block.page and b.bbox
        ]

    from learnloop.ingest.locators import BLOCK_SPAN_V1, format_block_span

    locator = format_block_span(extraction_id, span_id)
    exposure_event_id: str | None = None
    if record:
        exposure_event_id = repo.insert_source_exposure_event(
            {
                "context": context,
                "extraction_id": extraction_id,
                "span_id": span_id,
                "revision_id": revision_id,
                "source_id": source_id,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "page": block.page,
                "locator": locator,
                "section_path": list(block.section_path),
            },
            clock=clock,
        )

    return {
        "extraction_id": extraction_id,
        "span_id": span_id,
        "source_id": source_id,
        "revision_id": revision_id,
        "original_uri": original_uri,
        "canonical_uri": canonical_uri,
        "acquisition_kind": acquisition_kind,
        "viewer_mode": viewer_mode,
        "block_type": block.block_type,
        "page": block.page,
        "bbox": block.bbox,
        "polygon": block.polygon,
        "section_path": list(block.section_path),
        "text": block.text,
        "locator": locator,
        "locator_scheme": BLOCK_SPAN_V1,
        # Render opportunistically from an available local original. This keeps
        # the source layer byte-store-free while making local PDFs directly useful.
        "page_render": page_render,
        "page_render_size": page_render_size,
        "page_spans": same_page_spans,
        "previous_spans": previous_blocks,
        "next_spans": next_blocks,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "exposure_event_id": exposure_event_id,
    }


def record_span_exposures(
    repo: Repository,
    extraction_id: str,
    span_ids: list[str],
    *,
    context: str = "other",
    entity_type: str | None = None,
    entity_id: str | None = None,
    clock: Clock | None = None,
) -> list[str]:
    """Record a ``source_exposure`` event for each of these spans, in one
    transaction: the passages a surface DISPLAYED, not only the one it was
    asked for (Reader CA5a's peek shows a section's first blocks: Codex
    review F2). The same ledger and row shape as :func:`build_span_view`'s,
    so the coldness receipt's exposure scan matches each span exactly."""

    if context not in _VALID_CONTEXTS:
        context = "other"
    ir = repo.load_document_ir(extraction_id)
    if ir is None:
        raise SpanViewError("extraction_not_found", f"No extraction IR for '{extraction_id}'.")
    blocks = []
    for span_id in span_ids:
        block = ir.block_by_span(span_id)
        if block is None:
            raise SpanViewError("span_not_found", f"Span '{span_id}' not found in extraction '{extraction_id}'.")
        blocks.append(block)
    run = repo.get_extraction_run(extraction_id)
    revision_id = run.get("revision_id") if run else None
    revision = repo.get_source_revision(revision_id) if revision_id else None
    source_id = revision.get("source_id") if revision else None

    from learnloop.ingest.locators import format_block_span

    ids: list[str] = []
    with repo.atomic():
        for block in blocks:
            ids.append(repo.insert_source_exposure_event(
                {
                    "context": context,
                    "extraction_id": extraction_id,
                    "span_id": block.span_id,
                    "revision_id": revision_id,
                    "source_id": source_id,
                    "entity_type": entity_type,
                    "entity_id": entity_id,
                    "page": block.page,
                    "locator": format_block_span(extraction_id, block.span_id),
                    "section_path": list(block.section_path),
                },
                clock=clock,
            ))
    return ids


def _original_pdf_path(
    repo: Repository, revision: dict[str, Any] | None, fallback_uri: str | None
) -> Path | None:
    """Locate a readable local copy of the revision's original PDF: the vault's
    content-addressed store first (survives file moves), else the ingest-time
    ``original_uri``/``canonical_uri`` when it still points at a local file."""

    from learnloop.ingest.originals import is_pdf_file, resolve_original_file

    path = resolve_original_file(
        repo.sqlite_path.parent,
        digest=(revision or {}).get("asset_hash"),
        original_uri=(revision or {}).get("original_uri") or fallback_uri,
    )
    if path is not None and is_pdf_file(path):
        return path
    return None


# pdfium is not thread-safe, and the Reader's renders here are the only place
# the sidecar's own process enters it: imports read PDFs in worker processes
# (Marker: ingest/extractors/marker_worker.py; GLM-OCR's text layer and page
# images: glm_text_layer.pdfium_worker). This lock keeps the Reader's own
# renders one at a time whichever thread asks (a request, a view built in the
# background), and every pdfium object is closed inside it rather than
# whenever the garbage collector gets to it (docs/reviews/marker-pdfium-worker.md).
_PDFIUM_LOCK = threading.Lock()


@contextmanager
def _pdf_page(path: Path, page: int) -> Iterator[Any]:
    """The PDF's zero-based ``page`` (None when out of range), opened and
    closed under the pdfium lock."""

    import pypdfium2 as pdfium

    with _PDFIUM_LOCK:
        document = pdfium.PdfDocument(str(path))
        try:
            if page < 0 or page >= len(document):
                yield None
                return
            pdf_page = document[page]
            try:
                yield pdf_page
            finally:
                pdf_page.close()
        finally:
            document.close()


def _local_pdf_page_render(
    path: Path | None, page: int | None
) -> tuple[str | None, list[float] | None]:
    if path is None or page is None:
        return None, None
    try:
        with _pdf_page(path, int(page)) as pdf_page:
            if pdf_page is None:
                return None, None
            page_size = [float(value) for value in pdf_page.get_size()]
            bitmap = pdf_page.render(scale=1.4)
            try:
                output = io.BytesIO()
                bitmap.to_pil().save(output, format="PNG", optimize=True)
            finally:
                bitmap.close()
        encoded = "data:image/png;base64," + base64.b64encode(output.getvalue()).decode("ascii")
        return encoded, page_size
    except Exception:
        return None, None


_CROP_SCALE = 1.4


def _local_pdf_block_crop(
    path: Path | None, page: int | None, bbox: list[float] | None
) -> tuple[str | None, list[float] | None]:
    """Render an on-demand crop of one block's PDF region (spec §3.4). Derived from
    the pinned revision bytes + exact block geometry; NOT a new authoritative
    artifact and does not replace the source hash. bbox is in PDF-point space
    ([x0, y0, x1, y1], origin top-left) matching the page size before upscaling."""

    if path is None or page is None or not bbox or len(bbox) != 4:
        return None, None
    try:
        with _pdf_page(path, int(page)) as pdf_page:
            if pdf_page is None:
                return None, None
            page_size = [float(value) for value in pdf_page.get_size()]
            bitmap = pdf_page.render(scale=_CROP_SCALE)
            try:
                image = bitmap.to_pil()
                x0, y0, x1, y1 = (float(v) * _CROP_SCALE for v in bbox)
                left, right = sorted((x0, x1))
                top, bottom = sorted((y0, y1))
                left = max(0, int(left))
                top = max(0, int(top))
                right = min(image.width, int(round(right)))
                bottom = min(image.height, int(round(bottom)))
                if right <= left or bottom <= top:
                    return None, None
                output = io.BytesIO()
                image.crop((left, top, right, bottom)).save(output, format="PNG", optimize=True)
            finally:
                bitmap.close()
        encoded = "data:image/png;base64," + base64.b64encode(output.getvalue()).decode("ascii")
        return encoded, page_size
    except Exception:
        return None, None


def _local_pdf_crops(
    path: Path | None, page: int | None, boxes: list[list[float]]
) -> tuple[list[str | None], list[float] | None]:
    """Reader CA1: several crops of one PDF page, the page rendered once. Each
    box is in PDF-point space, as :func:`_local_pdf_block_crop`'s; a box that
    crops nothing gives None in its place (never the page)."""

    if path is None or page is None or not boxes:
        return [None for _ in boxes], None
    try:
        with _pdf_page(path, int(page)) as pdf_page:
            if pdf_page is None:
                return [None for _ in boxes], None
            page_size = [float(value) for value in pdf_page.get_size()]
            bitmap = pdf_page.render(scale=_CROP_SCALE)
            try:
                image = bitmap.to_pil()
                crops: list[str | None] = []
                for bbox in boxes:
                    if not bbox or len(bbox) != 4:
                        crops.append(None)
                        continue
                    x0, y0, x1, y1 = (float(v) * _CROP_SCALE for v in bbox)
                    left, right = sorted((x0, x1))
                    top, bottom = sorted((y0, y1))
                    left, top = max(0, int(left)), max(0, int(top))
                    right, bottom = min(image.width, int(round(right))), min(image.height, int(round(bottom)))
                    if right <= left or bottom <= top:
                        crops.append(None)
                        continue
                    output = io.BytesIO()
                    image.crop((left, top, right, bottom)).save(output, format="PNG", optimize=True)
                    crops.append("data:image/png;base64," + base64.b64encode(output.getvalue()).decode("ascii"))
            finally:
                bitmap.close()
        return crops, page_size
    except Exception:
        return [None for _ in boxes], None


def _local_pdf_page_label(path: Path | None, page: int | None) -> str | None:
    """The page's printed label from the PDF's own page labels (``/PageLabels``),
    or None when the file has none (the caller then shows the page's position)."""

    if path is None or page is None:
        return None
    try:
        import pypdfium2 as pdfium

        with _PDFIUM_LOCK:
            document = pdfium.PdfDocument(str(path))
            try:
                if page < 0 or page >= len(document):
                    return None
                label = document.get_page_label(int(page))
            finally:
                document.close()
    except Exception:
        return None
    label = (label or "").strip()
    return label or None


def build_block_region(
    repo: Repository,
    extraction_id: str,
    span_id: str,
    *,
    bbox: list[float] | None = None,
) -> dict[str, Any]:
    """On-demand original-region crop for one block (spec §3.4). Falls back to the
    whole page when no bbox is available, and records nothing (a pure read).

    ``bbox`` (reader workbench RW5a, a region of a figure): crop only that box,
    in the block's own coordinate space and clipped to the block, with no
    page fallback (a region that cannot be cropped is ``no_region``)."""

    ir = repo.load_document_ir(extraction_id)
    block = ir.block_by_span(span_id) if ir is not None else None
    if block is None:
        return {"extraction_id": extraction_id, "span_id": span_id, "region_render": None, "reason": "block_not_found"}
    if bbox is not None:
        return _block_subregion(repo, extraction_id, span_id, block, bbox)
    run = repo.get_extraction_run(extraction_id) or {}
    revision = repo.get_source_revision(run.get("revision_id")) if run.get("revision_id") else None
    source_id = (revision or {}).get("source_id")
    artifact = repo.get_source_artifact(source_id) if source_id else None
    uri = (revision or {}).get("original_uri") or (artifact or {}).get("canonical_uri")
    pdf_path = _original_pdf_path(repo, revision, uri)
    crop, page_size = _local_pdf_block_crop(pdf_path, block.page, block.bbox)
    reason = "crop"
    if crop is None:
        crop, page_size = _local_pdf_page_render(pdf_path, block.page)
        reason = "page_fallback" if crop is not None else "no_geometry"
    return {
        "extraction_id": extraction_id,
        "span_id": span_id,
        "page": block.page,
        "bbox": list(block.bbox) if block.bbox else None,
        "region_render": crop,
        "page_render_size": page_size,
        "reason": reason,
    }


def _original_pdf_for(repo: Repository, extraction_id: str) -> Path | None:
    run = repo.get_extraction_run(extraction_id) or {}
    revision = repo.get_source_revision(run.get("revision_id")) if run.get("revision_id") else None
    source_id = (revision or {}).get("source_id")
    artifact = repo.get_source_artifact(source_id) if source_id else None
    uri = (revision or {}).get("original_uri") or (artifact or {}).get("canonical_uri")
    return _original_pdf_path(repo, revision, uri)


def _block_subregion(repo: Repository, extraction_id: str, span_id: str, block: Any,
                     bbox: list[float]) -> dict[str, Any]:
    """A learner-drawn box inside one block: the box clipped to the block's own
    box (a box outside it crops nothing)."""

    base = {"extraction_id": extraction_id, "span_id": span_id, "page": block.page, "bbox": None,
            "region_render": None, "page_render_size": None, "reason": "no_region"}
    if not block.bbox or len(block.bbox) != 4 or len(bbox) != 4:
        return base
    try:
        x0, y0, x1, y1 = (float(value) for value in bbox)
    except (TypeError, ValueError):
        return base
    bx0, by0, bx1, by1 = (float(value) for value in block.bbox)
    left, right = max(min(x0, x1), min(bx0, bx1)), min(max(x0, x1), max(bx0, bx1))
    top, bottom = max(min(y0, y1), min(by0, by1)), min(max(y0, y1), max(by0, by1))
    if right - left < 2 or bottom - top < 2:
        return base
    clipped = [left, top, right, bottom]
    crop, page_size = _local_pdf_block_crop(_original_pdf_for(repo, extraction_id), block.page, clipped)
    if crop is None:
        return {**base, "bbox": clipped}
    return {**base, "bbox": clipped, "region_render": crop, "page_render_size": page_size, "reason": "crop"}
