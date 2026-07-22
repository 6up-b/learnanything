"""P4 step 3 -- interval-width viability of robust EVSI (spec_p4 §16.3, U-021/U-023).

The acceptance question: with ``heuristic``-width grader + likelihood channels, is
robust EVSI still USABLE, or does it degenerate (the stop rule fires immediately on a
truly-separating question, or the winner flips)? This sim sweeps the channel width and
measures the resulting **measure-mode abstention rate**. That rate must stay inside the
registered P0 abstention budget (``robust_composition.ABSTENTION_BUDGET_FRACTION``,
U-021); a breach RAISES the budget alarm rather than silently widening tolerances --
tying the Step-3 EVSI selector to the P0 ensemble-agreement/abstention gate.

Channel width is controlled by the Dirichlet concentration of the calibrated grader
channel (low concentration = wide intervals = noisy credible set). The instrument rows
``P(Z|H)`` are genuinely separating, so a well-calibrated width should measure; only a
pathologically wide channel should push abstention past the budget (and alarm).

Determinism: stdlib ``random.Random`` only (bit-for-bit replay, matching
``robust_composition``).
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Sequence

from learnloop.services import action_loss as AL
from learnloop.services import evsi as EV
from learnloop.services import robust_composition as rc

# The two-hypothesis separating loss table (different effective repairs).
_LOSS = AL.LossTable(
    hypotheses=("h1", "h2"),
    actions=("a1", "a2"),
    cells={
        ("h1", "a1"): AL.LossCell("h1", "a1", 0.0, {"kind": "effective_intervention",
                                                     "wasted_minutes": 0.0, "delay_minutes": 0.0}),
        ("h1", "a2"): AL.LossCell("h1", "a2", 6.0, {"kind": "ineffective_then_effective",
                                                    "wasted_minutes": 3.0, "delay_minutes": 3.0}),
        ("h2", "a1"): AL.LossCell("h2", "a1", 6.0, {"kind": "ineffective_then_effective",
                                                    "wasted_minutes": 3.0, "delay_minutes": 3.0}),
        ("h2", "a2"): AL.LossCell("h2", "a2", 0.0, {"kind": "effective_intervention",
                                                    "wasted_minutes": 0.0, "delay_minutes": 0.0}),
    },
    effective_action={"h1": "a1", "h2": "a2"},
    tie_break_order=("a1", "a2"),
)
_PRIOR = {"h1": 0.5, "h2": 0.5}
_EXPECTED_MINUTES = 1.0


@dataclass(frozen=True)
class WidthResult:
    concentration: float
    scenarios: int
    abstention_count: int
    abstention_rate: float
    within_budget: bool


@dataclass(frozen=True)
class ViabilityReport:
    budget: float
    per_width: tuple[WidthResult, ...]
    heuristic_concentration: float
    heuristic_within_budget: bool
    alarm: bool  # True when ANY swept width breaches the budget (must be surfaced)

    def as_dict(self) -> dict:
        return {
            "budget": self.budget,
            "heuristic_concentration": self.heuristic_concentration,
            "heuristic_within_budget": self.heuristic_within_budget,
            "alarm": self.alarm,
            "per_width": [
                {"concentration": w.concentration, "abstention_rate": round(w.abstention_rate, 4),
                 "within_budget": w.within_budget}
                for w in self.per_width
            ],
        }


def _joint_alpha(concentration: float, sep: float) -> dict[str, dict[str, float]]:
    """Grader channel ``P(E|Z)`` as Dirichlet alphas at a given concentration. Higher
    concentration = tighter credible intervals; ``sep`` is the channel fidelity."""

    hi, lo = 0.5 + sep / 2, 0.5 - sep / 2
    return {
        "z1": {"e1": concentration * hi, "e2": concentration * lo},
        "z2": {"e1": concentration * lo, "e2": concentration * hi},
    }


def _instrument_rows(strength: float) -> dict[str, dict[str, float]]:
    hi, lo = 0.5 + strength / 2, 0.5 - strength / 2
    return {"h1": {"z1": hi, "z2": lo}, "h2": {"z1": lo, "z2": hi}}


def _scenario_verdict(concentration: float, strength: float, sep: float, seed: str) -> str:
    ensemble = rc.build_ensemble(
        joint_alpha=_joint_alpha(concentration, sep),
        instrument_rows=_instrument_rows(strength),
        calibration_model_hash=f"width_{concentration}",
        decision_context_hash=seed,
        draw_count=64,
    )
    candidate = EV.DiagnosticCandidate(
        ref="q", members=tuple(ensemble.members), prior=_PRIOR, expected_minutes=_EXPECTED_MINUTES,
    )
    return EV.rank_feasible([candidate], _LOSS).verdict


def run_interval_width_viability(
    *,
    concentrations: Sequence[float] = (60.0, 30.0, 12.0, 4.0, 1.5),
    heuristic_concentration: float = 30.0,
    n_scenarios: int = 40,
    seed: int = 20260720,
    budget: float | None = None,
) -> ViabilityReport:
    """Sweep channel width; report the measure-mode abstention rate per width and
    whether the heuristic width stays inside the P0 abstention budget. The scenarios
    are genuinely separating (strong instrument rows), so abstention reflects channel
    UNUSABILITY, not a truly-common action."""

    budget = rc.ABSTENTION_BUDGET_FRACTION if budget is None else budget
    rng = random.Random(seed)
    # Fixed scenario bank (shared across widths) of strongly-separating questions.
    scenarios = [
        (rng.uniform(0.75, 0.95), rng.uniform(0.75, 0.95)) for _ in range(n_scenarios)
    ]

    per_width: list[WidthResult] = []
    for c in concentrations:
        abstained = 0
        for i, (strength, sep) in enumerate(scenarios):
            verdict = _scenario_verdict(c, strength, sep, seed=f"{c}:{i}")
            # measure-mode UNUSABLE = a truly-separating question the channel cannot
            # turn into a confident measurement (abstain or immediate stop).
            if verdict != "measure":
                abstained += 1
        rate = abstained / max(len(scenarios), 1)
        per_width.append(WidthResult(c, len(scenarios), abstained, rate, rate <= budget))

    heuristic = next((w for w in per_width if w.concentration == heuristic_concentration), per_width[0])
    alarm = any(not w.within_budget for w in per_width)
    return ViabilityReport(
        budget=budget, per_width=tuple(per_width),
        heuristic_concentration=heuristic_concentration,
        heuristic_within_budget=heuristic.within_budget, alarm=alarm,
    )
