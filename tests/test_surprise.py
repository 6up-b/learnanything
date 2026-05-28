from __future__ import annotations

from datetime import UTC, datetime

from learnloop.config import LearnLoopConfig, MasteryConfig
from learnloop.db.repositories import MasteryState
from learnloop.services.mastery import MasteryObservation, update_mastery
from learnloop.services.surprise import compute_surprise

VERSION = "mvp-0.1"
NOW = datetime(2026, 5, 19, 12, 0, tzinfo=UTC)


def _prior(mean: float) -> MasteryState:
    return MasteryState("lo", mean, 1.0, 0, None, VERSION, "2026-05-19T12:00:00Z")


def _obs(score: int, *, coverage=1.0) -> MasteryObservation:
    return MasteryObservation(
        rubric_score=score,
        max_points=4,
        evidence_coverage=coverage,
        hint_dampening=1.0,
        grader_confidence=1.0,
        attempt_type="independent_attempt",
        observed_at=NOW,
    )


def _surprise(prior_mean: float, score: int, *, item_b: float = 0.0, observed_error_type=None, prior_errors=None):
    config = LearnLoopConfig()
    prior = _prior(prior_mean)
    observation = _obs(score)
    posterior = update_mastery(prior, observation, MasteryConfig(), VERSION, item_b=item_b)
    return compute_surprise(
        prior=prior,
        posterior=posterior,
        observation=observation,
        observed_error_type=observed_error_type,
        prior_active_errors=prior_errors or [],
        config=config,
        item_b=item_b,
    )


def test_positive_surprise_when_hard_item_is_aced():
    # On a hard item (b=+2) acing it is strongly surprising (residual ~2.6 > theta_pos).
    result = _surprise(0.0, 4, item_b=2.0)
    assert result.surprise_direction == "positive"


def test_negative_surprise_when_easy_item_is_failed():
    # On a trivial item (b=-2) failing it is strongly surprising (residual ~-2.6).
    result = _surprise(0.0, 0, item_b=-2.0)
    assert result.surprise_direction == "negative"


def test_negative_surprise_when_high_prior_meets_low_score():
    result = _surprise(3.0, 1)
    assert result.surprise_direction == "negative"


def test_no_surprise_for_on_target_outcome():
    # A 50/50 (on-target, b=0) outcome is unsurprising either way (spec §9).
    assert _surprise(0.0, 4).surprise_direction == "none"
    assert _surprise(0.0, 0).surprise_direction == "none"


def test_no_surprise_for_expected_outcome():
    result = _surprise(0.0, 2)
    assert result.surprise_direction == "none"


def test_easy_correct_and_hard_wrong_are_unsurprising():
    # Expected outcomes barely move the standardized innovation (spec §4.2 / §9).
    assert _surprise(0.0, 4, item_b=-2.0).surprise_direction == "none"  # easy correct
    assert _surprise(0.0, 0, item_b=2.0).surprise_direction == "none"   # hard wrong


def test_error_type_channel_forces_negative():
    # No prior active errors -> observed error type has ~0 predicted mass -> negative.
    result = _surprise(0.0, 2, observed_error_type="conceptual_slip")
    assert result.surprise_direction == "negative"
    assert result.predicted_error_type_dist.get("conceptual_slip", 0.0) == 0.0


def test_fsrs_interval_factor_within_bounds():
    config = LearnLoopConfig()
    result = _surprise(3.0, 1)
    assert config.scheduler.surprise.f_min <= result.fsrs_interval_factor <= config.scheduler.surprise.f_max
