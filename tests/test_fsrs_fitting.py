"""Pure-Python FSRS fitter: recoverability on synthetic data, shrinkage at
small N, guards, determinism, and bounds/ordering projection."""

from __future__ import annotations

import random
from datetime import UTC, datetime, timedelta

import pytest

from learnloop.config import FsrsFittingConfig
from learnloop.scheduling.fsrs import FSRS6_DEFAULT_WEIGHTS, Rating, apply_review, forgetting_curve
from learnloop.scheduling.fsrs_fitting import (
    FIT_BOUNDS,
    FIT_INDICES,
    FsrsFittingError,
    fit_fsrs_weights,
    review_log_loss,
)
from learnloop.scheduling.review_log import ReviewLog, ReviewObservation

EPOCH = datetime(2026, 1, 1, tzinfo=UTC)


def _synthetic_log(true_weights: tuple[float, ...], *, items: int, reviews_per_item: int, seed: int) -> ReviewLog:
    rng = random.Random(seed)
    sequences: dict[str, list[ReviewObservation]] = {}
    total = 0
    for item_index in range(items):
        item_id = f"pi_{item_index:04d}"
        state = None
        observed_at = EPOCH + timedelta(hours=item_index)
        sequence: list[ReviewObservation] = []
        for review_index in range(reviews_per_item):
            if state is None:
                rating = Rating.GOOD
                elapsed = 0.0
            else:
                elapsed = rng.uniform(0.6, 12.0)
                recall_p = forgetting_curve(state.stability, elapsed, true_weights)
                rating = Rating.GOOD if rng.random() < recall_p else Rating.AGAIN
            observed_at = observed_at + timedelta(days=elapsed)
            sequence.append(
                ReviewObservation(
                    practice_item_id=item_id,
                    attempt_id=f"a_{item_index}_{review_index}",
                    rating=rating,
                    elapsed_days=elapsed,
                    weight=1.0,
                    observed_at=observed_at,
                    first_review=review_index == 0,
                )
            )
            state = apply_review(state, rating, elapsed, true_weights)
            total += 1
        sequences[item_id] = sequence
    return ReviewLog(sequences=sequences, total_reviews=total, data_through=None, skipped_attempts=0)


def test_recoverability_beats_defaults_on_perturbed_weights():
    # Ground truth: much faster decay + weaker initial stabilities than default.
    true_weights = list(FSRS6_DEFAULT_WEIGHTS)
    true_weights[20] = 0.4
    for index in (0, 1, 2, 3):
        true_weights[index] = FSRS6_DEFAULT_WEIGHTS[index] * 0.5
    true_weights = tuple(true_weights)

    log = _synthetic_log(true_weights, items=120, reviews_per_item=8, seed=7)
    config = FsrsFittingConfig(min_reviews=50, l2_lambda=0.01, max_iterations=60)
    result = fit_fsrs_weights(log, config=config)

    assert result.log_loss_fitted <= result.log_loss_default
    # And both must beat neither-true-nor-default nonsense: the truth scores
    # better than defaults on this data, so the fit should close the gap.
    truth_loss, _ = review_log_loss(log, true_weights, min_elapsed_days=config.min_elapsed_days)
    assert truth_loss < result.log_loss_default
    # Decay moved toward the truth (0.4) from the default (0.1542).
    assert result.weights[20] > FSRS6_DEFAULT_WEIGHTS[20]


def test_shrinkage_dominates_at_tiny_n():
    true_weights = list(FSRS6_DEFAULT_WEIGHTS)
    true_weights[20] = 0.5
    log = _synthetic_log(tuple(true_weights), items=10, reviews_per_item=7, seed=3)
    config = FsrsFittingConfig(min_reviews=20, l2_lambda=50.0, max_iterations=40)
    result = fit_fsrs_weights(log, config=config)
    for index in FIT_INDICES:
        assert result.weights[index] == pytest.approx(FSRS6_DEFAULT_WEIGHTS[index], rel=0.25), index


def test_refuses_below_min_reviews():
    log = _synthetic_log(FSRS6_DEFAULT_WEIGHTS, items=3, reviews_per_item=4, seed=1)
    with pytest.raises(FsrsFittingError, match="at least 50"):
        fit_fsrs_weights(log, config=FsrsFittingConfig())


def test_deterministic():
    log = _synthetic_log(FSRS6_DEFAULT_WEIGHTS, items=30, reviews_per_item=6, seed=11)
    config = FsrsFittingConfig(min_reviews=50, max_iterations=25)
    first = fit_fsrs_weights(log, config=config)
    second = fit_fsrs_weights(log, config=config)
    assert first.weights == second.weights
    assert first.log_loss_fitted == second.log_loss_fitted
    assert first.iterations == second.iterations


def test_bounds_and_ordering_projection():
    log = _synthetic_log(FSRS6_DEFAULT_WEIGHTS, items=40, reviews_per_item=6, seed=5)
    config = FsrsFittingConfig(min_reviews=50, l2_lambda=0.0, max_iterations=50)
    result = fit_fsrs_weights(log, config=config)
    for index, (low, high) in FIT_BOUNDS.items():
        assert low <= result.weights[index] <= high, index
    assert result.weights[0] <= result.weights[1] <= result.weights[2] <= result.weights[3]
    # Pinned indices untouched.
    for index in range(21):
        if index not in FIT_INDICES:
            assert result.weights[index] == FSRS6_DEFAULT_WEIGHTS[index]


def test_review_log_loss_skips_short_gaps_and_zero_weight():
    observations = [
        ReviewObservation("pi", "a1", Rating.GOOD, 0.0, 1.0, EPOCH, True),
        ReviewObservation("pi", "a2", Rating.GOOD, 0.1, 1.0, EPOCH, False),  # short gap: no loss term
        ReviewObservation("pi", "a3", Rating.AGAIN, 3.0, 0.0, EPOCH, False),  # zero weight: no loss term
        ReviewObservation("pi", "a4", Rating.GOOD, 2.0, 1.0, EPOCH, False),
    ]
    log = ReviewLog(sequences={"pi": observations}, total_reviews=4, data_through=None, skipped_attempts=0)
    loss, n = review_log_loss(log, FSRS6_DEFAULT_WEIGHTS, min_elapsed_days=0.5)
    assert n == 1
    assert loss > 0.0
