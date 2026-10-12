"""The pre-registered T8 analysis: a harness hook returning aggregates only.

The three-way interval rule, the gated heads and the descriptive comparisons,
exactly as recorded in ``docs/reviews/slice-2-t8.md`` and frozen in
``success_head.PREREGISTRATION`` (v4). Every interval in the T8 report
clusters on items. The verdict intervals (primary and gated) and the
descriptive ``emb_ridge_vs_tag_logistic`` comparison (the primary comparison
itself whenever e* is ``tag_logistic``) are cluster-robust t intervals (CR1,
df = items - 1); every other interval is a percentile item bootstrap (a drawn
item brings all its attempts): this analysis's splits and LLM comparisons
and, through the harness's ``bootstrap_unit="item"``, report 1 and report 2.
Each interval here names its ``method``. It reads the harness's in-memory
arrays and never exports a row.
"""
from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from decimal import ROUND_FLOOR, Decimal

import numpy as np

from learnloop.field.evaluation import (
    CLUSTER_T_METHOD, ReplayArrays, _loss, cluster_t_interval, paired_bootstrap,
)
from learnloop.field.success_head import (
    EXPLICIT_ARMS, GATED_ARMS, LLM_ARMS, PREREGISTRATION, PRIMARY_ARM, preregistration_hash,
)


BOOTSTRAP_METHOD = "item_bootstrap_percentile"


def _bootstrap(arrays: ReplayArrays, differences, clusters) -> dict:
    """A descriptive percentile item bootstrap, labelled with its method."""
    return {**paired_bootstrap(differences, samples=arrays.bootstrap_samples, seed=arrays.seed,
                               clusters=clusters), "method": BOOTSTRAP_METHOD}


def _comparison(arrays: ReplayArrays, challenger: str, baselines: Iterable[str], *,
                t_interval: bool = False) -> dict:
    """e* (the best of ``baselines``) against ``challenger`` on their common attempts.

    With ``t_interval`` (the verdict comparisons, and ``emb_ridge`` against
    ``tag_logistic``, which is the primary comparison whenever e* is
    ``tag_logistic``) the gain gets the cluster-robust t interval; any other
    comparison gets the descriptive item bootstrap. The splits are always
    descriptive.
    """
    predictions = arrays.predictions
    if arrays.item_clusters is None or len(arrays.item_clusters) != len(arrays.outcomes):
        raise ValueError("The T8 analysis clusters on items: the harness must supply item clusters")
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
        "log_loss_gain": (cluster_t_interval(differences[common], clusters[common]) if t_interval
                          else _bootstrap(arrays, differences[common], clusters[common])),
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
            result["splits"][dimension][value] = _bootstrap(arrays, differences[mask], clusters[mask])
    return result


def _number(value: float) -> str:
    return f"{value:.4g}"


def _bound(value: float, holds: Callable[[float], bool]) -> str:
    """``value`` at 4 significant figures, or as many more as it takes for the
    printed number to satisfy ``holds``, the comparison the reason states
    (review F3: 0.0049996 is not "0.005 < δ = 0.005")."""
    for digits in range(4, 18):
        text = f"{value:.{digits}g}"
        if holds(float(text)):
            return text
    return repr(value)


def _rounded_down(value: float) -> str:
    """``value`` rounded down to 4 significant figures, so "any δ <= it" stays true."""
    exact = Decimal(repr(value))
    if not exact:
        return "0"
    return _number(float(exact.quantize(Decimal(1).scaleb(exact.adjusted() - 3), rounding=ROUND_FLOOR)))


