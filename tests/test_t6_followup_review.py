"""T6 follow-up Codex review (2026-10-13): regressions for F1-F6.

F1 a transport-owned truncation retry is reserved at its doubled allowance;
F2 every verification attempt in the report passes the harness's shared caps,
and only after the cache was checked; F3 the dry run plans every candidate and
pair the run charges; F4 a failed verification is never scored as a ranking or
a verdict; F5 the report verifies the pool the tutor would verify; F6 a caller
retry never "doubles" past the transport's ceiling.
"""
from __future__ import annotations

from contextlib import closing
import json
from types import SimpleNamespace

import pytest

from learnloop.ai.errors import AIOutputTruncated
from learnloop.ai.output_budget import TruncationRetry, output_budget
from learnloop.ai.providers.openrouter import OpenRouterProviderClient
from learnloop.ai.spend import SpendBudget, SpendCaps, SpendEstimate, SpendLimitExceeded
from learnloop.ai.transport import execute_structured_operation
from learnloop.config import AIProviderConfig
from learnloop.config.schema import LearnLoopConfig
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.diagnosis.offline_review.spend import ReviewSpend, admitted_output_limit
from learnloop.ops.embedding_compare import SUITES, CompareRequest, run_compare
from learnloop.ops.pf_calls import ROLE_TASKS, PFCaller, RoleClient
from learnloop.practice_index.paid import PaidCalls, PaidRoute
from learnloop.source_retrieval.contracts import QueryRewrite
from learnloop.source_retrieval.corpus import library_scope
from learnloop.source_retrieval.dense import clear_cache
from learnloop.source_retrieval.evaluation import VERIFY_SYSTEMS, SourceRetrievalSuite
from learnloop.source_retrieval.search import search_spans
from learnloop.source_retrieval.suites import register_suites
from learnloop.source_retrieval.tutor import TutorSpanProvider
from learnloop.vault.repository import open_vault_repository
from tests.openai_fakes import FakeTruncated, install_fake_openai
from tests.practice_index_fakes import build_practice_vault, enable_practice_index
from tests.source_retrieval_fakes import EXAM_QUESTION, FakeSourceLLM, HashingEmbedder, loaded
from tests.test_source_retrieval_tutor import CLOCK, QUESTION, CitingTutor, ask, setup

REWRITE = json.dumps({"passage": "Eigenvalues solve det(A - tI) = 0.", "keywords": ["eigenvalue"]})
CUT = FakeTruncated('{"passage": "Eigenvalues solve')
QWEN = "qwen/qwen3-embedding-8b"
ROOMY = SpendCaps(max_candidates=10_000, max_pairs=10_000, max_retries=2, max_calls=5_000,
                  max_total_tokens=10**9, max_estimated_usd=10**4)


def _caps(**overrides) -> SpendCaps:
    values = dict(max_candidates=10, max_pairs=10, max_retries=2, max_calls=5,
                  max_total_tokens=10_000_000, max_estimated_usd=100.0)
    values.update(overrides)
    return SpendCaps(**values)


def _router(monkeypatch, *responses, **profile):
    monkeypatch.setenv("TEST_ROUTER_KEY", "fake")
    monkeypatch.setattr("learnloop.ai.providers.openai_chat._sleep", lambda _: None)
    fake = install_fake_openai(monkeypatch, *responses)
    client = OpenRouterProviderClient("router", AIProviderConfig(
        type="openrouter", model="vendor/model", api_key_env="TEST_ROUTER_KEY", **profile))
    return fake, client


def _wire(fake) -> list[int]:
    return [request["max_tokens"] for request in fake.instances[0].requests]


@pytest.fixture
def practice_vault(tmp_path):
    paths = build_practice_vault(tmp_path / "vault")
    enable_practice_index(paths, embeddings=False)
    open_vault_repository(paths.root, paths.sqlite_path)
    return paths


@pytest.fixture(autouse=True)
def _fresh():
    clear_cache()
    register_suites(SUITES, role_tasks=ROLE_TASKS)
    yield
    clear_cache()


