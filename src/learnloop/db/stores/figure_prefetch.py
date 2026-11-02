"""Reader RW5d P5: the prefetch ledgers' writes (migration 236; spec_reader_show_me_figures_v1 §13.2b).

``figure_prefetch_decisions`` is append-only: one row per decided candidate, and later only its
``request_id`` and ``input_hash`` (when the build stored its request) and its ``outcome`` with
``outcome_at`` (at the horizon), each set once (the trigger refuses anything else).
``plan_usage_pauses`` is append-only, one row per hit time. Within the caller's transaction.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Mapping, Sequence
from typing import Any

DECISION_COLUMNS = ("id", "trigger_kind", "trigger_ref", "request_key", "input_hash", "anchor_json", "goal_text",
                    "goal_author", "source_key", "p_open_content", "model_version", "posterior_digest", "sampled_eu",
                    "propensity", "w_minutes", "cost_minutes", "decision", "request_id", "horizon_kind", "outcome",
                    "outcome_at", "created_at")


def insert_decisions(connection: sqlite3.Connection, rows: Sequence[Mapping[str, Any]]) -> None:
    for row in rows:
        connection.execute(
            f"INSERT INTO figure_prefetch_decisions ({', '.join(DECISION_COLUMNS)}) "
            f"VALUES ({', '.join('?' for _ in DECISION_COLUMNS)})", tuple(row.get(column) for column in DECISION_COLUMNS))


def link_request(connection: sqlite3.Connection, decision_id: str, request_id: str, input_hash: str | None) -> None:
    """The decision's request and the figure's input hash, set once each (a later call keeps the first)."""

    connection.execute(
        "UPDATE figure_prefetch_decisions SET request_id = COALESCE(request_id, ?), input_hash = COALESCE(input_hash, ?) "
        "WHERE id = ?", (request_id, input_hash, decision_id))


def close_decision(connection: sqlite3.Connection, decision_id: str, outcome: str, outcome_at: str) -> bool:
    cursor = connection.execute(
        "UPDATE figure_prefetch_decisions SET outcome = ?, outcome_at = ? WHERE id = ? AND outcome IS NULL",
        (outcome, outcome_at, decision_id))
    return cursor.rowcount == 1


def insert_pause(connection: sqlite3.Connection, row: Mapping[str, Any]) -> bool:
    """One pause, idempotently by its hit time; True when it was new."""

    cursor = connection.execute(
        "INSERT OR IGNORE INTO plan_usage_pauses (id, hit_at, reset_at, plan_requests_today, plan_tokens_today_known, "
        "observed_at) VALUES (?, ?, ?, ?, ?, ?)",
        (row["id"], row["hit_at"], row.get("reset_at"), int(row.get("plan_requests_today") or 0),
         int(row.get("plan_tokens_today_known") or 0), row["observed_at"]))
    return cursor.rowcount == 1


__all__ = ["DECISION_COLUMNS", "close_decision", "insert_decisions", "insert_pause", "link_request"]
