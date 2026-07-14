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
    page_render, page_render_size = _local_pdf_page_render(
        original_uri or canonical_uri, block.page
    )
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


def _local_pdf_page_render(
    uri: str | None, page: int | None
) -> tuple[str | None, list[float] | None]:
    if not uri or page is None or uri.startswith(("http://", "https://")):
        return None, None
    candidate = uri[7:] if uri.startswith("file://") else uri
    path = Path(candidate).expanduser()
    if path.suffix.lower() != ".pdf" or not path.is_file():
        return None, None
    try:
        import pypdfium2 as pdfium

        document = pdfium.PdfDocument(str(path))
        page_index = int(page)
        if page_index < 0 or page_index >= len(document):
            return None, None
        pdf_page = document[page_index]
        page_size = [float(value) for value in pdf_page.get_size()]
        bitmap = pdf_page.render(scale=1.4)
        image = bitmap.to_pil()
        output = io.BytesIO()
        image.save(output, format="PNG", optimize=True)
        encoded = "data:image/png;base64," + base64.b64encode(output.getvalue()).decode("ascii")
        return encoded, page_size
    except Exception:
        return None, None
