"""One output-budget policy for every LLM role (owner, 2026-10-12).

Hard-coded per-role output caps cut reasoning models off (Haiku 5.5 was
truncated on 28 of 36 T6 question-writer calls and 6 of 68 rewrites). The
policy: one generous default (``ai.output_tokens``, 16,384), a profile's own
``max_tokens``, a per-route override, all used for spend reservations; a
truncation is logged with its role and model and retried once at double the
budget, never accepted; a route may ask for a reasoning effort.
"""
from __future__ import annotations

from contextlib import closing
import importlib
import json
import logging

import pytest
from pydantic import ValidationError

from learnloop.ai.errors import AIOutputTruncated
from learnloop.ai.execution import (
    generation_limit,
    requested_reasoning_effort,
    single_request,
    truncation_retry_allowed,
)
from learnloop.ai.output_budget import (
    DEFAULT_OUTPUT_TOKENS,
    TruncationRetry,
    output_budget,
    reasoning_effort,
)
from learnloop.ai.providers.openrouter import OpenRouterProviderClient
from learnloop.ai.spend import SpendBudget, SpendCaps
from learnloop.ai.transport import execute_structured_operation
from learnloop.config import AIProviderConfig
from learnloop.config.schema import LearnLoopConfig
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.diagnosis.offline_review.spend import ReviewSpend, admitted_output_limit
from learnloop.ops.pf_calls import PFCaller, RoleClient
from learnloop.practice_index.paid import PaidCalls, PaidRoute
from learnloop.source_retrieval.contracts import QueryRewrite
from learnloop.vault.loader import load_vault
from learnloop.vault.repository import open_vault_repository
from tests.openai_fakes import FakeTruncated, install_fake_openai
from tests.practice_index_fakes import build_practice_vault, enable_practice_index

REWRITE = json.dumps({"passage": "Eigenvalues solve det(A - tI) = 0.", "keywords": ["eigenvalue"]})
CUT = FakeTruncated('{"passage": "Eigenvalues solve')
CAPS = SpendCaps(max_candidates=10, max_pairs=10, max_retries=2, max_calls=5,
                 max_total_tokens=10_000_000, max_estimated_usd=100.0)


def _config(**ai) -> LearnLoopConfig:
    return LearnLoopConfig.model_validate({"ai": ai} if ai else {})


def _router(monkeypatch, *responses, **profile):
    monkeypatch.setenv("TEST_ROUTER_KEY", "fake")
    monkeypatch.setattr("learnloop.ai.providers.openai_chat._sleep", lambda _: None)
    fake = install_fake_openai(monkeypatch, *responses)
    client = OpenRouterProviderClient("router", AIProviderConfig(
        type="openrouter", model="vendor/model", api_key_env="TEST_ROUTER_KEY", **profile))
    return fake, client


@pytest.fixture
def vault(tmp_path):
    paths = build_practice_vault(tmp_path / "vault")
    enable_practice_index(paths, embeddings=False)
    open_vault_repository(paths.root, paths.sqlite_path)
    return paths


def _receipts(paths, owner_id: str) -> list[dict]:
    with closing(connect(paths.sqlite_path, read_only=True)) as connection:
        connection.row_factory = __import__("sqlite3").Row
        return [dict(row) for row in connection.execute(
            "SELECT purpose, status, model, output_budget_tokens, budget_json, parent_call_id "
            "FROM model_call_receipts WHERE owner_id = ? ORDER BY started_at, rowid", (owner_id,))]


# -- the policy --------------------------------------------------------------------------------


def test_the_default_budget_is_generous_and_the_profile_or_route_can_replace_it():
    config = _config()
    assert DEFAULT_OUTPUT_TOKENS == 16_384
    assert output_budget(None) == 16_384 and output_budget(config, "source_query_rewrite") == 16_384
    # A profile's own max_tokens is its maximum (DeepSeek Flash's 8,192).
    assert output_budget(config, "grading", provider="deepseek_flash") == 8192
    routed = _config(output_tokens=32_000, route_output_tokens={"source_rerank": 4096})
    assert output_budget(routed, "source_rerank") == 4096
    assert output_budget(routed, "source_query_rewrite") == 32_000


