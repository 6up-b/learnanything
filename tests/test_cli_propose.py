from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from typer.testing import CliRunner

from learnloop.cli import app
from learnloop.vault.loader import add_note
from learnloop.vault.loader import load_vault

from tests.helpers import create_basic_vault


def test_cli_propose_import_persists_and_accept_applies(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    proposal_file = tmp_path / "proposal.json"
    proposal_file.write_text(json.dumps(_proposal_payload()), encoding="utf-8")
    runner = CliRunner()

    proposed = runner.invoke(app, ["propose", "--vault", str(vault_root), "--file", str(proposal_file), "--json"])

    assert proposed.exit_code == 0, proposed.output
    patch_id = json.loads(proposed.output)["proposal_id"]

    listed = runner.invoke(app, ["proposals", "--vault", str(vault_root), "--json"])

    assert listed.exit_code == 0, listed.output
    assert json.loads(listed.output)["proposals"][0]["id"] == patch_id

    accepted = runner.invoke(app, ["accept", patch_id, "--vault", str(vault_root)])

    assert accepted.exit_code == 0, accepted.output
    loaded = load_vault(vault_root)
    assert "lo_svd_imported" in loaded.learning_objects
    assert "pi_svd_imported_001" in loaded.practice_items


def test_cli_propose_without_file_reports_codex_unavailable(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    runner = CliRunner()

    result = runner.invoke(app, ["propose", "--vault", str(vault_root), "--json"])

    assert result.exit_code == 1
    payload = json.loads(result.output)
    assert payload["error"] == "codex_missing"


def test_cli_propose_context_stats_does_not_require_codex_runtime(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    runner = CliRunner()

    result = runner.invoke(app, ["propose", "--vault", str(vault_root), "--context-stats", "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    stats = payload["authoring_context"]
    assert stats["counts"]["learning_objects"] == 1
    assert stats["counts"]["practice_items"] == 1
    assert stats["chars"]["prompt_plus_schema"] > stats["chars"]["context"]


def test_cli_propose_runs_codex_http_authoring_when_runtime_ready(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    add_note(vault_root, "linear-algebra", "svd", "SVD", "SVD supports low-rank approximation.")
    checkout = tmp_path / "codex"
    checkout.mkdir()
    (checkout / "HEAD").write_text("abc123", encoding="utf-8")

    proposal = _proposal_payload()
    proposal["source_refs"] = [{"ref_type": "note", "ref_id": "note_svd"}]
    for item in proposal["items"]:
        item["source_ref_ids"] = ["note_svd"]
        item["review_route"] = "auto_apply"
    server = _ProposalServer(proposal)
    server.start()
    try:
        _configure_codex(vault_root, checkout, server.base_url)
        runner = CliRunner()

        result = runner.invoke(
            app,
            [
                "propose",
                "--vault",
                str(vault_root),
                "--subjects",
                "linear-algebra",
                "--notes",
                "note_svd_missing",
                "--instructions",
                "Make one item.",
                "--json",
            ],
        )
    finally:
        server.stop()

    assert result.exit_code == 0, result.output
    patch_id = json.loads(result.output)["proposal_id"]
    assert patch_id
    loaded = load_vault(vault_root)
    assert "lo_svd_imported" in loaded.learning_objects
    assert server.requests[0]["path"] == "/authoring-proposal"
    assert server.requests[0]["body"]["context"]["subjects"] == ["linear-algebra"]
    assert server.requests[0]["body"]["context"]["instructions"] == "Make one item."


def _proposal_payload() -> dict:
    return {
        "summary": "Imported SVD proposal",
        "source_refs": [
            {
                "ref_type": "manual_context",
                "ref_id": "manual_svd",
            }
        ],
        "items": [
            {
                "client_item_id": "lo_1",
                "item_type": "learning_object",
                "operation": "create",
                "proposed_entity_id": "lo_svd_imported",
                "source_ref_ids": ["manual_svd"],
                "rationale": "Add an application LO.",
                "review_route": "review_required",
                "payload": {
                    "title": "Imported SVD use",
                    "subjects": ["linear-algebra"],
                    "concept_id": "singular_value_decomposition",
                    "knowledge_type": "application",
                    "summary": "SVD can compress matrices through low-rank approximation.",
                },
            },
            {
                "client_item_id": "pi_1",
                "item_type": "practice_item",
                "operation": "create",
                "proposed_entity_id": "pi_svd_imported_001",
                "source_ref_ids": ["manual_svd"],
                "rationale": "Practice the new application LO.",
                "review_route": "review_required",
                "payload": {
                    "learning_object_id": "lo_svd_imported",
                    "subjects": None,
                    "practice_mode": "short_answer",
                    "attempt_types_allowed": ["independent_attempt"],
                    "prompt": "What is one use of SVD?",
                    "expected_answer": "Low-rank approximation.",
                    "evidence_facets": ["application"],
                    "evidence_weights": {"application": 1.0},
                    "grading_rubric": {
                        "max_points": 4,
                        "criteria": [{"id": "correctness", "points": 4, "description": "Names a real use."}],
                        "fatal_errors": [],
                    },
                },
            },
        ],
    }


def _configure_codex(vault_root, checkout, base_url: str) -> None:
    config_path = vault_root / "learnloop.toml"
    text = config_path.read_text(encoding="utf-8")
    text = text.replace('provider = "sdk"', 'provider = "http"')
    text = text.replace('checkout_path = "../codex"', f'checkout_path = "{checkout.as_posix()}"')
    text = text.replace('revision = "<pinned-commit>"', 'revision = "abc123"')
    text = text.replace('base_url = "http://127.0.0.1:8765"', f'base_url = "{base_url}"')
    config_path.write_text(text, encoding="utf-8")


class _ProposalServer:
    def __init__(self, proposal: dict):
        self.proposal = proposal
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
                if self.path != "/health":
                    self.send_response(404)
                    self.end_headers()
                    return
                self._json({"status": "ready"})

            def do_POST(self):  # noqa: N802
                length = int(self.headers.get("Content-Length", "0"))
                body = json.loads(self.rfile.read(length).decode("utf-8"))
                owner.requests.append({"path": self.path, "body": body})
                if self.path == "/authoring-proposal":
                    self._json(owner.proposal)
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
