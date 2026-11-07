"""Mobile v2 stage V2, the Codex review's findings (docs/reviews/phone-v2-codex-review.md), reproduced.

* F1: a phone's plan write that names no open session (none, an unknown one, an ended one) is refused
  while the desktop owns the open session; with no open session, its pre-session minutes chip works.
* F2: ``plan_learner_pick`` is a serving door: the phone's pick of an item its step filter holds is
  refused before anything is served or written.
* F4: a stop the chooser draws at a phone boundary while work it left for the desktop is open is that
  stop, logged once; the held work stays the desktop's next Next, and the plan closes on that stop
  afterwards with no second draw.
* F5: the serve of the day's randomized check says ``noHelp`` to the phone, so a question restored from
  a checkpoint is as cold as the step that opened it; the desktop's serve is unchanged.
* F6: a desktop step whose session the phone adopted during its slow work commits nothing.

F3 (the follow-up panel through the real phone handlers) is in ``tests/test_mobile_v2_followup.py``.
No model and no network.
"""

from __future__ import annotations

import json
from dataclasses import replace

import pytest

pytest.importorskip("starlette")

from learnloop.daily_plan import engine
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.request_origin import RequestOrigin

from tests.mobile_host_helpers import rows
from tests.test_mobile_v2_plan import HELD, _call, _desktop, _dont_know, _next, plan_world  # noqa: F401


def _desktop_session(paths):
    ctx = _desktop(paths.root)
    return ctx, _call(ctx, "start_session", {"availableMinutes": 25})["sessionId"]


# -- F1 ---------------------------------------------------------------------------------------------


def test_f1_a_phone_write_naming_no_open_session_is_refused_while_the_desktop_owns_one(plan_world):
    phone, _host, repository, paths = plan_world
    _ctx, desktop_session = _desktop_session(paths)
    plan_before = rows(repository, "SELECT id, status FROM daily_plans")
    ended = "sess_no_such_session"
    for name, params in (
        ("plan_keep_going", {"stop": True}),
        ("plan_keep_going", {"sessionId": ended, "stop": True}),
        ("next_plan_item", {"skipPracticeItemId": "pi_b1"}),
        ("set_plan_minutes", {"minutes": 40}),
        ("plan_reading_ended", {"outcome": "skipped"}),
        ("plan_learner_pick", {"practiceItemId": "pi_b2"}),
    ):
        status, error = phone.error(name, params, request_id=f"key_{name}" if name == "next_plan_item" else None)
        assert (status, error["code"]) == (409, "session_moved"), name
        assert error["details"]["session_id"] == desktop_session, name
    # Nothing moved: the desktop's plan is as it was.
    assert rows(repository, "SELECT id, status FROM daily_plans") == plan_before


def test_f1_with_no_session_open_the_phones_minutes_chip_goes_through(plan_world):
    phone, _host, _repository, _paths = plan_world
    reply = phone.rpc("set_plan_minutes", {"minutes": 40})
    assert reply["enabled"] is True and reply["plan"]["minutesBudget"] == 40


def test_f1_the_desktops_sessionless_write_answers_as_before(plan_world):
    phone, _host, _repository, paths = plan_world
    phone.start()
    # A None origin keeps what it did before: no new refusal for a write naming no session.
    assert _call(_desktop(paths.root), "set_plan_minutes", {"minutes": 30})["enabled"] is True


# -- F2 ---------------------------------------------------------------------------------------------


def test_f2_the_phones_pick_of_a_held_item_is_refused_before_anything_is_served(plan_world):
    phone, _host, repository, _paths = plan_world
    session_id = phone.start()["sessionId"]
    phone.rpc("get_daily_plan", {"sessionId": session_id})
    served_before = rows(repository, "SELECT id FROM attention_block_events WHERE kind = 'item_served'")
    blocks_before = rows(repository, "SELECT id FROM attention_blocks")
    status, error = phone.error("plan_learner_pick", {"sessionId": session_id, "practiceItemId": HELD})
    assert (status, error["code"]) == (409, "desktop_only")
    assert error["details"]["practice_item_id"] == HELD
    assert rows(repository, "SELECT id FROM attention_block_events WHERE kind = 'item_served'") == served_before
    assert rows(repository, "SELECT id FROM attention_blocks") == blocks_before
    # An item the phone can show is still picked.
    assert phone.rpc("plan_learner_pick", {"sessionId": session_id, "practiceItemId": "pi_b2"})["step"]["kind"] == "item"


def test_f2_the_desktops_pick_of_the_same_item_is_served(plan_world):
    _phone, _host, _repository, paths = plan_world
    ctx, session_id = _desktop_session(paths)
    step = _call(ctx, "plan_learner_pick", {"sessionId": session_id, "practiceItemId": HELD})["step"]
    assert step["kind"] == "item" and step["practiceItemId"] == HELD


# -- F4 ---------------------------------------------------------------------------------------------


