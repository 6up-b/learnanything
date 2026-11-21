"""Registered ADM0 runs and aggregate diagnostics, never a production reader.

See adm0-preregistration.md for every experimental number. Timing is descriptive;
scientific selection failures are reported, not converted to passing tests.
"""
from __future__ import annotations

import math
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from time import perf_counter

import numpy as np
from scipy.stats import t as student_t

from learnloop.adaptive_difficulty import model as M
from learnloop.config import MasteryConfig
from learnloop.learner.mastery import MasteryObservation, initial_mastery_state, update_mastery
from learnloop.sim import ad_memory_synthetic as S


def metrics(p: np.ndarray, y: np.ndarray, covered: np.ndarray | None = None) -> dict:
    mask = np.isfinite(p)
    p, y = p[mask], np.asarray(y, dtype=float)[mask]
    if not len(p):
        return {"count": 0, "log_loss": None, "brier": None, "calibration": None, "bias": None, "coverage": None}
    clipped = np.clip(p, S.CLIP, 1 - S.CLIP)
    loss = -y * np.log(clipped) - (1 - y) * np.log1p(-clipped)
    bins = np.minimum((p * 10).astype(int), 9)
    calibration = sum(abs(float(np.sum(p[bins == k] - y[bins == k]))) for k in range(10)) / len(p)
    return {"count": int(len(p)), "log_loss": float(loss.mean()), "brier": float(np.mean((p - y) ** 2)),
            "calibration": calibration, "bias": float(np.mean(p - y)),
            "coverage": None if covered is None else float(np.mean(covered[mask]))}


def baseline_predictions(data: S.Dataset) -> dict[str, np.ndarray]:
    """All baselines consume only earlier labels, using the real mastery update."""
    counts = np.zeros(data.n)
    last = np.full(data.n, .5)
    out = {name: [] for name in ("fsrs", "last", "rate:.5", "rate:1", "rate:2", "mastery_ekf")}
    config = MasteryConfig()
    origin = datetime(2026, 1, 1, tzinfo=UTC)
    states = [initial_mastery_state("lo", "sim", origin.isoformat(),
                                   logit_variance=config.cold_start_prior_logit_variance) for _ in range(data.n)]
    for event, inputs, category in zip(data.events, data.inputs, data.categories, strict=True):
        out["fsrs"].append(np.full(data.n, np.nan) if inputs.item_r is None else inputs.item_r)
        out["last"].append(last.copy())
        for name, a in (("rate:.5", .5), ("rate:1", 1.), ("rate:2", 2.)):
            out[name].append((counts + a) / (event.index + 2 * a))
        out["mastery_ekf"].append(M.sigmoid(np.array([state.logit_mean for state in states]) - config.irt.difficulty_default))
        for i, state in enumerate(states):
            observation = MasteryObservation(rubric_score=int(category[i]) * 2, max_points=4,
                                             evidence_coverage=1., hint_dampening=1., grader_confidence=1.,
                                             attempt_type="independent_attempt", observed_at=origin + timedelta(days=event.at),
                                             attempt_evidence_mass=1.)
            states[i] = update_mastery(state, observation, config, "sim", item_a=1., item_b=config.irt.difficulty_default)
        last = (category == 2).astype(float)
        counts += last
    return {name: np.array(values) for name, values in out.items()}


def strata(data: S.Dataset) -> dict[str, np.ndarray]:
    events = data.events
    out = {"all": np.ones(len(events), dtype=bool)}
    for kind in ("first_surface", "same_item", "unseen_sibling", "singleton_first", "novel_after_drilling"):
        out[kind] = np.array([e.stratum == kind for e in events])
    out["all_first_surfaces"] = np.array([e.stratum in ("first_surface", "singleton_first", "novel_after_drilling") for e in events])
    out["singleton_all"] = np.array([e.singleton for e in events])
    for source in ("assigned", "natural"):
        out[source] = np.array([e.delay_source == source for e in events])
    delays = [i.item_delay for i in data.inputs]
    out["delay:none"] = np.array([d is None for d in delays])
    out["delay:<=1d"] = np.array([d is not None and d <= 1 for d in delays])
    out["delay:1..7d"] = np.array([d is not None and 1 < d <= 7 for d in delays])
    out["delay:>7d"] = np.array([d is not None and d > 7 for d in delays])
    return out


