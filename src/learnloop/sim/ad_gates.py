"""AD2+AD3's simulation gates as metrics (spec_adaptive_difficulty_v1 §14; pre-registration §1.5-1.9).

Each function runs one gate's pre-registered scenarios on :mod:`.ad_synthetic`
and returns its figures and, per pass condition, whether it holds. The tests
(``tests/test_ad23_sim.py``) assert the conditions; ``learnloop.sim.ad_gates``
run as a module prints every figure as JSON for the review file. Nothing is
tuned on a run: the scenarios, seeds and thresholds are the pre-registered ones.
"""

from __future__ import annotations

import json
import math
import sys
from collections.abc import Callable, Mapping
from typing import Any

import numpy as np

from learnloop.adaptive_difficulty import model as M
from learnloop.adaptive_difficulty import monitoring as MON
from learnloop.adaptive_difficulty import priors as P
from learnloop.sim import ad_synthetic as A

SUBJECT = "ad_threshold@subject"
UNIFORM = "ad_threshold@subject_uniform"


def _bootstrap_mean(values: np.ndarray, *, samples: int = 2000, seed: str = "ad-sim-bootstrap") -> list[float]:
    rng = A.rng_for(seed)
    values = np.asarray(values, dtype=float)
    means = values[rng.integers(0, len(values), (samples, len(values)))].mean(axis=1)
    return [float(np.quantile(means, 0.025)), float(np.quantile(means, 0.975))]


# -- G-AD2-18 -------------------------------------------------------------------------------------

def g_ad2_18(scenario: str, *, n: int = 200) -> dict[str, Any]:
    result = A.time_to_usable(scenario, n=n)
    if scenario in ("one_cell", "wrong_prior"):
        out = {"engaged_by_15": result.engaged_by(SUBJECT, 15), "band_hit_16_30": result.band_hit_rate(SUBJECT),
               "band_hit_1_15": result.band_hit_rate(SUBJECT, 1, 15),
               "band_mode_share": float(np.mean([log.band_mode.mean() for log in result.arms[SUBJECT]])),
               "trivial_success": result.trivial_success_rate(SUBJECT),
               "oracle_band_hit_bound_16_30": result.reachable_rate(SUBJECT)}
        if scenario == "one_cell":
            out["pass"] = {"engaged_by_15": out["engaged_by_15"] >= 0.80, "band_hit": out["band_hit_16_30"] >= 0.35}
        else:
            out["pass"] = {"band_hit": out["band_hit_16_30"] >= 0.30}
        return out
    arms = {}
    for name, logs in result.arms.items():
        seen: set[tuple[str, str]] = set()
        first_block = []
        for log in logs:
            first_block.append(log.cell not in seen)
            if len(first_block) % 5 == 0:
                seen.add(log.cell)
        never = [log for log, new in zip(logs, first_block) if new]
        seen_logs = [log for log, new in zip(logs, first_block) if not new]
        cells = sorted({log.cell for log in logs})
        arms[name] = {
            "band_hit_16_30": result.band_hit_rate(name), "trivial_success": result.trivial_success_rate(name),
            "oracle_band_hit_bound_16_30": result.reachable_rate(name),
            "band_mode_share": float(np.mean([log.band_mode.mean() for log in logs])),
            "band_hit_never_seen_cells": float(np.mean([log.hit.mean() for log in never])) if never else None,
            "band_hit_seen_cells": float(np.mean([log.hit.mean() for log in seen_logs])) if seen_logs else None,
            "own_answers_before_band_median": {f"{c[0]}:{c[1]}": float(np.median(A.own_answers_before_band(logs, c)))
                                               for c in cells},
        }
    ad = arms[SUBJECT]
    return {"arms": arms, "pass": {
        "band_hit_vs_incumbent": ad["band_hit_16_30"] >= arms["incumbent"]["band_hit_16_30"],
        "band_hit_vs_no_update": ad["band_hit_16_30"] >= arms["ad_no_update"]["band_hit_16_30"],
        "trivial_vs_incumbent": ad["trivial_success"] <= arms["incumbent"]["trivial_success"],
    }}


