"""Reader workbench RW2a: ``workbench_sessions`` and ``workbench_steps`` (migration 207).

Plain SQL over a caller's connection; the caller owns the transaction. The
only writer is :mod:`learnloop.reader.workbench`. ``workbench_sessions`` is
lifecycle state (WORKFLOW) and is updated in place; ``workbench_steps`` is
append-only (RAW_LEDGER, enforced by trigger). Replay and rebuild never read
either table: the submitted attempt carries the evidence.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterable, Mapping
from typing import Any

SESSIONS = "workbench_sessions"
STEPS = "workbench_steps"

SESSION_COLUMNS = (
    "id", "practice_item_id", "stem_md", "import_status", "import_batch_id", "import_request_json",
    "import_error", "origin", "entry", "parent_session_id", "extraction_id", "span_ids_json",
    "source_visible", "source_hidden_at", "source_shown_at", "practice_session_id",
    "assessment_contract_version_id", "contract_subject_id", "carried_hints", "earlier_opened_at",
    "scheduler_candidate_id", "plan_presentation_id",
    "help_style", "status",
    "attempt_id", "client_idempotency_key", "created_at", "updated_at", "closed_at",
)
#: The session columns a lifecycle change may set (never id or created_at).
#: ``origin`` changes only when a resume moves the session to another surface.
MUTABLE_SESSION_COLUMNS = frozenset(SESSION_COLUMNS) - {"id", "created_at", "entry", "client_idempotency_key"}

STEP_COLUMNS = (
    "id", "session_id", "ordinal", "kind", "body_md", "supersedes_id", "deleted",
    "client_idempotency_key", "created_at",
)


def _row(row: sqlite3.Row | None) -> dict[str, Any] | None:
    return dict(row) if row is not None else None


def insert_session(connection: sqlite3.Connection, values: Mapping[str, Any]) -> None:
    unknown = sorted(set(values) - set(SESSION_COLUMNS))
    if unknown:
        raise ValueError(f"unknown workbench session columns: {unknown}")
    names = [name for name in SESSION_COLUMNS if name in values]
    connection.execute(
        f"INSERT INTO {SESSIONS}({', '.join(names)}) VALUES ({', '.join('?' for _ in names)})",
        [values[name] for name in names],
    )


def update_session(connection: sqlite3.Connection, session_id: str, values: Mapping[str, Any]) -> None:
    unknown = sorted(set(values) - MUTABLE_SESSION_COLUMNS)
    if unknown:
        raise ValueError(f"workbench session columns that never change: {unknown}")
    if not values:
        return
    names = list(values)
    connection.execute(
        f"UPDATE {SESSIONS} SET {', '.join(f'{name} = ?' for name in names)} WHERE id = ?",
        [*(values[name] for name in names), session_id],
    )


def fetch_session(connection: sqlite3.Connection, session_id: str) -> dict[str, Any] | None:
    return _row(connection.execute(f"SELECT * FROM {SESSIONS} WHERE id = ?", (session_id,)).fetchone())


def session_by_key(connection: sqlite3.Connection, key: str) -> dict[str, Any] | None:
    return _row(connection.execute(
        f"SELECT * FROM {SESSIONS} WHERE client_idempotency_key = ?", (key,)
    ).fetchone())


def open_session_for_item(connection: sqlite3.Connection, practice_item_id: str) -> dict[str, Any] | None:
    return _row(connection.execute(
        f"SELECT * FROM {SESSIONS} WHERE practice_item_id = ? AND status = 'open'"
        " ORDER BY updated_at DESC, id DESC LIMIT 1",
        (practice_item_id,),
    ).fetchone())


def open_session_for_selection(
    connection: sqlite3.Connection, *, extraction_id: str, span_ids_json: str, stem_md: str
) -> dict[str, Any] | None:
    return _row(connection.execute(
        f"SELECT * FROM {SESSIONS} WHERE extraction_id = ? AND span_ids_json = ? AND stem_md = ?"
        " AND status = 'open' ORDER BY updated_at DESC, id DESC LIMIT 1",
        (extraction_id, span_ids_json, stem_md),
    ).fetchone())


def session_for_attempt(connection: sqlite3.Connection, attempt_id: str) -> dict[str, Any] | None:
    return _row(connection.execute(
        f"SELECT * FROM {SESSIONS} WHERE attempt_id = ? ORDER BY updated_at DESC LIMIT 1", (attempt_id,)
    ).fetchone())


def sessions_where(
    connection: sqlite3.Connection, *, column: str, value: str, statuses: Iterable[str]
) -> list[dict[str, Any]]:
    if column not in ("practice_item_id", "extraction_id"):
        raise ValueError(f"workbench sessions are not listed by {column!r}")
    wanted = list(statuses)
    rows = connection.execute(
        f"SELECT * FROM {SESSIONS} WHERE {column} = ? AND status IN ({', '.join('?' for _ in wanted)})"
        " ORDER BY updated_at DESC, id DESC",
        (value, *wanted),
    ).fetchall()
    return [dict(row) for row in rows]


def open_sessions(connection: sqlite3.Connection) -> list[dict[str, Any]]:
    """UX Phase 3 (Today's threads): every open problem worked on a source,
    newest first. Set-aside (abandoned) and submitted problems are not threads."""

    rows = connection.execute(
        f"SELECT * FROM {SESSIONS} WHERE status = 'open' AND extraction_id IS NOT NULL"
        " ORDER BY updated_at DESC, id DESC"
    ).fetchall()
    return [dict(row) for row in rows]


def steps_for_session(connection: sqlite3.Connection, session_id: str) -> list[dict[str, Any]]:
    rows = connection.execute(
        f"SELECT * FROM {STEPS} WHERE session_id = ? ORDER BY created_at, id", (session_id,)
    ).fetchall()
    return [dict(row) for row in rows]


def steps_for_sessions(connection: sqlite3.Connection, session_ids: Iterable[str]) -> dict[str, list[dict[str, Any]]]:
    wanted = list(session_ids)
    if not wanted:
        return {}
    rows = connection.execute(
        f"SELECT * FROM {STEPS} WHERE session_id IN ({', '.join('?' for _ in wanted)}) ORDER BY created_at, id",
        wanted,
    ).fetchall()
    out: dict[str, list[dict[str, Any]]] = {session_id: [] for session_id in wanted}
    for row in rows:
        out[row["session_id"]].append(dict(row))
    return out


def step_by_key(connection: sqlite3.Connection, session_id: str, key: str) -> dict[str, Any] | None:
    return _row(connection.execute(
        f"SELECT * FROM {STEPS} WHERE session_id = ? AND client_idempotency_key = ?", (session_id, key)
    ).fetchone())


def insert_step(connection: sqlite3.Connection, values: Mapping[str, Any]) -> None:
    unknown = sorted(set(values) - set(STEP_COLUMNS))
    if unknown:
        raise ValueError(f"unknown workbench step columns: {unknown}")
    names = [name for name in STEP_COLUMNS if name in values]
    connection.execute(
        f"INSERT INTO {STEPS}({', '.join(names)}) VALUES ({', '.join('?' for _ in names)})",
        [values[name] for name in names],
    )
