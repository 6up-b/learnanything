"""The only SQL writer for ``followup_value_decisions`` (migration 188).

mvp-0.17 (value-of-information stopping), Codex re-review F1: one RECEIPT row
per follow-up decision the value rule takes part in, with its own id and a
per-attempt ordinal, linked to its source attempt. Rows are append-only
(triggers); nothing in a rebuild or a replay writes them. Callers own the
transaction.
"""
from __future__ import annotations

from collections.abc import Mapping
import json
import sqlite3
from typing import Any

from learnloop.ids import new_ulid

COLUMNS = (
    "id", "source_attempt_id", "decision_ordinal", "learning_object_id", "session_id",
    "decision_outcome", "verdict", "manual_override", "recommended_ref", "served_ref", "need_id",
    "candidate_count", "forecast_version", "decision_json", "algorithm_version", "created_at",
)


def table_present(connection: sqlite3.Connection) -> bool:
    return connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'followup_value_decisions'"
    ).fetchone() is not None


def insert_decision(connection: sqlite3.Connection, row: Mapping[str, Any]) -> str:
    """Append one decision; its ordinal is the attempt's next (one statement,
    so it is atomic under SQLite's write lock)."""

    values = dict(row)
    values.setdefault("id", new_ulid())
    decision = values.get("decision_json")
    if decision is not None and not isinstance(decision, str):
        values["decision_json"] = json.dumps(decision, sort_keys=True, ensure_ascii=False)
    values["manual_override"] = 1 if values.get("manual_override") else 0
    insert_columns = [column for column in COLUMNS if column != "decision_ordinal"]
    connection.execute(
        f"INSERT INTO followup_value_decisions ({', '.join(insert_columns)}, decision_ordinal) "
        f"SELECT {', '.join('?' for _ in insert_columns)}, COALESCE(MAX(decision_ordinal), 0) + 1 "
        "FROM followup_value_decisions WHERE source_attempt_id = ?",
        (*(values.get(column) for column in insert_columns), values["source_attempt_id"]),
    )
    return str(values["id"])


def _decode(row: sqlite3.Row) -> dict[str, Any]:
    data = dict(row)
    raw = data.pop("decision_json", None)
    data["decision"] = json.loads(raw) if raw else None
    data["manual_override"] = bool(data.get("manual_override"))
    return data


def decisions_for_attempt(connection: sqlite3.Connection, source_attempt_id: str) -> list[dict[str, Any]]:
    """Every decision on ``source_attempt_id``, in decision order."""

    if not table_present(connection):
        return []
    rows = connection.execute(
        "SELECT * FROM followup_value_decisions WHERE source_attempt_id = ? ORDER BY decision_ordinal",
        (str(source_attempt_id),),
    ).fetchall()
    return [_decode(row) for row in rows]


__all__ = ["COLUMNS", "decisions_for_attempt", "insert_decision", "table_present"]
