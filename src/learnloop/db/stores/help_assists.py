"""Adaptive hints H0: ``help_assists`` (migration 210).

Plain SQL over a caller's connection; the caller owns the transaction. The
writers are :mod:`learnloop.hints.telemetry` (H0's authored reveals) and
:mod:`learnloop.hints.service` (H2a's served hints and discriminating
answers). One row per assist shown (or
requested and never shown) on any surface; shared with the Reader workbench
(spec_adaptive_hints_v1 §9, spec_reader_workbench_v1 §5.7). RAW_LEDGER and
never evidence: replay and rebuild never read it.
"""

from __future__ import annotations

from collections.abc import Mapping
import sqlite3
from typing import Any

TABLE = "help_assists"

#: Every column, in table order (the schema test pins this against the
#: migration and both specs, G-H17).
COLUMNS: tuple[str, ...] = (
    "id", "surface", "assist_kind", "practice_item_id", "practice_item_hash", "practice_session_id",
    "workbench_session_id", "attempt_id", "submission_id", "hint_kind", "level", "offered_level", "level_source", "horizon",
    "route_id", "from_node_id", "target_node_id", "map_id", "strategy", "body_md", "authored_index",
    "work_hash", "work_chars", "placement_json", "chooser", "options_json", "probabilities_json",
    "drawn_option_json", "propensity", "seed", "policy_version", "question_set_version", "state_hash",
    "request", "feedback_text", "feedback_shortcut", "contract_failures_json", "leak_flags_json", "shown",
    "counted_by", "model", "prompt_version", "input_hash", "latency_ms", "requested_at", "shown_at",
    "submitted_at", "submit_latency_seconds", "step_snapshot_json", "step_verdicts_json",
    "first_questionable_step_id", "error_kind_guess",
    "about_step_id", "continue_from_step_id", "rivals_json", "predicted_answers_json", "eig_nats",
    "feedback_step_id", "cited_span_ids_json", "retrieval_manifest_json", "alternatives_json",
)
_COLUMN_SET = frozenset(COLUMNS)


def insert_assist(connection: sqlite3.Connection, row: Mapping[str, Any]) -> None:
    """Insert one assist row; columns left out are NULL (or their default)."""

    unknown = set(row) - _COLUMN_SET
    if unknown:
        raise ValueError(f"help_assists has no columns {sorted(unknown)}")
    names = [name for name in COLUMNS if name in row]
    connection.execute(
        f"INSERT INTO help_assists ({', '.join(names)}) VALUES ({', '.join('?' for _ in names)})",
        tuple(row[name] for name in names),
    )


def stamp_submitted(
    connection: sqlite3.Connection,
    *,
    submission_id: str,
    practice_item_id: str,
    submitted_at: str,
    latency_seconds: float | None = None,
) -> int:
    """Record when a submission reached the sidecar, before grading, and the
    open-to-submit latency it sent, together, on its still-unattached rows.
    The first stamp stays, both values: a retry of the same submission (a
    grading fallback answered by a self-grade) keeps the time the learner
    first submitted and that submit's latency (review round 2, V3), never the
    retry's later one."""

    cursor = connection.execute(
        "UPDATE help_assists SET submitted_at = ?, submit_latency_seconds = ? "
        "WHERE submission_id = ? AND practice_item_id = ? AND attempt_id IS NULL AND submitted_at IS NULL",
        (submitted_at, _latency(latency_seconds), submission_id, practice_item_id),
    )
    return int(cursor.rowcount or 0)


