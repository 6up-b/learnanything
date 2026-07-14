from __future__ import annotations

import multiprocessing
import os

import pytest

from learnloop.db.repositories import Repository
from learnloop.services.apply_protocol import recover_apply_intents
from learnloop.services.patches import (
    PatchApplicationError,
    apply_accepted_items,
    compute_target_hash,
)
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths

from tests.helpers import NOW_ISO, create_basic_vault

LO_ID = "lo_svd_applications"
PI_ID = "pi_svd_applications_001"

_LO_PAYLOAD = {
    "id": LO_ID,
    "title": "SVD applications",
    "subjects": ["linear-algebra"],
    "concept_id": "singular_value_decomposition",
    "knowledge_type": "application",
    "summary": "SVD can be used for low-rank approximation.",
    "provenance": {
        "origin": "codex_proposal",
        "source_refs": [
            {
                "ref_type": "canonical_source",
                "ref_id": "src_axler",
                "source_id": "src_axler",
                "revision_id": "rev_axler_1",
                "locator": "block_span:p12",
                "locator_scheme": "block_span_v1",
                "relation": "primary",
                "span_hash": "sha256:deadbeef",
            }
        ],
    },
}

_PI_PAYLOAD = {
    "id": PI_ID,
    "learning_object_id": LO_ID,
    "subjects": None,
    "practice_mode": "short_answer",
    "attempt_types_allowed": ["independent_attempt"],
    "evidence_facets": ["application"],
    "evidence_weights": {"application": 1.0},
    "prompt": "Name one use of SVD.",
    "expected_answer": "Low-rank approximation is one use.",
    "grading_rubric": {
        "max_points": 4,
        "criteria": [{"id": "correctness", "points": 4, "description": "Names a real use."}],
        "fatal_errors": [],
    },
}


def _repo(paths) -> Repository:
    return Repository(paths.sqlite_path)


def _seed_agent(repository: Repository, agent_id: str) -> None:
    repository.insert_agent_run(
        {
            "id": agent_id,
            "purpose": "authoring",
            "provider": "fake",
            "output_schema": "AuthoringProposal",
            "started_at": NOW_ISO,
            "status": "completed",
            "completed_at": NOW_ISO,
        }
    )


def _seed_lo_and_pi_proposal(repository: Repository, patch_id: str = "patch_wa") -> None:
    _seed_agent(repository, f"agent_{patch_id}")
    repository.persist_proposal_batch(
        {
            "id": patch_id,
            "agent_run_id": f"agent_{patch_id}",
            "purpose": "authoring",
            "source_refs": [],
            "summary": "Create SVD LO + item",
            "created_at": NOW_ISO,
        },
        [
            {
                "id": "item_lo",
                "client_item_id": "client_lo",
                "item_type": "learning_object",
                "operation": "create",
                "payload": _LO_PAYLOAD,
                "validation_status": "valid",
                "validation_errors": [],
                "created_at": NOW_ISO,
            },
            {
                "id": "item_pi",
                "client_item_id": "client_pi",
                "item_type": "practice_item",
                "operation": "create",
                "payload": _PI_PAYLOAD,
                "depends_on_client_item_ids": ["client_lo"],
                "validation_status": "valid",
                "validation_errors": [],
                "created_at": NOW_ISO,
            },
        ],
    )


# --- happy path + provenance writes -----------------------------------------


