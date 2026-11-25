import pytest

from learnloop.adaptive_difficulty import surprise_forecast
from learnloop.teacher import service
from learnloop.vault.loader import load_vault
from tests.teacher_fakes import check_turn, clients, close_turn, plan_turn
from tests.test_teacher_te1_lesson import _open
from tests.test_teacher_te2_review_fixes import _served


@pytest.mark.parametrize("kind", ["check", "probe"])
def test_lesson_forecast_is_prepared_once_outside_the_writer(tmp_path, monkeypatch, kind):
    locks = []

    def forecast(vault, repository, **kwargs):
        connection = repository.connection()
        locks.append(connection.in_transaction)
        connection.close()
        return None

    monkeypatch.setattr(surprise_forecast, "safe_grade_receipt", forecast)
    if kind == "probe":
        lesson, _ = _served(tmp_path, version="mvp-0.74")
        lesson.act("answer_probe", {"answer": "(1, 0) by three"}, turns=[close_turn()])
    else:
        paths, repo, fake, view = _open(tmp_path, [plan_turn, check_turn()], version="mvp-0.74")
        vault = load_vault(paths.root)
        service.take_turn(vault, repo, lesson_id=view["lesson_id"], action="reply",
                          payload={"text": "Go ahead."}, clients=clients(fake))
        fake.turns = [close_turn()]
        service.take_turn(vault, repo, lesson_id=view["lesson_id"], action="answer_check",
                          payload={"answer": "det(A - tI) = 0"}, clients=clients(fake))
    assert locks == [False]


@pytest.mark.parametrize("kind", ["check", "probe"])
def test_withdrawal_during_preparation_discards_the_losing_grade(tmp_path, monkeypatch, kind):
    from learnloop.db.repositories import Repository
    from learnloop.db.stores import lessons

    if kind == "probe":
        lesson, probe = _served(tmp_path, version="mvp-0.74")
        repo, lesson_id = lesson.repository, lesson.lesson_id
        action, payload = "probe_retired", {"probe_ref": probe.ref, "reason": "withdrawn"}

        def submit():
            lesson.act("answer_probe", {"answer": "(1, 0) by three"}, turns=[close_turn()])
    else:
        paths, repo, fake, view = _open(tmp_path, [plan_turn, check_turn()], version="mvp-0.74")
        lesson_id = view["lesson_id"]
        vault = load_vault(paths.root)
        service.take_turn(vault, repo, lesson_id=lesson_id, action="reply", payload={"text": "Go ahead."},
                          clients=clients(fake))
        ref = service.load_state(repo, lesson_id).open_check["check_ref"]
        action, payload = "check_withdrawn", {"check_ref": ref}

        def submit():
            service.take_turn(vault, repo, lesson_id=lesson_id, action="answer_check",
                              payload={"answer": "det(A - tI) = 0"}, clients=clients(fake))

    prepared_ids = []

    def withdraw(_vault, repository, *, attempt_id, at, **kwargs):
        prepared_ids.append(attempt_id)
        other = Repository.attach(repository.sqlite_path)
        with other.atomic():
            lessons.append_turn(other.connection(), lesson_id=lesson_id, actor="code", action=action,
                                validation="ok", refs={}, payload=payload, created_at=at)

    monkeypatch.setattr(surprise_forecast, "safe_grade_receipt", withdraw)
    with pytest.raises(service.LessonError) as error:
        submit()
    assert error.value.code == f"stale_{kind}"
    [rejected] = prepared_ids
    assert repo.fetch_practice_attempt(rejected) is None
