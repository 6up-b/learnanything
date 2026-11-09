"""Instruct hand-off IH3's code review, M6, m2, m3, m4, m6, m8 and the contract half of m9
(docs/reviews/instruct-handoff-review.md): "Something else would help" through the phone's real host, on a vault whose plan
is on. A phone choice that serves nothing places nothing, what it says is what happened, and a retry says the same. Fakes
only; no model call.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

from learnloop.daily_plan import engine as E
from learnloop.daily_plan import learner_action as LA
from learnloop.daily_plan.types import BlockCandidate
from learnloop.db.stores import router as router_store
from learnloop.router.outcomes import derive_router_outcomes
from learnloop.router_objective import preferences as PF
from learnloop.scheduling.device_eligibility import PlanStepFilter

from tests.router_mixture_helpers import rows
from tests.test_ih2_lessons_compete import _env, _open_offer, draw  # noqa: F401 - the fixture
from tests.test_ih6_workbench_open_item import _phone_workbench
from tests.test_instruct_handoff_ih0 import make_world  # noqa: F401 - the fixture
from tests.test_mobile_phone_contract import _has
from tests.test_te3b_offers import offerable  # noqa: F401 - the fixture

#: What the phone's screens read of a plan-on reply (``practice/SomethingElse.tsx``, ``today/PlanToday.tsx``, ``App.openStep``).
#: The recorded contract's journey runs with the plan off, where these replies say only ``enabled``.
OPTIONS_READS = ("enabled", "options[].kind", "options[].ref", "options[].label", "options[].servable")
CHOICE_READS = ("enabled", "plan", "preference.id", "preference.outcome", "preference.kind", "preference.ref")
SERVED_STEP_READS = ("step.kind", "step.practiceItemId", "step.presentationId", "step.blockId")
#: What must not move when a choice places nothing. The learner_pick row and the preference are the point of it. The read of
#: the options runs the pool build and ``reconcile``, whose own rows are any read's (spec §6 limit 5).
PLACED_TABLES = ("attention_blocks", "router_objective_traces", "plan_presentations")


@pytest.fixture(autouse=True)
def _a_block_of_items_unless_a_test_asks(draw):
    """A real draw's seed is fresh each run, and a stop or a lesson at the floor would change what these tests start from."""

    draw.never_stop, draw.avoid = True, ("lesson_offer:",)


def _fake_lesson(_env, _record):
    return BlockCandidate(candidate_id="lesson_offer:lo_a", lane="new", action="instruct", subtype="lesson_offer",
                          learning_object_ids=("lo_a",), item_ids=(), reading=None, est_minutes=12.0, planner_value=0.1,
                          reason="", annotations={"reversible": True, "topic": "A"})


def _delta(before: dict[str, int], after: dict[str, int]) -> dict[str, int]:
    return {table: after[table] - before[table] for table in after if after[table] != before.get(table)}


def _choose(world, kind: str, ref: str | None, key: str, *, surface: str = "phone_today") -> dict[str, Any]:
    return world.phone.rpc("plan_something_else", {"sessionId": world.session, "kind": kind, "ref": ref, "surface": surface,
                                                   "preferenceId": key})


def test_a_lesson_kept_at_a_finished_block_draws_nothing_through_its_reply(make_world, monkeypatch):
    """Review M6: §6 says such a choice places nothing, and the reply's own read crossed the boundary."""

    monkeypatch.setattr(LA, "_lesson_candidate", _fake_lesson)
    world = make_world()
    world.to_boundary()
    world.wait_for_job()
    before = world.quiet_counts()
    made = _choose(world, "lesson", "lesson_offer:lo_a", "pref_lesson")
    delta = _delta(before, world.counts())
    assert made["preference"]["outcome"] == LA.WAITS_ON_DESKTOP
    assert made["step"] is None and made["plan"]["deciding"] is False
    assert delta["router_decisions"] == 1 and delta["router_learner_preferences"] == 1
    assert not set(delta) & set(PLACED_TABLES), delta
    with world.repository.connection() as connection:
        picks = connection.execute("SELECT decision_kind, chosen_ref FROM router_decisions ORDER BY created_at DESC, id DESC"
                                   ).fetchall()
    assert tuple(picks[0]) == ("learner_pick", "lesson_offer:lo_a")
    # The next explicit step still decides.
    assert world.next()["step"]["kind"] in ("item", "reading", "done", E.DEVICE_HELD_STEP)