# -- G-AD2-7 / G-AD2-8 / G-AD2-14 -----------------------------------------------------------------

def g_ad2_7(*, n: int = 200) -> dict[str, Any]:
    result = A.recovery(policy="monotone", n=n, no_feature_effect=True)
    labels = [A.feature_time_correlation(points) for points in result.served]
    confounded = {dim: float(np.mean([label[dim]["confounded"] for label in labels]))
                  for dim in ("complexity", "transfer")}
    return {"confounded_share": confounded, "pass": {"labelled_confounded": all(v >= 0.99 for v in confounded.values())}}


def g_ad2_8(*, n: int = 200) -> dict[str, Any]:
    result = A.recovery(policy="ad_select_v1", n=n)
    names = list(P.BETA_NAMES)
    within = (np.abs(result.beta_mean - result.beta_true) <= 2.0 * result.beta_sd)
    per_coordinate = {}
    never_varied = []
    codings = np.array([[A.coding(p) for p in seq] for seq in result.served])  # (n, T, β)
    for j, name in enumerate(names):
        recovered = [bool(within[i, j]) for i in range(n) if name not in result.prior_dependent[i]]
        varied = bool(np.any(codings[:, :, j].std(axis=1) > 0))
        if not varied:
            never_varied.append(name)
        per_coordinate[name] = {"seeds_identified": len(recovered),
                                "recovered": (float(np.mean(recovered)) if recovered else None)}
    aliased_ok = all(all(name in result.prior_dependent[i] for i in range(n)) for name in never_varied)
    recovered_ok = all(v["recovered"] is None or v["recovered"] >= 0.90 for v in per_coordinate.values())
    return {"per_coordinate": per_coordinate, "never_varied": never_varied,
            "pass": {"recovered_within_2sd_90pct": recovered_ok, "aliased_reported_prior_dependent": aliased_ok}}


def g_ad2_14(*, n: int = 200) -> dict[str, Any]:
    result = A.censoring(n=n)
    within = np.abs(result.predicted - result.true) <= 2.0 * result.sd
    bias = (result.dropped - result.true).mean(axis=1)
    se = float(bias.std(ddof=1) / math.sqrt(len(bias)))
    return {"within_2sd": float(within.mean()), "censored_bias": float((result.predicted - result.true).mean()),
            "dropped_bias": float(bias.mean()), "dropped_bias_lower_95": float(bias.mean() - 1.645 * se),
            "pass": {"within_2sd_90pct": float(within.mean()) >= 0.90,
                     "dropping_overestimates": float(bias.mean() - 1.645 * se) > 0.0}}


# -- G-AD3-6 ---------------------------------------------------------------------------------------

def g_ad3_6(point: P.HyperPoint, *, seeds: int = 25) -> dict[str, Any]:
    mass = A.hyperparameters_learned(point, seeds=seeds)
    share = float(np.mean(mass >= 0.5))
    return {"point": point.key(), "mean_mass": float(mass.mean()), "share_seeds_half": share,
            "pass": {"half_mass_80pct": share >= 0.80}}


# -- G-AD3-7 ---------------------------------------------------------------------------------------

