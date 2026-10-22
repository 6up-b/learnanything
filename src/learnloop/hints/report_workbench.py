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
from learnloop.symbolic_view import has_verdict_record, symbolic_outcomes, verdict_records

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


# ---------------------------------------------------------------------------
# Per-help outcomes on the workbench (spec_adaptive_hints_v1 §6.1; Reader §5.10, C13)
# ---------------------------------------------------------------------------

#: The help rows that count as further help between a help and the next check.
WORKBENCH_HELP_KINDS = ("hint", "bridge", "example", "compare_methods")
#: What :func:`workbench_unaided_progress` answers.
PROGRESS_OUTCOMES = ("continued", "not_continued", "more_help", "no_later_check", "unknown")


def _snapshot_pairs(value: Any) -> set[tuple[str, str]] | None:
    """A row's ``step_snapshot_json`` as ``(chain_id, content hash)`` pairs,
    or None when the row recorded none (the work at delivery is unknown)."""

    records = _loads(value, None)
    if not isinstance(records, list):
        return None
    return {(str(entry.get("chain_id")), str(entry.get("hash") or ""))
            for entry in records if isinstance(entry, Mapping) and entry.get("chain_id")}


def _parent(row: Mapping[str, Any]) -> str | None:
    placement = _loads(row.get("placement_json"), {})
    parent = placement.get("hint_assist_id") if isinstance(placement, Mapping) else None
    return str(parent) if parent else None


def workbench_unaided_progress(row: Mapping[str, Any], session_rows: Iterable[Mapping[str, Any]], *,
                               maps: Mapping[str, Mapping[str, list[str]]] | None = None) -> str:
    """Unaided next progress for one shown workbench help row (§6.1: "in the
    workbench, progress ... measured to the next valid step"): the ONE
    definition the Reader's ``help_outcomes`` reads (Reader §5.10, C13).

    * The **work at delivery** is the row's own step snapshot (a hint records
      the steps, with their content hashes, it was written against; a worked
      example records the steps it was searched with), or, for a passage
      shown under a hint, that hint's. With none on record the answer is
      ``unknown``: progress is never measured against work nobody recorded.
    * **The next check** is the problem's next shown check after the help.
      None yet: ``no_later_check``.
    * **Further help before it** is any other shown help row (a hint, a
      bridge, a worked example, a learner's "another passage", a comparison)
      between the help and that check, except what was delivered with the
      help itself (the hint, and the bridge and example its delivery
      started). Then ``more_help``, unless the next hint's placement on the
      same map settles whether this hint's target was reached first
      (:func:`learnloop.hints.report_adaptive.progress_by_next_placement`):
      ``continued`` / ``not_continued``.
    * Otherwise ``continued`` when that check found **progress where the help
      was placed** (fix round 2, 6), else ``not_continued``. Progress is a
      valid step new or changed since delivery (a ``(chain_id, hash)`` pair
      the snapshot does not hold: a step already on the page at delivery that
      a later check first validates is not progress) that is on the help's
      target node (the hint's target, or for a kind without one the next node
      from its placement, :func:`learnloop.hints.report_adaptive.hint_target`),
      is the step the help was about or the first questionable step, or comes
      after the step it continues from (its next step; with neither recorded,
      any step). A step that was already valid at delivery (the delivered
      verdicts) and was only edited is never progress unless it lands on the
      target: an unrelated edit to an earlier valid step is not recovery.
      The delivered verdicts are the row's own, a passage's hint's, or the
      last shown check before it (:func:`_valid_at_delivery`, fix round 3,
      M1); with none on record the answer is ``unknown``.

    ``session_rows``: the problem's workbench rows (any order); each needs
    ``id``, ``assist_kind``, ``shown``, ``shown_at`` / ``requested_at``,
    ``placement_json``, ``chooser``, ``step_snapshot_json`` and
    ``step_verdicts_json`` (and the map columns for the placement rule)."""

    from learnloop.hints import report_adaptive

    def at(value: Mapping[str, Any]) -> datetime | None:
        return _when(value.get("shown_at") or value.get("requested_at"))

    rows = [other for other in session_rows if other.get("shown")]
    by_id = {str(other["id"]): other for other in rows}
    shown = at(row)
    if shown is None:
        return "unknown"
    parent = _parent(row)
    head = str(row["id"]) if row.get("assist_kind") == "hint" else parent
    # What was delivered with the help: its hint and the passages that hint's
    # delivery started (a learner's "another passage" is a new request).
    package = {str(row["id"])} | ({head} if head else set())
    package |= {str(other["id"]) for other in rows
                if head and _parent(other) == head and other.get("chooser") != "learner_pick"}
    checks = sorted(((when, str(other["id"]), other) for other in rows
                     if other.get("assist_kind") == "check" and (when := at(other)) is not None and when > shown),
                    key=lambda entry: (entry[0], entry[1]))
    if not checks:
        return "no_later_check"
    following_at, _following_id, following = checks[0]
    between = sorted(((when, str(other["id"]), other) for other in rows
                      if other.get("assist_kind") in WORKBENCH_HELP_KINDS and str(other["id"]) not in package
                      and (when := at(other)) is not None and shown < when < following_at),
                     key=lambda entry: (entry[0], entry[1]))
    if between:
        nearest = between[0][2]
        if row.get("assist_kind") == "hint" and nearest.get("assist_kind") == "hint":
            settled = report_adaptive.progress_by_next_placement(row, nearest, maps or {})
            if settled is not None:
                return "continued" if settled == "reached" else "not_continued"
        return "more_help"
    snapshot_row = row if row.get("step_snapshot_json") else by_id.get(head or "")
    delivered = _snapshot_pairs((snapshot_row or {}).get("step_snapshot_json"))
    if delivered is None:
        return "unknown"
    # Where the help was placed: its own (a hint, a "show me" example) or,
    # for a passage under a hint, that hint's.
    placed = row if row.get("assist_kind") == "hint" or not head else (by_id.get(head) or row)
    # Fix round 3 (M1): which steps were already valid at delivery. Without
    # that record nothing can tell an unrelated edit from progress: unknown.
    valid_then = _valid_at_delivery(row, by_id.get(head or "") if head != str(row["id"]) else None, rows, at)
    if valid_then is None:
        return "unknown"
    return "continued" if _progress_at_placement(placed, snapshot_row or {}, delivered, following, maps or {},
                                                 valid_then=valid_then) else "not_continued"


