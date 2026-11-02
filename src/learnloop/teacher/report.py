"""The learned lesson-check weight's report lines (spec_teacher_v1 §12.1 "Kill switch and monitoring").

Read-only (``learnloop teacher report``; TE2 adds the lesson rows). Nothing
switches on any of these numbers: they show how far each learned quantity has
moved off its seeded prior, and how much its prior still decides.

* **Contraction:** each term's prior sd beside its posterior sd (η₀, β_c, β_p),
  and the per-LO offset scale's grid weights.
* **Prior sensitivity:** the global mass re-run with each prior mean shifted by
  ±1 prior sd.
* **Prequential log loss:** of the learned mass and of the fixed 0.5, side by
  side, over every resolved check (each scored before its own update).
* **The pool weight** λ̂ per forecaster, and the tap/hedge recalibration beside
  today's fixed map.
"""

from __future__ import annotations

import math
from typing import Any

from learnloop.learner import lesson_weight as LW


def _posterior_sd(state: LW.WeightState, index: int) -> float:
    weights = state.tau_weights()
    means = [float(bank.mean[index]) for bank in state.banks]
    mean = sum(w * m for w, m in zip(weights, means))
    second = sum(w * (float(bank.cov[index, index]) + float(bank.mean[index]) ** 2) for w, bank in zip(weights, state.banks))
    return math.sqrt(max(second - mean * mean, 0.0))


def report(vault: Any, repository: Any) -> dict[str, Any]:
    state = LW.replay_state(vault, repository)
    priors = {"eta0": LW.ETA0_PRIOR_SD, "beta_c": LW.BETA_C_PRIOR_SD, "beta_p": LW.BETA_P_PRIOR_SD}
    contraction = {}
    for term, index in LW.PRIOR_TERMS.items():
        sd = _posterior_sd(state, index)
        contraction[term] = {"prior_sd": priors[term], "posterior_sd": round(sd, 6),
                             "contraction": round(1.0 - sd / priors[term], 6)}
    baseline = state.learned_mass("", 0.0, 0.0)
    sensitivity = {}
    for term, sd in priors.items():
        sensitivity[term] = {
            sign: round(LW.replay_state(vault, repository, prior_shift={term: factor * sd}).learned_mass("", 0.0, 0.0), 6)
            for sign, factor in (("minus_1sd", -1.0), ("plus_1sd", 1.0))}
    learned_ll = sum(learned for learned, _fixed in state.prequential)
    fixed_ll = sum(fixed for _learned, fixed in state.prequential)
    lines = [
        f"lesson-check mass (global, no confidence or prediction effect): {baseline:.3f} "
        f"(prior centre 0.5; {state.updates} resolved check(s))",
        *[f"{term}: prior sd {entry['prior_sd']:.2f} -> posterior sd {entry['posterior_sd']:.3f}"
          for term, entry in contraction.items()],
        f"prequential log loss over {len(state.prequential)} resolved check(s): learned {-learned_ll:.4f} nats, "
        f"fixed 0.5 {-fixed_ll:.4f} nats",
        *[f"pool weight {family}: λ̂ = {state.pool_lambda(family):.3f} ({state.pool_updates.get(family, 0)} update(s); "
          "seeded prior Beta(1, 4), mean 0.2)" for family in sorted(state.pools)],
        "tap recalibration: " + ", ".join(
            f"{tap}: {state.tap_probability(tap):.2f} (map {LW.TAP_PRIOR_MAP[tap]:.2f})" for tap in LW.TAP_PRIOR_MAP)
        + f" ({state.tap.updates} answer(s))",
        "hedge recalibration: " + ", ".join(
            f"{value}: {state.hedge_probability(value):.2f}" for value in LW.HEDGE_VALUES)
        + f" ({state.hedge.updates} answer(s))",
    ]
    return {
        "priors_version": LW.PRIORS_VERSION,
        "global_mass": round(baseline, 6),
        "resolved_checks": state.updates,
        "contraction": contraction,
        "tau_weights": dict(zip([str(t) for t in LW.TAU_GRID], [round(float(w), 6) for w in state.tau_weights()])),
        "prior_sensitivity": sensitivity,
        "prequential_log_loss": {"n": len(state.prequential), "learned_nats": round(-learned_ll, 6),
                                 "fixed_half_nats": round(-fixed_ll, 6)},
        "pool": {family: {"lambda": round(state.pool_lambda(family), 6), "updates": state.pool_updates.get(family, 0)}
                 for family in sorted(state.pools)},
        "calibration": {"tap": {str(t): round(state.tap_probability(t), 6) for t in LW.TAP_PRIOR_MAP},
                        "tap_updates": state.tap.updates,
                        "hedge": {v: round(state.hedge_probability(v), 6) for v in LW.HEDGE_VALUES},
                        "hedge_updates": state.hedge.updates},
        "lines": lines,
    }


__all__ = ["report"]
