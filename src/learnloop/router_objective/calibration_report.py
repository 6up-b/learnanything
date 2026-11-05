"""RO5 §9: the calibration section of ``learnloop router objective-report``: each arm per day with what it costs in
minutes, the price's regime, the return model, the weight's scores, the goal-date read and the probe-versus-continue
contrast from FG1's ``no_intervention`` floor. Read-only; no model call.

* **The stop coin**: draws, offers (``offer_stop``) and next blocks presented over a drawn stop (``present_next``) per
  day, and their minutes: an accepted randomized offer forgoes at most the plan's suggested remainder at it (an
  upper bound, labelled), a presented block adds its estimate.
* **The checks**: assigned, administered and completed per day, noncompletion by reason, how often a check displaced
  a targeted question, the minutes it added net of the question it replaced, the generation needs it raised and the
  unseen items it used up (its cost in generation), the completion gap.
* **The open picks**: their assignments (the full section is ``learnloop data-capture report``'s); no minutes.
* **The floor** (§9 item 5): FG1's itemless decisions with ``no_intervention`` in their support: how many, the share
  drawn to it and to the probe, and each arm's delayed cold outcome (``router_outcomes.r_cold_value``), observed
  and inverse-propensity weighted, labelled exploratory. A typical day with none on the floor is the trigger the spec
  names for a higher no-probe share (recorded as a follow-up, not built).
"""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Mapping
import json
from statistics import median
from typing import Any

from learnloop.router_objective import assignments as A
from learnloop.router_objective import checks as C
from learnloop.router_objective import stop_coin as SC

VERSION = "ro5_calibration_report_v1"
FLOOR_LABEL = "exploratory: the floor's draws are randomized, the outcomes delayed and sparse"


def _local(stamp: str) -> str:
    from learnloop.clock import parse_utc

    moment = parse_utc(str(stamp))
    return moment.astimezone().date().isoformat() if moment is not None else str(stamp)[:10]


def stop_coin_section(connection: Any) -> dict[str, Any]:
    coins = A.rows(connection, A.STOP_COIN)
    days: dict[str, dict[str, Any]] = defaultdict(lambda: {"draws": 0, "offers": 0, "presented_over_stop": 0,
                                                          "policy": 0, "minutes_forgone_upper": 0.0,
                                                          "minutes_added": 0.0})
    responses = SC._decision_stop_responses(connection)
    for coin in coins:
        detail = coin["detail"]
        day = days[_local(coin["created_at"])]
        day["draws"] += 1
        availability = detail.get("availability") or {}
        if coin["variant"] == SC.OFFER_STOP:
            day["offers"] += 1
            if responses.get(str(coin["unit_id"])) != "overridden":
                mbar = float(availability.get("remembered_minutes") or 0.0)
                spent = float(availability.get("session_minutes") or 0.0)
                day["minutes_forgone_upper"] += max(mbar - spent, 0.0)
        elif coin["variant"] == SC.PRESENT_NEXT and detail.get("u_next") is not None:
            day["presented_over_stop"] += 1
            trace = connection.execute("SELECT trace_json FROM router_objective_traces WHERE decision_id = ?",
                                       (coin["unit_id"],)).fetchone()
            if trace is not None:
                served = (json.loads(trace[0]).get("candidates") or {}).get(str(detail.get("served"))) or {}
                day["minutes_added"] += float(served.get("minutes") or 0.0)
        else:
            day["policy"] += 1
    with_response = Counter(responses.get(str(coin["unit_id"]), "open") for coin in coins
                            if coin["variant"] == SC.OFFER_STOP)
    return {"draws": len(coins), "by_arm": dict(Counter(str(coin["variant"]) for coin in coins)),
            "offer_responses": dict(with_response), "days": {day: dict(value) for day, value in sorted(days.items())},
            "minutes_label": "forgone is an upper bound (the plan's suggested remainder at each accepted randomized "
                             "offer); added is each presented block's estimate"}


