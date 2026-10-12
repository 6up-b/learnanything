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


def test_the_registry_shortlist_reaches_the_diagnosis_context_as_of_the_attempt(tmp_path):
    """Review F8 (§5.2, §9.4): with S1.4a on, the diagnosis context adds a kNN
    shortlist over the WHOLE vault registry (here a belief on an LO outside
    the neighborhood), as of the diagnosed attempt, with provenance; without
    embeddings it falls back to the exact registry set."""

    import json as _json

    from tests.diagnosis_fakes import prompt_payload

    paths, vault, repository = _embedding_vault(tmp_path)
    unrelated_event = repository.raw_error_events_for_attempt("att_02_svd_fail")[0]["id"]
    far_id = repository.insert_misconception(
        learning_object_id="lo_unrelated",
        statement="The learner applies the rule in the wrong order.",
        concept_id="unrelated_topic",
        severity=0.5,
        source_error_event_ids=[unrelated_event],
        clock=FrozenClock(at(9)),
    )
    later_id = repository.insert_misconception(
        learning_object_id="lo_unrelated",
        statement="A belief recorded only after the diagnosed answer.",
        concept_id="unrelated_topic",
        severity=0.5,
        source_error_event_ids=[unrelated_event],
        clock=FrozenClock(at(40)),
    )
    client = ReviewFakeClient()
    embedder = FakeEmbeddingClient()
    result = submit(vault, repository, client, when=at(20))
    drain_jobs(vault, repository, client, embedding=embedder, clock=FrozenClock(at(21)))

    prompt = prompt_payload(client.prompts[client.calls.index("diagnosis")])
    offered = {row["id"] for row in prompt["context"]["registry_candidates"]}
    assert far_id in offered and later_id not in offered
    diagnosis = repository.latest_attempt_diagnosis(result.attempt_id)
    receipt = repository.diagnosis_context_receipt(diagnosis["id"])
    shortlist = receipt["retrieval"]["registry_retrieval"]
    assert shortlist["method"] == "knn" and shortlist["model_id"] == embedder.model_id
    assert f"durable:{far_id}" in shortlist["knn_only_registry_ids"]
    assert far_id in receipt["registry_candidate_ids"]
    assert all(row["source"] in {"knn", "both"} for row in shortlist["matches"])
    assert _vector_count(repository, "misconception") >= 1

    # No embedding client: the exact registry set, recorded as the fallback.
    second = submit(vault, repository, client, item_id="pi_svd_compute_002", answer="B = U Sigma V nope", when=at(22))
    drain_jobs(vault, repository, client, embedding=None, clock=FrozenClock(at(23)))
    fallback = repository.latest_attempt_diagnosis(second.attempt_id)
    fallback_receipt = repository.diagnosis_context_receipt(fallback["id"])
    assert fallback_receipt["retrieval"]["registry_retrieval"]["method"] == "exact_fallback"
    assert far_id not in fallback_receipt["registry_candidate_ids"]
    assert _json.dumps(fallback_receipt["retrieval"]["registry_retrieval"]["knn_only_registry_ids"]) == "[]"


def test_the_diagnoser_may_match_a_shortlisted_belief_from_outside_the_neighborhood(tmp_path):
    """Review F8: the shortlist is part of the closed world, so the
    diagnoser's registry_match on it validates (identity stays its call)."""

    from learnloop.diagnosis.split.contract import RegistryMatch

    paths, vault, repository = _embedding_vault(tmp_path)
    source = repository.raw_error_events_for_attempt("att_02_svd_fail")[0]["id"]
    far_id = repository.insert_misconception(
        learning_object_id="lo_unrelated",
        statement="The learner applies the rule in the wrong order.",
        concept_id="unrelated_topic",
        severity=0.5,
        source_error_event_ids=[source],
        clock=FrozenClock(at(9)),
    )

    class MatchFar(ReviewFakeClient):
        def _diagnosis(self, request, context):
            result = super()._diagnosis(request, context)
            offered = {row["id"] for row in context.get("registry_candidates") or []}
            assert far_id in offered
            events = [
                event.model_copy(update={
                    "misconception_statement": "The learner applies the rule in the wrong order.",
                    "registry_match": RegistryMatch(kind="durable", id=far_id),
                })
                for event in result.event_diagnoses
            ]
            return result.model_copy(update={"event_diagnoses": events})

    client = MatchFar()
    result = submit(vault, repository, client, when=at(20))
    drain_jobs(vault, repository, client, embedding=FakeEmbeddingClient(), clock=FrozenClock(at(21)))

    diagnosis = repository.latest_attempt_diagnosis(result.attempt_id)
    assert diagnosis["status"] == "completed"
    assert diagnosis["validation_report"].get("unknown_id_count", 0) == 0
    matches = {
        (event["registry_match"]["kind"], event["registry_match"].get("id"))
        for event in diagnosis["proposal"]["event_diagnoses"]
    }
    assert matches == {("durable", far_id)}
    # Merging an event into a belief owned by another LO stays outside
    # normalization's LO/confusable scope (promotion rules unchanged).