def g_ad3_7(flow: str, proposal_kind: str, *, n: int = 200) -> dict[str, Any]:
    result = A.related_topics(flow=flow, proposal_kind=proposal_kind, n=n)
    out: dict[str, Any] = {"flow": flow, "proposal": proposal_kind, "mates": {}, "unrelated": {}}
    mate_answers = {}
    loss_differences = []
    for lo in result.mates:
        coupled = result.own_answers_before_band(SUBJECT, lo)
        uniform = result.own_answers_before_band(UNIFORM, lo)
        loss_c = result.first_attempt_loss(SUBJECT, lo)
        loss_u = result.first_attempt_loss(UNIFORM, lo)
        loss_differences.append(loss_c - loss_u)
        mate_answers[lo] = (coupled, uniform)
        out["mates"][lo] = {"median_answers_before_band": [float(np.median(coupled)), float(np.median(uniform))],
                            "first_attempt_log_loss": [float(loss_c.mean()), float(loss_u.mean())]}
    pooled_c = np.concatenate([v[0] for v in mate_answers.values()])
    pooled_u = np.concatenate([v[1] for v in mate_answers.values()])
    difference = np.mean(np.stack(loss_differences), axis=0)
    ci = _bootstrap_mean(difference)
    out["related"] = {"median_answers_before_band": [float(np.median(pooled_c)), float(np.median(pooled_u))],
                      "first_attempt_log_loss_difference": float(difference.mean()), "ci95": ci}
    lo = result.unrelated
    loss = result.first_attempt_loss(SUBJECT, lo).mean() - result.first_attempt_loss(UNIFORM, lo).mean()
    hits = result.band_hit_rate(SUBJECT, lo) - result.band_hit_rate(UNIFORM, lo)
    out["unrelated"] = {"first_attempt_log_loss_difference": float(loss), "band_hit_difference": float(hits)}
    checks = {"unrelated_log_loss": bool(loss <= 0.02), "unrelated_band_hits": bool(hits >= -0.03)}
    if proposal_kind == "correct":
        checks["related_log_loss_lower"] = bool(ci[1] < 0.0)
        if flow == "practice":
            # Amendment A10: the band-mode criterion applies to the practice flow only.
            # Band mode never engaged (an infinite median) is never "2 fewer".
            coupled, uniform = float(np.median(pooled_c)), float(np.median(pooled_u))
            checks["related_two_fewer_answers"] = bool(math.isfinite(coupled) and coupled <= uniform - 2)
    out["pass"] = checks
    return out


def g_ad3_7_shrink(proposal_kind: str, *, n: int = 200) -> dict[str, Any]:
    result = A.wrong_proposal_shrinks(proposal_kind=proposal_kind, n=n)
    reach = result["weight_zero_reaches_half"]
    fires = result["flag_fires"]
    out = {"proposal": proposal_kind, "weight_zero_half_within_100": float(np.mean(reach <= 100)),
           "flag_within_200": float(np.mean(fires <= 200))}
    if proposal_kind == "wrong":
        out["pass"] = {"shrinks": out["weight_zero_half_within_100"] >= 0.80, "flags": out["flag_within_200"] >= 0.80}
    else:
        out["pass"] = {"no_false_flag": out["flag_within_200"] <= 0.05}
    return out


# -- G-AD3-8 / G-AD3-11 / G-AD3-15 (synthetic readers) ------------------------------------------------

def _reading_flag_and_losses(result: A.ReaderResult) -> tuple[np.ndarray, np.ndarray]:
    losses = []
    fires = []
    for i in range(len(result.records["y"])):
        y = result.records["y"][i]
        on, off = result.records["on"][i], result.records["off"][i]
        terms = [MON.log_loss_difference(a, b, c) for a, b, c in zip(on, off, y)]
        losses.append(np.mean([t[0] for t in terms]))
        fires.append(MON.comparison_flag("reading_worse_than_no_reading", [t[0] for t in terms],
                                         [t[1] for t in terms]).fires)
    return np.array(losses), np.array(fires)


def g_ad3_8(*, n: int = 200) -> dict[str, Any]:
    rise = A.readers(scenario="rise", n=n, los=500, reading_only=True, rise=0.3, arms=("on", "off"),
                     seed="g-ad3-8")
    losses, _fires = _reading_flag_and_losses(rise)
    ci = _bootstrap_mean(losses)
    flat = A.readers(scenario="flat", n=n, los=500, reading_only=True, rise=0.0, arms=("on", "off"), seed="g-ad3-8")
    _losses, fires = _reading_flag_and_losses(flat)
    full = flat.mean["reading"].sum(axis=1)
    return {"rise": {"log_loss_on_minus_off": float(losses.mean()), "ci95": ci},
            "flat": {"reading_full_effect_mean": float(full.mean()), "share_below_0_05": float(np.mean(full < 0.05)),
                     "flag_fires": float(fires.mean())},
            "pass": {"rise_lower_with_reading": ci[1] < 0.0, "flat_shrinks": float(np.mean(full < 0.05)) >= 0.90,
                     "flat_flag_rare": float(fires.mean()) <= 0.05}}


