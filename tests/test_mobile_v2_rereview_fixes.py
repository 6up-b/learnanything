"""Mobile v2 stage V2, the Codex re-review's findings (docs/reviews/phone-v2-codex-review.md,
"Re-review"), reproduced.

* F5 (reopened): a randomized check left partly answered overnight is still cold when its checkpoint
  restores it the next day: the coldness is the checkpoint's presentation's, not today's plan's.
* F6 (reopened): a phone's sessionless plan write pins the open session's generation, so a handoff
  during its slow work (even one adopted back) commits nothing.
* F7: a stop drawn past work held for the desktop is offered on the phone (*Keep going* / *Done for
  today*); *Keep going* overrides it in place, keeping the held work and the stop's receipt.

No model and no network.
"""

from __future__ import annotations

from datetime import timedelta

import pytest

pytest.importorskip("starlette")

import learnloop.clock as clock_module
from learnloop.daily_plan import engine
from learnloop.db.stores import plan_presentations as presentations
from learnloop.ids import new_ulid

from tests.mobile_host_helpers import rows
from tests.test_mobile_v2_plan import DAY, HELD, _call, _desktop, _dont_know, _next, plan_world  # noqa: F401
from tests.test_mobile_v2_review_fixes import _stop_past_held_work, _stops


# -- F5 ---------------------------------------------------------------------------------------------


def test_f5_a_check_restored_from_its_checkpoint_the_next_day_stays_cold(tmp_path):
    """The engine: today's lookup forgets yesterday's check; its presentation does not."""

    from learnloop.router_objective import checks as C
    from learnloop.scheduling.device_eligibility import PlanStepFilter

    from tests.daily_plan_fakes import record_attempt
    from tests.test_ro5_checks import _env

    env = _env(tmp_path)
    env.device = PlanStepFilter(device_filter=None)
    for _ in range(30):
        _record, step = engine.advance(env, serve=True)
        if step is None or step["kind"] != "item":
            pytest.skip("no check was administered")  # pragma: no cover
        with env.repository.connection() as connection:
            checks = {str(entry["practice_item_id"]) for entry in C.administered(connection).values()}
        if step["practice_item_id"] in checks:
            break
        env.clock.advance(2)
        record_attempt(env.repository, step["practice_item_id"], step["learning_object_id"], env.clock.now(),
                       session_id=env.session_id)
    check, presentation = step["practice_item_id"], step["presentation_id"]
    assert presentation and engine.open_randomized_check(env, check, presentation_id=presentation)
    # Overnight: no plan today holds it, but the checkpoint's presentation is still the check's.
    env.clock.advance(24 * 60)
    assert not engine.open_randomized_check(env, check)
    assert engine.open_randomized_check(env, check, presentation_id=presentation)
    # Not another item's, and not once it is answered.
    others = {item.practice_item_id for block in _record.blocks for item in block.items} - {check}
    if others:
        assert not engine.open_randomized_check(env, next(iter(others)), presentation_id=presentation)
    attempt = record_attempt(env.repository, check, step["learning_object_id"], env.clock.now(),
                             session_id=env.session_id)
    with env.repository.connection() as connection:
        connection.execute("UPDATE practice_attempts SET plan_presentation_id = ? WHERE id = ?", (presentation, attempt))
        connection.commit()
    assert not engine.open_randomized_check(env, check, presentation_id=presentation)


def _check_presentation(repository, practice_item_id: str) -> str:
    """Yesterday's randomized check's presentation of ``practice_item_id``: a copy of today's plan and
    its first block, dated the day before, carries it (the presentations are append-only, one per
    block and item)."""

    def copy(connection, table: str, row: dict, **changes) -> str:
        row = {**row, **changes, "id": new_ulid()}
        connection.execute(f"INSERT INTO {table} ({', '.join(row)}) VALUES ({', '.join('?' for _ in row)})",
                           tuple(row.values()))
        return str(row["id"])

    with repository.connection() as connection:
        plan = dict(connection.execute("SELECT * FROM daily_plans ORDER BY rowid LIMIT 1").fetchone())
        block = dict(connection.execute("SELECT * FROM attention_blocks WHERE daily_plan_id = ? ORDER BY rowid LIMIT 1",
                                        (plan["id"],)).fetchone())
        plan_id = copy(connection, "daily_plans", plan, local_date="2026-10-11", status="complete")
        block_id = copy(connection, "attention_blocks", block, daily_plan_id=plan_id)
        presentation_id = presentations.insert_plan_presentation(connection, {
            "id": new_ulid(), "block_id": block_id, "practice_item_id": practice_item_id, "position": 1,
            "origin": engine.ro5_check_origin(), "served_at": "2026-10-12T09:00:00Z",
        })
        connection.commit()
    return presentation_id


