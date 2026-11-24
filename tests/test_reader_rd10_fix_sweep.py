"""Where else a held LO's name could reach the workbench (spec §12.6.1, D15): the lesson windows' tabs and the path
view's lesson row (``lesson.list``) name nothing a due check covers, through the goal lens's one protection. Every
model is a fake."""
from __future__ import annotations

import re
from datetime import UTC, datetime, timedelta
from typing import Any

from learnloop.curriculum import commitments as C
from learnloop.curriculum import goal_lens as GL
from learnloop.source_retrieval import deliverable_path as DP
from learnloop.teacher import service as S
from learnloop.vault.loader import load_vault
from tests.teacher_fakes import TeacherFake, build_teacher_vault, clients, plan_turn


def _strings(value: Any, path: str = "") -> list[tuple[str, str]]:
    if isinstance(value, str):
        return [(path, value)]
    if isinstance(value, dict):
        return [found for key, child in value.items() for found in _strings(child, f"{path}.{key}" if path else key)]
    if isinstance(value, list):
        return [found for index, child in enumerate(value) for found in _strings(child, f"{path}[{index}]")]
    return []


def test_a_lesson_on_a_topic_whose_check_is_due_names_nothing_in_its_tab(tmp_path):
    from learnloop_sidecar.handlers import lesson as H
    from tests.teacher_te1_successor_helpers import _Ctx

    paths, repository = build_teacher_vault(tmp_path / "vault")
    ctx = _Ctx(paths, repository)
    S.open_lesson(load_vault(paths.root), repository, entry="learning_object", learning_object_ids=["lo_eigen"],
                  clients=clients(TeacherFake([plan_turn])))
    title = load_vault(paths.root).learning_objects["lo_eigen"].title
    assert H.lesson_list(ctx, H.LessonListInput())["lessons"][0]["title"] == title
    day = (datetime.now(UTC) - timedelta(days=1)).strftime("%Y-%m-%d")
    C.create_commitment(repository, action="test_me_later", intent_text="check", depth_preset=DP.READY_DEPTH_PRESET,
                        targets=[{"target_kind": "learning_object", "target_ref": "lo_eigen", "role": "required"}],
                        client_idempotency_key="rd10fix:lesson", due_hint=day, provenance={"via": "deliverable_ready"})
    listed = H.lesson_list(ctx, H.LessonListInput())["lessons"]
    assert (listed[0]["title"], listed[0]["goal"], listed[0]["held"]) == (GL.NEUTRAL_LO, None, True)
    word = title.split()[0].casefold()
    assert [(p, t) for p, t in _strings(listed) if word in t.casefold() and not re.search(r"(Id|Ids)(\[\d+\])?$", p)] == []