def checks_section(connection: Any, *, through: str) -> dict[str, Any]:
    resolved = C.resolve(connection, through=through)
    done = C.administered(connection)
    days: dict[str, dict[str, Any]] = defaultdict(lambda: {"assigned": 0, "administered": 0, "completed": 0,
                                                          "displaced_a_targeted_question": 0, "net_minutes": 0.0,
                                                          "not_completed": Counter()})
    for entry in resolved:
        day = days[entry.local_date]
        day["assigned"] += 1
        planned = done.get(entry.assignment_id)
        if planned is not None:
            day["administered"] += 1
            day["net_minutes"] += float(planned.get("net_minutes") or 0.0)
            if planned.get("replaced"):
                day["displaced_a_targeted_question"] += 1
        if entry.status == "completed":
            day["completed"] += 1
        else:
            day["not_completed"][entry.status] += 1
    needs = 0
    eligible_days = []
    for row in A.rows(connection, A.CHECK):
        if row["unit_id"].count(":") == 1:
            needs += len(row["detail"].get("generation_needs") or {})
            eligible_days.append(int(row["detail"].get("eligible_count") or 0))
    return {"days": {day: {**{k: v for k, v in value.items() if k != "not_completed"},
                           "not_completed": dict(value["not_completed"])} for day, value in sorted(days.items())},
            "completion": C.completion(connection, through=through),
            "generation": {"needs_raised": needs, "unseen_items_used": sum(1 for _ in done),
                           "eligible_topics_per_day_median": median(eligible_days) if eligible_days else None},
            "outcomes": {"completed": sum(1 for e in resolved if e.status == "completed"),
                         "successes": sum(1 for e in resolved if e.status == "completed" and e.outcome == 1.0)}}


def floor_section(connection: Any) -> dict[str, Any]:
    """§9 item 5: the probe-versus-continue contrast read from FG1's ``no_intervention`` floor."""

    rows = [dict(row) for row in connection.execute(
        "SELECT d.id, d.chosen_ref, d.propensity, d.created_at, d.candidates_json, o.r_cold_value, o.r_cold_status "
        "FROM router_decisions d LEFT JOIN router_outcomes o ON o.decision_id = d.id "
        "WHERE d.decision_kind = 'plan_interrupt' AND d.candidates_json LIKE '%no_intervention%' "
        "ORDER BY d.created_at, d.id")]
    arms: dict[str, dict[str, Any]] = defaultdict(lambda: {"decisions": 0, "observed": 0, "mean_r_cold": None,
                                                          "ipw_mean_r_cold": None, "_v": [], "_w": []})
    days = Counter()
    for row in rows:
        arm = "no_intervention" if row["chosen_ref"] == "no_intervention" else (
            "probe" if row["chosen_ref"] in ("insert_now", "continue_current") else str(row["chosen_ref"]))
        entry = arms[arm]
        entry["decisions"] += 1
        days[_local(row["created_at"])] += 1 if arm == "no_intervention" else 0
        if row["r_cold_status"] == "observed" and row["r_cold_value"] is not None:
            entry["observed"] += 1
            entry["_v"].append(float(row["r_cold_value"]))
            entry["_w"].append(1.0 / max(float(row["propensity"] or 1.0), 1e-9))
    out_arms = {}
    for arm, entry in arms.items():
        values, weights = entry.pop("_v"), entry.pop("_w")
        if values:
            entry["mean_r_cold"] = round(sum(values) / len(values), 4)
            entry["ipw_mean_r_cold"] = round(sum(v * w for v, w in zip(values, weights)) / sum(weights), 4)
        out_arms[arm] = dict(entry)
    total = len(rows)
    active_days = sorted({_local(row["created_at"]) for row in rows})
    typical = median([days.get(day, 0) for day in active_days]) if active_days else 0
    return {"decisions": total, "arms": out_arms,
            "no_intervention_share": round(out_arms.get("no_intervention", {}).get("decisions", 0) / total, 4)
            if total else None,
            "no_intervention_per_active_day_median": typical, "label": FLOOR_LABEL,
            "higher_no_probe_share": ("follow-up: the floor's count is zero on a typical day" if typical == 0
                                      else "not needed: the floor has draws on a typical day"),
            "leave_alone_arm": "not built (spec §12 D1)"}


