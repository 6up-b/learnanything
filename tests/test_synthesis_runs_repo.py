from __future__ import annotations

from learnloop.db.repositories import Repository
from learnloop.services.patches import apply_accepted_items
from learnloop.services.synthesis_manifests import build_manifest
from learnloop.services.synthesis_manifests import persist_manifest
from learnloop.vault.loader import load_vault

from tests.helpers import NOW_ISO, create_basic_vault
from tests.test_apply_write_ahead import _seed_lo_and_pi_proposal, LO_ID


def test_synthesis_run_lifecycle(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    repository = Repository(paths.sqlite_path)
    vault = load_vault(paths.root)

    manifest = build_manifest(vault, source_set_id="ss1", revision_ids=["rev_1"])
    manifest_id = persist_manifest(repository, manifest)

    run_id = repository.insert_synthesis_run(manifest_id=manifest_id, mode="bootstrap")
    created = repository.synthesis_run(run_id)
    assert created["status"] == "created"
    assert created["manifest_id"] == manifest_id

    repository.complete_synthesis_run(
        run_id,
        status="completed",
        proposal_id="patch_x",
        resolved_span_hashes=["sha256:a"],
        actual_usage={"input": 10, "output": 5},
    )
    done = repository.synthesis_run(run_id)
    assert done["status"] == "completed"
    assert done["proposal_id"] == "patch_x"
    assert done["resolved_span_hashes"] == ["sha256:a"]
    assert done["actual_usage"] == {"input": 10, "output": 5}
    assert done["completed_at"] is not None


def test_synthesis_run_introducing_entity_lineage(tmp_path):
    """patch -> agent run -> manifest lineage resolves for a created entity (§9.2)."""

    paths = create_basic_vault(tmp_path / "vault")
    repository = Repository(paths.sqlite_path)
    _seed_lo_and_pi_proposal(repository, "patch_syn")

    # A synthesis run whose proposal_id is the patch that introduced the LO.
    vault = load_vault(paths.root)
    manifest_id = persist_manifest(repository, build_manifest(vault, source_set_id="ss1"))
    repository.insert_synthesis_run(
        manifest_id=manifest_id, mode="bootstrap", proposal_id="patch_syn"
    )

    apply_accepted_items(paths.root, "patch_syn")

    run = repository.synthesis_run_introducing_entity("learning_object", LO_ID)
    assert run is not None
    assert run["proposal_id"] == "patch_syn"
    manifest = repository.synthesis_manifest(run["manifest_id"])
    assert manifest["manifest_hash"]


def test_notation_and_conflict_accessors(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    repository = Repository(paths.sqlite_path)

    repository.insert_notation_mapping(
        entity_type="facet",
        entity_id="f1",
        canonical_notation="det(A)",
        alternate_notation="|A|",
        status="active",
    )
    mappings = repository.notation_mappings_for_entity("facet", "f1")
    assert len(mappings) == 1 and mappings[0]["status"] == "active"

    conflict_id = repository.insert_source_conflict(
        entity_type="facet",
        entity_id="f1",
        statement="disagreement",
        resolution={"decision": "keep_both"},
    )
    conflicts = repository.source_conflicts_for_entity("facet", "f1")
    assert len(conflicts) == 1
    assert conflicts[0]["id"] == conflict_id
    assert conflicts[0]["status"] == "open"
    assert conflicts[0]["resolution"] == {"decision": "keep_both"}
