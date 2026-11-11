"""What other test files use from ``tests/test_stuck_prompt.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from types import SimpleNamespace

from learnloop.attempts.attempts import AttemptDraft, complete_attempt_with_ai_required
from learnloop.attempts.post_attempt import run_post_attempt_pipeline

from tests.diagnosis_fakes import ReviewFakeClient
from tests.split_live_helpers import ReadyRuntime, at


ITEM = "pi_svd_compute_001"


class StuckFake(ReviewFakeClient):
    """The M1/M2 fake, plus a stuck reading whenever the prompt asks for one."""

    def __init__(self, *, reading: dict | None = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.reading = reading or {"attempts_answer": True, "describes_confusion": False, "confusion_quote": ""}
        self.contexts: list[dict] = []

    def _blind_grading(self, request, context):
        self.contexts.append(context)
        model = request.result_model
        if "stuck_reading" not in getattr(model, "model_fields", {}):
            return super()._blind_grading(request, context)
        base_model = model.__mro__[1]
        base = super()._blind_grading(SimpleNamespace(result_model=base_model), context)
        return model.model_validate({**base.model_dump(mode="json"), "stuck_reading": self.reading})

    def _grading(self, request, context):
        # The joint grader (split off): the stuck reading when the joint
        # prompt asks for one (review F3), the plain proposal otherwise.
        self.contexts.append(context)
        base = super()._grading(request, context)
        model = request.result_model
        if "stuck_reading" not in getattr(model, "model_fields", {}):
            return base
        return model.model_validate({**base.model_dump(mode="json"), "stuck_reading": self.reading})


class RefusingClient(ReviewFakeClient):
    """Any model call is a test failure (the empty path has nothing to grade)."""

    def complete(self, request):  # pragma: no cover - must not run
        raise AssertionError(f"no model call expected, got {request.purpose}")


def _draft(answer: str, *, stuck: bool = True, **kwargs) -> AttemptDraft:
    return AttemptDraft(
        practice_item_id=kwargs.pop("item_id", ITEM),
        learner_answer_md=answer,
        attempt_type=kwargs.pop("attempt_type", "independent_attempt"),
        declared_stuck=stuck,
        **kwargs,
    )


def _grade(vault, repository, client, draft, *, when=21):
    from learnloop.clock import FrozenClock

    clock = FrozenClock(at(when))
    result = complete_attempt_with_ai_required(
        vault, repository, draft, runtime=ReadyRuntime(), ai_client=client, clock=clock
    )
    run_post_attempt_pipeline(vault, repository, result=result, clock=clock)
    return result
