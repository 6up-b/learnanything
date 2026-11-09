"""Instruct hand-off IH2 (docs/specs/spec_instruct_handoff_v1.md §5, §10): a lesson offer and a follow-up compete in one
logged decision wherever a lesson is available. The owner's decision of Nov 8: "lessons should compete with follow ups
whenever a lesson is available"; and no rule maps a score, a miss count or a stuck flag to an action.

Replays the Nov 7-8 trace's shape: a probe arriving during an open offer gets a new decision holding both, with exact
propensities, never a ``withdrawn`` block with reason ``forced_items``. Fakes only; no model call.
"""

from __future__ import annotations

import ast
from dataclasses import replace
import json
import pathlib
from types import SimpleNamespace
from typing import Any

import pytest

from learnloop.algorithm_versions import FAILURE_SHARE_ALGORITHM_VERSION, PHONE_PROBES_ALGORITHM_VERSION
from learnloop.config.schema import RouterObjectiveConfig
from learnloop.daily_plan import engine as E
from learnloop.daily_plan import lesson_offer as LO
from learnloop.daily_plan import lesson_suggestion as SG
from learnloop.daily_plan.engine import advance, build_plan
from learnloop.daily_plan.objective_chooser import objective_settings
from learnloop.daily_plan.router_chooser import CONTINUE_CURRENT, INSERT_NOW, NO_INTERVENTION
from learnloop.db.stores import followup_serve as store
from learnloop.db.stores import router_suggestions as suggestions
from learnloop.followup_run import jobs, router, serving
from learnloop.followup_serve import workflow as wf
from learnloop.params.parameter_registry import classify_config_path
from learnloop.router import lesson_suggestions as LS
from learnloop.router.outcomes import derive_router_outcomes
from learnloop.router_objective import mix
from learnloop.router_objective.value import PROBE, REPAIR
from learnloop.router_objective_switches import lessons_compete_with_followups_on
from learnloop.scheduling.device_eligibility import PlanStepFilter

from tests.daily_plan_fakes import record_attempt, scheduled
from tests.followup_serve_helpers import AuthorFake
from tests.router_mixture_helpers import mixture_env, rows
from tests.router_model_fakes import fake_runtime
from tests.test_daily_plan_build import _wide_items
from tests.test_te3b_offers import OFFER, offerable  # noqa: F401 - the fixture

TAG = FAILURE_SHARE_ALGORITHM_VERSION
OLD = PHONE_PROBES_ALGORITHM_VERSION
QUIET = "[router_objective]\nstop_coin = 0.0\n"
OFF = "[router_objective]\nstop_coin = 0.0\nlessons_compete_with_followups = false\n"
#: No day's check block in the way: these tests need an ordinary block with questions left.
NO_CHECKS = '[router_objective]\nstop_coin = 0.0\ncheck_rate = "off"\n'
OFF_NO_CHECKS = NO_CHECKS + "lessons_compete_with_followups = false\n"
FOLLOWUP_ITEM = "pi_diag_mid"

pytestmark = pytest.mark.usefixtures("offerable")


@pytest.fixture
def draw(monkeypatch):
    """Which ref the mix serves: the first of ``draw.prefer`` in the support (its probability the exact ``μ``, so G3 still
    holds); the uniforms are not reproduced, which no test here reads. Nothing named: the real draw."""

    real = mix.draw
    control = SimpleNamespace(prefer=(), never_stop=False)

    def fake(support, parts, weights, epsilon, seed):
        drawn = real(support, parts, weights, epsilon, seed)
        for ref in control.prefer:
            match = next((option for option in support if str(option).startswith(ref)), None)
            if match is not None:
                return replace(drawn, chosen=match, propensity=drawn.pi[match])
        if control.never_stop and drawn.chosen == "stop_for_today":
            other = next(ref for ref in support if ref != "stop_for_today")
            return replace(drawn, chosen=other, propensity=drawn.pi[other])
        return drawn

    monkeypatch.setattr(mix, "draw", fake)
    return control


def _env(tmp_path, *, version: str = TAG, toml: str = QUIET, session_id: str = "s1", items: Any = None):
    return mixture_env(tmp_path, fake_runtime(), version=version, toml=toml, items=items, session_id=session_id)


def _objective_rows(env, kind: str = "plan_block") -> list[dict[str, Any]]:
    return [row for row in rows(env, kind) if row["policy"] == mix.POLICY]


def _open_offer(env, draw) -> dict[str, Any]:
    """Serve and answer until the feedback prefetch draws the objective's first boundary: the offer, open and unanswered
    (the Nov 8 trace's 12:37 pm draw)."""

    draw.prefer = (OFFER,)
    for _ in range(8):
        _record, step = advance(env, serve=True)
        assert step is not None and step["kind"] == "item"
        env.clock.advance(2)
        record_attempt(env.repository, step["practice_item_id"], step["learning_object_id"], env.clock.now(),
                       session_id=env.session_id)
        _record, step = advance(env, serve=False)
        if _objective_rows(env):
            assert step["kind"] == "lesson_offer"
            return step
    raise AssertionError("the objective never decided a boundary")


def _ready_probe(env, *, item: str | None = None, held: int = 1, decision: str | None = None,
                 chosen: str | None = None) -> dict[str, Any]:
    """A real workflow whose generated probe became ready while the offer waits (the workflow path)."""

    record = E.latest_today(env)
    planned = {entry.practice_item_id for entry in record.items()}
    probe = item or sorted(item_id for item_id in env.vault.practice_items if item_id not in planned)[0]
    lo = str(env.vault.practice_items[probe].learning_object_id)
    record_attempt(env.repository, probe, lo, env.clock.now(), session_id=env.session_id)
    with env.repository.connection() as connection:
        attempt_id = connection.execute("SELECT id FROM practice_attempts ORDER BY created_at DESC, id DESC").fetchone()[0]
    with env.repository.atomic(), env.repository.connection() as connection:
        store.insert_workflow(connection, {
            "id": "fw_test", "source_attempt_id": attempt_id, "revision_key": "joint", "learning_object_id": lo,
            "session_id": env.session_id, "surface": "desktop", "origin": "practice", "feedback_held": held,
            "created_at": env.now_iso(),
        })
    wf.move(env.repository, "fw_test", to_state=wf.READY, reason="test", practice_item_id=probe, decision_id=decision,
            chosen_ref=chosen, factor_id="f", clock=env.clock)
    return wf.get(env.repository, "fw_test")


def _need_path_env(tmp_path, *, version: str = TAG, toml: str = QUIET):
    """The need path: a generated item the scheduler flags as a follow-up after the plan was built (Nov 8's probe)."""

    live = list(_wide_items())
    env = _env(tmp_path, version=version, toml=toml, items=lambda: list(live))
    return env, live


def _need_probe_arrives(live: list[Any]) -> str:
    live.insert(0, scheduled(FOLLOWUP_ITEM, "lo_diag", followup_kind="negative_surprise_followup"))
    return FOLLOWUP_ITEM


def _trace_of(connection: Any, decision_id: str) -> dict[str, Any]:
    return json.loads(connection.execute("SELECT trace_json FROM router_objective_traces WHERE decision_id = ?",
                                         (decision_id,)).fetchone()[0])


