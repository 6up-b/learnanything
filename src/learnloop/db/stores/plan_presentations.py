"""The only SQL writer for router R2a's ``plan_presentations`` (migration 205).

One append-only row per plan item served, written in the same transaction as
the plan's ``item_served`` event: the exact receipt between a block's router
decision and the attempt that answers what it served
(``practice_attempts.plan_presentation_id``). Callers own the transaction.
Nothing here is evidence: replay reads the rows and never re-decides.
"""
from __future__ import annotations

from collections.abc import Iterable, Mapping
import sqlite3
from typing import Any

PRESENTATION_COLUMNS: tuple[str, ...] = (
    "id", "block_id", "router_decision_id", "controller_decision_id", "practice_item_id",
    "position", "origin", "scheduler_candidate_id", "probe_presentation_id", "session_id", "served_at",
)


def plan_presentations_present(connection: sqlite3.Connection) -> bool:
    """Whether the database has the table (a vault below migration 205 has not)."""

    return connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'plan_presentations'"
    ).fetchone() is not None


def presentation_for(connection: sqlite3.Connection, block_id: str, practice_item_id: str) -> dict[str, Any] | None:
    row = connection.execute(
        "SELECT * FROM plan_presentations WHERE block_id = ? AND practice_item_id = ?",
        (block_id, practice_item_id),
    ).fetchone()
    return dict(row) if row is not None else None


def insert_plan_presentation(connection: sqlite3.Connection, row: Mapping[str, Any]) -> str:
    """Append one presentation, or return the standing one for its block and item.

    A plan item is served once per block (a reopen serves the same step), so
    ``(block_id, practice_item_id)`` names its presentation; a second serve
    returns the first row's id and writes nothing.
    """

    standing = presentation_for(connection, str(row["block_id"]), str(row["practice_item_id"]))
    if standing is not None:
        return str(standing["id"])
    connection.execute(
        f"INSERT INTO plan_presentations ({','.join(PRESENTATION_COLUMNS)}) "
        f"VALUES ({','.join('?' for _ in PRESENTATION_COLUMNS)})",
        tuple(row.get(column) for column in PRESENTATION_COLUMNS),
    )
    return str(row["id"])


def presentation_by_id(connection: sqlite3.Connection, presentation_id: str) -> dict[str, Any] | None:
    row = connection.execute("SELECT * FROM plan_presentations WHERE id = ?", (presentation_id,)).fetchone()
    return dict(row) if row is not None else None


def bindable_presentation(
    connection: sqlite3.Connection,
    presentation_id: str | None,
    *,
    practice_item_id: str,
    attempt_id: str | None = None,
) -> tuple[str | None, str | None]:
    """``(presentation id, None)`` when an attempt on ``practice_item_id`` may
    bind to it, else ``(None, why)``: unknown, another item's, or already
    answered by another attempt (``attempt_id``'s own row, a retried write,
    does not count). Never raises for a bad id (a submit never fails because
    its receipt cannot bind)."""

    if not presentation_id:
        return None, None
    if not plan_presentations_present(connection):
        return None, "no_presentation_ledger"
    row = presentation_by_id(connection, presentation_id)
    if row is None:
        return None, "unknown_presentation"
    if str(row["practice_item_id"]) != str(practice_item_id):
        return None, "presentation_of_another_item"
    taken = connection.execute(
        "SELECT 1 FROM practice_attempts WHERE plan_presentation_id = ? AND id IS NOT ? LIMIT 1",
        (presentation_id, attempt_id),
    ).fetchone()
    if taken is not None:
        return None, "presentation_already_answered"
    return str(presentation_id), None


def presentations_for_blocks(
    connection: sqlite3.Connection, block_ids: Iterable[str]
) -> dict[str, list[dict[str, Any]]]:
    """Each block's presentations in serving order (``served_at``, then id)."""

    ids = sorted({str(block_id) for block_id in block_ids if block_id})
    out: dict[str, list[dict[str, Any]]] = {}
    if not ids or not plan_presentations_present(connection):
        return out
    for start in range(0, len(ids), 500):
        chunk = ids[start:start + 500]
        for row in connection.execute(
            f"SELECT * FROM plan_presentations WHERE block_id IN ({','.join('?' for _ in chunk)}) "
            "ORDER BY served_at, id",
            chunk,
        ):
            out.setdefault(str(row["block_id"]), []).append(dict(row))
    return out


def presentations_for_controller_decision(
    connection: sqlite3.Connection, controller_decision_id: str
) -> list[dict[str, Any]]:
    """Presentations of every block whose router decision named the staged
    controller decision, in serving order (plan §5.3)."""

    if not plan_presentations_present(connection):
        return []
    rows = connection.execute(
        "SELECT p.* FROM plan_presentations p JOIN router_decisions d ON d.id = p.router_decision_id "
        "WHERE d.controller_decision_id = ? ORDER BY p.served_at, p.id",
        (controller_decision_id,),
    ).fetchall()
    return [dict(row) for row in rows]


__all__ = [
    "PRESENTATION_COLUMNS",
    "bindable_presentation",
    "insert_plan_presentation",
    "plan_presentations_present",
    "presentation_by_id",
    "presentation_for",
    "presentations_for_blocks",
    "presentations_for_controller_decision",
]
