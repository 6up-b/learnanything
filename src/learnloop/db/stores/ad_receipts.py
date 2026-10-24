"""Adaptive difficulty AD1's receipts: the only SQL writer of migration 213's tables.

* ``item_serve_inputs`` (RECEIPT, append-only by trigger): the features and
  signals one presentation of a never-attempted item froze at its serve
  (spec_adaptive_difficulty_v1 §7.5).
* ``ad_reading_opportunities`` (RECEIPT, append-only by trigger): reading and
  other learning opportunities per (opportunity, LO), with the D22 verdict
  rows (§5.11). Authority class ``salience_only``; no magnitude column.
* ``item_forecast_payloads`` (WORKFLOW): the raw request and response of a
  paid outside forecaster or of the feature audit's LLM judge (§8.1), pruned
  after ``router.payload_retention_days``.

Callers own the transaction (the serve's, a background job's or a
backfill's). Nothing serving, scoring, scheduling, evidence or certification
reads these rows, and a rebuild neither writes nor clears them.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from collections.abc import Iterable, Mapping
from typing import Any

from learnloop.ids import new_ulid

SERVE_INPUTS = "item_serve_inputs"
READING = "ad_reading_opportunities"
PAYLOADS = "item_forecast_payloads"

SERVE_INPUT_COLUMNS = (
    "id", "receipt_key", "presentation_kind", "plan_presentation_id", "probe_presentation_id",
    "scheduler_candidate_id", "practice_item_id", "learning_object_id", "content_hash", "served_at",
    "stamped_features_json", "task_feature_schema", "audit_json", "resolved_features_json", "signals_json",
    "z_v1_recalibration", "pre_exposed", "resolution_version", "loadings_json", "coupling_version", "created_at",
    "protection_epoch",
)

READING_COLUMNS = (
    "id", "opportunity_key", "kind", "subkind", "source_table", "source_id", "source_written_at",
    "learning_object_id", "facet_doses_json", "dose_offer_id", "mapping_version", "authority_class",
    "sweep", "sweep_ref", "swept_at", "protection_epoch",
)


def _dumps(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)


def _loads(value: Any, default: Any) -> Any:
    if value in (None, ""):
        return default
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return default


def has_table(connection: sqlite3.Connection, table: str) -> bool:
    return connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", (table,)
    ).fetchone() is not None


# -- item_serve_inputs ---------------------------------------------------------------------


def insert_serve_inputs(connection: sqlite3.Connection, row: Mapping[str, Any]) -> str | None:
    """Append one serve-input receipt; None when its receipt key already exists."""

    values = dict(row)
    values.setdefault("id", new_ulid())
    for name in ("stamped_features", "audit", "resolved_features", "signals", "loadings"):
        if name in values:
            payload = values.pop(name)
            values[f"{name}_json"] = None if payload is None else _dumps(payload)
    values["pre_exposed"] = 1 if values.get("pre_exposed") else 0
    unknown = sorted(set(values) - set(SERVE_INPUT_COLUMNS))
    if unknown:
        raise ValueError(f"unknown item_serve_inputs columns: {unknown}")
    cursor = connection.execute(
        f"INSERT OR IGNORE INTO {SERVE_INPUTS} ({', '.join(SERVE_INPUT_COLUMNS)}) "
        f"VALUES ({', '.join('?' for _ in SERVE_INPUT_COLUMNS)})",
        tuple(values.get(column) for column in SERVE_INPUT_COLUMNS),
    )
    return str(values["id"]) if cursor.rowcount > 0 else None


def _decode_serve_inputs(row: sqlite3.Row) -> dict[str, Any]:
    payload = dict(row)
    for name, default in (("stamped_features", None), ("audit", {}), ("resolved_features", None),
                          ("signals", {}), ("loadings", None)):
        payload[name] = _loads(payload.pop(f"{name}_json"), default)
    payload["pre_exposed"] = bool(payload["pre_exposed"])
    return payload


def serve_inputs(connection: sqlite3.Connection, *, practice_item_id: str | None = None) -> list[dict[str, Any]]:
    """Every serve-input receipt (decoded), oldest first; ``[]`` without the table."""

    if not has_table(connection, SERVE_INPUTS):
        return []
    where, parameters = ("", ()) if practice_item_id is None else (" WHERE practice_item_id = ?", (practice_item_id,))
    rows = connection.execute(
        f"SELECT * FROM {SERVE_INPUTS}{where} ORDER BY served_at, id", parameters
    ).fetchall()
    return [_decode_serve_inputs(row) for row in rows]


# -- ad_reading_opportunities --------------------------------------------------------------


def reading_opportunity_exists(connection: sqlite3.Connection, *, opportunity_key: str | None = None,
                               identity: tuple[str, str, str, str, str] | None = None) -> bool:
    if opportunity_key is not None and connection.execute(
        f"SELECT 1 FROM {READING} WHERE opportunity_key = ?", (opportunity_key,)
    ).fetchone() is not None:
        return True
    if identity is not None and connection.execute(
        f"SELECT 1 FROM {READING} WHERE kind = ? AND subkind = ? AND source_table = ? AND source_id = ? "
        "AND learning_object_id = ?", identity,
    ).fetchone() is not None:
        return True
    return False


def source_recorded(connection: sqlite3.Connection, *, kind: str, subkind: str, source_table: str,
                    source_id: str) -> bool:
    """Whether an earlier sweep already recorded this source row (for any LO)."""

    return connection.execute(
        f"SELECT 1 FROM {READING} WHERE kind = ? AND subkind = ? AND source_table = ? AND source_id = ? LIMIT 1",
        (kind, subkind, source_table, source_id),
    ).fetchone() is not None


def insert_reading_opportunity(connection: sqlite3.Connection, row: Mapping[str, Any]) -> str | None:
    """Append one opportunity; None when its key or its (kind, source, LO) exists."""

    values = dict(row)
    values.setdefault("id", new_ulid())
    values.setdefault("authority_class", "salience_only")
    # A receipt with no protection epoch is never in force ('' keeps its identity unique).
    values["protection_epoch"] = values.get("protection_epoch") or ""
    if "facet_doses" in values:
        values["facet_doses_json"] = _dumps(values.pop("facet_doses"))
    unknown = sorted(set(values) - set(READING_COLUMNS))
    if unknown:
        raise ValueError(f"unknown ad_reading_opportunities columns: {unknown}")
    cursor = connection.execute(
        f"INSERT OR IGNORE INTO {READING} ({', '.join(READING_COLUMNS)}) "
        f"VALUES ({', '.join('?' for _ in READING_COLUMNS)})",
        tuple(values.get(column) for column in READING_COLUMNS),
    )
    return str(values["id"]) if cursor.rowcount > 0 else None


def reading_opportunities(connection: sqlite3.Connection) -> list[dict[str, Any]]:
    """Every opportunity (decoded), in replay order: by source write time."""

    if not has_table(connection, READING):
        return []
    rows = connection.execute(f"SELECT * FROM {READING} ORDER BY source_written_at, id").fetchall()
    result = []
    for row in rows:
        payload = dict(row)
        payload["facet_doses"] = _loads(payload.pop("facet_doses_json"), {})
        result.append(payload)
    return result


def latest_source_written_at(connection: sqlite3.Connection) -> str | None:
    if not has_table(connection, READING):
        return None
    row = connection.execute(f"SELECT MAX(source_written_at) FROM {READING}").fetchone()
    return str(row[0]) if row is not None and row[0] is not None else None


def insert_item_snapshot(connection: sqlite3.Connection, *, content_hash_value: str, practice_item_id: str,
                         item_json: str, created_at: str) -> None:
    """The served revision in ``practice_item_snapshots`` (migration 164), once per hash."""

    connection.execute(
        "INSERT OR IGNORE INTO practice_item_snapshots(content_hash, practice_item_id, item_json, created_at) "
        "VALUES (?, ?, ?, ?)",
        (content_hash_value, practice_item_id, item_json, created_at),
    )


# -- item_forecast_payloads ----------------------------------------------------------------


def content_hash(content: Any) -> str:
    return hashlib.sha256(_dumps(content).encode("utf-8")).hexdigest()


def insert_payload(connection: sqlite3.Connection, *, owner_key: str, forecaster: str, kind: str,
                   content: Any, created_at: str) -> str | None:
    """Store one raw request or response (once per owner and kind)."""

    payload_id = new_ulid()
    cursor = connection.execute(
        f"INSERT OR IGNORE INTO {PAYLOADS}(id, owner_key, forecaster, kind, content_hash, content_json, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (payload_id, owner_key, forecaster, kind, content_hash(content), _dumps(content), created_at),
    )
    return payload_id if cursor.rowcount > 0 else None


def prune_payloads(connection: sqlite3.Connection, *, before: str) -> int:
    """Delete payloads stored before ``before`` (``router.payload_retention_days``)."""

    if not has_table(connection, PAYLOADS):
        return 0
    cursor = connection.execute(f"DELETE FROM {PAYLOADS} WHERE created_at < ?", (before,))
    return int(cursor.rowcount or 0)


def payloads(connection: sqlite3.Connection, owner_keys: Iterable[str] | None = None) -> list[dict[str, Any]]:
    if not has_table(connection, PAYLOADS):
        return []
    rows = connection.execute(f"SELECT * FROM {PAYLOADS} ORDER BY created_at, id").fetchall()
    wanted = None if owner_keys is None else set(owner_keys)
    result = []
    for row in rows:
        if wanted is not None and row["owner_key"] not in wanted:
            continue
        payload = dict(row)
        payload["content"] = _loads(payload.pop("content_json"), None)
        result.append(payload)
    return result


__all__ = [
    "PAYLOADS",
    "READING",
    "SERVE_INPUTS",
    "content_hash",
    "has_table",
    "insert_item_snapshot",
    "insert_payload",
    "insert_reading_opportunity",
    "insert_serve_inputs",
    "latest_source_written_at",
    "payloads",
    "prune_payloads",
    "reading_opportunities",
    "reading_opportunity_exists",
    "serve_inputs",
    "source_recorded",
]
