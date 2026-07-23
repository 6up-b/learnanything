"""Annotation storage + sub-block reanchoring (spec §4, §15.1)."""

from __future__ import annotations

from pathlib import Path

import pytest

from learnloop.db.repositories import Repository
from learnloop.ingest.ir import DocumentBlock, DocumentIR, DocumentUnit, ExtractionHealth
from learnloop.services import annotations as ANN
from tests.test_source_inventory import _persist, _register_revision


def _ir(blocks: list[DocumentBlock], extractor_version: str = "1") -> DocumentIR:
    return DocumentIR(
        extractor="marker", extractor_version=extractor_version,
        units=[DocumentUnit(unit_id="u1", label="x", ordinal=0, semantic_hash="sha256:s", span_ids=[b.span_id for b in blocks])],
        blocks=blocks, assets=[], health=ExtractionHealth(),
    )


def _setup(tmp_path: Path) -> Repository:
    repo = Repository(tmp_path / "state.sqlite")
    _register_revision(repo, source_id="src1", revision_id="rev1")
    blocks = [
        DocumentBlock.build(span_id="s1", block_type="Text", text="The spectral theorem is central here.", ordinal=1, page=0, bbox=[10, 50, 300, 90], section_path=["Ch1"]),
        DocumentBlock.build(span_id="s2", block_type="Text", text="Eigenvalues are the variances along principal axes.", ordinal=2, page=0, bbox=[10, 100, 300, 140], section_path=["Ch1"]),
    ]
    _persist(repo, _ir(blocks), revision_id="rev1", extraction_id="ext1")
    return repo


def test_single_block_roundtrip_exact_source_text(tmp_path: Path) -> None:
    repo = _setup(tmp_path)
    tr = ANN.translate_selection(repo, extraction_id="ext1", raw_selection={"nodes": [{"span_id": "s1", "start": 4, "end": 12}]})
    assert tr["status"] == "exact"
    assert tr["segments"][0]["exact_quote"] == "spectral"
    result = ANN.append_annotation(repo, source_id="src1", revision_id="rev1", extraction_id="ext1", annotation_type="highlight", translation=tr)
    head = repo.annotation_head(result["annotation_id"])
    assert head["segments"][0]["exact_quote"] == "spectral"
    assert head["anchor"]["status"] == "exact"


def test_multi_block_selection_stores_multiple_segments(tmp_path: Path) -> None:
    repo = _setup(tmp_path)
    tr = ANN.translate_selection(
        repo, extraction_id="ext1",
        raw_selection={"nodes": [{"span_id": "s1", "quote": "spectral theorem"}, {"span_id": "s2", "quote": "Eigenvalues"}]},
    )
    assert tr["status"] == "exact"
    assert len(tr["segments"]) == 2
    result = ANN.append_annotation(repo, source_id="src1", revision_id="rev1", extraction_id="ext1", annotation_type="interpretation", translation=tr)
    head = repo.annotation_head(result["annotation_id"])
    assert [s["span_id"] for s in head["segments"]] == ["s1", "s2"]


def test_whitespace_normalized_quote_still_anchors_exact(tmp_path: Path) -> None:
    # A PDF text-layer selection legitimately differs in spacing/line breaks from
    # the extraction text; a unique whitespace-normalized match anchors exact.
    repo = _setup(tmp_path)
    tr = ANN.translate_selection(
        repo, extraction_id="ext1",
        raw_selection={"nodes": [{"span_id": "s1", "quote": "spectral  theorem is\ncentral"}]},
    )
    assert tr["status"] == "exact"
    assert tr["segments"][0]["exact_quote"] == "spectral theorem is central"
    assert tr["segments"][0]["geometry"] == {"page": 0, "bbox": [10, 50, 300, 90]}


def test_whitespace_normalized_match_still_requires_uniqueness(tmp_path: Path) -> None:
    repo = Repository(tmp_path / "state.sqlite")
    _register_revision(repo, source_id="src1", revision_id="rev1")
    blocks = [DocumentBlock.build(span_id="s1", block_type="Text", text="the axis and the axis again", ordinal=1)]
    _persist(repo, _ir(blocks), revision_id="rev1", extraction_id="ext1")
    tr = ANN.translate_selection(
        repo, extraction_id="ext1", raw_selection={"nodes": [{"span_id": "s1", "quote": "the  axis"}]}
    )
    assert tr["status"] == "needs_reanchor"


def test_ambiguous_selection_becomes_needs_reanchor_and_keeps_text(tmp_path: Path) -> None:
    repo = _setup(tmp_path)
    tr = ANN.translate_selection(repo, extraction_id="ext1", raw_selection={"nodes": [{"span_id": "sX", "quote": "missing"}]})
    assert tr["status"] == "needs_reanchor"
    assert tr["raw_selection"]["nodes"][0]["quote"] == "missing"  # learner text preserved


