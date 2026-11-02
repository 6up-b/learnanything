"""Curriculum C4, folded into teacher TE1 (spec_deliverable_curriculum_v1 §8.2, §12 C4): the brief's goal
and sources from the deliverable and its path, the learner's linked notes as headers with ``read_note``,
behind ``teacher.brief.use_deliverable``. The fake tend over synthetic notes (C2's), every model a fake.
"""

from __future__ import annotations

import pytest

from learnloop.algorithm_versions import TEACHER_ALGORITHM_VERSION
from learnloop.teacher import service as S
from learnloop.vault.loader import load_vault
from tests.helpers import set_algorithm_version
from tests.reading_path_fixtures import call
from tests.teacher_fakes import TeacherFake, clients
from tests.test_notes_linked import _deliverable
from tests.ux_phase1_support import set_config


def _linked(tmp_path, monkeypatch):
    paths, repository, ctx, goal_id, fake_tend, corpus, notes = _deliverable(tmp_path, monkeypatch)
    call(ctx, "notes.path", {"goal_id": goal_id})
    set_algorithm_version(paths, TEACHER_ALGORITHM_VERSION)
    return paths, repository


def _note_reader(context):
    ids = [note["id"] for node in context["brief"]["nodes"] for note in node.get("your_notes") or []]
    return {"message": "Let me see what you wrote.", "requests": [{"action": "read_note", "refs": ids[:1]}]}


def test_the_brief_reads_the_deliverable_its_path_and_the_learners_notes(tmp_path, monkeypatch):
    paths, repository = _linked(tmp_path, monkeypatch)
    fake = TeacherFake([_note_reader, {"message": "Thanks."}])
    S.open_lesson(load_vault(paths.root), repository, entry="learning_object", learning_object_ids=["lo_eigen"],
                  clients=clients(fake))
    brief = fake.contexts[0]["brief"]
    goal = brief["goal"]
    assert goal["deliverable"]["sentence"] == "eigenvalues for my midterm"
    assert goal["resolved_by"]["lo_eigen"].startswith("your deliverable")
    node = next(node for node in brief["nodes"] if node["id"] == "lo_eigen")
    assert node["your_notes"] and all(note["voice"].startswith("the learner's own note") for note in node["your_notes"])
    assert "text" not in node["your_notes"][0]  # headers only; the text comes through read_note
    assert brief["sources"]["sections"][0]["ref"] == "ext_book/ch_eigen"
    notes = fake.contexts[1]["results"][0]["result"]["notes"]
    assert notes and notes[0]["text"] and notes[0]["voice"].startswith("the learner's own note")


def test_with_c4_off_the_brief_has_no_deliverable_no_notes_and_read_note_refuses(tmp_path, monkeypatch):
    paths, repository = _linked(tmp_path, monkeypatch)
    set_config(paths.root, {("teacher", "brief", "use_deliverable"): False})
    reader = {"message": "Let me see.", "requests": [{"action": "read_note", "refs": ["n:anything"]}]}
    fake = TeacherFake([reader, {"message": "ok"}])
    S.open_lesson(load_vault(paths.root), repository, entry="learning_object", learning_object_ids=["lo_eigen"],
                  clients=clients(fake))
    brief = fake.contexts[0]["brief"]
    assert "deliverable" not in brief["goal"]
    assert all("your_notes" not in node for node in brief["nodes"])
    assert "your deliverable" not in str(brief["goal"]["resolved_by"])
    assert fake.contexts[1]["results"][0]["result"]["refused"] == "notes_off"


def test_a_note_never_reaches_the_grader(tmp_path, monkeypatch):
    from tests.notes_fixtures import SENTINEL
    from tests.teacher_fakes import check_turn, plan_turn

    paths, repository = _linked(tmp_path, monkeypatch)
    fake = TeacherFake([_note_reader, plan_turn, check_turn()])
    view = S.open_lesson(load_vault(paths.root), repository, entry="learning_object",
                         learning_object_ids=["lo_eigen"], clients=clients(fake))
    S.turn(load_vault(paths.root), repository, lesson_id=view["lesson_id"], action="reply", payload={"text": "go"},
           clients=clients(fake))
    S.turn(load_vault(paths.root), repository, lesson_id=view["lesson_id"], action="answer_check",
           payload={"answer": "det(A - tI) = 0"}, clients=clients(fake))
    grading = [prompt for purpose, prompt in fake.prompts if purpose != "teacher_turn"]
    assert grading and all("Eigen stuff" not in p and SENTINEL not in p for p in grading)
