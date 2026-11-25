"""L4-2's review fix round (``docs/reviews/algorithm-mvp-0.72.md``, "Review fix round"): what the lesson-weight fit's
recomputation of mastery reads. Each test failed before its fix.

With ``mastery.irt.enabled = false`` mastery's logit-space update reads the score from the rubric fraction; the fit
passes the recorded score there too, so a full-credit check is full credit (L42-R10).

Mastery floors the variance after an update by the evidence's coverage. The recomputation applies each update's
recorded floor, and an update whose variance the floor set has no recoverable noise: its trajectory is labelled and
the fit takes its first-order form (L42-R7).

The recomputation starts from the state the check's update replayed from, so a regraded answer before the check
moves it as mastery moved; a transition the attempt updates do not carry (a re-anchoring claim inside the window)
leaves the recorded state unreproduced, and the trajectory is labelled instead of reported as complete (L42-R8).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from learnloop.algorithm_versions import FORECAST_SCORING_ALGORITHM_VERSION
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


def _weight_update(vault, repository):
    return next(entry for entry in LW.replay_state(vault, repository).trace if entry["kind"] == "weight_update")


def _floors(paths, value):
    set_config(paths.root, {("recall_coverage", "variance_floor_at_full_coverage"): value,
                            ("recall_coverage", "variance_floor_at_zero_coverage"): value})


def test_an_update_whose_variance_the_floor_set_is_labelled_not_recomputed(tmp_path):
    # Below mvp-0.75 (from it the noise is recorded and the update recomputed: ``test_lesson_weight_facts.py``).
    paths, repository = build_teacher_vault(tmp_path / "vault", version=FORECAST_SCORING_ALGORITHM_VERSION)
    _floors(paths, 2.5)  # above every posterior variance below: the floor sets each one
    _lesson_with_check(paths, repository, at=T)
    _cold(paths, repository, "pi_eig_2", T + timedelta(days=2), points=4)
    vault = load_vault(paths.root)
    update = _weight_update(vault, repository)
    assert update["detail"]["likelihood"] == "first_order"
    assert update["detail"]["trajectory_inputs"][0]["variance_floor_bound"] is True
    # The record's owner-copy label query counts it.
    with repository.atomic():
        LW.write_state(repository, LW.replay_state(vault, repository))
    likelihoods, labels, fallbacks = _owner_copy_label_queries()
    with repository.connection() as connection:
        assert [tuple(row) for row in connection.execute(likelihoods)] == [("first_order", 1)]
        assert [tuple(row) for row in connection.execute(labels)] == [("variance_floor_bound", 1)]
        assert [tuple(row) for row in connection.execute(fallbacks)] == []


def _owner_copy_label_queries() -> list[str]:
    """The record's owner-copy label query (three statements)."""

    from pathlib import Path

    record = (Path(__file__).resolve().parents[1] / "docs/reviews/algorithm-mvp-0.72.md").read_text()
    start = record.index("The successor's likelihoods, first-order labels")
    body = record[record.index("<<'SQL'\n", start) + len("<<'SQL'\n"):]
    return [statement.strip() for statement in body[:body.index("\nSQL\n")].split(";") if statement.strip()]


def test_the_recomputation_applies_the_recorded_floor_at_another_mass(tmp_path):
    paths, repository = build_teacher_vault(tmp_path / "vault")
    _floors(paths, 2.2)  # below the check's recorded variance, above it at full mass
    _lesson_with_check(paths, repository, at=T)
    outcome = _cold(paths, repository, "pi_eig_2", T + timedelta(days=2), points=4)
    vault = load_vault(paths.root)
    check, trajectory = _trajectory(repository, vault, outcome.attempt_id)
    assert trajectory is not None and len(trajectory) == 1
    sensitivity = LW.CheckSensitivity.from_dict(check["inputs"]["sensitivity"])
    recorded_mass = float(check["mass_applied"])
    assert recorded_mass < 1.0
    state = LW.trajectory_state(sensitivity, trajectory, mass=1.0, recorded_mass=recorded_mass,
                                mastery_config=vault.config.mastery, frozen=True)
    assert state.logit_variance == pytest.approx(2.2)
    assert _weight_update(vault, repository)["detail"]["likelihood"] == "recorded_trajectory"


