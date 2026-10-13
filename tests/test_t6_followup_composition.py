"""The T6 follow-up's output-budget policy composed with main (merge 2026-10-13).

Main moved on while the follow-up was built (owner batch 2's B1 fixes, the
ChatGPT-plan provider, learner-text gaps, facet identity, `learnloop ai
latency`). Each test here failed on the plain merge and pins one composition:

* PFCaller prices a truncation retry's doubled output at the output rate
  (owner batch 2's input/output pricing x the policy's retry);
* B1's writer budget follows the policy (and ``--writer-output-tokens``), and
  its local runner never lets the transport retry a truncated answer (B1's
  no-retry rule x the policy's transport retry);
* the ChatGPT-plan route never receives an output cap field, takes the
  route's reasoning effort, and a truncation retry on it is admitted on the
  subscription;
* the learner-text-gap calls, their seed unit, the escalated repair, the
  facet identity judge and the latency probe use the policy's budget.
"""
from __future__ import annotations

from contextlib import closing
from dataclasses import dataclass, field
import json
import sqlite3
from types import SimpleNamespace

import pytest
import tomlkit

from learnloop.ai.errors import AIOutputTruncated
from learnloop.ai.execution import output_limit
from learnloop.ai.output_budget import DEFAULT_OUTPUT_TOKENS
from learnloop.ai.spend import SpendCaps
from learnloop.db.repositories import Repository
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths

from tests.helpers import create_basic_vault


def _set_ai(root, **values) -> None:
    """Set ``[ai]`` keys (tables included) in a vault's learnloop.toml."""

    path = root / "learnloop.toml"
    document = tomlkit.parse(path.read_text(encoding="utf-8"))
    for key, value in values.items():
        document["ai"][key] = value
    path.write_text(tomlkit.dumps(document), encoding="utf-8")


class _Metered:
    """A metered client stand-in (never called): what ReviewSpend registers."""

    provider_type = "openrouter"
    provider_name = "router"
    model = "vendor/model"
    profile = SimpleNamespace(max_tokens=None)


# -- PFCaller: a truncation retry's doubled output is priced at the output rate --------------------


def test_pf_caller_prices_a_truncation_retry_at_its_doubled_output_budget(tmp_path, monkeypatch):
    from learnloop.ai.providers.openrouter import OpenRouterProviderClient
    from learnloop.config import AIProviderConfig
    from learnloop.ops.pf_calls import PFCaller, RoleClient, estimate_tokens
    from learnloop.source_retrieval.contracts import QueryRewrite

    from tests.openai_fakes import FakeTruncated, install_fake_openai

    root = tmp_path / "vault"
    create_basic_vault(root)
    vault = load_vault(root)
    monkeypatch.setenv("TEST_ROUTER_KEY", "fake")
    monkeypatch.setattr("learnloop.ai.providers.openai_chat._sleep", lambda _: None)
    answer = json.dumps({"passage": "Eigenvalues solve det(A - tI) = 0.", "keywords": ["eigenvalue"]})
    install_fake_openai(monkeypatch, FakeTruncated('{"passage": "Eig'), answer)
    client = OpenRouterProviderClient("router", AIProviderConfig(
        type="openrouter", model="vendor/model", api_key_env="TEST_ROUTER_KEY"))
    caps = SpendCaps(max_candidates=10, max_pairs=10, max_retries=2, max_calls=5,
                     max_total_tokens=10_000_000, max_estimated_usd=100.0)
    caller = PFCaller(vault, Repository(VaultPaths(vault.root, vault.config).sqlite_path), caps=caps,
                      price_per_million=None, input_price_per_million=1.0, output_price_per_million=10.0,
                      run_id="priced")
    entry = RoleClient(role="source_rewrite", provider="router", model="vendor/model", profile_type="openrouter",
                       subscription=False, client=client, settings={"provider": "router", "model": "vendor/model"})
    prompt = "Why eigenvalues?"
    caller.call(entry, prompt=prompt, prompt_version="v", result_model=QueryRewrite, output_tokens=1000)
    assert [event["retry_budget"] for event in caller.truncations] == [2000]

    def reserved(budget: int) -> float:
        tokens = estimate_tokens(prompt, QueryRewrite, budget)
        return ((tokens - budget) * 1.0 + budget * 10.0) / 1_000_000

    # No usage is reported, so each attempt is charged its reservation: the
    # retry's 2,000 output tokens all at the output rate.
    assert caller.metered.used.estimated_usd == pytest.approx(reserved(1000) + reserved(2000), rel=1e-9)


