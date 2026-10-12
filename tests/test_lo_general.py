from dataclasses import replace
from math import exp

import numpy as np
import pytest

import learnloop.field.memory  # noqa: F401 - the registry includes the PF-a memory arms
from learnloop.field.predictors import LoGeneral, MasteryEKF, create_predictor, registered_predictors
from learnloop.field.types import ArmConstants, AttemptRow, FacetRow, ItemFeatures, SignalRow


def features(**kwargs):
    return replace(ItemFeatures("i", "L", "2026-01-01T00:00:00Z"), **kwargs)


def row(i=0, outcome=1.0, **kwargs):
    return AttemptRow(str(i), features(), outcome, 1.0, **kwargs)


@pytest.mark.parametrize("primed", [False, True])
@pytest.mark.parametrize("a", [0.6, 1.0, 1.7])
def test_one_lo_limit_matches_incumbent_including_drift_and_priming(primed, a):
    incumbent = MasteryEKF()
    challenger = LoGeneral(constants=ArmConstants(general_variance=0, lo_variance=3))
    for i, y in enumerate([1, 0, 0.5, 1, 0]):
        f = features(a=a, b=0.8, primed=primed and i > 0,
                     observed_at=f"2026-01-{i + 1:02}T00:00:00Z")
        observation = replace(row(i, y), features=f)
        assert challenger.predict(f) == pytest.approx(incumbent.predict(f), abs=1e-13)
        incumbent.observe(observation)
        challenger.observe(observation)
        left, right = incumbent.region_estimates()["L"], challenger.region_estimates()["L"]
        assert left.mean == pytest.approx(right.mean, abs=1e-13)
        assert left.variance == pytest.approx(right.variance, abs=1e-13)


@pytest.mark.parametrize("name", registered_predictors())
@pytest.mark.parametrize("excluded", [False, True])
@pytest.mark.parametrize("outcome", [0, None])
def test_zero_mass_byte_invariance_including_no_new_region(name, excluded, outcome):
    model = create_predictor(name)
    first = FacetRow("first", features(facet_id="f"), 1, 1, facet_id="f")
    model.observe(first)
    before = model.snapshot_bytes()
    f = features(item_id="unknown", lo_id="unknown", subject_id="new",
                 capability="coordination", variant_relation="far", facet_id="new")
    # Predictions must not register the unseen region either.
    model.predict(f)
    model.observe(FacetRow("skip", f, outcome, 1 if excluded else 0,
                           revision_status="excluded" if excluded else "exact",
                           hints_used=2, mass_without_assistance=0, facet_id="new"))
    assert model.snapshot_bytes() == before


@pytest.mark.parametrize("name", registered_predictors())
def test_assistance_only_zero_mass_is_replaced_only_by_hint_arms(name):
    model = create_predictor(name)
    reference = create_predictor(name)
    before = model.snapshot_bytes()
    f = features(facet_id="f")
    model.observe(FacetRow("help", f, 1, 0, hints_used=2,
                           mass_without_assistance=0.8, facet_id="f"))
    if "hints" in getattr(model, "extensions", ()):
        graded_outcome = max(model.constants.hint_floor, 1 - 2 * model.constants.hint_step)
        reference.observe(FacetRow("help", f, graded_outcome, 0.8, facet_id="f"))
        assert model.snapshot_bytes() == reference.snapshot_bytes()
        assert model.snapshot_bytes() != before
    else:
        assert model.snapshot_bytes() == before


@pytest.mark.parametrize("name", ["lo_general+hints", "lo_general+composite"])
@pytest.mark.parametrize("mass", [0, -1, float("nan"), float("inf")])
def test_invalid_hint_replacement_mass_is_a_complete_noop(name, mass):
    model = create_predictor(name)
    before = model.snapshot_bytes()
    model.observe(replace(row(hints_used=2, mass_without_assistance=mass),
                          effective_mass=0))
    assert model.snapshot_bytes() == before


