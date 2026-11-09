"""RE0 §4.2: the records the cue label reads, gathered once into a :class:`~learnloop.recognition.cue.CueLedger`.

Read-only: a connection (read-only is fine), no model call, no write, no clock. Every read tolerates an older vault: a
table or column that is not there contributes nothing (the label then says so, in ``unreadable``, where it matters).
The sources, each the existing record and never a new one:

* attempts: ``practice_attempts``;
* reading and reveals: the Reader's exposures through data capture's one read (:func:`learnloop.data_capture.
  reading_exposures.read`) and ``reveal_events`` (a reveal tied to an attempt is kept with it, so it never cues it);
* lessons: ``lessons`` (a lesson exposes each of its learning objects when it ends);
* the frozen required method: the attempt's pinned assessment contract (:func:`learnloop.db.stores.write_provenance.
  pinned_contract_ids`), None where an attempt has none;
* the follow-up binding: ``followup_tasks.consumed_attempt_id``; ``followup_workflows`` (the attempt that answered its
  presentation, else the first attempt on its item after it was made);
* RO5's randomized checks: the attempts :func:`learnloop.router_objective.checks.resolve` ties to a drawn slot, which
  reads ``policy_experiment_assignments``.
"""

from __future__ import annotations

import json
import sqlite3
from typing import Any

from learnloop.recognition.cue import LESSON, READING, CueLedger, Exposure

#: The far future: ``checks.resolve``'s closure that admits every event.
_EVERYTHING = "9999-12-31"


def _present(connection: sqlite3.Connection, table: str) -> bool:
    return connection.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", (table,)).fetchone() is not None


def _columns(connection: sqlite3.Connection, table: str) -> set[str]:
    return {str(row[1]) for row in connection.execute(f"PRAGMA table_info({table})")}


def attempt_rows(connection: sqlite3.Connection) -> list[dict[str, Any]]:
    """Every attempt with what the label and the report read; ``active_seconds`` is None on a database below 252."""

    columns = _columns(connection, "practice_attempts")
    wanted = ["id", "session_id", "practice_item_id", "learning_object_id", "concept", "created_at", "latency_seconds",
              "attempt_type", "practice_mode", "correctness", "entry_surface", "plan_presentation_id",
              "probe_presentation_id", "active_seconds"]
    select = ", ".join(name if name in columns else f"NULL AS {name}" for name in wanted)
    return [dict(row) for row in connection.execute(f"SELECT {select} FROM practice_attempts ORDER BY created_at, id")]


def _reveals(connection: sqlite3.Connection) -> list[Exposure]:
    if not _present(connection, "reveal_events"):
        return []
    return [Exposure(str(lo), str(at), READING, str(attempt) if attempt else None)
            for lo, at, attempt in connection.execute(
                "SELECT learning_object_id, created_at, attempt_id FROM reveal_events "
                "WHERE learning_object_id IS NOT NULL")]


def _lessons(connection: sqlite3.Connection) -> list[Exposure]:
    if not _present(connection, "lessons"):
        return []
    out: list[Exposure] = []
    for ids_json, opened, closed in connection.execute("SELECT learning_object_ids_json, opened_at, closed_at FROM lessons"):
        try:
            ids = json.loads(ids_json or "[]")
        except ValueError:
            continue
        out.extend(Exposure(str(lo), str(closed or opened), LESSON) for lo in ids if lo)
    return out


def _methods(connection: sqlite3.Connection, attempts: list[dict[str, Any]]) -> dict[str, bool | None]:
    """Whether each attempt's pinned contract froze a required method; None where it has no pinned contract."""

    from learnloop.db.stores.write_provenance import pinned_contract_ids
    from learnloop.learner.assessment_contracts import contract_required_method

    pinned = pinned_contract_ids(connection, {str(row["id"]): row.get("practice_item_id") for row in attempts})
    versions = sorted(set(pinned.values()))
    contracts: dict[str, Any] = {}
    for start in range(0, len(versions), 500):
        chunk = versions[start:start + 500]
        for version, body in connection.execute(
                f"SELECT id, contract_json FROM assessment_contract_versions WHERE id IN ({','.join('?' for _ in chunk)})",
                chunk):
            try:
                contracts[str(version)] = json.loads(body)
            except ValueError:
                contracts[str(version)] = None
    out: dict[str, bool | None] = {}
    for row in attempts:
        contract = contracts.get(pinned.get(str(row["id"]), ""))
        out[str(row["id"])] = None if contract is None else contract_required_method(contract) is not None
    return out


def _followups(connection: sqlite3.Connection, attempts: list[dict[str, Any]]) -> frozenset[str]:
    """The attempts bound to a follow-up of an earlier miss."""

    bound: set[str] = set()
    if _present(connection, "followup_tasks"):
        bound.update(str(row[0]) for row in connection.execute(
            "SELECT consumed_attempt_id FROM followup_tasks WHERE consumed_attempt_id IS NOT NULL"))
    if _present(connection, "followup_workflows"):
        by_presentation = {str(row[key]): str(row["id"]) for row in attempts
                           for key in ("plan_presentation_id", "probe_presentation_id") if row.get(key)}
        by_item: dict[str, list[dict[str, Any]]] = {}
        for row in attempts:
            by_item.setdefault(str(row["practice_item_id"]), []).append(row)
        for source, item_id, presentation, made in connection.execute(
                "SELECT source_attempt_id, practice_item_id, presentation_id, created_at FROM followup_workflows"):
            if presentation and str(presentation) in by_presentation:
                bound.add(by_presentation[str(presentation)])
            elif item_id:
                later = next((row for row in by_item.get(str(item_id), ())
                              if str(row["id"]) != str(source) and str(row["created_at"]) >= str(made)), None)
                if later is not None:
                    bound.add(str(later["id"]))
    return frozenset(bound)


def _checks(connection: sqlite3.Connection) -> frozenset[str]:
    """The attempts RO5's randomized daily checks resolved to (whatever the grade later did with them)."""

    if not _present(connection, "policy_experiment_assignments") or not _present(connection, "attention_block_events"):
        return frozenset()
    from learnloop.router_objective import checks

    return frozenset(str(entry.attempt_id) for entry in checks.resolve(connection, through=_EVERYTHING)
                     if entry.attempt_id)


def build(connection: sqlite3.Connection, vault: Any, repository: Any, *, window_hours: float,
          session_gap_minutes: float, attempts: list[dict[str, Any]] | None = None) -> CueLedger:
    """The ledger of ``connection``'s records. ``window_hours`` is the warmth window (the report passes AD's seeded
    ``WARMTH_HOURS``) and ``session_gap_minutes`` the router objective's own session rule."""

    from learnloop.data_capture import reading_exposures

    rows = attempts if attempts is not None else attempt_rows(connection)
    reader = [Exposure(str(lo), str(at), READING)
              for lo, at in reading_exposures.read(connection, vault, repository)]
    return CueLedger(
        attempts=rows, exposures=[*reader, *_reveals(connection), *_lessons(connection)],
        method_stated=_methods(connection, rows), followups=_followups(connection, rows), checks=_checks(connection),
        window_hours=float(window_hours), session_gap_minutes=float(session_gap_minutes))
