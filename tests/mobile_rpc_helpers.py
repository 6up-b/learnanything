"""What other test files use from ``tests/test_mobile_rpc.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations


def _add_item(paths, repository, item_id: str, prompt: str) -> None:
    from learnloop.vault.writer import upsert_practice_item

    upsert_practice_item(paths.root, {
        "id": item_id, "learning_object_id": "lo_svd_definition", "subjects": None, "practice_mode": "short_answer",
        "attempt_types_allowed": ["independent_attempt"], "evidence_facets": ["recall"],
        "evidence_weights": {"recall": 1.0}, "prompt": prompt, "expected_answer": "An answer.",
        "grading_rubric": {"max_points": 4, "fatal_errors": [],
                           "criteria": [{"id": "correctness", "points": 4, "description": "Correct."}]},
        "created_at": "2026-05-16T12:00:00Z", "updated_at": "2026-05-16T12:00:00Z",
    })
    repository.upsert_practice_item_state(
        item_id, difficulty=5.0, stability=2.0, due_at="2026-05-18T12:00:00Z", last_attempt_at="2026-05-16T12:00:00Z",
        active=True,
    )
