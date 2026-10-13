"""EVSI calibration Part B persistence: ``voi_forecasts`` receipts (append-only).

The only writer is :func:`learnloop.scheduling.voi_forecasts.record_forecast`;
the only reader is the calibration report. Nothing serving reads it.
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Mapping
from typing import Any

from learnloop.clock import Clock, utc_now_iso
from learnloop.ids import new_ulid

TABLE = "voi_forecasts"

_COLUMNS = (
    "id", "receipt_key", "site", "decision_ref", "verdict", "learning_object_id",
    "probe_episode_id", "presentation_id", "source_attempt_id", "factor_id",
    "chosen_ref", "chosen_practice_item_id", "scheduler_candidate_id", "candidate_count",
    "eig_nats", "evsi_point_minutes", "evsi_lcb_minutes", "p_action_change",
    "forecast_json", "parameters_json", "versions_json", "forecast_version",
    "algorithm_version", "created_at",
)


def _dumps(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)


def _loads(value: Any, default: Any) -> Any:
    if value is None:
        return default
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return default


def has_table(connection: sqlite3.Connection) -> bool:
    return connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", (TABLE,)
    ).fetchone() is not None


def insert_forecast(
    connection: sqlite3.Connection,
    *,
    receipt_key: str,
    site: str,
    verdict: str,
    forecast: Mapping[str, Any],
    parameters: Any,
    versions: Mapping[str, Any],
    forecast_version: str,
    candidate_count: int,
    decision_ref: str | None = None,
    learning_object_id: str | None = None,
    probe_episode_id: str | None = None,
    presentation_id: str | None = None,
    source_attempt_id: str | None = None,
    factor_id: str | None = None,
    chosen_ref: str | None = None,
    chosen_practice_item_id: str | None = None,
    scheduler_candidate_id: str | None = None,
    eig_nats: float | None = None,
    evsi_point_minutes: float | None = None,
    evsi_lcb_minutes: float | None = None,
    p_action_change: float | None = None,
    algorithm_version: str | None = None,
    clock: Clock | None = None,
) -> str | None:
    """Append one forecast; None when its receipt key already exists."""

    forecast_id = new_ulid()
    values = (
        forecast_id, receipt_key, site, decision_ref, verdict, learning_object_id,
        probe_episode_id, presentation_id, source_attempt_id, factor_id,
        chosen_ref, chosen_practice_item_id, scheduler_candidate_id, int(candidate_count),
        eig_nats, evsi_point_minutes, evsi_lcb_minutes,
        None if p_action_change is None else min(max(float(p_action_change), 0.0), 1.0),
        _dumps(dict(forecast)), _dumps(parameters), _dumps(dict(versions)), forecast_version,
        algorithm_version, utc_now_iso(clock),
    )
    placeholders = ", ".join("?" for _ in _COLUMNS)
    cursor = connection.execute(
        f"INSERT OR IGNORE INTO {TABLE} ({', '.join(_COLUMNS)}) VALUES ({placeholders})", values
    )
    return forecast_id if cursor.rowcount > 0 else None


def _decode(row: sqlite3.Row) -> dict[str, Any]:
    payload = dict(row)
    payload["forecast"] = _loads(payload.pop("forecast_json"), {})
    payload["parameters"] = _loads(payload.pop("parameters_json"), [])
    payload["versions"] = _loads(payload.pop("versions_json"), {})
    return payload


def list_forecasts(connection: sqlite3.Connection, *, since: str | None = None) -> list[dict[str, Any]]:
    if not has_table(connection):
        return []
    if since:
        rows = connection.execute(
            f"SELECT * FROM {TABLE} WHERE created_at >= ? ORDER BY created_at, id", (since,)
        ).fetchall()
    else:
        rows = connection.execute(f"SELECT * FROM {TABLE} ORDER BY created_at, id").fetchall()
    return [_decode(row) for row in rows]
