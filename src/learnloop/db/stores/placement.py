"""The only SQL writer for learner-field F2 placement tables (migrations 172-173).

``assumption_decisions`` and ``assumption_returns`` are RECEIPT tables:
append-only, never cleared by replay, never evidence. ``placement_quick_checks``
and ``placement_quick_check_items`` are WORKFLOW queue state for the optional
quick check. Callers own the transaction (``with repository.connection() as
connection``).
"""
from __future__ import annotations

from collections.abc import Mapping
import sqlite3
from typing import Any

_DECISION_COLUMNS = (
    "id", "learning_object_id", "source", "trigger_kind", "trigger_ref", "p",
    "interval_json", "q_used", "theta_known", "predictor", "predictor_version",
    "first_review_due", "quick_check_session_id", "algorithm_version",
    "config_json", "inputs_json", "created_at",
)
_RETURN_COLUMNS = (
    "id", "assumption_id", "learning_object_id", "reason", "trigger_ref",
    "algorithm_version", "created_at",
)


def insert_assumption_decision(connection: sqlite3.Connection, row: Mapping[str, Any]) -> None:
    connection.execute(
        f"INSERT INTO assumption_decisions ({','.join(_DECISION_COLUMNS)}) "
        f"VALUES ({','.join('?' for _ in _DECISION_COLUMNS)})",
        tuple(row.get(column) for column in _DECISION_COLUMNS),
    )


def insert_assumption_return(connection: sqlite3.Connection, row: Mapping[str, Any]) -> None:
    connection.execute(
        f"INSERT INTO assumption_returns ({','.join(_RETURN_COLUMNS)}) "
        f"VALUES ({','.join('?' for _ in _RETURN_COLUMNS)})",
        tuple(row.get(column) for column in _RETURN_COLUMNS),
    )


def insert_quick_check(connection: sqlite3.Connection, row: Mapping[str, Any]) -> None:
    connection.execute(
        """INSERT INTO placement_quick_checks
        (calibration_session_id, session_id, learning_object_ids_json, k,
         budget_minutes, predictor, predictor_version, created_at, request_id)
        VALUES (?,?,?,?,?,?,?,?,?)""",
        (
            row["calibration_session_id"], row["session_id"], row["learning_object_ids_json"],
            row["k"], row["budget_minutes"], row["predictor"], row["predictor_version"],
            row["created_at"], row.get("request_id"),
        ),
    )


def finish_quick_check(
    connection: sqlite3.Connection, calibration_session_id: str, *, finished_at: str, outcome_json: str,
) -> bool:
    """Record the split once. Returns False when another caller finished it first."""

    cursor = connection.execute(
        """UPDATE placement_quick_checks
              SET finished_at = ?, outcome_json = ?
            WHERE calibration_session_id = ? AND finished_at IS NULL""",
        (finished_at, outcome_json, calibration_session_id),
    )
    return cursor.rowcount == 1


def insert_quick_check_item(connection: sqlite3.Connection, row: Mapping[str, Any]) -> None:
    """Persist one presentation of the quick check (at most k per check)."""

    connection.execute(
        """INSERT INTO placement_quick_check_items
        (calibration_session_id, ordinal, practice_item_id, learning_object_id, presented_at)
        VALUES (?,?,?,?,?)""",
        (
            row["calibration_session_id"], row["ordinal"], row["practice_item_id"],
            row["learning_object_id"], row["presented_at"],
        ),
    )


def bind_quick_check_item(
    connection: sqlite3.Connection,
    calibration_session_id: str,
    ordinal: int,
    *,
    attempt_id: str,
    answered_at: str,
) -> bool:
    """Associate a submission with its presentation, once."""

    cursor = connection.execute(
        """UPDATE placement_quick_check_items
              SET attempt_id = ?, answered_at = ?
            WHERE calibration_session_id = ? AND ordinal = ? AND attempt_id IS NULL""",
        (attempt_id, answered_at, calibration_session_id, ordinal),
    )
    return cursor.rowcount == 1
