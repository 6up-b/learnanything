from __future__ import annotations

import json

from typer.testing import CliRunner

from learnloop.cli import app
from learnloop.db.repositories import Repository
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths

from tests.helpers import create_basic_vault


def test_cli_attempt_json_and_show_attempt(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    runner = CliRunner()

    result = runner.invoke(
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

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    attempt_id = payload["attempt"]["attempt_id"]
    assert payload["attempt"]["rubric_score"] == 4
    assert payload["attempt"]["fsrs_rating"] == "easy"

    shown = runner.invoke(app, ["show", attempt_id, "--vault", str(vault_root), "--json"])

    assert shown.exit_code == 0, shown.output
    shown_payload = json.loads(shown.output)
    assert shown_payload["type"] == "practice_attempt"
    assert shown_payload["record"]["id"] == attempt_id

    why = runner.invoke(app, ["why", "pi_svd_define_001", "--vault", str(vault_root), "--json"])

    assert why.exit_code == 0, why.output
    why_payload = json.loads(why.output)
    assert why_payload["practice_item_id"] == "pi_svd_define_001"
    assert why_payload["components"]["active_goal"] == 0.8


def test_cli_show_attempt_includes_evidence_and_surprise(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "attempt",
            "pi_svd_define_001",
            "--vault",
            str(vault_root),
            "--answer",
            "SVD is exactly eigendecomposition.",
            "--criterion-points",
            "correctness=2",
            "--fatal-errors",
            "conceptual_slip",
            "--confidence",
            "4",
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    attempt_id = json.loads(result.output)["attempt"]["attempt_id"]
    loaded = load_vault(vault_root)
    repository = Repository(VaultPaths(loaded.root, loaded.config).sqlite_path)
    error_id = repository.active_errors_by_learning_object("lo_svd_definition")[0].id

    shown_attempt = runner.invoke(app, ["show", attempt_id, "--vault", str(vault_root), "--json"])
    shown_error = runner.invoke(app, ["show", error_id, "--vault", str(vault_root), "--json"])

    assert shown_attempt.exit_code == 0, shown_attempt.output
    attempt_payload = json.loads(shown_attempt.output)
    assert attempt_payload["record"]["grading_evidence"][0]["criterion_id"] == "correctness"
    assert attempt_payload["record"]["surprise"]["observed_joint_bucket"]["error_type"] == "conceptual_slip"
    assert shown_error.exit_code == 0, shown_error.output
    assert json.loads(shown_error.output)["record"]["error_type"] == "conceptual_slip"
