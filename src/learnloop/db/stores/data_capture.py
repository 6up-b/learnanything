"""Data capture's append-only records (migration 239). No policy here.

Every writer runs on the caller's connection, inside its transaction, and a
refused row rolls back alone (a savepoint) with a warning: a receipt never blocks
the learner's plan, as :func:`learnloop.db.stores.router.append_router_decision`.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
import json
import logging
import sqlite3
from typing import Any
import zlib

from learnloop.ids import new_ulid

logger = logging.getLogger(__name__)

RECEIPT_TABLES: tuple[str, ...] = ("prefilter_payloads", "prefilter_receipts")
OBJECTIVE_TABLES: tuple[str, ...] = ("decision_objectives", "decision_measurement_events")
#: Reader activity frozen for the delayed-completion definition, whatever AD's forecast logging says.
READING_EXPOSURES = "reading_exposure_receipts"
#: The frozen reading receipts: data capture's own, and adaptive difficulty's where its logging is on.
READING_RECEIPT_TABLES: tuple[str, ...] = (READING_EXPOSURES, "ad_reading_opportunities")

RECEIPT_COLUMNS: tuple[str, ...] = (
    "id", "decision_id", "decision_kind", "surface", "receipt_version", "algorithm_version", "code_revision",
    "config_hash", "versions_json", "session_present", "scheduler_trace", "considered_count", "admitted_count",
    "refused_count", "gates_hash", "classification_hash", "upstream_hash", "inputs_hash", "config_payload_hash",
    "created_at",
)
OBJECTIVE_COLUMNS: tuple[str, ...] = (
    "decision_id", "decision_kind", "objective_version", "learning_object_id", "source", "scope_json", "arm",
    "support_json", "measurement", "commitment_id", "practice_item_id", "pick_json", "experiment_id", "created_at",
)
#: A measurement's states (A2): treatment-dependent censoring stays visible.
MEASUREMENT_STATES: tuple[str, ...] = ("due", "offered", "answered", "unavailable")


def _present(connection: sqlite3.Connection, tables: Iterable[str]) -> bool:
    wanted = list(tables)
    found = connection.execute(
        f"SELECT COUNT(*) FROM sqlite_master WHERE type = 'table' AND name IN ({','.join('?' for _ in wanted)})",
        wanted,
    ).fetchone()[0]
    return int(found) == len(wanted)


def receipts_present(connection: sqlite3.Connection) -> bool:
    return _present(connection, RECEIPT_TABLES)


def objectives_present(connection: sqlite3.Connection) -> bool:
    return _present(connection, OBJECTIVE_TABLES)


def insert_prefilter_receipt(
    connection: sqlite3.Connection,
    row: Mapping[str, Any],
    parts: Mapping[str, tuple[str, str]],
) -> bool:
    """One decision's receipt and any part not stored yet, or False (a warning) when refused.

    ``parts`` maps each hash to ``(part, content_json)``. A part already stored
    (the same content under the same hash) is referenced, never copied."""

    connection.execute("SAVEPOINT prefilter_receipt_append")
    try:
        for content_hash, (part, content) in parts.items():
            raw = content.encode("utf-8")
            packed = zlib.compress(raw)
            connection.execute(
                "INSERT OR IGNORE INTO prefilter_payloads(content_hash, part, content_z, raw_bytes, stored_bytes, first_seen_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (content_hash, part, packed, len(raw), len(packed), row["created_at"]),
            )
        cursor = connection.execute(
            f"INSERT OR IGNORE INTO prefilter_receipts ({','.join(RECEIPT_COLUMNS)}) "
            f"VALUES ({','.join('?' for _ in RECEIPT_COLUMNS)})",
            [row[column] for column in RECEIPT_COLUMNS],
        )
    except sqlite3.Error:
        connection.execute("ROLLBACK TO prefilter_receipt_append")
        connection.execute("RELEASE prefilter_receipt_append")
        logger.warning("data capture: the prefilter receipt of %s was refused", row.get("decision_id"), exc_info=True)
        return False
    connection.execute("RELEASE prefilter_receipt_append")
    return cursor.rowcount > 0


def prefilter_receipt(connection: sqlite3.Connection, decision_id: str) -> dict[str, Any] | None:
    row = connection.execute("SELECT * FROM prefilter_receipts WHERE decision_id = ?", (decision_id,)).fetchone()
    return dict(row) if row is not None else None


def prefilter_part(connection: sqlite3.Connection, content_hash: str) -> Any:
    row = connection.execute(
        "SELECT content_z FROM prefilter_payloads WHERE content_hash = ?", (content_hash,)
    ).fetchone()
    return json.loads(zlib.decompress(row[0]).decode("utf-8")) if row is not None else None


def insert_objective(connection: sqlite3.Connection, row: Mapping[str, Any]) -> bool:
    """One decision's frozen objective, or False (a warning) when refused."""

    connection.execute("SAVEPOINT decision_objective_append")
    try:
        cursor = connection.execute(
            f"INSERT OR IGNORE INTO decision_objectives ({','.join(OBJECTIVE_COLUMNS)}) "
            f"VALUES ({','.join('?' for _ in OBJECTIVE_COLUMNS)})",
            [row.get(column) for column in OBJECTIVE_COLUMNS],
        )
    except sqlite3.Error:
        connection.execute("ROLLBACK TO decision_objective_append")
        connection.execute("RELEASE decision_objective_append")
        logger.warning("data capture: the objective of %s was refused", row.get("decision_id"), exc_info=True)
        return False
    connection.execute("RELEASE decision_objective_append")
    return cursor.rowcount > 0


