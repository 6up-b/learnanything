"""Teacher TE3b, Codex review (docs/reviews/router-te3b-codex-review.md): reproduce-first tests for F1-F3 (F4's are in
``test_te3b_value.py`` and ``test_te3b_clock.py``, on the receipt columns of migration 247).

* F1: a generated probe FG1 makes ready after a lesson offer was drawn (the feedback prefetch) is never placed inside
  the offer's block: the offer is taken back unanswered (``withdrawn``, an ``expired`` row: never the learner's
  ``ignored``), and the probe is served next, whether the learner then presses Next, answers the card, or had the card
  shown;
* F2: switching ``router.lesson_suggestions.in_objective`` off takes back a drawn, unanswered offer (the predecessor's
  boundary decides) and its card is neither shown nor answerable;
* F3: with the switch off, TE1b's daily draw reads TE1b's own decisions only (no offer response trains it).

Fakes only (``tests.router_model_fakes``); FG1's workflow is stood in by its one read (``session_rows``).
"""

from __future__ import annotations

import json
from typing import Any

import pytest

from learnloop.daily_plan import engine as E
from learnloop.daily_plan import lesson_offer as LO
from learnloop.daily_plan import lesson_suggestion as SG
from learnloop.daily_plan.engine import advance
from learnloop.daily_plan.policy import policy_for
from learnloop.db.stores import router_suggestions as suggestions
from learnloop.router import lesson_suggestions as LS

from tests.daily_plan_fakes import record_attempt
from tests.router_mixture_helpers import mixture_env, rows
from tests.router_model_fakes import fake_runtime
from tests.test_te3b_offers import TAG, _objective_rows, offer_drawn, offerable  # noqa: F401 - fixtures

pytestmark = pytest.mark.usefixtures("offerable", "offer_drawn")


def _env(tmp_path):
    """The TE3b mixture env with RO5's stop coin off (``stop_coin = 0``): the coin could otherwise serve ``stop`` at the
    first objective boundary, by its seeded draw, where these tests need the drawn offer."""

    return mixture_env(tmp_path, fake_runtime(), version=TAG, toml="[router_objective]\nstop_coin = 0.0\n")


def _prefetched_offer(env) -> tuple[Any, dict[str, Any]]:
    """Serve and answer until the feedback prefetch (``serve=False``) draws the objective's first boundary: the offer
    (``offer_drawn``), persisted and not yet shown."""

    for _ in range(8):
        _record, step = advance(env, serve=True)
        assert step is not None and step["kind"] == "item"
        env.clock.advance(2)
        record_attempt(env.repository, step["practice_item_id"], step["learning_object_id"], env.clock.now(),
                       session_id=env.session_id)
        record, step = advance(env, serve=False)
        if _objective_rows(env):
            assert step["kind"] == "lesson_offer" and step["boundary"] is True
            return record, step
    raise AssertionError("the objective never decided a boundary")


def _probe_ready(env, record, monkeypatch) -> str:
    """FG1's generation finishes while the offer waits: a ready probe on a new item of the session (its decision made
    on the generation slot), as ``followup_serve.workflow.session_rows`` reads it."""

    from learnloop.followup_serve import gates
    from learnloop.followup_serve import workflow

    planned = {item.practice_item_id for item in record.items()}
    probe = sorted(item_id for item_id in env.vault.practice_items if item_id not in planned)[0]
    lo = str(env.vault.practice_items[probe].learning_object_id)
    monkeypatch.setattr(gates, "generate_and_serve_on", lambda config: True)
    monkeypatch.setattr(workflow, "session_rows", lambda repository, session_id: [
        {"id": "fsw_probe", "practice_item_id": probe, "learning_object_id": lo, "state": workflow.READY,
         "decision_id": None}])
    return probe


def _settlement(env, decision_id: str) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    with env.repository.connection() as connection:
        return suggestions.response_for(connection, decision_id), LO.withdrawn(connection, decision_id)


