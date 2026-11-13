"""The phone's stop-and-handoff journeys (``tests/test_mobile_v2_rereview_fixes.py``, F7) on the objective's path.

Those run on the staged frame (``STAGED_ROUTER``). Here the vault serves the objective chooser, so the phone's boundary prefetch
and the pending stop meet: a stop forced at ``engine.decide`` is the chooser's stop, and the prefetch the boundary starts must
have finished before a step reads what it left.
"""

from __future__ import annotations

import threading

import pytest
from tests.mobile_v2_rereview_fixes_helpers import _record

pytest.importorskip("starlette")

from learnloop.daily_plan import engine

from tests.mobile_host_helpers import rows
from tests.mobile_v2_plan_helpers import HELD, _call, _desktop, _dont_know, _next, plan_world  # noqa: F401
from tests.router_model_fakes import FakeDecider, FakeLLM, fake_runtime, never_stop_or_offer_draws
from tests.ro4_objective_serving_helpers import policy_answer
from tests.mobile_v2_review_fixes_helpers import _stop_past_held_work, _stops

pytestmark = pytest.mark.parametrize("plan_world", [""], indirect=True)


@pytest.fixture(autouse=True)
def _only_the_forced_stop(monkeypatch):
    """The mix draws no stop of its own (the stop under test is the one forced at ``engine.decide``) and the numeric policy's
    Monte Carlo takes one fixed seed, so every run serves the same block order."""

    never_stop_or_offer_draws(monkeypatch, fixed_numeric_seed=True)


@pytest.fixture(autouse=True)
def _models_ready(monkeypatch):
    """The process's router runtime has fake models behind it, so the phone's ``plan_prefetch`` can start a boundary's job
    (it answers ``no_model`` otherwise and never reaches the plan)."""

    from learnloop.daily_plan import router_runtime

    monkeypatch.setattr(router_runtime, "_DEFAULT",
                        fake_runtime(decider=FakeDecider(), llm=FakeLLM(answer=policy_answer), inline=False))


def _settle(timeout: float = 60.0) -> None:
    """Wait for the boundary prefetch (the objective's job and its model threads) the last answer started: a step reads what
    it left, so a test waits for it rather than racing it."""

    for thread in list(threading.enumerate()):
        if thread.name.startswith(("learnloop-router-", "learnloop-objective-")):
            thread.join(timeout)


def _phone_to_pending_stop(phone, session_id: str, drawn: list) -> dict:
    for index in range(12):
        _settle()
        reply = _next(phone, session_id, f"f7_next_{index}")
        step = reply["step"]
        if step is None or step["kind"] != "item":
            break
        _dont_know(phone, session_id, step, f"f7_dk_{index}")
    _settle()
    assert drawn, "the phone never crossed a boundary past held work"
    return reply

def test_objective_f7_the_stop_drawn_past_held_work_is_offered_on_the_phone(plan_world, monkeypatch):
    phone, _host, repository, _paths = plan_world
    drawn = _stop_past_held_work(monkeypatch)
    session_id = phone.start()["sessionId"]
    reply = _phone_to_pending_stop(phone, session_id, drawn)
    step = reply["step"]
    assert step["kind"] == engine.DEVICE_HELD_STEP and reply["plan"]["status"] == "open"
    # The phone's boundary prefetch starts nothing for a plan whose stop is pending: the job it would run is for a
    # decision the stop already made.
    _settle()
    prefetch = phone.rpc("plan_prefetch", {"sessionId": session_id})
    assert prefetch["reason"] == "stop_pending" and prefetch["started"] is False
    assert step["stopOffer"] == {"stopReason": "a forced stop at the phone's boundary"}
    # A read says the same (the phone opened later, or another tab).
    read = phone.rpc("get_daily_plan", {"sessionId": session_id})
    read_step = read.get("step") or read["plan"].get("nextStep")
    assert read_step["stopOffer"] == {"stopReason": "a forced stop at the phone's boundary"}


