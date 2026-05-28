from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from math import copysign, exp, log
from typing import TYPE_CHECKING, Any

from learnloop.attempt_types import ATTEMPT_TYPE_FACTORS
from learnloop.clock import parse_utc
from learnloop.config import MasteryConfig
from learnloop.db.repositories import MasteryState

if TYPE_CHECKING:  # pragma: no cover - typing only
    from learnloop.vault.models import LearningObject, PracticeItem


@dataclass(frozen=True)
class MasteryObservation:
    rubric_score: int
    max_points: int
    evidence_coverage: float
    hint_dampening: float
    grader_confidence: float
    attempt_type: str
    observed_at: datetime
    item_coverage: float | None = None
    effective_coverage: float | None = None
    covered_facets: dict[str, float] | None = None
    facet_outcomes: dict[str, float] | None = None
    independent_evidence_discount: float = 1.0
    attempt_modifiers: dict[str, float] | None = None
    coverage_trace: dict[str, Any] | None = None
    reliability_trace: dict[str, Any] | None = None
    familiarity_trace: dict[str, Any] | None = None
    error_sharpening: float = 1.0
    observation_reliability: float | None = None
    observation_weight_override: float | None = None


@dataclass(frozen=True)
class MasteryDisplay:
    mastery_mean: float
    mastery_variance: float


@dataclass(frozen=True)
class IrtObservation:
    """The 2PL link linearized at the prior mean (spec_irt_difficulty.md §4.1).

    Shared by the Channel-1 mastery EKF and the probability-space surprise so
    both read the *same* observation mechanism for a given item.
    """

    p: float                    # predicted correctness sigma(a(mu - b)), clipped to p_clip
    sensitivity_h: float        # H = a * p(1-p)  (measurement sensitivity dp/dtheta)
    measurement_noise: float    # R_y = base * p(1-p) / max(weight, 0.10)
    predicted_variance: float   # P_pred = min(P + sigma2_drift * days_since, p_max)
    innovation_variance: float  # S = H^2 * P_pred + R_y
    kalman_gain: float          # K = P_pred * H / S


@dataclass(frozen=True)
class MasteryObservationTrace:
    """Full IRT picture of one mastery update, for debug logging (spec §7.1).

    Computed where the EKF math already runs; never re-queries state.
    """

    item_id: str
    difficulty_b: float
    discrimination_a: float
    theta_prior: float           # mu before
    expected_correctness: float  # p = sigma(a(mu - b))
    predicted_score: float       # max_points * p
    observed_y: float            # score / max_points
    innovation: float            # y - p (drives the mean move; the realized surprise)
    sensitivity_h: float         # H = a * p(1-p)
    fisher_information: float     # a^2 * p(1-p)  (the Channel-2 / selection quantity)
    measurement_noise: float     # R_y
    innovation_variance: float   # S = H^2 * P_pred + R_y
    kalman_gain: float           # K
    variance_reduction: float    # K * H  (fraction of P_pred removed)
    mu_before: float
    mu_after: float              # post step-cap and mu clamp
    mu_step: float               # mu_after - mu_before
    step_capped: bool
    mu_clamped: bool
    p_before: float
    p_after: float


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def sigmoid(value: float) -> float:
    return 1 / (1 + exp(-value))


def logit(value: float) -> float:
    clipped = clamp(value, 0.02, 0.98)
    return log(clipped / (1 - clipped))


def display_mastery(state: MasteryState) -> MasteryDisplay:
    mean = sigmoid(state.logit_mean)
    variance = (mean * (1 - mean)) ** 2 * state.logit_variance
    return MasteryDisplay(mastery_mean=mean, mastery_variance=variance)


def initial_mastery_state(learning_object_id: str, algorithm_version: str, now_iso: str) -> MasteryState:
    return MasteryState(
        learning_object_id=learning_object_id,
        logit_mean=0.0,
        logit_variance=1.0,
        evidence_count=0,
        last_evidence_at=None,
        algorithm_version=algorithm_version,
        updated_at=now_iso,
    )


