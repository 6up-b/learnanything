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


# --- TE5-R8: Try again and Continue target the step that waits ------------------------------------------------------

PHRASE = "when diagonalization fails"


def _proposal(_context):
    return {"message": "Here is another topic you could study.", "requests": [
        {"action": "create_goal_lo", "phrase": PHRASE, "title": "Defective matrices",
         "statement": "Recognize a missing eigenvector.", "anchors": []}]}


def test_try_again_after_an_interrupted_add_repeats_the_add(tmp_path):
    from tests.deliverable_fixtures import DeliverableFake

    paths, repository = build_teacher_vault(tmp_path / "vault")
    resolver = DeliverableFake(unmatched=(PHRASE,))
    fake = TeacherFake([_proposal])
    providers = clients(fake)
    providers.resolver = lambda: resolver
    lesson = S.open_lesson(load_vault(paths.root), repository, entry="learning_object",
                           learning_object_ids=["lo_eigen"], clients=providers)["lesson_id"]
    offer, = [row for row in S.load_state(repository, lesson).turns if row["action"] == "topic_offer"]
    add = {"text": f"Add t{offer['seq']}"}
    # The catalog changed, so Add needs a fresh resolution, and the resolver is down.
    from learnloop.ai.errors import AIProviderUnavailable

    from learnloop.vault.yaml_io import read_yaml, write_yaml

    path = paths.learning_object_path("linear-algebra", "lo_det")
    record = read_yaml(path)
    record["summary"] = "Determinants, revised."
    write_yaml(path, record)
    resolver.fail = AIProviderUnavailable("the plan is down")
    with pytest.raises(S.LessonError) as failed:
        S.take_turn(load_vault(paths.root), repository, lesson_id=lesson, action="reply", payload=add,
                    clients=providers)
    assert failed.value.details["retry"] == "repeat"  # nothing was recorded: resume would answer nothing
    assert S.retry_kind(repository, lesson) == "repeat"
    resolver.fail = None
    S.take_turn(load_vault(paths.root), repository, lesson_id=lesson, action="reply", payload=add, clients=providers)
    assert [row["action"] for row in S.load_state(repository, lesson).turns if row["refs"].get("offer")] == [
        "topic_requested", "topic_accepted"]


def test_continue_after_a_restart_answers_a_saved_reply(tmp_path):
    from learnloop.ai.errors import AIProviderUnavailable

    def down(_context):
        raise AIProviderUnavailable("the plan is down")

    paths, repository = build_teacher_vault(tmp_path / "vault")
    fake = TeacherFake([{"message": "Hello."}, down])
    lesson = S.open_lesson(load_vault(paths.root), repository, entry="learning_object",
                           learning_object_ids=["lo_eigen"], clients=clients(fake))["lesson_id"]
    with pytest.raises(S.LessonError) as failed:
        S.take_turn(load_vault(paths.root), repository, lesson_id=lesson, action="reply",
                    payload={"text": "what next?"}, clients=clients(fake))
    assert failed.value.details["retry"] == "resume"
    reopened = S.view_lesson(load_vault(paths.root), repository, lesson)  # the restart: the window reads the lesson
    assert reopened["awaiting_teacher"] is True
    fake.turns = [{"message": "Next: the characteristic polynomial."}]
    answered = S.take_turn(load_vault(paths.root), repository, lesson_id=lesson, action="resume", payload={},
                           clients=clients(fake))
    assert answered["awaiting_teacher"] is False
    assert answered["feed"][-1]["text"] == "Next: the characteristic polynomial."


# --- TE5-R9: an oversized catalog never wedges the lesson -----------------------------------------------------------


