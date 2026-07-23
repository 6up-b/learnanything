"""Sidecar contract tests for the teach-back conversation RPCs.

Mirrors tests/test_sidecar_tutor_qa.py: a mock HTTP provider serves /health,
/teach-back (naive-student questions) and /grading-proposal (full-points
grades over whatever restricted rubric it is shown).
"""

from __future__ import annotations

import io
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.vault.writer import upsert_practice_item
from learnloop_sidecar.server import serve

from tests.helpers import NOW, NOW_ISO, create_basic_vault, seed_due_item

TEACH_ITEM_ID = "pi_svd_teach_001"
LO_ID = "lo_svd_definition"


def _rpc(messages: list[dict]) -> list[dict]:
    stdin = io.StringIO("".join(json.dumps(message) + "\n" for message in messages))
    stdout = io.StringIO()
    serve(stdin, stdout)
    return [json.loads(line) for line in stdout.getvalue().splitlines()]


class _TeachBackServer:
    """Mock AI provider: /health + /teach-back + /grading-proposal."""

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
                context = body["context"]
                if self.path == "/teach-back":
                    self._json(
                        {
                            "question_md": (
                                f"Wait, I'm confused about {context['criterion_id']} — "
                                "can you explain that part again?"
                            )
                        }
                    )
                    return
                if self.path == "/grading-proposal":
                    criteria = context["rubric"]["criteria"]
                    evidence = []
                    total = 0.0
                    for criterion in criteria:
                        awarded = float(criterion["points"])
                        total += awarded
                        evidence.append(
                            {
                                "criterion_id": criterion["id"],
                                "points_awarded": awarded,
                                "evidence": f"Transcript covers {criterion['id']}.",
                            }
                        )
                    self._json(
                        {
                            "attempt_id": context["attempt_id"],
                            "practice_item_id": context["practice_item_id"],
                            "rubric_score": max(0, min(4, int(round(total)))),
                            "criterion_evidence": evidence,
                            "fatal_errors": [],
                            "error_attributions": [],
                            "grader_confidence": 0.9,
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


def _configure_http_provider(vault_root: Path, checkout: Path, base_url: str) -> None:
    config_path = vault_root / "learnloop.toml"
    text = config_path.read_text(encoding="utf-8")
    text = text.replace('type = "codex_sdk"', 'type = "http_adapter"', 1)
    text = text.replace('provider = "sdk"', 'provider = "http"')
    text = text.replace('checkout_path = ""', f'checkout_path = "{checkout.as_posix()}"')
    text = text.replace('revision = "<pinned-commit>"', 'revision = "abc123"')
    text = text.replace('base_url = "http://127.0.0.1:8765"', f'base_url = "{base_url}"')
    config_path.write_text(text, encoding="utf-8")


def _teach_item_payload() -> dict:
    return {
        "id": TEACH_ITEM_ID,
        "learning_object_id": LO_ID,
        "subjects": None,
        "practice_mode": "teach_back",
        "attempt_types_allowed": ["teach_back"],
        "evidence_facets": ["definition", "geometry", "uniqueness"],
        "evidence_weights": {"definition": 1.0, "geometry": 1.0, "uniqueness": 1.0},
        "criterion_facet_weights": {
            "core_definition": {"definition": 1.0},
            "core_geometry": {"geometry": 1.0},
            "core_uniqueness": {"uniqueness": 1.0},
            "transfer_rank_deficient": {"definition": 1.0},
            "transfer_rotation": {"geometry": 1.0},
        },
        "prompt": "Teach the singular value decomposition to a curious student.",
        "expected_answer": "A full explanation of SVD: definition, geometry, uniqueness.",
        "grading_rubric": {
            "max_points": 4,
            "criteria": [
                {"id": "core_definition", "points": 1.0, "tier": "core", "description": "States what U, Sigma, V are."},
                {"id": "core_geometry", "points": 1.0, "tier": "core", "description": "Explains the rotate-scale-rotate geometry."},
                {"id": "core_uniqueness", "points": 1.0, "tier": "core", "description": "Explains what is and is not unique."},
                {"id": "transfer_rank_deficient", "points": 0.5, "tier": "transfer", "description": "Rank-deficient matrix?"},
                {"id": "transfer_rotation", "points": 0.5, "tier": "transfer", "description": "SVD of a pure rotation?"},
            ],
            "fatal_errors": [],
        },
        "created_at": NOW_ISO,
        "updated_at": NOW_ISO,
    }


def _teach_vault(tmp_path, base_url: str):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    seed_due_item(paths)
    upsert_practice_item(vault_root, _teach_item_payload(), clock=FrozenClock(NOW))
    checkout = tmp_path / "codex"
    checkout.mkdir()
    (checkout / "HEAD").write_text("abc123", encoding="utf-8")
    _configure_http_provider(vault_root, checkout, base_url)
    return vault_root, paths


def _init(vault_root) -> dict:
    return {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"vaultPath": str(vault_root)}}


def _call(vault_root, method: str, params: dict) -> dict:
    return _rpc([_init(vault_root), {"jsonrpc": "2.0", "id": 2, "method": method, "params": params}])[1]


def _calls(vault_root, calls: list[tuple[str, dict]]) -> list[dict]:
    """Multiple RPCs within ONE sidecar process (shared in-memory ctx state)."""

    messages = [_init(vault_root)]
    for index, (method, params) in enumerate(calls, start=2):
        messages.append({"jsonrpc": "2.0", "id": index, "method": method, "params": params})
    return _rpc(messages)[1:]


def _start_session(vault_root) -> str:
    return _call(vault_root, "start_session", {"energy": "medium"})["result"]["sessionId"]


def test_sidecar_teach_back_conversation_checkpoints_and_grades(tmp_path):
    server = _TeachBackServer()
    server.start()
    try:
        vault_root, paths = _teach_vault(tmp_path, server.base_url)
        session_id = _start_session(vault_root)

        started = _call(
            vault_root,
            "start_teach_back",
            {"sessionId": session_id, "practiceItemId": TEACH_ITEM_ID},
        )["result"]
        assert started["practiceItemId"] == TEACH_ITEM_ID
        assert started["prompt"].startswith("Teach the singular value decomposition")
        assert started["budget"] == 4  # config max_followups
        assert started["state"]["turns"] == []

        def turn(answer_md: str, finish: bool = False) -> dict:
            return _call(
                vault_root,
                "submit_teach_back_turn",
                {
                    "sessionId": session_id,
                    "practiceItemId": TEACH_ITEM_ID,
                    "answerMd": answer_md,
                    "finish": finish,
                },
            )["result"]

        opening = turn("SVD factors any matrix into rotate, scale, rotate.")
        assert opening["done"] is False
        assert "confused about core_definition" in opening["questionMd"]
        assert opening["criterionId"] == "core_definition"
        assert opening["tier"] == "core"
        assert opening["questionNumber"] == 1
        assert opening["asked"] == 1
        assert opening["budget"] == 4

        # The conversation state is checkpointed (resume shape): opening + Q1.
        snapshot = _call(vault_root, "get_session", {"sessionId": session_id})["result"]
        checkpoint = snapshot["checkpoint"]
        assert checkpoint["currentPracticeItemId"] == TEACH_ITEM_ID
        teach_back = checkpoint["teachBack"]
        assert teach_back["practiceItemId"] == TEACH_ITEM_ID
        assert teach_back["askedCount"] == 1
        assert [entry["role"] for entry in teach_back["turns"]] == ["learner", "ai"]
        assert teach_back["turns"][0]["contentMd"].startswith("SVD factors")
        assert [entry["criterionId"] for entry in teach_back["planned"]] == [
            "core_definition",
            "core_geometry",
            "core_uniqueness",
            "transfer_rank_deficient",
        ]

        second = turn("U and V are orthogonal, Sigma is diagonal.")
        assert second["done"] is False
        assert second["questionNumber"] == 2

        third = turn("It rotates, scales along axes, then rotates again.")
        assert third["done"] is False
        assert third["questionNumber"] == 3

        # The guaranteed transfer slot is the last question.
        fourth = turn("Only the singular values are unique, not the factors.")
        assert fourth["done"] is False
        assert fourth["questionNumber"] == 4
        assert fourth["criterionId"] == "transfer_rank_deficient"
        assert fourth["tier"] == "transfer"

        # The AI question calls carried the transcript so far.
        teach_calls = [request for request in server.requests if request["path"] == "/teach-back"]
        assert len(teach_calls) == 4
        assert teach_calls[3]["body"]["context"]["question_number"] == 4
        assert len(teach_calls[3]["body"]["context"]["transcript"]) == 7

        final = turn("Zero singular values appear and the factorization loses uniqueness.")
        assert final["done"] is True
        attempt_id = final["attemptId"]
        assert final["rubricScore"] == 4
        assert sorted(final["gradedCriterionIds"]) == [
            "core_definition",
            "core_geometry",
            "core_uniqueness",
            "transfer_rank_deficient",
        ]
        assert "# Teach-back transcript" in final["transcriptMd"]

        repository = Repository(paths.sqlite_path)
        attempt = repository.fetch_practice_attempt(attempt_id)
        assert attempt["attempt_type"] == "teach_back"
        assert attempt["hints_used"] == 0
        # The checkpoint was cleared in the same call that recorded the attempt.
        assert repository.fetch_session_checkpoint(session_id) is None

        feedback = _call(vault_root, "get_feedback", {"attemptId": attempt_id})["result"]
        assert feedback["attemptId"] == attempt_id
        tiers = {row["criterionId"]: row["tier"] for row in feedback["criterionEvidence"]}
        assert tiers == {
            "core_definition": "core",
            "core_geometry": "core",
            "core_uniqueness": "core",
            "transfer_rank_deficient": "transfer",
        }
    finally:
        server.stop()


def test_sidecar_teach_back_finish_early_grades_only_asked_criteria(tmp_path):
    server = _TeachBackServer()
    server.start()
    try:
        vault_root, paths = _teach_vault(tmp_path, server.base_url)
        session_id = _start_session(vault_root)
        _call(vault_root, "start_teach_back", {"sessionId": session_id, "practiceItemId": TEACH_ITEM_ID})

        _call(
            vault_root,
            "submit_teach_back_turn",
            {"sessionId": session_id, "practiceItemId": TEACH_ITEM_ID, "answerMd": "Opening explanation."},
        )
        final = _call(
            vault_root,
            "submit_teach_back_turn",
            {
                "sessionId": session_id,
                "practiceItemId": TEACH_ITEM_ID,
                "answerMd": "Answer to question one.",
                "finish": True,
            },
        )["result"]
        assert final["done"] is True
        # Only the answered criterion was graded; unasked criteria contribute nothing.
        assert final["gradedCriterionIds"] == ["core_definition"]
        # Full marks on the asked subset project to full rubric score.
        assert final["rubricScore"] == 4

        repository = Repository(paths.sqlite_path)
        evidence = repository.fetch_grading_evidence(final["attemptId"])
        assert [row.criterion_id for row in evidence] == ["core_definition"]
        grading_calls = [request for request in server.requests if request["path"] == "/grading-proposal"]
        assert [c["id"] for c in grading_calls[0]["body"]["context"]["rubric"]["criteria"]] == [
            "core_definition"
        ]
    finally:
        server.stop()


def test_sidecar_teach_back_requires_ready_provider(tmp_path):
    # No mock server: the routed provider is unreachable.
    vault_root, _paths = _teach_vault(tmp_path, "http://127.0.0.1:1")
    session_id = _start_session(vault_root)
    response = _call(
        vault_root,
        "start_teach_back",
        {"sessionId": session_id, "practiceItemId": TEACH_ITEM_ID},
    )
    assert response["error"]["data"]["code"] == "provider_unavailable"
    assert response["error"]["data"]["retryable"] is True


def test_sidecar_teach_back_rejects_non_teach_back_items(tmp_path):
    server = _TeachBackServer()
    server.start()
    try:
        vault_root, _paths = _teach_vault(tmp_path, server.base_url)
        session_id = _start_session(vault_root)
        response = _call(
            vault_root,
            "start_teach_back",
            {"sessionId": session_id, "practiceItemId": "pi_svd_define_001"},
        )
        assert response["error"]["data"]["code"] == "validation_error"
    finally:
        server.stop()


def _queue_item_ids(vault_root, session_id: str) -> list[str]:
    snapshot = _call(vault_root, "get_today_queue", {"sessionId": session_id})["result"]
    return [
        item["practiceItemId"]
        for section in snapshot["sections"]
        for item in section["items"]
    ]


def test_sidecar_queue_excludes_teach_back_items_when_provider_unready(tmp_path):
    server = _TeachBackServer()
    server.start()
    try:
        vault_root, _paths = _teach_vault(tmp_path, server.base_url)
        session_id = _start_session(vault_root)
        item_ids = _queue_item_ids(vault_root, session_id)
        assert TEACH_ITEM_ID in item_ids  # provider ready: teach_back offered
    finally:
        server.stop()

    # Provider now unreachable: the teach_back item is filtered handler-side,
    # everything else keeps flowing.
    item_ids = _queue_item_ids(vault_root, session_id)
    assert TEACH_ITEM_ID not in item_ids
    assert "pi_svd_define_001" in item_ids


def test_sidecar_queue_excludes_teach_back_items_under_manual_grading(tmp_path):
    server = _TeachBackServer()
    server.start()
    try:
        vault_root, _paths = _teach_vault(tmp_path, server.base_url)
        session_id = _start_session(vault_root)
        # Question provider is ready, but grading is switched to manual in this
        # sidecar session: a transcript could be produced but never graded, so
        # the teach_back item must not be offered.
        responses = _calls(
            vault_root,
            [
                ("set_grading_provider", {"provider": "manual"}),
                ("get_today_queue", {"sessionId": session_id}),
            ],
        )
        assert responses[0]["result"]["manualGrading"] is True
        item_ids = [
            item["practiceItemId"]
            for section in responses[1]["result"]["sections"]
            for item in section["items"]
        ]
        assert TEACH_ITEM_ID not in item_ids
        assert "pi_svd_define_001" in item_ids
    finally:
        server.stop()


def test_sidecar_teach_back_finish_under_manual_grading_is_typed_and_preserves_checkpoint(tmp_path):
    server = _TeachBackServer()
    server.start()
    try:
        vault_root, paths = _teach_vault(tmp_path, server.base_url)
        session_id = _start_session(vault_root)
        _call(vault_root, "start_teach_back", {"sessionId": session_id, "practiceItemId": TEACH_ITEM_ID})
        _call(
            vault_root,
            "submit_teach_back_turn",
            {"sessionId": session_id, "practiceItemId": TEACH_ITEM_ID, "answerMd": "Opening explanation."},
        )

        # The learner switches grading to manual mid-conversation, then finishes.
        responses = _calls(
            vault_root,
            [
                ("set_grading_provider", {"provider": "manual"}),
                (
                    "submit_teach_back_turn",
                    {
                        "sessionId": session_id,
                        "practiceItemId": TEACH_ITEM_ID,
                        "answerMd": "Answer to question one.",
                        "finish": True,
                    },
                ),
            ],
        )
        error = responses[1]["error"]["data"]
        assert error["code"] == "manual_grading_unsupported"
        assert error["retryable"] is False

        # No attempt was recorded and the conversation checkpoint survived
        # (including the answer submitted with the failed finish).
        repository = Repository(paths.sqlite_path)
        checkpoint = repository.fetch_session_checkpoint(session_id)
        assert checkpoint is not None
        state = json.loads(checkpoint["current_answer"])["state"]
        assert [turn["role"] for turn in state["turns"]] == ["learner", "ai", "learner"]
        assert state["turns"][-1]["content_md"] == "Answer to question one."

        # Switching grading back off manual lets the same checkpoint finish.
        final = _call(
            vault_root,
            "submit_teach_back_turn",
            {"sessionId": session_id, "practiceItemId": TEACH_ITEM_ID, "answerMd": "", "finish": True},
        )["result"]
        assert final["done"] is True
        assert repository.fetch_session_checkpoint(session_id) is None
    finally:
        server.stop()


def test_sidecar_teach_back_finish_survives_post_step_failure(tmp_path, monkeypatch):
    server = _TeachBackServer()
    server.start()
    try:
        vault_root, paths = _teach_vault(tmp_path, server.base_url)
        session_id = _start_session(vault_root)
        _call(vault_root, "start_teach_back", {"sessionId": session_id, "practiceItemId": TEACH_ITEM_ID})
        _call(
            vault_root,
            "submit_teach_back_turn",
            {"sessionId": session_id, "practiceItemId": TEACH_ITEM_ID, "answerMd": "Opening explanation."},
        )

        def boom(*_args, **_kwargs):
            raise RuntimeError("follow-up evaluation exploded")

        monkeypatch.setattr("learnloop_sidecar.handlers.practice._evaluate_followup", boom)
        final = _call(
            vault_root,
            "submit_teach_back_turn",
            {
                "sessionId": session_id,
                "practiceItemId": TEACH_ITEM_ID,
                "answerMd": "Answer to question one.",
                "finish": True,
            },
        )["result"]

        # The attempt is recorded; a post-step failure must not fail the
        # response (which would trigger a retry and a double grade).
        assert final["done"] is True
        repository = Repository(paths.sqlite_path)
        attempts = repository.list_attempts_by_learning_object(LO_ID)
        assert [attempt["attempt_type"] for attempt in attempts] == ["teach_back"]
        assert attempts[0]["id"] == final["attemptId"]
        # And the checkpoint was cleared before the failing post-step ran.
        assert repository.fetch_session_checkpoint(session_id) is None
    finally:
        server.stop()


def test_sidecar_teach_back_finish_retry_returns_same_attempt(tmp_path):
    from learnloop_sidecar.handlers.sessions import SessionCheckpointInput, patch_checkpoint

    server = _TeachBackServer()
    server.start()
    try:
        vault_root, paths = _teach_vault(tmp_path, server.base_url)
        session_id = _start_session(vault_root)
        _call(vault_root, "start_teach_back", {"sessionId": session_id, "practiceItemId": TEACH_ITEM_ID})
        _call(
            vault_root,
            "submit_teach_back_turn",
            {"sessionId": session_id, "practiceItemId": TEACH_ITEM_ID, "answerMd": "Opening explanation."},
        )
        repository = Repository(paths.sqlite_path)
        checkpoint = repository.fetch_session_checkpoint(session_id)
        saved_answer = checkpoint["current_answer"]

        final = _call(
            vault_root,
            "submit_teach_back_turn",
            {
                "sessionId": session_id,
                "practiceItemId": TEACH_ITEM_ID,
                "answerMd": "Answer to question one.",
                "finish": True,
            },
        )["result"]
        assert final["done"] is True

        # Simulate the lost-response retry: the client never saw the result, so
        # its checkpoint (same conversation) is restored and finish is retried.
        patch_checkpoint(
            repository,
            SessionCheckpointInput(
                session_id=session_id,
                current_practice_item_id=TEACH_ITEM_ID,
                current_answer=saved_answer,
            ),
        )
        retry = _call(
            vault_root,
            "submit_teach_back_turn",
            {
                "sessionId": session_id,
                "practiceItemId": TEACH_ITEM_ID,
                "answerMd": "Answer to question one.",
                "finish": True,
            },
        )["result"]

        assert retry["done"] is True
        assert retry["attemptId"] == final["attemptId"]
        assert retry["duplicateFinish"] is True
        # Exactly one attempt exists and the transcript was graded exactly once.
        attempts = repository.list_attempts_by_learning_object(LO_ID)
        assert [attempt["id"] for attempt in attempts] == [final["attemptId"]]
        grading_calls = [request for request in server.requests if request["path"] == "/grading-proposal"]
        assert len(grading_calls) == 1
        # The retry cleared the restored checkpoint again.
        assert repository.fetch_session_checkpoint(session_id) is None
    finally:
        server.stop()


def test_sidecar_teach_back_resume_merges_pending_learner_answer(tmp_path):
    from learnloop_sidecar.handlers.sessions import SessionCheckpointInput, patch_checkpoint

    server = _TeachBackServer()
    server.start()
    try:
        vault_root, paths = _teach_vault(tmp_path, server.base_url)
        session_id = _start_session(vault_root)
        _call(vault_root, "start_teach_back", {"sessionId": session_id, "practiceItemId": TEACH_ITEM_ID})
        _call(
            vault_root,
            "submit_teach_back_turn",
            {"sessionId": session_id, "practiceItemId": TEACH_ITEM_ID, "answerMd": "Opening explanation."},
        )

        # Simulate a crash between answer persist and question generation: the
        # checkpointed state's last turn is a learner turn.
        repository = Repository(paths.sqlite_path)
        checkpoint = repository.fetch_session_checkpoint(session_id)
        envelope = json.loads(checkpoint["current_answer"])
        state = envelope["state"]
        state["turns"].append(
            {
                "role": "learner",
                "content_md": "first half of the answer",
                "criterion_id": state["turns"][-1]["criterion_id"],
            }
        )
        patch_checkpoint(
            repository,
            SessionCheckpointInput(
                session_id=session_id,
                current_practice_item_id=TEACH_ITEM_ID,
                current_answer=json.dumps({"mode": "teach_back", "state": state}, sort_keys=True),
            ),
        )

        resumed = _call(
            vault_root,
            "submit_teach_back_turn",
            {
                "sessionId": session_id,
                "practiceItemId": TEACH_ITEM_ID,
                "answerMd": "second half typed on resume",
            },
        )["result"]

        # The resumed submit's text was folded into the pending learner turn
        # (nothing silently vanishes) and the next question was generated.
        assert resumed["done"] is False
        turns = resumed["state"]["turns"]
        assert [turn["role"] for turn in turns] == ["learner", "ai", "learner", "ai"]
        assert turns[2]["contentMd"] == "first half of the answer\n\nsecond half typed on resume"
    finally:
        server.stop()


def test_sidecar_request_teach_back_finds_existing_card(tmp_path):
    server = _TeachBackServer()
    server.start()
    try:
        vault_root, _paths = _teach_vault(tmp_path, server.base_url)
        # The LO already has an active teach_back card: reuse, never mint.
        response = _call(
            vault_root, "request_teach_back", {"learningObjectId": LO_ID}
        )["result"]
        assert response["practiceItemId"] == TEACH_ITEM_ID
        assert response["created"] is False
    finally:
        server.stop()


def test_sidecar_request_teach_back_mints_and_is_idempotent(tmp_path):
    # No provider needed: find-or-mint touches only the vault. This vault has
    # NO teach_back card, so routing via a sibling item id mints one.
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    seed_due_item(paths)
    first, second = (
        call["result"]
        for call in _calls(
            vault_root,
            [
                ("request_teach_back", {"practiceItemId": "pi_svd_define_001"}),
                ("request_teach_back", {"practiceItemId": "pi_svd_define_001"}),
            ],
        )
    )
    assert first["created"] is True
    assert first["practiceItemId"].startswith("pi_")
    assert second["created"] is False
    assert second["practiceItemId"] == first["practiceItemId"]
