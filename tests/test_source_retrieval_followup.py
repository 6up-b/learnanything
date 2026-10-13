"""Slice 2 T6 follow-up (owner, 2026-10-12): the dense_plus_bm25 pool, tutor
timing on the receipt (no deadline cancellation), low reasoning effort for the
live rewrite and verification, and the report's query types and in-bench
verification."""
from __future__ import annotations

from contextlib import closing
import json

import pytest
from typer.testing import CliRunner

from learnloop.ai.spend import SpendCaps
from learnloop.cli import app
from learnloop.db.connection import connect
from learnloop.ops.embedding_compare import SUITES, CompareRequest, run_compare
from learnloop.ops.pf_calls import ROLE_TASKS
from learnloop.source_retrieval.corpus import library_scope
from learnloop.source_retrieval.dense import clear_cache
from learnloop.source_retrieval.evaluation import (
    SYSTEMS,
    SourceRetrievalSuite,
    _logged,
    type_counts,
    verification_metrics,
)
from learnloop.source_retrieval.library import search_library
from learnloop.source_retrieval.search import dense_plus_bm25, search_spans
from learnloop.source_retrieval.suites import register_suites
from learnloop.source_retrieval.timing import tutor_timing_report
from learnloop.source_retrieval.tutor import TIMED_STEPS, TutorSpanProvider
from learnloop.tutor.tutor_qa import ask_question
from tests.helpers import append_config_toml
from tests.source_retrieval_fakes import FakeSourceLLM, HashingEmbedder, loaded
from tests.test_source_retrieval_tutor import CLOCK, QUESTION, CitingTutor, setup

CAPS = SpendCaps(max_candidates=10_000, max_pairs=10_000, max_calls=5_000, max_total_tokens=10**9,
                 max_estimated_usd=10**4)
QWEN = "qwen/qwen3-embedding-8b"


@pytest.fixture(autouse=True)
def _fresh():
    clear_cache()
    register_suites(SUITES, role_tasks=ROLE_TASKS)
    yield
    clear_cache()


def _ask(paths, repository, provider, *, question=QUESTION, session="s1", tutor=None):
    return ask_question(loaded(paths), repository, tutor or CitingTutor(), context="practice",
                        question_md=question, practice_item_id="pi_eigen_1", session_id=session,
                        source_span_provider=provider, clock=CLOCK)


def _manifest(repository, result):
    return repository.question_event(result["event_id"])["source_context"]["source_retrieval"]


# -- the pool -----------------------------------------------------------------------------------


def test_the_pool_is_the_dense_top_k_then_bm25_extras_dense_missed():
    lists = {"meaning": ["d1", "d2", "d3", "d4"], "keyword": ["d2", "k1", "k2", "k3"],
             "provenance": ["p1", "d1"], "substring": ["s1"]}
    order, roles, ranks = dense_plus_bm25(lists, dense_k=3, extras_m=2, rrf_k=60,
                                          widening=("keyword", "provenance"))
    # d2 is already dense, so the BM25 top 2 adds only k1; the linked spans add p1.
    assert order == ["d1", "d2", "d3", "k1", "p1"]
    assert roles == {"d1": "dense", "d2": "dense", "d3": "dense", "k1": "keyword", "p1": "provenance"}
    assert ranks["d2"] == {"keyword": 1, "meaning": 2} and "s1" not in ranks
    fused, _roles, _ranks = dense_plus_bm25({"meaning": ["a", "b"], "rewrite_meaning": ["b", "c"]},
                                            dense_k=2, extras_m=0, rrf_k=60)
    assert fused == ["b", "a"]  # the rewrite's dense list is fused into the dense side


def test_search_spans_builds_the_pool_and_ranks_it_dense_first(tmp_path):
    paths, repository = setup(tmp_path)
    vault = loaded(paths)
    scope = library_scope(repository)
    embedder = HashingEmbedder()
    dense = search_spans(vault, repository, "orthogonal vectors basis", scope, deep=True, rewrite=False,
                         embedder=embedder, pool="dense_plus_bm25", pool_dense=3, pool_extras=0)
    pool = search_spans(vault, repository, "orthogonal vectors basis", scope, deep=True, rewrite=False,
                        embedder=embedder, pool="dense_plus_bm25", pool_dense=3, pool_extras=2)
    assert dense.pool["mode"] == pool.pool["mode"] == "dense_plus_bm25" and pool.pool["fallback"] is None
    assert [hit.pool_role for hit in dense.hits] == ["dense"] * 3
    assert [hit.key for hit in pool.hits[:3]] == [hit.key for hit in dense.hits]
    extras = pool.hits[3:]
    assert extras and {hit.pool_role for hit in extras} == {"keyword"} and len(extras) <= 2
    assert all(hit.ranks["keyword"] <= 2 for hit in extras)
    assert pool.timings_ms["total"] >= 0 and "query_embedding" in pool.timings_ms


