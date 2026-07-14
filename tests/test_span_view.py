"""Open-in-source viewer (spec_source_ingestion_v2 §9.2, §14).

A block_span_v1 PDF locator renders its page geometry (bbox highlighted) with an
honest text fallback (no page raster is persisted); HTML/text uses scroll-to-
anchor. EVERY view records a source_exposure event.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.ingest.ir import DocumentBlock, DocumentIR, DocumentUnit, ExtractionHealth
from learnloop.services.span_view import SpanViewError, build_span_view

from tests.test_source_inventory import _persist, _register_revision

_CLOCK = FrozenClock(datetime(2026, 7, 13, 12, 0, 0, tzinfo=UTC))


def _pdf_block(span_id, text, *, ordinal, page, bbox):
    return DocumentBlock.build(
        span_id=span_id, block_type="Text", text=text, ordinal=ordinal,
        page=page, bbox=bbox, section_path=["Chapter 1"],
    )


def _ir_with_geometry() -> DocumentIR:
    blocks = [
        _pdf_block("s0", "Intro paragraph.", ordinal=0, page=1, bbox=[10.0, 10.0, 200.0, 40.0]),
        _pdf_block("s1", "A real square matrix is symmetric when A^T = A.", ordinal=1, page=1, bbox=[10.0, 50.0, 200.0, 90.0]),
        _pdf_block("s2", "The spectral theorem follows.", ordinal=2, page=2, bbox=[10.0, 10.0, 200.0, 40.0]),
    ]
    unit = DocumentUnit(
        unit_id="chapter_symmetry", label="Symmetric matrices", ordinal=0,
        semantic_hash="sha256:sym", page_start=1, page_end=2, span_ids=["s0", "s1", "s2"],
    )
    return DocumentIR(extractor="marker", extractor_version="1", units=[unit], blocks=blocks, assets=[], health=ExtractionHealth())


def _setup(tmp_path: Path) -> Repository:
    repo = Repository(tmp_path / "state.sqlite")
    _register_revision(repo, source_id="src1", revision_id="rev1")
    _persist(repo, _ir_with_geometry(), revision_id="rev1", extraction_id="ext1")
    return repo


def test_open_in_source_records_source_exposure_event(tmp_path):
    repo = _setup(tmp_path)
    assert repo.source_exposure_events(extraction_id="ext1") == []

    view = build_span_view(
        repo, "ext1", "s1",
        context="provenance", entity_type="facet", entity_id="facet_symmetry",
        clock=_CLOCK,
    )

    # PDF geometry: page + bbox highlighted; this fixture has no local original,
    # so the viewer uses its honest text fallback.
    assert view["viewer_mode"] == "pdf_text"
    assert view["page"] == 1
    assert view["bbox"] == [10.0, 50.0, 200.0, 90.0]
    assert view["locator_scheme"] == "block_span_v1"
    assert view["locator"] == "span:ext1/s1"
    assert view["page_render"] is None
    assert view["text"].startswith("A real square matrix")
    # Neighboring spans for prev/next; same-page spans for multi-highlight.
    assert [n["span_id"] for n in view["previous_spans"]] == ["s0"]
    assert [n["span_id"] for n in view["next_spans"]] == ["s2"]
    assert {s["span_id"] for s in view["page_spans"]} == {"s0", "s1"}  # page 1 only

    # EVERY view records a source_exposure event.
    events = repo.source_exposure_events(extraction_id="ext1", span_id="s1")
    assert len(events) == 1
    event = events[0]
    assert event["context"] == "provenance"
    assert event["entity_type"] == "facet"
    assert event["entity_id"] == "facet_symmetry"
    assert event["page"] == 1
    assert event["section_path"] == ["Chapter 1"]
    assert view["exposure_event_id"] == event["id"]

    # A second view records a second event (one per view, not deduped).
    build_span_view(repo, "ext1", "s1", context="registry_review", clock=_CLOCK)
    assert len(repo.source_exposure_events(extraction_id="ext1", span_id="s1")) == 2


def test_span_view_text_anchor_mode_without_geometry(tmp_path):
    repo = Repository(tmp_path / "state.sqlite")
    _register_revision(repo, source_id="src1", revision_id="rev1")
    unit = DocumentUnit(unit_id="u1", label="Section", ordinal=0, semantic_hash="h", span_ids=["s0"])
    block = DocumentBlock.build(span_id="s0", block_type="Text", text="Plain HTML block.", ordinal=0)
    ir = DocumentIR(extractor="html", extractor_version="1", units=[unit], blocks=[block], assets=[], health=ExtractionHealth())
    _persist(repo, ir, revision_id="rev1", extraction_id="ext1")

    view = build_span_view(repo, "ext1", "s0", context="library", clock=_CLOCK)
    assert view["viewer_mode"] == "text_anchor"
    assert view["page"] is None
    assert view["bbox"] is None
    assert len(repo.source_exposure_events(extraction_id="ext1")) == 1


def test_span_view_renders_available_local_pdf_page(tmp_path):
    from pypdf import PdfWriter

    repo = _setup(tmp_path)
    pdf_path = tmp_path / "book.pdf"
    writer = PdfWriter()
    writer.add_blank_page(width=300, height=400)
    writer.add_blank_page(width=300, height=400)
    with pdf_path.open("wb") as output:
        writer.write(output)
    with repo.connection() as connection:
        connection.execute(
            "UPDATE source_revisions SET original_uri = ? WHERE id = 'rev1'",
            (str(pdf_path),),
        )
        connection.commit()

    view = build_span_view(repo, "ext1", "s1", record=False)
    assert view["viewer_mode"] == "pdf_page"
    assert view["page_render"].startswith("data:image/png;base64,")
    assert view["page_render_size"] == [300.0, 400.0]


def test_span_view_typed_errors(tmp_path):
    repo = _setup(tmp_path)
    for extraction_id, span_id, code in [("missing", "s1", "extraction_not_found"), ("ext1", "s99", "span_not_found")]:
        try:
            build_span_view(repo, extraction_id, span_id, clock=_CLOCK)
            raise AssertionError("expected SpanViewError")
        except SpanViewError as exc:
            assert exc.code == code
    # A failed lookup records no exposure event.
    assert repo.source_exposure_events() == []
