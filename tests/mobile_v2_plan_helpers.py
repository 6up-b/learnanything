"""What other test files use from ``tests/test_mobile_v2_plan.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
from starlette.testclient import TestClient

import learnloop.clock as clock_module
from learnloop_mobile.host import create_app
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.registry import METHOD_REGISTRY

from tests.helpers import create_daily_plan_vault, write_yaml
from tests.mobile_host_helpers import HOSTNAME, CountingGrader, Phone, config_for, install_grader, pair


DAY = datetime(2026, 10, 12, 9, 0, tzinfo=UTC)
#: Its prompt embeds an image (PR-6's ``embeds_image``): the phone leaves it for the desktop.
HELD = "pi_a1"
ITEMS = {"lo_a": [("pi_a1", 2.0), ("pi_a2", 2.0)], "lo_b": [("pi_b1", 2.0), ("pi_b2", 2.0)]}


def _held_prompt(root: Path, item_id: str = HELD) -> None:
    import yaml

    path = next(root.rglob(f"{item_id}.yaml"))
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    payload["prompt"] = "Read the graph.\n\n![the graph](figures/graph.png)\n\nWhat is its slope?"
    write_yaml(path, payload)


@pytest.fixture
def plan_world(tmp_path, monkeypatch):
    monkeypatch.setattr(clock_module.SystemClock, "now", lambda _self: DAY)
    paths = create_daily_plan_vault(tmp_path / "vault", learning_objects=ITEMS)
    _held_prompt(paths.root)
    from learnloop.db.repositories import Repository

    repository = Repository(paths.sqlite_path)
    install_grader(monkeypatch, CountingGrader())
    device = pair(repository)
    app = create_app(config_for(paths.root))
    with TestClient(app, base_url=f"https://{HOSTNAME}") as client:
        yield Phone(client, device), app.state.host, repository, paths


def _desktop(root: Path) -> SidecarContext:
    ctx = SidecarContext()
    ctx.load(root)
    ctx.grading_provider_override = "manual"
    return ctx


def _call(ctx: SidecarContext, name: str, params: dict) -> Any:
    spec = METHOD_REGISTRY[name]
    return spec.handler(ctx, spec.params_model.model_validate(params))


def _next(phone: Phone, session_id: str, key: str, *, serve: bool = True) -> dict[str, Any]:
    return phone.rpc("next_plan_item", {"sessionId": session_id, "serve": serve}, request_id=key)


def _dont_know(phone: Phone, session_id: str, step: dict[str, Any], key: str) -> None:
    response = phone.post("submit_dont_know", {
        "sessionId": session_id, "practiceItemId": step["practiceItemId"], "submissionId": key, "hintsUsed": 0,
        "planPresentationId": step.get("presentationId"),
    }, request_id=key)
    assert response.status_code == 200, response.text


def _phone_day(phone: Phone, session_id: str, *, limit: int = 12) -> list[dict[str, Any]]:
    """The phone's Next, answered each time, until it gets anything but an item."""

    steps = []
    for index in range(limit):
        reply = _next(phone, session_id, f"next_{index}")
        step = reply["step"]
        steps.append(reply)
        if step is None or step["kind"] != "item":
            break
        _dont_know(phone, session_id, step, f"dk_{index}")
    return steps
