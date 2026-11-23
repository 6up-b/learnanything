"""The only SQL writer for the workbench's scratchpads (migration 262): ``pads`` (WORKFLOW) and the
append-only ``pad_block_versions`` and ``pad_block_anchors`` (RAW_LEDGER, enforced by triggers).

A block's head is its one version that no other version supersedes. Callers own the transaction.
"""
from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterable, Mapping
from typing import Any

_PAD_FIELDS = frozenset({"title", "kept", "archived_at"})
VERSION_COLUMNS = (
    "version_id", "block_id", "supersedes_id", "pad_id", "position_key", "day", "kind", "body_md", "payload_json",
    "provenance", "tombstone", "client_id", "created_at",
)
_HEADS = (
    "SELECT v.* FROM pad_block_versions AS v WHERE {where} AND NOT EXISTS "
    "(SELECT 1 FROM pad_block_versions AS c WHERE c.supersedes_id = v.version_id)"
)


def _rows(connection: sqlite3.Connection, sql: str, params: Iterable[Any] = ()) -> list[dict[str, Any]]:
    cursor = connection.execute(sql, tuple(params))
    names = [column[0] for column in cursor.description]
    return [dict(zip(names, row, strict=True)) for row in cursor.fetchall()]


def _decoded(row: dict[str, Any]) -> dict[str, Any]:
    row = dict(row)
    row["payload"] = json.loads(row.pop("payload_json") or "{}")
    row["tombstone"] = bool(row["tombstone"])
    return row


# -- pads ------------------------------------------------------------------------------------------


def pad(connection: sqlite3.Connection, pad_id: str) -> dict[str, Any] | None:
    found = _rows(connection, "SELECT * FROM pads WHERE pad_id = ?", (pad_id,))
    return found[0] if found else None


def insert_pad(connection: sqlite3.Connection, *, pad_id: str, kind: str, title: str, home_desk_id: str | None,
               workbench_session_id: str | None, lesson_id: str | None, now: str) -> None:
    connection.execute(
        "INSERT INTO pads (pad_id, kind, title, kept, home_desk_id, workbench_session_id, lesson_id, version, "
        "created_at, updated_at) VALUES (?, ?, ?, 0, ?, ?, ?, 1, ?, ?)",
        (pad_id, kind, title, home_desk_id, workbench_session_id, lesson_id, now, now),
    )


def update_pad(connection: sqlite3.Connection, pad_id: str, fields: Mapping[str, Any], now: str) -> int:
    """Set ``fields`` on one pad and count the op in its version; returns the new version."""

    unknown = set(fields) - _PAD_FIELDS
    if unknown:  # pragma: no cover - callers pass this module's own names
        raise ValueError(f"not pad fields: {sorted(unknown)}")
    assignments = "".join(f"{name} = ?, " for name in fields)
    connection.execute(f"UPDATE pads SET {assignments}version = version + 1, updated_at = ? WHERE pad_id = ?",
                       (*fields.values(), now, pad_id))
    return int(connection.execute("SELECT version FROM pads WHERE pad_id = ?", (pad_id,)).fetchone()[0])


def touch_pad(connection: sqlite3.Connection, pad_id: str, now: str) -> None:
    """A block of the pad changed: the pad's last-changed time moves, its metadata version does not."""

    connection.execute("UPDATE pads SET updated_at = ? WHERE pad_id = ?", (now, pad_id))


def running_pad_ids(connection: sqlite3.Connection, desk_id: str) -> list[str]:
    return [str(row[0]) for row in connection.execute(
        "SELECT pad_id FROM pads WHERE home_desk_id = ? AND kind = 'running' AND archived_at IS NULL "
        "ORDER BY created_at, pad_id", (desk_id,))]


def list_pads(connection: sqlite3.Connection, *, desk_id: str | None, kept: bool | None, query: str | None,
              after: tuple[str, str] | None, page_size: int) -> list[dict[str, Any]]:
    """Pads, most recently changed first; ``query`` matches the title or a standing block's text."""

    clauses, params = ["p.archived_at IS NULL"], []
    if desk_id is not None:
        clauses.append("p.home_desk_id = ?")
        params.append(desk_id)
    if kept is not None:
        clauses.append("p.kept = ?")
        params.append(1 if kept else 0)
    if query:
        like = "%" + query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
        clauses.append(
            "(p.title LIKE ? ESCAPE '\\' OR EXISTS (" + _HEADS.format(where="v.pad_id = p.pad_id AND v.tombstone = 0")
            + " AND v.body_md LIKE ? ESCAPE '\\'))")
        params.extend([like, like])
    if after is not None:
        clauses.append("(p.updated_at < ? OR (p.updated_at = ? AND p.pad_id > ?))")
        params.extend([after[0], after[0], after[1]])
    sql = f"SELECT p.* FROM pads AS p WHERE {' AND '.join(clauses)} ORDER BY p.updated_at DESC, p.pad_id LIMIT ?"
    return _rows(connection, sql, [*params, page_size])


