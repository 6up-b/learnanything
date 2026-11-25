"""What other test files use from ``tests/test_exam_session.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from learnloop.attempts.attempts import ResolvedGrade
from learnloop.clock import FrozenClock
from learnloop.goals.exam_pool import reserve_exam_pool
from learnloop.goals.exam_session import start_exam
from learnloop.vault.loader import load_vault
from learnloop.vault.writer import upsert_practice_item

from tests.helpers import NOW, NOW_ISO, create_basic_vault, seed_due_item

LO_ID = "lo_svd_definition"
GOAL_ID = "goal_linear_algebra_ml"


def _grade(rubric_score: int) -> ResolvedGrade:
    return ResolvedGrade(
        rubric_score=rubric_score,
        criterion_points={"correctness": float(rubric_score)},
        evidence_rows=[],
        error_attributions=[],
        grader_confidence=1.0,
        confidence=4,
        manual_review_reason=None,
    )


def _add_item(root, item_id, *, facets, difficulty=0.5):
    upsert_practice_item(
        root,
        {
            "id": item_id,
            "learning_object_id": LO_ID,
            "subjects": None,
            "practice_mode": "short_answer",
            "attempt_types_allowed": ["independent_attempt", "dont_know"],
            "evidence_facets": facets,
            "evidence_weights": {facet: 1.0 for facet in facets},
            "prompt": f"Prompt {item_id}.",
            "expected_answer": "Answer.",
            "difficulty": difficulty,
            "grading_rubric": {
                "max_points": 4,
                "criteria": [{"id": "correctness", "points": 4, "description": "Correct."}],
                "fatal_errors": [],
            },
            "created_at": NOW_ISO,
            "updated_at": NOW_ISO,
        },
        clock=FrozenClock(NOW),
    )


def _vault(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    _add_item(vault_root, "pi_exam_a", facets=["recall"], difficulty=0.2)
    _add_item(vault_root, "pi_exam_b", facets=["apply"], difficulty=0.6)
    repository = seed_due_item(paths)
    return load_vault(vault_root), paths, repository


def _reserved_and_started(tmp_path):
    vault, _paths, repository = _vault(tmp_path)
    reserve_exam_pool(vault, repository, vault.goals[0], item_count=2, clock=FrozenClock(NOW))
    session = start_exam(vault, repository, GOAL_ID, clock=FrozenClock(NOW))
    return vault, repository, session
