"""Reads of the workbench's passage projections and exchange context (migration 262). No write: the one
writer is ``db.stores.span_projections``; the read-only union and the companion's history read through
this module, and the grader may not reach it (the grader's import fences).
"""
from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterable
from typing import Any

_TABLES = {"question_event_spans": "question_event_id", "learner_text_gap_spans": "gap_id"}


def _rows(connection: sqlite3.Connection, sql: str, params: Iterable[Any] = ()) -> list[dict[str, Any]]:
    cursor = connection.execute(sql, tuple(params))
    names = [column[0] for column in cursor.description]
    return [dict(zip(names, row, strict=True)) for row in cursor.fetchall()]


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


def exchange_context_exists(connection: sqlite3.Connection, question_event_id: str) -> bool:
    return connection.execute("SELECT 1 FROM companion_exchange_context WHERE question_event_id = ?",
                              (question_event_id,)).fetchone() is not None


__all__ = ["exchange_context_exists", "exchange_contexts", "rows_for", "rows_on_readings"]
