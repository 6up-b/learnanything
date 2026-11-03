"""A3: the honest time metric: calendar time and recorded minutes to a first delayed success.

**A first-delayed-success proxy, not goal attainment.** From a learning object's enrollment to the first
presentation the shared definition (:mod:`learnloop.delayed_completion`) calls a completed delayed attempt at
or above the success threshold the board already uses. An enrollment is the earliest of a goal's confirmed
contract (or its creation) whose scope holds the LO, or a learner's own commitment on it; with neither it is
the first exposure, and says so. No goal model: the goal contract in force at the success (or now) is pinned by
id, version and due date.

**Time is reported in two kinds and never blended.** ``active``: what a learner's activity was measured to take
(attempt latency, Reader active seconds). ``elapsed``: wall-clock spans around it (a presentation's serve to its
answer, a Reader visit's open to its close, a reading block's start to its end). Unrecorded time is not zero: a
trajectory carries its coverage, and an unfinished trajectory stays on the report (right-censored at ``as_of``).
A Reader visit is attributed to an LO only when a reading receipt or an exposure on that LO falls inside it
(split evenly when several do); the rest is reported ``unattributed``. Lessons' durations join with TE3.

Read-only; no model call. The router leaf: it imports no scheduler or substrate code.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, field
import json
import sqlite3
from typing import Any

from learnloop import delayed_completion as DC
from learnloop.clock import parse_utc
from learnloop.router.outcomes import OUTCOME_VERSION_V3, _completion, _decision_block, _Ledger, _table_present
from learnloop.vault.models import learning_object_facet_union

METRIC_VERSION = "first_delayed_success_proxy_v1"
LABEL = "first-delayed-success proxy, not goal attainment"

SOURCE_GOAL = "goal"
SOURCE_COMMITMENT = "commitment"
SOURCE_FIRST_EXPOSURE = "first_exposure"
#: Checks the system itself dated: never an enrollment.
_SYSTEM_VIA = frozenset({"measurement", "lesson"})
#: Attempt types that are no served problem (``scoreboard._NON_PROBLEM_ATTEMPT_TYPES``).
_NON_PROBLEM = frozenset({"self_report", "skip"})


@dataclass(frozen=True)
class Trajectory:
    learning_object_id: str
    enrolled_at: str
    enrollment_source: str
    goal: Mapping[str, Any] | None
    success_attempt_id: str | None
    success_at: str | None
    calendar_days: float | None
    open_calendar_days: float | None
    attempts: int
    attempts_with_latency: int
    attempts_bound_to_a_presentation: int
    attempts_before_enrollment: int
    active_attempt_seconds: float
    elapsed_attempt_seconds: float
    reading_visits: int
    active_reading_seconds: float
    elapsed_reading_seconds: float
    plan_reading_elapsed_seconds: float
    version: str = field(default=METRIC_VERSION)

    @property
    def reached(self) -> bool:
        return self.success_attempt_id is not None

    @property
    def complete_latency(self) -> bool:
        return self.attempts == self.attempts_with_latency

    @property
    def active_minutes(self) -> float:
        return (self.active_attempt_seconds + self.active_reading_seconds) / 60.0

    @property
    def elapsed_minutes(self) -> float:
        return (self.elapsed_attempt_seconds + self.elapsed_reading_seconds + self.plan_reading_elapsed_seconds) / 60.0

    def as_dict(self) -> dict[str, Any]:
        return {**asdict(self), "reached": self.reached, "active_minutes": round(self.active_minutes, 4),
                "elapsed_minutes": round(self.elapsed_minutes, 4), "complete_latency": self.complete_latency}


def _seconds(later: str, earlier: str) -> float | None:
    late, early = parse_utc(later), parse_utc(earlier)
    if late is None or early is None:
        return None
    return (late - early).total_seconds()


def _days(later: str, earlier: str) -> float | None:
    seconds = _seconds(later, earlier)
    return None if seconds is None else round(seconds / 86400.0, 6)


def _goal_scopes(vault: Any) -> dict[str, list[Any]]:
    """Each LO's goals (any status: an enrollment is a historical fact)."""

    out: dict[str, list[Any]] = {}
    for goal in getattr(vault, "goals", ()) or ():
        scope = getattr(goal, "facet_scope", None)
        if scope is None:
            continue
        concepts, facets = set(scope.concepts), set(scope.facets)
        for lo_id, learning_object in vault.learning_objects.items():
            if learning_object.concept in concepts or (facets & set(learning_object_facet_union(learning_object))):
                out.setdefault(str(lo_id), []).append(goal)
    return out


