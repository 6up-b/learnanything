from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from learnloop.codex.client import GradingContext, HttpCodexClient
from learnloop.codex.runtime import check_codex_runtime
from learnloop.config import CodexConfig


def test_http_codex_client_health_and_grading_round_trip(tmp_path):
    checkout = tmp_path / "codex"
    checkout.mkdir()
    (checkout / "HEAD").write_text("abc123", encoding="utf-8")
    server = _CodexServer(
        {
            "attempt_id": "attempt_1",
            "practice_item_id": "pi_1",
            "rubric_score": 4,
            "criterion_evidence": [{"criterion_id": "correctness", "points_awarded": 4, "evidence": "Correct."}],
            "grader_confidence": 0.95,
        }
    )
    server.start()
    try:
        config = CodexConfig(checkout_path=str(checkout), revision="abc123", base_url=server.base_url)

        report = check_codex_runtime(tmp_path, config)
        proposal = HttpCodexClient(config).run_grading_proposal(
            GradingContext(
                attempt_id="attempt_1",
                practice_item_id="pi_1",
                prompt="Prompt",
                expected_answer="Answer",
                learner_answer_md="Answer",
                rubric={"max_points": 4, "criteria": [{"id": "correctness", "points": 4}], "fatal_errors": []},
            )
        )
    finally:
        server.stop()

    assert report.ready is True
    assert proposal.rubric_score == 4
    assert server.requests[0]["path"] == "/grading-proposal"
    assert server.requests[0]["body"]["context"]["attempt_id"] == "attempt_1"


class _CodexServer:
    def __init__(self, grading_payload: dict):
        self.grading_payload = grading_payload
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
                    self._json({"proposal": owner.grading_payload})
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
