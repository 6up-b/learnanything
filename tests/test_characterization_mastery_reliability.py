"""Characterization tests (P0.0, spec_p0_measurement_correctness.md §2): pin current behavior;
these tests document reality, not desired behavior. When P0.x intentionally changes behavior,
update these tests in the same commit and note the change.

Target: the ALREADY-CORRECT mastery reliability path exercised by
``learnloop.services.attempts._apply_attempt`` (see ``resolve_reliability`` ->
``resolve_error_impact`` -> ``MasteryObservation.observation_weight_override`` ->
``update_mastery_traced``). The P0 spec requires characterizing this working path so the
refactor preserves it.

What this pins:
  * ``resolve_reliability`` resolves observation reliability as the product
    ``clamp(grader_confidence) * hint_dampening_product * attempt_evidence_mass`` for
    representative inputs.
  * That resolved reliability flows into the mastery update: with error_type=None,
    ``resolve_error_impact`` turns reliability into the observation weight, which gates the
    EKF measurement noise so higher reliability produces a strictly larger mastery mu step.
    Direction plus exact constructed values are pinned.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from learnloop.config import LearnLoopConfig, MasteryConfig
from learnloop.db.repositories import MasteryState
from learnloop.services.mastery import MasteryObservation, update_mastery_traced
from learnloop.services.recall_coverage import resolve_error_impact, resolve_reliability
from learnloop.vault.models import HintPolicy, PracticeItem, Rubric

NOW = datetime(2026, 5, 19, 12, 0, tzinfo=UTC)
VERSION = "mvp-0.1"


def _item(hint_dampening: dict | None = None) -> PracticeItem:
    hint_policy = HintPolicy(mastery_alpha_dampening_by_hint=hint_dampening or {})
    return PracticeItem(
        id="pi",
        learning_object_id="lo",
        practice_mode="short_answer",
        prompt="p",
        expected_answer="x",
        grading_rubric=Rubric(max_points=4, criteria=[], fatal_errors=[]),
        hint_policy=hint_policy,
        created_at="x",
        updated_at="x",
    )


# --- reliability resolution (where reliability currently comes from) ------------


def test_resolve_reliability_is_product_of_confidence_hint_and_attempt_mass():
    """observation_reliability = grader_confidence * hint_product * attempt_evidence_mass."""

    # Independent attempt, full grader confidence, no hints -> all factors 1.0.
    full = resolve_reliability(
        _item(), attempt_type="independent_attempt", hints_used=0, grader_confidence=1.0
    )
    assert full.observation_reliability == pytest.approx(1.0)
    assert full.trace["grader_confidence_factor"] == pytest.approx(1.0)
    assert full.trace["hint_mastery_factor"] == pytest.approx(1.0)
    assert full.trace["attempt_type_mastery_factor"] == pytest.approx(1.0)

    # Grader confidence alone scales reliability linearly.
    half_conf = resolve_reliability(
        _item(), attempt_type="independent_attempt", hints_used=0, grader_confidence=0.5
    )
    assert half_conf.observation_reliability == pytest.approx(0.5)

    # Attempt type carries its evidence mass: self_report=0.3, reconstruction=0.5.
    self_report = resolve_reliability(
        _item(), attempt_type="self_report", hints_used=0, grader_confidence=1.0
    )
    assert self_report.observation_reliability == pytest.approx(0.3)
    reconstruction = resolve_reliability(
        _item(),
        attempt_type="reconstruction_after_walkthrough",
        hints_used=0,
        grader_confidence=1.0,
    )
    assert reconstruction.observation_reliability == pytest.approx(0.5)


def test_resolve_reliability_applies_per_hint_dampening_product():
    """Each used hint multiplies reliability by its configured mastery dampening factor."""

    item = _item(hint_dampening={1: 0.8, 2: 0.5})
    one_hint = resolve_reliability(
        item, attempt_type="independent_attempt", hints_used=1, grader_confidence=1.0
    )
    assert one_hint.observation_reliability == pytest.approx(0.8)
    two_hints = resolve_reliability(
        item, attempt_type="independent_attempt", hints_used=2, grader_confidence=1.0
    )
    assert two_hints.observation_reliability == pytest.approx(0.8 * 0.5)


# --- reliability flows into the mastery update ---------------------------------


def _prior() -> MasteryState:
    # last_evidence_at=None -> days_since=0 -> P_pred == prior variance (1.0).
    return MasteryState("lo", 0.0, 1.0, 0, None, VERSION, "2026-05-19T12:00:00Z")


def _mastery_step_for_reliability(reliability: float) -> tuple[float, float]:
    """Run the attempts.py chain for a clean full-mark attempt at a given reliability.

    Mirrors ``_apply_attempt``: reliability -> resolve_error_impact (error_type=None,
    so observation_weight == effective_coverage * reliability * independent_evidence_discount)
    -> observation_weight_override -> update_mastery_traced. Returns (posterior_mean, mu_step).
    """

    impact = resolve_error_impact(
        LearnLoopConfig(),
        error_type=None,
        max_event_severity=0.0,
        effective_coverage=1.0,
        observation_reliability=reliability,
        independent_evidence_discount=1.0,
    )
    observation = MasteryObservation(
        rubric_score=4,
        max_points=4,
        evidence_coverage=1.0,
        hint_dampening=1.0,
        grader_confidence=1.0,
        attempt_type="independent_attempt",
        observed_at=NOW,
        observation_reliability=reliability,
        observation_weight_override=impact.observation_weight,
    )
    state, trace = update_mastery_traced(
        _prior(), observation, MasteryConfig(), VERSION, item_a=1.0, item_b=0.0
    )
    return state.logit_mean, trace.mu_step


def test_error_impact_turns_reliability_into_observation_weight():
    """With error_type=None the observation weight is exactly the reliability (coverage=1)."""

    impact = resolve_error_impact(
        LearnLoopConfig(),
        error_type=None,
        max_event_severity=0.0,
        effective_coverage=1.0,
        observation_reliability=0.3,
        independent_evidence_discount=1.0,
    )
    assert impact.error_sharpening == pytest.approx(1.0)
    assert impact.observation_weight == pytest.approx(0.3)


def test_higher_reliability_yields_larger_mastery_step():
    """Two identical full-mark attempts move mu more when reliability is higher.

    Same prior, same score, same item — only the resolved observation reliability differs.
    The exact mu steps are pinned; the ordering (strictly monotone in reliability) is the
    load-bearing behavior the refactor must preserve.
    """

    mean_high, step_high = _mastery_step_for_reliability(1.0)
    mean_mid, step_mid = _mastery_step_for_reliability(0.6)
    mean_low, step_low = _mastery_step_for_reliability(0.3)

    # Direction: reliability is monotone in the size of the belief move.
    assert step_high > step_mid > step_low > 0.0

    # Exact constructed values (prior mu=0, variance=1, a=1, b=0, full marks 4/4).
    assert step_high == pytest.approx(0.4)
    assert step_mid == pytest.approx(0.2608695652173913)
    assert step_low == pytest.approx(0.13953488372093023)
    assert mean_high == pytest.approx(0.4)
    assert mean_mid == pytest.approx(0.2608695652173913)
    assert mean_low == pytest.approx(0.13953488372093023)
