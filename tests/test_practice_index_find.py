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
              "model_call_receipts", "model_work_checkpoints", "sqlite_sequence"}


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


class _ItemAwareLLM(FakePracticeLLM):
    """Dossier text that depends on the grounding items, so a source edit changes it."""

    def _practice_dossier(self, context):
        draft = super()._practice_dossier(context)
        first = context["items"][0]["prompt"] if context.get("items") else "none"
        return draft.model_copy(update={"covers": [*draft.covers, f"grounded on {first}"]})


def test_changed_index_content_voids_an_earlier_evaluation_approval(indexed):
    """F3: approval binds to the evaluated item text, facet mapping and dossier revisions."""
    from learnloop.vault.yaml_io import read_yaml, write_yaml

    paths, vault, repository, llm, embedder = indexed
    _evaluation(repository, load_snapshot(vault, repository, embedder=embedder), "dossier")
    assert find_practice(vault, repository, QUERY, embedder=embedder,
                         rerank_client=llm)["path"] == "dossier"
    # Same models and recipe versions; only item text and the dossier it grounds change.
    item_path = paths.practice_item_path("linear-algebra", "pi_eigen_1")
    write_yaml(item_path, {**read_yaml(item_path),
                           "prompt": "Compute the eigenvalues of [[4,1],[2,3]] by hand."})
    assert generate_dossiers(load_vault(paths.root), caps=CAPS,
                             client=_ItemAwareLLM())["generated"] >= 1
    vault = load_vault(paths.root)
    assert backfill_embeddings(vault, caps=CAPS,
                               client_factory=lambda: embedder)["status"] == "complete"
    snapshot = load_snapshot(vault, repository, embedder=embedder)
    assert snapshot.dossier_available, snapshot.dossier_reason
    result = find_practice(vault, repository, QUERY, embedder=embedder, rerank_client=llm)
    assert result["path"] == "direct"
    assert "different index" in result["path_reason"]
    # A facet-mapping change alone also voids it.
    _evaluation(repository, snapshot, "dossier")
    assert find_practice(vault, repository, QUERY, embedder=embedder,
                         rerank_client=llm)["path"] == "dossier"
    span_item = paths.practice_item_path("linear-algebra", "pi_span_3")
    write_yaml(span_item, {**read_yaml(span_item),
                           "evidence_facets": ["facet_span", "facet_independence"],
                           "evidence_weights": {"facet_span": 1.0, "facet_independence": 1.0}})
    moved = load_vault(paths.root)
    assert load_snapshot(moved, repository, embedder=embedder).manifest_hash() != snapshot.manifest_hash()


class _OtherModelEmbedder(HashingEmbedder):
    model_id = model = "openai/text-embedding-3-small"


def test_an_alternative_embedding_model_takes_an_explicit_price(tmp_path):
    """F6: an owner price reaches query-embedding planning and execution; unknown stays closed."""
    from learnloop.practice_index.evaluation import run_retrieval_evaluation

    paths = build_practice_vault(tmp_path / "vault")
    enable_practice_index(paths)
    config = paths.root / "learnloop.toml"
    config.write_text(config.read_text().replace(
        'model = "qwen/qwen3-embedding-8b"', 'model = "openai/text-embedding-3-small"'))
    open_vault_repository(paths.root, paths.sqlite_path)
    llm, embedder = FakePracticeLLM(), _OtherModelEmbedder()
    assert generate_dossiers(load_vault(paths.root), caps=CAPS, client=llm)["status"] == "complete"
    vault = load_vault(paths.root)
    assert backfill_embeddings(vault, caps=CAPS, price_per_million=0.02,
                               client_factory=lambda: embedder)["status"] == "complete"
    vault, repository = load_vault(paths.root), Repository(paths.sqlite_path)
    eval_caps = SpendCaps(max_candidates=500, max_pairs=4000, max_calls=400, max_retries=4,
                          max_total_tokens=10_000_000, max_estimated_usd=1.0)
    clients = {"query_client": llm, "judge_client": llm, "embedder": embedder}
    # Unknown prices stay fail-closed.
    unpriced = find_practice(vault, repository, QUERY, embedder=embedder, rerank_client=llm)
    assert unpriced["signals"]["query_embedding"]["status"] == "skipped"
    refused = run_retrieval_evaluation(vault, caps=eval_caps, dry_run=True, queries=4, **clients)
    assert refused["status"] == "over_budget" and "--embedding-price-per-million" in refused["reason"]
    # An explicit price is used by planning and by the run alike.
    planned = run_retrieval_evaluation(vault, caps=eval_caps, dry_run=True, queries=4,
                                       embedding_price_per_million=0.02, **clients)
    assert planned["status"] == "dry_run", planned
    assert planned["estimate"]["query_embedding"]["price_per_million"] == 0.02
    assert planned["estimate"]["query_embedding"]["estimated_usd"] > 0
    report = run_retrieval_evaluation(vault, caps=eval_caps, queries=4,
                                      embedding_price_per_million=0.02, **clients)
    assert report["status"] == "complete", report
    assert report["query_embedding"]["status"] == "embedded"
    vault.config.practice_index.query_embedding_price_per_million = 0.02
    priced = find_practice(vault, repository, "practise orthogonal vectors", embedder=embedder,
                           rerank_client=llm)
    assert priced["signals"]["query_embedding"]["status"] == "embedded"
    assert "item_vector" in priced["signals"]["item"]


