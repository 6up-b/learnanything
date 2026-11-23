"""Reader workbench RD9a (spec §11.1, §12.5): the sidecar side of lesson windows.

``lesson.list`` names the lessons a window's tab and the path view's Teacher lesson row show (desktop only, no model
call, nothing written), with each lesson's additions pad. Review replay is ``lesson.view`` on a finished lesson: it
returns what was recorded, makes no model call and writes nothing. Every model is a fake; no network."""

from __future__ import annotations

import pytest

from learnloop.teacher import service as S
from learnloop.teacher.summaries import made_from
from learnloop.vault.loader import load_vault
from tests.teacher_fakes import TeacherFake, build_teacher_vault, check_turn, clients, close_turn, plan_turn


def _ctx(tmp_path):
    from tests.teacher_te1_successor_helpers import _Ctx

    paths, repository = build_teacher_vault(tmp_path / "vault")
    return paths, repository, _Ctx(paths, repository)


def _finished_lesson(paths, repository):
    """A lesson with a check answered and graded, whose next turn closes it (goal reached): what review must replay."""

    fake = TeacherFake([plan_turn, check_turn()])
    view = S.open_lesson(load_vault(paths.root), repository, entry="learning_object", learning_object_ids=["lo_eigen"],
                         clients=clients(fake))
    lesson_id = view["lesson_id"]
    S.take_turn(load_vault(paths.root), repository, lesson_id=lesson_id, action="reply", payload={"text": "go"},
                clients=clients(fake))
    fake.turns = [close_turn()]
    S.take_turn(load_vault(paths.root), repository, lesson_id=lesson_id, action="answer_check",
                payload={"answer": "det(A - tI) = 0"}, clients=clients(fake))
    closed = S.take_turn(load_vault(paths.root), repository, lesson_id=lesson_id, action="stop", payload={},
                         clients=clients(fake))
    assert closed["closed"]
    return lesson_id, closed


