"""RE0 §4.2: the section of ``learnloop data-capture report`` that splits results by cue.

``method_selection`` results, the practice pool the memory forecast reads, and the goal-date reads' results (the exam
answers and sittings the pool-to-goal transfer fits on, ``router_objective.goal_read``), each split by **uncued** against
**cued** (:mod:`learnloop.recognition.cue`), with the attempts' active seconds beside them.

**Observational.** Nothing here was randomized: which attempts were cued depends on what the router and the learner
chose, so a difference between the columns is a description, never an effect, and no stage reads it (RE7 and RE8 may,
once this has data). An attempt whose active seconds were not sent is **missing** and is counted so; a mean is over the
attempts that sent it and nothing is imputed from latency or from anything else (the two clocks are never blended).
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
import sqlite3
from typing import Any

from learnloop.recognition import cue as C
from learnloop.recognition import ledger as L

REPORT_VERSION = "re0_cue_report_v1"
OBSERVATIONAL = ("observational: attempts were not randomized to cues, so a difference between the columns describes "
                 "what the learner was given and is never an effect; no stage reads it")
EXAM_TYPES = ("exam_evidence", "exam_attempt")
METHOD_SELECTION = "method_selection"
ACTIVE_LABEL = ("active seconds are on the router objective's active clock, summed across resumes; a missing value is "
                "missing, never imputed from latency")


def _cell(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    scored = [float(row["correctness"]) for row in rows if row.get("correctness") is not None]
    sent = [int(row["active_seconds"]) for row in rows if row.get("active_seconds") is not None]
    return {
        "attempts": len(rows),
        "scored": len(scored),
        "mean_correctness": round(sum(scored) / len(scored), 4) if scored else None,
        "active_seconds_sent": len(sent),
        "active_seconds_missing": len(rows) - len(sent),
        "mean_active_seconds": round(sum(sent) / len(sent), 1) if sent else None,
        "latency_sent": sum(1 for row in rows if row.get("latency_seconds") is not None),
    }


def _split(rows: Sequence[Mapping[str, Any]], labels: Mapping[str, C.AttemptCue]) -> dict[str, Any]:
    by = {C.UNCUED: [], C.CUED: [], C.UNLABELLED: []}
    for row in rows:
        by[labels[str(row["id"])].label].append(row)
    return {name: _cell(found) for name, found in by.items()}


def warmth_window_hours() -> float:
    """The warmth window: the outcome contract's retention minimum, the delay under which a read is not a delayed one
    (``RETENTION_MIN_DELAY_SECONDS``, 24 hours). So a cue is "warm" in the sense the delayed outcomes already use, and
    no constant is invented here. (AD's 6-hour ``WARMTH_HOURS`` is a decay scale for its own forecasts, not a window,
    and importing it would make this package depend on adaptive difficulty.)"""

    from learnloop.outcome_contract import RETENTION_MIN_DELAY_SECONDS

    return RETENTION_MIN_DELAY_SECONDS / 3600.0


def section(connection: sqlite3.Connection, vault: Any, repository: Any, *,
            window_hours: float | None = None) -> dict[str, Any]:
    """The cue split (module docstring). Read-only; ``available`` False on a database with no attempts table.
    ``window_hours`` overrides :func:`warmth_window_hours` (tests)."""

    window_hours = warmth_window_hours() if window_hours is None else float(window_hours)
    if connection.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'practice_attempts'"
                          ).fetchone() is None:
        return {"available": False, "reason": "no attempts"}
    attempts = L.attempt_rows(connection)
    gap = float(vault.config.router_objective.session_gap_minutes)
    ledger = L.build(connection, vault, repository, window_hours=window_hours, session_gap_minutes=gap,
                     attempts=attempts)
    labels = C.cues([row for row in attempts if row.get("created_at")], ledger)
    rows = [row for row in attempts if str(row["id"]) in labels]
    practice = [row for row in rows if row.get("attempt_type") not in C.NOT_PRACTICE
                and row.get("attempt_type") != "exam_attempt"]
    fields = Counter()
    unreadable = Counter()
    uncued_unreadable = 0
    for row in practice:
        label = labels[str(row["id"])]
        fields.update(label.present)
        unreadable.update(label.unreadable)
        uncued_unreadable += 1 if label.label == C.UNCUED and label.unreadable else 0
    by_surface: dict[str, Counter[str]] = {}
    for row in rows:
        by_surface.setdefault(str(row.get("entry_surface") or "unspecified"), Counter())[
            "sent" if row.get("active_seconds") is not None else "missing"] += 1
    return {
        "available": True,
        "version": REPORT_VERSION,
        "cue_version": C.CUE_VERSION,
        "label": OBSERVATIONAL,
        "active_seconds_label": ACTIVE_LABEL,
        "window_hours": float(window_hours),
        "session_gap_minutes": gap,
        "practice_attempts": len(practice),
        "labels": dict(Counter(labels[str(row["id"])].label for row in practice)),
        "cue_present": {name: fields[name] for name in C.FIELDS},
        "unreadable": dict(sorted(unreadable.items())),
        "uncued_with_an_unreadable_field": uncued_unreadable,
        "active_seconds_by_surface": {name: dict(counts) for name, counts in sorted(by_surface.items())},
        "method_selection": _split([row for row in practice if row.get("practice_mode") == METHOD_SELECTION], labels),
        "practice_pool": _split(practice, labels),
        "goal_date_reads": {
            "basis": "exam answers and sittings (exam_evidence, exam_attempt): the results the goal-date transfer fits "
                     "on; an imported exam answer has no ledger, so it is unlabelled",
            **_split([row for row in rows if row.get("attempt_type") in EXAM_TYPES], labels)},
    }


def _cells(name: str, cells: Mapping[str, Mapping[str, Any]]) -> list[str]:
    out = [f"  {name}:"]
    for label in (C.UNCUED, C.CUED, C.UNLABELLED):
        cell = cells[label]
        if not cell["attempts"]:
            continue
        out.append(f"    {label}: {cell['attempts']} attempts, mean correctness {cell['mean_correctness']} "
                   f"({cell['scored']} scored); active seconds sent {cell['active_seconds_sent']}, missing "
                   f"{cell['active_seconds_missing']}, mean {cell['mean_active_seconds']}")
    return out


def lines(report: Mapping[str, Any]) -> list[str]:
    """The plain-text section."""

    if not report.get("available"):
        return [f"Recognition and effort (RE0): unavailable ({report.get('reason')})"]
    out = [f"Recognition and effort (RE0, {report['cue_version']}): {report['practice_attempts']} practice attempts, "
           f"{report['labels']}; {report['label']}",
           f"  cues present: {report['cue_present']}; unreadable: {report['unreadable']}; uncued with an unreadable "
           f"field: {report['uncued_with_an_unreadable_field']}",
           f"  {report['active_seconds_label']}; by surface: {report['active_seconds_by_surface']}"]
    out += _cells("method_selection", report["method_selection"])
    out += _cells("practice pool", report["practice_pool"])
    out += _cells("goal-date reads", {key: value for key, value in report["goal_date_reads"].items() if key != "basis"})
    return out
