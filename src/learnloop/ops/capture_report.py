"""``learnloop data-capture report``: is capture working? Counts and coverage for each new record.

Read-only: a read-only connection, no model call, no clock beyond the caller's "as of". For each record the
owner can see, after a week of ordinary use, how much was written, how much of what could be written was
written, and where measurement went missing (treatment-dependent censoring is the point of showing it by
arm). It estimates no effect.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping
import json
import sqlite3
from typing import Any

from learnloop.data_capture.gates import objective_receipts_on, receipts_on, serving_on
from learnloop.db.stores import data_capture as store
from learnloop.held_grades import held_for_review_attempts, pfc_assessments
from learnloop.router_objective import report as objective_report

REPORT_VERSION = "data_capture_report_v1"
#: Decisions that share another's receipt: a learner's pick from an offer reads its parent's.
_INHERITS_PARENT = frozenset({"learner_pick"})


def _present(connection: sqlite3.Connection, table: str) -> bool:
    return connection.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone() is not None


def _active_days(values: list[str]) -> int:
    return len({value[:10] for value in values if value})


def _per_day(total: float, days: int) -> float | None:
    return round(total / days, 1) if days else None


def prefilter_section(connection: sqlite3.Connection) -> dict[str, Any]:
    """A1: receipts by decision kind against the decisions they cover, and what they cost."""

    if not store.receipts_present(connection):
        return {"available": False, "reason": "this database predates migration 240"}
    decisions = Counter(str(row[0]) for row in connection.execute("SELECT decision_kind FROM router_decisions"))
    receipts = [dict(row) for row in connection.execute(
        "SELECT decision_kind, surface, session_present, scheduler_trace, considered_count, admitted_count, refused_count, "
        "code_revision, created_at FROM prefilter_receipts")]
    covered = Counter(str(row["decision_kind"]) for row in receipts)
    first = min((row["created_at"] for row in receipts), default=None)
    since = Counter()
    if first is not None:
        since = Counter(str(row[0]) for row in connection.execute(
            "SELECT decision_kind FROM router_decisions WHERE created_at >= ?", (first,)))
    payloads = connection.execute(
        "SELECT COUNT(*), COALESCE(SUM(stored_bytes), 0), COALESCE(SUM(raw_bytes), 0) FROM prefilter_payloads").fetchone()
    days = _active_days([row["created_at"] for row in receipts])
    rows_total = len(receipts) + int(payloads[0])
    stored_bytes = int(payloads[1])
    # Each receipt references its five parts; rows include the receipt rows themselves.
    referenced = 5 * len(receipts)
    return {
        "available": True,
        "receipts": len(receipts),
        "by_decision_kind": {
            kind: {
                "decisions": decisions[kind],
                "decisions_since_first_receipt": since[kind],
                "receipts": covered[kind],
                "coverage": ("inherits its parent's receipt" if kind in _INHERITS_PARENT else
                             round(covered[kind] / since[kind], 4) if since[kind] else None),
            }
            for kind in sorted(decisions)
        },
        "by_surface": dict(Counter(str(row["surface"]) for row in receipts)),
        "with_a_scheduler_trace": sum(1 for row in receipts if row["scheduler_trace"]),
        "built_with_no_session": sum(1 for row in receipts if not row["session_present"]),
        "considered_mean": round(sum(row["considered_count"] for row in receipts) / len(receipts), 1) if receipts else None,
        "refused_mean": round(sum(row["refused_count"] for row in receipts) / len(receipts), 1) if receipts else None,
        "code_revisions": sorted({str(row["code_revision"]) for row in receipts}),
        "size": {
            "parts_stored": int(payloads[0]),
            "parts_referenced": referenced,
            "bytes_stored": stored_bytes,
            "bytes_uncompressed": int(payloads[2]),
            "active_days": days,
            "rows_per_active_day": _per_day(rows_total, days),
            "bytes_per_active_day": _per_day(stored_bytes, days),
        },
    }


def measurement_section(connection: sqlite3.Connection) -> dict[str, Any]:
    """A2: objectives by arm, and each arm's measurement states (censoring by treatment, visible)."""

    if not store.objectives_present(connection):
        return {"available": False, "reason": "this database predates migration 240"}
    from learnloop.router.outcomes import fold_measurement

    objectives = store.objectives(connection)
    events = store.measurement_events(connection)
    by_arm: dict[str, Counter[str]] = {}
    reasons: Counter[str] = Counter()
    for decision_id, objective in objectives.items():
        state = fold_measurement(objective, events.get(decision_id, ()))
        arm = str(objective["arm"])
        by_arm.setdefault(arm, Counter())[state["state"]] += 1
        reasons.update(state["reasons"])
    return {
        "available": True,
        "objectives": len(objectives),
        "by_arrangement": dict(Counter(str(row["measurement"]) for row in objectives.values())),
        "by_source": dict(Counter(str(row["source"]) for row in objectives.values())),
        "states_by_arm": {arm: dict(counts) for arm, counts in sorted(by_arm.items())},
        "unavailable_reasons": dict(reasons),
        "with_an_experiment": sum(1 for row in objectives.values() if row.get("experiment_id")),
    }


