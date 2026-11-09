"""Instruct hand-off IH2's code review, M3, M4, M5 and m5 (docs/reviews/instruct-handoff-review.md).

An offer the learner never saw counts as neither a seen offer against the day's ceiling nor a decline (IH1's ``offer_shown``
is the record). An open offer being replaced can't be what ends it with no contest, and a lesson competes with a follow-up
whenever one is available, so an offer drawn after a follow-up's own decision is contested. What keeps draws finite without
the old count is pinned here too. Fakes only; no model call.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from learnloop.daily_plan import engine as E
from learnloop.daily_plan import lesson_offer as LO
from learnloop.daily_plan import lesson_suggestion as SG
from learnloop.daily_plan.engine import advance
from learnloop.daily_plan.router_chooser import CONTINUE_CURRENT, INSERT_NOW
from learnloop.db.stores import followup_serve as store
from learnloop.db.stores import router_suggestions as suggestions
from learnloop.followup_serve import workflow as wf
from learnloop.router import lesson_suggestions as LS

from tests.daily_plan_fakes import record_attempt, scheduled
from tests.router_mixture_helpers import rows
from tests.test_daily_plan_build import _wide_items
from tests.test_ih2_lessons_compete import (FOLLOWUP_ITEM, NO_CHECKS, OFF, OLD, QUIET, _answer, _author_refuses, _env, _miss_env, _need_path_env,
                                            _need_probe_arrives, _objective_rows, _open_offer, _ready_probe, _run_lane, draw)
from tests.test_te3b_offers import OFFER, offerable  # noqa: F401 - the fixture

pytestmark = pytest.mark.usefixtures("offerable")

_ = draw  # the fixture, imported by name


def _statuses(env) -> list[tuple[str, str | None]]:
    return [(row["chosen_ref"], (row["detail_json"].get("lesson_offers") or {}).get("status"))
            for row in rows(env, "plan_block")]


def _count(env) -> int:
    with env.repository.connection() as connection:
        decisions = [d for d in suggestions.all_decisions(connection)
                     if not LO.never_on_screen(env.vault.config, connection, d)]
        return LO.shown_today(decisions, env.today())


def _arrives(env, live, name: str) -> None:
    live.insert(0, scheduled(name, "lo_diag", followup_kind="negative_surprise_followup"))
    env.clock.advance(1)


def _show(env, step, surface: str = "offer_page") -> None:
    assert LO.record_shown(env.repository, block_id=step["block_id"], surface=surface, session_id=env.session_id)


# -- M3: the ceiling ----------------------------------------------------------------------------------------------------


def test_offers_nobody_saw_use_up_nothing_and_a_lesson_keeps_competing_past_the_ceiling(tmp_path, draw):
    """Review M3's scenario: background reads each draw an offer as follow-ups arrive. Default ceiling 3."""

    env, live = _need_path_env(tmp_path)
    _open_offer(env, draw)
    draw.prefer = (OFFER,)
    for number in range(5):
        _arrives(env, live, f"pi_need_{number}")
        advance(env, serve=False)
        assert _statuses(env)[-1][1] == "offered"
    assert _count(env) == 0
    with env.repository.connection() as connection:
        assert LO.shown_today(suggestions.all_decisions(connection), env.today()) == 6  # as the old count read them


def test_an_offer_nobody_saw_leaves_the_days_ceiling_free_at_the_next_fresh_boundary(tmp_path, draw):
    """Nothing is being replaced here, so it is the count that decides. Ceiling 1: the only drawn offer lost to a follow-up
    with the learner never seeing it, and when that follow-up is answered a lesson can still be offered."""

    env, live = _need_path_env(tmp_path, toml=QUIET + "\n[router.lesson_suggestions]\nceiling_per_day = 1\n")
    _open_offer(env, draw)
    probe = _need_probe_arrives(live)
    env.clock.advance(1)
    draw.prefer = ("followup_contest:",)
    _record, served = advance(env, serve=True)
    assert served["practice_item_id"] == probe
    env.clock.advance(1)
    record_attempt(env.repository, probe, served["learning_object_id"], env.clock.now(), session_id=env.session_id)
    env.clock.advance(1)
    draw.prefer = (OFFER,)
    for _ in range(8):
        _record, step = advance(env, serve=False)
        if step["kind"] == "lesson_offer":
            break
        _record, step = advance(env, serve=True)
        env.clock.advance(1)
        record_attempt(env.repository, step["practice_item_id"], step["learning_object_id"], env.clock.now(),
                       session_id=env.session_id)
    assert step["kind"] == "lesson_offer"
    assert rows(env, "plan_block")[-1]["detail_json"]["lesson_offers"]["ceiling"].get("replacing") is None


