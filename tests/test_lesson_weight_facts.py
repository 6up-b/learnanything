"""mvp-0.75: the lesson-weight fit reads what mastery recorded instead of inferring it
(``docs/reviews/algorithm-mvp-0.75.md``; design ``docs/reviews/refactor-l42-fit-redesign.md``).

Each test failed on the code before its fix (the second L4-2 review, ledger L42-R17 to L42-R25). Mastery records each
application's facts in the attempt's payload (``mastery.mastery_application_facts``), live and on replay; the fit
reads them through one reader (``lesson_weight.mastery_applications``) and every reader of a lesson outcome takes one
order (``lesson_weight.outcome_order``).
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

import pytest

from learnloop.algorithm_versions import FORECAST_SCORING_ALGORITHM_VERSION, LATEST_ALGORITHM_VERSION
from learnloop.clock import FrozenClock
from learnloop.learner import lesson_weight as LW
from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state
from learnloop.vault.loader import load_vault

from tests.lesson_weight_fit_helpers import apply_with_id as _apply
from tests.teacher_fakes import build_teacher_vault
from tests.teacher_te1_review_fixes_helpers import _cold, _lesson_with_check
from tests.ux_phase1_support import set_config

T = datetime(2026, 11, 1, 9, tzinfo=UTC)
#: Ids minted in this order (A before B) and applied in the other (B, then A).
A_ID, B_ID = "01ZZZZZZZZZZZZZZZZZZZZZZZA", "01ZZZZZZZZZZZZZZZZZZZZZZZB"


def _trace(vault, repository, kind="weight_update"):
    return [entry for entry in LW.replay_state(vault, repository).trace if entry["kind"] == kind]


def _mastery(repository):
    with repository.connection() as connection:
        return tuple(connection.execute(
            "SELECT logit_mean, logit_variance, last_evidence_at FROM learning_object_mastery "
            "WHERE learning_object_id = 'lo_eigen'").fetchone())


def test_a_grade_at_a_fractional_second_reads_the_same_live_and_after_a_rebuild(tmp_path):
    """L42-R17: live mastery observed at the subsecond clock while replay observes at the stored whole second, so a
    rebuild moved a live trajectory's drift interval (and the fit's likelihood)."""

    paths, repository = build_teacher_vault(tmp_path / "vault")
    _cold(paths, repository, "pi_eig_1", T, points=4)
    _cold(paths, repository, "pi_eig_2", T + timedelta(days=3, microseconds=900_000), points=0)
    live = _mastery(repository)
    rebuild_all_derived_state(load_vault(paths.root), repository)
    assert _mastery(repository) == live
    with repository.connection() as connection:
        (payload,) = connection.execute(
            "SELECT d.payload_json FROM attempt_debug_payloads d JOIN practice_attempts a ON a.id = d.attempt_id "
            "WHERE a.practice_item_id = 'pi_eig_2'").fetchone()
    assert json.loads(payload)["mastery_application"]["observed_at"] == "2026-11-04T09:00:00Z"


def test_a_check_is_stamped_under_the_writer_lock(tmp_path, monkeypatch):
    """L42-R18: the check stamped itself, then waited for the writer lock; an answer another process applied meanwhile
    in a later second was the check's prior and still resolved it."""

    from learnloop.teacher import service as S

    paths, repository = build_teacher_vault(tmp_path / "vault")
    committed: list[str] = []
    real = S._latest_forecast

    class Ticking:
        """The check's clock: the instant moves on once the other process's answer has committed."""

        def now(self):
            return T + timedelta(minutes=3, seconds=2 if committed else 0)

    def another_process_grades_first(state, kind, ref):
        if not committed:
            committed.append(_cold(paths, repository, "pi_eig_2", T + timedelta(minutes=3, seconds=1)).attempt_id)
        return real(state, kind, ref)

    from tests.teacher_fakes import TeacherFake, check_turn, clients, plan_turn

    fake = TeacherFake([plan_turn, check_turn()])
    view = S.open_lesson(load_vault(paths.root), repository, entry="learning_object", learning_object_ids=["lo_eigen"],
                         clients=clients(fake), clock=FrozenClock(T))
    S.take_turn(load_vault(paths.root), repository, lesson_id=view["lesson_id"], action="reply",
                payload={"text": "and?"}, clients=clients(fake), clock=FrozenClock(T + timedelta(minutes=2)))
    monkeypatch.setattr(S, "_latest_forecast", another_process_grades_first)
    S.take_turn(load_vault(paths.root), repository, lesson_id=view["lesson_id"], action="answer_check",
                payload={"answer": "det(A - tI) = 0", "tap": 5}, clients=clients(fake), clock=Ticking())
    with repository.connection() as connection:
        check_at, attempt_at = connection.execute(
            "SELECT c.created_at, a.created_at FROM lesson_checks c JOIN practice_attempts a ON a.id = c.attempt_id"
        ).fetchone()
    assert check_at == attempt_at == "2026-11-01T09:03:02Z"
    assert all(entry["resolving_attempt_id"] != committed[0] for entry in _trace(load_vault(paths.root), repository))


