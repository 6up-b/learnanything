"""AD2+AD3 composed onto plan-first transport T1 (item C4).

* AD's model routes (``ad_forecast_llm`` for the ``ad_item_forecast`` task, ``ad_feature_audit`` and
  ``ad_relatedness``) are in the plan-first route table: under code defaults each resolves to a
  ChatGPT-plan profile billed as the subscription; a Codex route is refused unless
  ``ai.agent_harness_opt_in``. ``ad_forecast_decider`` is a decider-only route (a plan profile is not a
  decider) and keeps its code-default decider profile.
* AD's model calls are background work: inside every AD operation (``plan_fallback.quiet()``), with
  the plan paused, an OpenRouter profile and key set, every price set and every AD task granted to the
  request, no route raises an offer, no grant serves one, and the paid route stays on the plan (the
  call reports unavailable; AD waits or skips). Outside an operation the same tasks would ask, which
  shows the operation is what makes them quiet.
* Each AD LLM task has its price setting in T1's table.

Fakes only: nothing is sent.
"""

from __future__ import annotations

import pytest

from learnloop.adaptive_difficulty import operation as O
from learnloop.ai import plan_fallback
from learnloop.ai.chatgpt_plan.session import PlanSession
from learnloop.ai.routing import DECIDER_TASKS, ROUTE_FOR_OPERATION, provider_for_task, ready_client_for_task
from learnloop.config.schema import CHATGPT_PLAN_PROVIDER_NAMES, DEFAULT_SERVING_TASK_ROUTES
from learnloop.db.repositories import Repository
from learnloop.practice_index.paid import plan_route, resolve_client
from learnloop.vault.loader import load_vault

from tests.chatgpt_plan_fakes import fake_chatgpt, sign_in
from tests.openai_fakes import install_fake_openai
from tests.test_plan_first_transport_paid_roles import LEARNER, _priced_vault, isolated, learner_request  # noqa: F401

AD_TASKS = ("ad_forecast_llm", "ad_feature_audit", "ad_relatedness")


def test_ads_routes_are_in_the_plan_first_table():
    assert {"ad_forecast_llm", "ad_feature_audit", "ad_relatedness"} <= set(DEFAULT_SERVING_TASK_ROUTES)
    assert all(DEFAULT_SERVING_TASK_ROUTES[task] in CHATGPT_PLAN_PROVIDER_NAMES for task in AD_TASKS)
    assert ROUTE_FOR_OPERATION["ad_item_forecast"] == "ad_forecast_llm"
    assert ROUTE_FOR_OPERATION["ad_relatedness"] == "ad_relatedness"
    assert "ad_forecast_decider" in DECIDER_TASKS
    assert all(plan_fallback.METERED_PRICE_SETTINGS.get(task) == "adaptive_difficulty.price_per_million"
               for task in AD_TASKS)


def test_under_code_defaults_each_ad_route_is_the_plan_and_codex_is_refused(tmp_path):
    root = _priced_vault(tmp_path)
    vault = load_vault(root)
    for task in AD_TASKS:
        selection = provider_for_task(vault.config, task)  # type: ignore[arg-type]
        assert selection.provider_name in CHATGPT_PLAN_PROVIDER_NAMES, task
        route = plan_route(vault, task)  # type: ignore[arg-type]
        assert route.provider in CHATGPT_PLAN_PROVIDER_NAMES and route.billing == "subscription", task
    vault.config.ai.routing.ad_relatedness = "codex"
    resolved = ready_client_for_task(root, vault.config, "ad_relatedness")  # type: ignore[arg-type]
    assert not resolved.ready and resolved.provider_name != "openrouter"


def test_inside_an_ad_operation_no_route_asks_and_no_grant_serves(tmp_path, monkeypatch):
    fake_openai = install_fake_openai(monkeypatch)
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key-never-sent")
    with fake_chatgpt() as server:
        session = PlanSession()
        sign_in(session, server)
        session.note_usage_limit(code="subscription_sharing_usage_limit_exceeded", request_id="req_ad_t1")
        root = _priced_vault(tmp_path)
        vault = load_vault(root)
        # Outside an operation (a learner's request), the paused plan asks about OpenRouter for them.
        with plan_fallback.collecting() as asked:
            for task in AD_TASKS:
                resolve_client(vault, plan_route(vault, task))  # type: ignore[arg-type]
        assert asked.hint() is not None and set(asked.hint()["fallback_tasks"]) == set(AD_TASKS)
        plan_fallback.grant_origin(root, LEARNER, list(AD_TASKS))
        assert plan_route(vault, "ad_relatedness").provider == "openrouter"  # the grant would serve it here
        from learnloop.vault.paths import VaultPaths

        repository = Repository(VaultPaths(vault.root, vault.config).sqlite_path)
        with repository.atomic(), O.ad_operation(vault, repository):
            assert plan_fallback.offers_suppressed()
            with plan_fallback.collecting() as offers:
                for task in AD_TASKS:
                    route = plan_route(vault, task)  # type: ignore[arg-type]
                    assert route.provider in CHATGPT_PLAN_PROVIDER_NAMES, task
                    assert not plan_fallback.is_granted(task, root), task
                    client, _message = resolve_client(vault, route)
                    assert client is None, task  # the plan is paused: AD waits or skips
            assert offers.hint() is None
        assert server.requests == []
    assert all(instance.requests == [] for instance in fake_openai.instances)