def test_at_the_ceiling_an_open_offer_seen_by_the_learner_still_meets_the_followup(tmp_path, draw):
    """Review M3 (the Nov 8 shape, ceiling 1): the open offer is what the count holds, and it can't block its own redraw."""

    env, live = _need_path_env(tmp_path, toml=QUIET + "\n[router.lesson_suggestions]\nceiling_per_day = 1\n")
    step = _open_offer(env, draw)
    _show(env, step)
    assert _count(env) == 1
    probe = _need_probe_arrives(live)
    env.clock.advance(1)
    draw.prefer = ("followup_contest:",)
    _record, served = advance(env, serve=True)
    new = rows(env, "plan_block")[-1]
    assert new["detail_json"]["mixture"]["support"] == [f"followup_contest:{probe}", OFFER]
    assert new["detail_json"]["lesson_offers"]["status"] == "offered"
    assert new["detail_json"]["lesson_offers"]["ceiling"]["replacing"] is True
    assert served["practice_item_id"] == probe


def test_replacing_again_at_the_ceiling_still_contests(tmp_path, draw):
    """Excluding only the open offer from the count would end the second replacement by rule: the first seen one now fills
    the count, and the card on offer would be cancelled with no contest."""

    env, live = _need_path_env(tmp_path, toml=QUIET + "\n[router.lesson_suggestions]\nceiling_per_day = 1\n")
    _show(env, _open_offer(env, draw))
    draw.prefer = (OFFER,)
    for name in ("pi_need_a", "pi_need_b"):
        _arrives(env, live, name)
        _record, step = advance(env, serve=False)
        assert step["kind"] == "lesson_offer"
        _show(env, step)
    assert [status for _ref, status in _statuses(env)[-2:]] == ["offered", "offered"]
    assert _count(env) == 3  # all were seen, and the count says so


def test_the_ceiling_still_binds_on_seen_offers_at_a_boundary_with_none_open(tmp_path, draw):
    env, _live = _need_path_env(tmp_path, toml=QUIET + "\n[router.lesson_suggestions]\nceiling_per_day = 1\n")
    step = _open_offer(env, draw)
    _show(env, step)
    SG.respond(env.vault, env.repository, decision_id=step["offer"]["decision_id"], response="declined", clock=env.clock)
    env.clock.advance(1)
    advance(env, serve=False)
    assert _statuses(env)[-1][1] == "none:ceiling_bound"


@pytest.mark.parametrize("how", ["offer_shown", "block_started", "answered"])
def test_what_counts_as_on_screen(tmp_path, draw, how):
    env, _live = _need_path_env(tmp_path)
    step = _open_offer(env, draw)
    assert _count(env) == 0
    if how == "offer_shown":
        _show(env, step, surface="today")
    elif how == "block_started":
        env.clock.advance(1)
        advance(env, serve=True)
    else:
        SG.respond(env.vault, env.repository, decision_id=step["offer"]["decision_id"], response="declined", clock=env.clock)
    assert _count(env) == 1


def test_an_unseen_offer_says_nothing_about_when_the_last_card_was_seen(tmp_path, draw):
    env, live = _need_path_env(tmp_path)
    _open_offer(env, draw)
    draw.prefer = (OFFER,)
    env.clock.advance(180)
    _arrives(env, live, "pi_need_a")
    advance(env, serve=False)
    # The acceptance model's context: no card has reached this learner, and the unseen offer doesn't say otherwise.
    assert rows(env, "plan_block")[-1]["detail_json"]["lesson_offers"]["context"]["days_since_last"] is None


def test_rows_from_before_the_record_keep_their_reading(tmp_path):
    """Below the tag a row has no ``offer_shown``, whatever the vault's version is now: drawn is shown, as it was. A TE1b
    card is no offer. Neither reads an event, so a connection that raises shows the rule is the row's own."""

    env = _env(tmp_path)

    class NoEvents:
        def execute(self, *_args):
            raise AssertionError("this row reads no event")

    old = {"id": "d", "algorithm_version": OLD, "detail": {"plan_offer": True, "shown": True, "block_id": "b"}}
    assert LO.never_on_screen(env.vault.config, NoEvents(), old) is False
    card = {"id": "c", "algorithm_version": env.vault.config.algorithms.algorithm_version, "detail": {"shown": True}}
    assert LO.never_on_screen(env.vault.config, NoEvents(), card) is False


