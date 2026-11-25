from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from math import exp, log, pi, sqrt
from typing import Any

from learnloop.clock import parse_utc
from learnloop.config import LearnLoopConfig
from learnloop.db.repositories import MasteryState
from learnloop.db.stores.learner_model import ActiveErrorEvent
from learnloop.numeric import clamp
from learnloop.learner.mastery import (
    MasteryObservation,
    irt_observation,
    irt_observation_at,
    logit,
    observation_weight,
    sigmoid,
)


@dataclass(frozen=True)
class SurpriseResult:
    predicted_score_dist: dict[str, float]
    predicted_error_type_dist: dict[str, float]
    observed_joint_bucket: dict[str, str | None]
    predictive_surprise: float
    bayesian_surprise: float
    surprise_direction: str
    fsrs_interval_factor: float
    posterior_delta: dict[str, float]

    def as_record(self, attempt_id: str, algorithm_version: str, created_at: str) -> dict[str, object]:
        return {
            "attempt_id": attempt_id,
            "predicted_score_dist": self.predicted_score_dist,
            "predicted_error_type_dist": self.predicted_error_type_dist,
            "observed_joint_bucket": self.observed_joint_bucket,
            "predictive_surprise": self.predictive_surprise,
            "bayesian_surprise": self.bayesian_surprise,
            "surprise_direction": self.surprise_direction,
            "fsrs_interval_factor": self.fsrs_interval_factor,
            "posterior_delta": self.posterior_delta,
            "triggered_actions": [],
            "suppressed_actions": [],
            "algorithm_version": algorithm_version,
            "created_at": created_at,
        }


def compute_observation_variance(observation: MasteryObservation, config: LearnLoopConfig) -> float:
    """Legacy logit-space observation variance (used when IRT is disabled)."""

    return config.mastery.base_observation_variance / max(observation_weight(observation), 0.10)


def _open_logit(p: float, clip: float) -> float:
    """``logit(p)``, exact inside (0, 1); a degenerate 0 or 1 is held at the configured clip."""

    q = p if 0.0 < p < 1.0 else clamp(p, clip, 1.0 - clip)
    return log(q / (1.0 - q))


