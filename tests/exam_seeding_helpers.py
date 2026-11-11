"""What other test files use from ``tests/test_exam_seeding.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.goals.exam_seeding import parse_exam_outcomes
from learnloop.vault.loader import load_vault
from learnloop.vault.writer import upsert_practice_item

from tests.helpers import NOW, create_basic_vault


EXAM_DATE = "2026-05-01"
LIVE_NOW = NOW  # 2026-05-19, after the exam date


def _exam_vault(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    clock = FrozenClock(NOW)
    for question, rubric in (
        ("1", {"max_points": 4, "criteria": [{"id": "correctness", "points": 4, "description": "Correct."}], "fatal_errors": []}),
        (
            "2",
            {
                "max_points": 4,
                "criteria": [
                    {"id": "setup", "points": 3, "description": "Sets up the factorization."},
                    {"id": "interpretation", "points": 1, "description": "Interprets the factors."},
                ],
                "fatal_errors": [],
            },
        ),
        ("3", {"max_points": 4, "criteria": [{"id": "correctness", "points": 4, "description": "Correct."}], "fatal_errors": []}),
    ):
        upsert_practice_item(
            vault_root,
            {
                "id": f"pi_exam_q{question}",
                "learning_object_id": "lo_svd_definition",
                "subjects": None,
                "practice_mode": "constructed_response",
                "attempt_types_allowed": ["independent_attempt", "dont_know"],
                "evidence_facets": ["recall"],
                "evidence_weights": {"recall": 1.0},
                "prompt": f"Exam question {question} about SVD.",
                "expected_answer": "Model solution.",
                "tags": ["exam_question", f"exam_q:{question}"],
                "grading_rubric": rubric,
                "created_at": "2026-05-19T12:00:00Z",
                "updated_at": "2026-05-19T12:00:00Z",
            },
            clock=clock,
        )
    loaded = load_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    return vault_root, loaded, repository


def _outcomes(**overrides):
    payload = {
        "exam_date": EXAM_DATE,
        "outcomes": {
            "1": {"score": 1.0},
            "2": {"score": 0.5, "answer_md": "Half-right setup.", "confidence": 2},
            "3": {"score": 0.0},
        },
    }
    payload.update(overrides)
    return parse_exam_outcomes(payload)
