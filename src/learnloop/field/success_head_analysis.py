"""The pre-registered T8 analysis: a harness hook returning aggregates only.

The three-way interval rule, the gated heads and the descriptive comparisons,
exactly as recorded in ``docs/reviews/slice-2-t8.md`` and frozen in
``success_head.PREREGISTRATION`` (v3). Every interval in the T8 report
resamples items, a drawn item bringing all its attempts: this analysis's own
and, through the harness's ``bootstrap_unit="item"``, report 1's metrics and
comparisons and report 2's miss rates. It reads the harness's in-memory arrays
and never exports a row.
"""
from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping

import numpy as np

from learnloop.field.evaluation import ReplayArrays, _loss, paired_bootstrap
from learnloop.field.success_head import (
    EXPLICIT_ARMS, GATED_ARMS, LLM_ARMS, PREREGISTRATION, PRIMARY_ARM, preregistration_hash,
)


def _comparison(arrays: ReplayArrays, challenger: str, baselines: Iterable[str]) -> dict:
    predictions = arrays.predictions
    if arrays.item_clusters is None or len(arrays.item_clusters) != len(arrays.outcomes):
        raise ValueError("The T8 analysis resamples items: the harness must supply item clusters")
    clusters = np.asarray(arrays.item_clusters)
    baselines = [name for name in baselines if name in predictions and name != challenger]
    if challenger not in predictions:
        return {"status": "unavailable", "reason": "arm not run"}
    if not baselines:
        return {"status": "unavailable", "reason": "no baseline arm"}
    common = arrays.ability & np.isfinite(predictions[challenger])
    for name in baselines:
        common &= np.isfinite(predictions[name])
    y = arrays.outcomes
    if not common.any():
        return {"status": "unavailable", "reason": "no common scored attempts", "n": 0}
    losses = {name: float(_loss(y[common], predictions[name][common]).mean()) for name in baselines}
    best = min(baselines, key=lambda name: (losses[name], name))
    differences = _loss(y, predictions[best]) - _loss(y, predictions[challenger])
    result = {
        "status": "computed", "baseline": best, "n": int(common.sum()),
        "baseline_log_loss": losses,
        "challenger_log_loss": float(_loss(y[common], predictions[challenger][common]).mean()),
        "log_loss_gain": paired_bootstrap(differences[common], samples=arrays.bootstrap_samples,
                                          seed=arrays.seed, clusters=clusters[common]),
        "splits": {},
    }
    for dimension in ("item_position", "attempt_position"):
        groups: dict[str, list[int]] = {}
        for index, label in enumerate(arrays.labels):
            groups.setdefault(label.get(dimension, "unknown"), []).append(index)
        result["splits"][dimension] = {}
        for value, indexes in sorted(groups.items()):
            mask = np.zeros(len(y), dtype=bool)
            mask[indexes] = True
            mask &= common
            result["splits"][dimension][value] = paired_bootstrap(
                differences[mask], samples=arrays.bootstrap_samples, seed=arrays.seed,
                clusters=clusters[mask])
    return result


def _number(value: float) -> str:
    return f"{value:.4g}"


def _verdict(comparison: dict, ability_scored: int) -> dict:
    """The v3 three-way rule on the 95% item-cluster interval of the gain."""
    margin = PREREGISTRATION["margin_nats_per_attempt"]
    worthwhile = PREREGISTRATION["smallest_worthwhile_gain_nats_per_attempt"]
    n = comparison.get("n", 0)
    gain = comparison.get("log_loss_gain") or {}
    interval = gain.get("ci95")
    coverage = n / ability_scored if ability_scored else 0.0
    caveats = ["partial_coverage"] if coverage < PREREGISTRATION["coverage_caveat_below"] else []
    if comparison["status"] != "computed":
        decision = "insufficient_data"
        reason = f"no interval: {comparison.get('reason', comparison['status'])}"
    elif interval is None:
        decision = "insufficient_data"
        reason = f"no interval: {gain.get('degenerate') or 'not computable'}"
    elif interval[0] > margin:
        decision = "embeddings_add_value"
        reason = f"lower bound {_number(interval[0])} > m = {margin}"
        if interval[1] < worthwhile:
            reason += (f"; the whole interval is below δ = {worthwhile}, so the gain is real "
                       "but smaller than the smallest worth building")
    elif interval[1] < worthwhile:
        decision = "kill"
        reason = (f"upper bound {_number(interval[1])} < δ = {worthwhile}: any gain is smaller "
                  "than the smallest worth building")
    else:
        decision = "insufficient_data"
        reason = (f"undecided: lower bound {_number(interval[0])} <= m = {margin} and upper bound "
                  f"{_number(interval[1])} >= δ = {worthwhile}; more attempts narrow the interval")
    return {"decision": decision, "reason": reason, "n": n, "item_clusters": gain.get("clusters", 0),
            "mean": gain.get("mean"), "ci95": interval, "margin_nats_per_attempt": margin,
            "smallest_worthwhile_gain_nats_per_attempt": worthwhile, "coverage": coverage,
            "caveats": caveats}


