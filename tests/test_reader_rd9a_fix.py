"""RD9a's fix round (backend): one additions pad per lesson, and a finished lesson's review in recorded order. Every
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