def attach_submission(
    connection: sqlite3.Connection,
    *,
    submission_id: str,
    practice_item_id: str,
    attempt_id: str,
    submitted_at: str | None = None,
    latency_seconds: float | None = None,
) -> int:
    """Fill ``attempt_id`` on the rows recorded under ``submission_id`` for the
    item (and ``submitted_at`` with ``latency_seconds``, together, where no
    stamp was made); returns how many it attached. Matching on the submission key alone, never on the session and
    item, means a row a failed attach left behind is never swept into a later
    submission's attempt, and the attach is idempotent: a retried submit or a
    recovery of the same submission repairs it. A row already attached keeps
    its attempt (the identity trigger refuses a move)."""

    # Every SET expression reads the row as it was: the latency is written
    # only where this update also writes the submit time.
    cursor = connection.execute(
        "UPDATE help_assists SET attempt_id = ?, submitted_at = COALESCE(submitted_at, ?), "
        "submit_latency_seconds = CASE WHEN submitted_at IS NULL AND ? IS NOT NULL THEN ? "
        "ELSE submit_latency_seconds END "
        "WHERE submission_id = ? AND practice_item_id = ? AND attempt_id IS NULL",
        (attempt_id, submitted_at, submitted_at, _latency(latency_seconds), submission_id, practice_item_id),
    )
    return int(cursor.rowcount or 0)


def assist(connection: sqlite3.Connection, assist_id: str) -> dict[str, Any] | None:
    """One row as a dict, or None."""

    row = connection.execute(
        f"SELECT {', '.join(COLUMNS)} FROM help_assists WHERE id = ?", (assist_id,)
    ).fetchone()
    return dict(zip(COLUMNS, tuple(row))) if row is not None else None


def submission_assists(
    connection: sqlite3.Connection, *, submission_id: str, practice_item_id: str
) -> list[dict[str, Any]]:
    """Every row recorded under a submission key for the item, in the order
    requested (shown or not, attached or not): this attempt's hints."""

    rows = connection.execute(
        f"SELECT {', '.join(COLUMNS)} FROM help_assists WHERE submission_id = ? AND practice_item_id = ? "
        "ORDER BY requested_at, rowid",
        (submission_id, practice_item_id),
    ).fetchall()
    return [dict(zip(COLUMNS, tuple(row))) for row in rows]


#: The attempts that close a row's count (H2a review F1; round 3, W1): its
#: own submission's, and any attempt of the same session and item committed
#: at or after the row was requested, whatever its submission key (NULL
#: included). The latter is the window a keyless submit folds ("since the
#: item's last attempt in this session", :func:`server_fold`), so a hint a
#: keyless attempt could have counted is never shown after it commits.
_CLOSED = (
    "EXISTS (SELECT 1 FROM practice_attempts "
    "WHERE practice_attempts.submission_id = help_assists.submission_id) "
    "OR EXISTS (SELECT 1 FROM practice_attempts "
    "WHERE practice_attempts.session_id = help_assists.practice_session_id "
    "AND practice_attempts.practice_item_id = help_assists.practice_item_id "
    "AND practice_attempts.created_at >= help_assists.requested_at)"
)


def mark_shown(connection: sqlite3.Connection, assist_id: str, *, shown_at: str) -> bool:
    """A prepared server hint (``shown = 0``) delivered to the learner: shown
    once, with its time. Never a row already attached to an attempt (its
    count was taken), never a row whose count is closed (:data:`_CLOSED`: its
    submission committed an attempt, H2a review F1, or an attempt of its
    session and item committed at or after it was requested, round 3 W1)
    and never twice; True when this call showed it. The caller holds the
    write lock (``BEGIN IMMEDIATE``), so no attempt commits in between."""

    cursor = connection.execute(
        "UPDATE help_assists SET shown = 1, shown_at = ? "
        "WHERE id = ? AND shown = 0 AND counted_by = 'server' AND attempt_id IS NULL "
        f"AND NOT ({_CLOSED})",
        (shown_at, assist_id),
    )
    return bool(cursor.rowcount)


def count_closed(connection: sqlite3.Connection, assist_id: str) -> bool:
    """Whether a row's count is closed by a committed attempt (:data:`_CLOSED`)."""

    row = connection.execute(f"SELECT 1 FROM help_assists WHERE id = ? AND ({_CLOSED})", (assist_id,)).fetchone()
    return row is not None


