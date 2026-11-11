"""What other test files use from ``tests/test_reader_rw1c_review.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from tests.reader_tutor_retrieval_helpers import _bound_session


ITEM = "pi_determinant_2"


def _rebind(paths, ctx):
    """A fresh context after the item's YAML changed (the vault reloads)."""

    from tests.library_ask_fixtures import context

    fresh = context(paths.root)
    fresh.reader_tutor_rerank_client = ctx.reader_tutor_rerank_client
    return fresh


def _cold_attempt(repository, vault, attempt_id: str, session_id: str | None) -> None:
    item = vault.practice_items[ITEM]
    repository.insert_practice_attempt({
        "id": attempt_id, "practice_item_id": item.id, "learning_object_id": item.learning_object_id,
        "practice_mode": "short_answer", "attempt_type": "independent_attempt", "session_id": session_id,
        "created_at": "2026-01-01T00:00:00Z",
    })


def _bound_to(repository, item_id: str, practice_session_id: str) -> str:
    """A workbench session bound to the item and to one practice session (its submit counts there)."""

    session = _bound_session(repository, item_id)
    with repository.connection() as connection:
        connection.execute("UPDATE workbench_sessions SET practice_session_id = ? WHERE id = ?",
                           (practice_session_id, session))
        connection.commit()
    return session
