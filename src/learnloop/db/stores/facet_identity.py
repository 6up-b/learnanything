"""Facet-identity action rows (migrations 183, 196), Library save intents (197), and facet_merges rows.

Actions: ``merge`` and ``absorb`` (a survivor plus retired facets) and, since
migration 196, ``reword`` (one facet's meaning changed by a proposal apply;
the row keeps the entry it replaced; a ``proposed`` reword is a change held for
the owner's confirm). Lifecycle: ``proposed`` (an ingest action riding on its
proposal, or a reword waiting for the owner's confirm),
``applying`` (a vault merge's write-ahead intent), ``applied``, ``undoing``
(an undo's write-ahead intent), ``undone``, and ``abandoned`` (an intent
withdrawn before its file write).

Library saves (migration 197, ``facet_registry_saves``): the write-ahead
intent of an owner's own edit of facets.yaml that records manual-authority
verdicts, ``applying`` until it lands (``applied``) or is withdrawn
(``abandoned``).

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
    limit: int | None = 200, survivor_facet_id: str | None = None,
) -> list[dict[str, Any]]:
    clauses: list[str] = []
    params: list[Any] = []
    if run_id is not None:
        clauses.append("run_id = ?")
        params.append(run_id)
    if survivor_facet_id is not None:
        clauses.append("survivor_facet_id = ?")
        params.append(survivor_facet_id)
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


def update_action(
    connection: sqlite3.Connection,
    action_id: str,
    *,
    status: str | None = None,
    judge: str | None = None,
    before: Mapping[str, Any] | None = None,
    after: Mapping[str, Any] | None = None,
    detail: Mapping[str, Any] | None = None,
    undo_detail: Mapping[str, Any] | None = None,
) -> None:
    """Rewrite a pending reword confirm as the owner confirms it (proposed -> applying, or back).

    A confirm writes the facet as it is when the owner taps it, so the row's
    ``before``/``after`` become what the write replaces and writes (its undo
    restores exactly that), and its judge becomes the owner.
    """

    values: dict[str, Any] = {
        "status": status, "judge": judge,
        "before_json": _dump(dict(before)) if before is not None else None,
        "after_json": _dump(dict(after)) if after is not None else None,
        "detail_json": _dump(dict(detail)) if detail is not None else None,
        "undo_detail_json": _dump(dict(undo_detail)) if undo_detail is not None else None,
    }
    assignments = [f"{column} = ?" for column, value in values.items() if value is not None]
    if not assignments:
        return
    params = [value for value in values.values() if value is not None]
    connection.execute(
        f"UPDATE facet_identity_actions SET {', '.join(assignments)} WHERE id = ?", (*params, action_id),
    )


# --- Library save intents (migration 197) ----------------------------------------------------

_SAVE_JSON_COLUMNS = {
    "facets_json": "facets",
    "judgment_ids_json": "judgment_ids",
    "action_ids_json": "action_ids",
    "settle_detail_json": "settle_detail",
}


def _decode_save(row: Mapping[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for column in row.keys():
        value = row[column]
        if column in _SAVE_JSON_COLUMNS:
            out[_SAVE_JSON_COLUMNS[column]] = json.loads(value) if value else None
        else:
            out[column] = value
    return out


def insert_registry_save(
    connection: sqlite3.Connection, *, save_id: str, created_at: str, facets: Mapping[str, Any],
    judgment_ids: Mapping[str, str], action_ids: Sequence[str],
) -> str:
    """Record a Library save's write-ahead intent (``applying``)."""

    connection.execute(
        """
        INSERT INTO facet_registry_saves(id, created_at, status, facets_json, judgment_ids_json, action_ids_json)
        VALUES (?, ?, 'applying', ?, ?, ?)
        """,
        (save_id, created_at, _dump(dict(facets)), _dump(dict(judgment_ids)), _dump(list(action_ids))),
    )
    return save_id


def registry_save_by_id(connection: sqlite3.Connection, save_id: str) -> dict[str, Any] | None:
    row = connection.execute("SELECT * FROM facet_registry_saves WHERE id = ?", (save_id,)).fetchone()
    return _decode_save(row) if row is not None else None


def registry_saves(connection: sqlite3.Connection, *, status: str) -> list[dict[str, Any]]:
    """Library saves in ``status``, oldest first (none before migration 197)."""

    if connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'facet_registry_saves'"
    ).fetchone() is None:
        return []
    rows = connection.execute(
        "SELECT * FROM facet_registry_saves WHERE status = ? ORDER BY created_at, rowid", (status,),
    ).fetchall()
    return [_decode_save(row) for row in rows]


def settle_registry_save(
    connection: sqlite3.Connection, save_id: str, status: str, *, at: str,
    settle_detail: Mapping[str, Any] | None = None,
) -> None:
    """Move an ``applying`` save to ``applied`` or ``abandoned`` (a settled save stays as it is)."""

    column = {"applied": "applied_at", "abandoned": "abandoned_at"}[status]
    connection.execute(
        f"UPDATE facet_registry_saves SET status = ?, {column} = ?, settle_detail_json = ? "
        "WHERE id = ? AND status = 'applying'",
        (status, at, _dump(dict(settle_detail)) if settle_detail is not None else None, save_id),
    )


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


def settled_merge_rows(connection: sqlite3.Connection) -> list[tuple[str, str]]:
    """``facet_merges`` rows, minus those of a facet-identity action still in flight.

    A vault merge commits its ``facet_merges`` rows (``applying``) before it
    writes ``facets.yaml``, and an undo (``undoing``) restores the file before
    it deletes them. Until the action settles, facets.yaml is the authority:
    its aliases already resolve a written merge, and a facet it still lists
    keeps its own evidence (review F12). A database without the actions table
    (before migration 183) has no such rows.
    """

    has_actions = connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'facet_identity_actions'"
    ).fetchone()
    if has_actions is None:
        rows = connection.execute("SELECT retired_facet_id, surviving_facet_id FROM facet_merges").fetchall()
    else:
        rows = connection.execute(
            """
            SELECT merge.retired_facet_id, merge.surviving_facet_id
              FROM facet_merges AS merge
             WHERE NOT EXISTS (
                   SELECT 1
                     FROM facet_identity_actions AS action, json_each(action.merge_rows_json) AS pair
                    WHERE action.status IN ('applying', 'undoing')
                      AND json_extract(pair.value, '$[0]') = merge.retired_facet_id
                      AND json_extract(pair.value, '$[1]') = merge.surviving_facet_id
             )
            """
        ).fetchall()
    return [(str(row[0]), str(row[1])) for row in rows]


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
    "settled_merge_rows",
    "update_action",
]
