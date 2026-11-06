"""Teacher TE1 persistence (migration 234; spec_teacher_v1 §18.1).

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


def pending_delayed_checks(connection: sqlite3.Connection, *, at: str) -> list[dict[str, Any]]:
    """Teacher TE3b (spec_teacher_v1 rev 5 §15.1a, owner decision 5): every lesson delayed check committed by a
    receipt written by ``at`` and not yet answered as of ``at`` (no attempt on its item after the lesson closed, at
    or before ``at``), oldest receipt first: ``{lesson_id, learning_object_id, item_id, purpose, due}``. None before
    migration 234. Ids, dates and purposes only."""

    if connection.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'lesson_receipts'"
                          ).fetchone() is None:
        return []
    out: list[dict[str, Any]] = []
    for lesson_id, raw, written, closed in connection.execute(
            "SELECT r.lesson_id, r.receipt_json, r.created_at, l.closed_at FROM lesson_receipts r "
            "JOIN lessons l ON l.id = r.lesson_id WHERE r.created_at <= ? ORDER BY r.created_at, r.lesson_id", (at,)):
        after = str(closed or written)
        for entry in (json.loads(raw or "{}").get("delayed_checks") or ()):
            item = entry.get("item_id")
            lo = entry.get("learning_object_id")
            if not entry.get("commitment_id") or not item or not lo:
                continue
            answered = connection.execute(
                "SELECT 1 FROM practice_attempts WHERE practice_item_id = ? AND created_at > ? AND created_at <= ? "
                "LIMIT 1", (item, after, at)).fetchone()
            if answered is None:
                out.append({"lesson_id": str(lesson_id), "learning_object_id": str(lo), "item_id": str(item),
                            "purpose": entry.get("purpose"), "due": entry.get("due")})
    return out


# --- Teacher TE2-log (migration 247): the episode log and the lesson screen's intervals -------------------

#: An episode's columns set at its opening (everything but the closing fields).
EPISODE_OPEN_COLUMNS: tuple[str, ...] = (
    "id", "lesson_id", "kind", "opened_by", "node_id", "learning_object_id", "opened_at", "hypothesis_count",
    "hypothesis_hash", "hypothesis_payload_id", "repair_class", "teacher_p", "teacher_forecast_receipt_id",
    "predicted_success", "predicted_low", "predicted_high", "predicted_source", "mastery_mean", "mastery_variance",
    "open_misconceptions", "open_hypotheses", "open_ids_json", "origin", "origin_decision_id", "objective_trace_id",
    "generation_job_id", "generated_item_id", "gap_job_id", "created_lo_id", "experiment_assignment_ids_json",
    "episode_version", "created_at",
)
#: The closing fields, set once (the table's close-once trigger).
EPISODE_CLOSE_COLUMNS: tuple[str, ...] = (
    "closed_at", "close_reason", "active_seconds", "elapsed_seconds", "unreported_seconds", "missing_intervals",
    "minutes_source", "outcome_attempt_id", "outcome_correctness", "recheck_attempt_id", "gap_result", "lo_undo_state",
    # Teacher TE2 (migration 248): a probe's refusal reason, and its generated item (unknown at the opening; set
    # once with the close, from NULL only).
    "refusal_reason", "generated_item_id",
)


def episode_tables_present(connection: sqlite3.Connection) -> bool:
    rows = connection.execute("SELECT name FROM sqlite_master WHERE type = 'table' AND name IN "
                              "('lesson_episodes', 'lesson_activity_intervals')").fetchall()
    return len(rows) == 2


def insert_episode(connection: sqlite3.Connection, row: Mapping[str, Any]) -> bool:
    """One episode at its opening; False when its opening action already has one (a recovered action)."""

    values = {**{column: None for column in EPISODE_OPEN_COLUMNS}, **{k: v for k, v in row.items()
                                                                      if k in EPISODE_OPEN_COLUMNS}}
    values["open_ids_json"] = _dumps(dict(row.get("open_ids") or {}))
    values["experiment_assignment_ids_json"] = _dumps(list(row.get("experiment_assignment_ids") or []))
    marks = ", ".join("?" for _ in EPISODE_OPEN_COLUMNS)
    cursor = connection.execute(
        f"INSERT OR IGNORE INTO lesson_episodes({', '.join(EPISODE_OPEN_COLUMNS)}) VALUES ({marks})",
        [values[column] for column in EPISODE_OPEN_COLUMNS])
    return cursor.rowcount == 1


def close_episode(connection: sqlite3.Connection, episode_id: str, fields: Mapping[str, Any]) -> bool:
    """Set an open episode's closing fields once; False when it was already closed."""

    columns = [column for column in EPISODE_CLOSE_COLUMNS if column in fields]
    if "closed_at" not in columns or "close_reason" not in columns:
        raise ValueError("an episode closes with closed_at and close_reason")
    cursor = connection.execute(
        f"UPDATE lesson_episodes SET {', '.join(f'{column} = ?' for column in columns)} "
        "WHERE id = ? AND closed_at IS NULL", [*[fields[column] for column in columns], episode_id])
    return cursor.rowcount == 1


def episodes(connection: sqlite3.Connection, lesson_id: str | None = None) -> list[dict[str, Any]]:
    where, params = ("WHERE lesson_id = ? ", (lesson_id,)) if lesson_id is not None else ("", ())
    cursor = connection.execute(f"SELECT * FROM lesson_episodes {where}ORDER BY opened_at, id", params)
    out = []
    for row in cursor.fetchall():
        data = _row(cursor, row)
        data["open_ids"] = json.loads(data.pop("open_ids_json") or "{}")
        data["experiment_assignment_ids"] = json.loads(data.pop("experiment_assignment_ids_json") or "[]")
        out.append(data)
    return out


def insert_interval(connection: sqlite3.Connection, row: Mapping[str, Any]) -> bool:
    """One activity interval; False when its (lesson, screen session, seq) is already recorded (a resend)."""

    cursor = connection.execute(
        "INSERT OR IGNORE INTO lesson_activity_intervals(id, lesson_id, screen_session, seq, started_at, ended_at, "
        "seconds, foreground, occurred_at, received_at, receipt_version) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (str(row.get("id") or f"lai_{new_ulid().lower()}"), row["lesson_id"], row["screen_session"], int(row["seq"]),
         row["started_at"], row["ended_at"], float(row["seconds"]), 1 if row["foreground"] else 0,
         row["occurred_at"], row["received_at"], row["receipt_version"]))
    return cursor.rowcount == 1


def intervals(connection: sqlite3.Connection, lesson_id: str | None = None) -> list[dict[str, Any]]:
    where, params = ("WHERE lesson_id = ? ", (lesson_id,)) if lesson_id is not None else ("", ())
    cursor = connection.execute(
        f"SELECT * FROM lesson_activity_intervals {where}ORDER BY started_at, screen_session, seq", params)
    return [_row(cursor, row) for row in cursor.fetchall()]


__all__ = [
    "EPISODE_CLOSE_COLUMNS",
    "EPISODE_OPEN_COLUMNS",
    "append_turn",
    "checks",
    "close_episode",
    "close_lesson",
    "episode_tables_present",
    "episodes",
    "insert_episode",
    "insert_interval",
    "intervals",
    "insert_check",
    "insert_lesson",
    "insert_plan",
    "insert_receipt",
    "lesson",
    "lessons_on",
    "pending_delayed_checks",
    "payload_hash",
    "plans",
    "receipt",
    "turns",
]
