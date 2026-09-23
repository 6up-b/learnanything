"""Every CLI command run and TUI session records its model calls as receipts."""
from __future__ import annotations

import asyncio
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from types import SimpleNamespace

from typer.testing import CliRunner

from learnloop.ai.execution import report_call_usage
from learnloop.db.connection import connect
from tests.helpers import begin_session, configure_codex_http, create_basic_vault, seed_due_item
from tests.test_source_set_synthesis import FakeSynthesisClient, _setup


def _receipts(sqlite_path):
    with connect(sqlite_path) as connection:
        return [dict(row) for row in connection.execute(
            "SELECT owner_kind, owner_id, purpose, status, input_tokens, output_tokens, budget_json "
            "FROM model_call_receipts ORDER BY started_at"
        )]


class _UsageReportingSynthesisClient(FakeSynthesisClient):
    """Reports usage on the operation's own receipt, as the Codex HTTP adapter does."""

    def complete(self, request):
        report_call_usage({"input_tokens": 1200, "output_tokens": 300})
        return super().complete(request)


def test_cli_synthesize_records_receipts_with_usage_and_budgets(tmp_path, monkeypatch):
    import learnloop.cli as cli_module
    from learnloop.cli import app

    root, _repo, *_ = _setup(tmp_path)
    client = _UsageReportingSynthesisClient()
    ready = SimpleNamespace(ready=True, status="ready", message="")
    monkeypatch.setattr(cli_module, "_ready_provider_for_task", lambda *args, **kwargs: ("codex", ready, client))

    result = CliRunner().invoke(app, ["synthesize", "set_la", "--vault", str(root), "--json"])

    assert result.exit_code == 0, result.output
    passes = [row for row in _receipts(root / "state.sqlite") if row["purpose"] == "source_set_synthesis"]
    assert passes, "the synthesis pass left no receipt"
    for row in passes:
        assert row["owner_kind"] == "cli"
        assert row["owner_id"].startswith("synthesize:")
        assert (row["status"], row["input_tokens"], row["output_tokens"]) == ("completed", 1200, 300)
        assert json.loads(row["budget_json"]) == {
            "synthesis_shard_input_tokens": 40000,
            "synthesis_shard_output_tokens": 10000,
            "synthesis_total_input_ceiling": 48000,
            "synthesis_output_tokens": 16000,
        }
    # One command run is one owner.
    assert len({row["owner_id"] for row in passes}) == 1


