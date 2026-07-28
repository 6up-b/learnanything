from __future__ import annotations

import pytest

from learnloop.services.mastery_step_attribution import WEIGHT_FLOOR, explain_mastery_step


def _payload(**overrides):
    """A debug payload shaped like the one attempts persist."""

    payload = {
        "observation_weight": 0.23086,
        "lo_relative_coverage": 0.35,
        "effective_coverage": 0.70,
        "predicted_correctness": 0.6091,
        "lo_relative_coverage_trace": {
            "required_facets": ["a", "b", "c", "d", "e", "f"],
            "per_facet_coverage": {"a": 0.7, "b": 0.7, "c": 0.7, "d": 0.0, "e": 0.0, "f": 0.0},
        },
        "reliability_trace": {
            "attempt_type_mastery_factor": 0.8,
            "grader_confidence_factor": 0.97,
            "hint_mastery_factor": 1.0,
        },
        "familiarity_trace": {
            "independent_evidence_discount": 0.85,
            "same_item_discount": 1.0,
            "same_facet_surface_discount": 0.85,
            "same_surface_family_discount": 1.0,
        },
        "error_impact_trace": {"error_sharpening": 1.0},
    }
    payload.update(overrides)
    return payload


def test_factor_product_reproduces_the_stored_observation_weight():
    """The strip is only honest if its factors multiply back to the real weight."""

    explanation = explain_mastery_step(_payload(), observed_correctness=1.0)

    assert explanation is not None
    product = 1.0
    for factor in explanation.factors:
        product *= factor.multiplier
    assert product == pytest.approx(explanation.observation_weight, abs=1e-9)
    assert explanation.product_reconciles is True


def test_neutral_factors_are_dropped_but_penalties_are_kept():
    explanation = explain_mastery_step(_payload(), observed_correctness=1.0)

    assert explanation is not None
    keys = [factor.key for factor in explanation.factors]
    # hints and error sharpening were both 1.0 -- they changed nothing.
    assert "hints" not in keys
    assert "error_sharpening" not in keys
    assert keys == ["facet_coverage", "attempt_type", "grader_confidence", "familiarity"]


def test_dominant_factor_is_the_largest_penalty():
    explanation = explain_mastery_step(_payload(), observed_correctness=1.0)

    assert explanation is not None
    assert explanation.dominant_factor_key == "facet_coverage"


def test_amplifying_factor_never_becomes_the_dominant_one():
    """Error sharpening multiplies above 1.0; it adds weight and must not 'win'."""

    payload = _payload(
        observation_weight=0.23086 * 1.4,
        error_impact_trace={"error_sharpening": 1.4},
    )
    explanation = explain_mastery_step(payload, observed_correctness=0.0)

    assert explanation is not None
    assert "error_sharpening" in [factor.key for factor in explanation.factors]
    assert explanation.dominant_factor_key == "facet_coverage"
    assert explanation.product_reconciles is True


def test_coverage_detail_counts_touched_against_required_facets():
    explanation = explain_mastery_step(_payload(), observed_correctness=1.0)

    assert explanation is not None
    coverage = next(f for f in explanation.factors if f.key == "facet_coverage")
    assert coverage.detail == "3 of 6 facets at 0.70 exposure"


def test_weight_floor_is_flagged_so_the_ui_can_say_the_step_stopped_tracking():
    below = explain_mastery_step(
        _payload(observation_weight=WEIGHT_FLOOR / 2), observed_correctness=1.0
    )
    above = explain_mastery_step(_payload(), observed_correctness=1.0)

    assert below is not None and below.at_weight_floor is True
    assert above is not None and above.at_weight_floor is False


def test_observed_correctness_comes_from_the_caller_not_the_payload():
    explanation = explain_mastery_step(_payload(), observed_correctness=0.25)

    assert explanation is not None
    assert explanation.observed_correctness == 0.25
    assert explanation.expected_correctness == 0.6091


def test_untraceable_attempts_return_none_rather_than_a_fabricated_chain():
    assert explain_mastery_step(None) is None
    assert explain_mastery_step({}) is None
    assert explain_mastery_step({"lo_relative_coverage": 0.35}) is None


def test_a_payload_missing_traces_reports_a_non_reconciling_chain():
    """A weight with no surviving factors must not claim to be explained."""

    explanation = explain_mastery_step({"observation_weight": 0.5})

    assert explanation is not None
    assert explanation.factors == ()
    assert explanation.product_reconciles is False
