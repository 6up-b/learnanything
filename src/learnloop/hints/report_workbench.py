"""Reader workbench RW2b: the workbench rows of ``learnloop hints report`` (spec_reader_workbench_v1 §13 RW2b
checkpoint, §15; UX §9.1).

Read-only, from ``help_assists`` (``surface = 'workbench'``), ``judgment_ledger``
(``hint_fit``) and the attempts, never a step's or a hint's text:

* **checks**: shown and requested, latency, verdict methods (checked,
  checked numerically, the model's reading), the symbolic kinds declared, how
  often the sandbox was missing, the error-kind guesses by kind;
* **rungs**: the rung taken against the rung suggested, by facet and ISO
  week, and the kinds taken at each rung (help levels and kinds over time);
* **recovery after a check**: whether the next check on the problem found
  the first questionable step later, none, or the same step;
* **doesn't connect** by shortcut and kind;
* **goals after a waypoint**: whether a later check placed a valid step on
  the waypoint's target node;
* **discriminating questions**: asked, answered (settled or not), skipped, and
  how many of their problems were diagnosed after Submit;
* **latency** of the check and hint routes (p50, p95).

Associations only, n = 1: it describes, never decides.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping
from contextlib import closing
from datetime import UTC, datetime
import json
from pathlib import Path
import sqlite3
from typing import Any

from learnloop.db.connection import connect
from learnloop.symbolic_view import symbolic_outcomes, verdict_records

REPORT_VERSION = "workbench-help-report-v1"


def _loads(value: Any, default: Any) -> Any:
    try:
        return json.loads(value) if value else default
    except (TypeError, ValueError):
        return default


def _when(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)


def _percentiles(values: Iterable[Any]) -> dict[str, Any]:
    ordered = sorted(float(value) for value in values if value is not None)
    if not ordered:
        return {"n": 0, "p50": None, "p95": None}

    def at(q: float) -> float:
        return ordered[min(len(ordered) - 1, max(0, int(round(q * (len(ordered) - 1)))))]

    return {"n": len(ordered), "p50": at(0.5), "p95": at(0.95)}


def _week(value: Any) -> str:
    when = _when(value)
    if when is None:
        return "unknown"
    year, week, _day = when.isocalendar()
    return f"{year}-W{week:02d}"


def build_workbench_report(sqlite_path: Path | str, *, item_facets: Mapping[str, Iterable[str]] | None = None,
                           since: str | None = None, symbolic_enabled: bool = False) -> dict[str, Any] | None:
    """The workbench block, or None when the vault has no workbench rows.
    Fix round 10: historical symbolic counts are reported only while
    ``workbench.symbolic_checks_enabled`` is on; otherwise they fold into
    ``model`` (the rows stay as they were)."""

    facets_of = {item: sorted(set(values)) for item, values in (item_facets or {}).items()}
    since_at = _when(since) if since else None
    with closing(connect(Path(sqlite_path), read_only=True)) as connection:
        connection.row_factory = sqlite3.Row
        if connection.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'help_assists'"
                              ).fetchone() is None:
            return None
        rows = [dict(row) for row in connection.execute(
            "SELECT * FROM help_assists WHERE surface = 'workbench' ORDER BY requested_at, rowid").fetchall()]
        rows = [row for row in rows if since_at is None or (_when(row["requested_at"]) or since_at) >= since_at]
        if not rows:
            return None
        fits = [dict(row) for row in connection.execute(
            "SELECT left_id, rationale FROM judgment_ledger WHERE task = 'hint_fit'").fetchall()]
        attempt_ids = sorted({row["attempt_id"] for row in rows if row["attempt_id"]})
        diagnosed: set[str] = set()
        if attempt_ids and connection.execute(
                "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'attempt_diagnoses'").fetchone():
            for start in range(0, len(attempt_ids), 500):
                chunk = attempt_ids[start:start + 500]
                diagnosed |= {str(found[0]) for found in connection.execute(
                    f"SELECT DISTINCT attempt_id FROM attempt_diagnoses WHERE attempt_id IN "
                    f"({', '.join('?' for _ in chunk)})", chunk).fetchall()}
    by_session: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_session[str(row["workbench_session_id"])].append(row)
    checks = [row for row in rows if row["assist_kind"] == "check"]
    shown_checks = [row for row in checks if row["shown"]]
    hints = [row for row in rows if row["assist_kind"] == "hint"]
    shown_hints = [row for row in hints if row["shown"]]

    # -- checks ------------------------------------------------------------------------------
    methods: Counter[str] = Counter()
    kinds_declared: Counter[str] = Counter()
    guesses: Counter[str] = Counter()
    sandbox_missing = 0
    for row in shown_checks:
        # Fix round 11: through the one accessor, with the switch given.
        for verdict in verdict_records(row, enabled=symbolic_enabled):
            methods[str(verdict["method"])] += 1
        placement = _loads(row["placement_json"], {})
        for entry in symbolic_outcomes(placement, enabled=symbolic_enabled):
            kinds_declared[str(entry["method"])] += 1
        if placement.get("symbolic_problem") == "sandbox_unavailable":
            sandbox_missing += 1
        if row["error_kind_guess"]:
            guesses[str(row["error_kind_guess"])] += 1
    check_block = {
        "requested": len(checks), "shown": len(shown_checks), "latency_ms": _percentiles(
            row["latency_ms"] for row in checks), "verdict_methods": dict(methods),
        "symbolic_outcomes": dict(kinds_declared), "sandbox_unavailable": sandbox_missing,
        "error_kind_guesses": dict(guesses),
    }

    # -- rungs taken against suggested, by facet and week ------------------------------------------
    rung_rows: dict[tuple[str, str], dict[str, Any]] = {}
    matrix: Counter[tuple[int, int]] = Counter()
    kinds_at: dict[int, Counter[str]] = defaultdict(Counter)
    for row in shown_hints:
        if row["request"] != "more" or row["level"] is None:
            continue
        level = int(row["level"])
        kinds_at[level][str(row["hint_kind"])] += 1
        if row["offered_level"]:
            matrix[(int(row["offered_level"]), level)] += 1
        for facet in facets_of.get(str(row["practice_item_id"]), ["(no facet)"]):
            key = (facet, _week(row["shown_at"] or row["requested_at"]))
            entry = rung_rows.setdefault(key, {"facet": facet, "week": key[1], "taken": Counter(),
                                               "suggested": Counter(), "learner_pick": 0})
            entry["taken"][str(level)] += 1
            if row["offered_level"]:
                entry["suggested"][str(row["offered_level"])] += 1
            if row["level_source"] == "learner_pick":
                entry["learner_pick"] += 1
    rungs = [{**entry, "taken": dict(entry["taken"]), "suggested": dict(entry["suggested"])}
             for _key, entry in sorted(rung_rows.items())]

    # -- recovery after a check ----------------------------------------------------------------------
    recovery = Counter()
    for session_rows in by_session.values():
        ordered = [row for row in session_rows if row["assist_kind"] == "check" and row["shown"]]
        for index, row in enumerate(ordered):
            first = row["first_questionable_step_id"]
            if not first:
                continue
            following = ordered[index + 1] if index + 1 < len(ordered) else None
            if following is None:
                recovery["no_later_check"] += 1
                continue
            between = any(other["assist_kind"] == "hint" and other["shown"]
                          and row["requested_at"] < other["requested_at"] < following["requested_at"]
                          for other in session_rows)
            later = following["first_questionable_step_id"]
            outcome = "none_questionable" if not later else ("same_step" if later == first else "moved_on")
            recovery[f"{outcome}{'_after_help' if between else '_unaided'}"] += 1

    # -- doesn't connect by shortcut and kind --------------------------------------------------------
    by_id = {row["id"]: row for row in rows}
    replies = Counter()
    for fit in fits:
        answered = by_id.get(str(fit["left_id"]))
        if answered is None:
            continue
        rationale = _loads(fit["rationale"], {})
        replies[(str(rationale.get("shortcut") or "none"), str(answered["hint_kind"]), int(answered["level"] or 0))] += 1
    doesnt_connect = [{"shortcut": shortcut, "kind": kind, "level": level, "replies": count}
                      for (shortcut, kind, level), count in sorted(replies.items())]
    rate = {kind: {"shown": total, "replied": sum(count for (_s, k, _l), count in replies.items() if k == kind)}
            for kind, total in Counter(str(row["hint_kind"]) for row in shown_hints).items()}

    # -- goals after a waypoint ------------------------------------------------------------------------
    goals = Counter()
    for row in shown_hints:
        if row["hint_kind"] != "waypoint" or not row["target_node_id"]:
            continue
        later_checks = [other for other in by_session[str(row["workbench_session_id"])]
                        if other["assist_kind"] == "check" and other["shown"]
                        and other["requested_at"] > row["requested_at"]]
        if not later_checks:
            goals["no_later_check"] += 1
            continue
        reached = any(verdict.get("map_node_id") == row["target_node_id"] and verdict.get("verdict") == "valid"
                      for other in later_checks for verdict in verdict_records(other, enabled=symbolic_enabled))
        goals["reached" if reached else "not_reached"] += 1
    smaller = sum(1 for row in shown_hints if row["request"] == "smaller_step")

    # -- discriminating questions --------------------------------------------------------------------
    questions = [row for row in shown_hints if row["hint_kind"] == "discriminating"]
    answers = {str(_loads(row["placement_json"], {}).get("question_assist_id")): row
               for row in rows if row["assist_kind"] == "discriminate_answer"}
    discriminating = Counter()
    for row in questions:
        answer = answers.get(str(row["id"]))
        if answer is not None:
            settled = bool(_loads(answer["placement_json"], {}).get("settled"))
            discriminating["answered_settled" if settled else "answered_both_stand"] += 1
            if answer["attempt_id"] and answer["attempt_id"] in diagnosed:
                discriminating["answered_then_diagnosed"] += 1
        elif any(other["assist_kind"] == "hint" and other["shown"] and other["requested_at"] > row["requested_at"]
                 for other in by_session[str(row["workbench_session_id"])]):
            discriminating["skipped_to_a_hint"] += 1
        else:
            discriminating["unanswered"] += 1
    return {
        "report_version": REPORT_VERSION,
        "problems": len(by_session),
        "checks": check_block,
        "rungs_by_facet_and_week": rungs,
        "taken_vs_suggested": [{"suggested": suggested, "taken": taken, "hints": count}
                               for (suggested, taken), count in sorted(matrix.items())],
        "kinds_by_rung": {str(level): dict(counter) for level, counter in sorted(kinds_at.items())},
        "recovery_after_check": dict(recovery),
        "doesnt_connect": doesnt_connect,
        "doesnt_connect_rate_by_kind": rate,
        "goals_after_waypoint": {**dict(goals), "smaller_steps_taken": smaller},
        "discriminating": {"asked": len(questions), **dict(discriminating)},
        "latency_ms": {"check": _percentiles(row["latency_ms"] for row in checks),
                       "hint": _percentiles(row["latency_ms"] for row in hints)},
    }


__all__ = ["REPORT_VERSION", "build_workbench_report"]
