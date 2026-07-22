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

    repository.save_synthesis_candidate(run_id, {"concepts": [{"client_item_id": "c1"}]})
    staged = repository.synthesis_run(run_id)
    assert staged["candidate_output"] == {"concepts": [{"client_item_id": "c1"}]}

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


def test_synthesis_shard_result_roundtrip_and_upsert(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    repository = Repository(paths.sqlite_path)

    assert repository.synthesis_shard_result("shard:missing") is None
    repository.save_synthesis_shard_result(
        shard_key="shard:abc",
        shard_ordinal=1,
        shard_count=3,
        manifest_hash="sha256:m1",
        result={"result": {"summary": "s"}, "span_request_count": 2,
                "resolved_span_hashes": ["sha256:a"]},
    )
    row = repository.synthesis_shard_result("shard:abc")
    assert row["shard_ordinal"] == 1
    assert row["shard_count"] == 3
    assert row["manifest_hash"] == "sha256:m1"
    assert row["output"]["span_request_count"] == 2

    # Re-saving the same key replaces the payload (retry after a partial run).
    repository.save_synthesis_shard_result(
        shard_key="shard:abc", shard_ordinal=1, shard_count=3,
        manifest_hash="sha256:m2", result={"result": {"summary": "s2"}},
    )
    row = repository.synthesis_shard_result("shard:abc")
    assert row["manifest_hash"] == "sha256:m2"
    assert row["output"]["result"]["summary"] == "s2"


def test_finalize_stale_synthesis_runs_spares_recent_rows(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    repository = Repository(paths.sqlite_path)
    vault = load_vault(paths.root)
    manifest_id = persist_manifest(repository, build_manifest(vault, source_set_id="ss1"))

    from datetime import UTC, datetime

    from learnloop.clock import FrozenClock

    old_clock = FrozenClock(datetime(2026, 7, 1, 12, 0, 0, tzinfo=UTC))
    new_clock = FrozenClock(datetime(2026, 7, 15, 12, 0, 0, tzinfo=UTC))
    stale = repository.insert_synthesis_run(manifest_id=manifest_id, mode="bootstrap", clock=old_clock)
    repository.save_synthesis_candidate(stale, {"summary": "kept"})
    live = repository.insert_synthesis_run(manifest_id=manifest_id, mode="bootstrap", clock=new_clock)
    finished = repository.insert_synthesis_run(manifest_id=manifest_id, mode="bootstrap", clock=old_clock)
    repository.complete_synthesis_run(finished, status="completed", clock=old_clock)

    finalized = repository.finalize_stale_synthesis_runs(
        before_iso="2026-07-10T00:00:00Z", clock=new_clock
    )

    assert finalized == [stale]
    stale_row = repository.synthesis_run(stale)
    assert stale_row["status"] == "failed"
    assert stale_row["completed_at"] is not None
    # A preserved candidate survives finalization.
    assert stale_row["candidate_output"] == {"summary": "kept"}
    assert repository.synthesis_run(live)["status"] == "created"
    assert repository.synthesis_run(finished)["status"] == "completed"