def summarize(runs: list[dict], masks: dict[str, np.ndarray]) -> dict:
    scores = {}
    for key, mask in masks.items():
        ps = np.concatenate([r["p"][mask].ravel() for r in runs])
        ys = np.concatenate([r["y"][mask].ravel() for r in runs])
        cover = None if runs[0]["covered"] is None else np.concatenate([r["covered"][mask].ravel() for r in runs])
        scores[key] = metrics(ps, ys, cover)
        scores[key]["seed_losses"] = [metrics(r["p"][mask].ravel(), r["y"][mask].ravel())["log_loss"] for r in runs]
    recovery = {}
    if runs[0].get("recovery"):
        for checkpoint in runs[0]["recovery"]:
            recovery[checkpoint] = {}
            for coordinate in runs[0]["recovery"][checkpoint]:
                entries = [r["recovery"][checkpoint][coordinate] for r in runs]
                row = {key: None if entries[0][key] is None else float(np.mean([e[key] for e in entries])) for key in entries[0]}
                row["rmse"] = math.sqrt(row.pop("mse"))
                recovery[checkpoint][coordinate] = row
    weights = np.array([r["rho_weights"] for r in runs]) if runs[0].get("rho_weights") else None
    return {"scores": scores, "recovery": recovery,
            "rho_weights": None if weights is None else weights.mean(axis=0).tolist(),
            "rho_entropy_fraction": None if weights is None or weights.shape[1] == 1 else
                float(np.mean(-np.sum(weights * np.log(np.maximum(weights, 1e-300)), axis=1)) / math.log(weights.shape[1]))}


def paired_interval(a: list[float], b: list[float]) -> list[float]:
    differences = np.array(a) - np.array(b)
    mean = float(differences.mean())
    radius = float(student_t.ppf(.975, len(a) - 1) * differences.std(ddof=1) / math.sqrt(len(a)))
    return [mean, mean - radius, mean + radius]


def compare(a: dict, b: dict) -> dict:
    intervals = {key: paired_interval(a["scores"][key]["seed_losses"], b["scores"][key]["seed_losses"])
                 for key in ("same_item", "unseen_sibling", "all_first_surfaces")}
    # Only quantities structurally exposed here; zero-variance rho endpoints have no free effect to recover.
    recovered = a["recovery"]["48"]
    coverage = min(row["coverage"] for key, row in recovered.items()
                   if key in ("ability", "memory_item", "memory_family") or key.startswith("warmth@"))
    favour = (all(intervals[key][2] < 0 for key in ("same_item", "unseen_sibling"))
              and intervals["all_first_surfaces"][1] <= 0 and coverage >= .90)
    return {"intervals": intervals, "minimum_recovery_coverage": coverage, "predictive_recovery_criteria": favour}


def selection_findings(results: dict) -> dict:
    out = {}
    for view in ("subject", "lo"):
        comparisons = (("R3-H3", "R1-H3"), ("R5-H3", "R3-H3"), ("R3-H3", "R3-H1"), ("R3-H5", "R3-H3")) if view == "subject" else (
            ("rho0.5-H3", "rho0.5-H1"), ("rho0.5-H5", "rho0.5-H3"))
        for a, b in comparisons:
            per_world = {world: compare(results[world][view][a], results[world][view][b]) for world in S.WORLDS}
            favourable = all(row["predictive_recovery_criteria"] for row in per_world.values())
            diagnostic = {}
            if a.startswith("R") and a.split("-")[0] != b.split("-")[0]:
                support = S.candidates(True)[a].rhos
                diagnostic["rho_mass_above_uniform"] = all(
                    results[world][view][a]["rho_weights"][support.index(S.WORLDS[world].rho)] > 1 / len(support)
                    for world in ("independent", "balanced", "shared"))
                diagnostic["quarter_point_truth_available"] = False if len(support) == 5 else None
                favourable &= diagnostic["rho_mass_above_uniform"] and len(support) != 5
            else:
                world = "family_memory" if a.endswith("H3") else "slow_retention"
                ca, cb = results[world][view][a]["recovery"]["48"], results[world][view][b]["recovery"]["48"]
                diagnostic["curve_rmse_reduced"] = np.mean([v["rmse"] ** 2 for k, v in ca.items() if k.startswith("warmth@")]) < np.mean(
                    [v["rmse"] ** 2 for k, v in cb.items() if k.startswith("warmth@")])
                diagnostic["curve_rmse_reduced"] = bool(diagnostic["curve_rmse_reduced"])
                favourable &= diagnostic["curve_rmse_reduced"]
            out[f"{view}:{a} vs {b}"] = {"worlds": per_world, "diagnostics": diagnostic,
                                         "verdict": "favoured in simulation" if favourable else "data cannot select this candidate"}
    return out


