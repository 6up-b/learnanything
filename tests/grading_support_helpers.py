"""What other test files use from ``tests/test_grading_support.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from tests.diagnosis_fakes import ReviewFakeClient


class _ZeroWithoutAttribution(ReviewFakeClient):
    """Marks ``result`` down to zero on any answer, naming no error at all."""

    def _blind_grading(self, request, context):
        result = super()._blind_grading(request, context)
        evidence = [
            row.model_copy(update={"points_awarded": 0.0}) if row.criterion_id == "result" else row
            for row in result.criterion_evidence
        ]
        return result.model_copy(
            update={
                "criterion_evidence": evidence,
                "rubric_score": int(sum(row.points_awarded for row in evidence)),
                "error_attributions": [],
            }
        )
