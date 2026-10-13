"""Offline answer-signal arms in the learner field's predictor duel (owner 2026-10-13).

(a) confidence alone, (b) an existing arm plus confidence, (c) the grader's
reading of the learner's hedging. Offline only: scored in the prequential
replay, never active, never imported by serving. Synthetic rows and a fresh
test vault; no model calls.
"""

from __future__ import annotations

from dataclasses import replace
from math import log
from pathlib import Path

import numpy as np
import pytest

from learnloop.field.answer_signals import (
    ARM_NAMES, AnswerSignalArm, default_pairs, fit_logistic, signal_feature, stacked_arm,
)
from learnloop.field.evaluation import brier_decomposition, evaluate, write_reports
from learnloop.field.predictors import create_predictor, registered_predictors, validate_active_predictor
from learnloop.field.types import ANSWER_CONFIDENCE_PROBABILITY, AnswerSignals, AttemptRow, ItemFeatures


def row(n, outcome=1.0, *, confidence=None, hedged=None, lo="lo", mass=1.0):
    signals = AnswerSignals(
        confidence=confidence,
        hedged_share=hedged,
        hedging_read=0 if hedged is None else 2,
    )
    return AttemptRow(
        f"a{n:03}", ItemFeatures(f"item{n}", lo, f"2026-01-01T00:{n // 60:02}:{n % 60:02}Z"),
        outcome, mass, answer_signals=signals,
    )


# -- the signals and the fit ---------------------------------------------------------


def test_signal_features_follow_the_duel_mapping_and_abstain_when_absent():
    assert signal_feature("confidence", AnswerSignals(confidence=5)) == pytest.approx(log(0.9 / 0.1))
    assert signal_feature("confidence", AnswerSignals(confidence=3)) == pytest.approx(0.0)
    assert signal_feature("confidence", AnswerSignals()) is None
    assert signal_feature("confidence", None) is None
    assert signal_feature("hedging", AnswerSignals(hedged_share=1.0, hedging_read=1)) == 1.0
    assert signal_feature("hedging", AnswerSignals(confidence=4)) is None
    with pytest.raises(ValueError):
        AnswerSignals(confidence=6)
    with pytest.raises(ValueError):
        AnswerSignals(hedged_share=1.5)


def test_confidence_alone_starts_at_the_duels_mapping():
    arm = create_predictor("answer_confidence")
    features = ItemFeatures("i", "lo", "2026-01-01T00:00:00Z")
    for level, probability in ANSWER_CONFIDENCE_PROBABILITY.items():
        assert arm.predict_answer(features, AnswerSignals(confidence=level)) == pytest.approx(probability)
    # Hedging alone starts neutral; a stack starts exactly at its base.
    hedging = create_predictor("answer_hedging")
    assert hedging.predict_answer(features, AnswerSignals(hedged_share=1.0, hedging_read=1)) == pytest.approx(0.5)
    stack = create_predictor("mastery_ekf+answer_confidence")
    base = create_predictor("mastery_ekf")
    assert stack.predict_answer(features, AnswerSignals(confidence=5)) == pytest.approx(base.predict(features))


def test_the_map_fit_learns_an_overconfident_learner():
    # Taps of 5 that are right only half the time pull the slope down.
    rows = [row(i, outcome=float(i % 2), confidence=5) for i in range(40)]
    arm = AnswerSignalArm(signal="confidence")
    for r in rows:
        arm.observe(r)
    p = arm.predict_answer(rows[0].features, AnswerSignals(confidence=5))
    assert 0.4 < p < 0.7
    a, b = fit_logistic([], [], [], prior_mean=(0.0, 1.0))
    assert (a, b) == (0.0, 1.0)
    # A stack fits one parameter, the signal's slope: its intercept stays 0, so
    # a gain over its base is the signal's, never a recalibrated base.
    stack = stacked_arm("mastery_ekf", "confidence")
    for r in rows:
        stack.observe(r)
    assert stack.coefficients[0] == 0.0 and stack.coefficients[1] != 0.0


def _log_posterior(features, offsets, outcomes, a, b, prior_mean):
    from math import exp, log1p

    def log_sigmoid(z):
        return -log1p(exp(-z)) if z >= 0 else z - log1p(exp(z))

    total = -((a - prior_mean[0]) ** 2 + (b - prior_mean[1]) ** 2) / 2
    for x, offset, y in zip(features, offsets, outcomes):
        z = offset + a + b * x
        total += y * log_sigmoid(z) + (1 - y) * log_sigmoid(-z)
    return total


