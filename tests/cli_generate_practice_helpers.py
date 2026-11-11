"""What other test files use from ``tests/test_cli_generate_practice.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from learnloop.clock import FrozenClock
from learnloop.db.repositories import MasteryState, Repository

from tests.helpers import NOW, NOW_ISO, configure_codex_http


def _complete_probe(sqlite_path) -> None:
    repository = Repository(sqlite_path)
    repository.upsert_mastery_state(
        MasteryState(
            learning_object_id="lo_svd_definition",
            logit_mean=0.0,
            logit_variance=0.5,
            evidence_count=3,
            last_evidence_at=NOW_ISO,
            algorithm_version="mvp-0.1",
            updated_at=NOW_ISO,
        )
    )
    repository.upsert_probe_state(
        learning_object_id="lo_svd_definition",
        status="complete",
        algorithm_version="mvp-0.1",
        probe_phase_id="probe_lo_svd_definition",
        hypothesis_set_id="hypotheses_lo_svd_definition",
        probe_attempts_completed=3,
        probe_attempts_target=3,
        completed_at=NOW_ISO,
        clock=FrozenClock(NOW),
    )


def _configure_codex(vault_root, checkout, base_url: str) -> None:
    configure_codex_http(vault_root, checkout, base_url)


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
