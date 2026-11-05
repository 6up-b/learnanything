"""RO4 §8.9: the objective's report, its evaluations kept apart, with counts and versioned comparators.

No evaluation here gates anything. Four questions, none standing in for another:

* **Forecast**: did the models predict observed outcomes? (the LLM policy's forecasts for the drawn option, bound to
  RO2's versioned resolver by :mod:`learnloop.router_objective.forecast_resolve`, per binding and comparator;
  conditional on observation. The memory model's own curve is not on the trace at this version);
* **Action value**: did predicted differences between actions match randomized outcome differences? (needs
  RO5's randomized checks; none exist before it);
* **Recommendation value**: did one policy's next recommendation produce more of the common return, under the live
  continuation? (§8.7's comparison score ``D̂``; none forms before RO5's checks, so ``w`` stays at its prior);
* **Whole policy**: not estimated from logs (sequential DR stays out; simulation is not evidence about a learner).

Counts are shown separately: decisions evaluated, unique completed assessments, decisions informed, pending,
censored by reason, model-supported value (a projection, labelled), closed scores and the posterior of ``Δ``, so a
reader can see whether ``w`` moved on evidence. Comparators are versioned: a new provider model, prompt, card or
objective version starts a new row, so a stronger LLM is not mistaken for learning. The serving section (the first
day's, as the upgrade's report) counts stop's share at each boundary, session length and each policy's share.
Read-only; no model call.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
import json
from statistics import mean
from typing import Any

REPORT_VERSION = "router_objective_report_v1"


def _share(counter: Counter, total: int) -> dict[str, float]:
    return {key: round(value / total, 4) for key, value in sorted(counter.items())} if total else {}


def build(connection: Any, *, now: str, weight: Mapping[str, Any] | None = None,
          forecasts: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """The report over every trace (``connection`` read-only; the traces table at migration 246). ``forecasts``: the
    LLM policy's forecasts resolved against observed outcomes (:func:`learnloop.router_objective.forecast_resolve.
    resolve`), reported as the forecast evaluation, apart from the others."""

    from learnloop.router_objective import forecast_resolve as FR

    from learnloop.db.stores import router_objective as store

    if not store.table_present(connection, store.TRACES):
        return {"status": "no_traces_table", "version": REPORT_VERSION}
    rows = [dict(row) for row in connection.execute(
        "SELECT decision_id, decision_kind, local_date, session_minutes, remembered_minutes, kappa0, kappa_how, "
        "chosen_ref, drawn_component, propensity, w, numeric_ref, llm_status, numeric_status, stop_in_support, "
        "guard_crossed, window_closes_at, trace_json, created_at FROM router_objective_traces ORDER BY created_at, id")]
    blocks = [row for row in rows if row["decision_kind"] == "plan_block"]
    total = len(blocks)
    drawn = Counter(str(row["drawn_component"]) for row in blocks)
    stops = sum(1 for row in blocks if row["chosen_ref"] == "stop_for_today")
    by_day: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in blocks:
        by_day[str(row["local_date"])].append(row)
    days = []
    for day, entries in sorted(by_day.items()):
        minutes = [float(row["session_minutes"]) for row in entries if row["session_minutes"] is not None]
        days.append({
            "local_date": day, "decisions": len(entries),
            "stop_share": round(sum(1 for row in entries if row["chosen_ref"] == "stop_for_today") / len(entries), 4),
            "stop_in_support_share": round(sum(1 for row in entries if row["stop_in_support"]) / len(entries), 4),
            "session_minutes_max": max(minutes) if minutes else None,
            "remembered_minutes": entries[-1]["remembered_minutes"],
            "kappa0": entries[0]["kappa0"], "kappa_how": entries[0]["kappa_how"],
            "policy_share": _share(Counter(str(row["drawn_component"]) for row in entries), len(entries)),
            "guard_crossings": sum(1 for row in entries if row["guard_crossed"]),
        })
    kappa_seed = _kappa_seed(rows)
    comparators: dict[str, dict[str, Any]] = {}
    model_supported: list[float] = []
    for row in rows:
        trace = json.loads(row["trace_json"])
        versions = trace.get("versions") or {}
        llm = (trace.get("policies") or {}).get("llm") or {}
        key = "|".join(str(part) for part in (llm.get("model"), versions.get("llm_schema"), versions.get("card"),
                                               versions.get("objective")))
        entry = comparators.setdefault(key, {"llm_model": llm.get("model"), "llm_schema": versions.get("llm_schema"),
                                             "card": versions.get("card"), "objective": versions.get("objective"),
                                             "decisions": 0, "llm_answered": 0, "numeric_answered": 0})
        entry["decisions"] += 1
        entry["llm_answered"] += 1 if row["llm_status"] == "answered" else 0
        entry["numeric_answered"] += 1 if row["numeric_status"] == "answered" else 0
        chosen = (trace.get("candidates") or {}).get(str(row["chosen_ref"])) or {}
        q = (chosen.get("terms") or {}).get("q")
        if isinstance(q, (int, float)):
            model_supported.append(float(q))
    closed = [row for row in rows if row["window_closes_at"] and str(row["window_closes_at"]) < now]
    pending = len(rows) - len(closed)
    fallback = sum(1 for row in rows if row["llm_status"] != "answered" or row["numeric_status"] != "answered")
    agree = sum(1 for row in rows if row["llm_status"] == "answered" and row["numeric_status"] == "answered"
                and _llm_favoured(row) == row["numeric_ref"])
    llm_timeouts = sum(1 for row in rows if row["llm_status"] == "timeout")
    return {
        "version": REPORT_VERSION,
        "serving": {
            "decisions": total, "interrupt_decisions": len(rows) - total,
            "stop_share": round(stops / total, 4) if total else None,
            "policy_share": _share(drawn, total),
            "llm_policy": {"answered": sum(1 for row in blocks if row["llm_status"] == "answered"),
                           "timeout_rate": round(llm_timeouts / len(rows), 4) if rows else None,
                           "statuses": dict(Counter(str(row["llm_status"]) for row in blocks))},
            "numeric_policy": {"statuses": dict(Counter(str(row["numeric_status"]) for row in blocks))},
            "days": days,
            "kappa_seed": kappa_seed,
            "note": "successful LLM calls and the deployed policy with its fallbacks are both counted: a decision "
                    "where a policy fell back keeps its row",
        },
        "forecast": FR.summary(forecasts),
        "action_value": {"status": "needs RO5's randomized checks; none exist", "randomized_contrasts": 0},
        "recommendation_value": {
            "decisions_evaluated": len(closed), "pending": pending, "unique_completed_assessments": 0,
            "decisions_informed": 0, "closed_scores": 0,
            "censored": {"no_valued_use_with_r_positive": len(closed) - sum(
                1 for row in closed if row["llm_status"] != "answered" or row["numeric_status"] != "answered"),
                "a_policy_fell_back": sum(1 for row in closed if row["llm_status"] != "answered"
                                          or row["numeric_status"] != "answered")},
            "fell_back_rows": fallback, "agreeing_rows": agree,
            "posterior": dict((weight or {}).get("posterior") or {}), "w": (weight or {}).get("w"),
            "note": "until RO5's randomized checks no score forms and w stays at its prior",
        },
        "whole_policy": {"status": "not estimated from logs (sequential DR stays out)"},
        "model_supported_value": {"label": "a projection by the model that chose; never evidence for it",
                                  "mean_chosen_q": round(mean(model_supported), 6) if model_supported else None,
                                  "n": len(model_supported)},
        "comparators": list(comparators.values()),
    }


def _kappa_seed(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Landing ruling R5: how each day's ``κ0`` seed was formed, counted over days (the first decision of a day that
    did not carry the day's seed), so the owner sees how often it fell back: floored at the last positive value,
    the tail's average marginal gain (accepted until RO5), or no frontier at all (the last value)."""

    from learnloop.router_objective import price as P

    seeded: dict[str, str] = {}
    for row in rows:
        how = row.get("kappa_how")
        if how and how != P.CARRIED_DAY:
            seeded.setdefault(str(row["local_date"]), str(how))
    from learnloop.router_objective import stop_coin as SC

    by_how = Counter(seeded.values())
    # RO5 (its landing, merging RO4's count): a day priced by κ0's posterior from stop offers did not fall back;
    # it is counted apart.
    return {"days": len(seeded), "by_how": dict(sorted(by_how.items())),
            "fell_back": sum(count for how, count in by_how.items() if how not in (P.DAY_SEED, SC.POSTERIOR)),
            "fell_back_to_tail_average": by_how.get(P.TAIL_AVERAGE, 0),
            "posterior_days": by_how.get(SC.POSTERIOR, 0),
            "note": "a day's seed is the day's marginal gain per minute at the remembered minutes; it falls back "
                    "when that is not positive; from RO5's first randomized stop offer with a response, κ0 is a "
                    "posterior instead (posterior_days)"}


def _llm_favoured(row: Mapping[str, Any]) -> str | None:
    trace = json.loads(row["trace_json"])
    return ((trace.get("policies") or {}).get("llm") or {}).get("favoured")


def lines(report: Mapping[str, Any]) -> list[str]:
    if report.get("status") == "no_traces_table":
        return ["router objective: this database predates the trace (migration 246)"]
    serving = report["serving"]
    out = [f"router objective report ({report['version']})",
           f"decisions {serving['decisions']} (plus {serving['interrupt_decisions']} follow-up decisions); stop chosen "
           f"{serving['stop_share']}; policy share {serving['policy_share']}"]
    for day in serving["days"]:
        out.append(f"- {day['local_date']}: {day['decisions']} decisions, stop {day['stop_share']}, longest session "
                   f"{day['session_minutes_max']} min of {day['remembered_minutes']} suggested, kappa0 {day['kappa0']} "
                   f"({day['kappa_how']}), shares {day['policy_share']}, guard crossings {day['guard_crossings']}")
    seed = serving.get("kappa_seed")
    if seed:
        out.append(f"kappa0 seed: fell back on {seed['fell_back']} of {seed['days']} days (to the tail's average on "
                   f"{seed['fell_back_to_tail_average']} of {seed['days']} days); by how {seed['by_how']}")
    value = report["recommendation_value"]
    out.append(f"recommendation value: evaluated {value['decisions_evaluated']}, pending {value['pending']}, closed "
               f"scores {value['closed_scores']}, censored {value['censored']}; w {value['w']} ({value['note']})")
    out.append(f"action value: {report['action_value']['status']}")
    forecast = report["forecast"]
    if "comparators" not in forecast:
        out.append(f"forecast: {forecast.get('status')}")
    else:
        out.append(f"forecast ({forecast['binding_version']}, {forecast['label']}): unique assessments "
                   f"{forecast['unique_assessments']}, censored at birth {forecast['censored_at_birth']}")
        for row in forecast["comparators"]:
            out.append(f"- {row['binding']} / {row['model']} / {row['prompt_version']}: scored {row['scored']}, pending "
                       f"{row['pending']}, censored {row['censored']}, mean forecast {row['mean_forecast']}, observed "
                       f"{row['observed_rate']}, log loss {row['mean_log_loss']}, Brier {row['brier']}")
    for row in report["comparators"]:
        out.append(f"comparator {row['llm_model']} / {row['llm_schema']} / {row['card']} / {row['objective']}: "
                   f"{row['decisions']} decisions, LLM answered {row['llm_answered']}, numeric {row['numeric_answered']}")
    return out


__all__ = ["REPORT_VERSION", "build", "lines"]
