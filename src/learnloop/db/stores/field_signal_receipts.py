"""The only SQL writer for RW2d's ``field_signal_receipts`` (migration 219).

A RECEIPT table, append-only by trigger: what the predecessor's field
derivation and placement rule would have decided where RW2d's workbench
signals changed a placement decision. Never evidence, never read by serving.
Callers own the transaction.
"""
from __future__ import annotations

from collections.abc import Mapping
import sqlite3
from typing import Any

_COLUMNS = (
    "id", "receipt_key", "decision_kind", "decision_ref", "learning_object_id", "signal_ids_json",
    "predecessor_json", "successor_json", "signal_version", "algorithm_version", "created_at",
)


def table_present(connection: sqlite3.Connection) -> bool:
    return connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'field_signal_receipts'"
    ).fetchone() is not None


def insert_receipt(connection: sqlite3.Connection, row: Mapping[str, Any]) -> bool:
    """Insert once per ``receipt_key``; True when a new row was written."""

    cursor = connection.execute(
        f"INSERT OR IGNORE INTO field_signal_receipts ({','.join(_COLUMNS)}) "
        f"VALUES ({','.join('?' for _ in _COLUMNS)})",
        tuple(row.get(column) for column in _COLUMNS),
    )
    return cursor.rowcount == 1


def receipts(connection: sqlite3.Connection, *, learning_object_id: str | None = None) -> list[dict[str, Any]]:
    if not table_present(connection):
        return []
    sql = "SELECT * FROM field_signal_receipts"
    params: tuple[Any, ...] = ()
    if learning_object_id is not None:
        sql += " WHERE learning_object_id = ?"
        params = (learning_object_id,)
    cursor = connection.execute(sql + " ORDER BY created_at, id", params)
    names = [column[0] for column in cursor.description]
    return [dict(zip(names, row, strict=True)) for row in cursor.fetchall()]


__all__ = ["insert_receipt", "receipts", "table_present"]
