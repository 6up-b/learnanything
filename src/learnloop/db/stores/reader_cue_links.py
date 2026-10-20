"""Reader workbench RW3b: ``passage_links`` and ``reader_cue_impressions`` (migration 215).

Plain SQL over a caller's connection; the caller owns the transaction. The
writers are :mod:`learnloop.source_retrieval.passage_cues` (links: the cue
judge's picks, paid outputs never re-run on rebuild) and the sidecar's cue
impressions RPC (receipts). Both tables are append-only by trigger; an
impression's first response is written once. Replay never reads either.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
import json
import sqlite3
from typing import Any

LINK_COLUMNS = ("id", "extraction_id", "span_id", "target_kind", "target_id", "relation", "quote", "pick_rank",
                "ranks_json", "roles_json", "ledger_id", "state_key", "model", "prompt_version", "created_at")
IMPRESSION_COLUMNS = ("id", "cue_id", "link_id", "extraction_id", "span_id", "learning_object_id", "kind", "visit_id",
                      "shown",
                      "suppressed_reason", "propensity", "seed", "p_open", "p_open_source", "density", "response",
                      "response_text_hash", "created_at", "responded_at")


def tables_present(connection: sqlite3.Connection) -> bool:
    found = {row[0] for row in connection.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name IN ('passage_links', 'reader_cue_impressions')")}
    return found == {"passage_links", "reader_cue_impressions"}


def _link(row: Any) -> dict[str, Any]:
    value = dict(zip(LINK_COLUMNS, row))
    value["ranks"] = json.loads(value.pop("ranks_json") or "{}")
    value["roles"] = json.loads(value.pop("roles_json") or "[]")
    return value


def insert_link(connection: sqlite3.Connection, row: Mapping[str, Any]) -> str:
    """Insert one pick; an identical (extraction, target, state, span) row
    already there is kept (the same paid answer recorded twice) and its id
    returned."""

    connection.execute(
        "INSERT OR IGNORE INTO passage_links (id, extraction_id, span_id, target_kind, target_id, relation, quote, "
        "pick_rank, ranks_json, roles_json, ledger_id, state_key, model, prompt_version, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (row["id"], row["extraction_id"], row["span_id"], row["target_kind"], row["target_id"], row["relation"],
         row["quote"], int(row["pick_rank"]), json.dumps(dict(row.get("ranks") or {}), sort_keys=True),
         json.dumps(list(row.get("roles") or [])), row["ledger_id"], row["state_key"], row["model"],
         row["prompt_version"], row["created_at"]),
    )
    found = connection.execute(
        "SELECT id FROM passage_links WHERE extraction_id = ? AND target_kind = ? AND target_id = ? "
        "AND state_key = ? AND span_id = ?",
        (row["extraction_id"], row["target_kind"], row["target_id"], row["state_key"], row["span_id"]),
    ).fetchone()
    return str(found[0])


def links_for_extraction(connection: sqlite3.Connection, extraction_id: str,
                         state_keys: Iterable[str] | None = None) -> list[dict[str, Any]]:
    """The links on one extraction, optionally only those of these target states."""

    sql = f"SELECT {', '.join(LINK_COLUMNS)} FROM passage_links WHERE extraction_id = ?"
    params: list[Any] = [extraction_id]
    if state_keys is not None:
        wanted = sorted(set(state_keys))
        if not wanted:
            return []
        sql += f" AND state_key IN ({','.join('?' for _ in wanted)})"
        params.extend(wanted)
    rows = connection.execute(sql + " ORDER BY target_kind, target_id, pick_rank, span_id", params).fetchall()
    return [_link(row) for row in rows]


def link_by_id(connection: sqlite3.Connection, link_id: str) -> dict[str, Any] | None:
    row = connection.execute(f"SELECT {', '.join(LINK_COLUMNS)} FROM passage_links WHERE id = ?",
                             (link_id,)).fetchone()
    return _link(row) if row is not None else None


def links_with_roles(connection: sqlite3.Connection, extraction_ids: Iterable[str],
                     roles: Iterable[str]) -> set[tuple[str, str]]:
    """Spans RW3b's own judge proposed one of ``roles`` for (positive use only)."""

    wanted = {str(role) for role in roles}
    extractions = sorted({str(value) for value in extraction_ids})
    if not wanted or not extractions:
        return set()
    rows = connection.execute(
        f"SELECT extraction_id, span_id, roles_json FROM passage_links WHERE extraction_id IN "
        f"({','.join('?' for _ in extractions)})", extractions).fetchall()
    found: set[tuple[str, str]] = set()
    for extraction_id, span_id, roles_json in rows:
        if wanted & {str(entry.get("role") if isinstance(entry, dict) else entry)
                     for entry in json.loads(roles_json or "[]")}:
            found.add((str(extraction_id), str(span_id)))
    return found