def _contract_rows(connection: sqlite3.Connection) -> dict[str, list[dict[str, Any]]]:
    if not _table_present(connection, "goal_contract_versions"):
        return {}
    rows: dict[str, list[dict[str, Any]]] = {}
    for row in connection.execute(
            "SELECT id, goal_id, version, contract_json, content_hash, created_at FROM goal_contract_versions "
            "ORDER BY goal_id, version"):
        rows.setdefault(str(row["goal_id"]), []).append(dict(row))
    return rows


def _pinned(goals: Sequence[Any], contracts: Mapping[str, list[dict[str, Any]]], as_of: str) -> dict[str, Any] | None:
    """The contract in force at ``as_of``: the newest confirmed version of the LO's first goal holding one."""

    fallback = None
    for goal in goals:
        versions = [row for row in contracts.get(str(goal.id), ()) if str(row["created_at"]) <= as_of]
        if not versions:
            fallback = fallback or {"goal_id": str(goal.id), "contract_version_id": None, "version": None,
                                    "content_hash": None, "due_at": getattr(goal, "due_at", None) or None}
            continue
        head = versions[-1]
        try:
            due = (json.loads(head["contract_json"]) or {}).get("due_at")
        except (TypeError, ValueError):
            due = None
        return {"goal_id": str(goal.id), "contract_version_id": str(head["id"]), "version": int(head["version"]),
                "content_hash": str(head["content_hash"]), "due_at": due}
    return fallback


def _commitment_times(connection: sqlite3.Connection, vault: Any) -> dict[str, str]:
    """Each LO's first commitment by the learner (a system-dated check is no enrollment)."""

    if not _table_present(connection, "commitment_target_versions"):
        return {}
    item_lo = {item.id: item.learning_object_id for item in vault.practice_items.values()}
    out: dict[str, str] = {}
    for row in connection.execute(
            "SELECT t.target_kind, t.target_ref, v.created_at, v.provenance_json FROM commitment_target_versions t "
            "JOIN commitment_versions v ON v.id = t.commitment_version_id "
            "WHERE t.target_kind IN ('learning_object', 'legacy_practice_item')"):
        try:
            via = (json.loads(row["provenance_json"] or "{}") or {}).get("via")
        except (TypeError, ValueError):
            via = None
        if via in _SYSTEM_VIA:
            continue
        lo = str(row["target_ref"]) if row["target_kind"] == "learning_object" else item_lo.get(str(row["target_ref"]))
        if lo and (lo not in out or str(row["created_at"]) < out[lo]):
            out[lo] = str(row["created_at"])
    return out


def _enrollment(lo: str, goals: Sequence[Any], contracts: Mapping[str, list[dict[str, Any]]],
                commitments: Mapping[str, str], ledger: _Ledger) -> tuple[str, str] | None:
    times: list[tuple[str, str]] = []
    for goal in goals:
        versions = contracts.get(str(goal.id), ())
        when = str(versions[0]["created_at"]) if versions else getattr(goal, "created_at", None)
        if when:
            times.append((str(when), SOURCE_GOAL))
    if lo in commitments:
        times.append((commitments[lo], SOURCE_COMMITMENT))
    if times:
        return min(times)
    exposures = ledger.lo_exposures.get(lo) or ()
    return (str(exposures[0][0]), SOURCE_FIRST_EXPOSURE) if exposures else None


def _visits(connection: sqlite3.Connection) -> list[dict[str, Any]]:
    """Reader visits as open, close, active seconds (a visit with no close has no recorded time)."""

    if not _table_present(connection, "interaction_events"):
        return []
    opened: dict[str, str] = {}
    visits: list[dict[str, Any]] = []
    for kind, payload, created_at, column_visit in connection.execute(
            "SELECT kind, payload_json, created_at, visit_id FROM interaction_events "
            "WHERE kind IN ('reader_view_opened', 'reader_view_closed') ORDER BY created_at, id"):
        try:
            data = json.loads(payload or "{}")
        except (TypeError, ValueError):
            continue
        visit = data.get("visit_id") or column_visit
        if not visit:
            continue
        if kind == "reader_view_opened":
            opened.setdefault(str(visit), str(created_at))
        elif str(visit) in opened:
            visits.append({"visit_id": str(visit), "opened_at": opened[str(visit)], "closed_at": str(created_at),
                           "active_seconds": float(data.get("active_seconds") or 0.0)})
    return visits


