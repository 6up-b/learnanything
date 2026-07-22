"""Characterization tests (P0.0, spec_p0_measurement_correctness.md §2): pin current behavior; these tests document reality, not desired behavior. When P0.x intentionally changes behavior, update these tests in the same commit and note the change."""

from __future__ import annotations

import pytest

from learnloop.services.probe_families import (
    DEFAULT_CONDITIONAL_PSEUDO_COUNT,
    GRADER_CHANNEL_RELIABILITY,
    ORDINAL_VOCABULARY,
    CompiledInstrument,
    InstrumentCard,
    ProbeFamilyTemplate,
    compose_with_grader_channel,
    grader_channel_matrix,
    instrument_conditionals,
    instrument_observation_likelihoods,
    validate_and_compile_card,
)

# --- Fixed protocol constants -------------------------------------------------


def test_ordinal_vocabulary_table_exact_values():
    # §9.3 canonical ordinal table: the exact anchors compiled from authored
    # ordinal words before per-row normalization.
    assert ORDINAL_VOCABULARY == {
        "dominant": 0.60,
        "likely": 0.25,
        "occasional": 0.10,
        "rare": 0.04,
        "negligible": 0.01,
    }
    # Pin the individual anchors so a single edited value is caught.
    assert ORDINAL_VOCABULARY["dominant"] == pytest.approx(0.60)
    assert ORDINAL_VOCABULARY["likely"] == pytest.approx(0.25)
    assert ORDINAL_VOCABULARY["occasional"] == pytest.approx(0.10)
    assert ORDINAL_VOCABULARY["rare"] == pytest.approx(0.04)
    assert ORDINAL_VOCABULARY["negligible"] == pytest.approx(0.01)


def test_default_conditional_pseudo_count_is_eight():
    assert DEFAULT_CONDITIONAL_PSEUDO_COUNT == pytest.approx(8.0)


def test_grader_channel_reliability_constants():
    # §7.6 fixed symmetric grader channels: one reliability per policy.
    assert GRADER_CHANNEL_RELIABILITY == {
        "diagnostic_microprobe_v1": 0.90,
        "diagnostic_longform_v1": 0.80,
    }
    assert GRADER_CHANNEL_RELIABILITY["diagnostic_microprobe_v1"] == pytest.approx(0.90)
    assert GRADER_CHANNEL_RELIABILITY["diagnostic_longform_v1"] == pytest.approx(0.80)


# --- grader_channel_matrix ----------------------------------------------------


def test_microprobe_channel_matrix_binary_alphabet():
    # r = 0.90; size 2 -> off-diagonal spread = (1-0.90)/(2-1) = 0.10.
    channel = grader_channel_matrix("diagnostic_microprobe_v1", ("correct", "incorrect"))
    assert channel == {
        "correct": {"correct": pytest.approx(0.90), "incorrect": pytest.approx(0.10)},
        "incorrect": {"correct": pytest.approx(0.10), "incorrect": pytest.approx(0.90)},
    }


def test_longform_channel_matrix_binary_alphabet():
    # r = 0.80; size 2 -> off-diagonal spread = (1-0.80)/(2-1) = 0.20.
    channel = grader_channel_matrix("diagnostic_longform_v1", ("correct", "incorrect"))
    assert channel == {
        "correct": {"correct": pytest.approx(0.80), "incorrect": pytest.approx(0.20)},
        "incorrect": {"correct": pytest.approx(0.20), "incorrect": pytest.approx(0.80)},
    }


def test_channel_matrix_five_class_spread():
    # r = 0.90; size 5 -> remainder 0.10 spread uniformly over 4 others = 0.025.
    alphabet = ("a", "b", "c", "d", "e")
    channel = grader_channel_matrix("diagnostic_microprobe_v1", alphabet)
    for true in alphabet:
        assert channel[true][true] == pytest.approx(0.90)
        for observed in alphabet:
            if observed != true:
                assert channel[true][observed] == pytest.approx(0.025)
        # Each row is a proper distribution.
        assert sum(channel[true].values()) == pytest.approx(1.0)


def test_unknown_policy_falls_back_to_reliability_point_nine():
    # An unregistered policy uses the hard-coded 0.9 default reliability.
    channel = grader_channel_matrix("policy_that_does_not_exist", ("correct", "incorrect"))
    assert channel["correct"]["correct"] == pytest.approx(0.90)
    assert channel["correct"]["incorrect"] == pytest.approx(0.10)


