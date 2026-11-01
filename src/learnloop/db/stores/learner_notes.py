"""Deliverable curriculum C2's tables (migration 229): ``learner_notes`` (snapshots of
the learner's notes, taken only when linked) and ``learner_note_links`` (the model's
proposals and the learner's links and hides). Both RAW_LEDGER, append-only by trigger.

Every function takes the caller's connection (and its transaction). Nothing that
scores, schedules, projects, grades, serves, generates or replays reads these tables:
the only reader is ``source_retrieval.note_links`` (display and learner-voice records).
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterable, Mapping
from typing import Any

NOTE_COLUMNS = (
    "id", "note_key", "path", "heading_path", "line", "content_hash", "title", "heading", "captured_on", "origin",
    "text_md", "truncated", "created_at",
)
LINK_COLUMNS = (
    "id", "note_id", "note_key", "target_kind", "target_key", "learning_object_id", "extraction_id", "section_id",
    "span_id", "goal_id", "authorship", "status", "how", "how_line", "state_key", "ledger_id", "model",
    "prompt_version", "created_at",
)


def tables_present(connection: sqlite3.Connection) -> bool:
    found = {str(row[0]) for row in connection.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name IN ('learner_notes', 'learner_note_links')")}
    return len(found) == 2


def _dicts(cursor: sqlite3.Cursor) -> list[dict[str, Any]]:
    names = [column[0] for column in cursor.description or ()]
    return [dict(zip(names, values)) for values in cursor.fetchall()]


def _insert(connection: sqlite3.Connection, table: str, columns: tuple[str, ...], row: Mapping[str, Any]) -> None:
    connection.execute(
        f"INSERT INTO {table} ({','.join(columns)}) VALUES ({','.join('?' for _ in columns)})",
        tuple(row.get(column) for column in columns))


# -- snapshots -----------------------------------------------------------------------------------

def snapshot(connection: sqlite3.Connection, note_key: str, content_hash: str) -> dict[str, Any] | None:
    rows = _dicts(connection.execute(
        "SELECT * FROM learner_notes WHERE note_key = ? AND content_hash = ?", (note_key, content_hash)))
    return rows[0] if rows else None


def insert_note(connection: sqlite3.Connection, row: Mapping[str, Any]) -> str:
    """Store a snapshot once per (note, content hash); returns the stored row's id."""

    found = snapshot(connection, str(row["note_key"]), str(row["content_hash"]))
    if found is not None:
        return str(found["id"])
    _insert(connection, "learner_notes", NOTE_COLUMNS, row)
    return str(row["id"])


def notes_by_id(connection: sqlite3.Connection, note_ids: Iterable[str]) -> dict[str, dict[str, Any]]:
    wanted = sorted({str(note_id) for note_id in note_ids})
    if not wanted:
        return {}
    return {str(row["id"]): row for row in _dicts(connection.execute(
        f"SELECT * FROM learner_notes WHERE id IN ({','.join('?' for _ in wanted)})", wanted))}


def latest_note(connection: sqlite3.Connection, note_key: str) -> dict[str, Any] | None:
    rows = _dicts(connection.execute(
        "SELECT * FROM learner_notes WHERE note_key = ? ORDER BY created_at DESC, rowid DESC LIMIT 1", (note_key,)))
    return rows[0] if rows else None


def note_count(connection: sqlite3.Connection) -> int:
    return int(connection.execute("SELECT COUNT(*) FROM learner_notes").fetchone()[0])


# -- links ---------------------------------------------------------------------------------------

def insert_link(connection: sqlite3.Connection, row: Mapping[str, Any]) -> None:
    _insert(connection, "learner_note_links", LINK_COLUMNS, row)


