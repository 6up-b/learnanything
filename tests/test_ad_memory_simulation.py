"""Fast numerical contracts; the final arc_close test is the registered report source."""
from __future__ import annotations

import json
from dataclasses import replace

import numpy as np
import pytest

from learnloop.adaptive_difficulty import model as M
from learnloop.adaptive_difficulty import priors as P
from learnloop.config import MasteryConfig
from learnloop.sim import ad_memory_synthetic as S


def test_stable_effects_and_common_random_numbers():
    data = S.generate("balanced", "contract", n=3)
    again = S.generate("balanced", "contract", n=3)
    other = S.generate("shared", "contract", n=3)
    np.testing.assert_array_equal(data.uniforms, again.uniforms)
    np.testing.assert_array_equal(data.categories, again.categories)
    np.testing.assert_array_equal(data.uniforms, other.uniforms)
    np.testing.assert_array_equal(data.initial_ability, other.initial_ability)
    e = data.events
    assert e[0].item == e[6].item and e[0].family == e[7].family
    assert e[0].item != e[7].item and e[0].family != e[11].family
    np.testing.assert_array_equal(data.item_effect[e[0].item], data.item_effect[e[6].item])
    arms = [S.MemoryArm(3, subject=subject, candidate=S.Candidate()) for subject in (False, True)]
    for arm in arms:
        result = S.replay(data, arm)
        np.testing.assert_array_equal(result.categories, data.categories)
        np.testing.assert_array_equal(result.uniforms, data.uniforms)
        assert arm.learning_count == 12


def test_predict_before_update_and_strict_memory_boundary():
    event = S.schedule()[0]
    fold = S.ReviewFold(2)
    fold.append(event, np.array([0, 2]))
    assert fold.inputs(event).item_r is None  # equality is not strictly before
    future = replace(event, at=event.at + 1)
    before = fold.inputs(future).item_r.copy()
    fold.append(replace(event, at=future.at + 1), np.array([2, 0]))
    np.testing.assert_array_equal(fold.inputs(future).item_r, before)
    a, b = [S.MemoryArm(2, subject=False, candidate=S.Candidate()) for _ in range(2)]
    inputs = S.MemoryInputs()
    pa = a.step(event, inputs, np.array([0, 0]))
    pb = b.step(event, inputs, np.array([2, 2]))
    np.testing.assert_array_equal(pa.probabilities, pb.probabilities)
    np.testing.assert_array_equal(pa.x_item, pb.x_item)
    assert not np.array_equal(a.bank.mu, b.bank.mu)
    # Stable effect coordinates are reused, not redrawn or reset on the repeat.
    names = tuple(a.bank.names)
    a.step(replace(event, at=1), inputs, np.array([2, 2]))
    assert tuple(a.bank.names) == names


def test_exact_once_per_surface_increment_in_both_views():
    for subject in (False, True):
        arm = S.MemoryArm(2, subject=subject, candidate=S.Candidate())
        for event in S.schedule():
            arm.step(event, S.MemoryInputs(), np.array([0, 2]))
            expected = arm.bank.mean("gamma") if arm.last_learned else np.zeros(arm.bank.B)
            np.testing.assert_allclose(arm.last_learning_delta, expected, atol=1e-14)
        assert arm.learning_count == len({e.family for e in S.schedule()}) == 12
    # Ineligible first graded attempt consumes the old one-opportunity rule.
    arm = S.MemoryArm(1, subject=False, candidate=S.Candidate())
    event = S.schedule()[0]
    arm.step(event, S.MemoryInputs(), np.array([2]), eligible=False)
    arm.step(replace(event, at=1), S.MemoryInputs(), np.array([2]))
    assert arm.learning_count == 0


@pytest.mark.parametrize("effect_scale", [.25, 1., 4.])
def test_same_item_joint_variance_floor(effect_scale):
    result = S.variance_floor(effect_scale=effect_scale, steps=128)
    assert result["minimum_ability_variance"] >= result["floor"] - 1e-10
    assert result["final_ability_variance"] < P.COLD_START_VARIANCE
    assert result["ability_effect_covariance"] < 0
    assert result["sibling_variance"] < result["novel_variance"]


