from __future__ import annotations

import json

from typer.testing import CliRunner

from learnloop.cli import app
from learnloop.db.repositories import Repository
from learnloop.substrate.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths

from tests.helpers import create_basic_vault
from tests.test_patch_applier import _seed_agent_and_proposal


def test_doctor_json_contract(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    runner = CliRunner()

    result = runner.invoke(app, ["doctor", "--vault", str(vault_root), "--fix-state", "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert set(payload) == {
        "clean",
        "ai_runtime",
        "codex_runtime",
        "contract_reachability",
        "deprecated_table_row_counts",
        "error_count",
        "issues",
        "root",
        "state_sync",
        "version",
        "warning_count",
    }
    assert payload["version"] == 1
    assert payload["ai_runtime"] is None
    assert payload["codex_runtime"] is None
    assert payload["state_sync"]["practice_item_states_created"] == 1


def test_misconception_gate_backfill_json_contract(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    repository.insert_misconception(
        id="mc_reverse_q",
        learning_object_id="lo_svd_definition",
        statement="reverses Q / Q^T",
        signature="Q^T x is the coordinate vector",
        facet_ids=["recall"],
        severity=0.8,
    )
    from learnloop.vault.writer import upsert_practice_item

    upsert_practice_item(
        paths.root,
        {
            "id": "pi_keyed_reverse",
            "learning_object_id": "lo_svd_definition",
            "subjects": None,
            "practice_mode": "short_answer",
            "attempt_types_allowed": ["independent_attempt"],
            "evidence_facets": ["recall"],
            "evidence_weights": {"recall": 1.0},
            "prompt": "Which of Qx / Q^T x is the coordinate vector?",
            "expected_answer": "Qx is the coordinate vector",
            "misconception_consistent_answer": "Q^T x is the coordinate vector",
            "surface_family": "computation",
            "grading_rubric": {
                "max_points": 4,
                "criteria": [{"id": "c1", "points": 4, "description": "correct"}],
                "fatal_errors": [
                    {"id": "fe", "description": "d", "misconception_id": "mc_reverse_q", "max_grade": 1}
                ],
            },
            "created_at": "2026-05-19T12:00:00Z",
            "updated_at": "2026-05-19T12:00:00Z",
        },
    )
    runner = CliRunner()

    result = runner.invoke(
        app, ["misconception-gate-backfill", "--vault", str(vault_root), "--json"]
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert set(payload) == {
        "version",
        "backfilled",
        "skipped_existing",
        "skipped_unregistered",
        "summary",
    }
    assert payload["summary"] == {
        "backfilled": 1,
        "skipped_existing": 0,
        "skipped_unregistered": 0,
    }
    assert payload["backfilled"][0]["practice_item_id"] == "pi_keyed_reverse"

    # Second run respects the existing row.
    again = json.loads(
        runner.invoke(
            app, ["misconception-gate-backfill", "--vault", str(vault_root), "--json"]
        ).output
    )
    assert again["summary"]["skipped_existing"] == 1
    assert again["summary"]["backfilled"] == 0


def test_review_why_attempt_show_json_contracts(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    runner = CliRunner()

    attempt = runner.invoke(
        app,
        [
            "attempt",
            "pi_svd_define_001",
            "--vault",
            str(vault_root),
            "--answer",
            "SVD is U Sigma V^T.",
            "--criterion-points",
            "correctness=4",
            "--confidence",
            "5",
            "--json",
        ],
    )

    assert attempt.exit_code == 0, attempt.output
    attempt_payload = json.loads(attempt.output)
    attempt_id = attempt_payload["attempt"]["attempt_id"]
    assert set(attempt_payload) == {"attempt", "version"}
    assert attempt_payload["attempt"]["grading_source"] == "self"
    assert attempt_payload["attempt"]["fallback_reason"] == "codex_missing"

    review = runner.invoke(app, ["review", "--vault", str(vault_root), "--json"])
    why = runner.invoke(app, ["why", "pi_svd_define_001", "--vault", str(vault_root), "--json"])
    shown = runner.invoke(app, ["show", attempt_id, "--vault", str(vault_root), "--json"])

    assert review.exit_code == 0, review.output
    review_payload = json.loads(review.output)
    assert set(review_payload) == {"items", "version"}
    assert review_payload["version"] == 1

    assert why.exit_code == 0, why.output
    why_payload = json.loads(why.output)
    assert set(why_payload) == {
        "components",
        "practice_item_id",
        "priority",
        "readiness_factor",
        "reasons",
        "source",
        "version",
    }

    assert shown.exit_code == 0, shown.output
    show_payload = json.loads(shown.output)
    assert set(show_payload) == {"id", "record", "type", "version"}
    assert show_payload["record"]["grading_evidence"][0]["grader_tier"] == 1
    assert show_payload["record"]["surprise"]["observed_joint_bucket"]["score_bucket"] == "high"


def test_proposals_json_contract(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    loaded = load_vault(vault_root)
    repository = Repository(VaultPaths(loaded.root, loaded.config).sqlite_path)
    sync_vault_state(loaded, repository)
    _seed_agent_and_proposal(repository)
    runner = CliRunner()

    result = runner.invoke(app, ["proposals", "--vault", str(vault_root), "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert set(payload) == {"proposals", "version"}
    assert payload["version"] == 1
    assert payload["proposals"][0]["id"] == "patch_authoring_1"
    assert payload["proposals"][0]["source_refs"] == [{"ref_id": "note_svd", "ref_type": "note"}]
    assert payload["proposals"][0]["items"][0]["id"] == "proposal_item_lo"
    assert payload["proposals"][0]["items"][0]["decision"] == "pending"
