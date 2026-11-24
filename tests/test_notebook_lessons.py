"""A Teacher lesson whose medium is a marimo notebook (spec §11.2), on the sidecar's side: where the notebook is
(``notebooks/lessons/<lesson id>.py``), ``lesson.view`` naming the medium, ``notebook.open`` opening a lesson on its
own notebook with its commit points and held cells, a closed lesson's notebook opened as a review (nothing
released), and no row written by any of it. No model call; the runtime is a recording fake (the real sandbox is
tests/test_notebook_runtime_sandbox.py)."""

from __future__ import annotations

from pathlib import Path

import pytest

from learnloop.notebook_runtime.lessons import LESSON_NOTEBOOKS, lesson_contract, lesson_notebook_path
from learnloop.teacher import service as S
from learnloop.vault.loader import load_vault
from learnloop_sidecar.errors import SidecarError
from tests.notebook_runtime_helpers import LESSON_NOTEBOOK, RecordingRuntime, session
from tests.teacher_fakes import TeacherFake, build_teacher_vault, clients, plan_turn


@pytest.fixture
def lessons(tmp_path):
    from tests.teacher_te1_successor_helpers import _Ctx

    paths, repository = build_teacher_vault(tmp_path / "vault")
    ctx = _Ctx(paths, repository)
    ctx.vault_root = paths.root
    ctx.notebook_runtime = RecordingRuntime()
    return paths, repository, ctx


def _open_lesson(paths, repository) -> str:
    view = S.open_lesson(load_vault(paths.root), repository, entry="learning_object", learning_object_ids=["lo_eigen"],
                         clients=clients(TeacherFake([plan_turn])))
    return str(view["lesson_id"])


def _close(paths, repository, lesson_id: str) -> None:
    S.take_turn(load_vault(paths.root), repository, lesson_id=lesson_id, action="stop", payload={},
                clients=clients(TeacherFake([])))


def _write_notebook(paths, lesson_id: str, text: str = LESSON_NOTEBOOK) -> Path:
    path = Path(paths.root) / LESSON_NOTEBOOKS / f"{lesson_id}.py"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path