# -- F1: a transport retry is reserved at the allowance it is sent with ----------------------------


@pytest.mark.parametrize(("cap", "admitted"), [(49_552, True), (49_551, False)])
def test_review_spend_reserves_the_transport_retry_at_its_doubled_allowance(monkeypatch, cap, admitted):
    # 200 input + 16,384 for the first request; 200 + 32,768 for its doubled retry.
    fake, client = _router(monkeypatch, CUT, REWRITE)
    spend = ReviewSpend(_caps(max_total_tokens=cap), price_per_million=1.0)
    spend.register("diagnosis_judge", client)
    if admitted:
        with spend.collector.observing(), spend.request("diagnosis_judge", "judge", input_tokens=200):
            execute_structured_operation(client, purpose="judge", prompt="q", result_model=QueryRewrite)
        assert _wire(fake) == [16_384, 32_768]
    else:
        with pytest.raises(SpendLimitExceeded), spend.collector.observing(), \
                spend.request("diagnosis_judge", "judge", input_tokens=200):
            execute_structured_operation(client, purpose="judge", prompt="q", result_model=QueryRewrite)
        assert _wire(fake) == [16_384]  # the doubled retry was refused before it was sent


@pytest.mark.parametrize(("slack", "admitted"), [(0, True), (-1, False)])
def test_project_calls_reserve_the_transport_retry_at_its_doubled_allowance(tmp_path, monkeypatch, slack, admitted):
    from learnloop.projects.ai_runtime import PaidCalls as ProjectCalls
    from learnloop.projects.ai_runtime import ProjectRoute
    from learnloop.projects.capture import estimate_tokens
    from learnloop.projects.experiment_store import ProjectStore

    fake, client = _router(monkeypatch, CUT, REWRITE)
    prompt = "Grade these probe answers."
    cap = (estimate_tokens(prompt) + 16_384) + (estimate_tokens(prompt) + 32_768) + slack
    calls = ProjectCalls(ProjectStore.for_vault(tmp_path), caps=_caps(max_total_tokens=cap), run_id="r",
                         price_per_million=1.0)
    route = ProjectRoute(role="grading", task="grading", provider_name="router", provider_type="openrouter",
                         model="vendor/model", subscription=False, ready=True, message=None, client=client)
    if admitted:
        calls.call(route, purpose="project_probe_grading", prompt=prompt, result_model=QueryRewrite,
                   output_tokens=16_384)
        assert _wire(fake) == [16_384, 32_768]
    else:
        with pytest.raises(SpendLimitExceeded):
            calls.call(route, purpose="project_probe_grading", prompt=prompt, result_model=QueryRewrite,
                       output_tokens=16_384)
        assert _wire(fake) == [16_384]


# -- F6: a caller-owned retry never re-sends the same ceiling ----------------------------------------


def test_a_route_override_cannot_exceed_the_profile_maximum():
    config = LearnLoopConfig.model_validate({"ai": {"route_output_tokens": {"grading": 32_000}}})
    # DeepSeek Flash declares max_tokens = 8,192: the transport would clamp to it.
    assert output_budget(config, "grading", provider="deepseek_flash") == 8192
    assert admitted_output_limit("grading", 8192, config) == 8192
    assert output_budget(config, "grading") == 32_000  # no profile maximum: the override stands


def test_a_truncation_retry_stops_at_the_transport_ceiling():
    at = TruncationRetry(8192, role="r", model="m", ceiling=8192)
    assert at.after_truncation() is False and at.budget == 8192
    assert at.events[-1]["next"] == "fail" and at.events[-1]["retry_budget"] is None
    below = TruncationRetry(8000, role="r", model="m", ceiling=12_000)
    assert below.after_truncation() is True
    assert below.budget == 12_000 and below.initial_budget == 8000
    assert below.events[-1]["retry_budget"] == 12_000


