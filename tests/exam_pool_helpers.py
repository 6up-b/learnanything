"""What other test files use from ``tests/test_exam_pool.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from learnloop.clock import FrozenClock
from learnloop.vault.loader import load_vault
from learnloop.vault.writer import upsert_practice_item

from tests.helpers import NOW, NOW_ISO, create_basic_vault, seed_due_item


LO_ID = "lo_svd_definition"


def _add_item(root, item_id, *, facets, difficulty=0.5, surface_family=None, mode="short_answer"):
    upsert_practice_item(
        root,
        {
            "id": item_id,
            "learning_object_id": LO_ID,
            "subjects": None,
            "practice_mode": mode,
            "attempt_types_allowed": ["independent_attempt", "dont_know"],
            "evidence_facets": facets,
            "evidence_weights": {facet: 1.0 for facet in facets},
            "prompt": f"Prompt {item_id}.",
            "expected_answer": "Answer.",
            "difficulty": difficulty,
            "surface_family": surface_family,
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


def _vault_with_items(tmp_path):
    """Basic vault + several never-attempted items covering the goal's facets.

    The goal's scope is the SVD concept (all facets required by its LOs). We add
    items testing 'recall', 'apply', and 'derive' so the pool has facets to cover
    and a difficulty/surface spread to stratify over.
    """

    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    _add_item(vault_root, "pi_pool_recall_easy", facets=["recall"], difficulty=0.1, surface_family="fam_a")
    _add_item(vault_root, "pi_pool_apply_mid", facets=["apply"], difficulty=0.5, surface_family="fam_b")
    _add_item(vault_root, "pi_pool_derive_hard", facets=["derive"], difficulty=0.9, surface_family="fam_c")
    _add_item(vault_root, "pi_pool_recall_dup", facets=["recall"], difficulty=0.5, surface_family="fam_a")
    repository = seed_due_item(paths)
    return load_vault(vault_root), paths, repository
