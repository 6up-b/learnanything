"""FG1c's records (migration 242): the exposure receipts and the raw marks ledger. No policy here;
``learnloop.followup_serve.marks`` and ``learnloop.followup_run.marks`` own it.

Every writer runs on the caller's connection. A refused receipt rolls back alone (a savepoint)
with a warning and returns False: a receipt never blocks an answer or a screen, as
:mod:`learnloop.db.stores.data_capture`.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
import json
import logging
import sqlite3
from typing import Any

from learnloop.ids import new_ulid

logger = logging.getLogger(__name__)

EXPOSURES = "hypothesis_list_exposures"
PROBE_LINKS = "hypothesis_exposure_probe_links"
MARKS = "hypothesis_marks"

EXPOSURE_COLUMNS: tuple[str, ...] = (
    "id", "attempt_id", "factor_id", "diagnosis_id", "workflow_id", "surface", "hypothesis_version_ids_json",
    "order_seed", "order_version", "probe_answered", "probe_attempt_id", "shown_at", "created_at",
)
MARK_COLUMNS: tuple[str, ...] = (
    "id", "attempt_id", "learning_object_id", "diagnosis_id", "factor_id", "workflow_id", "hypothesis_version_id",
    "hypothesis_key", "mark", "free_text", "display_position", "display_order_json", "order_seed", "order_version",
    "surface", "probe_answered", "probe_attempt_id", "probe_outcome_json", "created_at",
)


def present(connection: sqlite3.Connection) -> bool:
    """False on a database below migration 242: every reader treats that as no marks."""

    found = connection.execute(
        "SELECT COUNT(*) FROM sqlite_master WHERE type = 'table' AND name IN (?, ?, ?)", (EXPOSURES, PROBE_LINKS, MARKS)
    ).fetchone()[0]
    return int(found) == 3


def _insert(connection: sqlite3.Connection, table: str, columns: tuple[str, ...], row: Mapping[str, Any]) -> bool:
    connection.execute("SAVEPOINT hypothesis_marks_append")
    try:
        connection.execute(
            f"INSERT INTO {table} ({','.join(columns)}) VALUES ({','.join('?' for _ in columns)})",
            [row.get(column) for column in columns],
        )
    except sqlite3.Error:
        connection.execute("ROLLBACK TO hypothesis_marks_append")
        connection.execute("RELEASE hypothesis_marks_append")
        logger.warning("%s: a row for attempt %s was refused", table, row.get("attempt_id"), exc_info=True)
        return False
    connection.execute("RELEASE hypothesis_marks_append")
    return True


def insert_exposure(connection: sqlite3.Connection, row: Mapping[str, Any]) -> str | None:
    """One display of a list; its id, or None (a warning) when refused."""

    identified = {**row, "id": row.get("id") or new_ulid()}
    return str(identified["id"]) if _insert(connection, EXPOSURES, EXPOSURE_COLUMNS, identified) else None


def insert_mark(connection: sqlite3.Connection, row: Mapping[str, Any]) -> str | None:
    """One mark, appended; its id, or None (a warning) when refused."""

    identified = {**row, "id": row.get("id") or new_ulid()}
    return str(identified["id"]) if _insert(connection, MARKS, MARK_COLUMNS, identified) else None


def link_probe_answer(connection: sqlite3.Connection, *, attempt_id: str, probe_attempt_id: str, at: str) -> int:
    """Each earlier display of this attempt's list gets its later receipt; a repeat adds nothing, and
    the exposure rows themselves never change. How many were written; 0 (a warning) when refused."""

    connection.execute("SAVEPOINT hypothesis_marks_link")
    try:
        written = 0
        for row in connection.execute(
            f"SELECT id FROM {EXPOSURES} WHERE attempt_id = ? AND probe_answered = 0 ORDER BY created_at, id", (attempt_id,)
        ).fetchall():
            cursor = connection.execute(
                f"INSERT OR IGNORE INTO {PROBE_LINKS} (id, exposure_id, attempt_id, probe_attempt_id, created_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (new_ulid(), str(row[0]), attempt_id, probe_attempt_id, at),
            )
            written += max(cursor.rowcount, 0)
    except sqlite3.Error:
        connection.execute("ROLLBACK TO hypothesis_marks_link")
        connection.execute("RELEASE hypothesis_marks_link")
        logger.warning("%s: the links of attempt %s were refused", PROBE_LINKS, attempt_id, exc_info=True)
        return 0
    connection.execute("RELEASE hypothesis_marks_link")
    return written


def _rows(cursor: Iterable[Any]) -> list[dict[str, Any]]:
    return [dict(row) for row in cursor]


#: Each mark with the statement of the version it marked: the one place that text is joined.
_MARKS_WITH_STATEMENT = (
    f"SELECT m.*, h.statement AS hypothesis_statement FROM {MARKS} m "
    "LEFT JOIN causal_hypotheses h ON h.id = m.hypothesis_version_id"
)


def marks_for_attempt(connection: sqlite3.Connection, attempt_id: str) -> list[dict[str, Any]]:
    """Every mark on the attempt, oldest first."""

    return _rows(connection.execute(
        f"{_MARKS_WITH_STATEMENT} WHERE m.attempt_id = ? ORDER BY m.created_at, m.id", (attempt_id,)))


def marks_for_learning_objects(connection: sqlite3.Connection, learning_object_ids: Iterable[str], *,
                               before: str) -> list[dict[str, Any]]:
    """Every mark on these topics made before ``before``, oldest first."""

    wanted = sorted(set(learning_object_ids))
    if not wanted:
        return []
    return _rows(connection.execute(
        f"{_MARKS_WITH_STATEMENT} WHERE m.learning_object_id IN ({','.join('?' for _ in wanted)}) AND m.created_at < ? "
        "ORDER BY m.created_at, m.id",
        [*wanted, before],
    ))


def all_marks(connection: sqlite3.Connection) -> list[dict[str, Any]]:
    return _rows(connection.execute(f"{_MARKS_WITH_STATEMENT} ORDER BY m.created_at, m.id"))


def all_exposures(connection: sqlite3.Connection) -> list[dict[str, Any]]:
    return _rows(connection.execute(f"SELECT * FROM {EXPOSURES} ORDER BY created_at, id"))


def exposures_for_attempt(connection: sqlite3.Connection, attempt_id: str) -> list[dict[str, Any]]:
    return _rows(connection.execute(
        f"SELECT * FROM {EXPOSURES} WHERE attempt_id = ? ORDER BY created_at, id", (attempt_id,)))


def probe_links(connection: sqlite3.Connection, attempt_id: str | None = None) -> list[dict[str, Any]]:
    if attempt_id is None:
        return _rows(connection.execute(f"SELECT * FROM {PROBE_LINKS} ORDER BY created_at, id"))
    return _rows(connection.execute(
        f"SELECT * FROM {PROBE_LINKS} WHERE attempt_id = ? ORDER BY created_at, id", (attempt_id,)))


def latest_observation(connection: sqlite3.Connection, factor_id: str) -> dict[str, Any] | None:
    """The newest answered observation of a factor (the discriminating-observation receipt), or None."""

    row = connection.execute(
        "SELECT id, factor_id, attempt_id, probe_attempt_id, outcome, classified_as_json, supports_open_set, admitted, "
        "admissible_as_independent, created_at FROM causal_discriminating_observations "
        "WHERE factor_id = ? AND probe_attempt_id IS NOT NULL ORDER BY created_at DESC, id DESC LIMIT 1",
        (factor_id,),
    ).fetchone()
    return dict(row) if row is not None else None


def attempt_of_item(connection: sqlite3.Connection, practice_item_id: str) -> dict[str, Any] | None:
    """The first answer to a (single-use) item, or None."""

    row = connection.execute(
        "SELECT id, rubric_score, correctness, created_at FROM practice_attempts WHERE practice_item_id = ? "
        "ORDER BY created_at, id LIMIT 1",
        (practice_item_id,),
    ).fetchone()
    return dict(row) if row is not None else None


def decode_ids(value: Any) -> list[str]:
    try:
        decoded = json.loads(value or "[]")
    except (TypeError, ValueError):
        return []
    return [str(entry) for entry in decoded] if isinstance(decoded, list) else []
