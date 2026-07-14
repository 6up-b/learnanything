"""Deterministic cross-run span re-anchoring (spec_source_ingestion_v2 §2.4, §14 row 2)."""

from __future__ import annotations

from datetime import UTC, datetime

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.ingest.ir import IR_SCHEMA_VERSION, DocumentBlock, DocumentIR
from learnloop.ingest.reanchor import EXACT_HASH, GEOMETRY_SECTION, reanchor_spans
from learnloop.ingest.source_library import register_source_revision

_CLOCK = FrozenClock(datetime(2026, 7, 13, 12, 0, 0, tzinfo=UTC))


def _block(span_id, text, *, ordinal, page=None, section_path=None, bbox=None):
    return DocumentBlock.build(
        span_id=span_id,
        block_type="Text",
        text=text,
        ordinal=ordinal,
        page=page,
        section_path=section_path or [],
        bbox=bbox,
    )


def _ir(blocks):
    return DocumentIR(extractor="marker", extractor_version="1", blocks=blocks)


def test_unique_exact_hash_match_wins():
    old = _ir([_block("s1", "An eigenvector of A.", ordinal=1), _block("s2", "A basis spans V.", ordinal=2)])
    new = _ir([_block("t1", "A basis spans V.", ordinal=1), _block("t2", "An eigenvector of A.", ordinal=2)])
    result = reanchor_spans(old, new)
    assert result.needs_reanchor == []
    alias = result.alias_for("s1")
    assert alias.to_span_id == "t2"
    assert alias.match_kind == EXACT_HASH
    assert alias.confidence == 1.0


def test_duplicate_hashes_disambiguate_by_section_and_page():
    # Two blocks with identical text (repeated boilerplate/equation) must be
    # disambiguated by section path + page, not silently mismatched.
    old = _ir([
        _block("s1", "Q.E.D.", ordinal=1, page=1, section_path=["root", "proof-a"]),
        _block("s2", "Q.E.D.", ordinal=2, page=5, section_path=["root", "proof-b"]),
    ])
    new = _ir([
        _block("t1", "Q.E.D.", ordinal=1, page=5, section_path=["root", "proof-b"]),
        _block("t2", "Q.E.D.", ordinal=2, page=1, section_path=["root", "proof-a"]),
    ])
    result = reanchor_spans(old, new)
    assert result.needs_reanchor == []
    assert result.alias_for("s1").to_span_id == "t2"  # proof-a, page 1
    assert result.alias_for("s2").to_span_id == "t1"  # proof-b, page 5


def test_still_ambiguous_span_becomes_needs_reanchor():
    # Identical text, no distinguishing section/page/geometry/neighbors → ambiguous.
    old = _ir([_block("s1", "boilerplate", ordinal=1)])
    new = _ir([_block("t1", "boilerplate", ordinal=1), _block("t2", "boilerplate", ordinal=2)])
    result = reanchor_spans(old, new)
    assert result.aliases == []
    assert result.needs_reanchor == ["s1"]


def test_geometry_section_fallback_when_text_changed():
    # No exact-hash candidate (text re-OCR'd) → fall back to section/geometry.
    old = _ir([_block("s1", "eigenvalue lamda", ordinal=1, page=2, section_path=["root", "sec"], bbox=[0, 0, 1, 1])])
    new = _ir([_block("t1", "eigenvalue lambda", ordinal=1, page=2, section_path=["root", "sec"], bbox=[0, 0, 1, 1])])
    result = reanchor_spans(old, new)
    alias = result.alias_for("s1")
    assert alias is not None
    assert alias.match_kind == GEOMETRY_SECTION
    assert result.needs_reanchor == []


def test_reanchor_aliases_persist(tmp_path):
    repo = Repository(tmp_path / "state.sqlite")
    reg = register_source_revision(
        repo, acquisition_kind="pdf", canonical_uri="https://ex/b.pdf", raw_bytes=b"BYTES", clock=_CLOCK
    )
    for run_id, request_hash in (("ext_old", "sha256:old"), ("ext_new", "sha256:new")):
        repo.insert_extraction_run(
            id=run_id, revision_id=reg.revision_id, extractor="marker", extractor_version="1.9.0",
            extraction_request_hash=request_hash, ir_schema_version=IR_SCHEMA_VERSION, clock=_CLOCK,
        )
    repo.insert_span_reanchor(
        from_extraction_id="ext_old", from_span_id="s1",
        to_extraction_id="ext_new", to_span_id="t2",
        match_kind=EXACT_HASH, confidence=1.0, clock=_CLOCK,
    )
    rows = repo.span_reanchors_from("ext_old")
    assert len(rows) == 1
    assert rows[0]["to_span_id"] == "t2"
    assert rows[0]["match_kind"] == "exact_hash"
