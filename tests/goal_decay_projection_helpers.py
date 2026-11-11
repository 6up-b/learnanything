"""What other test files use from ``tests/test_goal_decay_projection.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from learnloop.clock import FrozenClock
from learnloop.vault.writer import upsert_practice_item

from tests.helpers import NOW, NOW_ISO


def _add_application_item(root) -> None:
    """A second active item on the same LO whose facet has no FSRS state."""

    upsert_practice_item(
        root,
        {
            "id": "pi_svd_apply_001",
            "learning_object_id": "lo_svd_definition",
            "subjects": None,
            "practice_mode": "short_answer",
            "attempt_types_allowed": ["independent_attempt"],
            "evidence_facets": ["application"],
            "evidence_weights": {"application": 1.0},
            "prompt": "Apply SVD to compress a matrix.",
            "expected_answer": "Truncate to the top singular values.",
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
