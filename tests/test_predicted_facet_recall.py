"""The facet-level prediction blend that powers goal attainment reporting."""

from __future__ import annotations

import math

import pytest

from learnloop.services.selection_rewards import predicted_facet_recall

BLEND = 4.0


def _sigmoid(value: float) -> float:
    return 1.0 / (1.0 + math.exp(-value))


def test_informed_mastery_dominates_at_low_mass():
    # 6 attempts of mastery evidence vs 0.2 facet mass: the backbone leads.
    prediction = predicted_facet_recall(2.5, 6, 0.5, 0.2, BLEND)
    assert prediction > 0.85
    assert prediction < _sigmoid(2.5)  # still pulled slightly toward the facet


def test_facet_mass_saturation_pulls_toward_facet_mean():
    low_mass = predicted_facet_recall(2.5, 6, 0.4, 0.5, BLEND)
    high_mass = predicted_facet_recall(2.5, 6, 0.4, 40.0, BLEND)
    assert high_mass < low_mass
    assert high_mass == pytest.approx(0.4, abs=0.06)


def test_thin_mastery_evidence_cannot_suppress_strong_facet_evidence():
    # One-attempt EKF at logit 0 vs facet mean 0.95 with mass 2.0: the prior
    # pseudo-count is capped at the mastery evidence count, so the facet leads.
    prediction = predicted_facet_recall(0.0, 1, 0.95, 2.0, BLEND)
    assert prediction >= 0.8


def test_zero_evidence_mastery_row_is_uninformative():
    assert predicted_facet_recall(0.0, 0, 0.9, 1.0, BLEND) == pytest.approx(0.9)
    # No facet evidence either: fall back to the (evidence-free) mastery mean.
    assert predicted_facet_recall(0.0, 0, None, 0.0, BLEND) == pytest.approx(0.5)


def test_absent_mastery_falls_back_to_facet_then_half():
    assert predicted_facet_recall(None, 0, 0.7, 1.0, BLEND) == pytest.approx(0.7)
    assert predicted_facet_recall(None, 0, None, 0.0, BLEND) == 0.5
    # Facet mean with zero mass is pure prior — ignore it.
    assert predicted_facet_recall(None, 0, 0.5, 0.0, BLEND) == 0.5


def test_monotone_in_facet_mass_when_facet_beats_mastery():
    predictions = [
        predicted_facet_recall(0.0, 8, 0.9, mass, BLEND) for mass in (0.0, 0.5, 1.0, 2.0, 4.0)
    ]
    assert predictions == sorted(predictions)
    assert predictions[0] == pytest.approx(0.5)


def test_result_is_clamped():
    assert 0.0 <= predicted_facet_recall(-10.0, 20, 0.0, 50.0, BLEND) <= 1.0
    assert 0.0 <= predicted_facet_recall(10.0, 20, 1.0, 50.0, BLEND) <= 1.0