def _row_count(connection: sqlite3.Connection, table: str) -> int:
    return int(connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]) if _present(connection, table) else 0


def outcome_section(connection: sqlite3.Connection, vault: Any, repository: Any) -> dict[str, Any]:
    """A2, A4: the derived outcomes under the vault's outcome version, and A4's skip reasons.

    ``r_cold_by_arm`` is one endpoint, the frozen objective's, for every arm of every decision that has
    one: a practice or insert arm reads the same record the reading, wait and stop arms do (its
    ``objective_itt``). ``action_bound_r_cold`` is each served action's own outcome, a different endpoint
    (it follows the item the arm happened to serve), kept apart so the two are never compared."""

    from learnloop.data_capture import reading_exposures
    from learnloop.router.outcomes import derive_router_outcomes, outcome_version_for, servable_items_by_learning_object

    attempt_ids = [row[0] for row in connection.execute("SELECT id FROM practice_attempts")]
    version = outcome_version_for(vault.config)
    rows = derive_router_outcomes(connection, pfc_states=pfc_assessments(connection, attempt_ids),
                                  servable_items_by_lo=servable_items_by_learning_object(vault),
                                  held_attempt_ids=held_for_review_attempts(connection), outcome_version=version,
                                  reader_exposures=reading_exposures.for_version(connection, vault, repository, version))
    by_arm: dict[str, Counter[str]] = {}
    action_bound: Counter[str] = Counter()
    completions: Counter[str] = Counter()
    skips: Counter[str] = Counter()
    no_outcome = 0
    for row in rows:
        detail = json.loads(row["detail_json"] or "{}")
        status = str(row["r_cold_status"])
        itt = detail.get("objective_itt")
        if detail.get("arm"):
            by_arm.setdefault(str(detail["arm"]), Counter())[status] += 1
        elif not detail.get("no_outcome"):
            action_bound[status] += 1
        if itt:
            by_arm.setdefault(str(itt.get("arm")), Counter())[str(itt.get("r_cold_status"))] += 1
        if detail.get("r_cold_completion"):
            completions[str(detail["r_cold_completion"])] += 1
        skips.update({str(key): int(value) for key, value in (detail.get("r_cold_skip_reasons") or {}).items()})
        no_outcome += 1 if detail.get("no_outcome") else 0
    return {
        "outcome_version": version,
        "decisions": len(rows),
        "r_cold_by_arm": {arm: dict(counts) for arm, counts in sorted(by_arm.items())},
        "action_bound_r_cold": dict(sorted(action_bound.items())),
        # The Reader's exposures reach the delayed definition through one read (the receipts plus the activity not yet
        # swept, so the labels above are the same either way); AD's own only under its forecast logging.
        "reading_exposure_receipts": _row_count(connection, "reading_exposure_receipts"),
        "reader_exposures_not_yet_swept": len(reading_exposures.not_yet_swept(connection, vault, repository)),
        "ad_reading_receipts": _row_count(connection, "ad_reading_opportunities"),
        "completions": dict(completions),
        "r_cold_skip_reasons": dict(skips),
        "no_frozen_objective": no_outcome,
    }


