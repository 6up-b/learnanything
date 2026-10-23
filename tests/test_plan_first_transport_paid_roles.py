"""Plan-first transport T1, landing onto main: the paid roles ask too.

T1's route-resolution property (``tests/test_plan_first_transport.py``,
section 1) resolves every ``AITask`` through ``ready_client_for_task``. The
paid roles do not: hints, the workbench check and RW2c's comparison lines
(``workbench.check.CheckRoute``), RW2c's worked-example search (the
``source_retrieval`` roles), RW5a's figure author (``figures.routes``), the
AD LLM routes, the practice-index and source-service judges each plan a
``PaidRoute`` (``practice_index.paid.plan_route``) and build it with
``resolve_client``. That path must follow the same owner decisions
(2026-10-21): every such route resolves to a plan profile by default, an
unavailable plan reports "unavailable" AND asks about OpenRouter (when it is
set up and the feature's price is set), a grant routes the task to OpenRouter
priced as metered (never as the subscription), a ready plan is always used
first, and a pinned selection or a readiness probe is never replaced. Nothing
is sent anywhere. Every task on the merged tree is enumerated
(``get_args(AITask)``), so a task a later stage adds is covered by
construction.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, get_args

import pytest
import tomlkit

from learnloop.ai import plan_fallback
from learnloop.ai.chatgpt_plan.session import PlanSession
from learnloop.ai.routing import AITask, DECIDER_TASKS, provider_for_task, ready_client_for_task
from learnloop.config.schema import CHATGPT_PLAN_PROVIDER_NAMES
from learnloop.practice_index.paid import plan_route, resolve_client
from learnloop.vault.loader import load_vault

from tests.chatgpt_plan_fakes import fake_chatgpt, sign_in
from tests.helpers import create_basic_vault
from tests.openai_fakes import install_fake_openai

TASKS: tuple[str, ...] = get_args(AITask)
#: Tasks pinned by construction (provider_for_task returns an explicit selection).
PINNED_BY_CONSTRUCTION = frozenset({"embedding", "field_question_classifier"}) | DECIDER_TASKS
#: The tasks main added after T1's base (55063be64) ride these existing tasks:
#: RW2c's comparison lines on CheckRoute (workbench_check), its example
#: search on the source-retrieval roles, RW5a's figures on figure_author.
MAIN_FEATURE_TASKS = ("workbench_check", "source_query_rewrite", "source_rerank", "figure_author")


@pytest.fixture(autouse=True)
def isolated(tmp_path, monkeypatch):
    monkeypatch.setenv("LEARNLOOP_CONFIG_DIR", str(tmp_path / "config"))
    for name in ("LEARNLOOP_AI_PROVIDER", "LEARNLOOP_AI_FALLBACK", "OPENROUTER_API_KEY", "OPENAI_API_KEY",
                 "DEEPSEEK_API_KEY"):
        monkeypatch.delenv(name, raising=False)
    plan_fallback.revoke_all()
    yield
    plan_fallback.revoke_all()


def _priced_vault(tmp_path: Path) -> Path:
    """A vault with every feature price set, so no task's offer is blocked (review F2)."""

    root = tmp_path / "vault"
    create_basic_vault(root)
    path = root / "learnloop.toml"
    document = tomlkit.parse(path.read_text(encoding="utf-8"))
    for dotted in sorted(set(plan_fallback.METERED_PRICE_SETTINGS.values())):
        table: Any = document
        *parents, leaf = dotted.split(".")
        for part in parents:
            if part not in table:
                table[part] = tomlkit.table()
            table = table[part]
        table[leaf] = 1.0
    path.write_text(tomlkit.dumps(document), encoding="utf-8")
    return root


def _routed_tasks(config) -> list[str]:
    tasks = [task for task in TASKS if not provider_for_task(config, task).explicit]  # type: ignore[arg-type]
    assert set(TASKS) - set(tasks) == PINNED_BY_CONSTRUCTION
    assert set(MAIN_FEATURE_TASKS) <= set(tasks)
    return tasks


