"""The grade's decision records (refactor B7, ADR-017): what the grader decided, and when a hold first applied.

A ``grade`` record is written once per live grade, by the attempt step's live
branch (``attempts.apply_attempt``, every recording door) and by a regrade,
inside their transactions and after the grade is computed. It carries ids, the
verdict class, the numbers and the versions: never the answer, the rubric's
prose or the feedback (the attempt row and the receipts hold those). When the
grade is held for review (``outcome_contract.grade_is_held``, evaluated in flight
by the step), a ``grade_held`` record follows it as its child. The hold stays a
predicate (``held_grades.held_for_review_attempts`` decides it on every read);
the record says when it first applied and why, so ``why attempt:<id>`` can.

Replay re-applies recorded attempts (``replace_existing``) and never reaches the
writers here (``tests/test_provenance.py``). The grader never reads the table.
"""

from __future__ import annotations

import logging
from collections.abc import Iterable, Mapping
from typing import Any

from learnloop import provenance
from learnloop.db.stores import provenance as decision_store

LOG = logging.getLogger(__name__)

GRADE = "grade"
GRADE_HELD = "grade_held"

#: The grade's verdict class, the record's ``rule``.
FULL_CREDIT, PARTIAL_CREDIT, NO_CREDIT, DONT_KNOW, STUCK = (
    "full_credit", "partial_credit", "no_credit", "dont_know", "stuck",
)

#: Who decided, by the grade's source (the blind door is named apart).
_DECIDED_BY = {"ai": "joint_grader", "codex": "joint_grader", "self": "self_grade", "deterministic": "deterministic"}

#: Ids named per list (review-reason ids, unverified criteria, error types); the rest are counted.
IDS_PER_LIST = 10


def _code(value: Any) -> str | None:
    return value if provenance.is_code(value) else None


def _ids(values: Iterable[Any]) -> tuple[list[str], int]:
    """Up to :data:`IDS_PER_LIST` code ids, and how many there were in all (odd ids counted, never named)."""

    values = [value for value in values if value is not None]
    named = [str(value) for value in values if provenance.is_code(str(value))]
    return sorted(set(named))[:IDS_PER_LIST], len(values)


def review_reason_class(reason: str | None) -> tuple[str | None, list[str]]:
    """``unknown_target_criterion:c1,c2`` -> (``unknown_target_criterion``, [``c1``, ``c2``]); prose -> ``unnamed``."""

    if not reason:
        return None, []
    head, _, rest = str(reason).partition(":")
    names, _ = _ids(part.strip() for part in rest.split(",") if part.strip())
    return (head if provenance.is_code(head) else "unnamed"), names


def verdict_class(*, rubric_score: float, max_points: float | None, correctness: float | None,
                  attempt_type: str | None, declared_dont_know: bool, declared_stuck: bool) -> str:
    if attempt_type == "dont_know" or declared_dont_know:
        return DONT_KNOW
    if declared_stuck:
        return STUCK
    if max_points:
        fraction = float(rubric_score) / float(max_points)
    else:
        fraction = float(correctness or 0.0)
    if fraction <= 0.0:
        return NO_CREDIT
    return FULL_CREDIT if fraction >= 1.0 else PARTIAL_CREDIT


def grade_record(
    *,
    attempt_id: str,
    practice_item_id: str | None,
    learning_object_id: str | None,
    rubric_score: float,
    max_points: float | None,
    correctness: float | None,
    grader_confidence: float | None,
    grading_source: str | None,
    grader_mode: str | None,
    manual_review_reason: str | None,
    fallback_reason: str | None = None,
    agent_run_id: str | None = None,
    attempt_type: str | None = None,
    hints_used: int = 0,
    declared_dont_know: bool = False,
    declared_stuck: bool = False,
    primed: bool = False,
    fsrs_rating: str | None = None,
    error_types: Iterable[Any] = (),
    held: bool = False,
    plan_presentation_id: str | None = None,
    probe_presentation_id: str | None = None,
    session_id: str | None = None,
    algorithm_version: str | None = None,
    grader_identity: tuple[str, str] | None = None,
    decided_by: str | None = None,
) -> provenance.DecisionRecord:
    """One grade's record (pure): the verdict class as ``rule``; the score, its maximum and the review reason's code
    in ``facts``; the grader's identity in ``versions``. ``decided_by`` overrides the grader's name (``regrade``)."""

    verdict = verdict_class(rubric_score=rubric_score, max_points=max_points, correctness=correctness,
                            attempt_type=attempt_type, declared_dont_know=declared_dont_know,
                            declared_stuck=declared_stuck)
    reason, reason_ids = review_reason_class(manual_review_reason)
    errors, errors_n = _ids(error_types)
    grader = decided_by or ("blind_grader" if grader_mode == "blind"
                            else _DECIDED_BY.get(str(grading_source or ""), _code(grading_source) or "unnamed"))
    facts: dict[str, Any] = {
        "rubric_score": float(rubric_score), "max_points": None if max_points is None else float(max_points),
        "correctness": None if correctness is None else round(float(correctness), 6),
        "grader_confidence": None if grader_confidence is None else round(float(grader_confidence), 6),
        "grading_source": _code(grading_source), "grader_mode": _code(grader_mode), "review_reason": reason,
        "review_reason_ids": reason_ids, "held": bool(held), "attempt_type": _code(attempt_type),
        "hints_used": int(hints_used or 0), "primed": bool(primed), "fsrs_rating": _code(fsrs_rating),
        "error_types": errors, "error_types_n": errors_n, "agent_run_id": _code(agent_run_id),
        "practice_item_id": _code(practice_item_id), "learning_object_id": _code(learning_object_id),
        "plan_presentation_id": _code(plan_presentation_id), "probe_presentation_id": _code(probe_presentation_id),
        "session_id": _code(session_id),
    }
    if fallback_reason:
        # The model grade failed and the learner's self-grade stood; the reason is a code, or it is not named.
        facts["fallback_reason"] = _code(fallback_reason) or "unnamed"
    versions: dict[str, Any] = {"algorithm_version": _code(algorithm_version)}
    if grader_identity:
        versions["grading_prompt_version"] = _code(grader_identity[0])
        versions["output_schema_version"] = _code(grader_identity[1])
    return provenance.DecisionRecord(
        kind=GRADE, status="fallback" if fallback_reason else "chosen", subject_kind="attempt",
        subject_id=attempt_id, chosen_ref=verdict, decided_by=grader, rule=verdict, facts=facts, versions=versions,
        detail_table="practice_attempts", detail_id=attempt_id, parent_id=provenance.current_cause(),
    )