def _curve_coverage(result: A.ReaderResult, kind: str) -> np.ndarray:
    ok = np.ones(result.mean[kind].shape[0], dtype=bool)
    for dose in range(1, 6):
        basis = np.array(M.dose_basis(dose))
        fitted = result.mean[kind] @ basis
        sd = np.sqrt(np.maximum(np.einsum("i,nij,j->n", basis, result.cov[kind], basis), 0.0))
        ok &= np.abs(fitted - A.true_curve(result.curves[kind], dose)) <= 2.0 * sd
    return ok


def g_ad3_11(scenario: str, *, floor: float = 0.10, n: int = 200) -> dict[str, Any]:
    result = A.readers(scenario=scenario, n=n, floor=floor)
    out: dict[str, Any] = {"scenario": scenario, "floor": floor, "kinds": {}}
    checks: dict[str, bool] = {}
    if scenario in ("base", "downturn"):
        for kind in A.KINDS:
            coverage = _curve_coverage(result, kind)
            true_n = A.true_useful_dose(result.curves[kind], A.MINUTES[kind])
            fitted = [A.fitted_useful_dose(result, kind, i) for i in range(n)]
            close = np.mean([f["n_star"] is not None and abs(f["n_star"] - true_n) <= 1 for f in fitted])
            entry = {"true": list(result.curves[kind]), "fitted_mean": result.mean[kind].mean(axis=0).round(4).tolist(),
                     "within_2sd_doses_1_5": float(coverage.mean()), "true_n_star": true_n,
                     "n_star_within_one": float(close)}
            checks[f"{kind}:curve"] = float(coverage.mean()) >= 0.90
            checks[f"{kind}:n_star"] = float(close) >= 0.80
            if result.curves[kind] == (0.0, 0.0):
                full = result.mean[kind].sum(axis=1)
                entry["full_effect_below_0_05"] = float(np.mean(full < 0.05))
                checks[f"{kind}:no_effect"] = float(np.mean(full < 0.05)) >= 0.90
            out["kinds"][kind] = entry
        if scenario == "downturn":
            found = []
            for i in range(n):
                c = result.mean["worked_example"][i]
                curve = [c[0] * M.dose_basis(d)[0] + c[1] * M.dose_basis(d)[1] for d in range(0, 11)]
                found.append(int(np.argmax(curve)) < 5)
            out["downturn_found"] = float(np.mean(found))
            checks["downturn_found"] = float(np.mean(found)) >= 0.80
    elif scenario == "confounding":
        from learnloop.adaptive_difficulty import dose_report as DR

        for variant, kind in A.OFFER_KIND.items():
            covers = []
            tested = []
            for i in range(n):
                effect = DR.offer_effect(result.offers[i], variant)
                ci = effect.get("ci95")
                covers.append(ci is not None and ci[0] <= 0.0 <= ci[1])
                c = result.mean[kind][i]
                curve_sign = float(c[0] * M.dose_basis(1)[0] + c[1] * M.dose_basis(1)[1])
                tested.append(DR.label(curve_sign, effect) == DR.TESTED)
            out["kinds"][kind] = {"ci_covers_zero": float(np.mean(covers)), "labelled_tested": float(np.mean(tested))}
            checks[f"{kind}:covers"] = 0.90 <= float(np.mean(covers)) <= 1.0
            checks[f"{kind}:never_tested"] = float(np.mean(tested)) <= 0.05
    out["pass"] = checks
    return out