def test_duplicate_quote_uses_context_or_needs_reanchor(tmp_path: Path) -> None:
    repo = Repository(tmp_path / "state.sqlite")
    _register_revision(repo, source_id="src1", revision_id="rev1")
    # "axis" appears twice -> quote-only is ambiguous -> needs_reanchor.
    blocks = [DocumentBlock.build(span_id="s1", block_type="Text", text="one axis then another axis follows.", ordinal=1)]
    _persist(repo, _ir(blocks), revision_id="rev1", extraction_id="ext1")
    tr = ANN.translate_selection(repo, extraction_id="ext1", raw_selection={"nodes": [{"span_id": "s1", "quote": "axis"}]})
    assert tr["status"] == "needs_reanchor"


def test_duplicate_quote_with_glyph_context_anchors_the_right_occurrence(tmp_path: Path) -> None:
    # Atomic-unit ctrl+click capture sends the text around the unit from the
    # rendered surface; a clear context winner anchors instead of refusing.
    repo = Repository(tmp_path / "state.sqlite")
    _register_revision(repo, source_id="src1", revision_id="rev1")
    blocks = [DocumentBlock.build(span_id="s1", block_type="Text", text="one axis then another axis follows.", ordinal=1)]
    _persist(repo, _ir(blocks), revision_id="rev1", extraction_id="ext1")
    tr = ANN.translate_selection(
        repo, extraction_id="ext1",
        raw_selection={"nodes": [{"span_id": "s1", "quote": "axis", "prefix": "then another ", "suffix": " follows."}]},
    )
    assert tr["status"] == "exact"
    segment = tr["segments"][0]
    assert (segment["codepoint_start"], segment["codepoint_end"]) == (22, 26)
    # Murky context (fits neither occurrence clearly) still refuses (§3.2).
    tr = ANN.translate_selection(
        repo, extraction_id="ext1",
        raw_selection={"nodes": [{"span_id": "s1", "quote": "axis", "prefix": "zzz ", "suffix": " qqq"}]},
    )
    assert tr["status"] == "needs_reanchor"


def test_glyph_quote_with_divergent_math_anchors_fuzzy(tmp_path: Path) -> None:
    # pdf.js glyphs render math the extraction dropped or stored as LaTeX; the
    # fuzzy tier still anchors the selection inside the learner-chosen block.
    repo = Repository(tmp_path / "state.sqlite")
    _register_revision(repo, source_id="src1", revision_id="rev1")
    blocks = [DocumentBlock.build(span_id="s1", block_type="Text", text="Suppose $\\alpha, \\beta \\in \\mathbb{C}$. Then multiplication commutes.", ordinal=1)]
    _persist(repo, _ir(blocks), revision_id="rev1", extraction_id="ext1")
    tr = ANN.translate_selection(
        repo, extraction_id="ext1",
        raw_selection={"nodes": [{"span_id": "s1", "quote": "Suppose α, β ∈ C. Then multiplication commutes."}]},
    )
    assert tr["status"] == "exact"
    assert "multiplication commutes" in tr["segments"][0]["exact_quote"]


def test_marker_rerender_same_extraction_does_not_change_anchors(tmp_path: Path) -> None:
    repo = _setup(tmp_path)
    tr = ANN.translate_selection(repo, extraction_id="ext1", raw_selection={"nodes": [{"span_id": "s1", "quote": "spectral"}]})
    result = ANN.append_annotation(repo, source_id="src1", revision_id="rev1", extraction_id="ext1", annotation_type="highlight", translation=tr)
    before = repo.annotation_head(result["annotation_id"])
    # A pure re-render of the same extraction rebuilds only the crosswalk; the
    # annotation head is unchanged (no new version).
    after = repo.annotation_head(result["annotation_id"])
    assert before == after
    assert len(repo.annotation_history(result["annotation_id"])["anchors"]) == 1


def test_reanchor_across_reextraction_preserves_old_anchor(tmp_path: Path) -> None:
    repo = _setup(tmp_path)
    tr = ANN.translate_selection(repo, extraction_id="ext1", raw_selection={"nodes": [{"span_id": "s1", "quote": "spectral"}]})
    result = ANN.append_annotation(repo, source_id="src1", revision_id="rev1", extraction_id="ext1", annotation_type="highlight", translation=tr)
    # New extraction over the same revision, same text but a NEW span id.
    new_blocks = [
        DocumentBlock.build(span_id="sNEW1", block_type="Text", text="The spectral theorem is central here.", ordinal=1),
        DocumentBlock.build(span_id="sNEW2", block_type="Text", text="Eigenvalues are the variances along principal axes.", ordinal=2),
    ]
    _persist(repo, _ir(new_blocks, extractor_version="2"), revision_id="rev1", extraction_id="ext2")
    r = ANN.reanchor_annotation(repo, annotation_id=result["annotation_id"], new_extraction_id="ext2")
    assert r["status"] == "reanchored"
    history = repo.annotation_history(result["annotation_id"])
    assert len(history["anchors"]) == 2  # old anchor preserved, successor appended
    assert history["anchors"][0]["extraction_id"] == "ext1"
    assert history["anchors"][1]["extraction_id"] == "ext2"
    assert repo.annotation_head(result["annotation_id"])["segments"][0]["span_id"] == "sNEW1"