def test_paid_calls_fail_a_truncation_at_the_profile_maximum_without_another_request(practice_vault, monkeypatch):
    fake, client = _router(monkeypatch, CUT, REWRITE, max_tokens=8192)
    route = PaidRoute("source_query_rewrite", "router", "openrouter", "vendor/model", "metered", output_tokens=8192)
    calls = PaidCalls(route=route, budget=SpendBudget(_caps()), price_per_million=1.0,
                      repository=Repository(practice_vault.sqlite_path), owner_kind="test", owner_id="ceiling")
    with pytest.raises(AIOutputTruncated):
        calls.call(client, purpose="source_query_rewrite", prompt="q", result_model=QueryRewrite,
                   output_tokens=8192, metadata={})
    assert _wire(fake) == [8192]
    assert [event["next"] for event in calls.totals.truncations] == ["fail"]
    assert calls.budget.used.calls == 1


def test_paid_calls_reserve_and_record_the_real_increased_limit(practice_vault, monkeypatch):
    fake, client = _router(monkeypatch, CUT, REWRITE, max_tokens=12_000)
    route = PaidRoute("source_query_rewrite", "router", "openrouter", "vendor/model", "metered", output_tokens=8000)
    calls = PaidCalls(route=route, budget=SpendBudget(_caps()), price_per_million=1.0,
                      repository=Repository(practice_vault.sqlite_path), owner_kind="test", owner_id="raised")
    result = calls.call(client, purpose="source_query_rewrite", prompt="q", result_model=QueryRewrite,
                        output_tokens=8000, metadata={})
    assert result.keywords == ["eigenvalue"]
    assert _wire(fake) == [8000, 12_000]
    [event] = calls.totals.truncations
    assert event["budget"] == 8000 and event["retry_budget"] == 12_000
    with closing(connect(practice_vault.sqlite_path, read_only=True)) as connection:
        roots = connection.execute(
            "SELECT output_budget_tokens, budget_json FROM model_call_receipts WHERE owner_id = 'raised' "
            "AND parent_call_id IS NULL ORDER BY started_at, rowid").fetchall()
    assert [row[0] for row in roots] == [8000, 12_000]
    note = json.loads(roots[1][1])["truncation_retry"]
    assert note["previous_budget"] == 8000 and note["budget"] == 12_000
    # The answer is recoverable from its receipt under the same request identity.
    again = PaidCalls(route=route, budget=SpendBudget(_caps()), price_per_million=1.0,
                      repository=Repository(practice_vault.sqlite_path), owner_kind="test", owner_id="raised2")
    with closing(connect(practice_vault.sqlite_path)) as connection:
        connection.execute("DELETE FROM model_work_checkpoints")
        connection.commit()
    assert again.call(client, purpose="source_query_rewrite", prompt="q", result_model=QueryRewrite,
                      output_tokens=8000, metadata={}).keywords == ["eigenvalue"]
    assert len(fake.instances[0].requests) == 2


def test_the_compare_harness_never_resends_a_profile_maximum(practice_vault, monkeypatch):
    fake, client = _router(monkeypatch, CUT, REWRITE, max_tokens=8192)
    caller = PFCaller(loaded(practice_vault), Repository(practice_vault.sqlite_path), caps=_caps(),
                      price_per_million=1.0, run_id="pf_ceiling")
    entry = RoleClient(role="source_rewrite", provider="router", model="vendor/model", profile_type="openrouter",
                       subscription=False, client=client, settings={"provider": "router", "model": "vendor/model"})
    with pytest.raises(AIOutputTruncated):
        caller.call(entry, prompt="Why eigenvalues?", prompt_version="v", result_model=QueryRewrite)
    assert _wire(fake) == [8192]  # never [8192, 8192]
    assert [event["next"] for event in caller.truncations] == ["fail"]


# -- F2: verification attempts pass the shared caps, after the cache -------------------------------


