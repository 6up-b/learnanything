"""What other test files use from ``tests/test_teach_back.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from learnloop.clock import FrozenClock
from learnloop.db.repositories import MasteryState, Repository
from learnloop.vault.loader import load_vault
from learnloop.vault.writer import upsert_practice_item

from tests.helpers import ALGORITHM_VERSION, NOW, NOW_ISO, create_basic_vault


LO_ID = "lo_svd_definition"
TEACH_ITEM_ID = "pi_svd_teach_001"


def _teach_item_payload(item_id: str = TEACH_ITEM_ID) -> dict:
    return {
        "id": item_id,
        "learning_object_id": LO_ID,
        "subjects": None,
        "practice_mode": "teach_back",
        "attempt_types_allowed": ["teach_back"],
        "evidence_facets": ["definition", "geometry", "uniqueness"],
        "evidence_weights": {"definition": 1.0, "geometry": 1.0, "uniqueness": 1.0},
        "criterion_facet_weights": {
            "core_definition": {"definition": 1.0},
            "core_geometry": {"geometry": 1.0},
            "core_uniqueness": {"uniqueness": 1.0},
            "transfer_rank_deficient": {"definition": 1.0},
            "transfer_rotation": {"geometry": 1.0},
        },
        "prompt": "Teach the singular value decomposition to a curious student.",
        "expected_answer": "A full explanation of SVD: definition, geometry, uniqueness.",
        "grading_rubric": {
            "max_points": 4,
            "criteria": [
                {"id": "core_definition", "points": 1.0, "tier": "core", "description": "States what U, Sigma, V are."},
                {"id": "core_geometry", "points": 1.0, "tier": "core", "description": "Explains the rotate-scale-rotate geometry."},
                {"id": "core_uniqueness", "points": 1.0, "tier": "core", "description": "Explains what is and is not unique."},
                {"id": "transfer_rank_deficient", "points": 0.5, "tier": "transfer", "description": "What happens for a rank-deficient matrix?"},
                {"id": "transfer_rotation", "points": 0.5, "tier": "transfer", "description": "What does the SVD of a pure rotation look like?"},
            ],
            "fatal_errors": [],
        },
        "created_at": NOW_ISO,
        "updated_at": NOW_ISO,
    }


def _setup(tmp_path, *, extra_items: list[dict] | None = None):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    clock = FrozenClock(NOW)
    upsert_practice_item(vault_root, _teach_item_payload(), clock=clock)
    for payload in extra_items or []:
        upsert_practice_item(vault_root, payload, clock=clock)
    vault = load_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    return vault_root, vault, repository


def _seed_lo_evidence(repository):
    repository.upsert_mastery_state(
        MasteryState(
            learning_object_id=LO_ID,
            logit_mean=0.0,
            logit_variance=1.0,
            evidence_count=1,
            last_evidence_at="2026-05-18T12:00:00Z",
            algorithm_version=ALGORITHM_VERSION,
            updated_at=NOW_ISO,
        )
    )