@pytest.mark.parametrize("version,toml", [("tag", OFF), ("old", QUIET)])
def test_off_or_below_the_tag_every_drawn_offer_counts_and_an_unseen_one_is_ignored(tmp_path, draw, version, toml):
    env, _live = _need_path_env(tmp_path, version=(OLD if version == "old" else "mvp-0.55"), toml=toml)
    step = _open_offer(env, draw)
    assert _count(env) == 1  # as the predecessor: a draw is a shown offer
    env.clock.advance(60 * 26)
    with env.repository.atomic(), env.repository.connection() as connection:
        assert LO.sweep_ignored(connection, config=env.vault.config, today=env.today(), now_iso=env.now_iso()) == 1
    with env.repository.connection() as connection:
        assert suggestions.response_for(connection, step["offer"]["decision_id"])["response"] == "ignored"


# -- what bounds the draws ----------------------------------------------------------------------------------------------


def _second_workflow(env, item: str, workflow_id: str) -> None:
    lo = str(env.vault.practice_items[item].learning_object_id)
    record_attempt(env.repository, item, lo, env.clock.now(), session_id=env.session_id)
    with env.repository.connection() as connection:
        attempt_id = connection.execute("SELECT id FROM practice_attempts ORDER BY created_at DESC, id DESC").fetchone()[0]
    with env.repository.atomic(), env.repository.connection() as connection:
        store.insert_workflow(connection, {
            "id": workflow_id, "source_attempt_id": attempt_id, "revision_key": "joint", "learning_object_id": lo,
            "session_id": env.session_id, "surface": "desktop", "origin": "practice", "feedback_held": 0,
            "created_at": env.now_iso(),
        })
    wf.move(env.repository, workflow_id, to_state=wf.READY, reason="test", practice_item_id=item, factor_id="f",
            clock=env.clock)


def test_reads_alone_never_redraw_two_followups_against_each_other(tmp_path, draw, monkeypatch):
    """With unseen offers no longer counted, nothing but the follow-ups themselves stops a redraw. Two written probes that
    each lost to a lesson must both wait on the newest offer, or each read's new offer passes the other's and it comes back."""

    env = _env(tmp_path)
    _open_offer(env, draw)
    draw.prefer = (OFFER,)
    planned = {entry.practice_item_id for entry in E.latest_today(env).items()}
    first, second = sorted(item for item in env.vault.practice_items if item not in planned)[:2]
    monkeypatch.setattr(wf, "waiting_still_valid", lambda *_args, **_kwargs: True)
    _second_workflow(env, first, "fw_a")
    env.clock.advance(1)
    advance(env, serve=False)
    _second_workflow(env, second, "fw_b")
    env.clock.advance(1)
    advance(env, serve=False)
    drawn = len(_objective_rows(env))
    for _ in range(12):
        env.clock.advance(1)
        _record, step = advance(env, serve=False)
        assert step["kind"] == "lesson_offer"
    assert len(_objective_rows(env)) == drawn, "a read with nothing newly ready drew again"
    latest = _objective_rows(env)[-1]["id"]
    for workflow_id in ("fw_a", "fw_b"):
        assert wf.lost_offer_decision(env.repository, workflow_id) == latest


def test_draws_on_reads_are_bounded_by_the_followups_that_became_ready(tmp_path, draw):
    env, live = _need_path_env(tmp_path)
    _open_offer(env, draw)
    draw.prefer = (OFFER,)
    start = len(_objective_rows(env))
    arrivals = 4
    for number in range(arrivals):
        _arrives(env, live, f"pi_need_{number}")
        for _ in range(5):  # several reads per arrival
            env.clock.advance(1)
            advance(env, serve=False)
    assert len(_objective_rows(env)) - start == arrivals


# -- M4: none:forced_items ----------------------------------------------------------------------------------------------