def test_a_phone_agreement_draws_nothing_either(make_world):
    world = make_world()
    world.to_boundary()
    world.wait_for_job()
    world.phone.rpc("get_daily_plan", {"sessionId": world.session})  # the read that draws: this block is the plan's pick
    options = world.phone.rpc("plan_something_else_options", {"sessionId": world.session})
    pick = next(option for option in options["options"] if option["plansPick"])
    before = world.quiet_counts()
    made = _choose(world, pick["kind"], pick["ref"], "pref_agree")
    assert made["preference"]["outcome"] == "agreed" and made["step"] is None
    delta = _delta(before, world.counts())
    assert delta["router_learner_preferences"] == 1
    assert "router_decisions" not in delta and not set(delta) & set(PLACED_TABLES), delta


def test_a_served_choice_replies_with_its_step_and_a_retry_says_the_same(make_world):
    """Review m4, through the host: a lost reply's retry gets what the first call said."""

    world = make_world()
    world.to_boundary()
    world.wait_for_job()
    options = world.phone.rpc("plan_something_else_options", {"sessionId": world.session})
    choice = next(option for option in options["options"]
                  if option["kind"] in ("question", "review", "new") and option["servable"] and not option["plansPick"])
    made = _choose(world, choice["kind"], choice["ref"], "pref_served")
    assert made["preference"]["outcome"] == "served" and made["preference"]["replayed"] is False
    assert all(_has(made, path) for path in CHOICE_READS + SERVED_STEP_READS), sorted(made)
    before = world.counts()
    again = _choose(world, choice["kind"], choice["ref"], "pref_served")
    assert again["preference"]["outcome"] == "served" and again["preference"]["replayed"] is True
    assert again["step"]["presentationId"] == made["step"]["presentationId"]
    assert again["step"]["practiceItemId"] == made["step"]["practiceItemId"]
    assert not {table for table in _delta(before, world.counts()) if table.startswith("router_")}


def test_a_retry_of_a_kept_lesson_still_says_it_waits(make_world, monkeypatch):
    monkeypatch.setattr(LA, "_lesson_candidate", _fake_lesson)
    world = make_world()
    world.to_boundary()
    world.wait_for_job()
    _choose(world, "lesson", "lesson_offer:lo_a", "pref_lesson")
    before = world.counts()
    again = _choose(world, "lesson", "lesson_offer:lo_a", "pref_lesson")
    assert again["preference"]["outcome"] == LA.WAITS_ON_DESKTOP and again["preference"]["replayed"] is True
    assert again["step"] is None
    assert not {table for table in _delta(before, world.counts()) if table.startswith(("router_", "attention_"))}


def test_the_replies_the_phone_reads_are_there_on_a_plan_vault(make_world):
    """Review m9: the recorded journey runs with the plan off, so these were checked against no real host."""

    world = make_world()
    step = world.next()["step"]
    plan = world.phone.rpc("get_daily_plan", {"sessionId": world.session})
    assert plan["somethingElse"] is True
    served = world.phone.rpc("next_plan_item", {"sessionId": world.session, "serve": True}, request_id="contract_next")
    assert served["somethingElse"] is True, "App decides the feedback link from this reply"
    assert step["kind"] == "item"
    options = world.phone.rpc("plan_something_else_options", {"sessionId": world.session})
    missing = [path for path in OPTIONS_READS if not _has(options, path)]
    assert not missing, (missing, sorted(options))


def test_a_question_in_progress_is_in_the_reply_the_phone_reads(make_world):
    world = make_world()
    world.to_boundary()
    world.wait_for_job()
    _phone_workbench(world)
    held = world.phone.rpc("get_daily_plan", {"sessionId": world.session})
    assert _has(held, "plan.questionInProgress"), sorted(held["plan"])
    assert held["plan"]["deciding"] is False


def test_with_the_switch_off_the_plan_says_nothing_of_the_link(make_world):
    world = make_world(toml="[router_objective]\nlearner_preferences = false\n")
    world.next()
    assert "somethingElse" not in world.phone.rpc("get_daily_plan", {"sessionId": world.session})
    assert "somethingElse" not in world.phone.rpc("next_plan_item", {"sessionId": world.session, "serve": True},
                                                  request_id="off_next")


# -- m2: learn this, on an offer the desktop drew --------------------------------------------------------------------------


