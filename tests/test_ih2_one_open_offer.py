"""Instruct hand-off IH2 (docs/specs/spec_instruct_handoff_v1.md §5, review R2-M1): at most one open offer, whatever the
timing. A decision can wait up to 40 s on its models with nothing held, and any other decision can commit meanwhile. These
tests run the second decision at exactly that point: inside the first one's wait, where the first has already read the plan.
Fakes only; no model call.
"""

from __future__ import annotations

import pytest

from learnloop.daily_plan import engine as E
from learnloop.daily_plan import lesson_offer as LO
from learnloop.daily_plan import lesson_suggestion as SG
from learnloop.daily_plan.engine import advance
from learnloop.daily_plan.objective_chooser import ObjectiveFollowupGate, ObjectiveRestraintGate
from learnloop.daily_plan.router_chooser import INSERT_NOW
from learnloop.db.stores import followup_serve as store
from learnloop.db.stores import router_suggestions as suggestions
from learnloop.followup_serve import workflow as wf
from learnloop.router import lesson_suggestions as LS

from tests.daily_plan_fakes import record_attempt, scheduled
from tests.router_mixture_helpers import rows
from tests.daily_plan_build_helpers import _wide_items
from tests.ih2_lessons_compete_helpers import (  # noqa: F401 - ``draw`` is a fixture
    FOLLOWUP_ITEM,
    NO_CHECKS,
    OFF_NO_CHECKS,
    _answer,
    _assert_exact_mu,
    _author_refuses,
    _env,
    _miss_env,
    _need_path_env,
    _need_probe_arrives,
    _open_offer,
    _run_lane,
    draw,
)
from tests.te3b_offers_helpers import OFFER, offerable  # noqa: F401 - the fixture

pytestmark = pytest.mark.usefixtures("offerable")

OTHER = ("new:", "push:", "repair:", "maintain:")


def open_offers(env) -> list[str]:
    """Read from the tables, not from :class:`PlanRecord`: what the invariant is about is what is stored."""

    with env.repository.connection() as connection:
        return [row[0] for row in connection.execute(
            "SELECT b.id FROM attention_blocks b JOIN daily_plans p ON p.id = b.daily_plan_id "
            "WHERE p.status = 'open' AND b.subtype = 'lesson_offer' AND NOT EXISTS ("
            "  SELECT 1 FROM attention_block_events e WHERE e.block_id = b.id AND e.kind = 'block_ended') "
            "ORDER BY b.plan_ordinal")]


def _to_boundary(env, draw) -> None:
    """The block in hand ends, with no offer drawn on the way: the next step is a boundary."""

    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(SG, "build_candidates", lambda *_a, **_k: ([], {}))
        draw.never_stop = True
        for _ in range(12):
            current = E.latest_today(env).current_block()
            item = next((entry for entry in current.items if not entry.resolved), None) if current else None
            if item is None:
                break
            E._skip(env, E.latest_today(env), item.practice_item_id)
    assert E.latest_today(env).current_block() is None


def _second_workflow(env, workflow_id: str = "fw_second") -> dict:
    """Another miss's workflow, with nothing written."""

    planned = {entry.practice_item_id for entry in E.latest_today(env).items()}
    item = sorted(item_id for item_id in env.vault.practice_items if item_id not in planned)[0]
    lo = str(env.vault.practice_items[item].learning_object_id)
    env.clock.advance(1)
    record_attempt(env.repository, item, lo, env.clock.now(), session_id=env.session_id)
    with env.repository.connection() as connection:
        attempt = connection.execute("SELECT id FROM practice_attempts ORDER BY created_at DESC, id DESC").fetchone()[0]
    with env.repository.atomic(), env.repository.connection() as connection:
        store.insert_workflow(connection, {
            "id": workflow_id, "source_attempt_id": attempt, "revision_key": "joint", "learning_object_id": lo,
            "session_id": env.session_id, "surface": "desktop", "origin": "practice", "feedback_held": 0,
            "created_at": env.now_iso(),
        })
    return wf.get(env.repository, workflow_id)


def _during(monkeypatch, owner, name: str, action) -> None:
    """``action`` runs once, inside the first call of ``owner.name``: after that decision read the plan, before it writes."""

    real = getattr(owner, name)
    done: list[bool] = []

    def wrapped(*args, **kwargs):
        if not done:
            done.append(True)
            action()
        return real(*args, **kwargs)

    monkeypatch.setattr(owner, name, wrapped)


