"""RO0 row 11 (spec_router_objective_v1 §4): a goal's lifecycle, seen at load.

A changed goal is a competing event, and an abandoned goal counts against a policy. Contract history covers versioned
contract edits and has no pause or abandon class; status lives in the vault's YAML, which several writers and the
learner's own editor change, so a change is detected at load: each goal is compared with its newest row here.

A goal's first row is ``created``, stamped with the goal's own ``created_at`` (a goal older than RO0 is seen once and
says when it really began). ``abandoned`` has no source yet: the YAML has no such status, and a removal says whether the
goal was still active in its reason. YAML holds no reasons, so a reason names what was seen. Never raises.
"""

from __future__ import annotations

from collections.abc import Mapping
import logging
from typing import Any

from learnloop.clock import Clock, utc_now_iso
from learnloop.data_capture.gates import objective_receipts_on
from learnloop.db.stores import router_objective as store
from learnloop.ids import new_ulid

logger = logging.getLogger(__name__)

RECEIPT_VERSION = "goal_lifecycle_v1"
CREATED = "created"
DATE_CHANGED = "date_changed"
REMOVED = "removed"
RESUMED = "resumed"
#: The YAML's status, as an event. ``active`` from anything else is a resumption.
_BY_STATUS: Mapping[str, str] = {"paused": "paused", "completed": "completed", "expired": "expired", "active": RESUMED}
#: What a row's reason says: the YAML gives none, so this names what was seen.
SEEN_AT_LOAD = "seen_at_load"


def _goals(vault: Any) -> dict[str, Any]:
    goals = getattr(vault, "goals", None) or ()
    values = goals.values() if isinstance(goals, Mapping) else goals
    return {str(goal.id): goal for goal in values}


def _row(goal_id: str, event: str, *, reason: str, status: Any, previous_status: Any, due_at: Any, previous_due_at: Any,
         contract: Any, occurred_at: Any, at: str) -> dict[str, Any]:
    return {"id": new_ulid(), "goal_id": goal_id, "event": event, "reason": reason, "status": status,
            "previous_status": previous_status, "due_at": due_at, "previous_due_at": previous_due_at,
            "contract_version_id": contract, "occurred_at": occurred_at, "receipt_version": RECEIPT_VERSION, "created_at": at}


def changes(vault: Any, latest: Mapping[str, Mapping[str, Any]], *, at: str) -> list[dict[str, Any]]:
    """What the vault's goals say that the newest rows do not (pure)."""

    rows: list[dict[str, Any]] = []
    goals = _goals(vault)
    for goal_id, goal in sorted(goals.items()):
        seen = latest.get(goal_id)
        common = {"due_at": goal.due_at, "contract": goal.confirmed_contract_head_id, "at": at}
        if seen is None or seen["event"] == REMOVED:
            rows.append(_row(goal_id, CREATED, reason=SEEN_AT_LOAD, status=goal.status, previous_status=None,
                             previous_due_at=None, occurred_at=goal.created_at, **common))
            continue
        if goal.status != seen["status"]:
            rows.append(_row(goal_id, _BY_STATUS.get(str(goal.status), str(goal.status)), reason=SEEN_AT_LOAD, status=goal.status,
                             previous_status=seen["status"], previous_due_at=seen["due_at"], occurred_at=goal.updated_at,
                             **common))
        if goal.due_at != seen["due_at"]:
            rows.append(_row(goal_id, DATE_CHANGED, reason=SEEN_AT_LOAD, status=goal.status, previous_status=seen["status"],
                             previous_due_at=seen["due_at"], occurred_at=goal.updated_at, **common))
    for goal_id, seen in sorted(latest.items()):
        if goal_id not in goals and seen["event"] != REMOVED:
            reason = f"removed_while_{seen['status'] or 'unknown'}"
            rows.append(_row(goal_id, REMOVED, reason=reason, status=None, previous_status=seen["status"], due_at=None,
                             previous_due_at=seen["due_at"], contract=seen["contract_version_id"], occurred_at=None, at=at))
    return rows


def sweep(vault: Any, repository: Any, *, clock: Clock | None = None) -> int:
    """Write what changed since the last load. Returns how many rows it wrote."""

    if not objective_receipts_on(getattr(vault, "config", None)):
        return 0
    try:
        with repository.connection() as connection:
            if not store.table_present(connection, store.GOAL_EVENTS):
                return 0
            pending = changes(vault, store.latest_goal_events(connection), at=utc_now_iso(clock))
        if not pending:
            return 0
        with repository.atomic(), repository.connection() as connection:
            return sum(1 for row in pending if store.insert_goal_event(connection, row))
    except Exception:  # noqa: BLE001 - a receipt never blocks a load
        logger.warning("router objective: the goals' lifecycle was not swept", exc_info=True)
        return 0


__all__ = ["CREATED", "DATE_CHANGED", "RECEIPT_VERSION", "REMOVED", "RESUMED", "SEEN_AT_LOAD", "changes", "sweep"]
