"""The retrieval evaluation: metrics, the bar, and an end-to-end run with fakes."""
from __future__ import annotations

import json

import pytest

from learnloop.ai.spend import SpendCaps
from learnloop.db.repositories import Repository
from learnloop.practice_index.evaluation import (
    MIN_SCORED_QUERIES,
    agreement,
    decide,
    paired_bootstrap,
    query_metrics,
    run_retrieval_evaluation,
)
from learnloop.practice_index.retrieval import find_practice
from learnloop.vault.loader import load_vault
from learnloop.vault.repository import open_vault_repository
from tests.practice_index_fakes import (
    FakePracticeLLM,
    HashingEmbedder,
    build_practice_vault,
    enable_practice_index,
)
from tests.test_practice_index_find import _index

CAPS = SpendCaps(max_candidates=500, max_pairs=4000, max_calls=400, max_retries=4,
                 max_total_tokens=10_000_000, max_estimated_usd=1.0)


class Forbidden:
    provider_name = "forbidden"
    provider_type = "codex_sdk"
    model = "forbidden"

    def supports(self, capability):
        return True

    def complete(self, request):
        raise AssertionError("a dry run must not call a model")

    def embed(self, inputs, task_prefix):
        raise AssertionError("a dry run must not embed")


def test_query_metrics_ndcg_and_recall():
    gains = {"a": 2.0, "b": 1.0, "c": 0.0}
    perfect = query_metrics(["a", "b", "c"], gains, {"a", "b"})
    assert perfect == {"ndcg@10": 1.0, "recall@10": 1.0}
    worse = query_metrics(["c", "b"], gains, {"a", "b"})
    assert 0 < worse["ndcg@10"] < 1 and worse["recall@10"] == 0.5
    assert query_metrics(["c"], {"c": 0.0}, set()) == {"ndcg@10": None, "recall@10": None}


def test_label_agreement_reports_exact_and_kappa():
    pairs = [("relevant", "relevant"), ("partial", "relevant"), ("not_relevant", "not_relevant"),
             ("partial", "partial")]
    report = agreement(pairs)
    assert report["pairs"] == 4 and report["exact"] == 0.75
    assert 0 < report["cohen_kappa"] < 1
    assert report["binary_exact"] == 1.0 and report["binary_cohen_kappa"] == 1.0
    assert agreement([])["cohen_kappa"] is None


def test_paired_bootstrap_is_seeded():
    first = paired_bootstrap([0.1, 0.2, 0.3, 0.0], samples=200, seed=3)
    assert first == paired_bootstrap([0.1, 0.2, 0.3, 0.0], samples=200, seed=3)
    assert first["ci95"][0] <= first["mean"] <= first["ci95"][1]
    assert paired_bootstrap([], samples=10, seed=0)["mean"] is None


def test_the_bar():
    few = {"n": MIN_SCORED_QUERIES - 1, "mean": 0.5, "ci95": [0.4, 0.6]}
    assert decide(few, {"mean": 0.1})[0] == "direct"
    win = {"n": MIN_SCORED_QUERIES, "mean": 0.2, "ci95": [0.05, 0.3]}
    assert decide(win, {"mean": 0.0})[0] == "dossier"
    assert decide(win, {"mean": -0.01})[0] == "direct"
    unclear = {"n": 40, "mean": 0.1, "ci95": [-0.01, 0.2]}
    winner, reason = decide(unclear, {"mean": 0.1})
    assert winner == "direct" and "did not beat" in reason


@pytest.fixture
def indexed(tmp_path):
    paths = build_practice_vault(tmp_path / "vault")
    enable_practice_index(paths)
    open_vault_repository(paths.root, paths.sqlite_path)
    return (paths, *_index(paths))


def _table(paths, table):
    with Repository(paths.sqlite_path).connection() as connection:
        return [dict(row) for row in connection.execute(f"SELECT * FROM {table}")]


def test_dry_run_estimates_without_clients_or_writes(indexed):
    paths, vault, _repository, _llm, _embedder = indexed
    before = paths.sqlite_path.read_bytes()
    report = run_retrieval_evaluation(vault, caps=CAPS, dry_run=True, queries=12,
                                      query_client=Forbidden(), judge_client=Forbidden(),
                                      embedder=HashingEmbedder())
    assert report["status"] == "dry_run", report
    assert report["query_set"] == {"existing": 0, "new_generated": 12, "new_logged": 0, "total": 12}
    assert report["estimate"]["relevance_labels"]["calls"] == 24
    assert report["estimate"]["query_writer"]["cost_basis"] == "estimated_only"
    assert report["estimate"]["query_embedding"]["pending"] == 12
    assert paths.sqlite_path.read_bytes() == before


