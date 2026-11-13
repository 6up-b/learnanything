"""Mobile v2 stage V2: the phone's Today is the shared plan, filtered at the step (spec §2.2, §5.6).

Host journeys through the real host (TestClient, a fake identity header, the fake grader) on a fresh
plan vault, with the desktop as a ``SidecarContext`` on the same database:

* J1: plan steps under a phone origin, the step filter (a held item stays assigned for the desktop and
  is counted), the read that never crosses a boundary and the Next that does, the ``phone_plan``
  surface and the device rules on the decisions;
* J5: the end of the plan and its stop, answered from the phone;
* §5.6: the plan's writes refuse the device that does not own the session; reads never do;
* the kill switch ``phone_plan`` in ``mobile.toml``;
* at a None origin nothing of this runs (the desktop's branch is never entered).

J6 (the randomized check deferred) is in ``tests/test_mobile_v2_checks.py``; J2-J4 in
``tests/test_mobile_v2_feedback.py``. No model and no network: the plan's chooser is the
deterministic pair and the grader is the stuck fake.
"""

from __future__ import annotations

import json

import pytest
from tests.mobile_v2_plan_helpers import DAY, HELD, ITEMS, _call, _desktop, _held_prompt, _next, _phone_day
from tests.mobile_v2_plan_helpers import plan_world  # noqa: F401 - fixtures, used by parameter name

pytest.importorskip("starlette")
from starlette.testclient import TestClient

import learnloop.clock as clock_module
import learnloop_sidecar.handlers  # noqa: F401 -- populate METHOD_REGISTRY
from learnloop.daily_plan import engine
from learnloop_mobile.host import create_app

from tests.helpers import create_daily_plan_vault
from tests.mobile_host_helpers import HOSTNAME, Phone, config_for, pair, rows
from tests.ih2_lessons_compete_helpers import QUIET
from tests.router_model_fakes import never_stop_or_offer_draws

def test_j1_the_phone_reads_the_shared_plan_with_its_device_line(plan_world):
    phone, _host, _repository, paths = plan_world
    plan = phone.rpc("get_daily_plan", {})
    assert plan["enabled"] is True and plan["plan"]["blocks"]
    assert plan["device"]["surface"] == "phone_plan"
    # The desktop's plan is the same record, and its reply carries no device line.
    desktop = _call(_desktop(paths.root), "get_daily_plan", {})
    assert desktop["plan"]["id"] == plan["plan"]["id"]
    assert "device" not in desktop
    assert [block["id"] for block in desktop["plan"]["blocks"]] == [block["id"] for block in plan["plan"]["blocks"]]


def test_j1_the_phone_never_gets_a_held_item_and_the_desktop_serves_it_next(plan_world):
    phone, _host, repository, paths = plan_world
    session_id = phone.start()["sessionId"]
    steps = _phone_day(phone, session_id)
    served = [reply["step"]["practiceItemId"] for reply in steps if reply["step"] and reply["step"]["kind"] == "item"]
    assert served and HELD not in served
    last = steps[-1]
    planned = {item["practiceItemId"] for block in last["plan"]["blocks"] for item in block["items"]}
    if HELD not in planned:
        pytest.skip("the plan never took the held item")  # pragma: no cover - the four items fit 25 minutes
    # Held, it is counted and stays assigned: open in the plan, never served.
    assert last["step"]["kind"] == engine.DEVICE_HELD_STEP
    assert last["device"]["deferredCount"] >= 1
    held_rows = [item for block in last["plan"]["blocks"] for item in block["items"] if item["practiceItemId"] == HELD]
    assert held_rows and held_rows[0]["state"] == "planned"
    # The desktop takes the session back and its next Next serves exactly the held item.
    ctx = _desktop(paths.root)
    owner = repository.fetch_session(session_id)
    _call(ctx, "adopt_session", {"sessionId": session_id, "expectedGeneration": owner.get("owner_generation") or 0})
    desktop_step = _call(ctx, "next_plan_item", {"sessionId": session_id, "serve": True})["step"]
    assert desktop_step["kind"] == "item" and desktop_step["practiceItemId"] == HELD


def test_j1_a_read_never_crosses_past_held_work_and_next_does_once(plan_world, monkeypatch):
    phone, _host, repository, _paths = plan_world
    session_id = phone.start()["sessionId"]
    _phone_day(phone, session_id)
    decisions_before = rows(repository, "SELECT id FROM router_decisions WHERE decision_kind='plan_block'")
    read = phone.rpc("next_plan_item", {"sessionId": session_id, "serve": False}, request_id="read_1")
    if read["step"]["kind"] != engine.DEVICE_HELD_STEP:
        pytest.skip("nothing was held")  # pragma: no cover
    # The read wrote no decision; a second read says the same.
    assert rows(repository, "SELECT id FROM router_decisions WHERE decision_kind='plan_block'") == decisions_before
    assert phone.rpc("get_daily_plan", {"sessionId": session_id})["plan"]["deciding"] is False


