"""Store-free, attempt-paired prequential evaluation. Never activates an arm.

This is the single offline harness behind ``learnloop eval``: the learner-field
reports 1-2 and the PF-a families report are arm selections over the same
replay loop. The only prediction input is immutable ItemFeatures. All
predictions for an attempt (including its facets) finish before any arm
receives its observation. Ability arms score positive-mass attempts; PF-a
memory arms score graded cold retrievals (``AttemptRow.memory_scored``), so
their sample counts can differ and each arm abstains on the other's rows.
Reports contain aggregates, not rows, prompts, answers, or readable topic names.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import asdict, replace
from hashlib import sha256
import json
from math import erf, isfinite, log, sqrt
from pathlib import Path
from typing import Iterable, Mapping

import numpy as np

from learnloop.clock import parse_utc
from learnloop.field import memory as _memory_arms  # noqa: F401 - registers the PF-a memory arms
from learnloop.field.predictors import create_predictor, registered_predictors
from learnloop.field.signals import blocks_fast_track
from learnloop.field.types import AttemptRow, FacetRow, ObservationRow, SignalRow


HARNESS_VERSION = "field-prequential-v2"

MEMORY_LIMITATIONS = (
    "Memory arms admit uncalibrated graded cold retrievals; ability arms require positive "
    "effective mass. Their sample counts can differ; comparisons pair only common attempts.",
    "Current fitted FSRS weights may include evaluation outcomes; the defaults arms are the "
    "strictly fixed-weight comparison.",
    "Current authored family assignments are a retrospective grouping, not historical family knowledge.",
    "Missing skeleton distances receive no invented discount; compare distance coverage before "
    "interpreting the distance arms.",
)


def family_arms() -> tuple[str, ...]:
    """The PF-a report's arm set: incumbent, lo_general, idea_hier and memory arms."""
    return registered_predictors(group="families")


def _hash(value: object) -> str:
    return sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                             allow_nan=False).encode()).hexdigest()


def report_digest(report: Mapping) -> str:
    """Content address of an aggregate report (names the families report files)."""
    return _hash(report)


def _time(row):
    value = parse_utc(row.observed_at)
    if value is None:
        raise ValueError("Every observation needs a valid timestamp")
    return value


def _uses_memory(arm) -> bool:
    return bool(getattr(arm, "uses_graded_memory", False))


def _eligible(row):
    if row.revision_status == "excluded":
        return False
    # An assistance-only zero is still assessable by the hint-replacement
    # arms. All arms predict the same rubric outcome; arms without replacement
    # keep their zero-mass posterior unchanged. Quarantine zeros both masses.
    replacement = row.mass_without_assistance
    return (
        isfinite(row.effective_mass) and row.effective_mass > 0
        or bool(row.hints_used or row.help_before_work)
        and replacement is not None and isfinite(replacement) and replacement > 0
    )


def _loss(y, p):
    return -y * np.log(p) - (1 - y) * np.log1p(-p)


def _interval(values):
    if not values:
        return None
    return [float(x) for x in np.quantile(values, [0.025, 0.975])]


def paired_bootstrap(differences, *, samples=1000, seed=0):
    """One difference per attempt: the same sampled attempt indexes pair arms."""
    values = np.asarray(differences, dtype=float)
    if not len(values):
        return {"n": 0, "mean": None, "ci95": None}
    rng = np.random.default_rng(seed)
    means = [float(values[rng.integers(0, len(values), len(values))].mean())
             for _ in range(samples)]
    return {"n": len(values), "mean": float(values.mean()), "ci95": _interval(means)}


