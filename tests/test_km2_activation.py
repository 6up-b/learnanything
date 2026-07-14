"""KM2 item 9 — atomic mvp-0.7 activation and mixed-version guards."""

from __future__ import annotations

from learnloop.services.vault_upgrade import (
    KM_ALGORITHM_VERSION,
    upgrade_to_mvp07,
    validate_mvp07_readiness,
)
from learnloop.vault.loader import load_vault
from learnloop.vault.yaml_io import write_yaml

from tests.helpers import create_basic_vault, set_algorithm_version, write_facets


def test_upgrade_refuses_when_facets_unregistered(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    # pi_svd_define_001 declares facet 'recall' but the registry is empty.
    result = upgrade_to_mvp07(paths.root)
    assert result.upgraded is False
    assert any("recall" in p for p in result.problems)
    # The version field was NOT flipped.
    assert load_vault(paths.root).config.algorithms.algorithm_version == "mvp-0.6"


def test_upgrade_succeeds_when_registry_complete(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    write_facets(
        paths,
        [{"id": "recall", "kind": "definition", "claim": "SVD recall definition."}],
    )
    result = upgrade_to_mvp07(paths.root)
    assert result.upgraded is True
    assert result.to_version == KM_ALGORITHM_VERSION
    assert load_vault(paths.root).config.algorithms.algorithm_version == KM_ALGORITHM_VERSION


def test_upgrade_is_idempotent(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    write_facets(
        paths,
        [{"id": "recall", "kind": "definition", "claim": "SVD recall definition."}],
    )
    upgrade_to_mvp07(paths.root)
    second = upgrade_to_mvp07(paths.root)
    assert second.upgraded is False
    assert "already mvp-0.7" in " ".join(second.problems)


def test_upgrade_refuses_from_unknown_version(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    write_facets(
        paths,
        [{"id": "recall", "kind": "definition", "claim": "SVD recall definition."}],
    )
    set_algorithm_version(paths, "mvp-0.5")
    result = upgrade_to_mvp07(paths.root)
    assert result.upgraded is False
    assert any("mvp-0.5" in p for p in result.problems)


def test_validate_readiness_flags_incomplete_contract(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    # Registered id but no claim/kind -> incomplete semantic contract.
    write_yaml(paths.facets_path, {"schema_version": 2, "facets": [{"id": "recall"}]})
    problems = validate_mvp07_readiness(load_vault(paths.root))
    assert any("incomplete semantic contract" in p for p in problems)
