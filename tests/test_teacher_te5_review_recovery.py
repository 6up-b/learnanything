"""TE5 review fix round, paid work and answers across a crash (TE5-R4, TE5-R7).

R4: a teacher turn whose response returned but whose acceptance did not commit is not bought again on resume (its
validated answer is saved under the request's identity); a check's answer is saved before its grader is called and its
grade under the answer's identity, so the reopened lesson shows the answer and Submit grades it once.
R7: an answer edited after a stranded one is its own revision: the transcript shows what was graded, on a grade and on
a budget refusal alike.
"""
from __future__ import annotations

import json
from datetime import timedelta

import pytest

from learnloop.clock import FrozenClock
from learnloop.db.stores import lessons as store
from learnloop.teacher import checks as CK
from learnloop.teacher import service as S
from learnloop.vault.loader import load_vault
from tests.helpers import NOW
from tests.teacher_fakes import TeacherFake, build_teacher_vault, check_turn, clients, plan_turn


def _payloads(repository, lesson_id, action):
    with repository.connection() as connection:
        return [(json.loads(refs), json.loads(payload)) for refs, payload in connection.execute(
            "SELECT t.refs_json, p.payload_json FROM lesson_turns t JOIN lesson_turn_payloads p ON p.turn_id = t.id "
            "WHERE t.lesson_id = ? AND t.action = ? ORDER BY t.seq", (lesson_id, action)).fetchall()]


def _teacher_calls(fake):
    return sum(1 for purpose, _prompt in fake.prompts if purpose == "teacher_turn")


def _lesson_with_open_check(tmp_path, fake):
    paths, repository = build_teacher_vault(tmp_path / "vault")
    lesson = S.open_lesson(load_vault(paths.root), repository, entry="learning_object", learning_object_ids=["lo_eigen"],
                           clients=clients(fake), clock=FrozenClock(NOW))["lesson_id"]
    S.take_turn(load_vault(paths.root), repository, lesson_id=lesson, action="reply", payload={"text": "and?"},
                clients=clients(fake), clock=FrozenClock(NOW + timedelta(minutes=1)))
    return paths, repository, lesson


def test_a_teacher_turn_returned_before_a_crash_is_not_bought_again(tmp_path, monkeypatch):
    paths, repository = build_teacher_vault(tmp_path / "vault")
    fake = TeacherFake([{"message": "Hello."}])
    lesson = S.open_lesson(load_vault(paths.root), repository, entry="learning_object",
                           learning_object_ids=["lo_eigen"], clients=clients(fake))["lesson_id"]
    real = S._record_reveals

    def crash(*_args, **_kwargs):
        raise RuntimeError("the process stopped after the teacher answered")

    fake.turns = [{"message": "A capybara walks two steps."}, {"message": "never bought"}]
    with monkeypatch.context() as patch:
        patch.setattr(S, "_record_reveals", crash)
        with pytest.raises(S.LessonError):
            S.take_turn(load_vault(paths.root), repository, lesson_id=lesson, action="reply",
                        payload={"text": "go on"}, clients=clients(fake))
    calls = _teacher_calls(fake)
    assert S._record_reveals is real
    resumed = S.take_turn(load_vault(paths.root), repository, lesson_id=lesson, action="resume", payload={},
                          clients=clients(fake))
    assert _teacher_calls(fake) == calls  # the saved answer, not a second purchase
    assert resumed["feed"][-1]["text"] == "A capybara walks two steps."
    with repository.connection() as connection:
        assert connection.execute("SELECT COUNT(*) FROM model_work_checkpoints WHERE purpose = ?",
                                  (S.TURN_CHECKPOINT_PURPOSE,)).fetchone()[0] == 0  # spent once recorded


