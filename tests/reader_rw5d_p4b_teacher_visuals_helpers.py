"""What other test files use from ``tests/test_reader_rw5d_p4b_teacher_visuals.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

import hashlib
import json

from learnloop.figures import service as FS
from learnloop.teacher import service as S
from learnloop.vault.loader import load_vault

from tests.figure_fixtures import AuthorFake, flagship
from tests.teacher_fakes import TeacherFake, build_teacher_vault


#: TE1's turn schema and doctrine as they stood at main 1a33bb5db3 (before RW5d P4b), pinned: with
#: teacher.visuals off the teacher is sent exactly these.
TE1_SCHEMA_SHA256 = "9668bbc1796bd73e2169c6a402a8b5c656906cff03c75ce20f587eb3ba042dc0"
TE1_DOCTRINE_SHA256 = "ecec5db5b07d2ceb878fbfc578a547c70011a7dc8cf2b25f6418475062d296ea"
GOAL = "Let the learner move lambda while p stays at 0.3; watch the mass left of zero."
FIGURE_WORDS = "WOMBATFIGURE how the mass splits around zero"


def _spec(**changes):
    """The flagship figure (with its own predictions), claims dropped (this vault has no §5.4)."""

    base = {"source_claims": [], "assumptions": [{"text": "lambda > 0", "span_id": None, "quote": None}],
            "demonstrates": FIGURE_WORDS}
    return flagship(**{**base, **changes})


def _aliases(context):
    return [p["alias"] for s in context["brief"]["sources"].get("sections", []) for p in s.get("passages", [])]


def visual_turn(context, *, goal=GOAL, prediction=True):
    turn = {"message": "Here only lambda is yours to move.",
            "visual": {"goal": goal, "anchors": _aliases(context)[:1], "planned_node": None}}
    if prediction:
        turn["prediction"] = {"node": "n1", "prompt": "What happens to the left mass as lambda grows?",
                              "choices": []}
    return turn


def _clients(fake, builder):
    return S.Clients(teacher=lambda: fake, grading=lambda: fake, grading_source="ai", figures=builder)


def _builder(paths, repository, author, *, calls=None, spawn=None):
    def build(request):
        if calls is not None:
            calls.append(request)
        return FS.build_figure(load_vault(paths.root), repository, request, author_client=author, spawn_rich=spawn)

    return build


def _open(tmp_path, turns, *, author=None, config=None, builder=True, calls=None):
    from tests.ux_phase1_support import set_config

    paths, repository = build_teacher_vault(tmp_path / "vault")
    if config:
        set_config(paths.root, config)
    author = author if author is not None else AuthorFake([_spec()])
    fake = TeacherFake(turns)
    build = _builder(paths, repository, author, calls=calls) if builder else None
    view = S.open_lesson(load_vault(paths.root), repository, entry="learning_object", learning_object_ids=["lo_eigen"],
                         clients=_clients(fake, build))
    return paths, repository, fake, author, view, build


def _schema_sha(model):
    from learnloop.ai.strict_schema import strict_output_schema

    return hashlib.sha256(json.dumps(strict_output_schema(model), sort_keys=True).encode()).hexdigest()
