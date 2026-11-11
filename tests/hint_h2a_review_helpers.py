"""What other test files use from ``tests/test_hint_h2a_review.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.registry import METHOD_REGISTRY

from tests.hint_fakes import ITEM, WORK, ChooserFake, hint_vault, prefer, store_map


ARGMAX = '[hints]\nchoice_policy = "argmax"\n'


def _call(ctx, name, params):
    spec = METHOD_REGISTRY[name]
    return spec.handler(ctx, spec.params_model.model_validate(params))


def _sidecar(tmp_path):
    paths = hint_vault(tmp_path, config=ARGMAX)
    store_map(paths)
    ctx = SidecarContext()
    ctx.load(paths.root)
    ctx.grading_provider_override = "manual"
    ctx.hints_inline = False
    ctx.hint_seed = "e"
    session = _call(ctx, "start_session", {"energy": "medium"})["sessionId"]
    return paths, ctx, session


def _request(ctx, session, option: str, writer):
    ctx.hint_writer_client = writer
    ctx.hint_chooser_client = ChooserFake(prefer(option, 0.9))
    return _call(ctx, "practice.request_hint", {"sessionId": session, "practiceItemId": ITEM,
                                                "submissionId": "k1", "answerMd": WORK})
