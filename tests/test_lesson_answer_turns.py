"""Review round 3, FR3-22 (class 4, atomic doors; the writer-fence review's lesson-check row): a lesson check's and a
lesson probe's answer turn commits with its grade. Before, the learner's answer turn committed before grading; a
grading failure (a refusal, an outage) left it behind and *Submit answer* again appended a second answer turn (for a
check under a second attempt reference). Now a failed grade leaves no turn, and the retry records exactly one.
"""

from __future__ import annotations

from datetime import timedelta

import pytest

from learnloop.clock import FrozenClock
from learnloop.teacher import checks as CK
from learnloop.teacher import probes as PR
from learnloop.teacher import service as S
from learnloop.vault.loader import load_vault

from tests.helpers import NOW
from tests.teacher_fakes import TeacherFake, build_teacher_vault, check_turn, clients, close_turn, plan_turn
from tests.teacher_te2_review_fixes_helpers import _served


def _turns(repository, lesson_id, action):
    with repository.connection() as connection:
        return connection.execute("SELECT refs_json FROM lesson_turns WHERE lesson_id = ? AND action = ?",
                                  (lesson_id, action)).fetchall()


def _failing_once(monkeypatch):
    real = CK.grade_answer
    calls = {"n": 0}

    def grade(*args, **kwargs):
        calls["n"] += 1
        if calls["n"] == 1:
            raise RuntimeError("the grader is unavailable")
        return real(*args, **kwargs)

    monkeypatch.setattr(CK, "grade_answer", grade)


def test_a_lesson_check_answer_turn_commits_with_its_grade(tmp_path, monkeypatch):
    paths, repository = build_teacher_vault(tmp_path / "vault")
    fake = TeacherFake([plan_turn, check_turn()])
    view = S.open_lesson(load_vault(paths.root), repository, entry="learning_object", learning_object_ids=["lo_eigen"],
                         clients=clients(fake), clock=FrozenClock(NOW))
    lesson_id = view["lesson_id"]
    S.take_turn(load_vault(paths.root), repository, lesson_id=lesson_id, action="reply", payload={"text": "and?"},
                clients=clients(fake), clock=FrozenClock(NOW + timedelta(minutes=1)))
    _failing_once(monkeypatch)
    answer = {"answer": "det(A - tI) = 0", "tap": 5}
    with pytest.raises(S.LessonError) as failed:
        S.take_turn(load_vault(paths.root), repository, lesson_id=lesson_id, action="answer_check", payload=answer,
                    clients=clients(fake), clock=FrozenClock(NOW + timedelta(minutes=2)))
    assert failed.value.code == "grading_unavailable"
    assert _turns(repository, lesson_id, "check_answer") == []  # failed before: the turn stayed behind
    S.take_turn(load_vault(paths.root), repository, lesson_id=lesson_id, action="answer_check", payload=answer,
                clients=clients(fake), clock=FrozenClock(NOW + timedelta(minutes=3)))
    assert len(_turns(repository, lesson_id, "check_answer")) == 1
    assert len(_turns(repository, lesson_id, "check_result")) == 1


def test_a_lesson_probe_answer_turn_commits_with_its_grade(tmp_path, monkeypatch):
    lesson, probe = _served(tmp_path)
    _failing_once(monkeypatch)
    with pytest.raises(S.LessonError) as failed:
        lesson.act("answer_probe", {"answer": "(1, 0) by three"}, turns=[close_turn()])
    assert failed.value.code == "grading_unavailable"
    assert _turns(lesson.repository, lesson.lesson_id, PR.ANSWER) == []  # failed before: the turn stayed behind
    lesson.act("answer_probe", {"answer": "(1, 0) by three"}, turns=[close_turn()])
    assert len(_turns(lesson.repository, lesson.lesson_id, PR.ANSWER)) == 1
    assert lesson.rows("SELECT COUNT(*) FROM practice_attempts WHERE id = ?", (probe.attempt_id,)) == [(1,)]


# -- Review round 4, R4-S1: a budget-limited lesson keeps the submitted answer ----------------------------------------


def _refused_by_the_budget(monkeypatch):
    from learnloop.ai.spend import SpendLimitExceeded

    def grade(*args, **kwargs):
        raise SpendLimitExceeded("the lesson's cap", rule="envelope_cap")

    monkeypatch.setattr(CK, "grade_answer", grade)


def _payloads(repository, lesson_id, action):
    from learnloop.db.stores import lessons as store

    with repository.connection() as connection:
        return [turn["payload"] for turn in store.turns(connection, lesson_id) if turn["action"] == action]