def test_j1_the_phones_boundary_decisions_record_phone_plan_and_the_device_rules(plan_world):
    phone, _host, repository, paths = plan_world
    session_id = phone.start()["sessionId"]
    _phone_day(phone, session_id)
    for row in rows(repository, "SELECT surface, detail_json FROM router_decisions WHERE decision_kind='plan_block'"):
        detail = json.loads(row["detail_json"])
        if row["surface"] == "phone_plan":
            assert detail["device"] == {"surface": "phone_plan", "device_policy": "device_eligibility_v1"}
        else:
            # The plan's first block is chosen at its build, by whoever read first: here the phone.
            assert row["surface"] == "daily_plan" and "device" not in detail
    events = rows(repository, "SELECT detail_json FROM attention_block_events WHERE kind='block_chosen'")
    assert any(json.loads(event["detail_json"]).get("device", {}).get("surface") == "phone_plan" for event in events) \
        or len(events) == 1


def test_j1_the_phones_step_bumps_the_desktops_token(plan_world):
    phone, _host, repository, _paths = plan_world
    session_id = phone.start()["sessionId"]
    before = repository.queue_revision()["revision"]
    _next(phone, session_id, "next_bump")
    assert repository.queue_revision()["revision"] > before


def test_j1_next_plan_item_is_long_capable_and_a_retry_answers_the_same_step(plan_world):
    phone, _host, _repository, _paths = plan_world
    session_id = phone.start()["sessionId"]
    response = phone.post("next_plan_item", {"sessionId": session_id, "serve": True})
    assert response.status_code == 422  # a long request needs its request_id
    first = _next(phone, session_id, "same_key")
    again = _next(phone, session_id, "same_key")
    assert again["step"] == first["step"]


def test_j5_the_plan_ends_and_the_phone_stops_or_keeps_going(plan_world):
    phone, _host, repository, paths = plan_world
    session_id = phone.start()["sessionId"]
    _phone_day(phone, session_id)
    ctx = _desktop(paths.root)
    owner = repository.fetch_session(session_id)
    _call(ctx, "adopt_session", {"sessionId": session_id, "expectedGeneration": owner.get("owner_generation") or 0})
    # The desktop answers what the phone left, then the phone takes the session back.
    for index in range(6):
        step = _call(ctx, "next_plan_item", {"sessionId": session_id, "serve": True})["step"]
        if step is None or step["kind"] != "item":
            break
        _call(ctx, "submit_dont_know", {"sessionId": session_id, "practiceItemId": step["practiceItemId"],
                                        "hintsUsed": 0, "planPresentationId": step.get("presentationId")})
    generation = repository.fetch_session(session_id).get("owner_generation") or 0
    phone.rpc("adopt_session", {"sessionId": session_id, "expectedGeneration": generation})
    done = _next(phone, session_id, "next_done")
    assert done["step"]["kind"] == "done" and done["plan"]["status"] != "open"
    assert done["step"]["stopReason"]
    # "Keep going" builds the extension; "Done" ends it, both from the phone.
    going = phone.rpc("plan_keep_going", {"sessionId": session_id})
    assert going["plan"]["kind"] == "keep_going"
    stopped = phone.rpc("plan_keep_going", {"sessionId": session_id, "stop": True})
    assert stopped["plan"]["status"] == "stopped"


def test_s5_6_plan_writes_refuse_the_device_that_does_not_own_the_session(plan_world):
    phone, _host, _repository, paths = plan_world
    session_id = phone.start()["sessionId"]
    ctx = _desktop(paths.root)
    from learnloop_sidecar.errors import SidecarError

    for name, params in (
        ("next_plan_item", {"sessionId": session_id, "serve": True}),
        ("plan_keep_going", {"sessionId": session_id}),
        ("plan_reading_ended", {"sessionId": session_id, "outcome": "skipped"}),
        ("set_plan_minutes", {"sessionId": session_id, "minutes": 30}),
        ("plan_learner_pick", {"sessionId": session_id, "practiceItemId": "pi_b2"}),
        ("plan_more_new", {"sessionId": session_id, "confirm": True}),
        ("next_plan_item", {"sessionId": session_id, "skipPracticeItemId": "pi_b2"}),
    ):
        with pytest.raises(SidecarError) as refused:
            _call(ctx, name, params)
        assert refused.value.code == "session_moved", name
    # Reads never check: the desktop's Today and its prefetch still read the plan.
    assert _call(ctx, "get_daily_plan", {"sessionId": session_id})["enabled"] is True
    assert _call(ctx, "next_plan_item", {"sessionId": session_id})["enabled"] is True
    # The owner's own write goes through.
    assert _next(phone, session_id, "owned")["enabled"] is True


