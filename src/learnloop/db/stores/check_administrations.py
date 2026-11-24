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
    # Migration 271 (RD7's fix round): what begin froze and what the close promised.
    "candidates_json", "presentation_json", "pending_before", "outcome_json", "exposure_ids_json",
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
    out["candidates"] = json.loads(out.pop("candidates_json") or "[]")
    presentation = out.pop("presentation_json")
    out["presentation"] = json.loads(presentation) if presentation else None
    out["pending_before"] = None if out["pending_before"] is None else bool(out["pending_before"])
    outcome = out.pop("outcome_json")
    out["outcome"] = json.loads(outcome) if outcome else None
    out["exposure_ids"] = json.loads(out.pop("exposure_ids_json") or "[]")
    return out


_SELECT = f"SELECT {', '.join(_ADMIN_COLUMNS)} FROM check_administrations"


def insert_administration(connection: sqlite3.Connection, row: Mapping[str, Any]) -> None:
    connection.execute(
        "INSERT INTO check_administrations (administration_token, request_id, commitment_id, surface, session_id, "
        "practice_item_id, contract_hash, cold, state, protection_method, exposure_json, opened_at, candidates_json, "
        "presentation_json) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'open', ?, '[]', ?, ?, ?)",
        (row["administration_token"], row["request_id"], row["commitment_id"], row["surface"], row["session_id"],
         row["practice_item_id"], row.get("contract_hash"), int(bool(row["cold"])), row["protection_method"],
         row["opened_at"], json.dumps(list(row.get("candidates") or ()), sort_keys=True),
         json.dumps(row["presentation"], sort_keys=True) if row.get("presentation") is not None else None),
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


def held_windows(connection: sqlite3.Connection) -> dict[str, list[tuple[str, str | None]]]:
    """Per commitment, every inline administration's (opened_at, closed_at): the times it held the check."""

    if not table_present(connection):
        return {}
    out: dict[str, list[tuple[str, str | None]]] = {}
    for commitment_id, opened_at, closed_at in connection.execute(
            "SELECT commitment_id, opened_at, closed_at FROM check_administrations ORDER BY opened_at"):
        out.setdefault(str(commitment_id), []).append((str(opened_at), None if closed_at is None else str(closed_at)))
    return out


def set_exposure(connection: sqlite3.Connection, token: str, exposure: Sequence[Mapping[str, Any]],
                 exposure_ids: Sequence[str] | None = None) -> bool:
    """Record the exposure (and the client's ids of the openings recorded); False when the row is not open, or a
    submission is reserved on it (the caller then refuses: nothing is recorded)."""

    if exposure_ids is None:
        cursor = connection.execute(
            "UPDATE check_administrations SET exposure_json = ? WHERE administration_token = ? AND state = 'open' "
            "AND submission_id IS NULL", (json.dumps(list(exposure), sort_keys=True), token))
    else:
        cursor = connection.execute(
            "UPDATE check_administrations SET exposure_json = ?, exposure_ids_json = ? WHERE administration_token = ? "
            "AND state = 'open' AND submission_id IS NULL",
            (json.dumps(list(exposure), sort_keys=True), json.dumps(list(exposure_ids)), token))
    return cursor.rowcount == 1


def set_submission(connection: sqlite3.Connection, token: str, submission_id: str, *, pending_before: bool) -> bool:
    """Name the submission before the attempt is recorded (a crash between the attempt and the close is found by it),
    with whether the check was pending then. True when this call reserved it, or it was already this submission's."""

    cursor = connection.execute(
        "UPDATE check_administrations SET submission_id = ?, pending_before = ? WHERE administration_token = ? "
        "AND state = 'open' AND submission_id IS NULL", (submission_id, int(pending_before), token))
    if cursor.rowcount == 1:
        return True
    row = connection.execute("SELECT submission_id FROM check_administrations WHERE administration_token = ?",
                             (token,)).fetchone()
    return row is not None and row[0] == submission_id


def close(connection: sqlite3.Connection, token: str, *, state: str, now: str, attempt_id: str | None = None,
          outcome: Mapping[str, Any] | None = None, unreserved: bool = False) -> bool:
    """Close an open administration (with its attempt and the outcome it promised). ``unreserved``: only while no
    submission is reserved on it (not now, while an answer is in flight, closes nothing). True when this call closed
    it."""

    cursor = connection.execute(
        "UPDATE check_administrations SET state = ?, closed_at = ?, attempt_id = COALESCE(?, attempt_id), "
        "outcome_json = COALESCE(?, outcome_json) WHERE administration_token = ? AND state = 'open'"
        + (" AND submission_id IS NULL" if unreserved else ""),
        (state, now, attempt_id, json.dumps(dict(outcome), sort_keys=True) if outcome is not None else None, token))
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
