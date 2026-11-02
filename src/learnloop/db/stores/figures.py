"""Reader workbench RW5a: ``interactive_figures`` and ``figure_predictions`` (migration 216);
Reader RW5d P1: ``figure_requests`` and the rebuilt ``interactive_figures`` (migration 224).

Plain SQL over a caller's connection; the caller owns the transaction. The
only writer is :mod:`learnloop.figures.service`. ``interactive_figures`` is
WORKFLOW (paid outputs, never re-run on rebuild); ``figure_predictions`` is
RAW_LEDGER, append-only by trigger except the one-time ``explanation_text``.
Replay, rebuild and every scoring, scheduling or serving path never read them.
``figure_requests`` (RW5d) is RAW_LEDGER: append-only by trigger, the only
update setting ``figure_id`` once.
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Mapping
from typing import Any

FIGURE_COLUMNS = ("id", "extraction_id", "span_ids_json", "region_json", "asset_id", "input_span_ids_json", "origin",
                  "supersedes_id", "revision_note", "spec_json", "spec_version", "kind", "verification", "verification_report_json",
                  "unsupported_kind", "model", "prompt_version", "input_hash", "created_at",
                  # RW5d P1 (migration 224): the request, the goal, the grounding and the
                  # retrieved passages' keys; the tier (grammar until P2).
                  "request_id", "goal_text", "grounding", "input_span_keys_json", "tier",
                  # RW5d P2: a sketch's program version, the engine it was
                  # verified under and the check lines code ran.
                  "program_version", "engine_sha256", "runtime_digest", "checks_json",
                  # RW5d P2b: a rich figure's video and the quick figure it follows.
                  "media_file_name", "fuller_of_id")
REQUEST_COLUMNS = ("id", "origin", "goal_text", "goal_author", "anchor_json", "reading_at_json", "host_ref_json",
                   "policy", "caller_kind", "policy_derived_from", "grounding", "grounding_manifest_json",
                   "build_mode", "tiers_allowed_json", "prefetch_decision_id", "figure_id", "created_at")
PREDICTION_COLUMNS = ("id", "figure_id", "extraction_id", "prediction_index", "learner_answer", "observed_json",
                      "matched", "explanation_text", "created_at",
                      # Reader RW5d P3 (migration 232): the open attempt's figure row the
                      # prediction was made under, and when "what changed?" was written.
                      "assist_id", "explained_at")
#: What a figure may be shown as.
SHOWN = ("verified", "illustrative")
#: The one stored value RW5a never writes (migration 216 keeps it for RW5c's
#: source check); the service shows such a row as an illustration.
VERIFIED_RW5C = "verified"


def shown_verification(verification: str | None) -> str | None:
    """A stored verification as RW5a shows and counts it: ``verified`` (never
    written by RW5a; RW5c's) is an illustration. The one normalization the
    figure view and the Reader report share (final round, High 2)."""

    return "illustrative" if verification == VERIFIED_RW5C else verification


def has_tables(connection: sqlite3.Connection) -> bool:
    names = {row[0] for row in connection.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name IN "
        "('interactive_figures', 'figure_predictions', 'figure_requests')")}
    return names == {"interactive_figures", "figure_predictions", "figure_requests"}


def insert_figure(connection: sqlite3.Connection, row: Mapping[str, Any]) -> None:
    values = {
        **row,
        "span_ids_json": json.dumps(list(row.get("span_ids") or ())),
        "input_span_ids_json": json.dumps(list(row.get("input_span_ids") or ())),
        "region_json": json.dumps(row["region"], sort_keys=True) if row.get("region") else None,
        "verification_report_json": json.dumps(row.get("verification_report") or {}, sort_keys=True, default=str),
        "input_span_keys_json": json.dumps([list(key) for key in row.get("input_span_keys") or ()]),
        "grounding": row.get("grounding") or "anchor",
        "tier": row.get("tier") or "grammar",
        "checks_json": json.dumps(list(row.get("checks") or ()), sort_keys=True),
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
    found["input_span_ids"] = json.loads(found.pop("input_span_ids_json") or "[]")
    found["region"] = json.loads(found.pop("region_json")) if found.get("region_json") else None
    found["verification_report"] = json.loads(found.pop("verification_report_json") or "{}")
    found["input_span_keys"] = [tuple(str(part) for part in key)
                                for key in json.loads(found.pop("input_span_keys_json") or "[]")]
    found["checks"] = json.loads(found.pop("checks_json") or "[]")
    return found


def figure(connection: sqlite3.Connection, figure_id: str) -> dict[str, Any] | None:
    return _figure(connection.execute(
        f"SELECT {', '.join(FIGURE_COLUMNS)} FROM interactive_figures WHERE id = ?", (figure_id,)).fetchone())


def insert_request(connection: sqlite3.Connection, row: Mapping[str, Any]) -> None:
    """One ``figure_requests`` row (RW5d): what was asked, before the figure."""

    def as_json(value: Any) -> str | None:
        return None if value is None else json.dumps(value, sort_keys=True, default=str)

    values = {
        **row,
        "anchor_json": as_json(row.get("anchor")),
        "reading_at_json": as_json(row.get("reading_at")),
        "host_ref_json": json.dumps(row.get("host_ref") or {}, sort_keys=True),
        "grounding_manifest_json": json.dumps(row.get("grounding_manifest") or {}, sort_keys=True, default=str),
        "tiers_allowed_json": json.dumps(list(row.get("tiers_allowed") or ["grammar"])),
        "build_mode": row.get("build_mode") or "pressed",
    }
    connection.execute(
        f"INSERT INTO figure_requests ({', '.join(REQUEST_COLUMNS)}) "
        f"VALUES ({', '.join('?' for _ in REQUEST_COLUMNS)})",
        tuple(values.get(column) for column in REQUEST_COLUMNS),
    )


def set_request_figure(connection: sqlite3.Connection, request_id: str, figure_id: str) -> bool:
    """Name the figure a request built or reused, once (the trigger refuses any other update)."""

    cursor = connection.execute(
        "UPDATE figure_requests SET figure_id = ? WHERE id = ? AND figure_id IS NULL", (figure_id, request_id))
    return cursor.rowcount == 1


def _request(row: sqlite3.Row | tuple | None) -> dict[str, Any] | None:
    if row is None:
        return None
    found = dict(zip(REQUEST_COLUMNS, row))
    for column, key, empty in (("anchor_json", "anchor", None), ("reading_at_json", "reading_at", None),
                               ("host_ref_json", "host_ref", "{}"),
                               ("grounding_manifest_json", "grounding_manifest", "{}"),
                               ("tiers_allowed_json", "tiers_allowed", "[]")):
        raw = found.pop(column)
        found[key] = json.loads(raw) if raw else (json.loads(empty) if empty else None)
    return found


def request(connection: sqlite3.Connection, request_id: str) -> dict[str, Any] | None:
    return _request(connection.execute(
        f"SELECT {', '.join(REQUEST_COLUMNS)} FROM figure_requests WHERE id = ?", (request_id,)).fetchone())


def requests(connection: sqlite3.Connection) -> list[dict[str, Any]]:
    """Every figure request, oldest first (the Reader report's show-me block)."""

    rows = connection.execute(
        f"SELECT {', '.join(REQUEST_COLUMNS)} FROM figure_requests ORDER BY created_at, id").fetchall()
    return [found for found in (_request(row) for row in rows) if found is not None]


def figures_for_extraction(connection: sqlite3.Connection, extraction_id: str) -> list[dict[str, Any]]:
    rows = connection.execute(
        f"SELECT {', '.join(FIGURE_COLUMNS)} FROM interactive_figures WHERE extraction_id = ? "
        "ORDER BY created_at, id", (extraction_id,)).fetchall()
    return [found for found in (_figure(row) for row in rows) if found is not None]


def shown_figures(connection: sqlite3.Connection, spec_versions: tuple[str, ...], *,
                  limit: int) -> list[dict[str, Any]]:
    """Reader RW5d P3: the newest shown figures of the given spec versions
    (a quick figure's own row, never a fuller version's), newest first, at
    most ``limit``: what the hint chooser's ``explore_figure`` precondition
    scans (the figure help module checks each)."""

    marks = ", ".join("?" for _ in spec_versions)
    rows = connection.execute(
        f"SELECT {', '.join(FIGURE_COLUMNS)} FROM interactive_figures WHERE verification IN (?, ?) "
        f"AND spec_version IN ({marks}) AND fuller_of_id IS NULL AND spec_json IS NOT NULL "
        "ORDER BY created_at DESC, id DESC LIMIT ?", (*SHOWN, *spec_versions, int(limit))).fetchall()
    return [found for found in (_figure(row) for row in rows) if found is not None]


def _versions(spec_version: str | tuple[str, ...]) -> tuple[tuple[str, ...], str]:
    """RW5d P2: one input may be answered under either spec version (a grammar
    spec or a sketch), so lookups take one version or several."""

    versions = (spec_version,) if isinstance(spec_version, str) else tuple(spec_version)
    return versions, ", ".join("?" for _ in versions)


def reusable(connection: sqlite3.Connection, input_hash: str, spec_version: str | tuple[str, ...]
             ) -> dict[str, Any] | None:
    """The newest figure built from the same input under the same spec
    version(s) that is shown or recorded as unsupported (a failed build is
    retried, so it is never reused)."""

    versions, marks = _versions(spec_version)
    return _figure(connection.execute(
        f"SELECT {', '.join(FIGURE_COLUMNS)} FROM interactive_figures WHERE input_hash = ? "
        f"AND spec_version IN ({marks}) "
        "AND verification IN ('verified', 'illustrative', 'unsupported') ORDER BY created_at DESC, id DESC LIMIT 1",
        (input_hash, *versions)).fetchone())


def latest_for_input(connection: sqlite3.Connection, input_hash: str, spec_version: str | tuple[str, ...]
                     ) -> dict[str, Any] | None:
    """The newest figure stored for this input under this spec version, whatever its verification."""

    versions, marks = _versions(spec_version)
    return _figure(connection.execute(
        f"SELECT {', '.join(FIGURE_COLUMNS)} FROM interactive_figures WHERE input_hash = ? "
        f"AND spec_version IN ({marks}) ORDER BY created_at DESC, id DESC LIMIT 1",
        (input_hash, *versions)).fetchone())


def builds_for_input(connection: sqlite3.Connection, input_hash: str, spec_version: str | tuple[str, ...]) -> int:
    """How many figures were stored for this input: a build's retry generation
    (a stored failure starts the next one; a crash before the row does not)."""

    versions, marks = _versions(spec_version)
    return int(connection.execute(
        f"SELECT COUNT(*) FROM interactive_figures WHERE input_hash = ? AND spec_version IN ({marks})",
        (input_hash, *versions)).fetchone()[0])


def fuller_rows(connection: sqlite3.Connection, figure_id: str) -> list[dict[str, Any]]:
    """RW5d P2b: the rich figures stored as the fuller version of ``figure_id``, oldest first."""

    rows = connection.execute(
        f"SELECT {', '.join(FIGURE_COLUMNS)} FROM interactive_figures WHERE fuller_of_id = ? "
        "ORDER BY created_at, id", (figure_id,)).fetchall()
    return [found for found in (_figure(row) for row in rows) if found is not None]


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


def set_explanation(connection: sqlite3.Connection, prediction_id: str, text: str, *,
                    at: str | None = None) -> bool:
    """Set "what changed?" once, with when (``explained_at``, RW5d P3); False
    when it was already set (the trigger refuses any other update)."""

    cursor = connection.execute(
        "UPDATE figure_predictions SET explanation_text = ?, explained_at = ? WHERE id = ? "
        "AND explanation_text IS NULL", (text, at, prediction_id))
    return cursor.rowcount == 1


def missed_prediction_ids(connection: sqlite3.Connection) -> list[str]:
    """Every missed prediction with an answer, oldest first (the formative backlog)."""

    if not has_tables(connection):
        return []
    return [str(row[0]) for row in connection.execute(
        "SELECT id FROM figure_predictions WHERE matched = 0 AND TRIM(learner_answer) != '' "
        "ORDER BY created_at, id")]


def figure_verdicts(connection: sqlite3.Connection, task: str, figure_id: str) -> list[dict[str, Any]]:
    """RW5d P2 (Codex review F8): a figure's ``judgment_ledger`` verdicts for
    one task in the order they were appended (the build's, then any engine
    re-verification)."""

    return [{"id": row[0], "judge": row[1], "input_hash": row[2], "verdict": row[3]} for row in connection.execute(
        "SELECT id, judge, input_hash, verdict FROM judgment_ledger WHERE task = ? AND left_kind = 'interactive_figure' "
        "AND left_id = ? AND right_kind IS NULL ORDER BY rowid", (task, figure_id))]


__all__ = [
    "FIGURE_COLUMNS",
    "PREDICTION_COLUMNS",
    "REQUEST_COLUMNS",
    "SHOWN",
    "VERIFIED_RW5C",
    "shown_verification",
    "builds_for_input",
    "figure",
    "figure_verdicts",
    "figures_for_extraction",
    "shown_figures",
    "has_tables",
    "insert_figure",
    "insert_prediction",
    "insert_request",
    "request",
    "requests",
    "set_request_figure",
    "latest_for_input",
    "missed_prediction_ids",
    "prediction",
    "prediction_for",
    "predictions_for_figure",
    "reusable",
    "set_explanation",
    "superseding",
]