@pytest.mark.parametrize("winner", ["followup_contest:", OFFER])
def test_an_offer_drawn_after_the_followups_decision_is_contested(tmp_path, draw, monkeypatch, winner):
    """Review M4's scenario, with the state the real path reaches: a decision that held a lesson drew insert_now; while its
    probe is written a boundary read draws an offer; the probe becomes ready."""

    env = _env(tmp_path)
    step = _open_offer(env, draw)
    monkeypatch.setattr(E, "_lesson_already_competed", lambda *_args, **_kwargs: True)
    probe = _ready_probe(env, decision="d_held_lesson", chosen=INSERT_NOW)["practice_item_id"]
    env.clock.advance(1)
    before = len(rows(env, "plan_block"))
    draw.prefer = (winner,)
    advance(env, serve=True)
    new = rows(env, "plan_block")[before:]
    assert len(new) == 1
    assert new[0]["detail_json"]["lesson_offers"]["status"] == "offered"
    assert new[0]["detail_json"]["mixture"]["support"] == [f"followup_contest:{probe}", OFFER]
    ended = next(block for block in E.latest_today(env).blocks if block.id == step["block_id"])
    assert ended.outcome == LO.SUPERSEDED


def test_a_followups_draw_stands_only_while_no_offer_has_been_drawn_since(tmp_path, draw, monkeypatch):
    """The rule itself, on the real path. A miss's decision held a lesson and drew the follow-up, so it stands. Then an offer
    is drawn and answered before the probe is ready: nothing is being replaced, and that decision never weighed that lesson."""

    env, row = _miss_env(tmp_path)
    draw.prefer = (INSERT_NOW,)
    _author_refuses(monkeypatch)
    _run_lane(env, row, monkeypatch)
    decision = rows(env, "plan_interrupt")[-1]
    assert any(str(ref).startswith("lesson_offer:") for ref in decision["detail_json"]["mixture"]["support"])
    wf.set_fields(env.repository, "fw_miss", practice_item_id="pi_x", clock=env.clock)
    assert E._lesson_already_competed(env, "pi_x")
    with env.repository.connection() as connection:
        assert not suggestions.offer_drawn_since(connection, "no_such_decision")
        assert not suggestions.offer_drawn_since(connection, decision["id"])
    env.clock.advance(1)
    draw.prefer = (OFFER,)
    for _ in range(12):
        _record, step = advance(env, serve=False)
        if step["kind"] == "lesson_offer":
            break
        _record, step = advance(env, serve=True)
        env.clock.advance(1)
        record_attempt(env.repository, step["practice_item_id"], step["learning_object_id"], env.clock.now(),
                       session_id=env.session_id)
    assert step["kind"] == "lesson_offer"
    with env.repository.connection() as connection:
        assert suggestions.offer_drawn_since(connection, decision["id"])
    assert not E._lesson_already_competed(env, "pi_x")


def test_a_request_or_a_check_still_keeps_a_lesson_out_while_an_open_offer_is_replaced(tmp_path, draw):
    """§5 item 2: the learner's act and the experiment's design stay forced. The one remaining ``none:forced_items`` here."""

    env, _live = _need_path_env(tmp_path)
    step = _open_offer(env, draw)
    block = next(b for b in E.latest_today(env).blocks if b.id == step["block_id"])
    requested = SimpleNamespace(practice_item_id="pi_requested", requested=True, check_kind=None)
    check = SimpleNamespace(practice_item_id="pi_check", requested=False, check_kind="check_once")
    follow_up = SimpleNamespace(practice_item_id="pi_f", requested=False, check_kind=None)
    assert not E._followups_compete(env, [requested], E.ORIGIN_FOLLOWUP, superseding=block)
    assert not E._followups_compete(env, [check], E.ORIGIN_FOLLOWUP, superseding=block)
    assert E._followups_compete(env, [follow_up], E.ORIGIN_FOLLOWUP, superseding=block)


# -- m5: a need follow-up's draw runs once --------------------------------------------------------------------------------