def test_without_a_complete_dense_index_the_pool_is_todays_hybrid(tmp_path):
    paths, repository = setup(tmp_path, embed=False)
    vault = loaded(paths)
    result = search_spans(vault, repository, "orthogonal vectors basis", library_scope(repository), deep=True,
                          rewrite=False, embedder=HashingEmbedder(), pool="dense_plus_bm25")
    assert result.pool["mode"] == "hybrid_rrf" and "dense index" in result.pool["fallback"]
    assert {hit.pool_role for hit in result.hits} == {None}


def test_the_library_deep_search_reports_its_pool(tmp_path):
    paths, repository = setup(tmp_path)
    append_config_toml(paths.root, "[source_retrieval]\npool = \"dense_plus_bm25\"\npool_keyword_extras = 2\n"
                                   "query_rewrite = false\n")
    report = search_library(loaded(paths), repository, query="orthogonal vectors basis", deep=True,
                            embedder=HashingEmbedder(), limit=6)
    pool = report["retrieval"]["pool"]
    assert pool["mode"] == "dense_plus_bm25" and pool["dense_k"] == 4 and pool["extras_m"] == 2
    assert len(report["hits"]) <= 6


def test_the_tutor_verifies_the_dense_pool_widened_by_bm25_and_linked_spans(tmp_path):
    paths, repository = setup(tmp_path)
    append_config_toml(paths.root, "[source_retrieval]\npool = \"dense_plus_bm25\"\ntutor_candidate_pool = 3\n"
                                   "pool_keyword_extras = 2\n")
    llm = FakeSourceLLM()
    provider = TutorSpanProvider(embedder=HashingEmbedder(), rewrite_client=llm, rerank_client=llm, clock=CLOCK)
    manifest = _manifest(repository, _ask(paths, repository, provider))
    assert manifest["pool"]["mode"] == "dense_plus_bm25"
    keys = manifest["candidate_keys"]
    assert 3 < len(keys) <= 3 + 2 + 2  # dense 3, then up to 2 BM25 and 2 linked-span extras
    [verified] = [context for purpose, context in llm.calls if purpose == "source_rerank"]
    assert len(verified["candidates"]) == len(keys)
    # No rewrite was asked for (tutor_query_rewrite is off): it is not timed as zero.
    assert "rewrite" not in manifest["timings_ms"] and manifest["timings_ms"]["verification"] >= 0


def test_the_hybrid_pool_option_keeps_todays_tutor_pool(tmp_path):
    paths, repository = setup(tmp_path)
    append_config_toml(paths.root, "[source_retrieval]\npool = \"hybrid_rrf\"\ntutor_candidate_pool = 3\n")
    llm = FakeSourceLLM()
    provider = TutorSpanProvider(embedder=HashingEmbedder(), rewrite_client=llm, rerank_client=llm, clock=CLOCK)
    manifest = _manifest(repository, _ask(paths, repository, provider))
    assert manifest["pool"]["mode"] == "hybrid_rrf" and len(manifest["candidate_keys"]) == 3


# -- timing: logged on the receipt, never cancelled -----------------------------------------------


def test_every_tutor_step_is_timed_and_a_slow_step_is_flagged_not_cancelled(tmp_path):
    paths, repository = setup(tmp_path)
    append_config_toml(paths.root, "[source_retrieval]\nretrieval_timeout_seconds = 0.000001\n"
                                   "tutor_query_rewrite = true\n")
    llm = FakeSourceLLM()
    provider = TutorSpanProvider(embedder=HashingEmbedder(), rewrite_client=llm, rerank_client=llm, clock=CLOCK)
    manifest = _manifest(repository, _ask(paths, repository, provider))
    assert manifest["basis"] == "retrieved_verified"  # ran to the end: nothing was cancelled
    assert manifest["deadline"] == "soft"
    assert set(manifest["timings_ms"]) == set(TIMED_STEPS)
    assert manifest["timings_ms"]["total"] >= manifest["timings_ms"]["verification"]
    assert "total" in manifest["over_soft_deadline"]
    assert [purpose for purpose, _ in llm.calls] == ["source_query_rewrite", "source_rerank"]


