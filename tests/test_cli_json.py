from __future__ import annotations

import json

from typer.testing import CliRunner

from learnloop.cli import app
from learnloop.db.repositories import Repository
from learnloop.services.state_sync import sync_vault_state
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
        "codex_runtime",
        "error_count",
        "issues",
        "root",
        "state_sync",
        "version",
        "warning_count",
    }
    assert payload["version"] == 1
    assert payload["codex_runtime"]["status"] == "codex_missing"
    assert payload["state_sync"]["practice_item_states_created"] == 1


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
    assert attempt_payload["attempt"]["fallback_reason"] is None

    review = runner.invoke(app, ["review", "--vault", str(vault_root), "--json"])
    why = runner.invoke(app, ["why", "pi_svd_define_001", "--vault", str(vault_root), "--json"])
    shown = runner.invoke(app, ["show", attempt_id, "--vault", str(vault_root), "--json"])

    assert review.exit_code == 0, review.output
    review_payload = json.loads(review.output)
    assert set(review_payload) == {"items", "version"}
    assert review_payload["version"] == 1

    assert why.exit_code == 0, why.output
    why_payload = json.loads(why.output)
    assert set(why_payload) == {"components", "practice_item_id", "priority", "reasons", "source", "version"}

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
