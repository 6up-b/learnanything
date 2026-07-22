"""P3 slice 3 -- post-cold reader restoration (spec §11, §15.6)."""

from __future__ import annotations

from pathlib import Path

import pytest

from learnloop.db.repositories import Repository
from learnloop.ingest.ir import DocumentBlock, DocumentIR, DocumentUnit, ExtractionHealth
from learnloop.services import annotations as ANN
from learnloop.services import reader_restoration as REST
from learnloop.services.salience_firewall import SalienceEvidenceRejected, reject_salience
from tests.test_source_inventory import _persist, _register_revision


def _ir(blocks, extractor_version="1"):
    return DocumentIR(
        extractor="marker", extractor_version=extractor_version,
        units=[DocumentUnit(unit_id="u1", label="x", ordinal=0, semantic_hash="sha256:s",
                            span_ids=[b.span_id for b in blocks])],
        blocks=blocks, assets=[], health=ExtractionHealth(),
    )


def _setup(tmp_path: Path) -> Repository:
    repo = Repository(tmp_path / "state.sqlite")
    _register_revision(repo, source_id="src1", revision_id="rev1")
    blocks = [
        DocumentBlock.build(span_id="s1", block_type="Text",
                            text="The spectral theorem is central here.", ordinal=1, page=0,
                            bbox=[10, 50, 300, 90], section_path=["Ch1"]),
        DocumentBlock.build(span_id="s2", block_type="Text",
                            text="Eigenvalues are the variances along principal axes.", ordinal=2,
                            page=0, bbox=[10, 100, 300, 140], section_path=["Ch1"]),
    ]
    _persist(repo, _ir(blocks), revision_id="rev1", extraction_id="ext1")
    return repo


def _annotate(repo, quote, learner_text, what=None):
    tr = ANN.translate_selection(repo, extraction_id="ext1", raw_selection={"nodes": [{"span_id": "s1", "quote": quote}]})
    return ANN.append_annotation(
        repo, source_id="src1", revision_id="rev1", extraction_id="ext1",
        annotation_type="interpretation", learner_text=learner_text, what_i_think_is_going_on=what,
        translation=tr,
    )


def test_restore_returns_cited_blocks_and_annotation_heads_alongside_learner_wording(tmp_path):
    repo = _setup(tmp_path)
    _annotate(repo, "spectral", "my note on spectral", what="I think this is the key idea")
    result = REST.restore(repo, source_id="src1", extraction_id="ext1")
    assert result["observation_mutated"] is False
    assert result["annotations"], "cited annotation head restored"
    entry = result["annotations"][0]
    # Learner wording shown ALONGSIDE (distinct from) the source text (§11.3).
    assert entry["learner_text"] == "my note on spectral"
    assert entry["source_text"] == "The spectral theorem is central here."
    assert entry["learner_text"] != entry["source_text"]
    assert entry["provenance"] == "learner"


def test_orphaned_annotation_shows_quote_without_false_attachment(tmp_path):
    repo = _setup(tmp_path)
    _annotate(repo, "spectral", "good note")
    orphan = _annotate(repo, "spectral", "will orphan")
    # Re-extract with the annotated text GONE -> the second annotation orphans.
    new_blocks = [DocumentBlock.build(span_id="sNEW", block_type="Text",
                                      text="Completely different content.", ordinal=1)]
    _persist(repo, _ir(new_blocks, extractor_version="2"), revision_id="rev1", extraction_id="ext2")
    ANN.reanchor_annotation(repo, annotation_id=orphan["annotation_id"], new_extraction_id="ext2")
    result = REST.restore(repo, source_id="src1", extraction_id="ext1")
    review = result["anchor_needs_review"]
    assert any(e["annotation_id"] == orphan["annotation_id"] for e in review)
    # It shows the quote/context but is NOT attached to source text.
    flagged = next(e for e in review if e["annotation_id"] == orphan["annotation_id"])
    assert flagged["quote"] is not None
    assert "source_text" not in flagged


def test_restoration_records_salience_exposure_and_cannot_be_evidence(tmp_path):
    repo = _setup(tmp_path)
    _annotate(repo, "spectral", "note")
    result = REST.restore(repo, source_id="src1", extraction_id="ext1")
    # The restoration event is salience-only; the firewall rejects it as evidence.
    events = repo.reader_interaction_events(kind="reader_source_restored")
    assert any(e["id"] == result["event_id"] for e in events)
    ev = next(e for e in events if e["id"] == result["event_id"])
    with pytest.raises(SalienceEvidenceRejected):
        reject_salience(ev)
    # A source-restoration exposure was recorded under the reader_restoration context.
    with repo.connection() as c:
        n = c.execute("SELECT COUNT(*) FROM source_exposure_events WHERE context='reader_restoration'").fetchone()[0]
    assert n >= 1


def test_early_open_is_contamination(tmp_path):
    repo = _setup(tmp_path)
    # Opening restoration material before the response is a contamination event; with
    # no open cold administration nothing is burned but the exposure is recorded.
    out = REST.restore_before_response(repo, extraction_id="ext1", span_id="s1")
    assert out["contamination"] is True
    assert out["text"] == "The spectral theorem is central here."