def _verdict(comparison: dict, ability_scored: int) -> dict:
    """The v4 three-way rule on the 95% cluster-robust t interval of the gain.

    ``kill`` if the upper bound is below δ, including a real gain below δ
    (``real_gain_below_delta``); otherwise ``embeddings_add_value`` if the
    lower bound is above m; otherwise ``insufficient_data``. The verdict is
    ``kill`` exactly when δ > ``flipping_delta`` (the upper bound), so that
    number is where a change of δ would change it. Every bound the reason
    prints reads on the side of m or δ that the rule says.
    """
    margin = PREREGISTRATION["margin_nats_per_attempt"]
    worthwhile = PREREGISTRATION["smallest_worthwhile_gain_nats_per_attempt"]
    n = comparison.get("n", 0)
    gain = comparison.get("log_loss_gain") or {}
    interval = gain.get("ci95")
    coverage = n / ability_scored if ability_scored else 0.0
    caveats = ["partial_coverage"] if coverage < PREREGISTRATION["coverage_caveat_below"] else []
    if comparison["status"] != "computed":
        decision, code = "insufficient_data", "no_interval"
        reason = f"no interval: {comparison.get('reason', comparison['status'])}"
    elif interval is None:
        decision, code = "insufficient_data", "no_interval"
        reason = f"no interval: {gain.get('degenerate') or 'not computable'}"
    elif interval[1] < worthwhile and interval[0] > margin:
        decision, code = "kill", "real_gain_below_delta"
        reason = (f"lower bound {_bound(interval[0], lambda v: v > margin)} > m = {margin} but "
                  f"upper bound {_bound(interval[1], lambda v: v < worthwhile)} < δ = {worthwhile}: "
                  "the gain is real but smaller than the smallest worth building (it would be "
                  f"embeddings_add_value for any δ <= {_rounded_down(interval[1])}); provisional: "
                  "the realized gain includes the embedding block's learning period, so rerun "
                  "when the data has grown")
    elif interval[1] < worthwhile:
        decision, code = "kill", "upper_bound_below_delta"
        reason = (f"upper bound {_bound(interval[1], lambda v: v < worthwhile)} < δ = {worthwhile}: "
                  "any gain is smaller than the smallest worth building")
    elif interval[0] > margin:
        decision, code = "embeddings_add_value", "lower_bound_above_margin"
        reason = (f"lower bound {_bound(interval[0], lambda v: v > margin)} > m = {margin} and "
                  f"upper bound {_bound(interval[1], lambda v: v >= worthwhile)} >= δ = {worthwhile}")
    else:
        decision, code = "insufficient_data", "undecided"
        reason = (f"undecided: lower bound {_bound(interval[0], lambda v: v <= margin)} <= m = "
                  f"{margin} and upper bound {_bound(interval[1], lambda v: v >= worthwhile)} >= "
                  f"δ = {worthwhile}; more attempts or items narrow the interval")
    return {"decision": decision, "reason_code": code, "reason": reason, "n": n,
            "item_clusters": gain.get("clusters", 0), "mean": gain.get("mean"), "se": gain.get("se"),
            "df": gain.get("df"), "t_critical": gain.get("t_critical"), "ci95": interval,
            "flipping_delta": None if interval is None else interval[1],
            "method": gain.get("method", CLUSTER_T_METHOD), "margin_nats_per_attempt": margin,
            "smallest_worthwhile_gain_nats_per_attempt": worthwhile, "coverage": coverage,
            "caveats": caveats}


def _decision_rule() -> dict:
    """The rule and constants in force, recorded in every report (the owner monitors δ)."""
    interval = PREREGISTRATION["decision_interval"]
    return {
        "smallest_worthwhile_gain_nats_per_attempt": PREREGISTRATION[
            "smallest_worthwhile_gain_nats_per_attempt"],
        "margin_nats_per_attempt": PREREGISTRATION["margin_nats_per_attempt"],
        "interval": {key: interval[key] for key in ("method", "level", "unit", "degrees_of_freedom")},
        "kill": "upper bound < δ (real_gain_below_delta when the lower bound is also > m)",
        "embeddings_add_value": "otherwise, lower bound > m",
        "insufficient_data": "otherwise, or no interval",
        "real_gain_below_delta": PREREGISTRATION["decision_rule"]["real_gain_below_delta"],
        "flipping_delta": ("each verdict's upper bound: the verdict is kill exactly when "
                           "δ > flipping_delta; at or below it, embeddings_add_value if the lower "
                           "bound is > m, otherwise insufficient_data"),
    }


def make_t8_analysis(*, unavailable: Mapping[str, str] | None = None) -> Callable[[ReplayArrays], dict]:
    """The pre-registered T8 analysis as a harness hook (aggregates only).

    ``unavailable`` names arms deliberately not run, with the reason (for
    example no solver-panel difficulty, or no prepared LLM cache).
    """
    unavailable = dict(unavailable or {})

    def analysis(arrays: ReplayArrays) -> dict:
        if arrays.bootstrap_unit != "item":
            # One unit per report: every T8 interval clusters on items (the descriptive
            # ones resample them).
            raise ValueError("The T8 report clusters on items: run the harness with bootstrap_unit='item'")
        ability_scored = int(arrays.ability.sum())
        primary = _comparison(arrays, PRIMARY_ARM, EXPLICIT_ARMS, t_interval=True)
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
            comparison = _comparison(arrays, arm, EXPLICIT_ARMS, t_interval=True)
            if comparison["status"] == "computed":
                gated_verdict = _verdict(comparison, ability_scored)
                comparison["verdict"] = gated_verdict["decision"]
                comparison["verdict_reason_code"] = gated_verdict["reason_code"]
                comparison["verdict_reason"] = gated_verdict["reason"]
                comparison["verdict_flipping_delta"] = gated_verdict["flipping_delta"]
            comparison["interpretation"] = "interpreted" if gate_open else "not_interpreted"
            gate_open = gate_open and comparison.get("verdict") == "embeddings_add_value"
            gated[arm] = comparison
        # The pure embedding increment. It is the primary comparison itself whenever
        # e* is tag_logistic, so it carries the verdict's t interval rather than a
        # second, narrower percentile one (review F4).
        descriptive = {"emb_ridge_vs_tag_logistic": _comparison(arrays, PRIMARY_ARM, ["tag_logistic"],
                                                                t_interval=True)}
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
            "decision_rule": _decision_rule(),
            "ability_scored_attempts": ability_scored,
            "primary": {"arm": PRIMARY_ARM, "explicit_arms": list(EXPLICIT_ARMS),
                        "comparison": primary, "verdict": verdict},
            "gated": gated,
            "descriptive": descriptive,
            "kill_rule": ("If the primary verdict is kill (the 95% cluster-robust t interval's upper "
                          f"bound is below δ = {verdict['smallest_worthwhile_gain_nats_per_attempt']} "
                          "nats per attempt, including a real gain below δ), embeddings add no "
                          "held-out predictive value worth building on and the GP success head is "
                          "not pursued (Slice 2 §11). A real_gain_below_delta kill is provisional: "
                          "the realized gain includes the embedding block's learning period, so "
                          "rerun when the data has grown. insufficient_data is no decision: rerun "
                          "with more data."),
            "activates": False,
        }

    return analysis


