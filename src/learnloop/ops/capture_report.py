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

from learnloop.causal_activity_policy import DISCRIMINATING_OUTCOMES
from learnloop.data_capture.gates import objective_receipts_on, receipts_on, serving_on
from learnloop.db.stores import data_capture as store
from learnloop.db.stores import hypothesis_marks as marks_store
from learnloop.followup_serve import marks as marks_rules
from learnloop.followup_serve.gates import hypothesis_marks_on
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


PROBE_AGREEMENT_LABEL = ("conditional on being observed: only causes the learner marked and a probe answer measured, "
                         "not the sensor's accuracy on anything else")
DELAYED_AGREEMENT_LABEL = ("conditional on being observed: only the opinion held before a later delayed answer on the topic; "
                           "a repair in between can move it, and marks made after that answer are reported apart, unscored")
#: How a marked answer's opinion reads against a delayed answer: the first scored against a miss, the third
#: against a success, the others reported and never scored (a delayed answer can't say which cause it was).
_OPINIONS = ("named_a_gap", "partly", "ruled_the_list_out", "rejected_some_causes")
POSITION_LABEL = ("conditional on being observed: only lists that were displayed and marks the learner chose to give; "
                  "the order is shuffled, so a difference by position reads as position bias")


def _exposure_coverage(connection: sqlite3.Connection, exposures: list[dict[str, Any]], links: list[dict[str, Any]]) -> dict[str, Any]:
    """The coverage row: how many attempts with causes since the first display had a list displayed, and what it costs."""

    first = min((str(row["created_at"]) for row in exposures), default=None)
    with_causes: set[str] = set()
    if first is not None and _present(connection, "causal_hypotheses"):
        with_causes = {str(row[0]) for row in connection.execute(
            "SELECT DISTINCT attempt_id FROM causal_hypotheses WHERE status <> 'open_set' AND created_at >= ?", (first,))}
    displayed = {str(row["attempt_id"]) for row in exposures}
    days = _active_days([str(row["created_at"]) for row in exposures])
    size = sum(len(str(value).encode("utf-8")) for row in exposures for value in row.values() if value is not None)
    return {
        "exposures": len(exposures),
        "by_surface": dict(Counter(str(row["surface"]) for row in exposures)),
        "attempts_displayed": len(displayed),
        "attempts_with_causes_since_first_display": len(with_causes),
        "coverage": round(len(displayed & with_causes) / len(with_causes), 4) if with_causes else None,
        "linked_to_a_later_probe_answer": len(links),
        "rows_per_active_day": _per_day(len(exposures), days),
        "bytes_per_active_day": _per_day(size, days),
    }


