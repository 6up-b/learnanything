"""Reader workbench RW5a: ``interactive_figures`` and ``figure_predictions`` (migration 216).

Plain SQL over a caller's connection; the caller owns the transaction. The
only writer is :mod:`learnloop.figures.service`. ``interactive_figures`` is
WORKFLOW (paid outputs, never re-run on rebuild); ``figure_predictions`` is
RAW_LEDGER, append-only by trigger except the one-time ``explanation_text``.
Replay, rebuild and every scoring, scheduling or serving path never read them.
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Mapping
from typing import Any

FIGURE_COLUMNS = ("id", "extraction_id", "span_ids_json", "region_json", "asset_id", "origin", "supersedes_id",
                  "revision_note", "spec_json", "spec_version", "kind", "verification", "verification_report_json",
                  "unsupported_kind", "model", "prompt_version", "input_hash", "created_at")
PREDICTION_COLUMNS = ("id", "figure_id", "extraction_id", "prediction_index", "learner_answer", "observed_json",
                      "matched", "explanation_text", "created_at")
#: What a figure may be shown as.
SHOWN = ("verified", "illustrative")


def has_tables(connection: sqlite3.Connection) -> bool:
    names = {row[0] for row in connection.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name IN ('interactive_figures', 'figure_predictions')")}
    return names == {"interactive_figures", "figure_predictions"}


def insert_figure(connection: sqlite3.Connection, row: Mapping[str, Any]) -> None:
    values = {
        **row,
        "span_ids_json": json.dumps(list(row.get("span_ids") or ())),
        "region_json": json.dumps(row["region"], sort_keys=True) if row.get("region") else None,
        "verification_report_json": json.dumps(row.get("verification_report") or {}, sort_keys=True, default=str),
    }
    connection.execute(
        f"INSERT INTO interactive_figures ({', '.join(FIGURE_COLUMNS)}) "
        f"VALUES ({', '.join('?' for _ in FIGURE_COLUMNS)})",
        tuple(values.get(column) for column in FIGURE_COLUMNS),
    )


def _figure(row: sqlite3.Row | tuple | None) -> dict[str, Any] | None:
    if row is None:
        return None
    found = dict(zip(FIGURE_COLUMNS, row))
    found["span_ids"] = json.loads(found.pop("span_ids_json") or "[]")
    found["region"] = json.loads(found.pop("region_json")) if found.get("region_json") else None
    found["verification_report"] = json.loads(found.pop("verification_report_json") or "{}")
    return found


def figure(connection: sqlite3.Connection, figure_id: str) -> dict[str, Any] | None:
    return _figure(connection.execute(
        f"SELECT {', '.join(FIGURE_COLUMNS)} FROM interactive_figures WHERE id = ?", (figure_id,)).fetchone())


def figures_for_extraction(connection: sqlite3.Connection, extraction_id: str) -> list[dict[str, Any]]:
    rows = connection.execute(
        f"SELECT {', '.join(FIGURE_COLUMNS)} FROM interactive_figures WHERE extraction_id = ? "
        "ORDER BY created_at, id", (extraction_id,)).fetchall()
    return [found for found in (_figure(row) for row in rows) if found is not None]


def reusable(connection: sqlite3.Connection, input_hash: str, spec_version: str) -> dict[str, Any] | None:
    """The newest figure built from the same input under the same spec
    version that is shown or recorded as unsupported (a failed build is
    retried, so it is never reused)."""

    return _figure(connection.execute(
        f"SELECT {', '.join(FIGURE_COLUMNS)} FROM interactive_figures WHERE input_hash = ? AND spec_version = ? "
        "AND verification IN ('verified', 'illustrative', 'unsupported') ORDER BY created_at DESC, id DESC LIMIT 1",
        (input_hash, spec_version)).fetchone())


def superseding(connection: sqlite3.Connection, figure_id: str) -> list[dict[str, Any]]:
    rows = connection.execute(
        f"SELECT {', '.join(FIGURE_COLUMNS)} FROM interactive_figures WHERE supersedes_id = ? "
        "ORDER BY created_at, id", (figure_id,)).fetchall()
    return [found for found in (_figure(row) for row in rows) if found is not None]


def insert_prediction(connection: sqlite3.Connection, row: Mapping[str, Any]) -> None:
    values = {**row, "observed_json": json.dumps(row.get("observed") or {}, sort_keys=True),
              "matched": int(bool(row["matched"]))}
    connection.execute(
        f"INSERT INTO figure_predictions ({', '.join(PREDICTION_COLUMNS)}) "
        f"VALUES ({', '.join('?' for _ in PREDICTION_COLUMNS)})",
        tuple(values.get(column) for column in PREDICTION_COLUMNS),
    )


def _prediction(row: sqlite3.Row | tuple | None) -> dict[str, Any] | None:
    if row is None:
        return None
    found = dict(zip(PREDICTION_COLUMNS, row))
    found["observed"] = json.loads(found.pop("observed_json") or "{}")
    found["matched"] = bool(found["matched"])
    return found


def prediction(connection: sqlite3.Connection, prediction_id: str) -> dict[str, Any] | None:
    return _prediction(connection.execute(
        f"SELECT {', '.join(PREDICTION_COLUMNS)} FROM figure_predictions WHERE id = ?", (prediction_id,)).fetchone())


def prediction_for(connection: sqlite3.Connection, figure_id: str, index: int) -> dict[str, Any] | None:
    return _prediction(connection.execute(
        f"SELECT {', '.join(PREDICTION_COLUMNS)} FROM figure_predictions WHERE figure_id = ? AND prediction_index = ?",
        (figure_id, int(index))).fetchone())


def predictions_for_figure(connection: sqlite3.Connection, figure_id: str) -> list[dict[str, Any]]:
    rows = connection.execute(
        f"SELECT {', '.join(PREDICTION_COLUMNS)} FROM figure_predictions WHERE figure_id = ? "
        "ORDER BY prediction_index", (figure_id,)).fetchall()
    return [found for found in (_prediction(row) for row in rows) if found is not None]


def set_explanation(connection: sqlite3.Connection, prediction_id: str, text: str) -> bool:
    """Set "what changed?" once; False when it was already set (the trigger
    refuses any other update)."""

    cursor = connection.execute(
        "UPDATE figure_predictions SET explanation_text = ? WHERE id = ? AND explanation_text IS NULL",
        (text, prediction_id))
    return cursor.rowcount == 1


def missed_prediction_ids(connection: sqlite3.Connection) -> list[str]:
    """Every missed prediction with an answer, oldest first (the formative backlog)."""

    if not has_tables(connection):
        return []
    return [str(row[0]) for row in connection.execute(
        "SELECT id FROM figure_predictions WHERE matched = 0 AND TRIM(learner_answer) != '' "
        "ORDER BY created_at, id")]


__all__ = [
    "FIGURE_COLUMNS",
    "PREDICTION_COLUMNS",
    "SHOWN",
    "figure",
    "figures_for_extraction",
    "has_tables",
    "insert_figure",
    "insert_prediction",
    "missed_prediction_ids",
    "prediction",
    "prediction_for",
    "predictions_for_figure",
    "reusable",
    "set_explanation",
    "superseding",
]