@pytest.mark.usefixtures("offerable")
def test_a_phone_choosing_the_drawn_lesson_is_told_it_waits_and_it_stays_an_agreement(tmp_path, draw):
    env = _env(tmp_path)
    step = _open_offer(env, draw)
    env.device = PlanStepFilter(device_filter=None)
    live = LA.options(env)
    lesson = next(option for option in live.options if option.kind == LA.LESSON)
    assert lesson.plans_pick and not lesson.servable
    picks = len(rows(env, "learner_pick"))
    made = LA.choose(env, kind="lesson", ref=None, surface="phone_feedback", attempt_id=None, note_md=None, preference_id="p")
    decision = step["offer"]["decision_id"]
    assert made.outcome == LA.WAITS_ON_DESKTOP and made.step is None and made.served_decision_id == decision
    assert len(rows(env, "learner_pick")) == picks
    with env.repository.connection() as connection:
        row = router_store.learner_preference(connection, "p")
        assert row["served_decision_id"] == decision and row["decision_id"] == decision
        outcomes = {entry["decision_id"]: entry for entry in derive_router_outcomes(connection, reader_exposures=())}
    assert outcomes[decision].get("outcome") != "overridden"
    # and a retry says the same
    again = LA.choose(env, kind="lesson", ref=None, surface="phone_feedback", attempt_id=None, note_md=None, preference_id="p")
    assert again.outcome == LA.WAITS_ON_DESKTOP and again.replayed


@pytest.mark.usefixtures("offerable")
def test_the_desktop_choosing_the_drawn_lesson_still_agrees(tmp_path, draw):
    env = _env(tmp_path)
    _open_offer(env, draw)
    made = LA.choose(env, kind="lesson", ref=None, surface="today", attempt_id=None, note_md=None, preference_id="p")
    assert made.outcome == "agreed"
    assert LA.choose(env, kind="lesson", ref=None, surface="today", attempt_id=None, note_md=None,
                     preference_id="p").outcome == "agreed"


# -- m3: a reading on the phone ----------------------------------------------------------------------------------------


@pytest.mark.parametrize("shows", [True, False])
def test_a_reading_is_servable_where_the_phones_reader_shows_it(shows):
    device = PlanStepFilter(device_filter=None, reading=lambda _reading: shows)
    env = SimpleNamespace(device=device)
    reading = SimpleNamespace(as_dict=lambda: {"extraction_id": "e", "section_id": "s"})
    assert LA._phone_serves(env, LA.READ, SimpleNamespace(reading=reading)) is shows
    assert LA._phone_serves(env, LA.READ, None, block=SimpleNamespace(reading={"extraction_id": "e"})) is shows
    assert LA._phone_serves(env, LA.READ, None) is False  # nothing to show
    assert LA._phone_serves(env, LA.LESSON, None) is False


def test_with_no_reader_a_reading_waits():
    env = SimpleNamespace(device=PlanStepFilter(device_filter=None))
    assert LA._phone_serves(env, LA.READ, SimpleNamespace(reading=SimpleNamespace(as_dict=dict))) is False


# -- m4: a retry on the desktop ------------------------------------------------------------------------------------------


@pytest.mark.usefixtures("offerable")
def test_a_retried_lesson_pick_opens_the_lesson(tmp_path):
    env = _env(tmp_path)
    E.get_or_create_today(env)
    first = LA.choose(env, kind="lesson", ref=None, surface="today", attempt_id=None, note_md=None, preference_id="p1")
    assert first.outcome == "lesson" and first.lesson
    again = LA.choose(env, kind="lesson", ref=None, surface="today", attempt_id=None, note_md=None, preference_id="p1")
    assert again.outcome == "lesson" and again.lesson == first.lesson and again.replayed


def test_a_retried_stop_says_stopped(tmp_path):
    env = _env(tmp_path)
    E.get_or_create_today(env)
    first = LA.choose(env, kind="stop", ref=None, surface="today", attempt_id=None, note_md=None, preference_id="p1")
    again = LA.choose(env, kind="stop", ref=None, surface="today", attempt_id=None, note_md=None, preference_id="p1")
    assert first.outcome == again.outcome == "stopped" and again.replayed and again.step["kind"] == "done"


def _a_question_option(env) -> LA.Option:
    return next(option for option in LA.options(env).options if option.kind in ("question", "review", "new") and option.candidate)


def test_a_crash_after_the_commit_is_finished_by_the_retry(tmp_path, monkeypatch):
    """The placement committed and the serve didn't happen: the retry owes that serve, once."""

    env = _env(tmp_path)
    E.get_or_create_today(env)
    option = _a_question_option(env)
    real = LA._serve_step

    def crash(*_args, **_kwargs):
        raise RuntimeError("the app stopped here")

    monkeypatch.setattr(LA, "_serve_step", crash)
    with pytest.raises(RuntimeError):
        LA.choose(env, kind=option.kind, ref=option.ref, surface="today", attempt_id=None, note_md=None, preference_id="p1")
    monkeypatch.setattr(LA, "_serve_step", real)
    again = LA.choose(env, kind=option.kind, ref=option.ref, surface="today", attempt_id=None, note_md=None, preference_id="p1")
    assert again.outcome == "served" and again.step["presentation_id"]
    third = LA.choose(env, kind=option.kind, ref=option.ref, surface="today", attempt_id=None, note_md=None, preference_id="p1")
    assert third.step["presentation_id"] == again.step["presentation_id"]