def _span(interval) -> str:
    return "none" if interval is None else f"[{_number(interval[0])}, {_number(interval[1])}]"


def _t_interval(gain: Mapping) -> str:
    if gain.get("df") is None:
        return f"95% cluster-robust t interval none ({gain.get('degenerate') or 'not computable'})"
    return (f"95% cluster-robust t interval (CR1 over items, df = {gain['df']}, "
            f"t = {_number(gain['t_critical'])}) {_span(gain['ci95'])}, standard error "
            f"{_number(gain['se'])}")


def summary_lines(analysis: Mapping) -> list[str]:
    """Aggregate-only markdown for the top of the T8 report."""
    primary = analysis["primary"]
    comparison, verdict = primary["comparison"], primary["verdict"]
    rule = analysis["decision_rule"]
    mean = verdict["mean"]
    gain = comparison.get("log_loss_gain") or {}
    lines = [
        "## T8 pre-registered verdict", "",
        f"- Pre-registration: `{analysis['preregistration']['version']}` "
        f"(hash `{analysis['preregistration']['hash'][:16]}`); deviations: "
        f"{', '.join(analysis['preregistration']['deviations']) or 'none'}.",
        f"- δ in force: {rule['smallest_worthwhile_gain_nats_per_attempt']} nats per attempt "
        f"(m = {rule['margin_nats_per_attempt']}); verdict interval: `{rule['interval']['method']}`, "
        f"{rule['interval']['level']:.0%}, df = {rule['interval']['degrees_of_freedom']}.",
        f"- Primary: `{primary['arm']}` vs best explicit arm `{comparison.get('baseline', 'n/a')}`: "
        f"n = {verdict['n']} common attempts in {verdict['item_clusters']} item clusters.",
        f"- Log-loss gain per attempt, loss(e*) − loss(`{primary['arm']}`): mean "
        f"{'none' if mean is None else _number(mean)}; "
        + (_t_interval(gain) if gain else "95% cluster-robust t interval none") + ".",
        f"- Rule: `kill` if the upper bound < δ = {verdict['smallest_worthwhile_gain_nats_per_attempt']} "
        "(`real_gain_below_delta` when the lower bound is also > m); otherwise "
        f"`embeddings_add_value` if the lower bound > m = {verdict['margin_nats_per_attempt']}; "
        "otherwise `insufficient_data`.",
        f"- **Decision: {verdict['decision']}** (`{verdict['reason_code']}`): {verdict['reason']}"
        + (f" (caveats: {', '.join(verdict['caveats'])})" if verdict["caveats"] else "")
        + f"; coverage {verdict['coverage']:.3f} of ability-scored attempts.",
    ]
    for arm, result in analysis["gated"].items():
        if result.get("status") != "computed":
            lines.append(f"- Gated `{arm}`: {result.get('status')} ({result.get('reason', '')}).")
        else:
            gated_gain = result["log_loss_gain"]
            lines.append(f"- Gated `{arm}` ({result['interpretation']}): {result['verdict']} "
                         f"(`{result['verdict_reason_code']}`), {result['verdict_reason']}; mean gain "
                         f"{_number(gated_gain['mean'])}, {_t_interval(gated_gain)}; n = {result['n']} "
                         f"in {gated_gain['clusters']} item clusters.")
    lines.append("- The descriptive `emb_ridge_vs_tag_logistic` comparison uses the same t interval; "
                 "every other interval in this report (report 1, report 2, the splits and the LLM "
                 "comparisons) is a percentile item bootstrap, descriptive only.")
    lines.append("- Nothing is activated; T8 has no live consumer.")
    return lines