def test_find_dry_run_plans_embedding_and_rerank_without_clients_or_writes(indexed, monkeypatch):
    """F7: a read-only plan of find_practice's paid steps, cache hits and effective caps."""
    from typer.testing import CliRunner

    from learnloop.cli import app
    from learnloop.practice_index.retrieval import plan_find_practice

    paths, vault, repository, llm, embedder = indexed

    def refuse(*args, **kwargs):
        raise AssertionError("a dry run never constructs a client")

    monkeypatch.setattr("learnloop.practice_index.paid.ready_client_for_task", refuse)
    monkeypatch.setattr("learnloop.practice_index.query_vectors.ready_client_for_task", refuse)
    before = paths.sqlite_path.read_bytes()
    plan = plan_find_practice(vault, repository, QUERY)
    assert plan["status"] == "dry_run" and plan["serves"] is False
    assert plan["query_embedding"]["status"] == "would_embed"
    assert plan["query_embedding"]["calls"] == 1 and plan["query_embedding"]["estimated_usd"] > 0
    assert plan["query_embedding"]["caps"]["max_calls"] == 1
    assert plan["rerank"]["status"] == "would_call"
    assert plan["rerank"]["billing"] == "subscription"  # the template routes Codex
    assert plan["rerank"]["estimated_tokens"] > 0 and plan["rerank"]["pool_exact"] is False
    assert plan["rerank"]["caps"]["max_calls"] == 2
    runner = CliRunner()
    result = runner.invoke(app, ["practice-index", "find", QUERY, "--vault", str(paths.root),
                                 "--dry-run", "--json"])
    assert result.exit_code == 0, result.output
    assert json.loads(result.stdout)["status"] == "dry_run"
    text = runner.invoke(app, ["practice-index", "find", QUERY, "--vault", str(paths.root),
                               "--dry-run", "--no-rerank"])
    assert text.exit_code == 0, text.output
    assert "query embedding: would_embed" in text.output and "rerank: disabled" in text.output
    assert paths.sqlite_path.read_bytes() == before
    with repository.connection() as connection:
        assert connection.execute("SELECT COUNT(*) FROM practice_index_proposals").fetchone()[0] == 0
    # After a real call, the same request is served from caches: nothing to pay.
    monkeypatch.undo()
    find_practice(vault, repository, QUERY, embedder=embedder, rerank_client=llm)
    calls = len(llm.calls)
    again = plan_find_practice(vault, repository, QUERY, embedder=embedder, rerank_client=llm)
    assert len(llm.calls) == calls  # an injected client only names the route
    assert again["query_embedding"]["status"] == "cached"
    assert again["rerank"]["status"] == "cached" and again["rerank"]["pool_exact"] is True
    assert again["estimate"]["calls"] == 0


