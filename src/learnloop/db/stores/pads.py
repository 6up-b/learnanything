"""The only SQL writer for the workbench's scratchpads (migration 262): ``pads`` (WORKFLOW) and the
append-only ``pad_block_versions`` and ``pad_block_anchors`` (RAW_LEDGER, enforced by triggers). Its reads are
``db.stores.pad_reads``. Callers own the transaction.
"""
from __future__ import annotations

import json
import sqlite3
from collections.abc import Mapping
from typing import Any

_PAD_FIELDS = frozenset({"title", "kept", "archived_at"})
VERSION_COLUMNS = (
    "version_id", "block_id", "supersedes_id", "pad_id", "position_key", "day", "kind", "body_md", "payload_json",
    "provenance", "tombstone", "client_id", "created_at",
)


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


def insert_version(connection: sqlite3.Connection, row: Mapping[str, Any]) -> None:
    values = dict(row)
    values["payload_json"] = json.dumps(values.pop("payload", None) or {}, sort_keys=True, ensure_ascii=False)
    values["tombstone"] = 1 if values.get("tombstone") else 0
    connection.execute(
        f"INSERT INTO pad_block_versions ({','.join(VERSION_COLUMNS)}) VALUES ({','.join('?' for _ in VERSION_COLUMNS)})",
        tuple(values.get(column) for column in VERSION_COLUMNS),
    )


def insert_anchor_event(connection: sqlite3.Connection, *, event_id: str, block_id: str, extraction_id: str,
                        span_id: str, anchor: Mapping[str, Any], annotation_id: str | None, action: str,
                        now: str) -> None:
    connection.execute(
        "INSERT INTO pad_block_anchors (event_id, block_id, extraction_id, span_id, anchor_json, annotation_id, action, "
        "created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (event_id, block_id, extraction_id, span_id, json.dumps(dict(anchor), sort_keys=True), annotation_id, action,
         now),
    )


__all__ = ["VERSION_COLUMNS", "insert_anchor_event", "insert_pad", "insert_version", "touch_pad", "update_pad"]
