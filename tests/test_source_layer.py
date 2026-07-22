"""Source-layer identity, hash split, extraction runs, adapters, and locator
backfill (spec_source_ingestion_v2 §2, §13, §14 rows 1-5 + hash split + backfill)."""

from __future__ import annotations

import io
from datetime import UTC, datetime

import pytest

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.ingest.extractors import (
    ExtractionContext,
    MarkerDocumentExtractor,
    PyPdfDocumentExtractor,
    captions_to_ir,
    markdown_to_ir,
)
from learnloop.ingest.extractors import marker as marker_mod
from learnloop.ingest.extractors.marker import MarkerUnavailableError, chunk_output_to_ir
from learnloop.ingest.hashing import (
    asset_hash,
    extraction_request_hash,
    extraction_result_hash,
)
from learnloop.ingest.ir import IR_SCHEMA_VERSION
from learnloop.ingest.locators import (
    ARXIV_LABEL_V1,
    BLOCK_SPAN_V1,
    HEADING_PATH_V1,
    TIME_RANGE_V1,
    detect_locator_scheme,
    format_block_span,
    parse_block_span,
)
from learnloop.ingest.source_library import register_source_revision
from tests.test_source_ingestion_adapters import _make_pdf_bytes

_CLOCK = FrozenClock(datetime(2026, 7, 13, 12, 0, 0, tzinfo=UTC))


def _repo(tmp_path) -> Repository:
    return Repository(tmp_path / "state.sqlite")


# --------------------------------------------------------------------------- #
# §14 row 1 — Import identity / dedup.
# --------------------------------------------------------------------------- #

def test_same_artifact_same_bytes_reuses_revision(tmp_path):
    repo = _repo(tmp_path)
    first = register_source_revision(
        repo, acquisition_kind="pdf", canonical_uri="https://ex/book.pdf", raw_bytes=b"BYTES", clock=_CLOCK
    )
    second = register_source_revision(
        repo, acquisition_kind="pdf", canonical_uri="https://ex/book.pdf", raw_bytes=b"BYTES", clock=_CLOCK
    )
    assert second.reused_revision is True
    assert first.revision_id == second.revision_id
    assert first.source_id == second.source_id


def test_different_artifacts_same_bytes_distinct_revisions(tmp_path):
    repo = _repo(tmp_path)
    one = register_source_revision(
        repo, acquisition_kind="pdf", canonical_uri="https://a/x.pdf", raw_bytes=b"SAME", clock=_CLOCK
    )
    two = register_source_revision(
        repo, acquisition_kind="pdf", canonical_uri="https://b/x.pdf", raw_bytes=b"SAME", clock=_CLOCK
    )
    assert one.source_id != two.source_id
    assert one.revision_id != two.revision_id
    # Same raw blob may be shared by mirrors: identical asset_hash is allowed.
    assert one.asset_hash == two.asset_hash


def test_same_artifact_changed_bytes_links_new_revision(tmp_path):
    repo = _repo(tmp_path)
    first = register_source_revision(
        repo, acquisition_kind="pdf", canonical_uri="https://ex/book.pdf", raw_bytes=b"V1", clock=_CLOCK
    )
    second = register_source_revision(
        repo, acquisition_kind="pdf", canonical_uri="https://ex/book.pdf", raw_bytes=b"V2", clock=_CLOCK
    )
    assert second.source_id == first.source_id
    assert second.revision_id != first.revision_id
    linked = repo.get_source_revision(second.revision_id)
    assert linked["supersedes_revision_id"] == first.revision_id
    artifact = repo.get_source_artifact(first.source_id)
    assert artifact["current_revision_id"] == second.revision_id


# --------------------------------------------------------------------------- #
# §14 hash-split row — request hash keys the retry ladder; result hash on
# completion drives cache/view identity.
# --------------------------------------------------------------------------- #

def test_retry_keys_on_request_hash_before_result_exists(tmp_path):
    repo = _repo(tmp_path)
    reg = register_source_revision(
        repo, acquisition_kind="pdf", canonical_uri="https://ex/b.pdf", raw_bytes=b"BYTES", clock=_CLOCK
    )
    request_hash = extraction_request_hash(
        revision_id=reg.revision_id,
        extractor="marker",
        extractor_version="1.9.0",
        package_version="1.9.0",
        config={"force_ocr": False},
        ir_schema_version=IR_SCHEMA_VERSION,
    )
    repo.insert_extraction_run(
        id="ext_1",
        revision_id=reg.revision_id,
        extractor="marker",
        extractor_version="1.9.0",
        extraction_request_hash=request_hash,
        ir_schema_version=IR_SCHEMA_VERSION,
        status="running",
        clock=_CLOCK,
    )
    # Retry finds the incomplete run by request hash alone (no IR needed yet).
    found = repo.extraction_run_by_request_hash(reg.revision_id, request_hash)
    assert found is not None
    assert found["extraction_result_hash"] is None
    assert found["status"] == "running"

    ir = chunk_output_to_ir(
        blocks=[{"id": "a", "block_type": "Text", "html": "<p>hi</p>", "page": 0, "bbox": None, "polygon": None, "section_hierarchy": None, "images": None}],
        metadata={},
        extractor_version="1.9.0",
    )
    result_hash = extraction_result_hash(request_hash, ir)
    repo.complete_extraction_run("ext_1", extraction_result_hash=result_hash, clock=_CLOCK)
    completed = repo.get_extraction_run("ext_1")
    assert completed["extraction_result_hash"] == result_hash
    assert completed["status"] == "completed"