def time_section(connection: sqlite3.Connection, vault: Any, repository: Any, *, as_of: str,
                 success_correctness: float) -> dict[str, Any]:
    """A3: the first-delayed-success proxy."""

    from learnloop.data_capture import reading_exposures
    from learnloop.router.first_delayed_success import summary, trajectories

    attempt_ids = [row[0] for row in connection.execute("SELECT id FROM practice_attempts")]
    rows, facts = trajectories(connection, vault, success_correctness=success_correctness, as_of=as_of,
                               pfc_states=pfc_assessments(connection, attempt_ids),
                               held_attempt_ids=held_for_review_attempts(connection),
                               reader_exposures=reading_exposures.read(connection, vault, repository))
    return summary(rows, facts)


def floor_and_pick_section(connection: sqlite3.Connection) -> dict[str, Any]:
    """A5, A6, A8: the not_ready floor's draws, the delayed picks' ties, the thin supports."""

    not_ready = {"decisions": 0, "drawn": 0, "not_the_rules_pick": 0}
    for row in connection.execute(
            "SELECT chosen_ref, propensity_kind, detail_json FROM router_decisions "
            "WHERE decision_kind IN ('plan_block', 'plan_interrupt') AND detail_json LIKE '%\"decided_by\":\"not_ready\"%'"):
        not_ready["decisions"] += 1
        detail = json.loads(row["detail_json"] or "{}")
        if row["propensity_kind"] == "exact":
            not_ready["drawn"] += 1
            if row["chosen_ref"] != (detail.get("mixture") or {}).get("staged_ref"):
                not_ready["not_the_rules_pick"] += 1
    picks = {"checks": 0, "with_a_pick_receipt": 0, "exact_ties": 0}
    if _present(connection, "commitment_versions"):
        for row in connection.execute(
                "SELECT provenance_json FROM commitment_versions WHERE provenance_json LIKE '%\"via\"%'"):
            provenance: Mapping[str, Any] = json.loads(row[0] or "{}") or {}
            if provenance.get("via") not in ("lesson", "measurement"):
                continue
            picks["checks"] += 1
            pick = provenance.get("pick")
            if pick:
                picks["with_a_pick_receipt"] += 1
                picks["exact_ties"] += 1 if int(pick.get("n") or 0) > 1 else 0
    thin = 0
    if _present(connection, "policy_experiment_assignments"):
        thin = connection.execute(
            "SELECT COUNT(*) FROM policy_experiment_assignments WHERE detail_json LIKE '%\"thin_support\":true%'").fetchone()[0]
    return {"not_ready_floor": not_ready, "delayed_picks": picks, "thin_support_assignments": int(thin)}


def _goals(vault: Any) -> list[Any]:
    goals = getattr(vault, "goals", None) or ()
    return list(goals.values() if isinstance(goals, Mapping) else goals)


def build_report(connection: sqlite3.Connection, vault: Any, repository: Any, *, as_of: str,
                 success_correctness: float) -> dict[str, Any]:
    return {
        "report_version": REPORT_VERSION,
        "as_of": as_of,
        "algorithm_version": vault.config.algorithms.algorithm_version,
        "switches": {"receipts": receipts_on(vault.config), "serving": serving_on(vault.config)},
        "prefilter_receipts": prefilter_section(connection),
        "measurements": measurement_section(connection),
        "outcomes": outcome_section(connection, vault, repository),
        "first_delayed_success": time_section(connection, vault, repository, as_of=as_of, success_correctness=success_correctness),
        "floor_and_picks": floor_and_pick_section(connection),
        "router_objective": {"receipts": objective_receipts_on(vault.config),
                             **objective_report.section(connection, goal_ids=[str(goal.id) for goal in _goals(vault)])},
    }