def test_f5_the_phones_serve_of_a_check_restored_the_next_day_says_no_help(plan_world, monkeypatch):
    phone, _host, repository, paths = plan_world
    session_id = phone.start()["sessionId"]
    phone.rpc("get_daily_plan", {"sessionId": session_id})
    presentation = _check_presentation(repository, "pi_b1")
    # The phone's draft of the check, saved with the presentation it answers.
    phone.rpc("save_practice_draft", {"sessionId": session_id, "practiceItemId": "pi_b1", "answerMd": "half an",
                                      "submissionId": "sub_f5_draft", "hintsUsed": 0,
                                      "planPresentationId": presentation})
    # The next morning: today's plan doesn't hold yesterday's check.
    monkeypatch.setattr(clock_module.SystemClock, "now", lambda _self: DAY + timedelta(days=1))
    served = phone.rpc("get_practice_item", {"practiceItemId": "pi_b1", "sessionId": session_id})
    assert served["noHelp"] is True
    # Another item's serve, and the desktop's serve of the same one, carry no new key.
    assert "noHelp" not in phone.rpc("get_practice_item", {"practiceItemId": "pi_b2", "sessionId": session_id})
    ctx = _desktop(paths.root)
    generation = repository.fetch_session(session_id).get("owner_generation") or 0
    _call(ctx, "adopt_session", {"sessionId": session_id, "expectedGeneration": generation})
    assert "noHelp" not in _call(ctx, "get_practice_item", {"practiceItemId": "pi_b1", "sessionId": session_id})


# -- F6 ---------------------------------------------------------------------------------------------


def test_f6_a_phones_sessionless_write_whose_session_moved_and_came_back_commits_nothing(plan_world, monkeypatch):
    phone, _host, repository, _paths = plan_world
    session_id = phone.start()["sessionId"]
    phone_device = phone.device["device_id"]
    real = engine._classified_pool
    moved = []

    def away_and_back(env, **kwargs):
        built = real(env, **kwargs)
        if not moved:
            # The desktop adopts the session during the phone's slow work, and the phone takes it back.
            generation = int(repository.fetch_session(session_id).get("owner_generation") or 0)
            repository.adopt_session(session_id, None, generation)
            repository.adopt_session(session_id, phone_device, generation + 1)
            moved.append(True)
        return built

    monkeypatch.setattr(engine, "_classified_pool", away_and_back)
    before = rows(repository, "SELECT id, minutes_budget, remembered_minutes, split_json FROM daily_plans")
    status, error = phone.error("set_plan_minutes", {"minutes": 45})
    assert moved and (status, error["code"]) == (409, "session_moved")
    assert rows(repository, "SELECT id, minutes_budget, remembered_minutes, split_json FROM daily_plans") == before


def test_f6_a_phones_sessionless_write_with_its_session_where_it_was_goes_through(plan_world):
    phone, _host, _repository, _paths = plan_world
    phone.start()
    assert phone.rpc("set_plan_minutes", {"minutes": 45})["enabled"] is True


# -- F7 ---------------------------------------------------------------------------------------------


def _phone_to_pending_stop(phone, session_id: str, drawn: list) -> dict:
    for index in range(12):
        reply = _next(phone, session_id, f"f7_next_{index}")
        step = reply["step"]
        if step is None or step["kind"] != "item":
            break
        _dont_know(phone, session_id, step, f"f7_dk_{index}")
    if not drawn:
        pytest.skip("the phone never crossed a boundary past held work")  # pragma: no cover
    return reply


def _record(repository):
    return engine.latest_today(engine.PlanEnv(vault=None, repository=repository))


def test_f7_the_stop_drawn_past_held_work_is_offered_on_the_phone(plan_world, monkeypatch):
    phone, _host, repository, _paths = plan_world
    drawn = _stop_past_held_work(monkeypatch)
    session_id = phone.start()["sessionId"]
    reply = _phone_to_pending_stop(phone, session_id, drawn)
    step = reply["step"]
    assert step["kind"] == engine.DEVICE_HELD_STEP and reply["plan"]["status"] == "open"
    assert step["stopOffer"] == {"stopReason": "a forced stop at the phone's boundary"}
    # A read says the same (the phone opened later, or another tab).
    read = phone.rpc("get_daily_plan", {"sessionId": session_id})
    read_step = read.get("step") or read["plan"].get("nextStep")
    assert read_step["stopOffer"] == {"stopReason": "a forced stop at the phone's boundary"}


def test_f7_keep_going_overrides_the_pending_stop_in_place_and_keeps_the_held_work(plan_world, monkeypatch):
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


def test_f7_done_for_today_on_the_pending_stop_leaves_the_held_work_for_the_desktop(plan_world, monkeypatch):
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