def test_an_oversized_catalog_is_noted_and_close_always_works(tmp_path, monkeypatch):
    from learnloop.source_retrieval import deliverables as DL
    from learnloop.teacher import actions as A
    from tests.deliverable_fixtures import DeliverableFake

    def too_large(*_args, **_kwargs):
        raise DL.DeliverableError("too_large", "Your vault has more topics than LearnLoop can read in one call.")

    paths, repository = build_teacher_vault(tmp_path / "vault")
    resolver = DeliverableFake(unmatched=(PHRASE,))
    fake = TeacherFake([_proposal])
    providers = clients(fake)
    providers.resolver = lambda: resolver
    with monkeypatch.context() as patch:
        patch.setattr(DL, "_bounded_topics", too_large)
        opened = S.open_lesson(load_vault(paths.root), repository, entry="learning_object",
                               learning_object_ids=["lo_eigen"], clients=providers)
    lesson = opened["lesson_id"]
    offer, = [row["payload"] for row in S.load_state(repository, lesson).turns if row["action"] == "topic_offer"]
    assert offer == {"status": "unavailable", "reason": "too_large"} and resolver.calls == 0
    assert "more topics than LearnLoop can read at once" in json.dumps(opened["feed"])
    # A turn whose offer fails every time it runs is left unexecuted: Close still closes the lesson.
    def broken(*_args, **_kwargs):
        raise RuntimeError("the offer cannot be resolved")

    monkeypatch.setattr(A, "resolve_offer", broken)
    fake.turns = [_proposal]
    with pytest.raises(RuntimeError):
        S.take_turn(load_vault(paths.root), repository, lesson_id=lesson, action="reply", payload={"text": "another?"},
                    clients=providers)
    assert S.load_state(repository, lesson).unexecuted is not None
    closed = S.take_turn(load_vault(paths.root), repository, lesson_id=lesson, action="close", payload={},
                         clients=providers)
    assert closed["closed"]


# --- TE5-R10: recovery uses the model that produced the accepted turn -----------------------------------------------


def test_a_recovered_forecast_names_the_model_that_produced_its_turn(tmp_path, monkeypatch):
    from tests.teacher_fakes import landed_turn

    class Second(TeacherFake):
        model = "second-teacher-model"

    paths, repository = build_teacher_vault(tmp_path / "vault")
    first = TeacherFake([plan_turn])
    lesson = S.open_lesson(load_vault(paths.root), repository, entry="learning_object",
                           learning_object_ids=["lo_eigen"], clients=clients(first))["lesson_id"]
    second = Second([landed_turn()])
    with monkeypatch.context() as patch:
        patch.setattr(S, "_forecast", lambda *_a, **_k: (_ for _ in ()).throw(RuntimeError("stopped")))
        with pytest.raises(RuntimeError):
            S.take_turn(load_vault(paths.root), repository, lesson_id=lesson, action="reply",
                        payload={"text": "go"}, clients=clients(second))
    S.view_lesson(load_vault(paths.root), repository, lesson)  # the recovery: no model call
    forecast, = [row["payload"] for row in S.load_state(repository, lesson).turns if row["action"] == "forecast"]
    assert str(forecast["family"]).endswith(":second-teacher-model")


# --- TE5-R11: consent recovery checks the catalog before it publishes ----------------------------------------------


def test_consent_interrupted_before_publication_rechecks_the_catalog(tmp_path, monkeypatch):
    from learnloop.goals import goal_lo
    from learnloop.source_retrieval.deliverables import create_lesson_topic
    from tests.deliverable_fixtures import DeliverableFake

    paths, repository = build_teacher_vault(tmp_path / "vault")
    resolver = DeliverableFake(unmatched=(PHRASE,))
    fake = TeacherFake([_proposal])
    providers = clients(fake)
    providers.resolver = lambda: resolver
    lesson = S.open_lesson(load_vault(paths.root), repository, entry="learning_object",
                           learning_object_ids=["lo_eigen"], clients=providers)["lesson_id"]
    offer, = [row for row in S.load_state(repository, lesson).turns if row["action"] == "topic_offer"]
    with monkeypatch.context() as patch:
        patch.setattr(goal_lo, "_write_goal_lo", lambda *_a, **_k: (_ for _ in ()).throw(RuntimeError("stopped")))
        with pytest.raises(RuntimeError):
            S.take_turn(load_vault(paths.root), repository, lesson_id=lesson, action="reply",
                        payload={"text": f"Add t{offer['seq']}"}, clients=providers)
    assert [row["action"] for row in S.load_state(repository, lesson).turns if row["refs"].get("offer")] == [
        "topic_requested"]
    # The equivalent topic is added elsewhere in the vault before the lesson resumes.
    existing = create_lesson_topic(load_vault(paths.root), repository, lesson_id="elsewhere", phrase=PHRASE,
                                   title="Defective matrices", statement="Recognize a missing eigenvector.",
                                   subject_id=offer["payload"]["subject_id"])
    resolver.unmatched = ()
    resolver.needs = (existing["learning_object_id"],)
    fake.turns = [{"message": "Go on."}]
    S.take_turn(load_vault(paths.root), repository, lesson_id=lesson, action="reply", payload={"text": "ok"},
                clients=providers)
    assert [row["action"] for row in S.load_state(repository, lesson).turns if row["refs"].get("offer")] == [
        "topic_requested", "topic_refused"]
    assert [lo for lo in load_vault(paths.root).learning_objects if lo.startswith("lo_goal_")] == [
        existing["learning_object_id"]]