def test_the_fit_converges_where_an_undamped_newton_step_oscillates():
    """Review F5: ten failures tapped 5 on a base at logit 4. A full Newton step
    from the prior overshoots into a saturated region and back again; the fit
    must reach the MAP optimum (b ~ -2.713, p ~ 0.123), not return the prior."""

    x = log(0.9 / 0.1)
    features, offsets, outcomes = [x] * 10, [4.0] * 10, [0.0] * 10
    a, b = fit_logistic(features, offsets, outcomes, prior_mean=(0.0, 0.0), intercept=False)
    assert a == 0.0 and b == pytest.approx(-2.713, abs=1e-3)
    assert 1 / (1 + np.exp(-(4.0 + b * x))) == pytest.approx(0.1234, abs=1e-3)
    best = _log_posterior(features, offsets, outcomes, 0.0, b, (0.0, 0.0))
    for delta in (-1e-4, 1e-4):
        assert _log_posterior(features, offsets, outcomes, 0.0, b + delta, (0.0, 0.0)) < best
    # The two-parameter fit on a saturated offset reaches its optimum too.
    saturated = [9.0] * 10
    a2, b2 = fit_logistic(features, saturated, outcomes, prior_mean=(0.0, 0.0))
    best2 = _log_posterior(features, saturated, outcomes, a2, b2, (0.0, 0.0))
    for da, db in ((1e-4, 0), (-1e-4, 0), (0, 1e-4), (0, -1e-4)):
        assert _log_posterior(features, saturated, outcomes, a2 + da, b2 + db, (0.0, 0.0)) < best2


def test_a_fit_that_cannot_converge_says_so():
    import learnloop.field.answer_signals as signals

    with pytest.raises(ArithmeticError, match="did not converge"):
        signals.fit_logistic([1.0] * 5, [0.0] * 5, [1.0] * 5, prior_mean=(0.0, 0.0), max_steps=1)


def test_a_prediction_never_sees_its_own_outcome():
    rows = [row(i, outcome=float(i % 3 == 0), confidence=1 + i % 5, hedged=(i % 4) / 4) for i in range(12)]
    for name in ("answer_confidence", "answer_hedging", "mastery_ekf+answer_confidence"):
        flipped = [*rows[:-1], replace(rows[-1], outcome=1.0 - rows[-1].outcome)]
        first = evaluate(rows, arms=[name], bootstrap_samples=5)
        second = evaluate(flipped, arms=[name], bootstrap_samples=5)
        # Only the last outcome differs: every prediction (and so the n) agrees.
        assert first["report1"]["arms"][name]["overall"]["n"] == second["report1"]["arms"][name]["overall"]["n"]
        a = AnswerSignalArm(signal="confidence") if name == "answer_confidence" else create_predictor(name)
        b = AnswerSignalArm(signal="confidence") if name == "answer_confidence" else create_predictor(name)
        for r in rows[:-1]:
            a.observe(r)
            b.observe(r)
        assert a.predict_answer(rows[-1].features, rows[-1].answer_signals) == b.predict_answer(
            flipped[-1].features, flipped[-1].answer_signals)


# -- the harness ------------------------------------------------------------------------


def test_signal_arms_abstain_without_their_signal_and_pair_on_common_attempts():
    rows = [row(1, 1.0, confidence=5), row(2, 0.0), row(3, 1.0, confidence=4, hedged=0.0),
            row(4, 0.0, hedged=1.0), row(5, 1.0)]
    report = evaluate(rows, arms=["mastery_ekf", "answer_confidence", "answer_hedging",
                                  "mastery_ekf+answer_confidence"],
                      bootstrap_samples=20, pairwise=[("mastery_ekf", "mastery_ekf+answer_confidence")])
    arms = report["report1"]["arms"]
    assert arms["mastery_ekf"]["overall"]["n"] == 5
    assert arms["answer_confidence"]["overall"]["n"] == 2
    assert arms["answer_confidence"]["unscored_attempts"] == 3
    assert arms["answer_hedging"]["overall"]["n"] == 2
    assert arms["mastery_ekf+answer_confidence"]["overall"]["n"] == 2
    pair = report["report1"]["pairwise"]["mastery_ekf+answer_confidence vs mastery_ekf"]
    assert pair["log_loss_improvement"]["n"] == 2
    assert report["counts"]["answer_confidence_present"] == 2
    assert report["counts"]["answer_hedging_read"] == 2
    assert report["counts"]["answer_confidence_share"] == pytest.approx(2 / 5)
    splits = arms["mastery_ekf"]["splits"]["answer_confidence"]
    assert (splits["present"]["n"], splits["absent"]["n"]) == (2, 3)
    assert arms["answer_confidence"]["answer_signal"]["offline_only"] is True
    assert "same call" in arms["answer_hedging"]["answer_signal"]["source"]
    assert any("offline only" in text for text in report["report1"]["limitations"])
    # Never a recommendation, whatever it scores.
    assert not any(name.startswith("answer_") or "+answer_" in name
                   for name in report["recommendation"]["candidates"])


def test_the_stack_keeps_its_base_exactly_on_every_row():
    rows = [row(i, outcome=float(i % 2), confidence=(5 if i % 3 else None)) for i in range(18)]
    stack = stacked_arm("lo_general", "confidence")
    base = create_predictor("lo_general")
    for r in rows:
        stack.observe(r)
        base.observe(r)
    assert stack.base.snapshot_bytes() == base.snapshot_bytes()


