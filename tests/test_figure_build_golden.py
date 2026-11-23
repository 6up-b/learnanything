"""The Show me figure build, golden (refactor K10.4's P-golden, strategy ``docs/reviews/k10-figures-strategy-2026-11-14.md``
section 4.2).

Each case presses a figure through the path the app takes (the sidecar's RPCs, or the lesson's builder) with fake
model answers and a fixed sandbox, and records: the prompts the figure author was sent; what the source check sent
its sandbox; every row the case wrote, changed or removed in the figure tables (``figure_build_golden_helpers.TABLES``);
the result the press returned; and the list the Reader reads after it. The structure steps K10.5-K10.9 move the
code that does all of this; they must leave every case byte for byte as recorded here (ids and wall times replaced
as the helper module says, everything else kept).

Recorded with ``FIGURE_BUILD_WRITE_GOLDEN=1`` into ``tests/fixtures/figure_build_golden.json``; never rewritten by
a structure step. No live model, no renderer, no sandbox process: the sealed sketch engine runs in process, as in
the other figure tests.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import pytest

from learnloop.figures import sketch_verify as SV
from learnloop.vault.loader import load_vault
from learnloop_sidecar.handlers import figures as FH
from tests import rich_fixtures as RF
from tests import sketch_fixtures as F
from tests.figure_build_golden_helpers import (
    check_golden,
    fixed_sandbox,
    normalized,
    recorded_twice,
    table_rows,
    written,
)
from tests.figure_fixtures import (
    EXTRACTION,
    AuthorFake,
    build,
    build_figure_vault,
    call,
    context,
    end_sketch_engine_absence,
    flagship,
    half_density,
    set_config,
)
from tests.rw5c_fixtures import build_check_vault

#: Thirty cases, each run twice in a vault of its own: about 45 s serial.
pytestmark = pytest.mark.slow

GOLDEN = Path(__file__).parent / "fixtures" / "figure_build_golden.json"
WRITE = os.environ.get("FIGURE_BUILD_WRITE_GOLDEN") == "1"
#: The order a case's record is walked in (the helper module's tokens are numbered by first appearance in it).
ORDER = ("prompts", "sandbox", "written", "result", "second", "delivered", "opened", "list", "lesson")
WHY = "a narrated video shows the spiral tighten as b grows"
#: A demonstrates line that reads like a code-owned check label (the label rule's repair).
LABEL_LIKE = "✓ checked against the book: the left mass is p"
PRESS = {"extractionId": EXTRACTION, "spanIds": ["p3"]}


class Press:
    """One vault, one sidecar context and one author, with the rows before the case began."""

    def __init__(self, root: Path, monkeypatch: Any, answers: list[Any], *, sketch: bool = False,
                 rich: bool = False, author: AuthorFake | None = None, extraction: str = EXTRACTION,
                 book: list[tuple[str, str, str]] | None = None) -> None:
        if book is None:
            self.paths, self.repository = build_figure_vault(root, sketch=sketch, rich=rich)
        else:
            self.paths, self.repository = build_check_vault(root, book)
            if rich:
                RF.configure(self.paths, rich_tiers_enabled=True)
        self.extraction = extraction
        if rich:
            set_config(self.paths, "figures", manim_opt_in="standing")
            RF.ready_manim(monkeypatch)
        self.author = author if author is not None else AuthorFake(answers)
        self.ctx = context(self.paths.root, author=self.author)
        if rich:
            # The rich job is enqueued and left there: its run is the rich job golden's.
            self.ctx.ingest_jobs.bind(self.ctx.repository, self.ctx.vault_root, background=False)
            monkeypatch.setattr(self.ctx.ingest_jobs, "_ensure_worker", lambda: None)
        self.before = table_rows(self.paths.sqlite_path)

    def listed(self) -> dict[str, Any]:
        return call(self.ctx, "reader.figures", {"extractionId": self.extraction})

    def record(self, sandbox: Any, **parts: Any) -> dict[str, Any]:
        listed = self.listed()  # first: a list read may write too (a re-verified sketch's verdict)
        found = {"prompts": list(self.author.prompts), "sandbox": list(sandbox.payloads),
                 "written": written(self.before, table_rows(self.paths.sqlite_path)), "list": listed, **parts}
        return normalized(found, ORDER)


def _pressed(tmp_path, monkeypatch, sandbox, answers, **vault: Any) -> dict[str, Any]:
    press = Press(tmp_path / "vault", monkeypatch, answers, **vault)
    return press.record(sandbox, result=build(press.ctx, dict(PRESS)))


# -- the grammar --------------------------------------------------------------------------------------------------


def case_grammar_accepted(tmp_path, monkeypatch, sandbox):
    return _pressed(tmp_path, monkeypatch, sandbox, [flagship()])


def case_grammar_failed_twice(tmp_path, monkeypatch, sandbox):
    return _pressed(tmp_path, monkeypatch, sandbox, [half_density(), half_density()])


def case_grammar_refused_then_accepted(tmp_path, monkeypatch, sandbox):
    return _pressed(tmp_path, monkeypatch, sandbox, ["{not json", flagship()])


def case_model_failed_twice(tmp_path, monkeypatch, sandbox):
    return _pressed(tmp_path, monkeypatch, sandbox, [RuntimeError("down"), RuntimeError("still down")])


def case_capped_before_the_second_attempt(tmp_path, monkeypatch, sandbox):
    from learnloop.ai.spend import SpendLimitExceeded

    return _pressed(tmp_path, monkeypatch, sandbox, [half_density(), SpendLimitExceeded("the day's figure envelope")])


def case_route_unavailable_for_the_second_attempt(tmp_path, monkeypatch, sandbox):
    from learnloop.figures.routes import FigureUnavailable

    return _pressed(tmp_path, monkeypatch, sandbox,
                    [half_density(), FigureUnavailable("unavailable", "the plan is not answering")])


def case_label_text_repaired(tmp_path, monkeypatch, sandbox):
    return _pressed(tmp_path, monkeypatch, sandbox, [flagship(kind="illustrative", demonstrates=LABEL_LIKE),
                                                     flagship(kind="illustrative")])


def case_label_text_stripped(tmp_path, monkeypatch, sandbox):
    bad = flagship(kind="illustrative", demonstrates=LABEL_LIKE)
    return _pressed(tmp_path, monkeypatch, sandbox, [bad, bad])


def case_prediction_dropped(tmp_path, monkeypatch, sandbox):
    bad = {"prompt": "the bad one", "change": {"nothing_called_this": 1},
           "observe": {"kind": "direction", "expr": "p*lam"}}
    return _pressed(tmp_path, monkeypatch, sandbox, [flagship(kind="illustrative", predictions=[bad])])


def case_unsupported(tmp_path, monkeypatch, sandbox):
    return _pressed(tmp_path, monkeypatch, sandbox, [("unsupported", "a 3-D surface")])


def case_source_check_differs_then_passes(tmp_path, monkeypatch, sandbox):
    from tests.rw5c_fixtures import EXTRACTION as BOOK, FLAGSHIP_EXPR, FLAGSHIP_TEX, HALF_EXPR, PARAMETERS, plot

    sandbox.verdicts[:] = ["different", "equal"]
    stated = {"parameters": PARAMETERS, "low": -3, "high": 3, "stated": "f(x)", "span": "s1"}
    press = Press(tmp_path / "vault", monkeypatch, [plot(HALF_EXPR, **stated), plot(FLAGSHIP_EXPR, **stated)],
                  extraction=BOOK, book=[("s1", "Text", f"The density is $${FLAGSHIP_TEX}$$ for a mixture.")])
    return press.record(sandbox, result=build(press.ctx, {"extractionId": BOOK, "spanIds": ["s1"]}))


# -- the sketch tier ----------------------------------------------------------------------------------------------


def case_sketch_accepted(tmp_path, monkeypatch, sandbox):
    return _pressed(tmp_path, monkeypatch, sandbox, [("sketch", F.walk())], sketch=True)


def case_sketch_fails_in_the_engine(tmp_path, monkeypatch, sandbox):
    wrong = F.planted()[0][1]  # the claim off by a constant
    return _pressed(tmp_path, monkeypatch, sandbox, [("sketch", wrong), ("sketch", wrong)], sketch=True)


def case_sketch_engine_raises_then_accepted(tmp_path, monkeypatch, sandbox):
    real = SV.verify_sketch
    raised = []

    def once(*args: Any, **kwargs: Any) -> Any:
        if not raised:
            raised.append(True)
            raise RuntimeError("the engine stopped")
        return real(*args, **kwargs)

    monkeypatch.setattr(SV, "verify_sketch", once)
    return _pressed(tmp_path, monkeypatch, sandbox, [("sketch", F.walk()), ("sketch", F.walk())], sketch=True)


def case_spec_with_the_sketch_tier_on(tmp_path, monkeypatch, sandbox):
    return _pressed(tmp_path, monkeypatch, sandbox, [flagship()], sketch=True)


class OffMenuStatusAuthor(AuthorFake):
    """A V2 answer (sketch tier on) whose status names no tier, with a spec that stands on its own."""

    def complete(self, request: Any) -> Any:
        assert request.purpose == "figure_author"
        self._record(request)
        return request.result_model.model_validate({
            "status": "drawing", "spec_json": json.dumps(flagship()), "sketch_json": "", "why_not_spec": "",
            "unsupported_kind": "", "unsupported_reason": ""})


def case_sketch_tier_status_off_the_menu(tmp_path, monkeypatch, sandbox):
    press = Press(tmp_path / "vault", monkeypatch, [], sketch=True, author=OffMenuStatusAuthor())
    return press.record(sandbox, result=build(press.ctx, dict(PRESS)))


# -- the rich tier (V3) -------------------------------------------------------------------------------------------


def case_v3_manim_with_a_quick_spec(tmp_path, monkeypatch, sandbox):
    return _pressed(tmp_path, monkeypatch, sandbox,
                    [("rich", "manim", RF.brief(), WHY, flagship(kind="illustrative"))], rich=True)


def case_v3_manim_only(tmp_path, monkeypatch, sandbox):
    return _pressed(tmp_path, monkeypatch, sandbox, [("rich", "manim", RF.brief(), WHY)], rich=True)


def case_v3_quick_spec_dropped(tmp_path, monkeypatch, sandbox):
    return _pressed(tmp_path, monkeypatch, sandbox, [("rich", "manim", RF.brief(), WHY, half_density())], rich=True)


class QuickSketchAuthor(AuthorFake):
    """A V3 answer whose quick figure is a sketch (``AuthorFake``'s rich answer carries a quick spec only)."""

    def __init__(self, program: dict[str, Any] | None = None) -> None:
        super().__init__()
        self.program = program if program is not None else F.walk()

    def complete(self, request: Any) -> Any:
        assert request.purpose == "figure_author"
        self._record(request)
        return request.result_model.model_validate({
            "status": "manim", "why_this_tier": WHY, "spec_json": "", "sketch_json": json.dumps(self.program),
            "rich_json": json.dumps(RF.brief()), "unsupported_kind": "", "unsupported_reason": ""})


def case_v3_quick_sketch(tmp_path, monkeypatch, sandbox):
    press = Press(tmp_path / "vault", monkeypatch, [], sketch=True, rich=True, author=QuickSketchAuthor())
    return press.record(sandbox, result=build(press.ctx, dict(PRESS)))


def case_v3_quick_sketch_fails_in_the_engine(tmp_path, monkeypatch, sandbox):
    author = QuickSketchAuthor(F.planted()[0][1])  # the claim off by a constant: dropped, the video carries on
    press = Press(tmp_path / "vault", monkeypatch, [], sketch=True, rich=True, author=author)
    return press.record(sandbox, result=build(press.ctx, dict(PRESS)))


def case_v3_quick_spec_differs_from_the_book(tmp_path, monkeypatch, sandbox):
    from tests.rw5c_fixtures import EXTRACTION as BOOK, FLAGSHIP_TEX, HALF_EXPR, PARAMETERS, plot

    sandbox.verdicts[:] = ["different"]
    quick = plot(HALF_EXPR, parameters=PARAMETERS, low=-3, high=3, stated="f(x)", span="s1")
    press = Press(tmp_path / "vault", monkeypatch, [("rich", "manim", RF.brief(), WHY, quick)], rich=True,
                  extraction=BOOK, book=[("s1", "Text", f"The density is $${FLAGSHIP_TEX}$$ for a mixture.")])
    return press.record(sandbox, result=build(press.ctx, {"extractionId": BOOK, "spanIds": ["s1"]}))


def case_v3_tier_reason_missing_then_given(tmp_path, monkeypatch, sandbox):
    return _pressed(tmp_path, monkeypatch, sandbox,
                    [("rich", "manim", RF.brief(), " ", flagship(kind="illustrative")),
                     ("rich", "manim", RF.brief(), WHY, flagship(kind="illustrative"))], rich=True)


def case_v3_spec_chosen(tmp_path, monkeypatch, sandbox):
    return _pressed(tmp_path, monkeypatch, sandbox, [flagship()], rich=True)


# -- reuse, revision, delivery ------------------------------------------------------------------------------------


def case_reuse_under_another_setting(tmp_path, monkeypatch, sandbox):
    press = Press(tmp_path / "vault", monkeypatch, [flagship()])
    first = build(press.ctx, dict(PRESS))
    # The same input under the sketch tier's setting (the engine runs now): reused through the reuse key's alternate.
    end_sketch_engine_absence()
    second = build(press.ctx, dict(PRESS))
    return press.record(sandbox, result=first, second=second)


def case_revision(tmp_path, monkeypatch, sandbox):
    press = Press(tmp_path / "vault", monkeypatch, [flagship(), flagship(kind="illustrative")])
    first = build(press.ctx, dict(PRESS))
    revised = build(press.ctx, {"figureId": first["figure"]["figureId"], "note": "show p = 0.7 instead"},
                    rpc="reader.figure_revise")
    return press.record(sandbox, result=first, second=revised)


def case_prediction_missed_and_explained(tmp_path, monkeypatch, sandbox):
    press = Press(tmp_path / "vault", monkeypatch, [flagship()])
    figure = build(press.ctx, dict(PRESS))["figure"]
    found = call(press.ctx, "reader.figure_predict", {"figureId": figure["figureId"], "predictionIndex": 0,
                                                      "answer": "rises"})
    explained = call(press.ctx, "reader.figure_explain", {"predictionId": found["predictionId"],
                                                          "text": "λ squeezes both sides toward 0, but p sets the split"})
    return press.record(sandbox, result=found, second=explained)


def case_delivery_withheld(tmp_path, monkeypatch, sandbox):
    from tests.figures_codex_review_helpers import _hold_out

    press = Press(tmp_path / "vault", monkeypatch, [flagship(kind="illustrative")])
    result = build(press.ctx, dict(PRESS))
    _hold_out(monkeypatch, "p4")  # a neighbour the author was sent is held out after the build
    delivered = FH.deliver_figure(press.ctx, dict(result))
    return press.record(sandbox, result=result, delivered=delivered)


# -- other hosts --------------------------------------------------------------------------------------------------


def case_attempt_host(tmp_path, monkeypatch, sandbox):
    from tests.figures_help_helpers import _call, _host, _show_me, _sidecar
    from tests.hint_fakes import EXPECTED

    author = AuthorFake([flagship(demonstrates=EXPECTED)])
    paths, ctx, session = _sidecar(tmp_path, author=author)
    before = table_rows(paths.sqlite_path)
    job = _show_me(ctx, _host(session))
    opened = _call(ctx, "figure.open", {"figureId": job["result"]["figure"]["figureId"], "hostRef": _host(session)})
    found = {"prompts": list(author.prompts), "sandbox": list(sandbox.payloads),
             "written": written(before, table_rows(paths.sqlite_path)), "result": job["result"], "opened": opened}
    return normalized(found, ORDER)


def case_lesson_visual(tmp_path, monkeypatch, sandbox):
    from learnloop.teacher import service as S
    from tests.reader_rw5d_p4b_teacher_visuals_helpers import _builder, _clients, _spec, visual_turn
    from tests.teacher_fakes import TeacherFake, build_teacher_vault

    paths, repository = build_teacher_vault(tmp_path / "vault")
    before = table_rows(paths.sqlite_path)
    author = AuthorFake([_spec()])
    view = S.open_lesson(load_vault(paths.root), repository, entry="learning_object", learning_object_ids=["lo_eigen"],
                         clients=_clients(TeacherFake([visual_turn]), _builder(paths, repository, author)))
    again = S.view_lesson(load_vault(paths.root), repository, view["lesson_id"])
    found = {"prompts": list(author.prompts), "sandbox": list(sandbox.payloads),
             "written": written(before, table_rows(paths.sqlite_path)),
             "result": [entry for entry in view["feed"] if entry["kind"] == "figure"],
             "lesson": [entry for entry in again["feed"] if entry["kind"] == "figure"]}
    return normalized(found, ORDER)


CASES = {name[len("case_"):]: function for name, function in sorted(globals().items()) if name.startswith("case_")}


@pytest.mark.parametrize("case", sorted(CASES))
def test_the_figure_build_is_as_recorded(case, tmp_path):
    runs = iter(("first", "second"))

    def run(monkeypatch):
        root = tmp_path / next(runs)
        root.mkdir()
        return CASES[case](root, monkeypatch, fixed_sandbox(monkeypatch))

    check_golden(GOLDEN, case, recorded_twice(run), write=WRITE)
