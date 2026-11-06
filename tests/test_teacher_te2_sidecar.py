"""Teacher TE2's RPCs (desktop only): ``lesson.goal`` (a typed goal through C0b's resolver), ``lesson.open_lessons``
(Today's "Continue your lesson"), ``lesson.turn``'s new actions and its worker wake-up, and the config key the desktop
reads (``teacher.te2``). Every model is a fake; no network."""

from __future__ import annotations

import pytest

from learnloop.algorithm_versions import ROUTER_LEARNED_TAIL_ALGORITHM_VERSION, TEACHER_PROBES_ALGORITHM_VERSION
from learnloop.teacher import service as S
from learnloop.vault.loader import load_vault
from tests.teacher_fakes import TeacherFake, build_teacher_vault, clients, plan_turn


def test_the_rpcs_are_registered_desktop_only():
    from learnloop_mobile.allowlist import ALLOWLIST
    from learnloop_sidecar import handlers  # noqa: F401 - populates the registry
    from learnloop_sidecar.handlers import lesson as H
    from learnloop_sidecar.registry import METHOD_REGISTRY

    assert H.LESSON_TE2_RPCS == ("lesson.goal", "lesson.open_lessons")
    for name in H.LESSON_TE2_RPCS:
        assert name in METHOD_REGISTRY and name not in ALLOWLIST
    assert not set(H.LESSON_TE2_RPCS) & (set(H.LESSON_RPCS) | set(H.LESSON_ACTIVITY_RPCS))
    turn = H.LessonTurnInput.model_validate({"action": "answer_probe", "lessonId": "l", "probeRef": "p1", "answer": "x"})
    assert turn.probe_ref == "p1"
    opened = H.LessonTurnInput.model_validate({"action": "open", "entry": "typed_goal", "goalText": "g",
                                               "addTopics": ["a"], "subjectId": "s"})
    assert opened.add_topics == ["a"] and opened.subject_id == "s"


def _ctx(tmp_path, version=TEACHER_PROBES_ALGORITHM_VERSION):
    from tests.test_teacher_te1_successor import _Ctx

    paths, repository = build_teacher_vault(tmp_path / "vault", version=version)
    return paths, repository, _Ctx(paths, repository)


def test_lesson_goal_and_open_lessons_through_the_handlers(tmp_path, monkeypatch):
    from learnloop.source_retrieval import deliverables as DL
    from learnloop_sidecar.handlers import lesson as H
    from tests.deliverable_fixtures import DeliverableFake

    paths, repository, ctx = _ctx(tmp_path)
    fake = DeliverableFake(unmatched=("when diagonalization fails",))
    original = DL.resolve_typed_goal
    monkeypatch.setattr(DL, "resolve_typed_goal", lambda *a, **k: original(*a, **{**k, "client": fake}))
    found = H.lesson_goal(ctx, H.LessonGoalInput.model_validate({"text": "eigenvalues, and when diagonalization fails"}))
    assert found["status"] == "ready" and found["unmatched"][0]["phrase"] == "when diagonalization fails"
    assert H.lesson_open_lessons(ctx, H.LessonOpenLessonsInput())["lessons"] == []
    view = S.open_lesson(load_vault(paths.root), repository, entry="learning_object", learning_object_ids=["lo_eigen"],
                         clients=clients(TeacherFake([plan_turn])))
    listed = H.lesson_open_lessons(ctx, H.LessonOpenLessonsInput())["lessons"]
    assert [entry.get("lessonId", entry.get("lesson_id")) for entry in listed] == [view["lesson_id"]]


def test_below_the_tag_the_goal_rpc_refuses_and_the_config_carries_no_te2_key(tmp_path):
    from learnloop_sidecar.context import config_dto
    from learnloop_sidecar.errors import SidecarError
    from learnloop_sidecar.handlers import lesson as H

    paths, _repository, ctx = _ctx(tmp_path, version=ROUTER_LEARNED_TAIL_ALGORITHM_VERSION)
    with pytest.raises(SidecarError) as refused:
        H.lesson_goal(ctx, H.LessonGoalInput.model_validate({"text": "eigenvalues"}))
    assert refused.value.code == "teacher_unavailable"
    assert "te2" not in config_dto(load_vault(paths.root)).get("teacher", {})
    on, _r, _c = _ctx(tmp_path / "on")
    assert config_dto(load_vault(on.root))["teacher"]["te2"] is True