def g_ad3_15(*, n: int = 200) -> dict[str, Any]:
    none = A.readers(scenario="verdicts", n=n, los=500, verdicts="none", seed="g-ad3-15")
    missed = A.readers(scenario="verdicts", n=n, los=500, verdicts="missed", seed="g-ad3-15")
    ok_none = (np.abs(none.verdict_mean) <= 0.05).all(axis=1) & (none.verdict_sd <= 0.10).all(axis=1)
    lam = missed.verdict_mean[:, 1]
    upper = lam + 1.96 * missed.verdict_sd[:, 1]
    ok_missed = (lam < 0) & (upper < 0)
    return {"no_signal": {"share_ok": float(ok_none.mean()), "mean": none.verdict_mean.mean(axis=0).tolist(),
                          "sd": none.verdict_sd.mean(axis=0).tolist()},
            "missed": {"share_ok": float(ok_missed.mean()), "lambda_missed_mean": float(lam.mean()),
                       "sd": float(missed.verdict_sd[:, 1].mean())},
            "pass": {"no_signal_shrinks": float(ok_none.mean()) >= 0.90,
                     "missed_recovered": float(ok_missed.mean()) >= 0.90}}


# -- G-AD3-9 (synthetic score logs) ----------------------------------------------------------------------

def g_ad3_9(*, seeds: int = 200, attempts: int = 300) -> dict[str, Any]:
    """Flags on synthetic logs: the worse model 0.15 nats worse per first attempt over 300 first
    attempts (and the other flags' stated conditions); none fires when nothing is worse."""

    shift = _shift_for_excess_loss(0.15)
    fired_worse: dict[str, list[bool]] = {name: [] for name in MON.FLAG_SWITCHES}
    fired_null: dict[str, list[bool]] = {name: [] for name in MON.FLAG_SWITCHES}
    for s in range(seeds):
        rng = A.rng_for(f"g-ad3-9:{s}")
        p = rng.uniform(0.3, 0.9, attempts)
        y = (rng.random(attempts) < p).astype(float)
        logit = np.log(p / (1 - p))
        worse = 1.0 / (1.0 + np.exp(-(logit + shift)))
        twin_a = 1.0 / (1.0 + np.exp(-(logit + rng.normal(0.0, 0.3, attempts))))
        twin_b = 1.0 / (1.0 + np.exp(-(logit + rng.normal(0.0, 0.3, attempts))))
        for name in ("sharing_worse_than_topic_only", "coupling_worse_than_uniform", "reading_worse_than_no_reading",
                     "verdicts_worse_than_no_verdicts"):
            terms = [MON.log_loss_difference(a, b, c) for a, b, c in zip(worse, p, y)]
            fired_worse[name].append(MON.comparison_flag(name, [t[0] for t in terms], [t[1] for t in terms]).fires)
            terms = [MON.log_loss_difference(a, b, c) for a, b, c in zip(twin_a, twin_b, y)]
            fired_null[name].append(MON.comparison_flag(name, [t[0] for t in terms], [t[1] for t in terms]).fires)
        # Readiness: the band-region error of a forecaster 0.10 too high, in two consecutive reports.
        band = rng.uniform(0.6, 0.9, attempts)
        yb = (rng.random(attempts) < band).astype(float)
        yb2 = (rng.random(attempts) < band).astype(float)
        high = np.clip(band + 0.10, 0, 0.995)
        fired_worse["readiness_miscalibrated"].append(MON.readiness_flag(
            [MON.band_region_error(high, yb), MON.band_region_error(high, yb2)]).fires)
        fired_null["readiness_miscalibrated"].append(MON.readiness_flag(
            [MON.band_region_error(band, yb), MON.band_region_error(band, yb2)]).fires)
        # Band missed: realized success 0.50 against 0.75 on 200 AD selections.
        fired_worse["band_missed"].append(MON.band_missed_flag((rng.random(200) < 0.50).astype(float)).fires)
        fired_null["band_missed"].append(MON.band_missed_flag((rng.random(200) < 0.75).astype(float)).fires)
        # Dose offers: 90% dismissed of 30 delivered (or three density lowerings in 14 days) vs 30%.
        delivered = [{"dismissed": bool(rng.random() < 0.9)} for _ in range(30)]
        lowered = ["2026-10-10T00:00:00Z", "2026-10-12T00:00:00Z", "2026-10-14T00:00:00Z"]
        fired_worse["dose_offers_a_burden"].append(
            MON.dose_burden_flag(delivered, [], now="2026-10-15T00:00:00Z").fires
            and MON.dose_burden_flag([], lowered, now="2026-10-15T00:00:00Z").fires)
        calm = [{"dismissed": bool(rng.random() < 0.3)} for _ in range(30)]
        fired_null["dose_offers_a_burden"].append(MON.dose_burden_flag(calm, lowered[:1], now="2026-10-15T00:00:00Z").fires)
    worse = {name: float(np.mean(v)) for name, v in fired_worse.items()}
    null = {name: float(np.mean(v)) for name, v in fired_null.items()}
    none_fires = float(np.mean([not any(fired_null[name][s] for name in fired_null) for s in range(seeds)]))
    return {"shift": shift, "fires_when_worse": worse, "fires_when_not": null, "seeds_none_fires": none_fires,
            "recommends": dict(MON.FLAG_SWITCHES),
            "pass": {"fire_when_worse": all(v >= 0.80 for v in worse.values()), "quiet_when_not": none_fires >= 0.95}}


