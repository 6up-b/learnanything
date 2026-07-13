from __future__ import annotations

import io
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.vault.loader import add_note
from learnloop.vault.writer import upsert_practice_item
from learnloop_sidecar.server import serve

from tests.helpers import NOW, NOW_ISO, create_basic_vault, seed_due_item


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
    """Point both the ai.providers.codex profile and legacy [codex] at the mock."""

    config_path = vault_root / "learnloop.toml"
    text = config_path.read_text(encoding="utf-8")
    text = text.replace('type = "codex_sdk"', 'type = "http_adapter"', 1)
    text = text.replace('provider = "sdk"', 'provider = "http"')
    text = text.replace('checkout_path = ""', f'checkout_path = "{checkout.as_posix()}"')
    text = text.replace('revision = "<pinned-commit>"', 'revision = "abc123"')
    text = text.replace('base_url = "http://127.0.0.1:8765"', f'base_url = "{base_url}"')
    config_path.write_text(text, encoding="utf-8")


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


def test_sidecar_ask_rate_transcript_and_limit(tmp_path):
    server = _TutorServer()
    server.start()
    try:
        vault_root, _paths = _tutor_vault(tmp_path, server)
        session_id = _rpc(
            [_init(vault_root), {"jsonrpc": "2.0", "id": 2, "method": "start_session", "params": {"energy": "medium"}}]
        )[1]["result"]["sessionId"]

        def ask(question: str):
            return _rpc(
                [
                    _init(vault_root),
                    {
                        "jsonrpc": "2.0",
                        "id": 2,
                        "method": "ask_tutor_question",
                        "params": {
                            "context": "practice",
                            "question": question,
                            "practiceItemId": "pi_svd_define_001",
                            "sessionId": session_id,
                            "secondsIntoAttempt": 12.0,
                        },
                    },
                ]
            )[1]

        first = ask("Why orthogonal?")["result"]
        assert first["answerMd"] == "Think about the factor shapes."
        assert first["questionType"] == "mechanism"
        assert first["facets"] == ["recall"]
        assert first["hintEquivalent"] is True
        assert first["leakSuspected"] is False
        assert first["remaining"] == 2

        second = ask("And Sigma?")["result"]
        assert second["remaining"] == 1
        # Multi-turn: the second AI call carries the first turn as thread context.
        tutor_calls = [request for request in server.requests if request["path"] == "/tutor-qa"]
        assert len(tutor_calls) == 2
        assert tutor_calls[1]["body"]["context"]["thread"][0]["question_md"] == "Why orthogonal?"

        third = ask("Third?")["result"]
        assert third["remaining"] == 0

        over = ask("Fourth?")
        assert over["error"]["data"]["code"] == "question_limit_reached"
        assert over["error"]["data"]["details"]["limit"] == 3

        transcript = _rpc(
            [
                _init(vault_root),
                {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "get_tutor_transcript",
                    "params": {
                        "context": "practice",
                        "practiceItemId": "pi_svd_define_001",
                        "sessionId": session_id,
                    },
                },
            ]
        )[1]["result"]
        assert transcript["remaining"] == 0
        assert [event["questionMd"] for event in transcript["events"]] == [
            "Why orthogonal?",
            "And Sigma?",
            "Third?",
        ]
        assert transcript["events"][0]["hintEquivalent"] is True
        assert transcript["events"][0]["secondsIntoAttempt"] == 12.0

        rated = _rpc(
            [
                _init(vault_root),
                {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "rate_tutor_answer",
                    "params": {"eventId": transcript["events"][0]["id"], "useful": True},
                },
            ]
        )[1]["result"]
        assert rated["ok"] is True
    finally:
        server.stop()


def test_sidecar_submit_attempt_counts_question_hint_equivalents(tmp_path):
    server = _TutorServer()
    server.start()
    try:
        vault_root, paths = _tutor_vault(tmp_path, server)
        session_id = _rpc(
            [_init(vault_root), {"jsonrpc": "2.0", "id": 2, "method": "start_session", "params": {"energy": "medium"}}]
        )[1]["result"]["sessionId"]

        for question in ("Why orthogonal?", "And Sigma?"):
            response = _rpc(
                [
                    _init(vault_root),
                    {
                        "jsonrpc": "2.0",
                        "id": 2,
                        "method": "ask_tutor_question",
                        "params": {
                            "context": "practice",
                            "question": question,
                            "practiceItemId": "pi_svd_define_001",
                            "sessionId": session_id,
                        },
                    },
                ]
            )[1]
            assert response["result"]["hintEquivalent"] is True

        submitted = _rpc(
            [
                _init(vault_root),
                {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "submit_attempt",
                    "params": {
                        "sessionId": session_id,
                        "practiceItemId": "pi_svd_define_001",
                        "answerMd": "SVD is U Sigma V transpose.",
                        "attemptType": "independent_attempt",
                        "hintsUsed": 0,
                    },
                },
            ]
        )[1]["result"]

        repository = Repository(paths.sqlite_path)
        attempt = repository.fetch_practice_attempt(submitted["attemptId"])
        # Two substantive questions became hint equivalents, capped at the
        # item's hint_policy.max_useful_hints (= 1 in the fixture item).
        assert attempt["hints_used"] == 1

        feedback = _rpc(
            [
                _init(vault_root),
                {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "get_feedback",
                    "params": {"attemptId": submitted["attemptId"]},
                },
            ]
        )[1]["result"]
        assert feedback["questionHintEquivalents"] == 2

        # Feedback-context questions have their own budget (5 per attempt).
        asked = _rpc(
            [
                _init(vault_root),
                {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "ask_tutor_question",
                    "params": {
                        "context": "feedback",
                        "question": "Why did I get full marks?",
                        "attemptId": submitted["attemptId"],
                    },
                },
            ]
        )[1]["result"]
        assert asked["remaining"] == 4
        assert asked["hintEquivalent"] is False
    finally:
        server.stop()


