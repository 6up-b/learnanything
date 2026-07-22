"""Outstanding-question queue (migration 102, services.question_queue,
sidecar list_question_queue / resolve_question_event).

The queue is learner-owned: a tutor-`answered` question stays `open` until the
learner marks it resolved or dismisses it, and reopening is a plain state flip.
"""

from __future__ import annotations

import io
import json
from pathlib import Path

import pytest

from learnloop.db.repositories import Repository
from learnloop.services.question_queue import (
    QuestionQueueError,
    count_open_questions,
    list_question_queue,
    set_question_resolution,
)
from learnloop.vault.loader import load_vault
from learnloop_sidecar.server import serve

from tests.helpers import create_basic_vault


def _seed(repo: Repository, event_id: str, *, question: str, created_at: str, answered: bool = True) -> None:
    repo.insert_question_event(
        {
            "id": event_id,
            "context": "practice",
            "question_md": question,
            "answer_md": "an answer" if answered else None,
            "answer_status": "answered" if answered else "failed",
            "created_at": created_at,
        }
    )


@pytest.fixture
def repo(tmp_path: Path) -> Repository:
    paths = create_basic_vault(tmp_path / "vault")
    load_vault(tmp_path / "vault")
    return Repository(paths.sqlite_path)


def test_captured_questions_start_open_and_list_newest_first(repo: Repository) -> None:
    _seed(repo, "q1", question="What is a spectral gap?", created_at="2026-07-01T10:00:00Z")
    _seed(repo, "q2", question="Why symmetric?", created_at="2026-07-02T10:00:00Z", answered=False)
    rows = list_question_queue(repo)
    assert [r["id"] for r in rows] == ["q2", "q1"]
    assert all(r["resolution"] == "open" for r in rows)
    # A tutor failure still leaves the learner's question in the queue.
    assert rows[0]["answer_status"] == "failed"
    assert count_open_questions(repo) == 2


def test_resolution_is_learner_owned_and_reopenable(repo: Repository) -> None:
    _seed(repo, "q1", question="Q", created_at="2026-07-01T10:00:00Z")
    event = set_question_resolution(repo, question_event_id="q1", resolution="resolved")
    assert event["resolution"] == "resolved"
    assert list_question_queue(repo) == []
    assert [r["id"] for r in list_question_queue(repo, resolution=None)] == ["q1"]
    # The confusion came back: reopen.
    set_question_resolution(repo, question_event_id="q1", resolution="open")
    assert count_open_questions(repo) == 1


def test_invalid_operations_raise(repo: Repository) -> None:
    with pytest.raises(QuestionQueueError):
        set_question_resolution(repo, question_event_id="missing", resolution="resolved")
    _seed(repo, "q1", question="Q", created_at="2026-07-01T10:00:00Z")
    with pytest.raises(QuestionQueueError):
        set_question_resolution(repo, question_event_id="q1", resolution="done")
    with pytest.raises(QuestionQueueError):
        list_question_queue(repo, resolution="unknown")


def test_sidecar_queue_roundtrip(tmp_path: Path) -> None:
    root = tmp_path / "vault"
    paths = create_basic_vault(root)
    load_vault(root)
    repo = Repository(paths.sqlite_path)
    _seed(repo, "q1", question="Open me", created_at="2026-07-01T10:00:00Z")
    _seed(repo, "q2", question="Settle me", created_at="2026-07-02T10:00:00Z")

    messages = [
        {"jsonrpc": "2.0", "id": 0, "method": "initialize", "params": {"vaultPath": str(root)}},
        {"jsonrpc": "2.0", "id": 1, "method": "list_question_queue", "params": {}},
        {"jsonrpc": "2.0", "id": 2, "method": "resolve_question_event", "params": {"eventId": "q2", "resolution": "resolved"}},
        {"jsonrpc": "2.0", "id": 3, "method": "list_question_queue", "params": {}},
        {"jsonrpc": "2.0", "id": 4, "method": "resolve_question_event", "params": {"eventId": "q2", "resolution": "nonsense"}},
    ]
    stdin = io.StringIO("".join(json.dumps(m) + "\n" for m in messages))
    stdout = io.StringIO()
    serve(stdin, stdout)
    out = [json.loads(line) for line in stdout.getvalue().splitlines()]

    first = out[1]["result"]
    assert first["openCount"] == 2
    assert [q["id"] for q in first["questions"]] == ["q2", "q1"]
    assert first["questions"][0]["questionMd"] == "Settle me"
    resolved = out[2]["result"]
    assert resolved == {"version": 1, "eventId": "q2", "resolution": "resolved", "openCount": 1}
    assert [q["id"] for q in out[3]["result"]["questions"]] == ["q1"]
    assert out[4]["error"]["data"]["code"] == "validation_error"
