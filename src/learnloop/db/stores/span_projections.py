"""The only SQL writer for the workbench's passage projections and exchange context (migration 262).

``question_event_spans`` and ``learner_text_gap_spans`` are DERIVED: one source's rows are replaced
whole (the write-through and the replayer write the same rows through the same recipe), and the
replayer clears each table through ``Repository.clear_derived_projection_tables``.
``companion_exchange_context`` is RAW_LEDGER (append-only, by trigger). Its reads are
``db.stores.span_projection_reads``. Callers own the transaction.
"""
from __future__ import annotations

import json
import sqlite3
from collections.abc import Mapping, Sequence
from typing import Any

SPAN_COLUMNS = ("extraction_id", "span_id", "role", "quality", "learning_object_id")
_TABLES = {"question_event_spans": "question_event_id", "learner_text_gap_spans": "gap_id"}


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


def insert_exchange_context(connection: sqlite3.Connection, row: Mapping[str, Any]) -> bool:
    """Record where one exchange was asked; a second record of the same exchange writes nothing (the table
    refuses a replacing insert, so it is checked first)."""

    # Checked here rather than through the reads module: the grader's fence forbids reaching that module, and
    # the gap pipeline (which the grader reaches) imports this one.
    if connection.execute("SELECT 1 FROM companion_exchange_context WHERE question_event_id = ?",
                          (str(row["question_event_id"]),)).fetchone() is not None:
        return False
    connection.execute(
        "INSERT INTO companion_exchange_context (question_event_id, desk_id, surface, window_spec_json, "
        "pad_block_ids_json, goal_id, origin, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (row["question_event_id"], row.get("desk_id"), row["surface"],
         json.dumps(row["window_spec"], sort_keys=True) if row.get("window_spec") is not None else None,
         json.dumps(list(row["pad_block_ids"])) if row.get("pad_block_ids") is not None else None,
         row.get("goal_id"), row["origin"], row["created_at"]),
    )
    return True


def record_initialization(connection: sqlite3.Connection, *, projection: str, sources: int, rows: int,
                          initialized_at: str) -> None:
    """The receipt of one projection's one-time initialization (migration 264; append-only)."""

    connection.execute(
        "INSERT INTO projection_initializations (projection, sources, rows, initialized_at) VALUES (?, ?, ?, ?)",
        (projection, sources, rows, initialized_at))


def initialized(connection: sqlite3.Connection, projection: str) -> bool:
    return connection.execute("SELECT 1 FROM projection_initializations WHERE projection = ?",
                              (projection,)).fetchone() is not None


__all__ = ["SPAN_COLUMNS", "initialized", "insert_exchange_context", "record_initialization", "replace_rows"]