def _last_check_verdicts(rows: Iterable[Mapping[str, Any]], before: datetime | None, at: Any
                         ) -> list[dict[str, Any]] | None:
    """The verdicts of the problem's last shown check at or before ``before``."""

    if before is None:
        return None
    checks = sorted(((when, str(other["id"]), other) for other in rows
                     if other.get("assist_kind") == "check" and (when := at(other)) is not None and when <= before),
                    key=lambda entry: (entry[0], entry[1]))
    return verdict_records(checks[-1][2], enabled=False) if checks else None


def _valid_at_delivery(row: Mapping[str, Any], head_row: Mapping[str, Any] | None,
                       rows: Iterable[Mapping[str, Any]], at: Any) -> set[str] | None:
    """The chains valid when the help was delivered (fix round 3, M1), or
    None when nothing records it:

    * the row's own ``step_verdicts_json`` (a hint's request context; a
      worked example stores the verdicts it was searched against);
    * a hint without one: the problem's last shown check at or before it, or
      none (no check had been shown: no step was known valid);
    * a passage under a hint without its own: that hint's, by the same rule;
    * a "show me" example without its own: the last shown check at or before
      it; none on record: None (``unknown``, never ``continued``)."""

    rows = list(rows)

    def valid(records: Iterable[Mapping[str, Any]]) -> set[str]:
        return {str(entry.get("chain_id")) for entry in records if entry.get("verdict") == "valid"}

    def of_hint(hint: Mapping[str, Any]) -> set[str]:
        if has_verdict_record(hint):
            return valid(verdict_records(hint, enabled=False))
        return valid(_last_check_verdicts(rows, at(hint), at) or [])

    if row.get("assist_kind") == "hint":
        return of_hint(row)
    if has_verdict_record(row):
        return valid(verdict_records(row, enabled=False))
    if head_row is not None:
        return of_hint(head_row)
    found = _last_check_verdicts(rows, at(row), at)
    return valid(found) if found is not None else None


def _positions(value: Any) -> dict[str, int]:
    records = _loads(value, None)
    out: dict[str, int] = {}
    for entry in records if isinstance(records, list) else []:
        if isinstance(entry, Mapping) and entry.get("chain_id") and entry.get("number") is not None:
            try:
                out[str(entry["chain_id"])] = int(entry["number"])
            except (TypeError, ValueError):
                continue
    return out


def _progress_at_placement(placed: Mapping[str, Any], snapshot_row: Mapping[str, Any],
                           delivered: set[tuple[str, str]], following: Mapping[str, Any],
                           maps: Mapping[str, Mapping[str, list[str]]], *, valid_then: set[str]) -> bool:
    """Whether the next check found progress where the help was placed
    (:func:`workbench_unaided_progress`, fix round 2, 6)."""

    from learnloop.hints import report_adaptive

    target = report_adaptive.hint_target(placed, maps.get(str(placed.get("map_id") or "")) or {}) \
        if placed.get("map_id") or placed.get("target_node_id") else None
    about = {str(value) for value in (placed.get("about_step_id"), placed.get("first_questionable_step_id"))
             if value}
    continue_from = str(placed.get("continue_from_step_id") or "") or None
    # Positions in the following check's work (an inserted step has one
    # there), else at delivery.
    positions = {**_positions(snapshot_row.get("step_snapshot_json")),
                 **_positions(following.get("step_snapshot_json"))}
    anchor = positions.get(continue_from) if continue_from else None
    if anchor is None and about:
        known = [positions[chain] for chain in about if chain in positions]
        anchor = min(known) - 1 if known else None
    if anchor is None and not continue_from:
        anchor = 0  # placed at the givens: every step is after it
    for entry in verdict_records(following, enabled=False):
        chain = str(entry.get("chain_id"))
        if entry.get("verdict") != "valid" or (chain, str(entry.get("hash") or "")) in delivered:
            continue
        if target and str(entry.get("map_node_id") or "") == target:
            return True
        if chain in valid_then:
            continue  # valid before the help, only edited since: not recovery
        if chain in about:
            return True
        if anchor is not None and chain in positions and positions[chain] > anchor:
            return True
    return False


__all__ = ["PROGRESS_OUTCOMES", "REPORT_VERSION", "WORKBENCH_HELP_KINDS", "build_workbench_report",
           "workbench_unaided_progress"]
