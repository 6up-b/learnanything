from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from math import exp, log

from learnloop.clock import parse_utc
from learnloop.config import MasteryConfig
from learnloop.db.repositories import MasteryState


ATTEMPT_TYPE_FACTORS: dict[str, float] = {
    "independent_attempt": 1.0,
    "diagnostic_probe": 1.0,
    "hinted_attempt": 1.0,
    "reconstruction_after_walkthrough": 0.5,
    "dont_know": 0.7,
    "self_report": 0.3,
    "guided_walkthrough": 0.0,
    "skip": 0.0,
}


@dataclass(frozen=True)
class MasteryObservation:
    rubric_score: int
    max_points: int
    evidence_coverage: float
    hint_dampening: float
    grader_confidence: float
    attempt_type: str
    observed_at: datetime


@dataclass(frozen=True)
class MasteryDisplay:
    mastery_mean: float
    mastery_variance: float


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


def _iso(value: datetime) -> str:
    return value.astimezone(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def update_mastery(
    prior: MasteryState,
    observation: MasteryObservation,
    config: MasteryConfig,
    algorithm_version: str,
) -> MasteryState:
    y = clamp(observation.rubric_score / max(observation.max_points, 1), 0.02, 0.98)
    z_obs = logit(y)
    attempt_factor = ATTEMPT_TYPE_FACTORS.get(observation.attempt_type, 1.0)
    weight = (
        clamp(observation.evidence_coverage, 0.0, 1.0)
        * clamp(observation.hint_dampening, 0.0, 1.0)
        * clamp(observation.grader_confidence, 0.0, 1.0)
        * attempt_factor
    )
    observation_variance = config.base_observation_variance / max(weight, 0.10)
    last_evidence_at = parse_utc(prior.last_evidence_at)
    days_since = 0.0
    if last_evidence_at is not None:
        days_since = max(0.0, (observation.observed_at - last_evidence_at).total_seconds() / 86400)
    predicted_variance = min(prior.logit_variance + config.sigma2_drift * days_since, config.p_max)
    kalman_gain = predicted_variance / (predicted_variance + observation_variance)
    next_mean = prior.logit_mean + kalman_gain * (z_obs - prior.logit_mean)
    next_variance = (1 - kalman_gain) * predicted_variance
    return MasteryState(
        learning_object_id=prior.learning_object_id,
        logit_mean=next_mean,
        logit_variance=next_variance,
        evidence_count=prior.evidence_count + 1,
        last_evidence_at=_iso(observation.observed_at),
        algorithm_version=algorithm_version,
        updated_at=_iso(observation.observed_at),
    )