def _assert_exact_mu(row: dict[str, Any]) -> dict[str, float]:
    """G3: the logged mixture recomputes to the logged per-candidate probabilities, and the row's propensity is the
    chosen ref's."""

    mixture = row["detail_json"]["mixture"]
    mu = mix.recompute(mixture)
    assert abs(sum(mu.values()) - 1.0) < 1e-9
    logged = {entry["ref"]: entry["propensity"] for entry in row["candidates_json"] if entry["ref"] in mu}
    assert set(logged) == set(mu)
    for ref, value in mu.items():
        assert logged[ref] == pytest.approx(value, abs=1e-12), ref
    assert row["propensity"] == pytest.approx(mu[row["chosen_ref"]], abs=1e-12)
    return mu


# -- item 1: redraw instead of withdrawing -----------------------------------------------------------------------------


@pytest.mark.parametrize("path", ["workflow", "need"])
def test_a_probe_arriving_during_an_open_offer_gets_a_new_decision_holding_both(tmp_path, draw, path):
    """The Nov 8 trace's shape. Never a ``withdrawn`` block with reason ``forced_items``."""

    if path == "workflow":
        env = _env(tmp_path)
        step = _open_offer(env, draw)
        probe = _ready_probe(env)["practice_item_id"]
    else:
        env, live = _need_path_env(tmp_path)
        step = _open_offer(env, draw)
        probe = _need_probe_arrives(live)
    first_decision, first_block = step["offer"]["decision_id"], step["block_id"]
    before = len(_objective_rows(env))
    env.clock.advance(1)
    draw.prefer = ("followup_contest:",)
    _record, served = advance(env, serve=True)
    assert served["kind"] == "item" and served["practice_item_id"] == probe and served["origin"] == "followup"
    new = _objective_rows(env)[before:]
    assert len(new) == 1
    support = new[0]["detail_json"]["mixture"]["support"]
    assert support == [f"followup_contest:{probe}", OFFER]
    mu = _assert_exact_mu(new[0])
    assert all(value > 0.0 for value in mu.values())
    assert new[0]["chosen_ref"] == f"followup_contest:{probe}" and new[0]["propensity_kind"] == "exact"
    assert new[0]["detail_json"]["followup_contest"]["item_ids"] == [probe]
    # The numeric policy answered on the contest (a failure there would be swallowed into a fallback).
    assert "numeric" not in new[0]["detail_json"]["mixture"]["failed"]
    assert new[0]["detail_json"]["mixture"]["numeric_choice"] in support
    # The unanswered offer records the newer decision, and it is the plan's act, not the learner's answer.
    with env.repository.connection() as connection:
        assert suggestions.response_for(connection, first_decision) is None
        row = LO.withdrawn(connection, first_decision)
        assert LO.sweep_ignored(connection, today=env.today(), now_iso=env.now_iso()) == 0
    detail = json.loads(row["detail_json"])
    assert row["response"] == "expired" and detail[LO.SUPERSEDED_BY] == new[0]["id"]
    assert LO.WITHDRAWN not in detail
    ended = next(block for block in E.latest_today(env).blocks if block.id == first_block)
    assert ended.outcome == LO.SUPERSEDED != LO.WITHDRAWN and ended.ended_reason == LO.SUPERSEDED_BY
    assert ended.items == []
    # A late answer on the card is refused.
    with pytest.raises(SG.SuggestionError) as refused:
        SG.respond(env.vault, env.repository, decision_id=first_decision, response="accepted", clock=env.clock)
    assert refused.value.code == "not_found"


def test_the_acceptance_model_never_reads_a_superseded_offer(tmp_path, draw):
    env = _env(tmp_path)
    _open_offer(env, draw)
    _ready_probe(env)
    env.clock.advance(1)
    draw.prefer = ("followup_contest:",)
    advance(env, serve=True)
    with env.repository.connection() as connection:
        decisions = suggestions.all_decisions(connection)
        details = {str(d["id"]): d["detail"] for d in decisions}
        assert LS.replay(LS.observations(details, suggestions.responses(connection))).updates == 0


def test_the_contest_values_a_generated_probe_with_rous_probe_interface_and_nothing_new(tmp_path, draw):
    env = _env(tmp_path)
    _open_offer(env, draw)
    probe = _ready_probe(env)["practice_item_id"]
    mode = env.vault.practice_items[probe].practice_mode
    env.clock.advance(1)
    draw.prefer = ("followup_contest:",)
    advance(env, serve=True)
    row = _objective_rows(env)[-1]
    with env.repository.connection() as connection:
        trace = _trace_of(connection, row["id"])
    entry = trace["candidates"][f"followup_contest:{probe}"]
    # A wide-vault item in practice mode is valued as a repair; a generated probe's mode gets the bundle (next test).
    assert entry["kind"] == (PROBE if mode in {"diagnostic_probe", "diagnostic_microprobe", "probe"} else REPAIR)
    assert trace["followup_contest"]["offer_declined_branch"].startswith("the follow-up")
    assert trace["stop_in_support"] is False
    # The offer's two branches are still its accepted and declined ones, the declined one now the follow-up.
    assert set(trace["candidates"][OFFER]["branches"]) >= {"accepted", "declined", "p_accept"}


# -- item 2: requested items and randomized checks stay forced ----------------------------------------------------------


def test_only_followups_compete_a_request_or_a_check_stays_forced(tmp_path):
    env = _env(tmp_path)
    plain = SimpleNamespace(practice_item_id="pi_x", requested=False, check_kind=None, lane="repair", est_minutes=1.0,
                            learning_object_id="lo_diag")
    assert E._followups_compete(env, [plain], E.ORIGIN_FOLLOWUP) is True
    assert E._followups_compete(env, [plain], E.ORIGIN_REQUESTED) is False
    assert E._followups_compete(env, [SimpleNamespace(**{**vars(plain), "requested": True})], E.ORIGIN_FOLLOWUP) is False
    assert E._followups_compete(env, [SimpleNamespace(**{**vars(plain), "check_kind": "check_once"})], E.ORIGIN_FOLLOWUP) is False


def test_a_requested_item_is_placed_at_the_build_with_no_offer_beside_it(tmp_path, draw):
    env = _env(tmp_path, toml=NO_CHECKS)
    env.repository.requested_practice_item_ids = lambda *, skip_commitment_ids=(): ["pi_r1a"]
    draw.prefer = (OFFER,)
    build_plan(env, kind="normal", budget=25.0, remembered=25, minutes_source="chip")
    decision = _objective_rows(env)[0]
    assert [entry["practice_item_id"] for entry in decision["detail_json"]["forced"]] == ["pi_r1a"]
    assert decision["detail_json"]["lesson_offers"]["status"] == "none:forced_items"
    assert not any(str(ref).startswith("lesson_offer:") for ref in decision["detail_json"]["mixture"]["support"])


def test_the_days_check_is_placed_before_the_contest_is_asked(tmp_path, draw, monkeypatch):
    """RO5's block is the rules': a check due at this boundary is administered before any decision, with the follow-ups
    first in it (``tests/test_ro5_*``). Here, the order at a boundary that has follow-ups."""

    env = _env(tmp_path)
    _open_offer(env, draw)
    probe = _ready_probe(env)["practice_item_id"]
    order: list[str] = []
    real_check, real_compete = E._randomized_check_block, E._followups_compete

    def check(env_, record, context, **kwargs):
        order.append("check")
        assert [item.practice_item_id for item in kwargs["forced"]] == [probe]
        return real_check(env_, record, context, **kwargs)

    def compete(*args, **kwargs):
        order.append("compete")
        return real_compete(*args, **kwargs)

    monkeypatch.setattr(E, "_randomized_check_block", check)
    monkeypatch.setattr(E, "_followups_compete", compete)
    env.clock.advance(1)
    draw.prefer = ("followup_contest:",)
    advance(env, serve=True)
    assert order == ["check", "compete"]