def _stop_past_held_work(monkeypatch):
    """The chooser draws a stop (with its propensity) at any boundary crossed while a block is open:
    only a device's step crosses one then."""

    real = engine.decide
    drawn = []

    def decide(record, context, policy, **kwargs):
        decision = real(record, context, policy, **kwargs)
        if record.current_block() is None or not decision.feasible:
            return decision
        drawn.append(record.id)
        stop = replace(decision.choice, candidate_id=engine.STOP_FOR_TODAY, propensity=0.25,
                       why="a forced stop at the phone's boundary")
        return replace(decision, choice=stop, candidate=None, stop_offered=True)

    monkeypatch.setattr(engine, "decide", decide)
    return drawn


def _stops(repository):
    return [json.loads(row["detail_json"]) for row in rows(
        repository, "SELECT detail_json FROM attention_block_events WHERE kind = 'block_chosen'")
        if json.loads(row["detail_json"]).get("stop_reason")]


def test_f4_a_stop_drawn_past_held_work_keeps_that_work_for_the_desktop_and_closes_after_it(plan_world, monkeypatch):
    phone, _host, repository, paths = plan_world
    drawn = _stop_past_held_work(monkeypatch)
    session_id = phone.start()["sessionId"]
    steps = []
    for index in range(12):
        reply = _next(phone, session_id, f"f4_next_{index}")
        steps.append(reply)
        step = reply["step"]
        if step is None or step["kind"] != "item":
            break
        _dont_know(phone, session_id, step, f"f4_dk_{index}")
    if not drawn:
        pytest.skip("the phone never crossed a boundary past held work")  # pragma: no cover
    last = steps[-1]
    # The stop is logged once, with its probability, and the plan is not closed by it yet.
    stops = _stops(repository)
    assert len(stops) == 1 and stops[0]["propensity"] == 0.25
    assert last["step"]["kind"] == engine.DEVICE_HELD_STEP and last["plan"]["status"] == "open"
    assert stops[0][engine.STOP_AFTER_HELD] == {"replans": 0}
    # The phone's next Next decides nothing again (the view's projections call the chooser too, so
    # the stop receipts and the decision rows are what count).
    decisions_at_stop = rows(repository, "SELECT id FROM router_decisions WHERE decision_kind = 'plan_block'")
    again = _next(phone, session_id, "f4_again")
    assert again["step"]["kind"] == engine.DEVICE_HELD_STEP and len(_stops(repository)) == 1
    assert rows(repository, "SELECT id FROM router_decisions WHERE decision_kind = 'plan_block'") == decisions_at_stop
    # The desktop takes the session back: its Next serves the held item, then the plan closes on that stop.
    ctx = _desktop(paths.root)
    generation = repository.fetch_session(session_id).get("owner_generation") or 0
    _call(ctx, "adopt_session", {"sessionId": session_id, "expectedGeneration": generation})
    decisions = rows(repository, "SELECT id FROM router_decisions WHERE decision_kind = 'plan_block'")
    served = []
    for _ in range(6):
        step = _call(ctx, "next_plan_item", {"sessionId": session_id, "serve": True})["step"]
        if step is None or step["kind"] != "item":
            break
        served.append(step["practiceItemId"])
        _call(ctx, "submit_dont_know", {"sessionId": session_id, "practiceItemId": step["practiceItemId"],
                                        "hintsUsed": 0, "planPresentationId": step.get("presentationId")})
    assert HELD in served
    assert step["kind"] == "done" and step["stopReason"] == "a forced stop at the phone's boundary"
    plan = rows(repository, "SELECT status, stop_reason FROM daily_plans ORDER BY created_at DESC LIMIT 1")[0]
    assert plan == {"status": "complete", "stop_reason": "a forced stop at the phone's boundary"}
    # Closed on the stop already drawn: no decision since, and still one stop.
    assert rows(repository, "SELECT id FROM router_decisions WHERE decision_kind = 'plan_block'") == decisions
    assert len(_stops(repository)) == 1


def test_f4_the_pending_stop_lapses_when_a_minutes_tap_re_plans(plan_world, monkeypatch):
    phone, _host, repository, _paths = plan_world
    drawn = _stop_past_held_work(monkeypatch)
    session_id = phone.start()["sessionId"]
    for index in range(12):
        step = _next(phone, session_id, f"f4m_next_{index}")["step"]
        if step is None or step["kind"] != "item":
            break
        _dont_know(phone, session_id, step, f"f4m_dk_{index}")
    if not drawn:
        pytest.skip("the phone never crossed a boundary past held work")  # pragma: no cover
    record = engine.latest_today(engine.PlanEnv(vault=None, repository=repository))
    assert engine._stop_pending(record) is not None
    phone.rpc("set_plan_minutes", {"sessionId": session_id, "minutes": 45})
    record = engine.latest_today(engine.PlanEnv(vault=None, repository=repository))
    assert engine._stop_pending(record) is None


# -- F5 ---------------------------------------------------------------------------------------------