def _observations(env) -> list[bool]:
    with env.repository.connection() as connection:
        details = {str(row["id"]): row["detail"] for row in suggestions.all_decisions(connection)}
        return [row.accepted for row in LS.observations(details, suggestions.responses(connection))]


def _ended(env, block_id: str) -> dict:
    with env.repository.connection() as connection:
        rows_ = [dict(row) for row in store_events(connection, block_id)]
    assert len(rows_) == 1
    return rows_[0]


def store_events(connection, block_id: str):
    import json

    for row in connection.execute("SELECT detail_json FROM attention_block_events WHERE block_id = ? AND kind = 'block_ended'",
                                  (block_id,)):
        yield json.loads(row[0])


# -- the finding: a plan read during a follow-up's decision --------------------------------------------------------------


def _read_during_the_jobs_decision(env, draw, monkeypatch) -> list[str]:
    """Spec §5's window: the job's decision holds the arm, a read draws an offer while its models answer, and then the job
    draws the lesson too. Returns the block the read placed."""

    placed: list[str] = []

    def read():
        _record, step = advance(env, serve=False)
        assert step["kind"] == "lesson_offer"
        placed.append(step["block_id"])

    _during(monkeypatch, ObjectiveFollowupGate, "decide_followup", read)
    return placed


@pytest.mark.parametrize("answer", ["accepted", "declined"])
def test_a_read_drawing_an_offer_during_a_jobs_decision_leaves_one_offer(tmp_path, draw, monkeypatch, answer):
    env, row = _miss_env(tmp_path)
    _to_boundary(env, draw)
    draw.prefer = (OFFER,)
    placed = _read_during_the_jobs_decision(env, draw, monkeypatch)
    _run_lane(env, row, monkeypatch)
    drawn = rows(env, "plan_interrupt")[-1]
    assert drawn["chosen_ref"] == OFFER and placed
    # One stands: the job's, whose draw is the newer. Both decisions keep their logged probabilities.
    assert len(open_offers(env)) == 1
    _assert_exact_mu(drawn)
    _assert_exact_mu(rows(env, "plan_block")[-1])
    ended = _ended(env, placed[0])
    assert ended["outcome"] == LO.SUPERSEDED and ended[LO.SUPERSEDED_BY] == drawn["id"]
    first = rows(env, "plan_block")[-1]
    with env.repository.connection() as connection:
        assert suggestions.response_for(connection, first["id"]) is None
        expired = suggestions.release_for(connection, first["id"])
        assert expired["response"] == "expired"
    # The workflow waits on what stands.
    waiting = wf.get(env.repository, "fw_miss")
    assert wf.lost_to_lesson(waiting) and wf.lost_offer_decision(env.repository, "fw_miss") == drawn["id"]
    # So one answer is one observation, and it settles the follow-up. Nothing offers the same lesson again.
    _record, step = advance(env, serve=False)
    assert step["kind"] == "lesson_offer" and step["offer"]["decision_id"] == drawn["id"]
    LO.record_shown(env.repository, block_id=step["block_id"], surface="offer_page", session_id=env.session_id)
    SG.respond(env.vault, env.repository, decision_id=drawn["id"], response=answer, clock=env.clock)
    env.clock.advance(1)
    _record, after = advance(env, serve=False)
    assert open_offers(env) == [] or after["block_id"] != step["block_id"]
    assert _observations(env) == [answer == "accepted"]
    if answer == "accepted":
        assert after["kind"] != "lesson_offer"
        assert wf.get(env.repository, "fw_miss")["state"] == wf.SETTLED
    # A tap on the page the old offer left is refused, and nothing is recorded: M2's page closes on this.
    with pytest.raises(SG.SuggestionError) as refused:
        SG.respond(env.vault, env.repository, decision_id=first["id"], response="declined", clock=env.clock)
    assert refused.value.code == "not_found"
    assert _observations(env) == [answer == "accepted"]


def test_a_superseded_offer_passing_a_later_day_is_not_read_as_a_decline(tmp_path, draw, monkeypatch):
    """The review's last line: what the plan ended never comes back as ``ignored``, whichever offer was on screen."""

    env, row = _miss_env(tmp_path)
    _to_boundary(env, draw)
    draw.prefer = (OFFER,)
    placed = _read_during_the_jobs_decision(env, draw, monkeypatch)
    _run_lane(env, row, monkeypatch)
    LO.record_shown(env.repository, block_id=placed[0], surface="offer_page", session_id=env.session_id)  # refused: ended
    env.clock.advance(60 * 26)
    with env.repository.atomic(), env.repository.connection() as connection:
        LO.sweep_ignored(connection, config=env.vault.config, today=env.today(), now_iso=env.now_iso())
    assert _observations(env) == []