# -- a lesson win: held feedback released, nothing generated -------------------------------------------------------------


def test_a_lesson_win_over_a_ready_probe_releases_what_was_held_and_the_probe_waits(tmp_path, draw):
    env = _env(tmp_path)
    step = _open_offer(env, draw)
    row = _ready_probe(env)
    assert serving.is_holding(row)
    env.clock.advance(1)
    before = len(_objective_rows(env))
    draw.prefer = (OFFER,)
    _record, served = advance(env, serve=True)
    assert served["kind"] == "lesson_offer" and served["block_id"] != step["block_id"]
    new = _objective_rows(env)[before:]
    assert len(new) == 1 and new[0]["chosen_ref"] == OFFER
    _assert_exact_mu(new[0])
    assert new[0]["detail_json"].get("items") == []
    after = wf.get(env.repository, "fw_test")
    assert after["state"] == wf.WAITING and after["chosen_ref"] == OFFER
    assert after["feedback_released_at"] and after["release_reason"] == wf.RELEASE_LESSON_OFFER
    assert after["exposed_at"], "a probe served later can't settle the cause"
    assert not serving.is_holding(after)
    # Next on the feedback goes on, and the view says nobody is waiting.
    action = serving.next_action(env.vault, env.repository, row["source_attempt_id"], plan_serves=True, clock=env.clock)
    assert action.action == "continue"
    assert serving.view(env.vault, env.repository, row["source_attempt_id"])["line"] is None
    # While the new offer is open no further decision re-runs the contest, however often the plan is read.
    for _ in range(3):
        _record, again = advance(env, serve=False)
        assert again["kind"] == "lesson_offer" and again["block_id"] == served["block_id"]
    assert len(_objective_rows(env)) == before + 1


def test_a_probe_win_serves_as_before_and_releases_nothing(tmp_path, draw):
    env = _env(tmp_path)
    _open_offer(env, draw)
    row = _ready_probe(env)
    env.clock.advance(1)
    draw.prefer = ("followup_contest:",)
    _record, served = advance(env, serve=True)
    assert served["kind"] == "item" and served["practice_item_id"] == row["practice_item_id"]
    after = wf.get(env.repository, "fw_test")
    assert after["state"] == wf.READY and serving.is_holding(after) and not after["exposed_at"]
    assert E.followup_placement(E.latest_today(env), row["practice_item_id"]) == E.FOLLOWUP_LIVE


# -- after "Not now" ----------------------------------------------------------------------------------------------------


def test_not_now_leaves_a_ready_probe_available_to_the_next_decision(tmp_path, draw, monkeypatch):
    monkeypatch.setattr(wf, "waiting_still_valid", lambda *_a: True)  # the stand-in factor; revalidated as any wait
    env = _env(tmp_path)
    _open_offer(env, draw)
    row = _ready_probe(env)
    env.clock.advance(1)
    draw.prefer = (OFFER,)
    _record, offer = advance(env, serve=True)
    SG.respond(env.vault, env.repository, decision_id=offer["offer"]["decision_id"], response="declined", clock=env.clock)
    # A lesson still available: it competes again, and neither vanishes nor is force-served.
    draw.prefer = ("followup_contest:",)
    before = len(_objective_rows(env))
    env.clock.advance(1)
    _record, served = advance(env, serve=True)
    new = _objective_rows(env)[before:]
    assert served["kind"] == "item" and served["practice_item_id"] == row["practice_item_id"]
    assert len(new) == 1 and new[0]["detail_json"]["mixture"]["support"][0].startswith("followup_contest:")


def test_not_now_with_the_ceiling_reached_the_followup_serves(tmp_path, draw, monkeypatch):
    """No lesson available at the next decision: the Nov 3 behaviour stands (the ceiling still binds, and is logged)."""

    monkeypatch.setattr(wf, "waiting_still_valid", lambda *_a: True)
    env = _env(tmp_path, toml=QUIET + "\n[router.lesson_suggestions]\nceiling_per_day = 2\n")
    _open_offer(env, draw)
    row = _ready_probe(env)
    env.clock.advance(1)
    draw.prefer = (OFFER,)
    _record, offer = advance(env, serve=True)  # the day's second offer
    SG.respond(env.vault, env.repository, decision_id=offer["offer"]["decision_id"], response="declined", clock=env.clock)
    env.clock.advance(1)
    _record, served = advance(env, serve=True)
    assert served["kind"] == "item" and served["practice_item_id"] == row["practice_item_id"]
    last = _objective_rows(env)[-1]
    assert last["detail_json"]["lesson_offers"]["status"] == "none:ceiling_bound"
    assert not any(str(ref).startswith("lesson_offer:") for ref in last["detail_json"]["mixture"]["support"])


def test_not_now_on_the_need_path_leaves_the_item_in_the_pool(tmp_path, draw):
    env, live = _need_path_env(tmp_path)
    _open_offer(env, draw)
    probe = _need_probe_arrives(live)
    env.clock.advance(1)
    draw.prefer = (OFFER,)
    _record, offer = advance(env, serve=True)
    assert offer["kind"] == "lesson_offer"
    block = next(b for b in E.latest_today(env).blocks if b.id == offer["block_id"])
    assert block.followups_lost == (probe,)
    SG.respond(env.vault, env.repository, decision_id=offer["offer"]["decision_id"], response="declined", clock=env.clock)
    draw.prefer = ("followup_contest:",)
    env.clock.advance(1)
    _record, served = advance(env, serve=True)
    assert served["practice_item_id"] == probe


def test_taking_the_lesson_settles_the_followup_honestly(tmp_path, draw):
    env = _env(tmp_path)
    _open_offer(env, draw)
    row = _ready_probe(env)
    env.clock.advance(1)
    draw.prefer = (OFFER,)
    _record, offer = advance(env, serve=True)
    SG.respond(env.vault, env.repository, decision_id=offer["offer"]["decision_id"], response="accepted", clock=env.clock)
    env.clock.advance(1)
    advance(env, serve=False)
    after = wf.get(env.repository, "fw_test")
    assert after["state"] == wf.SETTLED and not serving.is_holding(after)
    with env.repository.connection() as connection:
        assert [event["reason"] for event in store.workflow_events(connection, "fw_test")][-1] == "lesson_taken"
    # Never served as this follow-up (the stand-in item is an ordinary one, so the pool may still plan it as itself).
    assert not any(item.practice_item_id == row["practice_item_id"] and item.origin == "followup"
                   for item in E.latest_today(env).active_items())


# -- item 3: after a miss the post-feedback Next is a real decision ------------------------------------------------------