def test_route_budgets_and_efforts_name_known_routes():
    with pytest.raises(ValidationError, match="unknown routes: not_a_route"):
        _config(route_output_tokens={"not_a_route": 4096})
    with pytest.raises(ValidationError, match="at least 256"):
        _config(route_output_tokens={"source_rerank": 100})
    with pytest.raises(ValidationError, match="route_reasoning_effort"):
        _config(route_reasoning_effort={"source_rerank": "turbo"})


def test_t6_rewrite_and_verification_default_to_low_effort_and_an_owner_table_merges():
    config = _config()
    assert reasoning_effort(config, "source_query_rewrite") == "low"
    assert reasoning_effort(config, "source_rerank") == "low"
    assert reasoning_effort(config, "grading") is None
    owner = _config(route_reasoning_effort={"source_rerank": "medium", "grading": "high"})
    assert reasoning_effort(owner, "source_query_rewrite") == "low"  # default kept
    assert reasoning_effort(owner, "source_rerank") == "medium"
    assert reasoning_effort(_config(route_reasoning_effort={"source_rerank": ""}), "source_rerank") is None


def test_no_retired_hard_coded_output_cap_remains():
    retired = {
        "learnloop.source_retrieval.bench": ("QUESTION_OUTPUT_TOKENS", "LABEL_OUTPUT_TOKENS"),
        "learnloop.source_retrieval.verify": ("VERIFY_OUTPUT_TOKENS",),
        "learnloop.source_retrieval.queries": ("REWRITE_OUTPUT_TOKENS",),
        "learnloop.practice_index.evaluation": ("QUERY_OUTPUT_TOKENS", "LABEL_OUTPUT_TOKENS"),
        "learnloop.practice_index.retrieval": ("RERANK_OUTPUT_TOKENS", "MIXED_RERANK_OUTPUT_TOKENS"),
        "learnloop.practice_index.dossiers": ("DOSSIER_OUTPUT_TOKENS",),
        "learnloop.ops.family_proposals": ("OUTPUT_TOKENS",),
        "learnloop.ops.contamination.judge": ("OUTPUT_TOKENS",),
        "learnloop.ops.pf_generation": ("OUTPUT_TOKENS",),
        "learnloop.ops.embedding_compare": ("VA_OUTPUT_TOKENS",),
        "learnloop.diagnosis.recurrence.backlog": ("JUDGE_OUTPUT_TOKENS",),
        "learnloop.projects.probes": ("AUTHORING_OUTPUT_TOKENS", "CLOSED_BOOK_OUTPUT_TOKENS_PER_QUESTION",
                                      "GRADING_OUTPUT_TOKENS_PER_ITEM"),
        # Canonical sources (merged after the policy): no pinned caps either.
        "learnloop.ops.pf_verify": ("PANEL_OUTPUT_TOKENS", "EQUIVALENCE_OUTPUT_TOKENS",
                                    "SPAN_SUPPORT_OUTPUT_TOKENS"),
        "learnloop.content.authoring.source_exercise_import": ("SOLUTION_MATCH_OUTPUT_TOKENS",
                                                               "AUTHORING_OUTPUT_TOKENS"),
        "learnloop.source_retrieval.find_sources": ("INTENT_OUTPUT_TOKENS",),
        "learnloop.source_retrieval.compare": ("COMPARE_OUTPUT_TOKENS",),
        "learnloop.instructional.screen": ("SCREEN_OUTPUT_TOKENS",),
    }
    for module, names in retired.items():
        loaded = importlib.import_module(module)
        assert not [name for name in names if hasattr(loaded, name)], module
    # The Slice 1 review allowances follow the policy too (an embedding generates nothing).
    assert admitted_output_limit("diagnosis_judge", None) == 16_384
    assert admitted_output_limit("embedding", None) == 0
    assert admitted_output_limit("grading", 8192) == 8192
    assert admitted_output_limit("grading", None, _config(route_output_tokens={"grading": 20_000})) == 20_000
    from learnloop.projects.probes import authoring_output_tokens, grading_output_tokens

    assert authoring_output_tokens() == grading_output_tokens(40) == 16_384