def test_each_cli_run_is_its_own_owner(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    checkout = tmp_path / "codex"
    checkout.mkdir()
    (checkout / "HEAD").write_text("abc123", encoding="utf-8")
    server = _UsageReportingGradingServer()
    server.start()
    try:
        configure_codex_http(vault_root, checkout, server.base_url)
        for _ in range(2):
            result = _attempt(vault_root)
            assert result.exit_code == 0, result.output
    finally:
        server.stop()

    grading = [row for row in _receipts(vault_root / "state.sqlite") if row["input_tokens"] is not None]
    assert len(grading) == 2
    assert {row["owner_kind"] for row in grading} == {"cli"}
    assert all(row["owner_id"].startswith("attempt:") for row in grading)
    assert grading[0]["owner_id"] != grading[1]["owner_id"]
    assert (grading[0]["input_tokens"], grading[0]["output_tokens"]) == (900, 120)


def _attempt(vault_root):
    from learnloop.cli import app

    return CliRunner().invoke(app, [
        "attempt", "pi_svd_define_001", "--vault", str(vault_root),
        "--answer", "SVD is U Sigma V^T.", "--criterion-points", "correctness=1",
        "--confidence", "3", "--json",
    ])


def test_tui_grading_records_receipts_with_usage(tmp_path):
    from learnloop.tui.app import LearnLoopApp

    async def scenario():
        vault_root = tmp_path / "vault"
        paths = create_basic_vault(vault_root)
        seed_due_item(paths)
        checkout = tmp_path / "codex"
        checkout.mkdir()
        (checkout / "HEAD").write_text("abc123", encoding="utf-8")
        server = _UsageReportingGradingServer()
        server.start()
        try:
            configure_codex_http(vault_root, checkout, server.base_url)
            app = LearnLoopApp(vault_root)
            async with app.run_test() as pilot:
                await pilot.pause()
                today = await begin_session(app, pilot)
                await today.open_practice()
                await pilot.pause()
                practice = app.screen
                practice.set_answer("SVD is U Sigma V^T.")
                feedback = await practice.open_feedback()
                for _ in range(10):
                    await pilot.pause()
                    if feedback.result is not None:
                        break
                assert feedback.result is not None and feedback.result.grading_source == "codex"
                owner_id = app.state.receipt_owner_id
        finally:
            server.stop()
        return paths, owner_id

    paths, owner_id = asyncio.run(scenario())
    grading = [row for row in _receipts(paths.sqlite_path) if row["input_tokens"] is not None]
    assert grading, "the TUI grading call left no receipt with usage"
    assert {(row["owner_kind"], row["owner_id"]) for row in grading} == {("tui", owner_id)}
    assert all(row["status"] == "completed" for row in grading)
    assert (grading[0]["input_tokens"], grading[0]["output_tokens"]) == (900, 120)


class _UsageReportingGradingServer:
    """A Codex HTTP app-server whose grading proposals report OpenAI-shaped usage."""

    def __init__(self):
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
                if self.path != "/grading-proposal":
                    self.send_response(404)
                    self.end_headers()
                    return
                self._json({
                    "attempt_id": body["context"]["attempt_id"],
                    "practice_item_id": "pi_svd_define_001",
                    "rubric_score": 4,
                    "criterion_evidence": [{"criterion_id": "correctness", "points_awarded": 4, "evidence": "Correct."}],
                    "grader_confidence": 0.95,
                    "usage": {"prompt_tokens": 900, "completion_tokens": 120},
                })

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


def test_a_database_below_the_receipt_schema_lets_the_model_call_run_unrecorded(tmp_path, monkeypatch):
    """A paid call must not fail because its receipt cannot be written."""

    import shutil

    from learnloop.ai.schemas import WireModel
    from learnloop.ai.transport import STRUCTURED_COMPLETION, execute_structured_operation
    from learnloop.cli import app
    from learnloop.cli.runtime import _root
    from learnloop.db.migrate import applied_versions, apply_migrations, discover_migrations

    paths = create_basic_vault(tmp_path / "vault")
    paths.sqlite_path.unlink()
    through_164 = tmp_path / "through_164"
    through_164.mkdir()
    for migration in discover_migrations():
        if migration.version <= 164:
            shutil.copy2(migration.path, through_164 / migration.path.name)
    apply_migrations(paths.sqlite_path, migrations_dir=through_164)

    class Answer(WireModel):
        answer: str

    class Transport:
        provider_name = "codex_http"
        model = "codex-test"

        def supports(self, capability):
            return capability == STRUCTURED_COMPLETION

        def complete(self, request):
            report_call_usage({"input_tokens": 10, "output_tokens": 2})
            return Answer(answer="ok")

    answers = []

    # A command that calls a model before anything opens (and migrates) the
    # database: it only resolves its vault root.
    monkeypatch.setattr(app, "registered_commands", list(app.registered_commands))

    @app.command("receipt-schema-probe")
    def probe(vault: Path) -> None:
        _root(vault)
        for _ in range(2):
            answers.append(execute_structured_operation(Transport(), purpose="probe", prompt="p", result_model=Answer).answer)

    result = CliRunner().invoke(app, ["receipt-schema-probe", str(paths.root)])

    assert result.exit_code == 0, result.output
    assert answers == ["ok", "ok"]
    assert max(applied_versions(paths.sqlite_path)) == 164
    with connect(paths.sqlite_path) as connection:
        assert connection.execute("SELECT count(*) FROM model_call_receipts").fetchone()[0] == 0
    notices = [line for line in result.stderr.splitlines() if "not recorded" in line]
    assert len(notices) == 1
    assert "migration 164" in notices[0] and "receipts need 165" in notices[0]
    assert f"learnloop upgrade --vault {paths.root}" in notices[0]
