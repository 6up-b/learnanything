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
    # The space (its identity) is part of every delivery receipt; the
    # consumer's boundary writes the deliveries (Codex review F9).
    rows = _feedback(repository)
    assert [row["event"] for row in rows] == ["query"] and rows[0]["consumer"] == "library"
    feedback.deliver(loaded(paths), repository, result, [hit.key for hit in result.hits])
    rows = _feedback(repository)
    voyage = selection["spaces"]["voyage"]["list"]
    assert voyage.startswith("voyage@hs_")
    delivered = [row for row in rows if row["event"] == "delivered" and row["extraction_id"] == "ext_new"]
    assert delivered and all(voyage in row["payload"]["space_ranks"] for row in delivered
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
    feedback.deliver(loaded(paths), repository, result, [hit.key for hit in result.hits[:3]])
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


def test_the_tutor_citation_hook_does_nothing_with_the_switches_off_and_joins_its_delivery_when_on(
        tmp_path, monkeypatch):
    from learnloop.tutor import tutor_qa

    paths, repository = _vault(tmp_path)

    touched: list[str] = []

    class _Watched:
        def connection(self):  # the off path must not even read (the hook swallows errors, so record)
            touched.append("connection")
            return repository.connection()

    context = {"source_retrieval": {"owner_id": "tq_7"}}
    tutor_qa._record_retrieval_citations(loaded(paths), _Watched(), context,
                                         [{"extraction_id": "ext_book", "span_id": "any"}])
    assert touched == []
    _fallback(paths, monkeypatch)
    searched = _search(paths, repository, owner_id="tq_7", consumer="tutor")
    first = searched.hits[0]
    feedback.deliver(loaded(paths), repository, searched, [first.key])
    tutor_qa._record_retrieval_citations(loaded(paths), repository, context,
                                         [{"extraction_id": first.extraction_id, "span_id": first.span_id}])
    cited = [row for row in _feedback(repository) if row["event"] == "cited"]
    assert [(row["owner_id"], row["span_id"]) for row in cited] == [("tq_7", first.span_id)]


def _identities(paths, repository):
    selection = _search(paths, repository).space_selection
    return {name: row["list"] for name, row in selection["spaces"].items()}


def test_the_seed_serves_while_the_learned_rule_is_only_logged(tmp_path, monkeypatch):
    paths, repository = _vault(tmp_path)
    client = _fallback(paths, monkeypatch)
    fallback_space.backfill_fallback_vectors(loaded(paths), repository, "ext_book", client=client)
    ids = _identities(paths, repository)
    posterior = {"global": {"lists": [ids["qwen"], ids["voyage"]], "mean": [0.1, 5.0], "signals": 9,
                            "covariance": (np.eye(2) * 0.01).tolist(), "context_key": "global", "rrf_k": 15.0}}
    monkeypatch.setattr("learnloop.db.stores.retrieval_spaces.fusion_posteriors", lambda _c: posterior)
    logged = _search(paths, repository)
    weights = logged.space_selection["weights"]
    assert weights["source"] == "seed" and weights["served"]["qwen"] == 1.0
    assert weights["learned"]["voyage"] > weights["learned"]["qwen"]
    assert logged.space_selection["rrf_k"] == 60.0  # the seed serves at the configured rrf_k
    assert logged.space_selection["exploration"] == {}
    append_config_toml(paths.root, "[embedding.source_space]\nlearned_fusion = true\n")
    learned = _search(paths, repository)
    selection = learned.space_selection
    assert selection["weights"]["source"] == "learned"
    assert "voyage" in selection["contributing"] and client.query_calls
    # Codex review F14: the posterior's rrf_k serves with its coefficients.
    assert selection["rrf_k"] == 15.0
    # Codex review F7: a Thompson draw, its query propensities logged.
    propensity = selection["weights"]["query_propensity"]
    assert propensity[ids["voyage"]] > 0.99 and 0.5 < propensity[ids["qwen"]] < 1.0


def test_a_successor_space_never_inherits_its_predecessors_weights(tmp_path, monkeypatch):
    """Codex review F12: a posterior learned for one Voyage model is not the
    posterior of another: the new space is a new list, at its own prior."""

    paths, repository = _vault(tmp_path)
    client = _fallback(paths, monkeypatch)
    fallback_space.backfill_fallback_vectors(loaded(paths), repository, "ext_book", client=client)
    ids = _identities(paths, repository)
    old_voyage = ids["voyage"].replace("voyage@hs_", "voyage@hs_old")
    posterior = {"global": {"lists": [ids["qwen"], old_voyage], "mean": [0.0, 9.0], "signals": 9,
                            "covariance": (np.eye(2) * 1e-6).tolist(), "context_key": "global", "rrf_k": 60.0}}
    monkeypatch.setattr("learnloop.db.stores.retrieval_spaces.fusion_posteriors", lambda _c: posterior)
    weights = _search(paths, repository).space_selection["weights"]
    assert weights["learned"] is None  # the old space's coefficient is not this space's
    rows = fusion.refit([
        {"id": "q", "receipt_id": "r", "event": "query", "consumer": "library", "query_kind": "lookup",
         "extraction_id": None, "span_id": None, "position": None, "created_at": "t",
         "payload": {"lists_available": [ids["qwen"], ids["voyage"]], "queried": [ids["qwen"]]}},
        {"id": "d", "receipt_id": "r", "event": "delivered", "consumer": "library", "query_kind": "lookup",
         "extraction_id": "ext_book", "span_id": "s2", "position": 1, "created_at": "t",
         "payload": {"space_ranks": {ids["qwen"]: 1}}},
    ], default="qwen", rrf_k_seed=60.0)
    assert rows and rows[0]["lists"] == [ids["qwen"], ids["voyage"]]


def test_exploration_is_its_own_switch_and_logs_its_delivered_propensities(tmp_path, monkeypatch):
    paths, repository = _vault(tmp_path)
    _fallback(paths, monkeypatch, extra="\n\n[embedding.source_space]\nexploration = true")
    ids = _identities(paths, repository)
    unsure = {"global": {"lists": [ids["qwen"]], "mean": [1.0], "signals": 3, "rrf_k": 60.0,
                         "covariance": [[1e8]], "context_key": "global"}}
    monkeypatch.setattr("learnloop.db.stores.retrieval_spaces.fusion_posteriors", lambda _c: unsure)
    explored = _search(paths, repository)
    assert explored.space_selection["weights"]["source"] == "seed"
    keys = [hit.key for hit in explored.hits[:6]]
    order = feedback.deliver(loaded(paths), repository, explored, keys)
    assert sorted(order) == list(range(len(keys)))
    info = explored.resolution.exploration
    assert info["explored"] and info["bands"]
    assert info["seed"] == fusion.rng_seed(explored.space_selection["receipt_id"] + ":delivered")
    delivered = [row for row in _feedback(repository) if row["event"] == "delivered"]
    assert [(row["extraction_id"], row["span_id"]) for row in delivered] == [keys[index] for index in order]
    assert [row["position"] for row in delivered] == list(range(1, len(keys) + 1))
    assert any(row["payload"]["propensity"] < 1.0 for row in delivered)
    assert all(row["payload"]["explored"] for row in delivered)


def test_the_fallback_query_spends_from_the_callers_budget_and_is_planned(tmp_path, monkeypatch):
    """Codex review F2: a Voyage query is admitted against the caller's budget
    (a zero budget sends nothing) and the dry run plans it."""

    from learnloop.ai.spend import SpendBudget
    from learnloop.source_retrieval.library import deep_search_caps, plan_library_search

    paths, repository = _vault(tmp_path)
    seed_source(repository, source_id="src_new", revision_id="rev_new", extraction_id="ext_new",
                title="Bases Notes", units=NEW_BOOK)
    client = _fallback(paths, monkeypatch)
    assert fallback_space.backfill_fallback_vectors(loaded(paths), repository, "ext_new", client=client)["status"] == "complete"
    question = "what is a basis of a vector space"
    zero = SpendBudget(deep_search_caps(max_calls=0, max_tokens=0, max_cost_usd=0.0))
    clear_cache()
    result = search_spans(loaded(paths), repository, question, library_scope(repository), deep=True, rewrite=False,
                          embedder=HashingEmbedder(), pool="hybrid_rrf", consumer="library", budget=zero)
    assert client.query_calls == [] and zero.used.calls == 0
    assert result.space_selection["spaces"]["voyage"]["query"]["status"] == "over_budget"
    roomy = SpendBudget(deep_search_caps(max_calls=5, max_tokens=50_000, max_cost_usd=0.05))
    clear_cache()
    result = search_spans(loaded(paths), repository, question, library_scope(repository), deep=True, rewrite=False,
                          embedder=HashingEmbedder(), pool="hybrid_rrf", consumer="library", budget=roomy)
    assert len(client.query_calls) == 1 and roomy.used.calls == 2  # Qwen's query and Voyage's, one budget
    assert result.space_selection["spaces"]["voyage"]["query"]["charged"]["calls"] == 1
    plan = plan_library_search(loaded(paths), repository, query="a new question about bases", deep=True)
    fallback = plan["fallback_query_embedding"]
    assert fallback["calls"] == 1 and fallback["estimated_usd"] > 0
    assert plan["calls"] >= 1 + plan["query_embedding"]["calls"]


class _DownEmbedder(HashingEmbedder):
    def embed(self, inputs, task_prefix):
        from learnloop.ai.errors import AIProviderUnavailable

        raise AIProviderUnavailable("the embedding provider is down")


def test_a_failed_query_hands_its_sources_to_an_available_fallback(tmp_path, monkeypatch):
    """Codex review F6: Qwen and Voyage both cover the book; Qwen holds the
    weight, but its query fails. Voyage answers for it, and coverage counts
    only what an answered query covers."""

    paths, repository = _vault(tmp_path)
    client = _fallback(paths, monkeypatch)
    fallback_space.backfill_fallback_vectors(loaded(paths), repository, "ext_book", client=client)
    clear_cache()
    result = search_spans(loaded(paths), repository, QUERY, library_scope(repository), deep=True, rewrite=False,
                          embedder=_DownEmbedder(), pool="hybrid_rrf", consumer="library")
    selection = result.space_selection
    assert selection["spaces"]["qwen"]["status"] == "encoder_unavailable"
    assert selection["contributing"] == ["qwen", "voyage"] and len(client.query_calls) == 1
    assert "meaning" in result.lists and any(key[0] == "ext_book" for key in result.fused_keys)
    assert selection["coverage"] in ("ready", "partial")
    # With no fallback available, the same failure reports no meaning coverage.
    paths2, repository2 = _vault(tmp_path / "two")
    clear_cache()
    alone = search_spans(loaded(paths2), repository2, QUERY, library_scope(repository2), deep=True, rewrite=False,
                         embedder=HashingEmbedder(), pool="hybrid_rrf", consumer="library")
    assert alone.space_selection == {}  # (resolver off: today's path)


def test_a_challenger_learns_its_way_up_from_resolver_receipts(tmp_path, monkeypatch):
    """Codex review F7, through the production path: Qwen covers everything and
    is the default; Voyage starts at zero weight. With learned fusion on, the
    Thompson draws query Voyage some of the time, its ranks are observed, the
    learner opens what Voyage ranks first, and the refit raises Voyage's
    weight. No rank or posterior is injected: every row is the resolver's."""

    paths, repository = _vault(tmp_path)
    client = _fallback(paths, monkeypatch, extra="\n\n[embedding.source_space]\nlearned_fusion = true")
    fallback_space.backfill_fallback_vectors(loaded(paths), repository, "ext_book", client=client)
    from learnloop.source_retrieval.library import search_library

    questions = ["eigenvalues of symmetric matrices", "determinant row swap sign", "orthogonal vectors basis",
                 "characteristic polynomial roots", "cofactor expansion along a row", "projection onto a unit vector",
                 "invertible matrix determinant", "eigenvectors span eigenspaces", "dot product zero",
                 "linearly independent orthogonal"]
    voyage_queried = 0
    rng = np.random.default_rng(5)
    for round_index in range(4):
        for question in questions:
            clear_cache()
            vault = loaded(paths)
            response = search_library(vault, repository, query=f"{question} {round_index}", deep=True,
                                      embedder=HashingEmbedder())
            selection = response["retrieval"]["space_selection"]
            voyage_queried += int("voyage" in selection["contributing"])
            voyage_key = selection["spaces"]["voyage"]["list"]
            rows = [row for row in _feedback(repository) if row["receipt_id"] == selection["receipt_id"]
                    and row["event"] == "delivered"]
            # The learner examines result p with probability 1/p and opens it more
            # often when Voyage (the better space here) ranked it near the top.
            opened = [row for row in rows if rng.random() < (1.0 / row["position"]) * (
                0.9 if row["payload"]["space_ranks"].get(voyage_key, 99) <= 2 else 0.15)]
            for row in opened:
                feedback.record_open(repository, receipt_id=selection["receipt_id"],
                                     extraction_id=row["extraction_id"], span_id=row["span_id"])
        fusion.refit_posteriors(loaded(paths), repository)
    with closing(sqlite3.connect(paths.sqlite_path)) as connection:
        posteriors = fusion_posteriors(connection)
    learned = fusion.learned_weights(posteriors["global"], posteriors["global"]["lists"])
    assert voyage_queried > 0  # the draw explored the challenger
    assert learned is not None and learned[voyage_key] > 0.0, posteriors["global"]
