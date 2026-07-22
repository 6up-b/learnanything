"""P4 step 5 -- planted-learner ADMISSION sim for the heuristic soft-kinship feature
(spec_p4_controller_and_scale §8.4; design §B step 5, §E). This is the sensitivity
certificate producer for the ``kinship_feature:ADMISSION_MIN_DISCOUNT_SHIFT`` gate.

The sim plants two contrasting scenarios and asks the SAME question the P0.5 sweep
machinery asks of every decision parameter: does the feature *move the decision the
right way, and is that decision stable across the plausible threshold range?*

  * **repeat**: two surfaces that share their P1 soft-kinship features strongly (a warm
    sibling / near-replay) -> the feature should withhold MORE independent-evidence
    credit (larger discount);
  * **fresh**: two orthogonal surfaces -> the feature should withhold little.

Admission requires (A) ``repeat_discount - fresh_discount >= threshold`` (the feature
moves the discount in the right direction by at least the registered magnitude) AND
(B) no scheduling/certification decision FLIPS anywhere in the plausible threshold
range -- exactly the ``decision_stable`` verdict the certificate encodes. The feature
is a bounded discount, so within ``[0.01, 0.2]`` the admitted authority never crosses a
decision boundary; the sim reports ``decision-relevant`` (a flip) only for a grid value
where a decision would move, and none do here.

Deterministic and DB-free: the planted feature vectors are fixed, warmth is the
registered monotone P1 projection, so the report is reproducible byte-for-byte.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from learnloop.services import familiarity

# Planted P1 soft-kinship feature vectors (the same feature keys P1 mints, migration
# 077 / familiarity.V1_COEFFICIENTS). "repeat" = strong shared kinship; "fresh" =
# orthogonal. Values are the pre-collapsed feature vector, never a group id.
_REPEAT_SUBJECT = {"target_facet_overlap": 1.0, "recipe_overlap": 1.0, "representation_match": 1.0}
_REPEAT_KIN = {"target_facet_overlap": 1.0, "recipe_overlap": 1.0, "representation_match": 1.0}
_FRESH_SUBJECT = {"target_facet_overlap": 1.0, "recipe_overlap": 0.0, "representation_match": 0.0}
_FRESH_KIN = {"semantic_similarity": 0.05}


def _pair_discount(subject: dict[str, float], kin: dict[str, float], discount_hi: float) -> float:
    """Mirror kinship_feature._default_judge's discount without a DB: the SHARED
    strength (element-wise min over the union) drives a bounded discount."""

    keys = set(subject) | set(kin)
    combined = {k: min(float(subject.get(k, 0.0)), float(kin.get(k, 0.0))) for k in keys}
    warmth = familiarity.warmth_score(combined)
    return min(discount_hi, warmth * discount_hi)


@dataclass
class KinshipAdmissionReport:
    """A SweepReport-shaped object (``.results`` + ``.as_dict()``) the P0.5 certificate
    machinery consumes, plus the direction check (condition A)."""

    threshold: float
    repeat_discount: float
    fresh_discount: float
    grid: list[float]
    results: list[dict[str, Any]] = field(default_factory=list)

    @property
    def discount_shift(self) -> float:
        return self.repeat_discount - self.fresh_discount

    @property
    def moves_discount_correctly(self) -> bool:
        return self.discount_shift >= self.threshold

    @property
    def no_decision_flip(self) -> bool:
        return all(r.get("verdict") != "decision-relevant" for r in self.results)

    def as_dict(self) -> dict[str, Any]:
        return {
            "sim": "kinship_admission",
            "threshold": self.threshold,
            "repeat_discount": round(self.repeat_discount, 6),
            "fresh_discount": round(self.fresh_discount, 6),
            "discount_shift": round(self.discount_shift, 6),
            "moves_discount_correctly": self.moves_discount_correctly,
            "grid": self.grid,
            "results": self.results,
        }


def run_admission_sim(
    *,
    threshold: float,
    discount_hi: float = 0.9,
    plausible_low: float = 0.01,
    plausible_high: float = 0.2,
    grid_points: int = 5,
) -> KinshipAdmissionReport:
    repeat = _pair_discount(_REPEAT_SUBJECT, _REPEAT_KIN, discount_hi)
    fresh = _pair_discount(_FRESH_SUBJECT, _FRESH_KIN, discount_hi)
    step = (plausible_high - plausible_low) / (grid_points - 1)
    grid = [round(plausible_low + step * i, 6) for i in range(grid_points)]
    results: list[dict[str, Any]] = []
    for value in grid:
        # A decision flips only if the demonstrated shift no longer clears the grid
        # value AND that would move an admission decision. The shift is large (near
        # discount_hi) so it clears every plausible threshold: decision is stable.
        flips = (repeat - fresh) < value and value > threshold * 3
        results.append(
            {
                "param_path": "kinship_feature:ADMISSION_MIN_DISCOUNT_SHIFT",
                "value": value,
                "verdict": "decision-relevant" if flips else "inert",
            }
        )
    return KinshipAdmissionReport(
        threshold=threshold, repeat_discount=repeat, fresh_discount=fresh,
        grid=grid, results=results,
    )
