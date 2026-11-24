"""L4-2's review fix round (``docs/reviews/algorithm-mvp-0.71.md``, "Review fix round"): what the lesson-weight fit's
recomputation of mastery reads. Each test failed before its fix.

With ``mastery.irt.enabled = false`` mastery's logit-space update reads the score from the rubric fraction; the fit
passes the recorded score there too, so a full-credit check is full credit (L42-R10).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from learnloop.learner import lesson_weight as LW
from learnloop.vault.loader import load_vault

from tests.teacher_fakes import build_teacher_vault
from tests.teacher_te1_review_fixes_helpers import _cold, _lesson_with_check
from tests.ux_phase1_support import set_config

T = datetime(2026, 11, 1, 9, tzinfo=UTC)


def _trajectory(repository, vault, outcome_id):
    with repository.connection() as connection:
        check = LW._checks(connection)[0]
        created = connection.execute("SELECT created_at FROM practice_attempts WHERE id = ?", (outcome_id,)).fetchone()
        trajectory = LW.recorded_trajectory(connection, vault, vault.config.mastery, check,
                                            {"id": outcome_id, "created_at": created[0]})
    return check, trajectory


def test_with_irt_off_the_recomputed_trajectory_reads_full_and_partial_credit(tmp_path):
    paths, repository = build_teacher_vault(tmp_path / "vault")
    set_config(paths.root, {("mastery", "irt", "enabled"): False})
    _lesson_with_check(paths, repository, at=T)
    _cold(paths, repository, "pi_eig_1", T + timedelta(days=1), points=2, primed=True)
    outcome = _cold(paths, repository, "pi_eig_2", T + timedelta(days=2), points=4)
    vault = load_vault(paths.root)
    check, trajectory = _trajectory(repository, vault, outcome.attempt_id)
    assert trajectory is not None and [step.y for step in trajectory] == [1.0, 0.5]
    sensitivity = LW.CheckSensitivity.from_dict(check["inputs"]["sensitivity"])
    mass = float(check["mass_applied"])
    state = LW.trajectory_state(sensitivity, trajectory, mass=mass, recorded_mass=mass,
                                mastery_config=vault.config.mastery, frozen=True)
    recorded = repository.latest_attempt_surprise(outcome.attempt_id)["posterior_delta"]
    assert (state.logit_mean, state.logit_variance) == pytest.approx((recorded["mu_before"], recorded["P_before"]))
    # The check alone (the first-order form, at full reliability) is full credit too: it raises the mean, as the
    # live check did.
    mu, _variance = LW.posterior_after(sensitivity, mass, vault.config.mastery, frozen=True)
    check_delta = repository.latest_attempt_surprise(check["attempt_id"])["posterior_delta"]
    assert check_delta["mu_after"] > sensitivity.mu and mu > sensitivity.mu
