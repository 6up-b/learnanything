"""Instruct hand-off IH3 (docs/specs/spec_instruct_handoff_v1.md §6, §10): "Something else would help".

The learner names the router's next action. An override serves the action as a ``learner_pick`` decision (no propensity,
``parent_decision_id`` the drawn decision) and writes the preference row in the same transaction, idempotent on retry; a
preference with no draw is stored with a null ``decision_id``; a phone logs a lesson pick and serves nothing; the ledger is
append-only; the parent reads ``overridden``; the switch off leaves behavior as it was. Fakes only; no model call.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import replace
from types import SimpleNamespace
from typing import Any

import pytest

from learnloop.algorithm_versions import FAILURE_SHARE_ALGORITHM_VERSION, PHONE_PROBES_ALGORITHM_VERSION
from learnloop.daily_plan import engine as E
from learnloop.daily_plan import learner_action as LA
from learnloop.daily_plan.engine import advance
from learnloop.db.stores import router as router_store
from learnloop.db.table_roles import TABLE_ROLES, TableRole
from learnloop.router.outcomes import derive_router_outcomes
from learnloop.router_objective import mix
from learnloop.router_objective_switches import learner_preferences_on
from learnloop.scheduling.device_eligibility import PlanStepFilter

from tests.daily_plan_fakes import record_attempt
from tests.router_mixture_helpers import mixture_env, rows
from tests.router_model_fakes import fake_runtime
from tests.test_te3b_offers import OFFER, offerable  # noqa: F401 - the fixture

TAG = FAILURE_SHARE_ALGORITHM_VERSION
OLD = PHONE_PROBES_ALGORITHM_VERSION
QUIET = "[router_objective]\nstop_coin = 0.0\n"
OFF = QUIET + "learner_preferences = false\n"

pytestmark = pytest.mark.usefixtures("offerable")


@pytest.fixture
def draw(monkeypatch):
    """The mix serves the first of ``draw.prefer`` in the support (its probability the exact ``μ``)."""

    real = mix.draw
    control = SimpleNamespace(prefer=())

    def fake(support, parts, weights, epsilon, seed):
        drawn = real(support, parts, weights, epsilon, seed)
        for ref in control.prefer:
            match = next((option for option in support if str(option).startswith(ref)), None)
            if match is not None:
                return replace(drawn, chosen=match, propensity=drawn.pi[match])
        return drawn

    monkeypatch.setattr(mix, "draw", fake)
    return control


def _env(tmp_path, *, version: str = TAG, toml: str = QUIET):
    return mixture_env(tmp_path, fake_runtime(), version=version, toml=toml, session_id="s1")


def _open_offer(env, draw) -> dict[str, Any]:
    """Serve and answer until the feedback prefetch draws the first boundary: the offer, open and unanswered."""

    draw.prefer = (OFFER,)
    for _ in range(8):
        _record, step = advance(env, serve=True)
        assert step is not None and step["kind"] == "item"
        env.clock.advance(2)
        record_attempt(env.repository, step["practice_item_id"], step["learning_object_id"], env.clock.now(),
                       session_id=env.session_id)
        _record, step = advance(env, serve=False)
        if any(row["policy"] == mix.POLICY for row in rows(env)):
            assert step["kind"] == "lesson_offer"
            return step
    raise AssertionError("the objective never decided a boundary")


def _preferences(env) -> list[dict[str, Any]]:
    with env.repository.connection() as connection:
        return router_store.learner_preference_rows(connection)


def _picks(env) -> list[dict[str, Any]]:
    return [row for row in rows(env, "learner_pick") if str(row["receipt_key"]).startswith(router_store.OVERRIDE_KEY_PREFIX)]


def _plain_pick(live: LA.Options) -> LA.Option:
    return next(option for option in live.options if option.candidate is not None and option.kind != LA.LESSON)


# -- the options -----------------------------------------------------------------------------------------------


def test_the_options_are_the_plans_own_candidates_and_the_waiting_draw_is_the_parent(tmp_path, draw):
    env = _env(tmp_path)
    step = _open_offer(env, draw)
    live = LA.options(env)
    assert live.enabled and live.device == "desktop"
    parent = [row for row in rows(env) if row["policy"] == mix.POLICY][-1]
    # the waiting drawn decision is the parent; its own pick (the lesson offer) stands for its kind
    assert live.decision_id == parent["id"] and live.parent_is_offer and live.parent_block_id == step["block_id"]
    kinds = [option.kind for option in live.options]
    assert LA.LESSON in kinds and kinds[-1] == LA.STOP and len(kinds) == len(set(kinds))
    lesson = next(option for option in live.options if option.kind == LA.LESSON)
    assert lesson.plans_pick and lesson.ref == parent["chosen_ref"]
    # a probability only where the decision logged one: the offer's is its exact draw probability
    assert lesson.propensity == pytest.approx(parent["propensity"])
    others = [option for option in live.options if option.kind not in (LA.LESSON, LA.STOP)]
    assert others and all(option.candidate is not None and not option.plans_pick for option in others)
    assert live.offered()["drawn"] is True and live.offered()["router_pick"]["ref"] == parent["chosen_ref"]
    # reading the options writes no decision, no preference
    assert _preferences(env) == [] and _picks(env) == []


def test_with_no_draw_the_options_are_what_the_plan_can_produce_and_say_so(tmp_path, draw):
    env = _env(tmp_path)
    _record, step = advance(env, serve=True)
    assert step["kind"] == "item"
    live = LA.options(env)  # mid-block: the next step is no new decision
    assert live.enabled and live.decision_id is None and live.no_draw_reason == "mid_block"
    assert not any(option.plans_pick or option.propensity is not None for option in live.options)
    assert live.offered()["drawn"] is False and live.offered()["no_draw"] == "mid_block"
    pick = _plain_pick(live)
    result = LA.choose(env, kind=pick.kind, ref=pick.ref, surface="feedback", attempt_id="a1", note_md=None,
                       preference_id="p_nodraw")
    row = _preferences(env)[0]
    assert result.outcome == "served" and row["decision_id"] is None and row["attempt_id"] == "a1"
    assert json.loads(row["offered_json"])["drawn"] is False
    served = _picks(env)[0]
    assert served["parent_decision_id"] is None and served["propensity"] is None and served["learner_pick"] == 1


# -- the override ----------------------------------------------------------------------------------------------


def test_an_override_serves_the_action_logs_both_rows_and_the_parent_reads_overridden(tmp_path, draw):
    env = _env(tmp_path)
    step = _open_offer(env, draw)
    live = LA.options(env)
    parent_id = live.decision_id
    pick = _plain_pick(live)
    result = LA.choose(env, kind=pick.kind, ref=pick.ref, surface="offer_page", attempt_id=None,
                       note_md="  a different kind of question, please  ", preference_id="p1")
    assert result.outcome == "served" and result.step["kind"] == "item"
    (preference,) = _preferences(env)
    (served,) = _picks(env)
    assert preference["id"] == "p1" and preference["decision_id"] == parent_id
    assert preference["served_decision_id"] == served["id"] and preference["surface"] == "offer_page"
    assert preference["chosen_kind"] == pick.kind and preference["chosen_ref"] == pick.ref
    assert preference["note_md"] == "a different kind of question, please"
    assert preference["algorithm_version"] == TAG
    offered = json.loads(preference["offered_json"])
    assert offered["drawn"] is True and {o["kind"] for o in offered["options"]} >= {pick.kind, LA.LESSON, LA.STOP}
    # a learner pick: no propensity, the parent named, labelled self-selected
    assert served["decision_kind"] == "learner_pick" and served["propensity_kind"] == "none"
    assert served["propensity"] is None and served["learner_pick"] == 1 and served["policy"] == "learner"
    assert served["parent_decision_id"] == parent_id
    assert served["detail_json"]["self_selected"] is True
    # the unanswered offer it replaced ended superseded, outside the learner's answers
    record = E.latest_today(env)
    assert record.open_lesson_offer() is None
    assert any(b.id == step["block_id"] for b in record.blocks) and result.step["block_id"] != step["block_id"]
    # the block the choice placed is the learner's, bound to the served decision
    block = next(b for b in record.blocks if b.id == result.step["block_id"])
    assert block.chosen_by == "learner_pick" and block.decision_ref == served["id"]
    with env.repository.connection() as connection:
        status = {row["decision_id"]: row["action_status"] for row in derive_router_outcomes(connection, reader_exposures=())}
    assert status[parent_id] == "overridden"


def test_the_override_and_the_preference_are_one_transaction(tmp_path, draw, monkeypatch):
    env = _env(tmp_path)
    _open_offer(env, draw)
    live = LA.options(env)
    pick = _plain_pick(live)
    before = (len(rows(env, "learner_pick")), len(rows(env)))

    def boom(*args, **kwargs):
        raise RuntimeError("the block could not be placed")

    monkeypatch.setattr(E, "_persist_block", boom)
    with pytest.raises(RuntimeError):
        LA.choose(env, kind=pick.kind, ref=pick.ref, surface="today", attempt_id=None, note_md=None,
                  preference_id="p_fail")
    # nothing of the act survived: no preference, no decision, the offer still open
    assert _preferences(env) == [] and (len(rows(env, "learner_pick")), len(rows(env))) == before
    assert E.latest_today(env).open_lesson_offer() is not None


def test_a_retry_with_the_same_key_writes_nothing_again(tmp_path, draw):
    env = _env(tmp_path)
    _open_offer(env, draw)
    pick = _plain_pick(LA.options(env))
    first = LA.choose(env, kind=pick.kind, ref=pick.ref, surface="feedback", attempt_id=None, note_md="x",
                      preference_id="p_once")
    again = LA.choose(env, kind=pick.kind, ref=pick.ref, surface="feedback", attempt_id=None, note_md="x",
                      preference_id="p_once")
    assert first.outcome == "served" and again.replayed and again.outcome == "served"
    assert again.served_decision_id == first.served_decision_id
    assert again.step is not None and again.step["practice_item_id"] == first.step["practice_item_id"]
    assert len(_preferences(env)) == 1 and len(_picks(env)) == 1
    with env.repository.connection() as connection:
        blocks = connection.execute("SELECT COUNT(*) FROM attention_blocks WHERE chosen_by = 'learner_pick'").fetchone()[0]
    assert blocks == 1


def test_choosing_what_the_plan_had_drawn_serves_nothing_new(tmp_path, draw):
    env = _env(tmp_path)
    _open_offer(env, draw)
    live = LA.options(env)
    lesson = next(option for option in live.options if option.plans_pick)
    blocks_before = len(E.latest_today(env).blocks)
    result = LA.choose(env, kind=lesson.kind, ref=lesson.ref, surface="feedback", attempt_id=None, note_md=None,
                       preference_id="p_agree")
    (preference,) = _preferences(env)
    assert result.outcome == "agreed" and result.step is None
    # the preference names the parent as what was served: an agreement, no new decision, no override
    assert preference["served_decision_id"] == preference["decision_id"] == live.decision_id
    assert _picks(env) == [] and len(E.latest_today(env).blocks) == blocks_before
    assert E.latest_today(env).open_lesson_offer() is not None


def test_stop_ends_the_plan_as_the_learners_own_choice(tmp_path, draw):
    env = _env(tmp_path)
    _open_offer(env, draw)
    result = LA.choose(env, kind=LA.STOP, ref=None, surface="today", attempt_id=None, note_md=None,
                       preference_id="p_stop")
    assert result.outcome == "stopped" and result.step["kind"] == "done"
    (preference,) = _preferences(env)
    (served,) = _picks(env)
    assert served["chosen_ref"] == "stop_for_today" and preference["chosen_kind"] == LA.STOP
    assert not E.latest_today(env).is_open


def test_an_unknown_choice_is_refused_and_writes_nothing(tmp_path, draw):
    env = _env(tmp_path)
    _open_offer(env, draw)
    with pytest.raises(LA.PreferenceError) as bad_surface:
        LA.choose(env, kind=LA.NEW, ref=None, surface="phone_today", attempt_id=None, note_md=None)
    assert bad_surface.value.code == "validation_error"
    with pytest.raises(LA.PreferenceError):
        LA.choose(env, kind="nonsense", ref=None, surface="today", attempt_id=None, note_md=None)
    assert _preferences(env) == [] and _picks(env) == []


# -- the phone ---------------------------------------------------------------------------------------------------


def test_the_phone_logs_a_lesson_pick_and_hands_it_to_the_desktop(tmp_path, draw):
    env = _env(tmp_path)
    _record, step = advance(env, serve=True)
    env.device = PlanStepFilter(device_filter=None)
    live = LA.options(env)
    lesson = next(option for option in live.options if option.kind == LA.LESSON)
    # the phone offers it, and says it can't serve it
    assert live.device == "phone" and lesson.servable is False
    blocks_before = len(E.latest_today(env).blocks)
    result = LA.choose(env, kind=LA.LESSON, ref=lesson.ref, surface="phone_feedback", attempt_id="a1",
                       note_md="I keep losing the sign", preference_id="p_phone")
    assert result.outcome == LA.WAITS_ON_DESKTOP and result.step is None and result.lesson is None
    (preference,) = _preferences(env)
    assert preference["surface"] == "phone_feedback" and preference["chosen_kind"] == LA.LESSON
    assert preference["note_md"] == "I keep losing the sign"
    assert json.loads(preference["offered_json"])["device"] == "phone"
    (served,) = _picks(env)
    assert served["surface"] == "phone_plan" and served["detail_json"]["override"]["serving"] == LA.WAITS_ON_DESKTOP
    # nothing was placed and no lesson started
    assert len(E.latest_today(env).blocks) == blocks_before
    env.device = None
    with env.repository.connection() as connection:
        assert connection.execute("SELECT COUNT(*) FROM lessons").fetchone()[0] == 0


def test_a_phone_surface_is_for_the_phone_only(tmp_path, draw):
    env = _env(tmp_path)
    advance(env, serve=True)
    with pytest.raises(LA.PreferenceError) as desktop:
        LA.choose(env, kind=LA.NEW, ref=None, surface="phone_feedback", attempt_id=None, note_md=None)
    assert desktop.value.code == "validation_error"
    env.device = PlanStepFilter(device_filter=None)
    with pytest.raises(LA.PreferenceError) as phone:
        LA.choose(env, kind=LA.NEW, ref=None, surface="feedback", attempt_id=None, note_md=None)
    assert phone.value.code == "validation_error"
    assert _preferences(env) == []


def test_the_desktop_opens_a_chosen_lesson(tmp_path, draw):
    env = _env(tmp_path)
    advance(env, serve=True)  # mid-block: no offer is waiting, so a lesson is not the plan's own pick
    live = LA.options(env)
    lesson = next(option for option in live.options if option.kind == LA.LESSON)
    assert lesson.servable and not lesson.plans_pick
    result = LA.choose(env, kind=LA.LESSON, ref=lesson.ref, surface="today", attempt_id=None, note_md=None,
                       preference_id="p_lesson")
    assert result.outcome == "lesson" and result.lesson["learning_object_ids"] and result.lesson["title"]
    (served,) = _picks(env)
    assert served["chosen_ref"].startswith("lesson_offer:") and served["chosen_practice_item_id"] is None
    assert served["detail_json"]["override"]["serving"] == "desktop_opens_lesson"


# -- the ledger ----------------------------------------------------------------------------------------------


def test_the_ledger_is_append_only_and_classified(tmp_path, draw):
    env = _env(tmp_path)
    advance(env, serve=True)
    pick = _plain_pick(LA.options(env))
    LA.choose(env, kind=pick.kind, ref=pick.ref, surface="today", attempt_id=None, note_md=None, preference_id="p_ao")
    with env.repository.connection() as connection:
        with pytest.raises(sqlite3.DatabaseError, match="append-only"):
            connection.execute("UPDATE router_learner_preferences SET note_md = 'edited'")
        with pytest.raises(sqlite3.DatabaseError, match="append-only"):
            connection.execute("DELETE FROM router_learner_preferences")
    assert len(_preferences(env)) == 1
    assert TABLE_ROLES["router_learner_preferences"] == TableRole.RAW_LEDGER


def test_an_override_changes_no_score_and_is_never_evidence(tmp_path, draw):
    env = _env(tmp_path)
    _open_offer(env, draw)
    with env.repository.connection() as connection:
        before = {name: connection.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0] for name in (
            "practice_attempts", "item_state", "error_events")
                  if connection.execute("SELECT 1 FROM sqlite_master WHERE name = ?", (name,)).fetchone()}
    pick = _plain_pick(LA.options(env))
    LA.choose(env, kind=pick.kind, ref=pick.ref, surface="today", attempt_id=None, note_md="I know this", preference_id="p_ev")
    with env.repository.connection() as connection:
        after = {name: connection.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0] for name in before}
    # no attempt, no mastery state, no error event came of it, and the learner gave the offer no answer: the only
    # response is the plan's own ``expired`` (the offer ended superseded), which the acceptance model never reads
    assert after == before
    with env.repository.connection() as connection:
        responses = [row[0] for row in connection.execute("SELECT response FROM router_suggestion_responses")]
    assert responses == ["expired"]


# -- the switch --------------------------------------------------------------------------------------------------


def test_with_the_switch_off_there_is_no_link_and_nothing_is_written(tmp_path, draw):
    env = _env(tmp_path, toml=OFF)
    assert not learner_preferences_on(env.vault.config) and not LA.enabled(env)
    _record, step = advance(env, serve=True)
    assert step["kind"] == "item"
    assert LA.options(env).enabled is False and LA.options(env).options == ()
    with pytest.raises(LA.PreferenceError) as error:
        LA.choose(env, kind=LA.NEW, ref=None, surface="today", attempt_id=None, note_md=None)
    assert error.value.code == "plan_off"
    assert _preferences(env) == [] and _picks(env) == []
    # the plan's view carries no flag
    from learnloop_sidecar.handlers import daily_plan as handler

    assert handler._preference_line(env) == {}


def test_below_the_tag_the_switch_does_nothing(tmp_path, draw):
    env = _env(tmp_path, version=OLD)
    assert not learner_preferences_on(env.vault.config) and not LA.enabled(env)
    assert LA.options(env).enabled is False


def test_the_plan_view_carries_the_flag_only_with_the_switch_on(tmp_path):
    from learnloop_sidecar.handlers import daily_plan as handler

    assert handler._preference_line(_env(tmp_path / "on")) == {"something_else": True}
    assert handler._preference_line(_env(tmp_path / "off", toml=OFF)) == {}
    assert handler._preference_line(_env(tmp_path / "below", version=OLD)) == {}


def test_the_switch_is_in_the_registry_and_the_default_is_on(tmp_path):
    from learnloop.config.schema import RouterObjectiveConfig
    from learnloop.params.parameter_registry import classify_config_path

    assert RouterObjectiveConfig().learner_preferences is True
    rule = classify_config_path("router_objective.learner_preferences")
    assert rule is not None and "kill switch" in rule.rationale and "IH3" in rule.rationale
