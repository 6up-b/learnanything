"""What other test files use from ``tests/test_reader_ca2_one_ask.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations


ITEM = "pi_svd_define_001"


def _attempt(repository, attempt_id: str, created_at: str, *, hints: int = 0) -> None:
    with repository.connection() as connection:
        connection.execute(
            "INSERT INTO practice_attempts(id, practice_item_id, learning_object_id, practice_mode, attempt_type, "
            "learner_answer_md, hints_used, created_at, session_id, rubric_score) "
            "VALUES (?, ?, 'lo_svd_definition', 'short_answer', 'independent_attempt', 'my answer', ?, ?, 'sess_1', 3)",
            (attempt_id, ITEM, hints, created_at))
        connection.commit()