def _charged_caller(paths, *, calls: int, metered: int, subscription: int) -> PFCaller:
    caps = SpendCaps(max_candidates=10_000, max_pairs=10_000, max_retries=5, max_calls=calls,
                     max_total_tokens=10**9, max_estimated_usd=10**4)
    caller = PFCaller(loaded(paths), Repository(paths.sqlite_path), caps=caps, price_per_million=1.0,
                      run_id="shared_caps")
    for budget, count in ((caller.metered, metered), (caller.subscription, subscription)):
        for _ in range(count):
            with budget.request(SpendEstimate(calls=1, total_tokens=10, estimated_usd=0.0)) as charge:
                charge.reconcile(total_tokens=10, estimated_usd=0.0)
    return caller


def _verify_ctx(caller: PFCaller, llm: FakeSourceLLM) -> SimpleNamespace:
    entry = RoleClient(role="source_verify", provider=llm.provider_name, model=llm.model,
                       profile_type=llm.provider_type, subscription=llm.provider_type == "codex_sdk",
                       client=llm, settings={})
    return SimpleNamespace(caller=caller, role=lambda _role: [entry])


def test_every_verification_attempt_is_admitted_under_the_shared_caps(tmp_path):
    paths, repository = setup(tmp_path)
    vault = loaded(paths)
    hits = search_spans(vault, repository, QUESTION, library_scope(repository), deep=False, limit=6).hits
    assert hits
    # Three metered calls and one subscription call already charged; max_calls 5.
    caller = _charged_caller(paths, calls=5, metered=3, subscription=1)
    llm = FakeSourceLLM(provider_type="openrouter", fail=True)
    try:
        SourceRetrievalSuite()._verify(_verify_ctx(caller, llm), vault, QUESTION, hits)
    except SpendLimitExceeded:
        pass
    assert sum(1 for purpose, _ in llm.calls if purpose == "source_rerank") == 1  # the retry was refused
    assert caller._shared_used("calls") <= 5


def test_a_cached_verification_is_served_even_when_the_caps_are_spent(tmp_path):
    paths, repository = setup(tmp_path)
    vault = loaded(paths)
    hits = search_spans(vault, repository, QUESTION, library_scope(repository), deep=False, limit=6).hits
    llm = FakeSourceLLM(provider_type="openrouter")
    first, _ = SourceRetrievalSuite()._verify(_verify_ctx(_charged_caller(paths, calls=10, metered=0,
                                                                          subscription=0), llm),
                                              vault, QUESTION, hits)
    assert first.status == "verified"
    spent = _charged_caller(paths, calls=4, metered=2, subscription=2)
    again, _ = SourceRetrievalSuite()._verify(_verify_ctx(spent, llm), vault, QUESTION, hits)
    assert again.status == "cached"


# -- F3: the dry run plans every candidate and pair the run charges ---------------------------------


def _clients(llm, verifier=None):
    return {"source_question_writer": llm, "source_relevance": llm, "source_rewrite": llm,
            "source_verify": verifier or llm}


def test_insufficient_candidate_caps_fail_at_the_dry_run(tmp_path):
    paths, _repository = setup(tmp_path)
    llm = FakeSourceLLM()
    request = CompareRequest(suite="source_retrieval", output_dir=tmp_path / "out", max_cases=8, dry_run=True)
    roomy = run_compare(loaded(paths), request=request, caps=ROOMY, price_per_million=1.0,
                        clients=_clients(llm), embedding_clients={QWEN: HashingEmbedder()})
    assert roomy["status"] == "dry_run"
    planned = roomy["estimate"]
    candidates = planned["metered"]["candidates"] + planned["subscription"]["candidates"]
    pairs = planned["metered"]["pairs"] + planned["subscription"]["pairs"]
    verify = roomy["plan"]["roles"]["source_verify"]
    assert verify["candidates"] > 0 and verify["pairs"] == verify["candidates"]
    assert candidates >= verify["candidates"] + roomy["plan"]["roles"]["source_question_writer"]["candidates"]
    tight = SpendCaps(max_candidates=candidates - 1, max_pairs=10_000, max_retries=2, max_calls=5_000,
                      max_total_tokens=10**9, max_estimated_usd=10**4)
    refused = run_compare(loaded(paths), request=request, caps=tight, price_per_million=1.0,
                          clients=_clients(llm), embedding_clients={QWEN: HashingEmbedder()})
    assert refused["status"] == "over_budget" and "candidates" in refused["reason"]
    assert llm.calls == []
    # The plan bounds the run: caps set to exactly the plan admit every charge.
    exact = SpendCaps(max_candidates=candidates, max_pairs=pairs, max_retries=2, max_calls=5_000,
                      max_total_tokens=10**9, max_estimated_usd=10**4)
    report = run_compare(loaded(paths), request=CompareRequest(**{**request.__dict__, "dry_run": False}),
                         caps=exact, price_per_million=1.0, clients=_clients(llm),
                         embedding_clients={QWEN: HashingEmbedder()})
    assert report["status"] == "complete", report.get("reason")


