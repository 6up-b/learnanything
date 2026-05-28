from __future__ import annotations

import json

from typer.testing import CliRunner

from learnloop.cli import app
from learnloop.db.repositories import Repository

from tests.helpers import create_basic_vault


EMITTING_TEMPLATE = """
schema_version: 1
fields:
  - id: answer
    type: text
  - id: confidence
    type: scale
emits:
  attempt_type: independent_attempt
  answer_field: answer
  criterion_points_field: criterion_points
  confidence_field: confidence
"""

NON_EMITTING_TEMPLATE = """
schema_version: 1
fields:
  - id: reflection
    type: text
"""


def _register_template(runner: CliRunner, vault_root, template_file, *, title="Recall") -> str:
    result = runner.invoke(
        app,
        [
            "register-observation-template",
            "--vault",
            str(vault_root),
            "--file",
            str(template_file),
            "--domain",
            "linear-algebra",
            "--version",
            "1",
            "--title",
            title,
            "--json",
        ],
    )
    assert result.exit_code == 0, result.output
    return json.loads(result.output)["observation_template"]["id"]


def test_register_and_list_observation_templates(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    template_file = tmp_path / "reflection.yaml"
    template_file.write_text(NON_EMITTING_TEMPLATE, encoding="utf-8")
    inactive_file = tmp_path / "inactive.yaml"
    inactive_file.write_text(NON_EMITTING_TEMPLATE, encoding="utf-8")
    runner = CliRunner()

    active_id = _register_template(runner, vault_root, template_file, title="Reflection")
    inactive = runner.invoke(
        app,
        [
            "register-observation-template",
            "--vault",
            str(vault_root),
            "--file",
            str(inactive_file),
            "--domain",
            "linear-algebra",
            "--version",
            "1",
            "--title",
            "Inactive",
            "--inactive",
            "--json",
        ],
    )

    assert inactive.exit_code == 0, inactive.output
    active_only = runner.invoke(app, ["observation-templates", "--vault", str(vault_root), "--json"])
    all_templates = runner.invoke(app, ["observation-templates", "--vault", str(vault_root), "--all", "--json"])

    assert active_only.exit_code == 0, active_only.output
    active_payload = json.loads(active_only.output)["observation_templates"]
    assert [template["id"] for template in active_payload] == [active_id]
    assert active_payload[0]["emits_attempt"] is False

    assert all_templates.exit_code == 0, all_templates.output
    all_payload = json.loads(all_templates.output)["observation_templates"]
    assert len(all_payload) == 2
    assert {template["active"] for template in all_payload} == {False, True}


def test_record_observation_emits_attempt_when_practice_binding_is_resolved(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    template_file = tmp_path / "recall.yaml"
    template_file.write_text(EMITTING_TEMPLATE, encoding="utf-8")
    runner = CliRunner()
    template_id = _register_template(runner, vault_root, template_file)

    response = {
        "answer": "U Sigma V transpose",
        "criterion_points": {"correctness": 4},
        "confidence": 5,
    }
    result = runner.invoke(
        app,
        [
            "record-observation",
            template_id,
            "--vault",
            str(vault_root),
            "--response-json",
            json.dumps(response),
            "--subject",
            "linear-algebra",
            "--learning-object-id",
            "lo_svd_definition",
            "--practice-item-id",
            "pi_svd_define_001",
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    observation = json.loads(result.output)["observation"]
    assert observation["binding_mode"] == "template_fixed"
    assert observation["emitted_attempt_id"] is not None
    assert observation["attempt"]["rubric_score"] == 4

    repository = Repository(paths.sqlite_path)
    event = repository.observation_events()[0]
    attempt = repository.fetch_practice_attempt(observation["emitted_attempt_id"])
    assert event["emitted_attempt_id"] == observation["emitted_attempt_id"]
    assert event["subject"] == "linear-algebra"
    assert attempt["practice_item_id"] == "pi_svd_define_001"


def test_record_observation_without_practice_binding_lands_pending(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    template_file = tmp_path / "recall.yaml"
    template_file.write_text(EMITTING_TEMPLATE, encoding="utf-8")
    response_file = tmp_path / "response.yaml"
    response_file.write_text("answer: partial\nconfidence: 3\n", encoding="utf-8")
    runner = CliRunner()
    template_id = _register_template(runner, vault_root, template_file)

    result = runner.invoke(
        app,
        [
            "record-observation",
            template_id,
            "--vault",
            str(vault_root),
            "--response-file",
            str(response_file),
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    observation = json.loads(result.output)["observation"]
    assert observation["binding_mode"] == "pending"
    assert observation["emitted_attempt_id"] is None

    repository = Repository(paths.sqlite_path)
    assert repository.observation_events()[0]["binding_mode"] == "pending"


def test_record_observation_rejects_two_response_sources(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    template_file = tmp_path / "reflection.yaml"
    template_file.write_text(NON_EMITTING_TEMPLATE, encoding="utf-8")
    response_file = tmp_path / "response.yaml"
    response_file.write_text("reflection: ok\n", encoding="utf-8")
    runner = CliRunner()
    template_id = _register_template(runner, vault_root, template_file)

    result = runner.invoke(
        app,
        [
            "record-observation",
            template_id,
            "--vault",
            str(vault_root),
            "--response-json",
            '{"reflection": "ok"}',
            "--response-file",
            str(response_file),
            "--json",
        ],
    )

    assert result.exit_code == 1
    assert json.loads(result.output)["error"] == "invalid_observation"
