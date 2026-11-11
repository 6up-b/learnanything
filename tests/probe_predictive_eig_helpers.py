"""What other test files use from ``tests/test_probe_predictive_eig.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from learnloop.clock import FrozenClock
from learnloop.vault.writer import upsert_practice_item

from tests.helpers import NOW, NOW_ISO


LO_ID = "lo_svd_definition"
CLOCK = FrozenClock(NOW)


def _add_item(vault_root, item_id, surface_family):
    upsert_practice_item(
        vault_root,
        {
            "id": item_id,
            "learning_object_id": LO_ID,
            "practice_mode": "short_answer",
            "attempt_types_allowed": ["diagnostic_probe", "dont_know"],
            "evidence_facets": ["recall"],
            "prompt": f"Prompt for {item_id}.",
            "expected_answer": "Answer.",
            "surface_family": surface_family,
            "grading_rubric": {
                "max_points": 4,
                "criteria": [{"id": "correctness", "points": 4, "description": "Correct."}],
            },
            "created_at": NOW_ISO,
            "updated_at": NOW_ISO,
        },
        clock=CLOCK,
    )