def test_a_need_followups_draw_stands_at_the_boundary(tmp_path, draw):
    """Review m5. Its own ``plan_interrupt`` held a lesson and let it wait, so the boundary places it, with no second draw."""

    live = list(_wide_items())
    env = _env(tmp_path, toml=NO_CHECKS, items=lambda: list(live))
    _answer(env, questions_left=True)
    live.insert(0, scheduled(FOLLOWUP_ITEM, "lo_diag", followup_kind="negative_surprise_followup"))
    draw.prefer = (CONTINUE_CURRENT,)
    env.clock.advance(1)
    advance(env, serve=False)
    decided = [row for row in rows(env, "plan_interrupt") if row["policy"].startswith("router_objective")]
    assert decided and decided[-1]["chosen_ref"] == CONTINUE_CURRENT
    assert any(str(ref).startswith("lesson_offer:") for ref in decided[-1]["detail_json"]["mixture"]["support"])
    plan = E.latest_today(env).id
    assert E._lesson_already_competed(env, FOLLOWUP_ITEM, plan_id=plan)
    draw.prefer = (OFFER, "followup_contest:")
    for _ in range(12):
        _record, step = advance(env, serve=True)
        assert step["kind"] == "item"
        if step["practice_item_id"] == FOLLOWUP_ITEM:
            break
        env.clock.advance(1)
        record_attempt(env.repository, step["practice_item_id"], step["learning_object_id"], env.clock.now(),
                       session_id=env.session_id)
        env.clock.advance(1)
    else:
        raise AssertionError("the follow-up never served")
    last = rows(env, "plan_block")[-1]
    assert "followup_contest" not in last["detail_json"]
    assert last["detail_json"]["lesson_offers"]["status"] == "none:forced_items"
    assert [entry["practice_item_id"] for entry in last["detail_json"]["forced"]] == [FOLLOWUP_ITEM]


# -- M5: never rendered is no decline -------------------------------------------------------------------------------------


def _observations(env) -> list[bool]:
    with env.repository.connection() as connection:
        details = {str(d["id"]): d["detail"] for d in suggestions.all_decisions(connection)}
        return [o.accepted for o in LS.observations(details, suggestions.responses(connection))]


def _sweep(env) -> int:
    with env.repository.atomic(), env.repository.connection() as connection:
        return LO.sweep_ignored(connection, config=env.vault.config, today=env.today(), now_iso=env.now_iso())


def test_an_offer_drawn_after_a_miss_and_never_rendered_is_no_decline(tmp_path, draw, monkeypatch):
    """Review M5's scenario: a miss's job draws the lesson, the learner closes the app on feedback, the next day comes."""

    env, row = _miss_env(tmp_path)
    draw.prefer = (OFFER,)
    _run_lane(env, row, monkeypatch)
    decision = rows(env, "plan_interrupt")[-1]["id"]
    env.clock.advance(60 * 26)
    assert _sweep(env) == 1
    with env.repository.connection() as connection:
        assert suggestions.response_for(connection, decision) is None
        release = LO.withdrawn(connection, decision)
        assert release is not None and release["response"] == "expired"
        assert LO.offer_standing(connection, decision, today=env.today()) == LO.OFFER_PASSED
    assert _observations(env) == []
    assert _sweep(env) == 0  # once
    with pytest.raises(SG.SuggestionError):  # and it takes no late answer
        SG.respond(env.vault, env.repository, decision_id=decision, response="accepted", clock=env.clock)


def test_an_offer_seen_and_left_is_still_ignored(tmp_path, draw):
    env, _live = _need_path_env(tmp_path)
    step = _open_offer(env, draw)
    _show(env, step)
    env.clock.advance(60 * 26)
    assert _sweep(env) == 1
    with env.repository.connection() as connection:
        assert suggestions.response_for(connection, step["offer"]["decision_id"])["response"] == "ignored"
    assert _observations(env) == [False]


def test_the_todays_card_sweep_agrees(tmp_path, draw):
    """TE1b's sweep reaches an earlier day's offer first when Today's card is read before the plan's next boundary."""

    env, _live = _need_path_env(tmp_path)
    step = _open_offer(env, draw)
    env.clock.advance(60 * 26)
    with env.repository.atomic(), env.repository.connection() as connection:
        SG._sweep_ignored(connection, suggestions.all_decisions(connection), config=env.vault.config, today=env.today(),
                          now_iso=env.now_iso())
    with env.repository.connection() as connection:
        assert suggestions.response_for(connection, step["offer"]["decision_id"]) is None
        assert LO.withdrawn(connection, step["offer"]["decision_id"]) is not None
    assert _observations(env) == []


def test_the_block_of_an_offer_nobody_saw_ends_taken_back(tmp_path, draw):
    env, _live = _need_path_env(tmp_path)
    step = _open_offer(env, draw)
    plan = E.latest_today(env).id
    env.clock.advance(60 * 26)
    _sweep(env)
    ended = next(block for block in E._reload(env, plan).blocks if block.id == step["block_id"])
    assert ended.outcome == LO.WITHDRAWN and ended.finished