def build(connection: Any, vault: Any, *, now: str, weight: Mapping[str, Any] | None = None) -> dict[str, Any]:
    from learnloop.router_objective import goal_read as G
    from learnloop.router_objective import picks as PK
    from learnloop.router_objective import scores as S
    from learnloop.router_objective import weight as W

    through = _local(now)
    details = S.scores(connection, vault.config, at=now) if A.rows(connection, A.CHECK) else []
    posterior = W.posterior([detail.scored for detail in details], W.Seeds.from_config(vault.config), at=now)
    unique = W.unique_assessments((key, detail.scored.decision_id) for detail in details for key in detail.assessments)
    kappa = SC.handed_over(connection, vault.config)
    slope_rows = SC.return_rows(connection, gap_minutes=float(vault.config.router_objective.session_gap_minutes))
    return {
        "version": VERSION,
        "stop_coin": stop_coin_section(connection),
        "checks": checks_section(connection, through=through),
        "open_picks": {"assignments": dict(Counter(str(row["variant"]) for row in A.rows(connection, A.PICK))),
                       "minutes": 0.0, "detail": "learnloop data-capture report (open_picks)",
                       "version": PK.VERSION},
        "price": {"regime": "posterior" if kappa is not None else "seed", "posterior": kappa},
        "return_model": {**SC.fit_return_slope(slope_rows, float(vault.config.router_objective.return_slope_prior_sd)
                                               ).as_dict(), "sessions": len(slope_rows)},
        "weight": {"closed_scores": sum(1 for detail in details if detail.scored.value is not None),
                   "censored": dict(Counter(detail.scored.reason for detail in details
                                            if detail.scored.value is None)),
                   "unique_completed_assessments": unique, "posterior": posterior.as_dict(),
                   "w": W.weight(posterior.p, W.Seeds.from_config(vault.config)),
                   "moved": posterior.source == "posterior", "served_w": (weight or {}).get("w")},
        "goal_read": G.read(connection, vault, now=now),
        "floor": floor_section(connection),
    }


def lines(report: Mapping[str, Any]) -> list[str]:
    coin, checks, weight = report["stop_coin"], report["checks"], report["weight"]
    out = [f"calibration ({report['version']}): stop coin {coin['draws']} draws {coin['by_arm']}, offer responses "
           f"{coin['offer_responses']}"]
    for day, value in coin["days"].items():
        out.append(f"- {day}: coin draws {value['draws']}, offers {value['offers']}, next block over a stop "
                   f"{value['presented_over_stop']}, minutes forgone <= {value['minutes_forgone_upper']:.1f}, "
                   f"added {value['minutes_added']:.1f}")
    for day, value in checks["days"].items():
        out.append(f"- {day}: checks assigned {value['assigned']}, administered {value['administered']}, completed "
                   f"{value['completed']}, displaced a targeted question {value['displaced_a_targeted_question']}, "
                   f"net minutes {value['net_minutes']:.1f}, not completed {value['not_completed']}")
    out.append(f"checks: completion {checks['completion']['rate']} ({checks['completion']['days_without_session']} days "
               f"without a session), generation {checks['generation']}")
    out.append(f"price: {report['price']['regime']}; return model {report['return_model']['source']} "
               f"(n {report['return_model']['n']})")
    out.append(f"weight: closed scores {weight['closed_scores']}, censored {weight['censored']}, unique assessments "
               f"{weight['unique_completed_assessments']}, w {weight['w']:.3f} (moved: {weight['moved']})")
    floor = report["floor"]
    out.append(f"floor (§9 item 5): {floor['decisions']} decisions, no_intervention share "
               f"{floor['no_intervention_share']}, arms {floor['arms']}; {floor['higher_no_probe_share']}")
    reads = report["goal_read"]["reads"]
    out.append(f"goal-date read: {len(reads)} goals; calibration n {report['goal_read']['calibration']['n']}; ready "
               f"reads {report['goal_read']['ready_reads']['n']} (self-selected)")
    return out


__all__ = ["FLOOR_LABEL", "VERSION", "build", "checks_section", "floor_section", "lines", "stop_coin_section"]