def test_extraction_request_hash_unique_constraint(tmp_path):
    repo = _repo(tmp_path)
    reg = register_source_revision(
        repo, acquisition_kind="pdf", canonical_uri="https://ex/c.pdf", raw_bytes=b"BYTES", clock=_CLOCK
    )
    kwargs = dict(
        revision_id=reg.revision_id,
        extractor="marker",
        extractor_version="1.9.0",
        extraction_request_hash="sha256:dup",
        ir_schema_version=IR_SCHEMA_VERSION,
        clock=_CLOCK,
    )
    repo.insert_extraction_run(id="ext_a", **kwargs)
    with pytest.raises(Exception):
        repo.insert_extraction_run(id="ext_b", **kwargs)


def test_persist_and_load_document_ir_round_trips(tmp_path):
    repo = _repo(tmp_path)
    reg = register_source_revision(
        repo, acquisition_kind="pdf", canonical_uri="https://ex/d.pdf", raw_bytes=b"BYTES", clock=_CLOCK
    )
    ir = chunk_output_to_ir(
        blocks=[
            {"id": "a", "block_type": "SectionHeader", "html": "<h1>Eigenvalues</h1>", "page": 0, "bbox": [0, 0, 1, 1], "polygon": [[0, 0]], "section_hierarchy": {1: "Eigenvalues"}, "images": None},
            {"id": "b", "block_type": "Equation", "html": "$$Av=\\lambda v$$", "page": 0, "bbox": [0, 1, 1, 2], "polygon": None, "section_hierarchy": {1: "Eigenvalues"}, "images": None},
        ],
        metadata={"table_of_contents": [{"title": "Eigenvalues", "heading_level": 1, "page_id": 0}]},
        extractor_version="1.9.0",
    )
    repo.insert_extraction_run(
        id="ext_1", revision_id=reg.revision_id, extractor="marker", extractor_version="1.9.0",
        extraction_request_hash="sha256:req", ir_schema_version=IR_SCHEMA_VERSION, clock=_CLOCK,
    )
    repo.persist_document_ir("ext_1", ir)
    loaded = repo.load_document_ir("ext_1")
    assert loaded is not None
    assert [b.span_id for b in loaded.blocks] == [b.span_id for b in ir.blocks]
    assert loaded.units[0].semantic_hash == ir.units[0].semantic_hash
    assert loaded.blocks[1].block_type == "Equation"
    assert "\\lambda" in loaded.blocks[1].text  # equation kept verbatim


# --------------------------------------------------------------------------- #
# §14 marker adapter contract — chunks/ToC/page stats/figures map into IR.
# --------------------------------------------------------------------------- #

def _marker_chunk_output():
    blocks = [
        {"id": "/page/0/SectionHeader/0", "block_type": "SectionHeader", "html": "<h1>Eigenvalues</h1>", "page": 0, "bbox": [0, 0, 10, 1], "polygon": [[0, 0], [10, 0]], "section_hierarchy": {1: "Eigenvalues"}, "images": None},
        {"id": "/page/0/Text/1", "block_type": "Text", "html": "<p>An eigenvector of A is a nonzero vector.</p>", "page": 0, "bbox": [0, 1, 10, 2], "polygon": None, "section_hierarchy": {1: "Eigenvalues"}, "images": None},
        {"id": "/page/0/Equation/2", "block_type": "Equation", "html": "$$Av = \\lambda v$$", "page": 0, "bbox": [0, 2, 10, 3], "polygon": None, "section_hierarchy": {1: "Eigenvalues"}, "images": None},
        {"id": "/page/0/Figure/3", "block_type": "Figure", "html": "<p>Geometric action</p>", "page": 0, "bbox": [0, 3, 10, 4], "polygon": None, "section_hierarchy": {1: "Eigenvalues"}, "images": {"/page/0/Figure/3": "BASE64PNGDATA"}},
        {"id": "/page/1/Text/0", "block_type": "Text", "html": "<p>Exercises follow.</p>", "page": 1, "bbox": [0, 0, 10, 1], "polygon": None, "section_hierarchy": {1: "Exercises"}, "images": None},
    ]
    metadata = {
        "table_of_contents": [
            {"title": "Eigenvalues", "heading_level": 1, "page_id": 0, "polygon": [[0, 0]]},
            {"title": "Exercises", "heading_level": 1, "page_id": 1, "polygon": [[0, 0]]},
        ],
        "page_stats": [
            {"page_id": 0, "text_extraction_method": "surya", "block_counts": [["SectionHeader", 1], ["Text", 1], ["Equation", 1], ["Figure", 1]]},
            {"page_id": 1, "text_extraction_method": "pdftext", "block_counts": [["Text", 1]]},
        ],
    }
    return blocks, metadata