def test_a_graded_answer_survives_a_crash_and_is_graded_once(tmp_path, monkeypatch):
    fake = TeacherFake([plan_turn, check_turn()])
    paths, repository, lesson = _lesson_with_open_check(tmp_path, fake)
    answer = {"answer": "det(A - tI) = 0", "thinking": "the roots of the polynomial", "tap": 4}

    def crash(*_args, **_kwargs):
        raise RuntimeError("the process stopped after the grade returned")

    with monkeypatch.context() as patch:
        patch.setattr(CK, "prepare_check_attempt", crash)
        with pytest.raises(RuntimeError):
            S.take_turn(load_vault(paths.root), repository, lesson_id=lesson, action="answer_check", payload=answer,
                        clients=clients(fake), clock=FrozenClock(NOW + timedelta(minutes=2)))
    graded = len(fake.grading_contexts)
    assert graded == 1
    reopened = S.view_lesson(load_vault(paths.root), repository, lesson)
    assert reopened["open_check"]["submitted"] == answer  # the reopened lesson shows what was submitted
    S.take_turn(load_vault(paths.root), repository, lesson_id=lesson, action="answer_check", payload=answer,
                clients=clients(fake), clock=FrozenClock(NOW + timedelta(minutes=3)))
    assert len(fake.grading_contexts) == graded  # graded once
    (_refs, turn), = _payloads(repository, lesson, "check_answer")
    assert turn["answer"] == answer["answer"] and turn["thinking"] == answer["thinking"]
    assert S.view_lesson(load_vault(paths.root), repository, lesson)["open_check"] is None


def _strand(repository, lesson, answer):
    state = S.load_state(repository, lesson)
    with repository.atomic():
        store.append_turn(repository.connection(), lesson_id=lesson, actor="learner", action="check_answer",
                          validation="ok", refs={"item": state.open_check["item_id"], "attempt": "01STRANDED0000000000"},
                          payload={"check_ref": state.open_check["check_ref"], "answer": answer, "thinking": None,
                                   "tap": 3}, created_at=(NOW + timedelta(minutes=2)).isoformat())


def test_an_answer_edited_after_a_stranded_one_is_graded_as_its_own_revision(tmp_path):
    fake = TeacherFake([plan_turn, check_turn()])
    paths, repository, lesson = _lesson_with_open_check(tmp_path, fake)
    _strand(repository, lesson, "2")
    S.take_turn(load_vault(paths.root), repository, lesson_id=lesson, action="answer_check",
                payload={"answer": "3", "tap": 4}, clients=clients(fake), clock=FrozenClock(NOW + timedelta(minutes=3)))
    assert fake.grading_contexts[-1].learner_answer_md == "3"
    answers = _payloads(repository, lesson, "check_answer")
    (result_refs, _result), = _payloads(repository, lesson, "check_result")
    graded = [payload["answer"] for refs, payload in answers if refs["attempt"] == result_refs["attempt"]]
    assert graded == ["3"] and result_refs["attempt"] != "01STRANDED0000000000"
    assert [payload["answer"] for _refs, payload in answers] == ["2", "3"]


def test_an_edited_answer_refused_by_the_budget_is_saved_as_typed(tmp_path, monkeypatch):
    from learnloop.ai.spend import SpendLimitExceeded

    fake = TeacherFake([plan_turn, check_turn()])
    paths, repository, lesson = _lesson_with_open_check(tmp_path, fake)
    _strand(repository, lesson, "2")

    def refused(*_args, **_kwargs):
        raise SpendLimitExceeded("over the lesson's cap", rule="max_estimated_usd")

    monkeypatch.setattr(CK, "grade_answer", refused)
    view = S.take_turn(load_vault(paths.root), repository, lesson_id=lesson, action="answer_check",
                       payload={"answer": "3", "tap": 4}, clients=clients(fake))
    assert view["closed"] and view["close_reason"] == "budget"
    answers = [payload for _refs, payload in _payloads(repository, lesson, "check_answer")]
    assert [row["answer"] for row in answers] == ["2", "3"]
    assert answers[-1]["assessed"] is False
