"""Local contextual retrieval P1: the space resolver seam in ``search_spans``.

Byte-identity at the defaults and with the default left at Qwen; the Voyage
fallback serving what Qwen does not cover (with receipts and reasons); the
local space through a query-encoder hook; epoch drift; the feedback receipts,
the tutor citation signal, result opens, the refit and its replay; the seed
weights serving while the learned rule is only logged. Fakes only."""
from __future__ import annotations

from contextlib import closing
import json
import sqlite3

import numpy as np
import pytest

from learnloop.ai.spend import SpendCaps
from learnloop.db.stores.retrieval_spaces import feedback_rows, fusion_posteriors, set_space_status
from learnloop.local_embeddings import fusion
from learnloop.ops.embedding_backfill import backfill_embeddings
from learnloop.source_retrieval import fallback_space, feedback, local_index, spaces
from learnloop.source_retrieval.corpus import library_scope
from learnloop.source_retrieval.dense import clear_cache
from learnloop.source_retrieval.find_sources import find_sources
from learnloop.source_retrieval.recipes import SOURCE_RETRIEVAL_RECIPES
from learnloop.source_retrieval.search import search_spans
from tests.helpers import append_config_toml
from tests.local_embeddings_fakes import (
    VOYAGE_PROFILE,
    FakeLocalModel,
    FakeVoyageClient,
    InProcessLauncher,
    no_locks,
    set_up_data_root,
)
from tests.source_retrieval_fakes import HashingEmbedder, build_retrieval_vault, loaded, seed_source

CAPS = SpendCaps(max_candidates=10_000, max_pairs=0, max_calls=100, max_total_tokens=10**8, max_estimated_usd=10.0)
QUERY = "eigenvalues of a symmetric matrix"
NEW_BOOK = {"ch_basis": ("Chapter 2 Bases", [
    ("A basis is a linearly independent spanning list of a vector space.", 2),
    ("Every finite-dimensional vector space has a basis, and all bases have the same length.", 2),
])}


@pytest.fixture(autouse=True)
def _fresh(monkeypatch, tmp_path):
    clear_cache()
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "xdg"))
    yield
    clear_cache()


def _vault(tmp_path):
    paths, repository = build_retrieval_vault(tmp_path / "vault")
    report = backfill_embeddings(loaded(paths), caps=CAPS, recipes=("source_block",), registry=SOURCE_RETRIEVAL_RECIPES,
                                 client_factory=HashingEmbedder)
    assert report["status"] == "complete", report
    return paths, repository


def _search(paths, repository, **kwargs):
    clear_cache()
    return search_spans(loaded(paths), repository, QUERY, library_scope(repository), deep=True, rewrite=False,
                        embedder=HashingEmbedder(), pool="hybrid_rrf", **kwargs)


def _feedback(repository):
    with closing(sqlite3.connect(repository.sqlite_path)) as connection:
        return feedback_rows(connection)


def _fallback(paths, monkeypatch, client=None, extra=""):
    append_config_toml(paths.root, VOYAGE_PROFILE.replace("enabled = true", "enabled = true" + extra))
    client = client or FakeVoyageClient()
    monkeypatch.setattr(fallback_space, "fallback_client", lambda _vault: (client, None))
    return client


def test_with_the_new_switches_off_the_search_is_todays(tmp_path):
    paths, repository = _vault(tmp_path)
    result = _search(paths, repository)
    assert result.space_selection == {} and "space_selection" not in result.describe()
    assert "meaning" in result.lists and _feedback(repository) == []


def test_with_the_default_at_qwen_the_fallback_changes_nothing_served(tmp_path, monkeypatch):
    paths, repository = _vault(tmp_path)
    before = _search(paths, repository)
    hits_before = find_sources(loaded(paths), repository, QUERY, policy="reading", embedder=HashingEmbedder())
    client = _fallback(paths, monkeypatch)
    assert fallback_space.backfill_fallback_vectors(loaded(paths), repository, "ext_book", client=client)["status"] == "complete"
    after = _search(paths, repository)
    hits_after = find_sources(loaded(paths), repository, QUERY, policy="reading", embedder=HashingEmbedder())
    assert [(h.key, h.ranks, h.pool_role) for h in after.hits] == [(h.key, h.ranks, h.pool_role) for h in before.hits]
    assert after.fused_keys == before.fused_keys and after.lists == before.lists
    assert after.list_ends == before.list_ends and after.dense == before.dense
    assert json.dumps(hits_after.hits, sort_keys=True) == json.dumps(hits_before.hits, sort_keys=True)
    selection = after.space_selection
    assert selection["contributing"] == ["qwen"] and selection["weights"]["source"] == "seed"
    assert selection["spaces"]["voyage"]["status"] == "ok" and selection["spaces"]["voyage"]["assigned_sources"] == 0
    assert client.query_calls == []  # a zero-weight hosted space is never queried (never silently paid)