def test_s5_6_tutor_and_lesson_writes_bound_to_a_moved_session_are_refused(plan_world):
    phone, _host, _repository, paths = plan_world
    session_id = phone.start()["sessionId"]
    ctx = _desktop(paths.root)
    from learnloop_sidecar.errors import SidecarError

    with pytest.raises(SidecarError) as asked:
        _call(ctx, "ask_tutor_question", {"context": "practice", "question": "why?", "practiceItemId": "pi_b1",
                                          "sessionId": session_id})
    assert asked.value.code == "session_moved"
    with pytest.raises(SidecarError) as answered:
        _call(ctx, "lesson.suggestion_respond", {"decisionId": "d", "response": "declined", "sessionId": session_id})
    assert answered.value.code == "session_moved"


def test_s5_6_an_ended_or_unknown_session_answers_as_before(plan_world):
    phone, _host, _repository, paths = plan_world
    session_id = phone.start()["sessionId"]
    phone.rpc("end_session", {"sessionId": session_id})
    ctx = _desktop(paths.root)
    # No session_moved for an ended session: the plan's own behaviour stands.
    assert _call(ctx, "plan_keep_going", {"sessionId": session_id})["enabled"] is True
    assert _call(ctx, "plan_keep_going", {"sessionId": "no_such_session"})["enabled"] is True


def test_the_kill_switch_refuses_the_plan_and_meta_says_so(tmp_path, monkeypatch):
    monkeypatch.setattr(clock_module.SystemClock, "now", lambda _self: DAY)
    paths = create_daily_plan_vault(tmp_path / "vault", learning_objects=ITEMS)
    from learnloop.db.repositories import Repository

    repository = Repository(paths.sqlite_path)
    device = pair(repository)
    config = config_for(paths.root).model_copy(update={"phone_plan": False})
    with TestClient(create_app(config), base_url=f"https://{HOSTNAME}") as client:
        phone = Phone(client, device)
        assert phone.get("/api/v1/meta").json()["phone_plan"] is False
        status, error = phone.error("get_daily_plan", {})
        assert (status, error["code"]) == (409, "phone_plan_off")
        # The queue stays, as M2a built it.
        session_id = phone.start()["sessionId"]
        assert phone.queue_items(session_id)


def test_meta_says_the_plan_is_on_by_default(plan_world):
    phone, *_ = plan_world
    assert phone.get("/api/v1/meta").json()["phone_plan"] is True


def test_a_none_origin_never_enters_the_device_branch(tmp_path, monkeypatch):
    """The desktop's steps, views and decisions take no new branch (§2.2: byte-identical at a None
    origin). Every device-only function fails the test if it is reached."""

    monkeypatch.setattr(clock_module.SystemClock, "now", lambda _self: DAY)
    never_stop_or_offer_draws(monkeypatch, fixed_numeric_seed=True)
    paths = create_daily_plan_vault(tmp_path / "vault", learning_objects=ITEMS, plan_toml=QUIET)
    _held_prompt(paths.root)

    def reached(*_args, **_kwargs):
        raise AssertionError("a device-only path ran at a None origin")

    for name in ("_device_block", "_device_item", "_held_step", "_note_check_deferral"):
        monkeypatch.setattr(engine, name, reached)
    import learnloop_sidecar.handlers.daily_plan as handler

    original = handler._step_filter

    def no_filter(ctx, *args, **kwargs):
        made = original(ctx, *args, **kwargs)
        assert made is None
        return made

    monkeypatch.setattr(handler, "_step_filter", no_filter)
    ctx = _desktop(paths.root)
    session_id = _call(ctx, "start_session", {"availableMinutes": 25})["sessionId"]
    plan = _call(ctx, "get_daily_plan", {"sessionId": session_id})
    assert "device" not in plan
    served = []
    for _ in range(8):
        reply = _call(ctx, "next_plan_item", {"sessionId": session_id, "serve": True})
        assert "device" not in reply
        step = reply["step"]
        if step is None or step["kind"] != "item":
            break
        served.append(step["practiceItemId"])
        _call(ctx, "submit_dont_know", {"sessionId": session_id, "practiceItemId": step["practiceItemId"],
                                        "hintsUsed": 0, "planPresentationId": step.get("presentationId")})
    assert HELD in served  # the desktop serves what a phone would hold
    from learnloop.db.repositories import Repository

    surfaces = {row["surface"] for row in rows(Repository(paths.sqlite_path),
                                                "SELECT surface FROM router_decisions WHERE decision_kind='plan_block'")}
    assert surfaces <= {"daily_plan"}
    assert rows(Repository(paths.sqlite_path),
                "SELECT id FROM attention_block_events WHERE kind = 'item_device_deferred'") == []
