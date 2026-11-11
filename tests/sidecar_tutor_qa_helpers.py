"""What other test files use from ``tests/test_sidecar_tutor_qa.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

import io
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from learnloop_sidecar.server import serve

from tests.helpers import configure_codex_http, create_basic_vault, seed_due_item


def _rpc(messages: list[dict]) -> list[dict]:
    stdin = io.StringIO("".join(json.dumps(message) + "\n" for message in messages))
    stdout = io.StringIO()
    serve(stdin, stdout)
    return [json.loads(line) for line in stdout.getvalue().splitlines()]


class _TutorServer:
    """Mock AI provider: /health + /tutor-qa + /grading-proposal + /promotion-analysis."""

    def __init__(
        self,
        *,
        question_type: str = "mechanism",
        answer_md: str = "Think about the factor shapes.",
        promotion_analysis: dict | None = None,
    ):
        self.requests: list[dict] = []
        self.question_type = question_type
        self.answer_md = answer_md
        self.promotion_analysis = promotion_analysis or {
            "attributed_facets": [],
            "question_nature": "mechanism",
            "attempted_in_thread": False,
            "covered_by_practice_item_id": None,
        }
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
                if self.path == "/tutor-qa":
                    candidates = body["context"].get("candidate_facets", [])
                    self._json(
                        {
                            "answer_md": owner.answer_md,
                            "question_type": owner.question_type,
                            "facets": candidates,
                        }
                    )
                    return
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
                if self.path == "/promotion-analysis":
                    self._json(owner.promotion_analysis)
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


def _configure_http_provider(vault_root: Path, checkout: Path, base_url: str) -> None:
    """Point the canonical Codex provider profile at the mock."""

    configure_codex_http(vault_root, checkout, base_url)


def _tutor_vault(tmp_path, server: _TutorServer):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    seed_due_item(paths)
    checkout = tmp_path / "codex"
    checkout.mkdir()
    (checkout / "HEAD").write_text("abc123", encoding="utf-8")
    _configure_http_provider(vault_root, checkout, server.base_url)
    return vault_root, paths


def _init(vault_root) -> dict:
    return {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"vaultPath": str(vault_root)}}