def _answer(env, *, questions_left: bool = True) -> dict[str, Any]:
    """Build the plan, then serve and answer a question, with no lesson available and no stop drawn on the way (the draws
    are live, and what comes after is what the test is about). ``questions_left``: until an answer leaves questions in
    its block, since a block may hold one."""

    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(SG, "build_candidates", lambda vault, repository, *, now_iso: ([], {}))
        real = mix.draw

        def never_stop(support, parts, weights, epsilon, seed):
            drawn = real(support, parts, weights, epsilon, seed)
            if drawn.chosen != "stop_for_today":
                return drawn
            other = next(ref for ref in support if ref != "stop_for_today")
            return replace(drawn, chosen=other, propensity=drawn.pi[other])

        patch.setattr(mix, "draw", never_stop)
        build_plan(env, kind="normal", budget=25.0, remembered=25, minutes_source="chip")
        for _ in range(12):
            _record, step = advance(env, serve=True)
            assert step is not None and step["kind"] == "item"
            env.clock.advance(1)
            record_attempt(env.repository, step["practice_item_id"], step["learning_object_id"], env.clock.now(),
                           session_id=env.session_id)
            env.clock.advance(1)
            block = next(b for b in E.latest_today(env).blocks if b.id == step["block_id"])
            if not questions_left or any(item.practice_item_id != step["practice_item_id"] and not item.resolved
                                         for item in block.items):
                return step
    raise AssertionError("no block held a second question")


def _miss_env(tmp_path, *, version: str = TAG, toml: str = NO_CHECKS, questions_left: bool = False):
    env = mixture_env(tmp_path, fake_runtime(), version=version, toml=toml, items=lambda: list(_wide_items()))
    step = _answer(env, questions_left=questions_left)
    with env.repository.connection() as connection:
        attempt_id = connection.execute("SELECT id FROM practice_attempts ORDER BY created_at DESC, id DESC").fetchone()[0]
    with env.repository.atomic(), env.repository.connection() as connection:
        store.insert_workflow(connection, {
            "id": "fw_miss", "source_attempt_id": attempt_id, "revision_key": "joint",
            "learning_object_id": step["learning_object_id"], "session_id": env.session_id, "surface": "desktop",
            "origin": "practice", "feedback_held": 1, "created_at": env.now_iso(),
        })
    return env, wf.get(env.repository, "fw_miss")


def _author_refuses(monkeypatch) -> None:
    """The author is reached (the decision came first, and the lesson lost) and its question is refused: the arm's own
    path ends there, with nothing of the workflow's probe machinery needed."""

    from learnloop.followup_run import admission

    def refuse(*_a, **_k):
        raise admission.OfferRefused("author_reached")

    monkeypatch.setattr(admission, "author_probe", refuse)


def _run_lane(env, row, monkeypatch, author: Any = None) -> AuthorFake:
    """The generation slot's decision and whatever follows it, on the standing plan."""

    author = author or AuthorFake()
    monkeypatch.setattr(router, "hard_refusal", lambda *_a, **_k: None)
    monkeypatch.setattr(router, "_card_facts", lambda *_a, **_k: [])
    monkeypatch.setattr(router, "observational", lambda *_a, **_k: {})
    monkeypatch.setattr(jobs.identity, "retire_unbound", lambda *_a, **_k: None)

    def context(*_a, **_k):
        from learnloop.daily_plan.objective_chooser import ObjectiveFollowupGate

        restraint = env.policy.restraint
        record = E.get_or_create_today(env, create=False)
        gate = ObjectiveFollowupGate(env.vault, env.repository, restraint.runtime, frame=restraint.frame,
                                     card_builder=restraint.card_builder, session_id=env.session_id, clock=env.clock,
                                     may_defer=False)
        return env, record, gate

    monkeypatch.setattr(router, "_plan_context", context)
    clients = SimpleNamespace(author=author, authoring=None, runtime=env.policy.restraint.runtime)
    choice = SimpleNamespace(factor_id="f", hypothesis_ids=())
    jobs._run_probe_lane(env.vault, env.repository, row, choice=choice, clients=clients, clock=env.clock)
    return author


def test_a_lesson_win_after_a_miss_generates_nothing_and_the_offer_page_opens_from_next(tmp_path, draw, monkeypatch):
    env, row = _miss_env(tmp_path)
    draw.prefer = (OFFER,)
    author = _run_lane(env, row, monkeypatch)
    assert author.calls == 0, "a lesson that wins costs no generation"
    decision = rows(env, "plan_interrupt")[-1]
    assert decision["policy"] == mix.POLICY and decision["chosen_ref"] == OFFER and decision["propensity_kind"] == "exact"
    assert set(decision["detail_json"]["mixture"]["support"]) >= {INSERT_NOW, OFFER}
    assert "numeric" not in decision["detail_json"]["mixture"]["failed"]
    _assert_exact_mu(decision)
    after = wf.get(env.repository, "fw_miss")
    assert after["state"] == wf.WAITING and not after["practice_item_id"] and after["chosen_ref"] == OFFER
    assert after["release_reason"] == wf.RELEASE_LESSON_OFFER and not serving.is_holding(after)
    # Feedback's Next goes on, and the plan's next step is the offer page's, with the rest of the block after it.
    action = serving.next_action(env.vault, env.repository, row["source_attempt_id"], plan_serves=True, clock=env.clock)
    assert action.action == "continue"
    _record, step = advance(env, serve=True)
    assert step["kind"] == "lesson_offer" and step["offer"]["decision_id"] == decision["id"]
    assert step["offer"]["suggestion"]["learning_object_ids"] == ["lo_diag"]
    with env.repository.connection() as connection:
        assert store.bindings_for_decision(connection, decision["id"])["outcome"]["outcome"] == "lesson_offer"
    assert wf.desktop_waiting_count(env.repository) == 0


def test_not_now_after_a_miss_goes_back_to_a_new_decision_and_the_block_resumes(tmp_path, draw, monkeypatch):
    env, row = _miss_env(tmp_path, questions_left=True)
    draw.prefer = (OFFER,)
    _run_lane(env, row, monkeypatch)
    lost = rows(env, "plan_interrupt")[-1]
    _record, offer = advance(env, serve=True)
    below = E.latest_today(env).block_below_offer()
    assert below is not None and any(not item.resolved for item in below.items)
    SG.respond(env.vault, env.repository, decision_id=offer["offer"]["decision_id"], response="declined", clock=env.clock)
    env.clock.advance(1)
    _record, resumed = advance(env, serve=True)
    # The block it interrupted resumes at once ...
    assert resumed["kind"] == "item" and resumed["block_id"] == below.id
    # ... and the follow-up, with nothing generated yet, is back at its decision on the generation slot.
    reopened = wf.get(env.repository, "fw_miss")
    assert reopened["state"] == wf.PENDING and not reopened["chosen_ref"] and not reopened["decision_id"]
    assert reopened["exposed_at"] and not serving.is_holding(reopened)
    action = serving.next_action(env.vault, env.repository, row["source_attempt_id"], plan_serves=True, clock=env.clock)
    assert action.action == "continue", "nobody waits on a question whose feedback is already out"
    with env.repository.connection() as connection:
        job = store.generation_job(connection, "workflow:fw_miss")
    assert job["state"] == "queued" and int(job["attempt_count"]) == 0
    # A new draw is a new receipt naming the decision it lost, and the row it lost stays as it was.
    draw.prefer = (INSERT_NOW,)
    outcome = router.decide_once(env.vault, env.repository, reopened, choice=SimpleNamespace(factor_id="f", hypothesis_ids=()),
                                 clients=SimpleNamespace(runtime=env.policy.restraint.runtime), clock=env.clock)
    latest = rows(env, "plan_interrupt")[-1]
    assert outcome.chosen_ref == INSERT_NOW and latest["id"] != lost["id"] and latest["parent_decision_id"] == lost["id"]
    assert rows(env, "plan_interrupt")[-2]["chosen_ref"] == OFFER