def initial_mastery_state_for_learning_object(vault, repository, learning_object_id: str, now_iso: str) -> MasteryState:
    state = initial_mastery_state(learning_object_id, vault.config.algorithms.algorithm_version, now_iso)
    claim = covering_learner_claim(vault, repository, learning_object_id)
    if claim is None:
        return state
    claimed_level = float(claim["claimed_level"])
    if claimed_level < vault.config.probe.claim_skip_threshold:
        return state
    prior_pseudo_count = max(float(claim["prior_pseudo_count"]), 0.25)
    return MasteryState(
        learning_object_id=learning_object_id,
        logit_mean=logit(claimed_level),
        logit_variance=1 / prior_pseudo_count,
        evidence_count=0,
        last_evidence_at=None,
        algorithm_version=vault.config.algorithms.algorithm_version,
        updated_at=now_iso,
    )


def covering_learner_claim(vault, repository, learning_object_id: str) -> dict[str, Any] | None:
    learning_object = vault.learning_objects.get(learning_object_id)
    if learning_object is None:
        return None
    candidates = [
        claim
        for claim in repository.learner_claims()
        if _claim_covers_learning_object(claim, learning_object)
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda claim: _claim_rank(claim))


def _claim_covers_learning_object(claim: dict[str, Any], learning_object) -> bool:
    scope_type = claim.get("scope_type")
    scope_id = claim.get("scope_id")
    if scope_type == "global":
        return True
    if scope_type == "learning_object":
        return scope_id == learning_object.id
    if scope_type == "concept":
        return scope_id == learning_object.concept
    if scope_type in {"subject", "domain"}:
        return scope_id is None or scope_id in set(learning_object.subjects)
    return False


def _claim_rank(claim: dict[str, Any]) -> tuple[int, float, float, str, str]:
    specificity = {
        "learning_object": 4,
        "concept": 3,
        "subject": 2,
        "domain": 2,
        "global": 1,
    }.get(str(claim.get("scope_type")), 0)
    return (
        specificity,
        float(claim.get("prior_pseudo_count") or 0.0),
        float(claim.get("claimed_level") or 0.0),
        str(claim.get("created_at") or ""),
        str(claim.get("id") or ""),
    )


