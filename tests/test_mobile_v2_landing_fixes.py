"""Mobile v2 stage V2, the final verify's findings (docs/reviews/phone-v2-codex-review.md, "Final
verify"), reproduced, with the orchestrator's rulings at landing:

* R1 (F6): a phone write's ownership check revalidates the session and generation it pinned when
  it started, independently of the current-session lookup: a session that disappeared, ended or
  was replaced refuses the write with ``session_moved``, and nothing commits.
* R2 (F8): *Done for today* on a pending stop records acceptance of that stop (its decision's stop
  response) while the plan stays open for the held work; the session's end is the accepted stop.
* R3 (F9): *Keep going* computes the re-split first, then commits the override receipt and the plan
  update in one ownership-checked transaction: a ``session_moved`` refusal leaves no receipt.

No model and no network.
"""

from __future__ import annotations

import pytest

pytest.importorskip("starlette")

from learnloop.daily_plan import engine
from learnloop.router_objective import stop_coin

from tests.mobile_host_helpers import rows
from tests.test_mobile_v2_plan import _desktop, _call, plan_world  # noqa: F401
from tests.test_mobile_v2_rereview_fixes import _phone_to_pending_stop, _record
from tests.test_mobile_v2_review_fixes import _stop_past_held_work

_PLANS = "SELECT id, minutes_budget, remembered_minutes, split_json, status FROM daily_plans"


# -- R1 (F6) ----------------------------------------------------------------------------------------


def _desktop_adopts_and_ends_during_the_pool_build(monkeypatch, repository, session_id: str, *, then=None):
    """Codex's reproduction: during a phone write's slow pool build the desktop adopts the phone's
    session and ends it; ``then`` runs after (the phone starting a replacement)."""

    real = engine._classified_pool
    moved: list[bool] = []

    def adopt_and_end(env, **kwargs):
        built = real(env, **kwargs)
        if not moved:
            moved.append(True)
            generation = int(repository.fetch_session(session_id).get("owner_generation") or 0)
            repository.adopt_session(session_id, None, generation)
            repository.end_session_owned(session_id, None, clear=lambda _sid: None)
            if then is not None:
                then()
        return built

    monkeypatch.setattr(engine, "_classified_pool", adopt_and_end)
    return moved


def test_r1_a_phones_sessionless_write_whose_session_was_taken_and_ended_commits_nothing(plan_world, monkeypatch):
    phone, _host, repository, _paths = plan_world
    session_id = phone.start()["sessionId"]
    moved = _desktop_adopts_and_ends_during_the_pool_build(monkeypatch, repository, session_id)
    before = rows(repository, _PLANS)
    status, error = phone.error("set_plan_minutes", {"minutes": 45})
    assert moved and (status, error["code"]) == (409, "session_moved")
    assert rows(repository, _PLANS) == before


def test_r1_a_phones_sessionless_write_whose_session_was_replaced_by_its_own_commits_nothing(plan_world, monkeypatch):
    phone, _host, repository, _paths = plan_world
    session_id = phone.start()["sessionId"]
    phone_device = phone.device["device_id"]
    started: list[str] = []

    def phone_starts_b() -> None:
        started.append(repository.start_session_exclusive({"available_minutes": 25}, phone_device))

    moved = _desktop_adopts_and_ends_during_the_pool_build(monkeypatch, repository, session_id, then=phone_starts_b)
    before = rows(repository, _PLANS)
    status, error = phone.error("set_plan_minutes", {"minutes": 45})
    assert moved and started and (status, error["code"]) == (409, "session_moved")
    assert rows(repository, _PLANS) == before


def test_r1_a_phones_sessionless_write_with_no_session_at_its_start_goes_through(plan_world):
    phone, _host, _repository, _paths = plan_world
    assert phone.rpc("set_plan_minutes", {"minutes": 45})["enabled"] is True


def test_r1_the_desktops_sessionless_write_still_goes_through_with_the_phones_session_open(plan_world):
    """The desktop (a None origin) answers as it always did: only a phone's write pins a session."""

    phone, _host, _repository, paths = plan_world
    phone.start()
    assert _call(_desktop(paths.root), "set_plan_minutes", {"minutes": 45})["enabled"] is True


# -- R2 (F8) ----------------------------------------------------------------------------------------


def _receipts(repository, kind: str):
    return rows(repository, "SELECT session_id, end_reason, end_basis, stop_decision_id, plan_id, detail_json "
                            f"FROM session_receipts WHERE kind = '{kind}' ORDER BY created_at, id")


def test_r2_done_for_today_on_a_pending_stop_records_that_stop_accepted(plan_world, monkeypatch):
    phone, _host, repository, _paths = plan_world
    drawn = _stop_past_held_work(monkeypatch)
    session_id = phone.start()["sessionId"]
    _phone_to_pending_stop(phone, session_id, drawn)
    record = _record(repository)
    decision = record.stops()[-1].decision_ref
    assert decision and engine._stop_pending(record) is not None
    phone.rpc("plan_keep_going", {"sessionId": session_id, "stop": True})
    # The plan stays open for the held work, its stop still pending.
    after = _record(repository)
    assert after.id == record.id and after.is_open and engine._stop_pending(after) is not None
    # That stop's response: accepted, by this session, for this plan.
    responses = _receipts(repository, "stop_response")
    assert [(r["session_id"], r["end_reason"], r["stop_decision_id"], r["plan_id"]) for r in responses] == [
        (session_id, "offered_stop_accepted", decision, record.id)]
    # Done again records nothing more.
    phone.rpc("plan_keep_going", {"sessionId": session_id, "stop": True})
    assert len(_receipts(repository, "stop_response")) == 1
    # The phone ends the session without a reason: the end is the accepted stop, never unprompted.
    phone.rpc("end_session", {"sessionId": session_id})
    ends = _receipts(repository, "end")
    assert [(r["session_id"], r["end_reason"], r["stop_decision_id"]) for r in ends] == [
        (session_id, "offered_stop_accepted", decision)]
    with repository.connection() as connection:
        assert stop_coin._decision_stop_responses(connection) == {decision: "accepted"}


def test_r2_keep_going_after_done_on_a_pending_stop_is_the_overridden_response(plan_world, monkeypatch):
    """The last response to a stop is its response: a Keep going after Done overrides it."""

    phone, _host, repository, _paths = plan_world
    drawn = _stop_past_held_work(monkeypatch)
    session_id = phone.start()["sessionId"]
    _phone_to_pending_stop(phone, session_id, drawn)
    decision = _record(repository).stops()[-1].decision_ref
    phone.rpc("plan_keep_going", {"sessionId": session_id, "stop": True})
    phone.rpc("plan_keep_going", {"sessionId": session_id, "stop": False})
    with repository.connection() as connection:
        assert stop_coin._decision_stop_responses(connection) == {decision: "overridden"}