def links(connection: sqlite3.Connection, *, extraction_id: str | None = None,
          learning_object_ids: Iterable[str] | None = None, note_key: str | None = None) -> list[dict[str, Any]]:
    """Link rows, oldest first, narrowed by reading, LO or note (all of them with no filter)."""

    clauses: list[str] = []
    params: list[Any] = []
    if extraction_id is not None:
        clauses.append("extraction_id = ?")
        params.append(extraction_id)
    if learning_object_ids is not None:
        wanted = sorted({str(lo) for lo in learning_object_ids})
        if not wanted:
            return []
        clauses.append(f"learning_object_id IN ({','.join('?' for _ in wanted)})")
        params.extend(wanted)
    if note_key is not None:
        clauses.append("note_key = ?")
        params.append(note_key)
    where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
    return _dicts(connection.execute(f"SELECT * FROM learner_note_links{where} ORDER BY created_at, rowid", params))


def learner_rows_for(connection: sqlite3.Connection, note_keys: Iterable[str]) -> list[dict[str, Any]]:
    """The learner's own rows on these notes (their links and hides), oldest first."""

    wanted = sorted({str(key) for key in note_keys})
    if not wanted:
        return []
    return _dicts(connection.execute(
        f"SELECT * FROM learner_note_links WHERE authorship = 'learner' AND note_key IN "
        f"({','.join('?' for _ in wanted)}) ORDER BY created_at, rowid", wanted))


def ai_rows_for_state(connection: sqlite3.Connection, learning_object_id: str, state_key: str) -> list[dict[str, Any]]:
    return _dicts(connection.execute(
        "SELECT * FROM learner_note_links WHERE authorship = 'ai' AND learning_object_id = ? AND state_key = ? "
        "ORDER BY created_at, rowid", (learning_object_id, state_key)))


def judged(connection: sqlite3.Connection, task: str, learning_object_id: str, state_key: str) -> bool:
    """Was this topic's candidate state judged (the model's verdict rows in the ledger)?"""

    return connection.execute(
        "SELECT 1 FROM judgment_ledger WHERE task = ? AND left_kind = 'learning_object' AND left_id = ? "
        "AND input_hash = ? AND judge = 'llm' LIMIT 1", (task, learning_object_id, state_key)).fetchone() is not None


def latest_states(connection: sqlite3.Connection, task: str, learning_object_ids: Iterable[str]) -> dict[str, str]:
    """The newest judged state per topic (an older judgment's proposals give way to it)."""

    wanted = sorted({str(lo) for lo in learning_object_ids})
    if not wanted:
        return {}
    out: dict[str, str] = {}
    for left_id, input_hash in connection.execute(
            f"SELECT left_id, input_hash FROM judgment_ledger WHERE task = ? AND left_kind = 'learning_object' "
            f"AND judge = 'llm' AND left_id IN ({','.join('?' for _ in wanted)}) ORDER BY created_at, rowid",
            (task, *wanted)):
        out[str(left_id)] = str(input_hash)
    return out


def takes_quoting_notes(connection: sqlite3.Connection, prefix: str) -> int:
    """RW4d takes written from a note (*use as my take*), counted by their quote's prefix."""

    found = connection.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='source_object_relations'").fetchone()
    if found is None:
        return 0
    return int(connection.execute(
        "SELECT COUNT(*) FROM source_object_relations WHERE relation_type = 'learner_connects' "
        "AND substr(COALESCE(learner_text, ''), 1, ?) = ?", (len(prefix), prefix)).fetchone()[0])


def link_counts(connection: sqlite3.Connection) -> dict[str, int]:
    """Aggregates for the report: rows by authorship and status (never a note's text)."""

    out: dict[str, int] = {}
    for authorship, status, count in connection.execute(
            "SELECT authorship, status, COUNT(*) FROM learner_note_links GROUP BY authorship, status"):
        out[f"{authorship}:{status}"] = int(count)
    return out


__all__ = [
    "LINK_COLUMNS",
    "NOTE_COLUMNS",
    "ai_rows_for_state",
    "insert_link",
    "judged",
    "latest_states",
    "takes_quoting_notes",
    "insert_note",
    "latest_note",
    "learner_rows_for",
    "link_counts",
    "links",
    "note_count",
    "notes_by_id",
    "snapshot",
    "tables_present",
]
