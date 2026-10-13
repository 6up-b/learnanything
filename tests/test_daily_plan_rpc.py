"""Daily-loop DL1 plan RPCs through the sidecar (§6.5-§6.7, §6.10, §7; gates G2, G3).

Includes the §6.6 remembered-minutes cases: 40, then a 10-minute keep going,
defaults to 40 the next day; a 15-minute re-entry plan and the post-re-entry
remainder leave 40 in place; a chip tap on a re-entry plan changes the
remembered value but not the re-entry cap.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

import learnloop.clock as clock_module
import learnloop_sidecar.handlers  # noqa: F401 -- populate METHOD_REGISTRY
from learnloop.daily_plan.split import split_line
from learnloop.db.repositories import Repository
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.registry import METHOD_REGISTRY
from tests.helpers import create_daily_plan_vault

DAY1 = datetime(2026, 10, 12, 9, 0, tzinfo=UTC)


def _call(ctx: SidecarContext, name: str, params: dict):
    spec = METHOD_REGISTRY[name]
    return spec.handler(ctx, spec.params_model.model_validate(params))


class _Clock:
    def __init__(self, monkeypatch, start: datetime):
        self.moment = start
        monkeypatch.setattr(clock_module.SystemClock, "now", lambda _self: self.moment)

    def advance(self, **delta) -> None:
        self.moment = self.moment + timedelta(**delta)


def _ctx(root):
    ctx = SidecarContext()
    ctx.load(root)
    ctx.grading_provider_override = "manual"
    return ctx


@pytest.fixture
def vault(tmp_path):
    return create_daily_plan_vault(
        tmp_path / "vault",
        learning_objects={"lo_extra": [("pi_extra_1", 2.0), ("pi_extra_2", 2.0)]},
    )


def test_the_plan_dto_is_the_one_source_of_every_number(vault, monkeypatch):
    _Clock(monkeypatch, DAY1)
    ctx = _ctx(vault.root)
    plan = _call(ctx, "get_daily_plan", {})
    assert plan["enabled"] is True
    body = plan["plan"]
    assert body["minutesBudget"] == 25 and body["rememberedMinutes"] == 25  # D1 on a fresh vault
    lanes = {row["lane"]: row["displayMinutes"] for row in body["split"]["lanes"]}
    assert body["split"]["line"] == split_line(25, lanes)
    assert sum(lanes.values()) <= 25
    # The first block is chosen at build; its line and Start's "First:" agree.
    first = body["blocks"][0]
    assert body["firstBlock"]["itemCount"] == len(first["items"])
    assert body["firstBlock"]["estMinutes"] == first["estMinutes"]
    assert first["estMinutes"] == pytest.approx(sum(item["estMinutes"] for item in first["items"]))
    # "Block 1 of about N": chosen plus projected, all inside the budget.
    assert body["blockCountEstimate"] == len(body["blocks"]) + len(body["projected"])
    planned = body["totals"]["plannedMinutes"] + sum(row["estMinutes"] for row in body["projected"])
    assert planned <= 25 + 1e-6
    assert body["nextStep"]["kind"] == "item" and body["nextStep"]["boundary"] is True


def test_next_plan_item_serves_with_the_offer_that_ranked_it_and_advances(vault, monkeypatch):
    clock = _Clock(monkeypatch, DAY1)
    ctx = _ctx(vault.root)
    session_id = _call(ctx, "start_session", {"availableMinutes": 25})["sessionId"]
    served = _call(ctx, "next_plan_item", {"sessionId": session_id, "serve": True})
    step = served["step"]
    assert step["kind"] == "item" and step["schedulerCandidateId"]
    repository = Repository(vault.sqlite_path)
    # The offer belongs to this session and item, so the answer can bind it.
    assert repository.bind_submission_offer(
        submission_id="sub_1", session_id=session_id, practice_item_id=step["practiceItemId"],
        scheduler_candidate_id=step["schedulerCandidateId"],
    ) == step["schedulerCandidateId"]
    # Answer it ("I don't know" needs no grader); the prefetch made while
    # feedback shows names the next item.
    clock.advance(minutes=3)
    _call(
        ctx,
        "submit_dont_know",
        {
            "sessionId": session_id, "practiceItemId": step["practiceItemId"], "latencySeconds": 150,
            "submissionId": "sub_1", "schedulerCandidateId": step["schedulerCandidateId"],
        },
    )
    clock.advance(minutes=1)
    peek = _call(ctx, "next_plan_item", {"sessionId": session_id, "serve": False})
    done_items = [
        item for block in peek["plan"]["blocks"] for item in block["items"] if item["state"] == "done"
    ]
    assert [item["practiceItemId"] for item in done_items] == [step["practiceItemId"]]
    assert peek["step"]["practiceItemId"] != step["practiceItemId"]


def test_skipping_moves_on_and_counts_the_estimate(vault, monkeypatch):
    _Clock(monkeypatch, DAY1)
    ctx = _ctx(vault.root)
    session_id = _call(ctx, "start_session", {"availableMinutes": 25})["sessionId"]
    first = _call(ctx, "next_plan_item", {"sessionId": session_id, "serve": True})["step"]
    after = _call(ctx, "next_plan_item", {"sessionId": session_id, "serve": False, "skipPracticeItemId": first["practiceItemId"]})
    assert after["step"]["practiceItemId"] != first["practiceItemId"]
    assert after["plan"]["totals"]["skippedItems"] == 1


def test_remembered_minutes_survive_keep_going_into_the_next_day(vault, monkeypatch):
    clock = _Clock(monkeypatch, DAY1)
    ctx = _ctx(vault.root)
    tapped = _call(ctx, "set_plan_minutes", {"minutes": 40})
    assert tapped["plan"]["minutesBudget"] == 40 and tapped["plan"]["minutesSource"] == "chip"
    stopped = _call(ctx, "plan_keep_going", {"stop": True})
    assert stopped["plan"]["status"] == "stopped"
    extension = _call(ctx, "plan_keep_going", {})
    assert extension["plan"]["kind"] == "keep_going"
    assert extension["plan"]["minutesBudget"] == 10  # D3
    assert extension["plan"]["minutesSource"] == "generated"
    assert extension["plan"]["rememberedMinutes"] == 40  # generated budgets never change it
    clock.advance(days=1)
    tomorrow = _call(ctx, "get_daily_plan", {})
    assert tomorrow["plan"]["kind"] == "normal"
    assert tomorrow["plan"]["minutesBudget"] == 40 and tomorrow["plan"]["minutesSource"] == "carried"


def _break_of(ctx, clock, days):
    session_id = _call(ctx, "start_session", {"availableMinutes": 40})["sessionId"]
    _call(ctx, "end_session", {"sessionId": session_id})
    clock.advance(days=days)


def test_reentry_and_its_remainder_leave_the_remembered_minutes_in_place(vault, monkeypatch):
    clock = _Clock(monkeypatch, DAY1)
    ctx = _ctx(vault.root)
    _call(ctx, "set_plan_minutes", {"minutes": 40})
    _call(ctx, "plan_keep_going", {"stop": True})
    _break_of(ctx, clock, 10)
    reentry = _call(ctx, "get_daily_plan", {})["plan"]
    assert reentry["kind"] == "reentry"
    assert reentry["minutesBudget"] == 15 and reentry["rememberedMinutes"] == 40
    _call(ctx, "plan_keep_going", {"stop": True})
    remainder = _call(ctx, "plan_keep_going", {})["plan"]
    assert remainder["kind"] == "normal" and remainder["minutesSource"] == "generated"
    assert remainder["rememberedMinutes"] == 40
    assert remainder["minutesBudget"] == pytest.approx(40 - reentry["totals"]["plannedMinutes"])
    # The learner practised that day (a session is real activity, F1), so the
    # next day is an ordinary plan again, at the remembered 40.
    session_id = _call(ctx, "start_session", {"availableMinutes": 15})["sessionId"]
    _call(ctx, "end_session", {"sessionId": session_id})
    clock.advance(days=1)
    tomorrow = _call(ctx, "get_daily_plan", {})["plan"]
    assert tomorrow["kind"] == "normal" and tomorrow["minutesBudget"] == 40


def test_a_chip_on_a_reentry_plan_sets_the_remembered_value_not_the_cap(vault, monkeypatch):
    clock = _Clock(monkeypatch, DAY1)
    ctx = _ctx(vault.root)
    _call(ctx, "set_plan_minutes", {"minutes": 25})
    _call(ctx, "plan_keep_going", {"stop": True})
    _break_of(ctx, clock, 9)
    assert _call(ctx, "get_daily_plan", {})["plan"]["kind"] == "reentry"
    tapped = _call(ctx, "set_plan_minutes", {"minutes": 60})["plan"]
    assert tapped["kind"] == "reentry"
    assert tapped["rememberedMinutes"] == 60
    assert tapped["minutesBudget"] == 15  # the re-entry cap holds
    smaller = _call(ctx, "set_plan_minutes", {"minutes": 10})["plan"]
    assert smaller["minutesBudget"] == 10


def test_more_new_material_shows_the_trade_off_before_it_adds_anything(vault, monkeypatch):
    _Clock(monkeypatch, DAY1)
    ctx = _ctx(vault.root)
    _call(ctx, "get_daily_plan", {})
    _call(ctx, "plan_keep_going", {"stop": True})
    preview = _call(ctx, "plan_more_new", {"confirm": False})
    assert preview["plan"]["kind"] == "normal"  # nothing built yet
    trade = preview["preview"]
    assert trade["available"] in (True, False)
    if trade["available"]:
        assert trade["addsMinutesPerDay"] > 0
        confirmed = _call(ctx, "plan_more_new", {"confirm": True})
        assert confirmed["plan"]["kind"] == "keep_going"
        assert confirmed["plan"]["admission"]["override"] == "more_new"


def test_headline_rpc_lists_each_lo_once(vault, monkeypatch):
    _Clock(monkeypatch, DAY1)
    ctx = _ctx(vault.root)
    headline = _call(ctx, "get_today_headline", {})
    assert headline["enabled"] is True
    total = sum(headline["counts"].values())
    assert total == len(headline["learningObjects"])
    assert headline["line"].startswith(f"{headline['counts']['demonstrated']} demonstrated")
    assert headline["expectedRecallTooltip"] == "a model estimate, not a test"


def test_rpcs_validate_their_inputs(vault, monkeypatch):
    from learnloop_sidecar.errors import SidecarError

    _Clock(monkeypatch, DAY1)
    ctx = _ctx(vault.root)
    with pytest.raises(SidecarError):
        _call(ctx, "set_plan_minutes", {"minutes": 0})
    with pytest.raises(SidecarError):
        _call(ctx, "next_plan_item", {"serve": True})
    with pytest.raises(SidecarError):
        _call(ctx, "plan_learner_pick", {"practiceItemId": "pi_missing"})


def test_g3_every_shown_number_is_what_the_plan_serves(vault, monkeypatch):
    """Gate G3: the DTO's figures are the engine's own (the client only shows them)."""

    from learnloop.daily_plan.engine import PlanEnv, day_records, latest_today
    from learnloop.vault.loader import load_vault

    clock = _Clock(monkeypatch, DAY1)
    ctx = _ctx(vault.root)
    session_id = _call(ctx, "start_session", {"availableMinutes": 25})["sessionId"]
    for _ in range(3):
        step = _call(ctx, "next_plan_item", {"sessionId": session_id, "serve": True})["step"]
        if step["kind"] != "item":
            break
        clock.advance(minutes=2)
        _call(ctx, "submit_dont_know", {"sessionId": session_id, "practiceItemId": step["practiceItemId"], "latencySeconds": 90})
        clock.advance(minutes=1)
    dto = _call(ctx, "get_daily_plan", {"sessionId": session_id})
    env = PlanEnv(vault=load_vault(vault.root), repository=Repository(vault.sqlite_path))
    record = latest_today(env)
    body = dto["plan"]
    # The split the engine enforces is the split shown.
    assert {row["lane"]: row["minutes"] for row in body["split"]["lanes"]} == pytest.approx(
        {lane: row["minutes"] for lane, row in record.split["lanes"].items()}
    )
    assert body["minutesBudget"] == record.budget
    assert body["minutesLeft"] == pytest.approx(record.minutes_left(), abs=1e-3)
    # Each block's "about N min" and its items are the persisted plan's.
    assert [b["estMinutes"] for b in body["blocks"]] == pytest.approx([b.est_minutes() for b in record.blocks], abs=1e-3)
    assert [[i["practiceItemId"] for i in b["items"]] for b in body["blocks"]] == [
        [i.practice_item_id for i in b.items if not i.displaced] for b in record.blocks
    ]
    # The done screen's figures are the day's own.
    day = day_records(env)
    done = [item for r in day for item in r.items() if item.done]
    assert dto["day"]["doneItems"] == len(done) >= 1
    assert dto["day"]["actualMinutes"] == pytest.approx(sum((item.wall_ms or 0) for item in done) / 60000, abs=1e-3)
    assert body["totals"]["plannedMinutes"] == pytest.approx(record.minutes_planned(), abs=1e-3)