def test_marker_adapter_maps_chunks_toc_stats_and_figures(tmp_path):
    blocks, metadata = _marker_chunk_output()
    ir = chunk_output_to_ir(blocks=blocks, metadata=metadata, extractor_version="1.9.0")

    assert ir.extractor == "marker"
    assert ir.ir_schema_version == IR_SCHEMA_VERSION
    assert [b.span_id for b in ir.blocks] == ["s1", "s2", "s3", "s4", "s5"]
    assert ir.blocks[0].extractor_block_id == "/page/0/SectionHeader/0"
    assert ir.blocks[2].role_hint == "equation"
    assert "\\lambda" in ir.blocks[2].text  # equation verbatim
    assert ir.blocks[3].role_hint == "figure"

    # Figures become assets with a content hash and citation context.
    assert len(ir.assets) == 1
    assert ir.assets[0].content_hash.startswith("sha256:")
    assert ir.assets[0].neighboring_span_ids == ["s4"]

    # ToC → units, blocks assigned by page range.
    labels = {u.label: u for u in ir.units}
    assert set(labels) == {"Eigenvalues", "Exercises"}
    assert labels["Eigenvalues"].span_ids == ["s1", "s2", "s3", "s4"]
    assert labels["Exercises"].span_ids == ["s5"]

    # page_stats → health; page 1 method differs from its only neighbor.
    assert {p.page for p in ir.health.pages} == {0, 1}
    page1 = next(p for p in ir.health.pages if p.page == 1)
    assert "method_differs_from_neighbors" in page1.flags


def test_marker_semantic_hash_stable_under_cosmetic_html(tmp_path):
    blocks, metadata = _marker_chunk_output()
    fussy = [dict(block) for block in blocks]
    fussy[1]["html"] = "<div><span>An eigenvector of A is a nonzero vector.</span></div>"
    ir_a = chunk_output_to_ir(blocks=blocks, metadata=metadata, extractor_version="1.9.0")
    ir_b = chunk_output_to_ir(blocks=fussy, metadata=metadata, extractor_version="1.9.0")
    unit_a = next(u for u in ir_a.units if u.label == "Eigenvalues")
    unit_b = next(u for u in ir_b.units if u.label == "Eigenvalues")
    assert unit_a.semantic_hash == unit_b.semantic_hash


def test_missing_marker_degrades_explicitly(monkeypatch, tmp_path):
    monkeypatch.setattr(marker_mod, "marker_available", lambda: False)
    extractor = MarkerDocumentExtractor()
    with pytest.raises(MarkerUnavailableError):
        extractor.extract(b"%PDF-1.4", ExtractionContext(revision_id="rev_1"))


def test_marker_adapter_defaults_pdftext_to_one_worker():
    options = marker_mod._marker_runtime_options({})
    assert options["pdftext_workers"] == 1


def test_marker_adapter_preserves_explicit_pdftext_worker_override():
    options = marker_mod._marker_runtime_options({"pdftext_workers": 2})
    assert options["pdftext_workers"] == 2


def test_pypdf_fallback_produces_same_ir_contract():
    extractor = PyPdfDocumentExtractor()
    ir = extractor.extract(
        _make_pdf_bytes(["Eigenvalues are scalars.", "Second page text."]),
        ExtractionContext(revision_id="rev_1"),
    )
    assert ir.extractor == "pypdf"
    assert ir.ir_schema_version == IR_SCHEMA_VERSION
    assert len(ir.blocks) >= 1  # one block per page with native text
    assert "Eigenvalues are scalars." in " ".join(b.text for b in ir.blocks)
    assert ir.units and ir.units[0].semantic_hash
    assert all(b.content_hash.startswith("sha256:") for b in ir.blocks)


