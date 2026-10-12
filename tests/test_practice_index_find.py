"""find_practice: recall, rerank, admit, receipt; it proposes and never serves."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta
import json

import pytest

from learnloop.ai.spend import SpendCaps
from learnloop.attempts.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.db.stores.practice_index import insert_evaluation
from learnloop.ops.embedding_backfill import backfill_embeddings
from learnloop.practice_index.dossiers import generate_dossiers
from learnloop.practice_index.retrieval import PracticeConstraints, find_practice, load_snapshot
from learnloop.practice_index.tool import run_find_practice_tool
from learnloop.practice_index.usage import record_practice_usage, sweep_practice_usage, usage_summary
from learnloop.vault.loader import load_vault
from learnloop.vault.repository import open_vault_repository
from tests.practice_index_fakes import (
    FakePracticeLLM,
    HashingEmbedder,
    build_practice_vault,
    enable_practice_index,
)

CAPS = SpendCaps(max_candidates=1000, max_calls=100, max_total_tokens=10_000_000, max_estimated_usd=1.0)
QUERY = "eigenvalues of a matrix"
OWN_TABLES = {"practice_index_proposals", "judgment_ledger", "embedding_vectors",
              "model_call_receipts", "sqlite_sequence"}


def _index(paths, *, embeddings=True):
    vault = load_vault(paths.root)
    llm, embedder = FakePracticeLLM(), HashingEmbedder()
    assert generate_dossiers(vault, caps=CAPS, client=llm)["status"] == "complete"
    if embeddings:
        vault = load_vault(paths.root)
        report = backfill_embeddings(vault, caps=CAPS, client_factory=lambda: embedder)
        assert report["status"] == "complete", report
    return load_vault(paths.root), Repository(paths.sqlite_path), llm, embedder


@pytest.fixture
def indexed(tmp_path):
    paths = build_practice_vault(tmp_path / "vault")
    enable_practice_index(paths)
    open_vault_repository(paths.root, paths.sqlite_path)
    return (paths, *_index(paths))


def _counts(paths):
    with Repository(paths.sqlite_path).connection() as connection:
        tables = [row[0] for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table'")]
        return {table: connection.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
                for table in tables if table not in OWN_TABLES}


def test_direct_item_search_is_the_default_and_leaves_a_receipt(indexed):
    paths, vault, repository, llm, embedder = indexed
    result = find_practice(vault, repository, QUERY, embedder=embedder, rerank_client=llm)
    assert result["status"] == "ok" and result["serves"] is False
    assert result["path"] == "direct"
    assert "dossiers must beat direct item search" in result["path_reason"]
    assert result["signals"]["item"] == ["item_bm25", "item_vector"]
    assert result["reranked"] is True
    assert result["items"][0]["practice_item_id"].startswith("pi_eigen_")
    assert "expected_answer" not in json.dumps(result)
    with repository.connection() as connection:
        row = connection.execute("SELECT * FROM practice_index_proposals").fetchone()
    assert row["id"] == result["proposal_id"]
    assert row["path"] == "direct" and row["origin"] == "api"
    assert [entry["practice_item_id"] for entry in json.loads(row["proposed_json"])] == [
        item["practice_item_id"] for item in result["items"]
    ]


def test_proposing_never_serves_or_writes_learning_state(indexed):
    paths, vault, repository, llm, embedder = indexed
    before = _counts(paths)
    for query in (QUERY, "span of vectors", "orthogonal projection"):
        find_practice(vault, repository, query, embedder=embedder, rerank_client=llm)
    assert _counts(paths) == before


def _evaluation(repository, snapshot, winner, *, manifest_hash=None):
    with repository.connection() as connection:
        insert_evaluation(
            connection, id=f"pie_{winner}_{manifest_hash or snapshot.manifest_hash()}",
            created_at="2026-10-12T00:00:00Z",
            winner=winner, reason=f"{winner} won", manifest_hash=manifest_hash or snapshot.manifest_hash(),
            manifest=snapshot.manifest(), metrics={}, run_id="run",
        )


def test_the_dossier_path_needs_a_winning_evaluation_on_the_current_index(indexed):
    _paths, vault, repository, llm, embedder = indexed
    snapshot = load_snapshot(vault, repository, embedder=embedder)
    assert snapshot.dossier_available, snapshot.dossier_reason
    _evaluation(repository, snapshot, "dossier", manifest_hash="other-index")
    stale = find_practice(vault, repository, QUERY, embedder=embedder, rerank_client=llm)
    assert stale["path"] == "direct" and "different index" in stale["path_reason"]
    _evaluation(repository, snapshot, "dossier")
    result = find_practice(vault, repository, QUERY, embedder=embedder, rerank_client=llm)
    assert result["path"] == "dossier"
    assert result["signals"]["facet"] == ["dossier_bm25", "dossier_contrast", "dossier_errors",
                                          "dossier_moves", "dossier_scope"]
    assert "facet_stage" in result["signals"]["item"]
    assert result["facets"][0]["facet_id"] == "facet_eigen"
    top = {facet["facet_id"] for facet in result["facets"]}
    # Five facets cover 15 admissible items, so a sixth fills the pool of 20.
    assert len(top) == 6
    assert all(set(item["facet_ids"]) & top for item in result["items"])
    vault.config.practice_index.facet_top_k = 1
    vault.config.practice_index.candidate_pool = 3
    snapshot = load_snapshot(vault, repository, embedder=embedder)
    _evaluation(repository, snapshot, "dossier")
    narrow = find_practice(vault, repository, QUERY, embedder=embedder, rerank_client=llm)
    assert narrow["path"] == "dossier"
    assert [facet["facet_id"] for facet in narrow["facets"]] == ["facet_eigen"]
    assert {item["practice_item_id"] for item in narrow["items"]} <= {"pi_eigen_1", "pi_eigen_2", "pi_eigen_3"}


def test_a_forced_dossier_path_falls_back_while_dossiers_are_missing(tmp_path):
    paths = build_practice_vault(tmp_path / "vault")
    enable_practice_index(paths, embeddings=False)
    config = paths.root / "learnloop.toml"
    config.write_text(config.read_text().replace(
        "[practice_index]\n", '[practice_index]\nretrieval_path = "dossier"\n'))
    vault = load_vault(paths.root)
    repository = open_vault_repository(vault.root, paths.sqlite_path)
    result = find_practice(vault, repository, QUERY, rerank_client=FakePracticeLLM())
    assert result["path"] == "direct"
    assert "6 of 6 facets have no current dossier" in result["path_reason"]
    assert result["signals"]["item"] == ["item_bm25"]
    assert result["signals"]["query_embedding"]["status"] == "unused"


def test_rerank_verdicts_go_to_the_ledger_and_are_reused(indexed):
    _paths, vault, repository, llm, embedder = indexed
    first = find_practice(vault, repository, QUERY, embedder=embedder, rerank_client=llm)
    calls = len(llm.calls)
    second = find_practice(vault, repository, QUERY, embedder=embedder, rerank_client=llm)
    assert first["rerank_status"] == "reranked" and second["rerank_status"] == "cached"
    assert len(llm.calls) == calls
    assert [i["practice_item_id"] for i in first["items"]] == [i["practice_item_id"] for i in second["items"]]
    assert second["signals"]["query_embedding"]["status"] == "cached"
    with repository.connection() as connection:
        rows = connection.execute(
            "SELECT * FROM judgment_ledger WHERE task='practice_relevance'").fetchall()
    assert rows and {row["judge"] for row in rows} == {"llm"}
    assert {row["prompt_version"] for row in rows} == {"practice_rerank.v1"}
    assert {row["judge_model"] for row in rows} == {"fake-practice-model"}
    assert all(item["relevance"] in {"relevant", "partial"} for item in first["items"])
    picked = [json.loads(row["rationale"])["pick_rank"] for row in rows]
    assert sorted(rank for rank in picked if rank) == list(range(1, len(first["items"]) + 1))


def test_a_metered_rerank_without_a_price_is_skipped_and_labelled(indexed):
    _paths, vault, repository, _llm, embedder = indexed
    metered = FakePracticeLLM(provider_type="openrouter")
    result = find_practice(vault, repository, QUERY, embedder=embedder, rerank_client=metered)
    assert result["reranked"] is False
    assert result["rerank_status"].startswith("skipped")
    assert metered.calls == []
    assert len(result["items"]) == vault.config.practice_index.proposals
    assert all(item["relevance"] is None for item in result["items"])


def test_constraints_filter_before_ranking(indexed):
    _paths, vault, repository, llm, embedder = indexed
    result = find_practice(
        vault, repository, "vectors", PracticeConstraints(
            limit=2, learning_object_ids=("lo_vectors",), exclude_item_ids=("pi_span_1",),
            rerank=False,
        ), embedder=embedder,
    )
    assert len(result["items"]) == 2
    assert {item["learning_object_id"] for item in result["items"]} == {"lo_vectors"}
    assert "pi_span_1" not in {item["practice_item_id"] for item in result["items"]}
    assert result["admission"]["excluded"]["constraints"] == 19 - 5
    with pytest.raises(ValueError):
        PracticeConstraints.from_mapping({"serve": True})
    with pytest.raises(ValueError):
        find_practice(vault, repository, "   ", embedder=embedder)


def test_kill_switch_and_the_agent_tool(indexed):
    _paths, vault, repository, llm, embedder = indexed
    result = run_find_practice_tool(vault, repository, {"query": "determinant", "limit": 1},
                                    embedder=embedder, rerank_client=llm)
    assert result["status"] == "ok" and len(result["items"]) == 1
    with repository.connection() as connection:
        assert connection.execute("SELECT origin FROM practice_index_proposals").fetchone()[0] == "tool"
    vault.config.practice_index.enabled = False
    assert find_practice(vault, repository, QUERY)["status"] == "disabled"


def test_usage_signals_are_ledgered_and_joined_to_attempts(indexed):
    _paths, vault, repository, llm, embedder = indexed
    now = datetime.now(UTC)
    result = find_practice(vault, repository, QUERY, embedder=embedder, rerank_client=llm,
                           clock=FrozenClock(now))
    proposal, first, second = result["proposal_id"], *[i["practice_item_id"] for i in result["items"][:2]]
    record_practice_usage(repository, proposal_id=proposal, practice_item_id=second, signal="too_easy")
    record_practice_usage(repository, proposal_id=proposal, practice_item_id=second, signal="too_easy")
    with pytest.raises(ValueError):
        record_practice_usage(repository, proposal_id=proposal, practice_item_id="pi_span_3", signal="skipped")
    with pytest.raises(ValueError):
        record_practice_usage(repository, proposal_id=proposal, practice_item_id=first, signal="loved_it")
    complete_self_graded_attempt(
        vault, repository,
        AttemptDraft(practice_item_id=first, learner_answer_md="an answer",
                     attempt_type="independent_attempt"),
        SelfGradeInput(criterion_points={"correct": 4}, fatal_errors=[], confidence=3),
        clock=FrozenClock(now + timedelta(minutes=5)),
    )
    later = FrozenClock(now + timedelta(hours=1))
    assert sweep_practice_usage(repository, window_hours=72, clock=later)["added"] == 1
    assert sweep_practice_usage(repository, window_hours=72, clock=later)["added"] == 0
    with repository.connection() as connection:
        rows = connection.execute(
            "SELECT judge, verdict, right_id FROM judgment_ledger WHERE task='practice_usage' "
            "ORDER BY judge").fetchall()
    assert [tuple(row) for row in rows] == [("exact_key", "practised", first),
                                            ("learner_card", "too_easy", second)]
    summary = usage_summary(repository)
    assert summary["signals_by_path"] == {"direct": {"exact_key:practised": 1, "learner_card:too_easy": 1}}
    assert QUERY not in json.dumps(summary)


def test_a_partial_rerank_is_retried_then_reported_unreranked(indexed):
    _paths, vault, repository, _llm, embedder = indexed

    class Partial(FakePracticeLLM):
        def _practice_rerank(self, context):
            result = super()._practice_rerank(context)
            return result.model_copy(update={"judgments": result.judgments[1:]})

    partial = Partial()
    result = find_practice(vault, repository, QUERY, embedder=embedder, rerank_client=partial)
    assert result["rerank_status"] == "failed: AIInvalidOutput"
    assert result["reranked"] is False
    assert len(partial.calls) == 2  # the first answer and one retry
    assert len(result["items"]) == vault.config.practice_index.proposals
    with repository.connection() as connection:
        assert connection.execute(
            "SELECT COUNT(*) FROM judgment_ledger WHERE task='practice_relevance'").fetchone()[0] == 0