def _reading_marks(connection: sqlite3.Connection) -> list[tuple[str, str]]:
    """``(time, LO)`` of reading on an LO: its reading receipts and source exposures."""

    marks: list[tuple[str, str]] = []
    if _table_present(connection, "ad_reading_opportunities"):
        marks += [(str(row[0]), str(row[1])) for row in connection.execute(
            "SELECT source_written_at, learning_object_id FROM ad_reading_opportunities")]
    if _table_present(connection, "source_exposure_events"):
        marks += [(str(row[0]), str(row[1])) for row in connection.execute(
            "SELECT created_at, entity_id FROM source_exposure_events WHERE entity_type = 'learning_object' "
            "AND entity_id IS NOT NULL")]
    return sorted(marks)


def _attribute_visits(visits: Sequence[Mapping[str, Any]], marks: Sequence[tuple[str, str]]) -> tuple[dict[str, list[dict[str, Any]]], float]:
    """Each LO's visits, an even share of each, and the active seconds no LO could be named for."""

    by_lo: dict[str, list[dict[str, Any]]] = {}
    unattributed = 0.0
    for visit in visits:
        los = sorted({lo for at, lo in marks if visit["opened_at"] <= at <= visit["closed_at"]})
        if not los:
            unattributed += float(visit["active_seconds"])
            continue
        elapsed = _seconds(visit["closed_at"], visit["opened_at"]) or 0.0
        for lo in los:
            by_lo.setdefault(lo, []).append({"at": visit["closed_at"], "active": visit["active_seconds"] / len(los),
                                             "elapsed": elapsed / len(los)})
    return by_lo, unattributed


