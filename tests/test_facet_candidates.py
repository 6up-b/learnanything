from __future__ import annotations

from learnloop.db.repositories import Repository
from learnloop.services.facet_candidates import harvest_facet_candidates
from learnloop.vault.loader import load_vault

from tests.helpers import create_basic_vault


def test_harvests_candidates_from_multiple_sources(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    result = harvest_facet_candidates(vault, repository)
    kinds = {candidate["source_kind"] for candidate in result["candidates"]}
    # LO summary, rubric criterion, and fatal error are all present in the basic vault.
    assert {"lo_summary", "rubric_criterion", "fatal_error"} <= kinds
    for candidate in result["candidates"]:
        assert candidate["suggested_facet_id"].startswith("facet_")


def test_similarity_pair_is_review_proposal_only(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    # Two near-identical LO summaries should surface a review pair, never a merge.
    vault.learning_objects["lo_svd_definition"].summary = "the spectral theorem applies to symmetric matrices"
    from learnloop.vault.models import LearningObject

    clone = vault.learning_objects["lo_svd_definition"].model_copy(
        update={"id": "lo_clone", "summary": "the spectral theorem applies to symmetric matrices here"}
    )
    vault.learning_objects["lo_clone"] = clone

    result = harvest_facet_candidates(vault)
    assert result["review_pairs"], "expected at least one lexical review pair"
    pair = result["review_pairs"][0]
    assert 0.0 <= pair["similarity"] <= 1.0
    # A pair is a review proposal only, never a merge (§3.3).
    assert pair["reason"] == "lexical_similarity_review_only"
    assert "no pair is a merge" in result["notes"]


def test_harvest_is_deterministic(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    first = harvest_facet_candidates(vault)
    second = harvest_facet_candidates(vault)
    assert first == second
