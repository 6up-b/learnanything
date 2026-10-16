"""Saved forecasts: ``forecast_receipts`` persistence (append-only, migration 206).

The only writer is :func:`learnloop.scheduling.forecast_receipts.record_receipts`,
always inside the caller's (the deciding) transaction; the only reader is the
calibration report (``learnloop diagnosis calibration``). Nothing serving,
scoring or scheduling reads it, and a rebuild neither writes nor clears it.
The JSON encoding is ``voi_forecasts``' (the receipt family it generalizes).
"""

from __future__ import annotations

import sqlite3
from collections.abc import Mapping
from typing import Any

from learnloop.db.stores.voi_forecasts import _dumps, _loads
from learnloop.ids import new_ulid

TABLE = "forecast_receipts"

COLUMNS = (
    "id", "receipt_key", "kind", "forecaster", "forecaster_version", "scope", "decision_kind",
    "decision_ref", "source_attempt_id", "learning_object_id", "facet_id", "hypothesis_ref",
    "practice_item_id", "item_content_hash", "binding_kind", "plan_presentation_id",
    "probe_presentation_id", "followup_task_id", "scheduler_candidate_id", "censor_reason", "event", "p",
    "forecast_json", "inputs_json", "inputs_hash", "inputs_as_of", "parameters_json",
    "versions_json", "status", "algorithm_version", "created_at", "received_at",
)

#: Columns a caller may set beside the JSON bodies (the rest are derived here).
OPTIONAL_COLUMNS = (
    "decision_ref", "source_attempt_id", "learning_object_id", "facet_id", "hypothesis_ref",
    "practice_item_id", "item_content_hash", "plan_presentation_id", "probe_presentation_id",
    "followup_task_id", "scheduler_candidate_id", "censor_reason", "p", "algorithm_version", "received_at",
)


def has_table(connection: sqlite3.Connection) -> bool:
    return connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", (TABLE,)
    ).fetchone() is not None


def insert_receipt(
    connection: sqlite3.Connection,
    *,
    receipt_key: str,
    kind: str,
    forecaster: str,
    forecaster_version: str,
    scope: str,
    decision_kind: str,
    binding_kind: str,
    event: str,
    forecast: Mapping[str, Any],
    inputs: Mapping[str, Any],
    inputs_hash: str,
    inputs_as_of: str,
    parameters: Any,
    versions: Mapping[str, Any],
    created_at: str,
    status: str = "ok",
    **columns: Any,
) -> str | None:
    """Append one receipt; None when its receipt key already exists.

    The caller owns the transaction (the decision's own).
    """

    unknown = sorted(set(columns) - set(OPTIONAL_COLUMNS))
    if unknown:
        raise ValueError(f"unknown forecast receipt columns: {unknown}")
    receipt_id = new_ulid()
    values: dict[str, Any] = {name: columns.get(name) for name in OPTIONAL_COLUMNS}
    values.update(
        id=receipt_id, receipt_key=receipt_key, kind=kind, forecaster=forecaster,
        forecaster_version=forecaster_version, scope=scope, decision_kind=decision_kind,
        binding_kind=binding_kind, event=event,
        forecast_json=_dumps(dict(forecast)), inputs_json=_dumps(dict(inputs)), inputs_hash=inputs_hash,
        inputs_as_of=inputs_as_of, parameters_json=_dumps(parameters), versions_json=_dumps(dict(versions)),
        status=status, created_at=created_at,
    )
    if values["p"] is not None:
        values["p"] = min(max(float(values["p"]), 0.0), 1.0)
    cursor = connection.execute(
        f"INSERT OR IGNORE INTO {TABLE} ({', '.join(COLUMNS)}) VALUES ({', '.join('?' for _ in COLUMNS)})",
        tuple(values[name] for name in COLUMNS),
    )
    return receipt_id if cursor.rowcount > 0 else None


def _decode(row: sqlite3.Row) -> dict[str, Any]:
    payload = dict(row)
    payload["forecast"] = _loads(payload.pop("forecast_json"), {})
    payload["inputs"] = _loads(payload.pop("inputs_json"), {})
    payload["parameters"] = _loads(payload.pop("parameters_json"), [])
    payload["versions"] = _loads(payload.pop("versions_json"), {})
    return payload


def list_receipts(
    connection: sqlite3.Connection,
    *,
    since: str | None = None,
    kind: str | None = None,
) -> list[dict[str, Any]]:
    """Every receipt (decoded), oldest first; ``[]`` on a database without the table."""

    if not has_table(connection):
        return []
    clauses: list[str] = []
    parameters: list[Any] = []
    if since:
        clauses.append("created_at >= ?")
        parameters.append(since)
    if kind:
        clauses.append("kind = ?")
        parameters.append(kind)
    where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
    rows = connection.execute(
        f"SELECT * FROM {TABLE}{where} ORDER BY created_at, id", parameters
    ).fetchall()
    return [_decode(row) for row in rows]


__all__ = ["COLUMNS", "OPTIONAL_COLUMNS", "TABLE", "has_table", "insert_receipt", "list_receipts"]
