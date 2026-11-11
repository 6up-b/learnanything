"""What other test files use from ``tests/test_active_errors_overlay.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from tests.diagnosis_fakes import ReviewFakeClient


_DIAGNOSED = "The learner thinks V needs no transpose in the SVD."


class _StatementFake(ReviewFakeClient):
    """The M1 fake, with the diagnoser naming a misconception statement."""

    def __init__(self, *, causal_class: str = "learner_state", **kwargs):
        super().__init__(**kwargs)
        self.causal_class = causal_class

    def _diagnosis(self, request, context):
        result = super()._diagnosis(request, context)
        events = [
            event.model_copy(
                update={"misconception_statement": _DIAGNOSED, "causal_class": self.causal_class}
            )
            for event in result.event_diagnoses
        ]
        return result.model_copy(update={"event_diagnoses": events})
