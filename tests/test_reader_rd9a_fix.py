"""Lesson windows: one additions pad per lesson, and a finished lesson's review in recorded order. Every
model is a fake."""
from __future__ import annotations

from learnloop.teacher import service as S
from learnloop.vault.loader import load_vault
from tests.reading_path_fixtures import call, context
from tests.teacher_fakes import TeacherFake, build_teacher_vault, clients, plan_turn


def _lesson(tmp_path):
    paths, repository = build_teacher_vault(tmp_path / "vault")
    view = S.open_lesson(load_vault(paths.root), repository, entry="learning_object", learning_object_ids=["lo_eigen"],
                         clients=clients(TeacherFake([plan_turn])))
    return paths, repository, view["lesson_id"]


def _create(ctx, client: str, pad_id: str, lesson_id: str) -> dict:
    return call(ctx, "pad.apply", {"clientId": client, "seq": 1, "padId": pad_id, "ops": [
        {"op": "create_pad", "kind": "lesson_additions", "title": "your additions", "lessonId": lesson_id}]})


def test_a_lesson_has_one_additions_pad_and_older_duplicates_are_all_named(tmp_path):
    from learnloop.db.stores import pads as pad_store

    paths, repository, lesson_id = _lesson(tmp_path)
    ctx = context(paths.root)
    assert _create(ctx, "window-a", "pad_a", lesson_id)["results"][0]["status"] == "ok"
    # Another window that had not seen pad_a: refused, so the lesson keeps one pad.
    refused = _create(ctx, "window-b", "pad_b", lesson_id)["results"][0]
    assert (refused["status"], refused["code"]) == ("refused", "lesson_additions_exists")
    listed = call(ctx, "lesson.list", {})["lessons"][0]
    assert (listed["additionsPadId"], listed["additionsPadIds"]) == ("pad_a", ["pad_a"])
    # Two pads made before the rule (as two clients could): both are named, the oldest first.
    with repository.atomic():
        pad_store.insert_pad(repository.connection(), pad_id="pad_z", kind="lesson_additions", title="", home_desk_id=None,
                             workbench_session_id=None, lesson_id=lesson_id, now="2099-01-01T00:00:00Z")
    listed = call(ctx, "lesson.list", {})["lessons"][0]
    assert (listed["additionsPadId"], listed["additionsPadIds"]) == ("pad_a", ["pad_a", "pad_z"])


def test_a_finished_te2_lesson_reviews_its_quick_question_in_recorded_order(tmp_path):
    from tests.teacher_fakes import close_turn
    from tests.teacher_te2_probes_helpers import _Lesson, probe_turn

    lesson = _Lesson(tmp_path, [probe_turn])
    lesson.generate()
    lesson.look()
    lesson.act("answer_probe", {"answer": "(1, 0) by three"}, turns=[close_turn()])
    lesson.act("stop", {}, turns=[close_turn()])
    review = lesson.look()
    assert review["closed"]
    kinds = [entry["kind"] for entry in review["feed"]]
    # The question, the answer and its result where they happened; the close card last.
    assert "probe_question" in kinds and kinds[-1] == "close"
    at = kinds.index("probe_question")
    assert kinds[at + 1:at + 3] == ["learner", "probe_result"]
    question = review["feed"][at]
    assert question["question"] and question["probe_ref"]


def test_a_quick_question_is_never_served_or_answered_in_a_desk_window(tmp_path):
    from learnloop.teacher import probes as PR
    from learnloop_sidecar.errors import SidecarError
    from tests.teacher_te2_probes_helpers import _Lesson, probe_turn

    lesson = _Lesson(tmp_path, [probe_turn])
    lesson.generate()
    served = "SELECT COUNT(*) FROM lesson_turns WHERE lesson_id = ? AND action = 'probe_served'"
    with PR.held_serving(True):
        window = S.view_lesson(lesson.vault(), lesson.repository, lesson.lesson_id)
    assert window["probe"]["status"] == "waiting" and "question" not in window["probe"]
    assert lesson.rows(served, (lesson.lesson_id,)) == [(0,)]
    # The lesson screen asks it (served there, as before the desks).
    screen = lesson.look()
    assert screen["probe"]["status"] == "open" and screen["probe"]["question"]
    assert lesson.rows(served, (lesson.lesson_id,)) == [(1,)]
    # A window's step never answers it, whatever it sends.
    ctx = context(lesson.paths.root)
    import pytest

    with pytest.raises(SidecarError) as refused:
        call(ctx, "lesson.turn", {"action": "answer_probe", "lesson_id": lesson.lesson_id, "probe_ref": screen["probe"]["probeRef"]
                                  if "probeRef" in screen["probe"] else screen["probe"]["probe_ref"],
                                  "answer": "(1, 0)", "frame": "window"})
    assert refused.value.code == "probe_on_lesson_screen"
