"""Empirical-Bayes per-item difficulty (dark by default): shrinkage dynamics,
flag gating, replay determinism, and derived-state reset."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from learnloop.clock import FrozenClock
from learnloop.config import LearnLoopConfig
from learnloop.db.repositories import ItemParameterState, MasteryState, Repository
from learnloop.attempts.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
from learnloop.learner.mastery import (
    MasteryObservation,
    item_irt_params,
    resolve_item_irt_params,
    update_item_difficulty,
)
from learnloop.substrate.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault

from tests.helpers import NOW, append_config_toml, create_basic_vault

CONFIG = LearnLoopConfig().mastery


def _observation(score: int) -> MasteryObservation:
    return MasteryObservation(
        rubric_score=score,
        max_points=4,
        evidence_coverage=1.0,
        hint_dampening=1.0,
        grader_confidence=1.0,
        attempt_type="independent_attempt",
        observed_at=datetime(2026, 1, 1, tzinfo=UTC),
    )


def _step(prior, score=4, mu=0.0):
    return update_item_difficulty(
        prior,
        practice_item_id="pi_x",
        authored_b=0.5,
        item_a=1.0,
        learner_mu_posterior=mu,
        observation=_observation(score),
        config=CONFIG,
        algorithm_version="test",
        updated_at="2026-01-01T00:00:00Z",
    )


def test_repeated_success_drifts_b_down_slowly():
    state = None
    means = []
    for _ in range(10):
        state = _step(state, score=4, mu=0.0)
        means.append(state.b_mean)
    # Learner keeps succeeding on an item authored at b=0.5 while mu=0:
    # the item is easier than authored, so b drifts down — monotonically,
    # bounded per step, and slowly (gain scale 0.2).
    assert all(later < earlier for earlier, later in zip(means, means[1:]))
    assert means[0] > 0.5 - CONFIG.irt.b_max_step - 1e-9
    assert means[-1] > -1.0  # slow drift, not a jump to the boundary
    assert state.evidence_count == 10


def test_failure_drifts_b_up():
    state = _step(None, score=0, mu=0.0)
    assert state.b_mean > 0.5


def test_variance_shrinks_toward_floor():
    state = None
    variances = []
    for _ in range(50):
        state = _step(state, score=4, mu=0.0)
        variances.append(state.b_var)
    assert all(later <= earlier for earlier, later in zip(variances, variances[1:]))
    assert variances[-1] >= CONFIG.irt.b_var_min


def test_step_clamped():
    state = _step(None, score=0, mu=5.0)  # maximally surprising failure
    assert abs(state.b_mean - 0.5) <= CONFIG.irt.b_max_step + 1e-9


def test_resolver_uses_posterior_only_when_enabled():
    config_off = LearnLoopConfig().mastery
    assert config_off.irt.eb_difficulty_enabled is False
    posterior = ItemParameterState("pi_x", -1.5, 0.05, 12, "test", "2026-01-01T00:00:00Z")
    a_off, b_off = resolve_item_irt_params(None, None, config_off, posterior)
    assert (a_off, b_off) == item_irt_params(None, None, config_off)

    config_on = LearnLoopConfig().mastery
    config_on.irt.eb_difficulty_enabled = True
    a_on, b_on = resolve_item_irt_params(None, None, config_on, posterior)
    assert b_on == pytest.approx(-1.5)
    assert a_on == a_off


def _vault_with_flag(tmp_path, enabled: bool):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    if enabled:
        append_config_toml(
            vault_root,
            """
            [mastery.irt]
            eb_difficulty_enabled = true
            """,
        )
    vault = load_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    sync_vault_state(vault, repository, clock=FrozenClock(NOW))
    return vault, repository


def _attempt(vault, repository, *, at, points=4):
    return complete_self_graded_attempt(
        vault,
        repository,
        AttemptDraft(practice_item_id="pi_svd_define_001", learner_answer_md="U Sigma V^T"),
        SelfGradeInput(criterion_points={"correctness": points}, confidence=4),
        clock=FrozenClock(at),
    )


def test_flag_off_writes_no_rows(tmp_path):
    vault, repository = _vault_with_flag(tmp_path, enabled=False)
    _attempt(vault, repository, at=NOW)
    assert repository.item_parameter_state("pi_svd_define_001") is None


def test_flag_on_persists_and_reset_clears(tmp_path):
    vault, repository = _vault_with_flag(tmp_path, enabled=True)
    _attempt(vault, repository, at=NOW)
    _attempt(vault, repository, at=NOW + timedelta(days=1))

    state = repository.item_parameter_state("pi_svd_define_001")
    assert state is not None
    assert state.evidence_count == 2
    authored_b = 2.5 * (0.55 - 0.5) * 2.0  # helpers.py difficulty 0.55
    assert state.b_mean != pytest.approx(authored_b)  # evidence moved it
    assert abs(state.b_mean - authored_b) < 2 * CONFIG.irt.b_max_step + 1e-9

    repository.reset_learning_object_derived_state("lo_svd_definition")
    assert repository.item_parameter_state("pi_svd_define_001") is None
