"""Reading-signal firewall (spec_p3_reader_integration §15.4, §8.2; design §C).

Parametrized over the FULL reader/reading kind vocabulary + every salience
projection: each must be rejected by the evidence-ingestion chokepoint. Plus a
static-import guard mirroring the familiarity rule-5 precedent: the belief-math /
certification modules never import the reading-signal firewall as an evidence
source. A newly-added reader kind that forgets its authority class fails here.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from learnloop.services import salience_firewall as SF
from learnloop.services.attempts import apply_attempt

ALL_SALIENCE = list(SF.READING_EVENT_KINDS) + list(SF.SALIENCE_PROJECTIONS)


@pytest.mark.parametrize("kind", ALL_SALIENCE)
def test_reject_salience_hard_rejects_every_reading_signal(kind: str) -> None:
    event = {"kind": kind, "payload": SF.salience_payload({"kind": kind})}
    with pytest.raises(SF.SalienceEvidenceRejected):
        SF.reject_salience(event)


@pytest.mark.parametrize("kind", ALL_SALIENCE)
def test_apply_attempt_chokepoint_rejects_salience(kind: str) -> None:
    # A salience-tagged input reaching the single evidence ingest step raises before
    # any belief work (the guard is the first line of apply_attempt).
    salient = SimpleNamespace(authority_class=SF.SALIENCE_ONLY, kind=kind)
    with pytest.raises(SF.SalienceEvidenceRejected):
        apply_attempt(None, None, salient)  # type: ignore[arg-type]


def test_salience_payload_always_stamps_authority_class() -> None:
    assert SF.salience_payload({})["authority_class"] == SF.SALIENCE_ONLY
    assert SF.salience_payload({"x": 1})["authority_class"] == SF.SALIENCE_ONLY


def test_non_salience_input_is_not_rejected() -> None:
    # Ordinary evidence has no salience authority class -> the guard is a no-op.
    SF.reject_salience({"kind": "attempt_duration", "payload": {"ms": 10}})
    SF.reject_salience(SimpleNamespace(kind="graded_attempt"))


def test_highlights_may_reorder_proposals_only() -> None:
    # The ONE allowed downstream (§8.2): proposal priority. It accepts salience and
    # never touches evidence.
    priority = SF.proposal_priority_signal(
        [
            {"kind": "reader_highlight", "subject_id": "s1"},
            {"kind": "reader_highlight", "subject_id": "s1"},
            {"kind": "reader_dwell", "subject_id": "s2"},
        ]
    )
    assert priority["s1"] > priority["s2"]


def test_salience_projection_v1_is_salience_only_and_rejected_as_evidence() -> None:
    """The versioned projector v1 (§8.2, slice 3) emits ONLY salience_only outputs; its
    whole result is rejected at the evidence chokepoint even though it carries a
    proposal_priority + depth_suggestion (those reorder proposals / suggest depth ONLY)."""

    events = [
        {"kind": "reader_highlight", "subject_id": "s1"},
        {"kind": "reader_highlight", "subject_id": "s1"},
        {"kind": "reader_view_opened", "subject_id": "s1"},
        {"kind": "reader_dwell", "subject_id": "s2"},
        {"kind": "reader_action_invoked", "subject_id": "s1",
         "payload": {"action": "mark_confusing"}},
    ]
    projection = SF.salience_projection_v1(events)
    assert projection["authority_class"] == SF.SALIENCE_ONLY
    assert projection["projector_version"] == SF.SALIENCE_PROJECTOR_VERSION
    # The one allowed downstream: reorder proposals / suggest depth. Never evidence.
    assert projection["proposal_priority"]["s1"] > 0
    assert projection["depth_suggestion"]["s1"] > 0
    with pytest.raises(SF.SalienceEvidenceRejected):
        SF.reject_salience(projection)


def test_salience_projection_dwell_is_bounded() -> None:
    # Even a flood of dwell segments is capped at DWELL_SEGMENT_MAX (§8.2): no
    # high-frequency timer ticks leak an unbounded number.
    events = [{"kind": "reader_dwell", "subject_id": "s1"} for _ in range(1000)]
    projection = SF.salience_projection_v1(events)
    assert projection["bounded_dwell"]["s1"] == SF.DWELL_SEGMENT_MAX


def test_belief_modules_never_import_the_reading_firewall() -> None:
    """Static guard (design §C.3): no belief-math / certification / projection module
    may import the reading-signal firewall as an evidence source. The reject guard
    lives at the ingest boundary (attempts), never inside the belief modules."""

    src = Path(__file__).resolve().parents[1] / "src" / "learnloop" / "services"
    belief_modules = (
        "evidence.py",
        "certification.py",
        "mastery.py",
        "canonical_projection.py",
        "probe_episodes.py",
        "goal_contracts.py",
    )
    for module in belief_modules:
        path = src / module
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        assert "salience_firewall" not in text, module
        assert "reader_capture" not in text, module