def test_a_probe_win_after_a_miss_generates_and_serves_as_before(tmp_path, draw, monkeypatch):
    env, row = _miss_env(tmp_path)
    draw.prefer = (INSERT_NOW,)
    _author_refuses(monkeypatch)
    _run_lane(env, row, monkeypatch)
    decision = rows(env, "plan_interrupt")[-1]
    assert decision["chosen_ref"] == INSERT_NOW and decision["propensity_kind"] == "exact"
    _assert_exact_mu(decision)
    # The author was reached: the decision came first, the lesson lost, and the question is written as before.
    after = wf.get(env.repository, "fw_miss")
    assert after["state"] == wf.REFUSED
    with env.repository.connection() as connection:
        assert [row["reason"] for row in store.workflow_events(connection, "fw_miss")][-1] == "author_reached"


def test_the_followup_decision_values_the_unwritten_probe_with_the_probe_interface(tmp_path, draw, monkeypatch):
    env, row = _miss_env(tmp_path)
    draw.prefer = (OFFER,)
    _run_lane(env, row, monkeypatch)
    decision = rows(env, "plan_interrupt")[-1]
    with env.repository.connection() as connection:
        trace = _trace_of(connection, decision["id"])
    assert trace["candidates"][OFFER]["kind"] == "lesson"
    assert trace["candidates"][OFFER]["offer"]["sensors"]["p_accept"]["mean"] is not None
    # The stand-in is valued by RO §8.1's probe interface: as the bundle, or a step of a sequence when questions are left.
    assert trace["candidates"][INSERT_NOW]["kind"] in {"sequence", PROBE}


def test_a_question_not_yet_written_takes_the_probe_interface_only_with_the_lesson_in_the_support(tmp_path):
    from learnloop.daily_plan import objective_inputs as OI
    from learnloop.daily_plan.types import BlockCandidate

    env = _env(tmp_path)
    plain = BlockCandidate(candidate_id=INSERT_NOW, lane="repair", action="practice", subtype=None,
                           learning_object_ids=("lo_diag",), item_ids=("followup:fw",), reading=None, est_minutes=2.0,
                           planner_value=0.0, reason="r")
    assert OI.action_for(env.vault, env.repository, plain, practiced=set(), spread=0.0).kind == REPAIR
    marked = replace(plain, annotations={OI.FOLLOWUP_PROBE_NOTE: True})
    action = OI.action_for(env.vault, env.repository, marked, practiced=set(), spread=0.0)
    assert action.kind == PROBE and action.repair is not None and action.repair.kind == REPAIR


def test_no_lesson_available_the_followup_decision_is_the_predecessors(tmp_path, draw, monkeypatch):
    monkeypatch.setattr(SG, "build_candidates", lambda vault, repository, *, now_iso: ([], {}))
    env, row = _miss_env(tmp_path)
    draw.prefer = (INSERT_NOW,)
    _author_refuses(monkeypatch)
    _run_lane(env, row, monkeypatch)
    decision = rows(env, "plan_interrupt")[-1]
    assert set(decision["detail_json"]["mixture"]["support"]) == {INSERT_NOW, CONTINUE_CURRENT, NO_INTERVENTION}
    assert decision["detail_json"]["lesson_offers"]["status"] == "none:no_candidate"
    assert not any(entry["kind"] == "lesson_offer" for entry in decision["candidates_json"])


def test_with_no_room_to_wait_a_lesson_makes_it_a_real_draw_and_with_none_it_stays_deterministic(tmp_path, draw, monkeypatch):
    env, row = _miss_env(tmp_path)
    record = E.latest_today(env)
    from learnloop.daily_plan.objective_chooser import ObjectiveFollowupGate

    restraint = env.policy.restraint
    gate = ObjectiveFollowupGate(env.vault, env.repository, restraint.runtime, frame=restraint.frame,
                                 card_builder=restraint.card_builder, session_id=env.session_id, clock=env.clock,
                                 may_defer=False)
    offer = E.interrupt_offer(env, record, None)
    assert offer.candidate is not None
    draw.prefer = (OFFER,)
    outcome = gate.decide_followup(record, None, row, wait_feasible=False, offer=offer)
    assert outcome.record["mixture"]["support"] == [INSERT_NOW, OFFER] and 0.0 < outcome.propensity < 1.0
    assert outcome.chosen_ref == OFFER and outcome.record["objective_followup"]["support"] == [INSERT_NOW, OFFER]
    alone = gate.decide_followup(record, None, row, wait_feasible=False)
    assert alone.chosen_ref == INSERT_NOW and alone.propensity == 1.0 and alone.record["policy"] == "staged_v1"


def test_an_offer_never_interrupts_a_check_or_a_probe(tmp_path, draw):
    env, _row = _miss_env(tmp_path)
    record = E.latest_today(env)
    block = next(b for b in record.blocks if any(not i.resolved for i in b.items))
    assert E._offer_may_interrupt(env, block) is True
    first = next(i for i in block.items if not i.resolved)
    first.origin = E.ro5_check_origin()
    assert E._offer_may_interrupt(env, block) is False
    first.origin = "chooser"
    first.check_kind = "check_once"
    assert E._offer_may_interrupt(env, block) is False


def test_while_an_offer_is_open_a_followups_decision_holds_no_second_offer(tmp_path, draw):
    env = _env(tmp_path)
    _open_offer(env, draw)
    record = E.latest_today(env)
    assert record.open_lesson_offer() is not None
    assert E.interrupt_offer(env, record, record.current_block()) is None


def test_the_need_paths_mid_block_decision_gains_the_lesson_arm(tmp_path, draw, monkeypatch):
    live = list(_wide_items())
    env = _env(tmp_path, items=lambda: list(live), toml=NO_CHECKS)
    _answer(env)
    current = E.latest_today(env).current_block()
    probe = _need_probe_arrives(live)
    draw.prefer = (OFFER,)
    _record, offer = advance(env, serve=True)
    decision = rows(env, "plan_interrupt")[-1]
    assert offer["kind"] == "lesson_offer" and decision["chosen_ref"] == OFFER
    _assert_exact_mu(decision)
    assert decision["detail_json"]["offer_block_id"] == offer["block_id"]
    assert decision["chosen_practice_item_id"] is None
    block = next(b for b in E.latest_today(env).blocks if b.id == offer["block_id"])
    assert block.interrupts and block.followups_lost == (probe,)
    SG.respond(env.vault, env.repository, decision_id=decision["id"], response="declined", clock=env.clock)
    draw.prefer = (INSERT_NOW,)
    env.clock.advance(1)
    _record, served = advance(env, serve=True)
    assert served["practice_item_id"] == probe and served["block_id"] == current.id
    again = rows(env, "plan_interrupt")[-1]
    assert again["parent_decision_id"] == decision["id"] and again["chosen_ref"] == INSERT_NOW
    assert again["id"] != decision["id"] and again["receipt_key"] != decision["receipt_key"]


