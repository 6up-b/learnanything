"""What other test files use from ``tests/test_voi_forecasts.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from learnloop.db.repositories import Repository
from learnloop.db.stores import voi_forecasts as store
from learnloop.scheduling import action_loss as AL

from tests.causal_shadow_selection_helpers import LO_ID


def _forecasts(repository: Repository) -> list[dict]:
    with repository.connection() as connection:
        return store.list_forecasts(connection)


_STAGED_PRIOR = {"memory_lapse": 0.5, "false_belief_or_confusion": 0.5}


def _staged_loss():
    return AL.build_loss_table(
        routes=[{"reason": "memory_lapse", "first_intervention": "reveal"},
                {"reason": "false_belief_or_confusion", "first_intervention": "contrast"}],
        duration_overrides={"reveal": 2.0, "contrast": 4.0},
    )


def _separating(prefix: str) -> dict:
    return {"memory_lapse": {f"{prefix}1": 0.9, f"{prefix}2": 0.1},
            "false_belief_or_confusion": {f"{prefix}1": 0.1, f"{prefix}2": 0.9}}


def _attempt(connection, attempt_id: str, created_at: str, latency: int | None) -> None:
    connection.execute(
        "INSERT INTO practice_attempts (id, practice_item_id, learning_object_id, practice_mode, attempt_type, "
        "latency_seconds, created_at) VALUES (?, 'pi_svd_define_001', ?, 'short_answer', 'independent_attempt', ?, ?)",
        (attempt_id, LO_ID, latency, created_at),
    )
