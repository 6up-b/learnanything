"""P4 step 4 -- the single randomization layer (U-024, spec §9.3, design §B step 4).

ALL policy experimentation runs through here. There is no separate crossover
machinery. Three (and only three) admissible designs:

- ``mrt_reversible`` -- micro-randomized decisions among REVERSIBLE, near-equivalent
  feasible candidates;
- ``epsilon_tiebreak`` -- ε tie-breaking when the top feasible candidates fall within a
  declared margin (a special case of the above at the selection seam);
- ``commitment_parallel`` -- for durable interventions whose effects are persistent
  state changes (no washout), the experimental unit is the COMMITMENT, not time.

Every random draw logs its **seed + true propensity BEFORE selection** so an off-policy
IPS/DR join is valid (§9.3). Randomization is INERT unless a decision is genuinely
near-equivalent (the ε margin): a non-tie ranks deterministically and no assignment is
written. Proximal outcomes are read at the NEXT SPACED COLD REVIEW (never end-of-session
-- desirable difficulties invert immediate rankings): :func:`open_outcome_window`
anchors the window there. An intervention that fits neither reversible-MRT nor
commitment-parallel-with-carryover stays **hypothesis-grade** regardless of accumulated
data -- :func:`grade_for` enforces the label.
"""

from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from learnloop.clock import Clock
from learnloop.db.repositories import Repository
from learnloop.services import controller_store as store
from learnloop.services import parameter_registry as pr

# Structural schema version of the randomization layer (enum, not a decision knob).
RANDOMIZATION_LAYER_VERSION = 1

# Near-equivalence margin (§9.3): two feasible candidates are near-equivalent when
# their per-minute values fall within this FRACTION of the top value. Below the margin,
# the ε tie-break randomizes with a logged propensity; above it, selection is
# deterministic and randomization is inert. Heuristic decision parameter (design §E).
EPSILON_TIE_MARGIN = 0.05

# Propensity floor guardrail (§9.3): a variant may not be assigned below this true
# probability, or off-policy support collapses. Dormant -- only binds when a design
# would spread propensity mass too thin (bind-logged, not swept, U-022).
PROPENSITY_FLOOR = 0.05

_GRADES = ("experimental", "hypothesis_grade")


def _seed_int(seed: str) -> int:
    return int.from_bytes(hashlib.sha256(seed.encode("utf-8")).digest()[:8], "big")


@dataclass(frozen=True)
class Assignment:
    """The result of one randomization draw (persisted; propensity logged first)."""

    assignment_id: str | None
    experiment_id: str
    design: str
    unit_kind: str
    unit_id: str | None
    variant: str
    propensity: float
    seed: str
    draw: float | None
    near_equivalent: bool
    grade: str
    randomized: bool  # False = inert (deterministic top; no random draw)

    def as_dict(self) -> dict[str, Any]:
        return {
            "assignment_id": self.assignment_id,
            "experiment_id": self.experiment_id,
            "design": self.design,
            "unit_kind": self.unit_kind,
            "unit_id": self.unit_id,
            "variant": self.variant,
            "propensity": round(self.propensity, 6),
            "seed": self.seed,
            "draw": self.draw,
            "near_equivalent": self.near_equivalent,
            "grade": self.grade,
            "randomized": self.randomized,
        }


def grade_for(*, reversible: bool, commitment_unit: bool, carryover_modeled: bool) -> str:
    """The experiment grade (§9.3 label enforcement). An intervention is
    ``experimental`` only if it is reversible (MRT/ε design) OR runs as a
    commitment-level parallel unit WITH an explicit carryover model. Anything else --
    not reversible, no credible commitment-level unit, no carryover model -- is
    ``hypothesis_grade`` regardless of how much data accumulates."""

    if reversible:
        return "experimental"
    if commitment_unit and carryover_modeled:
        return "experimental"
    return "hypothesis_grade"


def is_near_equivalent(values: Sequence[float], margin: float = EPSILON_TIE_MARGIN) -> bool:
    """True when the top-2 feasible values fall within ``margin`` fraction of the top
    (the ε near-equivalence test). A single candidate is trivially not a tie."""

    if len(values) < 2:
        return False
    ordered = sorted(values, reverse=True)
    top = ordered[0]
    if top <= 0:
        # Non-positive top values: near-equivalent iff the gap is within the margin.
        return abs(ordered[0] - ordered[1]) <= margin
    return (top - ordered[1]) / top <= margin