def _iso(value: datetime) -> str:
    return value.astimezone(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def observation_weight(observation: MasteryObservation) -> float:
    """Reliability weight of an observation (spec §4.1).

    Low-confidence / self-graded / hinted attempts move ``mu`` less.
    """

    if observation.observation_weight_override is not None:
        return max(0.0, observation.observation_weight_override)
    attempt_factor = ATTEMPT_TYPE_FACTORS.get(observation.attempt_type, 1.0)
    return (
        clamp(observation.evidence_coverage, 0.0, 1.0)
        * clamp(observation.hint_dampening, 0.0, 1.0)
        * clamp(observation.grader_confidence, 0.0, 1.0)
        * attempt_factor
    )


def predicted_logit_variance(
    prior: MasteryState,
    observation: MasteryObservation,
    config: MasteryConfig,
) -> float:
    """``P_pred = min(P + sigma2_drift * days_since, p_max)`` — prior variance grown by drift."""

    last_evidence_at = parse_utc(prior.last_evidence_at)
    days_since = 0.0
    if last_evidence_at is not None:
        days_since = max(0.0, (observation.observed_at - last_evidence_at).total_seconds() / 86400)
    return min(prior.logit_variance + config.sigma2_drift * days_since, config.p_max)


def item_irt_params(
    item: "PracticeItem | None",
    learning_object: "LearningObject | None",
    config: MasteryConfig,
) -> tuple[float, float]:
    """Resolve ``(a, b)`` for an item from **static** authored/LLM fields (spec §4.3).

    ``b`` falls back ``PracticeItem.difficulty`` -> ``LearningObject.difficulty_prior``
    -> ``difficulty_default``. The FSRS ``practice_item_state.difficulty`` is never
    consulted — only the static vault field.
    """

    irt = config.irt
    a = irt.discrimination_default
    if not irt.difficulty_from_prior:
        return a, irt.difficulty_default
    difficulty = getattr(item, "difficulty", None) if item is not None else None
    if difficulty is None and learning_object is not None:
        difficulty = getattr(learning_object, "difficulty_prior", None)
    if difficulty is None:
        return a, irt.difficulty_default
    b = irt.difficulty_prior_scale * (float(difficulty) - 0.5) * 2.0
    return a, clamp(b, -irt.b_abs_max, irt.b_abs_max)


def irt_observation(
    item_a: float,
    item_b: float,
    prior: MasteryState,
    observation: MasteryObservation,
    config: MasteryConfig,
) -> IrtObservation:
    """Linearize the 2PL link at the prior mean (spec §4.1).

    ``R_y`` carries the Bernoulli variance ``p(1-p)`` so the ``p(1-p)`` cancels in
    ``K`` and the gain stays well-defined as ``p -> 0/1``.
    """

    irt = config.irt
    p_raw = sigmoid(item_a * (prior.logit_mean - item_b))
    p = clamp(p_raw, irt.p_clip, 1.0 - irt.p_clip)
    pq = p * (1.0 - p)
    sensitivity_h = item_a * pq
    weight = observation_weight(observation)
    measurement_noise = config.base_observation_variance * pq / max(weight, 0.10)
    predicted_variance = predicted_logit_variance(prior, observation, config)
    innovation_variance = sensitivity_h * sensitivity_h * predicted_variance + measurement_noise
    kalman_gain = predicted_variance * sensitivity_h / innovation_variance if innovation_variance > 0 else 0.0
    return IrtObservation(
        p=p,
        sensitivity_h=sensitivity_h,
        measurement_noise=measurement_noise,
        predicted_variance=predicted_variance,
        innovation_variance=innovation_variance,
        kalman_gain=kalman_gain,
    )


def update_mastery(
    prior: MasteryState,
    observation: MasteryObservation,
    config: MasteryConfig,
    algorithm_version: str,
    *,
    item_a: float = 1.0,
    item_b: float = 0.0,
) -> MasteryState:
    state, _trace = update_mastery_traced(
        prior, observation, config, algorithm_version, item_a=item_a, item_b=item_b
    )
    return state


def update_mastery_traced(
    prior: MasteryState,
    observation: MasteryObservation,
    config: MasteryConfig,
    algorithm_version: str,
    *,
    item_a: float = 1.0,
    item_b: float = 0.0,
    item_id: str = "",
) -> tuple[MasteryState, MasteryObservationTrace]:
    """Difficulty-aware mastery update returning the posterior plus an IRT trace.

    With ``config.irt.enabled`` the probability-space EKF of §4.1 runs; otherwise
    the legacy logit-space Kalman update is reproduced bit-for-bit (§6.2).
    """

    if not config.irt.enabled:
        return _legacy_update_mastery(prior, observation, config, algorithm_version, item_a, item_b, item_id)
    return _ekf_update_mastery(prior, observation, config, algorithm_version, item_a, item_b, item_id)


def _ekf_update_mastery(
    prior: MasteryState,
    observation: MasteryObservation,
    config: MasteryConfig,
    algorithm_version: str,
    item_a: float,
    item_b: float,
    item_id: str,
) -> tuple[MasteryState, MasteryObservationTrace]:
    irt = config.irt
    max_points = max(observation.max_points, 1)
    y = clamp(observation.rubric_score / max_points, 0.0, 1.0)
    obs = irt_observation(item_a, item_b, prior, observation, config)

    mu_before = prior.logit_mean
    innovation = y - obs.p
    mu_raw = mu_before + obs.kalman_gain * innovation

    # Step cap: the single linearization can overshoot on a broad prior with an
    # extreme observation; K is not bounded by 1 (spec §4.4).
    step = mu_raw - mu_before
    step_capped = abs(step) > irt.max_logit_step
    if step_capped:
        mu_raw = mu_before + copysign(irt.max_logit_step, step)

    # mu sanity clamp (mean only; leave P_new from the filter).
    mu_after = clamp(mu_raw, -irt.mu_abs_max, irt.mu_abs_max)
    mu_clamped = mu_after != mu_raw

    variance_reduction = obs.kalman_gain * obs.sensitivity_h
    next_variance = (1.0 - variance_reduction) * obs.predicted_variance

    state = MasteryState(
        learning_object_id=prior.learning_object_id,
        logit_mean=mu_after,
        logit_variance=next_variance,
        evidence_count=prior.evidence_count + 1,
        last_evidence_at=_iso(observation.observed_at),
        algorithm_version=algorithm_version,
        updated_at=_iso(observation.observed_at),
    )
    trace = MasteryObservationTrace(
        item_id=item_id,
        difficulty_b=item_b,
        discrimination_a=item_a,
        theta_prior=mu_before,
        expected_correctness=obs.p,
        predicted_score=max_points * obs.p,
        observed_y=y,
        innovation=innovation,
        sensitivity_h=obs.sensitivity_h,
        fisher_information=item_a * obs.sensitivity_h,
        measurement_noise=obs.measurement_noise,
        innovation_variance=obs.innovation_variance,
        kalman_gain=obs.kalman_gain,
        variance_reduction=variance_reduction,
        mu_before=mu_before,
        mu_after=mu_after,
        mu_step=mu_after - mu_before,
        step_capped=step_capped,
        mu_clamped=mu_clamped,
        p_before=obs.p,
        p_after=sigmoid(item_a * (mu_after - item_b)),
    )
    return state, trace


def _legacy_update_mastery(
    prior: MasteryState,
    observation: MasteryObservation,
    config: MasteryConfig,
    algorithm_version: str,
    item_a: float,
    item_b: float,
    item_id: str,
) -> tuple[MasteryState, MasteryObservationTrace]:
    """The pre-IRT logit-space Kalman update, reproduced bit-for-bit (spec §6.2)."""

    y = clamp(observation.rubric_score / max(observation.max_points, 1), 0.02, 0.98)
    z_obs = logit(y)
    observation_variance = config.base_observation_variance / max(observation_weight(observation), 0.10)
    predicted_variance = predicted_logit_variance(prior, observation, config)
    kalman_gain = predicted_variance / (predicted_variance + observation_variance)
    next_mean = prior.logit_mean + kalman_gain * (z_obs - prior.logit_mean)
    next_variance = (1 - kalman_gain) * predicted_variance
    state = MasteryState(
        learning_object_id=prior.learning_object_id,
        logit_mean=next_mean,
        logit_variance=next_variance,
        evidence_count=prior.evidence_count + 1,
        last_evidence_at=_iso(observation.observed_at),
        algorithm_version=algorithm_version,
        updated_at=_iso(observation.observed_at),
    )
    p_before = sigmoid(prior.logit_mean)
    observed_y = observation.rubric_score / max(observation.max_points, 1)
    trace = MasteryObservationTrace(
        item_id=item_id,
        difficulty_b=item_b,
        discrimination_a=item_a,
        theta_prior=prior.logit_mean,
        expected_correctness=p_before,
        predicted_score=max(observation.max_points, 1) * p_before,
        observed_y=observed_y,
        innovation=observed_y - p_before,
        sensitivity_h=0.0,
        fisher_information=0.0,
        measurement_noise=observation_variance,
        innovation_variance=predicted_variance + observation_variance,
        kalman_gain=kalman_gain,
        variance_reduction=kalman_gain,
        mu_before=prior.logit_mean,
        mu_after=next_mean,
        mu_step=next_mean - prior.logit_mean,
        step_capped=False,
        mu_clamped=False,
        p_before=p_before,
        p_after=sigmoid(next_mean),
    )
    return state, trace
