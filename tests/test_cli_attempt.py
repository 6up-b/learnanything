from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from typer.testing import CliRunner

from learnloop.cli import app
from learnloop.db.repositories import MasteryState, Repository
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths
from learnloop.vault.yaml_io import read_yaml, write_yaml

from tests.helpers import NOW_ISO, create_basic_vault


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


def test_cli_attempt_defaults_to_allowed_open_text_attempt_type(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    practice_path = paths.practice_item_path("linear-algebra", "pi_svd_define_001")
    practice_item = read_yaml(practice_path)
    practice_item["practice_mode"] = "constructed_response"
    practice_item["attempt_types_allowed"] = ["open_text"]
    write_yaml(practice_path, practice_item)
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
    attempt_id = json.loads(result.output)["attempt"]["attempt_id"]
    repository = Repository(paths.sqlite_path)
    assert repository.fetch_practice_attempt(attempt_id)["attempt_type"] == "open_text"


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


def test_cli_attempt_passes_available_minutes_to_followup_gate(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    repository.upsert_mastery_state(
        MasteryState(
            learning_object_id="lo_svd_definition",
            logit_mean=2.0,
            logit_variance=1.0,
            evidence_count=3,
            last_evidence_at=NOW_ISO,
            algorithm_version="mvp-0.1",
            updated_at=NOW_ISO,
        )
    )
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
            "correctness=1",
            "--fatal-errors",
            "conceptual_slip",
            "--confidence",
            "4",
            "--available-minutes",
            "0",
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    attempt_id = json.loads(result.output)["attempt"]["attempt_id"]
    surprise = repository.latest_attempt_surprise(attempt_id)
    assert surprise["suppressed_actions"] == ["intervention_followup:no_time"]


def test_cli_attempt_uses_codex_http_when_runtime_ready(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    checkout = tmp_path / "codex"
    checkout.mkdir()
    (checkout / "HEAD").write_text("abc123", encoding="utf-8")
    server = _GradingServer()
    server.start()
    try:
        _configure_codex(vault_root, checkout, server.base_url)
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
                "correctness=1",
                "--confidence",
                "3",
                "--json",
            ],
        )
    finally:
        server.stop()

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["attempt"]["grading_source"] == "codex"
    assert payload["attempt"]["rubric_score"] == 4
    assert server.requests[0]["path"] == "/grading-proposal"


def _configure_codex(vault_root, checkout, base_url: str) -> None:
    config_path = vault_root / "learnloop.toml"
    text = config_path.read_text(encoding="utf-8")
    text = text.replace('provider = "sdk"', 'provider = "http"')
    text = text.replace('checkout_path = "../codex"', f'checkout_path = "{checkout.as_posix()}"')
    text = text.replace('revision = "<pinned-commit>"', 'revision = "abc123"')
    text = text.replace('base_url = "http://127.0.0.1:8765"', f'base_url = "{base_url}"')
    config_path.write_text(text, encoding="utf-8")


class _GradingServer:
    def __init__(self):
        self.requests: list[dict] = []
        self._server = HTTPServer(("127.0.0.1", 0), self._handler())
        self.base_url = f"http://127.0.0.1:{self._server.server_port}"
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)

    def start(self) -> None:
        self._thread.start()

    def stop(self) -> None:
        self._server.shutdown()
        self._thread.join(timeout=5)
        self._server.server_close()

    def _handler(self):
        owner = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):  # noqa: N802
                if self.path == "/health":
                    self._json({"status": "ready"})
                    return
                self.send_response(404)
                self.end_headers()

            def do_POST(self):  # noqa: N802
                length = int(self.headers.get("Content-Length", "0"))
                body = json.loads(self.rfile.read(length).decode("utf-8"))
                owner.requests.append({"path": self.path, "body": body})
                if self.path == "/grading-proposal":
                    self._json(
                        {
                            "attempt_id": body["context"]["attempt_id"],
                            "practice_item_id": "pi_svd_define_001",
                            "rubric_score": 4,
                            "criterion_evidence": [
                                {"criterion_id": "correctness", "points_awarded": 4, "evidence": "Correct."}
                            ],
                            "grader_confidence": 0.95,
                        }
                    )
                    return
                self.send_response(404)
                self.end_headers()

            def log_message(self, *_args):
                return

            def _json(self, payload: dict) -> None:
                raw = json.dumps(payload).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)

        return Handler
