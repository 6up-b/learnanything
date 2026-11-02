"""Teacher TE1: the Codex review's findings, each reproduced first (spec_teacher_v1 §7, §9.3, §12.1, §12.2,
§13, §17; docs/reviews/teacher-te1-first-lesson-codex-review.md). Every model is a fake; no network.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest

from learnloop.clock import FrozenClock
from learnloop.learner import lesson_weight as LW
from learnloop.teacher import service as S
from learnloop.vault.loader import load_vault
from tests.teacher_fakes import (
    TeacherFake,
    build_teacher_vault,
    check_turn,
    clients,
    landed_turn,
    plan_turn,
)
from tests.ux_phase1_support import set_config

T0 = datetime(2026, 11, 1, 9, 0, tzinfo=UTC)
KEY = "quokka zebra marmot: two, five"


def _rows(repository, sql, params=()):
    with repository.connection() as connection:
        return [tuple(row) for row in connection.execute(sql, params).fetchall()]


def _open(tmp_path, turns, *, fake: TeacherFake | None = None, **kwargs):
    paths, repository = build_teacher_vault(tmp_path / "vault", **kwargs)
    fake = fake or TeacherFake(turns)
    view = S.open_lesson(load_vault(paths.root), repository, entry="learning_object", learning_object_ids=["lo_eigen"],
                         clients=clients(fake))
    return paths, repository, fake, view


def _turn(paths, repository, lesson_id, fake, action="reply", **payload):
    payload = payload or {"text": "go"}
    return S.take_turn(load_vault(paths.root), repository, lesson_id=lesson_id, action=action, payload=payload,
                       clients=clients(fake))


# --- F1: the per-lesson cap bounds every metered request ----------------------------------------------


class MeteredTeacher(TeacherFake):
    """A teacher and grader on a metered route: each physical request goes through ``model_call`` (the
    real providers' seam, where the request gate admits it) and reports no usage (its reservation stands)."""

    provider_name = "openrouter_test"
    provider_type = "fake"  # the settings gate stays open; the spend gate still meters it (not a subscription)

    def complete(self, request: Any) -> Any:
        from learnloop.ai.execution import model_call

        with model_call(self, purpose=request.purpose, prompt=request.prompt):
            return super().complete(request)

    def run_blind_grading_proposal(self, context: Any) -> Any:
        from learnloop.ai.execution import model_call

        with model_call(self, purpose="grading", prompt=json.dumps(str(context))):
            return super().run_blind_grading_proposal(context)


def _spend(repository):
    return [json.loads(row[0]) for row in _rows(
        repository, "SELECT p.payload_json FROM lesson_turns t JOIN lesson_turn_payloads p ON p.turn_id = t.id "
                    "WHERE t.action = 'spend' ORDER BY t.seq")]


def _metered(tmp_path, turns, *, cap_factor: float):
    """Open on a metered route with a price and no cap, then cap the lesson at what it spent plus
    ``cap_factor`` times the opening request's reservation."""

    paths, repository = build_teacher_vault(tmp_path / "vault")
    set_config(paths.root, {("teacher", "metered_price_per_million"): 1.0})
    fake = MeteredTeacher([{"message": "Welcome."}])
    view = S.open_lesson(load_vault(paths.root), repository, entry="learning_object", learning_object_ids=["lo_eigen"],
                         clients=clients(fake))
    first = _spend(repository)
    assert len(first) == 1 and first[0]["usd"] > 0
    spent = sum(row["usd"] for row in first)
    cap = spent + cap_factor * first[0]["estimated_usd"]
    set_config(paths.root, {("teacher", "max_lesson_cost_usd"): cap})
    fake.turns = list(turns)
    return paths, repository, fake, view["lesson_id"], cap


def test_f1_a_second_request_in_one_action_is_refused_when_it_would_pass_the_cap(tmp_path):
    reads = {"message": "Let me read.", "requests": [{"action": "read_source", "refs": ["ext_book/ch_det"]}]}
    paths, repository, fake, lesson_id, cap = _metered(tmp_path, [reads, {"message": "Read it."}], cap_factor=1.5)
    view = _turn(paths, repository, lesson_id, fake)
    # The follow-up call (same action) would have passed the cap: refused before it was sent; the lesson closed.
    assert view["closed"] and view["close_reason"] == "budget"
    spend = _spend(repository)
    assert len(spend) == 2 and sum(row["usd"] for row in spend) <= cap + 1e-12
    assert [p for purpose, p in fake.prompts if purpose == "teacher_turn"].__len__() == 2
    receipt = json.loads(_rows(repository, "SELECT receipt_json FROM lesson_receipts")[0][0])
    assert receipt["cost"]["metered_usd"] == pytest.approx(sum(row["usd"] for row in spend))


def test_f1_the_inline_grader_is_inside_the_lesson_envelope(tmp_path):
    paths, repository, fake, lesson_id, _cap = _metered(tmp_path, [check_turn()], cap_factor=10.0)
    view = _turn(paths, repository, lesson_id, fake)
    assert view["open_check"] is not None and not view["closed"]
    # Cap the lesson at exactly what it spent: the grader's request is refused before it is sent.
    cap = sum(row["usd"] for row in _spend(repository))
    set_config(paths.root, {("teacher", "max_lesson_cost_usd"): cap})
    view = _turn(paths, repository, lesson_id, fake, action="answer_check", answer="det(A - tI) = 0")
    assert view["closed"] and view["close_reason"] == "budget"
    assert not fake.grading_contexts and _rows(repository, "SELECT COUNT(*) FROM lesson_checks") == [(0,)]
    assert sum(row["usd"] for row in _spend(repository)) == pytest.approx(cap)


def test_f1_a_graded_check_spends_from_the_lesson_envelope(tmp_path):
    paths, repository, fake, lesson_id, _cap = _metered(tmp_path, [check_turn(), {"message": "Good."}],
                                                        cap_factor=100.0)
    _turn(paths, repository, lesson_id, fake)
    _turn(paths, repository, lesson_id, fake, action="answer_check", answer="det(A - tI) = 0")
    assert "grading" in {row["purpose"] for row in _spend(repository)}


# --- F3: plan statements and recaps pass the guards and are accounted ----------------------------------


def test_f3_a_key_in_a_plan_statement_or_a_recap_is_withheld(tmp_path):
    plan_leak = {"message": "", "requests": [{"action": "write_plan", "plan": [
        {"id": "n1", "statement": f"The answer is {KEY}.", "lo_id": "lo_eigen", "anchors": [], "premises": []}]}]}
    recap_leak = {"message": "", "requests": [{"action": "close", "close_reason": "goal_reached",
                                               "recap": f"Remember: {KEY}."}]}
    paths, repository, fake, view = _open(tmp_path, [plan_leak, recap_leak, {"message": "Let's begin."}])
    assert _rows(repository, "SELECT validation FROM lesson_turns WHERE actor = 'teacher' ORDER BY seq") == [
        ("withheld",), ("withheld",), ("ok",)]
    assert _rows(repository, "SELECT COUNT(*) FROM lesson_plans") == [(0,)]
    assert not view["closed"] and "quokka" not in json.dumps(view)


def test_f3_every_displayed_field_writes_reveal_rows(tmp_path):
    plan_only = {"message": "", "requests": [{"action": "write_plan", "plan": [
        {"id": "n1", "statement": "Picture a capybara walking two steps.", "lo_id": "lo_eigen", "anchors": [],
         "premises": []}]}]}
    paths, repository, fake, view = _open(tmp_path, [plan_only])
    rows = _rows(repository, "SELECT practice_item_id, source_kind FROM reveal_events WHERE amount > 0")
    assert ("pi_det_1", "tutor_answer") in rows


# --- F4: resumed lessons never resend material that became protected ----------------------------------


def test_f4_a_passage_held_out_after_delivery_is_never_resent_or_read_back(tmp_path):
    from tests.section_coverage_fixtures import hold_out

    reads = {"message": "Let me read.", "requests": [{"action": "read_source", "refs": ["ext_lay/lay_char"]}]}
    paths, repository, fake, view = _open(tmp_path, [reads, {"message": "Read it."}])
    delivered = fake.contexts[-1]["results"][0]["result"]["sections"][0]["passages"]
    alias = delivered[0]["alias"]
    assert "roots of the characteristic equation" in delivered[0]["text"]
    hold_out(repository, "lay_char")
    reread = {"message": "Again.", "requests": [{"action": "read_source", "refs": [alias]}]}
    fake.turns = [reread, {"message": "ok"}]
    _turn(paths, repository, view["lesson_id"], fake)
    later = [prompt for purpose, prompt in fake.prompts if purpose == "teacher_turn"][-2:]
    assert all("roots of the characteristic equation" not in prompt for prompt in later)
    result = fake.contexts[-1]["results"][0]["result"]["sections"][0]
    assert result.get("refused") and "passages" not in result


def test_f4_a_revoked_alias_cannot_be_cited(tmp_path):
    from tests.section_coverage_fixtures import hold_out

    reads = {"message": "Let me read.", "requests": [{"action": "read_source", "refs": ["ext_lay/lay_char"]}]}
    paths, repository, fake, view = _open(tmp_path, [reads, {"message": "Read it."}])
    alias = fake.contexts[-1]["results"][0]["result"]["sections"][0]["passages"][0]["alias"]
    hold_out(repository, "lay_char")
    fake.turns = [{"message": f"As the book says [{alias}]."}, {"message": "Fine."}]
    _turn(paths, repository, view["lesson_id"], fake)
    assert "unknown_citation" in str(_rows(repository, "SELECT payload_json FROM lesson_turn_payloads"))


# --- F7: delayed checks never reuse the lesson's material ---------------------------------------------


def _close_after_check(tmp_path, *, question: str, family: dict[str, str] | None = None):
    from learnloop.vault.yaml_io import read_yaml, write_yaml

    paths, repository = build_teacher_vault(tmp_path / "vault")
    for item_id, family_id in (family or {}).items():
        path = paths.practice_item_path("linear-algebra", item_id)
        data = read_yaml(path)
        data.update({"family_id": family_id, "variant_relation": "isomorph"})
        write_yaml(path, data)
    turn = check_turn()
    turn["check"]["question"] = question
    fake = TeacherFake([plan_turn, turn])
    view = S.open_lesson(load_vault(paths.root), repository, entry="learning_object", learning_object_ids=["lo_eigen"],
                         clients=clients(fake))
    _turn(paths, repository, view["lesson_id"], fake)
    fake.turns = [{"message": "Landed.", "requests": [
        {"action": "forecast", "forecast_kind": "lesson_step_retained", "node": "n1", "p": 0.7},
        {"action": "close", "close_reason": "goal_reached", "recap": "Retrieve the characteristic equation."}]}]
    _turn(paths, repository, view["lesson_id"], fake, action="answer_check", answer="det(A - tI) = 0")
    receipt = json.loads(_rows(repository, "SELECT receipt_json FROM lesson_receipts")[0][0])
    return receipt


def test_f7_a_vault_question_reused_as_a_check_is_never_the_cold_check(tmp_path):
    receipt = _close_after_check(tmp_path, question="Find the eigenvalues of [[2,0],[0,5]].")
    picked = {check["item_id"] for check in receipt["delayed_checks"]}
    assert "pi_eig_1" in receipt["exposure"]["shown_items"]
    assert "pi_eig_1" not in picked


def test_f7_a_sibling_of_a_shown_item_is_never_the_cold_check(tmp_path):
    receipt = _close_after_check(tmp_path, question="Find the eigenvalues of [[2,0],[0,5]].",
                                 family={"pi_eig_1": "fam_diag", "pi_eig_2": "fam_diag"})
    picked = {check["item_id"] for check in receipt["delayed_checks"]}
    assert not picked & {"pi_eig_1", "pi_eig_2"}


# --- F8: transfer only where the relation is established ----------------------------------------------


def test_f8_a_downstream_edge_alone_is_not_transfer(tmp_path):
    from learnloop.teacher import delayed as D

    paths, repository = build_teacher_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    assert "lo_eigen" in D.downstream_learning_objects(vault, ["lo_det"])
    out, warnings = D.commit_checks(vault, repository, lesson_id="les_x", landed=[{"id": "n1", "lo_id": "lo_det"}],
                                    goal_learning_object_ids=["lo_det"], lesson_items_by_lo={}, shown_items=[],
                                    clock=FrozenClock(T0))
    transfer = next(check for check in out if check["purpose"] == "transfer")
    # lo_eigen depends on lo_det, but no lo_eigen item's rubric measures a facet lo_det teaches, and no lo_det
    # item records a presentation: transfer is reported unavailable, not filled by a look-alike.
    assert transfer["item_id"] is None and transfer.get("missing")
    assert any("transfer" in warning for warning in warnings)


def test_f8_a_downstream_item_whose_rubric_measures_a_taught_facet_is_transfer(tmp_path, monkeypatch):
    from learnloop.teacher import delayed as D

    paths, repository = build_teacher_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    item = vault.practice_items["pi_eig_3"]
    monkeypatch.setattr(item, "evidence_facets", ["f_det_rows"])
    monkeypatch.setattr(D, "taught_facets", lambda _vault, los: {"f_det_rows"} if "lo_det" in los else set())
    out, _warnings = D.commit_checks(vault, repository, lesson_id="les_x", landed=[{"id": "n1", "lo_id": "lo_det"}],
                                     goal_learning_object_ids=["lo_det"], lesson_items_by_lo={}, shown_items=[],
                                     clock=FrozenClock(T0))
    transfer = next(check for check in out if check["purpose"] == "transfer")
    assert transfer["item_id"] == "pi_eig_3"


# --- F9: accepted turns recover across an interruption ------------------------------------------------


def test_f9_an_accepted_check_turn_interrupted_before_its_effects_recovers_on_reload(tmp_path, monkeypatch):
    paths, repository, fake, view = _open(tmp_path, [plan_turn, check_turn()])
    real = S._execute
    calls = {"n": 0}

    def dies(*args, **kwargs):
        calls["n"] += 1
        raise KeyboardInterrupt("the process died")

    monkeypatch.setattr(S, "_execute", dies)
    with pytest.raises(KeyboardInterrupt):
        _turn(paths, repository, view["lesson_id"], fake)
    monkeypatch.setattr(S, "_execute", real)
    accepted = _rows(repository, "SELECT COUNT(*) FROM lesson_turns WHERE action = 'teacher_turn' AND validation = 'ok'")
    assert accepted == [(2,)] and _rows(repository, "SELECT COUNT(*) FROM lesson_turns WHERE action = 'pose_check'") \
        == [(0,)]
    reloaded = S.view_lesson(load_vault(paths.root), repository, view["lesson_id"])
    assert reloaded["open_check"] is not None
    assert _rows(repository, "SELECT COUNT(*) FROM lesson_turns WHERE action = 'pose_check'") == [(1,)]
    # Idempotent: a second reload runs nothing again.
    S.view_lesson(load_vault(paths.root), repository, view["lesson_id"])
    assert _rows(repository, "SELECT COUNT(*) FROM lesson_turns WHERE action = 'pose_check'") == [(1,)]
    forecasts = _rows(repository, "SELECT COUNT(*) FROM forecast_receipts WHERE kind = 'lesson_check_correct'")
    assert forecasts == [(1,)]


def test_f9_closing_is_one_transaction_and_an_interrupted_close_recovers(tmp_path, monkeypatch):
    close = {"message": "Done.", "requests": [{"action": "close", "close_reason": "goal_reached", "recap": "Recall it."}]}
    paths, repository, fake, view = _open(tmp_path, [plan_turn, close])
    real = S._append

    def dies(repository_, state, *, action, **kwargs):
        if action == "close":
            raise KeyboardInterrupt("the process died")
        return real(repository_, state, action=action, **kwargs)

    monkeypatch.setattr(S, "_append", dies)
    with pytest.raises(KeyboardInterrupt):
        _turn(paths, repository, view["lesson_id"], fake)
    monkeypatch.setattr(S, "_append", real)
    # Never a closed row without its close entry: nothing of the close was kept.
    assert _rows(repository, "SELECT closed_at FROM lessons") == [(None,)]
    assert _rows(repository, "SELECT COUNT(*) FROM lesson_receipts") == [(0,)]
    reloaded = S.view_lesson(load_vault(paths.root), repository, view["lesson_id"])
    assert reloaded["closed"] and reloaded["feed"][-1]["kind"] == "close"
    assert _rows(repository, "SELECT COUNT(*) FROM lesson_receipts") == [(1,)]


# --- F10: deferred results survive an outage ----------------------------------------------------------


def test_f10_deferred_read_results_are_kept_until_a_turn_consumes_them(tmp_path):
    from learnloop.ai.errors import AIProviderUnavailable

    first = {"message": "Let me read.", "requests": [{"action": "read_source", "refs": ["ext_book/ch_det"]}]}
    second = {"message": "And one more.", "requests": [{"action": "read_source", "refs": ["ext_lay/lay_char"]}]}
    paths, repository, fake, view = _open(tmp_path, [first, second])

    def down(_context):
        raise AIProviderUnavailable("the plan is down")

    fake.turns = [down]
    with pytest.raises(S.LessonError) as raised:
        _turn(paths, repository, view["lesson_id"], fake)
    assert raised.value.code == "plan_unavailable"
    fake.turns = [{"message": "Back."}, {"message": "And again."}]
    _turn(paths, repository, view["lesson_id"], fake, text="are you there?")
    results = fake.contexts[-1]["results"]
    assert results and results[0]["action"] == "read_source"
    assert "roots of the characteristic equation" in json.dumps(results)
    # Delivered once, then it stays in the transcript for every later call.
    _turn(paths, repository, view["lesson_id"], fake, text="next")
    assert not fake.contexts[-1]["results"]
    assert "roots of the characteristic equation" in json.dumps(fake.contexts[-1]["transcript"])


# --- F11: an opening failure leaves a resumable lesson ------------------------------------------------


def test_f11_an_opening_failure_carries_the_saved_lesson_and_resume_runs_it(tmp_path):
    from learnloop.ai.errors import AIProviderUnavailable

    def down(_context):
        raise AIProviderUnavailable("the plan is down")

    paths, repository = build_teacher_vault(tmp_path / "vault")
    fake = TeacherFake([down])
    with pytest.raises(S.LessonError) as raised:
        S.open_lesson(load_vault(paths.root), repository, entry="learning_object", learning_object_ids=["lo_eigen"],
                      clients=clients(fake))
    lesson_id = raised.value.details["lesson_id"]
    assert _rows(repository, "SELECT id FROM lessons") == [(lesson_id,)]
    fake.turns = [{"message": "Hello again."}]
    view = _turn(paths, repository, lesson_id, fake, action="resume", text=None)
    assert view["feed"][0]["text"] == "Hello again."
    # Nothing waits any more: resume makes no call.
    calls = len(fake.prompts)
    _turn(paths, repository, lesson_id, fake, action="resume", text=None)
    assert len(fake.prompts) == calls


def test_f11_the_sidecar_error_carries_the_lesson_id():
    from learnloop_sidecar.handlers.lesson import _error

    error = _error(S.LessonError("plan_unavailable", "down", details={"lesson_id": "les_1"}))
    assert error.retryable and error.details == {"lesson_id": "les_1"}


# --- F12: provider schema failures are contract refusals ----------------------------------------------


def test_f12_three_provider_invalid_outputs_close_the_lesson_as_a_contract_failure(tmp_path):
    from learnloop.ai.errors import AIInvalidOutput

    def invalid(_context):
        raise AIInvalidOutput("TeacherTurnV1 did not validate after repair")

    paths, repository, fake, view = _open(tmp_path, [invalid, invalid, invalid])
    assert view["closed"] and view["close_reason"] == "teacher_contract_failure"
    assert _rows(repository, "SELECT validation FROM lesson_turns WHERE action = 'teacher_turn'") == [
        ("invalid",)] * 3


# --- F2: held grades never train the weight, the pool or the recalibration -----------------------------


def _lesson_with_check(paths, repository, *, at, retained: float | None = None):
    fake = TeacherFake([plan_turn, check_turn()])
    view = S.open_lesson(load_vault(paths.root), repository, entry="learning_object", learning_object_ids=["lo_eigen"],
                         clients=clients(fake), clock=FrozenClock(at))
    if retained is not None:
        fake.turns = [landed_turn(p=retained), check_turn()]
        S.take_turn(load_vault(paths.root), repository, lesson_id=view["lesson_id"], action="reply",
                    payload={"text": "go"}, clients=clients(fake), clock=FrozenClock(at + timedelta(minutes=1)))
    S.take_turn(load_vault(paths.root), repository, lesson_id=view["lesson_id"], action="reply",
                payload={"text": "and?"}, clients=clients(fake), clock=FrozenClock(at + timedelta(minutes=2)))
    S.take_turn(load_vault(paths.root), repository, lesson_id=view["lesson_id"], action="answer_check",
                payload={"answer": "det(A - tI) = 0", "tap": 5}, clients=clients(fake),
                clock=FrozenClock(at + timedelta(minutes=3)))
    return view["lesson_id"]


def _cold(paths, repository, item_id, at, *, points: int = 4, confidence: int | None = 4, hints: int = 0):
    from learnloop.attempts.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt

    return complete_self_graded_attempt(
        load_vault(paths.root), repository,
        AttemptDraft(practice_item_id=item_id, learner_answer_md="cold answer",
                     attempt_type="hinted_attempt" if hints else "independent_attempt", hints_used=hints,
                     answer_confidence=confidence),
        SelfGradeInput(criterion_points={"correctness": points}, confidence=4), clock=FrozenClock(at))


def test_f2_a_held_cold_grade_resolves_nothing_until_released(tmp_path):
    from learnloop.attempts.grade_resolution import append_adjudication_evidence_revision
    from tests.test_held_grade_evidence import _hold_by_regrade

    paths, repository = build_teacher_vault(tmp_path / "vault")
    _lesson_with_check(paths, repository, at=T0, retained=0.9)
    cold = _cold(paths, repository, "pi_eig_2", T0 + timedelta(days=3), confidence=5)
    vault = load_vault(paths.root)
    _hold_by_regrade(vault, repository, cold.attempt_id, T0 + timedelta(days=3, hours=1))
    held = LW.replay_state(vault, repository)
    assert held.updates == 0 and not held.pool_updates
    with repository.connection() as connection:
        assert all(o["id"] != cold.attempt_id for o in LW.qualifying_outcomes(connection, ["lo_eigen"], "2026-01-01"))
        calibration = LW._calibration_attempts(connection, LW.read_hedges(connection), None)
    assert cold.attempt_id not in {row["id"] for row in calibration}
    append_adjudication_evidence_revision(
        repository, attempt_id=cold.attempt_id, resolved_fraction=1.0, adjudication_id="adj-te1-f2",
        adjudicator_source="human_owner", rationale="valid", vault=vault,
        clock=FrozenClock(T0 + timedelta(days=3, hours=2)))
    released = LW.replay_state(load_vault(paths.root), repository)
    assert released.updates == 1 and sum(released.pool_updates.values()) == 1


# --- F5: the pool compares both predictors on the same cold item and horizon ---------------------------


def test_f5_the_pool_inverts_on_the_committed_cold_item_not_the_check(tmp_path):
    paths, repository = build_teacher_vault(tmp_path / "vault")
    _lesson_with_check(paths, repository, at=T0, retained=0.3)
    inputs = json.loads(_rows(repository, "SELECT weight_inputs_json FROM lesson_checks")[0][0])
    pool, sensitivity = inputs["pool"], LW.CheckSensitivity.from_dict(inputs["sensitivity"])
    assert 1e-4 < inputs["mass_applied"] < inputs["mass_learned"]  # a pessimistic forecast, within reach
    reference = pool["reference"]
    assert reference["item_id"] and reference["item_id"].startswith("pi_eig")
    vault = load_vault(paths.root)
    config = vault.config.mastery
    # The applied mass makes the predicted success on the reference item at the horizon equal the pool target.
    mu, var = LW.posterior_after(sensitivity, inputs["mass_applied"], config)
    p_ref = LW.predicted_success(mu, var, a=reference["a"], b=reference["b"], drift=config.sigma2_drift,
                                 days=reference["days"])
    assert p_ref == pytest.approx(pool["target"], abs=1e-6)
    # At λ = 0 the pool would apply exactly §12.1's mass: p_A is computed for the same item and horizon.
    mu_l, var_l = LW.posterior_after(sensitivity, inputs["mass_learned"], config)
    assert pool["p_a"] == pytest.approx(LW.predicted_success(mu_l, var_l, a=reference["a"], b=reference["b"],
                                                             drift=config.sigma2_drift, days=reference["days"]))


def test_f5_a_forecast_agreeing_with_the_cold_prediction_leaves_the_mass_near_the_learned_one(tmp_path):
    """The review's probe: an easy check item and a harder cold item. A teacher forecast equal to the
    mastery prediction for the cold item must not drive the mass to the search bound."""

    from learnloop.config.schema import MasteryConfig

    config = MasteryConfig()
    sensitivity = LW.CheckSensitivity(mu=1.0, variance=1.0, last_evidence_at=None, item_a=1.5, item_b=-2.0,
                                      correctness=1.0, observed_at="2026-11-01T09:00:00Z")
    learned, cold_a, cold_b, days = 0.5, 1.0, 0.5, 3.0
    mu, var = LW.posterior_after(sensitivity, learned, config)
    p_check = LW.predicted_success(mu, var, a=sensitivity.item_a, b=sensitivity.item_b)
    p_cold = LW.predicted_success(mu, var, a=cold_a, b=cold_b, drift=config.sigma2_drift, days=days)
    assert p_check > p_cold + 0.1
    target = 0.2 * p_cold + 0.8 * p_cold  # the teacher agrees with the cold prediction
    mass = LW.pool_implied_mass(sensitivity, target, config, a=cold_a, b=cold_b, days=days)
    assert mass == pytest.approx(learned, abs=1e-6)


# --- F6: the likelihood recomputes the LO's recorded trajectory ----------------------------------------


def test_f6_the_trajectory_at_the_recorded_mass_reproduces_the_outcomes_recorded_prior(tmp_path):
    paths, repository = build_teacher_vault(tmp_path / "vault")
    _lesson_with_check(paths, repository, at=T0)
    # Two intervening updates on the same LO that resolve nothing: an item the lesson's teaching exposed
    # (a reveal row), and a hinted attempt (its own observation factors: the hint dampening).
    _cold(paths, repository, "pi_eig_3", T0 + timedelta(days=1), points=0)
    _cold(paths, repository, "pi_eig_1", T0 + timedelta(days=2), points=4, hints=1)
    outcome = _cold(paths, repository, "pi_eig_2", T0 + timedelta(days=4), points=4)
    vault = load_vault(paths.root)
    with repository.connection() as connection:
        check = LW._checks(connection)[0]
        outcome_row = {"id": outcome.attempt_id, "created_at": connection.execute(
            "SELECT created_at FROM practice_attempts WHERE id = ?", (outcome.attempt_id,)).fetchone()[0]}
        trajectory = LW.recorded_trajectory(connection, vault, vault.config.mastery, check, outcome_row)
    assert trajectory is not None and [u.varied for u in trajectory] == [True, False, False]
    recorded = repository.latest_attempt_surprise(outcome.attempt_id)["posterior_delta"]
    sensitivity = LW.CheckSensitivity.from_dict(check["inputs"]["sensitivity"])
    state = LW.trajectory_state(sensitivity, trajectory, mass=float(check["mass_applied"]),
                                recorded_mass=float(check["mass_applied"]), mastery_config=vault.config.mastery)
    assert state.logit_mean == pytest.approx(recorded["mu_before"], abs=1e-6)
    assert state.logit_variance == pytest.approx(recorded["P_before"], abs=1e-6)
    # The live replay resolves the check through that trajectory, intervening updates included.
    replay = LW.replay_state(vault, repository)
    update = next(entry for entry in replay.trace if entry["kind"] == "weight_update")
    assert update["detail"]["likelihood"] == "recorded_trajectory" and update["detail"]["intervening"] == 2


# --- F13: check-correctness forecasts resolve on the check's attempt -----------------------------------


def test_f13_lesson_forecasts_have_resolvers(tmp_path):
    from learnloop.evsi_calibration.forecast_report import resolved_receipts

    paths, repository = build_teacher_vault(tmp_path / "vault")
    _lesson_with_check(paths, repository, at=T0, retained=0.8)
    rows = {receipt["kind"]: resolution for receipt, resolution in resolved_receipts(load_vault(paths.root))
            if receipt["kind"].startswith("lesson_")}
    assert rows["lesson_check_correct"]["state"] == "resolved"
    assert rows["lesson_check_correct"]["emission"] == "success"
    assert rows["lesson_step_retained"]["state"] == "pending"
    _cold(paths, repository, "pi_eig_2", T0 + timedelta(days=3), points=0)
    rows = {receipt["kind"]: resolution for receipt, resolution in resolved_receipts(load_vault(paths.root))
            if receipt["kind"].startswith("lesson_")}
    assert rows["lesson_step_retained"]["state"] == "resolved"
    assert rows["lesson_step_retained"]["emission"] == "failure"


def test_f13_a_withdrawn_check_censors_its_forecast(tmp_path):
    from learnloop.evsi_calibration.forecast_report import resolved_receipts

    paths, repository, fake, view = _open(tmp_path, [plan_turn, check_turn(solution="the roots of det(A - tI) = 0")])
    _turn(paths, repository, view["lesson_id"], fake)
    fake.turns = [{"message": "Here it is: the roots of det(A - tI) = 0."}]
    _turn(paths, repository, view["lesson_id"], fake, text="help?")
    rows = [resolution for receipt, resolution in resolved_receipts(load_vault(paths.root))
            if receipt["kind"] == "lesson_check_correct"]
    assert rows and rows[0]["state"] == "censored" and rows[0]["reason"] == "check_withdrawn"