def make_t8_analysis(*, unavailable: Mapping[str, str] | None = None) -> Callable[[ReplayArrays], dict]:
    """The pre-registered T8 analysis as a harness hook (aggregates only).

    ``unavailable`` names arms deliberately not run, with the reason (for
    example no solver-panel difficulty, or no prepared LLM cache).
    """
    unavailable = dict(unavailable or {})

    def analysis(arrays: ReplayArrays) -> dict:
        if arrays.bootstrap_unit != "item":
            # One unit per report: the T8 registration resamples items in every interval.
            raise ValueError("The T8 report resamples items: run the harness with bootstrap_unit='item'")
        ability_scored = int(arrays.ability.sum())
        primary = _comparison(arrays, PRIMARY_ARM, EXPLICIT_ARMS)
        verdict = _verdict(primary, ability_scored)
        # Hierarchical: each gated comparison is read only if every earlier
        # one (the primary first) was embeddings_add_value; kill,
        # insufficient_data or an unavailable arm closes the gate.
        gate_open = verdict["decision"] == "embeddings_add_value"
        gated = {}
        for arm in GATED_ARMS:
            if arm in unavailable:
                gated[arm] = {"status": "unavailable", "reason": unavailable[arm]}
                gate_open = False
                continue
            comparison = _comparison(arrays, arm, EXPLICIT_ARMS)
            if comparison["status"] == "computed":
                gated_verdict = _verdict(comparison, ability_scored)
                comparison["verdict"] = gated_verdict["decision"]
                comparison["verdict_reason"] = gated_verdict["reason"]
            comparison["interpretation"] = "interpreted" if gate_open else "not_interpreted"
            gate_open = gate_open and comparison.get("verdict") == "embeddings_add_value"
            gated[arm] = comparison
        descriptive = {"emb_ridge_vs_tag_logistic": _comparison(arrays, PRIMARY_ARM, ["tag_logistic"])}
        for arm in LLM_ARMS:
            if arm in unavailable:
                descriptive[arm] = {"status": "unavailable", "reason": unavailable[arm]}
                continue
            descriptive[arm] = {
                "vs_best_explicit": _comparison(arrays, arm, EXPLICIT_ARMS),
                "vs_emb_ridge": _comparison(arrays, arm, [PRIMARY_ARM]),
            }
        registered = PREREGISTRATION["bootstrap"]
        deviations = [
            name for name, value in (("bootstrap_samples", arrays.bootstrap_samples), ("seed", arrays.seed))
            if value != registered["samples" if name == "bootstrap_samples" else "seed"]
        ]
        return {
            "preregistration": {"version": PREREGISTRATION["version"], "hash": preregistration_hash(),
                                "deviations": deviations},
            "ability_scored_attempts": ability_scored,
            "primary": {"arm": PRIMARY_ARM, "explicit_arms": list(EXPLICIT_ARMS),
                        "comparison": primary, "verdict": verdict},
            "gated": gated,
            "descriptive": descriptive,
            "kill_rule": ("If the primary verdict is kill (the 95% item-cluster interval's upper bound "
                          f"is below δ = {verdict['smallest_worthwhile_gain_nats_per_attempt']} nats "
                          "per attempt), embeddings add no held-out predictive value worth building "
                          "on and the GP success head is not pursued (Slice 2 §11). "
                          "insufficient_data is no decision: rerun with more data."),
            "activates": False,
        }

    return analysis


def _span(interval) -> str:
    return "none" if interval is None else f"[{_number(interval[0])}, {_number(interval[1])}]"


def summary_lines(analysis: Mapping) -> list[str]:
    """Aggregate-only markdown for the top of the T8 report."""
    primary = analysis["primary"]
    comparison, verdict = primary["comparison"], primary["verdict"]
    mean = verdict["mean"]
    lines = [
        "## T8 pre-registered verdict", "",
        f"- Pre-registration: `{analysis['preregistration']['version']}` "
        f"(hash `{analysis['preregistration']['hash'][:16]}`); deviations: "
        f"{', '.join(analysis['preregistration']['deviations']) or 'none'}.",
        f"- Primary: `{primary['arm']}` vs best explicit arm `{comparison.get('baseline', 'n/a')}`: "
        f"n = {verdict['n']} common attempts in {verdict['item_clusters']} item clusters.",
        f"- Log-loss gain per attempt, loss(e*) − loss(`{primary['arm']}`): mean "
        f"{'none' if mean is None else _number(mean)}; 95% item-cluster interval {_span(verdict['ci95'])}.",
        f"- Rule: `embeddings_add_value` if the lower bound > m = {verdict['margin_nats_per_attempt']}; "
        f"`kill` if the upper bound < δ = {verdict['smallest_worthwhile_gain_nats_per_attempt']}; "
        "otherwise `insufficient_data`.",
        f"- **Decision: {verdict['decision']}**: {verdict['reason']}"
        + (f" (caveats: {', '.join(verdict['caveats'])})" if verdict["caveats"] else "")
        + f"; coverage {verdict['coverage']:.3f} of ability-scored attempts.",
    ]
    for arm, result in analysis["gated"].items():
        if result.get("status") != "computed":
            lines.append(f"- Gated `{arm}`: {result.get('status')} ({result.get('reason', '')}).")
        else:
            gain = result["log_loss_gain"]
            lines.append(f"- Gated `{arm}` ({result['interpretation']}): {result['verdict']}, "
                         f"{result['verdict_reason']}; mean gain {_number(gain['mean'])}, 95% "
                         f"item-cluster interval {_span(gain['ci95'])}, n = {result['n']} in "
                         f"{gain['clusters']} item clusters.")
    lines.append("- Nothing is activated; T8 has no live consumer.")
    return lines
