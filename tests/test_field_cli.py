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
        "eval", "--vault", str(paths.root), "--output-dir", str(output),
        "--bootstrap-samples", "20", "--json",
    ])
    assert result.exit_code == 0, result.output
    response = json.loads(result.output)
    assert response["status"] == "complete"
    report = json.loads((output / "evaluation.json").read_text())
    assert "report1" in report and "report2" in report
    assert (output / "evaluation.md").is_file()
    assert hashlib.sha256(paths.sqlite_path.read_bytes()).hexdigest() == before