def test_the_live_rewrite_and_verification_ask_for_low_reasoning_effort(tmp_path):
    paths, repository = setup(tmp_path)
    append_config_toml(paths.root, "[source_retrieval]\ntutor_query_rewrite = true\n")
    llm = FakeSourceLLM()
    provider = TutorSpanProvider(embedder=HashingEmbedder(), rewrite_client=llm, rerank_client=llm, clock=CLOCK)
    _ask(paths, repository, provider)
    assert llm.efforts == [("source_query_rewrite", "low"), ("source_rerank", "low")]
    append_config_toml(paths.root, "[ai.route_reasoning_effort]\nsource_rerank = \"medium\"\n")
    again = FakeSourceLLM()
    provider = TutorSpanProvider(embedder=HashingEmbedder(), rewrite_client=again, rerank_client=again, clock=CLOCK)
    _ask(paths, repository, provider, question="Why do symmetric matrices have real eigenvalues?", session="s2")
    assert again.efforts == [("source_query_rewrite", "low"), ("source_rerank", "medium")]


def test_sources_report_gives_p50_and_p90_per_step_and_counts_truncations(tmp_path):
    paths, repository = setup(tmp_path)
    append_config_toml(paths.root, "[source_retrieval]\nretrieval_timeout_seconds = 0.000001\n")
    for index, question in enumerate((QUESTION, "Why do symmetric matrices have real eigenvalues?",
                                      "How does cofactor expansion compute a determinant?")):
        llm = FakeSourceLLM()
        _ask(paths, repository, TutorSpanProvider(embedder=HashingEmbedder(), rewrite_client=llm,
                                                  rerank_client=llm, clock=CLOCK),
             question=question, session=f"s{index}")
    with repository.connection() as connection:
        connection.execute(
            "INSERT INTO model_call_receipts(id, owner_kind, owner_id, purpose, provider, model, status, "
            "started_at) VALUES ('call_cut', 'test', 't', 'source_rerank', 'router', 'vendor/model', "
            "'truncated', '2026-10-12T12:00:00Z')")
    report = tutor_timing_report(repository, soft_deadline_seconds=0.000001)
    assert report["questions"] == 3
    total = report["steps"]["total"]
    assert total["n"] == 3 and total["p50_ms"] is not None and total["p90_ms"] >= total["p50_ms"]
    assert report["over_soft_deadline"]["total"] == 3
    assert report["truncated_answers"] == [{"purpose": "source_rerank", "model": "vendor/model", "truncated": 1}]
    result = CliRunner().invoke(app, ["sources", "report", "--vault", str(paths.root), "--json"])
    assert result.exit_code == 0, result.output
    cli = json.loads(result.stdout)
    assert cli["questions"] == 3 and cli["cancels_at_deadline"] is False
    text = CliRunner().invoke(app, ["sources", "report", "--vault", str(paths.root)])
    assert "p50 ms" in text.stdout and "exceeded the" in text.stdout and "source_rerank vendor/model: 1" in text.stdout


# -- the report: query types, logged questions, verification in the bench -------------------------


def test_generated_questions_split_evenly_across_the_four_types():
    assert type_counts(10) == {"conceptual": 3, "keyword": 3, "compositional": 2, "procedural": 2}
    assert type_counts(0) == {"conceptual": 0, "keyword": 0, "compositional": 0, "procedural": 0}


def test_every_logged_learner_question_is_included(tmp_path):
    paths, repository = setup(tmp_path, embed=False)
    for index in range(12):
        _ask(paths, repository, None, question=f"Why does question number {index} matter here?",
             session=f"s{index}")
    assert len(_logged(repository, library_scope(repository))) == 12
    request = CompareRequest(suite="source_retrieval", output_dir=tmp_path / "out", max_cases=8, dry_run=True)
    data = SourceRetrievalSuite().load(loaded(paths), request)
    assert len(data.logged) == 12 and data.manifest["query_types"]["logged"] == 12