def submission_committed(connection: sqlite3.Connection, submission_id: str | None) -> bool:
    """Whether a submission key already committed its attempt."""

    if not submission_id:
        return False
    row = connection.execute(
        "SELECT 1 FROM practice_attempts WHERE submission_id = ? LIMIT 1", (submission_id,)
    ).fetchone()
    return row is not None


def keyless_window_start(connection: sqlite3.Connection, *, practice_item_id: str, session_id: str) -> str | None:
    """Where a keyless submit's window starts: the item's last attempt in
    this session (round 3, W1), or None."""

    row = connection.execute(
        "SELECT MAX(created_at) FROM practice_attempts WHERE practice_item_id = ? AND session_id = ?",
        (practice_item_id, session_id),
    ).fetchone()
    return str(row[0]) if row is not None and row[0] is not None else None


def server_fold(
    connection: sqlite3.Connection,
    *,
    practice_item_id: str,
    session_id: str,
    submission_id: str | None,
    since: str | None = None,
) -> tuple[int, bool]:
    """The server-counted hints a submission folds (hints spec §5): how many
    shown rows at levels 1-3, and whether any shown row is at level 4-5
    (``primed``). Only rows still unattached (an attempt already took its
    own), of this session and item, under the submission's key when it has
    one (H0 review F1: never another submission's rows); a client with no key
    folds the session's unattached rows requested after ``since`` (the item's
    last attempt in this session: the window ``mark_shown`` closes)."""

    where, values = _fold_rows(practice_item_id=practice_item_id, session_id=session_id,
                               submission_id=submission_id, since=since)
    row = connection.execute(
        "SELECT COALESCE(SUM(CASE WHEN level BETWEEN 1 AND 3 THEN 1 ELSE 0 END), 0), "
        "COALESCE(MAX(CASE WHEN level BETWEEN 4 AND 5 THEN 1 ELSE 0 END), 0) "
        f"FROM help_assists WHERE {where}",
        values,
    ).fetchone()
    return int(row[0] or 0), bool(row[1])


def _fold_rows(*, practice_item_id: str, session_id: str, submission_id: str | None,
               since: str | None) -> tuple[str, tuple[Any, ...]]:
    """The rows a fold counts (:func:`server_fold`) and a keyless attempt
    attaches (:func:`attach_keyless_fold`): one definition, so the rows
    attached are exactly the rows counted. Only unattached rows: a row an
    attempt took is never counted again, whatever its key."""

    clauses = ["practice_item_id = ?", "practice_session_id = ?", "attempt_id IS NULL", "shown = 1",
               "counted_by = 'server'", "assist_kind = 'hint'"]
    values: list[Any] = [practice_item_id, session_id]
    if submission_id is not None:
        clauses.append("submission_id = ?")
        values.append(submission_id)
    elif since is not None:
        clauses.append("requested_at > ?")
        values.append(since)
    return " AND ".join(clauses), tuple(values)


def attach_keyless_fold(
    connection: sqlite3.Connection, *, practice_item_id: str, session_id: str, since: str | None, attempt_id: str
) -> int:
    """A keyless attempt takes the server hint rows its fold counted (round
    3b): ``attempt_id`` set once (NULL to a value, as H0's attach writes and
    its identity trigger allows), in the attempt's own write transaction, so
    no later fold, keyed or keyless, counts them again. Only server-counted
    hint rows: H0's authored-reveal telemetry is attached by key as before."""

    where, values = _fold_rows(practice_item_id=practice_item_id, session_id=session_id, submission_id=None,
                               since=since)
    cursor = connection.execute(f"UPDATE help_assists SET attempt_id = ? WHERE {where}", (attempt_id, *values))
    return int(cursor.rowcount or 0)


def _latency(value: float | None) -> float | None:
    """A latency the client sent, or None (a negative one is not believed)."""

    if value is None:
        return None
    seconds = float(value)
    return seconds if seconds >= 0 else None


__all__ = [
    "COLUMNS", "TABLE", "assist", "attach_keyless_fold", "attach_submission", "count_closed", "insert_assist", "keyless_window_start",
    "mark_shown", "server_fold", "stamp_submitted", "submission_assists", "submission_committed",
]
