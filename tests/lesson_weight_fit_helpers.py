"""Shared by the lesson-weight fit's tests: a graded answer with a chosen id (``tests/test_lesson_weight_fit_reads.py``,
``tests/test_lesson_weight_facts.py``)."""

from __future__ import annotations

from learnloop.vault.loader import load_vault


def apply_with_id(paths, repository, item_id, points, *, attempt_id, when, primed=False):
    """A self-graded answer with a chosen id, through the shared attempt step."""

    from learnloop.attempts.attempts import (
        ApplyAttemptInput,
        AttemptDraft,
        ResolvedGrade,
        apply_attempt,
        calculate_rubric_score,
    )
    from learnloop.attempts.grading import resolved_rubric
    from learnloop.clock import FrozenClock

    vault = load_vault(paths.root)
    rubric = resolved_rubric(vault, vault.practice_items[item_id])
    criterion = {"correctness": float(points)}
    stamp = when.isoformat().replace("+00:00", "Z")
    return apply_attempt(vault, repository, ApplyAttemptInput(
        draft=AttemptDraft(practice_item_id=item_id, learner_answer_md="an answer", attempt_type="independent_attempt",
                           primed=primed),
        attempt_id=attempt_id,
        grade=ResolvedGrade(
            rubric_score=calculate_rubric_score(rubric, criterion, []), criterion_points=criterion,
            evidence_rows=[{"id": f"ge_{attempt_id}", "criterion_id": "correctness", "points_awarded": float(points),
                            "evidence": "self", "notes": None, "local_grader_id": "self", "grader_tier": 1,
                            "created_at": stamp}],
            error_attributions=[], grader_confidence=1.0, confidence=3, manual_review_reason=None,
            feedback_md="self-graded"),
        grading_source="self"), clock=FrozenClock(when))