@pytest.mark.parametrize("name", ["lo_general+hints", "lo_general+composite"])
def test_excluded_hint_row_cannot_be_restored_by_replacement_mass(name):
    model = create_predictor(name)
    before = model.snapshot_bytes()
    model.observe(row(hints_used=2, mass_without_assistance=1, revision_status="excluded"))
    assert model.snapshot_bytes() == before


@pytest.mark.parametrize("predictor", [LoGeneral, MasteryEKF])
@pytest.mark.parametrize("a", [0.6, 1.7])
def test_priming_probability_uses_shifted_difficulty_without_mutation(predictor, a):
    model = predictor()
    f = features(a=a, b=0.8, primed=True)
    before = model.snapshot_bytes()
    b_eff = f.b - model.config.irt.priming_b_offset
    assert model.predict(f) == pytest.approx(1 / (1 + exp(a * b_eff)), abs=1e-14)
    assert model.snapshot_bytes() == before


def test_joint_update_generalizes_only_within_subject_and_keeps_directness():
    a, b = features(), features(item_id="j", lo_id="M")
    c = features(item_id="k", lo_id="N", subject_id="other")
    model = LoGeneral(items=[a, b, c])
    for i in range(5):
        model.observe(row(i))
    assert model.predict(b) > 0.5
    assert model.predict(c) == 0.5
    estimates = model.region_estimates()
    assert not estimates["L"].untested
    assert estimates["M"].untested
    assert estimates["M"].n_eff > 0
    assert estimates["N"].n_eff == 0
    assert model.covariance.dtype == np.float64
    assert model.mean.dtype == np.float64
    assert np.linalg.eigvalsh(model.covariance).min() >= -1e-14


def test_no_graph_input_and_incumbent_never_propagates():
    model = MasteryEKF(items=[features(lo_id="M", item_id="j")])
    model.observe(row())
    assert model.predict(features(lo_id="M")) == 0.5
    with pytest.raises(TypeError):
        LoGeneral(edges=[("L", "M", "part_of")])


def test_practice_is_predicted_before_outcome_and_not_committed_by_prediction():
    base, practice = LoGeneral(), create_predictor("lo_general+practice")
    before = practice.snapshot_bytes()
    assert practice.predict(features()) > base.predict(features())
    assert practice.predict(features()) == practice.predict(features())
    assert practice.snapshot_bytes() == before
    for i in range(5):
        base.observe(row(i))
        practice.observe(row(i))
    assert practice.predict(features()) > base.predict(features())
    assert practice.predict(features(cold=False)) < practice.predict(features())


@pytest.mark.parametrize("cold", [False, True])
def test_practice_zero_innovation_commits_exactly_gamma_only_when_cold(cold):
    model = create_predictor("lo_general+practice")
    f = features(cold=cold, a=1.7, b=0.4)
    gamma = model.constants.practice_gamma
    for i in range(4):
        expected_mean = (i + 1) * gamma if cold else 0
        expected_p = 1 / (1 + exp(-f.a * (expected_mean - f.b)))
        before = model.snapshot_bytes()
        assert model.predict(f) == pytest.approx(expected_p, abs=1e-14)
        assert model.snapshot_bytes() == before
        model.observe(AttemptRow(str(i), f, model.predict(f), 1))
        assert model.mean[model.keys.index("general:default")] == 0
        assert model.mean[model.keys.index("lo:L")] == pytest.approx(expected_mean, abs=1e-14)


@pytest.mark.parametrize("chosen_cold", [[], [True], [True, True], [False, False],
                                       [True, False, True]])
