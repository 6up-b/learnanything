"""Why the mastery posterior moved as far as it did (read-time attribution).

The EKF step size is dominated by the observation weight ``w``, which enters the
measurement noise as ``R = base_variance * pq / max(w, weight_floor)``. ``w`` is
built multiplicatively in :func:`learnloop.learner.recall_coverage.resolve_error_impact`
from LO-relative coverage, reliability, and the familiarity discount -- so a
full-credit attempt can still move ``mu`` very little, and the learner has no way
to see why from the posterior alone.

This module reconstructs that product from the persisted attempt debug payload.
It is derivation only: no new state, no writes, and every factor comes from a
trace the attempt already stored, so it works retroactively on old attempts.
Factors are emitted in the order they are applied and their product reproduces
the stored ``observation_weight`` -- an honest chain the UI can render as-is
rather than a re-derivation that could drift from the filter.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

# Below this the chain is reported but flagged: R is floored at
# ``pq / WEIGHT_FLOOR``, so further shrinkage of w stops shrinking the step.
# Mirrors the ``max(weight, 0.10)`` guard in ``mastery.irt_observation``.
WEIGHT_FLOOR = 0.10

# Product agreement tolerance. The chain is float-multiplied in a different order
# than the pipeline built it, so exact equality is not available.
_PRODUCT_TOLERANCE = 1e-6

# A factor within this of 1.0 changed nothing; it is dropped so the strip stays
# short. Dropping is safe for the product invariant precisely because it is ~1.
_NEUTRAL_EPSILON = 1e-9


@dataclass(frozen=True)
class MasteryStepFactor:
    """One multiplicative term in the observation weight."""

    key: str
    label: str
    detail: str
    multiplier: float


@dataclass(frozen=True)
class MasteryStepExplanation:
    observation_weight: float
    factors: tuple[MasteryStepFactor, ...]
    expected_correctness: float | None
    observed_correctness: float | None
    #: Key of the factor that cost the most weight, for emphasis in the UI.
    dominant_factor_key: str | None
    #: ``w`` sits at/below the noise floor, so the step no longer tracks it.
    at_weight_floor: bool
    #: Product of ``factors`` matches the stored weight. False means the payload
    #: predates a scoring change; callers should present the chain as partial.
    product_reconciles: bool


def _number(source: Mapping[str, Any] | None, key: str) -> float | None:
    if not isinstance(source, Mapping):
        return None
    value = source.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


def _mapping(source: Mapping[str, Any] | None, key: str) -> Mapping[str, Any] | None:
    if not isinstance(source, Mapping):
        return None
    value = source.get(key)
    return value if isinstance(value, Mapping) else None


def _coverage_detail(trace: Mapping[str, Any] | None, effective_coverage: float | None) -> str:
    """``3 of 6 facets`` -- the LO surface this item can actually reach."""

    per_facet = _mapping(trace, "per_facet_coverage") or {}
    required = trace.get("required_facets") if isinstance(trace, Mapping) else None
    total = len(required) if isinstance(required, list) else len(per_facet)
    touched = sum(1 for value in per_facet.values() if isinstance(value, (int, float)) and value > 0.0)
    if total <= 0:
        return "facet coverage unavailable"
    exposure = f" at {effective_coverage:.2f} exposure" if effective_coverage is not None else ""
    return f"{touched} of {total} facets{exposure}"


def _familiarity_detail(trace: Mapping[str, Any] | None) -> str:
    """Name the surface that made this attempt less novel."""

    same_item = _number(trace, "same_item_discount")
    same_facet = _number(trace, "same_facet_surface_discount")
    same_family = _number(trace, "same_surface_family_discount")
    if same_item is not None and same_item < 1.0:
        return "same item practiced recently"
    if same_facet is not None and same_facet < 1.0:
        return "same facets practiced recently"
    if same_family is not None and same_family < 1.0:
        return "similar item practiced recently"
    return "recently practiced"


def explain_mastery_step(
    debug_payload: Mapping[str, Any] | None,
    *,
    observed_correctness: float | None = None,
) -> MasteryStepExplanation | None:
    """Attribute the observation weight to its factors, or ``None`` if untraceable.

    ``observed_correctness`` is the attempt's graded score; it lives on the
    attempt row rather than the debug payload, so callers pass it in to pair the
    filter's expectation with what actually happened.

    Returns ``None`` rather than a partial chain when the payload carries no
    ``observation_weight`` -- there is nothing to explain and a fabricated
    breakdown would be worse than silence.
    """

    weight = _number(debug_payload, "observation_weight")
    if debug_payload is None or weight is None:
        return None

    reliability = _mapping(debug_payload, "reliability_trace")
    familiarity = _mapping(debug_payload, "familiarity_trace")
    coverage_trace = _mapping(debug_payload, "lo_relative_coverage_trace")
    error_impact = _mapping(debug_payload, "error_impact_trace")

    lo_coverage = _number(debug_payload, "lo_relative_coverage")
    effective_coverage = _number(debug_payload, "effective_coverage")

    candidates: list[MasteryStepFactor] = []
    if lo_coverage is not None:
        candidates.append(
            MasteryStepFactor(
                key="facet_coverage",
                label="facet coverage",
                detail=_coverage_detail(coverage_trace, effective_coverage),
                multiplier=lo_coverage,
            )
        )
    attempt_factor = _number(reliability, "attempt_type_mastery_factor")
    if attempt_factor is not None:
        candidates.append(
            MasteryStepFactor(
                key="attempt_type",
                label="attempt type",
                detail="evidence weight for this practice mode",
                multiplier=attempt_factor,
            )
        )
    grader_factor = _number(reliability, "grader_confidence_factor")
    if grader_factor is not None:
        candidates.append(
            MasteryStepFactor(
                key="grader_confidence",
                label="grader confidence",
                detail="how sure the grader was",
                multiplier=grader_factor,
            )
        )
    hint_factor = _number(reliability, "hint_mastery_factor")
    if hint_factor is not None:
        candidates.append(
            MasteryStepFactor(
                key="hints",
                label="hints used",
                detail="hinted work is weaker evidence",
                multiplier=hint_factor,
            )
        )
    sharpening = _number(debug_payload, "error_sharpening") or _number(error_impact, "error_sharpening")
    if sharpening is not None:
        candidates.append(
            MasteryStepFactor(
                key="error_sharpening",
                label="error severity",
                detail="a severe error sharpens the update",
                multiplier=sharpening,
            )
        )
    discount = _number(familiarity, "independent_evidence_discount")
    if discount is not None:
        candidates.append(
            MasteryStepFactor(
                key="familiarity",
                label="familiarity",
                detail=_familiarity_detail(familiarity),
                multiplier=discount,
            )
        )

    factors = tuple(f for f in candidates if abs(f.multiplier - 1.0) > _NEUTRAL_EPSILON)

    product = 1.0
    for factor in factors:
        product *= factor.multiplier
    product_reconciles = bool(factors) and abs(product - weight) <= _PRODUCT_TOLERANCE

    # Emphasise the term that cost the most weight, not merely the smallest one:
    # a factor above 1.0 (error sharpening) adds weight and must never win.
    penalties = [f for f in factors if f.multiplier < 1.0]
    dominant = min(penalties, key=lambda f: f.multiplier).key if penalties else None

    return MasteryStepExplanation(
        observation_weight=weight,
        factors=factors,
        expected_correctness=_number(debug_payload, "predicted_correctness"),
        observed_correctness=observed_correctness,
        dominant_factor_key=dominant,
        at_weight_floor=weight <= WEIGHT_FLOOR,
        product_reconciles=product_reconciles,
    )
