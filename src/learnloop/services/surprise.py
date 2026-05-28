from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from math import exp, log, pi, sqrt

from learnloop.clock import parse_utc
from learnloop.config import LearnLoopConfig
from learnloop.db.repositories import ActiveErrorEvent, MasteryState
from learnloop.services.mastery import (
    MasteryObservation,
    clamp,
    irt_observation,
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
) -> SurpriseResult:
    prior_variance = max(prior.logit_variance, 1e-9)
    posterior_variance = max(posterior.logit_variance, 1e-9)
    if config.mastery.irt.enabled:
        # Probability-space standardized innovation: (y - p) / sqrt(H^2 P + R_y).
        obs = irt_observation(item_a, item_b, prior, observation, config.mastery)
        y = clamp(observation.rubric_score / max(observation.max_points, 1), 0.0, 1.0)
        expected_correctness = obs.p
        predictive_variance = max(obs.innovation_variance, 1e-9)
        residual = (y - obs.p) / sqrt(predictive_variance)
    else:
        observation_variance = compute_observation_variance(observation, config)
        z_obs = logit(clamp(observation.rubric_score / max(observation.max_points, 1), 0.02, 0.98))
        predictive_variance = max(prior_variance + observation_variance, 1e-9)
        residual = (z_obs - prior.logit_mean) / sqrt(predictive_variance)
        expected_correctness = sigmoid(prior.logit_mean)

    predictive_surprise = 0.5 * (residual**2 + log(2 * pi * predictive_variance))
    bayesian_surprise = 0.5 * (
        log(prior_variance / posterior_variance)
        + posterior_variance / prior_variance
        + ((prior.logit_mean - posterior.logit_mean) ** 2) / prior_variance
        - 1
    )
    fsrs_interval_factor = clamp(
        exp(config.scheduler.surprise.alpha_interval * residual),
        config.scheduler.surprise.f_min,
        config.scheduler.surprise.f_max,
    )
    predicted_error_dist = predicted_error_type_distribution(
        prior_active_errors,
        observed_at=observation.observed_at,
    )
    observed = {
        "score_bucket": score_bucket(observation.rubric_score),
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


def score_bucket(rubric_score: int) -> str:
    if rubric_score <= 1:
        return "low"
    if rubric_score <= 3:
        return "mid"
    return "high"