def test_a_job_that_draws_the_followup_leaves_the_read_offer_alone(tmp_path, draw, monkeypatch):
    env, row = _miss_env(tmp_path)
    _to_boundary(env, draw)
    draw.prefer = (OFFER,)
    placed: list[str] = []

    def read():
        _record, step = advance(env, serve=False)
        placed.append(step["block_id"])
        draw.prefer = (INSERT_NOW,)

    _during(monkeypatch, ObjectiveFollowupGate, "decide_followup", read)
    _author_refuses(monkeypatch)
    _run_lane(env, row, monkeypatch)
    assert rows(env, "plan_interrupt")[-1]["chosen_ref"] == INSERT_NOW
    assert open_offers(env) == placed


# -- the other way round: a serve's decision, with a job's offer placed under it -------------------------------------------


def test_a_boundary_drawing_an_offer_replaces_the_jobs_offer_placed_under_it(tmp_path, draw, monkeypatch):
    env, row = _miss_env(tmp_path)
    _to_boundary(env, draw)
    draw.prefer = (OFFER,)
    _during(monkeypatch, E, "decide", lambda: _run_lane(env, row, monkeypatch))
    _record, step = advance(env, serve=True)
    interrupt = rows(env, "plan_interrupt")[-1]
    drawn = rows(env, "plan_block")[-1]
    assert interrupt["chosen_ref"] == drawn["chosen_ref"] == OFFER
    assert step["kind"] == "lesson_offer" and step["offer"]["decision_id"] == drawn["id"]
    assert open_offers(env) == [step["block_id"]]
    with env.repository.connection() as connection:
        assert suggestions.release_for(connection, interrupt["id"])["response"] == "expired"
    assert wf.lost_offer_decision(env.repository, "fw_miss") == drawn["id"]
    assert wf.get(env.repository, "fw_miss")["state"] == wf.WAITING, "it waits on the offer that replaced the one it lost to"


def test_a_boundary_drawing_a_block_leaves_the_jobs_offer_first_and_its_own_block_next(tmp_path, draw, monkeypatch):
    """Both draws stand: nothing here ended the job's offer by rule. The block's ordinal is read in its transaction (the
    stale one is a unique-index failure on the whole decision), and its item isn't served under the offer."""

    env, row = _miss_env(tmp_path)
    _to_boundary(env, draw)
    draw.prefer = (OFFER,)

    def job():
        _run_lane(env, row, monkeypatch)
        draw.prefer = OTHER

    _during(monkeypatch, E, "decide", job)
    _record, step = advance(env, serve=True)
    interrupt = rows(env, "plan_interrupt")[-1]
    assert interrupt["chosen_ref"] == OFFER
    assert step["kind"] == "lesson_offer" and step["offer"]["decision_id"] == interrupt["id"]
    assert open_offers(env) == [step["block_id"]]
    record = E.latest_today(env)
    below = next(block for block in record.blocks if not block.finished and not block.is_lesson_offer)
    assert all(item.served_at is None for item in below.items)
    SG.respond(env.vault, env.repository, decision_id=interrupt["id"], response="declined", clock=env.clock)
    env.clock.advance(1)
    _record, resumed = advance(env, serve=True)
    assert resumed["kind"] == "item" and resumed["block_id"] == below.id


def test_two_reads_contesting_one_offer_decide_it_once(tmp_path, draw, monkeypatch):
    """A boundary is decided once. The second decision to reach its write finds the block the first placed and is dropped
    with nothing logged; the step is what stands. Before, the ordinal's unique index failed the whole call."""

    env, live = _need_path_env(tmp_path)
    first = _open_offer(env, draw)
    _need_probe_arrives(live)
    draw.prefer = (OFFER,)
    inner: list[str] = []
    decisions: list[int] = []

    def read():
        _record, step = advance(env, serve=False)
        inner.append(step["block_id"])
        decisions.append(len(rows(env, "plan_block")))

    _during(monkeypatch, E, "decide", read)
    _record, step = advance(env, serve=False)
    assert step["kind"] == "lesson_offer" and inner and step["block_id"] == inner[0] != first["block_id"]
    assert open_offers(env) == [step["block_id"]]
    assert len(rows(env, "plan_block")) == decisions[0], "the dropped decision logged nothing"
    assert _ended(env, first["block_id"])[LO.SUPERSEDED_BY] == rows(env, "plan_block")[-1]["id"]


