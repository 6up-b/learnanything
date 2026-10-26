"""Deliverable curriculum C0a's table (migration 222): ``section_coverage``
(WORKFLOW, append-only by trigger; display and retrieval context only).

Every function takes the caller's connection (and its transaction). Replay,
the plan, scheduling, grading and serving never read this table.
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterable, Mapping
from typing import Any

COLUMNS = (
    "id", "extraction_id", "section_id", "learning_object_id", "treatment", "roles_json", "assumes_json",
    "notation_md", "origin", "candidate_rank", "learner_override", "learner_text", "section_hash", "lo_hash",
    "state_key", "ledger_id", "model", "prompt_version", "created_at",
)


def table_present(connection: sqlite3.Connection) -> bool:
    return connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name = 'section_coverage'").fetchone() is not None


def _dicts(cursor: sqlite3.Cursor) -> list[dict[str, Any]]:
    names = [column[0] for column in cursor.description or ()]
    rows = []
    for values in cursor.fetchall():
        row = dict(zip(names, values))
        for column in ("roles_json", "assumes_json"):
            try:
                row[column[: -len("_json")]] = json.loads(row.get(column) or "[]")
            except (TypeError, ValueError):
                row[column[: -len("_json")]] = []
        rows.append(row)
    return rows


def insert(connection: sqlite3.Connection, row: Mapping[str, Any]) -> None:
    connection.execute(
        f"INSERT INTO section_coverage ({','.join(COLUMNS)}) VALUES ({','.join('?' for _ in COLUMNS)})",
        tuple(row.get(column) for column in COLUMNS))


def judged(connection: sqlite3.Connection, learning_object_id: str, state_key: str) -> list[dict[str, Any]]:
    """The judge's rows for exactly this LO and state (the cache hit)."""

    return _dicts(connection.execute(
        "SELECT * FROM section_coverage WHERE learning_object_id = ? AND state_key = ? "
        "AND learner_override IS NULL ORDER BY candidate_rank, id", (learning_object_id, state_key)))


def judged_states(connection: sqlite3.Connection,
                  learning_object_ids: Iterable[str]) -> dict[str, list[list[dict[str, Any]]]]:
    """Per LO, every judgment's judge rows (one list per state key), newest
    judgment first; each list in candidate order. The reader picks the
    current one (``section_coverage.standing``)."""

    out: dict[str, list[list[dict[str, Any]]]] = {}
    for lo_id in sorted({str(value) for value in learning_object_ids}):
        rows = _dicts(connection.execute(
            "SELECT * FROM section_coverage WHERE learning_object_id = ? AND learner_override IS NULL "
            "ORDER BY created_at DESC, rowid DESC", (lo_id,)))
        states: dict[str, list[dict[str, Any]]] = {}
        for row in rows:
            states.setdefault(str(row["state_key"]), []).append(row)
        if states:
            out[lo_id] = [sorted(group, key=lambda row: (row["candidate_rank"] or 0, row["id"]))
                          for group in states.values()]
    return out


def learning_objects_named(connection: sqlite3.Connection, extraction_id: str, section_id: str) -> list[str]:
    """Every LO any row (judge or learner) names for this section, oldest first."""

    return [str(row[0]) for row in connection.execute(
        "SELECT learning_object_id FROM section_coverage WHERE extraction_id = ? AND section_id = ? "
        "GROUP BY learning_object_id ORDER BY MIN(created_at), learning_object_id", (extraction_id, section_id))]


def corrections(connection: sqlite3.Connection, *, learning_object_ids: Iterable[str] | None = None,
                sections: Iterable[tuple[str, str]] | None = None) -> dict[tuple[str, str, str], dict[str, Any]]:
    """The newest learner row per (reading, section, LO) (``none`` is a cleared one),
    for these LOs or these sections."""

    clauses, params = ["learner_override IS NOT NULL"], []
    if learning_object_ids is not None:
        wanted = sorted({str(value) for value in learning_object_ids})
        if not wanted:
            return {}
        clauses.append(f"learning_object_id IN ({','.join('?' for _ in wanted)})")
        params.extend(wanted)
    rows = _dicts(connection.execute(
        f"SELECT * FROM section_coverage WHERE {' AND '.join(clauses)} ORDER BY created_at, rowid", params))
    keep = None if sections is None else {(str(e), str(s)) for e, s in sections}
    found: dict[tuple[str, str, str], dict[str, Any]] = {}
    for row in rows:
        if keep is not None and (row["extraction_id"], row["section_id"]) not in keep:
            continue
        found[(str(row["extraction_id"]), str(row["section_id"]), str(row["learning_object_id"]))] = row
    return found


def counts(connection: sqlite3.Connection) -> dict[str, int]:
    """Aggregates only (for reports): judge rows, learner rows, LOs judged."""

    judge, learner, los = connection.execute(
        "SELECT SUM(learner_override IS NULL), SUM(learner_override IS NOT NULL), "
        "COUNT(DISTINCT CASE WHEN learner_override IS NULL THEN learning_object_id END) FROM section_coverage"
    ).fetchone()
    return {"judge_rows": int(judge or 0), "learner_rows": int(learner or 0), "learning_objects": int(los or 0)}


__all__ = [
    "COLUMNS",
    "corrections",
    "counts",
    "insert",
    "judged",
    "judged_states",
    "learning_objects_named",
    "table_present",
]