def test_the_same_cause_judge_is_no_longer_held_to_600_tokens(tmp_path):
    from learnloop.diagnosis.recurrence.backlog import command_spend
    from learnloop.diagnosis.recurrence.kind import SAME_CAUSE_ROUTE

    paths = build_practice_vault(tmp_path / "vault")
    spend = command_spend(load_vault(paths.root), CAPS, embedding=False)
    assert isinstance(spend, ReviewSpend) and spend.output_limit(SAME_CAUSE_ROUTE) == 16_384


# -- requests carry the budget and the effort ---------------------------------------------------


def test_a_route_effort_reaches_openrouter_as_reasoning_effort(monkeypatch):
    fake, client = _router(monkeypatch, REWRITE)
    with requested_reasoning_effort("low"), generation_limit(16_384):
        execute_structured_operation(client, purpose="source_query_rewrite", prompt="q", result_model=QueryRewrite)
    request = fake.instances[0].requests[0]
    assert request["extra_body"] == {"reasoning": {"effort": "low"}}
    assert request["max_tokens"] == 16_384


def test_the_route_effort_wins_over_a_profile_that_disables_thinking(monkeypatch):
    fake, client = _router(monkeypatch, REWRITE, REWRITE, thinking="disabled", reasoning_effort="high")
    execute_structured_operation(client, purpose="p", prompt="q", result_model=QueryRewrite)
    assert "extra_body" not in fake.instances[0].requests[0]  # unchanged without a route effort
    with requested_reasoning_effort("low"):
        execute_structured_operation(client, purpose="p", prompt="q", result_model=QueryRewrite)
    assert fake.instances[0].requests[1]["extra_body"] == {"reasoning": {"effort": "low"}}


# -- truncation: logged, retried once at double the budget, never accepted ----------------------


def test_an_admitting_caller_lets_the_transport_retry_a_truncation_at_double(monkeypatch, caplog):
    # Slice 1's ReviewSpend and the project probes admit each physical request
    # as it starts, so the transport may retry for them.
    fake, client = _router(monkeypatch, CUT, REWRITE)
    with caplog.at_level(logging.WARNING), generation_limit(500), truncation_retry_allowed():
        result = execute_structured_operation(client, purpose="tutor_qa", prompt="q", result_model=QueryRewrite)
    assert result.keywords == ["eigenvalue"]
    assert [request["max_tokens"] for request in fake.instances[0].requests] == [500, 1000]
    assert "LLM output truncated: role=tutor_qa provider=router model=vendor/model budget=500" in caplog.text


def test_a_second_truncation_fails_and_is_never_accepted(monkeypatch):
    fake, client = _router(monkeypatch, CUT, CUT)
    with pytest.raises(AIOutputTruncated), generation_limit(500), truncation_retry_allowed():
        execute_structured_operation(client, purpose="p", prompt="q", result_model=QueryRewrite)
    assert len(fake.instances[0].requests) == 2


def test_a_profile_maximum_is_never_exceeded_by_the_retry(monkeypatch):
    fake, client = _router(monkeypatch, CUT, REWRITE, max_tokens=800)
    with pytest.raises(AIOutputTruncated), truncation_retry_allowed():
        execute_structured_operation(client, purpose="p", prompt="q", result_model=QueryRewrite)
    assert [request["max_tokens"] for request in fake.instances[0].requests] == [800]


def test_an_owner_set_budget_is_never_exceeded_and_its_truncation_is_logged(monkeypatch, caplog):
    # [ingest.budgets] (synthesis, inventory) are exempt: the owner's budget is the limit.
    fake, client = _router(monkeypatch, CUT, REWRITE)
    with caplog.at_level(logging.WARNING), pytest.raises(AIOutputTruncated), generation_limit(3000):
        execute_structured_operation(client, purpose="source_unit_inventory", prompt="q", result_model=QueryRewrite)
    assert len(fake.instances[0].requests) == 1
    assert "role=source_unit_inventory" in caplog.text and "failing" in caplog.text


