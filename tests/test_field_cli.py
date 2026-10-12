"""Owner-facing offline commands must stay read-only and credential-free."""
import hashlib
import json

from typer.testing import CliRunner

from learnloop.cli import app
from tests.helpers import create_basic_vault


def _forbid_external_inputs(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("Offline field commands must not call models or load secrets")

    monkeypatch.setattr("learnloop.config.loader.load_dotenv", forbidden)
    monkeypatch.setattr("learnloop.config.loader.global_settings_path", forbidden)
    monkeypatch.setattr("learnloop.ai.client.make_ai_provider_client", forbidden)


def test_field_data_check_read_only_and_no_credentials(tmp_path, monkeypatch):
    paths = create_basic_vault(tmp_path / "vault")
    _forbid_external_inputs(monkeypatch)
    before = hashlib.sha256(paths.sqlite_path.read_bytes()).hexdigest()
    result = CliRunner().invoke(app, ["field", "data-check", "--vault", str(paths.root), "--json"])
    assert result.exit_code == 0, result.output
    report = json.loads(result.output)
    assert report["vault_validation_issues"] >= 0
    assert hashlib.sha256(paths.sqlite_path.read_bytes()).hexdigest() == before


def test_field_data_check_requires_explicit_valid_vault(tmp_path):
    result = CliRunner().invoke(app, ["field", "data-check", "--vault", str(tmp_path), "--json"])
    assert result.exit_code == 1
    assert json.loads(result.output)["status"] == "invalid"


def test_eval_writes_both_reports_without_models_or_database_writes(tmp_path, monkeypatch):
    paths = create_basic_vault(tmp_path / "vault")
    _forbid_external_inputs(monkeypatch)
    before = hashlib.sha256(paths.sqlite_path.read_bytes()).hexdigest()
    output = tmp_path / "reports"
    result = CliRunner().invoke(app, [
        "eval", "--vault", str(paths.root), "--section", "field", "--output-dir", str(output),
        "--bootstrap-samples", "20", "--json",
    ])
    assert result.exit_code == 0, result.output
    response = json.loads(result.output)
    assert response["status"] == "complete"
    report = json.loads((output / "evaluation.json").read_text())
    assert "report1" in report and "report2" in report
    assert (output / "evaluation.md").is_file()
    assert hashlib.sha256(paths.sqlite_path.read_bytes()).hexdigest() == before


def test_default_eval_stays_the_legacy_calibration_report(tmp_path, monkeypatch):
    paths = create_basic_vault(tmp_path / "vault")
    _forbid_external_inputs(monkeypatch)
    output = tmp_path / "reports"
    result = CliRunner().invoke(app, [
        "eval", "--vault", str(paths.root), "--output-dir", str(output), "--json",
    ])
    assert result.exit_code == 0, result.output
    assert set(json.loads(result.output)) == {"version", "eval"}
    assert not output.exists()  # field reports are opt-in via --section field


def test_eval_families_runs_the_shared_harness_read_only(tmp_path, monkeypatch):
    from learnloop.db.repositories import Repository
    from learnloop.field.evaluation import family_arms

    paths = create_basic_vault(tmp_path / "vault")
    _forbid_external_inputs(monkeypatch)

    def forbidden(*args, **kwargs):
        raise AssertionError("offline replay must not read live memory or scheduling caches")

    for name in ("practice_item_state", "activity_card_state", "item_parameter_state"):
        monkeypatch.setattr(Repository, name, forbidden)
    before = hashlib.sha256(paths.sqlite_path.read_bytes()).hexdigest()
    output = tmp_path / "reports"
    runs = []
    for _ in range(2):
        result = CliRunner().invoke(app, [
            "eval", "families", "--vault", str(paths.root), "--output", str(output),
            "--bootstrap-samples", "20", "--json",
        ])
        assert result.exit_code == 0, result.output
        runs.append(json.loads(result.output))
    assert runs[0] == runs[1]
    report = runs[0]["evaluation"]
    assert set(report["report1"]["arms"]) == set(family_arms())
    assert report["manifest"]["harness"] == "field-prequential-v2"
    weights = report["manifest"]["memory"]["weights"]
    assert weights["current_fit"]["is_defaults"]
    assert weights["current_fit"]["hash"] == weights["defaults"]["hash"]
    assert report["data_check"]["legacy_fallback"] == "exclude"
    assert sorted(path.name for path in output.iterdir()) == sorted(
        name.rsplit("/", 1)[-1] for name in runs[0]["reports"].values())
    assert all(path.name.startswith("pf-a-") for path in output.iterdir())
    assert hashlib.sha256(paths.sqlite_path.read_bytes()).hexdigest() == before


def test_one_explicit_legacy_fallback_for_every_report(tmp_path, monkeypatch):
    paths = create_basic_vault(tmp_path / "vault")
    _forbid_external_inputs(monkeypatch)
    for command in (["field", "data-check"], ["eval", "families"], ["eval", "--section", "field"]):
        result = CliRunner().invoke(app, [
            *command, "--vault", str(paths.root), "--legacy-fallback", "current_content",
            *(["--output-dir", str(tmp_path / "out")] if command[0] == "eval" else []), "--json",
        ])
        assert result.exit_code == 0, result.output
        payload = json.loads(result.output)
        counts = payload["evaluation"]["data_check"] if "evaluation" in payload else payload
        assert counts["legacy_fallback"] == "current_content"
        invalid = CliRunner().invoke(app, [
            *command, "--vault", str(paths.root), "--legacy-fallback", "guess",
            *(["--output-dir", str(tmp_path / "out")] if command[0] == "eval" else []), "--json",
        ])
        assert invalid.exit_code == 1
        assert json.loads(invalid.output)["status"] == "invalid"