def test_a_regraded_answer_before_the_check_moves_the_recomputations_start(tmp_path):
    from tests.regrade_contract_replay_helpers import _regrade

    paths, repository = build_teacher_vault(tmp_path / "vault")
    earlier = _cold(paths, repository, "pi_eig_3", T - timedelta(days=1), points=4)
    _lesson_with_check(paths, repository, at=T)
    outcome = _cold(paths, repository, "pi_eig_2", T + timedelta(days=2), points=4)
    _regrade(load_vault(paths.root), repository, earlier.attempt_id, {"correctness": 0}, when=T + timedelta(days=3))
    vault = load_vault(paths.root)
    check, trajectory = _trajectory(repository, vault, outcome.attempt_id)
    replayed = repository.latest_attempt_surprise(check["attempt_id"])["posterior_delta"]
    assert replayed["mu_before"] != check["inputs"]["sensitivity"]["mu"]
    assert trajectory is not None
    mass = float(check["mass_applied"])
    state = LW.trajectory_state(LW.CheckSensitivity.from_dict(check["inputs"]["sensitivity"]), trajectory,
                                mass=mass, recorded_mass=mass, mastery_config=vault.config.mastery, frozen=True)
    recorded = repository.latest_attempt_surprise(outcome.attempt_id)["posterior_delta"]
    assert (state.logit_mean, state.logit_variance) == pytest.approx((recorded["mu_before"], recorded["P_before"]))
    assert _weight_update(vault, repository)["detail"]["likelihood"] == "recorded_trajectory"


def test_a_reanchoring_claim_inside_the_window_is_labelled_not_recomputed(tmp_path):
    from learnloop.learner.mastery import reanchor_mastery_from_claim

    # Below mvp-0.75 (from it the chain of recorded states breaks: ``test_lesson_weight_facts.py``).
    paths, repository = build_teacher_vault(tmp_path / "vault", version=FORECAST_SCORING_ALGORITHM_VERSION)
    _lesson_with_check(paths, repository, at=T)
    stamp = (T + timedelta(days=1)).isoformat().replace("+00:00", "Z")
    claim_id = repository.insert_learner_claim({
        "claim_type": "self_rating", "scope_type": "learning_object", "scope_id": "lo_eigen",
        "evidence_family": "recall", "claimed_level": 0.9, "prior_pseudo_count": 2.0,
        "source": "tutor_gap_declaration", "created_at": stamp})
    reanchor_mastery_from_claim(load_vault(paths.root), repository, "lo_eigen", claimed_level=0.9,
                                prior_pseudo_count=2.0, now_iso=stamp, claim_id=claim_id)
    _cold(paths, repository, "pi_eig_2", T + timedelta(days=2), points=4)
    update = _weight_update(load_vault(paths.root), repository)
    assert update["detail"]["likelihood"] == "first_order"
    assert update["detail"]["trajectory_inputs"][-1]["outcome_prior_not_reproduced"] is True


def test_a_flat_response_keeps_the_learned_mass(tmp_path):
    """L42-R14: on an item with no discrimination (a = 0) every mass predicts the same success, so the pool's
    forecast says nothing about the mass. The check keeps its learned mass and records why, instead of the search's
    nearest end (almost no mass)."""

    from learnloop.teacher import checks as CK

    paths, repository = build_teacher_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    mass = CK.check_mass(vault, repository, learning_object_id="lo_eigen", tap=4, hedge=None, correctness=1.0,
                         item=vault.practice_items["pi_eig_1"], as_of="2026-11-01T09:00:00Z", p_teacher_retained=0.8,
                         family="doctrine_v1:fake", reference={"a": 0.0, "b": 0.0, "days": 1.0})
    assert mass["pool"]["lambda"] > 0.0
    assert mass["mass_applied"] == mass["mass_learned"]
    assert mass["pool"]["implied"] == "flat_response"
