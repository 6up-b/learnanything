"""Slice 2 T5: embedding nominations for ingest and graph review.

Nominations only, never identity: these tests pin that embeddings shortlist and
the deciding model (or the owner) decides, that review passes never pay, that
every degraded path falls back to today's lexical behaviour with an honest
label, and that the kill switch restores the pre-T5 behaviour exactly.
"""

from __future__ import annotations

from contextlib import closing
import json

import numpy as np
import pytest

from learnloop.ai.spend import SpendCaps
from learnloop.content.synthesis.append_neighborhood import select_neighborhood
from learnloop.content.synthesis.facet_doctor import near_duplicate_facet_review
from learnloop.content.synthesis.facet_mint_gate import MintDisposition, judge_facet_mints
from learnloop.content.synthesis.graph_nomination import (
    CONCEPT_RECIPE,
    FACET_RECIPE,
    GraphNominator,
    annotate_mint_report,
    concept_query,
    facet_query,
    inventory_queries,
)
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.db.stores.embedding_vectors import (
    IncompleteEmbeddingIndex,
    current_vectors,
    get_vector_by_content,
    put_vector,
    retrieve,
)
from learnloop.ops.doctor import HealthIssue, _check_concept_merge_candidates, review_nominator
from learnloop.ops.embedding_backfill import backfill_embeddings
from learnloop.vault.embedding_recipes import (
    EMBEDDING_RECIPES,
    concept_definition_text,
    embedding_records,
    facet_definition_text,
)
from learnloop.vault.loader import load_vault
from learnloop.vault.models import Concept, EvidenceFacet

from tests.embedding_fakes import BagOfWordsEmbedder, ExplodingFactory
from tests.helpers import create_basic_vault

NOW = "2026-10-12T00:00:00+00:00"


def _facet(facet_id: str, claim: str, **fields) -> EvidenceFacet:
    return EvidenceFacet(id=facet_id, claim=claim, **fields)