# -- m8: the override's receipts -----------------------------------------------------------------------------------------


def test_an_override_keeps_the_state_a_pick_keeps(tmp_path):
    env = _env(tmp_path)
    E.get_or_create_today(env)
    option = _a_question_option(env)
    made = LA.choose(env, kind=option.kind, ref=option.ref, surface="today", attempt_id=None, note_md=None, preference_id="p1")
    with env.repository.connection() as connection:
        state = connection.execute("SELECT decision_kind, candidate_items FROM decision_state_receipts WHERE decision_id = ?",
                                   (made.served_decision_id,)).fetchone()
    assert state is not None and state["decision_kind"] == "learner_pick"
    assert state["candidate_items"] == len(option.candidate.item_ids)
    with env.repository.connection() as connection:
        assert connection.execute("SELECT decision_kind FROM prefilter_receipts WHERE decision_id = ?",
                                  (made.served_decision_id,)).fetchone()[0] == "learner_pick"


# -- m6: the choice model's feature ----------------------------------------------------------------------------------------


def test_last_miss_reads_the_latest_graded_answer(tmp_path):
    """An ungraded answer says nothing, so it can't hide the miss before it."""

    from tests.daily_plan_fakes import record_attempt

    env = _env(tmp_path)
    record = E.get_or_create_today(env)
    item = sorted(env.vault.practice_items)[0]
    lo = str(env.vault.practice_items[item].learning_object_id)
    missed = record_attempt(env.repository, item, lo, env.clock.now(), session_id=env.session_id)
    with env.repository.connection() as connection:
        connection.execute("UPDATE practice_attempts SET correctness = 0.0 WHERE id = ?", (missed,))
        connection.commit()
    env.clock.advance(5)
    record_attempt(env.repository, item, lo, env.clock.now(), session_id=env.session_id)  # not graded yet
    env.clock.advance(5)
    with env.repository.connection() as connection:
        features = PF.features_at(connection, env.vault.config, at=env.now_iso(), minutes_left=float(record.minutes_left()))
    assert features.last_miss == 1.0


# -- second review, R2-m4: a retry's two edges ------------------------------------------------------------------------


def test_a_retry_owes_no_serve_once_the_plan_has_closed(tmp_path, monkeypatch):
    env = _env(tmp_path)
    E.get_or_create_today(env)
    option = _a_question_option(env)
    real = LA._serve_step

    def crash(*_args, **_kwargs):
        raise RuntimeError("the app stopped here")

    monkeypatch.setattr(LA, "_serve_step", crash)
    with pytest.raises(RuntimeError):
        LA.choose(env, kind=option.kind, ref=option.ref, surface="today", attempt_id=None, note_md=None, preference_id="p1")
    monkeypatch.setattr(LA, "_serve_step", real)
    record = E.latest_today(env)
    block = next(b for b in record.blocks if (b.chosen or {}).get("preference_id") == "p1")
    E._close(env, record, status="stopped", reason="learner_stopped")
    again = LA.choose(env, kind=option.kind, ref=option.ref, surface="today", attempt_id=None, note_md=None, preference_id="p1")
    assert again.outcome == "served" and again.replayed and again.step is None
    with env.repository.connection() as connection:
        assert connection.execute("SELECT COUNT(*) FROM attention_block_events WHERE block_id = ? AND kind = 'item_served'",
                                  (block.id,)).fetchone()[0] == 0


def test_a_key_is_one_act_another_option_on_it_is_refused_and_writes_nothing(tmp_path):
    env = _env(tmp_path)
    E.get_or_create_today(env)
    option = _a_question_option(env)
    LA.choose(env, kind=option.kind, ref=option.ref, surface="today", attempt_id=None, note_md=None, preference_id="p1")
    other = next(entry.kind for entry in LA.options(env).options if entry.kind != option.kind)
    with env.repository.connection() as connection:
        before = connection.execute("SELECT COUNT(*) FROM router_learner_preferences").fetchone()[0]
    with pytest.raises(LA.PreferenceError) as refused:
        LA.choose(env, kind=other, ref=None, surface="today", attempt_id=None, note_md=None, preference_id="p1")
    assert refused.value.code == "validation_error"
    with env.repository.connection() as connection:
        assert connection.execute("SELECT COUNT(*) FROM router_learner_preferences").fetchone()[0] == before
