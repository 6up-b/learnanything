from __future__ import annotations

import pytest

from learnloop.services.fsrs import (
    FSRS6_DEFAULT_WEIGHTS,
    MemoryState,
    Rating,
    apply_review,
    forgetting_curve,
    initial_stability,
    interval_for_retention,
    rating_from_score,
)


def test_rating_from_score_buckets():
    assert rating_from_score(0, 4) is Rating.AGAIN
    assert rating_from_score(1, 4) is Rating.HARD
    assert rating_from_score(2, 4) is Rating.HARD
    assert rating_from_score(3, 4) is Rating.GOOD
    assert rating_from_score(4, 4) is Rating.EASY


def test_first_review_uses_initial_weights():
    state = apply_review(None, Rating.GOOD, 0.0)
    assert state.stability == pytest.approx(FSRS6_DEFAULT_WEIGHTS[2])
    assert state.retrievability == 1.0
    assert 1.0 <= state.difficulty <= 10.0
    assert initial_stability(Rating.EASY) == pytest.approx(FSRS6_DEFAULT_WEIGHTS[3])


def test_forgetting_curve_is_one_at_zero_and_decreases():
    assert forgetting_curve(2.0, 0.0) == pytest.approx(1.0)
    early = forgetting_curve(2.0, 1.0)
    late = forgetting_curve(2.0, 10.0)
    assert 0.0 < late < early < 1.0


def test_good_review_increases_stability_over_time():
    previous = MemoryState(difficulty=5.0, stability=2.0, retrievability=1.0)
    reviewed = apply_review(previous, Rating.GOOD, 5.0)
    assert reviewed.stability > previous.stability


def test_again_does_not_increase_stability_like_good():
    previous = MemoryState(difficulty=5.0, stability=4.0, retrievability=0.9)
    again = apply_review(previous, Rating.AGAIN, 5.0)
    good = apply_review(previous, Rating.GOOD, 5.0)
    assert again.stability < good.stability


def test_interval_grows_with_stability():
    short = interval_for_retention(1.0)
    long = interval_for_retention(10.0)
    assert long > short > 0.0
