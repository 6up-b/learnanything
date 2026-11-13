"""What other test files use from ``tests/test_mobile_v3_probes.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from learnloop.algorithm_versions import LATEST_ALGORITHM_VERSION
from learnloop.diagnosis.split.jobs import drain
from learnloop.followup_serve import workflow as wf
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.registry import METHOD_REGISTRY
from learnloop_sidecar.request_origin import RequestOrigin

from tests.followup_serve_helpers import LIVE_ITEM, BlindRivalClient, live_shape_vault
from tests.followup_rival_factor_helpers import _Ready, _generate


TAG = LATEST_ALGORITHM_VERSION
PHONE = RequestOrigin(device_id="dev_phone", phone_probes=True)


def _call(ctx, name, params, origin=None):
    spec = METHOD_REGISTRY[name]
    with ctx.acting_as(origin):
        return spec.handler(ctx, spec.params_model.model_validate(params))


def _refused(ctx, name, params, origin, code):
    with pytest.raises(SidecarError) as caught:
        _call(ctx, name, params, origin)
    assert caught.value.code == code, caught.value
    return caught.value


def _world(tmp_path, monkeypatch, *, version: str = TAG, owner=PHONE):
    paths, _vault, _repository = live_shape_vault(tmp_path, version=version)
    ctx = SidecarContext()
    ctx.load(paths.root)
    ctx.post_attempt_worker.autostart = False
    client = BlindRivalClient()
    monkeypatch.setattr("learnloop_sidecar.handlers.practice.ready_grading_provider",
                        lambda *_a, **_k: ("fake", _Ready(), client))
    session = _call(ctx, "start_session", {"availableMinutes": 30}, owner)["sessionId"]
    return SimpleNamespace(ctx=ctx, client=client, session=session, paths=paths)


@pytest.fixture
def world(tmp_path, monkeypatch):
    return _world(tmp_path, monkeypatch)


def _miss(world, origin) -> str:
    vault, repository = world.ctx.require_vault()
    result = _call(world.ctx, "submit_attempt", {
        "sessionId": world.session, "practiceItemId": LIVE_ITEM, "answerMd": "A = U Sigma V wrong",
        "attemptType": "independent_attempt", "latencySeconds": 60,
    }, origin)
    attempt_id = result["attemptId"]
    drain(vault, repository, client_factory=lambda: world.client, embedding_factory=lambda: None)
    return attempt_id


def _ready(world, origin):
    """A miss on ``origin``'s device with two rival causes, its question generated and ready."""

    attempt_id = _miss(world, origin)
    _generate(world)
    world.ctx.reload(maintenance=False)
    _vault, repository = world.ctx.require_vault()
    row = wf.attempt_workflow(repository, attempt_id)
    assert row["state"] == wf.READY and row["practice_item_id"], row
    return attempt_id, row, repository


def _adopt(world, origin):
    _vault, repository = world.ctx.require_vault()
    generation = int(repository.fetch_session(world.session).get("owner_generation") or 0)
    _call(world.ctx, "adopt_session", {"sessionId": world.session, "expectedGeneration": generation}, origin)