@pytest.mark.parametrize("candidate_cold", [False, True])
def test_practice_conditional_gain_accumulates_only_chosen_cold_transitions(
    chosen_cold, candidate_cold,
):
    # A single scalar LO makes each hypothetical covariance update analytic.
    model = LoGeneral(extensions=("practice",),
                      constants=ArmConstants(general_variance=0, lo_variance=3))
    f = features(a=1.7, b=-0.3, cold=candidate_cold)
    chosen = [replace(f, item_id=str(i), cold=cold) for i, cold in enumerate(chosen_cold)]
    variance, mean = 3.0, 0.0
    for cold in [*chosen_cold, candidate_cold]:
        predicted_mean = mean + (model.constants.practice_gamma if cold else 0)
        p = 1 / (1 + exp(-f.a * (predicted_mean - f.b)))
        h = f.a * p * (1 - p)
        noise = model.config.base_observation_variance * p * (1 - p)
        reduction = (variance * h) ** 2 / (h * h * variance + noise)
        variance -= reduction
        mean = predicted_mean
    before = model.snapshot_bytes()
    assert model.conditional_gain(f, chosen, {"L": 1}) == pytest.approx(reduction, abs=1e-14)
    assert model.snapshot_bytes() == before


def test_capability_and_transfer_offsets():
    capability = create_predictor("lo_general+capability")
    for i in range(5):
        capability.observe(replace(row(i), features=features(capability="retrieval")))
    assert capability.predict(features(lo_id="new", capability="retrieval")) > capability.predict(
        features(lo_id="new", capability="coordination"))
    transfer = create_predictor("lo_general+transfer")
    predictions = [transfer.predict(features(variant_relation=value))
                   for value in ("same_target", "isomorph", "near", "far")]
    assert predictions[0] == predictions[1] > predictions[2] > predictions[3]


def test_retrievability_and_beta_zero_sweep():
    model = create_predictor("lo_general+retrievability")
    assert model.predict(features(retrievability=0.9)) > model.predict(features(retrievability=0.1))
    zero = create_predictor("lo_general+retrievability:beta=0")
    assert zero.predict(features(retrievability=0.1)) == LoGeneral().predict(features())


def test_hints_replace_not_stack_assistance_discount():
    hints = create_predictor("lo_general+hints")
    reference = LoGeneral()
    hints.observe(AttemptRow(
        "0", features(), 1, 0.08, hints_used=2, mass_without_assistance=0.8, assisted=True))
    reference.observe(AttemptRow("0", features(), 0.6, 0.8))
    assert hints.region_estimates() == reference.region_estimates()
    early = create_predictor("lo_general+hints")
    early.observe(row(hints_used=1, help_before_work=True, mass_without_assistance=1))
    assert early.predict(features()) < 0.5


def test_hint_replacement_requires_explicit_factorization():
    with pytest.raises(ValueError, match="mass_without_assistance"):
        create_predictor("lo_general+hints").observe(row(hints_used=1))


def test_signals_are_weak_capped_and_not_demonstration():
    model = create_predictor("lo_general+tutor_signals")
    signal = SignalRow("s", "L", features().observed_at, "prerequisite", 0, 0.15)
    model.observe(signal)
    assert model.predict(features()) < 0.5
    assert model.region_estimates()["L"].untested
    model.observe(replace(signal, signal_id="s2"))
    before = model.snapshot_bytes()
    model.observe(replace(signal, signal_id="s3"))
    assert model.snapshot_bytes() == before
    base = LoGeneral()
    before = base.snapshot_bytes()
    base.observe(signal)
    assert base.snapshot_bytes() == before


def test_llm_difficulty_only_widens_measurement_uncertainty():
    authored, llm = LoGeneral(), LoGeneral()
    authored.observe(row())
    llm.observe(replace(row(), features=features(difficulty_source="llm")))
    assert llm.region_estimates()["L"].variance > authored.region_estimates()["L"].variance
    assert 0.5 < llm.predict(features()) < authored.predict(features())


def test_drift_adds_variance_without_mean_decay():
    model = LoGeneral()
    model.observe(row())
    before = model.predict_item(features())
    after = model.predict_item(features(observed_at="2026-02-01T00:00:00Z"))
    assert before.p_success == after.p_success
    assert after.logit_variance > before.logit_variance