def test_brier_split_is_exact_and_separates_reliability_from_resolution():
    rng = np.random.default_rng(0)
    p = rng.choice([0.1, 0.3, 0.5, 0.7, 0.9], size=200)
    y = (rng.random(200) < p).astype(float)
    split = brier_decomposition(y, p)
    assert split["brier"] == pytest.approx(np.mean((p - y) ** 2))
    assert split["brier"] == pytest.approx(
        split["reliability"] - split["resolution"] + split["uncertainty"] + split["within_bin"])
    assert split["within_bin"] == pytest.approx(0.0, abs=1e-12)  # one forecast per bin
    # A constant forecast at the base rate: no resolution, no miscalibration.
    flat = brier_decomposition(y, np.full(200, y.mean()))
    assert flat["resolution"] == pytest.approx(0.0, abs=1e-12)
    assert flat["reliability"] == pytest.approx(0.0, abs=1e-12)
    assert brier_decomposition([], [])["brier"] is None


def test_every_arm_reports_the_split_and_the_markdown_shows_it(tmp_path):
    rows = [row(i, outcome=float(i % 2), confidence=1 + i % 5) for i in range(10)]
    report = evaluate(rows, arms=["mastery_ekf", "answer_confidence"], bootstrap_samples=5)
    for values in report["report1"]["arms"].values():
        assert set(values["overall"]["brier_decomposition"]) >= {"reliability", "resolution", "uncertainty"}
    files = write_reports(report, tmp_path)
    text = Path(files["markdown"]).read_text(encoding="utf-8")
    assert "| Reliability | Resolution |" in text
    assert "pre-answer confidence present on 10" in text


# -- offline only -------------------------------------------------------------------------


def test_signal_arms_are_registered_offline_and_can_never_be_active():
    names = registered_predictors()
    for name in (*ARM_NAMES.values(), *(challenger for _, challenger in default_pairs())):
        assert name in names
        with pytest.raises(ValueError, match="calibrated uncertainty"):
            validate_active_predictor(name)
    with pytest.raises(TypeError, match="outcome-free"):
        create_predictor("answer_confidence").predict(row(1))


def test_no_serving_module_imports_the_signal_arms():
    root = Path(__file__).resolve().parents[1] / "src" / "learnloop"
    allowed = {root / "field" / "answer_signals.py", root / "field" / "evaluation.py",
               root / "cli" / "field.py"}
    offenders = [
        str(path.relative_to(root))
        for path in root.rglob("*.py")
        if path not in allowed and "answer_signals" in path.read_text(encoding="utf-8")
        and "field.answer_signals" in path.read_text(encoding="utf-8")
    ]
    assert offenders == []


# -- the vault loader ----------------------------------------------------------------------


def test_the_loader_reads_the_tap_and_the_graders_tone_reading(tmp_path):
    from contextlib import closing

    from learnloop.attempts.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
    from learnloop.clock import FrozenClock
    from learnloop.db.connection import connect
    from learnloop.field.outcomes import data_check, load_attempt_rows
    from learnloop.vault.loader import load_vault
    from tests.helpers import NOW, create_basic_vault

    paths = create_basic_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    from learnloop.db.repositories import Repository

    repository = Repository(paths.sqlite_path)
    first = complete_self_graded_attempt(
        vault, repository,
        AttemptDraft(practice_item_id="pi_svd_define_001", learner_answer_md="U Sigma V transpose, I think.",
                     attempt_type="independent_attempt", answer_confidence=2),
        SelfGradeInput(criterion_points={"correctness": 4}, confidence=2),
        clock=FrozenClock(NOW),
    )
    with repository.connection() as connection:
        connection.execute(
            "UPDATE grading_evidence SET learner_confidence = 'hedged' WHERE attempt_id = ?",
            (first.attempt_id,),
        )
        connection.commit()
    with closing(connect(paths.sqlite_path)) as connection:
        rows = load_attempt_rows(connection, vault, legacy_fallback="current_content")
        counts = data_check(connection, vault, legacy_fallback="current_content")["answer_signals"]
    signals = {r.attempt_id: r.answer_signals for r in rows}[first.attempt_id]
    assert signals.confidence == 2
    assert signals.hedged_share == 1.0 and signals.hedging_read >= 1
    assert counts["confidence_present"] >= 1 and counts["confidence_levels"]["2"] >= 1


def test_a_control_twin_separates_the_signal_from_recalibration():
    """A tap that never varies carries nothing beyond recalibrating the base:
    the stack and its control (same rows, constant covariate) score alike, while
    both may beat a miscalibrated base."""

    rows = [row(i, outcome=float(i % 5 != 0), confidence=5) for i in range(40)]
    stack, control = "mastery_ekf+answer_confidence", "mastery_ekf+answer_confidence:control"
    report = evaluate(rows, arms=["mastery_ekf", stack, control], bootstrap_samples=10,
                      pairwise=[("mastery_ekf", stack), (control, stack)])
    signal_only = report["report1"]["pairwise"][f"{stack} vs {control}"]["log_loss_improvement"]
    # No gain beyond recalibration (the two differ only in prior scale).
    assert signal_only["n"] == 40 and signal_only["mean"] < 0.01
    assert ("mastery_ekf+answer_confidence:control", stack) in default_pairs()
    with pytest.raises(ValueError, match="calibrated uncertainty"):
        validate_active_predictor(control)
