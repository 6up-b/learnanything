"""The only SQL for the learner's ink (migration 267): ``ink_strokes`` (RAW_LEDGER) and ``ink_transcriptions``
(RECEIPT), both append-only by trigger. Callers own the transaction.

An owner's saves are read in write order (``rowid``: the table refuses deletes, so it only grows), which is the order
its strokes were drawn in.
"""
from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterable, Mapping
from typing import Any

_STROKE_COLUMNS = ("ink_id", "owner_kind", "owner_id", "kind", "encoding", "strokes_blob", "content_hash",
                   "stroke_count", "pointer_meta", "client_id", "created_at")
_READING_COLUMNS = ("transcription_id", "owner_kind", "owner_id", "content_hash", "latex_md", "confidence_label",
                    "task", "provider", "model", "prompt_version", "created_at")


def _row(row: sqlite3.Row | tuple | None, columns: tuple[str, ...]) -> dict[str, Any] | None:
    if row is None:
        return None
    out = dict(zip(columns, tuple(row), strict=True))
    if "pointer_meta" in out:
        out["pointer_meta"] = json.loads(out["pointer_meta"] or "{}")
    return out


def insert_save(connection: sqlite3.Connection, row: Mapping[str, Any]) -> None:
    values = dict(row)
    values["pointer_meta"] = json.dumps(dict(values.get("pointer_meta") or {}), sort_keys=True, ensure_ascii=False)
    connection.execute(
        f"INSERT INTO ink_strokes ({', '.join(_STROKE_COLUMNS)}) VALUES ({', '.join('?' for _ in _STROKE_COLUMNS)})",
        tuple(values[column] for column in _STROKE_COLUMNS),
    )


def save(connection: sqlite3.Connection, ink_id: str) -> dict[str, Any] | None:
    return _row(connection.execute(f"SELECT {', '.join(_STROKE_COLUMNS)} FROM ink_strokes WHERE ink_id = ?",
                                   (ink_id,)).fetchone(), _STROKE_COLUMNS)


def owner_saves(connection: sqlite3.Connection, owner_kind: str, owner_id: str) -> list[dict[str, Any]]:
    """Every save and erase of one owner, in write order."""

    rows = connection.execute(
        f"SELECT {', '.join(_STROKE_COLUMNS)} FROM ink_strokes WHERE owner_kind = ? AND owner_id = ? ORDER BY rowid",
        (owner_kind, owner_id)).fetchall()
    return [_row(row, _STROKE_COLUMNS) for row in rows]  # type: ignore[misc]


def owners_with_ink(connection: sqlite3.Connection, owner_kind: str, owner_ids: Iterable[str]) -> list[str]:
    wanted = sorted(set(owner_ids))
    if not wanted:
        return []
    marks = ", ".join("?" for _ in wanted)
    rows = connection.execute(
        f"SELECT DISTINCT owner_id FROM ink_strokes WHERE owner_kind = ? AND owner_id IN ({marks}) ORDER BY owner_id",
        (owner_kind, *wanted)).fetchall()
    return [str(row[0]) for row in rows]


def annotation_exists(connection: sqlite3.Connection, annotation_id: str) -> bool:
    return connection.execute("SELECT 1 FROM source_annotations WHERE id = ?", (annotation_id,)).fetchone() is not None


def insert_reading(connection: sqlite3.Connection, row: Mapping[str, Any]) -> None:
    connection.execute(
        f"INSERT INTO ink_transcriptions ({', '.join(_READING_COLUMNS)}) "
        f"VALUES ({', '.join('?' for _ in _READING_COLUMNS)})",
        tuple(row.get(column) for column in _READING_COLUMNS),
    )


def reading_for(connection: sqlite3.Connection, owner_kind: str, owner_id: str,
                content_hash: str) -> dict[str, Any] | None:
    """The reading of exactly these strokes of this owner, if they were read."""

    return _row(connection.execute(
        f"SELECT {', '.join(_READING_COLUMNS)} FROM ink_transcriptions "
        "WHERE owner_kind = ? AND owner_id = ? AND content_hash = ?", (owner_kind, owner_id, content_hash)).fetchone(),
        _READING_COLUMNS)


def latest_reading(connection: sqlite3.Connection, owner_kind: str, owner_id: str) -> dict[str, Any] | None:
    """The owner's newest reading (of whatever strokes stood then)."""

    return _row(connection.execute(
        f"SELECT {', '.join(_READING_COLUMNS)} FROM ink_transcriptions WHERE owner_kind = ? AND owner_id = ? "
        "ORDER BY rowid DESC LIMIT 1", (owner_kind, owner_id)).fetchone(), _READING_COLUMNS)


__all__ = ["annotation_exists", "insert_reading", "insert_save", "latest_reading", "owner_saves", "owners_with_ink",
           "reading_for", "save"]
