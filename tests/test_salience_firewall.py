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

from learnloop.attempts import salience_firewall as SF
from learnloop.attempts.attempts import apply_attempt

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

    src = Path(__file__).resolve().parents[1] / "src" / "learnloop"
    belief_modules = (
        "attempts/evidence.py",
        "goals/certification.py",
        "learner/mastery.py",
        "substrate/canonical_projection.py",
        "diagnosis/probe_episodes.py",
        "goals/goal_contracts.py",
    )
    for module in belief_modules:
        path = src / module
        assert path.exists(), module
        text = path.read_text(encoding="utf-8")
        assert "salience_firewall" not in text, module
        assert "reader_capture" not in text, module


# -- the confirmed exception's carve-out (spec_adaptive_difficulty_v1 A12, §5.11; G-AD3-13) -----------

#: Every source table a reading record can come from, and some it never may.
_SOURCE_TABLES = ("reader_section_progress", "source_exposure_events", "question_events",
                  "reader_authored_questions", "interaction_events", "judgment_ledger", "reader_observations",
                  "practice_attempts", "salience_projections")
_MAGNITUDES = ("dwell_ms", "dwell_seconds", "active_seconds", "idle_seconds", "scroll_depth", "scroll_count",
               "highlight_count", "revisit_count", "outcome_class", "response_md", "answer_md", "answer_text",
               "visibility_ms", "payload_json")


def _record(kind: str, subkind: str, source_table: str, **extra: object) -> dict:
    return {"id": f"o:{kind}:{subkind}:{source_table}", "kind": kind, "subkind": subkind,
            "source_table": source_table, "source_id": "src", "source_written_at": "2026-10-12T09:00:00Z",
            "learning_object_id": "lo1", "facet_doses_json": '{"f1": 1.0}', "authority_class": SF.SALIENCE_ONLY,
            **extra}


#: §5.11's table, exactly: (kind, subkind, source table).
_LISTED = {
    ("reading", "section_read", "reader_section_progress"),
    ("reading", "passage_viewed", "source_exposure_events"),
    *{("reader_tutor_exchange", mode, "question_events")
      for mode in ("answer_directly", "help_me_reason", "ask_me_first", "unknown")},
    ("worked_example", "shown", "source_exposure_events"),
    ("worked_example", "in_completed_section", "reader_section_progress"),
    *{("in_passage_question", style, "reader_authored_questions")
      for style in ("recall", "next_step", "why_step", "assumptions")},
    ("in_passage_question", "owner_placed", "interaction_events"),
    ("in_passage_question", "self_check:matched", "judgment_ledger"),
    ("in_passage_question", "self_check:missed", "judgment_ledger"),
}
_KINDS = ("reading", "reader_tutor_exchange", "worked_example", "in_passage_question")
_CANDIDATES = sorted({(kind, subkind, table)
                      for kind in [*_KINDS, *SF.READING_EVENT_KINDS, *SF.SALIENCE_PROJECTIONS]
                      for subkind in {s for _k, s, _t in _LISTED} | {kind, "dwell", "skipped", "reconstruct"}
                      for table in _SOURCE_TABLES})


@pytest.mark.parametrize("source", _CANDIDATES)
def test_firewall_carve_out_admits_only_listed_kinds(source) -> None:
    """G-AD3-13 (fail-first: no carve-out existed). Over every reading kind, every salience
    projection and every source table, ``learning_opportunity_events`` admits exactly the listed
    sources of §5.11 and returns nothing for any other; no record carries a magnitude field; every
    record stays stamped ``salience_only``, so ``reject_salience`` and ``apply_attempt`` refuse it."""

    kind, subkind, table = source
    magnitudes = {name: 99 for name in _MAGNITUDES}
    records = SF.learning_opportunity_events([_record(kind, subkind, table, **magnitudes)])
    if source in _LISTED:
        (record,) = records
        assert set(record) == set(SF.LEARNING_OPPORTUNITY_FIELDS)
        assert not set(record) & set(_MAGNITUDES)
        assert record["authority_class"] == SF.SALIENCE_ONLY and record["facet_doses"] == {"f1": 1.0}
        with pytest.raises(SF.SalienceEvidenceRejected):
            SF.reject_salience(record)
        with pytest.raises(SF.SalienceEvidenceRejected):
            apply_attempt(None, None, SimpleNamespace(**record))  # type: ignore[arg-type]
    else:
        assert records == []


def test_carve_out_allowlist_is_the_sweeps_list_and_the_only_typed_value_is_the_verdict() -> None:
    from learnloop.adaptive_difficulty import reading

    assert set(SF.LEARNING_OPPORTUNITY_SOURCES) == _LISTED
    assert reading.SOURCES is SF.LEARNING_OPPORTUNITY_SOURCES
    verdicts = [(k, s, t) for k, s, t in SF.LEARNING_OPPORTUNITY_SOURCES if s.startswith("self_check:")]
    assert verdicts == [("in_passage_question", "self_check:matched", "judgment_ledger"),
                        ("in_passage_question", "self_check:missed", "judgment_ledger")]
    # The verdict comes from judgment_ledger only: never reader_authored_questions or an observation.
    for table in ("reader_authored_questions", "reader_observations", "interaction_events"):
        assert SF.learning_opportunity_events([_record("in_passage_question", "self_check:missed", table)]) == []
    # A record that is not salience-only, or carries no dose or LO, never passes.
    assert SF.learning_opportunity_events([_record("reading", "section_read", "reader_section_progress",
                                                   authority_class="evidence")]) == []
    assert SF.learning_opportunity_events([_record("reading", "section_read", "reader_section_progress",
                                                   facet_doses_json='{"f1": 5.0}')]) == []


def test_ad_replayer_reads_the_receipt_only_through_the_carve_out() -> None:
    src = Path(__file__).resolve().parents[1] / "src" / "learnloop" / "adaptive_difficulty"
    replay = (src / "replay.py").read_text(encoding="utf-8")
    assert "learning_opportunity_events(" in replay
    readers = [path.name for path in src.glob("*.py")
               if "ad_reading_opportunities" in path.read_text(encoding="utf-8")
               or "receipt_store.READING" in path.read_text(encoding="utf-8")]
    # The sweep writes it; the replayer reads it through the carve-out; the dose arm and the
    # serve's warmth read only ids and times (never a dose into the state). Since AD2+AD3 fix
    # round 8 every read goes through the material view (which revalidates each receipt's source
    # and hands the replayer rows that still pass only through the carve-out).
    assert set(readers) <= {"reading.py", "replay.py", "dose.py", "serving.py", "data_check.py", "backfill.py",
                            "material_view.py"}
