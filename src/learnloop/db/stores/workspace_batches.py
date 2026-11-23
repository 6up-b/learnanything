"""The stored replies of the workbench's write batches (migration 262): ``desk_op_receipts`` and
``pad_op_receipts``, both RECEIPT, append-only by trigger.

A client numbers every batch it sends, desk and pad batches alike, in one sequence (spec §3.4: ``seq``
is strictly increasing per client), so the client's last applied number is the larger of the two tables'.
Callers own the transaction.
"""
from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from typing import Any

DESK = "desk"
PAD = "pad"


@dataclass(frozen=True)
class StoredReceipt:
    channel: str
    request_hash: str
    result: dict[str, Any]


def last_seq(connection: sqlite3.Connection, client_id: str) -> int:
    """The client's highest applied batch number across both channels (0: none yet)."""

    row = connection.execute(
        "SELECT MAX(seq) FROM (SELECT seq FROM desk_op_receipts WHERE client_id = ? "
        "UNION ALL SELECT seq FROM pad_op_receipts WHERE client_id = ?)",
        (client_id, client_id),
    ).fetchone()
    return int(row[0] or 0)


def find_receipt(connection: sqlite3.Connection, client_id: str, seq: int) -> StoredReceipt | None:
    for channel, table in ((DESK, "desk_op_receipts"), (PAD, "pad_op_receipts")):
        row = connection.execute(
            f"SELECT request_hash, result_json FROM {table} WHERE client_id = ? AND seq = ?", (client_id, seq)
        ).fetchone()
        if row is not None:
            return StoredReceipt(channel, str(row[0]), json.loads(row[1]))
    return None


def insert_receipt(connection: sqlite3.Connection, *, channel: str, client_id: str, seq: int, request_hash: str,
                   result: dict[str, Any], applied_at: str, pad_id: str | None = None) -> None:
    body = json.dumps(result, sort_keys=True, ensure_ascii=False)
    if channel == DESK:
        connection.execute(
            "INSERT INTO desk_op_receipts (client_id, seq, request_hash, result_json, applied_at) VALUES (?, ?, ?, ?, ?)",
            (client_id, seq, request_hash, body, applied_at),
        )
    elif channel == PAD:
        connection.execute(
            "INSERT INTO pad_op_receipts (client_id, seq, pad_id, request_hash, result_json, applied_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (client_id, seq, str(pad_id or ""), request_hash, body, applied_at),
        )
    else:  # pragma: no cover - the two channels are this module's constants
        raise ValueError(f"unknown batch channel {channel!r}")


def client_heads(connection: sqlite3.Connection) -> list[tuple[str, int]]:
    """Every client's highest applied batch number, by client id."""

    rows = connection.execute(
        "SELECT client_id, MAX(seq) FROM (SELECT client_id, seq FROM desk_op_receipts "
        "UNION ALL SELECT client_id, seq FROM pad_op_receipts) GROUP BY client_id ORDER BY client_id"
    ).fetchall()
    return [(str(row[0]), int(row[1])) for row in rows]


__all__ = ["DESK", "PAD", "StoredReceipt", "client_heads", "find_receipt", "insert_receipt", "last_seq"]
