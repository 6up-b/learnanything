"""Primed retries: IRT easiness shift, last_evidence_at anchoring, source-ref
resolution for the feedback source-review panel, and the sim priming model."""

from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace

import pytest

from learnloop.config import MasteryConfig
from learnloop.db.repositories import MasteryState, Repository
from learnloop.ingest.extractors.normalizers import markdown_to_ir
from learnloop.ingest.hashing import extraction_request_hash
from learnloop.ingest.ir import IR_SCHEMA_VERSION
from learnloop.ingest.source_library import register_source_revision
from learnloop.services.mastery import MasteryObservation, update_mastery
from learnloop.services.source_review import resolve_source_refs
from learnloop.sim.student import Misconception, StudentProfile, SyntheticStudent
from learnloop.vault.models import Note, PracticeItem, Provenance, SourceRef

VERSION = "mvp-0.5"
NOW = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)
ANCHOR = "2026-07-01T09:00:00Z"


def _prior(mean: float = 0.0, variance: float = 1.0) -> MasteryState:
    return MasteryState("lo", mean, variance, 3, ANCHOR, VERSION, ANCHOR)


def _obs(score: int, *, primed: bool = False) -> MasteryObservation:
    return MasteryObservation(
        rubric_score=score,
        max_points=4,
        evidence_coverage=1.0,
        hint_dampening=1.0,
        grader_confidence=1.0,
        attempt_type="independent_attempt",
        observed_at=NOW,
        primed=primed,
    )


# ── mastery asymmetry under the priming b-offset ─────────────────────────────


def test_primed_success_moves_mean_less_than_cold_success():
    config = MasteryConfig()
    cold = update_mastery(_prior(), _obs(4), config, VERSION, item_b=0.0)
    primed = update_mastery(_prior(), _obs(4, primed=True), config, VERSION, item_b=-config.irt.priming_b_offset)
    assert 0.0 < primed.logit_mean - 0.0 < cold.logit_mean


def test_primed_failure_moves_mean_more_than_cold_failure():
    config = MasteryConfig()
    cold = update_mastery(_prior(), _obs(0), config, VERSION, item_b=0.0)
    primed = update_mastery(_prior(), _obs(0, primed=True), config, VERSION, item_b=-config.irt.priming_b_offset)
    assert primed.logit_mean < cold.logit_mean < 0.0


def test_primed_success_shrinks_variance_less():
    config = MasteryConfig()
    cold = update_mastery(_prior(), _obs(4), config, VERSION, item_b=0.0)
    primed = update_mastery(_prior(), _obs(4, primed=True), config, VERSION, item_b=-config.irt.priming_b_offset)
    assert primed.logit_variance > cold.logit_variance


def test_primed_attempt_keeps_last_evidence_at_ekf():
    posterior = update_mastery(_prior(), _obs(4, primed=True), MasteryConfig(), VERSION, item_b=-2.0)
    assert posterior.last_evidence_at == ANCHOR
    assert posterior.evidence_count == 4  # the belief still updates


def test_primed_attempt_keeps_last_evidence_at_legacy():
    config = MasteryConfig()
    config.irt.enabled = False
    posterior = update_mastery(_prior(), _obs(4, primed=True), config, VERSION)
    assert posterior.last_evidence_at == ANCHOR


def test_cold_attempt_advances_last_evidence_at():
    posterior = update_mastery(_prior(), _obs(4), MasteryConfig(), VERSION)
    assert posterior.last_evidence_at == "2026-07-06T12:00:00Z"


# ── source-ref resolution ─────────────────────────────────────────────────────


TEXT_BODY = """# Guide

## Background

First paragraph about the topic.

Second paragraph with the key definition.
"""

VIDEO_BODY = """# YouTube video abc123

[t=10.0-15.5] the derivative measures instantaneous change

[t=15.5-21.0] which we compute as the limit of secant slopes

[t=21.0-27.5] and this limit is what we call the derivative
"""


def _note(note_id: str, body: str, canonical: dict | None = None, path: str | None = None) -> Note:
    payload: dict = {
        "id": note_id,
        "source_type": "canonical_source",
        "body": body,
        "path": path or f"subjects/calc/notes/{note_id}.md",
    }
    if canonical is not None:
        payload["canonical_source"] = canonical
    return Note(**payload)