def test_find_dry_run_names_metered_rerank_prices_and_caps(indexed):
    from learnloop.practice_index.retrieval import plan_find_practice

    _paths, vault, repository, _llm, _embedder = indexed
    vault.config.ai.routing.practice_rerank = "openrouter_test"
    from learnloop.config.schema import AIProviderConfig

    vault.config.ai.providers["openrouter_test"] = AIProviderConfig.model_validate(
        {"type": "openrouter", "model": "vendor/model"})
    plan = plan_find_practice(vault, repository, QUERY, {"rerank": True})
    assert plan["rerank"]["status"].startswith("skipped")
    vault.config.practice_index.rerank_price_per_million = 3.0
    priced = plan_find_practice(vault, repository, QUERY)
    assert priced["rerank"]["status"] == "would_call"
    assert priced["rerank"]["billing"] == "metered" and priced["rerank"]["estimated_usd"] > 0
    vault.config.practice_index.rerank_max_cost_usd = 0.0
    capped = plan_find_practice(vault, repository, QUERY)
    assert capped["rerank"]["status"].startswith("over_budget")


def _live_rerank_prompt(repository):
    with repository.connection() as connection:
        rows = connection.execute(
            "SELECT input_text FROM model_call_receipts WHERE purpose='practice_rerank' "
            "AND parent_call_id IS NULL ORDER BY started_at").fetchall()
    return rows[-1]["input_text"] if rows else None


@pytest.mark.parametrize("query", [
    "zqxv wplk brrt",            # no keyword overlap: BM25 finds nothing
    "eigenvalues zqxv wplk",     # partial overlap: BM25 finds only a few items
])
def test_find_dry_run_bounds_the_rerank_pool_the_query_vector_will_fill(indexed, query):
    """F9: before the query is embedded, the keyword-only pool says nothing about
    the rerank pool; the plan bounds it by the admissible corpus and candidate_pool."""
    from learnloop.practice_index.contracts import PracticeRerank
    from learnloop.practice_index.paid import estimated_call_tokens
    from learnloop.practice_index.paid import plan_route
    from learnloop.practice_index.retrieval import plan_find_practice

    _paths, vault, repository, llm, embedder = indexed
    vault.config.practice_index.query_embedding_price_per_million = 0.02
    plan = plan_find_practice(vault, repository, query)
    bound = min(vault.config.practice_index.candidate_pool, plan["admission"]["admitted"])
    assert plan["query_embedding"]["status"] == "would_embed"
    rerank = plan["rerank"]
    assert rerank["status"] == "would_call", rerank
    assert rerank["pool_exact"] is False and rerank["pool"] == bound
    assert rerank["caps"]["max_candidates"] == bound and rerank["caps"]["max_pairs"] == bound
    assert rerank["budget_charge"]["candidates"] == bound
    assert plan["admission"]["pool"] == bound and plan["admission"]["pool_exact"] is False
    assert plan["estimate"]["calls"] == 2

    result = find_practice(vault, repository, query, embedder=embedder, rerank_client=llm)
    assert result["signals"]["query_embedding"]["status"] == "embedded"
    assert result["rerank_status"] == "reranked"
    live = [payload for purpose, payload in llm.calls if purpose == "practice_rerank"][-1]
    assert 0 < len(live["context"]["candidates"]) <= rerank["pool"]
    # The rerank's output budget is its route's under the shared policy.
    live_tokens = estimated_call_tokens(_live_rerank_prompt(repository), PracticeRerank,
                                        plan_route(vault, "practice_rerank", llm).output_tokens)
    assert rerank["estimated_tokens"] >= live_tokens


def test_find_dry_run_keeps_the_keyword_pool_when_no_query_embedding_will_run(indexed, monkeypatch):
    """F9: when the query embedding is skipped, keyword search alone is the live pool."""
    from learnloop.practice_index.retrieval import plan_find_practice

    _paths, vault, repository, llm, embedder = indexed
    monkeypatch.setattr("learnloop.practice_index.retrieval.query_embedding_price",
                        lambda model_id, override: (None, "unknown"))
    plan = plan_find_practice(vault, repository, "zqxv wplk brrt")
    assert plan["query_embedding"]["status"] == "skipped"
    assert plan["rerank"]["status"] == "empty_pool" and plan["rerank"]["pool_exact"] is True
    assert plan["admission"]["pool"] == 0 and plan["estimate"]["calls"] == 0