@pytest.fixture
def vault(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    loaded = load_vault(paths.root)
    config = loaded.config
    config.embedding.enabled = True
    config.embedding.backfill_enabled = True
    config.embedding.dimensions = 64
    config.graph_nomination.top_k = 2
    loaded.evidence_facets.update({
        "facet_spectral": _facet(
            "facet_spectral", "Spectral theorem statement",
            preconditions=["the matrix is real and symmetric"],
            postconditions=["orthogonally diagonalizable"],
            instructional_repairs=["check symmetry before invoking the spectral theorem"],
            error_signatures=["applies the theorem to a non-symmetric matrix"],
        ),
        "facet_elimination": _facet(
            "facet_elimination", "Gaussian elimination reaches row echelon form",
            preconditions=["row operations preserve the solution set"],
            instructional_repairs=["practise one pivot at a time"],
        ),
        "facet_trace": _facet(
            "facet_trace", "The trace equals the sum of the eigenvalues",
            instructional_repairs=["compute the trace and the eigenvalue sum side by side"],
        ),
    })
    loaded.concepts.clear()
    loaded.concepts["concept_symmetric"] = Concept(
        title="Symmetric matrix", type="concept",
        description="A square matrix equal to its own transpose.",
        created_at=NOW, updated_at=NOW,
    )
    loaded.concepts["concept_elimination"] = Concept(
        title="Gaussian elimination", type="procedure",
        description="Row reduction of a linear system to echelon form.",
        created_at=NOW, updated_at=NOW,
    )
    return loaded, Repository(paths.sqlite_path), paths


def _backfill(loaded, embedder, recipes=(FACET_RECIPE, CONCEPT_RECIPE, "facet_repair/text")):
    report = backfill_embeddings(
        loaded, caps=SpendCaps(max_candidates=1000, max_total_tokens=10**7),
        recipes=recipes, client_factory=lambda: embedder,
    )
    assert report["status"] == "complete", report
    return report


# --- recipes and the store -------------------------------------------------


def test_concept_and_repair_recipes_embed_llm_written_definitions(vault):
    loaded, _repo, _paths = vault
    concept = loaded.concepts["concept_symmetric"]
    text = concept_definition_text(concept)
    assert "Description: A square matrix equal to its own transpose." in text
    assert "created_at" not in text and "concept_symmetric" not in text
    records = {(r.record_kind, r.record_id): r for r in embedding_records(loaded, (CONCEPT_RECIPE,))}
    assert set(records) == {("concept", "concept_symmetric"), ("concept", "concept_elimination")}
    repairs = embedding_records(loaded, ("facet_repair/text",))
    assert len(repairs) == 3 and len({r.record_id for r in repairs}) == 3
    # One text is one record, even when two facets prescribe it.
    loaded.evidence_facets["facet_trace"].instructional_repairs.append(
        "practise one pivot at a time"
    )
    assert len(embedding_records(loaded, ("facet_repair/text",))) == 3
    loaded.evidence_facets["facet_elimination"].status = "retired"
    loaded.evidence_facets["facet_trace"].instructional_repairs.pop()
    assert len(embedding_records(loaded, ("facet_repair/text",))) == 2


def test_candidate_payload_text_hashes_like_the_registry_record(vault):
    loaded, _repo, _paths = vault
    facet = loaded.evidence_facets["facet_spectral"]
    payload = facet.model_dump(mode="json")
    record = next(r for r in embedding_records(loaded, (FACET_RECIPE,)) if r.record_id == facet.id)
    assert facet_definition_text(payload) == record.text
    assert facet_query(payload).content_hash == record.content_hash
    concept = loaded.concepts["concept_symmetric"]
    synth_like = {"title": concept.title, "type": concept.type,
                  "description": concept.description, "aliases": []}
    stored = next(r for r in embedding_records(loaded, (CONCEPT_RECIPE,)) if r.record_id == "concept_symmetric")
    assert concept_query(synth_like, "client_c1").content_hash == stored.content_hash


def test_content_addressed_lookup_and_complete_index(vault):
    loaded, repo, _paths = vault
    recipe = EMBEDDING_RECIPES[FACET_RECIPE]
    records = list(recipe.records(loaded))
    manifest = {r.record_id: r.content_hash for r in records}
    with repo.connection() as connection:
        with pytest.raises(IncompleteEmbeddingIndex):
            current_vectors(connection, record_kind="facet", field="definition",
                            model_id="m", task_prefix="retrieval-document", expected_records=manifest)
        for index, record in enumerate(records):
            # Saved under a different record id (an ingest candidate's id).
            put_vector(connection, record_kind="facet", record_id=f"candidate_{index}",
                       field="definition", content_hash=record.content_hash, model_id="m",
                       task_prefix="retrieval-document", vector=[1.0 + index, 0.0, 1.0])
        found = current_vectors(connection, record_kind="facet", field="definition",
                                model_id="m", task_prefix="retrieval-document",
                                expected_records=manifest)
        assert set(found) == set(manifest)
        assert get_vector_by_content(connection, record_kind="facet", field="definition",
                                     content_hash=records[0].content_hash, model_id="m",
                                     task_prefix="retrieval-document") is not None
        assert get_vector_by_content(connection, record_kind="facet", field="definition",
                                     content_hash=records[0].content_hash, model_id="other",
                                     task_prefix="retrieval-document") is None


# --- the nominator ------------------------------------------------------------


def test_switches_return_no_nominator(vault):
    loaded, repo, _paths = vault
    loaded.config.graph_nomination.enabled = False
    assert GraphNominator.for_review(loaded) is None
    assert GraphNominator.for_ingest(loaded, repo) is None
    assert review_nominator(loaded) is None
    loaded.config.graph_nomination.enabled = True
    loaded.config.embedding.enabled = False
    assert GraphNominator.for_review(loaded) is None
    assert GraphNominator.for_ingest(loaded, repo) is None


def test_ranking_matches_phase_1_retrieval(vault):
    loaded, repo, _paths = vault
    embedder = BagOfWordsEmbedder()
    _backfill(loaded, embedder)
    nominator = GraphNominator.for_review(loaded)
    index = nominator.index(FACET_RECIPE)
    assert index is not None and len(index) == 3
    query = np.asarray(embedder.vector("a real symmetric matrix is orthogonally diagonalizable"))
    manifest = {r.record_id: r.content_hash for r in embedding_records(loaded, (FACET_RECIPE,))}
    with closing(connect(repo.sqlite_path, read_only=True)) as connection:
        expected = retrieve(connection, record_kind="facet", field="definition",
                            model_id=embedder.model_id, task_prefix="retrieval-document",
                            query=query, expected_records=manifest, limit=3)
    ours = index.nearest(query, 3)
    assert [m.record_id for m in expected] == [n.record_id for n in ours]
    assert [round(m.score, 6) for m in expected] == [round(n.cosine, 6) for n in ours]
    assert ours[0].record_id == "facet_spectral"


def test_review_mode_never_constructs_a_client(vault):
    loaded, _repo, _paths = vault
    _backfill(loaded, BagOfWordsEmbedder())
    nominator = GraphNominator(loaded, _paths.sqlite_path, allow_new_text=False,
                               client_factory=ExplodingFactory())
    query = facet_query({"claim": "never embedded before"}, "new")
    assert nominator.nominate(FACET_RECIPE, [query]) == {}
    summary = nominator.summary()
    assert summary["counts"]["calls"] == 0
    assert "review_uses_stored_vectors_only" in summary["notes"]


def test_incomplete_index_degrades_without_paying(vault):
    loaded, repo, _paths = vault
    factory = ExplodingFactory()
    nominator = GraphNominator.for_ingest(loaded, repo, client_factory=factory)
    assert nominator.nominate(FACET_RECIPE, [facet_query({"claim": "x"}, "new")]) == {}
    assert factory.calls == 0
    summary = nominator.summary()
    assert summary["status"] == "lexical_only"
    assert summary["indexes"] == {FACET_RECIPE: "index_incomplete"}


@pytest.mark.durability
def test_ingest_embeds_new_text_once_with_receipts(vault):
    loaded, repo, _paths = vault
    embedder = BagOfWordsEmbedder()
    _backfill(loaded, embedder)
    calls_after_backfill = len(embedder.calls)
    nominator = GraphNominator.for_ingest(loaded, repo, client_factory=lambda: embedder)
    query = facet_query({"claim": "real symmetric matrices are orthogonally diagonalizable"}, "cand")
    first = nominator.nominate(FACET_RECIPE, [query])
    assert first["cand"][0].record_id == "facet_spectral"
    assert len(embedder.calls) == calls_after_backfill + 1
    assert nominator.nominate(FACET_RECIPE, [query]) == first
    assert len(embedder.calls) == calls_after_backfill + 1  # in-run cache
    # A later run (or a revalidation) finds the paid vector by content.
    again = GraphNominator(loaded, repo.sqlite_path, allow_new_text=False)
    assert again.nominate(FACET_RECIPE, [facet_query(
        {"claim": "real symmetric matrices are orthogonally diagonalizable"}, "other_id",
    )])["other_id"][0].record_id == "facet_spectral"
    with repo.connection() as connection:
        row = connection.execute(
            "SELECT purpose,status,budget_json FROM model_call_receipts WHERE owner_kind='graph_nomination'"
        ).fetchone()
    assert tuple(row[:2]) == ("embedding", "completed")
    budget = json.loads(row[2])
    assert budget["graph_nomination"]["model_id"] == embedder.model_id
    assert budget["max_estimated_usd"] == loaded.config.graph_nomination.max_query_cost_usd


@pytest.mark.parametrize("case", ["unknown_price", "caps", "provider_down", "mismatch"])
def test_paid_path_failures_degrade_to_lexical(vault, case):
    loaded, repo, _paths = vault
    _backfill(loaded, BagOfWordsEmbedder())
    embedder = BagOfWordsEmbedder(fail=case == "provider_down")
    if case == "unknown_price":
        loaded.config.embedding.model = embedder.model_id = embedder.model = "vendor/unpriced-embedder"
    if case == "caps":
        loaded.config.graph_nomination.max_query_calls = 0
    if case == "mismatch":
        embedder.dims = 32
    nominator = GraphNominator.for_ingest(loaded, repo, client_factory=lambda: embedder)
    query = facet_query({"claim": "something new"}, "cand")
    if case == "unknown_price":
        # The registry is indexed under the backfilled model only.
        assert nominator.nominate(FACET_RECIPE, [query]) == {}
        assert nominator.summary()["indexes"][FACET_RECIPE] == "index_incomplete"
        assert nominator.vectors([query]) == {}
        assert "unknown_embedding_price" in nominator.summary()["notes"]
        assert embedder.calls == []
        return
    assert nominator.nominate(FACET_RECIPE, [query]) == {}
    notes = nominator.summary()["notes"]
    expected = {
        "caps": "query_caps_reached",
        "provider_down": "embedding_failed:AIProviderUnavailable",
        "mismatch": "embedding_client_mismatch",
    }[case]
    assert expected in notes
    if case in {"caps", "mismatch"}:
        assert embedder.calls == []


# --- append neighbourhood ---------------------------------------------------


_INVENTORY = [{
    "inventory": {
        "claims": [{"statement": "a real symmetric matrix is orthogonally diagonalizable"}],
        "concept_mentions": [{"name": "Gaussian elimination"}],
    },
}]


def test_append_neighbourhood_unions_embedding_nominations_after_lexical(vault):
    loaded, repo, _paths = vault
    embedder = BagOfWordsEmbedder()
    _backfill(loaded, embedder)
    baseline = select_neighborhood(loaded, repo, _INVENTORY, budget_tokens=10_000)
    assert "facet:facet_spectral" not in baseline.match_reasons  # lexically unmatched
    nominator = GraphNominator.for_ingest(loaded, repo, client_factory=lambda: embedder)
    nominated = select_neighborhood(loaded, repo, _INVENTORY, budget_tokens=10_000, nominator=nominator)
    reasons = nominated.match_reasons["facet:facet_spectral"]
    assert [r["kind"] for r in reasons] == ["embedding"]
    assert "rank 1" in reasons[0]["detail"]
    # Lexical matches keep their order and come first; embeddings only add.
    lexical_refs = list(baseline.match_reasons)
    assert list(nominated.match_reasons)[: len(lexical_refs)] == lexical_refs
    for ref in lexical_refs:
        assert nominated.match_reasons[ref][: len(baseline.match_reasons[ref])] == baseline.match_reasons[ref]
    assert nominated.as_manifest_record()["nomination"]["status"] == "active"
    assert "nomination" not in baseline.as_manifest_record()


def test_append_neighbourhood_without_vectors_is_the_lexical_selection(vault):
    loaded, repo, _paths = vault
    baseline = select_neighborhood(loaded, repo, _INVENTORY, budget_tokens=10_000)
    nominator = GraphNominator.for_ingest(loaded, repo, client_factory=ExplodingFactory())
    degraded = select_neighborhood(loaded, repo, _INVENTORY, budget_tokens=10_000, nominator=nominator)
    record = degraded.as_manifest_record()
    assert record.pop("nomination")["status"] == "lexical_only"
    assert record == baseline.as_manifest_record()
    assert degraded.as_context() == baseline.as_context()


def test_inventory_queries_are_deterministic_and_deduplicated():
    inventories = [
        {"inventory": {"claims": [{"statement": "B"}, {"statement": "A"}, {"statement": "B"}],
                       "concept_mentions": [{"name": "X", "aliases": ["x1"]}],
                       "procedure_signals": [{"contract": "do the thing"}]}},
    ]
    claims, concepts = inventory_queries(inventories)
    assert [q.text for q in claims] == ["Claim: B", "Claim: A", "Claim: do the thing"]
    assert [q.text for q in concepts] == ["Title: X\nAliases: x1"]
    assert claims == inventory_queries(inventories)[0]


# --- the D2 mint gate shadow ------------------------------------------------


def test_mint_shadow_never_changes_a_disposition(vault):
    """R1: an identical definition embedding alone never aliases a candidate."""

    loaded, repo, _paths = vault
    embedder = BagOfWordsEmbedder()
    _backfill(loaded, embedder)
    registered = [f.model_dump(mode="json") for f in loaded.evidence_facets.values()]
    twin = {
        **loaded.evidence_facets["facet_spectral"].model_dump(mode="json"),
        "id": "facet_spectral_twin",
        # Different (normalized) repair text and signatures: D2 mints it.
        "instructional_repairs": ["verify A equals its transpose before using the spectral theorem"],
        "error_signatures": ["forgets the realness condition"],
    }
    candidates = [twin]
    plain = judge_facet_mints(candidates, registered=registered)
    nominator = GraphNominator.for_ingest(loaded, repo, client_factory=lambda: embedder)
    record = annotate_mint_report(nominator, plain, candidates, registered)
    again = judge_facet_mints(candidates, registered=registered)
    assert [v.as_dict() for v in again.verdicts] == [v.as_dict() for v in plain.verdicts]
    entry = record["candidates"][0]
    top = entry["embedding_neighbours"][0]
    assert top["id"] == "facet_spectral" and top["registered"]
    assert top["cosine"] > 0.99  # identical definition text
    assert plain.verdicts[0].disposition is MintDisposition.MINT


def test_repair_shadow_reports_the_text_verdict_and_embedding_view(vault):
    loaded, repo, _paths = vault
    embedder = BagOfWordsEmbedder()
    _backfill(loaded, embedder)
    registered = [f.model_dump(mode="json") for f in loaded.evidence_facets.values()]
    candidate = {
        "id": "facet_spectral_paraphrase",
        "claim": "Spectral theorem statement",
        "error_signatures": ["applies the theorem to a non-symmetric matrix", "confuses orthogonal with symmetric"],
        # Same repair, reworded: the text test calls it distinct.
        "instructional_repairs": ["before invoking the spectral theorem check symmetry"],
    }
    report = judge_facet_mints([candidate], registered=registered)
    verdict = report.verdicts[0]
    assert verdict.neighbours and verdict.neighbours[0].facet_id == "facet_spectral"
    nominator = GraphNominator.for_ingest(loaded, repo, client_factory=lambda: embedder)
    shadows = annotate_mint_report(nominator, report, [candidate], registered)["candidates"][0]["repair_shadows"]
    shadow = next(s for s in shadows if s["neighbour_id"] == "facet_spectral")
    assert shadow["text_distinct_repair"] is True
    assert shadow["exclusive_repairs"] == 1
    assert shadow["min_best_cosine"] > 0.99  # same words, different order
    assert shadow["cosine_kind"] == "raw"


# --- review passes: the cosine column ----------------------------------------


def test_review_passes_gain_a_cosine_column(vault):
    loaded, _repo, _paths = vault
    loaded.evidence_facets["facet_spectral_copy"] = loaded.evidence_facets["facet_spectral"].model_copy(
        update={"id": "facet_spectral_copy"},
    )
    plain = [p.as_dict() for p in near_duplicate_facet_review(loaded)]
    assert plain and all("cosine" not in p for p in plain)
    nominator = review_nominator(loaded)
    # Before the backfill: honest about why there is no value.
    degraded = near_duplicate_facet_review(loaded, nominator=nominator)[0].as_dict()
    assert degraded["cosine"] is None and degraded["cosine_status"] == "index_incomplete"
    _backfill(loaded, BagOfWordsEmbedder())
    proposal = near_duplicate_facet_review(loaded, nominator=review_nominator(loaded))[0]
    assert proposal.as_dict()["cosine"] > 0.99
    assert "cosine" in proposal.reason and "jaccard" in proposal.reason

    loaded.concepts["concept_symmetric_copy"] = loaded.concepts["concept_symmetric"]
    issues: list[HealthIssue] = []
    _check_concept_merge_candidates(loaded, issues, review_nominator(loaded))
    details = next(i.details for i in issues if "concept_symmetric_copy" in i.message)
    assert details["cosine"] > 0.99 and "cosine=" in next(
        i.message for i in issues if "concept_symmetric_copy" in i.message
    )
    issues_off: list[HealthIssue] = []
    _check_concept_merge_candidates(loaded, issues_off, None)
    assert all("cosine" not in i.details for i in issues_off)


def test_synthesis_gate_and_facet_candidates_show_cosine_beside_jaccard(vault):
    from learnloop.content.synthesis.facet_candidates import harvest_facet_candidates
    from learnloop.content.synthesis.synthesis_gates import (
        GateContext, GateItem, GateProposal, _gate_near_duplicate_facets,
    )

    payload = {"claim": "A real symmetric matrix is orthogonally diagonalizable"}
    proposal = GateProposal(items=[
        GateItem(client_item_id="a", item_type="facet", entity_id="facet_a", payload=dict(payload)),
        GateItem(client_item_id="b", item_type="facet", entity_id="facet_b", payload=dict(payload)),
    ])
    plain = _gate_near_duplicate_facets(proposal, GateContext())
    assert "cosine" not in plain[0].message
    seen = []

    def cosine(left, right):
        seen.append((left, right))
        return 0.97

    with_column = _gate_near_duplicate_facets(proposal, GateContext(facet_cosine=cosine))
    assert with_column[0].message == plain[0].message.replace("(jaccard 1.00)", "(jaccard 1.00, cosine 0.97)")
    assert seen == [(payload, payload)]
    assert [d.severity for d in with_column] == [d.severity for d in plain]  # display only

    loaded, _repo, _paths = vault
    loaded.evidence_facets["facet_spectral_copy"] = loaded.evidence_facets["facet_spectral"].model_copy(
        update={"id": "facet_spectral_copy", "claim": "Spectral theorem statement restated"},
    )
    _backfill(loaded, BagOfWordsEmbedder())
    off = harvest_facet_candidates(loaded)
    on = harvest_facet_candidates(loaded, nominator=review_nominator(loaded))
    assert all("cosine" not in pair for pair in off["review_pairs"])
    registry_pairs = [
        pair for pair in on["review_pairs"]
        if {pair["left"], pair["right"]} <= {c["candidate_id"] for c in on["candidates"] if c["source_kind"] == "registry"}
    ]
    assert registry_pairs and all(pair["cosine"] is not None for pair in registry_pairs)