def _latest_marks(marks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_attempt: dict[str, list[dict[str, Any]]] = {}
    for row in marks:
        by_attempt.setdefault(str(row["attempt_id"]), []).append(row)
    return [dict(row) for rows in by_attempt.values() for row in marks_rules.latest_marks(rows).values()]


def _hypothesis_keys(connection: sqlite3.Connection) -> dict[str, str]:
    """Each hypothesis version's stable identity."""

    return {str(row[0]): str(row[1]) for row in connection.execute("SELECT id, episode_key FROM causal_hypotheses")}


def _observations(connection: sqlite3.Connection) -> dict[str, dict[str, Any]]:
    """Per factor, its newest answered observation, with what it measured and classified as stable identities.

    ``independent`` is the receipt's own field: admission is another question (a clean answer to a question
    that didn't discriminate is not admitted), and only an assessed clean answer reads as independent.
    ``covered``: every cause of the list was put at risk, what a no-match needs before it says anything."""

    if not _present(connection, "causal_discriminating_observations"):
        return {}
    keys = _hypothesis_keys(connection)
    out: dict[str, dict[str, Any]] = {}
    for row in connection.execute(
        "SELECT factor_id, outcome, classified_as_json, admissible_as_independent, declared_keys_observed, detail_json "
        "FROM causal_discriminating_observations WHERE probe_attempt_id IS NOT NULL ORDER BY created_at, id"
    ):
        detail = json.loads(row["detail_json"] or "{}")
        out[str(row["factor_id"])] = {
            "outcome": str(row["outcome"]),
            "classified": {keys.get(str(value), str(value)) for value in json.loads(row["classified_as_json"] or "[]")},
            "measured": {keys.get(str(value), str(value)) for value in detail.get("measured_hypothesis_ids") or []},
            "independent": row["admissible_as_independent"] == 1,
            "covered": bool(row["declared_keys_observed"]),
        }
    return out


def _probe_agreement(connection: sqlite3.Connection, latest: list[dict[str, Any]]) -> dict[str, Any]:
    """Marks against what a probe's answer classified. Counted apart by whether the answer was independent
    and whether the mark came before it, since a learner who has answered knows more."""

    observations = _observations(connection)
    table: dict[str, dict[str, int]] = {}
    not_discriminating = not_measured = no_probe = none_uncovered = 0
    scored = {"independent_answer": [0, 0], "not_independent_answer": [0, 0]}
    for row in latest:
        factor = row.get("factor_id")
        observation = observations.get(str(factor)) if factor else None
        if observation is None:
            no_probe += 1
            continue
        if observation["outcome"] not in DISCRIMINATING_OUTCOMES:
            not_discriminating += 1
            continue
        mark = str(row["mark"])
        no_match = observation["outcome"] == "no_bundle_matched"
        if mark == marks_rules.NONE_OF_THESE:
            if no_match and not observation["covered"]:
                # A cause the question never put at risk could still be the one: this says nothing about the list.
                none_uncovered += 1
                continue
            supported = no_match
        elif str(row["hypothesis_key"]) not in observation["measured"]:
            not_measured += 1
            continue
        else:
            supported = str(row["hypothesis_key"]) in observation["classified"]
        timing = "marked_after_the_answer" if row.get("probe_answered") else "marked_before_the_answer"
        independence = "independent_answer" if observation["independent"] else "not_independent_answer"
        verdict = "probe_supports" if supported else "probe_does_not_support"
        slot = table.setdefault(f"{mark}|{verdict}|{independence}|{timing}", {"marks": 0})
        slot["marks"] += 1
        # "Partly" is neither side of agreement: it is reported, never scored.
        if mark in {marks_rules.MY_GAP, marks_rules.NONE_OF_THESE}:
            scored[independence][0 if supported else 1] += 1
        elif mark == marks_rules.NOT_IT:
            scored[independence][1 if supported else 0] += 1
    return {
        "label": PROBE_AGREEMENT_LABEL,
        **{
            f"{name}s": {
                "agree": agree,
                "disagree": disagree,
                "agreement": round(agree / (agree + disagree), 4) if agree + disagree else None,
            }
            for name, (agree, disagree) in scored.items()
        },
        "by_mark_outcome_independence_and_timing": {
            key: value["marks"] for key, value in sorted(table.items())
        },
        "marks_with_no_probe_answer": no_probe,
        "marks_on_a_cause_the_probe_did_not_measure": not_measured,
        "marks_on_a_probe_that_did_not_discriminate": not_discriminating,
        "none_of_these_on_a_probe_that_did_not_measure_every_cause": none_uncovered,
    }


def _rejected_the_whole_list(latest: Mapping[str | None, Mapping[str, Any]], rows: list[Mapping[str, Any]],
                             keys: Mapping[str, str]) -> bool:
    """None of these, or Not it on every cause of the list as the newest mark displayed it. Marks are optional
    per cause, so a cause left unmarked (or added since) was not rejected."""

    if marks_rules.NONE_OF_THESE in {str(row["mark"]) for row in latest.values()}:
        return True
    rejected = {key for key, row in latest.items() if row["mark"] == marks_rules.NOT_IT}
    displayed = marks_store.decode_ids(rows[-1].get("display_order_json")) if rows else []
    return bool(displayed) and all(keys.get(version) in rejected for version in displayed)


def _opinion_reading(rows: list[Mapping[str, Any]], keys: Mapping[str, str]) -> str | None:
    """One attempt's opinion in ``rows`` (oldest first), or None with nothing held: one of ``_OPINIONS``."""

    latest = marks_rules.latest_marks(rows)
    if not latest:
        return None
    held = {str(row["mark"]) for row in latest.values()}
    if marks_rules.MY_GAP in held:
        return "named_a_gap"
    if marks_rules.PARTLY in held:
        return "partly"
    return "ruled_the_list_out" if _rejected_the_whole_list(latest, rows, keys) else "rejected_some_causes"


def _delayed_agreement(connection: sqlite3.Connection, vault: Any, repository: Any, marks: list[dict[str, Any]],
                       success_correctness: float) -> dict[str, Any]:
    """Marks against delayed answers on the topic under the shared definition: the opinion held before the first
    delayed answer that had one, so the answer is what it predicted and hindsight replaces nothing. A learner
    naming a gap agrees with a later miss; one ruling the whole list out agrees with a later success. An opinion
    formed or changed after a delayed answer is counted apart against the newest answer it could have seen."""

    from learnloop.data_capture import reading_exposures
    from learnloop.router.outcomes import delayed_outcomes_after

    by_attempt: dict[str, list[dict[str, Any]]] = {}
    learning_objects: dict[str, str] = {}
    for row in marks:
        by_attempt.setdefault(str(row["attempt_id"]), []).append(row)
        learning_objects[str(row["attempt_id"])] = str(row["learning_object_id"])

    def table() -> dict[str, dict[str, int]]:
        return {name: {"later_success": 0, "later_miss": 0} for name in _OPINIONS}

    apart = table()
    out: dict[str, Any] = {"label": DELAYED_AGREEMENT_LABEL, "agree": 0, "disagree": 0, "agreement": None, **table(),
                           "marked_answers_with_no_later_delayed_answer": 0, "marked_after_a_delayed_answer": apart}
    if not by_attempt:
        return out
    attempt_ids = [row[0] for row in connection.execute("SELECT id FROM practice_attempts")]
    outcomes = delayed_outcomes_after(
        connection, learning_objects, pfc_states=pfc_assessments(connection, attempt_ids),
        held_attempt_ids=frozenset(held_for_review_attempts(connection)),
        reader_exposures=reading_exposures.read(connection, vault, repository),
    )
    keys = _hypothesis_keys(connection)

    def later(outcome: Mapping[str, Any]) -> str:
        success = outcome["completion"] == "completed" and float(outcome["value"] or 0.0) >= success_correctness
        return "later_success" if success else "later_miss"

    for attempt_id, rows in sorted(by_attempt.items()):
        found = outcomes.get(attempt_id) or []
        scored = False
        for outcome in found:
            reading = _opinion_reading([row for row in rows if str(row["created_at"]) < str(outcome["presented_at"])], keys)
            if reading is None:
                continue
            scored = True
            out[reading][later(outcome)] += 1
            if reading == "named_a_gap":
                out["agree" if later(outcome) == "later_miss" else "disagree"] += 1
            elif reading == "ruled_the_list_out":
                out["agree" if later(outcome) == "later_success" else "disagree"] += 1
            break
        final = _opinion_reading(rows, keys)
        if final is None:
            continue
        if not scored:
            out["marked_answers_with_no_later_delayed_answer"] += 1
        seen = [outcome for outcome in found if str(outcome["presented_at"]) <= str(rows[-1]["created_at"])]
        if seen:
            apart[final][later(seen[-1])] += 1
    decided = out["agree"] + out["disagree"]
    out["agreement"] = round(out["agree"] / decided, 4) if decided else None
    return out


def _position_rates(exposures: list[dict[str, Any]], latest: list[dict[str, Any]]) -> dict[str, Any]:
    """Mark rates by the position each cause held on the marks panel: shown once per attempt and cause."""

    shown: Counter[int] = Counter()
    seen: set[tuple[str, str]] = set()
    for row in exposures:
        if not row.get("order_seed"):
            continue
        for position, version in enumerate(marks_store.decode_ids(row["hypothesis_version_ids_json"]), start=1):
            if (str(row["attempt_id"]), version) not in seen:
                seen.add((str(row["attempt_id"]), version))
                shown[position] += 1
    marked: dict[int, Counter[str]] = {}
    for row in latest:
        if row.get("display_position"):
            marked.setdefault(int(row["display_position"]), Counter())[str(row["mark"])] += 1
    positions = sorted(set(shown) | set(marked))
    return {
        "label": POSITION_LABEL,
        "by_position": {
            str(position): {
                "shown": shown[position],
                "marks": dict(marked.get(position, Counter())),
                "mark_rate": (round(sum(marked.get(position, Counter()).values()) / shown[position], 4)
                              if shown[position] else None),
            }
            for position in positions
        },
    }


def hypothesis_marks_section(connection: sqlite3.Connection, vault: Any, repository: Any, *,
                             success_correctness: float) -> dict[str, Any]:
    """FG1c (spec §7) and row 6 of the router objective's logging: the exposure table's coverage, and how far
    the marks can be trusted, each labelled as conditional on being observed. It estimates no effect."""

    if not marks_store.present(connection):
        return {"available": False, "reason": "this database predates migration 242"}
    exposures = marks_store.all_exposures(connection)
    marks = marks_store.all_marks(connection)
    latest = _latest_marks(marks)
    return {
        "available": True,
        "exposure_coverage": _exposure_coverage(connection, exposures, marks_store.probe_links(connection)),
        "marks": {
            "rows": len(marks),
            "attempts": len({str(row["attempt_id"]) for row in marks}),
            "latest_by_mark": dict(Counter(str(row["mark"]) for row in latest)),
            "changes_of_mind": len(marks) - len({(str(row["attempt_id"]), row["hypothesis_key"]) for row in marks}),
            "with_free_text": sum(1 for row in latest if row.get("free_text")),
        },
        "agreement_with_probe_outcomes": _probe_agreement(connection, latest),
        "agreement_with_delayed_performance": _delayed_agreement(connection, vault, repository, marks, success_correctness),
        "mark_rates_by_display_position": _position_rates(exposures, latest),
    }


def build_report(connection: sqlite3.Connection, vault: Any, repository: Any, *, as_of: str,
                 success_correctness: float) -> dict[str, Any]:
    from learnloop.router_objective_switches import calibration_tag

    extra: dict[str, Any] = {}
    if calibration_tag(vault.config):
        # Router objective RO5 (spec §9 item 6): the open picks' assignment, eligibility, gate reasons,
        # administration, completion and intervening instruction, each apart; agreement labelled.
        from learnloop.router_objective import picks as ro5_picks

        extra["open_picks"] = ro5_picks.section(connection)
    return {**{
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
        "hypothesis_marks": {
            "switch_on": hypothesis_marks_on(vault.config),
            **hypothesis_marks_section(connection, vault, repository, success_correctness=success_correctness),
        },
    }, **extra}


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
    marks = report["hypothesis_marks"]
    if marks.get("available"):
        coverage = marks["exposure_coverage"]
        out.append(f"Hypothesis-list exposures: {coverage['exposures']} by surface {coverage['by_surface']}; "
                   f"{coverage['attempts_displayed']} attempts displayed of "
                   f"{coverage['attempts_with_causes_since_first_display']} with causes since the first display "
                   f"(coverage {coverage['coverage']}); {coverage['linked_to_a_later_probe_answer']} linked to a later "
                   f"probe answer; {coverage['rows_per_active_day']} rows and {coverage['bytes_per_active_day']} bytes per active day")
        counts = marks["marks"]
        out.append(f"Marks on possible causes: {counts['rows']} rows on {counts['attempts']} attempts, latest "
                   f"{counts['latest_by_mark']}, {counts['changes_of_mind']} changes of mind, {counts['with_free_text']} with free text")
        probe = marks["agreement_with_probe_outcomes"]
        clean, exposed = probe["independent_answers"], probe["not_independent_answers"]
        out.append(f"  with probe outcomes: agreement {clean['agreement']} on independent answers ({clean['agree']} agree, "
                   f"{clean['disagree']} disagree), {exposed['agreement']} on answers given after the causes were shown "
                   f"({exposed['agree']} agree, {exposed['disagree']} disagree); {probe['label']}")
        delayed = marks["agreement_with_delayed_performance"]
        afterwards = sum(sum(row.values()) for row in delayed["marked_after_a_delayed_answer"].values())
        out.append(f"  with delayed performance: agreement {delayed['agreement']} ({delayed['agree']} agree, "
                   f"{delayed['disagree']} disagree); {afterwards} marked or changed after a delayed answer, unscored; "
                   f"{delayed['label']}")
        position = marks["mark_rates_by_display_position"]
        out.append(f"  by display position: {position['by_position']}; {position['label']}")
    else:
        out.append(f"Marks on possible causes: unavailable ({marks.get('reason')})")
    picks = report.get("open_picks")
    if picks is not None and picks.get("available"):
        out.append(f"Open picks (router objective RO5 §9 item 6): assigned {picks['assignments']}, eligibility "
                   f"{picks['eligibility']}, administered {picks['administered']}, completed {picks['completed']}")
        out.append(f"  gate reasons {picks['gate_reasons']}; intervening instruction (reveals) "
                   f"{picks['intervening_instruction_reveals']}")
        agreement = picks["pick_probe_agreement"]
        out.append(f"  pick-probe agreement: open {agreement['open']}, resolve {agreement['resolve']}; "
                   f"{agreement['label']}")
        delayed = picks["delayed_performance"]
        out.append(f"  delayed performance: open {delayed['open']}, resolve {delayed['resolve']}; {delayed['label']}")
    return out



__all__ = ["REPORT_VERSION", "build_report", "lines"]