def test_the_fallback_serves_a_source_qwen_does_not_cover(tmp_path, monkeypatch):
    paths, repository = _vault(tmp_path)
    seed_source(repository, source_id="src_new", revision_id="rev_new", extraction_id="ext_new",
                title="Bases Notes", units=NEW_BOOK)
    client = _fallback(paths, monkeypatch)
    assert fallback_space.backfill_fallback_vectors(loaded(paths), repository, "ext_new", client=client)["status"] == "complete"
    result = search_spans(loaded(paths), repository, "what is a basis of a vector space", library_scope(repository),
                          deep=True, rewrite=False, embedder=HashingEmbedder(), pool="hybrid_rrf", consumer="library")
    meaning = [key for key in result.fused_keys if key[0] == "ext_new"]
    assert meaning and "meaning" in result.lists
    selection = result.space_selection
    assert selection["contributing"] == ["qwen", "voyage"] and selection["coverage"] == "ready"
    assert selection["spaces"]["voyage"]["assigned_sources"] == 1
    assert selection["spaces"]["voyage"]["query"]["paid"] is True and len(client.query_calls) == 1
    with closing(sqlite3.connect(paths.sqlite_path)) as connection:
        paid = connection.execute("SELECT COUNT(*) FROM model_call_receipts WHERE owner_kind = 'source_query_embedding' "
                                  "AND parent_call_id IS NULL").fetchone()[0]
    assert paid >= 2  # Qwen's query and Voyage's, each receipted
    # The space is part of every delivery receipt.
    rows = _feedback(repository)
    assert [row["event"] for row in rows].count("query") == 1 and rows[0]["consumer"] == "library"
    delivered = [row for row in rows if row["event"] == "delivered" and row["extraction_id"] == "ext_new"]
    assert delivered and all("voyage" in row["payload"]["space_ranks"] for row in delivered
                             if row["payload"]["space_ranks"])


def _local(tmp_path, paths, repository, monkeypatch, *, default=None):
    from learnloop.local_embeddings import pins

    root = pins.data_root()
    root.mkdir(parents=True, exist_ok=True)
    set_up_data_root(root)
    append_config_toml(paths.root, "[embedding.local]\nenabled = true\n" + (
        f"\n[embedding.source_space]\ndefault = \"{default}\"\n" if default else ""))
    model = FakeLocalModel()
    report = local_index.run_local_index(loaded(paths), repository, launcher=InProcessLauncher(model),
                                         preflight=lambda: [], locks=no_locks, force=True)
    assert report["status"] == "complete", report
    return model, report


class _Encoder:
    encoder_id = "qe_fake_teacher"

    def __init__(self, model):
        self.model = model

    def encode(self, texts, *, deadline=None):
        return [row[0] for row in self.model.encode_queries(list(texts))]


def test_the_local_space_reports_no_encoder_in_p1_and_serves_through_the_hook(tmp_path, monkeypatch):
    paths, repository = _vault(tmp_path)
    model, report = _local(tmp_path, paths, repository, monkeypatch, default="local:grouped")
    no_encoder = _search(paths, repository)
    local = no_encoder.space_selection["spaces"]["local:grouped"]
    assert local["status"] == "encoder_unavailable" and local["covered_sources"] == 2
    assert no_encoder.space_selection["contributing"] == ["qwen"]  # Qwen stands in (cheapest available)
    monkeypatch.setattr(spaces, "LOCAL_QUERY_ENCODER", lambda _vault: _Encoder(model))
    embedder = HashingEmbedder()
    clear_cache()
    served = search_spans(loaded(paths), repository, QUERY, library_scope(repository), deep=True, rewrite=False,
                          embedder=embedder, pool="hybrid_rrf")
    assert served.space_selection["contributing"] == ["local:grouped"] and "meaning" in served.lists
    assert served.space_selection["spaces"]["local:grouped"]["query"]["paid"] is False
    assert embedder.calls == []  # Qwen's zero-weight list is never queried
    with closing(sqlite3.connect(paths.sqlite_path)) as connection:
        set_space_status(connection, report["spaces"]["local:grouped"], "epoch_drift", reason="a canary moved")
        connection.commit()
    drifted = _search(paths, repository)
    assert drifted.space_selection["spaces"]["local:grouped"]["status"] == "epoch_drift"
    assert "local:grouped" not in drifted.space_selection["contributing"]


