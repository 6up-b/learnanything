"""What other test files use from ``tests/test_teacher_te1_lesson.py``, kept here because a test file never imports
another (``tests/test_test_layout.py``)."""

from __future__ import annotations

from learnloop.teacher import service as S
from learnloop.vault.loader import load_vault
from tests.teacher_fakes import TeacherFake, build_teacher_vault, clients


def _open(tmp_path, turns, **kwargs):
    paths, repository = build_teacher_vault(tmp_path / "vault", **kwargs)
    fake = TeacherFake(turns)
    vault = load_vault(paths.root)
    view = S.open_lesson(vault, repository, entry="learning_object", learning_object_ids=["lo_eigen"],
                         clients=clients(fake))
    return paths, repository, fake, view
