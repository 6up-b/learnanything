from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from typer.testing import CliRunner

from learnloop.cli import app
from learnloop.vault.loader import load_vault

from tests.helpers import create_basic_vault


def test_cli_ingest_runs_canonical_endpoint_and_reports_json(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    html = _source_file(tmp_path)
    checkout = tmp_path / "codex"
    checkout.mkdir()
    (checkout / "HEAD").write_text("abc123", encoding="utf-8")
    server = _CanonicalIngestServer()
    server.start()
    try:
        _configure_codex(vault_root, checkout, server.base_url)
        runner = CliRunner()

        result = runner.invoke(
            app,
            [
                "ingest",
                str(html),
                "--vault",
                str(vault_root),
                "--subject",
                "linear-algebra",
                "--json",
            ],
        )
    finally:
        server.stop()

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["ingest"]["proposal_id"]
    assert payload["ingest"]["source_kind"] == "website_page"
    assert payload["ingest"]["auto_applied_count"] == 2
    assert server.requests[0]["path"] == "/canonical-ingest"
    context = server.requests[0]["body"]["context"]
    assert context["source_kind"] == "website_page"
    assert context["target_subject"] == "linear-algebra"
    assert context["chunks"]
    assert "lo_cli_ingested_svd" in load_vault(vault_root).learning_objects


def test_cli_ingest_reports_windows_path_escape_hint(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    config_path = vault_root / "learnloop.toml"
    config_path.write_text(
        config_path.read_text(encoding="utf-8").replace(
            'checkout_path = "../codex"',
            r'checkout_path = "C:\Users\banan\OneDrive\Documents\thinking\learnloop\codex"',
            1,
        ),
        encoding="utf-8",
    )
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "ingest",
            "https://example.edu/svd",
            "--vault",
            str(vault_root),
            "--subject",
            "linear-algebra",
            "--json",
        ],
    )

    assert result.exit_code == 1
    payload = json.loads(result.output)
    assert payload["error"] == "invalid_config"
    assert "Windows path" in payload["message"]
    assert "forward slashes" in payload["message"]
    assert "checkout_path" in payload["message"]
    assert "TOMLDecodeError" not in result.output


def _source_file(tmp_path):
    text = " ".join(
        [
            "Singular value decomposition describes a matrix as a product involving orthogonal factors.",
            "The source explains singular values as scale factors and motivates recall practice.",
            "Learners should be able to state the definition and explain what the factors mean.",
        ]
        * 5
    )
    html = tmp_path / "svd_cli.html"
    html.write_text(
        f"""
        <html>
          <head><title>SVD CLI source</title></head>
          <body><h1>Singular Value Decomposition</h1><p>{text}</p></body>
        </html>
        """,
        encoding="utf-8",
    )
    return html


def _configure_codex(vault_root, checkout, base_url: str) -> None:
    config_path = vault_root / "learnloop.toml"
    text = config_path.read_text(encoding="utf-8")
    text = text.replace('provider = "sdk"', 'provider = "http"')
    text = text.replace('checkout_path = "../codex"', f'checkout_path = "{checkout.as_posix()}"')
    text = text.replace('revision = "<pinned-commit>"', 'revision = "abc123"')
    text = text.replace('base_url = "http://127.0.0.1:8765"', f'base_url = "{base_url}"')
    config_path.write_text(text, encoding="utf-8")


class _CanonicalIngestServer:
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
                if self.path != "/health":
                    self.send_response(404)
                    self.end_headers()
                    return
                self._json({"status": "ready"})

            def do_POST(self):  # noqa: N802
                length = int(self.headers.get("Content-Length", "0"))
                body = json.loads(self.rfile.read(length).decode("utf-8"))
                owner.requests.append({"path": self.path, "body": body})
                if self.path == "/canonical-ingest":
                    context = body["context"]
                    self._json(_proposal_payload(context))
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


def _proposal_payload(context: dict) -> dict:
    source_ref_id = context["canonical_source"]["id"]
    locator = context["chunks"][0]["locator"]
    return {
        "summary": "CLI canonical ingest proposal.",
        "source_refs": [
            {
                "ref_type": "canonical_source",
                "ref_id": source_ref_id,
                "path": context["canonical_source"]["path"],
                "locator": locator,
            }
        ],
        "items": [
            {
                "client_item_id": "lo_cli_ingested_svd",
                "item_type": "learning_object",
                "operation": "create",
                "proposed_entity_id": "lo_cli_ingested_svd",
                "source_ref_ids": [source_ref_id],
                "rationale": "Extract the definition.",
                "review_route": "auto_apply",
                "payload": {
                    "title": "CLI ingested SVD definition",
                    "subjects": [context["target_subject"]],
                    "concept_id": "singular_value_decomposition",
                    "knowledge_type": "definition",
                    "summary": "SVD represents a matrix using orthogonal factors and singular values.",
                },
            },
            {
                "client_item_id": "pi_cli_ingested_svd",
                "item_type": "practice_item",
                "operation": "create",
                "proposed_entity_id": "pi_cli_ingested_svd_001",
                "source_ref_ids": [source_ref_id],
                "rationale": "Add recall practice.",
                "review_route": "auto_apply",
                "payload": {
                    "learning_object_id": "lo_cli_ingested_svd",
                    "subjects": None,
                    "practice_mode": "short_answer",
                    "attempt_types_allowed": ["independent_attempt"],
                    "prompt": "What factors appear in an SVD?",
                    "expected_answer": "Orthogonal factors and singular values.",
                    "evidence_facets": ["recall"],
                    "evidence_weights": {"recall": 1.0},
                    "grading_rubric": {
                        "max_points": 4,
                        "criteria": [{"id": "correctness", "points": 4, "description": "Names the factors."}],
                        "fatal_errors": [],
                    },
                },
            },
        ],
    }