def test_every_reader_of_a_lesson_outcome_takes_the_fits_order(tmp_path):
    """L42-R19: the fit took the order mastery applied two first answers of one second in, while the retained-forecast
    report (and the router's miss-cause learning) took the legacy id order: one answer, two outcomes."""

    from learnloop.evsi_calibration import forecast_report as FR

    paths, repository = build_teacher_vault(tmp_path / "vault")
    _lesson_with_check(paths, repository, at=T, retained=0.8)
    when = T + timedelta(days=1)
    _apply(paths, repository, "pi_eig_2", 4, attempt_id=B_ID, when=when)
    _apply(paths, repository, "pi_eig_2", 0, attempt_id=A_ID, when=when)
    vault = load_vault(paths.root)
    fitted = _trace(vault, repository, "pool_update")[0]
    assert (fitted["resolving_attempt_id"], fitted["detail"]["y"]) == (B_ID, 1.0)
    with repository.connection() as connection:
        key, inputs, created = connection.execute(
            "SELECT receipt_key, inputs_json, created_at FROM forecast_receipts "
            "WHERE kind = 'lesson_step_retained'").fetchone()
        resolution = FR.resolve_lesson_step(FR._Ledgers(connection, vault),
                                            {"receipt_key": key, "inputs": json.loads(inputs), "created_at": created})
    assert (resolution["attempt_id"], resolution["emission"]) == (B_ID, FR._lesson_emission(1.0))
    # The router's miss-cause learning reads the same order; below the tag every reader but the fit kept the legacy.
    assert LW.outcome_order(LATEST_ALGORITHM_VERSION, fit=False) == LW.outcome_order(LATEST_ALGORITHM_VERSION, fit=True)
    assert LW.outcome_order(FORECAST_SCORING_ALGORITHM_VERSION, fit=False) == LW.LEGACY_ORDER


def _claim_inside_the_window(paths, repository):
    from learnloop.learner.mastery import reanchor_mastery_from_claim

    stamp = (T + timedelta(days=1)).isoformat().replace("+00:00", "Z")
    claim_id = repository.insert_learner_claim({
        "claim_type": "self_rating", "scope_type": "learning_object", "scope_id": "lo_eigen",
        "evidence_family": "recall", "claimed_level": 0.9, "prior_pseudo_count": 2.0,
        "source": "tutor_gap_declaration", "created_at": stamp})
    reanchor_mastery_from_claim(load_vault(paths.root), repository, "lo_eigen", claimed_level=0.9,
                                prior_pseudo_count=2.0, now_iso=stamp, claim_id=claim_id)


def _adjudicate_to_zero(paths, repository, attempt_id):
    """A ruling that the answer earned nothing, applied as the CLI applies it (its revision, then the LO's replay)."""

    from learnloop.attempts.grade_resolution import append_adjudication_evidence_revision
    from learnloop.substrate.replay import replay_learning_object

    vault = load_vault(paths.root)
    with repository.atomic():
        revision = append_adjudication_evidence_revision(
            repository, attempt_id=attempt_id, resolved_fraction=0, adjudication_id="adj_check",
            adjudicator_source="human", rationale=None, vault=vault)
        assert revision["status"] == "revised"
        replay_learning_object(vault, repository, "lo_eigen", applying_grade_to=attempt_id)
    assert repository.fetch_practice_attempt(attempt_id)["correctness"] == 0.0


