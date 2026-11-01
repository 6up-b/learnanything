"""Reader workbench RW6b: ``reader_session_digests`` (migration 227).

Plain SQL over a caller's connection; the caller owns the transaction. The
writer is :mod:`learnloop.instructional.reader_followups`. One row per reader
session follow-ups were planned for: the typed summary as it stood, the
``test_me_later`` commitments created and the valuation receipt (WORKFLOW: a
paid relevance step stands behind it, so a rebuild never clears or re-runs
it; replay never reads it).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import json
import sqlite3
from typing import Any

TABLE = "reader_session_digests"
STATUSES = ("planned", "incomplete")
#: The columns a later step may set (never the session, its summary's time or its id).
MUTABLE_COLUMNS = frozenset({"status", "summary_json", "followup_commitment_ids_json", "valuation_json",
                             "revaluation_json", "revalued_on", "dismissed_at", "updated_at"})

_JSON_COLUMNS = {"visit_ids_json": ("visit_ids", []), "summary_json": ("summary", {}),
                 "followup_commitment_ids_json": ("followup_commitment_ids", []),
                 "valuation_json": ("valuation", {}), "revaluation_json": ("revaluation", None),
                 "cited_event_ids_json": ("cited_event_ids", None)}


def _dumps(value: Any) -> str:
    return json.dumps(value, sort_keys=True, default=str, ensure_ascii=False)


def insert_digest(connection: sqlite3.Connection, row: Mapping[str, Any]) -> None:
    if row["status"] not in STATUSES:
        raise ValueError(f"status must be one of {', '.join(STATUSES)}")
    connection.execute(
        "INSERT INTO reader_session_digests (id, extraction_id, session_key, visit_ids_json, started_at, ended_at, "
        "status, summary_json, followup_commitment_ids_json, valuation_json, created_at, updated_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (row["id"], row["extraction_id"], row["session_key"], _dumps(list(row.get("visit_ids") or [])),
         row["started_at"], row["ended_at"], row["status"], _dumps(row.get("summary") or {}),
         _dumps(list(row.get("followup_commitment_ids") or [])), _dumps(row.get("valuation") or {}),
         row["created_at"], row["created_at"]),
    )


def update_digest(connection: sqlite3.Connection, digest_id: str, **columns: Any) -> None:
    unknown = set(columns) - MUTABLE_COLUMNS
    if unknown:
        raise ValueError(f"reader_session_digests columns {sorted(unknown)} are not updatable")
    if "status" in columns and columns["status"] not in STATUSES:
        raise ValueError(f"status must be one of {', '.join(STATUSES)}")
    values = {name: (_dumps(value) if name.endswith("_json") and value is not None else value)
              for name, value in columns.items()}
    names = sorted(values)
    connection.execute(
        f"UPDATE reader_session_digests SET {', '.join(f'{name} = ?' for name in names)} WHERE id = ?",
        (*[values[name] for name in names], digest_id))


#: RW6b part 2: the narrative's columns. Written once per session by
#: :func:`set_narrative` (``learnloop.instructional.reader_digest``), never by
#: ``update_digest``; part 1's planner compares a row without them.
NARRATIVE_COLUMNS = ("narrative_md", "cited_event_ids_json", "model", "prompt_version")
#: The narrative's label on every surface (spec §9.2, UX §4.8) and its
#: authority (W1 tier 1: salience only, never evidence).
NARRATIVE_LABEL = "summary written by LearnLoop's model"
NARRATIVE_AUTHORITY = "salience_only"
#: The decoded keys of the narrative's columns (``_decode``'s names).
NARRATIVE_KEYS = frozenset({"narrative_md", "cited_event_ids", "model", "prompt_version"})


def set_narrative(connection: sqlite3.Connection, digest_id: str, *, narrative_md: str | None,
                  cited_event_ids: Sequence[str] | None, model: str, prompt_version: str) -> bool:
    """Write the session's narrative once (RW6b part 2): True when written.

    ``narrative_md`` None records an attempt whose narrative was dropped
    (``prompt_version`` set marks the session as narrated either way: once
    per session). A row already narrated is left as it is (another process
    got there first). ``updated_at`` is left alone: it is part 1's planning
    clock, and a narrative never supersedes a plan."""

    cursor = connection.execute(
        "UPDATE reader_session_digests SET narrative_md = ?, cited_event_ids_json = ?, model = ?, "
        "prompt_version = ? WHERE id = ? AND prompt_version IS NULL",
        (narrative_md, _dumps(list(cited_event_ids)) if cited_event_ids is not None else None, model,
         prompt_version, digest_id))
    return cursor.rowcount == 1


def without_narrative(row: Mapping[str, Any] | None) -> dict[str, Any] | None:
    """A decoded digest row without its narrative (part 1's comparisons)."""

    return None if row is None else {key: value for key, value in row.items() if key not in NARRATIVE_KEYS}


def _decode(row: sqlite3.Row | Mapping[str, Any]) -> dict[str, Any]:
    out = dict(row)
    for column, (name, default) in _JSON_COLUMNS.items():
        raw = out.pop(column, None)
        try:
            out[name] = json.loads(raw) if raw else default
        except (TypeError, ValueError):
            out[name] = default
    return out


def digest(connection: sqlite3.Connection, digest_id: str) -> dict[str, Any] | None:
    row = connection.execute("SELECT * FROM reader_session_digests WHERE id = ?", (digest_id,)).fetchone()
    return _decode(row) if row is not None else None


def digest_for_session(connection: sqlite3.Connection, extraction_id: str, session_key: str) -> dict[str, Any] | None:
    row = connection.execute(
        "SELECT * FROM reader_session_digests WHERE extraction_id = ? AND session_key = ?",
        (extraction_id, session_key)).fetchone()
    return _decode(row) if row is not None else None


def digests(connection: sqlite3.Connection, *, extraction_id: str | None = None,
            ended_after: str | None = None) -> list[dict[str, Any]]:
    clauses: list[str] = []
    params: list[Any] = []
    if extraction_id is not None:
        clauses.append("extraction_id = ?")
        params.append(extraction_id)
    if ended_after is not None:
        clauses.append("ended_at > ?")
        params.append(ended_after)
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    return [_decode(row) for row in connection.execute(
        f"SELECT * FROM reader_session_digests {where} ORDER BY ended_at, id", params)]


def digest_for_commitment(connection: sqlite3.Connection, commitment_id: str) -> dict[str, Any] | None:
    row = connection.execute(
        "SELECT d.* FROM reader_session_digests d, json_each(d.followup_commitment_ids_json) j "
        "WHERE j.value = ? ORDER BY d.created_at LIMIT 1", (commitment_id,)).fetchone()
    return _decode(row) if row is not None else None


def session_keys(connection: sqlite3.Connection, extraction_ids: Sequence[str] | None = None) -> set[tuple[str, str]]:
    rows = connection.execute("SELECT extraction_id, session_key FROM reader_session_digests").fetchall()
    wanted = None if extraction_ids is None else set(extraction_ids)
    return {(str(r[0]), str(r[1])) for r in rows if wanted is None or str(r[0]) in wanted}


__all__ = ["MUTABLE_COLUMNS", "NARRATIVE_AUTHORITY", "NARRATIVE_COLUMNS", "NARRATIVE_KEYS", "NARRATIVE_LABEL", "STATUSES", "TABLE", "digest",
           "digest_for_commitment", "digest_for_session", "digests", "insert_digest", "session_keys",
           "set_narrative", "update_digest", "without_narrative"]
