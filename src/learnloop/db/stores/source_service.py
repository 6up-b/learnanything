"""SQL for the canonical-sources service (spec_source_practice_and_probes_v1).

Callers own transactions and pass a connection, as with ``practice_index``.
``db`` sits below every domain, so the attempt transaction, the tutor and the
remediation path can record and read here without importing the service
(SC12). Nothing here is evidence; the one DERIVED table (S5's outcome join)
is cleared and rebuilt only by its replayer.
"""
from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
import json
import sqlite3
from typing import Any


def table_exists(connection: sqlite3.Connection, name: str) -> bool:
    return connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,),
    ).fetchone() is not None


def column_exists(connection: sqlite3.Connection, table: str, column: str) -> bool:
    if not table_exists(connection, table):
        return False
    return any(row[1] == column for row in connection.execute(f'PRAGMA table_info("{table}")'))


def _dumps(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, default=str)


def _loads(raw: Any, default: Any = None) -> Any:
    if raw is None or raw == "":
        return default
    try:
        return json.loads(raw)
    except (TypeError, ValueError):
        return default


# -- S0: impressions (migration 184) ----------------------------------------


IMPRESSION_SURFACES = ("tutor_strip", "plan", "dl3_box", "reader", "other")


def insert_impression(connection: sqlite3.Connection, *, id: str, created_at: str, surface: str,
                      caller_kind: str | None, caller_ref: str | None, proposal_id: str,
                      candidate_kind: str, practice_item_id: str | None,
                      extraction_id: str | None, span_ids: Sequence[str],
                      shown_fields: Mapping[str, Any], session_id: str | None) -> None:
    connection.execute(
        "INSERT INTO instructional_impressions (id,created_at,surface,caller_kind,caller_ref,"
        "proposal_id,candidate_kind,practice_item_id,extraction_id,span_ids_json,"
        "shown_fields_json,session_id) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        (id, created_at, surface, caller_kind, caller_ref, proposal_id, candidate_kind,
         practice_item_id, extraction_id, _dumps(list(span_ids)), _dumps(dict(shown_fields)),
         session_id),
    )


def _impression(row: sqlite3.Row) -> dict[str, Any]:
    value = dict(row)
    value["span_ids"] = _loads(value.pop("span_ids_json"), [])
    value["shown_fields"] = _loads(value.pop("shown_fields_json"), {})
    return value


def impressions_for_proposal(connection: sqlite3.Connection, proposal_id: str) -> list[dict[str, Any]]:
    if not table_exists(connection, "instructional_impressions"):
        return []
    return [_impression(row) for row in connection.execute(
        "SELECT * FROM instructional_impressions WHERE proposal_id=? ORDER BY created_at, id",
        (proposal_id,),
    )]


def impressions_of_item(connection: sqlite3.Connection, practice_item_id: str, *,
                        since: str | None = None) -> list[dict[str, Any]]:
    if not table_exists(connection, "instructional_impressions"):
        return []
    sql = "SELECT * FROM instructional_impressions WHERE practice_item_id=?"
    params: list[Any] = [practice_item_id]
    if since is not None:
        sql += " AND created_at >= ?"
        params.append(since)
    return [_impression(row) for row in connection.execute(sql + " ORDER BY created_at, id", params)]


def impressions_of_spans(connection: sqlite3.Connection, extraction_id: str,
                         span_ids: Iterable[str], *, since: str | None = None) -> list[dict[str, Any]]:
    """Impressions of a source exercise whose shown spans overlap ``span_ids``."""

    if not table_exists(connection, "instructional_impressions"):
        return []
    wanted = set(span_ids)
    sql = "SELECT * FROM instructional_impressions WHERE extraction_id=?"
    params: list[Any] = [extraction_id]
    if since is not None:
        sql += " AND created_at >= ?"
        params.append(since)
    rows = [_impression(row) for row in connection.execute(sql + " ORDER BY created_at, id", params)]
    return [row for row in rows if wanted & set(row["span_ids"])]


__all__ = [
    "IMPRESSION_SURFACES",
    "column_exists",
    "impressions_for_proposal",
    "impressions_of_item",
    "impressions_of_spans",
    "insert_impression",
    "table_exists",
]
