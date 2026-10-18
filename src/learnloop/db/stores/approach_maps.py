"""Adaptive hints H1: ``approach_maps`` (migration 211).

Plain SQL over a caller's connection; the caller owns the transaction. The
only writer is :mod:`learnloop.hints.map_builder`. One immutable row per map
version of one practice item (WORKFLOW: paid output, never rebuilt; replay
never reads it). ``help_assists.map_id`` names a row here as a soft
reference, checked by :func:`map_exists` (no foreign key; H0 friction note 1).
"""

from __future__ import annotations

from collections.abc import Mapping
import json
import sqlite3
from typing import Any

TABLE = "approach_maps"

#: Every column, in table order (the schema test pins this against the migration).
COLUMNS: tuple[str, ...] = (
    "id", "practice_item_id", "practice_item_hash", "family_id", "version", "map_json", "seeds_json",
    "seeds_hash", "structure_hash", "validation_json", "verified_goal", "trigger", "model", "prompt_version",
    "input_hash", "created_at", "supersedes_id",
)
_JSON_COLUMNS = ("map_json", "seeds_json", "validation_json")


def table_exists(connection: sqlite3.Connection) -> bool:
    return connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", (TABLE,)
    ).fetchone() is not None


def _decode(row: sqlite3.Row | tuple[Any, ...] | None) -> dict[str, Any] | None:
    if row is None:
        return None
    record = dict(zip(COLUMNS, tuple(row)))
    for column in _JSON_COLUMNS:
        record[column.removesuffix("_json")] = json.loads(record[column] or "{}")
    record["verified_goal"] = bool(record["verified_goal"])
    return record


_SELECT = f"SELECT {', '.join(COLUMNS)} FROM approach_maps"


def insert_map(connection: sqlite3.Connection, row: Mapping[str, Any]) -> None:
    """Insert one map version. Raises ``sqlite3.IntegrityError`` when another
    builder already stored this item revision and seeds, or this version."""

    unknown = set(row) - set(COLUMNS)
    if unknown:
        raise ValueError(f"approach_maps has no columns {sorted(unknown)}")
    names = [name for name in COLUMNS if name in row]
    connection.execute(
        f"INSERT INTO approach_maps ({', '.join(names)}) VALUES ({', '.join('?' for _ in names)})",
        tuple(row[name] for name in names),
    )


def latest_map(connection: sqlite3.Connection, practice_item_id: str) -> dict[str, Any] | None:
    """The item's newest version, of any revision."""

    if not table_exists(connection):
        return None
    return _decode(connection.execute(
        f"{_SELECT} WHERE practice_item_id = ? ORDER BY version DESC LIMIT 1", (practice_item_id,)
    ).fetchone())


def current_map(connection: sqlite3.Connection, practice_item_id: str, *, practice_item_hash: str,
                structure_hash: str) -> dict[str, Any] | None:
    """The newest version built for this item revision and these item-side seeds."""

    if not table_exists(connection):
        return None
    return _decode(connection.execute(
        f"{_SELECT} WHERE practice_item_id = ? AND practice_item_hash = ? AND structure_hash = ? "
        "ORDER BY version DESC LIMIT 1",
        (practice_item_id, practice_item_hash, structure_hash),
    ).fetchone())


def next_version(connection: sqlite3.Connection, practice_item_id: str) -> tuple[int, str | None]:
    """The version a new row of the item takes, and the row it supersedes."""

    latest = connection.execute(
        "SELECT id, version FROM approach_maps WHERE practice_item_id = ? ORDER BY version DESC LIMIT 1",
        (practice_item_id,),
    ).fetchone()
    if latest is None:
        return 1, None
    return int(latest[1]) + 1, str(latest[0])


def family_template(connection: sqlite3.Connection, family_id: str, *,
                    exclude_item_id: str) -> dict[str, Any] | None:
    """The family's newest map of another item (a sibling's builder's template, §4.3)."""

    if not table_exists(connection):
        return None
    return _decode(connection.execute(
        f"{_SELECT} WHERE family_id = ? AND practice_item_id != ? ORDER BY created_at DESC, version DESC LIMIT 1",
        (family_id, exclude_item_id),
    ).fetchone())


def map_row(connection: sqlite3.Connection, map_id: str) -> dict[str, Any] | None:
    if not table_exists(connection):
        return None
    return _decode(connection.execute(f"{_SELECT} WHERE id = ?", (map_id,)).fetchone())


def map_exists(connection: sqlite3.Connection, map_id: str | None) -> bool:
    """Whether ``map_id`` names a stored map: the code check that stands in for
    a foreign key from ``help_assists.map_id`` (H0 friction note 1)."""

    if not map_id or not table_exists(connection):
        return False
    return connection.execute("SELECT 1 FROM approach_maps WHERE id = ?", (map_id,)).fetchone() is not None


def all_maps(connection: sqlite3.Connection) -> list[dict[str, Any]]:
    """Every stored version, oldest first (the report)."""

    if not table_exists(connection):
        return []
    return [record for row in connection.execute(f"{_SELECT} ORDER BY practice_item_id, version")
            if (record := _decode(row)) is not None]


__all__ = [
    "COLUMNS",
    "TABLE",
    "all_maps",
    "current_map",
    "family_template",
    "insert_map",
    "latest_map",
    "map_exists",
    "map_row",
    "next_version",
    "table_exists",
]
