"""Review round 3, class 4 (atomic doors), exam finish: FR3-3 (an answer accepted while finish runs is applied before
the sitting completes, or the sitting stays open while it is pending; never reported with no attempt) and FR3-13 (an
attempt's failed completion work is not dropped: the next finish of the sitting resumes it). The intervention
allowance on retry is ``tests/test_post_attempt_pipeline.py``'s."""

from __future__ import annotations

import pytest

from learnloop.attempts import post_attempt
from learnloop.clock import FrozenClock
from learnloop.goals import exam_session
from learnloop.goals.exam_session import ExamSessionError, finish_exam, queue_exam_answer, record_exam_answer

from tests.exam_session_helpers import _grade, _reserved_and_started
from tests.helpers import NOW


def _during_finish(monkeypatch, action):
    real = exam_session.with_grade_forecast
    calls = {"n": 0}

    def forecast(*args, **kwargs):
        calls["n"] += 1
        if calls["n"] == 1:
            action()
        return real(*args, **kwargs)

    monkeypatch.setattr(exam_session, "with_grade_forecast", forecast)


def test_an_answer_accepted_while_finish_runs_is_applied_before_the_sitting_completes(tmp_path, monkeypatch):
    vault, repository, session = _reserved_and_started(tmp_path)
    session_id = session["session_id"]
    record_exam_answer(vault, repository, session_id, "pi_exam_a", answer_md="A", resolved_grade=_grade(4))
    _during_finish(monkeypatch, lambda: record_exam_answer(vault, repository, session_id, "pi_exam_b",
                                                           answer_md="B", resolved_grade=_grade(1)))
    finish_exam(vault, repository, session_id, clock=FrozenClock(NOW))
    answers = repository.exam_answers(session_id)
    assert len(answers) == 2 and all(answer["attempt_id"] for answer in answers)  # failed before: B had none
    assert repository.exam_session(session_id)["status"] == "completed"


def test_a_pending_answer_accepted_while_finish_runs_keeps_the_sitting_open(tmp_path, monkeypatch):
    vault, repository, session = _reserved_and_started(tmp_path)
    session_id = session["session_id"]
    record_exam_answer(vault, repository, session_id, "pi_exam_a", answer_md="A", resolved_grade=_grade(4))
    _during_finish(monkeypatch, lambda: queue_exam_answer(vault, repository, session_id, "pi_exam_b", answer_md="B"))
    with pytest.raises(ExamSessionError, match="pending"):
        finish_exam(vault, repository, session_id, clock=FrozenClock(NOW))
    assert repository.exam_session(session_id)["status"] == "in_progress"  # failed before: completed without B
    # Its grade lands; the next finish applies it and completes the sitting with both answers linked.
    monkeypatch.undo()
    record_exam_answer(vault, repository, session_id, "pi_exam_b", answer_md="B", resolved_grade=_grade(1))
    finish_exam(vault, repository, session_id, clock=FrozenClock(NOW))
    assert all(answer["attempt_id"] for answer in repository.exam_answers(session_id))
    assert repository.exam_session(session_id)["status"] == "completed"


def test_an_answers_failed_completion_work_is_resumed_by_the_next_finish(tmp_path, monkeypatch):
    vault, repository, session = _reserved_and_started(tmp_path)
    session_id = session["session_id"]
    record_exam_answer(vault, repository, session_id, "pi_exam_a", answer_md="A", resolved_grade=_grade(1))
    real = post_attempt.run_post_attempt_pipeline
    with monkeypatch.context() as patch:
        patch.setattr(post_attempt, "run_post_attempt_pipeline",
                      lambda *a, **k: (_ for _ in ()).throw(RuntimeError("bookkeeping failure")))
        report = finish_exam(vault, repository, session_id, clock=FrozenClock(NOW))
    (answer,) = repository.exam_answers(session_id)
    assert repository.attempt_completion(answer["attempt_id"])["status"] != "completed"
    assert post_attempt.run_post_attempt_pipeline is real
    assert finish_exam(vault, repository, session_id, clock=FrozenClock(NOW)) == report
    # Failed before: the stored report came back and the work stayed pending.
    assert repository.attempt_completion(answer["attempt_id"])["status"] == "completed"


def test_a_second_grade_of_the_same_answer_neither_replaces_the_first_nor_clears_its_link(tmp_path, monkeypatch):
    """Review round 4, R4-S11 (FR3-3's residue): two graders start on the same pending answer. The first grade stands:
    the second, of the same text, changes neither the stored grade nor, while finish applies the answer, its link
    (failed before: the upsert replaced the score and wrote the link back to none)."""

    vault, repository, session = _reserved_and_started(tmp_path)
    session_id = session["session_id"]
    queue_exam_answer(vault, repository, session_id, "pi_exam_a", answer_md="A")
    record_exam_answer(vault, repository, session_id, "pi_exam_a", answer_md="A", resolved_grade=_grade(4))
    record_exam_answer(vault, repository, session_id, "pi_exam_a", answer_md="A", resolved_grade=_grade(1))
    assert repository.exam_answer(session_id, "pi_exam_a")["rubric_score"] == 4  # failed before: 1

    real = exam_session.apply_attempt

    def late_grade_then_apply(*args, **kwargs):
        result = real(*args, **kwargs)
        record_exam_answer(vault, repository, session_id, "pi_exam_a", answer_md="A", resolved_grade=_grade(1))
        return result

    monkeypatch.setattr(exam_session, "apply_attempt", late_grade_then_apply)
    finish_exam(vault, repository, session_id, clock=FrozenClock(NOW))
    [answer] = repository.exam_answers(session_id)
    assert answer["attempt_id"] and answer["rubric_score"] == 4  # failed before: the link was cleared
    assert repository.exam_session(session_id)["status"] == "completed"