def _row_counts(repository) -> dict[str, int]:
    with repository.connection() as connection:
        names = [row[0] for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'").fetchall()]
        return {name: int(connection.execute(f'SELECT COUNT(*) FROM "{name}"').fetchone()[0]) for name in names}


def test_the_rpc_is_registered_desktop_only_and_refuses_extra_fields():
    from learnloop_mobile.allowlist import ALLOWLIST
    from learnloop_sidecar import handlers  # noqa: F401 - populates the registry
    from learnloop_sidecar.handlers import lesson as H
    from learnloop_sidecar.registry import METHOD_REGISTRY

    assert H.LESSON_WINDOW_RPCS == ("lesson.list",)
    assert "lesson.list" in METHOD_REGISTRY and "lesson.list" not in ALLOWLIST
    assert H.LessonListInput.model_validate({"lessonIds": ["les_1"]}).lesson_ids == ["les_1"]
    with pytest.raises(ValueError):
        H.LessonListInput.model_validate({"lessonIds": [], "extra": 1})


@pytest.mark.parametrize(("lesson", "refs", "expected"), [
    ({"origin": "router", "entry": "reader_selection"}, {"probe_episode": "pe1"}, "suggestion"),
    ({"origin": "learner_pick", "entry": "learning_object"}, {"probe_episode": "pe1"}, "check"),
    ({"origin": "learner_pick", "entry": "learning_object", "goal": {"typed": {"text": "t"}}}, {}, "question"),
    ({"origin": "learner_pick", "entry": "reader_selection"}, {}, "selection"),
    ({"origin": "learner_pick", "entry": "learning_object"}, {}, "topic"),
])
def test_made_from_reads_the_lessons_own_record(lesson, refs, expected):
    assert made_from(lesson, refs) == expected


def test_lesson_list_names_each_lesson_with_its_additions_pad(tmp_path):
    from learnloop.db.stores import pads as pad_store
    from learnloop_sidecar.handlers import lesson as H

    paths, repository, ctx = _ctx(tmp_path)
    assert H.lesson_list(ctx, H.LessonListInput())["lessons"] == []
    finished, _closed = _finished_lesson(paths, repository)
    open_view = S.open_lesson(load_vault(paths.root), repository, entry="learning_object",
                              learning_object_ids=["lo_eigen"], clients=clients(TeacherFake([plan_turn])))
    with repository.atomic():
        pad_store.insert_pad(repository.connection(), pad_id="pad_add1", kind="lesson_additions", title="",
                             home_desk_id=None, workbench_session_id=None, lesson_id=finished,
                             now="2026-11-23T09:00:00Z")
    before = _row_counts(repository)
    listed = H.lesson_list(ctx, H.LessonListInput())["lessons"]
    assert _row_counts(repository) == before
    by_id = {entry["lessonId"]: entry for entry in listed}
    assert set(by_id) == {finished, open_view["lesson_id"]}
    assert by_id[finished]["closed"] is True and by_id[finished]["closeReason"] == "goal_reached"
    assert by_id[finished]["additionsPadId"] == "pad_add1"
    assert by_id[open_view["lesson_id"]]["closed"] is False and by_id[open_view["lesson_id"]]["additionsPadId"] is None
    assert by_id[finished]["madeFrom"] == "topic" and by_id[finished]["learningObjectIds"] == ["lo_eigen"]
    assert by_id[finished]["title"] and by_id[finished]["openedAt"]
    named = H.lesson_list(ctx, H.LessonListInput.model_validate({"lessonIds": [finished]}))["lessons"]
    assert [entry["lessonId"] for entry in named] == [finished]
    assert H.lesson_list(ctx, H.LessonListInput.model_validate({"learningObjectIds": ["lo_nowhere"]}))["lessons"] == []
    on_lo = H.lesson_list(ctx, H.LessonListInput.model_validate({"learningObjectIds": ["lo_eigen"]}))["lessons"]
    assert {entry["lessonId"] for entry in on_lo} == {finished, open_view["lesson_id"]}


def test_lesson_list_is_empty_with_lessons_off(tmp_path):
    from learnloop_sidecar.handlers import lesson as H
    from tests.ux_phase1_support import set_config

    paths, repository, ctx = _ctx(tmp_path)
    _finished_lesson(paths, repository)
    assert H.lesson_list(ctx, H.LessonListInput())["lessons"]
    set_config(paths.root, {("teacher", "enabled"): False})
    assert H.lesson_list(ctx, H.LessonListInput())["lessons"] == []


def test_review_replays_a_finished_lesson_with_no_model_call_and_no_write(tmp_path):
    from learnloop_sidecar.dto import versioned
    from learnloop_sidecar.handlers import lesson as H

    paths, repository, ctx = _ctx(tmp_path)
    lesson_id, closed = _finished_lesson(paths, repository)
    before = _row_counts(repository)
    calls: list[str] = []

    def no_model(*_args, **_kwargs):
        calls.append("model")
        raise AssertionError("review made a model call")

    import learnloop.teacher.service as service

    original = service.execute_structured_operation
    service.execute_structured_operation = no_model
    try:
        replay = H.lesson_view(ctx, H.LessonViewInput(lesson_id=lesson_id))
        again = H.lesson_view(ctx, H.LessonViewInput(lesson_id=lesson_id))
    finally:
        service.execute_structured_operation = original
    assert calls == []
    assert _row_counts(repository) == before
    replay.pop("version", None)
    again.pop("version", None)
    assert replay == again
    # Exactly what was recorded: the feed the lesson showed when it closed, the check, its result and the close card.
    assert replay["feed"] == versioned(closed)["feed"]
    kinds = [entry["kind"] for entry in replay["feed"]]
    assert "check" in kinds and "check_result" in kinds and kinds[-1] == "close"
    assert replay["closed"] is True and replay["openCheck"] is None and replay["openPrediction"] is None