def _auc(y, p):
    # AUC has no unambiguous binary interpretation for fractional rubric scores.
    binary = (y == 0) | (y == 1)
    y, p = y[binary], p[binary]
    positives, negatives = int(sum(y == 1)), int(sum(y == 0))
    if not positives or not negatives:
        return None, len(y)
    order = np.argsort(p, kind="stable")
    p, y = p[order], y[order]
    concordant = below = 0.0
    i = 0
    while i < len(p):
        j = i + 1
        while j < len(p) and p[j] == p[i]:
            j += 1
        pos, neg = sum(y[i:j] == 1), sum(y[i:j] == 0)
        concordant += pos * (below + neg / 2)
        below += neg
        i = j
    return float(concordant / (positives * negatives)), len(y)


def _metrics(y, p, samples, seed):
    y, p = np.asarray(y), np.asarray(p)
    loss, brier = _loss(y, p), (y - p) ** 2
    auc, auc_n = _auc(y, p)
    reliability = []
    for i in range(10):
        mask = (p >= i / 10) & (p < (i + 1) / 10)
        reliability.append({
            "lower": i / 10, "upper": (i + 1) / 10, "n": int(sum(mask)),
            "predicted": float(p[mask].mean()) if any(mask) else None,
            "observed": float(y[mask].mean()) if any(mask) else None,
        })
    return {
        "n": len(y),
        "log_loss": paired_bootstrap(loss, samples=samples, seed=seed),
        "brier": paired_bootstrap(brier, samples=samples, seed=seed),
        "auc": auc, "auc_binary_n": auc_n, "reliability": reliability,
    }


def _wilson(failures, n):
    if not n:
        return None
    p, z = failures / n, 1.959963984540054
    center = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return [max(0., center - half), min(1., center + half)]


def _paired_miss_improvement(baseline, challenger, *, samples, seed):
    """Paired attempt-cluster resampling with each policy's own denominator."""
    left, right = dict(baseline), dict(challenger)
    keys = sorted(left.keys() | right.keys())
    if not left or not right:
        return {"n": len(keys), "mean": None, "ci95": None}
    rng = np.random.default_rng(seed)
    draws = []
    for _ in range(samples):
        indexes = [keys[i] for i in rng.integers(0, len(keys), len(keys))]
        a, b = [left[i] for i in indexes if i in left], [right[i] for i in indexes if i in right]
        if a and b:
            draws.append(float(np.mean(a) - np.mean(b)))
    return {"n": len(keys), "mean": float(np.mean(list(left.values())) - np.mean(list(right.values()))),
            "ci95": _interval(draws)}


def _known_probability(arm, lo_id):
    if not getattr(arm, "calibrated_uncertainty", False):
        return None
    regions = arm.region_estimates()
    region = regions.get(lo_id) or regions.get(f"lo:{lo_id}")
    if region is None or region.untested:
        return None
    if not isfinite(region.mean) or not isfinite(region.variance) or region.variance < 0:
        raise ValueError("Invalid calibrated region uncertainty")
    threshold = log(3)  # logit(.75), on ability, not item success probability.
    if region.variance == 0:
        return float(region.mean > threshold)
    return (1 + erf((region.mean - threshold) / sqrt(2 * region.variance))) / 2


