"""Scratch-only tables for the Slice 1 M1 offline diagnosis review.

These tables are created ONLY inside a backup-API copy of a vault database
(the run's ``scratch.sqlite``); they are never a vault migration and never
appear in a live vault. :func:`ensure_review_schema` writes a marker row and
every writer calls :func:`assert_scratch` first, so a review artifact cannot
land in a vault database by accident.

Rows are append-only in spirit: the runner skips work whose row exists (the
checkpoint), and spot-check verdicts append a successor instead of editing.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from typing import Any, Iterable, Mapping
from uuid import uuid4

REVIEW_SCHEMA_VERSION = "diagnosis-review-v1"

_DDL = (
    """
    CREATE TABLE IF NOT EXISTS review_scratch_marker (
        run_id TEXT PRIMARY KEY,
        schema_version TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS review_runs (
        id TEXT PRIMARY KEY,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        status TEXT NOT NULL,
        seed INTEGER NOT NULL,
        plan_json TEXT NOT NULL,
        manifest_json TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS review_targets (
        id TEXT PRIMARY KEY,
        run_id TEXT NOT NULL,
        kind TEXT NOT NULL CHECK (kind IN ('real', 'planted')),
        attempt_id TEXT NOT NULL,
        practice_item_id TEXT NOT NULL,
        learning_object_id TEXT NOT NULL,
        completed_at TEXT NOT NULL,
        stratum TEXT,
        planted_case_id TEXT,
        position INTEGER NOT NULL,
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS review_planted_cases (
        id TEXT PRIMARY KEY,
        run_id TEXT NOT NULL,
        shape TEXT NOT NULL,
        target_attempt_id TEXT NOT NULL,
        truth_json TEXT NOT NULL,
        history_json TEXT NOT NULL,
        source TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS review_blind_grades (
        id TEXT PRIMARY KEY,
        run_id TEXT NOT NULL,
        attempt_id TEXT NOT NULL,
        purpose TEXT NOT NULL,
        status TEXT NOT NULL,
        provider TEXT,
        model TEXT,
        prompt_version TEXT NOT NULL,
        context_hash TEXT NOT NULL,
        proposal_json TEXT,
        record_json TEXT,
        error TEXT,
        latency_seconds REAL,
        created_at TEXT NOT NULL,
        UNIQUE (run_id, attempt_id, purpose)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS review_diagnoses (
        id TEXT PRIMARY KEY,
        run_id TEXT NOT NULL,
        target_id TEXT NOT NULL,
        arm TEXT NOT NULL,
        mode TEXT NOT NULL,
        status TEXT NOT NULL,
        provider TEXT,
        model TEXT,
        prompt_version TEXT,
        proposal_json TEXT,
        validation_report_json TEXT NOT NULL,
        anchoring_suspect INTEGER NOT NULL DEFAULT 0,
        unknown_id_count INTEGER NOT NULL DEFAULT 0,
        latency_seconds REAL,
        error TEXT,
        created_at TEXT NOT NULL,
        UNIQUE (run_id, target_id, arm)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS review_context_receipts (
        diagnosis_id TEXT PRIMARY KEY,
        context_hash TEXT,
        failure_attempt_ids_json TEXT NOT NULL,
        success_attempt_ids_json TEXT NOT NULL,
        history_attempt_ids_json TEXT NOT NULL,
        hypothesis_ids_json TEXT NOT NULL,
        registry_candidate_ids_json TEXT NOT NULL,
        prerequisite_refs_json TEXT NOT NULL,
        retrieval_json TEXT NOT NULL,
        anchoring_suspect INTEGER NOT NULL DEFAULT 0,
        validated_citations_json TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS review_calls (
        id TEXT PRIMARY KEY,
        run_id TEXT NOT NULL,
        stage TEXT NOT NULL,
        route TEXT NOT NULL,
        purpose TEXT NOT NULL,
        subject_id TEXT,
        arm TEXT,
        provider TEXT,
        model TEXT,
        billing TEXT NOT NULL,
        cost_basis TEXT NOT NULL,
        input_tokens INTEGER,
        output_tokens INTEGER,
        cached_input_tokens INTEGER,
        reasoning_tokens INTEGER,
        estimated_usd REAL,
        latency_seconds REAL,
        status TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS review_probes (
        id TEXT PRIMARY KEY,
        run_id TEXT NOT NULL,
        probe TEXT NOT NULL,
        practice_item_id TEXT NOT NULL,
        status TEXT NOT NULL,
        known_score REAL,
        max_points REAL,
        blind_score REAL,
        detail_json TEXT NOT NULL,
        created_at TEXT NOT NULL,
        UNIQUE (run_id, probe, practice_item_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS review_judgments (
        id TEXT PRIMARY KEY,
        run_id TEXT NOT NULL,
        session_id TEXT,
        screen TEXT NOT NULL,
        task TEXT NOT NULL,
        subject_kind TEXT NOT NULL,
        subject_id TEXT NOT NULL,
        other_kind TEXT,
        other_id TEXT,
        judge TEXT NOT NULL,
        verdict TEXT NOT NULL,
        detail_json TEXT NOT NULL,
        supersedes_id TEXT,
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS review_spot_check_sessions (
        id TEXT PRIMARY KEY,
        run_id TEXT NOT NULL,
        started_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        finished_at TEXT,
        plan_json TEXT NOT NULL,
        position INTEGER NOT NULL DEFAULT 0
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_review_diagnoses_target ON review_diagnoses(run_id, target_id)",
    "CREATE INDEX IF NOT EXISTS idx_review_judgments_subject ON review_judgments(run_id, task, subject_id)",
)

#: Columns written as JSON text: callers pass Python values for these.
_JSON_SUFFIX = "_json"
_TABLES = frozenset(
    {
        "review_runs",
        "review_targets",
        "review_planted_cases",
        "review_blind_grades",
        "review_diagnoses",
        "review_context_receipts",
        "review_calls",
        "review_probes",
        "review_judgments",
        "review_spot_check_sessions",
    }
)


class NotAScratchDatabase(RuntimeError):
    """A review write was attempted outside a review scratch copy."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_review_schema(connection: sqlite3.Connection, *, run_id: str) -> None:
    """Create the review tables and mark this database as a review scratch copy."""

    for statement in _DDL:
        connection.execute(statement)
    connection.execute(
        "INSERT OR IGNORE INTO review_scratch_marker (run_id, schema_version, created_at) VALUES (?, ?, ?)",
        (run_id, REVIEW_SCHEMA_VERSION, _now()),
    )


def is_scratch(connection: sqlite3.Connection) -> bool:
    row = connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='review_scratch_marker'"
    ).fetchone()
    if row is None:
        return False
    return connection.execute("SELECT 1 FROM review_scratch_marker LIMIT 1").fetchone() is not None


def assert_scratch(connection: sqlite3.Connection) -> None:
    if not is_scratch(connection):
        raise NotAScratchDatabase("review artifacts may only be written to a review scratch copy")


def _encode(table: str, values: Mapping[str, Any]) -> dict[str, Any]:
    if table not in _TABLES:
        raise ValueError(f"unknown review table {table!r}")
    encoded: dict[str, Any] = {}
    for key, value in values.items():
        if not key.replace("_", "").isalnum():
            raise ValueError(f"invalid column {key!r}")
        if key.endswith(_JSON_SUFFIX) and not isinstance(value, str) and value is not None:
            value = json.dumps(value, sort_keys=True, ensure_ascii=False, default=str)
        elif isinstance(value, bool):
            value = int(value)
        encoded[key] = value
    return encoded


def insert_review_row(
    connection: sqlite3.Connection,
    table: str,
    values: Mapping[str, Any],
    *,
    or_ignore: bool = False,
    or_replace: bool = False,
) -> str:
    """Insert one row (an ``id`` is minted when absent); returns the id.

    ``or_replace`` lets a resumed run replace a FAILED unit of work with its
    retry; completed rows are never replaced (callers skip them).
    """

    assert_scratch(connection)
    row = dict(values)
    if table != "review_context_receipts":
        row.setdefault("id", str(uuid4()))
    if table in {"review_runs", "review_spot_check_sessions"}:
        row.setdefault("updated_at", _now())
    if table not in {"review_context_receipts", "review_spot_check_sessions"}:
        row.setdefault("created_at", _now())
    elif table == "review_spot_check_sessions":
        row.setdefault("started_at", _now())
    encoded = _encode(table, row)
    columns = ", ".join(encoded)
    placeholders = ", ".join("?" for _ in encoded)
    verb = "INSERT OR IGNORE INTO" if or_ignore else ("INSERT OR REPLACE INTO" if or_replace else "INSERT INTO")
    connection.execute(
        f"{verb} {table} ({columns}) VALUES ({placeholders})",
        tuple(encoded.values()),
    )
    return str(row.get("id") or row.get("diagnosis_id"))


def update_run(
    connection: sqlite3.Connection,
    run_id: str,
    *,
    status: str | None = None,
    manifest: Mapping[str, Any] | None = None,
) -> None:
    assert_scratch(connection)
    if status is not None:
        connection.execute(
            "UPDATE review_runs SET status = ?, updated_at = ? WHERE id = ?",
            (status, _now(), run_id),
        )
    if manifest is not None:
        connection.execute(
            "UPDATE review_runs SET manifest_json = ?, updated_at = ? WHERE id = ?",
            (json.dumps(dict(manifest), sort_keys=True, default=str), _now(), run_id),
        )


def update_target_positions(connection: sqlite3.Connection, positions: Mapping[str, int]) -> None:
    """Reorder targets (planted cases are interleaved among real ones)."""

    assert_scratch(connection)
    for target_id, position in positions.items():
        connection.execute(
            "UPDATE review_targets SET position = ? WHERE id = ?", (int(position), target_id)
        )


def update_spot_check_session(
    connection: sqlite3.Connection,
    session_id: str,
    *,
    position: int,
    finished: bool = False,
) -> None:
    assert_scratch(connection)
    connection.execute(
        "UPDATE review_spot_check_sessions SET position = ?, updated_at = ?, "
        "finished_at = CASE WHEN ? THEN ? ELSE finished_at END WHERE id = ?",
        (position, _now(), int(finished), _now(), session_id),
    )


def _decode(row: sqlite3.Row | tuple, columns: Iterable[str]) -> dict[str, Any]:
    payload = dict(zip(columns, row))
    for key in list(payload):
        if key.endswith(_JSON_SUFFIX) and isinstance(payload[key], str):
            try:
                payload[key[: -len(_JSON_SUFFIX)]] = json.loads(payload[key])
            except ValueError:
                payload[key[: -len(_JSON_SUFFIX)]] = None
    return payload


def review_rows(
    connection: sqlite3.Connection,
    table: str,
    *,
    where: Mapping[str, Any] | None = None,
    order_by: str = "rowid",
) -> list[dict[str, Any]]:
    """Read rows with JSON columns decoded (``x_json`` also appears as ``x``)."""

    if table not in _TABLES:
        raise ValueError(f"unknown review table {table!r}")
    if not all(part.strip().replace("_", "").isalnum() for part in order_by.split(",")):
        raise ValueError("invalid order_by")
    clauses = []
    params: list[Any] = []
    for key, value in (where or {}).items():
        if not key.replace("_", "").isalnum():
            raise ValueError(f"invalid column {key!r}")
        clauses.append(f"{key} = ?")
        params.append(value)
    sql = f"SELECT * FROM {table}"
    if clauses:
        sql += " WHERE " + " AND ".join(clauses)
    sql += f" ORDER BY {order_by}"
    cursor = connection.execute(sql, params)
    columns = [description[0] for description in cursor.description]
    return [_decode(row, columns) for row in cursor.fetchall()]


__all__ = [
    "NotAScratchDatabase",
    "REVIEW_SCHEMA_VERSION",
    "assert_scratch",
    "ensure_review_schema",
    "insert_review_row",
    "is_scratch",
    "review_rows",
    "update_run",
    "update_spot_check_session",
    "update_target_positions",
]