def test_inside_a_caller_budget_the_transport_leaves_the_retry_to_the_caller(monkeypatch):
    fake, client = _router(monkeypatch, CUT, REWRITE)
    with pytest.raises(AIOutputTruncated), single_request(), generation_limit(500):
        execute_structured_operation(client, purpose="p", prompt="q", result_model=QueryRewrite)
    assert len(fake.instances[0].requests) == 1


def test_paid_calls_retry_a_truncation_once_at_double_the_admitted_budget(vault, monkeypatch):
    fake, client = _router(monkeypatch, CUT, REWRITE)
    repository = Repository(vault.sqlite_path)
    route = PaidRoute("source_query_rewrite", "router", "openrouter", "vendor/model", "metered",
                      output_tokens=2000, reasoning_effort="low")
    calls = PaidCalls(route=route, budget=SpendBudget(CAPS), price_per_million=1.0, repository=repository,
                      owner_kind="test", owner_id="paid_trunc")
    result = calls.call(client, purpose="source_query_rewrite", prompt="Why eigenvalues?",
                        result_model=QueryRewrite, output_tokens=route.output_tokens, metadata={})
    assert result.passage.startswith("Eigenvalues")
    requests = fake.instances[0].requests
    assert [request["max_tokens"] for request in requests] == [2000, 4000]
    assert all(request["extra_body"] == {"reasoning": {"effort": "low"}} for request in requests)
    # Admitted and charged as a retry, at the doubled budget.
    assert calls.budget.used.calls == 2 and calls.budget.used.retries == 1
    [event] = calls.totals.truncations
    assert event["role"] == "source_query_rewrite" and event["model"] == "vendor/model"
    assert event["budget"] == 2000 and event["retry_budget"] == 4000
    roots = [row for row in _receipts(vault, "paid_trunc") if row["parent_call_id"] is None]
    assert [row["status"] for row in roots] == ["truncated", "completed"]
    assert [row["output_budget_tokens"] for row in roots] == [2000, 4000]
    note = json.loads(roots[1]["budget_json"])["truncation_retry"]
    assert note == {"role": "source_query_rewrite", "model": "vendor/model", "previous_budget": 2000,
                    "budget": 4000}


def test_paid_calls_fail_on_a_second_truncation(vault, monkeypatch):
    fake, client = _router(monkeypatch, CUT, CUT, REWRITE)
    route = PaidRoute("source_query_rewrite", "router", "openrouter", "vendor/model", "metered", output_tokens=2000)
    calls = PaidCalls(route=route, budget=SpendBudget(CAPS), price_per_million=1.0,
                      repository=Repository(vault.sqlite_path), owner_kind="test", owner_id="paid_fail")
    with pytest.raises(AIOutputTruncated):
        calls.call(client, purpose="source_query_rewrite", prompt="q", result_model=QueryRewrite,
                   output_tokens=2000, metadata={})
    assert len(fake.instances[0].requests) == 2
    assert [event["next"] for event in calls.totals.truncations] == ["retry", "fail"]


def test_the_compare_harness_uses_the_policy_budget_and_retries_a_truncation(vault, monkeypatch):
    from learnloop.ops.embedding_compare import SUITES
    from learnloop.ops.pf_calls import ROLE_TASKS
    from learnloop.source_retrieval.suites import register_suites

    register_suites(SUITES, role_tasks=ROLE_TASKS)
    fake, client = _router(monkeypatch, CUT, REWRITE)
    loaded = load_vault(vault.root)
    caller = PFCaller(loaded, Repository(vault.sqlite_path), caps=CAPS, price_per_million=1.0, run_id="pf_trunc")
    entry = RoleClient(role="source_rewrite", provider="router", model="vendor/model", profile_type="openrouter",
                       subscription=False, client=client, settings={"provider": "router", "model": "vendor/model"})
    call = caller.call(entry, prompt="Why eigenvalues?", prompt_version="v", result_model=QueryRewrite)
    assert call.result.keywords == ["eigenvalue"]
    requests = fake.instances[0].requests
    assert [request["max_tokens"] for request in requests] == [16_384, 32_768]
    assert requests[0]["extra_body"] == {"reasoning": {"effort": "low"}}  # the rewrite route's default
    report = caller.report()
    assert [(event["role"], event["model"]) for event in report["truncations"]] == [("source_rewrite", "vendor/model")]
    assert report["charged"]["metered"]["retries"] == 1


