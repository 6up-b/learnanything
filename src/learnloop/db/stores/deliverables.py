"""Deliverable curriculum C0b's tables (migration 228): ``deliverable_scope_inputs``
(RAW_LEDGER), ``deliverable_scope_resolutions`` and ``deliverable_path_sections``
(WORKFLOW). Append-only by trigger; display only.

Every function takes the caller's connection (and its transaction). Replay,
the plan, scheduling, grading and serving never read these tables.
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterable, Mapping
from typing import Any

INPUT_COLUMNS = ("id", "goal_id", "kind", "text_md", "extraction_id", "span_ids_json", "context_json", "created_at")
RESOLUTION_COLUMNS = (
    "id", "goal_id", "origin", "input_ids_json", "learning_objects_json", "unmatched_json", "facet_scope_json",
    "state_key", "ledger_id", "model", "prompt_version", "created_at",
)
PATH_COLUMNS = (
    "id", "goal_id", "depth", "learning_object_id", "extraction_id", "section_id", "label", "ordinal", "reason",
    "exercise_span_id", "learner_override", "commitment_id", "state_key", "ledger_id", "model", "prompt_version",
    "created_at",
)
_JSON = ("span_ids_json", "context_json", "input_ids_json", "learning_objects_json", "unmatched_json",
         "facet_scope_json")


def tables_present(connection: sqlite3.Connection) -> bool:
    found = {str(row[0]) for row in connection.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name IN "
        "('deliverable_scope_inputs', 'deliverable_scope_resolutions', 'deliverable_path_sections')")}
    return len(found) == 3


def _dicts(cursor: sqlite3.Cursor) -> list[dict[str, Any]]:
    names = [column[0] for column in cursor.description or ()]
    rows = []
    for values in cursor.fetchall():
        row = dict(zip(names, values))
        for column in _JSON:
            if column in row:
                try:
                    row[column[: -len("_json")]] = json.loads(row.get(column) or "null")
                except (TypeError, ValueError):
                    row[column[: -len("_json")]] = None
        rows.append(row)
    return rows


def _insert(connection: sqlite3.Connection, table: str, columns: tuple[str, ...], row: Mapping[str, Any]) -> None:
    connection.execute(
        f"INSERT INTO {table} ({','.join(columns)}) VALUES ({','.join('?' for _ in columns)})",
        tuple(row.get(column) for column in columns))


# -- scope inputs --------------------------------------------------------------------------------

def insert_input(connection: sqlite3.Connection, row: Mapping[str, Any]) -> None:
    _insert(connection, "deliverable_scope_inputs", INPUT_COLUMNS, row)


def inputs(connection: sqlite3.Connection, goal_id: str) -> list[dict[str, Any]]:
    """The goal's scope inputs in the order the learner gave them."""

    return _dicts(connection.execute(
        "SELECT * FROM deliverable_scope_inputs WHERE goal_id = ? ORDER BY created_at, rowid", (goal_id,)))


def goals_with_inputs(connection: sqlite3.Connection) -> list[str]:
    return [str(row[0]) for row in connection.execute(
        "SELECT DISTINCT goal_id FROM deliverable_scope_inputs ORDER BY goal_id")]


# -- resolutions ---------------------------------------------------------------------------------

def insert_resolution(connection: sqlite3.Connection, row: Mapping[str, Any]) -> None:
    _insert(connection, "deliverable_scope_resolutions", RESOLUTION_COLUMNS, row)


def latest_resolution(connection: sqlite3.Connection, goal_id: str) -> dict[str, Any] | None:
    rows = _dicts(connection.execute(
        "SELECT * FROM deliverable_scope_resolutions WHERE goal_id = ? ORDER BY created_at DESC, rowid DESC LIMIT 1",
        (goal_id,)))
    return rows[0] if rows else None


def resolution(connection: sqlite3.Connection, resolution_id: str) -> dict[str, Any] | None:
    rows = _dicts(connection.execute("SELECT * FROM deliverable_scope_resolutions WHERE id = ?", (resolution_id,)))
    return rows[0] if rows else None


def resolver_state(connection: sqlite3.Connection, goal_id: str, state_key: str) -> dict[str, Any] | None:
    """The newest resolver row for exactly this state (the cache hit)."""

    rows = _dicts(connection.execute(
        "SELECT * FROM deliverable_scope_resolutions WHERE goal_id = ? AND state_key = ? AND origin = 'resolver' "
        "ORDER BY created_at DESC, rowid DESC LIMIT 1", (goal_id, state_key)))
    return rows[0] if rows else None


def resolved_goals(connection: sqlite3.Connection) -> list[str]:
    return [str(row[0]) for row in connection.execute(
        "SELECT DISTINCT goal_id FROM deliverable_scope_resolutions ORDER BY goal_id")]


# -- path rows -----------------------------------------------------------------------------------

def insert_path_row(connection: sqlite3.Connection, row: Mapping[str, Any]) -> None:
    _insert(connection, "deliverable_path_sections", PATH_COLUMNS, row)


def judged(connection: sqlite3.Connection, goal_id: str, depth: str, state_key: str) -> list[dict[str, Any]]:
    """The judge's rows for exactly this goal, depth and state (the cache hit)."""

    return _dicts(connection.execute(
        "SELECT * FROM deliverable_path_sections WHERE goal_id = ? AND depth = ? AND state_key = ? "
        "AND learner_override IS NULL ORDER BY ordinal, rowid", (goal_id, depth, state_key)))


def latest_judged(connection: sqlite3.Connection, goal_id: str, depth: str) -> list[dict[str, Any]]:
    """The newest judgment's rows at this depth (whatever its state)."""

    row = connection.execute(
        "SELECT state_key FROM deliverable_path_sections WHERE goal_id = ? AND depth = ? "
        "AND learner_override IS NULL ORDER BY created_at DESC, rowid DESC LIMIT 1", (goal_id, depth)).fetchone()
    return judged(connection, goal_id, depth, str(row[0])) if row is not None else []


def overrides(connection: sqlite3.Connection, goal_id: str, depth: str) -> dict[str, dict[str, Any]]:
    """The learner's newest row per LO at this depth (``none`` included: it clears)."""

    out: dict[str, dict[str, Any]] = {}
    for row in _dicts(connection.execute(
            "SELECT * FROM deliverable_path_sections WHERE goal_id = ? AND depth = ? AND learner_override IS NOT NULL "
            "ORDER BY created_at, rowid", (goal_id, depth))):
        out[str(row["learning_object_id"])] = row
    return out


def rows_naming(connection: sqlite3.Connection, extraction_ids: Iterable[str]) -> list[dict[str, Any]]:
    wanted = sorted({str(extraction_id) for extraction_id in extraction_ids})
    if not wanted:
        return []
    return _dicts(connection.execute(
        f"SELECT * FROM deliverable_path_sections WHERE extraction_id IN ({','.join('?' for _ in wanted)}) "
        "ORDER BY created_at, rowid", wanted))


def all_path_rows(connection: sqlite3.Connection) -> list[dict[str, Any]]:
    return _dicts(connection.execute("SELECT * FROM deliverable_path_sections ORDER BY created_at, rowid"))


__all__ = [
    "INPUT_COLUMNS",
    "PATH_COLUMNS",
    "RESOLUTION_COLUMNS",
    "all_path_rows",
    "goals_with_inputs",
    "inputs",
    "insert_input",
    "insert_path_row",
    "insert_resolution",
    "judged",
    "latest_judged",
    "latest_resolution",
    "overrides",
    "resolution",
    "resolved_goals",
    "resolver_state",
    "rows_naming",
    "tables_present",
]
