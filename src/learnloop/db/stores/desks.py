"""The only SQL writer for the workbench's desks and windows (migration 262): ``desks`` and
``desk_windows``, both WORKFLOW. Views, never evidence. Callers own the transaction.
"""
from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterable, Mapping
from typing import Any

_DESK_FIELDS = frozenset({"title", "position", "focus_window_id", "goal_id", "companion_dock", "companion_shown",
                          "archived_at"})
_WINDOW_FIELDS = frozenset({"desk_id", "slot", "pane", "active", "view_json", "closed_at"})


def _rows(connection: sqlite3.Connection, sql: str, params: Iterable[Any] = ()) -> list[dict[str, Any]]:
    cursor = connection.execute(sql, tuple(params))
    names = [column[0] for column in cursor.description]
    return [dict(zip(names, row, strict=True)) for row in cursor.fetchall()]


def desk(connection: sqlite3.Connection, desk_id: str) -> dict[str, Any] | None:
    found = _rows(connection, "SELECT * FROM desks WHERE desk_id = ?", (desk_id,))
    return found[0] if found else None


def open_desks(connection: sqlite3.Connection) -> list[dict[str, Any]]:
    """Every desk not archived, in strip order (position, then id: equal keys never tie)."""

    return _rows(connection, "SELECT * FROM desks WHERE archived_at IS NULL ORDER BY position, desk_id")


def insert_desk(connection: sqlite3.Connection, *, desk_id: str, title: str, position: str, goal_id: str | None,
                companion_dock: str, now: str) -> None:
    connection.execute(
        "INSERT INTO desks (desk_id, title, position, goal_id, companion_dock, companion_shown, version, created_at, "
        "updated_at) VALUES (?, ?, ?, ?, ?, 0, 1, ?, ?)",
        (desk_id, title, position, goal_id, companion_dock, now, now),
    )


def update_desk(connection: sqlite3.Connection, desk_id: str, fields: Mapping[str, Any], now: str) -> int:
    """Set ``fields`` on one desk and count the op in its version; returns the new version."""

    unknown = set(fields) - _DESK_FIELDS
    if unknown:  # pragma: no cover - callers pass this module's own names
        raise ValueError(f"not desk fields: {sorted(unknown)}")
    assignments = "".join(f"{name} = ?, " for name in fields)
    connection.execute(
        f"UPDATE desks SET {assignments}version = version + 1, updated_at = ? WHERE desk_id = ?",
        (*fields.values(), now, desk_id),
    )
    return int(connection.execute("SELECT version FROM desks WHERE desk_id = ?", (desk_id,)).fetchone()[0])


def window(connection: sqlite3.Connection, window_id: str) -> dict[str, Any] | None:
    found = _rows(connection, "SELECT * FROM desk_windows WHERE window_id = ?", (window_id,))
    return found[0] if found else None


def open_windows(connection: sqlite3.Connection, desk_id: str) -> list[dict[str, Any]]:
    """A desk's open windows in strip order (slot, then pane)."""

    return _rows(connection, "SELECT * FROM desk_windows WHERE desk_id = ? AND closed_at IS NULL ORDER BY slot, pane",
                 (desk_id,))


def insert_window(connection: sqlite3.Connection, *, window_id: str, desk_id: str, slot: int, kind: str,
                  spec: Mapping[str, Any], view: Mapping[str, Any], now: str) -> None:
    connection.execute(
        "INSERT INTO desk_windows (window_id, desk_id, slot, pane, active, kind, spec_json, view_json, opened_at) "
        "VALUES (?, ?, ?, 0, 1, ?, ?, ?, ?)",
        (window_id, desk_id, slot, kind, json.dumps(dict(spec), sort_keys=True), json.dumps(dict(view), sort_keys=True),
         now),
    )


def update_window(connection: sqlite3.Connection, window_id: str, fields: Mapping[str, Any]) -> None:
    unknown = set(fields) - _WINDOW_FIELDS
    if unknown:  # pragma: no cover - callers pass this module's own names
        raise ValueError(f"not window fields: {sorted(unknown)}")
    if not fields:
        return
    assignments = ", ".join(f"{name} = ?" for name in fields)
    connection.execute(f"UPDATE desk_windows SET {assignments} WHERE window_id = ?", (*fields.values(), window_id))


__all__ = ["desk", "insert_desk", "insert_window", "open_desks", "open_windows", "update_desk", "update_window",
           "window"]