def test_priors_and_conditional_information_are_pure():
    f = features()
    model = LoGeneral(items=[f], general_means={"default": 0.8})
    assert model.predict(f) > 0.5
    estimate = model.region_estimates()["L"]
    assert estimate.mean == 0.8 and estimate.variance == 3 and estimate.untested
    before = model.snapshot_bytes()
    gain = model.conditional_gain(f, [], {"L": 1})
    assert 0 < model.conditional_gain(f, [f], {"L": 1}) < gain
    assert model.conditional_gain(f, [], {"missing": 1}) == 0
    assert model.snapshot_bytes() == before


def test_small_mass_is_not_floored_in_challenger():
    weak, ordinary = LoGeneral(), LoGeneral()
    weak.observe(replace(row(), effective_mass=0.001))
    ordinary.observe(replace(row(), effective_mass=0.1))
    assert 0.5 < weak.predict(features()) < ordinary.predict(features())
    assert weak.region_estimates()["L"].variance > ordinary.region_estimates()["L"].variance


def test_hint_sweep_and_versions_include_constants():
    shallow = create_predictor("lo_general+hints:step=0.1")
    deep = create_predictor("lo_general+hints:step=0.3")
    observation = row(hints_used=2, mass_without_assistance=1)
    shallow.observe(observation)
    deep.observe(observation)
    assert shallow.predict(features()) > deep.predict(features())
    assert shallow.version_hash != deep.version_hash


def test_signal_cap_resets_only_on_next_day():
    model = create_predictor("lo_general+tutor_signals")
    signal = SignalRow("s", "L", features().observed_at, "prerequisite", 0, 0.3)
    model.observe(signal)
    before = model.snapshot_bytes()
    model.observe(replace(signal, signal_id="same-day"))
    assert model.snapshot_bytes() == before
    model.observe(replace(signal, signal_id="next-day", observed_at="2026-01-02T00:00:00Z"))
    assert model.snapshot_bytes() != before


def test_facet_beta_uses_share_without_multiplying_attempt_mass():
    model = create_predictor("facet_beta")
    for facet in ("f", "g"):
        model.observe(FacetRow(facet, features(facet_id=facet), 1, 1,
                               facet_id=facet, facet_share=0.5))
    assert sum(alpha + beta - 2 for alpha, beta in model.counts.values()) == 1
    assert model.predict(features(facet_id="f")) == 0.6


@pytest.mark.parametrize("kwargs", [
    {"general_variance": -1}, {"lo_variance": float("nan")},
    {"general_variance": 0, "lo_variance": 0}, {"hint_floor": 2},
])
def test_constants_are_validated(kwargs):
    with pytest.raises(ValueError):
        ArmConstants(**kwargs)


@pytest.mark.parametrize("name", registered_predictors())
def test_rebuild_deterministic_and_no_external_io(name, monkeypatch):
    import socket
    import sqlite3

    from learnloop.ai.providers.codex import SdkCodexClient
    from learnloop.ai.providers.codex_http import HttpCodexClient
    from learnloop.ai.providers.openai_chat import OpenAIChatProviderClient
    from learnloop.ai.providers.openai_embedding import OpenAIEmbeddingProviderClient

    def forbidden(*args, **kwargs):
        raise AssertionError("predictors must not perform I/O")

    monkeypatch.setattr(socket, "socket", forbidden)
    monkeypatch.setattr(sqlite3, "connect", forbidden)
    monkeypatch.setattr(OpenAIChatProviderClient, "complete", forbidden)
    monkeypatch.setattr(SdkCodexClient, "complete", forbidden)
    monkeypatch.setattr(HttpCodexClient, "complete_legacy", forbidden)
    monkeypatch.setattr(OpenAIEmbeddingProviderClient, "embed", forbidden)
    model = create_predictor(name)
    rows = [FacetRow(str(i), features(facet_id="f"), float(i % 2), 1, facet_id="f")
            for i in range(8)]
    model.rebuild(rows)
    before = model.snapshot_bytes()
    model.rebuild(reversed(rows))
    assert model.snapshot_bytes() == before