# -- B1: the writer's default budget is the policy's; no transport retry on the local runner --------


def _b1_vault(tmp_path):
    from tests.test_recurrence_benchmarks import _bench_vault, _eedi

    paths, _vault, repository = _bench_vault(tmp_path)
    _eedi(tmp_path / "eedi")
    return paths, repository


def test_b1_writer_budget_follows_the_policy_and_the_flag(tmp_path):
    from tests.test_recurrence_benchmarks import B1_WRITER_ROLE, _harness

    paths, _repository = _b1_vault(tmp_path)
    vault = load_vault(paths.root)
    assert _harness(vault, tmp_path, dry_run=True)["plan"]["writer"]["output_tokens"] == DEFAULT_OUTPUT_TOKENS
    _set_ai(paths.root, route_output_tokens={"diagnosis": 4096})
    vault = load_vault(paths.root)
    planned = _harness(vault, tmp_path, dry_run=True)["plan"]
    assert planned["writer"]["output_tokens"] == 4096
    assert planned["roles"][B1_WRITER_ROLE]["output_tokens"] == 4096 * 4
    flagged = _harness(vault, tmp_path, dry_run=True, writer_output_tokens=900)["plan"]
    assert flagged["writer"]["output_tokens"] == 900


def test_b1_local_runner_never_lets_the_transport_retry_a_truncated_writer(tmp_path, monkeypatch):
    """Owner batch 2: a truncated hypothesis is one failed case, not retried.
    The policy lets a ReviewSpend unit's transport retry a truncation at double
    the budget; B1's local runner (``learnloop recurrence bench``) opts out."""

    from learnloop.diagnosis.recurrence.benchmarks import BenchRequest, run_bench

    from tests.diagnosis_fakes import FakeEmbeddingClient
    from tests.openai_fakes import install_fake_openai
    from tests.test_recurrence_benchmarks import CAPS, _completion, _hypothesis_json, _openrouter_writer

    paths, _repository = _b1_vault(tmp_path)
    vault = _openrouter_writer(paths, effort=None)
    monkeypatch.setenv("OPENROUTER_API_KEY", "offline-test-key")
    monkeypatch.setattr("learnloop.ai.providers.openai_chat._sleep", lambda _: None)
    responses = [_completion(_hypothesis_json()) for _ in range(5)]
    responses[1] = _completion('{"misconception": "an unfinished', finish_reason="length", completion_tokens=2000)
    fake = install_fake_openai(monkeypatch, *responses)
    qwen = "qwen/qwen3-embedding-8b"
    request = BenchRequest(suite="b1", output_dir=tmp_path / "out", benchmark_dir=tmp_path / "eedi",
                           models=(qwen,), dims=(16,))
    report = run_bench(vault, request=request, caps=CAPS, price_per_million=1.6,
                       embedding_clients={qwen: FakeEmbeddingClient(dims=16)})
    assert report["status"] == "complete", report
    requests = fake.instances[0].requests
    assert len(requests) == 4, "the truncated case is not retried by the transport either"
    assert all(entry["max_tokens"] == DEFAULT_OUTPUT_TOKENS for entry in requests)
    assert report["results"]["writer"]["failed_by_error"] == {"AIOutputTruncated": 1}


# -- the ChatGPT-plan route --------------------------------------------------------------------------


@pytest.fixture
def plan_server(tmp_path, monkeypatch):
    from learnloop.ai.chatgpt_plan.session import PlanSession

    from tests.chatgpt_plan_fakes import fake_chatgpt, sign_in

    monkeypatch.setenv("LEARNLOOP_CONFIG_DIR", str(tmp_path / "config"))
    monkeypatch.delenv("LEARNLOOP_AI_PROVIDER", raising=False)
    monkeypatch.setattr("learnloop.ai.providers.chatgpt_plan._sleep", lambda _seconds: None)
    with fake_chatgpt() as fake:
        sign_in(PlanSession(), fake)
        yield fake


def _plan_vault(tmp_path, server, *, routes=None, profile=None, ai=None):
    root = tmp_path / "vault"
    create_basic_vault(root)
    path = root / "learnloop.toml"
    document = tomlkit.parse(path.read_text(encoding="utf-8"))
    table = tomlkit.table()
    for key, value in {"type": "chatgpt_plan", "model": "gpt-test-fast", "base_url": server.base_url,
                       "timeout_seconds": 10, **(profile or {})}.items():
        table[key] = value
    document["ai"]["providers"]["chatgpt"] = table
    for task, name in (routes or {}).items():
        document["ai"]["routing"][task] = name
    for key, value in (ai or {}).items():
        document["ai"][key] = value
    path.write_text(tomlkit.dumps(document), encoding="utf-8")
    return root