def _groups(rows):
    """Validate a complete attempt+facet stream before any arm is called."""
    attempts, facets, signals = {}, defaultdict(list), []
    for row in rows:
        _time(row)
        if isinstance(row, SignalRow):
            signals.append(row)
            continue
        if not isinstance(row, AttemptRow):
            raise TypeError("Evaluation accepts only immutable observation rows")
        if not isfinite(row.outcome) or not 0 <= row.outcome <= 1:
            raise ValueError("Outcome must be finite and in [0, 1]")
        if not isfinite(row.effective_mass) or row.effective_mass < 0:
            raise ValueError("Effective mass must be finite and nonnegative")
        if isinstance(row, FacetRow):
            facets[row.attempt_id].append(row)
        elif row.attempt_id in attempts:
            raise ValueError("Duplicate attempt rows; resolve grading epochs first")
        else:
            attempts[row.attempt_id] = row
    for attempt_id, group in facets.items():
        if attempt_id not in attempts:
            raise ValueError("Facet rows require their authoritative attempt row")
        attempt = attempts[attempt_id]
        if len({r.facet_id for r in group}) != len(group):
            raise ValueError("Duplicate facets within an attempt")
        if (any(not isfinite(r.facet_share) or r.facet_share < 0 for r in group)
                or abs(sum(r.facet_share for r in group) - 1) > 1e-8):
            raise ValueError("Facet shares must sum to one")
        if any(r.features != attempt.features for r in group):
            raise ValueError("Facet and attempt features must describe the same item")
    events = [(row, sorted(facets[key], key=lambda x: x.facet_id))
              for key, row in attempts.items()]
    events.extend((s, []) for s in signals)
    # Tied-time signals follow all attempts: a post-grade question cannot leak
    # into the attempt merely because its clock has second resolution.
    events.sort(key=lambda pair: (
        _time(pair[0]), isinstance(pair[0], SignalRow),
        (pair[0].signal_id if isinstance(pair[0], SignalRow) else pair[0].attempt_id),
    ))
    return events