# -- block versions ----------------------------------------------------------------------------------


def head(connection: sqlite3.Connection, block_id: str) -> dict[str, Any] | None:
    found = _rows(connection, _HEADS.format(where="v.block_id = ?"), (block_id,))
    return _decoded(found[0]) if found else None


def heads(connection: sqlite3.Connection, pad_id: str) -> list[dict[str, Any]]:
    """Every block head of one pad (tombstones included), ordered by position, then block id."""

    rows = _rows(connection, _HEADS.format(where="v.pad_id = ?") + " ORDER BY v.position_key, v.block_id", (pad_id,))
    return [_decoded(row) for row in rows]


def first_versions(connection: sqlite3.Connection, block_ids: Iterable[str]) -> dict[str, str]:
    wanted = sorted(set(block_ids))
    if not wanted:
        return {}
    marks = ",".join("?" for _ in wanted)
    return {str(row[0]): str(row[1]) for row in connection.execute(
        f"SELECT block_id, created_at FROM pad_block_versions WHERE supersedes_id IS NULL AND block_id IN ({marks})",
        wanted)}


def version_exists(connection: sqlite3.Connection, version_id: str) -> bool:
    return connection.execute("SELECT 1 FROM pad_block_versions WHERE version_id = ?", (version_id,)).fetchone() is not None


def insert_version(connection: sqlite3.Connection, row: Mapping[str, Any]) -> None:
    values = dict(row)
    values["payload_json"] = json.dumps(values.pop("payload", None) or {}, sort_keys=True, ensure_ascii=False)
    values["tombstone"] = 1 if values.get("tombstone") else 0
    connection.execute(
        f"INSERT INTO pad_block_versions ({','.join(VERSION_COLUMNS)}) VALUES ({','.join('?' for _ in VERSION_COLUMNS)})",
        tuple(values.get(column) for column in VERSION_COLUMNS),
    )


# -- anchors -----------------------------------------------------------------------------------------


def insert_anchor_event(connection: sqlite3.Connection, *, event_id: str, block_id: str, extraction_id: str,
                        span_id: str, anchor: Mapping[str, Any], annotation_id: str | None, action: str,
                        now: str) -> None:
    connection.execute(
        "INSERT INTO pad_block_anchors (event_id, block_id, extraction_id, span_id, anchor_json, annotation_id, action, "
        "created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (event_id, block_id, extraction_id, span_id, json.dumps(dict(anchor), sort_keys=True), annotation_id, action,
         now),
    )


_STANDING = (
    "SELECT a.* FROM pad_block_anchors AS a WHERE {where} AND a.action = 'link' AND a.rowid = ("
    "SELECT b.rowid FROM pad_block_anchors AS b WHERE b.block_id = a.block_id AND b.extraction_id = a.extraction_id "
    "AND b.span_id = a.span_id ORDER BY b.rowid DESC LIMIT 1)"
)


def standing_anchors_for_blocks(connection: sqlite3.Connection, block_ids: Iterable[str]) -> list[dict[str, Any]]:
    """The links that stand (the latest event per block and passage is a link), in written order."""

    wanted = sorted(set(block_ids))
    if not wanted:
        return []
    marks = ",".join("?" for _ in wanted)
    rows = _rows(connection, _STANDING.format(where=f"a.block_id IN ({marks})") + " ORDER BY a.rowid", wanted)
    return [{**row, "anchor": json.loads(row.pop("anchor_json") or "{}")} for row in rows]


def standing_anchors_for_spans(connection: sqlite3.Connection, extraction_ids: Iterable[str]) -> list[dict[str, Any]]:
    """Every standing link onto the given readings, each with its block's head (pad and kind)."""

    wanted = sorted(set(extraction_ids))
    if not wanted:
        return []
    marks = ",".join("?" for _ in wanted)
    rows = _rows(connection, _STANDING.format(where=f"a.extraction_id IN ({marks})") + " ORDER BY a.rowid", wanted)
    return [{**row, "anchor": json.loads(row.pop("anchor_json") or "{}")} for row in rows]


__all__ = [
    "VERSION_COLUMNS", "first_versions", "head", "heads", "insert_anchor_event", "insert_pad", "insert_version",
    "list_pads", "pad", "running_pad_ids", "standing_anchors_for_blocks", "standing_anchors_for_spans", "touch_pad",
    "update_pad", "version_exists",
]