def _row_counts(repository) -> dict[str, int]:
    with repository.connection() as connection:
        names = [row[0] for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'").fetchall()]
        return {name: int(connection.execute(f'SELECT COUNT(*) FROM "{name}"').fetchone()[0]) for name in names}


def _open(ctx, owner, **extra):
    from learnloop_sidecar.handlers import notebooks as N

    return N.notebook_open_handler(ctx, N.NotebookOpenInput.model_validate({"owner": owner, **extra}))


# -- where the notebook is, and what it holds ------------------------------------------------------------------------

def test_a_lessons_notebook_is_its_vault_file_or_none(tmp_path):
    assert lesson_notebook_path(tmp_path, "les_1") is None
    (tmp_path / LESSON_NOTEBOOKS).mkdir(parents=True)
    (tmp_path / LESSON_NOTEBOOKS / "les_1.py").write_text("import marimo\n")
    assert lesson_notebook_path(tmp_path, "les_1") == "notebooks/lessons/les_1.py"
    assert lesson_notebook_path(tmp_path, "../les_1") is None and lesson_notebook_path(tmp_path, "a/b") is None


def test_commit_points_and_held_cells_are_read_from_the_notebooks_cells():
    contract = lesson_contract(LESSON_NOTEBOOK.encode())
    assert contract == {"points": [{"name": "commit_square", "held": ["reveal_square"]}], "held": ["preface", "reveal_square"]}
    two = '''import marimo
app = marimo.App()
@app.cell(hide_code=True)
def commit_a(mo):
    return
@app.cell(disabled=True, hide_code=True)
def reveal_a(mo):
    return
@app.cell
def commit_b(mo):
    return
@app.cell(disabled=True)
def reveal_b1(mo):
    return
@app.cell(disabled=False)
def plain(mo):
    return
@app.cell(disabled=True)
def reveal_b2(mo):
    return
def not_a_cell():
    return
'''
    assert lesson_contract(two.encode())["points"] == [{"name": "commit_a", "held": ["reveal_a"]},
                                                     {"name": "commit_b", "held": ["reveal_b1", "reveal_b2"]}]
    assert lesson_contract(b"def (") == {"points": [], "held": []}


def test_a_commit_is_a_value_on_a_commit_points_own_control_and_a_review_commits_nothing(tmp_path):
    from learnloop.notebook_runtime.supervisor import note_commits

    held = session(tmp_path)
    held.contract = lesson_contract(LESSON_NOTEBOOK.encode())
    held.cell_ids = {"commit_square": "vblA", "echo": "bkHC", "reveal_square": "lEQa"}
    note_commits(held, {"vblA-0": "", "bkHC-0": "faster"})
    assert held.commits == set() and held.releasable() == set()
    note_commits(held, {"vblA-0": "faster"})
    assert held.commits == {"commit_square"} and held.releasable() == {"reveal_square"}
    assert held.view_dict()["lesson"] == {"review": False, "released": [], "commit_points": [
        {"name": "commit_square", "held": ["reveal_square"], "committed": True}]}
    review = session(tmp_path)
    review.contract, review.review, review.cell_ids = held.contract, True, held.cell_ids
    note_commits(review, {"vblA-0": "faster"})
    assert review.commits == set() and review.releasable() == set()
    assert "lesson" not in session(tmp_path).view_dict()  # any other notebook says nothing of lessons


# -- the RPCs ------------------------------------------------------------------------------------------------------

def test_lesson_view_names_the_notebook_medium_only_when_the_lesson_has_one(lessons):
    from learnloop_sidecar.handlers import lesson as H

    paths, repository, ctx = lessons
    lesson_id = _open_lesson(paths, repository)
    plain = H.lesson_view(ctx, H.LessonViewInput(lesson_id=lesson_id))
    assert "medium" not in plain and "notebookPath" not in plain
    _write_notebook(paths, lesson_id)
    shown = H.lesson_view(ctx, H.LessonViewInput(lesson_id=lesson_id))
    assert shown["medium"] == "notebook" and shown["notebookPath"] == f"notebooks/lessons/{lesson_id}.py"
    assert {key: value for key, value in shown.items() if key not in ("medium", "notebookPath")} == plain


def test_a_lesson_opens_on_its_own_notebook_with_its_commit_points(lessons):
    paths, repository, ctx = lessons
    lesson_id = _open_lesson(paths, repository)
    _write_notebook(paths, lesson_id)
    _open(ctx, f"lesson:{lesson_id}")
    opened = ctx.notebook_runtime.opens[-1]
    assert opened["source"] == LESSON_NOTEBOOK.encode() and opened["view"] == "app"
    assert opened["contract"] == lesson_contract(LESSON_NOTEBOOK.encode()) and opened["review"] is False
    _open(ctx, f"lesson:{lesson_id}", path=f"notebooks/lessons/{lesson_id}.py")  # its own path, named: the same
    assert ctx.notebook_runtime.opens[-1]["source"] == opened["source"]
    other = Path(paths.root) / "notebooks" / "other.py"
    other.write_text("import marimo\n")
    with pytest.raises(SidecarError) as caught:
        _open(ctx, f"lesson:{lesson_id}", path="notebooks/other.py")
    assert caught.value.code == "notebook_path_invalid"


def test_a_lesson_without_a_notebook_and_an_unknown_lesson_without_a_path_are_refused(lessons):
    paths, repository, ctx = lessons
    lesson_id = _open_lesson(paths, repository)
    for owner in (f"lesson:{lesson_id}", "lesson:les_nowhere"):
        with pytest.raises(SidecarError) as caught:
            _open(ctx, owner)
        assert caught.value.code == "notebook_path_invalid"
    assert ctx.notebook_runtime.opens == []


def test_a_finished_lessons_notebook_is_a_review_and_writes_nothing(lessons):
    from learnloop_sidecar.handlers import lesson as H

    paths, repository, ctx = lessons
    lesson_id = _open_lesson(paths, repository)
    _close(paths, repository, lesson_id)
    _write_notebook(paths, lesson_id)
    before = _row_counts(repository)
    view = H.lesson_view(ctx, H.LessonViewInput(lesson_id=lesson_id))
    _open(ctx, f"lesson:{lesson_id}")
    assert view["closed"] is True and view["medium"] == "notebook"
    assert ctx.notebook_runtime.opens[-1]["review"] is True
    assert _row_counts(repository) == before


def test_a_refused_release_is_said_and_the_inputs_refuse_extra_fields(lessons):
    from learnloop.notebook_runtime.runtime import ReleaseRefused
    from learnloop_sidecar.handlers import notebooks as N

    _paths, _repository, ctx = lessons
    ctx.notebook_runtime = RecordingRuntime(refuse_release=ReleaseRefused("a review releases nothing"))
    with pytest.raises(SidecarError) as caught:
        N.notebook_release_handler(ctx, N.NotebookReleaseInput.model_validate({"sessionId": "nbs_1", "cells": ["reveal"]}))
    assert caught.value.code == "notebook_release_refused"
    with pytest.raises(ValueError):
        N.NotebookOpenInput.model_validate({"owner": "lesson:les_1", "review": True})


def test_a_lesson_closed_elsewhere_releases_nothing_more(lessons):
    """The lesson closes on another surface while its notebook runs: the next status reads it as a review and a
    release is refused, from the lesson's own record, not the frame's."""

    from learnloop_sidecar.handlers import notebooks as N

    paths, repository, ctx = lessons
    lesson_id = _open_lesson(paths, repository)
    _write_notebook(paths, lesson_id)
    _open(ctx, f"lesson:{lesson_id}")
    release = N.NotebookReleaseInput.model_validate({"sessionId": "nbs_rec", "cells": ["reveal_square"]})
    assert N.notebook_release_handler(ctx, release)["released"] == ["reveal_square"]
    _close(paths, repository, lesson_id)
    status = N.notebook_status_handler(ctx, N.NotebookSessionInput.model_validate({"sessionId": "nbs_rec"}))
    assert status["lesson"]["review"] is True
    with pytest.raises(SidecarError) as caught:
        N.notebook_release_handler(ctx, release)
    assert caught.value.code == "notebook_release_refused"
    assert ctx.notebook_runtime.releases == [["reveal_square"]]