def compute_surprise(
    *,
    prior: MasteryState,
    posterior: MasteryState,
    observation: MasteryObservation,
    observed_error_type: str | None,
    prior_active_errors: list[ActiveErrorEvent],
    config: LearnLoopConfig,
    item_a: float = 1.0,
    item_b: float = 0.0,
    forecast: Any = None,
    priming_offset: float = 0.0,
    record_source: bool = False,
    direct: bool = False,
) -> SurpriseResult:
    """``forecast`` (a :class:`~learnloop.attempts.surprise_forecast.SurpriseForecast`, from the label's
    retirement): adaptive difficulty's ``p̄`` made before the answer, which the predictive part is scored against
    (its innovation, variance and direction around ``b' = μ_prior − logit(p̄)/a``, the ``b`` at which the 2PL link
    at the prior mean equals ``p̄``; a primed answer takes the same ``priming_offset`` mastery's ``b`` took).
    Mastery's own ``(a, b)``, its prediction (``expected_correctness``) and the Bayesian surprise (the mastery
    update's KL) are unchanged, and the interval factor always reads mastery's residual, so FSRS never reads AD.
    ``record_source``: the row records which prediction it was scored against (from the retirement's tag).
    ``direct`` (from the fix round's tag): the forecast's probability is scored directly (:func:`_open_logit`, the
    configured clip once), also without the IRT link, and every row names its source."""

    prior_variance = max(prior.logit_variance, 1e-9)
    posterior_variance = max(posterior.logit_variance, 1e-9)
    scored: dict[str, Any] = {}
    if config.mastery.irt.enabled:
        # Probability-space standardized innovation: (y - p) / sqrt(H^2 P + R_y).
        obs = irt_observation(item_a, item_b, prior, observation, config.mastery)
        y = clamp(observation.rubric_score / max(observation.max_points, 1), 0.0, 1.0)
        expected_correctness = obs.p
        predictive_variance = max(obs.innovation_variance, 1e-9)
        residual = (y - obs.p) / sqrt(predictive_variance)
        mastery_residual = residual
        if forecast is not None and direct:
            # The forecast's own probability, shifted on its logit by a primed answer's offset and clipped once by
            # the configured clip; no inverse through ``b`` (none exists at a = 0) and no second clamp.
            p_effective = sigmoid(_open_logit(float(forecast.p), config.mastery.irt.p_clip) + item_a * priming_offset)
            scored_obs = irt_observation_at(p_effective, item_a, prior, observation, config.mastery)
            predictive_variance = max(scored_obs.innovation_variance, 1e-9)
            residual = (y - scored_obs.p) / sqrt(predictive_variance)
            scored = {"prediction_source": forecast.source, "receipt_key": forecast.receipt_key,
                      "forecaster": forecast.forecaster, "p_ad": float(forecast.p), "p_scored": scored_obs.p,
                      **({"b_scored": prior.logit_mean - log(scored_obs.p / (1.0 - scored_obs.p)) / item_a}
                         if item_a else {})}
        elif forecast is not None:
            clip = config.mastery.irt.p_clip
            p_effective = sigmoid(logit(clamp(float(forecast.p), clip, 1.0 - clip)) + item_a * priming_offset)
            b_scored = prior.logit_mean - logit(clamp(p_effective, clip, 1.0 - clip)) / item_a
            scored_obs = irt_observation(item_a, b_scored, prior, observation, config.mastery)
            predictive_variance = max(scored_obs.innovation_variance, 1e-9)
            residual = (y - scored_obs.p) / sqrt(predictive_variance)
            scored = {"prediction_source": forecast.source, "receipt_key": forecast.receipt_key,
                      "forecaster": forecast.forecaster, "p_ad": float(forecast.p),
                      "p_scored": scored_obs.p, "b_scored": b_scored}
        elif record_source:
            scored = {"prediction_source": "mastery", "p_scored": obs.p}
    else:
        observation_variance = compute_observation_variance(observation, config)
        z_obs = logit(clamp(observation.rubric_score / max(observation.max_points, 1), 0.02, 0.98))
        predictive_variance = max(prior_variance + observation_variance, 1e-9)
        residual = (z_obs - prior.logit_mean) / sqrt(predictive_variance)
        mastery_residual = residual
        expected_correctness = sigmoid(prior.logit_mean)
        if direct and forecast is not None:
            # Without the IRT link the observation is a logit score: surprise is centred on the forecast's logit
            # (a primed answer's offset added) instead of mastery's mean; the mastery update and the interval factor
            # keep mastery's residual.
            centre = _open_logit(float(forecast.p), config.mastery.irt.p_clip) + priming_offset
            residual = (z_obs - centre) / sqrt(predictive_variance)
            scored = {"prediction_source": forecast.source, "receipt_key": forecast.receipt_key,
                      "forecaster": forecast.forecaster, "p_ad": float(forecast.p), "p_scored": sigmoid(centre)}
        elif direct and record_source:
            scored = {"prediction_source": "mastery", "p_scored": expected_correctness}

    predictive_surprise = 0.5 * (residual**2 + log(2 * pi * predictive_variance))
    bayesian_surprise = 0.5 * (
        log(prior_variance / posterior_variance)
        + posterior_variance / prior_variance
        + ((prior.logit_mean - posterior.logit_mean) ** 2) / prior_variance
        - 1
    )
    fsrs_interval_factor = clamp(
        exp(config.scheduler.surprise.alpha_interval * mastery_residual),
        config.scheduler.surprise.f_min,
        config.scheduler.surprise.f_max,
    )
    predicted_error_dist = predicted_error_type_distribution(
        prior_active_errors,
        observed_at=observation.observed_at,
    )
    observed = {
        "score_bucket": score_bucket(observation.rubric_score, observation.max_points),
        "error_type": observed_error_type,
    }
    if (
        observed_error_type is not None
        and predicted_error_dist.get(observed_error_type, 0.0) < config.scheduler.surprise.epsilon_error_surprise
    ):
        direction = "negative"
    elif residual > config.scheduler.surprise.theta_pos:
        direction = "positive"
    elif residual < -config.scheduler.surprise.theta_neg:
        direction = "negative"
    else:
        direction = "none"

    return SurpriseResult(
        predicted_score_dist={
            "mu_z": prior.logit_mean,
            "sigma_z": sqrt(predictive_variance),
            "b": item_b,
            "a": item_a,
            "expected_correctness": expected_correctness,
            **scored,
        },
        predicted_error_type_dist=predicted_error_dist,
        observed_joint_bucket=observed,
        predictive_surprise=predictive_surprise,
        bayesian_surprise=bayesian_surprise,
        surprise_direction=direction,
        fsrs_interval_factor=fsrs_interval_factor,
        posterior_delta={
            "mu_before": prior.logit_mean,
            "mu_after": posterior.logit_mean,
            "P_before": prior.logit_variance,
            "P_after": posterior.logit_variance,
        },
    )


def predicted_error_type_distribution(
    prior_active_errors: list[ActiveErrorEvent],
    *,
    observed_at: datetime,
) -> dict[str, float]:
    weights: dict[str, float] = {"null": 1.0}
    now = observed_at.astimezone(UTC)
    for event in prior_active_errors:
        created_at = parse_utc(event.created_at)
        if created_at is None:
            continue
        days_since = max(0.0, (now - created_at).total_seconds() / 86400)
        weights[event.error_type] = weights.get(event.error_type, 0.0) + event.severity * exp(-days_since / 7)
    total = sum(weights.values())
    if total <= 0:
        return {"null": 1.0}
    return {key: value / total for key, value in sorted(weights.items())}


def score_bucket(rubric_score: int, max_points: int = 4) -> str:
    normalized = 4.0 * rubric_score / max(max_points, 1)
    if normalized <= 1:
        return "low"
    if normalized <= 3:
        return "mid"
    return "high"
