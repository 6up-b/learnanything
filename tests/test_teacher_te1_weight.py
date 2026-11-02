"""Teacher TE1: the learned lesson-check weight, the forecast pool and the tap/hedge recalibration
(spec_teacher_v1 §12.1, §12.2, §18.4; LP-min). DERIVED replay equivalence, filtering as of each check,
the one seam into mastery, and the report. Every model is a fake; no network.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import numpy as np
import pytest

from learnloop.attempts.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
from learnloop.clock import FrozenClock
from learnloop.learner import lesson_weight as LW
from learnloop.teacher import service as S
from learnloop.vault.loader import load_vault
from tests.teacher_fakes import TeacherFake, build_teacher_vault, check_turn, clients, landed_turn, plan_turn

T0 = datetime(2026, 11, 1, 9, 0, tzinfo=UTC)


def _rows(repository, sql, params=()):
    with repository.connection() as connection:
        return [tuple(row) for row in connection.execute(sql, params).fetchall()]


def _snapshot(repository):
    return {table: _rows(repository, f"SELECT * FROM {table} ORDER BY 1") for table in LW.DERIVED_TABLES}


def _lesson_with_check(paths, repository, *, at, retained: float | None = None, full: bool = True):
    turns = [plan_turn, check_turn()]
    fake = TeacherFake(turns, full=full)
    clock = FrozenClock(at)
    view = S.open_lesson(load_vault(paths.root), repository, entry="learning_object",
                         learning_object_ids=["lo_eigen"], clients=clients(fake), clock=clock)
    if retained is not None:
        # The teacher forecast the node's retention before the check opened (an earlier landing).
        fake.turns = [landed_turn(p=retained), check_turn()]
        S.take_turn(load_vault(paths.root), repository, lesson_id=view["lesson_id"], action="reply",
               payload={"text": "go"}, clients=clients(fake), clock=FrozenClock(at + timedelta(minutes=1)))
        S.take_turn(load_vault(paths.root), repository, lesson_id=view["lesson_id"], action="reply",
               payload={"text": "and?"}, clients=clients(fake), clock=FrozenClock(at + timedelta(minutes=2)))
    else:
        S.take_turn(load_vault(paths.root), repository, lesson_id=view["lesson_id"], action="reply",
               payload={"text": "go"}, clients=clients(fake), clock=FrozenClock(at + timedelta(minutes=2)))
    S.take_turn(load_vault(paths.root), repository, lesson_id=view["lesson_id"], action="answer_check",
           payload={"answer": "det(A - tI) = 0", "tap": 5}, clients=clients(fake),
           clock=FrozenClock(at + timedelta(minutes=3)))
    return view["lesson_id"]


def _cold(paths, repository, item_id, at, *, points: int = 4):
    complete_self_graded_attempt(
        load_vault(paths.root), repository,
        AttemptDraft(practice_item_id=item_id, learner_answer_md="cold answer", attempt_type="independent_attempt"),
        SelfGradeInput(criterion_points={"correctness": points}, confidence=4), clock=FrozenClock(at))


def test_the_tap_map_and_the_hedge_read_are_the_existing_ones():
    from learnloop.goals.exam_calibration import _ANSWER_CONFIDENCE_PROBABILITY

    assert dict(LW.TAP_PRIOR_MAP) == _ANSWER_CONFIDENCE_PROBABILITY


def test_the_hedge_reader_matches_confidence_events(tmp_path):
    from learnloop.confidence_events import read_hedges

    paths, repository = build_teacher_vault(tmp_path / "vault")
    _lesson_with_check(paths, repository, at=T0)
    with repository.connection() as connection:
        assert LW.read_hedges(connection) == read_hedges(connection)


def test_before_any_outcome_the_mass_is_the_seeded_prior_centre():
    state = LW.WeightState()
    mass = state.learned_mass("lo_x", 0.0, 0.0)
    assert 0.49 < mass < 0.51
    assert abs(state.pool_lambda("any") - 0.2) < 0.02  # Beta(1, 4)'s mean on the grid


def test_a_later_cold_outcome_resolves_the_check_and_moves_the_weight(tmp_path):
    paths, repository = build_teacher_vault(tmp_path / "vault")
    _lesson_with_check(paths, repository, at=T0)
    first_mass = _rows(repository, "SELECT mass_applied FROM lesson_checks")[0][0]
    # Two cold right answers on unseen lo_eigen items, days later.
    _cold(paths, repository, "pi_eig_2", T0 + timedelta(days=3))
    state = LW.replay_state(load_vault(paths.root), repository)
    assert state.updates == 1
    kinds = [entry["kind"] for entry in state.trace]
    assert kinds.count("mass") == 1 and kinds.count("weight_update") == 1
    update = next(entry for entry in state.trace if entry["kind"] == "weight_update")
    assert update["detail"]["mass_after"] != pytest.approx(update["detail"]["mass_before"], abs=1e-9)
    # A second lesson's check, after the outcome, is entered at the moved posterior (filtering).
    _lesson_with_check(paths, repository, at=T0 + timedelta(days=4))
    masses = [row[0] for row in _rows(repository, "SELECT mass_applied FROM lesson_checks ORDER BY created_at")]
    assert masses[0] == first_mass and masses[1] != pytest.approx(first_mass, abs=1e-9)
    assert LW.mass_mismatches(LW.replay_state(load_vault(paths.root), repository)) == []


def test_a_primed_or_hinted_or_seen_or_earlier_attempt_never_resolves_a_check(tmp_path):
    paths, repository = build_teacher_vault(tmp_path / "vault")
    _cold(paths, repository, "pi_eig_3", T0 - timedelta(days=1))  # before the check
    _lesson_with_check(paths, repository, at=T0)
    complete_self_graded_attempt(
        load_vault(paths.root), repository,
        AttemptDraft(practice_item_id="pi_eig_2", learner_answer_md="hinted", attempt_type="hinted_attempt",
                     hints_used=1),
        SelfGradeInput(criterion_points={"correctness": 4}, confidence=4), clock=FrozenClock(T0 + timedelta(days=2)))
    _cold(paths, repository, "pi_eig_3", T0 + timedelta(days=3))  # not the item's first attempt
    state = LW.replay_state(load_vault(paths.root), repository)
    assert state.updates == 0


def test_the_derived_state_rebuild_reproduces_the_live_tables_exactly(tmp_path):
    paths, repository = build_teacher_vault(tmp_path / "vault")
    _lesson_with_check(paths, repository, at=T0)
    _cold(paths, repository, "pi_eig_2", T0 + timedelta(days=3))
    _lesson_with_check(paths, repository, at=T0 + timedelta(days=4))
    live = _snapshot(repository)
    assert live["lesson_weight_state"] and live["lesson_weight_trace"] and live["confidence_calibration_state"]
    vault = load_vault(paths.root)
    with repository.atomic():
        LW.rebuild_lesson_weight_state(vault, repository)
    first = _snapshot(repository)
    with repository.atomic():
        LW.rebuild_lesson_weight_state(vault, repository)
    assert _snapshot(repository) == first
    # The live writer and the replayer agree on every row except the outcome folded after the
    # last live write (the live tables are refreshed at each check).
    assert first["lesson_weight_state"] == live["lesson_weight_state"]
    assert first["confidence_calibration_state"] == live["confidence_calibration_state"]


def test_a_lessonless_vault_rebuilds_to_empty_tables(tmp_path):
    paths, repository = build_teacher_vault(tmp_path / "vault")
    _cold(paths, repository, "pi_eig_2", T0)
    with repository.atomic():
        LW.rebuild_lesson_weight_state(load_vault(paths.root), repository)
    assert all(rows == [] for rows in _snapshot(repository).values())


def test_the_attempt_step_reads_the_recorded_mass_live_and_in_replay(tmp_path):
    from learnloop.substrate.replay import rebuild_derived_state

    paths, repository = build_teacher_vault(tmp_path / "vault")
    _lesson_with_check(paths, repository, at=T0)
    attempt_id, mass = _rows(repository, "SELECT attempt_id, mass_applied FROM lesson_checks")[0]
    assert LW.lesson_check_mass(repository, attempt_id, "reconstruction_after_walkthrough") == mass
    assert LW.lesson_check_mass(repository, attempt_id, "independent_attempt") is None
    before = _rows(repository, "SELECT learning_object_id, logit_mean, logit_variance FROM learning_object_mastery "
                               "WHERE learning_object_id = 'lo_eigen'")
    rebuild_derived_state(load_vault(paths.root), repository, learning_object_ids=["lo_eigen"])
    after = _rows(repository, "SELECT learning_object_id, logit_mean, logit_variance FROM learning_object_mastery "
                              "WHERE learning_object_id = 'lo_eigen'")
    assert after == before


def test_the_pool_mixes_in_the_teachers_forecast_and_learns_from_the_outcome(tmp_path):
    paths, repository = build_teacher_vault(tmp_path / "vault")
    _lesson_with_check(paths, repository, at=T0, retained=0.95)
    row = _rows(repository, "SELECT mass_applied, mass_learned, json_extract(weight_inputs_json, '$.rule'), "
                            "json_extract(weight_inputs_json, '$.pool.lambda') FROM lesson_checks")[0]
    assert row[2] == "pool" and abs(row[3] - 0.2) < 0.02
    assert 0.0 < row[0] < 1.0 and row[0] != pytest.approx(row[1], abs=1e-6)
    _cold(paths, repository, "pi_eig_2", T0 + timedelta(days=3), points=4)
    state = LW.replay_state(load_vault(paths.root), repository)
    families = list(state.pools)
    assert len(families) == 1 and state.pool_updates[families[0]] == 1
    assert state.pool_lambda(families[0]) > 0.2  # the forecast (0.95) predicted the right answer better


def test_parametric_source_drops_the_pool(tmp_path):
    from tests.ux_phase1_support import set_config

    paths, repository = build_teacher_vault(tmp_path / "vault")
    set_config(paths.root, {("teacher", "weight", "source"): "parametric"})
    _lesson_with_check(paths, repository, at=T0, retained=0.95)
    row = _rows(repository, "SELECT mass_applied, mass_learned, json_extract(weight_inputs_json, '$.rule') "
                            "FROM lesson_checks")[0]
    assert row[2] == "learned" and row[0] == row[1]


def test_the_pool_implied_mass_is_the_parametric_mass_at_lambda_zero():
    sensitivity = LW.CheckSensitivity(mu=0.0, variance=1.0, last_evidence_at=None, item_a=1.0, item_b=0.0,
                                      correctness=1.0, observed_at="2026-11-01T09:00:00Z")
    from learnloop.config.schema import MasteryConfig

    config = MasteryConfig()
    for mass in (0.2, 0.5, 0.8):
        mu, var = LW.posterior_after(sensitivity, mass, config)
        target = LW.predicted_success(mu, var, a=1.0, b=0.0)
        assert LW.pool_implied_mass(sensitivity, target, config) == pytest.approx(mass, abs=1e-6)


def test_planted_recovery_a_check_whose_cold_outcomes_agree_raises_the_mass():
    """Right checks followed by right cold outcomes favour a larger mass than wrong cold outcomes do."""

    from learnloop.config.schema import MasteryConfig

    config = MasteryConfig()

    def run(y_cold: float) -> float:
        state = LW.WeightState()
        for index in range(12):
            check = {"id": f"c{index}", "learning_object_id": f"lo{index % 3}", "inputs": {
                "z_c": 0.0, "z_p": 0.0, "sensitivity": LW.CheckSensitivity(
                    mu=-1.0, variance=1.5, last_evidence_at=None, item_a=1.0, item_b=0.0, correctness=1.0,
                    observed_at="2026-11-01T09:00:00Z").as_dict()}}
            outcome = {"id": f"o{index}", "correctness": y_cold, "created_at": "2026-11-03T09:00:00Z"}
            LW._resolve_check(state, check, outcome, 1.0, config)
        return state.learned_mass("lo0", 0.0, 0.0)

    assert run(1.0) > 0.5 > run(0.0)


def test_the_tap_recalibration_learns_from_every_tapped_graded_answer(tmp_path):
    paths, repository = build_teacher_vault(tmp_path / "vault")
    for index, item_id in enumerate(["pi_eig_1", "pi_eig_2", "pi_eig_3", "pi_det_1", "pi_det_2", "pi_eig_1"]):
        complete_self_graded_attempt(
            load_vault(paths.root), repository,
            AttemptDraft(practice_item_id=item_id, learner_answer_md="x", attempt_type="independent_attempt",
                         answer_confidence=5),
            SelfGradeInput(criterion_points={"correctness": 0}, confidence=5),
            clock=FrozenClock(T0 + timedelta(hours=index)))
    state = LW.replay_state(load_vault(paths.root), repository)
    assert state.tap.updates == 6
    assert state.tap_probability(5) < LW.TAP_PRIOR_MAP[5]  # sure and wrong, six times: less trusted


def test_the_report_lines(tmp_path):
    from learnloop.teacher.report import report

    paths, repository = build_teacher_vault(tmp_path / "vault")
    _lesson_with_check(paths, repository, at=T0)
    _cold(paths, repository, "pi_eig_2", T0 + timedelta(days=3))
    out = report(load_vault(paths.root), repository)
    assert out["resolved_checks"] == 1 and out["prequential_log_loss"]["n"] == 1
    assert set(out["contraction"]) == {"eta0", "beta_c", "beta_p"}
    sens = out["prior_sensitivity"]["eta0"]
    assert sens["minus_1sd"] < out["global_mass"] < sens["plus_1sd"]
    assert any(line.startswith("prequential log loss") for line in out["lines"])


def test_the_adf_quadrature_is_ads():
    from learnloop.adaptive_difficulty import model as M
    from learnloop.adf_numeric import NODES, WEIGHTS, gauss_hermite

    nodes, weights = gauss_hermite(32)
    assert np.array_equal(nodes, M.X32) and np.array_equal(weights, M.W32)
    assert np.array_equal(NODES, M.X32) and np.array_equal(WEIGHTS, M.W32)