def judged_left_ids(connection: sqlite3.Connection, task: str, left_kind: str,
                    left_ids: Iterable[str]) -> set[str]:
    """Which target states the cue judge already judged (a verdict row exists,
    picks or not), so a source open never pays for them twice."""

    wanted = sorted(set(left_ids))
    if not wanted:
        return set()
    rows = connection.execute(
        f"SELECT DISTINCT left_id FROM judgment_ledger WHERE task = ? AND left_kind = ? AND judge = 'llm' "
        f"AND left_id IN ({','.join('?' for _ in wanted)})", (task, left_kind, *wanted)).fetchall()
    return {str(row[0]) for row in rows}


def _impression(row: Any) -> dict[str, Any]:
    value = dict(zip(IMPRESSION_COLUMNS, row))
    value["shown"] = bool(value["shown"])
    return value


def insert_impression(connection: sqlite3.Connection, row: Mapping[str, Any]) -> tuple[dict[str, Any], bool]:
    """Record one (visit, cue) impression; the first one of a visit stands.
    Returns the stored row and whether this call wrote it."""

    cursor = connection.execute(
        "INSERT OR IGNORE INTO reader_cue_impressions (id, cue_id, link_id, extraction_id, span_id, learning_object_id, "
        "kind, visit_id, shown, suppressed_reason, propensity, seed, p_open, p_open_source, density, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (row["id"], row["cue_id"], row.get("link_id"), row["extraction_id"], row["span_id"],
         row.get("learning_object_id") or None, row["kind"],
         row["visit_id"], int(bool(row["shown"])), row.get("suppressed_reason"), row.get("propensity"),
         row.get("seed"), row.get("p_open"), row.get("p_open_source"), row["density"], row["created_at"]),
    )
    stored = impression_for(connection, str(row["visit_id"]), str(row["cue_id"]))
    assert stored is not None
    return stored, cursor.rowcount == 1


def impression_for(connection: sqlite3.Connection, visit_id: str, cue_id: str) -> dict[str, Any] | None:
    row = connection.execute(
        f"SELECT {', '.join(IMPRESSION_COLUMNS)} FROM reader_cue_impressions WHERE visit_id = ? AND cue_id = ?",
        (visit_id, cue_id)).fetchone()
    return _impression(row) if row is not None else None


def record_response(connection: sqlite3.Connection, impression_id: str, *, response: str,
                    text_hash: str | None, at: str) -> bool:
    """Write the learner's first response; a later one changes nothing."""

    cursor = connection.execute(
        "UPDATE reader_cue_impressions SET response = ?, response_text_hash = ?, responded_at = ? "
        "WHERE id = ? AND response = 'none'", (response, text_hash, at, impression_id))
    return cursor.rowcount == 1


def impressions(connection: sqlite3.Connection, *, since: str | None = None) -> list[dict[str, Any]]:
    if connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='reader_cue_impressions'").fetchone() is None:
        return []
    sql = f"SELECT {', '.join(IMPRESSION_COLUMNS)} FROM reader_cue_impressions"
    params: tuple[Any, ...] = ()
    if since is not None:
        sql += " WHERE created_at >= ?"
        params = (since,)
    return [_impression(row) for row in connection.execute(sql + " ORDER BY created_at, id", params).fetchall()]


__all__ = [
    "IMPRESSION_COLUMNS",
    "LINK_COLUMNS",
    "impression_for",
    "impressions",
    "insert_impression",
    "insert_link",
    "judged_left_ids",
    "link_by_id",
    "links_for_extraction",
    "links_with_roles",
    "record_response",
    "tables_present",
]
