"""Evidence-mass collapse (Fable's-take item 3): one config-owned primitive
replaces the three former module tables. Locks the derivation semantics and the
two documented intentional behavior changes."""

import pytest

from learnloop.config import EvidenceConfig, LearnLoopConfig, load_config
from learnloop.attempts.evidence import (
    DEFAULT_EVIDENCE,
    attempt_evidence_mass,
    attempt_surface_exposure,
    practice_mode_item_coverage,
)

# The retired mastery-side table (attempt_types.ATTEMPT_TYPE_FACTORS) — the
# canonical values evidence_mass must reproduce exactly.
OLD_ATTEMPT_TYPE_FACTORS = {
    "independent_attempt": 1.0,
    "open_text": 1.0,
    "diagnostic_probe": 1.0,
    "hinted_attempt": 1.0,
    "reconstruction_after_walkthrough": 0.5,
    "dont_know": 0.7,
    "self_report": 0.3,
    "guided_walkthrough": 0.0,
    "skip": 0.0,
}

# The retired coverage-side table (recall_coverage.ATTEMPT_TYPE_COVERAGE_FACTORS).
OLD_COVERAGE_FACTORS = {
    "dont_know": 1.0,
    "independent_attempt": 1.0,
    "open_text": 1.0,
    "diagnostic_probe": 1.0,
    "hinted_attempt": 0.90,
    "reconstruction_after_walkthrough": 0.60,
    "self_report": 0.30,
    "guided_walkthrough": 0.0,
    "skip": 0.0,
}

# Intentional divergences from the old coverage table (documented in the plan):
# hinted hint-dampening is owned per-hint by item.hint_policy (0.90 double-counted);
# reconstruction takes the mastery-side 0.5 (calibration bands were tuned against it).
INTENTIONAL_COVERAGE_CHANGES = {
    "hinted_attempt": 1.0,
    "reconstruction_after_walkthrough": 0.5,
}


def test_evidence_mass_reproduces_old_mastery_table_exactly() -> None:
    for attempt_type, factor in OLD_ATTEMPT_TYPE_FACTORS.items():
        assert attempt_evidence_mass(attempt_type) == pytest.approx(factor), attempt_type


def test_surface_exposure_matches_old_coverage_table_except_documented_changes() -> None:
    for attempt_type, old_factor in OLD_COVERAGE_FACTORS.items():
        expected = INTENTIONAL_COVERAGE_CHANGES.get(attempt_type, old_factor)
        assert attempt_surface_exposure(attempt_type) == pytest.approx(expected), attempt_type


def test_dont_know_two_axis_contract() -> None:
    # A confident "don't know" fully covers the surface as evidence-of-absence
    # but carries dampened weight on the mastery belief (self-diagnosis).
    assert attempt_surface_exposure("dont_know") == 1.0
    assert attempt_evidence_mass("dont_know") == pytest.approx(0.7)


def test_non_recording_types_carry_zero_on_both_axes() -> None:
    for attempt_type in ("guided_walkthrough", "skip"):
        assert attempt_evidence_mass(attempt_type) == 0.0
        assert attempt_surface_exposure(attempt_type) == 0.0


def test_unknown_attempt_type_defaults_to_full_evidence() -> None:
    # Preserves the old `.get(..., 1.0)` semantics on both axes.
    assert attempt_evidence_mass("future_mode") == 1.0
    assert attempt_surface_exposure("future_mode") == 1.0


def test_practice_mode_item_coverage_matches_old_defaults() -> None:
    old = {
        "constructed_response": 0.85,
        "open_text": 0.85,
        "short_answer": 0.75,
        "diagnostic_probe": 0.80,
        "independent_attempt": 0.75,
        "hinted_attempt": 0.65,
        "multiple_choice": 0.45,
        "self_report": 0.25,
    }
    for mode, coverage in old.items():
        assert practice_mode_item_coverage(mode) == pytest.approx(coverage), mode
    assert practice_mode_item_coverage("unknown_mode") == pytest.approx(0.75)


def test_default_config_text_round_trips_canonical_values() -> None:
    # DEFAULT_CONFIG_TEXT and the pydantic default factories are duplicated by
    # convention; they must agree.
    import tomllib

    from learnloop.config import DEFAULT_CONFIG_TEXT

    parsed = LearnLoopConfig.model_validate(tomllib.loads(DEFAULT_CONFIG_TEXT))
    assert parsed.evidence == DEFAULT_EVIDENCE


def test_partial_toml_override_keeps_other_types_at_defaults(tmp_path) -> None:
    config_path = tmp_path / "learnloop.toml"
    config_path.write_text(
        "schema_version = 1\n"
        "[evidence.attempt_types.self_report]\n"
        "evidence_mass = 0.4\n",
        encoding="utf-8",
    )
    config = load_config(config_path)
    assert attempt_evidence_mass("self_report", config.evidence) == pytest.approx(0.4)
    # Untouched entries keep canonical values instead of resetting to 1.0.
    assert attempt_evidence_mass("reconstruction_after_walkthrough", config.evidence) == pytest.approx(0.5)
    assert attempt_surface_exposure("dont_know", config.evidence) == 1.0
    assert attempt_evidence_mass("skip", config.evidence) == 0.0


def test_override_flows_through_resolvers(tmp_path) -> None:
    from learnloop.learner.mastery import MasteryObservation, observation_weight
    from datetime import UTC, datetime

    evidence = EvidenceConfig.model_validate(
        {"attempt_types": {"self_report": {"evidence_mass": 0.4}}}
    )
    assert attempt_evidence_mass("self_report", evidence) == pytest.approx(0.4)

    observation = MasteryObservation(
        rubric_score=3,
        max_points=4,
        evidence_coverage=1.0,
        hint_dampening=1.0,
        grader_confidence=1.0,
        attempt_type="self_report",
        observed_at=datetime(2026, 1, 1, tzinfo=UTC),
        attempt_evidence_mass=attempt_evidence_mass("self_report", evidence),
    )
    assert observation_weight(observation) == pytest.approx(0.4)
    # Without the resolved mass the observation falls back to canonical defaults.
    fallback = MasteryObservation(
        rubric_score=3,
        max_points=4,
        evidence_coverage=1.0,
        hint_dampening=1.0,
        grader_confidence=1.0,
        attempt_type="self_report",
        observed_at=datetime(2026, 1, 1, tzinfo=UTC),
    )
    assert observation_weight(fallback) == pytest.approx(0.3)