def evaluate(
    rows: Iterable[ObservationRow], *, arms=None, bootstrap_samples=1000, seed=0,
    config: Mapping | None = None, general_means=None, lo_priors=None,
    fast_track_q=0.9, fast_track_min_correct=2, switching_margin=0.0,
    fsrs_weights=None, fsrs_fit_id=None, pairwise=(),
):
    """Return JSON-ready report1/report2/manifest/recommendation aggregates.

    ``arms`` accepts names or freshly constructed store-free predictor instances.
    Claims/priors, if supplied, must be frozen before the earliest observation.
    No current database state or full future item catalogue is passed to an arm.
    The conservative q=.9 is fixed before replay; .8 requires the caller's
    prior decision that report-2 evidence is sufficient, never fitting this run.
    ``fsrs_weights`` is the caller-resolved current FSRS fit for the memory
    arms (``fsrs_fit_id`` its provenance); without it they use the defaults.
    ``pairwise`` names ``(baseline, challenger)`` arm pairs to compare on
    their common attempts (log-loss improvement of the challenger, overall
    and on first attempts at a never-seen LO, against ``switching_margin``).
    It reports; it never recommends or activates.
    """
    if bootstrap_samples < 1:
        raise ValueError("bootstrap_samples must be positive")
    if fast_track_q not in (0.8, 0.9) or fast_track_min_correct < 2:
        raise ValueError("Fast-track requires q=.8 or .9 and at least two answers")
    if not isfinite(switching_margin) or switching_margin < 0:
        raise ValueError("Switching margin must be nonnegative and fixed before replay")
    config = dict(config or {})
    events = _groups(tuple(rows))
    kwargs = {"general_means": general_means, "lo_priors": lo_priors,
              "fsrs_weights": tuple(fsrs_weights) if fsrs_weights is not None else None}
    if "mastery" in config:
        from learnloop.config import MasteryConfig
        kwargs["config"] = MasteryConfig.model_validate(config["mastery"])
    selected = registered_predictors() if arms is None else tuple(arms)
    predictors = [create_predictor(a, **kwargs) if isinstance(a, str) else a for a in selected]
    names = [a.name for a in predictors]
    if not names or len(names) != len(set(names)):
        raise ValueError("Choose at least one arm, with unique names")
    if any(a.granularity not in ("attempt", "facet") for a in predictors):
        raise ValueError("Arm granularity must be attempt or facet")
    memory_names = {a.name for a in predictors if _uses_memory(a)}
    if any(predictors[names.index(name)].granularity != "attempt" for name in memory_names):
        raise ValueError("Memory arms review attempts, not facets")

    seen, blocked, initial_correct = set(), set(), Counter()
    predictions, outcomes, labels, ability_rows = defaultdict(list), [], [], []
    assumed = {name: set() for name in names}
    later = {name: [] for name in names}
    counts, revisions = Counter(), Counter()
    for row, facets in events:
        if isinstance(row, SignalRow):
            counts["signals"] += 1
            if blocks_fast_track(row):
                blocked.add(row.lo_id)
            for arm in predictors:
                arm.observe(row)
            continue
        revisions[row.revision_status] += 1
        counts["attempts"] += 1
        counts["zero_ability_mass"] += not (isfinite(row.effective_mass) and row.effective_mass > 0)
        counts["memory_scored"] += row.memory_scored
        counts["memory_training"] += row.memory_eligible
        counts["missing_variant_distance"] += (
            row.memory_scored and row.features.family_id is not None
            and row.features.variant_distance is None
        )
        first = row.lo_id not in seen
        seen.add(row.lo_id)
        ability = _eligible(row)
        memory = bool(memory_names) and row.memory_scored
        if not ability and not memory:
            counts["excluded"] += 1
            blocked.add(row.lo_id)  # unknown initial answers cannot establish fast-track
            continue
        counts["ability_scored"] += ability
        values = {}
        for arm in predictors:
            if arm.name in memory_names:
                if not (memory and arm.scores(row)):
                    values[arm.name] = float("nan")
                    continue
                p = arm.predict(row.features)
            elif not ability:
                # A memory-only graded retrieval is not ability evidence.
                values[arm.name] = float("nan")
                continue
            elif arm.granularity == "facet":
                if not facets:
                    # No measured facet is not a synthetic generic facet. This
                    # arm abstains; paired comparisons use common attempts only.
                    values[arm.name] = float("nan")
                    continue
                ps = [arm.predict(replace(row.features, facet_id=f.facet_id,
                                          facet_share=f.facet_share)) for f in facets]
                if any(not isfinite(p) or not 0 < p < 1 for p in ps):
                    raise ValueError("Arms must predict finite probabilities in (0, 1)")
                p = sum(f.facet_share * p for f, p in zip(facets, ps))
            else:
                p = arm.predict(row.features)
            if not isfinite(p) or not 0 < p < 1:
                raise ValueError("Arms must predict finite probabilities in (0, 1)")
            values[arm.name] = p
        ability_rows.append(ability)
        family_id = row.features.family_id
        # Outcomes are not handed to ANY arm until EVERY prediction has completed.
        outcomes.append(row.outcome)
        labels.append({
            "attempt_position": "first_unseen_lo" if first else "later",
            "serving_origin": row.serving_origin if row.serving_origin in {
                "learner_pick", "system_probe", "forced_followup", "requested", "unknown"
            } else "unknown",
            "revision_status": row.revision_status if row.revision_status in {
                "exact", "reconstructed_current", "excluded"
            } else "unknown",
            "topic": _hash([row.features.subject_id, row.lo_id])[:16],
            "questions_or_hints": "with" if row.preceded_by_question or row.hints_used else "without",
            "questions": "with" if row.preceded_by_question else "without",
            "hints": "with" if row.hints_used else "without",
            "relation": row.features.variant_relation or ("unrelated" if family_id else "unfamilied"),
            "retrieval": "cold" if row.retrieval_cold else "warm",
            "grader_model": row.grader_model,
            "calibration_status": row.calibration_status,
            "family_judge_model": "+".join(row.family_judge_models) or (
                "authored" if family_id else "unfamilied"),
        })
        clean_correct = (ability and row.outcome == 1 and row.features.cold and not row.features.primed
                         and not row.assisted and not row.hints_used and not row.help_before_work)
        if not clean_correct:
            blocked.add(row.lo_id)
        if row.lo_id not in blocked:
            initial_correct[row.lo_id] += 1
        for arm in predictors:
            predictions[arm.name].append(values[arm.name])
            if arm.name not in memory_names and not ability:
                # Ability arms never see a row they could not score.
                continue
            if ability and row.lo_id in assumed[arm.name]:
                later[arm.name].append((len(outcomes) - 1, float(row.outcome < 1)))
            if arm.granularity == "facet":
                for facet in facets:
                    arm.observe(facet)
            else:
                arm.observe(row)
            if (ability and row.lo_id not in assumed[arm.name] and row.lo_id not in blocked
                    and initial_correct[row.lo_id] >= fast_track_min_correct):
                p_known = _known_probability(arm, row.lo_id)
                if p_known is not None and p_known >= fast_track_q:
                    assumed[arm.name].add(row.lo_id)

    y = np.asarray(outcomes)
    ability_mask = np.asarray(ability_rows, dtype=bool)
    splits = defaultdict(lambda: defaultdict(list))
    for i, label in enumerate(labels):
        for dimension, value in label.items():
            splits[dimension][value].append(i)
    report1, report2 = {}, {}
    for name in names:
        p = np.asarray(predictions[name])
        valid = np.isfinite(p)
        arm = predictors[names.index(name)]
        report1[name] = {
            "model": getattr(arm, "model", "not_used"),
            "scores": "graded_cold_retrievals" if name in memory_names else "positive_mass_attempts",
            "missing_facet_exclusions": int(sum(ability_mask & ~valid)) if arm.granularity == "facet" else 0,
            "unscored_attempts": int(sum(~valid)),
            "overall": _metrics(y[valid], p[valid], bootstrap_samples, seed),
            "splits": {
                dimension: {value: _metrics(y[indexes][valid[indexes]], p[indexes][valid[indexes]],
                                           bootstrap_samples, seed)
                            for value, indexes in sorted(groups.items())}
                for dimension, groups in sorted(splits.items())
            },
        }
        failures = [v for _, v in later[name]]
        report2[name] = {
            "eligible_uncertainty": bool(getattr(predictors[names.index(name)], "calibrated_uncertainty", False)),
            "historical_los": len(seen), "assumed_los": len(assumed[name]),
            "assumed_share": len(assumed[name]) / len(seen) if seen else None,
            "assumed_share_ci95": _wilson(len(assumed[name]), len(seen)),
            "later_attempts": len(failures), "later_failures": int(sum(failures)),
            "miss_rate": paired_bootstrap(failures, samples=bootstrap_samples, seed=seed),
            # Wilson remains informative with zero observed misses / tiny samples.
            "miss_rate_wilson_ci95": _wilson(sum(failures), len(failures)),
        }

    comparisons, candidates = {}, []
    if "mastery_ekf" in names:
        baseline_loss = _loss(y, np.asarray(predictions["mastery_ekf"]))
        first_indexes = splits["attempt_position"].get("first_unseen_lo", [])
        for name in names:
            if name == "mastery_ekf":
                continue
            differences = baseline_loss - _loss(y, np.asarray(predictions[name]))
            overall = paired_bootstrap(differences[np.isfinite(differences)], samples=bootstrap_samples, seed=seed)
            first_differences = differences[first_indexes]
            first = paired_bootstrap(first_differences[np.isfinite(first_differences)], samples=bootstrap_samples, seed=seed)
            miss_improvement = _paired_miss_improvement(
                later["mastery_ekf"], later[name], samples=bootstrap_samples, seed=seed)
            # No observed later reviews is uncertainty, not a zero miss rate.
            no_worse = (miss_improvement["ci95"] is not None
                        and miss_improvement["ci95"][0] >= 0
                        and miss_improvement["mean"] >= 0)
            clears = all(stat["ci95"] is not None and stat["ci95"][0] > switching_margin
                         for stat in (overall, first))
            eligible_name = name == "lo_general" or name.startswith("lo_general+") or name == "idea_hier"
            recommend = bool(clears and no_worse and eligible_name and
                             report2[name]["eligible_uncertainty"] and ":" not in name)
            comparisons[name] = {"log_loss_improvement": overall, "first_log_loss_improvement": first,
                                 "report2_miss_improvement": miss_improvement,
                                 "report2_miss_no_worse": no_worse, "recommend_review": recommend}
            if recommend:
                candidates.append(name)
    pairs = {}
    first_indexes = splits["attempt_position"].get("first_unseen_lo", [])
    for baseline, challenger in pairwise:
        if baseline not in names or challenger not in names:
            raise ValueError(f"Pairwise comparison names an unselected arm: {baseline} vs {challenger}")
        differences = _loss(y, np.asarray(predictions[baseline])) - _loss(y, np.asarray(predictions[challenger]))
        overall = paired_bootstrap(differences[np.isfinite(differences)], samples=bootstrap_samples, seed=seed)
        first_differences = differences[first_indexes]
        first = paired_bootstrap(first_differences[np.isfinite(first_differences)],
                                 samples=bootstrap_samples, seed=seed)
        pairs[f"{challenger} vs {baseline}"] = {
            "baseline": baseline, "challenger": challenger,
            "log_loss_improvement": overall, "first_log_loss_improvement": first,
            "clears_margin": {
                key: stat["ci95"] is not None and stat["ci95"][0] > switching_margin
                for key, stat in (("overall", overall), ("first", first))
            },
        }
    memory_manifest = None
    if memory_names:
        from learnloop.scheduling.family_memory_model import weights_digest
        from learnloop.scheduling.fsrs import FSRS6_DEFAULT_WEIGHTS

        current = tuple(fsrs_weights) if fsrs_weights is not None else FSRS6_DEFAULT_WEIGHTS
        memory_manifest = {
            "weights": {
                "current_fit": {"values": list(current), "hash": weights_digest(current),
                                "fit_id": fsrs_fit_id,
                                "is_defaults": fsrs_weights is None or fsrs_fit_id is None},
                "defaults": {"values": list(FSRS6_DEFAULT_WEIGHTS),
                             "hash": weights_digest(FSRS6_DEFAULT_WEIGHTS)},
            },
            "family_grouping": "current authored assignment, applied retrospectively",
            "distance_source": "unavailable: PF-b skeleton measurements not present",
            "training": "graded cold same_target/isomorph or unfamilied retrievals; near/far are probes",
            "cold_start_probability": 0.5,
        }
    manifest = {
        "harness": HARNESS_VERSION, "algorithm": config.get("algorithms", {}).get("algorithm_version", "unspecified"),
        "kernel": "not_used", "embedding_model": "not_used",
        "config_hash": _hash(config), "data_snapshot": _hash([
            {"row_type": type(r).__name__, "row": asdict(r), "facets": [asdict(f) for f in fs]}
            for r, fs in events]),
        "arm_hashes": {a.name: a.version_hash for a in predictors},
        "arm_models": {a.name: getattr(a, "model", "not_used") for a in predictors},
        "bootstrap": {"unit": "attempt", "paired": True, "samples": bootstrap_samples, "seed": seed},
        "frozen_policy": {"fast_track_q": fast_track_q, "fast_track_min_correct": fast_track_min_correct,
                          "theta_known": log(3), "switching_margin": switching_margin},
        "prior_inputs_hash": _hash({"general_means": general_means, "lo_priors": lo_priors}),
        "claims": "caller_frozen_before_replay" if general_means or lo_priors else "unavailable_zero_prior",
        "prequential": True,
        "ordering": ["observed_at", "signals_after_attempts", "attempt_id"],
    }
    if memory_manifest is not None:
        manifest["memory"] = memory_manifest
    return {
        "manifest": manifest,
        "counts": {"attempts": counts["attempts"], "scored_attempts": len(y),
                   "ability_scored_attempts": counts["ability_scored"],
                   "memory_scored_attempts": counts["memory_scored"],
                   "memory_training_rows": counts["memory_training"],
                   "missing_variant_distance": counts["missing_variant_distance"],
                   "zero_ability_mass": counts["zero_ability_mass"],
                   "excluded_attempts": counts["excluded"], "signals": counts["signals"],
                   "revision_status": dict(sorted(revisions.items()))},
        "report1": {"arms": report1, "comparisons": comparisons, **({"pairwise": pairs} if pairs else {}),
                    "validity": "One learner; only large differences are detectable. Sweep results are exploratory.",
                    "limitations": list(MEMORY_LIMITATIONS) if memory_names else []},
        "report2": {"arms": report2, "bias": "History shows only what was actually served; not a causal off-policy estimate.",
                    "failure_definition": "Any later rubric fraction below 1; triggering initial answers excluded.",
                    "thin_data_conservative": fast_track_q == .9},
        "recommendation": {"decision": "review_challenger" if candidates else "keep_incumbent",
                           "candidates": candidates, "activates": False,
                           "requires": "Owner review, algorithm successor and kill switch; this report never activates."},
    }


