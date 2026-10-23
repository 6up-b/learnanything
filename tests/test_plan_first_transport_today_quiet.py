"""Plan-first transport T1, landing onto main: opening Today never asks about OpenRouter.

Owner rule: LearnLoop asks "Use OpenRouter instead" only when a feature the
learner USED could not run. Today (the queue and the daily plan) runs two
readiness probes while it builds: the teach-back filter
(``teach_back_offerable``: teach-back items are dropped while their AI is
down) and the empty probe-pool sweep (``authoring_provider_available``:
generation needs are queued only while authoring is ready). Neither is a
feature the learner used, so neither makes an offer:

* the teach-back filter honours a grant (``quiet(honour_grants=True)``): once
  the learner chose OpenRouter for teach-back, Today offers teach-back items
  again, served there;
* the probe-pool sweep queues background generation, so it honours no grant
  (``quiet()``; a grant never serves background work).

Starting a teach-back (the feature, used) still offers. Nothing is sent.
"""
from __future__ import annotations

from typing import Any

import pytest

from learnloop.ai import plan_fallback
from learnloop.clock import FrozenClock

from tests.helpers import NOW, create_basic_vault, seed_due_item
from tests.openai_fakes import install_fake_openai
from tests.test_router_offer_log import _TEACH_BACK_ITEM

OFFER_KEYS = ("fallbackAvailable", "fallback_available", "fallbackTasks", "fallback_tasks")


@pytest.fixture(autouse=True)
def isolated(tmp_path, monkeypatch):
    monkeypatch.setenv("LEARNLOOP_CONFIG_DIR", str(tmp_path / "config"))  # the plan is signed out
    for name in ("LEARNLOOP_AI_PROVIDER", "LEARNLOOP_AI_FALLBACK", "OPENAI_API_KEY", "DEEPSEEK_API_KEY"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key-never-sent")
    plan_fallback.revoke_all()
    yield
    plan_fallback.revoke_all()


def _offers(value: Any) -> dict[str, Any]:
    found: dict[str, Any] = {}

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            for key, child in node.items():
                if key in OFFER_KEYS:
                    found[key] = child
                else:
                    walk(child)
        elif isinstance(node, list):
            for child in node:
                walk(child)

    walk(value)
    return found


def _served(response: dict[str, Any]) -> list[str]:
    result = response.get("result") or {}
    return [item["practiceItemId"] for section in result.get("sections", []) for item in section["items"]]


def _today_vault(tmp_path):
    from learnloop.vault.writer import upsert_practice_item

    paths = create_basic_vault(tmp_path / "vault")
    repository = seed_due_item(paths)
    upsert_practice_item(paths.root, _TEACH_BACK_ITEM, clock=FrozenClock(NOW))
    session_id = repository.create_session(energy=None, sleep_quality=None, available_minutes=20,
                                           notes_md_path=None)
    return paths, repository, session_id


def _rpc(ctx):
    from learnloop_sidecar.server import _handle

    def rpc(method_name: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        return _handle(ctx, {"jsonrpc": "2.0", "id": 1, "method": method_name, "params": params or {}})

    return rpc


def test_opening_today_never_asks_and_using_teach_back_still_does(tmp_path, monkeypatch):
    import learnloop_sidecar.handlers  # noqa: F401
    from learnloop_sidecar.context import SidecarContext

    fake_openai = install_fake_openai(monkeypatch)
    paths, _repository, session_id = _today_vault(tmp_path)
    ctx = SidecarContext()
    ctx.load(paths.root, maintenance=False)
    rpc = _rpc(ctx)
    # The RPCs the desktop runs on vault load and on Today make no offer.
    for method_name, params in (("load_vault", {}), ("get_ai_connection", {}), ("get_runtime_health", {}),
                                ("get_today_headline", {}), ("get_start_summary", {}),
                                ("get_today_queue", {"sessionId": session_id}), ("get_today_queue", {})):
        response = rpc(method_name, params)
        assert "result" in response, (method_name, response.get("error"))
        assert _offers(response) == {}, method_name
    # Teach-back is still filtered out while its AI is down (the probe answers "not ready").
    assert "pi_svd_teach_back" not in _served(rpc("get_today_queue", {"sessionId": session_id}))
    # The feature, used: starting the teach-back reports unavailable AND asks.
    started = rpc("start_teach_back", {"sessionId": session_id, "practiceItemId": "pi_svd_teach_back"})
    assert started["error"]["data"]["code"] == "provider_unavailable"
    assert started["error"]["data"]["details"]["fallback_tasks"] == ["teach_back"]
    # The learner chose OpenRouter for teach-back (and its grader): Today serves teach-back again, asking nothing.
    plan_fallback.remember_offer(paths.root, {"fallback_tasks": ["teach_back", "grading"]})
    plan_fallback.grant(paths.root, ["teach_back", "grading"])
    granted = rpc("get_today_queue", {"sessionId": session_id})
    assert _offers(granted) == {}
    assert "pi_svd_teach_back" in _served(granted)
    assert all(instance.requests == [] for instance in fake_openai.instances)  # built at most, never called


def test_the_probe_pool_sweep_asks_nothing_and_honours_no_grant(tmp_path):
    from learnloop.diagnosis.diagnostic_surface_supply import authoring_provider_available
    from learnloop.vault.loader import load_vault

    paths = create_basic_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    with plan_fallback.collecting() as offers:
        assert authoring_provider_available(vault) is None
    assert offers.hint() is None
    # Background generation is never served by a grant.
    plan_fallback.remember_offer(paths.root, {"fallback_tasks": ["authoring"]})
    plan_fallback.grant(paths.root, ["authoring"])
    with plan_fallback.collecting() as offers:
        assert authoring_provider_available(vault) is None
    assert offers.hint() is None
