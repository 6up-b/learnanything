from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from learnloop.config import MasteryConfig
from learnloop.db.repositories import MasteryState
from learnloop.services.mastery import (
    MasteryObservation,
    display_mastery,
    initial_mastery_state,
    sigmoid,
    update_mastery,
)

VERSION = "mvp-0.1"
NOW = datetime(2026, 5, 19, 12, 0, tzinfo=UTC)


def _prior(mean: float = 0.0, variance: float = 1.0, last_evidence_at: str | None = None) -> MasteryState:
    return MasteryState("lo", mean, variance, 0, last_evidence_at, VERSION, "2026-05-19T12:00:00Z")


def _obs(score: int, *, coverage=1.0, hint=1.0, grader=1.0, attempt_type="independent_attempt") -> MasteryObservation:
    return MasteryObservation(
        rubric_score=score,
        max_points=4,
        evidence_coverage=coverage,
        hint_dampening=hint,
        grader_confidence=grader,
        attempt_type=attempt_type,
        observed_at=NOW,
    )


def test_positive_score_raises_mean():
    posterior = update_mastery(_prior(), _obs(4), MasteryConfig(), VERSION)
    assert posterior.logit_mean > 0.0
    assert posterior.evidence_count == 1


def test_zero_score_does_not_raise_mean():
    posterior = update_mastery(_prior(), _obs(0, coverage=0.0), MasteryConfig(), VERSION)
    assert posterior.logit_mean <= 0.0


def test_low_confidence_moves_mean_less_than_high_confidence():
    high = update_mastery(_prior(), _obs(4, grader=1.0), MasteryConfig(), VERSION)
    low = update_mastery(_prior(), _obs(4, grader=0.2), MasteryConfig(), VERSION)
    assert high.logit_mean > low.logit_mean > 0.0


def test_hint_dampening_reduces_update():
    full = update_mastery(_prior(), _obs(4, hint=1.0), MasteryConfig(), VERSION)
    damped = update_mastery(_prior(), _obs(4, hint=0.5), MasteryConfig(), VERSION)
    assert full.logit_mean > damped.logit_mean


def test_drift_increases_movement_after_long_gap():
    recent = update_mastery(_prior(last_evidence_at="2026-05-19T12:00:00Z"), _obs(4), MasteryConfig(), VERSION)
    stale_prior = _prior(last_evidence_at=(NOW - timedelta(days=200)).isoformat().replace("+00:00", "Z"))
    stale = update_mastery(stale_prior, _obs(4), MasteryConfig(), VERSION)
    assert stale.logit_mean > recent.logit_mean


def test_display_mastery_formula():
    state = _prior(mean=0.0, variance=1.0)
    display = display_mastery(state)
    assert display.mastery_mean == pytest.approx(0.5)
    assert display.mastery_variance == pytest.approx((0.5 * 0.5) ** 2 * 1.0)
    assert sigmoid(0.0) == pytest.approx(0.5)