def test_sidecar_save_tutor_answer_note_and_facet_question_counts(tmp_path):
    server = _TutorServer()
    server.start()
    try:
        vault_root, _paths = _tutor_vault(tmp_path, server)
        add_note(
            vault_root,
            "linear-algebra",
            "note_svd_intro",
            "SVD intro",
            "SVD factorizes any matrix into rotations and scalings.",
            related_los=["lo_svd_definition"],
            clock=FrozenClock(NOW),
        )

        asked = _rpc(
            [
                _init(vault_root),
                {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "ask_tutor_question",
                    "params": {
                        "context": "library",
                        "question": "What is an orthogonal matrix?",
                        "noteId": "note_svd_intro",
                    },
                },
            ]
        )[1]["result"]
        assert asked["remaining"] == 7

        saved = _rpc(
            [
                _init(vault_root),
                {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "save_tutor_answer_note",
                    "params": {"eventId": asked["eventId"]},
                },
            ]
        )[1]["result"]
        note_path = Path(saved["path"])
        assert note_path.exists()
        assert saved["noteId"] == note_path.stem
        content = note_path.read_text(encoding="utf-8")
        assert "lo_svd_definition" in content
        assert "What is an orthogonal matrix?" in content
        assert "Think about the factor shapes." in content

        facets = _rpc(
            [
                _init(vault_root),
                {"jsonrpc": "2.0", "id": 2, "method": "get_facet_mastery", "params": {}},
            ]
        )[1]["result"]
        recall = next(facet for facet in facets["facets"] if facet["facetId"] == "recall")
        assert recall["questionCount"] == 1
    finally:
        server.stop()


def test_sidecar_ask_is_rejected_during_teach_back(tmp_path):
    server = _TutorServer()
    server.start()
    try:
        vault_root, _paths = _tutor_vault(tmp_path, server)
        upsert_practice_item(
            vault_root,
            {
                "id": "pi_svd_teach_001",
                "learning_object_id": "lo_svd_definition",
                "subjects": None,
                "practice_mode": "teach_back",
                "attempt_types_allowed": ["teach_back"],
                "evidence_facets": ["recall"],
                "evidence_weights": {"recall": 1.0},
                "prompt": "Teach the SVD to a curious student.",
                "expected_answer": "A full explanation of SVD.",
                "grading_rubric": {
                    "max_points": 4,
                    "criteria": [{"id": "core_definition", "points": 4, "tier": "core", "description": "Defines SVD."}],
                    "fatal_errors": [],
                },
                "created_at": NOW_ISO,
                "updated_at": NOW_ISO,
            },
            clock=FrozenClock(NOW),
        )

        response = _rpc(
            [
                _init(vault_root),
                {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "ask_tutor_question",
                    "params": {
                        "context": "practice",
                        "question": "What is the answer?",
                        "practiceItemId": "pi_svd_teach_001",
                        "sessionId": "sess_x",
                    },
                },
            ]
        )[1]

        # Server-side backstop: the tutor is disabled while the AI plays the
        # naive student — the request never reaches the provider.
        assert response["error"]["data"]["code"] == "tutor_disabled_teach_back"
        assert response["error"]["data"]["retryable"] is False
        assert [request for request in server.requests if request["path"] == "/tutor-qa"] == []
    finally:
        server.stop()


def test_sidecar_ask_requires_ready_provider(tmp_path):
    # No mock server: the routed provider is unreachable.
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    seed_due_item(paths)
    checkout = tmp_path / "codex"
    checkout.mkdir()
    (checkout / "HEAD").write_text("abc123", encoding="utf-8")
    _configure_http_provider(vault_root, checkout, "http://127.0.0.1:1")

    response = _rpc(
        [
            _init(vault_root),
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "ask_tutor_question",
                "params": {
                    "context": "practice",
                    "question": "Why?",
                    "practiceItemId": "pi_svd_define_001",
                    "sessionId": "sess_x",
                },
            },
        ]
    )[1]
    assert response["error"]["data"]["code"] == "provider_unavailable"
    assert response["error"]["data"]["retryable"] is True


