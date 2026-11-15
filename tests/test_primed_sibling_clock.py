"""The primed retry's sibling ranking reads the clock it is given (K9.3).

An item answered within the repair lane's recent-attempt window ranks last, whatever else it
covers: answered minutes ago, it would re-measure short-term memory, not the retry. "Minutes ago"
is measured against the clock the caller passes, so a frozen-clock test or a replay sees its own
time, not the machine's.
"""

from __future__ import annotations

from datetime import timedelta

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths
from learnloop.vault.writer import upsert_practice_item
from learnloop_sidecar.handlers.feedback import _pick_primed_sibling

from tests.helpers import NOW, NOW_ISO, create_basic_vault, write_facets

LO_ID = "lo_svd_definition"
SOURCE_ITEM = "pi_svd_define_001"
COVERS_THE_NEED = "pi_svd_sibling_recall"
COVERS_ANOTHER = "pi_svd_sibling_explain"


def _sibling(root, item_id: str, facet: str) -> None:
    upsert_practice_item(
        root,
        {
            "id": item_id,
            "learning_object_id": LO_ID,
            "subjects": None,
            "practice_mode": "short_answer",
            "attempt_types_allowed": ["independent_attempt", "dont_know"],
            "evidence_facets": [facet],
            "evidence_weights": {facet: 1.0},
            "prompt": f"Prompt for {item_id}.",
            "expected_answer": "A factorization into U, Sigma, and V transpose.",
            "grading_rubric": {
                "max_points": 4,
                "criteria": [{"id": "correctness", "points": 4, "description": "Correct definition."}],
                "fatal_errors": [],
            },
            "created_at": NOW_ISO,
            "updated_at": NOW_ISO,
        },
        clock=FrozenClock(NOW),
    )


def test_a_sibling_answered_minutes_ago_by_the_given_clock_ranks_last(tmp_path):
    root = tmp_path / "vault"
    paths = create_basic_vault(root)
    write_facets(paths, [
        {"id": "recall", "kind": "definition", "claim": "Recall the SVD definition."},
        {"id": "explain", "kind": "definition", "claim": "Explain what the SVD's factors do."},
    ])
    _sibling(root, COVERS_THE_NEED, "recall")
    _sibling(root, COVERS_ANOTHER, "explain")
    vault = load_vault(root)
    repository = Repository(VaultPaths(vault.root, vault.config).sqlite_path)
    # The sibling that covers the need's facet was answered at NOW; the other never was.
    repository.upsert_practice_item_state(COVERS_THE_NEED, last_attempt_at=NOW_ISO, active=True)
    attempt = {"id": "att_missed", "learning_object_id": LO_ID, "practice_item_id": SOURCE_ITEM}
    need = {"target_facets": ["recall"]}

    minutes_later = FrozenClock(NOW + timedelta(minutes=10))
    picked, _ = _pick_primed_sibling(vault, repository, attempt, need, clock=minutes_later)
    assert picked.id == COVERS_ANOTHER

    # Two days on, the recent answer no longer counts against it, and covering the need wins.
    days_later = FrozenClock(NOW + timedelta(days=2))
    picked, _ = _pick_primed_sibling(vault, repository, attempt, need, clock=days_later)
    assert picked.id == COVERS_THE_NEED
