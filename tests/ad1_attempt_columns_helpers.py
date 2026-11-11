"""What other test files use from ``tests/test_ad1_attempt_columns.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.registry import METHOD_REGISTRY

from tests.helpers import append_config_toml, create_basic_vault


ITEM = "pi_svd_define_001"


def _call(ctx, name: str, params: dict):
    spec = METHOD_REGISTRY[name]
    return spec.handler(ctx, spec.params_model.model_validate(params))


def _sidecar(tmp_path, *, config: str = ""):
    paths = create_basic_vault(tmp_path / "vault")
    if config:
        append_config_toml(paths.root, config)
    ctx = SidecarContext()
    ctx.load(paths.root)
    ctx.grading_provider_override = "manual"
    session = _call(ctx, "start_session", {"energy": "medium"})
    return paths, ctx, session["sessionId"]


def _save_draft(ctx, session_id, key, answer, **extra):
    return _call(ctx, "save_practice_draft", {"sessionId": session_id, "practiceItemId": ITEM, "answerMd": answer,
                                              "hintsUsed": 1, "submissionId": key, **extra})


def _checkpoint(ctx, session_id):
    return _call(ctx, "get_session", {"sessionId": session_id})["checkpoint"]
