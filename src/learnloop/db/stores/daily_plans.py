"""The only SQL writer for daily-loop DL1 plan rows (migration 174).

``daily_plans`` is WORKFLOW state (status, budget, the remembered minutes).
A plan's blocks are ``attention_blocks`` rows carrying the DL1 columns
(``daily_plan_id``, ``plan_ordinal``, ``lane``, ``chosen_by``, ``decision_ref``,
``reading_json``); every decision about them is an append-only
``attention_block_events`` receipt. Nothing here is evidence, and replay never
reads these rows. Callers own the transaction (``with repository.atomic(),
repository.connection() as connection``).
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
import json
import sqlite3
from typing import Any

_PLAN_COLUMNS = (
    "id", "local_date", "kind", "parent_plan_id", "minutes_budget", "remembered_minutes",
    "minutes_source", "split_json", "admission_json", "estimator_version", "source",
    "chooser", "status", "stop_reason", "algorithm_version", "config_hash", "created_at",
    "updated_at", "completed_at",
)
_PLAN_UPDATABLE = frozenset(
    {
        "minutes_budget", "remembered_minutes", "minutes_source", "split_json", "status",
        "stop_reason", "updated_at", "completed_at",
    }
)


def _json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _loads(value: str | None) -> Any:
    return json.loads(value) if value else None


def insert_plan(connection: sqlite3.Connection, row: Mapping[str, Any]) -> None:
    values = dict(row)
    for key in ("split_json", "admission_json"):
        if not isinstance(values.get(key), str):
            values[key] = _json(values.get(key) or {})
    connection.execute(
        f"INSERT INTO daily_plans ({','.join(_PLAN_COLUMNS)}) "
        f"VALUES ({','.join('?' for _ in _PLAN_COLUMNS)})",
        tuple(values.get(column) for column in _PLAN_COLUMNS),
    )


def update_plan(connection: sqlite3.Connection, plan_id: str, **fields: Any) -> None:
    unknown = set(fields) - _PLAN_UPDATABLE
    if unknown:
        raise ValueError(f"daily_plans columns not updatable: {sorted(unknown)}")
    if not fields:
        return
    values = dict(fields)
    if "split_json" in values and not isinstance(values["split_json"], str):
        values["split_json"] = _json(values["split_json"])
    assignments = ", ".join(f"{column} = ?" for column in values)
    connection.execute(
        f"UPDATE daily_plans SET {assignments} WHERE id = ?",
        (*values.values(), plan_id),
    )


def abandon_open_plans_before(
    connection: sqlite3.Connection, local_date: str, *, now: str
) -> int:
    """An open plan from an earlier day is abandoned (§6.10): progress is kept elsewhere."""

    cursor = connection.execute(
        "UPDATE daily_plans SET status = 'abandoned', stop_reason = 'day_ended', "
        "updated_at = ?, completed_at = COALESCE(completed_at, ?) "
        "WHERE status = 'open' AND local_date < ?",
        (now, now, local_date),
    )
    return cursor.rowcount


def insert_plan_block(connection: sqlite3.Connection, row: Mapping[str, Any]) -> None:
    connection.execute(
        "INSERT INTO attention_blocks(id, session_id, commitment_id, action, subtype, "
        "budget_minutes, neighborhood_json, exit_rules_json, short_circuit_reason, "
        "content_hash, created_at, daily_plan_id, plan_ordinal, lane, chosen_by, "
        "decision_ref, reading_json) VALUES (?, ?, NULL, ?, ?, ?, ?, '[]', ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            row["id"], row.get("session_id"), row["action"], row.get("subtype"),
            float(row["budget_minutes"]), _json(dict(row.get("neighborhood") or {})),
            row.get("short_circuit_reason"), row["content_hash"], row["created_at"],
            row["daily_plan_id"], int(row["plan_ordinal"]), row.get("lane"), row["chosen_by"],
            row.get("decision_ref"),
            _json(row["reading"]) if row.get("reading") is not None else None,
        ),
    )


def append_block_event(
    connection: sqlite3.Connection,
    *,
    event_id: str,
    block_id: str,
    kind: str,
    detail: Mapping[str, Any] | None,
    created_at: str,
) -> int:
    row = connection.execute(
        "SELECT COALESCE(MAX(event_ordinal), 0) AS m FROM attention_block_events WHERE block_id = ?",
        (block_id,),
    ).fetchone()
    ordinal = int(row[0]) + 1
    connection.execute(
        "INSERT INTO attention_block_events(id, block_id, event_ordinal, kind, detail_json, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (event_id, block_id, ordinal, kind, _json(dict(detail)) if detail is not None else None, created_at),
    )
    return ordinal


# -- reads -----------------------------------------------------------------


def _plan_dict(row: sqlite3.Row | Mapping[str, Any]) -> dict[str, Any]:
    plan = dict(row)
    plan["split"] = _loads(plan.pop("split_json", None)) or {}
    plan["admission"] = _loads(plan.pop("admission_json", None)) or {}
    return plan


def plan_by_id(connection: sqlite3.Connection, plan_id: str) -> dict[str, Any] | None:
    row = connection.execute("SELECT * FROM daily_plans WHERE id = ?", (plan_id,)).fetchone()
    return _plan_dict(row) if row is not None else None


def plans_for_date(connection: sqlite3.Connection, local_date: str) -> list[dict[str, Any]]:
    rows = connection.execute(
        "SELECT * FROM daily_plans WHERE local_date = ? ORDER BY created_at, id", (local_date,)
    ).fetchall()
    return [_plan_dict(row) for row in rows]


def latest_plan(connection: sqlite3.Connection) -> dict[str, Any] | None:
    row = connection.execute(
        "SELECT * FROM daily_plans ORDER BY created_at DESC, id DESC LIMIT 1"
    ).fetchone()
    return _plan_dict(row) if row is not None else None


def all_plans(connection: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = connection.execute("SELECT * FROM daily_plans ORDER BY created_at, id").fetchall()
    return [_plan_dict(row) for row in rows]


def plan_blocks(connection: sqlite3.Connection, plan_ids: Iterable[str]) -> list[dict[str, Any]]:
    ids = list(plan_ids)
    if not ids:
        return []
    marks = ",".join("?" for _ in ids)
    rows = connection.execute(
        f"SELECT * FROM attention_blocks WHERE daily_plan_id IN ({marks}) "
        "ORDER BY daily_plan_id, plan_ordinal",
        ids,
    ).fetchall()
    blocks = []
    for row in rows:
        block = dict(row)
        block["neighborhood"] = _loads(block.pop("neighborhood_json", None)) or {}
        block["reading"] = _loads(block.pop("reading_json", None))
        blocks.append(block)
    return blocks


def block_events_for(connection: sqlite3.Connection, block_ids: Iterable[str]) -> list[dict[str, Any]]:
    ids = list(block_ids)
    if not ids:
        return []
    marks = ",".join("?" for _ in ids)
    rows = connection.execute(
        f"SELECT * FROM attention_block_events WHERE block_id IN ({marks}) "
        "ORDER BY block_id, event_ordinal",
        ids,
    ).fetchall()
    events = []
    for row in rows:
        event = dict(row)
        event["detail"] = _loads(event.pop("detail_json", None)) or {}
        events.append(event)
    return events


def daily_plan_tables_present(connection: sqlite3.Connection) -> bool:
    row = connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'daily_plans'"
    ).fetchone()
    return row is not None


__all__ = [
    "abandon_open_plans_before",
    "all_plans",
    "append_block_event",
    "block_events_for",
    "daily_plan_tables_present",
    "insert_plan",
    "insert_plan_block",
    "latest_plan",
    "plan_blocks",
    "plan_by_id",
    "plans_for_date",
    "update_plan",
]
