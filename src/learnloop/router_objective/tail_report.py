"""RO6 (spec_router_objective_v1 §10): the learned tail's section of ``learnloop router objective-report``.

It states the narrow claim and keeps §8.9's evaluations beside it (the report's other sections: forecast, action
value, recommendation value, whole policy), never standing in for them:

* **the claim**: the logger's value plus one small improvement step. A coin followed by the logger tests
  ``Q^{π_b}(a) − Q^{π_b}(a′)``; more data does not lift this. **No improvement guarantee is claimed**: a ``2δ``
  per-decision bound needs a uniform ``Q`` error bound and an expected-value update whose feasible set contains the
  baseline, and calibration slopes and rank agreement do not establish those;
* **the fits** as of now, one per generator version (its own transitions only), with their size, coefficients by
  feature, noise, conditioning and source; the change points between versions; the transitions censored by reason;
* **ŵ's history** from the traces (each decision froze the ``ŵ`` it used, with its slope, rank and count), and ``ŵ``
  as of now; with each, the missing terms (RO6's landing ruling R1: counted per window), the bound used and the
  estimate with the missing terms left out beside it (shown only, never served);
* **the residual's share** of ``Ṽ`` at each decision, and how often the residual moved the numeric policy's argmax;
* **the partial-history cross-check** (importance weights of the improvement step near the logger) beside the fit's
  own projection of the same step: if they disagree beyond the weighted interval, the fit does not decide (a
  reading, not a gate; nothing here gates anything).

Read-only; no model call.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping
import json
from statistics import median
from typing import Any

from learnloop.router_objective import learned_tail as LT
from learnloop.router_objective import tail_data as TD

VERSION = "ro6_learned_tail_report_v1"
CLAIM = ("the logger's value plus one small improvement step: a stop coin followed by the logger tests "
         "Q^pi_b(a) - Q^pi_b(a'); more data does not lift this")
NO_GUARANTEE = ("no improvement guarantee is claimed: a 2-delta per-decision bound needs a uniform Q error bound and "
                "an expected-value update whose feasible set contains the baseline; calibration slopes and rank "
                "agreement do not establish those, so the report keeps showing the forecast, action-value, "
                "recommendation-value and whole-policy evaluations")


def _history(connection: Any) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    days: dict[str, list[dict[str, Any]]] = defaultdict(list)
    shares: list[float] = []
    moved = 0
    applied = 0
    timings: list[int] = []
    carried: list[int] = []
    statuses: dict[str, int] = defaultdict(int)
    previous_statuses: dict[str, int] = defaultdict(int)
    for local_date, created_at, body in connection.execute(
            "SELECT local_date, created_at, trace_json FROM router_objective_traces WHERE decision_kind = 'plan_block' "
            "ORDER BY created_at, id"):
        trace = json.loads(body)
        record = trace.get("residual")
        if not isinstance(record, Mapping):
            continue
        statuses[str(record.get("status"))] += 1
        if record.get("elapsed_ms") is not None:
            timings.append(int(record["elapsed_ms"]))
        if record.get("status") != "applied":
            continue
        applied += 1
        previous = record.get("previous") if isinstance(record.get("previous"), Mapping) else {}
        if previous.get("elapsed_ms") is not None:
            # The second valuation at the earlier decision's carried cutoff (Codex re-review F3).
            carried.append(int(previous["elapsed_ms"]))
        if previous.get("status"):
            previous_statuses[f"{previous.get('status')}:{previous.get('q_status', '-')}"] += 1
        weight = record.get("weight") or {}
        unbounded = weight.get("unbounded") if isinstance(weight.get("unbounded"), Mapping) else {}
        missing = weight.get("missing") if isinstance(weight.get("missing"), Mapping) else {}
        excluded = weight.get("excluded") if isinstance(weight.get("excluded"), Mapping) else {}
        days[str(local_date)].append({"at": created_at, "w_hat": record.get("w_hat"), "n": weight.get("n"),
                                      "excluded_terms": excluded.get("terms"),
                                      "excluded_contrasts": excluded.get("contrasts"),
                                      "slope_mean": weight.get("slope_mean"), "slope_sd": weight.get("slope_sd"),
                                      "rank": weight.get("rank"), "p_rank": weight.get("p_rank"),
                                      "bound": weight.get("bound"), "missing_contrasts": missing.get("contrasts"),
                                      "missing_terms": missing.get("terms"),
                                      # R10: the forced windows' missing terms by kind (the trace's summary)
                                      "missing_by_reason": dict((((record.get("contrasts") or {}).get("missing")
                                                                  or {}).get("by_reason")) or {}),
                                      "w_hat_unbounded": unbounded.get("w_hat"),
                                      "slope_unbounded": unbounded.get("slope_mean"),
                                      "fit_basis": record.get("fit_basis"),
                                      "transitions": (record.get("transitions") or {}).get("n")})
        for entry in (record.get("candidates") or {}).values():
            v_tilde, v_res, w_hat = entry.get("v_tilde"), entry.get("v_residual"), record.get("w_hat")
            if isinstance(v_tilde, (int, float)) and isinstance(v_res, (int, float)) and v_tilde:
                shares.append(abs(float(w_hat or 0.0) * float(v_res)) / abs(float(v_tilde)))
        tie = ((trace.get("policies") or {}).get("numeric") or {}).get("tie") or {}
        # (IH4: the residual's own move, before any shift by w_pref)
        if tie.get("tail_argmax") is not None and tie.get("before_preferences_argmax", tie.get("argmax")) != tie.get("tail_argmax"):
            moved += 1
    history = [{"local_date": day, "decisions": len(rows), "w_hat_first": rows[0]["w_hat"], "w_hat_last": rows[-1]["w_hat"],
                "contrasts": rows[-1]["n"], "slope_mean": rows[-1]["slope_mean"], "slope_sd": rows[-1]["slope_sd"],
                "rank": rows[-1]["rank"], "p_rank": rows[-1]["p_rank"], "bound": rows[-1]["bound"],
                "missing_contrasts": rows[-1]["missing_contrasts"], "missing_terms": rows[-1]["missing_terms"],
                "missing_by_reason": rows[-1]["missing_by_reason"],
                "excluded_terms": rows[-1]["excluded_terms"], "excluded_contrasts": rows[-1]["excluded_contrasts"],
                "w_hat_unbounded": rows[-1]["w_hat_unbounded"], "slope_unbounded": rows[-1]["slope_unbounded"],
                "fit_basis": rows[-1]["fit_basis"],
                "transitions": rows[-1]["transitions"]} for day, rows in sorted(days.items())]
    summary = {"decisions_with_residual": applied, "statuses": dict(statuses), "argmax_moved": moved,
               "share_of_v_tilde": ({"median": median(shares), "max": max(shares), "n": len(shares)} if shares else None),
               "serving_ms": ({"median": median(timings), "max": max(timings), "n": len(timings)} if timings else None),
               "carried_cutoff_ms": ({"median": median(carried), "max": max(carried), "n": len(carried)}
                                     if carried else None),
               "previous_cutoff": dict(previous_statuses)}
    return history, summary


def build(connection: Any, vault: Any, *, now: str) -> dict[str, Any]:
    """The section (module docstring), as of ``now``."""

    config = vault.config
    rows = TD.logged(connection, config, at=now)
    fitted = TD.fits(connection, config, at=now, rows=rows)
    contrasts, censored_contrasts = TD.contrasts(connection, config, rows, at=now)
    weight = LT.residual_weight(contrasts, prior_sd=float(config.router_objective.residual_weight_prior_sd), at=now)
    spans: dict[str, dict[str, Any]] = {}
    for row in rows:
        span = spans.setdefault(row.generator, {"generator": row.generator, "first": row.created_at, "decisions": 0,
                                                "algorithm_version": row.algorithm_version, "features": {}})
        span["last"] = row.created_at
        span["decisions"] += 1
        span["features"][row.features_source] = span["features"].get(row.features_source, 0) + 1
    versions = []
    for key in fitted.order:
        model = fitted.by_generator.get(key)
        entry = dict(spans.get(key) or {"generator": key})
        entry["fit"] = ({"n": model.n, "coefficients": dict(zip(model.names, model.coef)), "sigma2": model.sigma2,
                         "condition": model.condition, "passes": model.passes, "source": model.source,
                         "prior_sd": model.prior_sd, "version": model.version}
                        if model is not None else {"n": 0, "source": "no transition of this version"})
        versions.append(entry)
    history, summary = _history(connection)
    return {
        "version": VERSION, "claim": CLAIM, "no_guarantee": NO_GUARANTEE,
        "kept_evaluations": ["forecast", "action_value", "recommendation_value", "whole_policy"],
        "fit_version": LT.FIT_VERSION, "features_version": TD.features_version(config),
        "features": list(LT.names_for(TD.features_version(config))),
        "model_class": "Bayesian linear regression (ridge) on the standardized features; FQE's fixed point under a "
                       "Gaussian prior (residual_prior_sd), never accepted on its TD fit",
        "versions": versions, "change_points": list(fitted.steps.change_points),
        "transitions": {"n": len(fitted.steps.transitions), "censored": dict(fitted.steps.censored),
                        "returns_censored": dict(fitted.steps.returns_censored), "decisions": fitted.decisions},
        "w_hat": {**weight.as_dict(), "contrasts_censored": censored_contrasts,
                  "label": "moved only by randomized stop-coin contrasts observed through the randomized checks; "
                           "calibrated on the measurable part of the return only (the terms a check could measure "
                           "as of the coin's draw; landing ruling R7)"},
        "w_hat_history": history, "serving": summary,
        "cross_check": {"partial_history": TD.cross_check(connection, config, rows, at=now),
                        "fit_projection": TD.predicted_improvement(rows),
                        "reading": "if the two disagree beyond the weighted interval, the fit does not decide "
                                   "(a reading, not a gate)"},
    }


def lines(report: Mapping[str, Any]) -> list[str]:
    weight = report["w_hat"]
    out = [f"learned tail ({report['version']}): {report['claim']}",
           f"- {report['no_guarantee']}",
           f"- w^ {weight['w_hat']:.4f} (slope {weight['slope_mean']:+.4f} sd {weight['slope_sd']:.4f}, rank "
           f"{weight['rank']}, P(rank > 0) {weight['p_rank']:.3f}, {weight['n']} randomized contrasts, "
           f"{weight['forced']} forced; {weight['source']})",
           "- w^ is calibrated on the measurable part of the return only: the terms a check could measure as of the "
           f"coin's draw ({weight['excluded']['terms']} terms in {weight['excluded']['contrasts']} contrasts were "
           "outside it, unsupported at the draw)",
           f"- missing terms: {weight['missing']['terms']} in {weight['missing']['contrasts']} contrasts; bound "
           f"{weight['bound']} ({weight.get('bound_definition') or 'no missing term'}); with the missing terms left "
           "out (shown only, never served) w^ "
           f"{weight['unbounded']['w_hat']:.4f}, slope {weight['unbounded']['slope_mean']:+.4f}",
           f"- transitions {report['transitions']['n']} of {report['transitions']['decisions']} decisions; censored "
           f"{report['transitions']['censored']}; change points {len(report['change_points'])}"]
    for entry in report["versions"]:
        fit = entry.get("fit") or {}
        out.append(f"- version {entry.get('generator')} ({entry.get('algorithm_version')}, {entry.get('decisions')} "
                   f"decisions {entry.get('first')} .. {entry.get('last')}): fit n {fit.get('n')}, {fit.get('source')}")
    for day in report["w_hat_history"]:
        out.append(f"- {day['local_date']}: w^ {day['w_hat_first']} -> {day['w_hat_last']} over {day['decisions']} "
                   f"decisions ({day['contrasts']} contrasts, {day['excluded_terms']} terms unsupported at the draw "
                   f"in {day['excluded_contrasts']}, {day['missing_terms']} missing terms in "
                   f"{day['missing_contrasts']} {day.get('missing_by_reason') or {}}, bound {day['bound']}, "
                   f"unbounded w^ {day['w_hat_unbounded']}; "
                   f"{day['transitions']} transitions, {day['fit_basis']})")
    serving = report["serving"]
    out.append(f"- residual applied at {serving['decisions_with_residual']} decisions, argmax moved "
               f"{serving['argmax_moved']}, share of V~ {serving['share_of_v_tilde']}, serving ms {serving['serving_ms']}, "
               f"valued again at the earlier cutoff ms {serving.get('carried_cutoff_ms')}")
    check = report["cross_check"]
    partial = check["partial_history"]
    out.append(f"- cross-check (partial-history weights): {partial.get('one_step') or partial.get('status')}; the fit's "
               f"projection {check['fit_projection']['mean']} over {check['fit_projection']['n']}; {check['reading']}")
    return out


__all__ = ["CLAIM", "NO_GUARANTEE", "VERSION", "build", "lines"]