def test_removed_block_never_silently_steals_annotation(tmp_path: Path) -> None:
    repo = _setup(tmp_path)
    tr = ANN.translate_selection(repo, extraction_id="ext1", raw_selection={"nodes": [{"span_id": "s1", "quote": "spectral"}]})
    result = ANN.append_annotation(repo, source_id="src1", revision_id="rev1", extraction_id="ext1", annotation_type="highlight", translation=tr)
    # New extraction where the annotated block's text is GONE (replaced content).
    new_blocks = [DocumentBlock.build(span_id="sNEW", block_type="Text", text="Completely different content about matrices.", ordinal=1)]
    _persist(repo, _ir(new_blocks, extractor_version="2"), revision_id="rev1", extraction_id="ext2")
    r = ANN.reanchor_annotation(repo, annotation_id=result["annotation_id"], new_extraction_id="ext2")
    assert r["status"] == "needs_reanchor"  # never attaches to the wrong block


def test_manual_anchor_appends_successor(tmp_path: Path) -> None:
    repo = _setup(tmp_path)
    tr = ANN.translate_selection(repo, extraction_id="ext1", raw_selection={"nodes": [{"span_id": "s1", "quote": "spectral"}]})
    result = ANN.append_annotation(repo, source_id="src1", revision_id="rev1", extraction_id="ext1", annotation_type="highlight", translation=tr)
    r = ANN.manual_anchor(
        repo, annotation_id=result["annotation_id"], source_id="src1", revision_id="rev1", extraction_id="ext1",
        segments=[{"span_id": "s2", "block_content_hash": "sha256:x", "codepoint_start": 0, "codepoint_end": 11, "exact_quote": "Eigenvalues", "selection_text_hash": "h"}],
    )
    assert r["status"] == "manually_anchored"
    assert repo.annotation_head(result["annotation_id"])["anchor"]["status"] == "manually_anchored"
    assert len(repo.annotation_history(result["annotation_id"])["anchors"]) == 2


def test_edit_appends_version_and_delete_is_tombstone(tmp_path: Path) -> None:
    repo = _setup(tmp_path)
    tr = ANN.translate_selection(repo, extraction_id="ext1", raw_selection={"nodes": [{"span_id": "s1", "quote": "spectral"}]})
    result = ANN.append_annotation(repo, source_id="src1", revision_id="rev1", extraction_id="ext1", annotation_type="interpretation", learner_text="first", translation=tr)
    before_seg = repo.annotation_head(result["annotation_id"])["segments"][0]
    ANN.edit_annotation(repo, annotation_id=result["annotation_id"], learner_text="second")
    head = repo.annotation_head(result["annotation_id"])
    assert head["version"]["learner_text"] == "second"
    # A text-only edit carries the resolved anchor geometry/section/neighbors forward
    # unchanged (rather than blanking them).
    after_seg = head["segments"][0]
    assert after_seg["geometry_json"] == before_seg["geometry_json"]
    assert after_seg["section_path_json"] == before_seg["section_path_json"]
    assert after_seg["neighbor_hashes_json"] == before_seg["neighbor_hashes_json"]
    assert len(repo.annotation_history(result["annotation_id"])["versions"]) == 2
    # delete-intent is a tombstone event; the annotation row is not removed,
    # but the reading-surface listing honors the learner's delete intent.
    assert len(repo.annotations_for_source("src1")) == 1
    ANN.delete_intent_annotation(repo, annotation_id=result["annotation_id"], reason="no longer relevant")
    events = repo.annotation_history(result["annotation_id"])["events"]
    assert any(e["event_type"] == "delete_intent" for e in events)
    assert repo.annotation_head(result["annotation_id"]) is not None
    assert repo.annotations_for_source("src1") == []


def test_review_volume_budget_parks_over_budget(tmp_path: Path) -> None:
    repo = _setup(tmp_path)
    # Two annotations that will both fail to reanchor (content replaced).
    for quote in ("spectral", "Eigenvalues"):
        tr = ANN.translate_selection(repo, extraction_id="ext1", raw_selection={"nodes": [{"span_id": "s1" if quote == "spectral" else "s2", "quote": quote}]})
        ANN.append_annotation(repo, source_id="src1", revision_id="rev1", extraction_id="ext1", annotation_type="highlight", translation=tr)
    new_blocks = [DocumentBlock.build(span_id="sZ", block_type="Text", text="Unrelated replacement text.", ordinal=1)]
    _persist(repo, _ir(new_blocks, extractor_version="2"), revision_id="rev1", extraction_id="ext2")
    summary = ANN.reanchor_annotations_for_source(repo, source_id="src1", new_extraction_id="ext2", review_batch=1)
    assert summary["needs_reanchor"] == 2
    assert summary["parked_for_review"] is True
    assert len(summary["surfaced_for_review"]) == 1  # budget caps surfaced volume
