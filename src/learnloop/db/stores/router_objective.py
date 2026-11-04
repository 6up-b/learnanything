"""RO0's append-only records (migration 242; spec_router_objective_v1 §4). No policy here.

Every writer runs on the caller's connection, inside its transaction, and a refused row rolls back alone (a
savepoint) with a warning: a receipt never blocks a plan or an answer, as
:func:`learnloop.db.stores.data_capture.insert_prefilter_receipt`. Receipts hold ids and numbers, no protected
text. Nothing serving, scheduling, certification or replay reads these tables.
"""

from __future__ import annotations

from collections.abc import Mapping
import json
import logging
import sqlite3
from typing import Any
import zlib

logger = logging.getLogger(__name__)

SESSION_RECEIPTS = "session_receipts"
DECISION_STATE = "decision_state_receipts"
GOAL_EVENTS = "goal_lifecycle_events"

SESSION_COLUMNS: tuple[str, ...] = (
    "id", "session_id", "kind", "minutes_offered", "minutes_source", "local_time", "time_zone", "utc_offset_minutes",
    "device", "external_window_json", "end_reason", "end_basis", "ended_at", "plan_id", "block_id", "stop_decision_id",
    "detail_json", "receipt_version", "created_at",
)
STATE_COLUMNS: tuple[str, ...] = (
    "id", "decision_id", "decision_kind", "receipt_version", "algorithm_version", "session_id", "ad_state_hash",
    "session_active_minutes", "day_active_minutes", "pending_reports", "candidate_items", "candidate_los", "state_z",
    "raw_bytes", "stored_bytes", "created_at",
)
GOAL_COLUMNS: tuple[str, ...] = (
    "id", "goal_id", "event", "reason", "status", "previous_status", "due_at", "previous_due_at",
    "contract_version_id", "occurred_at", "receipt_version", "created_at",
)


def table_present(connection: sqlite3.Connection, table: str) -> bool:
    return connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", (table,)
    ).fetchone() is not None


def column_present(connection: sqlite3.Connection, table: str, column: str) -> bool:
    """Whether the database has the column (a vault below migration 242 has not)."""

    return any(str(row[1]) == column for row in connection.execute(f"PRAGMA table_info({table})"))


def _append(connection: sqlite3.Connection, table: str, columns: tuple[str, ...], row: Mapping[str, Any]) -> bool:
    connection.execute(f"SAVEPOINT {table}_append")
    try:
        cursor = connection.execute(
            f"INSERT OR IGNORE INTO {table} ({','.join(columns)}) VALUES ({','.join('?' for _ in columns)})",
            [row.get(column) for column in columns],
        )
    except sqlite3.Error:
        connection.execute(f"ROLLBACK TO {table}_append")
        connection.execute(f"RELEASE {table}_append")
        logger.warning("router objective: a %s row was refused", table, exc_info=True)
        return False
    connection.execute(f"RELEASE {table}_append")
    return cursor.rowcount > 0


def set_question_state(connection: sqlite3.Connection, question_event_id: str, state: str) -> bool:
    """Row 1's state on a question just inserted, or False (a warning): refused, the question stands without it."""

    connection.execute("SAVEPOINT question_state_write")
    try:
        connection.execute("UPDATE question_events SET reveal_state_json = ? WHERE id = ?", (state, question_event_id))
    except sqlite3.Error:
        connection.execute("ROLLBACK TO question_state_write")
        connection.execute("RELEASE question_state_write")
        logger.warning("router objective: the disclosure state of question %s was refused", question_event_id, exc_info=True)
        return False
    connection.execute("RELEASE question_state_write")
    return True


def insert_session_receipt(connection: sqlite3.Connection, row: Mapping[str, Any]) -> bool:
    """One session receipt, or False: refused (a warning), or that session already has one of this kind."""

    return _append(connection, SESSION_RECEIPTS, SESSION_COLUMNS, row)


def session_receipt(connection: sqlite3.Connection, session_id: str, kind: str) -> dict[str, Any] | None:
    row = connection.execute(
        "SELECT * FROM session_receipts WHERE session_id = ? AND kind = ? ORDER BY created_at, id LIMIT 1",
        (session_id, kind),
    ).fetchone()
    return dict(row) if row is not None else None


def insert_decision_state(connection: sqlite3.Connection, row: Mapping[str, Any], content: str) -> bool:
    """One decision's state, compressed, or False (a warning) when refused. ``content`` is canonical JSON."""

    raw = content.encode("utf-8")
    packed = zlib.compress(raw)
    return _append(connection, DECISION_STATE, STATE_COLUMNS,
                   {**row, "state_z": packed, "raw_bytes": len(raw), "stored_bytes": len(packed)})


def decision_state(connection: sqlite3.Connection, decision_id: str) -> dict[str, Any] | None:
    """One decision's receipt with its state decompressed (read-only), or None."""

    row = connection.execute("SELECT * FROM decision_state_receipts WHERE decision_id = ?", (decision_id,)).fetchone()
    if row is None:
        return None
    found = dict(row)
    found["state"] = json.loads(zlib.decompress(found.pop("state_z")).decode("utf-8"))
    return found


def insert_goal_event(connection: sqlite3.Connection, row: Mapping[str, Any]) -> bool:
    return _append(connection, GOAL_EVENTS, GOAL_COLUMNS, row)


def latest_goal_events(connection: sqlite3.Connection) -> dict[str, dict[str, Any]]:
    """Each goal's newest lifecycle row, what the next load compares its YAML against."""

    latest: dict[str, dict[str, Any]] = {}
    for row in connection.execute("SELECT * FROM goal_lifecycle_events ORDER BY created_at, id"):
        latest[str(row["goal_id"])] = dict(row)
    return latest


__all__ = [
    "DECISION_STATE",
    "GOAL_COLUMNS",
    "GOAL_EVENTS",
    "SESSION_COLUMNS",
    "SESSION_RECEIPTS",
    "STATE_COLUMNS",
    "column_present",
    "decision_state",
    "insert_decision_state",
    "insert_goal_event",
    "insert_session_receipt",
    "latest_goal_events",
    "session_receipt",
    "set_question_state",
    "table_present",
]
