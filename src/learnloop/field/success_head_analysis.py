"""The pre-registered T8 analysis: a harness hook returning aggregates only.

The kill rule, the gated heads and the descriptive comparisons, exactly as
recorded in ``docs/reviews/slice-2-t8.md`` and frozen in
``success_head.PREREGISTRATION``. It reads the harness's in-memory arrays and
never exports a row.
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
                                          seed=arrays.seed),
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
                differences[mask], samples=arrays.bootstrap_samples, seed=arrays.seed)
    return result


def _verdict(comparison: dict, ability_scored: int) -> dict:
    margin = PREREGISTRATION["margin_nats_per_attempt"]
    n = comparison.get("n", 0)
    coverage = n / ability_scored if ability_scored else 0.0
    caveats = ["partial_coverage"] if coverage < PREREGISTRATION["coverage_caveat_below"] else []
    if comparison["status"] != "computed" or n < PREREGISTRATION["min_common_attempts"]:
        decision = "insufficient_data"
    else:
        interval = comparison["log_loss_gain"]["ci95"]
        decision = "embeddings_add_value" if interval[0] > margin else "kill"
    return {"decision": decision, "margin_nats_per_attempt": margin, "coverage": coverage,
            "caveats": caveats}


def make_t8_analysis(*, unavailable: Mapping[str, str] | None = None) -> Callable[[ReplayArrays], dict]:
    """The pre-registered T8 analysis as a harness hook (aggregates only).

    ``unavailable`` names arms deliberately not run, with the reason (for
    example no solver-panel difficulty, or no prepared LLM cache).
    """
    unavailable = dict(unavailable or {})

    def analysis(arrays: ReplayArrays) -> dict:
        ability_scored = int(arrays.ability.sum())
        primary = _comparison(arrays, PRIMARY_ARM, EXPLICIT_ARMS)
        verdict = _verdict(primary, ability_scored)
        # Hierarchical: each gated comparison is read only if every earlier
        # one (the primary first) passed; any other outcome closes the gate.
        gate_open = verdict["decision"] == "embeddings_add_value"
        gated = {}
        for arm in GATED_ARMS:
            if arm in unavailable:
                gated[arm] = {"status": "unavailable", "reason": unavailable[arm]}
                gate_open = False
                continue
            comparison = _comparison(arrays, arm, EXPLICIT_ARMS)
            if comparison["status"] == "computed":
                comparison["verdict"] = _verdict(comparison, ability_scored)["decision"]
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
            "kill_rule": ("If the primary verdict is kill, embeddings add no held-out predictive value "
                          "and the GP success head is not pursued (Slice 2 §11)."),
            "activates": False,
        }

    return analysis


def summary_lines(analysis: Mapping) -> list[str]:
    """Aggregate-only markdown for the top of the T8 report."""
    primary = analysis["primary"]
    comparison, verdict = primary["comparison"], primary["verdict"]
    gain = comparison.get("log_loss_gain", {})
    lines = [
        "## T8 pre-registered verdict", "",
        f"- Pre-registration: `{analysis['preregistration']['version']}` "
        f"(hash `{analysis['preregistration']['hash'][:16]}`); deviations: "
        f"{', '.join(analysis['preregistration']['deviations']) or 'none'}.",
        f"- Primary: `{primary['arm']}` vs best explicit arm `{comparison.get('baseline', 'n/a')}` "
        f"on {comparison.get('n', 0)} common attempts.",
        f"- Log-loss gain per attempt: mean {gain.get('mean')}, 95% CI {gain.get('ci95')} "
        f"(margin {verdict['margin_nats_per_attempt']}).",
        f"- **Decision: {verdict['decision']}**"
        + (f" (caveats: {', '.join(verdict['caveats'])})" if verdict["caveats"] else "")
        + f"; coverage {verdict['coverage']:.3f} of ability-scored attempts.",
    ]
    for arm, result in analysis["gated"].items():
        if result.get("status") != "computed":
            lines.append(f"- Gated `{arm}`: {result.get('status')} ({result.get('reason', '')}).")
        else:
            lines.append(f"- Gated `{arm}` ({result['interpretation']}): gain "
                         f"{result['log_loss_gain']['mean']}, 95% CI {result['log_loss_gain']['ci95']}, "
                         f"n {result['n']}.")
    lines.append("- Nothing is activated; T8 has no live consumer.")
    return lines
