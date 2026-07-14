from __future__ import annotations

from learnloop.vault.facet_fingerprint import normalized_contract, semantic_fingerprint
from learnloop.vault.loader import load_vault
from learnloop.vault.models import EvidenceFacet
from learnloop.vault.yaml_io import write_yaml

from tests.helpers import NOW_ISO, create_basic_vault
from learnloop.vault.paths import VaultPaths


def _write_facets(paths: VaultPaths, facets: list[dict], *, schema_version: int = 2) -> None:
    write_yaml(paths.facets_path, {"schema_version": schema_version, "facets": facets})


def test_v1_registry_loads_unchanged(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    _write_facets(
        paths,
        [{"id": "recall", "title": "Recall", "aliases": ["recall_svd"]}],
        schema_version=1,
    )
    vault = load_vault(paths.root)
    facet = vault.evidence_facets["recall"]
    assert facet.title == "Recall"
    assert facet.aliases == ["recall_svd"]
    # v2 fields default cleanly; a fingerprint is computed at load.
    assert facet.kind is None
    assert facet.claim is None
    assert facet.semantic_fingerprint is not None


def test_semantic_fingerprint_deterministic_and_ignores_naming():
    base = EvidenceFacet(
        id="facet_matrix_symmetry_definition",
        kind="definition",
        claim="A real square matrix is symmetric exactly when A^T = A.",
        preconditions=["the matrix is real and square"],
        negative_examples=["an orthogonal rotation matrix that is not symmetric"],
    )
    # Same contract, different naming/lifecycle metadata -> same fingerprint.
    renamed = base.model_copy(
        update={
            "id": "facet_other_id",
            "title": "Symmetry",
            "aliases": ["symmetry definition"],
            "status": "proposed",
            "version": 7,
        }
    )
    assert semantic_fingerprint(base) == semantic_fingerprint(renamed)

    # Reordering list entries does not change identity (order is not semantic).
    reordered = base.model_copy(update={"preconditions": list(reversed(base.preconditions))})
    assert semantic_fingerprint(base) == semantic_fingerprint(reordered)

    # A different claim changes the fingerprint.
    changed = base.model_copy(update={"claim": "A matrix is orthogonal when A^T A = I."})
    assert semantic_fingerprint(base) != semantic_fingerprint(changed)


def test_fingerprint_normalization_collapses_whitespace_and_case():
    left = normalized_contract({"kind": "Definition", "claim": "A  matrix   is Symmetric."})
    right = normalized_contract({"kind": "definition", "claim": "a matrix is symmetric."})
    assert left == right


def test_rename_alias_preserves_identity(tmp_path):
    """A rename via the alias path resolves history to the same facet id (§3.4)."""

    paths = create_basic_vault(tmp_path / "vault")
    _write_facets(
        paths,
        [
            {
                "id": "facet_svd_definition",
                "kind": "definition",
                "claim": "SVD factorizes a matrix into U, Sigma, V^T.",
                # The item declares the old name "recall"; the rename records it
                # as an alias so the item's evidence still resolves canonically.
                "aliases": ["recall"],
            }
        ],
    )
    vault = load_vault(paths.root)
    assert vault.canonical_facet_id("recall") == "facet_svd_definition"
    item = vault.practice_items["pi_svd_define_001"]
    # Loader canonicalizes the item's evidence facets through the alias map.
    assert item.evidence_facets == ["facet_svd_definition"]