def lines(report: Mapping[str, Any]) -> list[str]:
    """The plain-text report."""

    out = [f"Data capture ({report['algorithm_version']}, as of {report['as_of']})",
           f"  receipts {'on' if report['switches']['receipts'] else 'off'}, "
           f"serving changes {'on' if report['switches']['serving'] else 'off'}"]
    pre = report["prefilter_receipts"]
    if pre.get("available"):
        size = pre["size"]
        out.append(f"Prefilter receipts: {pre['receipts']} ({pre['with_a_scheduler_trace']} with a scheduler trace, "
                   f"{pre['built_with_no_session']} built with no session)")
        for kind, row in pre["by_decision_kind"].items():
            out.append(f"  {kind}: {row['receipts']} of {row['decisions_since_first_receipt']} since the first "
                       f"receipt (coverage {row['coverage']})")
        out.append(f"  stored: {size['parts_stored']} parts for {size['parts_referenced']} references, "
                   f"{size['bytes_stored']} bytes; {size['rows_per_active_day']} rows and "
                   f"{size['bytes_per_active_day']} bytes per active day")
    else:
        out.append(f"Prefilter receipts: unavailable ({pre.get('reason')})")
    measured = report["measurements"]
    if measured.get("available"):
        out.append(f"Measurements: {measured['objectives']} frozen objectives, {measured['by_arrangement']}")
        for arm, counts in measured["states_by_arm"].items():
            out.append(f"  {arm}: {counts}")
        if measured["unavailable_reasons"]:
            out.append(f"  unavailable because: {measured['unavailable_reasons']}")
    outcomes = report["outcomes"]
    out.append(f"Outcomes ({outcomes['outcome_version']}): {outcomes['decisions']} decisions, "
               f"{outcomes['no_frozen_objective']} with no frozen objective")
    out.append("  R_cold on the frozen objective, by arm:")
    for arm, counts in outcomes["r_cold_by_arm"].items():
        out.append(f"    {arm}: {counts}")
    out.append(f"  R_cold of the served action (action-bound, not comparable with the above): {outcomes['action_bound_r_cold']}")
    out.append(f"  reading exposures on record: {outcomes['reading_exposure_receipts']}, "
               f"not yet swept: {outcomes['reader_exposures_not_yet_swept']} (read either way)")
    if outcomes["completions"]:
        out.append(f"  delayed completions: {outcomes['completions']}")
    first = report["first_delayed_success"]
    out.append(f"Time ({first['label']}): {first['reached']} of {first['learning_objects']} reached; "
               f"{first['unfinished']} unfinished")
    out.append(f"  mean {first['mean_calendar_days_to_success']} calendar days, {first['mean_active_minutes_to_success']} "
               f"active minutes ({first['reached_with_complete_latency']} with complete latency), "
               f"{first['mean_elapsed_minutes_to_success']} elapsed minutes")
    coverage = first["coverage"]
    out.append(f"  coverage: {coverage['attempts_with_latency']} of {coverage['attempts']} attempts timed, "
               f"{coverage['attempts_bound_to_a_presentation']} bound to a presentation, "
               f"{coverage['unattributed_active_reading_seconds']} active reading seconds unattributed")
    floor = report["floor_and_picks"]
    out.append(f"Not-ready floor: {floor['not_ready_floor']}; delayed picks: {floor['delayed_picks']}; "
               f"thin-support assignments: {floor['thin_support_assignments']}")
    out.extend(objective_report.lines(report["router_objective"]))
    return out



__all__ = ["REPORT_VERSION", "build_report", "lines"]
