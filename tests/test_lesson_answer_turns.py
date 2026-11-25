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