def test_explicit_reliability_override_beats_policy_constant():
    channel = grader_channel_matrix(
        "diagnostic_microprobe_v1", ("correct", "incorrect"), reliability=0.75
    )
    assert channel["correct"]["correct"] == pytest.approx(0.75)
    assert channel["correct"]["incorrect"] == pytest.approx(0.25)


def test_channel_is_symmetric_overcall_equals_undercall():
    # The confusion channel is symmetric: mistaking true `low` for observed
    # `high` (an over-call) is exactly as likely as mistaking true `high` for
    # observed `low` (an under-call). Overcall and undercall are treated
    # identically.
    channel = grader_channel_matrix("diagnostic_microprobe_v1", ("low", "high"))
    assert channel["low"]["high"] == channel["high"]["low"]
    assert channel["low"]["high"] == pytest.approx(0.10)

    # Same for the 5-class alphabet: every off-diagonal entry is identical
    # regardless of direction (no asymmetric over/undercall penalty).
    alphabet = ("v0", "v1", "v2", "v3", "v4")
    five = grader_channel_matrix("diagnostic_longform_v1", alphabet)
    for i in alphabet:
        for j in alphabet:
            assert five[i][j] == pytest.approx(five[j][i])


# --- compose_with_grader_channel ----------------------------------------------


def test_compose_point_mass_recovers_channel_column():
    channel = grader_channel_matrix("diagnostic_microprobe_v1", ("correct", "incorrect"))
    # A true-outcome point mass composes to that outcome's channel column.
    composed = compose_with_grader_channel(
        {"h": {"correct": 1.0, "incorrect": 0.0}}, channel
    )
    assert composed["h"]["correct"] == pytest.approx(0.90)
    assert composed["h"]["incorrect"] == pytest.approx(0.10)

    mirror = compose_with_grader_channel(
        {"h": {"correct": 0.0, "incorrect": 1.0}}, channel
    )
    assert mirror["h"]["correct"] == pytest.approx(0.10)
    assert mirror["h"]["incorrect"] == pytest.approx(0.90)


def test_compose_mixed_true_row():
    # P(obs | h) = Σ_true P(obs | true) P(true | h).
    channel = grader_channel_matrix("diagnostic_microprobe_v1", ("correct", "incorrect"))
    composed = compose_with_grader_channel(
        {"h": {"correct": 0.9375, "incorrect": 0.0625}}, channel
    )
    # correct: 0.90*0.9375 + 0.10*0.0625 = 0.85
    assert composed["h"]["correct"] == pytest.approx(0.85)
    # incorrect: 0.10*0.9375 + 0.90*0.0625 = 0.15
    assert composed["h"]["incorrect"] == pytest.approx(0.15)
    assert sum(composed["h"].values()) == pytest.approx(1.0)


# --- Card compilation: ordinal anchors + pseudo-count of 8 --------------------


def _binary_template() -> ProbeFamilyTemplate:
    return ProbeFamilyTemplate(
        id="fam_char",
        version=1,
        instrument_kind="microprobe",
        observation_alphabet=("correct", "incorrect"),
        hypothesis_slots=("mastered", "not_mastered"),
        grader_policy="diagnostic_microprobe_v1",
    )


def _mirror_card() -> InstrumentCard:
    return InstrumentCard(
        id="card_char",
        version=1,
        family_template_id="fam_char",
        family_template_version=1,
        learning_object_id="lo_x",
        target_decision="decide",
        bindings={},
        hypotheses=("mastered", "not_mastered"),
        conditional_observations={
            "mastered": {"correct": "dominant", "incorrect": "rare"},
            "not_mastered": {"correct": "rare", "incorrect": "dominant"},
        },
    )


def test_compiled_card_defaults_to_pseudo_count_eight_and_normalized_ordinal_rows():
    compiled = validate_and_compile_card(_mirror_card(), _binary_template())
    # The pseudo-count carried by a card with no explicit override is 8.
    assert compiled.pseudo_count == pytest.approx(8.0)
    # Rows are the ordinal anchors normalized per row: dominant=0.60, rare=0.04,
    # total 0.64 -> 0.9375 / 0.0625.
    assert compiled.rows["mastered"]["correct"] == pytest.approx(0.60 / 0.64)
    assert compiled.rows["mastered"]["incorrect"] == pytest.approx(0.04 / 0.64)
    assert compiled.rows["mastered"]["correct"] == pytest.approx(0.9375)
    assert compiled.rows["mastered"]["incorrect"] == pytest.approx(0.0625)
    assert compiled.rows["not_mastered"]["correct"] == pytest.approx(0.0625)
    assert compiled.rows["not_mastered"]["incorrect"] == pytest.approx(0.9375)


