from __future__ import annotations

from learnloop.db.repositories import Repository
from learnloop.content.synthesis.facet_candidates import harvest_facet_candidates
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


def test_harvests_candidates_from_unit_inventories(tmp_path):
    # KM §3.3 seam: once ING M4 inventory rows exist, harvesting reads their
    # claims/concept mentions as candidates (never canonical).
    from tests.test_source_inventory import (
        FakeInventoryClient,
        _block,
        _ir,
        _persist,
        _register_revision,
    )
    from learnloop.content.synthesis.source_unit_inventory import run_unit_inventory

    paths = create_basic_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    _register_revision(repository)
    ir = _ir([("u1", "Eigen", [_block("s1", "An eigenvector of A is a nonzero vector.")], "sha256:h1", 1)])
    _persist(repository, ir, revision_id="rev1", extraction_id="ext1")
    run_unit_inventory(repository, "ext1", "u1", role="primary_textbook", profile="semantic", client=FakeInventoryClient())

    result = harvest_facet_candidates(vault, repository)
    kinds = {candidate["source_kind"] for candidate in result["candidates"]}
    assert "unit_inventory" in kinds
    texts = {candidate["text"] for candidate in result["candidates"] if candidate["source_kind"] == "unit_inventory"}
    assert any("eigenvector" in text.lower() for text in texts)