def test_a_regraded_check_is_scored_with_its_current_grade_in_the_first_order_form(tmp_path):
    """L42-R20: the first-order form read the check's immutable sensitivity, so a check regraded from full credit to
    zero still entered the fit as a success."""

    paths, repository = build_teacher_vault(tmp_path / "vault")
    _lesson_with_check(paths, repository, at=T)
    _claim_inside_the_window(paths, repository)  # the trajectory is unavailable: the first-order form runs
    with repository.connection() as connection:
        (check_attempt,) = connection.execute("SELECT attempt_id FROM lesson_checks").fetchone()
    _adjudicate_to_zero(paths, repository, check_attempt)
    _cold(paths, repository, "pi_eig_2", T + timedelta(days=2), points=4)
    vault = load_vault(paths.root)
    (update,) = _trace(vault, repository)
    detail = update["detail"]
    assert detail["likelihood"] == "first_order"
    assert detail["first_order_inputs"]["correctness"] == 0.0
    # The prior is the state the check's update replayed from, as mastery recorded it.
    record = LW.mastery_applications(repository.connection(), [check_attempt])[check_attempt]
    assert (detail["first_order_inputs"]["mu"], detail["first_order_inputs"]["variance"]) == record.prior[:2]
    # Rebuilt, the same.
    rebuild_all_derived_state(vault, repository)
    assert _trace(load_vault(paths.root), repository)[0]["detail"] == detail


def _floors(paths, value):
    set_config(paths.root, {("recall_coverage", "variance_floor_at_full_coverage"): value,
                            ("recall_coverage", "variance_floor_at_zero_coverage"): value})


def test_a_floor_bound_update_at_the_cap_with_equal_numbers_is_applied(tmp_path):
    """L42-R21: at the mean cap and the variance floor, a full-credit answer leaves both numbers as they were, yet
    mastery applied it and advanced its evidence clock. The fit inferred "not applied" and drifted from the check."""

    paths, repository = build_teacher_vault(tmp_path / "vault")
    _floors(paths, 2.5)
    set_config(paths.root, {("mastery", "irt", "mu_abs_max"): 0.2})
    _lesson_with_check(paths, repository, at=T)
    middle = _cold(paths, repository, "pi_eig_1", T + timedelta(days=1), points=4)
    outcome = _cold(paths, repository, "pi_eig_2", T + timedelta(days=3), points=4)
    vault = load_vault(paths.root)
    with repository.connection() as connection:
        check = LW._checks(connection)[0]
        (middle_at,) = connection.execute("SELECT created_at FROM practice_attempts WHERE id = ?",
                                          (middle.attempt_id,)).fetchone()
        delta = json.loads(connection.execute("SELECT posterior_delta_json FROM attempt_surprise WHERE attempt_id = ?",
                                              (middle.attempt_id,)).fetchone()[0])
        assert (delta["mu_before"], delta["P_before"]) == (delta["mu_after"], delta["P_after"])
        trajectory = LW.recorded_trajectory(connection, vault, vault.config.mastery, check,
                                            {"id": outcome.attempt_id, "created_at": "2026-11-04T09:00:00Z"})
    assert trajectory is not None and [step.applied for step in trajectory] == [True, True]
    mass = float(check["mass_applied"])
    state = LW.trajectory_state(LW.CheckSensitivity.from_dict(check["inputs"]["sensitivity"]), trajectory, mass=mass,
                                recorded_mass=mass, mastery_config=vault.config.mastery, frozen=True)
    assert state.last_evidence_at == middle_at
    assert _trace(vault, repository)[0]["detail"]["likelihood"] == "recorded_trajectory"


