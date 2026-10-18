"""Adaptive hints H0: ``help_assists`` (migration 210).

Plain SQL over a caller's connection; the caller owns the transaction. The
only writer is :mod:`learnloop.hints.telemetry`. One row per assist shown (or
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
    "submitted_at", "step_snapshot_json", "step_verdicts_json", "first_questionable_step_id", "error_kind_guess",
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
) -> int:
    """Record when a submission reached the sidecar, before grading, on its
    still-unattached rows. The first stamp stays: a retry of the same
    submission (a grading fallback answered by a self-grade) keeps the time
    the learner first submitted."""

    cursor = connection.execute(
        "UPDATE help_assists SET submitted_at = ? "
        "WHERE submission_id = ? AND practice_item_id = ? AND attempt_id IS NULL AND submitted_at IS NULL",
        (submitted_at, submission_id, practice_item_id),
    )
    return int(cursor.rowcount or 0)


def attach_submission(
    connection: sqlite3.Connection,
    *,
    submission_id: str,
    practice_item_id: str,
    attempt_id: str,
    submitted_at: str | None = None,
) -> int:
    """Fill ``attempt_id`` on the rows recorded under ``submission_id`` for the
    item (and ``submitted_at`` where no stamp was made); returns how many it
    attached. Matching on the submission key alone, never on the session and
    item, means a row a failed attach left behind is never swept into a later
    submission's attempt, and the attach is idempotent: a retried submit or a
    recovery of the same submission repairs it. A row already attached keeps
    its attempt (the identity trigger refuses a move)."""

    cursor = connection.execute(
        "UPDATE help_assists SET attempt_id = ?, submitted_at = COALESCE(submitted_at, ?) "
        "WHERE submission_id = ? AND practice_item_id = ? AND attempt_id IS NULL",
        (attempt_id, submitted_at, submission_id, practice_item_id),
    )
    return int(cursor.rowcount or 0)


__all__ = ["COLUMNS", "TABLE", "attach_submission", "insert_assist", "stamp_submitted"]