def test_a_rerank_whose_checkpoint_failed_is_recovered_from_its_receipt(indexed, monkeypatch):
    """F8 (re-review): a completed rerank receipt whose checkpoint never committed
    is recovered (same request identity, validated), not paid for again."""
    import sqlite3

    from learnloop.db.stores.model_calls import ModelCallStoreMixin
    from learnloop.practice_index.retrieval import plan_find_practice

    _paths, vault, repository, llm, embedder = indexed
    real_save = ModelCallStoreMixin.save_model_checkpoint

    def failing_save(self, cache_key, *, purpose, result, usage=None):
        if purpose == "practice_rerank":
            raise sqlite3.OperationalError("disk I/O error")
        return real_save(self, cache_key, purpose=purpose, result=result, usage=usage)

    monkeypatch.setattr(ModelCallStoreMixin, "save_model_checkpoint", failing_save)
    with pytest.raises(sqlite3.OperationalError):
        find_practice(vault, repository, QUERY, embedder=embedder, rerank_client=llm)
    reranks = sum(1 for purpose, _ in llm.calls if purpose == "practice_rerank")
    assert reranks == 1
    monkeypatch.setattr(ModelCallStoreMixin, "save_model_checkpoint", real_save)
    plan = plan_find_practice(vault, repository, QUERY, embedder=embedder, rerank_client=llm)
    assert plan["rerank"]["status"] == "recoverable" and plan["estimate"]["calls"] == 0
    result = find_practice(vault, repository, QUERY, embedder=embedder, rerank_client=llm)
    assert result["rerank_status"] == "reranked" and result["items"]
    assert sum(1 for purpose, _ in llm.calls if purpose == "practice_rerank") == reranks
    assert result["rerank_model"] == llm.model


def _store_skeletons(repository, vault, item_ids):
    from learnloop.db.stores.pf import insert_skeleton
    from learnloop.vault.hashes import skeleton_content_hash

    with repository.connection() as connection:
        for item_id in item_ids:
            item = vault.practice_items[item_id]
            insert_skeleton(
                connection, skeleton_id=f"sk_{item_id}",
                content_hash=skeleton_content_hash(item.prompt, item.expected_answer),
                subject_kind="practice_item", subject_id=item_id, model_id="fake/skeleton",
                prompt_version="pf-skeleton-test", techniques=["outline"], operations=[],
                checkpoints=[], skeleton_text=f"Outline: {item.prompt}",
                created_at="2026-10-12T00:00:00Z",
            )


def test_item_skeleton_vectors_rank_items_only_once_they_cover_every_item(indexed):
    """Phase 5a merge: PF-b skeletons exist only for the items it generated or
    judged, so a partial item/skeleton index never displaces item-text vectors."""
    paths, vault, repository, llm, embedder = indexed
    assert load_snapshot(vault, repository, embedder=embedder).item_recipe == "item/stem"
    items = sorted(item_id for item_id, item in vault.practice_items.items() if item.status != "retired")
    _store_skeletons(repository, vault, items[:1])
    vault = load_vault(paths.root)
    assert backfill_embeddings(vault, caps=CAPS, client_factory=lambda: embedder)["status"] == "complete"
    partial = load_snapshot(vault, repository, embedder=embedder)
    assert partial.item_recipe == "item/stem"
    assert set(partial.item_manifest) == set(items)
    _store_skeletons(repository, vault, items[1:])
    vault = load_vault(paths.root)
    assert backfill_embeddings(vault, caps=CAPS, client_factory=lambda: embedder)["status"] == "complete"
    full = load_snapshot(vault, repository, embedder=embedder)
    assert full.item_recipe == "item/skeleton" and set(full.item_manifest) == set(items)
    result = find_practice(vault, repository, QUERY, embedder=embedder, rerank_client=llm)
    assert result["signals"]["item"] == ["item_bm25", "item_vector"]