def test_an_outcome_without_its_record_fails_closed(tmp_path):
    """L42-R22 (first half): with the outcome's prior gone the endpoint check passed and the trace claimed a recorded
    trajectory."""

    paths, repository = build_teacher_vault(tmp_path / "vault")
    _lesson_with_check(paths, repository, at=T)
    outcome = _cold(paths, repository, "pi_eig_2", T + timedelta(days=2), points=4)
    with repository.connection() as connection:
        connection.execute("DELETE FROM attempt_surprise WHERE attempt_id = ?", (outcome.attempt_id,))
        connection.execute("UPDATE attempt_debug_payloads SET payload_json = json_remove(payload_json, "
                           "'$.mastery_application') WHERE attempt_id = ?", (outcome.attempt_id,))
        connection.commit()
    (update,) = _trace(load_vault(paths.root), repository)
    assert update["detail"]["likelihood"] == "first_order"
    assert update["detail"]["trajectory_inputs"][-1]["outcome_record_missing"] is True


def test_a_resolver_whose_frozen_pair_differs_from_masterys_is_on_the_trace(tmp_path):
    """L42-R22 (second half): a resolver's own curve does not move its prior, so an endpoint-only disagreement between
    the frozen pair and the one mastery applied reproduced exactly and went unrecorded."""

    from tests.grade_curves_migration_helpers import forget_captures

    paths, repository = build_teacher_vault(tmp_path / "vault")
    _lesson_with_check(paths, repository, at=T, retained=0.8)
    outcome = _cold(paths, repository, "pi_eig_2", T + timedelta(days=2), points=4)
    with repository.connection() as connection:
        rows = connection.execute("SELECT * FROM attempt_grade_curves").fetchall()
    forget_captures(repository)
    with repository.connection() as connection:
        for row in rows:
            values = list(row)
            if values[0] == outcome.attempt_id:
                values[4] = 0.7  # the label's b, as a resolver captured before the retirement walked it
            connection.execute("INSERT INTO attempt_grade_curves VALUES (?, ?, ?, ?, ?, ?, ?)", values)
        connection.commit()
    vault = load_vault(paths.root)
    applied = LW.mastery_applications(repository.connection(), [outcome.attempt_id])[outcome.attempt_id]
    for kind in ("weight_update", "pool_update"):
        (update,) = _trace(vault, repository, kind)
        assert update["detail"]["resolving_input"]["item_b"] == 0.7
        assert update["detail"]["resolving_pair_differs_from_applied"] == [applied.item_a, applied.item_b]


def test_a_floor_bound_update_is_recomputed_from_its_recorded_noise(tmp_path):
    """The facts carry the interpretation noise, so an update whose variance the floor set (labelled and sent to the
    first-order form at mvp-0.72, L42-R7) is recomputed, and reproduces mastery at the recorded mass."""

    paths, repository = build_teacher_vault(tmp_path / "vault")
    _floors(paths, 2.5)
    _lesson_with_check(paths, repository, at=T)
    _cold(paths, repository, "pi_eig_2", T + timedelta(days=2), points=4)
    (update,) = _trace(load_vault(paths.root), repository)
    assert update["detail"]["likelihood"] == "recorded_trajectory"
    assert not any(key in entry for entry in update["detail"]["trajectory_inputs"]
                   for key in ("variance_floor_bound", "update_not_reproduced"))


@pytest.mark.parametrize("version", [FORECAST_SCORING_ALGORITHM_VERSION, LATEST_ALGORITHM_VERSION])
def test_a_reanchoring_claim_breaks_the_chain_on_both_sides_of_the_tag(tmp_path, version):
    paths, repository = build_teacher_vault(tmp_path / "vault", version=version)
    _lesson_with_check(paths, repository, at=T)
    _claim_inside_the_window(paths, repository)
    _cold(paths, repository, "pi_eig_2", T + timedelta(days=2), points=4)
    (update,) = _trace(load_vault(paths.root), repository)
    label = "outcome_prior_not_reproduced" if version == FORECAST_SCORING_ALGORITHM_VERSION else "outcome_chain_broken"
    assert update["detail"]["likelihood"] == "first_order"
    assert update["detail"]["trajectory_inputs"][-1][label] is True
