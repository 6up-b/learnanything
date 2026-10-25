"""Reader workbench RW7a's tables (migration 217): ``reader_path_sections`` and
``reader_path_depths`` (WORKFLOW, append-only by trigger; display only).

Every function takes the caller's connection (and its transaction). Replay
and evidence never read these tables; the plan reads them only at RW7b's tag
(``source_retrieval.reading_paths.plan_path``, behind
``reading_paths.plan_uses_path``), when it chooses its reading block.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Mapping
from typing import Any

SECTION_COLUMNS = (
    "id", "extraction_id", "depth", "section_id", "label", "reason", "exercise_span_id", "learner_override",
    "ledger_id", "state_key", "model", "prompt_version", "created_at",
)
DEPTH_COLUMNS = ("id", "source_id", "depth", "created_at")


def tables_present(connection: sqlite3.Connection) -> bool:
    rows = connection.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name IN ('reader_path_sections', 'reader_path_depths')"
    ).fetchall()
    return len(rows) == 2


def _dicts(cursor: sqlite3.Cursor) -> list[dict[str, Any]]:
    names = [column[0] for column in cursor.description or ()]
    return [dict(zip(names, row)) for row in cursor.fetchall()]


def insert_depth(connection: sqlite3.Connection, row: Mapping[str, Any]) -> None:
    connection.execute(
        f"INSERT INTO reader_path_depths ({','.join(DEPTH_COLUMNS)}) VALUES ({','.join('?' for _ in DEPTH_COLUMNS)})",
        tuple(row[column] for column in DEPTH_COLUMNS))


def latest_depth(connection: sqlite3.Connection, source_id: str) -> dict[str, Any] | None:
    rows = _dicts(connection.execute(
        "SELECT * FROM reader_path_depths WHERE source_id = ? ORDER BY created_at DESC, id DESC LIMIT 1",
        (source_id,)))
    return rows[0] if rows else None


def insert_section(connection: sqlite3.Connection, row: Mapping[str, Any]) -> None:
    connection.execute(
        f"INSERT INTO reader_path_sections ({','.join(SECTION_COLUMNS)}) "
        f"VALUES ({','.join('?' for _ in SECTION_COLUMNS)})",
        tuple(row.get(column) for column in SECTION_COLUMNS))


def judged(connection: sqlite3.Connection, extraction_id: str, depth: str, state_key: str) -> list[dict[str, Any]]:
    """The judge's rows for exactly this state (the cache hit)."""

    return _dicts(connection.execute(
        "SELECT * FROM reader_path_sections WHERE extraction_id = ? AND depth = ? AND state_key = ? "
        "AND learner_override IS NULL ORDER BY created_at, id", (extraction_id, depth, state_key)))


def latest_judged(connection: sqlite3.Connection, extraction_id: str, depth: str) -> list[dict[str, Any]]:
    """The judge's rows of the newest state judged at this depth (shown while
    a newer state is being judged)."""

    newest = connection.execute(
        "SELECT state_key FROM reader_path_sections WHERE extraction_id = ? AND depth = ? "
        "AND learner_override IS NULL ORDER BY created_at DESC, id DESC LIMIT 1", (extraction_id, depth)).fetchone()
    if newest is None:
        return []
    return judged(connection, extraction_id, depth, str(newest[0]))


def overrides(connection: sqlite3.Connection, extraction_id: str, depth: str) -> dict[str, dict[str, Any]]:
    """The newest learner override per section at this depth (kept across
    re-judgments); ``none`` is a cleared one."""

    found: dict[str, dict[str, Any]] = {}
    for row in _dicts(connection.execute(
            "SELECT * FROM reader_path_sections WHERE extraction_id = ? AND depth = ? "
            "AND learner_override IS NOT NULL ORDER BY created_at, id", (extraction_id, depth))):
        found[str(row["section_id"])] = row
    return found


__all__ = [
    "DEPTH_COLUMNS",
    "SECTION_COLUMNS",
    "insert_depth",
    "insert_section",
    "judged",
    "latest_depth",
    "latest_judged",
    "overrides",
    "tables_present",
]