def test_a_followup_arriving_over_an_interrupting_offer_joins_the_block_below_and_the_offer_stands(tmp_path, draw, monkeypatch):
    live = list(_wide_items())
    env = _env(tmp_path, items=lambda: list(live), toml=NO_CHECKS)
    _answer(env)
    below = E.latest_today(env).current_block()
    first = _need_probe_arrives(live)
    draw.prefer = (OFFER,)
    _record, offer = advance(env, serve=True)
    live.insert(0, scheduled("pi_diag_easy", "lo_diag", followup_kind="negative_surprise_followup"))
    env.clock.advance(1)
    _record, again = advance(env, serve=False)
    assert again["kind"] == "lesson_offer" and again["block_id"] == offer["block_id"]
    record = E.latest_today(env)
    assert record.open_lesson_offer().id == offer["block_id"] and record.current_block().interrupts
    assert first not in {item.practice_item_id for item in below.items}
    with env.repository.connection() as connection:
        assert LO.withdrawn(connection, offer["offer"]["decision_id"]) is None


def test_an_interrupting_offer_never_comes_over_an_open_item(tmp_path, draw, monkeypatch):
    live = list(_wide_items())
    env = _env(tmp_path, items=lambda: list(live), toml=NO_CHECKS)
    _answer(env)
    _need_probe_arrives(live)
    draw.prefer = (OFFER,)
    _record, offer = advance(env, serve=True)
    record = E.latest_today(env)
    below = record.block_below_offer()
    open_item = next(item for item in below.items if not item.resolved)
    assert record.current_block().id == offer["block_id"]
    open_item.served_at = env.now_iso()  # served before the draw landed
    assert record.current_block().id == below.id


# -- a follow-up whose own decision already held a lesson -----------------------------------------------------------------


def test_a_probe_whose_decision_already_beat_the_lesson_is_not_contested_twice(tmp_path, draw, monkeypatch):
    env, row = _miss_env(tmp_path)
    draw.prefer = (INSERT_NOW,)
    _author_refuses(monkeypatch)
    _run_lane(env, row, monkeypatch)
    decision = rows(env, "plan_interrupt")[-1]
    assert any(str(ref).startswith("lesson_offer:") for ref in decision["detail_json"]["mixture"]["support"])
    env2 = _env(tmp_path / "second")
    _open_offer(env2, draw)
    probe_row = _ready_probe(env2, decision="d_no_lesson", chosen=INSERT_NOW)
    assert not E._lesson_already_competed(env2, probe_row["practice_item_id"])  # its decision held none
    wf.set_fields(env.repository, "fw_miss", practice_item_id="pi_x", clock=env.clock)
    assert E._lesson_already_competed(env, "pi_x")  # this one did


# -- the phone ----------------------------------------------------------------------------------------------------------


def test_a_phone_decision_holds_no_offer_and_serves_what_it_can(tmp_path, draw):
    env, live = _need_path_env(tmp_path)
    env.device = PlanStepFilter(device_filter=None)
    draw.prefer = (OFFER, "followup_contest:")
    for _ in range(8):
        _record, step = advance(env, serve=True)
        assert step is not None
        if _objective_rows(env):
            break
        assert step["kind"] == "item"
        env.clock.advance(2)
        record_attempt(env.repository, step["practice_item_id"], step["learning_object_id"], env.clock.now(),
                       session_id=env.session_id)
    row = _objective_rows(env)[-1]
    support = row["detail_json"]["mixture"]["support"]
    assert not any(str(ref).startswith(("lesson_offer:", "followup_contest:")) for ref in support)
    assert row["detail_json"]["lesson_offers"]["status"] == "none:device_serves_no_lesson"
    assert step["kind"] != "held_for_desktop", "a draw the phone can't serve would have held the step"


def test_a_phone_follow_up_stays_forced_beside_an_open_desktop_offer(tmp_path, draw):
    env, live = _need_path_env(tmp_path)
    step = _open_offer(env, draw)
    probe = _need_probe_arrives(live)
    env.device = PlanStepFilter(device_filter=None)
    env.clock.advance(1)
    _record, served = advance(env, serve=True)
    assert served["kind"] == "item" and served["practice_item_id"] == probe
    env.device = None
    with env.repository.connection() as connection:
        # The offer stays open for the desktop: the phone neither answers nor replaces it.
        assert suggestions.release_for(connection, step["offer"]["decision_id"]) is None
    assert E.latest_today(env).open_lesson_offer().id == step["block_id"]


def test_a_miss_on_the_phones_surface_decides_with_no_lesson_arm(tmp_path, draw, monkeypatch):
    env, row = _miss_env(tmp_path)
    with env.repository.atomic(), env.repository.connection() as connection:
        connection.execute("UPDATE followup_workflows SET surface = 'phone' WHERE id = 'fw_miss'")
    row = wf.get(env.repository, "fw_miss")
    draw.prefer = (OFFER,)
    _author_refuses(monkeypatch)
    _run_lane(env, row, monkeypatch)
    support = rows(env, "plan_interrupt")[-1]["detail_json"]["mixture"]["support"]
    assert not any(str(ref).startswith("lesson_offer:") for ref in support)


# -- switch off and below the tag: the predecessor exactly --------------------------------------------------------------


@pytest.mark.parametrize("version,toml", [(TAG, OFF), (OLD, QUIET)])
def test_off_or_below_the_tag_a_probe_withdraws_the_offer_as_the_predecessor(tmp_path, draw, version, toml):
    env = _env(tmp_path, version=version, toml=toml)
    step = _open_offer(env, draw)
    assert not lessons_compete_with_followups_on(env.vault.config)
    row = _ready_probe(env)
    env.clock.advance(1)
    before = len(_objective_rows(env))
    draw.prefer = (OFFER,)
    _record, served = advance(env, serve=True)
    assert served["kind"] == "item" and served["practice_item_id"] == row["practice_item_id"]
    with env.repository.connection() as connection:
        withdrawal = LO.withdrawn(connection, step["offer"]["decision_id"])
    assert json.loads(withdrawal["detail_json"])[LO.WITHDRAWN] == LO.WITHDRAWN_FORCED
    ended = next(b for b in E.latest_today(env).blocks if b.id == step["block_id"])
    assert ended.outcome == LO.WITHDRAWN and ended.ended_reason == LO.WITHDRAWN_FORCED
    new = _objective_rows(env)[before:]
    assert new, "the next boundary decided"
    for decision in new:
        assert not any(str(ref).startswith(("lesson_offer:", "followup_contest:"))
                       for ref in decision["detail_json"]["mixture"]["support"])
        assert decision["detail_json"]["lesson_offers"]["status"] == "none:forced_items"
    assert wf.get(env.repository, "fw_test")["release_reason"] is None


@pytest.mark.parametrize("version,toml", [(TAG, OFF_NO_CHECKS), (OLD, NO_CHECKS)])
def test_off_or_below_the_tag_the_followup_decision_is_the_predecessors(tmp_path, draw, monkeypatch, version, toml):
    env, row = _miss_env(tmp_path, version=version, toml=toml)
    draw.prefer = (INSERT_NOW,)
    _author_refuses(monkeypatch)
    _run_lane(env, row, monkeypatch)
    decision = rows(env, "plan_interrupt")[-1]
    assert set(decision["detail_json"]["mixture"]["support"]) == {INSERT_NOW, CONTINUE_CURRENT, NO_INTERVENTION}
    assert "lesson_offers" not in decision["detail_json"] and "offer_block_id" not in decision["detail_json"]
    assert [entry["ref"] for entry in decision["candidates_json"]] == [INSERT_NOW, CONTINUE_CURRENT, NO_INTERVENTION, "decline"]
    assert decision["parent_decision_id"] is None