def test_f5_the_open_randomized_check_is_named_cold_until_it_is_answered(tmp_path):
    from learnloop.router_objective import checks as C
    from learnloop.scheduling.device_eligibility import PlanStepFilter

    from tests.daily_plan_fakes import record_attempt
    from tests.test_ro5_checks import _env

    env = _env(tmp_path)
    env.device = PlanStepFilter(device_filter=None)
    for _ in range(30):
        _record, step = engine.advance(env, serve=True)
        if step is None or step["kind"] != "item":
            pytest.skip("no check was administered")  # pragma: no cover
        with env.repository.connection() as connection:
            checks = {str(entry["practice_item_id"]) for entry in C.administered(connection).values()}
        if step["practice_item_id"] in checks:
            break
        assert not engine.open_randomized_check(env, step["practice_item_id"])
        env.clock.advance(2)
        record_attempt(env.repository, step["practice_item_id"], step["learning_object_id"], env.clock.now(),
                       session_id=env.session_id)
    check = step["practice_item_id"]
    assert engine.open_randomized_check(env, check)
    env.clock.advance(2)
    record_attempt(env.repository, check, step["learning_object_id"], env.clock.now(), session_id=env.session_id)
    engine.reconcile(env, engine.latest_today(env))
    assert not engine.open_randomized_check(env, check)


def test_f5_the_phones_serve_of_the_check_says_no_help_and_the_desktops_is_unchanged(plan_world, monkeypatch):
    phone, _host, _repository, paths = plan_world
    session_id = phone.start()["sessionId"]
    monkeypatch.setattr(engine, "open_randomized_check",
                        lambda env, practice_item_id, **_kwargs: practice_item_id == "pi_b1")
    served = phone.rpc("get_practice_item", {"practiceItemId": "pi_b1", "sessionId": session_id})
    assert served["noHelp"] is True
    assert "noHelp" not in phone.rpc("get_practice_item", {"practiceItemId": "pi_b2", "sessionId": session_id})
    # The desktop's reply carries no new key (a None origin is byte-identical).
    ctx = _desktop(paths.root)
    generation = _repository.fetch_session(session_id).get("owner_generation") or 0
    _call(ctx, "adopt_session", {"sessionId": session_id, "expectedGeneration": generation})
    assert "noHelp" not in _call(ctx, "get_practice_item", {"practiceItemId": "pi_b1", "sessionId": session_id})


# -- F6 ---------------------------------------------------------------------------------------------


def test_f6_a_desktop_step_whose_session_moved_during_its_work_commits_nothing(plan_world, monkeypatch):
    phone, _host, repository, paths = plan_world
    ctx, session_id = _desktop_session(paths)
    phone_device = phone.device["device_id"]
    real = engine._classified_pool
    adopted = []

    def adopt_meanwhile(env, **kwargs):
        built = real(env, **kwargs)
        if not adopted:
            # The phone adopts the session while the desktop's step is building its pool.
            session = repository.fetch_session(session_id)
            repository.adopt_session(session_id, phone_device, int(session.get("owner_generation") or 0))
            adopted.append(True)
        return built

    monkeypatch.setattr(engine, "_classified_pool", adopt_meanwhile)
    served_before = rows(repository, "SELECT id FROM attention_block_events WHERE kind IN ('item_served', 'block_chosen')")
    with pytest.raises(SidecarError) as moved:
        _call(ctx, "next_plan_item", {"sessionId": session_id, "serve": True})
    assert adopted and moved.value.code == "session_moved"
    after = rows(repository, "SELECT id FROM attention_block_events WHERE kind IN ('item_served', 'block_chosen')")
    assert after == served_before


def test_f6_nothing_changes_for_a_step_whose_session_stayed(plan_world, caplog):
    _phone, _host, _repository, paths = plan_world
    ctx, session_id = _desktop_session(paths)
    for _ in range(3):
        step = _call(ctx, "next_plan_item", {"sessionId": session_id, "serve": True})["step"]
        assert step["kind"] == "item" and step["presentationId"]
        _call(ctx, "submit_dont_know", {"sessionId": session_id, "practiceItemId": step["practiceItemId"],
                                        "hintsUsed": 0, "planPresentationId": step["presentationId"]})
    # The check runs once per transaction it begins, never inside AD's guarded serve receipts.
    assert not [record for record in caplog.records if "guard denied" in record.getMessage()
                or "not recorded" in record.getMessage()]


def test_f6_the_check_is_a_phone_origins_too(plan_world):
    """The phone's own step is checked again at commit as well (the same wrapper)."""

    phone, _host, repository, paths = plan_world
    session_id = phone.start()["sessionId"]
    ctx = _desktop(paths.root)
    origin = RequestOrigin(device_id=phone.device["device_id"])
    real = engine._classified_pool
    adopted = []

    def adopt_meanwhile(env, **kwargs):
        built = real(env, **kwargs)
        if not adopted:
            session = repository.fetch_session(session_id)
            repository.adopt_session(session_id, None, int(session.get("owner_generation") or 0))
            adopted.append(True)
        return built

    monkeypatch_target = pytest.MonkeyPatch()
    monkeypatch_target.setattr(engine, "_classified_pool", adopt_meanwhile)
    try:
        with ctx.acting_as(origin), pytest.raises(SidecarError) as moved:
            _call(ctx, "next_plan_item", {"sessionId": session_id, "serve": True})
    finally:
        monkeypatch_target.undo()
    assert adopted and moved.value.code == "session_moved"