def test_a_pick_landing_during_a_boundarys_decision_takes_that_boundary(tmp_path, draw, monkeypatch):
    env, _row = _miss_env(tmp_path)
    _to_boundary(env, draw)
    draw.prefer = (OFFER,)
    planned = {entry.practice_item_id for entry in E.latest_today(env).items()}
    item = sorted(item_id for item_id in env.vault.practice_items if item_id not in planned)[0]
    picked: list[str] = []

    def pick():
        _record, step = E.learner_pick(env, item)
        picked.append(step["block_id"])

    _during(monkeypatch, E, "decide", pick)
    _record, step = advance(env, serve=False)
    assert picked and step["block_id"] == picked[0] and open_offers(env) == []


def test_a_need_decision_replacing_an_interrupting_offer_keeps_its_place_and_what_it_beat(tmp_path, draw, monkeypatch):
    """The mid-block path writes through the same door, and the block below still resumes after the answer."""

    live = list(_wide_items())
    env = _env(tmp_path, toml=NO_CHECKS, items=lambda: list(live))
    _answer(env, questions_left=True)
    workflow = _second_workflow(env)
    _run = {}
    draw.prefer = (OFFER,)

    def job():
        _run_lane(env, workflow, monkeypatch)
        _run["offer"] = E.latest_today(env).open_lesson_offer()

    live.insert(0, scheduled(FOLLOWUP_ITEM, "lo_diag", followup_kind="negative_surprise_followup"))
    _during(monkeypatch, ObjectiveRestraintGate, "decide", job)
    _record, step = advance(env, serve=False)
    assert _run["offer"] is not None and _run["offer"].interrupts
    assert step["kind"] == "lesson_offer" and step["block_id"] != _run["offer"].id
    assert open_offers(env) == [step["block_id"]]
    record = E.latest_today(env)
    new = record.open_lesson_offer()
    assert new.interrupts and record.current_block().id == new.id
    assert FOLLOWUP_ITEM in new.followups_lost
    drawn = rows(env, "plan_interrupt")[-1]
    assert wf.lost_offer_decision(env.repository, workflow["id"]) == drawn["id"]
    SG.respond(env.vault, env.repository, decision_id=drawn["id"], response="declined", clock=env.clock)
    env.clock.advance(1)
    _record, resumed = advance(env, serve=False)
    assert resumed["kind"] == "item"


def test_an_offer_that_finds_a_check_below_it_at_its_write_does_not_come_first(tmp_path, draw, monkeypatch):
    """What ``interrupt_offer`` asked before the wait is asked again where it counts: a card never comes over a check."""

    env, row = _miss_env(tmp_path, questions_left=True)
    draw.prefer = (OFFER,)
    monkeypatch.setattr(E, "_offer_may_interrupt", lambda _env, block: block is None)
    real = E.interrupt_offer

    def asked_while_it_was_allowed(env_, record, block):
        with pytest.MonkeyPatch.context() as allow:
            allow.setattr(E, "_offer_may_interrupt", lambda *_a: True)
            return real(env_, record, block)

    monkeypatch.setattr(E, "interrupt_offer", asked_while_it_was_allowed)
    _run_lane(env, row, monkeypatch)
    record = E.latest_today(env)
    offer = record.open_lesson_offer()
    assert offer is not None and not offer.interrupts and not record.current_block().is_lesson_offer


# -- every pairing ------------------------------------------------------------------------------------------------------