_OUTPUT_CAP_FIELDS = {"max_output_tokens", "max_tokens", "max_completion_tokens"}
_REWRITE = '{"passage": "Conditional probability rescales by the event.", "keywords": ["conditional"]}'


def _rewrite(root, question="why does conditioning rescale probabilities?"):
    from learnloop.source_retrieval.queries import rewrite_query

    loaded = load_vault(root)
    repository = Repository(VaultPaths(loaded.root, loaded.config).sqlite_path)
    return rewrite_query(loaded, repository, question, owner_id="t")


def test_the_plan_route_gets_the_policy_budget_in_the_prompt_and_the_routes_effort(tmp_path, plan_server):
    from tests.chatgpt_plan_fakes import Reply, completed_events

    root = _plan_vault(tmp_path, plan_server, routes={"source_query_rewrite": "chatgpt"},
                       profile={"reasoning_effort": "medium"})
    plan_server.replies.append(Reply(events=completed_events(_REWRITE)))
    rewrite = _rewrite(root)
    assert rewrite.status == "rewritten", rewrite
    body = plan_server.requests[-1]["body"]
    assert not set(body) & _OUTPUT_CAP_FIELDS
    assert f"within {DEFAULT_OUTPUT_TOKENS} output tokens" in body["input"][0]["content"]
    # ai.route_reasoning_effort.source_query_rewrite defaults to low: it wins
    # over the profile's medium, as on Codex and OpenRouter.
    assert body["reasoning"] == {"effort": "low"}


def test_a_plan_truncation_is_retried_once_on_the_subscription_with_no_output_cap(tmp_path, plan_server):
    from tests.chatgpt_plan_fakes import Reply, completed_events

    root = _plan_vault(tmp_path, plan_server, routes={"source_query_rewrite": "chatgpt"})
    path = root / "learnloop.toml"
    document = tomlkit.parse(path.read_text(encoding="utf-8"))
    if "source_retrieval" not in document:
        document["source_retrieval"] = tomlkit.table()
    # A metered cap far below one reservation: the subscription is never held to it.
    document["source_retrieval"]["rewrite_max_cost_usd"] = 0.0
    path.write_text(tomlkit.dumps(document), encoding="utf-8")
    incomplete = completed_events("{")[:-1] + [{"type": "response.incomplete", "response": {
        "id": "r", "status": "incomplete", "incomplete_details": {"reason": "max_output_tokens"},
        "usage": {"input_tokens": 5, "output_tokens": 9}}}]
    plan_server.replies.extend([Reply(events=incomplete), Reply(events=completed_events(_REWRITE))])
    rewrite = _rewrite(root)
    assert rewrite.status == "rewritten", rewrite
    bodies = [request["body"] for request in plan_server.requests]
    assert len(bodies) == 2
    assert all(not set(body) & _OUTPUT_CAP_FIELDS for body in bodies)
    assert f"within {DEFAULT_OUTPUT_TOKENS} output tokens" in bodies[0]["input"][0]["content"]
    assert f"within {2 * DEFAULT_OUTPUT_TOKENS} output tokens" in bodies[1]["input"][0]["content"]
    assert rewrite.usage["billing"] == "subscription"
    assert [event["next"] for event in rewrite.usage["usage"]["truncations"]] == ["retry"]


# -- learner-text gaps --------------------------------------------------------------------------------


def _gap_vault(tmp_path, **ai):
    root = tmp_path / "vault"
    create_basic_vault(root)
    if ai:
        _set_ai(root, **ai)
    return load_vault(root)


def test_text_gap_routes_follow_the_vaults_output_budget_policy(tmp_path):
    from learnloop.diagnosis.text_gaps.judges import TextBudget

    vault = _gap_vault(tmp_path, route_output_tokens={"learner_gap_judge": 4096})
    budget = TextBudget.for_text(vault, price_per_million=1.0)
    budget.register_llm("learner_gap_judge", _Metered())
    budget.register_llm("learner_gap_reader", _Metered())
    assert budget.spend.routes["learner_gap_judge"].output_limit == 4096
    assert budget.spend.routes["learner_gap_reader"].output_limit == DEFAULT_OUTPUT_TOKENS