def test_pypdf_fallback_extracts_only_selected_original_pages():
    from pypdf import PdfReader, PdfWriter

    writer = PdfWriter()
    for text in ("First page text.", "Only this page.", "Last page text."):
        writer.add_page(PdfReader(io.BytesIO(_make_pdf_bytes([text]))).pages[0])
    stream = io.BytesIO()
    writer.write(stream)
    extractor = PyPdfDocumentExtractor()
    ir = extractor.extract(
        stream.getvalue(),
        ExtractionContext(revision_id="rev_1", page_selection=(1,)),
    )
    assert [block.page for block in ir.blocks] == [1]
    assert "Only this page." in ir.blocks[0].text
    assert ir.units[0].page_start == 1
    assert ir.units[0].page_end == 1


def test_pypdf_fallback_rejects_page_range_past_document_end():
    extractor = PyPdfDocumentExtractor()
    with pytest.raises(ValueError, match="exceeds the document's 1 pages"):
        extractor.extract(
            _make_pdf_bytes(["First page text."]),
            ExtractionContext(revision_id="rev_1", page_selection=(1,)),
        )


def test_non_pdf_normalizers_emit_trivial_ir():
    md = "# Intro\n\nFirst para.\n\n# Details\n\nSecond para.\n"
    html_ir = markdown_to_ir(md, title="Doc", extractor_name="html")
    assert html_ir.extractor == "html"
    assert {u.label for u in html_ir.units} == {"intro", "details"}
    assert all(b.page is None and b.bbox is None for b in html_ir.blocks)  # no geometry

    caption_ir = captions_to_ir(
        [{"start": 0.0, "end": 4.0, "text": "Welcome"}, {"start": 4.0, "end": 8.0, "text": "Today we cover eigenvalues"}],
        title="Lecture",
    )
    assert caption_ir.extractor == "youtube"
    assert caption_ir.units[0].locator["scheme"] == "time_range"
    assert caption_ir.units[0].locator["end"] == 8.0
    assert all(b.page is None for b in caption_ir.blocks)


# --------------------------------------------------------------------------- #
# §14 locator backfill — existing refs get shape-detected schemes; all resolve.
# --------------------------------------------------------------------------- #

def test_locator_scheme_shape_detection():
    assert detect_locator_scheme("root/eigenvalues/p1") == HEADING_PATH_V1
    assert detect_locator_scheme("t=12.5-30.0") == TIME_RANGE_V1
    assert detect_locator_scheme("thm:4.2") == ARXIV_LABEL_V1
    assert detect_locator_scheme("eq:1.2") == ARXIV_LABEL_V1
    assert detect_locator_scheme(format_block_span("ext_1", "s17")) == BLOCK_SPAN_V1
    assert detect_locator_scheme("") is None


def test_block_span_locator_round_trip():
    locator = format_block_span("ext_1", "s17")
    assert locator == "span:ext_1/s17"
    assert parse_block_span(locator) == ("ext_1", "s17")


def test_backfill_locator_schemes_stamps_and_is_idempotent(tmp_path):
    repo = _repo(tmp_path)
    legacy = ["root/eigenvalues/p1", "t=12.5-30.0", "thm:4.2", "eq:1.2"]
    stamped = repo.backfill_locator_schemes(legacy, clock=_CLOCK)
    assert stamped == {
        "root/eigenvalues/p1": HEADING_PATH_V1,
        "t=12.5-30.0": TIME_RANGE_V1,
        "thm:4.2": ARXIV_LABEL_V1,
        "eq:1.2": ARXIV_LABEL_V1,
    }
    # Declared schemes are never re-detected/converted on a second pass.
    again = repo.backfill_locator_schemes(legacy, clock=_CLOCK)
    assert again == stamped
    assert repo.locator_scheme("thm:4.2") == ARXIV_LABEL_V1


def test_legacy_locators_still_resolve_after_backfill(tmp_path):
    # The backfill is additive: legacy resolution is untouched (§2.4 permanence).
    from learnloop.codex.client import SourceChunk
    from learnloop.services.source_ingestion import _locator_resolves

    chunks = [
        SourceChunk(locator="root/eigenvalues/p1", text="An eigenvector.", chunk_kind="prose", heading_path=["root", "eigenvalues"], ordinal=1),
        SourceChunk(locator="t=0.0-4.0", text="Welcome", chunk_kind="caption", heading_path=["transcript"], ordinal=2),
        SourceChunk(locator="t=4.0-8.0", text="Eigenvalues", chunk_kind="caption", heading_path=["transcript"], ordinal=3),
    ]
    repo = _repo(tmp_path)
    repo.backfill_locator_schemes([chunk.locator for chunk in chunks], clock=_CLOCK)
    assert _locator_resolves(chunks, "root/eigenvalues/p1") is True
    assert _locator_resolves(chunks, "t=0.0-8.0") is True
