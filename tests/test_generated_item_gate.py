from __future__ import annotations

import pytest

from learnloop.services.patches import PatchApplicationError, compile_proposal_item
from learnloop.vault.loader import load_vault

from tests.helpers import create_basic_vault, set_algorithm_version, write_facets


def _practice_item_proposal(facet: str) -> dict:
    return {
        "id": "ppi_new",
        "item_type": "practice_item",
        "operation": "create",
        "target_entity_id": "pi_generated_001",
        "payload": {
            "id": "pi_generated_001",
            "learning_object_id": "lo_svd_definition",
            "practice_mode": "short_answer",
            "attempt_types_allowed": ["independent_attempt"],
            "evidence_facets": [facet],
            "evidence_weights": {facet: 1.0},
            "prompt": "Define SVD again.",
            "expected_answer": "A factorization into U, Sigma, V^T.",
        },
    }


def test_unregistered_facet_rejected(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    set_algorithm_version(paths, "mvp-0.7")
    write_facets(
        paths,
        [{"id": "recall", "kind": "definition", "claim": "SVD factorization definition."}],
    )
    vault = load_vault(paths.root)
    with pytest.raises(PatchApplicationError) as exc:
        compile_proposal_item(vault, _practice_item_proposal("facet_not_registered"))
    assert "unregistered" in str(exc.value)


def test_registered_facet_accepted(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    set_algorithm_version(paths, "mvp-0.7")
    write_facets(
        paths,
        [{"id": "recall", "kind": "definition", "claim": "SVD factorization definition."}],
    )
    vault = load_vault(paths.root)
    compiled = compile_proposal_item(vault, _practice_item_proposal("recall"))
    assert compiled.entity_id == "pi_generated_001"


def test_legacy_vault_allows_unregistered_facet(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")  # mvp-0.6 default
    write_facets(
        paths,
        [{"id": "recall", "title": "Recall"}],
        schema_version=1,
    )
    vault = load_vault(paths.root)
    # Legacy generation is not gated (doctor warns instead); compile succeeds.
    compiled = compile_proposal_item(vault, _practice_item_proposal("facet_not_registered"))
    assert compiled.entity_id == "pi_generated_001"
