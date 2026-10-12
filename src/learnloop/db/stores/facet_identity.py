"""Facet-identity action rows (migration 172) and the facet_merges rows they own.

Lifecycle: ``proposed`` (an ingest action riding on its proposal),
``applying`` (a vault merge's write-ahead intent), ``applied``, ``undoing``
(an undo's write-ahead intent), ``undone``, and ``abandoned`` (an intent
withdrawn before its file write).

Writes only within the caller's transaction (``Repository.atomic``). The
policy (what an action changes in the vault, when undo is legal) lives in
``learnloop.content.facet_identity.actions``.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
import json
import sqlite3
from typing import Any
from uuid import uuid4

ACTION_COLUMNS = (
    "id", "created_at", "origin", "scope", "run_id", "proposal_id", "action",
    "survivor_facet_id", "retired_facet_ids_json", "before_json", "after_json",
    "merge_rows_json", "judgment_ids_json", "judge", "judge_model", "prompt_version",
    "detail_json", "status", "applied_at", "undone_at", "undo_detail_json",
)
_JSON_COLUMNS = {
    "retired_facet_ids_json": "retired_facet_ids",
    "before_json": "before",
    "after_json": "after",
    "merge_rows_json": "merge_rows",
    "judgment_ids_json": "judgment_ids",
    "detail_json": "detail",
    "undo_detail_json": "undo_detail",
}


def _dump(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, default=str)


def _decode(row: Mapping[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for column in ACTION_COLUMNS:
        value = row[column]
        if column in _JSON_COLUMNS:
            out[_JSON_COLUMNS[column]] = json.loads(value) if value else None
        else:
            out[column] = value
    return out


def insert_action(connection: sqlite3.Connection, record: Mapping[str, Any], *, created_at: str) -> str:
    action_id = str(record.get("id") or uuid4().hex)
    values = {
        "id": action_id,
        "created_at": record.get("created_at") or created_at,
        "origin": record["origin"],
        "scope": record["scope"],
        "run_id": record["run_id"],
        "proposal_id": record.get("proposal_id"),
        "action": record["action"],
        "survivor_facet_id": record["survivor_facet_id"],
        "retired_facet_ids_json": _dump(list(record["retired_facet_ids"])),
        "before_json": _dump(record["before"]),
        "after_json": _dump(record["after"]),
        "merge_rows_json": _dump(list(record.get("merge_rows") or [])),
        "judgment_ids_json": _dump(list(record.get("judgment_ids") or [])),
        "judge": record["judge"],
        "judge_model": record.get("judge_model"),
        "prompt_version": record.get("prompt_version"),
        "detail_json": _dump(dict(record.get("detail") or {})),
        "status": record["status"],
        "applied_at": record.get("applied_at"),
        "undone_at": None,
        "undo_detail_json": None,
    }
    connection.execute(
        f"INSERT INTO facet_identity_actions({','.join(ACTION_COLUMNS)}) "
        f"VALUES ({','.join('?' for _ in ACTION_COLUMNS)})",
        tuple(values[column] for column in ACTION_COLUMNS),
    )
    return action_id


def action_by_id(connection: sqlite3.Connection, action_id: str) -> dict[str, Any] | None:
    row = connection.execute("SELECT * FROM facet_identity_actions WHERE id = ?", (action_id,)).fetchone()
    return _decode(row) if row is not None else None


def list_actions(
    connection: sqlite3.Connection, *, run_id: str | None = None, status: str | None = None,
    limit: int | None = 200,
) -> list[dict[str, Any]]:
    clauses: list[str] = []
    params: list[Any] = []
    if run_id is not None:
        clauses.append("run_id = ?")
        params.append(run_id)
    if status is not None:
        clauses.append("status = ?")
        params.append(status)
    query = "SELECT * FROM facet_identity_actions"
    if clauses:
        query += " WHERE " + " AND ".join(clauses)
    query += " ORDER BY created_at DESC, rowid DESC"
    if limit is not None:
        query += " LIMIT ?"
        params.append(int(limit))
    return [_decode(row) for row in connection.execute(query, params).fetchall()]


def set_status(
    connection: sqlite3.Connection,
    action_id: str,
    status: str,
    *,
    applied_at: str | None = None,
    undone_at: str | None = None,
    undo_detail: Mapping[str, Any] | None = None,
) -> None:
    """Move an action along its lifecycle (applying -> applied -> undoing -> undone)."""

    assignments = ["status = ?"]
    params: list[Any] = [status]
    if applied_at is not None:
        assignments.append("applied_at = ?")
        params.append(applied_at)
    if undone_at is not None:
        assignments.append("undone_at = ?")
        params.append(undone_at)
    if undo_detail is not None:
        assignments.append("undo_detail_json = ?")
        params.append(_dump(dict(undo_detail)))
    params.append(action_id)
    connection.execute(f"UPDATE facet_identity_actions SET {', '.join(assignments)} WHERE id = ?", params)


def graded_contract_version_ids(connection: sqlite3.Connection) -> list[str]:
    """Every assessment contract version a live grading row was written against.

    Their criteria are frozen: the canonical projection replays an attempt
    from its contract, never from the item as it loads today (review F1).
    """

    rows = connection.execute(
        """
        SELECT DISTINCT assessment_contract_version_id FROM grading_evidence
         WHERE superseded_at IS NULL
           AND assessment_contract_version_id IS NOT NULL
           AND assessment_contract_version_id != ''
        """
    ).fetchall()
    return sorted(str(row[0]) for row in rows)


def delete_merge_rows(connection: sqlite3.Connection, rows: Iterable[Sequence[str]]) -> int:
    """Remove exactly the ``facet_merges`` rows an action inserted (its undo)."""

    deleted = 0
    for retired, survivor in rows:
        cursor = connection.execute(
            "DELETE FROM facet_merges WHERE retired_facet_id = ? AND surviving_facet_id = ?", (retired, survivor),
        )
        deleted += cursor.rowcount or 0
    return deleted


__all__ = [
    "ACTION_COLUMNS",
    "action_by_id",
    "delete_merge_rows",
    "graded_contract_version_ids",
    "insert_action",
    "list_actions",
    "set_status",
]
