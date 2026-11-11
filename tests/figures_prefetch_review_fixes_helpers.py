"""What other test files use from ``tests/test_figures_prefetch_review_fixes.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from learnloop.vault.loader import load_vault

from tests.figure_fixtures import set_config


def _planned_lesson(tmp_path, author):
    from learnloop.teacher import service as S
    from tests.teacher_fakes import TeacherFake, build_teacher_vault, plan_turn
    from tests.figures_prefetch_helpers import seed_wait
    from tests.reader_rw5d_p4b_teacher_visuals_helpers import GOAL, _aliases, _builder, _clients

    def plan_with_visual(context):
        turn = plan_turn(context)
        turn["requests"][0]["plan"][0]["visual"] = {"goal": GOAL, "anchors": _aliases(context)[:1]}
        return turn

    def step(context):
        return {"message": "Step one.", "visual": {"goal": "", "anchors": [], "planned_node": "n1"}}

    paths, repository = build_teacher_vault(tmp_path / "vault")
    set_config(paths, "figures", prefetch_enabled=True)
    seed_wait(repository)
    fake = TeacherFake([plan_with_visual, step])
    build = _builder(paths, repository, author)
    view = S.open_lesson(load_vault(paths.root), repository, entry="learning_object", learning_object_ids=["lo_eigen"],
                         clients=_clients(fake, build))
    return paths, repository, fake, build, view
