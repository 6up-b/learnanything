"""The only SQL writer for the workbench's passage projections and exchange context (migration 262).

``question_event_spans`` and ``learner_text_gap_spans`` are DERIVED: one source's rows are replaced
whole (the write-through and the replayer write the same rows through the same recipe), and the
replayer clears each table through ``Repository.clear_derived_projection_tables``.
``companion_exchange_context`` is RAW_LEDGER (append-only, by trigger). Callers own the transaction.
"""
from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterable, Mapping, Sequence
from typing import Any

SPAN_COLUMNS = ("extraction_id", "span_id", "role", "quality", "learning_object_id")
_TABLES = {"question_event_spans": "question_event_id", "learner_text_gap_spans": "gap_id"}


def _rows(connection: sqlite3.Connection, sql: str, params: Iterable[Any] = ()) -> list[dict[str, Any]]:
    cursor = connection.execute(sql, tuple(params))
    names = [column[0] for column in cursor.description]
    return [dict(zip(names, row, strict=True)) for row in cursor.fetchall()]


def replace_rows(connection: sqlite3.Connection, table: str, owner_id: str, rows: Sequence[Mapping[str, Any]]) -> int:
    """Replace one source's projected rows (a source projected twice keeps one copy of each row)."""

    key = _TABLES[table]
    connection.execute(f"DELETE FROM {table} WHERE {key} = ?", (owner_id,))
    columns = (key, *SPAN_COLUMNS)
    written = 0
    for row in rows:
        cursor = connection.execute(
            f"INSERT OR IGNORE INTO {table} ({','.join(columns)}) VALUES ({','.join('?' for _ in columns)})",
            (owner_id, *(row.get(column) for column in SPAN_COLUMNS)),
        )
        written += cursor.rowcount
    return written


def rows_for(connection: sqlite3.Connection, table: str, owner_ids: Iterable[str] | None = None) -> list[dict[str, Any]]:
    key = _TABLES[table]
    if owner_ids is None:
        return _rows(connection, f"SELECT * FROM {table} ORDER BY {key}, extraction_id, span_id, role, "
                                 "learning_object_id")
    wanted = sorted(set(owner_ids))
    if not wanted:
        return []
    marks = ",".join("?" for _ in wanted)
    return _rows(connection, f"SELECT * FROM {table} WHERE {key} IN ({marks}) ORDER BY {key}, extraction_id, span_id, "
                             "role, learning_object_id", wanted)


def rows_on_readings(connection: sqlite3.Connection, table: str, extraction_ids: Iterable[str]) -> list[dict[str, Any]]:
    wanted = sorted(set(extraction_ids))
    if not wanted:
        return []
    marks = ",".join("?" for _ in wanted)
    return _rows(connection, f"SELECT * FROM {table} WHERE extraction_id IN ({marks})", wanted)


def insert_exchange_context(connection: sqlite3.Connection, row: Mapping[str, Any]) -> bool:
    """Record where one exchange was asked; a second record of the same exchange is ignored."""

    cursor = connection.execute(
        "INSERT OR IGNORE INTO companion_exchange_context (question_event_id, desk_id, surface, window_spec_json, "
        "pad_block_ids_json, goal_id, origin, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (row["question_event_id"], row.get("desk_id"), row["surface"],
         json.dumps(row["window_spec"], sort_keys=True) if row.get("window_spec") is not None else None,
         json.dumps(list(row["pad_block_ids"])) if row.get("pad_block_ids") is not None else None,
         row.get("goal_id"), row["origin"], row["created_at"]),
    )
    return cursor.rowcount > 0


def exchange_contexts(connection: sqlite3.Connection, question_event_ids: Iterable[str]) -> dict[str, dict[str, Any]]:
    wanted = sorted(set(question_event_ids))
    if not wanted:
        return {}
    marks = ",".join("?" for _ in wanted)
    out: dict[str, dict[str, Any]] = {}
    for row in _rows(connection, f"SELECT * FROM companion_exchange_context WHERE question_event_id IN ({marks})",
                     wanted):
        row["window_spec"] = json.loads(row.pop("window_spec_json")) if row.get("window_spec_json") else None
        row["pad_block_ids"] = json.loads(row.pop("pad_block_ids_json")) if row.get("pad_block_ids_json") else None
        out[str(row["question_event_id"])] = row
    return out


__all__ = ["SPAN_COLUMNS", "exchange_contexts", "insert_exchange_context", "replace_rows", "rows_for",
           "rows_on_readings"]
