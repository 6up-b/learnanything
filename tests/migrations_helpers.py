"""What other test files use from ``tests/test_migrations.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations


def _insert_attempt(connection, *, attempt_id: str, attempt_type: str) -> None:
    connection.execute(
        """
        INSERT INTO practice_attempts(
          id, practice_item_id, learning_object_id, subject, concept, practice_mode,
          attempt_type, learner_answer_md, evidence_facets_json, evidence_weights_json,
          rubric_score, correctness, confidence, latency_seconds, hints_used,
          error_type, grader_confidence, manual_review, manual_review_reason,
          created_at, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            attempt_id,
            "pi_svd",
            "lo_svd",
            "linear-algebra",
            "singular_value_decomposition",
            "constructed_response",
            attempt_type,
            "answer",
            "[]",
            "{}",
            4,
            1.0,
            5,
            10,
            0,
            None,
            0.9,
            0,
            None,
            "2026-05-19T12:00:00Z",
            "2026-05-19T12:00:00Z",
        ),
    )