def test_the_seed_unit_is_admitted_at_the_policy_budget(tmp_path, monkeypatch):
    from learnloop.diagnosis.text_gaps import pipeline
    from learnloop.diagnosis.text_gaps.contract import LearnerText
    from learnloop.diagnosis.text_gaps.judges import TextBudget

    vault = _gap_vault(tmp_path, output_tokens=9000)
    budget = TextBudget.for_text(vault, price_per_million=1.0)
    seen: dict[str, int | None] = {}

    def seed(root, **_kwargs):
        seen["limit"] = output_limit()
        return "item_seed", "seeded"

    monkeypatch.setattr(pipeline.actions, "seed_from_question", seed)
    text = LearnerText(source_kind="tutor_question", source_id="q1", text="why?", context_judge="tutor",
                       created_at="2026-10-13T00:00:00Z", question_event_id="q1")
    clients = pipeline.PipelineClients(tutor=_Metered, drafter=_Metered)
    assert pipeline._seed(vault.root, text, "lo_1", budget=budget, clients=clients, clock=None) == (
        "item_seed", "seeded")
    assert seen["limit"] == 9000  # the hand-set 6,000 is retired


def test_the_gaps_command_budgets_with_the_vaults_policy(tmp_path, monkeypatch):
    from typer.testing import CliRunner

    from learnloop.cli import app

    vault = _gap_vault(tmp_path, route_output_tokens={"learner_gap_reader": 3000})
    captured = {}

    def run_pending(_root, _repository, *, owner, max_jobs, budget_factory):
        captured["budget"] = budget_factory(None)
        return []

    monkeypatch.setattr("learnloop.diagnosis.text_gaps.jobs.run_pending", run_pending)
    result = CliRunner().invoke(app, ["gaps", "run", "--vault", str(vault.root), "--json"])
    assert result.exit_code == 0, result.output
    spend = captured["budget"].spend
    spend.register("learner_gap_reader", _Metered())
    assert spend.routes["learner_gap_reader"].output_limit == 3000


def test_the_escalated_repair_budgets_with_the_vaults_policy(tmp_path):
    from learnloop.diagnosis.recurrence.escalation import per_job_spend

    vault = _gap_vault(tmp_path, route_output_tokens={"diagnosis": 5000})
    spend = per_job_spend(None, vault.config)
    spend.register("diagnosis", _Metered())
    assert spend.routes["diagnosis"].output_limit == 5000


# -- facet identity's LLM judge -------------------------------------------------------------------


@dataclass
class _BudgetedJudge:
    """Wraps the study's fake judge: records each request's output budget and
    stops for length the first ``truncate`` times."""

    inner: object
    truncate: int = 0
    budgets: list = field(default_factory=list)
    provider_name: str = "codex_luna"
    provider_type: str = "codex_sdk"
    model: str = "fake-judge-1"

    def supports(self, capability):
        return self.inner.supports(capability)

    def complete(self, request):
        self.budgets.append(request.output_budget_tokens)
        if self.truncate > 0:
            self.truncate -= 1
            raise AIOutputTruncated("fake length stop")
        return self.inner.complete(request)

    def consume_usage(self):
        return self.inner.consume_usage()


@pytest.fixture
def facet_vault(tmp_path):
    from tests.test_facet_identity import _regression_vault

    return _regression_vault(tmp_path / "vault")


def _facet_judge(root, repository, data, *, truncate=0, max_retries=2):
    from learnloop.content.facet_identity.judge import build_judge

    from tests.test_facet_identity import _study_judge

    client = _BudgetedJudge(_study_judge(data), truncate=truncate)
    judge, route = build_judge(load_vault(root), repository, owner_id="run1", client=client,
                               caps=SpendCaps(max_pairs=10_000, max_candidates=1_000, max_retries=max_retries))
    return judge, route, client


def test_the_facet_judge_asks_for_and_reserves_the_policy_budget(facet_vault):
    from learnloop.content.facet_identity.dedupe import plan_dedupe, run_dedupe

    from tests.test_facet_identity import _study_judge

    root, repository, data = facet_vault
    judge, route, client = _facet_judge(root, repository, data)
    assert route.output_tokens == DEFAULT_OUTPUT_TOKENS
    outcome = judge.run(plan_dedupe(load_vault(root))[0])[0]
    assert outcome.status == "judged"
    assert client.budgets == [DEFAULT_OUTPUT_TOKENS]  # was 1,200 + 160 per facet
    before = run_dedupe(root, dry_run=True, client=_study_judge(data))
    _set_ai(root, route_output_tokens={"facet_identity_judge": 5000})
    after = run_dedupe(root, dry_run=True, client=_study_judge(data))
    assert after["route"]["output_tokens"] == 5000
    calls = after["estimate"]["calls"]
    assert before["estimate"]["total_tokens"] - after["estimate"]["total_tokens"] == (
        DEFAULT_OUTPUT_TOKENS - 5000) * calls