def test_objective_f7_keep_going_overrides_the_pending_stop_in_place_and_keeps_the_held_work(plan_world, monkeypatch):
    phone, _host, repository, paths = plan_world
    drawn = _stop_past_held_work(monkeypatch)
    session_id = phone.start()["sessionId"]
    _phone_to_pending_stop(phone, session_id, drawn)
    record = _record(repository)
    stop_receipts = _stops(repository)
    held_before = [item.practice_item_id for item in record.items() if not item.resolved]
    assert HELD in held_before and len(stop_receipts) == 1
    extension = float(_desktop(paths.root).require_vault()[0].config.plan.keep_going_minutes)
    reply = phone.rpc("plan_keep_going", {"sessionId": session_id, "stop": False})
    after = _record(repository)
    # The same plan, still open, its held work and the stop's receipt as they were; the stop lapsed.
    assert after.id == record.id and after.is_open and reply["plan"]["id"] == record.id
    assert engine._stop_pending(after) is None
    assert _stops(repository) == stop_receipts
    assert HELD in [item.practice_item_id for item in after.items() if not item.resolved]
    # The desktop's Keep going extension, past what the plan already holds.
    assert after.budget == pytest.approx(max(record.budget, record.minutes_planned()) + extension)
    # The override is recorded as the desktop's Keep going is (RO0 row 7).
    overrides = rows(repository, "SELECT detail_json FROM session_receipts "
                                 "WHERE end_reason = 'offered_stop_overridden'")
    assert overrides and '"keep_going"' in overrides[-1]["detail_json"]
    # Nothing offers the stop again: the phone's step is no longer a stop offer.
    read = phone.rpc("get_daily_plan", {"sessionId": session_id})
    read_step = read.get("step") or read["plan"].get("nextStep")
    assert not (read_step or {}).get("stopOffer")
    # The desktop takes the session back: its Next still serves the held item.
    ctx = _desktop(paths.root)
    generation = repository.fetch_session(session_id).get("owner_generation") or 0
    _call(ctx, "adopt_session", {"sessionId": session_id, "expectedGeneration": generation})
    served = []
    for _ in range(8):
        step = _call(ctx, "next_plan_item", {"sessionId": session_id, "serve": True})["step"]
        if step is None or step["kind"] != "item":
            break
        served.append(step["practiceItemId"])
        _call(ctx, "submit_dont_know", {"sessionId": session_id, "practiceItemId": step["practiceItemId"],
                                        "hintsUsed": 0, "planPresentationId": step.get("presentationId")})
    assert HELD in served


def test_objective_f7_done_for_today_on_the_pending_stop_leaves_the_held_work_for_the_desktop(plan_world, monkeypatch):
    phone, _host, repository, paths = plan_world
    drawn = _stop_past_held_work(monkeypatch)
    session_id = phone.start()["sessionId"]
    _phone_to_pending_stop(phone, session_id, drawn)
    record = _record(repository)
    phone.rpc("plan_keep_going", {"sessionId": session_id, "stop": True})
    after = _record(repository)
    # The stop already drawn stands: the plan waits for the desktop's held work, then closes on it.
    assert after.id == record.id and after.is_open and engine._stop_pending(after) is not None
    assert len(_stops(repository)) == 1
    ctx = _desktop(paths.root)
    generation = repository.fetch_session(session_id).get("owner_generation") or 0
    _call(ctx, "adopt_session", {"sessionId": session_id, "expectedGeneration": generation})
    served = []
    for _ in range(6):
        step = _call(ctx, "next_plan_item", {"sessionId": session_id, "serve": True})["step"]
        if step is None or step["kind"] != "item":
            break
        served.append(step["practiceItemId"])
        _call(ctx, "submit_dont_know", {"sessionId": session_id, "practiceItemId": step["practiceItemId"],
                                        "hintsUsed": 0, "planPresentationId": step.get("presentationId")})
    assert HELD in served and step["kind"] == "done"
    assert step["stopReason"] == "a forced stop at the phone's boundary"
