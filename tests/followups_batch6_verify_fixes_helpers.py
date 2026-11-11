"""What other test files use from ``tests/test_followups_batch6_verify_fixes.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

import json
from datetime import UTC, datetime

from learnloop.db.stores import daily_plans as PLAN_STORE


def _today() -> str:
    return datetime.now(UTC).astimezone().date().isoformat()


def _plan_row(connection, plan_id: str, local_date: str, created_at: str, *, split_json: object = None) -> None:
    PLAN_STORE.insert_plan(connection, {
        "id": plan_id, "local_date": local_date, "kind": "normal", "minutes_budget": 25.0, "remembered_minutes": 25,
        "minutes_source": "carried", "split_json": split_json if split_json is not None else {},
        "admission_json": {}, "estimator_version": "test", "source": "test", "chooser": "test", "status": "open",
        "algorithm_version": "test", "config_hash": "test", "created_at": created_at, "updated_at": created_at})


def _block(connection, plan_id: str, block_id: str, ordinal: int | None, created_at: str) -> None:
    PLAN_STORE.insert_plan_block(connection, {
        "id": block_id, "action": "practice", "budget_minutes": 5.0, "neighborhood": {}, "content_hash": block_id,
        "created_at": created_at, "daily_plan_id": plan_id, "plan_ordinal": ordinal, "lane": "new",
        "chosen_by": "chooser"})


def _event(connection, block_id: str, kind: str, **detail: object) -> None:
    PLAN_STORE.append_block_event(connection, event_id=f"{block_id}:{kind}:{json.dumps(detail, sort_keys=True)}",
                                  block_id=block_id, kind=kind, detail=detail, created_at="2026-11-02T10:00:00+00:00")


def _plan_holds(repository, item_id: str, *resolved_by: str, plan_id: str = "dp_v1", local_date: str | None = None) -> None:
    """Today's stored plan has selected ``item_id``, not yet answered (``resolved_by``: the
    events that have resolved it since)."""

    with repository.connection() as connection:
        _plan_row(connection, plan_id, local_date or _today(), "2026-11-02T09:00:00+00:00")
        _block(connection, plan_id, f"{plan_id}_b1", 1, "2026-11-02T09:00:00+00:00")
        _event(connection, f"{plan_id}_b1", "item_planned", practice_item_id=item_id, learning_object_id="lo")
        for kind in resolved_by:
            _event(connection, f"{plan_id}_b1", kind, practice_item_id=item_id)
        connection.commit()
