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


def _score_irt_off_at(tag: str, *, p: float, priming: float = 0.0, p_clip: float = 0.10):
    config = LearnLoopConfig()
    config.algorithms.algorithm_version = tag
    config.mastery.irt.enabled = False
    config.mastery.irt.p_clip = p_clip
    prior = MasteryState("lo", 0.0, 1.0, 0, None, tag, "2026-05-19T12:00:00Z")
    observation = MasteryObservation(rubric_score=0, max_points=4, evidence_coverage=1.0, hint_dampening=1.0,
                                     grader_confidence=1.0, attempt_type="independent_attempt", observed_at=NOW)
    posterior = update_mastery(prior, observation, config.mastery, tag, item_a=1.0, item_b=-priming)
    return compute_surprise(prior=prior, posterior=posterior, observation=observation, observed_error_type=None,
                            prior_active_errors=[], config=config, item_a=1.0, item_b=-priming,
                            forecast=SurpriseForecast(p, GRADE_RECEIPT, "key", "ad_threshold@grade"),
                            priming_offset=priming, record_source=True, direct=True)


@pytest.mark.parametrize("priming", [0.0, 2.0])
def test_without_the_irt_link_the_configured_clip_holds_after_the_priming_shift_from_the_tag(priming):
    """FR3-16: an interior forecast outside the configured clip (p = 0.95, or 0.9 shifted up by a priming offset, with
    p_clip = 0.10) is scored at the clip's bound 0.90 from mvp-0.76, the residual centred on that same probability;
    below the tag mvp-0.75's unclipped centre is kept exactly."""

    p = 0.95 if priming == 0.0 else 0.9
    at = _score_irt_off_at("mvp-0.76", p=p, priming=priming)
    assert at.predicted_score_dist["p_scored"] == pytest.approx(0.90)
    unclipped_centre = log(p / (1.0 - p)) + priming
    below = _score_irt_off_at("mvp-0.75", p=p, priming=priming)
    assert below.predicted_score_dist["p_scored"] == pytest.approx(1.0 / (1.0 + exp(-unclipped_centre)))
    # The residual is centred on the scored probability's logit: a miss against 0.90 is less surprising than against
    # the unclipped forecast.
    assert at.predictive_surprise < below.predictive_surprise
    sigma = at.predicted_score_dist["sigma_z"]
    z_obs = log(0.02 / 0.98)
    assert at.predictive_surprise == pytest.approx(
        0.5 * (((z_obs - log(0.9 / 0.1)) / sigma) ** 2 + log(2 * 3.141592653589793 * sigma**2)))


@pytest.mark.parametrize("p", [0.99, 0.005])
def test_without_the_irt_link_a_clip_below_two_percent_is_the_only_clip(p):
    """Review round 4, R4-S6 (a same-day correction inside mvp-0.76): with the default clip (1e-4) a forecast of 0.99,
    or 0.005, is inside the configured interval and is scored as it is, the residual centred on its exact logit. Failed
    before: mastery's logit, which holds any value to [0.02, 0.98], scored it at 0.98 (0.02)."""

    at = _score_irt_off_at("mvp-0.76", p=p, p_clip=1e-4)
    assert at.predicted_score_dist["p_scored"] == pytest.approx(p)
    sigma = at.predicted_score_dist["sigma_z"]
    z_obs = log(0.02 / 0.98)
    assert at.predictive_surprise == pytest.approx(
        0.5 * (((z_obs - log(p / (1.0 - p))) / sigma) ** 2 + log(2 * 3.141592653589793 * sigma**2)))
    # A forecast beyond the configured clip is scored at it, on both tails.
    edge = _score_irt_off_at("mvp-0.76", p=1.0 if p > 0.5 else 0.0, p_clip=1e-4)
    assert edge.predicted_score_dist["p_scored"] == pytest.approx(1.0 - 1e-4 if p > 0.5 else 1e-4)