# -- F4: a failed verification is not a ranking and blocks its verdicts -----------------------------


def test_a_failed_verification_is_never_scored_and_blocks_its_verdicts(tmp_path):
    paths, _repository = setup(tmp_path)
    llm = FakeSourceLLM()
    report = run_compare(loaded(paths), request=CompareRequest(suite="source_retrieval", output_dir=tmp_path / "out",
                                                               max_cases=8),
                         caps=ROOMY, price_per_million=1.0, clients=_clients(llm, FakeSourceLLM(fail=True)),
                         embedding_clients={QWEN: HashingEmbedder()})
    assert report["status"] == "complete", report.get("reason")
    results = report["results"]
    coverage = results["verification"]["coverage"]
    for system in VERIFY_SYSTEMS:
        assert coverage[system]["verified"] == 0 and coverage[system]["questions"] > 0
        assert coverage[system]["share"] == 0.0
        assert results["summary"]["means"][system]["ndcg@10"] is None
    for name in ("hybrid_verify - hybrid", "pool_verify - hybrid_verify", "dense_verify - hybrid_verify"):
        assert results["verdicts"][name] is False
        assert "verification" in results["verdict_blocks"][name]
    assert "hybrid - meaning" not in results["verdict_blocks"]


# -- F5: the report verifies the pool the tutor would verify ------------------------------------------


def test_the_report_verifies_the_tutors_own_pool_with_its_item_in_context(tmp_path):
    paths, repository = setup(tmp_path)
    live = FakeSourceLLM()
    provider = TutorSpanProvider(embedder=HashingEmbedder(), rewrite_client=live, rerank_client=live, clock=CLOCK)
    ask(paths, repository, CitingTutor(), span_provider=provider)  # a logged practice question (pi_eigen_1)
    [production] = [context for purpose, context in live.calls if purpose == "source_rerank"]
    assert production.get("practice_question")
    bench = FakeSourceLLM(model="bench-model")  # another model: never served from the live verdicts
    report = run_compare(loaded(paths), request=CompareRequest(suite="source_retrieval", output_dir=tmp_path / "out",
                                                               max_cases=6, views=("pool_verify", "hybrid_verify")),
                         caps=ROOMY, price_per_million=1.0, clients=_clients(bench),
                         embedding_clients={QWEN: HashingEmbedder()})
    assert report["status"] == "complete", report.get("reason")
    verified = [context for purpose, context in bench.calls if purpose == "source_rerank"]
    logged = [context for context in verified if context["question"] == production["question"]]
    assert logged, "the logged practice question was verified in the bench"
    # pool_verify is the default pool (dense_plus_bm25): the tutor's very candidates and context.
    assert any([c["passage"] for c in context["candidates"]] == [c["passage"] for c in production["candidates"]]
               and context.get("practice_question") == production["practice_question"] for context in logged)
    # The tutor never verifies an assessment passage, so the bench never does either.
    assert all(EXAM_QUESTION not in candidate["passage"] for context in verified
               for candidate in context["candidates"])