@pytest.mark.parametrize("inner_draws", ["lesson", "other"])
@pytest.mark.parametrize("outer_draws", ["lesson", "other"])
@pytest.mark.parametrize("inner", ["read", "job"])
@pytest.mark.parametrize("outer", ["job", "boundary_read", "boundary_serve"])
def test_at_most_one_open_offer_across_read_and_job_interleavings(tmp_path, draw, monkeypatch, outer, inner, outer_draws,
                                                                  inner_draws):
    env, row = _miss_env(tmp_path)
    _to_boundary(env, draw)
    _author_refuses(monkeypatch)
    prefer = {"lesson": (OFFER,), "other": (*OTHER, INSERT_NOW)}
    draw.never_stop = True
    other_row = _second_workflow(env) if inner == "job" and outer == "job" else row
    answers: list[bool] = []

    def run_inner():
        draw.prefer = prefer[inner_draws]
        if inner == "read":
            advance(env, serve=False)
        else:
            _run_lane(env, other_row, monkeypatch)
        assert len(open_offers(env)) <= 1
        draw.prefer = prefer[outer_draws]

    if outer == "job":
        _during(monkeypatch, ObjectiveFollowupGate, "decide_followup", run_inner)
        _run_lane(env, row, monkeypatch)
    else:
        _during(monkeypatch, E, "decide", run_inner)
        advance(env, serve=outer == "boundary_serve")
    assert len(open_offers(env)) <= 1
    # Reads alone change nothing further, and answering what stands is one observation, whatever was replaced on the way.
    settled = open_offers(env)
    for _ in range(3):
        env.clock.advance(1)
        advance(env, serve=False)
        assert open_offers(env) == settled
    if settled:
        offer = E.latest_today(env).open_lesson_offer()
        SG.respond(env.vault, env.repository, decision_id=offer.decision_ref, response="declined", clock=env.clock)
        answers.append(False)
    assert _observations(env) == answers
    for decision in (*rows(env, "plan_block"), *rows(env, "plan_interrupt")):
        if decision["policy"] == "router_objective_v1" and decision["propensity_kind"] == "exact":
            _assert_exact_mu(decision)


def test_off_a_draw_racing_a_draw_is_the_predecessors(tmp_path, draw, monkeypatch):
    """The kill switch: nothing here ends an offer and nothing is dropped quietly. The read keeps mvp-0.54's write, which
    the ordinal's unique index stops, and the failed call wrote nothing."""

    import sqlite3

    env, _row = _miss_env(tmp_path, toml=OFF_NO_CHECKS)
    _to_boundary(env, draw)
    draw.prefer = (OFFER,)
    _during(monkeypatch, E, "decide", lambda: advance(env, serve=False))
    with pytest.raises(sqlite3.IntegrityError):
        advance(env, serve=False)
    assert len(open_offers(env)) == 1


# -- R2-m2: a workflow with nothing written moves with the offer -------------------------------------------------------


def test_an_unwritten_workflow_waits_on_the_offer_that_replaced_the_one_it_lost_to(tmp_path, draw, monkeypatch):
    env, row = _miss_env(tmp_path)
    _to_boundary(env, draw)
    draw.prefer = (OFFER,)
    author = _run_lane(env, row, monkeypatch)
    assert author.calls == 0
    old = rows(env, "plan_interrupt")[-1]
    assert wf.lost_offer_decision(env.repository, "fw_miss") == old["id"]
    # A written probe arrives, and the contest it starts replaces the offer with a new one.
    monkeypatch.setattr(wf, "waiting_still_valid", lambda *_a, **_k: True)
    second = _second_workflow(env)
    planned = {entry.practice_item_id for entry in E.latest_today(env).items()}
    probe = sorted(item for item in env.vault.practice_items if item not in planned and item != FOLLOWUP_ITEM)[1]
    wf.move(env.repository, second["id"], to_state=wf.READY, reason="test", practice_item_id=probe, factor_id="f",
            clock=env.clock)
    env.clock.advance(1)
    _record, step = advance(env, serve=False)
    new = rows(env, "plan_block")[-1]
    assert step["kind"] == "lesson_offer" and new["chosen_ref"] == OFFER and new["id"] != old["id"]
    # The next read finds it waiting on the new offer: not reopened, so no job pays for a question while a lesson stands.
    env.clock.advance(1)
    _record, again = advance(env, serve=False)
    assert again["block_id"] == step["block_id"]
    moved = wf.get(env.repository, "fw_miss")
    assert moved["state"] == wf.WAITING and moved["chosen_ref"] == OFFER and not moved["practice_item_id"]
    assert wf.lost_offer_decision(env.repository, "fw_miss") == new["id"]
    with env.repository.connection() as connection:
        assert store.generation_job(connection, "workflow:fw_miss") is None or \
            store.generation_job(connection, "workflow:fw_miss")["state"] != "queued"
    # Its one further decision comes only after this offer passes, and names the decision it lost.
    SG.respond(env.vault, env.repository, decision_id=new["id"], response="declined", clock=env.clock)
    env.clock.advance(1)
    advance(env, serve=False)
    assert wf.get(env.repository, "fw_miss")["state"] == wf.PENDING
