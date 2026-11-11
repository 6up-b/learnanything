"""What other test files use from ``tests/test_exam_session.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from learnloop.attempts.attempts import ResolvedGrade


def _grade(rubric_score: int) -> ResolvedGrade:
    return ResolvedGrade(
        rubric_score=rubric_score,
        criterion_points={"correctness": float(rubric_score)},
        evidence_rows=[],
        error_attributions=[],
        grader_confidence=1.0,
        confidence=4,
        manual_review_reason=None,
    )