def test_a_truncated_facet_judgment_is_retried_once_at_double_the_budget(facet_vault):
    from learnloop.content.facet_identity.dedupe import plan_dedupe

    root, repository, data = facet_vault
    judge, _route, client = _facet_judge(root, repository, data, truncate=1)
    outcome = judge.run(plan_dedupe(load_vault(root))[0])[0]
    assert outcome.status == "judged"
    assert client.budgets == [DEFAULT_OUTPUT_TOKENS, 2 * DEFAULT_OUTPUT_TOKENS]
    assert [event["next"] for event in judge.truncations] == ["retry"]
    assert judge.budget.used.retries == 1
    with closing(sqlite3.connect(repository.sqlite_path)) as connection:
        notes = [json.loads(row[0]).get("truncation_retry") for row in connection.execute(
            "SELECT budget_json FROM model_call_receipts WHERE owner_kind = 'facet_identity' "
            "AND parent_call_id IS NULL ORDER BY started_at, rowid")]
    assert notes[-1] == {"role": "facet_identity_judge", "model": "fake-judge-1",
                         "previous_budget": DEFAULT_OUTPUT_TOKENS, "budget": 2 * DEFAULT_OUTPUT_TOKENS}
    twice, _route, cut = _facet_judge(root, repository, data, truncate=2)
    twice.output_tokens = 4096  # another budget: no checkpoint to reuse
    failed = twice.run(plan_dedupe(load_vault(root))[0])[0]
    assert failed.status == "failed" and failed.error == "AIOutputTruncated"
    assert cut.budgets == [4096, 8192]
    assert [event["next"] for event in twice.truncations] == ["retry", "fail"]


# -- `learnloop ai latency` ------------------------------------------------------------------------


def test_the_latency_probe_asks_for_each_profiles_policy_budget(tmp_path, plan_server):
    from typer.testing import CliRunner

    from learnloop.cli import app

    from tests.chatgpt_plan_fakes import Reply, completed_events

    root = _plan_vault(tmp_path, plan_server)
    runner = CliRunner()
    dry = runner.invoke(app, ["ai", "latency", "--vault", str(root), "--provider", "chatgpt", "--dry-run", "--json"])
    assert dry.exit_code == 0, dry.output
    (entry,) = json.loads(dry.stdout)["plan"]
    assert entry["output_tokens"] == DEFAULT_OUTPUT_TOKENS  # was 64: a reasoning model was cut off
    assert entry["tokens_per_call"] == 400 + DEFAULT_OUTPUT_TOKENS
    plan_server.replies.append(Reply(events=completed_events(json.dumps({"ok": True, "n": 1}))))
    run = runner.invoke(app, ["ai", "latency", "--vault", str(root), "--provider", "chatgpt", "--runs", "1",
                              "--json"])
    assert run.exit_code == 0, run.output
    body = plan_server.requests[-1]["body"]
    assert not set(body) & _OUTPUT_CAP_FIELDS
    assert f"within {DEFAULT_OUTPUT_TOKENS} output tokens" in body["input"][0]["content"]


def test_a_truncated_latency_call_is_logged_and_failed(tmp_path, plan_server):
    from typer.testing import CliRunner

    from learnloop.cli import app

    from tests.chatgpt_plan_fakes import Reply, completed_events

    # A plan profile declares no maximum (its route takes no output cap), so
    # its budget is ai.output_tokens.
    root = _plan_vault(tmp_path, plan_server, ai={"output_tokens": 2048})
    incomplete = completed_events("{")[:-1] + [{"type": "response.incomplete", "response": {
        "id": "r", "status": "incomplete", "incomplete_details": {"reason": "max_output_tokens"},
        "usage": {"input_tokens": 5, "output_tokens": 9}}}]
    plan_server.replies.append(Reply(events=incomplete))
    run = CliRunner().invoke(app, ["ai", "latency", "--vault", str(root), "--provider", "chatgpt", "--runs", "1",
                                   "--json"])
    assert run.exit_code == 0, run.output
    (row,) = json.loads(run.stdout)["results"]
    assert row["output_tokens"] == 2048
    (call,) = row["runs"]
    assert call["ok"] is False and call["truncation"]["budget"] == 2048 and call["truncation"]["next"] == "fail"
    assert len(plan_server.requests) == 1
