"""Daily-loop DL1 §6.4 (Q12): the learner's own durations, an authored estimate as the prior.

est_minutes = answer_minutes + feedback_minutes, with answer_minutes the item's
own (winsorized) latencies shrunk toward g, g the practice-mode median shrunk
toward the prior (``expected_minutes``, else 3.0), k = 3 pseudo-observations.
"""

from __future__ import annotations

from statistics import median

import pytest

from learnloop.daily_plan.estimates import (
    DEFAULT_FEEDBACK_MINUTES,
    FALLBACK_PRIOR_MINUTES,
    FEEDBACK_CAP_MINUTES,
    DurationEvidence,
    Estimator,
    answer_minutes,
    feedback_minutes,
    load_duration_evidence,
    mode_prior,
    reading_minutes,
    winsorize_minutes,
)
from learnloop.db.repositories import Repository
from learnloop.vault.hashes import practice_item_hash
from learnloop.vault.loader import load_vault
from learnloop.vault.models import PracticeItem
from tests.helpers import create_daily_plan_vault


def test_no_history_falls_back_to_the_prior_then_three_minutes():
    estimator = Estimator(DurationEvidence())
    authored = estimator.estimate("pi_a", "short_answer", 2.0)
    assert authored.answer_minutes == pytest.approx(2.0)
    assert authored.prior_source == "expected_minutes"
    assert authored.minutes == pytest.approx(2.0 + DEFAULT_FEEDBACK_MINUTES)
    fallback = estimator.estimate("pi_b", "short_answer", None)
    assert fallback.answer_minutes == pytest.approx(FALLBACK_PRIOR_MINUTES)
    assert fallback.prior_source == "fallback"


def test_shrinkage_moves_from_the_prior_toward_own_latencies():
    # g = (n_mode * median_mode + k * prior) / (n_mode + k)
    mode = (1.0, 2.0, 4.0)
    g = mode_prior(mode, 3.0)
    assert g == pytest.approx((3 * median(mode) + 3 * 3.0) / 6)
    own = (10.0,)
    assert answer_minutes(own, g) == pytest.approx((10.0 + 3 * g) / 4)
    # More own observations weigh more.
    many = (10.0,) * 30
    assert answer_minutes(many, g) == pytest.approx((300.0 + 3 * g) / 33)
    assert answer_minutes(many, g) > answer_minutes(own, g)
    evidence = DurationEvidence(latencies_by_item={"pi_a": own}, latencies_by_mode={"short_answer": mode})
    estimate = Estimator(evidence).estimate("pi_a", "short_answer", 3.0)
    assert estimate.n_item == 1 and estimate.n_mode == 3
    assert estimate.answer_minutes == pytest.approx(answer_minutes(own, g))


def test_latencies_are_winsorized_at_the_cap():
    assert winsorize_minutes(60 * 60, 15.0) == 15.0
    assert winsorize_minutes(90, 15.0) == pytest.approx(1.5)
    assert winsorize_minutes(-5, 15.0) == 0.0


def test_feedback_dwell_needs_ten_observations_and_is_capped():
    assert feedback_minutes([4.0] * 9) == DEFAULT_FEEDBACK_MINUTES
    assert feedback_minutes([1.0] * 10) == pytest.approx(1.0)
    assert feedback_minutes([9.0] * 12) == FEEDBACK_CAP_MINUTES


def test_reading_estimate_is_words_left_over_the_pace():
    assert reading_minutes(1200, 120) == pytest.approx(10.0)
    assert reading_minutes(0, 120) == 0.0
    assert Estimator(DurationEvidence(), read_words_per_minute=200).reading_minutes(1000) == pytest.approx(5.0)


def test_loaded_evidence_reads_own_and_mode_latencies(tmp_path):
    paths = create_daily_plan_vault(tmp_path / "vault", learning_objects={"lo_x": [("pi_x1", 2.0)]})
    repository = Repository(paths.sqlite_path)
    with repository.connection() as connection:
        for index, (item, seconds) in enumerate([("pi_x1", 120), ("pi_x1", 3600), ("pi_diag_mid", 60)]):
            connection.execute(
                "INSERT INTO practice_attempts(id, practice_item_id, learning_object_id, practice_mode, "
                "attempt_type, latency_seconds, created_at) VALUES (?, ?, ?, 'short_answer', 'independent_attempt', ?, ?)",
                (f"att_{index}", item, "lo_x", seconds, f"2026-05-1{index}T10:00:00Z"),
            )
        connection.commit()
    evidence = load_duration_evidence(repository, latency_cap_minutes=15.0)
    assert evidence.latencies_by_item["pi_x1"] == (2.0, 15.0)  # the hour is winsorized
    assert sorted(evidence.latencies_by_mode["short_answer"]) == [1.0, 2.0, 15.0]


def test_expected_minutes_is_optional_omitted_when_null_and_outside_the_hash():
    base = {
        "id": "pi", "learning_object_id": "lo", "practice_mode": "short_answer",
        "prompt": "p", "expected_answer": "a", "created_at": "x", "updated_at": "x",
    }
    plain = PracticeItem.model_validate(base)
    timed = PracticeItem.model_validate({**base, "expected_minutes": 4.0})
    assert "expected_minutes" not in plain.model_dump(mode="json")
    assert timed.model_dump(mode="json")["expected_minutes"] == 4.0
    # Not in the scheduling hash: a planning label never changes item identity.
    assert practice_item_hash(plain) == practice_item_hash(timed)


def test_vault_items_carry_expected_minutes_into_the_estimate(tmp_path):
    paths = create_daily_plan_vault(tmp_path / "vault", learning_objects={"lo_x": [("pi_x1", 6.0)]})
    vault = load_vault(paths.root)
    assert vault.practice_items["pi_x1"].expected_minutes == 6.0
    assert Estimator(DurationEvidence()).item_minutes(vault, "pi_x1") == pytest.approx(6.5)
    assert Estimator(DurationEvidence()).item_minutes(vault, "pi_diag_mid") == pytest.approx(3.5)
