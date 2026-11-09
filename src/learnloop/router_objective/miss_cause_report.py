"""``learnloop data-capture report``'s slip-or-gap section (``docs/specs/spec_slip_vs_gap_v1.md`` §3, SG1 item 4).
Read-only, and nothing reads it back.

Over the router decisions whose lesson offer froze a miss-cause sensor (SG1, on the offer's record):

* **cause classes among offers**: the sensors' statuses, and the expected number of offers per cause class (the sum of
  each diagnosed offer's ``p_gap``, ``p_slip``, ``p_unknown``: a probability is never rounded into a class);
* **how often the lesson won, by class**: the same sums over the decisions that drew the offer, and their ratio;
* **later cold results, by class**: the first later qualifying cold outcome on the offer's topic
  (``lesson_weight.qualifying_outcomes``), its grade averaged with each offer's class probabilities as weights, for all
  offers and for the ones that won. Labelled observational (:data:`miss_cause.OBSERVATIONAL`): nothing here is
  randomized by cause, so no line says what a lesson does after a slip.

The latest decision trace's ``β`` and cause slopes are shown beside them, with what moves each.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping
import json
from typing import Any

from learnloop.router_objective import miss_cause as MC

VERSION = "sg_miss_cause_report_v1"
OFFER_PREFIX = "lesson_offer:"
WHAT_MOVES = ("beta moves once diagnosed misses are followed by a cold check on the same topic with nothing in between "
              "and the diagnosis is not all on one side; gamma_gap and gamma_slip move once a lesson that ran from an "
              "offer with a diagnosed sensor has a later qualifying cold outcome on its topic")


def _loads(raw: Any) -> Any:
    try:
        return json.loads(raw or "{}")
    except (TypeError, ValueError):
        return {}


def _weighted(rows: list[tuple[Mapping[str, Any], float | None]]) -> dict[str, Any]:
    mass = {name: 0.0 for name in MC.CLASSES}
    graded = {name: 0.0 for name in MC.CLASSES}
    with_outcome = {name: 0.0 for name in MC.CLASSES}
    for sensor, outcome in rows:
        for name, key in ((MC.GAP, "p_gap"), (MC.SLIP, "p_slip"), (MC.UNKNOWN, "p_unknown")):
            p = float(sensor.get(key) or 0.0)
            mass[name] += p
            if outcome is not None:
                with_outcome[name] += p
                graded[name] += p * outcome
    return {MC.CLASS_WORDS[name]: {"expected_offers": round(mass[name], 6),
                                   "expected_with_a_later_cold_result": round(with_outcome[name], 6),
                                   "mean_later_cold_grade": (round(graded[name] / with_outcome[name], 6)
                                                             if with_outcome[name] else None)}
            for name in MC.CLASSES}


def section(connection: Any) -> dict[str, Any]:
    from learnloop.learner.lesson_weight import qualifying_outcomes

    if connection.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='router_decisions'").fetchone() is None:
        return {"version": VERSION, "available": False, "reason": "no router decisions table"}
    statuses: Counter[str] = Counter()
    every: list[tuple[Mapping[str, Any], float | None]] = []
    won: list[tuple[Mapping[str, Any], float | None]] = []
    offers = 0
    latest_trace: Mapping[str, Any] | None = None
    for detail_json, chosen, created in connection.execute(
            "SELECT detail_json, chosen_ref, created_at FROM router_decisions ORDER BY created_at, id"):
        detail = _loads(detail_json)
        trace = detail.get("objective_trace") if isinstance(detail, Mapping) else None
        if isinstance(trace, Mapping) and isinstance(trace.get("miss_cause"), Mapping):
            latest_trace = trace["miss_cause"]
        offer = detail.get("lesson_offers") if isinstance(detail, Mapping) else None
        if not isinstance(offer, Mapping) or offer.get("status") != "offered" or "miss_cause" not in offer:
            continue
        offers += 1
        sensor = offer.get("miss_cause")
        if not isinstance(sensor, Mapping):
            statuses["no_miss_since_last_lesson"] += 1
            continue
        statuses[str(sensor.get("status"))] += 1
        if sensor.get("status") != MC.DIAGNOSED:
            continue
        lo = str(offer.get("learning_object_id") or "")
        outcomes = qualifying_outcomes(connection, [lo], str(created)) if lo else []
        outcome = float(outcomes[0]["correctness"]) if outcomes else None
        every.append((sensor, outcome))
        if str(chosen or "").startswith(OFFER_PREFIX):
            won.append((sensor, outcome))
    all_offers = _weighted(every)
    won_offers = _weighted(won)
    win_rate = {name: (round(won_offers[name]["expected_offers"] / all_offers[name]["expected_offers"], 6)
                       if all_offers[name]["expected_offers"] else None) for name in all_offers}
    return {
        "version": VERSION, "available": True,
        "offers_with_a_sensor": offers, "statuses": dict(statuses),
        "by_class": {"all_offers": all_offers, "offers_drawn": won_offers, "lesson_drawn_share": win_rate},
        "later_cold_results_label": MC.OBSERVATIONAL,
        "latest_fit": ({"beta": (latest_trace.get("in_value") or {}).get("beta"),
                        "slopes": (latest_trace.get("in_value") or {}).get("slopes")} if latest_trace else None),
        "what_moves_the_fits": WHAT_MOVES,
    }


def lines(report: Mapping[str, Any]) -> list[str]:
    if not report.get("available"):
        return [f"Slip or gap: {report.get('reason')}"]
    out = [f"Slip or gap: {report['offers_with_a_sensor']} offers with a miss sensor; statuses "
           + (", ".join(f"{key} {value}" for key, value in sorted(report["statuses"].items())) or "none")]
    by_class = report["by_class"]
    for name in ("gap", "slip", "unknown"):
        every, drawn = by_class["all_offers"][name], by_class["offers_drawn"][name]
        out.append(f"  {name}: expected offers {every['expected_offers']}, drawn {drawn['expected_offers']} "
                   f"(share {by_class['lesson_drawn_share'][name]}); later cold grade {every['mean_later_cold_grade']} "
                   f"over {every['expected_with_a_later_cold_result']}")
    out.append(f"  ({report['later_cold_results_label']})")
    fit = report.get("latest_fit") or {}
    beta = fit.get("beta") or {}
    slopes = fit.get("slopes") or {}
    if beta:
        out.append(f"  beta {beta.get('mean')} (variance {beta.get('variance')}, {beta.get('n')} rows; {beta.get('label')})")
    if slopes:
        out.append(f"  gamma_gap {slopes.get('gap')}, gamma_slip {slopes.get('slip')} from {slopes.get('n')} lessons")
    out.append(f"  {report['what_moves_the_fits']}")
    return out


__all__ = ["VERSION", "lines", "section"]
