"""A local fake of the Decisions API (OpenRouter and Perplexity shapes).

It enforces the documented contract the client must satisfy: POST to the
dialect's path, ``Authorization: Bearer``, a JSON body with exactly
``model``/``state``/``questions`` (any other top-level field is a 400, as
Perplexity documents), 1-128 named questions with ``instructions``, and
typed criteria. It answers deterministically, with ``usage`` and, for the
OpenRouter dialect, ``id``/``provider``/``usage.cost`` and a dated model.
No network leaves the machine: the server binds 127.0.0.1.
"""
from __future__ import annotations

from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import threading
from typing import Any, Callable

ALLOWED_TOP_LEVEL = {"model", "state", "questions"}


def answer_for(name: str, question: dict[str, Any], p_yes: float = 0.73) -> dict[str, Any]:
    kind = question["type"]
    if kind == "noul":
        return {"type": "noul", "noul": p_yes}
    if kind == "choice":
        options = list(question["criteria"])
        weights = {option: 1.0 / len(options) for option in options}
        return {"type": "choice", "choice": options[0], "probabilities": weights, "confidence": 0.5}
    levels = question["criteria"]
    probabilities = {str(i): 1.0 / len(levels) for i in range(len(levels))}
    return {
        "type": "score", "score": (len(levels) - 1) / 2, "probabilities": probabilities,
        "confidence": 0.5, "legend": {str(i): level for i, level in enumerate(levels)},
    }


def validate(body: Any) -> str | None:
    """The 400 reason, or None for a valid request."""

    if not isinstance(body, dict):
        return "body is not an object"
    unknown = set(body) - ALLOWED_TOP_LEVEL
    if unknown:
        return f"Unknown field(s): {', '.join(sorted(unknown))}"
    if not body.get("model"):
        return "model is required"
    if body.get("state") is None:
        return "state must not be null"
    questions = body.get("questions")
    if not isinstance(questions, dict) or not 1 <= len(questions) <= 128:
        return "questions must hold 1 to 128 entries"
    for name, question in questions.items():
        if not name or not isinstance(question, dict) or not question.get("instructions"):
            return "every question needs a name and instructions"
        kind = question.get("type")
        if kind == "noul":
            criteria = question.get("criteria")
            if criteria is not None and set(criteria) != {"true", "false"}:
                return "noul criteria need true and false"
        elif kind == "choice":
            if not isinstance(question.get("criteria"), dict) or not 1 <= len(question["criteria"]) <= 255:
                return "choice needs 1 to 255 options"
        elif kind == "score":
            if not isinstance(question.get("criteria"), list) or not 1 <= len(question["criteria"]) <= 10:
                return "score needs 1 to 10 levels"
        else:
            return f"unknown question type {kind!r}"
    return None


class FakeDecisionsServer:
    def __init__(self, *, dialect: str = "openrouter", key: str = "test-key",
                 respond: Callable[[dict[str, Any]], tuple[int, Any, dict[str, str]] | None] | None = None,
                 p_yes: float = 0.73) -> None:
        self.dialect = dialect
        self.key = key
        self.respond = respond
        self.p_yes = p_yes
        self.requests: list[dict[str, Any]] = []
        self.path = "/api/alpha/decisions" if dialect == "openrouter" else "/v1/decisions"
        self._server: ThreadingHTTPServer | None = None

    @property
    def base_url(self) -> str:
        host, port = self._server.server_address  # type: ignore[union-attr]
        root = f"http://{host}:{port}"
        return f"{root}/api" if self.dialect == "openrouter" else root

    def handler(self):
        fake = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):  # noqa: D401 - silence the test log
                return

            def _send(self, status: int, payload: Any, headers: dict[str, str] | None = None) -> None:
                raw = json.dumps(payload).encode()
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                for key, value in (headers or {}).items():
                    self.send_header(key, value)
                self.send_header("Content-Length", str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)

            def do_GET(self):  # noqa: N802
                self._send(405, {"error": {"message": "Method not allowed", "type": "invalid_request"}})

            def do_POST(self):  # noqa: N802
                length = int(self.headers.get("Content-Length") or 0)
                raw = self.rfile.read(length)
                try:
                    body = json.loads(raw)
                except ValueError:
                    body = None
                record = {"path": self.path, "headers": dict(self.headers), "body": body}
                fake.requests.append(record)
                if self.path != fake.path:
                    self._send(404, {})
                    return
                if self.headers.get("Authorization") != f"Bearer {fake.key}":
                    self._send(401, {"error": {"message": "Missing or invalid key", "type": "auth"}})
                    return
                reason = validate(body)
                if reason is not None:
                    self._send(400, {"error": {"message": reason, "type": "invalid_request", "code": "400"}})
                    return
                if fake.respond is not None:
                    custom = fake.respond(body)
                    if custom is not None:
                        status, payload, headers = custom
                        self._send(status, payload, headers)
                        return
                answers = {name: answer_for(name, q, fake.p_yes) for name, q in body["questions"].items()}
                input_tokens = max(1, len(raw) // 4)
                payload: dict[str, Any] = {
                    "model": body["model"],
                    "answers": answers,
                    "usage": {"input_tokens": input_tokens, "output_tokens": 3},
                }
                if fake.dialect == "openrouter":
                    payload["model"] = body["model"] + "-20261006"
                    payload["id"] = f"gen-dec-{len(fake.requests)}"
                    payload["provider"] = "Perplexity"
                    payload["usage"]["cost"] = input_tokens * 0.02 / 1_000_000
                self._send(200, payload, {"x-request-id": "test"})

        return Handler

    def __enter__(self) -> "FakeDecisionsServer":
        self._server = ThreadingHTTPServer(("127.0.0.1", 0), self.handler())
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()
        return self

    def __exit__(self, *exc) -> None:
        assert self._server is not None
        self._server.shutdown()
        self._server.server_close()


@contextmanager
def fake_decisions(**kwargs):
    with FakeDecisionsServer(**kwargs) as server:
        yield server


class ScriptedDecider:
    """An in-process DecisionClient double: records states, returns P(yes)."""

    provider_name = "fake_decider"
    provider_type = "decider"

    def __init__(self, p_yes: float | Callable[[Any], float] = 0.6, model: str = "fake/decider") -> None:
        from learnloop.ai.execution import model_call, report_call_usage

        self._model_call, self._report = model_call, report_call_usage
        self.p_yes = p_yes
        self.model = model
        self.states: list[Any] = []

    def decide(self, state, questions, *, purpose):
        from learnloop.ai.decisions import DecisionResult, NoulAnswer

        self.states.append(state)
        p = self.p_yes(state) if callable(self.p_yes) else self.p_yes
        with self._model_call(self, purpose=purpose, prompt=json.dumps(state, sort_keys=True)):
            self._report({"input_tokens": 100, "output_tokens": 3, "cost": 0.000002,
                          "resolved_model": self.model + "-dated"})
            return DecisionResult(
                answers={name: NoulAnswer(p) for name in questions}, model=self.model + "-dated",
                input_tokens=100, output_tokens=3, cost=0.000002, response_id="r", provider="Fake",
            )