def test_calibration_posterior_mean_uses_pseudo_count_eight():
    # Posterior mean = (pseudo*prior + counts) / (pseudo + n), pseudo = 8.
    template = _binary_template()
    card = _mirror_card()
    calibration_counts = {"mastered": {"correct": 8.0, "incorrect": 0.0}}
    compiled = validate_and_compile_card(
        card, template, calibration_counts=calibration_counts
    )
    # correct: (8*0.9375 + 8) / (8 + 8) = 15.5/16 = 0.96875
    assert compiled.rows["mastered"]["correct"] == pytest.approx(0.96875)
    # incorrect: (8*0.0625 + 0) / 16 = 0.5/16 = 0.03125
    assert compiled.rows["mastered"]["incorrect"] == pytest.approx(0.03125)
    # The uncalibrated slot keeps the prior mean.
    assert compiled.rows["not_mastered"]["correct"] == pytest.approx(0.0625)


# --- End-to-end conditionals through the grader channel -----------------------


def test_instrument_conditionals_compose_prior_rows_through_microprobe_channel():
    compiled = validate_and_compile_card(_mirror_card(), _binary_template())
    conditionals = instrument_conditionals(compiled)
    # mastered row 0.9375/0.0625 composed through r=0.90 -> 0.85/0.15.
    assert conditionals["mastered"]["correct"] == pytest.approx(0.85)
    assert conditionals["mastered"]["incorrect"] == pytest.approx(0.15)
    assert conditionals["not_mastered"]["correct"] == pytest.approx(0.15)
    assert conditionals["not_mastered"]["incorrect"] == pytest.approx(0.85)


def test_observation_likelihoods_are_symmetric_over_over_and_undercall():
    compiled = validate_and_compile_card(_mirror_card(), _binary_template())
    slot_map = {"h_mastered": "mastered", "h_not": "not_mastered"}

    on_correct = instrument_observation_likelihoods(compiled, slot_map, "correct")
    on_incorrect = instrument_observation_likelihoods(compiled, slot_map, "incorrect")

    assert on_correct["h_mastered"] == pytest.approx(0.85)
    assert on_correct["h_not"] == pytest.approx(0.15)
    assert on_incorrect["h_mastered"] == pytest.approx(0.15)
    assert on_incorrect["h_not"] == pytest.approx(0.85)

    # Overcall likelihood (observe `correct` under not_mastered) equals undercall
    # likelihood (observe `incorrect` under mastered): the channel penalizes both
    # error directions identically.
    assert on_correct["h_not"] == pytest.approx(on_incorrect["h_mastered"])
    # The mirror-image hypotheses give mirror-image likelihoods.
    assert on_correct["h_mastered"] == pytest.approx(on_incorrect["h_not"])


def test_grader_reliability_override_flows_into_composed_likelihoods():
    compiled = validate_and_compile_card(_mirror_card(), _binary_template())
    slot_map = {"h_mastered": "mastered", "h_not": "not_mastered"}
    # With reliability forced to 0.5 the channel is maximally confused: composed
    # rows collapse toward uniform.
    likelihoods = instrument_observation_likelihoods(
        compiled, slot_map, "correct", grader_reliability=0.5
    )
    # mastered: 0.5*0.9375 + 0.5*0.0625 = 0.5
    assert likelihoods["h_mastered"] == pytest.approx(0.5)
    assert likelihoods["h_not"] == pytest.approx(0.5)


def test_direct_compiled_instrument_uses_grader_policy_reliability():
    # A CompiledInstrument built directly (no card) still composes through its
    # declared grader_policy's fixed reliability.
    instrument = CompiledInstrument(
        outcome_alphabet=("correct", "incorrect"),
        rows={
            "mastered": {"correct": 0.9, "incorrect": 0.1},
            "not_mastered": {"correct": 0.2, "incorrect": 0.8},
        },
        pseudo_count=8.0,
        grader_policy="diagnostic_microprobe_v1",
        provenance="test",
    )
    conditionals = instrument_conditionals(instrument)
    # mastered correct: 0.9*0.9 + 0.1*0.1 = 0.82
    assert conditionals["mastered"]["correct"] == pytest.approx(0.82)
    assert conditionals["mastered"]["incorrect"] == pytest.approx(0.18)
    # not_mastered correct: 0.9*0.2 + 0.1*0.8 = 0.26
    assert conditionals["not_mastered"]["correct"] == pytest.approx(0.26)
    assert conditionals["not_mastered"]["incorrect"] == pytest.approx(0.74)