def _plan_reading(connection: sqlite3.Connection, decisions: Sequence[Mapping[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    """A reading block's start-to-end, on its frozen objective's LO (plan timing, mvp-0.44 on)."""

    if not decisions or not _table_present(connection, "attention_block_events"):
        return {}
    events: dict[str, dict[str, str]] = {}
    for block_id, kind, at in connection.execute(
            "SELECT block_id, kind, created_at FROM attention_block_events WHERE kind IN ('block_started', 'block_ended')"):
        events.setdefault(str(block_id), {}).setdefault(str(kind), str(at))
    out: dict[str, list[dict[str, Any]]] = {}
    for decision in decisions:
        block = events.get(_decision_block(decision) or "") or {}
        span = _seconds(block["block_ended"], block["block_started"]) if {"block_started", "block_ended"} <= set(block) else None
        if span is not None and decision.get("learning_object_id"):
            out.setdefault(str(decision["learning_object_id"]), []).append({"at": block["block_ended"], "elapsed": span})
    return out


def trajectories(
    connection: sqlite3.Connection,
    vault: Any,
    *,
    success_correctness: float,
    as_of: str,
    pfc_states: Mapping[str, str] | None = None,
    held_attempt_ids: frozenset[str] | set[str] = frozenset(),
) -> tuple[list[Trajectory], dict[str, Any]]:
    """Every enrolled LO's trajectory, reached or not, and the report-level timing facts."""

    pfc_states = pfc_states or {}
    ledger = _Ledger(connection, held_attempt_ids=frozenset(held_attempt_ids), version=OUTCOME_VERSION_V3)
    goal_scopes = _goal_scopes(vault)
    contracts = _contract_rows(connection)
    commitments = _commitment_times(connection, vault)
    visits_by_lo, unattributed = _attribute_visits(_visits(connection), _reading_marks(connection))
    reading_decisions: list[dict[str, Any]] = []
    if _table_present(connection, "decision_objectives"):
        reading_decisions = [dict(row) for row in connection.execute(
            "SELECT d.receipt_key, d.decision_kind, o.learning_object_id FROM decision_objectives o "
            "JOIN router_decisions d ON d.id = o.decision_id WHERE o.arm = 'reading'")]
    plan_reading = _plan_reading(connection, reading_decisions)
    candidates = set(goal_scopes) | set(commitments) | set(ledger.lo_exposures)
    out: list[Trajectory] = []
    for lo in sorted(candidates):
        goals = goal_scopes.get(lo, ())
        enrolled = _enrollment(lo, goals, contracts, commitments, ledger)
        if enrolled is None:
            continue
        enrolled_at, source = enrolled
        rows = ledger.by_lo.get(lo, [])
        success = None
        counted = latency = bound = before = 0
        active = elapsed = 0.0
        for index, row in enumerate(rows):
            if str(row["created_at"]) < enrolled_at:
                before += 1
                continue
            if row["attempt_type"] in _NON_PROBLEM:
                continue
            counted += 1
            if row.get("latency_seconds") is not None:
                latency += 1
                active += float(row["latency_seconds"])
            presented = ledger.presented_at(row)
            if row.get("plan_presentation_id") and presented != row["created_at"]:
                bound += 1
                elapsed += _seconds(str(row["created_at"]), presented) or 0.0
            completion = _completion(row, ledger, pfc_states,
                                     source_session_id=rows[index - 1]["session_id"] if index else None)
            if completion.status == DC.COMPLETED and float(completion.value or 0.0) >= success_correctness:
                success = row
                break
        end = str(success["created_at"]) if success is not None else as_of
        visits = [visit for visit in visits_by_lo.get(lo, ()) if enrolled_at <= visit["at"] <= end]
        blocks = [block for block in plan_reading.get(lo, ()) if enrolled_at <= block["at"] <= end]
        out.append(Trajectory(
            learning_object_id=lo,
            enrolled_at=enrolled_at,
            enrollment_source=source,
            goal=_pinned(goals, contracts, end),
            success_attempt_id=str(success["id"]) if success is not None else None,
            success_at=str(success["created_at"]) if success is not None else None,
            calendar_days=_days(end, enrolled_at) if success is not None else None,
            open_calendar_days=_days(end, enrolled_at) if success is None else None,
            attempts=counted,
            attempts_with_latency=latency,
            attempts_bound_to_a_presentation=bound,
            attempts_before_enrollment=before,
            active_attempt_seconds=round(active, 3),
            elapsed_attempt_seconds=round(elapsed, 3),
            reading_visits=len(visits),
            active_reading_seconds=round(sum(visit["active"] for visit in visits), 3),
            elapsed_reading_seconds=round(sum(visit["elapsed"] for visit in visits), 3),
            plan_reading_elapsed_seconds=round(sum(block["elapsed"] for block in blocks), 3),
        ))
    return out, {"unattributed_active_reading_seconds": round(unattributed, 3)}


def summary(rows: Sequence[Trajectory], facts: Mapping[str, Any]) -> dict[str, Any]:
    """The report's numbers: counts, means over those reached, and the coverage that bounds them."""

    reached = [row for row in rows if row.reached]
    timed = [row for row in reached if row.complete_latency]
    attempts = sum(row.attempts for row in rows)

    def mean(values: Sequence[float]) -> float | None:
        return round(sum(values) / len(values), 4) if values else None

    return {
        "metric_version": METRIC_VERSION,
        "label": LABEL,
        "delayed_completion_version": DC.DELAYED_COMPLETION_VERSION,
        "learning_objects": len(rows),
        "reached": len(reached),
        "unfinished": len(rows) - len(reached),
        "by_enrollment": {source: sum(1 for row in rows if row.enrollment_source == source)
                          for source in (SOURCE_GOAL, SOURCE_COMMITMENT, SOURCE_FIRST_EXPOSURE)},
        "mean_calendar_days_to_success": mean([float(row.calendar_days or 0.0) for row in reached]),
        "mean_active_minutes_to_success": mean([row.active_minutes for row in timed]),
        "mean_elapsed_minutes_to_success": mean([row.elapsed_minutes for row in reached]),
        "reached_with_complete_latency": len(timed),
        "coverage": {
            "attempts": attempts,
            "attempts_with_latency": sum(row.attempts_with_latency for row in rows),
            "attempts_bound_to_a_presentation": sum(row.attempts_bound_to_a_presentation for row in rows),
            "reading_visits": sum(row.reading_visits for row in rows),
            "unattributed_active_reading_seconds": facts.get("unattributed_active_reading_seconds", 0.0),
        },
        "note": ("Calendar and recorded minutes from enrollment to the first delayed, unexposed, unassisted success. "
                 "Active and elapsed are never blended; unfinished trajectories stay counted; lessons' durations are "
                 "not joined yet."),
    }


__all__ = ["LABEL", "METRIC_VERSION", "Trajectory", "summary", "trajectories"]
