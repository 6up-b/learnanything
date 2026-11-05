"""RO0's append-only records (migration 243; spec_router_objective_v1 §4). No policy here.

Every writer runs on the caller's connection, inside its transaction, and a refused row rolls back alone (a
savepoint) with a warning: a receipt never blocks a plan or an answer, as
:func:`learnloop.db.stores.data_capture.insert_prefilter_receipt`. RO0's columns on older tables follow their row in
the same way (:func:`fill_receipt`). Receipts hold ids and numbers, no protected text. Nothing serving, scheduling,
certification or replay reads these tables.
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
    """Whether the database has the column (a vault below migration 243 has not)."""

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


#: RO0's fields on tables that existed before it (landing ruling R1). None is ever written in its row's own insert: the
#: row is inserted with its predecessor's fields and these follow in their own savepoint (:func:`fill_receipt`), so a
#: refused receipt leaves the row standing with them null. ``question_events`` holds row 1's state and the generating
#: process RO0 fills (rows 2 and 3); the three append-only tables' update guards (migration 243) allow exactly this fill.
RECEIPT_FIELDS: Mapping[str, tuple[str, ...]] = {
    "question_events": ("reveal_state_json", "hints_used_before", "scaffold_level", "preceding_tutor_move", "learner_mode",
                        "question_opportunity"),
    "plan_presentations": ("ask_available",),
    "source_exposure_events": ("initiator", "initiator_block_id", "initiator_session_id", "initiator_visit_id"),
    "decision_objectives": ("delay_json",),
    "decision_measurement_events": ("non_service_type", "delay_json"),
}
_RECEIPT_KEYS: Mapping[str, str] = {
    "question_events": "id", "plan_presentations": "id", "source_exposure_events": "id",
    "decision_objectives": "decision_id", "decision_measurement_events": "id",
}
_RECEIPT_WHAT: Mapping[str, str] = {
    "question_events": "the disclosure state and generating process of question",
    "plan_presentations": "Ask's availability on presentation",
    "source_exposure_events": "the initiator of exposure",
    "decision_objectives": "the check delay of objective",
    "decision_measurement_events": "the delay and type of measurement event",
}


def split_receipt(table: str, row: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    """``row`` as its predecessor wrote it (RO0's fields out), and RO0's fields on it that hold a value."""

    fields = RECEIPT_FIELDS[table]
    return ({key: value for key, value in row.items() if key not in fields},
            {key: row[key] for key in fields if row.get(key) is not None})


def fill_receipt(connection: sqlite3.Connection, table: str, key: Any, values: Mapping[str, Any]) -> bool:
    """RO0's fields on a row just inserted without them, in their own savepoint, or False: nothing to write (a vault
    below migration 243 has no such column), or refused, with a warning, and the row stands with them null."""

    present = {str(row[1]) for row in connection.execute(f"PRAGMA table_info({table})")}
    filled = {name: value for name, value in values.items()
              if name in RECEIPT_FIELDS[table] and value is not None and name in present}
    if not filled:
        return False
    savepoint = f"{table}_receipt_fill"
    connection.execute(f"SAVEPOINT {savepoint}")
    try:
        connection.execute(
            f"UPDATE {table} SET {', '.join(f'{name} = ?' for name in filled)} WHERE {_RECEIPT_KEYS[table]} = ?",
            [*filled.values(), key],
        )
    except sqlite3.Error:
        connection.execute(f"ROLLBACK TO {savepoint}")
        connection.execute(f"RELEASE {savepoint}")
        logger.warning("router objective: %s %s was refused", _RECEIPT_WHAT[table], key, exc_info=True)
        return False
    connection.execute(f"RELEASE {savepoint}")
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


TRACES = "router_objective_traces"
TRACE_COLUMNS: tuple[str, ...] = (
    "id", "decision_id", "decision_kind", "decision_state_id", "trace_version", "objective_version", "algorithm_version",
    "local_date", "session_id", "session_minutes", "remembered_minutes", "kappa0", "kappa_how", "kappa_regime",
    "chosen_ref", "drawn_component", "propensity", "w", "numeric_ref", "llm_status", "numeric_status",
    "stop_in_support", "guard_crossed", "window_closes_at", "trace_json", "content_hash", "created_at",
)


def insert_trace(connection: sqlite3.Connection, row: Mapping[str, Any]) -> bool:
    """RO4 §8.8: one decision's trace (migration 246), in its own savepoint; False (a warning) when refused."""

    if not table_present(connection, TRACES):
        return False
    return _append(connection, TRACES, TRACE_COLUMNS, row)


def trace(connection: sqlite3.Connection, decision_id: str) -> dict[str, Any] | None:
    """One decision's trace with its JSON decoded (read-only), or None."""

    if not table_present(connection, TRACES):
        return None
    row = connection.execute("SELECT * FROM router_objective_traces WHERE decision_id = ? OR id = ?",
                             (decision_id, decision_id)).fetchone()
    if row is None:
        return None
    found = dict(row)
    found["trace"] = json.loads(found.pop("trace_json"))
    return found


def traces(connection: sqlite3.Connection, *, since: str | None = None, limit: int | None = None) -> list[dict[str, Any]]:
    """The traces' columns (not their JSON), oldest first."""

    if not table_present(connection, TRACES):
        return []
    columns = ", ".join(column for column in TRACE_COLUMNS if column != "trace_json")
    sql = f"SELECT {columns} FROM router_objective_traces"
    parameters: list[Any] = []
    if since is not None:
        sql += " WHERE created_at >= ?"
        parameters.append(since)
    sql += " ORDER BY created_at, id"
    if limit is not None:
        sql += " LIMIT ?"
        parameters.append(int(limit))
    return [dict(row) for row in connection.execute(sql, parameters)]


def insert_goal_event(connection: sqlite3.Connection, row: Mapping[str, Any]) -> bool:
    return _append(connection, GOAL_EVENTS, GOAL_COLUMNS, row)


#: Router objective RO5 (§9): the arms' rows in migration 098's ``policy_experiment_assignments``, through its existing
#: ``experiment_id`` (``router_objective.assignments``).
ASSIGNMENTS = "policy_experiment_assignments"
ASSIGNMENT_COLUMNS: tuple[str, ...] = (
    "id", "experiment_id", "decision_id", "unit_kind", "unit_id", "variant", "propensity", "seed", "draw",
    "epsilon_margin", "near_equivalent", "design", "grade", "candidate_refs_json", "detail_json", "created_at",
)


def insert_assignment(connection: sqlite3.Connection, row: Mapping[str, Any]) -> bool:
    """One RO5 assignment, in its own savepoint; False (a warning) when refused."""

    if not table_present(connection, ASSIGNMENTS):
        return False
    return _append(connection, ASSIGNMENTS, ASSIGNMENT_COLUMNS, row)


def latest_goal_events(connection: sqlite3.Connection) -> dict[str, dict[str, Any]]:
    """Each goal's newest lifecycle row, what the next load compares its YAML against."""

    latest: dict[str, dict[str, Any]] = {}
    for row in connection.execute("SELECT * FROM goal_lifecycle_events ORDER BY created_at, id"):
        latest[str(row["goal_id"])] = dict(row)
    return latest


__all__ = [
    "ASSIGNMENTS",
    "ASSIGNMENT_COLUMNS",
    "insert_assignment",
    "DECISION_STATE",
    "TRACES",
    "TRACE_COLUMNS",
    "insert_trace",
    "trace",
    "traces",
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
    "RECEIPT_FIELDS",
    "fill_receipt",
    "session_receipt",
    "split_receipt",
    "table_present",
]
