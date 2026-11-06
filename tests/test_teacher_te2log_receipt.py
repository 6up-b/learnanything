"""Teacher TE2-log, part 5: the receipt's ``episodes`` and ``minutes`` (spec_teacher_v1 §8.3, §11.6, §11.9).

With ``teacher.episode_log`` on, ``LessonReceiptV1`` lists the lesson's episode ids by kind, its active and elapsed
minutes side by side with their source (missing intervals counted, never filled in), and its ``lesson_node_held``
forecast keys; a detour note whose row was refused is a warning. Off, the receipt is TE1's (tests in
test_teacher_te2log_episodes.py).
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

from learnloop.clock import FrozenClock
from learnloop.teacher import episodes as E
from learnloop.teacher import service as S
from learnloop.vault.loader import load_vault
from tests.teacher_fakes import TeacherFake, build_teacher_vault, check_turn, clients, close_turn, plan_turn
from tests.test_teacher_te2log_episodes import detour_turn
from tests.test_teacher_te2log_node_held import held_plan

T0 = datetime(2026, 11, 5, 15, 0, tzinfo=UTC)


def revised_plan(context):
    """The held plan with a new foundation stepped back to before n1 (no note: an unlogged detour)."""

    turn = held_plan(context)
    turn["requests"][0]["plan"].insert(1, {"id": "nf", "statement": "A matrix acts on vectors.", "lo_id": "lo_det",
                                           "anchors": [], "premises": []})
    return turn


def _iso(minutes: float) -> str:
    return (T0 + timedelta(minutes=minutes)).strftime("%Y-%m-%dT%H:%M:%S.000Z")


def _rows(repository, sql, params=()):
    with repository.connection() as connection:
        return [tuple(row) for row in connection.execute(sql, params).fetchall()]


def _run(tmp_path, *, intervals=(), refuse=False, monkeypatch=None):
    paths, repository = build_teacher_vault(tmp_path / "vault")
    fake = TeacherFake([held_plan])
    view = S.open_lesson(load_vault(paths.root), repository, entry="learning_object", learning_object_ids=["lo_eigen"],
                         clients=clients(fake), clock=FrozenClock(T0))
    lesson_id = view["lesson_id"]

    def act(minute, action, payload, turns, right=True):
        fake.turns, fake.full = list(turns), right
        return S.take_turn(load_vault(paths.root), repository, lesson_id=lesson_id, action=action, payload=payload,
                           clients=clients(fake), clock=FrozenClock(T0 + timedelta(minutes=minute)))

    act(1, "reply", {"text": "go"}, [check_turn()])
    if refuse:
        from learnloop.db.stores import lessons as store

        monkeypatch.setattr(store, "insert_episode", lambda connection, row: (_ for _ in ()).throw(RuntimeError("no")))
    act(2, "answer_check", {"answer": "no"}, [detour_turn()], right=False)
    if refuse:
        monkeypatch.undo()
    act(3, "reply", {"text": "lost"}, [revised_plan])
    if intervals:
        E.record_intervals(load_vault(paths.root), repository, lesson_id=lesson_id, intervals=list(intervals),
                           occurred_at=_iso(9), received_at=_iso(9))
    view = act(10, "reply", {"text": "stop"}, [close_turn()])
    assert view["closed"]
    receipt = json.loads(_rows(repository, "SELECT receipt_json FROM lesson_receipts")[0][0])
    return repository, lesson_id, receipt


def test_the_receipt_lists_episodes_by_kind_minutes_and_placement_forecasts(tmp_path):
    intervals = [{"screen_session": "s", "seq": 1, "started_at": _iso(0), "ended_at": _iso(4), "foreground": True},
                 {"screen_session": "s", "seq": 3, "started_at": _iso(6), "ended_at": _iso(8), "foreground": False}]
    repository, lesson_id, receipt = _run(tmp_path, intervals=intervals)
    ids = [row[0] for row in _rows(repository, "SELECT id FROM lesson_episodes ORDER BY opened_at, id")]
    assert receipt["episodes"] == {"probe": [], "detour": ids, "gap": [], "goal_lo": []} and len(ids) == 2
    # Active (the foreground intervals) and elapsed (closed - opened) side by side; never blended.
    assert receipt["minutes"] == {"active_minutes": 4.0, "elapsed_minutes": 10.0, "unreported_minutes": 4.0,
                                  "missing_intervals": 1, "intervals": 2, "source": "lesson_activity"}
    held = [row[0] for row in _rows(repository, "SELECT receipt_key FROM forecast_receipts "
                                                "WHERE kind = 'lesson_node_held' ORDER BY created_at, receipt_key")]
    # Two plan versions, each forecasting n0 and n1 (the nodes with p_held on a topic).
    assert receipt["node_held_forecasts"] == held and len(held) == 4
    # Every episode closed with the lesson or at its re-check, none left open.
    assert _rows(repository, "SELECT COUNT(*) FROM lesson_episodes WHERE closed_at IS NULL") == [(0,)]


def test_with_no_interval_the_minutes_say_so_and_active_is_unknown(tmp_path):
    _repository, _lesson_id, receipt = _run(tmp_path)
    assert receipt["minutes"]["source"] == "no_intervals"
    assert receipt["minutes"]["active_minutes"] is None and receipt["minutes"]["elapsed_minutes"] == 10.0
    assert receipt["minutes"]["unreported_minutes"] == 10.0


def test_a_refused_detour_row_is_a_receipt_warning(tmp_path, monkeypatch):
    repository, _lesson_id, receipt = _run(tmp_path, refuse=True, monkeypatch=monkeypatch)
    # The refused note's row is missing; the later unlogged detour stands.
    assert [row[0] for row in _rows(repository, "SELECT repair_class FROM lesson_episodes")] == [E.UNLOGGED]
    assert any("detour note(s) have no episode row" in warning for warning in receipt["warnings"])
