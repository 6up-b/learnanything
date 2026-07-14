from __future__ import annotations

from learnloop.db.repositories import Repository
from learnloop.services.synthesis_manifests import (
    agent_run_input_context_hash,
    build_manifest,
    persist_manifest,
)
from learnloop.vault.loader import load_vault

from tests.helpers import create_basic_vault


def _manifest(vault, **overrides):
    kwargs = dict(
        source_set_id="sourceset_la",
        membership=[{"source_id": "src_axler", "revision_id": "rev_1", "role": "primary_textbook"}],
        revision_ids=["rev_1"],
        asset_hashes=["sha256:abc"],
        extraction_ids=["ext_1"],
        unit_inventory_versions={"chapter_02": "inv_v1"},
        scope={"units": ["chapter_02"]},
        brief={"level": "intro", "depth": "standard"},
        prompt_version="synthesis-v1",
        provider="codex",
        model="gpt-5",
        token_budget={"input": 100000, "output": 20000},
    )
    kwargs.update(overrides)
    return build_manifest(vault, **kwargs)


def test_manifest_idempotency_identical_inputs_same_hash(tmp_path):
    """§14: identical complete manifest -> same hash; any input change -> new hash."""

    vault = load_vault(create_basic_vault(tmp_path / "vault").root)

    first = _manifest(vault)
    second = _manifest(vault)
    assert first["manifest_hash"] == second["manifest_hash"]

    # The completeness fields (§12.4) are populated and part of identity.
    assert first["curriculum_snapshot_hash"]
    assert first["facet_registry_hash"]
    assert first["task_graph_hash"]
    assert first["learner_model_contract_version"] == vault.config.algorithms.algorithm_version

    # Any input change mints a new manifest hash.
    assert _manifest(vault, revision_ids=["rev_2"])["manifest_hash"] != first["manifest_hash"]
    assert _manifest(vault, scope={"units": ["chapter_03"]})["manifest_hash"] != first["manifest_hash"]
    assert _manifest(vault, brief={"level": "advanced"})["manifest_hash"] != first["manifest_hash"]
    assert (
        _manifest(vault, unit_inventory_versions={"chapter_02": "inv_v2"})["manifest_hash"]
        != first["manifest_hash"]
    )
    assert (
        _manifest(vault, token_budget={"input": 1, "output": 1})["manifest_hash"]
        != first["manifest_hash"]
    )


def test_curriculum_change_changes_manifest_hash(tmp_path):
    """A curriculum snapshot change (new registered facet) mints a new hash."""

    paths = create_basic_vault(tmp_path / "vault")
    vault_root = paths.root
    vault = load_vault(vault_root)
    before = _manifest(vault)["manifest_hash"]

    from learnloop.vault.yaml_io import read_yaml, write_yaml

    data = read_yaml(paths.facets_path)
    data.setdefault("facets", []).append(
        {"id": "facet_new_atom", "title": "New atom", "status": "reviewed"}
    )
    write_yaml(paths.facets_path, data)

    after = _manifest(load_vault(vault_root))["manifest_hash"]
    assert after != before


def test_persist_manifest_is_idempotent_and_seam_documented(tmp_path):
    vault_root = create_basic_vault(tmp_path / "vault")
    vault = load_vault(vault_root.root)
    repository = Repository(vault_root.sqlite_path)

    manifest = _manifest(vault)
    first_id = persist_manifest(repository, manifest)
    second_id = persist_manifest(repository, manifest)
    assert first_id == second_id  # identical manifest reuses the row (cache seam)

    stored = repository.synthesis_manifest_by_hash(manifest["manifest_hash"])
    assert stored is not None
    assert stored["revision_ids"] == ["rev_1"]

    # The documented seam: agent_runs.input_context_hash = manifest_hash.
    assert agent_run_input_context_hash(manifest) == manifest["manifest_hash"]