def held_record(*, attempt_id: str, parent_id: str | None, manual_review_reason: str | None,
                unverified_criterion_ids: Iterable[Any] = (), contract_unrecorded: bool = False,
                algorithm_version: str | None = None) -> provenance.DecisionRecord:
    """The record of a hold's first application (pure): the grade is provisional, no evidence and no FSRS review,
    until a regrade or an adjudication assesses a criterion. ``rule`` names the hold."""

    from learnloop.outcome_contract import GRADE_CONTRACT_UNRECORDED, GRADE_HELD_FOR_REVIEW

    reason, reason_ids = review_reason_class(manual_review_reason)
    unverified, unverified_n = _ids(unverified_criterion_ids)
    return provenance.DecisionRecord(
        kind=GRADE_HELD, status="deferred", subject_kind="attempt", subject_id=attempt_id,
        decided_by="held_grade_predicate",
        rule=GRADE_CONTRACT_UNRECORDED if contract_unrecorded else GRADE_HELD_FOR_REVIEW,
        facts={"review_reason": reason, "review_reason_ids": reason_ids, "unverified_criteria": unverified,
               "unverified_criteria_n": unverified_n, "evidence": "withheld"},
        versions={"algorithm_version": _code(algorithm_version)},
        detail_table="practice_attempts", detail_id=attempt_id, parent_id=parent_id,
    )


def record_grade(repository: Any, *, held: bool, unverified_criterion_ids: Iterable[Any] = (),
                 **grade: Any) -> str | None:
    """Write the grade's record, and its hold's when ``held``, in the caller's transaction; the grade record's id.

    Never raises: a record that cannot be built or written logs a warning with the trace and the grade stands.
    """

    try:
        record = grade_record(held=held, **grade)
    except Exception as exc:  # noqa: BLE001 - a record never changes the decision it describes
        LOG.warning("decision record %r not written (trace %s): %s", GRADE, provenance.current_trace(),
                    type(exc).__name__)
        return None
    grade_id = decision_store.write_decision(repository, record)
    if held:
        try:
            hold = held_record(attempt_id=str(grade["attempt_id"]), parent_id=grade_id,
                               manual_review_reason=grade.get("manual_review_reason"),
                               unverified_criterion_ids=unverified_criterion_ids,
                               algorithm_version=grade.get("algorithm_version"))
        except Exception as exc:  # noqa: BLE001 - as above
            LOG.warning("decision record %r not written (trace %s): %s", GRADE_HELD, provenance.current_trace(),
                        type(exc).__name__)
        else:
            decision_store.write_decision(repository, hold)
    return grade_id


def held_now(repository: Any, attempt_id: str) -> bool:
    """THE held predicate over the ledger for one attempt, for a record only: a failed read is ``False`` and a warning,
    never an exception into the grade it describes."""

    try:
        from learnloop.held_grades import attempt_grade_held

        return bool(attempt_grade_held(repository, attempt_id))
    except Exception as exc:  # noqa: BLE001 - a record never changes the decision it describes
        LOG.warning("held predicate unread for a record (trace %s): %s", provenance.current_trace(),
                    type(exc).__name__)
        return False


def error_types_of(events: Iterable[Mapping[str, Any]]) -> list[Any]:
    return [event.get("error_type") for event in events if isinstance(event, Mapping)]