def test_signals_join_their_delivery_and_the_posterior_replays_byte_identically(tmp_path, monkeypatch):
    from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state

    paths, repository = _vault(tmp_path)
    _fallback(paths, monkeypatch)
    result = _search(paths, repository, owner_id="tq_1", consumer="tutor")
    receipt = result.space_selection["receipt_id"]
    first = result.hits[0]
    assert feedback.record_citations(repository, consumer="tutor", owner_id="tq_1",
                                     citations=[{"extraction_id": first.extraction_id, "span_id": first.span_id}]) == 1
    assert feedback.record_open(repository, receipt_id=receipt, extraction_id=first.extraction_id,
                                span_id=first.span_id)
    assert not feedback.record_open(repository, receipt_id=receipt, extraction_id="nope", span_id="none")
    events = [row["event"] for row in _feedback(repository)]
    assert events.count("cited") == 1 and events.count("opened") == 1
    report = fusion.refit_posteriors(loaded(paths), repository)
    assert report["written"] >= 1
    with closing(sqlite3.connect(paths.sqlite_path)) as connection:
        once = fusion_posteriors(connection)
    rebuild_all_derived_state(loaded(paths), repository)
    with closing(sqlite3.connect(paths.sqlite_path)) as connection:
        twice = fusion_posteriors(connection)
    assert once == twice and set(once) >= {"global"}


def test_the_seed_serves_while_the_learned_rule_is_only_logged(tmp_path, monkeypatch):
    paths, repository = _vault(tmp_path)
    client = _fallback(paths, monkeypatch)
    fallback_space.backfill_fallback_vectors(loaded(paths), repository, "ext_book", client=client)
    posterior = {"global": {"lists": list(fusion.SPACE_LISTS), "mean": [0.1, 0.0, 0.0, 5.0], "signals": 9,
                            "covariance": np.eye(4).tolist(), "context_key": "global"}}
    monkeypatch.setattr("learnloop.db.stores.retrieval_spaces.fusion_posteriors", lambda _c: posterior)
    logged = _search(paths, repository)
    weights = logged.space_selection["weights"]
    assert weights["source"] == "seed" and weights["served"]["qwen"] == 1.0
    assert weights["learned"]["voyage"] > weights["learned"]["qwen"]
    assert logged.space_selection["exploration"] == {}
    append_config_toml(paths.root, "[embedding.source_space]\nlearned_fusion = true\n")
    learned = _search(paths, repository)
    assert learned.space_selection["weights"]["source"] == "learned"
    assert learned.space_selection["contributing"] == ["qwen", "voyage"] and client.query_calls


def test_exploration_is_its_own_switch_and_logs_its_propensities(tmp_path, monkeypatch):
    paths, repository = _vault(tmp_path)
    _fallback(paths, monkeypatch, extra="\n\n[embedding.source_space]\nexploration = true")
    unsure = {"global": {"lists": list(fusion.SPACE_LISTS), "mean": [1.0, 0.0, 0.0, 0.0], "signals": 3,
                         "covariance": (np.eye(4) * 1e8).tolist(), "context_key": "global"}}
    monkeypatch.setattr("learnloop.db.stores.retrieval_spaces.fusion_posteriors", lambda _c: unsure)
    explored = _search(paths, repository)
    info = explored.space_selection["exploration"]
    assert info["explored"] and info["bands"] and info["seed"] == fusion.rng_seed(explored.space_selection["receipt_id"])
    assert explored.space_selection["weights"]["source"] == "seed"
    delivered = [row for row in _feedback(repository) if row["event"] == "delivered"]
    assert any(row["payload"]["propensity"] < 1.0 for row in delivered)