def _item(refs: list[SourceRef]) -> PracticeItem:
    return PracticeItem(
        id="pi_1",
        learning_object_id="lo_1",
        practice_mode="short_answer",
        prompt="?",
        expected_answer="!",
        provenance=Provenance(origin="canonical_extract", source_refs=refs),
        created_at=ANCHOR,
        updated_at=ANCHOR,
    )


def _vault(*notes: Note) -> SimpleNamespace:
    return SimpleNamespace(notes={note.id: note for note in notes})


def test_resolves_text_locator_to_section():
    note = _note("guide", TEXT_BODY, {"kind": "website_page", "title": "The Guide", "original_uri": "https://x.test/guide"})
    ref = SourceRef(ref_type="canonical_source", ref_id="guide", locator="guide/background/p2")
    [resolved] = resolve_source_refs(_vault(note), _item([ref]))
    assert resolved["locator_resolved"] is True
    assert resolved["section_md"] == "Second paragraph with the key definition."
    assert resolved["heading_path"] == ["guide", "background"]
    assert resolved["title"] == "The Guide"
    assert resolved["external_url"] == "https://x.test/guide"
    assert resolved["video"] is None


def test_dangling_locator_falls_back_to_quote():
    note = _note("guide", TEXT_BODY, {"kind": "website_page", "title": "The Guide"})
    ref = SourceRef(
        ref_type="canonical_source", ref_id="guide",
        locator="root/removed-section/p9", quote="The original excerpt.",
    )
    [resolved] = resolve_source_refs(_vault(note), _item([ref]))
    assert resolved["locator_resolved"] is False
    assert resolved["source_changed"] is True
    assert resolved["section_md"] == "The original excerpt."


def test_resolves_video_time_range():
    note = _note(
        "vid", VIDEO_BODY,
        {"kind": "youtube_video", "title": "Derivatives", "original_uri": "https://www.youtube.com/watch?v=abc123"},
    )
    ref = SourceRef(ref_type="canonical_source", ref_id="vid", locator="t=15.5-21.0")
    [resolved] = resolve_source_refs(_vault(note), _item([ref]))
    assert resolved["locator_resolved"] is True
    assert resolved["video"] == {"video_id": "abc123", "start_seconds": 15.5, "end_seconds": 21.0}
    # Excerpt window includes surrounding cues, not just the matched one.
    assert "secant slopes" in resolved["section_md"]
    assert "instantaneous change" in resolved["section_md"]


def test_bare_video_timestamp_resolves_single_cue():
    note = _note(
        "vid", VIDEO_BODY,
        {"kind": "youtube_video", "title": "Derivatives", "original_uri": "https://youtu.be/abc123"},
    )
    ref = SourceRef(ref_type="canonical_source", ref_id="vid", locator="t=22.0")
    [resolved] = resolve_source_refs(_vault(note), _item([ref]))
    assert resolved["locator_resolved"] is True
    assert resolved["video"]["video_id"] == "abc123"
    assert resolved["video"]["start_seconds"] == 22.0
    assert resolved["video"]["end_seconds"] is None
    assert "call the derivative" in resolved["section_md"]


def test_missing_note_falls_back_to_quote():
    ref = SourceRef(ref_type="canonical_source", ref_id="gone", quote="Lost excerpt.")
    [resolved] = resolve_source_refs(_vault(), _item([ref]))
    assert resolved["locator_resolved"] is False
    assert resolved["source_changed"] is True
    assert resolved["section_md"] == "Lost excerpt."


