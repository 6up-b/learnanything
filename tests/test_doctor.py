from __future__ import annotations

import json

from typer.testing import CliRunner

from learnloop.cli import app
from learnloop.services.doctor import run_doctor
from learnloop.vault.loader import init_vault
from learnloop.vault.yaml_io import read_yaml, write_yaml

from tests.helpers import NOW_ISO, create_basic_vault


def test_doctor_clean_fresh_vault(tmp_path):
    vault_root = tmp_path / "vault"
    init_vault(vault_root)

    report = run_doctor(vault_root)

    assert report.clean is True
    assert report.error_count == 0
    assert report.warning_count == 0


def test_doctor_reports_and_fixes_missing_derived_state(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)

    report = run_doctor(vault_root)

    assert {issue.code for issue in report.issues} == {
        "sql:missing_learning_object_mastery",
        "sql:missing_practice_item_state",
    }

    fixed = run_doctor(vault_root, fix_state=True)

    assert fixed.clean is True
    assert fixed.state_sync is not None
    assert fixed.state_sync.practice_item_states_created == 1
    assert fixed.state_sync.mastery_states_created == 1


def test_doctor_reports_reference_issues_and_json_cli(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    write_yaml(
        paths.relations_path,
        {
            "schema_version": 1,
            "edges": [
                {
                    "id": "edge_missing",
                    "relation_type": "related",
                    "source": "singular_value_decomposition",
                    "target": "missing_concept",
                    "strength": 1.0,
                    "created_at": NOW_ISO,
                    "updated_at": NOW_ISO,
                }
            ],
        },
    )
    runner = CliRunner()

    result = runner.invoke(app, ["doctor", "--vault", str(vault_root), "--json"])

    assert result.exit_code == 1
    payload = json.loads(result.output)
    codes = {issue["code"] for issue in payload["issues"]}
    assert "concept_edge:missing_target" in codes
    assert "sql:missing_practice_item_state" in codes
    assert payload["clean"] is False

    fixed = runner.invoke(app, ["doctor", "--vault", str(vault_root), "--fix-state", "--json"])

    assert fixed.exit_code == 1
    fixed_payload = json.loads(fixed.output)
    fixed_codes = {issue["code"] for issue in fixed_payload["issues"]}
    assert "sql:missing_practice_item_state" not in fixed_codes
    assert "concept_edge:missing_target" in fixed_codes
    assert fixed_payload["state_sync"]["practice_item_states_created"] == 1


def test_doctor_warns_on_unknown_yaml_key_that_looks_like_typo(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    practice_item_path = paths.practice_item_path("linear-algebra", "pi_svd_define_001")
    practice_item = read_yaml(practice_item_path)
    practice_item["promtp"] = "typo"
    write_yaml(practice_item_path, practice_item)

    report = run_doctor(vault_root, fix_state=True)

    typo_issues = [issue for issue in report.issues if issue.code == "yaml:unknown_key_typo"]
    assert len(typo_issues) == 1
    assert "promtp" in typo_issues[0].message
    assert "prompt" in typo_issues[0].message
