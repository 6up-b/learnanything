"""The retrieval evaluation: metrics, the bar, and an end-to-end run with fakes."""
from __future__ import annotations

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
    assert report["query_set"] == {"existing": 0, "recovered": 0, "new_generated": 12,
                                   "new_logged": 0, "total": 12}
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
    # A rerun pays for nothing: queries, vectors and labels are persisted inputs,
    # and the dry run says so exactly.
    planned = run_retrieval_evaluation(vault, caps=CAPS, dry_run=True, queries=12, logged_queries=0,
                                       query_client=llm, judge_client=llm, embedder=embedder)
    assert planned["estimate"]["relevance_labels"]["calls"] == 0
    assert planned["estimate"]["relevance_labels"]["exact_queries"] == 13
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
    fresh = FakePracticeLLM()
    report = run_retrieval_evaluation(vault, caps=tight, queries=4, query_client=fresh,
                                      judge_client=fresh, embedder=embedder)
    assert report["status"] == "over_budget"
    assert "decision" not in report
    assert "pairs exceeds max_pairs" in report["reason"]
    assert fresh.calls == []  # the whole plan is refused before any request


def test_caps_are_checked_against_the_whole_plan_first(indexed):
    _paths, vault, _repository, _llm, embedder = indexed
    metered = FakePracticeLLM(provider_type="openrouter")
    report = run_retrieval_evaluation(vault, caps=CAPS, queries=4, query_client=metered,
                                      judge_client=metered, embedder=embedder)
    assert report["status"] == "over_budget"
    assert "--price-per-million" in report["reason"]
    few_calls = SpendCaps(max_candidates=500, max_pairs=4000, max_calls=3, max_retries=0,
                          max_total_tokens=10_000_000, max_estimated_usd=1.0)
    llm = FakePracticeLLM()
    report = run_retrieval_evaluation(vault, caps=few_calls, queries=4, query_client=llm,
                                      judge_client=llm, embedder=embedder)
    assert report["status"] == "over_budget" and llm.calls == []


def test_paid_labels_and_queries_survive_a_failed_write(indexed, monkeypatch):
    """F8: written queries and label passes are checkpointed before their rows commit."""
    import sqlite3

    from learnloop.practice_index import evaluation as evaluation_module

    _paths, vault, _repository, llm, embedder = indexed
    real_query, real_judgment = evaluation_module.insert_eval_query, evaluation_module.append_judgment
    writes = {"queries": 0}

    def failing_query(connection, **values):
        if values["seed_kind"] != "logged":
            writes["queries"] += 1
            if writes["queries"] > 8:  # the second writer batch
                raise sqlite3.OperationalError("disk I/O error")
        return real_query(connection, **values)

    monkeypatch.setattr(evaluation_module, "insert_eval_query", failing_query)
    with pytest.raises(sqlite3.OperationalError):
        run_retrieval_evaluation(vault, caps=CAPS, queries=12, query_client=llm,
                                 judge_client=llm, embedder=embedder)
    writer_calls = sum(1 for purpose, _ in llm.calls if purpose == "practice_query_writer")
    assert writer_calls == 2
    monkeypatch.setattr(evaluation_module, "insert_eval_query", real_query)

    def failing_judgment(connection, **values):
        raise sqlite3.OperationalError("disk I/O error")

    monkeypatch.setattr(evaluation_module, "append_judgment", failing_judgment)
    planned = run_retrieval_evaluation(vault, caps=CAPS, dry_run=True, queries=12, logged_queries=0,
                                       query_client=llm, judge_client=llm, embedder=embedder)
    assert planned["query_set"]["recovered"] == 4
    assert planned["query_set"]["new_generated"] == 0
    with pytest.raises(sqlite3.OperationalError):
        run_retrieval_evaluation(vault, caps=CAPS, queries=12, logged_queries=0, query_client=llm,
                                 judge_client=llm, embedder=embedder)
    assert sum(1 for purpose, _ in llm.calls if purpose == "practice_query_writer") == writer_calls
    judged = sum(1 for purpose, _ in llm.calls if purpose == "practice_relevance_judge")
    assert judged == 1
    monkeypatch.setattr(evaluation_module, "append_judgment", real_judgment)
    report = run_retrieval_evaluation(vault, caps=CAPS, queries=12, logged_queries=0,
                                      query_client=llm, judge_client=llm, embedder=embedder)
    assert report["status"] == "complete", report
    assert report["query_set"]["total"] == 12
    assert sum(1 for purpose, _ in llm.calls if purpose == "practice_query_writer") == writer_calls
    # The interrupted label pass was recovered, not paid for again.
    assert report["spend"]["relevance_judge"]["usage"]["recovered"] == 1
    assert sum(1 for purpose, _ in llm.calls if purpose == "practice_relevance_judge") == (
        judged + report["label_calls"] - 1)


def test_duplicate_queries_cannot_manufacture_a_winning_evaluation(indexed, monkeypatch):
    """F5: one request written by ten seeds is one observation, not ten."""
    from learnloop.db.stores.practice_index import insert_eval_query
    from learnloop.practice_index import evaluation as evaluation_module

    _paths, vault, repository, llm, embedder = indexed
    variants = ["eigenvalues characteristic polynomial", "Eigenvalues  characteristic polynomial",
                "eigenvalues characteristic polynomial "]
    with repository.connection() as connection:
        for index in range(10):
            insert_eval_query(
                connection, id=f"peq_dup{index}", query_text=variants[index % 3].strip(),
                seed_kind="item" if index % 2 else "facet", seed_id=f"seed_{index}",
                model_id="fake-practice-model", prompt_version=evaluation_module.QUERY_PROMPT_VERSION,
                input_hash="h", run_id=None, created_at="2026-10-12T00:00:00Z",
            )
    eigen = ["pi_eigen_3", "pi_eigen_1", "pi_eigen_2"]
    others = sorted(item for item in vault.practice_items
                    if item.startswith(("pi_span", "pi_independence", "pi_orthogonal")))

    def rankings(snapshot, repository, text, vector, corpus):
        # This one request favours dossiers: a real win, but a single observation.
        return {"direct": others[:10], "dossier": (eigen + others)[:10]}

    monkeypatch.setattr(evaluation_module, "_rankings", rankings)
    report = run_retrieval_evaluation(vault, caps=CAPS, queries=0, logged_queries=0,
                                      query_client=llm, judge_client=llm, embedder=embedder)
    assert report["status"] == "complete", report
    metrics = report["metrics"]
    assert metrics["scored_queries"] == 1
    assert metrics["duplicate_query_rows"] == 9
    assert metrics["summary"]["ndcg@10"]["difference"]["n"] == 1
    assert metrics["summary"]["ndcg@10"]["difference"]["mean"] > 0
    assert report["decision"]["winner"] == "direct"
    assert "insufficient evidence" in report["decision"]["reason"]
    # Provenance is kept: the one query came from both seed kinds.
    assert metrics["query_provenance"] == {"facet": 5, "item": 5}