def _assert_probe_served(env, step, probe: str, offer_block_id: str) -> None:
    assert step is not None and step["kind"] == "item" and step["practice_item_id"] == probe
    record = E.latest_today(env)
    block = record.current_block()
    assert block is not None and block.id != offer_block_id and not block.is_lesson_offer
    assert E.followup_placement(record, probe) == E.FOLLOWUP_LIVE
    ended = next(b for b in record.blocks if b.id == offer_block_id)
    assert ended.finished and ended.items == []  # the offer's block never held the probe


# --- F1 -----------------------------------------------------------------------------------------------------------


def test_f1_a_probe_ready_after_the_prefetched_offer_is_served_next_and_the_offer_withdrawn(tmp_path, monkeypatch):
    env = _env(tmp_path)
    record, step = _prefetched_offer(env)
    decision_id, block_id = step["offer"]["decision_id"], step["block_id"]
    probe = _probe_ready(env, record, monkeypatch)
    env.clock.advance(1)
    _record, served = advance(env, serve=True)  # Next
    _assert_probe_served(env, served, probe, block_id)
    response, withdrawal = _settlement(env, decision_id)
    assert response is None  # not the learner's answer: the acceptance model never reads it
    assert json.loads(withdrawal["detail_json"])[LO.WITHDRAWN] == LO.WITHDRAWN_FORCED
    ended = next(b for b in E.latest_today(env).blocks if b.id == block_id)
    assert ended.outcome == LO.WITHDRAWN and ended.ended_reason == LO.WITHDRAWN_FORCED
    with env.repository.connection() as connection:
        # The next boundary's sweep leaves it withdrawn (never ``ignored``).
        assert LO.sweep_ignored(connection, today=env.today(), now_iso=env.now_iso()) == 0
    assert _settlement(env, decision_id)[0] is None


@pytest.mark.parametrize("answer", ["accepted", "declined"])
def test_f1_an_answer_after_the_plan_took_the_offer_back_is_refused_and_the_probe_served(tmp_path, monkeypatch,
                                                                                        answer):
    env = _env(tmp_path)
    record, step = _prefetched_offer(env)
    decision_id, block_id = step["offer"]["decision_id"], step["block_id"]
    probe = _probe_ready(env, record, monkeypatch)
    _record, again = advance(env, serve=False)  # a second read (the plan view's) while the card is up
    assert again["kind"] == "item" and again["practice_item_id"] == probe
    with pytest.raises(SG.SuggestionError) as refused:
        SG.respond(env.vault, env.repository, decision_id=decision_id, response=answer, clock=env.clock)
    assert refused.value.code == "not_found"
    assert _settlement(env, decision_id)[0] is None
    _record, served = advance(env, serve=True)
    _assert_probe_served(env, served, probe, block_id)


def test_f1_a_start_answered_before_the_plan_reads_again_keeps_the_lesson_and_the_probe_is_next(tmp_path, monkeypatch):
    env = _env(tmp_path)
    record, step = _prefetched_offer(env)
    decision_id, block_id = step["offer"]["decision_id"], step["block_id"]
    probe = _probe_ready(env, record, monkeypatch)
    answer = SG.respond(env.vault, env.repository, decision_id=decision_id, response="accepted", clock=env.clock)
    assert answer["lesson"]["lesson_id"]
    _record, served = advance(env, serve=True)
    _assert_probe_served(env, served, probe, block_id)
    response, withdrawal = _settlement(env, decision_id)
    assert response["response"] == "accepted" and withdrawal is None


def test_f1_a_shown_card_with_a_probe_ready_is_withdrawn_not_ignored(tmp_path, monkeypatch):
    env = _env(tmp_path)
    record, step = _prefetched_offer(env)
    decision_id, block_id = step["offer"]["decision_id"], step["block_id"]
    _record, shown = advance(env, serve=True)  # the card is shown
    assert shown["kind"] == "lesson_offer" and shown["boundary"] is True
    probe = _probe_ready(env, record, monkeypatch)
    env.clock.advance(1)
    _record, served = advance(env, serve=True)
    _assert_probe_served(env, served, probe, block_id)
    response, withdrawal = _settlement(env, decision_id)
    assert response is None and withdrawal is not None


