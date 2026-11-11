"""Teacher TE2-log, part 3: ``lesson_activity_intervals`` and ``lesson.activity`` (spec_teacher_v1 §11.6).

Active minutes are the foreground intervals' sum, elapsed minutes ``closed − opened``: the two are reported side by
side and never blended. An interval that never arrives is recorded as missing (a seq gap; the elapsed time no
interval covers is unreported), never filled in. Every model is a fake; no network.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

import pytest

from learnloop.clock import FrozenClock
from learnloop.teacher import episodes as E
from learnloop.teacher import service as S
from learnloop.vault.loader import load_vault
from tests.teacher_fakes import TeacherFake, build_teacher_vault, check_turn, clients, close_turn, plan_turn

T0 = datetime(2026, 11, 5, 15, 0, tzinfo=UTC)


def _iso(minutes: float) -> str:
    return (T0 + timedelta(minutes=minutes)).strftime("%Y-%m-%dT%H:%M:%S.000Z")


def _interval(seq, start, end, foreground=True, session="screen-a"):
    return {"screen_session": session, "seq": seq, "started_at": _iso(start), "ended_at": _iso(end),
            "foreground": foreground}


def _rows(repository, sql, params=()):
    with repository.connection() as connection:
        return [tuple(row) for row in connection.execute(sql, params).fetchall()]


def _lesson(tmp_path, *, config=None):
    from tests.ux_phase1_support import set_config

    paths, repository = build_teacher_vault(tmp_path / "vault")
    if config:
        set_config(paths.root, config)
    fake = TeacherFake([plan_turn])
    view = S.open_lesson(load_vault(paths.root), repository, entry="learning_object", learning_object_ids=["lo_eigen"],
                         clients=clients(fake), clock=FrozenClock(T0))
    return paths, repository, fake, view


def _record(paths, repository, lesson_id, intervals, *, received=60.0):
    return E.record_intervals(load_vault(paths.root), repository, lesson_id=lesson_id, intervals=intervals,
                              occurred_at=_iso(received - 0.5), received_at=_iso(received))


def test_intervals_are_appended_once_each_with_both_times(tmp_path):
    paths, repository, _fake, view = _lesson(tmp_path)
    assert view["activity_log"] is True
    result = _record(paths, repository, view["lesson_id"], [_interval(1, 0, 4), _interval(2, 4, 6, foreground=False)])
    assert result == {"recorded": 2, "refused": 0, "enabled": True}
    # A resend (the client retries a failed batch) writes nothing.
    assert _record(paths, repository, view["lesson_id"], [_interval(1, 0, 4)])["recorded"] == 0
    rows = _rows(repository, "SELECT seq, seconds, foreground, occurred_at, received_at, receipt_version "
                             "FROM lesson_activity_intervals ORDER BY seq")
    assert rows == [(1, 240.0, 1, _iso(59.5), _iso(60), E.INTERVAL_VERSION),
                    (2, 120.0, 0, _iso(59.5), _iso(60), E.INTERVAL_VERSION)]


def test_a_bad_interval_is_refused_alone(tmp_path, monkeypatch):
    from learnloop.db.stores import lessons as store

    paths, repository, _fake, view = _lesson(tmp_path)
    real = store.insert_interval

    def flaky(connection, row):
        if row["seq"] == 2:
            connection.execute("INSERT INTO lesson_activity_intervals(id) VALUES ('x')")  # refused by the table
        return real(connection, row)

    monkeypatch.setattr(store, "insert_interval", flaky)
    result = _record(paths, repository, view["lesson_id"],
                     [_interval(1, 0, 1), _interval(2, 1, 2), _interval(3, 3, 2), _interval(4, 2, 3)])
    # seq 2's row rolled back alone; seq 3 ends before it starts (refused before any write); 1 and 4 stand.
    assert result["recorded"] == 2 and result["refused"] == 1
    assert [row[0] for row in _rows(repository, "SELECT seq FROM lesson_activity_intervals ORDER BY seq")] == [1, 4]


def test_minutes_keep_active_and_elapsed_apart_and_missing_as_missing():
    spans = [_interval(1, 0, 10), _interval(2, 10, 15, foreground=False),
             # seq 3 never arrived; seq 4 covers 20-30 (but only 20-25 is inside the window below)
             _interval(4, 20, 30)]
    counted = E.minutes(spans, _iso(0), _iso(25))
    assert counted["elapsed_seconds"] == 25 * 60.0
    assert counted["active_seconds"] == 15 * 60.0  # the foreground intervals only, clipped to the window
    assert counted["unreported_seconds"] == 5 * 60.0  # 15-20: no interval covers it; never active, never idle
    assert counted["missing_intervals"] == 1 and counted["source"] == "lesson_activity"
    # Never blended: active is not elapsed minus anything, and with no interval it is unknown, not elapsed.
    none = E.minutes([], _iso(0), _iso(25))
    assert none["active_seconds"] is None and none["elapsed_seconds"] == 25 * 60.0
    assert none["unreported_seconds"] == 25 * 60.0 and none["source"] == "no_intervals"
    # Overlapping intervals from two screen sessions (the screen remounted) are counted once.
    double = E.minutes([_interval(1, 0, 10), _interval(1, 5, 12, session="screen-b")], _iso(0), _iso(12))
    assert double["active_seconds"] == 12 * 60.0 and double["missing_intervals"] == 0


def test_an_episodes_minutes_come_from_the_screens_intervals(tmp_path):
    paths, repository, fake, view = _lesson(tmp_path)
    lesson_id = view["lesson_id"]

    def act(minute, action, payload, turns, right=True):
        fake.turns, fake.full = list(turns), right
        return S.take_turn(load_vault(paths.root), repository, lesson_id=lesson_id, action=action, payload=payload,
                           clients=clients(fake), clock=FrozenClock(T0 + timedelta(minutes=minute)))

    detour = {"message": "Again, differently.", "requests": [
        {"action": "note_detour", "node": "n1", "hypothesis": "mixes up the two", "repair": "reteach", "p": 0.5}]}
    act(1, "reply", {"text": "go"}, [check_turn()])
    act(2, "answer_check", {"answer": "no"}, [detour], right=False)  # the detour opens at minute 2
    _record(paths, repository, lesson_id, [_interval(1, 0, 3), _interval(2, 3, 5, foreground=False),
                                           _interval(4, 7, 9)])
    act(10, "reply", {"text": "ok"}, [check_turn()])
    act(12, "answer_check", {"answer": "det(A - tI) = 0"}, [close_turn()])  # the re-check closes it at minute 12
    (row,) = _rows(repository, "SELECT active_seconds, elapsed_seconds, unreported_seconds, missing_intervals, "
                               "minutes_source FROM lesson_episodes")
    # From minute 2 to 12: active 2-3 and 7-9 (3 min), background 3-5, nothing reported 5-7 and 9-12.
    assert row == (180.0, 600.0, 300.0, 1, "lesson_activity")


def test_switch_off_writes_nothing_and_the_screen_is_not_asked(tmp_path):
    paths, repository, _fake, view = _lesson(tmp_path, config={("teacher", "episode_log"): False})
    assert "activity_log" not in view
    assert _record(paths, repository, view["lesson_id"], [_interval(1, 0, 4)]) == {"recorded": 0, "enabled": False}
    assert _rows(repository, "SELECT COUNT(*) FROM lesson_activity_intervals") == [(0,)]


def test_an_unknown_lesson_is_refused(tmp_path):
    paths, repository, _fake, _view = _lesson(tmp_path)
    with pytest.raises(E.ActivityRefused):
        _record(paths, repository, "les_nope", [_interval(1, 0, 1)])


# --- the desktop RPC ------------------------------------------------------------------------------


def test_lesson_activity_is_a_desktop_only_rpc_that_records_intervals(tmp_path):
    from learnloop_mobile.allowlist import ALLOWLIST
    from learnloop_sidecar import handlers  # noqa: F401 - populates the registry
    from learnloop_sidecar.handlers import lesson as H
    from learnloop_sidecar.registry import METHOD_REGISTRY
    from tests.teacher_te1_successor_helpers import _Ctx

    assert H.LESSON_ACTIVITY_RPCS == ("lesson.activity",)
    assert "lesson.activity" in METHOD_REGISTRY and "lesson.activity" not in ALLOWLIST
    assert not set(H.LESSON_ACTIVITY_RPCS) & set(H.LESSON_RPCS)
    paths, repository, _fake, view = _lesson(tmp_path)
    ctx = _Ctx(paths, repository)
    params = H.LessonActivityInput.model_validate({
        "lessonId": view["lesson_id"], "occurredAt": _iso(5),
        "intervals": [{"screenSession": "s1", "seq": 1, "startedAt": _iso(0), "endedAt": _iso(2), "foreground": True}]})
    result = H.lesson_activity(ctx, params)
    assert result["recorded"] == 1 and result["enabled"] is True
    assert _rows(repository, "SELECT screen_session, seq, foreground, occurred_at FROM lesson_activity_intervals") == \
        [("s1", 1, 1, _iso(5))]
    from learnloop_sidecar.errors import SidecarError

    with pytest.raises(SidecarError):
        H.lesson_activity(ctx, H.LessonActivityInput.model_validate({"lessonId": "les_nope", "intervals": []}))
    assert json.dumps(result)
