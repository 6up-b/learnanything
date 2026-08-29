"""One post-attempt pipeline, every door (exam-remediation package items 2+3).

Covers: ``finish_exam`` running the shared pipeline (needs/causal hooks/cold
probes minted from exam failures, feedback deferred to the report), the
per-sitting insertion cap with its typed suppression, and the lossless
``exam_answers.grade_json`` round-trip that lets exam error events carry the
P0b causal axes ``_hypothesis_specs`` reads.
"""

from __future__ import annotations

import dataclasses

from learnloop.clock import FrozenClock
from learnloop.attempts import post_attempt
from learnloop.attempts.attempts import GradeAttribution, ResolvedGrade
from learnloop.goals.exam_pool import reserve_exam_pool
from learnloop.goals.exam_session import (
    _grade_from_dict,
    _grade_to_dict,
    finish_exam,
    record_exam_answer,
    start_exam,
)
from learnloop.diagnosis.followups import FollowupDecision
from learnloop.attempts.post_attempt import (
    EXAM_SITTING_CAP_REASON,
    PostAttemptOutcome,
    run_exam_sitting_pipeline,
)
from learnloop.vault.loader import load_vault
from learnloop.vault.writer import upsert_practice_item

from tests.helpers import NOW, NOW_ISO, create_basic_vault, seed_due_item

LO_ID = "lo_svd_definition"
GOAL_ID = "goal_linear_algebra_ml"


def _add_item(root, item_id, *, facets, difficulty=0.5):
    upsert_practice_item(
        root,
        {
            "id": item_id,
            "learning_object_id": LO_ID,
            "subjects": None,
            "practice_mode": "short_answer",
            "attempt_types_allowed": ["independent_attempt", "dont_know"],
            "evidence_facets": facets,
            "evidence_weights": {facet: 1.0 for facet in facets},
            "prompt": f"Prompt {item_id}.",
            "expected_answer": "Answer.",
            "difficulty": difficulty,
            "grading_rubric": {
                "max_points": 4,
                "criteria": [{"id": "correctness", "points": 4, "description": "Correct."}],
                "fatal_errors": [],
            },
            "created_at": NOW_ISO,
            "updated_at": NOW_ISO,
        },
        clock=FrozenClock(NOW),
    )


