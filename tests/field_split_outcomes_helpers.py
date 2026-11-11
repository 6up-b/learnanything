"""What other test files use from ``tests/test_field_split_outcomes.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from tests.diagnosis_fakes import ReviewFakeClient


class _ZeroEverythingWithoutAttribution(ReviewFakeClient):
    """Marks every criterion down to zero, naming no error at all."""

    def _blind_grading(self, request, context):
        result = super()._blind_grading(request, context)
        evidence = [row.model_copy(update={"points_awarded": 0.0}) for row in result.criterion_evidence]
        return result.model_copy(
            update={"criterion_evidence": evidence, "rubric_score": 0, "error_attributions": []}
        )
