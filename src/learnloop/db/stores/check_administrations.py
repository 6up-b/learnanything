"""The only SQL for the Reader's inline check administrations (migration 270): ``check_administrations`` (WORKFLOW:
the open administration and the lock it holds with Today) and the append-only ``check_veil_sets`` (RECEIPT: what each
protection computation veiled and what had been opened). Callers own the transaction for writes.
"""
from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterable, Mapping, Sequence
from typing import Any

_ADMIN_COLUMNS = (
    "administration_token", "request_id", "commitment_id", "surface", "session_id", "practice_item_id", "contract_hash",
    "cold", "state", "protection_method", "exposure_json", "submission_id", "attempt_id", "opened_at", "closed_at",
)


def table_present(connection: sqlite3.Connection) -> bool:
    return connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'check_administrations'").fetchone() is not None


def _admin(row: sqlite3.Row | Sequence[Any] | None) -> dict[str, Any] | None:
    if row is None:
        return None
    out = dict(zip(_ADMIN_COLUMNS, tuple(row), strict=True))
    out["cold"] = bool(out["cold"])
    out["exposure"] = json.loads(out.pop("exposure_json") or "[]")
    return out


_SELECT = f"SELECT {', '.join(_ADMIN_COLUMNS)} FROM check_administrations"


def insert_administration(connection: sqlite3.Connection, row: Mapping[str, Any]) -> None:
    connection.execute(
        "INSERT INTO check_administrations (administration_token, request_id, commitment_id, surface, session_id, "
        "practice_item_id, contract_hash, cold, state, protection_method, exposure_json, opened_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'open', ?, '[]', ?)",
        (row["administration_token"], row["request_id"], row["commitment_id"], row["surface"], row["session_id"],
         row["practice_item_id"], row.get("contract_hash"), int(bool(row["cold"])), row["protection_method"],
         row["opened_at"]),
    )


def by_token(connection: sqlite3.Connection, token: str) -> dict[str, Any] | None:
    return _admin(connection.execute(f"{_SELECT} WHERE administration_token = ?", (token,)).fetchone())


def by_request(connection: sqlite3.Connection, request_id: str) -> dict[str, Any] | None:
    return _admin(connection.execute(f"{_SELECT} WHERE request_id = ?", (request_id,)).fetchone())


def open_administration(connection: sqlite3.Connection) -> dict[str, Any] | None:
    """The one open administration, if any (the partial unique index allows no second)."""

    return _admin(connection.execute(f"{_SELECT} WHERE state = 'open'").fetchone())


def open_commitments(connection: sqlite3.Connection) -> frozenset[str]:
    """The commitments an open administration holds (the lock Today reads)."""

    if not table_present(connection):
        return frozenset()
    return frozenset(str(row[0]) for row in connection.execute(
        "SELECT commitment_id FROM check_administrations WHERE state = 'open'"))


def set_exposure(connection: sqlite3.Connection, token: str, exposure: Sequence[Mapping[str, Any]]) -> None:
    connection.execute("UPDATE check_administrations SET exposure_json = ? WHERE administration_token = ? "
                       "AND state = 'open'", (json.dumps(list(exposure), sort_keys=True), token))


def set_submission(connection: sqlite3.Connection, token: str, submission_id: str) -> None:
    """Name the submission before the attempt is recorded: a crash between the attempt and the close is found by it."""

    connection.execute("UPDATE check_administrations SET submission_id = ? WHERE administration_token = ? "
                       "AND state = 'open' AND submission_id IS NULL", (submission_id, token))


def close(connection: sqlite3.Connection, token: str, *, state: str, now: str, attempt_id: str | None = None) -> bool:
    cursor = connection.execute(
        "UPDATE check_administrations SET state = ?, closed_at = ?, attempt_id = COALESCE(?, attempt_id) "
        "WHERE administration_token = ? AND state = 'open'", (state, now, attempt_id, token))
    return cursor.rowcount == 1


def insert_veil_set(connection: sqlite3.Connection, *, veil_set_id: str, token: str, commitment_id: str, kind: str,
                    method: str, veiled: Iterable[Mapping[str, Any]], opened: Iterable[Mapping[str, Any]],
                    now: str) -> int:
    seq = int(connection.execute("SELECT COALESCE(MAX(seq), 0) + 1 FROM check_veil_sets WHERE administration_token = ?",
                                 (token,)).fetchone()[0])
    connection.execute(
        "INSERT INTO check_veil_sets (veil_set_id, administration_token, commitment_id, seq, kind, method, veiled_json, "
        "opened_json, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (veil_set_id, token, commitment_id, seq, kind, method, json.dumps(list(veiled), sort_keys=True),
         json.dumps(list(opened), sort_keys=True), now),
    )
    return seq


def veil_sets(connection: sqlite3.Connection, token: str) -> list[dict[str, Any]]:
    rows = connection.execute(
        "SELECT veil_set_id, seq, kind, method, veiled_json, opened_json, created_at FROM check_veil_sets "
        "WHERE administration_token = ? ORDER BY seq", (token,)).fetchall()
    return [{"veil_set_id": row[0], "seq": int(row[1]), "kind": row[2], "method": row[3],
             "veiled": json.loads(row[4] or "[]"), "opened": json.loads(row[5] or "[]"), "created_at": row[6]}
            for row in rows]


__all__ = [
    "by_request", "by_token", "close", "insert_administration", "insert_veil_set", "open_administration",
    "open_commitments", "set_exposure", "set_submission", "table_present", "veil_sets",
]