def test_a_truncation_retry_obeys_the_retry_cap():
    retry = TruncationRetry(1000, role="r", model="m")
    assert retry.after_truncation(allowed=False) is False and retry.budget == 1000
    assert retry.events[-1]["next"] == "fail"
    again = TruncationRetry(1000, role="r", model="m")
    assert again.after_truncation() is True and again.budget == 2000 and again.initial_budget == 1000
    assert again.after_truncation() is False  # once only


def test_codex_turns_take_the_routes_effort_for_that_turn_only(tmp_path, monkeypatch):
    import sys
    from enum import Enum
    from types import ModuleType, SimpleNamespace

    from learnloop.ai.providers.codex import SdkCodexClient
    from learnloop.ai.schemas import WireModel
    from learnloop.ai.transport import StructuredRequest
    from learnloop.config import CodexConfig

    efforts: list = []

    class Summary(WireModel):
        summary: str

    class FakeCodex:
        def __init__(self, config):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def close(self):
            return None

        def thread_start(self, **_kwargs):
            return SimpleNamespace(turn=lambda prompt, **kwargs: efforts.append(kwargs["effort"]) or SimpleNamespace(
                run=lambda: SimpleNamespace(final_response='{"summary": "ok"}'), interrupt=lambda: None))

    class ReasoningEffort(Enum):
        low = "low"
        medium = "medium"

    sdk = ModuleType("openai_codex")
    sdk.Codex = FakeCodex
    sdk.CodexConfig = lambda **kwargs: SimpleNamespace(**kwargs)
    types_module = ModuleType("openai_codex.types")
    types_module.Personality = SimpleNamespace(pragmatic="pragmatic")
    types_module.ReasoningEffort = ReasoningEffort
    types_module.ReasoningSummary = SimpleNamespace(model_validate=lambda value: value)
    monkeypatch.setitem(sys.modules, "openai_codex", sdk)
    monkeypatch.setitem(sys.modules, "openai_codex.types", types_module)
    client = SdkCodexClient(CodexConfig(checkout_path=str(tmp_path / "codex"), reasoning_effort="medium"), tmp_path)
    request = StructuredRequest(purpose="source_rerank", prompt="judge", result_model=Summary, reasoning_effort="low")
    assert client.complete(request).summary == "ok"
    plain = StructuredRequest(purpose="grading", prompt="grade", result_model=Summary)
    assert client.complete(plain).summary == "ok"
    assert efforts == [ReasoningEffort.low, ReasoningEffort.medium]  # the profile's effort is restored


def test_slice1_review_spend_admits_the_transports_truncation_retry_at_double(monkeypatch):
    fake, client = _router(monkeypatch, CUT, REWRITE)
    spend = ReviewSpend(CAPS, price_per_million=1.0)
    info = spend.register("diagnosis_judge", client)
    assert info.output_limit == 16_384  # was a 4,000-token allowance
    with spend.collector.observing(), spend.request("diagnosis_judge", "judge", input_tokens=200):
        result = execute_structured_operation(client, purpose="judge", prompt="q", result_model=QueryRewrite)
    assert result.keywords == ["eigenvalue"]
    assert [request["max_tokens"] for request in fake.instances[0].requests] == [16_384, 32_768]
    assert spend.budget.used.calls == 2 and spend.budget.used.retries == 1  # the retry was admitted
