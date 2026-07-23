"""Reliability-aware EffectiveObservation (spec_p0_measurement_correctness §4.3).

Canonical certification (and the mastery reliability path) consume an
``EffectiveObservation``, not raw attempt columns. For a coarse outcome
distribution ``p(z) = P(Z | E)``::

    certainty        = 1 - H(p) / log(K)               # K = number of true classes
    certainty_LCB    = lower-pct of certainty across the calibration ensemble
    epistemic_factor = certainty_LCB / certainty       # 1 as the ensemble tightens
    effective_mass   = attempt_type_mass
                     * assistance_discount
                     * familiarity_discount
                     * epistemic_factor
    positive_mass    = effective_mass * E[true_score_fraction]
    negative_mass    = effective_mass * (1 - E[true_score_fraction])

``E[true_score_fraction] = sum_z P(Z|E) * score_fraction[z]`` from the bound outcome
schema. The posterior spread ALREADY hedges the mass split (P4.2 revision): a
0.8/0.1/0.1 posterior banks 0.85 positive / 0.15 negative, so multiplying the mass
by the certainty LCB as well double-counted the same aleatoric uncertainty and made
Demonstrated effectively unreachable under the permanent heuristic prior. The mass
discount is now only the EPISTEMIC part — how far model uncertainty (the Dirichlet
ensemble spread) degrades the interpretive certainty below its point value. It
tends to 1 as calibration data accumulates and stays 1 for deterministic grades,
while a genuinely noisy grader keeps paying through the posterior split itself.

Reliability *discounts* (never creates) mass, so the existing correlation caps,
dependency localization, assistance, and familiarity discounts still bind AFTER
this discount. Deterministic / point-adjudicated outcomes have certainty 1; a
uniform interpretation has certainty 0 -> zero mass (its LCB is also 0 and the
factor is defined as 0 there); a quarantined observation contributes zero until
an append-only resolution activates a new interpretation.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from typing import Any, Mapping

from learnloop.db.repositories import Repository
from learnloop.services import robust_composition as rc

# The projection-algorithm version the shared certainty context is derived under.
# Kept in sync with grade_resolution.PROJECTION_ALGORITHM_VERSION (asserted in the
# H1 regression test); duplicated here to avoid a circular import.
SHARED_CERTAINTY_PROJECTION_VERSION = "grade_interpretation_v1"


def shared_certainty_lcb(
    *,
    joint_alpha: Mapping[str, Mapping[str, float]],
    observed_emission: str,
    calibration_model_hash: str,
    posterior: Mapping[str, float],
    projection_algorithm_version: str = SHARED_CERTAINTY_PROJECTION_VERSION,
    quantile: float | None = None,
) -> float:
    """THE one canonical certainty LCB (spec §4.3 final ¶).

    Both the mastery path (``grade_resolution.response_certainty_lcb``) and the
    certification path (``build_effective_observation``) compute the certainty
    lower credible bound through this single helper so they can never disagree
    about grader trust. It draws the pooled resolved model's Dirichlet at ONE
    canonical decision context (independent of episode/observation/item identity
    -- those inputs are what made the two paths diverge), so the value is a pure
    function of the pinned model + emission + posterior + registered params.

    ``quantile`` is the ensemble percentile the bound reads (P4: a fitted policy
    knob, ``fitted_params.resolve_grader_channel_prior``); ``None`` keeps the
    robust-composition default.
    """

    ctx = rc.decision_context_hash(
        episode_id=None,
        candidate_card_version=None,
        resolved_slot_map=None,
        posterior_at_selection=posterior,
        projection_algorithm_version=projection_algorithm_version,
    )
    kwargs: dict[str, Any] = {}
    if quantile is not None:
        kwargs["quantile"] = quantile
    return rc.certainty_lcb(
        joint_alpha=joint_alpha,
        observed_emission=observed_emission,
        calibration_model_hash=calibration_model_hash,
        decision_context_hash=ctx,
        **kwargs,
    )


def _certainty(posterior: Mapping[str, float]) -> float:
    """1 - H(p)/log(K): 0 for uniform, 1 for a point mass (§4.3)."""

    k = len(posterior)
    if k <= 1:
        return 1.0
    entropy = 0.0
    for p in posterior.values():
        if p > 0:
            entropy -= p * math.log(p)
    return max(0.0, min(1.0, 1.0 - entropy / math.log(k)))


def expected_true_score_fraction(
    posterior: Mapping[str, float], score_fraction: Mapping[str, float]
) -> float:
    """``E[true_score_fraction] = sum_z P(Z|E) * score_fraction[z]``."""

    return sum(
        float(p) * float(score_fraction.get(z, 0.0)) for z, p in posterior.items()
    )


@dataclass(frozen=True)
class EffectiveObservation:
    """The reliability-discounted evidence one graded observation contributes.

    ``effective_mass`` is the pre-cap discounted mass; ``positive_mass`` /
    ``negative_mass`` split it by the calibrated expected true-score fraction. The
    projection applies caps / localization / assistance / familiarity discounts on
    top of these (they can only shrink mass further -- reliability never creates)."""

    observation_id: str | None
    posterior: dict[str, float]
    certainty: float
    certainty_lcb: float
    expected_true_score_fraction: float
    attempt_type_mass: float
    assistance_discount: float
    familiarity_discount: float
    quarantined: bool
    unassessable: bool
    calibration_model_id: str | None
    calibration_model_hash: str | None
    calibration_status: str
    projection_algorithm_version: str | None
    lineage_model_ids: tuple[str, ...]

    @property
    def epistemic_factor(self) -> float:
        """``certainty_lcb / certainty`` — model-level doubt only (module docstring).

        The ratio strips the aleatoric component (already priced into the
        positive/negative split via ``expected_true_score_fraction``) out of the
        LCB: a cold-but-consistent channel scores ~0.9, a data-backed channel ~1,
        and a uniform/empty posterior (certainty 0) scores 0 so the §4.3
        zero-mass invariants hold unchanged.
        """

        # Epsilon guards float dust: an exactly-uniform posterior computes
        # certainty ~1e-16, and a bare ratio would blow that up to 1.
        if self.certainty < 1e-9:
            return 0.0
        return max(0.0, min(1.0, self.certainty_lcb / self.certainty))

    @property
    def effective_mass(self) -> float:
        if self.quarantined or self.unassessable:
            return 0.0
        mass = (
            self.attempt_type_mass
            * self.assistance_discount
            * self.familiarity_discount
            * self.epistemic_factor
        )
        return max(0.0, mass)

    @property
    def positive_mass(self) -> float:
        return self.effective_mass * self.expected_true_score_fraction

    @property
    def negative_mass(self) -> float:
        return self.effective_mass * (1.0 - self.expected_true_score_fraction)


def effective_observation_from_posterior(
    *,
    observation_id: str | None,
    posterior: Mapping[str, float],
    score_fraction: Mapping[str, float],
    certainty_lcb: float,
    attempt_type_mass: float,
    assistance_discount: float = 1.0,
    familiarity_discount: float = 1.0,
    quarantined: bool = False,
    unassessable: bool = False,
    calibration_model_id: str | None = None,
    calibration_model_hash: str | None = None,
    calibration_status: str = "heuristic",
    projection_algorithm_version: str | None = None,
    lineage_model_ids: tuple[str, ...] = (),
) -> EffectiveObservation:
    """Build an EffectiveObservation from an already-computed posterior + LCB.

    Pure/unit-testable core (§9.2). A uniform posterior yields certainty 0 (its LCB
    is <= its point certainty, also 0) and thus zero mass."""

    posterior = {z: max(0.0, float(p)) for z, p in posterior.items()}
    return EffectiveObservation(
        observation_id=observation_id,
        posterior=dict(posterior),
        certainty=_certainty(posterior),
        certainty_lcb=max(0.0, min(1.0, float(certainty_lcb))),
        expected_true_score_fraction=expected_true_score_fraction(posterior, score_fraction),
        attempt_type_mass=float(attempt_type_mass),
        assistance_discount=float(assistance_discount),
        familiarity_discount=float(familiarity_discount),
        quarantined=quarantined,
        unassessable=unassessable,
        calibration_model_id=calibration_model_id,
        calibration_model_hash=calibration_model_hash,
        calibration_status=calibration_status,
        projection_algorithm_version=projection_algorithm_version,
        lineage_model_ids=tuple(lineage_model_ids),
    )


def build_effective_observation(
    repository: Repository,
    *,
    interpretation: Mapping[str, Any] | None,
    score_fraction: Mapping[str, float],
    attempt_type_mass: float,
    assistance_discount: float = 1.0,
    familiarity_discount: float = 1.0,
    observation_id: str | None = None,
    unassessable: bool = False,
) -> EffectiveObservation:
    """Assemble the EffectiveObservation for a P0.2 calibrated interpretation.

    ``interpretation`` is the active ``grade_interpretations`` row (or None for a
    legacy observation with no P0.2 row -- falls to the compatibility branch: zero
    reliable mass, never a silent full-credit, §4.3). The certainty LCB is drawn
    from the resolved model's Dirichlet ensemble seeded on the interpretation's
    pinned ``calibration_model_hash`` (byte-stable)."""

    if interpretation is None:
        return effective_observation_from_posterior(
            observation_id=observation_id,
            posterior={},
            score_fraction=score_fraction,
            certainty_lcb=0.0,
            attempt_type_mass=attempt_type_mass,
            assistance_discount=assistance_discount,
            familiarity_discount=familiarity_discount,
            quarantined=False,
            unassessable=unassessable,
            calibration_status="missing_interpretation",
        )

    posterior = json.loads(interpretation["response_posterior_json"])
    quarantined = interpretation.get("quarantine_state") == "quarantined"
    model_id = interpretation.get("calibration_model_id")
    model_hash = interpretation.get("calibration_model_hash") or ""
    proj_version = interpretation.get("projection_algorithm_version")
    lineage = tuple(json.loads(interpretation.get("reference_prior_ids_json") or "[]"))

    # Resolve the calibration status from the persisted model row (heuristic ->
    # calibrated wording gate, §9.3). Fallback models are heuristic.
    model_row = repository.find_calibration_model_by_hash(model_hash) if model_hash else None
    status = model_row.get("status") if model_row else "heuristic"

    stored = interpretation.get("shared_certainty_lcb")
    if stored is not None:
        # H1: consume the ONE certainty LCB persisted at interpretation time from
        # the pooled resolved model (spec §4.3 final ¶); mastery reads the same.
        certainty_lcb_value = max(0.0, min(1.0, float(stored)))
    else:
        certainty_lcb_value = _certainty_lcb_for_interpretation(
            repository, interpretation, posterior
        )

    return effective_observation_from_posterior(
        observation_id=observation_id or interpretation.get("observation_id"),
        posterior=posterior,
        score_fraction=score_fraction,
        certainty_lcb=certainty_lcb_value,
        attempt_type_mass=attempt_type_mass,
        assistance_discount=assistance_discount,
        familiarity_discount=familiarity_discount,
        quarantined=quarantined,
        unassessable=unassessable,
        calibration_model_id=model_id,
        calibration_model_hash=model_hash or None,
        calibration_status=status or "heuristic",
        projection_algorithm_version=proj_version,
        lineage_model_ids=lineage,
    )


def _certainty_lcb_for_interpretation(
    repository: Repository,
    interpretation: Mapping[str, Any],
    posterior: Mapping[str, float],
) -> float:
    """Fallback recompute of the shared certainty LCB for a row that predates the
    persisted ``shared_certainty_lcb`` column (H1, spec §4.3 final ¶).

    Reconstructs the POOLED resolved-model alpha by summing the contributing
    models' Dirichlet rows (persisted in ``reference_prior_ids_json``) -- the same
    pooled composite mastery/certification wrote -- then routes through
    :func:`shared_certainty_lcb` so the recompute matches what would have been
    persisted. A point-adjudicated / deterministic posterior short-circuits to 1.
    """

    from learnloop.services import grader_calibration as gc

    # Deterministic / point-adjudicated: the posterior is already a point mass.
    top = max(posterior.values()) if posterior else 0.0
    if top >= 1.0 - 1e-9:
        return 1.0

    model_hash = interpretation.get("calibration_model_hash") or ""
    lineage: tuple[str, ...] = tuple(
        json.loads(interpretation.get("reference_prior_ids_json") or "[]")
    )
    if lineage:
        pooled = gc._sum_alphas(
            [repository.fetch_calibration_alphas(mid) for mid in lineage]
        )
    else:
        model_id = interpretation.get("calibration_model_id")
        pooled = repository.fetch_calibration_alphas(model_id) if model_id else {}
    if not pooled:
        # No persisted model row (should not happen post-P0.2); conservative bound.
        return _certainty(posterior)

    raw = repository.raw_grade_event(interpretation["raw_grade_event_id"])
    if raw is None:
        return _certainty(posterior)
    emission = f"{raw['observed_class']}|{raw['confidence_bucket']}"
    from learnloop.services.fitted_params import resolve_grader_channel_prior

    return shared_certainty_lcb(
        joint_alpha=pooled,
        observed_emission=emission,
        calibration_model_hash=model_hash,
        posterior=posterior,
        projection_algorithm_version=str(
            interpretation.get("projection_algorithm_version")
            or SHARED_CERTAINTY_PROJECTION_VERSION
        ),
        quantile=resolve_grader_channel_prior(repository).lcb_quantile,
    )
