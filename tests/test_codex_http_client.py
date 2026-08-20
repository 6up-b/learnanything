from __future__ import annotations

import json
import logging
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from learnloop.attempts.ai_contracts import GradingContext
from learnloop.ai.providers.codex_http import HttpCodexClient
from learnloop.ai.providers.codex import check_codex_runtime
from learnloop.attempts.grading import request_grading_proposal
from learnloop.diagnosis.ai_contracts import MisconceptionMatch, MisconceptionMatchContext
from learnloop.diagnosis.misconceptions import request_misconception_match
from learnloop.config import CodexConfig


def test_http_codex_client_health_and_grading_round_trip(tmp_path, caplog):
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
    caplog.set_level(logging.DEBUG, logger="learnloop.ai.providers.codex")
    try:
        config = CodexConfig(provider="http", checkout_path=str(checkout), revision="abc123", base_url=server.base_url)

        report = check_codex_runtime(tmp_path, config)
        proposal = request_grading_proposal(
            HttpCodexClient(config),
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
    request_log = _logged_event(caplog.records, "codex.http.request")
    response_log = _logged_event(caplog.records, "codex.http.response")
    assert request_log["purpose"] == "grading"
    assert request_log["path"] == "/grading-proposal"
    assert request_log["request_payload"]["context"]["learner_answer_md"] == "Answer"
    assert response_log["response"]["proposal"]["rubric_score"] == 4


def test_http_codex_client_misconception_match_round_trip(tmp_path):
    server = _CodexServer(
        {"attempt_id": "attempt_1", "practice_item_id": "pi_1", "rubric_score": 4, "criterion_evidence": [], "grader_confidence": 0.9},
        misconception_payload={"decision": "same", "misconception_id": "mis_1"},
    )
    server.start()
    try:
        config = CodexConfig(provider="http", base_url=server.base_url)
        result = request_misconception_match(
            HttpCodexClient(config),
            MisconceptionMatchContext(
                statement="halves the exponent when differentiating",
                learning_object_id="lo_1",
                candidates=[{"id": "mis_1", "statement": "drops the coefficient"}],
            )
        )
    finally:
        server.stop()

    assert isinstance(result, MisconceptionMatch)
    assert result.decision == "same"
    assert result.misconception_id == "mis_1"
    assert server.requests[0]["path"] == "/misconception-match"
    assert server.requests[0]["body"]["context"]["statement"] == "halves the exponent when differentiating"
    assert server.requests[0]["body"]["context"]["candidates"][0]["id"] == "mis_1"


def test_http_codex_client_misconception_match_bare_payload(tmp_path):
    server = _CodexServer(
        {"attempt_id": "a", "practice_item_id": "p", "rubric_score": 0, "criterion_evidence": [], "grader_confidence": 0.5},
        misconception_payload={"decision": "new"},
        misconception_bare=True,
    )
    server.start()
    try:
        config = CodexConfig(provider="http", base_url=server.base_url)
        result = request_misconception_match(
            HttpCodexClient(config),
            MisconceptionMatchContext(statement="x", learning_object_id="lo_1", candidates=[{"id": "m", "statement": "y"}])
        )
    finally:
        server.stop()

    assert isinstance(result, MisconceptionMatch)
    assert result.decision == "new"
    assert result.misconception_id is None


def _logged_event(records, event: str) -> dict:
    for record in records:
        if record.getMessage() == event:
            fields = getattr(record, "event_fields", None)
            if isinstance(fields, dict):
                return fields
    raise AssertionError(f"missing log event {event}")


class _CodexServer:
    def __init__(self, grading_payload: dict, misconception_payload: dict | None = None, misconception_bare: bool = False):
        self.grading_payload = grading_payload
        self.misconception_payload = misconception_payload
        self.misconception_bare = misconception_bare
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
                if self.path == "/misconception-match" and owner.misconception_payload is not None:
                    if owner.misconception_bare:
                        self._json(owner.misconception_payload)
                    else:
                        self._json({"proposal": owner.misconception_payload})
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