@pytest.mark.parametrize("state", ["paused", "signed_out"])
def test_every_paid_role_resolves_to_the_plan_and_asks_before_openrouter(tmp_path, monkeypatch, state):
    fake_openai = install_fake_openai(monkeypatch)
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key-never-sent")
    with fake_chatgpt() as server:
        if state == "paused":
            session = PlanSession()
            sign_in(session, server)
            session.note_usage_limit(code="subscription_sharing_usage_limit_exceeded", request_id="req_t1_land")
        root = _priced_vault(tmp_path)
        vault = load_vault(root)
        config = vault.config
        for task in _routed_tasks(config):
            route = plan_route(vault, task)  # type: ignore[arg-type]
            # By default every paid role is on a plan profile, billed as the subscription.
            assert route.provider in CHATGPT_PLAN_PROVIDER_NAMES, task
            assert route.billing == "subscription", task
            with plan_fallback.collecting() as paid_offers:
                client, message = resolve_client(vault, route)
            with plan_fallback.collecting() as routing_offers:
                routed = ready_client_for_task(root, config, task)  # type: ignore[arg-type]
            # Unavailable through the degrade path, and asked exactly as routing asks.
            assert client is None, task
            assert paid_offers.hint() == routing_offers.hint(), task
            if routed.runtime.fallback_available == "openrouter":
                assert paid_offers.hint()["fallback_tasks"] == [task], task
                assert "Use OpenRouter instead" in (message or ""), task
        for task in MAIN_FEATURE_TASKS:
            with plan_fallback.collecting() as offers:
                resolve_client(vault, plan_route(vault, task))  # type: ignore[arg-type]
            assert offers.hint() is not None and offers.hint()["fallback_tasks"] == [task], task
        # Readiness probes ask nothing.
        with plan_fallback.quiet(), plan_fallback.collecting() as offers:
            assert resolve_client(vault, plan_route(vault, "workbench_check"))[0] is None
        assert offers.hint() is None
        # A pinned selection (LEARNLOOP_AI_PROVIDER) reports unavailable and never asks.
        monkeypatch.setenv("LEARNLOOP_AI_PROVIDER", "chatgpt")
        with plan_fallback.collecting() as offers:
            assert resolve_client(vault, plan_route(vault, "workbench_check"))[0] is None
        assert offers.hint() is None
        monkeypatch.delenv("LEARNLOOP_AI_PROVIDER")
        assert server.requests == []
    assert all(instance.requests == [] for instance in fake_openai.instances)


def test_a_grant_routes_a_paid_role_to_openrouter_priced_as_metered_and_a_ready_plan_comes_first(tmp_path,
                                                                                               monkeypatch):
    fake_openai = install_fake_openai(monkeypatch)
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key-never-sent")
    with fake_chatgpt() as server:
        root = _priced_vault(tmp_path)
        vault = load_vault(root)
        config = vault.config
        tasks = _routed_tasks(config)
        plan_fallback.remember_offer(root, {"fallback_tasks": tasks})
        plan_fallback.grant(root, tasks)
        served = 0
        for task in tasks:
            routed = ready_client_for_task(root, config, task)  # type: ignore[arg-type]
            route = plan_route(vault, task)  # type: ignore[arg-type]
            client, _message = resolve_client(vault, route)
            if routed.ready and routed.provider_name == "openrouter":
                # The route names the profile that serves, so its caps and receipts are metered.
                assert route.provider == "openrouter" and route.billing == "metered", task
                assert client is not None and client.provider_name == "openrouter", task
                served += 1
            else:
                assert client is None, task
        assert set(MAIN_FEATURE_TASKS) <= {task for task in tasks
                                           if plan_route(vault, task).provider == "openrouter"}  # type: ignore[arg-type]
        assert served >= 40
        # A readiness probe honours no grant (a grant never serves background work).
        with plan_fallback.quiet():
            assert plan_route(vault, "workbench_check").provider in CHATGPT_PLAN_PROVIDER_NAMES
        # "Stop using OpenRouter" ends a route planned under the grant before it is built.
        planned = plan_route(vault, "workbench_check")
        assert planned.provider == "openrouter"
        plan_fallback.revoke(root)
        client, message = resolve_client(vault, planned)
        assert client is None and "no longer serves it" in (message or "")
        plan_fallback.remember_offer(root, {"fallback_tasks": tasks})
        plan_fallback.grant(root, tasks)
        # A ready plan always serves first, granted or not.
        sign_in(PlanSession(), server)
        for task in MAIN_FEATURE_TASKS:
            route = plan_route(vault, task)  # type: ignore[arg-type]
            assert route.provider in CHATGPT_PLAN_PROVIDER_NAMES and route.billing == "subscription", task
            client, _message = resolve_client(vault, route)
            assert client is not None and client.provider_type == "chatgpt_plan", task
        assert server.requests == []
    assert all(instance.requests == [] for instance in fake_openai.instances)  # built, never called
