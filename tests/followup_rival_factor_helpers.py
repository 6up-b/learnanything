"""What other test files use from ``tests/test_followup_rival_factor.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from learnloop.diagnosis.split.jobs import drain
from learnloop.followup_run import jobs
from learnloop_sidecar.registry import METHOD_REGISTRY

from tests.followup_serve_helpers import LIVE_ITEM, AuthorFake, author_clients


class _Ready:
    ready = True
    status = "ready"
    active_provider = "fake"
    provider_type = "codex_sdk"
    model = "fake-model"
    provider_revision = None
    message = None


def _call(ctx, name, params):
    spec = METHOD_REGISTRY[name]
    return spec.handler(ctx, spec.params_model.model_validate(params))


def _miss(desk, shape):
    desk.client.shape = shape
    vault, repository = desk.ctx.require_vault()
    result = _call(desk.ctx, "submit_attempt", {
        "sessionId": desk.session, "practiceItemId": LIVE_ITEM, "answerMd": "A = U Sigma V wrong",
        "attemptType": "independent_attempt", "latencySeconds": 60,
    })
    attempt_id = result.get("attemptId") or result["attempt_id"]
    drain(vault, repository, client_factory=lambda: desk.client, embedding_factory=lambda: None)
    return attempt_id


def _generate(desk, fake=None):
    vault, repository = desk.ctx.require_vault()
    fake = fake or AuthorFake()
    while jobs.process_next_job(vault, repository, owner="test", clients=author_clients(fake)) is not None:
        pass
    return fake