def test_missing_note_resolves_youtube_ingest_identity(tmp_path):
    repository = Repository(tmp_path / "state.sqlite")
    registered = register_source_revision(
        repository,
        acquisition_kind="youtube",
        canonical_uri="https://www.youtube.com/watch?v=abc123",
        raw_bytes=b"captions",
        original_uri="https://www.youtube.com/watch?v=abc123",
        display_title="Derivatives from First Principles — Math Channel",
    )
    ref = SourceRef(
        ref_type="canonical_source",
        ref_id=registered.source_id,
        revision_id=registered.revision_id,
        locator="t=15.5-21.0",
        quote="The derivative is a limit of secant slopes.",
    )

    [resolved] = resolve_source_refs(_vault(), _item([ref]), repository)

    assert resolved["title"] == "Derivatives from First Principles — Math Channel"
    assert resolved["external_url"] == "https://www.youtube.com/watch?v=abc123"
    assert resolved["video"] == {
        "video_id": "abc123",
        "start_seconds": 15.5,
        "end_seconds": 21.0,
    }


def test_feedback_resolves_current_ingest_span_and_filename(tmp_path):
    repository = Repository(tmp_path / "state.sqlite")
    registered = register_source_revision(
        repository,
        acquisition_kind="pdf",
        canonical_uri="file:///home/learner/problem-set.pdf",
        raw_bytes=b"%PDF-problem-set",
        original_uri="file:///home/learner/problem-set.pdf",
    )
    ir = markdown_to_ir(
        "# Exercises\nUse the singular-value decomposition to solve this problem.",
        title="Problem set",
        extractor_name="marker",
    )
    request_hash = extraction_request_hash(
        revision_id=registered.revision_id,
        extractor=ir.extractor,
        extractor_version=ir.extractor_version,
        ir_schema_version=IR_SCHEMA_VERSION,
    )
    repository.insert_extraction_run(
        id="ext_feedback",
        revision_id=registered.revision_id,
        extractor=ir.extractor,
        extractor_version=ir.extractor_version,
        extraction_request_hash=request_hash,
        ir_schema_version=IR_SCHEMA_VERSION,
    )
    repository.persist_document_ir("ext_feedback", ir)
    span = next(block for block in ir.blocks if "singular-value" in block.text)
    ref = SourceRef(
        ref_type="canonical_source",
        ref_id=registered.source_id,
        locator=f"span:ext_feedback/{span.span_id}",
    )

    [resolved] = resolve_source_refs(_vault(), _item([ref]), repository)

    assert resolved["title"] == "problem-set.pdf"
    assert resolved["locator_resolved"] is True
    assert "singular-value decomposition" in resolved["section_md"]


def test_non_displayable_ref_types_skipped():
    ref = SourceRef(ref_type="session", ref_id="s1")
    assert resolve_source_refs(_vault(), _item([ref])) == []


# ── sim priming model ─────────────────────────────────────────────────────────


def _criteria() -> list[tuple[str, float, dict[str, float]]]:
    return [("c1", 4.0, {"facet_a": 1.0})]


def test_priming_floors_effective_knowledge():
    profile = StudentProfile(true_mastery=0.05, slip=0.0, guess=0.0, dont_know_propensity=0.0, priming_level=1.0)
    student = SyntheticStudent(profile, seed=7)
    outcome = student.attempt(
        day=0.0, item_facet_weights={"facet_a": 1.0}, criteria=_criteria(), hints_available=0, primed=True
    )
    assert outcome.p_correct_truth == 1.0
    assert outcome.criterion_points["c1"] == 4.0


def test_sticky_misconception_survives_priming():
    profile = StudentProfile(
        true_mastery=0.9,
        source_remediation_rate=0.0,
        misconceptions=[Misconception(facet_id="facet_a", error_type="sign_error", strength=1.0)],
    )
    student = SyntheticStudent(profile, seed=7)
    outcome = student.attempt(
        day=0.0, item_facet_weights={"facet_a": 1.0}, criteria=_criteria(), hints_available=0, primed=True
    )
    assert outcome.misconception_fired == "sign_error"


def test_shallow_misconception_repaired_by_priming():
    profile = StudentProfile(
        true_mastery=0.9,
        source_remediation_rate=1.0,
        misconceptions=[Misconception(facet_id="facet_a", error_type="sign_error", strength=1.0)],
    )
    student = SyntheticStudent(profile, seed=7)
    outcome = student.attempt(
        day=0.0, item_facet_weights={"facet_a": 1.0}, criteria=_criteria(), hints_available=0, primed=True
    )
    assert outcome.misconception_fired is None
    assert student.misconception_strengths["facet_a"] == 0.0