def test_verification_metrics_score_the_picks_against_the_whole_pool():
    labels = {"a": ["answers", "answers"], "b": ["unrelated", "unrelated"], "c": ["related", "answers"],
              "d": ["unrelated", "related"]}
    metrics = verification_metrics(["b", "a", "c", "d"], ["a", "c"], 2, labels)
    assert metrics["pick_precision"] == 1.0 and metrics["top_precision"] == 0.5
    assert metrics["ndcg@picks"] == 1.0 and metrics["relevant_in_pool"] == 2
    assert verification_metrics(["a", "x"], [], 2, labels) is None  # an unlabelled pool member
    empty = verification_metrics(["a", "b"], [], 2, labels)
    assert empty["empty_with_relevant"] and empty["pick_precision"] is None


def test_the_report_runs_the_production_verification_by_query_type(tmp_path):
    paths, repository = setup(tmp_path)
    llm = FakeSourceLLM()
    clients = {"source_question_writer": llm, "source_relevance": llm, "source_rewrite": llm, "source_verify": llm}
    request = CompareRequest(suite="source_retrieval", output_dir=tmp_path / "out", max_cases=8)
    dry = run_compare(loaded(paths), request=CompareRequest(**{**request.__dict__, "dry_run": True}), caps=CAPS,
                      price_per_million=1.0, clients=clients, embedding_clients={QWEN: HashingEmbedder()})
    plan = dry["plan"]
    assert plan["roles"]["source_verify"]["calls"] == plan["questions"] * 3
    assert set(plan["output_tokens"].values()) == {16_384}  # the policy budget, every role
    assert llm.calls == []
    report = run_compare(loaded(paths), request=request, caps=CAPS, price_per_million=1.0, clients=clients,
                         embedding_clients={QWEN: HashingEmbedder()})
    assert report["status"] == "complete", report.get("reason")
    results = report["results"]
    assert results["systems"] == list(SYSTEMS)
    verification = results["verification"]
    assert set(verification["systems"]) == {"hybrid_verify", "pool_verify", "dense_verify"}
    assert all(set(statuses) <= {"verified", "cached"} for statuses in verification["statuses"].values())
    assert verification["systems"]["pool_verify"]["questions"] == results["scored_questions"]
    assert set(verification["pool_modes"]["pool_verify"]) == {"dense_plus_bm25"}
    assert {"pool_verify - hybrid_verify", "pool_verify - dense_verify"} <= set(verification["differences"])
    assert set(results["by_type"]) >= {"conceptual", "keyword", "procedural"}
    for entry in results["by_type"].values():
        assert set(entry["means"]) == set(SYSTEMS) and "pool_verify" in entry["verification"]
    # Verification ran the production step: the live route's purpose, at its effort.
    assert ("source_rerank", "low") in llm.efforts
    assert report["usage"]["calls_by_role"]["source_verify"] >= 1
    markdown = (tmp_path / "out" / report["report_files"][1]).read_text(encoding="utf-8")
    assert "Verification (production verify_spans" in markdown and "By query type" in markdown
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        verdicts = connection.execute(
            "SELECT COUNT(*) FROM judgment_ledger WHERE task = 'source_relevance' AND id LIKE 'ssv_%'").fetchone()[0]
    assert verdicts > 0
    # A rerun pays for nothing: questions, rewrites, labels and verdicts are reused.
    calls = len(llm.calls)
    again = run_compare(loaded(paths), request=request, caps=CAPS, price_per_million=1.0, clients=clients,
                        embedding_clients={QWEN: HashingEmbedder()})
    assert again["status"] == "complete" and len(llm.calls) == calls


def test_the_label_pool_bound_counts_what_each_verification_pool_can_add():
    class Config:
        tutor_candidate_pool = 12
        pool_keyword_extras = 4

    # The tutor's own pools (review F5): the teaching scope, so no overlap with
    # the library's display lists is assumed; pool_verify widens the dense top
    # 12 by up to 4 BM25 and 4 linked-span extras, and holds dense_verify's pool.
    assert SourceRetrievalSuite.label_pool_bound(SYSTEMS, Config) == 60 + (12 + 4 + 4) + 12
    assert SourceRetrievalSuite.label_pool_bound(("pool_verify",), Config) == 12 + 4 + 4
    assert SourceRetrievalSuite.label_pool_bound(("dense_verify",), Config) == 12
    assert [SourceRetrievalSuite.verify_pool_bound(system, Config)
            for system in ("hybrid_verify", "pool_verify", "dense_verify")] == [12, 20, 12]