def _shift_for_excess_loss(target: float) -> float:
    """The logit shift whose expected excess log loss over the truth (p ~ U(0.3, 0.9)) is ``target``."""

    p = np.linspace(0.3, 0.9, 601)
    logit = np.log(p / (1 - p))

    def excess(shift: float) -> float:
        q = 1.0 / (1.0 + np.exp(-(logit + shift)))
        return float(np.mean(p * np.log(p / q) + (1 - p) * np.log((1 - p) / (1 - q))))

    low, high = 0.0, 5.0
    for _ in range(80):
        mid = 0.5 * (low + high)
        if excess(mid) < target:
            low = mid
        else:
            high = mid
    return 0.5 * (low + high)


GATES: dict[str, Callable[[], Mapping[str, Any]]] = {
    "G-AD2-7": g_ad2_7,
    "G-AD2-8": g_ad2_8,
    "G-AD2-14": g_ad2_14,
    "G-AD2-18:one_cell": lambda: g_ad2_18("one_cell"),
    "G-AD2-18:wrong_prior": lambda: g_ad2_18("wrong_prior"),
    "G-AD2-18:plan_flow": lambda: g_ad2_18("plan_flow"),
    "G-AD3-7:practice:correct": lambda: g_ad3_7("practice", "correct"),
    "G-AD3-7:practice:noisy": lambda: g_ad3_7("practice", "noisy"),
    "G-AD3-7:practice:wrong": lambda: g_ad3_7("practice", "wrong"),
    "G-AD3-7:reading:correct": lambda: g_ad3_7("reading", "correct"),
    "G-AD3-7:shrink:wrong": lambda: g_ad3_7_shrink("wrong"),
    "G-AD3-7:shrink:correct": lambda: g_ad3_7_shrink("correct"),
    "G-AD3-8": g_ad3_8,
    "G-AD3-9": g_ad3_9,
    "G-AD3-11:base:0.10": lambda: g_ad3_11("base", floor=0.10),
    "G-AD3-11:base:0.30": lambda: g_ad3_11("base", floor=0.30),
    "G-AD3-11:downturn": lambda: g_ad3_11("downturn"),
    "G-AD3-11:confounding:0.10": lambda: g_ad3_11("confounding", floor=0.10),
    "G-AD3-11:confounding:0.30": lambda: g_ad3_11("confounding", floor=0.30),
    "G-AD3-15:6": g_ad3_15,
}


def main(argv: list[str]) -> int:
    names = argv or list(GATES)
    if names == ["G-AD3-6"]:
        for point in P.hyper_grid():
            print(json.dumps({"gate": "G-AD3-6", **g_ad3_6(point)}, sort_keys=True), flush=True)
        return 0
    for name in names:
        print(json.dumps({"gate": name, **GATES[name]()}, sort_keys=True, default=float), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))


__all__ = ["GATES", "g_ad2_14", "g_ad2_18", "g_ad2_7", "g_ad2_8", "g_ad3_11", "g_ad3_15", "g_ad3_6", "g_ad3_7",
           "g_ad3_7_shrink", "g_ad3_8", "g_ad3_9", "main"]
