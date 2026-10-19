"""Adaptive difficulty AD2+AD3's tables: the only SQL writer of migration 214.

* ``ad_selections`` (RAW_LEDGER, append-only): every serve and commission draw
  (spec_adaptive_difficulty_v1 §6.1), written before the item is served;
* ``ad_commission_results`` (RECEIPT, append-only): a landed commission's
  re-forecast (§7.4);
* ``ad_dose_offers`` (RAW_LEDGER, append-only): the Reader's randomized dose
  offers and their uptake rows (§5.12);
* ``ad_relatedness_runs`` and ``ad_coupling_versions`` (RECEIPT, append-only):
  the relatedness proposal's runs and each adopted coupling version (§5.10);
* ``ad_state``, ``ad_attempt_trace`` (DERIVED, the AD replayer) and
  ``item_forecast_scores`` (DERIVED, the forecast-score replayer): cleared and
  rebuilt with zero model calls.

Callers own the transaction. Nothing here touches evidence, mastery, FSRS or
certification (A2).
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterable, Mapping
from typing import Any

from learnloop.ids import new_ulid

SELECTIONS = "ad_selections"
COMMISSION_RESULTS = "ad_commission_results"
DOSE_OFFERS = "ad_dose_offers"
RELATEDNESS_RUNS = "ad_relatedness_runs"
COUPLING_VERSIONS = "ad_coupling_versions"
STATE = "ad_state"
TRACE = "ad_attempt_trace"
SCORES = "item_forecast_scores"


def dumps(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)


def loads(value: Any, default: Any = None) -> Any:
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


def _row(cursor: sqlite3.Cursor, row: tuple) -> dict[str, Any]:
    return {description[0]: value for description, value in zip(cursor.description, row)}


def _select(connection: sqlite3.Connection, sql: str, args: Iterable[Any] = ()) -> list[dict[str, Any]]:
    cursor = connection.execute(sql, tuple(args))
    return [_row(cursor, row) for row in cursor.fetchall()]


def _insert(connection: sqlite3.Connection, table: str, values: Mapping[str, Any]) -> None:
    columns = list(values)
    connection.execute(
        f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({', '.join('?' for _ in columns)})",
        tuple(values[column] for column in columns),
    )


# -- ad_selections --------------------------------------------------------------------------

def insert_selection(connection: sqlite3.Connection, row: Mapping[str, Any]) -> str:
    values = dict(row)
    values.setdefault("id", new_ulid())
    for name in ("support", "excluded", "constants", "chosen_point", "versions"):
        if name in values:
            payload = values.pop(name)
            values[f"{name}_json"] = None if payload is None else dumps(payload)
    values["empty_support"] = 1 if values.get("empty_support") else 0
    _insert(connection, SELECTIONS, values)
    return str(values["id"])


def selection(connection: sqlite3.Connection, selection_id: str) -> dict[str, Any] | None:
    rows = _select(connection, f"SELECT * FROM {SELECTIONS} WHERE id = ?", (selection_id,))
    return _decode_selection(rows[0]) if rows else None


def selection_by_key(connection: sqlite3.Connection, decision_key: str) -> dict[str, Any] | None:
    rows = _select(connection, f"SELECT * FROM {SELECTIONS} WHERE decision_key = ?", (decision_key,))
    return _decode_selection(rows[0]) if rows else None


def selections(connection: sqlite3.Connection, *, kind: str | None = None) -> list[dict[str, Any]]:
    if not has_table(connection, SELECTIONS):
        return []
    sql = f"SELECT * FROM {SELECTIONS}" + (" WHERE kind = ?" if kind else "") + " ORDER BY created_at, id"
    return [_decode_selection(row) for row in _select(connection, sql, (kind,) if kind else ())]


def _decode_selection(row: dict[str, Any]) -> dict[str, Any]:
    out = dict(row)
    for name in ("support", "excluded", "constants", "chosen_point", "versions"):
        out[name] = loads(out.pop(f"{name}_json", None), [] if name in ("support", "excluded") else None)
    out["empty_support"] = bool(out.get("empty_support"))
    return out


def open_commissions(connection: sqlite3.Connection) -> list[dict[str, Any]]:
    """Commission draws with no landed result yet (§6.1: at most one open per active cell)."""

    if not has_table(connection, SELECTIONS):
        return []
    rows = _select(connection, f"SELECT s.* FROM {SELECTIONS} s WHERE s.kind = 'commission' AND "
                               "s.chosen_point_json IS NOT NULL AND NOT EXISTS (SELECT 1 FROM "
                               f"{COMMISSION_RESULTS} r WHERE r.selection_id = s.id) ORDER BY s.created_at, s.id")
    return [_decode_selection(row) for row in rows]


# -- ad_commission_results --------------------------------------------------------------------

def insert_commission_result(connection: sqlite3.Connection, row: Mapping[str, Any]) -> str | None:
    values = dict(row)
    values.setdefault("id", new_ulid())
    if "features" in values:
        values["features_json"] = dumps(values.pop("features"))
    existing = connection.execute(
        f"SELECT id FROM {COMMISSION_RESULTS} WHERE selection_id = ? AND practice_item_id = ?",
        (values["selection_id"], values["practice_item_id"]),
    ).fetchone()
    if existing is not None:
        return None
    _insert(connection, COMMISSION_RESULTS, values)
    return str(values["id"])


def commission_results(connection: sqlite3.Connection) -> list[dict[str, Any]]:
    if not has_table(connection, COMMISSION_RESULTS):
        return []
    rows = _select(connection, f"SELECT * FROM {COMMISSION_RESULTS} ORDER BY created_at, id")
    for row in rows:
        row["features"] = loads(row.pop("features_json", None), None)
    return rows


# -- ad_dose_offers -----------------------------------------------------------------------------

def insert_dose_row(connection: sqlite3.Connection, row: Mapping[str, Any]) -> str:
    values = dict(row)
    values.setdefault("id", new_ulid())
    for name in ("learning_object_ids", "feasible", "infeasible", "propensities", "content", "detail"):
        if name in values:
            payload = values.pop(name)
            values[f"{name}_json"] = None if payload is None else dumps(payload)
    _insert(connection, DOSE_OFFERS, values)
    return str(values["id"])


def dose_rows(connection: sqlite3.Connection) -> list[dict[str, Any]]:
    if not has_table(connection, DOSE_OFFERS):
        return []
    rows = _select(connection, f"SELECT * FROM {DOSE_OFFERS} ORDER BY created_at, id")
    for row in rows:
        for name in ("learning_object_ids", "feasible", "infeasible", "propensities", "content", "detail"):
            row[name] = loads(row.pop(f"{name}_json", None), None)
    return rows


def dose_draw_by_key(connection: sqlite3.Connection, draw_key: str) -> dict[str, Any] | None:
    for row in dose_rows(connection):
        if row.get("draw_key") == draw_key:
            return row
    return None


# -- relatedness runs and coupling versions -------------------------------------------------

def insert_relatedness_run(connection: sqlite3.Connection, row: Mapping[str, Any]) -> str | None:
    values = dict(row)
    values.setdefault("id", new_ulid())
    for name in ("units", "judgment_ids"):
        if name in values:
            values[f"{name}_json"] = dumps(values.pop(name))
    if connection.execute(f"SELECT 1 FROM {RELATEDNESS_RUNS} WHERE run_key = ?", (values["run_key"],)).fetchone():
        return None
    _insert(connection, RELATEDNESS_RUNS, values)
    return str(values["id"])


def relatedness_runs(connection: sqlite3.Connection, *, subject_id: str | None = None) -> list[dict[str, Any]]:
    if not has_table(connection, RELATEDNESS_RUNS):
        return []
    sql = f"SELECT * FROM {RELATEDNESS_RUNS}" + (" WHERE subject_id = ?" if subject_id else "") + \
        " ORDER BY created_at, id"
    rows = _select(connection, sql, (subject_id,) if subject_id else ())
    for row in rows:
        row["units"] = loads(row.pop("units_json", None), [])
        row["judgment_ids"] = loads(row.pop("judgment_ids_json", None), [])
    return rows


def insert_coupling_version(connection: sqlite3.Connection, row: Mapping[str, Any]) -> str:
    values = dict(row)
    values.setdefault("id", new_ulid())
    if "run_ids" in values:
        values["run_ids_json"] = dumps(values.pop("run_ids"))
    _insert(connection, COUPLING_VERSIONS, values)
    return str(values["id"])


def coupling_versions(connection: sqlite3.Connection) -> list[dict[str, Any]]:
    if not has_table(connection, COUPLING_VERSIONS):
        return []
    rows = _select(connection, f"SELECT * FROM {COUPLING_VERSIONS} ORDER BY subject_id, version")
    for row in rows:
        row["run_ids"] = loads(row.pop("run_ids_json", None), [])
    return rows


# -- DERIVED: ad_state, ad_attempt_trace, item_forecast_scores -------------------------------------

def clear_derived(connection: sqlite3.Connection, tables: Iterable[str]) -> None:
    for table in tables:
        if has_table(connection, table):
            connection.execute(f"DELETE FROM {table}")


def write_state(connection: sqlite3.Connection, rows: Iterable[Mapping[str, Any]]) -> int:
    count = 0
    for row in rows:
        _insert(connection, STATE, {
            "view": row["view"], "part": row["part"], "payload_json": dumps(row["payload"]),
            "state_hash": row["state_hash"], "as_of": row.get("as_of"), "versions_json": dumps(row["versions"]),
        })
        count += 1
    return count


def write_trace(connection: sqlite3.Connection, rows: Iterable[Mapping[str, Any]]) -> int:
    count = 0
    for row in rows:
        _insert(connection, TRACE, {
            "attempt_id": row["attempt_id"], "view": row["view"], "input_status": row["input_status"],
            "category": row.get("category"), "prior_mean": row.get("prior_mean"), "prior_var": row.get("prior_var"),
            "post_mean": row.get("post_mean"), "post_var": row.get("post_var"),
            "p_categories_json": dumps(row.get("p_categories")), "information": row.get("information"),
            "points_json": dumps(row.get("points")) if row.get("points") is not None else None,
            "detail_json": dumps(row.get("detail") or {}),
        })
        count += 1
    return count


def write_scores(connection: sqlite3.Connection, rows: Iterable[Mapping[str, Any]]) -> int:
    count = 0
    for row in rows:
        _insert(connection, SCORES, {
            "receipt_id": row["receipt_id"], "forecaster": row["forecaster"],
            "practice_item_id": row.get("practice_item_id"), "plan_presentation_id": row.get("plan_presentation_id"),
            "attempt_id": row.get("attempt_id"), "p": row.get("p"), "outcome": row.get("outcome"),
            "status": row["status"], "log_loss": row.get("log_loss"), "brier": row.get("brier"),
            "first_attempt_lo": None if row.get("first_attempt_lo") is None else int(bool(row["first_attempt_lo"])),
            "first_surface_cell": None if row.get("first_surface_cell") is None else int(bool(row["first_surface_cell"])),
            "capability": row.get("capability"), "detail_json": dumps(row.get("detail") or {}),
        })
        count += 1
    return count


def read_state(connection: sqlite3.Connection) -> list[dict[str, Any]]:
    if not has_table(connection, STATE):
        return []
    rows = _select(connection, f"SELECT * FROM {STATE} ORDER BY view, part")
    for row in rows:
        row["payload"] = loads(row.pop("payload_json"), {})
        row["versions"] = loads(row.pop("versions_json"), {})
    return rows


def read_trace(connection: sqlite3.Connection) -> list[dict[str, Any]]:
    if not has_table(connection, TRACE):
        return []
    rows = _select(connection, f"SELECT * FROM {TRACE} ORDER BY attempt_id, view")
    for row in rows:
        row["p_categories"] = loads(row.pop("p_categories_json"), None)
        row["points"] = loads(row.pop("points_json"), None)
        row["detail"] = loads(row.pop("detail_json"), {})
    return rows


def read_scores(connection: sqlite3.Connection) -> list[dict[str, Any]]:
    if not has_table(connection, SCORES):
        return []
    rows = _select(connection, f"SELECT * FROM {SCORES} ORDER BY receipt_id")
    for row in rows:
        row["detail"] = loads(row.pop("detail_json"), {})
    return rows


__all__ = [
    "COMMISSION_RESULTS",
    "COUPLING_VERSIONS",
    "DOSE_OFFERS",
    "RELATEDNESS_RUNS",
    "SCORES",
    "SELECTIONS",
    "STATE",
    "TRACE",
    "clear_derived",
    "commission_results",
    "coupling_versions",
    "dose_draw_by_key",
    "dose_rows",
    "dumps",
    "has_table",
    "insert_commission_result",
    "insert_coupling_version",
    "insert_dose_row",
    "insert_relatedness_run",
    "insert_selection",
    "loads",
    "open_commissions",
    "read_scores",
    "read_state",
    "read_trace",
    "relatedness_runs",
    "selection",
    "selection_by_key",
    "selections",
    "write_scores",
    "write_state",
    "write_trace",
]
