"""Instruct hand-off IH1 (spec_instruct_handoff_v1 §4, §10): the offer page's server side.

Fakes only (the router's models are ``tests.router_model_fakes``). Pinned here:

* the offer step carries the router's own words and the offer's rounded minutes (the page's sentence is pinned in
  ``LessonOfferPage.test.tsx``);
* ``offer_shown`` is one ``attention_block_events`` row per block and surface, only on a live offer's block, and the
  plan's fold ignores it (it neither starts nor ends the block);
* the sidecar method never raises, and the phone host does not allow it (the phone shows no offers);
* an open item is never joined by a new draw: reads while an item is served and unanswered write no decision.
"""

from __future__ import annotations

import json
from dataclasses import replace


from learnloop.algorithm_versions import LATEST_ALGORITHM_VERSION
from learnloop.daily_plan import lesson_offer as LO
from learnloop.daily_plan import lesson_suggestion as SG
from learnloop.daily_plan.engine import advance
from learnloop.router_objective import mix

from tests.router_mixture_helpers import mixture_env, rows
from tests.router_model_fakes import block_drawing_seed, fake_runtime
from tests.te3b_offers_helpers import (  # noqa: F401 - fixtures
    OFFER, TAG, _first_decision, _objective_rows, _policy_arm_seed, offer_drawn, offerable)


def _events(env, block_id: str, kind: str = LO.SHOWN_EVENT) -> list[dict]:
    with env.repository.connection() as connection:
        return [dict(r) for r in connection.execute(
            "SELECT * FROM attention_block_events WHERE block_id = ? AND kind = ? ORDER BY event_ordinal",
            (block_id, kind))]


def _offer(tmp_path):
    env = mixture_env(tmp_path, fake_runtime(seed=_policy_arm_seed()), version=LATEST_ALGORITHM_VERSION)
    record, step = _first_decision(env)
    assert step["kind"] == "lesson_offer"
    return env, record, step


def test_the_offer_step_carries_the_routers_words_and_rounded_minutes(tmp_path, offerable, offer_drawn):
    _env, _record, step = _offer(tmp_path)
    assert isinstance(step["offer"]["minutes"], int) and step["offer"]["minutes"] >= 1
    assert step["offer"]["suggestion"]["title"]
    assert isinstance(step["why"], str) and "why_kind" in step


def test_offer_shown_is_written_once_per_block_and_surface(tmp_path, offerable, offer_drawn):
    env, _record, step = _offer(tmp_path)
    block_id = step["block_id"]
    assert _events(env, block_id) == []  # building and serving the step shows nothing by itself
    assert LO.record_shown(env.repository, block_id=block_id, surface="offer_page", session_id="s1", clock=env.clock)
    assert not LO.record_shown(env.repository, block_id=block_id, surface="offer_page", session_id="s1")
    assert LO.record_shown(env.repository, block_id=block_id, surface="today", session_id="s1")
    assert not LO.record_shown(env.repository, block_id=block_id, surface="today")
    shown = _events(env, block_id)
    assert [json.loads(r["detail_json"])["surface"] for r in shown] == ["offer_page", "today"]
    detail = json.loads(shown[0]["detail_json"])
    assert detail["decision_id"] == step["offer"]["decision_id"] and detail["session_id"] == "s1"
    assert shown[0]["created_at"]  # the time


def test_offer_shown_is_ignored_by_the_plan_and_changes_no_decision(tmp_path, offerable, offer_drawn):
    env, _record, step = _offer(tmp_path)
    before = len(rows(env))
    LO.record_shown(env.repository, block_id=step["block_id"], surface="offer_page", session_id="s1")
    record, again = advance(env, serve=False)
    block = next(b for b in record.blocks if b.id == step["block_id"])
    assert not block.finished and again["kind"] == "lesson_offer"
    assert len(rows(env)) == before
    # Answering still ends the block, and a later card on an answered offer writes nothing.
    SG.respond(env.vault, env.repository, decision_id=step["offer"]["decision_id"], response="declined", clock=env.clock)
    record, _step = advance(env, serve=False)
    assert next(b for b in record.blocks if b.id == step["block_id"]).finished
    assert not LO.record_shown(env.repository, block_id=step["block_id"], surface="today")