# --- F2 -----------------------------------------------------------------------------------------------------------


def _switch_off(env) -> None:
    env.vault.config.router.lesson_suggestions.in_objective = False
    env.policy = policy_for(env.vault, env.repository, session_id=env.session_id, clock=env.clock,
                            runtime=fake_runtime(), serve=True)
    assert env.policy.lesson_offer is None and not LO.offers_on(env.vault)


def test_f2_switching_off_takes_back_a_prefetched_offer_and_its_card(tmp_path):
    from learnloop.daily_plan.view import plan_view

    env = _env(tmp_path)
    record, step = _prefetched_offer(env)
    decision_id, block_id = step["offer"]["decision_id"], step["block_id"]

    def row() -> dict[str, Any]:
        view = plan_view(env, E.latest_today(env), context=None, next_step=None)
        return next(b for b in view["plan"]["blocks"] if b["id"] == block_id)

    assert row()["lesson_offer"]["decision_id"] == decision_id  # on: the waiting card is on its row
    _switch_off(env)
    # Off: the view no longer shows the waiting card, and it cannot be answered.
    assert "lesson_offer" not in row()
    with pytest.raises(SG.SuggestionError):
        SG.respond(env.vault, env.repository, decision_id=decision_id, response="accepted", clock=env.clock)
    before = len(_objective_rows(env))
    _record, served = advance(env, serve=True)
    assert served is not None and served["kind"] != "lesson_offer"
    response, withdrawal = _settlement(env, decision_id)
    assert response is None and json.loads(withdrawal["detail_json"])[LO.WITHDRAWN] == LO.WITHDRAWN_OFF
    ended = next(b for b in E.latest_today(env).blocks if b.id == block_id)
    assert ended.outcome == LO.WITHDRAWN
    # The boundary after it is the predecessor's: no offer in its support, no offer record.
    after = _objective_rows(env)[before:]
    assert after, "the next boundary was decided"
    for decision in after:
        assert not any(ref.startswith("lesson_offer:") for ref in decision["detail_json"]["mixture"]["support"])
        assert "lesson_offers" not in decision["detail_json"]


# --- F3 -----------------------------------------------------------------------------------------------------------


def test_f3_with_the_switch_off_the_daily_draw_never_learns_from_offer_responses(tmp_path):
    env = _env(tmp_path)
    _record, step = _prefetched_offer(env)
    decision_id = step["offer"]["decision_id"]
    SG.respond(env.vault, env.repository, decision_id=decision_id, response="declined", clock=env.clock)
    env.vault.config.router.lesson_suggestions.in_objective = False
    assert SG.suggestions_active(env.vault)
    env.clock.advance(5)
    SG.today_suggestion(env.vault, env.repository, clock=env.clock)
    daily = rows(env, kind="lesson_suggestion")
    assert len(daily) == 1
    detail = daily[0]["detail_json"]
    # The predecessor's draw: TE1b's own ledger (empty), so the priors' model, no "since last" and nothing shown today.
    assert detail["model"] == LS.replay([]).summary()
    assert detail["context"]["days_since_last"] is None
    assert detail["ceiling"]["shown_today"] == 0
    prior = LS.AcceptanceState()
    context = LS.Context.from_dict(detail["context"])
    for entry in daily[0]["candidates_json"]:
        candidate = LS.Candidate.from_dict(entry)
        # (the logged candidate's inputs are rounded, so the recomputation agrees to the rounding)
        assert entry["p_accept"] == pytest.approx(prior.p_accept(context, candidate), rel=1e-5)
    with env.repository.connection() as connection:
        assert SG._model(connection, with_offers=True)[0].updates == 1  # on: one model for offers and cards
        assert SG._model(connection, with_offers=False)[0].updates == 0
