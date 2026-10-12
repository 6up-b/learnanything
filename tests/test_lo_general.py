from dataclasses import replace

import numpy as np
import pytest

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
def test_zero_mass_byte_invariance_including_no_new_region(name, excluded):
    model = create_predictor(name)
    first = FacetRow("first", features(facet_id="f"), 1, 1, facet_id="f")
    model.observe(first)
    before = model.snapshot_bytes()
    f = features(item_id="unknown", lo_id="unknown", subject_id="new",
                 capability="coordination", variant_relation="far", facet_id="new")
    # Predictions must not register the unseen region either.
    model.predict(f)
    model.observe(FacetRow("skip", f, 0, 1 if excluded else 0,
                           revision_status="excluded" if excluded else "exact",
                           hints_used=2, mass_without_assistance=1, facet_id="new"))
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

    def forbidden(*args, **kwargs):
        raise AssertionError("predictors must not perform I/O")

    monkeypatch.setattr(socket, "socket", forbidden)
    monkeypatch.setattr(sqlite3, "connect", forbidden)
    model = create_predictor(name)
    rows = [FacetRow(str(i), features(facet_id="f"), float(i % 2), 1, facet_id="f")
            for i in range(8)]
    model.rebuild(rows)
    before = model.snapshot_bytes()
    model.rebuild(reversed(rows))
    assert model.snapshot_bytes() == before
