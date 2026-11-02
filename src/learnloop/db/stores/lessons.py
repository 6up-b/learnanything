"""Teacher TE1 persistence (migration 233; spec_teacher_v1 §18.1).

The lesson ledger (``lessons``, ``lesson_turns``, ``lesson_plans``: append-only,
a lesson closes once), the raw turn text (``lesson_turn_payloads``), and the
check and lesson receipts (``lesson_checks``, ``lesson_receipts``: append-only).
The callers own the transaction. The DERIVED weight tables are written only by
``learner.lesson_weight``.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from collections.abc import Mapping, Sequence
from typing import Any

from learnloop.ids import new_ulid


def _dumps(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, default=str)


def _row(cursor: sqlite3.Cursor, row: Sequence[Any]) -> dict[str, Any]:
    return {description[0]: value for description, value in zip(cursor.description, row)}


def payload_hash(payload: Any) -> str:
    return hashlib.sha256(_dumps(payload).encode("utf-8")).hexdigest()


def insert_lesson(connection: sqlite3.Connection, row: Mapping[str, Any]) -> str:
    lesson_id = str(row.get("id") or f"les_{new_ulid().lower()}")
    connection.execute(
        "INSERT INTO lessons(id, driver, origin, origin_ref, entry, goal_text, goal_json, learning_object_ids_json, "
        "doctrine_version, brief_version, route, model, algorithm_version, opened_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (lesson_id, row["driver"], row["origin"], row.get("origin_ref"), row["entry"], row["goal_text"],
         _dumps(row["goal"]), _dumps(list(row["learning_object_ids"])), row["doctrine_version"],
         row["brief_version"], row.get("route"), row.get("model"), row["algorithm_version"], row["opened_at"]))
    return lesson_id


def close_lesson(connection: sqlite3.Connection, lesson_id: str, *, reason: str, closed_at: str) -> bool:
    cursor = connection.execute(
        "UPDATE lessons SET closed_at = ?, close_reason = ? WHERE id = ? AND closed_at IS NULL",
        (closed_at, reason, lesson_id))
    return cursor.rowcount == 1


def lesson(connection: sqlite3.Connection, lesson_id: str) -> dict[str, Any] | None:
    cursor = connection.execute("SELECT * FROM lessons WHERE id = ?", (lesson_id,))
    row = cursor.fetchone()
    if row is None:
        return None
    out = _row(cursor, row)
    out["goal"] = json.loads(out.pop("goal_json") or "{}")
    out["learning_object_ids"] = json.loads(out.pop("learning_object_ids_json") or "[]")
    return out


def lessons_on(connection: sqlite3.Connection, learning_object_ids: Sequence[str], *, closed_only: bool = True,
               exclude: str | None = None) -> list[dict[str, Any]]:
    """Lessons whose LOs meet ``learning_object_ids``, newest first."""

    wanted = set(learning_object_ids)
    cursor = connection.execute("SELECT * FROM lessons ORDER BY opened_at DESC, id DESC")
    out = []
    for row in cursor.fetchall():
        data = _row(cursor, row)
        if exclude is not None and data["id"] == exclude:
            continue
        if closed_only and data["closed_at"] is None:
            continue
        los = json.loads(data["learning_object_ids_json"] or "[]")
        if wanted & set(los):
            data["learning_object_ids"] = los
            data["goal"] = json.loads(data["goal_json"] or "{}")
            out.append(data)
    return out


def next_seq(connection: sqlite3.Connection, lesson_id: str) -> int:
    row = connection.execute("SELECT COALESCE(MAX(seq), 0) FROM lesson_turns WHERE lesson_id = ?", (lesson_id,)).fetchone()
    return int(row[0]) + 1


def append_turn(connection: sqlite3.Connection, *, lesson_id: str, actor: str, action: str, validation: str,
                refs: Mapping[str, Any] | None, payload: Any, created_at: str) -> dict[str, Any]:
    turn_id = f"lt_{new_ulid().lower()}"
    seq = next_seq(connection, lesson_id)
    digest = payload_hash(payload) if payload is not None else None
    connection.execute(
        "INSERT INTO lesson_turns(id, lesson_id, seq, actor, action, validation, refs_json, payload_hash, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (turn_id, lesson_id, seq, actor, action, validation, _dumps(dict(refs or {})), digest, created_at))
    if payload is not None:
        connection.execute(
            "INSERT INTO lesson_turn_payloads(turn_id, lesson_id, payload_json, created_at) VALUES (?, ?, ?, ?)",
            (turn_id, lesson_id, _dumps(payload), created_at))
    return {"id": turn_id, "seq": seq}


def turns(connection: sqlite3.Connection, lesson_id: str) -> list[dict[str, Any]]:
    cursor = connection.execute(
        "SELECT t.id, t.seq, t.actor, t.action, t.validation, t.refs_json, t.created_at, p.payload_json "
        "FROM lesson_turns t LEFT JOIN lesson_turn_payloads p ON p.turn_id = t.id "
        "WHERE t.lesson_id = ? ORDER BY t.seq", (lesson_id,))
    out = []
    for row in cursor.fetchall():
        data = _row(cursor, row)
        data["refs"] = json.loads(data.pop("refs_json") or "{}")
        payload = data.pop("payload_json")
        data["payload"] = json.loads(payload) if payload else None
        out.append(data)
    return out


def insert_plan(connection: sqlite3.Connection, *, lesson_id: str, outline: Any, created_at: str) -> int:
    row = connection.execute("SELECT COALESCE(MAX(version), 0) FROM lesson_plans WHERE lesson_id = ?",
                             (lesson_id,)).fetchone()
    version = int(row[0]) + 1
    connection.execute(
        "INSERT INTO lesson_plans(id, lesson_id, version, outline_json, created_at) VALUES (?, ?, ?, ?, ?)",
        (f"lp_{new_ulid().lower()}", lesson_id, version, _dumps(outline), created_at))
    return version


def plans(connection: sqlite3.Connection, lesson_id: str) -> list[dict[str, Any]]:
    rows = connection.execute(
        "SELECT version, outline_json, created_at FROM lesson_plans WHERE lesson_id = ? ORDER BY version",
        (lesson_id,)).fetchall()
    return [{"version": int(row[0]), "outline": json.loads(row[1]), "created_at": row[2]} for row in rows]


def insert_check(connection: sqlite3.Connection, row: Mapping[str, Any]) -> str:
    check_id = str(row.get("id") or f"lc_{new_ulid().lower()}")
    connection.execute(
        "INSERT INTO lesson_checks(id, lesson_id, node_id, check_ref, learning_object_id, minted_item_id, status, "
        "attempt_id, correctness, tap, hedge, predicted_success, predicted_source, mass_learned, mass_applied, "
        "forecast_correct_key, forecast_retained_key, weight_inputs_json, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (check_id, row["lesson_id"], row["node_id"], row["check_ref"], row["learning_object_id"],
         row["minted_item_id"], row["status"], row.get("attempt_id"), row.get("correctness"), row.get("tap"),
         row.get("hedge"), row.get("predicted_success"), row.get("predicted_source"), row.get("mass_learned"),
         row.get("mass_applied"), row.get("forecast_correct_key"), row.get("forecast_retained_key"),
         _dumps(dict(row.get("weight_inputs") or {})), row["created_at"]))
    return check_id


def checks(connection: sqlite3.Connection, lesson_id: str) -> list[dict[str, Any]]:
    cursor = connection.execute("SELECT * FROM lesson_checks WHERE lesson_id = ? ORDER BY created_at, id", (lesson_id,))
    out = []
    for row in cursor.fetchall():
        data = _row(cursor, row)
        data["weight_inputs"] = json.loads(data.pop("weight_inputs_json") or "{}")
        out.append(data)
    return out


def insert_receipt(connection: sqlite3.Connection, *, lesson_id: str, version: str, close_reason: str,
                   receipt: Mapping[str, Any], created_at: str) -> None:
    connection.execute(
        "INSERT INTO lesson_receipts(lesson_id, receipt_version, close_reason, receipt_json, created_at) "
        "VALUES (?, ?, ?, ?, ?)", (lesson_id, version, close_reason, _dumps(dict(receipt)), created_at))


def receipt(connection: sqlite3.Connection, lesson_id: str) -> dict[str, Any] | None:
    row = connection.execute("SELECT receipt_json FROM lesson_receipts WHERE lesson_id = ?", (lesson_id,)).fetchone()
    return json.loads(row[0]) if row is not None else None


__all__ = [
    "append_turn",
    "checks",
    "close_lesson",
    "insert_check",
    "insert_lesson",
    "insert_plan",
    "insert_receipt",
    "lesson",
    "lessons_on",
    "payload_hash",
    "plans",
    "receipt",
    "turns",
]
