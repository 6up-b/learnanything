"""What other test files use from ``tests/test_held_grade_evidence.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from datetime import timedelta

from learnloop.attempts.attempts import (
    ApplyAttemptInput,
    AttemptDraft,
    ResolvedGrade,
    apply_attempt,
    calculate_rubric_score,
    unverified_attribution_json,
)
from learnloop.attempts.grading import resolved_rubric
from learnloop.clock import FrozenClock
from learnloop.substrate.canonical_projection import (
    UNASSESSED_INTERPRETATION,
    UNVERIFIED_INTERPRETATION_KEY,
    held_for_review_attempts,
)

from tests.split_live_helpers import submit
from tests.route_rules_in_grader_helpers import (
    ALTERNATIVE,
    CLOCK,
    DivergentUnlocatedGrader,
    FullCreditGrader,
    _first_scheduled_attempt,
)


#: The gate version and review reason of mvp-0.17's route-check records (the
#: synthetic holds below are such records: history the predicate still reads).
PROOF_CHECK_VERSION = "proof-route-check-v3"
PROOF_ROUTE_REVIEW_REASON = "proof_route_check_flag"


def held_attempt_ids(repository, attempt_ids=None) -> frozenset[str]:
    """The ledger's held set (``learnloop.held_grades``), through the name the
    merge composed (``canonical_projection.held_for_review_attempts``)."""

    with repository.connection() as connection:
        return held_for_review_attempts(connection, attempt_ids)


def attempt_grade_held(repository, attempt_id) -> bool:
    return attempt_id in held_attempt_ids(repository, (attempt_id,))


#: The grader alone holds a divergent, unlocated grade (nothing assessed,
#: nothing validated) and releases it once it validates the route.
HOLDING = DivergentUnlocatedGrader
VALIDATING = FullCreditGrader


def _iso(when) -> str:
    return when.isoformat().replace("+00:00", "Z")


def _held_support(rubric) -> dict:
    every = sorted(criterion.id for criterion in rubric.criteria)
    return {
        "proof_route_check": {
            "status": "checked", "applied": True, "held_for_review": True,
            "version": PROOF_CHECK_VERSION, "unverified_criterion_ids": every,
            "unlocated_criterion_ids": every,
        },
        "unverified_criterion_ids": every,
        "valid_alternative_gate_applied": True,
        "valid_alternative_gate": {"final_answer": False, "proof_route": True},
        "assessed_shortfall": False,
        UNVERIFIED_INTERPRETATION_KEY: UNASSESSED_INTERPRETATION,
    }


def _held_apply(
    vault, repository, item_id, points, *, attempt_id, when, attempt_type="independent_attempt",
    presentation_id=None, answer_confidence=None, record=True, error_attributions=(),
):
    """A held grade through the shared attempt step, as the live door hands it
    (every criterion unassessed, the grader's own score, ``grade_held_for_review``),
    then its blind record (written after the step, as the live door does)."""

    rubric = resolved_rubric(vault, vault.practice_items[item_id])
    every = tuple(sorted(criterion.id for criterion in rubric.criteria))
    result = apply_attempt(
        vault,
        repository,
        ApplyAttemptInput(
            draft=AttemptDraft(
                practice_item_id=item_id, learner_answer_md="a route of my own",
                attempt_type=attempt_type, probe_presentation_id=presentation_id,
                answer_confidence=answer_confidence,
            ),
            attempt_id=attempt_id,
            grade=ResolvedGrade(
                rubric_score=calculate_rubric_score(rubric, dict(points), []),
                criterion_points=dict(points),
                evidence_rows=[
                    {
                        "id": f"ge_{attempt_id}_{cid}", "criterion_id": cid,
                        "points_awarded": float(value), "evidence": "grader", "notes": None,
                        "local_grader_id": "test", "grader_tier": 3, "created_at": _iso(when),
                        "attribution_json": unverified_attribution_json(),
                    }
                    for cid, value in points.items()
                ],
                error_attributions=list(error_attributions),
                grader_confidence=0.9,
                confidence=3,
                manual_review_reason=PROOF_ROUTE_REVIEW_REASON,
                feedback_md="held",
            ),
            grading_source="ai",
            unverified_criterion_ids=every,
            grade_held_for_review=True,
        ),
        clock=FrozenClock(when),
    )
    if record:
        repository.insert_blind_grade_record(
            attempt_id=attempt_id, agent_run_id=None, grading_prompt_version="blind-test",
            output_schema_version="BlindGradingProposal", context_hash=f"ctx-{attempt_id}",
            record={
                "practice_item_id": item_id, "rubric_score": result.rubric_score,
                "max_points": rubric.max_points,
                "criteria": [{"criterion_id": cid, "points_awarded": value} for cid, value in points.items()],
                "error_attributions": [], "fatal_errors": [],
                "grading_support": _held_support(rubric),
            },
            clock=FrozenClock(when),
        )
    return result


def _graded_apply(
    vault, repository, item_id, points, *, attempt_id, when, answer_confidence=None, error_attributions=(),
):
    """An ordinary (assessed) model grade through the shared attempt step."""

    rubric = resolved_rubric(vault, vault.practice_items[item_id])
    return apply_attempt(
        vault,
        repository,
        ApplyAttemptInput(
            draft=AttemptDraft(
                practice_item_id=item_id, learner_answer_md="an answer",
                attempt_type="independent_attempt", answer_confidence=answer_confidence,
            ),
            attempt_id=attempt_id,
            grade=ResolvedGrade(
                rubric_score=calculate_rubric_score(rubric, dict(points), []),
                criterion_points=dict(points),
                evidence_rows=[
                    {
                        "id": f"ge_{attempt_id}_{cid}", "criterion_id": cid,
                        "points_awarded": float(value), "evidence": "grader", "notes": None,
                        "local_grader_id": "test", "grader_tier": 3, "created_at": _iso(when),
                    }
                    for cid, value in points.items()
                ],
                error_attributions=list(error_attributions),
                grader_confidence=0.9,
                confidence=3,
                manual_review_reason=None,
                feedback_md="graded",
            ),
            grading_source="ai",
        ),
        clock=FrozenClock(when),
    )


T = CLOCK.now()


def _held_live(vault, repository):
    _first_scheduled_attempt(vault, repository)
    held = submit(vault, repository, HOLDING(), answer=ALTERNATIVE + " (again)",
                  when=T + timedelta(days=3))
    assert attempt_grade_held(repository, held.attempt_id)
    return held


def _hold_by_regrade(vault, repository, attempt_id, when):
    """The ledger a regrade INTO a hold leaves on an assessed attempt (review
    F1's supersession): every criterion re-graded unassessed over the machine
    tiers it replaces, the grader's own 0, and a held blind record. Readers
    that read the ledger see exactly what ``regrade_attempt`` writes; the
    vaults these readers live in run no route check of their own."""

    attempt = repository.fetch_practice_attempt(attempt_id)
    rubric = resolved_rubric(vault, vault.practice_items[attempt["practice_item_id"]])
    rows = [
        {
            "id": f"ge_hold_{attempt_id}_{criterion.id}", "criterion_id": criterion.id,
            "points_awarded": 0.0, "evidence": "regraded, held", "notes": None, "agent_run_id": None,
            "local_grader_id": None, "grader_tier": 3, "created_at": _iso(when),
            "attribution_json": unverified_attribution_json(),
        }
        for criterion in rubric.criteria
    ]
    repository.insert_regrade_evidence(
        attempt_id=attempt_id, new_evidence_rows=rows, superseded_by_evidence_id=rows[0]["id"],
        supersede_tiers=(1, 3), clock=FrozenClock(when),
    )
    repository.insert_blind_grade_record(
        attempt_id=attempt_id, agent_run_id=None, grading_prompt_version="blind-test",
        output_schema_version="BlindGradingProposal", context_hash=f"ctx-hold-{attempt_id}",
        record={
            "practice_item_id": attempt["practice_item_id"], "rubric_score": 0,
            "max_points": rubric.max_points,
            "criteria": [{"criterion_id": criterion.id, "points_awarded": 0.0} for criterion in rubric.criteria],
            "error_attributions": [], "fatal_errors": [], "regrade": True,
            "grading_support": _held_support(rubric),
        },
        clock=FrozenClock(when),
    )
    assert attempt_grade_held(repository, attempt_id)