def test_the_switch_defaults_on_is_classified_and_names_itself_in_the_prefetch_key(tmp_path):
    assert RouterObjectiveConfig().lessons_compete_with_followups is True
    rule = classify_config_path("router_objective.lessons_compete_with_followups")
    assert rule is not None and "kill switch" in rule.rationale and "IH2" in rule.rationale
    on = _env(tmp_path / "on")
    off = _env(tmp_path / "off", toml=OFF)
    below = _env(tmp_path / "below", version=OLD)
    assert objective_settings(on.vault.config)["lessons_compete_with_followups"] is True
    assert objective_settings(off.vault.config)["lessons_compete_with_followups"] is False
    assert "lessons_compete_with_followups" not in objective_settings(below.vault.config)
    assert lessons_compete_with_followups_on(on.vault.config)
    assert not lessons_compete_with_followups_on(off.vault.config)
    assert not lessons_compete_with_followups_on(below.vault.config)


# -- replay -------------------------------------------------------------------------------------------------------------


def test_replay_gives_every_logged_decision_its_logged_mu(tmp_path, draw, monkeypatch):
    """Every decision this stage logs, on a plain ledger read: the contest's and the follow-up's, won and lost."""

    env = _env(tmp_path)
    _open_offer(env, draw)
    _ready_probe(env)
    env.clock.advance(1)
    draw.prefer = (OFFER,)
    advance(env, serve=True)
    draw.prefer = ()
    env2, row = _miss_env(tmp_path / "miss")
    draw.prefer = (OFFER,)
    _run_lane(env2, row, monkeypatch)
    checked = 0
    for one in (env, env2):
        for kind in ("plan_block", "plan_interrupt"):
            for decision in _objective_rows(one, kind):
                if any(str(ref).startswith("lesson_offer:") for ref in decision["detail_json"]["mixture"]["support"]):
                    _assert_exact_mu(decision)
                    checked += 1
    assert checked >= 3
    # An interrupt's offer joins no item: its outcome row has no action, and the derivation reads it without error.
    with env2.repository.connection() as connection:
        outcomes = {row["decision_id"]: row for row in derive_router_outcomes(connection, reader_exposures=())}
    drawn = next(row for row in rows(env2, "plan_interrupt") if row["chosen_ref"] == OFFER)
    assert outcomes[drawn["id"]].get("action_attempt_id") is None


# -- no rule from a score to an action ----------------------------------------------------------------------------------


DECISION_MODULES = (
    "daily_plan/objective_chooser.py", "daily_plan/router_chooser.py", "daily_plan/lesson_offer.py", "daily_plan/policy.py",
    "followup_run/router.py", "router_objective/mix.py", "daily_plan/staged_frame.py",
)
EVIDENCE_WORDS = ("stuck", "correctness", "miss_count", "misses", "n_misses", "score_on_attempt", "last_score")


def _names_in(tree: ast.AST) -> set[str]:
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            found.add(node.id.lower())
        elif isinstance(node, ast.Attribute):
            found.add(node.attr.lower())
        elif isinstance(node, ast.Constant) and isinstance(node.value, str) and len(node.value) < 40:
            found.add(node.value.lower())
    return found


def test_no_decision_module_reads_a_score_or_a_stuck_flag():
    """Static: the modules that form a decision's support and its draw name none of these in any condition or call.
    A guard against a rule being added, with its limits in the module's report (spec §5 "As built")."""

    root = pathlib.Path(E.__file__).resolve().parents[1]
    for relative in DECISION_MODULES:
        tree = ast.parse((root / relative).read_text())
        conditions = [node.test for node in ast.walk(tree) if isinstance(node, (ast.If, ast.IfExp, ast.While, ast.Assert))]
        for condition in conditions:
            hit = _names_in(condition) & set(EVIDENCE_WORDS)
            assert not hit, f"{relative} branches on {hit}"


def test_a_stuck_miss_changes_no_support_and_the_draw_is_the_mix(tmp_path, draw, monkeypatch):
    """Behavioural: the same boundary after a stuck zero and after a full answer has the same support, and the choice is
    the logged draw's, not the evidence's: either arm serves under either history."""

    outcomes: dict[str, set[str]] = {}
    for label, correctness in (("zero", 0.0), ("full", 1.0)):
        for prefer in ("followup_contest:", OFFER):
            env = _env(tmp_path / f"{label}-{prefer.strip(':')}")
            _open_offer(env, draw)
            row = _ready_probe(env)
            with env.repository.atomic(), env.repository.connection() as connection:
                connection.execute("UPDATE practice_attempts SET correctness = ? WHERE id = ?",
                                   (correctness, row["source_attempt_id"]))
            env.clock.advance(1)
            draw.prefer = (prefer,)
            _record, served = advance(env, serve=True)
            decision = _objective_rows(env)[-1]
            support = tuple(ref.split(":")[0] for ref in decision["detail_json"]["mixture"]["support"])
            assert support == ("followup_contest", "lesson_offer")
            outcomes.setdefault(label, set()).add(served["kind"])
    assert outcomes["zero"] == outcomes["full"] == {"item", "lesson_offer"}


# -- the value of a real probe, and the job that runs again ---------------------------------------------------------------


def test_a_probe_mode_item_in_a_contest_is_valued_by_the_probe_bundle(tmp_path, draw, monkeypatch):
    """RO §8.1's interface on the real path: the kind is ``probe``, its bundle's branches are in the trace, and the
    numeric policy answered (its failure would be swallowed into a fallback)."""

    from learnloop.daily_plan import objective_inputs as OI
    from learnloop.router_objective import value as V

    env = _env(tmp_path)
    _open_offer(env, draw)
    probe = _ready_probe(env)["practice_item_id"]
    real = OI.action_for

    def as_probe(vault, repository, candidate, *, practiced, spread):
        if candidate.item_ids == (probe,):
            lo = candidate.learning_object_ids[0]
            repair = V.Action(ref=f"{candidate.candidate_id}:repair", kind=V.REPAIR, item_los=(lo,),
                              minutes=candidate.est_minutes)
            return V.Action(ref=candidate.candidate_id, kind=V.PROBE, item_los=(lo,), minutes=candidate.est_minutes,
                            repair=repair)
        return real(vault, repository, candidate, practiced=practiced, spread=spread)

    monkeypatch.setattr(OI, "action_for", as_probe)
    env.clock.advance(1)
    draw.prefer = ("followup_contest:",)
    advance(env, serve=True)
    row = _objective_rows(env)[-1]
    assert "numeric" not in row["detail_json"]["mixture"]["failed"]
    with env.repository.connection() as connection:
        entry = _trace_of(connection, row["id"])["candidates"][f"followup_contest:{probe}"]
    assert entry["kind"] == PROBE
    assert {"none", "repair", "on_result"} <= set(entry["branches"])


def test_the_offers_declined_branch_is_the_followup_not_the_tail(tmp_path):
    """Value: against a follow-up a "Not now" leads to that follow-up; with none named, the tail's block, as RO4's."""

    from learnloop.router_objective import value as V
    from tests.test_te3b_value import _inputs  # the value tests' own frozen belief

    inputs = _inputs()
    lo = inputs.topics[0].lo
    offer = V.Action(ref="lesson_offer:x", kind=V.LESSON, item_los=(lo,), minutes=15.0, accept=(1.0, 1.0))
    follow = V.Action(ref="follow", kind=V.REPAIR, item_los=(lo,), minutes=2.0)
    plain = V._Model(inputs, 16, "seed").value(offer)[1]["branches"]
    named = V._Model(inputs, 16, "seed").value(replace(offer, declined=follow))[1]["branches"]
    assert named["accepted"] == pytest.approx(plain["accepted"])
    assert named["declined"] != pytest.approx(plain["declined"])