def test_sibling_novel_and_singleton_residuals():
    arm = S.MemoryArm(1, subject=False, candidate=S.Candidate(rhos=(.5,)))
    e = S.schedule()
    p0 = arm.step(e[0], S.MemoryInputs(), np.array([2]))
    same = arm.predict(e[1], S.MemoryInputs())
    sibling = arm.predict(e[7], S.MemoryInputs())
    novel = arm.predict(e[11], S.MemoryInputs())
    np.testing.assert_array_equal(p0.residual, 1)
    np.testing.assert_array_equal(same.residual, 0)
    np.testing.assert_array_equal(sibling.residual, .5)
    np.testing.assert_array_equal(novel.residual, 1)
    assert sibling.mean[0] != novel.mean[0]
    arm.step(e[9], S.MemoryInputs(family_r=np.array([.8])), np.array([2]))
    assert not arm.bank.has(S.family_name(e[9].family))
    p = arm.predict(e[10], S.MemoryInputs(item_r=np.array([.8]), family_r=np.array([.8])))
    np.testing.assert_array_equal(p.x_family, 0)


def test_drilled_success_does_not_identify_transferable_ability():
    """The same repeat likelihood can hide different novel-family predictions."""
    arms = [S.MemoryArm(1, subject=False, candidate=S.Candidate(rhos=(.5,), ladder=(6.,))) for _ in range(2)]
    event = S.schedule()[0]
    for arm, ability, familiarity in zip(arms, (1., -1.), (0., 2.), strict=True):
        arm.step(event, S.MemoryInputs(), np.array([2]))
        # Two hypothetical posterior locations with identical covariance, not fitted truths.
        arm.bank.mu[:] = 0.
        arm.bank.mu[:, arm.bank.index[M.subject_name("subject")]] = ability
        arm.bank.mu[:, arm.bank.index[S.item_name(event.item)]] = familiarity
    repeat = [arm.predict(event, S.MemoryInputs()) for arm in arms]
    np.testing.assert_array_equal(repeat[0].probabilities, repeat[1].probabilities)
    novel = [arm.predict(S.schedule()[11], S.MemoryInputs()) for arm in arms]
    assert novel[0].probabilities[0, 2] > novel[1].probabilities[0, 2]


@pytest.mark.parametrize("bad_variance", [-1., np.nan, np.inf])
def test_residual_seam_rejects_invalid_values_without_mutating_state(bad_variance):
    bank = M.Bank((P.LO_VIEW_POINT,))
    before = bank.state_hash()
    with pytest.raises(ValueError, match="residual variance"):
        bank.update(np.zeros(bank.d), 2, residual_variance=bad_variance)
    assert bank.state_hash() == before


@pytest.mark.parametrize("ladder", S.LADDERS)
def test_warmth_equal_mean_added_variance(ladder):
    for hours in (0, 1.5, 6, 24, 96):
        result = S.warmth_check(ladder, hours)
        assert result["mean"] == pytest.approx(result["old_mean"], abs=1e-14)
        assert result["variance"] - result["old_variance"] == pytest.approx(result["added_variance"], abs=1e-14)
        if len(ladder) > 1 and hours == 0:
            assert result["success"] != result["old_success"]
            assert result["band"] != result["old_band"]


def test_no_repeat_novel_prediction_matches_predecessor():
    for subject in (False, True):
        old = S.MemoryArm(2, subject=subject, candidate=None)
        new = S.MemoryArm(2, subject=subject, candidate=S.Candidate(rhos=(.5,), ladder=(6.,)))
        event = S.schedule()[0]
        a, b = old.predict(event, S.MemoryInputs()), new.predict(event, S.MemoryInputs())
        np.testing.assert_array_equal(a.mean, b.mean)
        np.testing.assert_array_equal(a.variance + a.residual, b.variance + b.residual)
        np.testing.assert_array_equal(a.probabilities, b.probabilities)


