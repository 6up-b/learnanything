"""What other test files use from ``tests/test_owner_capture_1025.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from learnloop_sidecar.registry import METHOD_REGISTRY

from tests.hint_fakes import ITEM, WORK


def _call(ctx, name, params):
    spec = METHOD_REGISTRY[name]
    return spec.handler(ctx, spec.params_model.model_validate(params))


def _press(ctx, session, key):
    return _call(ctx, "practice.request_hint", {"sessionId": session, "practiceItemId": ITEM, "submissionId": key,
                                                "answerMd": WORK})["result"]
