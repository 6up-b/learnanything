"""The only SQL for teacher TE1b's lesson suggestions (migration 236; spec_teacher_v1 §15.1, §18.1).

A suggestion is a ``router_decisions`` row (``decision_kind = 'lesson_suggestion'``,
written by :func:`learnloop.db.stores.router.insert_router_decision`, one per
local day by its receipt key ``lesson_suggestion:<date>``); the learner's one
response to a shown one is a ``router_suggestion_responses`` row (RAW_LEDGER,
append-only, unique per decision). Callers own the transaction.
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Mapping, Sequence
from typing import Any

from learnloop.ids import new_ulid

RECEIPT_PREFIX = "lesson_suggestion:"

RESPONSE_COLUMNS: tuple[str, ...] = (
    "id", "decision_id", "response", "candidate_ref", "learning_object_ids_json", "lesson_id", "session_id",
    "responded_at", "detail_json", "created_at",
)


def tables_present(connection: sqlite3.Connection) -> bool:
    return connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='router_suggestion_responses'"
    ).fetchone() is not None


def receipt_key(day: str) -> str:
    return f"{RECEIPT_PREFIX}{day}"


def _decision(row: sqlite3.Row | Mapping[str, Any]) -> dict[str, Any]:
    out = dict(row)
    out["detail"] = json.loads(out.get("detail_json") or "{}")
    out["candidates"] = json.loads(out.get("candidates_json") or "[]")
    out["day"] = str(out.get("receipt_key") or "")[len(RECEIPT_PREFIX):]
    return out


def decision_for_day(connection: sqlite3.Connection, day: str) -> dict[str, Any] | None:
    row = connection.execute(
        "SELECT * FROM router_decisions WHERE receipt_key = ? AND decision_kind = 'lesson_suggestion'",
        (receipt_key(day),),
    ).fetchone()
    return _decision(row) if row is not None else None


def decision(connection: sqlite3.Connection, decision_id: str) -> dict[str, Any] | None:
    row = connection.execute(
        "SELECT * FROM router_decisions WHERE id = ? AND decision_kind = 'lesson_suggestion'", (decision_id,)
    ).fetchone()
    return _decision(row) if row is not None else None


def decisions(connection: sqlite3.Connection) -> list[dict[str, Any]]:
    """Every lesson-suggestion decision, oldest first."""

    return [_decision(row) for row in connection.execute(
        "SELECT * FROM router_decisions WHERE decision_kind = 'lesson_suggestion' ORDER BY created_at, id")]


def responses(connection: sqlite3.Connection) -> list[dict[str, Any]]:
    """Every response, in response order."""

    if not tables_present(connection):
        return []
    return [dict(row) for row in connection.execute(
        "SELECT * FROM router_suggestion_responses ORDER BY responded_at, id")]


def response_for(connection: sqlite3.Connection, decision_id: str) -> dict[str, Any] | None:
    row = connection.execute(
        "SELECT * FROM router_suggestion_responses WHERE decision_id = ?", (decision_id,)
    ).fetchone()
    return dict(row) if row is not None else None


def response_for_lesson(connection: sqlite3.Connection, lesson_id: str) -> dict[str, Any] | None:
    row = connection.execute(
        "SELECT * FROM router_suggestion_responses WHERE lesson_id = ?", (lesson_id,)
    ).fetchone()
    return dict(row) if row is not None else None


def insert_response(
    connection: sqlite3.Connection,
    *,
    decision_id: str,
    response: str,
    candidate_ref: str,
    learning_object_ids: Sequence[str],
    responded_at: str,
    lesson_id: str | None = None,
    session_id: str | None = None,
    detail: Mapping[str, Any] | None = None,
) -> bool:
    """Append the decision's one response; a second response to the same decision is a no-op (False)."""

    cursor = connection.execute(
        f"INSERT INTO router_suggestion_responses ({','.join(RESPONSE_COLUMNS)}) "
        f"VALUES ({','.join('?' for _ in RESPONSE_COLUMNS)}) ON CONFLICT(decision_id) DO NOTHING",
        (f"rsr_{new_ulid().lower()}", decision_id, response, candidate_ref,
         json.dumps(list(learning_object_ids)), lesson_id, session_id, responded_at,
         json.dumps(dict(detail or {}), sort_keys=True), responded_at),
    )
    return cursor.rowcount > 0


def lesson_exists(connection: sqlite3.Connection, lesson_id: str) -> bool:
    return connection.execute("SELECT 1 FROM lessons WHERE id = ?", (lesson_id,)).fetchone() is not None


def open_lesson_learning_objects(connection: sqlite3.Connection) -> set[str]:
    """The LOs of every lesson still open."""

    out: set[str] = set()
    if connection.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='lessons'").fetchone() is None:
        return out
    for (raw,) in connection.execute("SELECT learning_object_ids_json FROM lessons WHERE closed_at IS NULL"):
        out.update(str(lo) for lo in json.loads(raw or "[]"))
    return out


def last_lesson_opened_by_learning_object(connection: sqlite3.Connection) -> dict[str, str]:
    """Per LO, when the latest lesson on it opened."""

    out: dict[str, str] = {}
    if connection.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='lessons'").fetchone() is None:
        return out
    for raw, opened in connection.execute("SELECT learning_object_ids_json, opened_at FROM lessons ORDER BY opened_at, id"):
        for lo in json.loads(raw or "[]"):
            out[str(lo)] = str(opened)
    return out


def attempts_by_learning_object(connection: sqlite3.Connection) -> dict[str, list[dict[str, Any]]]:
    """Each LO's attempts, oldest first (what the candidate reasons read)."""

    out: dict[str, list[dict[str, Any]]] = {}
    for row in connection.execute(
        "SELECT id, learning_object_id, attempt_type, correctness, hints_used, primed, created_at "
        "FROM practice_attempts ORDER BY created_at, id"
    ):
        out.setdefault(str(row["learning_object_id"]), []).append(dict(row))
    return out


__all__ = [
    "RECEIPT_PREFIX",
    "attempts_by_learning_object",
    "decision",
    "decision_for_day",
    "decisions",
    "insert_response",
    "last_lesson_opened_by_learning_object",
    "lesson_exists",
    "open_lesson_learning_objects",
    "receipt_key",
    "response_for",
    "response_for_lesson",
    "responses",
    "tables_present",
]