@pytest.mark.parametrize("subject", [False, True])
def test_novel_only_sequence_preserves_predecessor_prediction_and_drift_order(subject):
    old = S.MemoryArm(1, subject=subject, candidate=None)
    new = S.MemoryArm(1, subject=subject, candidate=S.Candidate(rhos=(.5,), ladder=(6.,)))
    for index in range(8):
        event = replace(S.schedule()[0], index=index, at=float(index), item=f"new:{index}", family=f"new-family:{index}")
        a, b = [arm.predict(event, S.MemoryInputs()) for arm in (old, new)]
        np.testing.assert_allclose(a.mean, b.mean, atol=1e-13)
        np.testing.assert_allclose(a.variance + a.residual, b.variance + b.residual, atol=1e-13)
        np.testing.assert_allclose(a.probabilities, b.probabilities, atol=1e-13)
        for arm, prediction in ((old, a), (new, b)):
            arm.observe(event, prediction, np.array([index % 3]))


def test_residual_seam_default_is_bit_identical():
    for category in (M.CENSORED, 0, 1, 2):
        a = M.Bank((P.LO_VIEW_POINT,), groups=2)
        b = a.copy()
        u = np.zeros((a.B, a.d))
        u[:, a.index["zeta"]] = 1
        before = a.state_hash()
        ra = a.update(u, category)
        rb = b.update(u, category, residual_variance=(P.A * P.TAU0) ** 2)
        assert a.state_hash() == b.state_hash() != before
        np.testing.assert_array_equal(ra.category_probabilities, rb.category_probabilities)
        np.testing.assert_array_equal(ra.log_z, rb.log_z)


def test_no_configuration_or_global_prior_mutation():
    config = MasteryConfig().model_dump()
    priors = (P.versions(), P.hyper_grid(), P.GAMMA_PRIOR, P.ZETA_PRIOR, P.TAU0)
    data = S.generate("balanced", "contract-no-mutation", n=2)
    first = S.replay(data, S.MemoryArm(2, subject=False, candidate=S.Candidate()))
    second = S.replay(data, S.MemoryArm(2, subject=False, candidate=S.Candidate()))
    np.testing.assert_array_equal(first.probabilities, second.probabilities)
    assert config == MasteryConfig().model_dump()
    assert priors == (P.versions(), P.hyper_grid(), P.GAMMA_PRIOR, P.ZETA_PRIOR, P.TAU0)


def test_full_subject_grid_matches_duplicate_collapsed_grid():
    data = S.generate("balanced", "contract-grid", n=1)
    for candidate in (None, S.Candidate()):
        small = S.replay(data, S.MemoryArm(1, subject=True, candidate=candidate))
        full = S.replay(data, S.MemoryArm(1, subject=True, candidate=candidate, full_grid=True))
        np.testing.assert_allclose(small.probabilities, full.probabilities, atol=1e-13)


def test_metrics_and_recovery_are_not_outcome_coverage():
    from learnloop.sim.ad_memory_experiment import metrics

    result = metrics(np.array([.25, .75]), np.array([False, True]), np.array([True, False]))
    assert result["count"] == 2
    assert result["brier"] == .0625
    assert result["bias"] == 0
    assert result["coverage"] == .5
    assert result["log_loss"] == pytest.approx(-np.log(.75))


@pytest.mark.arc_close
def test_registered_experiment(record_property):
    """The one full run: its JSON is captured with --junitxml for report rendering."""
    from learnloop.sim.ad_memory_experiment import run_registered

    result = run_registered()
    assert result["trajectories"] == 384
    assert result["presentations"] == 18432
    assert len(result["seeds"]) == 8
    assert len(result["worlds"]) == 6
    record_property("adm0_results", json.dumps(result, allow_nan=False, sort_keys=True))