def test_end_to_end_with_fakes_persists_a_decision_and_reruns_free(indexed, tmp_path):
    paths, vault, repository, llm, embedder = indexed
    logged = find_practice(vault, repository, "practise determinants please",
                           embedder=embedder, rerank_client=llm)
    assert logged["status"] == "ok"
    out = tmp_path / "reports"
    report = run_retrieval_evaluation(vault, caps=CAPS, queries=12, query_client=llm,
                                      judge_client=llm, embedder=embedder, output_dir=out)
    assert report["status"] == "complete", report
    assert report["query_set"]["total"] == 13  # 12 written + 1 logged request
    metrics = report["metrics"]
    assert metrics["scored_queries"] == 13 and metrics["incomplete_queries"] == 0
    assert metrics["label_agreement"]["pairs"] > 0
    assert set(metrics["by_seed_kind"]) == {"facet", "item", "logged"}
    assert metrics["label_models"] == {"fake-practice-model": 2 * metrics["label_agreement"]["pairs"]}
    assert report["decision"]["persisted"] is True
    winner = report["decision"]["winner"]
    evaluations = _table(paths, "practice_index_evaluations")
    assert [row["winner"] for row in evaluations] == [winner]
    labels = [row for row in _table(paths, "judgment_ledger")
              if row["prompt_version"].startswith("practice_relevance_label")]
    assert {row["prompt_version"] for row in labels} == {
        "practice_relevance_label.v1.pass1", "practice_relevance_label.v1.pass2",
    }
    assert len(labels) == 2 * metrics["label_agreement"]["pairs"]
    # Aggregate only: no query text, item text or answers in the written report.
    written = (out / f"practice-index-eval-{report['run_id']}.json").read_text()
    for row in _table(paths, "practice_eval_queries"):
        assert row["query_text"] not in written
    for item in vault.practice_items.values():
        assert item.prompt not in written
    assert "ANSWER-" not in written
    # find_practice now follows the evaluation on this index.
    follow = find_practice(vault, repository, "span of vectors", embedder=embedder, rerank_client=llm)
    assert follow["path"] == winner
    # A rerun pays for nothing: queries, vectors and labels are persisted inputs.
    calls, embeds = len(llm.calls), len(embedder.calls)
    again = run_retrieval_evaluation(vault, caps=CAPS, queries=12, logged_queries=0,
                                     query_client=llm, judge_client=llm, embedder=embedder)
    assert again["status"] == "complete"
    assert (len(llm.calls), len(embedder.calls)) == (calls, embeds)
    assert again["decision"] == report["decision"]
    assert again["label_calls"] == 0


def test_blocked_states_make_no_calls(tmp_path):
    paths = build_practice_vault(tmp_path / "vault")
    enable_practice_index(paths)
    vault = load_vault(paths.root)
    open_vault_repository(vault.root, paths.sqlite_path)
    report = run_retrieval_evaluation(vault, caps=CAPS, query_client=Forbidden(),
                                      judge_client=Forbidden(), embedder=HashingEmbedder())
    assert report["status"] == "dossier_unavailable"
    vault, *_ = _index(paths, embeddings=False)
    report = run_retrieval_evaluation(vault, caps=CAPS, query_client=Forbidden(),
                                      judge_client=Forbidden(), embedder=HashingEmbedder())
    assert report["status"] == "dossier_unavailable"  # dossier vectors are missing
    assert "embedding backfill" in report["reason"]


def test_switch_off_and_caps_stop_before_a_decision(indexed):
    _paths, vault, _repository, llm, embedder = indexed
    vault.config.practice_index.evaluation_enabled = False
    assert run_retrieval_evaluation(vault, caps=CAPS, queries=4, query_client=llm, judge_client=llm,
                                    embedder=embedder)["status"] == "disabled"
    vault.config.practice_index.evaluation_enabled = True
    tight = SpendCaps(max_candidates=500, max_pairs=5, max_calls=400, max_retries=0,
                      max_total_tokens=10_000_000, max_estimated_usd=1.0)
    report = run_retrieval_evaluation(vault, caps=tight, queries=4, query_client=llm,
                                      judge_client=llm, embedder=embedder)
    assert report["status"] == "over_budget"
    assert "decision" not in report
    assert json.dumps(report["charged"])
