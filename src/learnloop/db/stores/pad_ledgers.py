"""The only SQL writer for the scratchpads' later tables (migration 266): ``pad_block_submissions``,
``carried_question_events`` and ``proposal_labels`` (RAW_LEDGER) and ``pad_proposals`` (RECEIPT), all append-only by
trigger, and ``carried_questions`` (WORKFLOW). Its reads are ``db.stores.pad_reads``. Callers own the transaction.
"""
from __future__ import annotations

import json
import sqlite3
from collections.abc import Mapping
from typing import Any


def insert_submission(connection: sqlite3.Connection, row: Mapping[str, Any]) -> None:
    connection.execute(
        "INSERT INTO pad_block_submissions (submission_id, block_id, version_id, pad_id, submitted_as, "
        "practice_item_id, session_id, attempt_id, teach_back_id, request_hash, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (row["submission_id"], row["block_id"], row["version_id"], row["pad_id"], row["submitted_as"],
         row["practice_item_id"], row["session_id"], row.get("attempt_id"), row.get("teach_back_id"),
         row["request_hash"], row["created_at"]),
    )


def insert_carried(connection: sqlite3.Connection, row: Mapping[str, Any]) -> None:
    anchor = row.get("anchor")
    connection.execute(
        "INSERT INTO carried_questions (carried_id, text, origin_kind, origin_ref, anchor_json, desk_id, since, state, "
        "version, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, 'carried', 1, ?)",
        (row["carried_id"], row["text"], row["origin_kind"], row.get("origin_ref"),
         json.dumps(dict(anchor), sort_keys=True) if anchor is not None else None, row.get("desk_id"), row["since"],
         row["since"]),
    )


def set_carried_state(connection: sqlite3.Connection, carried_id: str, state: str, now: str) -> int:
    """Set a carried question's latest label and count it in its version; returns the new version."""

    connection.execute("UPDATE carried_questions SET state = ?, version = version + 1, updated_at = ? "
                       "WHERE carried_id = ?", (state, now, carried_id))
    return int(connection.execute("SELECT version FROM carried_questions WHERE carried_id = ?",
                                  (carried_id,)).fetchone()[0])


def insert_carried_event(connection: sqlite3.Connection, *, event_id: str, carried_id: str, event: str,
                         ref: str | None, at: str) -> None:
    connection.execute("INSERT INTO carried_question_events (event_id, carried_id, event, ref, at) "
                       "VALUES (?, ?, ?, ?, ?)", (event_id, carried_id, event, ref, at))


def insert_proposal(connection: sqlite3.Connection, row: Mapping[str, Any]) -> None:
    connection.execute(
        "INSERT INTO pad_proposals (proposal_id, block_version_id, block_id, pad_id, found_by, target_spec_json, "
        "reason_md, quote, judgment_ref, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (row["proposal_id"], row["block_version_id"], row["block_id"], row["pad_id"], row["found_by"],
         json.dumps(dict(row["target_spec"]), sort_keys=True), row["reason_md"], row.get("quote") or "",
         row.get("judgment_ref"), row["created_at"]),
    )


def insert_label(connection: sqlite3.Connection, *, label_id: str, proposal_kind: str, proposal_id: str, label: str,
                 at: str) -> None:
    connection.execute("INSERT INTO proposal_labels (label_id, proposal_kind, proposal_id, label, at) "
                       "VALUES (?, ?, ?, ?, ?)", (label_id, proposal_kind, proposal_id, label, at))


__all__ = [
    "insert_carried", "insert_carried_event", "insert_label", "insert_proposal", "insert_submission",
    "set_carried_state",
]