def next_inputs(fold: S.ReviewFold, at: float) -> list[tuple[S.Event, S.MemoryInputs]]:
    """Cached-input workload: stable item metadata plus strict past-only fold lookup."""
    source = S.schedule()
    events = [replace(source[i], at=at, warmth_hours=24.) for i in (0, 7, 11)]
    events[1] = replace(events[1], item="next-unseen-sibling")
    events[2] = replace(events[2], item="next-novel", family="next-novel-family")
    return [(event, fold.inputs(event)) for event in events]


def synthetic_next(arm: S.MemoryArm, inputs: list[tuple[S.Event, S.MemoryInputs]]) -> np.ndarray:
    predictions = [arm.predict(event, memory) for event, memory in inputs]
    novel = predictions[-1]
    demand = np.linspace(-2., 2., 16)
    # The novel-family residual is tau0², so the production band kernel applies unchanged.
    band = M.band_probability(novel.mean[:, None] - demand, novel.variance[:, None], 0., (.7, .8))
    return np.concatenate([p.probabilities.ravel() for p in predictions] + [arm.mix(band).ravel()])


def benchmark() -> dict:
    costs = {k: [] for k in ("predecessor_cold", "candidate_cold", "full_grid_cold", "cached_inputs", "synthetic_next")}
    dimensions = {}
    for seed in S.SEEDS:
        data = S.generate("balanced", seed, n=1)
        for label, candidate, full in (("predecessor_cold", None, False), ("candidate_cold", S.Candidate(), False),
                                      ("full_grid_cold", S.Candidate(), True)):
            start = perf_counter()
            arm = S.MemoryArm(1, subject=True, candidate=candidate, full_grid=full)
            S.replay(data, arm)
            costs[label].append(perf_counter() - start)
            dimensions[label] = {"filters": arm.bank.B, "coordinates": arm.bank.d,
                                 "covariance_bytes": arm.bank.S.nbytes + arm.bank.S0.nbytes}
        fold = S.ReviewFold(1)
        for event, category in zip(data.events, data.categories, strict=True):
            fold.append(event, category)
        at = data.events[-1].at + 1
        start = perf_counter()
        for _ in range(100):
            frozen = next_inputs(fold, at)
        costs["cached_inputs"].append((perf_counter() - start) / 100)
        start = perf_counter()
        for _ in range(100):
            synthetic_next(arm, frozen)
        costs["synthetic_next"].append((perf_counter() - start) / 100)
    return {key: {"median_seconds": float(np.median(values)), "min_seconds": min(values), "max_seconds": max(values),
                  "seeds": len(S.SEEDS), "calls_per_seed": 100 if key in ("cached_inputs", "synthetic_next") else 1,
                  **dimensions.get(key, {})} for key, values in costs.items()}


def run_registered() -> dict:
    start = perf_counter()
    results = {}
    for world in S.WORLDS:
        grouped = {view: {} for view in ("subject", "lo", "baselines")}
        for seed in S.SEEDS:
            data = S.generate(world, seed)
            masks = strata(data)
            for view, subject in (("subject", True), ("lo", False)):
                arms = {"predecessor": None, **S.candidates(subject)}
                for name, candidate in arms.items():
                    arm = S.MemoryArm(data.n, subject=subject, candidate=candidate)
                    result = S.replay(data, arm)
                    grouped[view].setdefault(name, []).append({"p": result.probabilities, "y": data.categories == 2,
                        "covered": result.covered, "recovery": result.recovery, "rho_weights": result.rho_weights})
            for name, probabilities in baseline_predictions(data).items():
                grouped["baselines"].setdefault(name, []).append({"p": probabilities, "y": data.categories == 2,
                                                                  "covered": None})
        results[world] = {view: {name: summarize(runs, masks) for name, runs in values.items()} for view, values in grouped.items()}
    grid_seconds = perf_counter() - start
    return {"seeds": list(S.SEEDS), "worlds": list(S.WORLDS), "learners_per_seed": S.LEARNERS,
            "trajectories": len(S.SEEDS) * len(S.WORLDS) * S.LEARNERS,
            "presentations": len(S.SEEDS) * len(S.WORLDS) * S.LEARNERS * len(S.schedule()),
            "results": results, "selection": selection_findings(results), "candidate_grid_seconds": grid_seconds,
            "floor": [S.variance_floor(effect_scale=scale) for scale in (.25, 1., 4.)],
            "warmth": [S.warmth_check(ladder, h) for ladder in S.LADDERS for h in S.CURVE_HOURS],
            "cost": benchmark(), "seconds": perf_counter() - start}
