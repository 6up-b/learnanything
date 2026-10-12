"""The six llm_probability arms in the unified harness (field §7.2, G11).

Store-free tests: arms read a prepared cache only, predict before any outcome,
recalibrate on their own past predictions, and can never be active.
"""
from __future__ import annotations

from math import log

import pytest

from learnloop.field.evaluation import evaluate
from learnloop.field.predictors import registered_predictors, validate_active_predictor
from learnloop.field.probability_arms import (
    CLIP, CachedProbabilityArm, all_arm_names, arm_name, fit_intercept, parse_arm_selection,
    position_key,
)
from learnloop.field.types import AttemptRow, ItemFeatures, SignalRow


def attempt(n, lo="lo", outcome=1.0, **kwargs):
    return AttemptRow(str(n), ItemFeatures(f"item{n}", lo, f"2026-01-{n:02}T00:00:00Z"), outcome, 1.0, **kwargs)


def cache_for(rows, p=0.7):
    """A prepared cache keyed exactly as the harness will look it up."""

    history, cache = [], {}
    for row in rows:
        cache[position_key(row.features, history)] = p(row) if callable(p) else p
        history.append((row.attempt_id, row.outcome))
    return cache


def arms_for(rows, p=0.7, **kwargs):
    cache = cache_for(rows, p)
    return [
        CachedProbabilityArm(variant="v2", judge="decider", probabilities=cache, model="fake/decider", **kwargs),
        CachedProbabilityArm(variant="v2", judge="decider", probabilities=cache, model="fake/decider",
                             recalibrated=True, **kwargs),
    ]


def test_selection_names_and_order():
    assert parse_arm_selection(["all"]) == (
        ("v1", "decider"), ("v2", "decider"), ("v3", "decider"), ("v1", "llm"), ("v2", "llm"), ("v3", "llm"))
    assert parse_arm_selection(["v3/llm", "v1"]) == (("v1", "decider"), ("v1", "llm"), ("v3", "llm"))
    assert parse_arm_selection(["llm,v2/decider"]) == (
        ("v2", "decider"), ("v1", "llm"), ("v2", "llm"), ("v3", "llm"))
    with pytest.raises(ValueError, match="Unknown probability arm"):
        parse_arm_selection(["v4"])
    with pytest.raises(ValueError, match="at least one"):
        parse_arm_selection([" "])
    assert len(all_arm_names()) == 12
    assert arm_name("v3", "llm", recalibrated=True) == "llm_probability/v3/llm+recal"


def test_arms_are_off_by_default_and_can_never_be_active():
    names = registered_predictors()
    assert not any(name.startswith("llm_probability/") for name in names)
    report = evaluate([attempt(1)], bootstrap_samples=2)
    assert not any(name.startswith("llm_probability/") for name in report["report1"]["arms"])
    for name in all_arm_names():
        with pytest.raises(ValueError, match="cannot be active"):
            validate_active_predictor(name)
    arm = arms_for([attempt(1)])[0]
    assert arm.calibrated_uncertainty is False


def test_position_key_is_outcome_free_and_tracks_the_observed_past():
    a, b = attempt(1, outcome=0.0), attempt(1, outcome=1.0)
    assert position_key(a.features, []) == position_key(b.features, [])
    assert position_key(a.features, [("x", 0.0)]) != position_key(a.features, [("x", 1.0)])
    with pytest.raises(TypeError):
        position_key(a, [])


def test_harness_replays_the_cache_with_zero_calls_and_no_store(monkeypatch):
    import socket
    import sqlite3

    rows = [attempt(1, outcome=0), attempt(2, outcome=0), attempt(3, outcome=1)]
    arms = arms_for(rows)
    monkeypatch.setattr(sqlite3, "connect", lambda *a, **k: pytest.fail("store access"))
    monkeypatch.setattr(socket, "socket", lambda *a, **k: pytest.fail("network access"))
    report = evaluate(rows, arms=["mastery_ekf", *arms], bootstrap_samples=20)
    raw = report["report1"]["arms"]["llm_probability/v2/decider"]
    recal = report["report1"]["arms"]["llm_probability/v2/decider+recal"]
    assert raw["model"] == recal["model"] == "fake/decider"
    assert raw["overall"]["n"] == recal["overall"]["n"] == 3
    expected = -(log(1 - .7) * 2 + log(.7)) / 3
    assert raw["overall"]["log_loss"]["mean"] == pytest.approx(expected)
    # Two observed failures pull the recalibrated third prediction down, so
    # its loss on the final success is worse, and it never saw that outcome.
    assert recal["overall"]["log_loss"]["mean"] != pytest.approx(expected)
    assert report["recommendation"]["candidates"] == []
    assert report["manifest"]["arm_models"]["llm_probability/v2/decider"] == "fake/decider"


