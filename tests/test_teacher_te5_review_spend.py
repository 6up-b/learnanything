"""TE5 review fix round, spend (TE5-R3): every physical request a lesson makes meets the lesson's settings on the route
it actually takes. A subscription teacher with a separately metered grader and the lesson's price or cap unset: the
grader's request is never sent, the answer is kept unassessed and the lesson says why in plain words."""
from __future__ import annotations

import json

import pytest

from learnloop.teacher import service as S
from learnloop.vault.loader import load_vault
from tests.teacher_fakes import TeacherFake, build_teacher_vault, check_turn, plan_turn
from tests.teacher_te1_review_fixes_helpers import MeteredTeacher
from tests.ux_phase1_support import set_config


class SubscriptionTeacher(TeacherFake):
    provider_name = "plan_teacher"
    provider_type = "chatgpt_plan"


class MeteredGrader(MeteredTeacher):
    provider_name = "openrouter_grader"
    provider_type = "openrouter"


def _rows(repository, sql, params=()):
    with repository.connection() as connection:
        return [tuple(row) for row in connection.execute(sql, params).fetchall()]


@pytest.mark.parametrize(("price", "cap"), [(None, None), (1.0, None), (None, 5.0)])
def test_a_metered_grader_without_the_lessons_settings_is_never_sent(tmp_path, price, cap):
    paths, repository = build_teacher_vault(tmp_path / "vault")
    settings = {key: value for key, value in ((("teacher", "metered_price_per_million"), price),
                                              (("teacher", "max_lesson_cost_usd"), cap)) if value is not None}
    if settings:
        set_config(paths.root, settings)
    teacher, grader = SubscriptionTeacher([plan_turn, check_turn()]), MeteredGrader()
    providers = S.Clients(teacher=lambda: teacher, grading=lambda: grader, grading_source="ai")
    view = S.open_lesson(load_vault(paths.root), repository, entry="learning_object", learning_object_ids=["lo_eigen"],
                         clients=providers)
    lesson = view["lesson_id"]
    S.take_turn(load_vault(paths.root), repository, lesson_id=lesson, action="reply", payload={"text": "go"},
                clients=providers)
    closed = S.take_turn(load_vault(paths.root), repository, lesson_id=lesson, action="answer_check",
                         payload={"answer": "det(A - tI) = 0", "tap": 4}, clients=providers)
    assert not grader.grading_contexts  # never sent
    assert closed["closed"] and closed["close_reason"] == "budget"
    assert S.METERED_SETTINGS_LINE in closed["notices"]
    answer, = [json.loads(row[0]) for row in _rows(
        repository, "SELECT p.payload_json FROM lesson_turns t JOIN lesson_turn_payloads p ON p.turn_id = t.id "
                    "WHERE t.action = 'check_answer'")]
    assert answer["assessed"] is False and answer["answer"] == "det(A - tI) = 0"
    assert not _rows(repository, "SELECT 1 FROM lesson_turns WHERE action IN ('spend', 'spend_reserved')")


def test_a_metered_grader_with_the_settings_is_reserved_and_settled_into_the_close(tmp_path):
    paths, repository = build_teacher_vault(tmp_path / "vault")
    set_config(paths.root, {("teacher", "metered_price_per_million"): 1.0, ("teacher", "max_lesson_cost_usd"): 5.0})
    teacher, grader = SubscriptionTeacher([plan_turn, check_turn(), {"message": "Bye."}]), MeteredGrader()
    providers = S.Clients(teacher=lambda: teacher, grading=lambda: grader, grading_source="ai")
    lesson = S.open_lesson(load_vault(paths.root), repository, entry="learning_object", learning_object_ids=["lo_eigen"],
                           clients=providers)["lesson_id"]
    S.take_turn(load_vault(paths.root), repository, lesson_id=lesson, action="reply", payload={"text": "go"},
                clients=providers)
    S.take_turn(load_vault(paths.root), repository, lesson_id=lesson, action="answer_check",
                payload={"answer": "det(A - tI) = 0", "tap": 4}, clients=providers)
    assert len(grader.grading_contexts) == 1
    S.take_turn(load_vault(paths.root), repository, lesson_id=lesson, action="close", payload={}, clients=providers)
    spend = [json.loads(row[0]) for row in _rows(
        repository, "SELECT p.payload_json FROM lesson_turns t JOIN lesson_turn_payloads p ON p.turn_id = t.id "
                    "WHERE t.action = 'spend'")]
    assert spend and {row["purpose"] for row in spend} <= {"grading", "blind_grading"}  # the double's seam and the real one
    receipt, = _rows(repository, "SELECT json_extract(receipt_json, '$.cost.metered_usd') FROM lesson_receipts")
    assert receipt[0] == pytest.approx(sum(row["usd"] for row in spend)) and receipt[0] > 0


def test_a_budget_refused_answer_says_it_was_saved_and_not_graded(tmp_path):
    """TE5-R18: the feed shows the saved status beside the answer the budget kept unassessed."""
    paths, repository = build_teacher_vault(tmp_path / "vault")
    teacher, grader = SubscriptionTeacher([plan_turn, check_turn()]), MeteredGrader()
    providers = S.Clients(teacher=lambda: teacher, grading=lambda: grader, grading_source="ai")
    lesson = S.open_lesson(load_vault(paths.root), repository, entry="learning_object", learning_object_ids=["lo_eigen"],
                           clients=providers)["lesson_id"]
    S.take_turn(load_vault(paths.root), repository, lesson_id=lesson, action="reply", payload={"text": "go"},
                clients=providers)
    closed = S.take_turn(load_vault(paths.root), repository, lesson_id=lesson, action="answer_check",
                         payload={"answer": "det(A - tI) = 0", "tap": 4}, clients=providers)
    answer, = [entry for entry in closed["feed"] if entry["kind"] == "learner" and entry["text"] == "det(A - tI) = 0"]
    assert answer["note"] == "Saved. This answer wasn't graded."
    reopened = S.view_lesson(load_vault(paths.root), repository, lesson)
    assert [entry.get("note") for entry in reopened["feed"] if entry["kind"] == "learner"] == [
        None, "Saved. This answer wasn't graded."]  # the reply "go", then the kept answer
