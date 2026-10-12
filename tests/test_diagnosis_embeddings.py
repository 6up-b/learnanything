"""Slice 1 S1.4a/S1.4b: hypothesis/registry embeddings, would-merge log, hybrid kNN."""

from __future__ import annotations

from learnloop.ai.spend import SpendCaps
from learnloop.clock import FrozenClock
from learnloop.diagnosis.split.embeddings import (
    hypothesis_records,
    misconception_records,
)
from learnloop.diagnosis.split.embeddings import backfill_with_db_recipes as backfill_embeddings
from learnloop.vault.loader import load_vault

from tests.diagnosis_fakes import FakeEmbeddingClient, ReviewFakeClient
from tests.split_live_helpers import at, drain_jobs, enable_embeddings, split_vault, submit


def _embedding_vault(tmp_path, *, config: str = ""):
    paths, _vault, repository = split_vault(tmp_path, config=config)
    enable_embeddings(paths.root)
    toml = paths.root / "learnloop.toml"
    toml.write_text(toml.read_text(encoding="utf-8").replace("dimensions = 4096", "dimensions = 16"), encoding="utf-8")
    return paths, load_vault(paths.root), repository


def _vector_count(repository, kind):
    with repository.connection() as connection:
        return connection.execute(
            "SELECT COUNT(*) FROM embedding_vectors WHERE record_kind = ?", (kind,)
        ).fetchone()[0]


def test_embeddings_off_queue_no_embed_job(tmp_path):
    _paths, vault, repository = split_vault(tmp_path)
    client = ReviewFakeClient()
    result = submit(vault, repository, client)
    drain_jobs(vault, repository, client)
    assert [job["kind"] for job in repository.post_attempt_jobs(attempt_id=result.attempt_id)] == ["diagnose"]


def test_embed_on_write_is_idempotent_and_logs_would_merge_against_earlier_hypotheses(tmp_path):
    _paths, vault, repository = _embedding_vault(tmp_path)
    client = ReviewFakeClient()
    embedder = FakeEmbeddingClient()
    first = submit(vault, repository, client, when=at(20))
    drain_jobs(vault, repository, client, embedding=embedder, clock=FrozenClock(at(21)))
    second = submit(vault, repository, client, item_id="pi_svd_compute_002", answer="B = U Sigma V nope", when=at(22))
    drain_jobs(vault, repository, client, embedding=embedder, clock=FrozenClock(at(23)))

    kinds = [job["kind"] for job in repository.post_attempt_jobs(attempt_id=second.attempt_id)]
    assert kinds == ["diagnose", "embed"]
    # Embed-on-write covers what the diagnoses minted; older history is the
    # backfill's job (``learnloop embeddings backfill --record-kind hypothesis``).
    minted = hypothesis_records(repository, attempt_ids=[first.attempt_id, second.attempt_id])
    assert minted and _vector_count(repository, "hypothesis") == len(minted)
    assert _vector_count(repository, "misconception") == len(misconception_records(repository))
    calls = embedder.calls
    drain_jobs(vault, repository, client, embedding=embedder)
    assert embedder.calls == calls  # nothing left to embed

    rows = repository.would_merge_rows()
    second_ids = {row["id"] for row in repository.causal_hypotheses_for_attempt(second.attempt_id)}
    first_ids = {row["id"] for row in repository.causal_hypotheses_for_attempt(first.attempt_id)}
    logged = [row for row in rows if row["hypothesis_id"] in second_ids]
    assert logged
    for row in logged:
        neighbor_ids = {neighbor["hypothesis_id"] for neighbor in row["neighbors"]}
        # Only EARLIER hypotheses are candidates; never the attempt's own.
        assert not neighbor_ids & second_ids
        assert [neighbor["rank"] for neighbor in row["neighbors"]] == list(range(1, len(row["neighbors"]) + 1))
    # The identical statement minted by the first attempt is the exact-key group.
    assert any(set(row["exact_group_ids"]) & first_ids for row in logged)


def test_backfill_embeds_db_recipes_only_when_named(tmp_path):
    _paths, vault, repository = _embedding_vault(tmp_path)
    caps = SpendCaps(max_candidates=500, max_calls=50, max_total_tokens=500_000, max_estimated_usd=1.0)
    plan = backfill_embeddings(vault, caps=caps, dry_run=True, recipes=("hypothesis", "misconception"))
    assert plan["status"] == "dry_run"
    assert plan["recipes"] == ["hypothesis", "misconception"]
    assert plan["records"] == len(hypothesis_records(repository)) + len(misconception_records(repository))
    default = backfill_embeddings(vault, caps=caps, dry_run=True)
    assert "hypothesis" not in default["recipes"]

    embedder = FakeEmbeddingClient()
    done = backfill_embeddings(vault, caps=caps, recipes=("hypothesis",), client_factory=lambda: embedder)
    assert done["status"] == "complete" and done["embedded"] == plan["records"] - len(misconception_records(repository))
    again = backfill_embeddings(vault, caps=caps, recipes=("hypothesis",), client_factory=lambda: embedder)
    assert again["pending"] == 0


def test_hybrid_mode_uses_knn_and_degrades_to_exact_without_embeddings(tmp_path):
    paths, vault, repository = _embedding_vault(tmp_path, config='[diagnosis]\nhistory_mode = "hybrid"')
    client = ReviewFakeClient()
    embedder = FakeEmbeddingClient()
    result = submit(vault, repository, client, when=at(20))
    drain_jobs(vault, repository, client, embedding=embedder, clock=FrozenClock(at(21)))

    diagnosis = repository.latest_attempt_diagnosis(result.attempt_id)
    assert diagnosis["history_mode"] == "hybrid"
    retrieval = repository.diagnosis_context_receipt(diagnosis["id"])["retrieval"]
    assert retrieval["method"] == "hybrid"
    assert retrieval["embedding_model_id"] == embedder.model_id
    assert any(row["source"] in {"knn", "both"} for row in retrieval["retrieval"])
    # The divergence recipe was embedded for the hybrid index (S1.4b).
    assert _vector_count(repository, "attempt") >= 1

    # Embedding provider unavailable: hybrid silently falls back to exact (S6).
    second = submit(vault, repository, client, item_id="pi_svd_compute_002", answer="B = U Sigma V nope", when=at(22))
    drain_jobs(vault, repository, client, embedding=None, clock=FrozenClock(at(23)))
    fallback = repository.latest_attempt_diagnosis(second.attempt_id)
    assert fallback["status"] == "completed"
    assert repository.diagnosis_context_receipt(fallback["id"])["retrieval"]["method"] == "exact_fallback"