def write_reports(report, output_dir, *, stem="evaluation", title="Learner-field evaluation"):
    """Write the aggregate report to the caller's explicitly chosen directory."""
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    json_path, markdown_path = directory / f"{stem}.json", directory / f"{stem}.md"
    payload = json.dumps(report, sort_keys=True, indent=2, allow_nan=False)
    json_path.write_text(payload + "\n", encoding="utf-8")
    lines = [
        f"# {title}", "",
        "Prequential: only past observations predict each outcome. No activation is performed.", "",
        "## Report 1: prequential replay", "",
        "| Arm | Scores | Attempts | Log loss | Brier | AUC (binary outcomes) |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for name, values in report["report1"]["arms"].items():
        m = values["overall"]
        lines.append(f"| {name} | {values['scores']} | {m['n']} | {m['log_loss']['mean']} | "
                     f"{m['brier']['mean']} | {m['auc']} |")
    lines.extend(["", report["report1"]["validity"], ""])
    lines.extend(f"- {value}" for value in report["report1"].get("limitations", ()))
    pairwise = report["report1"].get("pairwise") or {}
    if pairwise:
        lines.extend([
            "", "### Paired comparisons", "",
            "Positive means the challenger has lower log loss on the same attempts. "
            "Clears margin: the 95% bootstrap interval lies above the frozen switching margin.", "",
            "| Comparison | Attempts | Improvement | 95% CI | First-attempt improvement | 95% CI | Clears (overall, first) |",
            "|---|---:|---:|---|---:|---|---|",
        ])
        for label, values in pairwise.items():
            overall, first = values["log_loss_improvement"], values["first_log_loss_improvement"]
            clears = values["clears_margin"]
            lines.append(f"| {label} | {overall['n']} | {overall['mean']} | {overall['ci95']} | "
                         f"{first['mean']} | {first['ci95']} | {clears['overall']}, {clears['first']} |")
    lines.extend(["", "## Report 2: fast-track simulation", "",
                  report["report2"]["bias"], "", "| Arm | Assumed LOs | Later attempts | Miss rate | 95% Wilson CI |",
                  "|---|---:|---:|---:|---|"])
    for name, values in report["report2"]["arms"].items():
        lines.append(f"| {name} | {values['assumed_los']} | {values['later_attempts']} | "
                     f"{values['miss_rate']['mean']} | {values['miss_rate_wilson_ci95']} |")
    lines.extend(["", "## Counts", "", "```json",
                  json.dumps(report["counts"], sort_keys=True, indent=2), "```",
                  "", "## Full aggregate metrics, splits, intervals and manifest", "",
                  "Topic identifiers are one-way hashed. No individual attempts or learner text are exported.",
                  "", "```json", payload, "```", ""])
    markdown_path.write_text("\n".join(lines), encoding="utf-8")
    return {"json": str(json_path), "markdown": str(markdown_path)}