def test_a_budget_refused_check_answer_is_saved_unassessed_with_the_close(tmp_path, monkeypatch):
    paths, repository = build_teacher_vault(tmp_path / "vault")
    fake = TeacherFake([plan_turn, check_turn()])
    view = S.open_lesson(load_vault(paths.root), repository, entry="learning_object", learning_object_ids=["lo_eigen"],
                         clients=clients(fake), clock=FrozenClock(NOW))
    lesson_id = view["lesson_id"]
    view = S.take_turn(load_vault(paths.root), repository, lesson_id=lesson_id, action="reply",
                       payload={"text": "and?"}, clients=clients(fake), clock=FrozenClock(NOW + timedelta(minutes=1)))
    check_ref = view["open_check"]["check_ref"]
    _refused_by_the_budget(monkeypatch)
    view = S.take_turn(load_vault(paths.root), repository, lesson_id=lesson_id, action="answer_check",
                       payload={"answer": "det(A - tI) = 0", "tap": 4},
                       clients=clients(fake), clock=FrozenClock(NOW + timedelta(minutes=2)))
    assert view["closed"] and view["close_reason"] == "budget"
    saved = _payloads(repository, lesson_id, "check_answer")
    # Failed before: the lesson closed and the learner's text was kept nowhere.
    assert len(saved) == 1
    assert saved[0]["check_ref"] == check_ref and saved[0]["answer"] == "det(A - tI) = 0" and saved[0]["tap"] == 4
    assert saved[0]["assessed"] is False and saved[0]["unassessed_because"] == "budget"
    assert _turns(repository, lesson_id, "check_result") == []
    with repository.connection() as connection:
        assert connection.execute("SELECT COUNT(*) FROM practice_attempts").fetchone()[0] == 0


def test_a_budget_refused_probe_answer_is_saved_unassessed_with_the_close(tmp_path, monkeypatch):
    lesson, probe = _served(tmp_path)
    _refused_by_the_budget(monkeypatch)
    view = lesson.act("answer_probe", {"answer": "(1, 0) by three", "tap": 3}, turns=[close_turn()])
    assert view["closed"] and view["close_reason"] == "budget"
    saved = _payloads(lesson.repository, lesson.lesson_id, PR.ANSWER)
    assert len(saved) == 1  # failed before: none
    assert saved[0]["probe_ref"] == probe.ref and saved[0]["answer"] == "(1, 0) by three"
    assert saved[0]["assessed"] is False and saved[0]["unassessed_because"] == "budget"
    assert lesson.rows("SELECT COUNT(*) FROM practice_attempts WHERE id = ?", (probe.attempt_id,)) == [(0,)]


def test_a_retry_of_a_stranded_check_answer_turn_appends_no_second(tmp_path, monkeypatch):
    """A check answer turn an earlier build left behind when its grade failed (it wrote the turn before grading): the
    retry grades under that turn's attempt reference and appends no second answer turn."""

    from learnloop.db.stores import lessons as store

    paths, repository = build_teacher_vault(tmp_path / "vault")
    fake = TeacherFake([plan_turn, check_turn()])
    view = S.open_lesson(load_vault(paths.root), repository, entry="learning_object", learning_object_ids=["lo_eigen"],
                         clients=clients(fake), clock=FrozenClock(NOW))
    lesson_id = view["lesson_id"]
    view = S.take_turn(load_vault(paths.root), repository, lesson_id=lesson_id, action="reply",
                       payload={"text": "and?"}, clients=clients(fake), clock=FrozenClock(NOW + timedelta(minutes=1)))
    check_ref = view["open_check"]["check_ref"]
    item_id = S.load_state(repository, lesson_id).open_check["item_id"]
    with repository.atomic():
        store.append_turn(repository.connection(), lesson_id=lesson_id, actor="learner", action="check_answer",
                          validation="ok", refs={"item": item_id, "attempt": "01STRANDEDATTEMPT00000000"},
                          payload={"check_ref": check_ref, "answer": "det(A - tI) = 0", "thinking": None, "tap": 5},
                          created_at=(NOW + timedelta(minutes=2)).isoformat())
    S.take_turn(load_vault(paths.root), repository, lesson_id=lesson_id, action="answer_check",
                payload={"answer": "det(A - tI) = 0", "tap": 5}, clients=clients(fake),
                clock=FrozenClock(NOW + timedelta(minutes=3)))
    answers = _turns(repository, lesson_id, "check_answer")
    assert len(answers) == 1  # failed before: a second answer turn under a second attempt reference
    results = _turns(repository, lesson_id, "check_result")
    assert len(results) == 1
    import json

    assert json.loads(results[0][0])["attempt"] == "01STRANDEDATTEMPT00000000"
