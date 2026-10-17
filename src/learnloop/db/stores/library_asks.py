"""Reader workbench RW4a: ``library_asks`` (migration 209).

Plain SQL over a caller's connection; the caller owns the transaction. The
only writer is :mod:`learnloop.source_retrieval.library_ask`.
One row per library question: its manifests (the ``find_sources`` calls), the
organizer's validated lines, and the comparison and tutor exchange it led to
(WORKFLOW: paid outputs, never re-run on rebuild; replay never reads it).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import json
import sqlite3
from typing import Any

TABLE = "library_asks"
#: The columns a later step may set (never the question, its anchor or its time).
MUTABLE_COLUMNS = frozenset({"organizer_json", "model", "comparison_id", "question_event_id", "kept_json",
                             "kept_at"})


def insert_ask(connection: sqlite3.Connection, row: Mapping[str, Any]) -> None:
    connection.execute(
        "INSERT INTO library_asks (id, caller, entry, query_md, query_hash, extraction_id, anchor_json, "
        "personalized, requested_perspectives_json, manifest_json, organizer_json, prompt_version, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (row["id"], row.get("caller", "learner"), row["entry"], row["query_md"], row["query_hash"],
         row.get("extraction_id"), json.dumps(row.get("anchor") or {}, sort_keys=True),
         int(bool(row["personalized"])), json.dumps(list(row.get("requested_perspectives") or [])),
         json.dumps(row.get("manifest") or {}, sort_keys=True, default=str),
         json.dumps(row.get("organizer") or {}, sort_keys=True, default=str), row.get("prompt_version"),
         row["created_at"]),
    )


def update_ask(connection: sqlite3.Connection, ask_id: str, **columns: Any) -> None:
    unknown = set(columns) - MUTABLE_COLUMNS
    if unknown:
        raise ValueError(f"library_asks columns {sorted(unknown)} are not updatable")
    names = sorted(columns)
    connection.execute(f"UPDATE library_asks SET {', '.join(f'{name} = ?' for name in names)} WHERE id = ?",
                       (*[columns[name] for name in names], ask_id))


def ask_row(connection: sqlite3.Connection, ask_id: str) -> dict[str, Any] | None:
    row = connection.execute(
        "SELECT id, entry, query_md, extraction_id, anchor_json, personalized, manifest_json, organizer_json, "
        "comparison_id, question_event_id FROM library_asks WHERE id = ?", (ask_id,)).fetchone()
    if row is None:
        return None
    return {"id": row[0], "entry": row[1], "query": row[2], "extraction_id": row[3],
            "anchor": json.loads(row[4] or "{}"), "personalized": bool(row[5]),
            "manifest": json.loads(row[6] or "{}"), "organizer": json.loads(row[7] or "{}"),
            "comparison_id": row[8], "question_event_id": row[9]}


def notes_for_ledger_ids(connection: sqlite3.Connection, ledger_ids: Sequence[str]) -> dict[str, dict[str, Any]]:
    """The validated organizer notes an earlier ask stored for these ledger rows."""

    wanted = {ledger_id for ledger_id in ledger_ids if ledger_id}
    found: dict[str, dict[str, Any]] = {}
    if not wanted:
        return found
    for (text,) in connection.execute(
            "SELECT organizer_json FROM library_asks WHERE organizer_json LIKE ? ORDER BY created_at DESC",
            (f"%{sorted(wanted)[0]}%",)).fetchall():
        for note in json.loads(text or "{}").get("notes") or []:
            ledger_id = str(note.get("ledger_id") or "")
            if ledger_id in wanted and ledger_id not in found:
                found[ledger_id] = note
        if set(found) >= wanted:
            break
    return found


__all__ = ["MUTABLE_COLUMNS", "TABLE", "ask_row", "insert_ask", "notes_for_ledger_ids", "update_ask"]