def _vault(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    _add_item(vault_root, "pi_exam_a", facets=["recall"], difficulty=0.2)
    _add_item(vault_root, "pi_exam_b", facets=["apply"], difficulty=0.6)
    repository = seed_due_item(paths)
    return load_vault(vault_root), paths, repository


def _passing_grade() -> ResolvedGrade:
    return ResolvedGrade(
        rubric_score=4,
        criterion_points={"correctness": 4.0},
        evidence_rows=[],
        error_attributions=[],
        grader_confidence=1.0,
        confidence=4,
        manual_review_reason=None,
        feedback_md="Clean.",
    )


def _failing_grade_with_causal_axes() -> ResolvedGrade:
    return ResolvedGrade(
        rubric_score=0,
        criterion_points={"correctness": 0.0},
        evidence_rows=[],
        error_attributions=[
            GradeAttribution(
                error_type="recall_failure",
                severity=1.0,
                evidence="Stopped after naming the transformation.",
                is_misconception=False,
                misconception_statement="Believes transported operations equal the originals.",
                target_criterion_ids=["correctness"],
                resolution_status="resolved",
                cause_scope="learner_state",
                first_divergence={
                    "anchor_kind": "whole_answer",
                    "quote": "I know we need a transformation function",
                },
                candidate_causes=[
                    {
                        "statement": "Cannot derive the transported identity element.",
                        "target_ref": {
                            "kind": "criterion",
                            "criterion_id": "correctness",
                        },
                    }
                ],
            )
        ],
        grader_confidence=0.9,
        confidence=None,
        manual_review_reason=None,
        feedback_md="The identity must be derived through T, not assumed.",
        diagnosis_md="The learner names T but never applies T inverse to zero.",
    )


def _started_exam(tmp_path):
    vault, _paths, repository = _vault(tmp_path)
    reserve_exam_pool(vault, repository, vault.goals[0], item_count=2, clock=FrozenClock(NOW))
    session = start_exam(vault, repository, GOAL_ID, clock=FrozenClock(NOW))
    return vault, repository, session["session_id"]


# ----------------------------------------------------------------------
# Lossless grade round-trip (deliverable 2)
# ----------------------------------------------------------------------


def test_grade_json_round_trip_is_lossless_for_every_attribution_field():
    grade = _failing_grade_with_causal_axes()
    restored = _grade_from_dict(_grade_to_dict(grade))
    original = dataclasses.asdict(grade.error_attributions[0])
    round_tripped = dataclasses.asdict(restored.error_attributions[0])
    assert round_tripped == original
    assert restored.diagnosis_md == grade.diagnosis_md
    assert restored.feedback_md == grade.feedback_md


def test_grade_json_round_trip_tolerates_legacy_six_field_rows():
    legacy = {
        "rubric_score": 2,
        "criterion_points": {"correctness": 2.0},
        "evidence_rows": [],
        "error_attributions": [
            {
                "error_type": "recall_failure",
                "severity": 0.4,
                "evidence": None,
                "is_misconception": False,
                "target_evidence_families": [],
                "target_criterion_ids": ["correctness"],
            }
        ],
        "grader_confidence": 1.0,
        "confidence": None,
        "manual_review_reason": None,
        "feedback_md": None,
        "repair_suggestions": [],
        "fatal_errors": [],
    }
    restored = _grade_from_dict(legacy)
    attribution = restored.error_attributions[0]
    assert attribution.error_type == "recall_failure"
    assert attribution.candidate_causes == []
    assert attribution.first_divergence is None
    assert restored.diagnosis_md is None


# ----------------------------------------------------------------------
# finish_exam runs the shared pipeline (deliverables 1 + 2 end to end)
# ----------------------------------------------------------------------


def test_finish_exam_failure_reaches_needs_metadata_and_hypotheses(tmp_path):
    vault, repository, session_id = _started_exam(tmp_path)
    record_exam_answer(
        vault, repository, session_id, "pi_exam_a",
        answer_md="Correct derivation.", resolved_grade=_passing_grade(),
    )
    record_exam_answer(
        vault, repository, session_id, "pi_exam_b",
        answer_md="I know we need a transformation function",
        resolved_grade=_failing_grade_with_causal_axes(),
    )

    finish_exam(vault, repository, session_id, clock=FrozenClock(NOW))

    failing = repository.exam_answer(session_id, "pi_exam_b")
    attempt_id = failing["attempt_id"]
    assert attempt_id

    # The causal axes survived grade_json and landed on the error event.
    events = repository.error_events_for_attempt(attempt_id)
    assert events, "exam failure must persist its error event"
    plans = [event.get("repair_plan") or {} for event in events]
    assert any(plan.get("candidate_causes") for plan in plans)

    # The causal lane engaged: hypotheses exist instead of stalling at zero.
    hypotheses = repository.causal_hypotheses_for_attempt(attempt_id)
    assert hypotheses, "exam failure must produce causal hypotheses"

    # The pipeline persisted the metadata the exam report reads back.
    metadata = repository.fetch_attempt_feedback_metadata(attempt_id) or {}
    assert metadata.get("feedback_md") == (
        "The identity must be derived through T, not assumed."
    )

    # The intervention evaluator ran: the attempt's surprise row carries the
    # follow-up decision (queued, need recorded, or a typed suppression).
    surprise = repository.latest_attempt_surprise(attempt_id) or {}
    actions = list(surprise.get("triggered_actions") or []) + list(
        surprise.get("suppressed_actions") or []
    )
    assert any("intervention_followup" in action for action in actions)


def test_finish_exam_passing_answers_do_not_mint_followup_noise(tmp_path):
    vault, repository, session_id = _started_exam(tmp_path)
    for item_id in ("pi_exam_a", "pi_exam_b"):
        record_exam_answer(
            vault, repository, session_id, item_id,
            answer_md="Correct.", resolved_grade=_passing_grade(),
        )
    report = finish_exam(vault, repository, session_id, clock=FrozenClock(NOW))
    assert report["answered_count"] == 2
    assert repository.pending_intervention_needs() == [] or all(
        need.get("learning_object_id") != LO_ID
        for need in repository.pending_intervention_needs()
    )


def test_finish_exam_remains_idempotent_with_pipeline(tmp_path):
    vault, repository, session_id = _started_exam(tmp_path)
    record_exam_answer(
        vault, repository, session_id, "pi_exam_b",
        answer_md="wrong", resolved_grade=_failing_grade_with_causal_axes(),
    )
    first = finish_exam(vault, repository, session_id, clock=FrozenClock(NOW))
    hypotheses_after_first = len(
        repository.causal_hypotheses_for_attempt(
            repository.exam_answer(session_id, "pi_exam_b")["attempt_id"]
        )
    )
    second = finish_exam(vault, repository, session_id, clock=FrozenClock(NOW))
    assert second == first
    assert (
        len(
            repository.causal_hypotheses_for_attempt(
                repository.exam_answer(session_id, "pi_exam_b")["attempt_id"]
            )
        )
        == hypotheses_after_first
    )


# ----------------------------------------------------------------------
# The sitting cap (deliverable 1's batch nuance)
# ----------------------------------------------------------------------


@dataclasses.dataclass(frozen=True)
class _StubResult:
    attempt_id: str
    correctness: float | None


def _inserted_outcome(attempt_id: str) -> PostAttemptOutcome:
    decision = FollowupDecision(
        triggered=True,
        practice_item_id="pi_next",
        reason="severe_error",
        triggered_actions=[],
        suppressed_actions=[],
    )
    return PostAttemptOutcome(attempt_id=attempt_id, followup=decision)


def test_exam_sitting_cap_processes_worst_first_and_suppresses_the_rest(monkeypatch):
    calls: list[tuple[str, str | None]] = []

    def fake_pipeline(vault, repository, *, result, purpose, suppress_insertion_reason, clock):
        calls.append((result.attempt_id, suppress_insertion_reason))
        if suppress_insertion_reason is not None:
            return PostAttemptOutcome(
                attempt_id=result.attempt_id,
                followup=None,
                notes=(suppress_insertion_reason,),
            )
        return _inserted_outcome(result.attempt_id)

    monkeypatch.setattr(post_attempt, "run_post_attempt_pipeline", fake_pipeline)
    results = [
        _StubResult("a_pass", 1.0),
        _StubResult("b_worst", 0.0),
        _StubResult("c_bad", 0.25),
        _StubResult("d_mid", 0.5),
        _StubResult("e_low", 0.1),
    ]
    outcomes = run_exam_sitting_pipeline(
        object(), object(), results=results, intervention_cap=3
    )

    # Worst-first: ascending correctness, id as the deterministic tiebreak.
    assert [attempt for attempt, _ in calls] == [
        "b_worst", "e_low", "c_bad", "d_mid", "a_pass",
    ]
    # The three worst insert; everything after the cap is typed suppression.
    assert [reason for _, reason in calls] == [
        None, None, None, EXAM_SITTING_CAP_REASON, EXAM_SITTING_CAP_REASON,
    ]
    assert sum(1 for outcome in outcomes if outcome.inserted) == 3


def test_exam_sitting_pipeline_survives_a_failing_attempt(monkeypatch):
    def exploding_pipeline(vault, repository, *, result, purpose, suppress_insertion_reason, clock):
        if result.attempt_id == "boom":
            raise RuntimeError("bookkeeping failure")
        return _inserted_outcome(result.attempt_id)

    monkeypatch.setattr(post_attempt, "run_post_attempt_pipeline", exploding_pipeline)
    outcomes = run_exam_sitting_pipeline(
        object(),
        object(),
        results=[_StubResult("boom", 0.0), _StubResult("fine", 0.5)],
    )
    by_id = {outcome.attempt_id: outcome for outcome in outcomes}
    assert by_id["boom"].notes == ("pipeline_failed",)
    assert by_id["fine"].inserted
