"""What other test files use from ``tests/test_teacher_te2log_receipt.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

from learnloop.clock import FrozenClock
from learnloop.teacher import episodes as E
from learnloop.teacher import service as S
from learnloop.vault.loader import load_vault

from tests.teacher_fakes import TeacherFake, build_teacher_vault, check_turn, clients, close_turn
from tests.teacher_te2log_episodes_helpers import detour_turn
from tests.teacher_te2log_node_held_helpers import held_plan


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