def test_the_workflows_one_job_runs_again_for_a_new_decision(tmp_path):
    from learnloop.followup_serve import queue

    env = _env(tmp_path)
    build_plan(env, kind="normal", budget=25.0, remembered=25, minutes_source="chip")
    _ready_probe(env)
    wf.set_fields(env.repository, "fw_test", clock=env.clock)
    assert queue.enqueue_workflow(env.repository, "fw_test", clock=env.clock)
    with env.repository.atomic(), env.repository.connection() as connection:
        job = store.lease_next_generation_job(connection, owner="t", now=env.now_iso(), lease_expires_at="2999-01-01T00:00:00Z")
        # Out now: nothing changes (its own run is still deciding).
        assert store.requeue_generation_job(connection, "workflow:fw_test", at=env.now_iso()) is False
        assert store.finish_generation_job(connection, job, state="done", at=env.now_iso())
    assert queue.requeue_workflow(env.repository, "fw_test", clock=env.clock) is True
    with env.repository.connection() as connection:
        again = store.generation_job(connection, "workflow:fw_test")
        count = connection.execute("SELECT COUNT(*) FROM followup_generation_jobs WHERE dedupe_key = 'workflow:fw_test'").fetchone()[0]
    assert again["state"] == "queued" and int(again["attempt_count"]) == 0 and count == 1


# -- the whole journey, through the real diagnosis, worker and author doors --------------------------------------------------


@pytest.mark.parametrize("contested", [False, True])
def test_the_journey_on_a_real_miss_lesson_then_not_now_then_the_question(tmp_path, draw, monkeypatch, contested):
    """A real miss in a blind vault with a plan: the lesson wins with nothing written and what was held released; the
    page opens from the plan; "Not now" sends the workflow back to the worker, whose new decision generates exactly one
    question, labelled exposed; and the plan serves it. ``contested``: a new offer is drawn at the next boundary first,
    so the new decision holds no lesson, and the real generated probe arrives during an open offer (the Nov 8 shape): it
    meets the offer in a new decision, valued by RO §8.1's probe interface through its own item's mode."""

    from learnloop.daily_plan.policy import policy_for
    from learnloop.vault.loader import load_vault
    from tests.daily_plan_fakes import make_env
    from tests.followup_serve_helpers import (
        LIVE_ITEM,
        BlindRivalClient,
        author_clients,
        live_miss,
        live_shape_vault,
        run_jobs,
    )
    from tests.test_causal_p2_acceptance import CLOCK

    paths, vault, repository = live_shape_vault(tmp_path, version=TAG, config=NO_CHECKS, task_features=True)
    lo = str(vault.practice_items[LIVE_ITEM].learning_object_id)
    offer_ref = f"lesson_offer:{lo}"
    monkeypatch.setattr(SG, "build_candidates", lambda _vault, _repository, *, now_iso: ([LS.Candidate(
        ref=LS.lesson_ref(lo), learning_object_ids=(lo,), reason="cold_failing", predicted_success=0.3, title="Topic")], {}))
    runtime = fake_runtime()
    others = [scheduled(item_id, str(item.learning_object_id)) for item_id, item in vault.practice_items.items()
              if item_id != LIVE_ITEM]
    assert others, "the plan stays open past the first block"
    env = make_env(paths.root, [scheduled(LIVE_ITEM, lo), *others], clock=CLOCK, session_id="s1")
    env.policy = policy_for(env.vault, env.repository, session_id="s1", clock=CLOCK, runtime=runtime, serve=True)
    draw.never_stop = True
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(SG, "build_candidates", lambda *_a, **_k: ([], {}))
        build_plan(env, kind="normal", budget=25.0, remembered=25, minutes_source="chip")
    author = AuthorFake()
    clients = author_clients(author)
    clients.runtime = runtime
    _result, outcome = live_miss(vault, repository, BlindRivalClient(), session_id="s1")
    row = wf.get(repository, outcome.workflow_id)
    assert row is not None and serving.is_holding(row)

    draw.prefer = (offer_ref,)
    run_jobs(vault, repository, clients=clients)
    assert author.calls == 0
    row = wf.get(repository, outcome.workflow_id)
    assert row["state"] == wf.WAITING and row["chosen_ref"] == offer_ref and not row["practice_item_id"]
    assert row["release_reason"] == wf.RELEASE_LESSON_OFFER and row["exposed_at"] and not serving.is_holding(row)
    assert row["lane"] == wf.LANE_PROBE
    lost = row["decision_id"]

    action = serving.next_action(vault, repository, row["source_attempt_id"], plan_serves=True, clock=CLOCK)
    assert action.action == "continue"
    _record, page = advance(env, serve=True)
    assert page["kind"] == "lesson_offer" and page["offer"]["decision_id"] == lost

    SG.respond(env.vault, env.repository, decision_id=lost, response="declined", clock=CLOCK)
    draw.prefer = (INSERT_NOW,)
    advance(env, serve=False)
    row = wf.get(repository, outcome.workflow_id)
    assert row["state"] == wf.PENDING and not row["chosen_ref"]
    if contested:
        draw.prefer = (offer_ref,)
        for _ in range(12):
            current = E.latest_today(env).current_block()
            if current.is_lesson_offer:
                break
            item = next(entry for entry in current.items if not entry.resolved)
            advance(env, serve=False, skip_practice_item_id=item.practice_item_id)
        assert E.latest_today(env).current_block().is_lesson_offer
        before_offer = current.decision_ref
        draw.prefer = (INSERT_NOW,)

    run_jobs(vault, repository, clients=clients)
    assert author.calls == 1, "one question, written after the new decision"
    row = wf.get(repository, outcome.workflow_id)
    assert row["state"] == wf.READY and row["practice_item_id"] and row["exposed_at"]
    new = rows(env, "plan_interrupt")[-1]
    assert new["id"] == row["decision_id"] != lost and new["parent_decision_id"] == lost and new["chosen_ref"] == INSERT_NOW

    env.vault = load_vault(paths.root)
    env.vault.config = vault.config
    env.policy = policy_for(env.vault, env.repository, session_id="s1", clock=CLOCK, runtime=runtime, serve=True)
    if contested:
        draw.prefer = ("followup_contest:",)
        before = len(_objective_rows(env))
    _record, served = advance(env, serve=True)
    assert served["kind"] == "item" and served["practice_item_id"] == row["practice_item_id"]
    if contested:
        decision = _objective_rows(env)[before:][-1]
        _assert_exact_mu(decision)
        assert decision["detail_json"]["mixture"]["support"] == [f"followup_contest:{row['practice_item_id']}", offer_ref]
        with env.repository.connection() as connection:
            assert json.loads(LO.withdrawn(connection, before_offer)["detail_json"])[LO.SUPERSEDED_BY] == decision["id"]
        assert "numeric" not in decision["detail_json"]["mixture"]["failed"]
        with env.repository.connection() as connection:
            trace = _trace_of(connection, decision["id"])
        entry = trace["candidates"][f"followup_contest:{row['practice_item_id']}"]
        assert entry["kind"] == PROBE and {"none", "repair", "on_result"} <= set(entry["branches"])
    assert wf.probe_answer_exposed(repository, str(row["presentation_id"])) == "followup_feedback_released_before_probe"
