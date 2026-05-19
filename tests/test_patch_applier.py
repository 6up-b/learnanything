from __future__ import annotations

import sqlite3

import pytest
from typer.testing import CliRunner

from learnloop.cli import app
from learnloop.db.repositories import Repository
from learnloop.services.patches import PatchApplicationError, apply_accepted_items
from learnloop.services.proposals import reject_items
from learnloop.vault.loader import load_vault

from tests.helpers import NOW_ISO, create_basic_vault


def test_accept_proposal_creates_yaml_content_events_and_state(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    _seed_agent_and_proposal(repository)

    result = apply_accepted_items(vault_root, "patch_authoring_1")

    loaded = load_vault(vault_root)
    assert result.applied_count == 2
    assert "lo_svd_applications" in loaded.learning_objects
    assert "pi_svd_applications_001" in loaded.practice_items
    assert repository.mastery_state("lo_svd_applications") is not None
    assert repository.practice_item_state("pi_svd_applications_001") is not None

    with sqlite3.connect(paths.sqlite_path) as connection:
        change_batches = connection.execute("SELECT COUNT(*) FROM change_batches").fetchone()[0]
        content_events = connection.execute("SELECT entity_type, entity_id FROM content_events ORDER BY entity_type").fetchall()
        decisions = connection.execute("SELECT decision, applied_change_batch_id FROM proposed_patch_items ORDER BY id").fetchall()

    assert change_batches == 2
    assert content_events == [
        ("learning_object", "lo_svd_applications"),
        ("practice_item", "pi_svd_applications_001"),
    ]
    assert all(decision == "accepted" and change_batch_id for decision, change_batch_id in decisions)


def test_accept_cli_applies_and_show_proposal_includes_items(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    _seed_agent_and_proposal(repository)
    runner = CliRunner()

    accepted = runner.invoke(app, ["accept", "patch_authoring_1", "--items", "proposal_item_lo", "--vault", str(vault_root)])
    shown = runner.invoke(app, ["show", "patch_authoring_1", "--vault", str(vault_root), "--json"])

    assert accepted.exit_code == 0, accepted.output
    assert "Accepted and applied 1 proposal item" in accepted.output
    assert shown.exit_code == 0, shown.output
    assert "proposal_item_lo" in shown.output
    assert load_vault(vault_root).learning_objects["lo_svd_applications"].title == "SVD applications"


def test_reject_proposal_item_does_not_mutate_yaml(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    _seed_agent_and_proposal(repository)

    count = reject_items(vault_root, "patch_authoring_1", ["proposal_item_lo"])

    assert count == 1
    assert "lo_svd_applications" not in load_vault(vault_root).learning_objects


def test_invalid_proposal_item_cannot_be_accepted(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    _seed_agent_and_proposal(repository, validation_status="invalid")

    with pytest.raises(PatchApplicationError, match="invalid"):
        apply_accepted_items(vault_root, "patch_authoring_1", ["proposal_item_lo"])

    assert "lo_svd_applications" not in load_vault(vault_root).learning_objects


def _seed_agent_and_proposal(repository: Repository, *, validation_status: str = "valid") -> None:
    repository.insert_agent_run(
        {
            "id": "agent_run_authoring_1",
            "purpose": "authoring",
            "provider": "fake",
            "output_schema": "AuthoringProposal",
            "started_at": NOW_ISO,
            "status": "completed",
            "completed_at": NOW_ISO,
        }
    )
    repository.persist_proposal_batch(
        {
            "id": "patch_authoring_1",
            "agent_run_id": "agent_run_authoring_1",
            "purpose": "authoring",
            "source_refs": [{"ref_type": "note", "ref_id": "note_svd"}],
            "summary": "Create SVD application practice",
            "created_at": NOW_ISO,
        },
        [
            {
                "id": "proposal_item_lo",
                "client_item_id": "client_lo",
                "item_type": "learning_object",
                "operation": "create",
                "payload": {
                    "id": "lo_svd_applications",
                    "title": "SVD applications",
                    "subjects": ["linear-algebra"],
                    "concept_id": "singular_value_decomposition",
                    "knowledge_type": "application",
                    "summary": "SVD can be used for low-rank approximation.",
                },
                "validation_status": validation_status,
                "validation_errors": ["bad"] if validation_status == "invalid" else [],
                "created_at": NOW_ISO,
            },
            {
                "id": "proposal_item_pi",
                "client_item_id": "client_pi",
                "item_type": "practice_item",
                "operation": "create",
                "payload": {
                    "id": "pi_svd_applications_001",
                    "learning_object_id": "lo_svd_applications",
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
                },
                "validation_status": validation_status,
                "validation_errors": ["bad"] if validation_status == "invalid" else [],
                "created_at": NOW_ISO,
            },
        ],
    )
