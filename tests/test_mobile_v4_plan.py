"""Mobile v2 stage V4: the plan's reading blocks on the phone (spec §2.2, §3.4; the V2 filter lifted).

V2 held every reading block for the desktop ("readings wait for the desktop until V4"). With the host's
``phone_reader`` on and an app that says it has the Reader, the phone's Next serves a reading block its Reader
can show, records its progress and its end exactly as the desktop does, and leaves the rest held. A cached V3
app (no ``phone_reader`` capability) keeps V3's plan. The desktop's steps are untouched (a None origin never
reaches the device branch). Same world as ``tests/test_daily_plan_reading.py``: an as-you-read book, no model.
"""

from __future__ import annotations

import json
from typing import Any

import pytest

pytest.importorskip("starlette")
from starlette.testclient import TestClient

import learnloop_sidecar.handlers  # noqa: F401 -- populate METHOD_REGISTRY
from learnloop.db.repositories import Repository
from learnloop_mobile.host import create_app
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.registry import METHOD_REGISTRY

from tests.helpers import create_daily_plan_vault
from tests.mobile_host_helpers import HOSTNAME, Phone, config_for, pair, poll_job, rows
from tests.daily_plan_reading_helpers import DAY1, _Clock, _seed_as_you_read, _sections

READER_APP = ("phone_probes", "phone_reader")


def _call(ctx, name, params):
    spec = METHOD_REGISTRY[name]
    return spec.handler(ctx, spec.params_model.model_validate(params))


def _desktop(root) -> SidecarContext:
    ctx = SidecarContext()
    ctx.load(root)
    ctx.grading_provider_override = "manual"
    return ctx


def _job(phone: Phone, method: str, params: dict, key: str) -> Any:
    response = phone.post(method, params, request_id=key)
    if response.status_code == 202:
        body = poll_job(phone, response.json()["accepted"]["job_id"])
        assert body["state"] == "completed", body
        return body["result"]
    assert response.status_code == 200, response.text
    return response.json()["result"]


@pytest.fixture
def world(tmp_path, monkeypatch):
    clock = _Clock(monkeypatch, DAY1)
    paths = create_daily_plan_vault(tmp_path / "vault")
    _seed_as_you_read(paths)
    repository = Repository(paths.sqlite_path)
    device = pair(repository)
    config = config_for(paths.root).model_copy(update={"page_cache_dir": tmp_path / "pages"})
    with TestClient(create_app(config), base_url=f"https://{HOSTNAME}") as client:
        yield {"client": client, "device": device, "root": paths.root, "repo": repository, "clock": clock,
               "sqlite": paths.sqlite_path}


def _phone_reading(phone: Phone, session_id: str) -> dict[str, Any]:
    """The phone's Next until a reading step (or anything but an item), skipping items as the desktop's test does."""

    for index in range(20):
        step = _job(phone, "next_plan_item", {"sessionId": session_id, "serve": True}, f"next_{index}")["step"]
        if step["kind"] != "item":
            return step
        _job(phone, "next_plan_item", {"sessionId": session_id, "skipPracticeItemId": step["practiceItemId"]},
             f"skip_{index}")
    raise AssertionError("no reading step")


def _desktop_reading(ctx, session_id) -> dict[str, Any]:
    for _ in range(20):
        step = _call(ctx, "next_plan_item", {"sessionId": session_id, "serve": True})["step"]
        if step["kind"] != "item":
            return step
        _call(ctx, "next_plan_item", {"sessionId": session_id, "skipPracticeItemId": step["practiceItemId"]})
    raise AssertionError("no reading step")


def _block_events(sqlite, reading_ids) -> list[tuple[str, dict]]:
    """The reading blocks' events (``reading_ids``: the plan view's ids of its reading blocks)."""

    out = []
    for block_id in reading_ids:
        for row in rows(Repository(sqlite), "SELECT kind, detail_json FROM attention_block_events WHERE block_id = ? "
                                            "ORDER BY created_at, rowid", block_id):
            detail = json.loads(row["detail_json"] or "{}")
            detail.pop("session_id", None)  # each device's own session
            out.append((row["kind"], detail))
    return out


def _reading_ids(plan_reply) -> list[str]:
    return [block["id"] for block in plan_reply["plan"]["blocks"] if block["reading"]]


