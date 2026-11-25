"""Surprise scored against adaptive difficulty's forecast from the fix round's tag (mvp-0.73): the forecast's own
probability, shifted by a primed answer's offset and clipped once by the configured clip, with no inverse through
``b`` (none exists at a = 0) and no second clamp; without mastery's IRT link, centred on the forecast's logit; and every
row names its source. Below the tag the label retirement's scoring is kept exactly."""

from __future__ import annotations

from datetime import UTC, datetime
from math import exp, log

import pytest

from learnloop.adaptive_difficulty.surprise_forecast import GRADE_RECEIPT, SurpriseForecast
from learnloop.attempts.surprise import compute_surprise
from learnloop.config import LearnLoopConfig
from learnloop.db.repositories import MasteryState
from learnloop.learner.mastery import MasteryObservation, update_mastery

NOW = datetime(2026, 5, 19, 12, 0, tzinfo=UTC)
FORECAST = SurpriseForecast(0.9, GRADE_RECEIPT, "key", "ad_threshold@grade")


def _score(*, direct: bool, item_a: float = 1.0, priming: float = 0.0, irt: bool = True, forecast=FORECAST,
           score: int = 4):
    config = LearnLoopConfig()
    config.mastery.irt.enabled = irt
    config.mastery.irt.discrimination_default = item_a
    prior = MasteryState("lo", 0.0, 1.0, 0, None, "mvp-0.73", "2026-05-19T12:00:00Z")
    observation = MasteryObservation(rubric_score=score, max_points=4, evidence_coverage=1.0, hint_dampening=1.0,
                                     grader_confidence=1.0, attempt_type="independent_attempt", observed_at=NOW)
    posterior = update_mastery(prior, observation, config.mastery, "mvp-0.73", item_a=item_a, item_b=-priming)
    return compute_surprise(prior=prior, posterior=posterior, observation=observation, observed_error_type=None,
                            prior_active_errors=[], config=config, item_a=item_a, item_b=-priming, forecast=forecast,
                            priming_offset=priming, record_source=True, direct=direct)


def test_a_primed_forecast_is_scored_at_its_shifted_probability_clipped_once():
    expected = 1.0 / (1.0 + exp(-(log(0.9 / 0.1) + 2.0)))
    assert expected == pytest.approx(0.9852, abs=1e-4)
    assert _score(direct=True, priming=2.0).predicted_score_dist["p_scored"] == pytest.approx(expected)
    # Below the tag the second clamp held it at 0.98.
    assert _score(direct=False, priming=2.0).predicted_score_dist["p_scored"] == pytest.approx(0.98)


def test_a_zero_discrimination_scores_the_forecast_and_records_no_implied_b():
    dist = _score(direct=True, item_a=0.0).predicted_score_dist
    assert dist["p_scored"] == pytest.approx(0.9) and "b_scored" not in dist
    with pytest.raises(ZeroDivisionError):
        _score(direct=False, item_a=0.0)


def test_without_the_irt_link_surprise_is_centred_on_the_forecast_and_names_its_source():
    on = _score(direct=True, irt=False, score=0)
    assert on.predicted_score_dist["prediction_source"] == GRADE_RECEIPT
    assert on.predicted_score_dist["p_scored"] == pytest.approx(0.9)
    off = _score(direct=False, irt=False, score=0)
    assert "prediction_source" not in off.predicted_score_dist
    # A miss against a 0.9 forecast is more surprising than against mastery's 0.5.
    assert on.predictive_surprise > off.predictive_surprise
    assert _score(direct=True, irt=False, forecast=None).predicted_score_dist["prediction_source"] == "mastery"