def test_apply_writes_entity_source_links_and_marks_intent_applied(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    repository = _repo(paths)
    _seed_lo_and_pi_proposal(repository)

    result = apply_accepted_items(paths.root, "patch_wa")

    assert result.applied_count == 2
    loaded = load_vault(paths.root)
    assert LO_ID in loaded.learning_objects
    assert PI_ID in loaded.practice_items

    links = repository.entity_source_links("learning_object", LO_ID)
    assert len(links) == 1
    link = links[0]
    assert link["relation"] == "primary"
    assert link["revision_id"] == "rev_axler_1"
    assert link["locator"] == "block_span:p12"
    assert link["status"] == "current"

    # No mid-flight intents remain; the intent completed.
    assert repository.pending_apply_intents() == []


# --- dependency closure -----------------------------------------------------


def test_dependency_closure_reject_prereq_blocks_dependents(tmp_path):
    """§14: reject a proposed prerequisite while accepting its dependent ->
    dependent blocked, no dangling writes."""

    paths = create_basic_vault(tmp_path / "vault")
    repository = _repo(paths)
    _seed_agent(repository, "agent_closure")
    repository.persist_proposal_batch(
        {
            "id": "patch_closure",
            "agent_run_id": "agent_closure",
            "purpose": "authoring",
            "source_refs": [],
            "summary": "facet prereq + dependent LO",
            "created_at": NOW_ISO,
        },
        [
            {
                "id": "item_facet",
                "client_item_id": "client_facet",
                "item_type": "facet",
                "operation": "create",
                "payload": {"id": "facet_low_rank", "title": "Low-rank approximation"},
                "validation_status": "valid",
                "validation_errors": [],
                "created_at": NOW_ISO,
            },
            {
                "id": "item_lo",
                "client_item_id": "client_lo",
                "item_type": "learning_object",
                "operation": "create",
                "payload": _LO_PAYLOAD,
                "depends_on_client_item_ids": ["client_facet"],
                "validation_status": "valid",
                "validation_errors": [],
                "created_at": NOW_ISO,
            },
        ],
    )

    # Reject the prerequisite facet.
    repository.set_proposal_item_decision("patch_closure", "rejected", ["item_facet"])

    # Accept only the dependent LO.
    result = apply_accepted_items(paths.root, "patch_closure", ["item_lo"])

    assert result.applied_count == 0
    assert LO_ID not in load_vault(paths.root).learning_objects  # no dangling write

    blocked = repository.proposal_item("item_lo")
    assert blocked["dependency_status"] == "blocked"
    assert blocked["decision"] == "pending"  # never partially applied
    reason = blocked["dependency_block_reason"]
    assert reason["reason"] == "prerequisite_rejected"
    assert reason["blocking_item_id"] == "item_facet"


def test_dependency_closure_accepts_full_closure_in_order(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    repository = _repo(paths)
    _seed_lo_and_pi_proposal(repository)

    result = apply_accepted_items(paths.root, "patch_wa", ["item_lo", "item_pi"])

    assert result.applied_count == 2
    loaded = load_vault(paths.root)
    assert LO_ID in loaded.learning_objects and PI_ID in loaded.practice_items


# --- accept-time race refusal -----------------------------------------------


def _seed_lo_update_proposal(repository: Repository, expected_hash: str) -> None:
    _seed_agent(repository, "agent_update")
    payload = {
        "id": LO_ID,
        "summary": "Refined summary of SVD applications for exam prep.",
        "expected_target_hash": expected_hash,
    }
    repository.persist_proposal_batch(
        {
            "id": "patch_update",
            "agent_run_id": "agent_update",
            "purpose": "authoring",
            "source_refs": [],
            "summary": "Update SVD LO",
            "created_at": NOW_ISO,
        },
        [
            {
                "id": "item_update",
                "client_item_id": "client_update",
                "item_type": "learning_object",
                "operation": "update",
                "target_entity_type": "learning_object",
                "target_entity_id": LO_ID,
                "payload": payload,
                "validation_status": "valid",
                "validation_errors": [],
                "created_at": NOW_ISO,
            }
        ],
    )


def test_race_attempt_inserted_after_synthesis_refuses_under_lock(tmp_path):
    """§14: proposal synthesized, then an attempt is inserted; acceptance is
    refused while holding the mutation lock, leaving no partial YAML/DB decision."""

    paths = create_basic_vault(tmp_path / "vault")
    repository = _repo(paths)
    _seed_lo_and_pi_proposal(repository)
    apply_accepted_items(paths.root, "patch_wa")  # LO now exists

    vault = load_vault(paths.root)
    expected_hash = compute_target_hash(vault, "learning_object", LO_ID)
    _seed_lo_update_proposal(repository, expected_hash)

    # After synthesis: a real learner attempt lands against the LO -> it locks.
    with repository.connection() as connection:
        connection.execute(
            """
            INSERT INTO practice_attempts
              (id, practice_item_id, learning_object_id, practice_mode, attempt_type, hints_used, created_at)
            VALUES (?, ?, ?, 'short_answer', 'independent_attempt', 0, ?)
            """,
            ("attempt_race", PI_ID, LO_ID, NOW_ISO),
        )
        connection.commit()

    before = load_vault(paths.root).learning_objects[LO_ID].summary
    with pytest.raises(PatchApplicationError, match="locked"):
        apply_accepted_items(paths.root, "patch_update")

    # No partial write: the summary is unchanged, the item stays pending, and no
    # intent was left behind.
    assert load_vault(paths.root).learning_objects[LO_ID].summary == before
    assert repository.proposal_item("item_update")["decision"] == "pending"
    assert repository.pending_apply_intents() == []


def test_expected_target_hash_mismatch_refuses(tmp_path):
    """§8.2: acceptance refuses if the target changed after synthesis, even when
    lock state did not."""

    paths = create_basic_vault(tmp_path / "vault")
    repository = _repo(paths)
    _seed_lo_and_pi_proposal(repository)
    apply_accepted_items(paths.root, "patch_wa")

    # Synthesis stamped a hash that no longer matches (target edited since).
    _seed_lo_update_proposal(repository, "sha256:stale-hash-from-synthesis")

    with pytest.raises(PatchApplicationError, match="target changed after synthesis"):
        apply_accepted_items(paths.root, "patch_update")
    assert repository.proposal_item("item_update")["decision"] == "pending"


# --- crash recovery (process-kill at each boundary) -------------------------


def _crash_child(vault_root: str, patch_id: str, boundary: str) -> None:
    """Runs the write-ahead protocol against a temp vault and kills itself at a
    named boundary (a real crash, not an exception)."""

    from pathlib import Path

    from learnloop.services import apply_protocol
    from learnloop.services.patches import _proposal_origin

    vault = load_vault(Path(vault_root))
    repository = Repository(VaultPaths(vault.root, vault.config).sqlite_path)
    requested = repository.pending_proposal_items(patch_id)
    origin = _proposal_origin(repository, patch_id)
    ordered_ids, _blocked = apply_protocol.compute_dependency_closure(repository, requested)
    by_id = {item["id"]: item for item in requested}
    ordered_items = [by_id[item_id] for item_id in ordered_ids]
    targets, db_plan = apply_protocol.stage_target_contents(
        vault.root, vault, ordered_items, origin, patch_id, clock=None
    )
    repository.insert_apply_intent(
        proposed_patch_id=patch_id,
        item_ids=ordered_ids,
        targets=targets,
        db_plan=db_plan,
    )
    if boundary == "after_intent":
        os._exit(1)  # crash between DB intent commit and the YAML rename
    apply_protocol.materialize_targets(vault.root, targets)
    if boundary == "after_rename":
        os._exit(1)  # crash between the rename and the applied mark
    os._exit(0)


def _run_crash(vault_root, patch_id: str, boundary: str) -> None:
    proc = multiprocessing.get_context("fork").Process(
        target=_crash_child, args=(str(vault_root), patch_id, boundary)
    )
    proc.start()
    proc.join(timeout=30)
    assert proc.exitcode == 1


def test_crash_between_intent_and_rename_recovers(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    repository = _repo(paths)
    _seed_lo_and_pi_proposal(repository)

    _run_crash(paths.root, "patch_wa", "after_intent")

    # Intent committed, YAML not yet written.
    assert len(repository.pending_apply_intents()) == 1
    assert LO_ID not in load_vault(paths.root).learning_objects
    assert repository.proposal_item("item_lo")["decision"] == "pending"

    recovered = recover_apply_intents(paths.root, repository)

    assert len(recovered) == 1
    loaded = load_vault(paths.root)
    assert LO_ID in loaded.learning_objects and PI_ID in loaded.practice_items
    assert repository.proposal_item("item_lo")["decision"] == "accepted"
    assert repository.entity_source_links("learning_object", LO_ID)
    assert repository.mastery_state(LO_ID) is not None  # derived state synced
    assert repository.pending_apply_intents() == []


def test_crash_between_rename_and_applied_mark_recovers(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    repository = _repo(paths)
    _seed_lo_and_pi_proposal(repository)

    _run_crash(paths.root, "patch_wa", "after_rename")

    # YAML written, but the DB side effects and applied mark did not happen.
    assert len(repository.pending_apply_intents()) == 1
    assert LO_ID in load_vault(paths.root).learning_objects  # files renamed into place
    assert repository.proposal_item("item_lo")["decision"] == "pending"
    assert repository.entity_source_links("learning_object", LO_ID) == []

    recovered = recover_apply_intents(paths.root, repository)

    assert len(recovered) == 1
    assert repository.proposal_item("item_lo")["decision"] == "accepted"
    assert repository.proposal_item("item_pi")["decision"] == "accepted"
    assert repository.entity_source_links("learning_object", LO_ID)
    assert repository.pending_apply_intents() == []


def test_recovery_is_idempotent_and_noop_when_clean(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    repository = _repo(paths)
    _seed_lo_and_pi_proposal(repository)
    apply_accepted_items(paths.root, "patch_wa")

    # Nothing pending -> recovery is a no-op, and a second call stays clean.
    assert recover_apply_intents(paths.root, repository) == []
    assert recover_apply_intents(paths.root, repository) == []


def test_doctor_fix_recovers_mid_flight_intent(tmp_path):
    from learnloop.services.doctor import run_doctor

    paths = create_basic_vault(tmp_path / "vault")
    repository = _repo(paths)
    _seed_lo_and_pi_proposal(repository)
    _run_crash(paths.root, "patch_wa", "after_intent")
    assert len(repository.pending_apply_intents()) == 1

    # Plain doctor reports the mid-flight intent without mutating.
    report = run_doctor(paths.root)
    assert any(issue.code == "apply_intents:pending" for issue in report.issues)
    assert len(repository.pending_apply_intents()) == 1

    # doctor --fix completes it under the mutation lock.
    fixed = run_doctor(paths.root, fix_state=True)
    assert any(issue.code == "apply_intents:recovered" for issue in fixed.issues)
    assert repository.pending_apply_intents() == []
    assert LO_ID in load_vault(paths.root).learning_objects
    assert repository.proposal_item("item_lo")["decision"] == "accepted"