def insert_measurement_event(
    connection: sqlite3.Connection,
    *,
    decision_id: str,
    state: str,
    reason: str = "",
    practice_item_id: str | None = None,
    attempt_id: str | None = None,
    detail: Mapping[str, Any] | None = None,
    at: str,
    episode: str = "",
) -> bool:
    """A measurement's state, once per reason and episode: a repeat is a no-op (returns False)."""

    cursor = connection.execute(
        "INSERT OR IGNORE INTO decision_measurement_events"
        "(id, decision_id, state, reason, practice_item_id, attempt_id, detail_json, created_at, episode) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (new_ulid(), decision_id, state, reason, practice_item_id, attempt_id,
         json.dumps(dict(detail or {}), sort_keys=True, separators=(",", ":")), at, episode),
    )
    return cursor.rowcount > 0


def latest_episode(connection: sqlite3.Connection, decision_id: str, *, reason: str) -> str:
    """The episode the newest ``due`` or ``offered`` state of this check opened: a loss is counted once per it."""

    row = connection.execute(
        "SELECT episode FROM decision_measurement_events WHERE decision_id = ? AND reason = ? "
        "AND state IN ('due', 'offered') ORDER BY created_at DESC, id DESC LIMIT 1", (decision_id, reason)).fetchone()
    return str(row[0]) if row is not None else ""


def reading_exposures_present(connection: sqlite3.Connection) -> bool:
    return _present(connection, (READING_EXPOSURES,))


def reading_receipts(connection: sqlite3.Connection) -> set[tuple[str, str]]:
    """``(LO, source time)`` of every stored reading receipt, data capture's own and AD's where its logging wrote any."""

    out: set[tuple[str, str]] = set()
    for table in READING_RECEIPT_TABLES:
        if _present(connection, (table,)):
            out.update((str(row[0]), str(row[1])) for row in connection.execute(
                f"SELECT learning_object_id, source_written_at FROM {table} WHERE learning_object_id IS NOT NULL"))
    return out


def reading_exposure_recorded(connection: sqlite3.Connection, where: str, args: Iterable[Any] = ()) -> bool:
    return connection.execute(f"SELECT 1 FROM {READING_EXPOSURES} WHERE {where} LIMIT 1", tuple(args)).fetchone() is not None


def insert_reading_exposure(connection: sqlite3.Connection, *, kind: str, subkind: str, source_table: str, source_id: str,
                            source_written_at: str, learning_object_id: str, mapping_version: str, swept_at: str) -> bool:
    """One reading exposure on one LO, once: a repeat is a no-op (returns False)."""

    cursor = connection.execute(
        f"INSERT OR IGNORE INTO {READING_EXPOSURES}(id, kind, subkind, source_table, source_id, source_written_at, "
        "learning_object_id, mapping_version, swept_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (new_ulid(), kind, subkind, source_table, source_id, source_written_at, learning_object_id, mapping_version, swept_at),
    )
    return cursor.rowcount > 0


def objectives(connection: sqlite3.Connection) -> dict[str, dict[str, Any]]:
    """Every frozen objective by decision id, ``[]`` of absent tables tolerated."""

    if not objectives_present(connection):
        return {}
    return {str(row["decision_id"]): dict(row) for row in connection.execute("SELECT * FROM decision_objectives")}


def measurement_events(connection: sqlite3.Connection) -> dict[str, list[dict[str, Any]]]:
    if not objectives_present(connection):
        return {}
    out: dict[str, list[dict[str, Any]]] = {}
    for row in connection.execute("SELECT * FROM decision_measurement_events ORDER BY created_at, id"):
        out.setdefault(str(row["decision_id"]), []).append(dict(row))
    return out


__all__ = [
    "READING_EXPOSURES",
    "MEASUREMENT_STATES",
    "OBJECTIVE_COLUMNS",
    "RECEIPT_COLUMNS",
    "insert_measurement_event",
    "insert_reading_exposure",
    "latest_episode",
    "READING_RECEIPT_TABLES",
    "reading_exposure_recorded",
    "reading_receipts",
    "reading_exposures_present",
    "insert_objective",
    "insert_prefilter_receipt",
    "measurement_events",
    "objectives",
    "objectives_present",
    "prefilter_part",
    "prefilter_receipt",
    "receipts_present",
]