# --- promote_tutor_question (spec_tutor_promotion.md §8 W4) -----------------


def test_sidecar_promote_tutor_question_dedup_route_is_idempotent(tmp_path):
    """Dedup short-circuit (route='existing_item') + a re-promote replay returns the same row."""

    server = _TutorServer(
        promotion_analysis={
            "attributed_facets": ["recall"],
            "question_nature": "mechanism",
            "attempted_in_thread": True,
            # Dedup short-circuit: the analysis names an existing item that already
            # covers this probe, so nothing gets authored (§3 Step 0).
            "covered_by_practice_item_id": "pi_svd_define_001",
        }
    )
    server.start()
    try:
        vault_root, _paths = _tutor_vault(tmp_path, server)
        session_id = _rpc(
            [_init(vault_root), {"jsonrpc": "2.0", "id": 2, "method": "start_session", "params": {"energy": "medium"}}]
        )[1]["result"]["sessionId"]

        asked = _rpc(
            [
                _init(vault_root),
                {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "ask_tutor_question",
                    "params": {
                        "context": "practice",
                        "question": "Why must U have orthonormal columns?",
                        "practiceItemId": "pi_svd_define_001",
                        "sessionId": session_id,
                    },
                },
            ]
        )[1]["result"]
        event_id = asked["eventId"]

        def do_promote():
            return _rpc(
                [
                    _init(vault_root),
                    {
                        "jsonrpc": "2.0",
                        "id": 2,
                        "method": "promote_tutor_question",
                        "params": {"eventId": event_id, "intent": "practice"},
                    },
                ]
            )[1]["result"]

        first = do_promote()
        assert first["route"] == "existing_item"
        assert first["existingPracticeItemId"] == "pi_svd_define_001"
        assert first["questionEventId"] == event_id
        assert first["intent"] == "practice"
        analysis_calls_after_first = len(
            [request for request in server.requests if request["path"] == "/promotion-analysis"]
        )
        assert analysis_calls_after_first == 1

        # Idempotent replay: same row back, no additional analysis call (the
        # service short-circuits on the existing question_promotions PK before
        # touching the provider at all).
        second = do_promote()
        assert second == first
        analysis_calls_after_second = len(
            [request for request in server.requests if request["path"] == "/promotion-analysis"]
        )
        assert analysis_calls_after_second == analysis_calls_after_first

        # The transcript surfaces the persisted promotion state (spec §2
        # idempotency: chip instead of button on remount).
        transcript = _rpc(
            [
                _init(vault_root),
                {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "get_tutor_transcript",
                    "params": {
                        "context": "practice",
                        "practiceItemId": "pi_svd_define_001",
                        "sessionId": session_id,
                    },
                },
            ]
        )[1]["result"]
        transcript_promotion = transcript["events"][0]["promotion"]
        assert transcript_promotion["existingPracticeItemId"] == "pi_svd_define_001"
    finally:
        server.stop()


def test_sidecar_promote_tutor_question_gap_rejected_in_library_context(tmp_path):
    """Gap route requires an origin LO — restricted to practice/feedback (§3, §7 Q7)."""

    server = _TutorServer()
    server.start()
    try:
        vault_root, _paths = _tutor_vault(tmp_path, server)
        add_note(
            vault_root,
            "linear-algebra",
            "note_svd_intro",
            "SVD intro",
            "SVD factorizes any matrix into rotations and scalings.",
            related_los=["lo_svd_definition"],
            clock=FrozenClock(NOW),
        )
        asked = _rpc(
            [
                _init(vault_root),
                {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "ask_tutor_question",
                    "params": {
                        "context": "library",
                        "question": "What is an orthogonal matrix?",
                        "noteId": "note_svd_intro",
                    },
                },
            ]
        )[1]["result"]

        response = _rpc(
            [
                _init(vault_root),
                {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "promote_tutor_question",
                    "params": {"eventId": asked["eventId"], "intent": "gap"},
                },
            ]
        )[1]
        assert response["error"]["data"]["code"] == "validation_error"
    finally:
        server.stop()


def test_sidecar_promote_tutor_question_requires_ready_provider(tmp_path):
    # No mock server: the routed provider is unreachable, so the handler must
    # fail fast with the same provider_unavailable shape ask_tutor_question uses,
    # before ever touching the (nonexistent) question event.
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    seed_due_item(paths)
    checkout = tmp_path / "codex"
    checkout.mkdir()
    (checkout / "HEAD").write_text("abc123", encoding="utf-8")
    _configure_http_provider(vault_root, checkout, "http://127.0.0.1:1")

    response = _rpc(
        [
            _init(vault_root),
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "promote_tutor_question",
                "params": {"eventId": "evt_nonexistent", "intent": "practice"},
            },
        ]
    )[1]
    assert response["error"]["data"]["code"] == "provider_unavailable"
    assert response["error"]["data"]["retryable"] is True