def test_offer_shown_only_on_a_live_offers_block(tmp_path, offerable, offer_drawn):
    env, record, step = _offer(tmp_path)
    other = next((b for b in record.blocks if not b.is_lesson_offer), None)
    if other is not None:
        assert not LO.record_shown(env.repository, block_id=other.id, surface="today")
        assert _events(env, other.id) == []
    assert not LO.record_shown(env.repository, block_id="no_such_block", surface="today")
    assert not LO.record_shown(env.repository, block_id=None, surface="today")
    assert not LO.record_shown(env.repository, block_id=step["block_id"], surface="somewhere_else")
    assert _events(env, step["block_id"]) == []


def test_record_shown_never_raises(tmp_path, offerable, offer_drawn):
    class Broken:
        def atomic(self):
            raise RuntimeError("database is down")

    assert LO.record_shown(Broken(), block_id="b", surface="today") is False


def test_the_sidecar_method_never_fails_the_page_and_is_not_phone_allowed(tmp_path, offerable, offer_drawn):
    import learnloop_sidecar.handlers  # noqa: F401 - populate the registry
    from learnloop_mobile.allowlist import ALLOWLIST
    from learnloop_sidecar.handlers import daily_plan as handler
    from learnloop_sidecar.registry import METHOD_REGISTRY

    env, _record, step = _offer(tmp_path)

    class Ctx:
        def require_vault(self):
            return env.vault, env.repository

    params = handler.OfferShownInput(block_id=step["block_id"], surface="offer_page", session_id="s1")
    assert handler.record_offer_shown(Ctx(), params)["recorded"] is True
    assert handler.record_offer_shown(Ctx(), params)["recorded"] is False

    class NoVault:
        def require_vault(self):
            raise RuntimeError("no vault open")

    assert handler.record_offer_shown(NoVault(), params)["recorded"] is False
    assert "record_offer_shown" in METHOD_REGISTRY
    assert "record_offer_shown" not in ALLOWLIST and "record_offer_shown" not in handler.DAILY_PLAN_RPCS


def test_no_new_draw_joins_an_open_item(tmp_path, offerable, monkeypatch):
    """While an item is served and unanswered, reads (the Today poll, the workbench's plan read) write no decision and
    place no offer: a boundary is only crossed when the block's items are done."""

    real = mix.draw

    def draw(support, parts, weights, epsilon, seed):
        drawn = real(support, parts, weights, epsilon, seed)
        if drawn.chosen == OFFER:
            other = next(key for key in support if key != OFFER)
            return replace(drawn, chosen=other, propensity=drawn.pi[other])
        return drawn

    monkeypatch.setattr(mix, "draw", draw)
    # A block at the first decision, deterministically (refactor bug ledger D-15): the stop coin's policy arm alone
    # left the mix's draw to the numeric policy's share, whose Monte Carlo is seeded on the plan's fresh id, so its
    # argmax was stop about one run in forty. ``block_drawing_seed`` serves the staged rule's block.
    env = mixture_env(tmp_path, fake_runtime(seed=block_drawing_seed()), version=LATEST_ALGORITHM_VERSION)
    _record, step = _first_decision(env)
    assert step["kind"] == "item"
    before = rows(env)
    for _ in range(3):
        env.clock.advance(60)
        record, read = advance(env, serve=False)
        assert read["kind"] == "item" and read["practice_item_id"] == step["practice_item_id"]
        assert not any(b.is_lesson_offer for b in record.blocks)
    assert [r["id"] for r in rows(env)] == [r["id"] for r in before]