def test_recalibration_uses_only_past_predictions():
    rows = [attempt(1, outcome=0), attempt(2, outcome=0), attempt(3, outcome=0)]
    raw, recal = arms_for(rows)
    seen = []
    for row in rows:
        seen.append((raw.predict(row.features), recal.predict(row.features)))
        raw.observe(row)
        recal.observe(row)
    assert seen[0] == (pytest.approx(.7), pytest.approx(.7))  # nothing past: no shift
    assert seen[1][1] < seen[1][0] and seen[2][1] < seen[1][1]
    assert recal.intercept == pytest.approx(fit_intercept([log(.7 / .3)] * 3, [0, 0, 0]))
    signal = SignalRow("s", "lo", "2026-01-04T00:00:00Z", "hint")
    before = recal.intercept
    recal.observe(signal)
    assert recal.intercept == before


def test_a_cache_from_a_different_past_fails_closed():
    rows = [attempt(1, outcome=0), attempt(2)]
    arms = arms_for(rows)
    regraded = [rows[0], AttemptRow("2", rows[1].features, 1.0, 1.0)]
    other_past = [attempt(1, outcome=1), rows[1]]
    with pytest.raises(KeyError, match="re-run preparation"):
        evaluate(other_past, arms=arms, bootstrap_samples=2)
    assert evaluate(regraded, arms=arms_for(rows), bootstrap_samples=2)["counts"]["scored_attempts"] == 2


def test_probabilities_are_clipped_and_validated():
    rows = [attempt(1)]
    arm = CachedProbabilityArm(variant="v1", judge="llm", probabilities=cache_for(rows, 1.0), model="m")
    assert arm.predict(rows[0].features) == CLIP[1]
    arm = CachedProbabilityArm(variant="v1", judge="llm", probabilities=cache_for(rows, 0.0), model="m")
    assert arm.predict(rows[0].features) == CLIP[0]
    with pytest.raises(ValueError, match="not in"):
        CachedProbabilityArm(variant="v1", judge="llm", probabilities={"k": 1.5}, model="m")


def test_intercept_fit_is_penalized_and_finite():
    assert fit_intercept([], []) == 0.0
    assert fit_intercept([0.0] * 10, [0.5] * 10) == pytest.approx(0.0)
    up = fit_intercept([0.0] * 10, [1.0] * 10)
    assert 0 < up < 10  # the N(0, 1) prior keeps an all-success past finite
    assert fit_intercept([0.0] * 10, [0.0] * 10) == pytest.approx(-up)


def test_pairwise_comparisons_report_without_recommending():
    rows = [attempt(n, outcome=n % 2) for n in range(1, 9)]
    good = CachedProbabilityArm(
        variant="v3", judge="llm", model="m",
        probabilities=cache_for(rows, lambda row: 0.9 if row.outcome else 0.1))
    weak = CachedProbabilityArm(variant="v2", judge="llm", probabilities=cache_for(rows, 0.5), model="m")
    report = evaluate(rows, arms=[weak, good], bootstrap_samples=50,
                      pairwise=[(weak.name, good.name)])
    pair = report["report1"]["pairwise"]["llm_probability/v3/llm vs llm_probability/v2/llm"]
    assert pair["log_loss_improvement"]["mean"] > 0
    assert pair["clears_margin"]["overall"] is True
    assert report["recommendation"]["decision"] == "keep_incumbent"
    fresh = CachedProbabilityArm(variant="v2", judge="llm", probabilities=cache_for(rows, 0.5), model="m")
    with pytest.raises(ValueError, match="unselected arm"):
        evaluate(rows, arms=[fresh], bootstrap_samples=2, pairwise=[(fresh.name, good.name)])