def test_the_phone_takes_a_reading_block_and_ends_it_as_the_desktop_does(world, tmp_path, monkeypatch):
    phone = Phone(world["client"], world["device"], READER_APP)
    phone.rpc("set_plan_minutes", {"minutes": 40})
    session_id = phone.start(availableMinutes=40)["sessionId"]
    step = _phone_reading(phone, session_id)
    assert step["kind"] == "reading", step
    reading = step["reading"]
    first = _sections(world["repo"], "ext_book")[0]
    assert reading["extractionId"] == "ext_book" and reading["sectionId"] == first["id"]
    # The phone's Reader loads that section and reports it, as the desktop's does.
    section = phone.rpc("reader.render_view", {"extractionId": "ext_book", "sectionId": reading["sectionId"]})
    assert [block["spanId"] for block in section["blocks"]][0] == first["span_ids"][0]
    world["clock"].advance(minutes=4)
    _job(phone, "reader.mark_section_progress",
         {"extractionId": "ext_book", "sectionId": reading["sectionId"], "spansSeen": 1, "spanCount": 2}, "p1")
    world["clock"].advance(minutes=4)
    _job(phone, "reader.mark_section_progress",
         {"extractionId": "ext_book", "sectionId": reading["sectionId"], "completed": True}, "p2")
    after = phone.rpc("get_daily_plan", {"sessionId": session_id})
    block = next(block for block in after["plan"]["blocks"] if block["reading"])
    assert block["outcome"] == "section_completed" and block["status"] == "done"
    phone_events = _block_events(world["sqlite"], _reading_ids(after))

    # The same day on the desktop, in an identical vault, at the same times.
    world["clock"].moment = DAY1
    other = create_daily_plan_vault(tmp_path / "desktop")
    _seed_as_you_read(other)
    ctx = _desktop(other.root)
    _call(ctx, "set_plan_minutes", {"minutes": 40})
    desk_session = _call(ctx, "start_session", {"availableMinutes": 40})["sessionId"]
    desk_step = _desktop_reading(ctx, desk_session)
    assert desk_step["kind"] == "reading"
    assert {**desk_step["reading"], "sourceId": None} == {**reading, "sourceId": None}  # the vault's own source id
    world["clock"].advance(minutes=4)
    _call(ctx, "reader.mark_section_progress",
          {"extractionId": "ext_book", "sectionId": reading["sectionId"], "spansSeen": 1, "spanCount": 2})
    world["clock"].advance(minutes=4)
    _call(ctx, "reader.mark_section_progress",
          {"extractionId": "ext_book", "sectionId": reading["sectionId"], "completed": True})
    desk_plan = _call(ctx, "get_daily_plan", {"sessionId": desk_session})
    desk_events = _block_events(other.sqlite_path, _reading_ids(desk_plan))
    # The reading's own events are the desktop's exactly. The block's choice is a decision, which names the
    # device it was taken under (V2's ``device`` entry) and each vault's own ids.
    reading_kinds = ("block_started", "reading_progress", "block_ended")
    ours = [event for event in phone_events if event[0] in reading_kinds]
    assert ours == [event for event in desk_events if event[0] in reading_kinds]
    assert [kind for kind, _detail in ours] == ["block_started", "reading_progress", "reading_progress",
                                               "block_ended"]
    (chosen,) = [detail for kind, detail in phone_events if kind == "block_chosen"]
    assert chosen["device"] == {"surface": "phone_plan", "device_policy": "device_eligibility_v2",
                                "readings": "phone_reader"}


@pytest.mark.parametrize("outcome", ["left_reader", "skipped"])
def test_the_phones_plan_reading_ended_is_the_desktops(world, outcome):
    phone = Phone(world["client"], world["device"], READER_APP)
    phone.rpc("set_plan_minutes", {"minutes": 40})
    session_id = phone.start(availableMinutes=40)["sessionId"]
    step = _phone_reading(phone, session_id)
    assert step["kind"] == "reading"
    before = phone.rpc("get_daily_plan", {"sessionId": session_id})["plan"]
    ended = phone.rpc("plan_reading_ended", {"outcome": outcome, "sessionId": session_id})
    block = next(b for b in ended["plan"]["blocks"] if b["reading"])
    assert block["outcome"] == outcome and block["status"] == "done"
    assert ended["plan"]["totals"]["plannedMinutes"] == pytest.approx(before["totals"]["plannedMinutes"])
    (ended_event,) = [detail for kind, detail in _block_events(world["sqlite"], _reading_ids(ended))
                      if kind == "block_ended"]
    assert set(ended_event) == {"outcome", "minutes_counted"} and ended_event["outcome"] == outcome


def test_a_cached_v3_app_keeps_every_reading_for_the_desktop(world):
    phone = Phone(world["client"], world["device"], ("phone_probes",))
    phone.rpc("set_plan_minutes", {"minutes": 40})
    session_id = phone.start(availableMinutes=40)["sessionId"]
    step = _phone_reading(phone, session_id)
    assert step["kind"] != "reading"
    plan = phone.rpc("get_daily_plan", {"sessionId": session_id})
    assert _reading_ids(plan), "the plan has its reading block"
    assert plan["device"]["readingsWaiting"] >= 1 or step["kind"] == "held_for_desktop"
    # Nothing of the reading block started on the phone.
    assert all(kind != "block_started" for kind, _detail in _block_events(world["sqlite"], _reading_ids(plan)))


def test_the_phones_decisions_name_its_reader_and_the_media_rules(world):
    phone = Phone(world["client"], world["device"], READER_APP)
    phone.rpc("set_plan_minutes", {"minutes": 40})
    session_id = phone.start(availableMinutes=40)["sessionId"]
    _phone_reading(phone, session_id)
    found = rows(world["repo"], "SELECT detail_json FROM router_decisions WHERE surface = 'phone_plan' "
                                "AND decision_kind = 'plan_block'")
    assert found, "the phone's boundary decisions"
    for row in found:
        device = json.loads(row["detail_json"]).get("device")
        assert device == {"surface": "phone_plan", "device_policy": "device_eligibility_v2", "readings": "phone_reader"}


def test_a_reading_the_phone_may_not_show_stays_held(world):
    """A reading the phone's Reader would refuse (here its book opted out of the Reader at ingest) waits for the
    desktop, even with the Reader on. (A book exam material covers whole is never planned as reading at all.)"""

    (artifact,) = world["repo"].all_source_artifacts()
    with world["repo"].connection() as connection:
        connection.execute("UPDATE source_artifacts SET reader_enabled = 0 WHERE id = ?", (artifact["id"],))
        connection.commit()
    phone = Phone(world["client"], world["device"], READER_APP)
    phone.rpc("set_plan_minutes", {"minutes": 40})
    session_id = phone.start(availableMinutes=40)["sessionId"]
    step = _phone_reading(phone, session_id)
    assert step["kind"] != "reading"
    plan = phone.rpc("get_daily_plan", {"sessionId": session_id})
    assert _reading_ids(plan), "the plan has its reading block"
    assert all(kind != "block_started" for kind, _detail in _block_events(world["sqlite"], _reading_ids(plan)))