def _tied_set(refs: Sequence[str], values: Sequence[float], margin: float) -> list[str]:
    ordered = sorted(zip(values, refs), key=lambda t: (t[0], t[1]), reverse=True)
    top = ordered[0][0]
    tied: list[str] = []
    for v, r in ordered:
        if top <= 0:
            within = abs(top - v) <= margin
        else:
            within = (top - v) / top <= margin
        if within:
            tied.append(r)
    return sorted(tied)


def _clamped_uniform_propensity(
    repository: Repository | None, n: int, *, floor: float, clock: Clock | None
) -> float:
    """Uniform propensity 1/n, guarded by the dormant propensity floor. When the floor
    would bind (too many variants), bind-log it (U-022) and clamp to the floor."""

    p = 1.0 / max(n, 1)
    if p < floor:
        if repository is not None:
            pr.record_bind(
                repository, "randomization_layer:PROPENSITY_FLOOR",
                {"variants": n, "uniform_propensity": p, "floor": floor}, clock=clock,
            )
        return floor
    return p


def epsilon_tiebreak(
    repository: Repository | None,
    *,
    experiment_id: str,
    refs: Sequence[str],
    values: Sequence[float],
    seed: str,
    decision_id: str | None = None,
    reversible: bool = True,
    margin: float = EPSILON_TIE_MARGIN,
    clock: Clock | None = None,
) -> Assignment:
    """ε tie-break among feasible candidates (§9.3). If the top candidates are NOT
    near-equivalent, selection is deterministic and randomization is inert (no draw,
    no assignment). If they are, randomize uniformly over the tied set with the true
    propensity logged BEFORE the choice is returned."""

    if not refs:
        return Assignment(None, experiment_id, "epsilon_tiebreak", "decision", decision_id,
                          "", 0.0, seed, None, False, "experimental", False)

    ordered = sorted(zip(values, refs), key=lambda t: (t[0], t[1]), reverse=True)
    deterministic_top = ordered[0][1]

    if not is_near_equivalent(values, margin):
        # Inert: deterministic winner, propensity 1.0, no random draw, no persistence.
        return Assignment(None, experiment_id, "epsilon_tiebreak", "decision", decision_id,
                          deterministic_top, 1.0, seed, None, False,
                          grade_for(reversible=reversible, commitment_unit=False,
                                    carryover_modeled=False), False)

    tied = _tied_set(refs, values, margin)
    propensity = _clamped_uniform_propensity(repository, len(tied), floor=PROPENSITY_FLOOR, clock=clock)
    rng = random.Random(_seed_int(seed))
    draw = rng.random()
    chosen = tied[min(int(draw * len(tied)), len(tied) - 1)]
    grade = grade_for(reversible=reversible, commitment_unit=False, carryover_modeled=False)

    assignment_id = None
    if repository is not None:
        assignment_id = store.persist_experiment_assignment(
            repository, experiment_id=experiment_id, decision_id=decision_id,
            unit_kind="decision", unit_id=decision_id, variant=chosen, propensity=propensity,
            seed=seed, draw=draw, epsilon_margin=margin, near_equivalent=True,
            design="epsilon_tiebreak", grade=grade, candidate_refs=tied,
            detail={"tied": tied, "deterministic_top": deterministic_top}, clock=clock,
        )
    return Assignment(assignment_id, experiment_id, "epsilon_tiebreak", "decision",
                      decision_id, chosen, propensity, seed, draw, True, grade, True)


def micro_randomize(
    repository: Repository | None,
    *,
    experiment_id: str,
    variants: Sequence[str],
    seed: str,
    reversible: bool,
    decision_id: str | None = None,
    clock: Clock | None = None,
) -> Assignment:
    """Micro-randomize among REVERSIBLE near-equivalent variants (MRT, §9.3). A
    non-reversible intervention is refused this design -- it is hypothesis-grade and no
    assignment is written (the caller must use commitment-parallel or stay hypothesis
    grade)."""

    variants = sorted(set(variants))
    if not variants:
        return Assignment(None, experiment_id, "mrt_reversible", "decision", decision_id,
                          "", 0.0, seed, None, False, "hypothesis_grade", False)
    if not reversible:
        # Not eligible for MRT; label hypothesis-grade, no random assignment.
        return Assignment(None, experiment_id, "mrt_reversible", "decision", decision_id,
                          variants[0], 1.0, seed, None, False, "hypothesis_grade", False)

    propensity = _clamped_uniform_propensity(repository, len(variants), floor=PROPENSITY_FLOOR, clock=clock)
    rng = random.Random(_seed_int(seed))
    draw = rng.random()
    chosen = variants[min(int(draw * len(variants)), len(variants) - 1)]
    assignment_id = None
    if repository is not None:
        assignment_id = store.persist_experiment_assignment(
            repository, experiment_id=experiment_id, decision_id=decision_id,
            unit_kind="decision", unit_id=decision_id, variant=chosen, propensity=propensity,
            seed=seed, draw=draw, epsilon_margin=None, near_equivalent=True,
            design="mrt_reversible", grade="experimental", candidate_refs=variants,
            detail={"variants": variants}, clock=clock,
        )
    return Assignment(assignment_id, experiment_id, "mrt_reversible", "decision", decision_id,
                      chosen, propensity, seed, draw, True, "experimental", True)


def commitment_parallel_assign(
    repository: Repository | None,
    *,
    experiment_id: str,
    commitment_id: str,
    variants: Sequence[str],
    seed: str,
    carryover_modeled: bool,
    clock: Clock | None = None,
) -> Assignment:
    """Assign a COMMITMENT to a variant for a durable intervention (§9.3). At n=1 the
    experimental unit is the commitment, not time. The grade is ``experimental`` only
    when a carryover model is declared; otherwise the durable intervention stays
    hypothesis-grade regardless of accumulated data."""

    variants = sorted(set(variants))
    grade = grade_for(reversible=False, commitment_unit=True, carryover_modeled=carryover_modeled)
    if not variants:
        return Assignment(None, experiment_id, "commitment_parallel", "commitment",
                          commitment_id, "", 0.0, seed, None, False, grade, False)
    propensity = _clamped_uniform_propensity(repository, len(variants), floor=PROPENSITY_FLOOR, clock=clock)
    rng = random.Random(_seed_int(seed))
    draw = rng.random()
    chosen = variants[min(int(draw * len(variants)), len(variants) - 1)]
    assignment_id = None
    if repository is not None:
        assignment_id = store.persist_experiment_assignment(
            repository, experiment_id=experiment_id, decision_id=None,
            unit_kind="commitment", unit_id=commitment_id, variant=chosen,
            propensity=propensity, seed=seed, draw=draw, epsilon_margin=None,
            near_equivalent=False, design="commitment_parallel", grade=grade,
            candidate_refs=variants,
            detail={"variants": variants, "carryover_modeled": carryover_modeled}, clock=clock,
        )
    return Assignment(assignment_id, experiment_id, "commitment_parallel", "commitment",
                      commitment_id, chosen, propensity, seed, draw, True, grade, True)


def open_outcome_window(
    repository: Repository,
    *,
    decision_id: str | None,
    assignment: Assignment | None,
    card_ref: str | None,
    commitment_id: str | None = None,
    candidate_ref: str | None = None,
    anchor_kind: str = "administration_committed",
    anchor_ref: str | None = None,
    next_spaced_cold_review_at: str | None = None,
    clock: Clock | None = None,
) -> str:
    """Open a delayed outcome window anchored to the NEXT SPACED COLD REVIEW (§9.3).
    The window inherits the hypothesis-grade label when the assignment is
    hypothesis-grade (unmodeled carryover)."""

    hypothesis_grade = bool(assignment is not None and assignment.grade == "hypothesis_grade")
    return store.open_outcome_window(
        repository, decision_id=decision_id,
        assignment_id=(assignment.assignment_id if assignment else None),
        candidate_ref=candidate_ref, commitment_id=commitment_id, card_ref=card_ref,
        anchor_kind=anchor_kind, anchor_ref=anchor_ref,
        due_at=next_spaced_cold_review_at, hypothesis_grade=hypothesis_grade, clock=clock,
    )
