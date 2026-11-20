"""The author loop's rules for one answer, with literal answers (``learnloop.figures.author_answer``).

Each test hands :func:`read_answer` an answer as the model's output contract carries it (V1 with the grammar
alone, V2 with the sketch tier, V3 with a rich tier on the menu) and checks what the loop is told: retry with
which problems and record code, unsupported, or which parsed figure goes on to its checks, with the tier verdict
and the codes noted beside it. No vault, model, gate or engine: the whole build is pinned by the figure goldens.
"""

from __future__ import annotations

import json
from typing import Any

from learnloop.figures import author_answer as AA
from learnloop.figures import labels as L
from learnloop.figures import records as FR
from learnloop.figures import routes as R
from tests import figure_panels_corpus as PC
from tests import rich_fixtures as RF
from tests import sketch_fixtures as F
from tests.figure_fixtures import flagship

WHY = "a narrated video shows the spiral tighten as b grows"
MENU = ("grammar", "sketch", "manim")
LABEL_LIKE = "✓ checked against the book: the left mass is p"


def v1(spec: Any = None, **fields: Any) -> R.FigureAuthorOutputV1:
    found = {"status": "spec", "spec_json": _text(spec), "unsupported_kind": "", "unsupported_reason": "", **fields}
    return R.FigureAuthorOutputV1.model_validate(found)


def v2(status: str = "spec", **fields: Any) -> R.FigureAuthorOutputV2:
    found = {"status": status, "spec_json": "", "sketch_json": "", "why_not_spec": "", "unsupported_kind": "",
             "unsupported_reason": "", **fields}
    return R.FigureAuthorOutputV2.model_validate(found)


def v3(status: str = "manim", **fields: Any) -> R.FigureAuthorOutputV3:
    found = {"status": status, "why_this_tier": WHY, "spec_json": "", "sketch_json": "",
             "rich_json": json.dumps(RF.brief()) if status == "manim" else "", "unsupported_kind": "",
             "unsupported_reason": "", **fields}
    return R.FigureAuthorOutputV3.model_validate(found)


def _text(value: Any) -> str:
    return "" if value is None else value if isinstance(value, str) else json.dumps(value)


def read(output: Any, *, last: bool = False, tiers: Any = None, sketch: bool = False, grounded: bool = True,
         advanced: bool = True) -> AA.Reading:
    return AA.read_answer(output, last=last, tiers=tiers, sketch=sketch, grounded=grounded, advanced=advanced)


# -- the grammar alone (V1) --------------------------------------------------------------------------------------


def test_a_spec_that_parses_goes_on_to_its_checks_with_no_tier_verdict():
    reading = read(v1(flagship()))
    assert isinstance(reading.then, AA.Spec) and reading.then.dropped == []
    assert (reading.status, reading.verdict, reading.notes) == ("spec", None, ())
    assert reading.then.figure.spec.demonstrates == flagship()["demonstrates"]


def test_a_spec_that_does_not_parse_is_retried_with_the_parsers_problems():
    reading = read(v1("{not json"))
    assert isinstance(reading.then, AA.Retry)
    assert (reading.then.rule, reading.then.counted, reading.then.parsed) == (FR.SPEC_INVALID, True, "spec")
    assert reading.then.problems[0].startswith("not JSON")


def test_a_bad_prediction_is_dropped_and_the_spec_kept():
    bad = {"prompt": "the bad one", "change": {"nothing_called_this": 1},
           "observe": {"kind": "direction", "expr": "p*lam"}}
    reading = read(v1(flagship(predictions=[bad])))
    assert isinstance(reading.then, AA.Spec) and reading.then.figure.spec.predictions == []
    (note,) = reading.then.dropped
    assert note.startswith("the bad one: prediction 1:") and "nothing_called_this" in note


def test_with_the_panels_off_an_advanced_panel_is_a_parse_problem():
    reading = read(v1(PC.gradient_field()), advanced=False)
    assert isinstance(reading.then, AA.Retry) and reading.then.rule == FR.SPEC_INVALID
    assert "switched off (figures.advanced_panels_enabled)" in reading.then.problems[0]
    assert isinstance(read(v1(PC.gradient_field())).then, AA.Spec)


def test_with_nothing_from_the_books_the_spec_quotes_nothing_and_is_an_illustration():
    reading = read(v1(flagship(kind="reconstructed")), grounded=False)
    spec = reading.then.figure.spec
    assert spec.kind == "illustrative" and spec.source_claims == []
    assert all(assumption.quote is None for assumption in spec.assumptions)


def test_unsupported_names_what_it_would_take_and_why():
    reading = read(v1(status=" Unsupported ", unsupported_kind="  a 3-D\nsurface ", unsupported_reason="no 3-D"))
    assert reading.then == AA.Unsupported("a 3-D surface", "no 3-D") and reading.status == "unsupported"
    assert read(v1(status="unsupported")).then == AA.Unsupported("something else", "")


def test_label_like_text_is_retried_in_codes_words_then_stripped_on_the_last_attempt():
    answer = v1(flagship(kind="illustrative", demonstrates=LABEL_LIKE))
    first = read(answer)
    assert isinstance(first.then, AA.Retry) and (first.then.rule, first.then.counted) == (FR.LABEL_TEXT, True)
    assert first.then.problems[0].startswith("spec_json.demonstrates reads like one of LearnLoop's check labels")
    assert first.verdict is None and first.notes == ()
    last = read(answer, last=True)
    assert isinstance(last.then, AA.Spec) and last.notes == (FR.LABEL_TEXT_STRIPPED,)
    assert last.then.figure.spec.demonstrates == ""


# -- the sketch tier on (V2) -------------------------------------------------------------------------------------


def test_a_sketch_that_parses_goes_to_the_engine_with_its_tier_verdict():
    reading = read(v2("sketch", sketch_json=json.dumps(F.walk()), why_not_spec=" the grammar has\nno random walk "),
                   sketch=True)
    assert isinstance(reading.then, AA.Sketch) and reading.then.dropped == []
    assert reading.verdict == ("sketch", "the grammar has no random walk")


def test_a_sketch_that_does_not_parse_is_retried_and_ends_an_earlier_figure():
    reading = read(v2("sketch", sketch_json="{not json"), sketch=True)
    assert isinstance(reading.then, AA.Retry)
    assert (reading.then.rule, reading.then.parsed) == (FR.SKETCH_INVALID, "sketch")
    assert "not JSON" in reading.then.problems[0] and reading.verdict == ("sketch", "")


def test_a_v2_spec_is_judged_spec_and_a_status_outside_the_three_is_noted_and_read_as_a_spec():
    spec = read(v2("spec", spec_json=json.dumps(flagship())), sketch=True)
    assert spec.verdict == ("spec", "") and isinstance(spec.then, AA.Spec) and spec.notes == ()
    drawing = read(v2("drawing", spec_json=json.dumps(flagship())), sketch=True)
    assert drawing.verdict == ("invalid", "") and drawing.notes == (FR.STATUS_INVALID,)
    assert isinstance(drawing.then, AA.Spec)


def test_a_v2_unsupported_is_judged_with_its_reason():
    reading = read(v2("unsupported", unsupported_kind="a 3-D surface", unsupported_reason="no 3-D"), sketch=True)
    assert reading.verdict == ("unsupported", "no 3-D") and reading.then == AA.Unsupported("a 3-D surface", "no 3-D")


def test_a_label_like_tier_reason_is_retried_then_kept_out_of_the_verdict():
    answer = v2("sketch", sketch_json=json.dumps(F.walk()), why_not_spec="✓ checked: a random process needs it")
    first = read(answer, sketch=True)
    assert isinstance(first.then, AA.Retry) and first.then.problems[0].startswith("why_not_spec reads like")
    last = read(answer, sketch=True, last=True)
    assert last.verdict == ("sketch", L.REASON_WITHHELD) and isinstance(last.then, AA.Sketch)


def test_with_the_sketch_tier_off_a_sketch_status_is_read_as_a_spec():
    reading = read(v1(flagship(), status="sketch"))
    assert isinstance(reading.then, AA.Spec) and reading.verdict is None


# -- a rich tier on the menu (V3) --------------------------------------------------------------------------------


def test_a_status_off_the_menu_is_retried_uncounted_with_the_media_offered():
    reading = read(v3("animation"), tiers=MENU, sketch=True)
    assert isinstance(reading.then, AA.Retry)
    assert (reading.then.rule, reading.then.counted) == (FR.STATUS_INVALID, False)
    assert reading.then.problems == ["status 'animation' is not one of the media offered "
                                     "(['manim', 'sketch', 'spec', 'unsupported'])"]
    assert reading.verdict == ("invalid", WHY)
    without_sketch = read(v3("sketch", sketch_json=json.dumps(F.walk())), tiers=("grammar", "manim"))
    assert isinstance(without_sketch.then, AA.Retry) and without_sketch.then.rule == FR.STATUS_INVALID


def test_a_status_no_menu_offers_has_its_rich_text_left_unread():
    """No tier but ``manim`` is rich: a JavaScript animation status is off the menu, and its brief is never read."""

    labelled = json.dumps(RF.brief(tier="js_animation", demonstrates=LABEL_LIKE))
    reading = read(v3("js_animation", rich_json=labelled), tiers=MENU, sketch=True)
    assert isinstance(reading.then, AA.Retry) and reading.then.rule == FR.STATUS_INVALID


def test_an_empty_tier_reason_is_retried_uncounted():
    reading = read(v3(why_this_tier="  "), tiers=MENU)
    assert isinstance(reading.then, AA.Retry)
    assert (reading.then.rule, reading.then.counted) == (FR.TIER_REASON_MISSING, False)
    assert reading.then.problems[0].startswith("why_this_tier is empty") and reading.verdict == ("manim", "")


def test_a_brief_that_does_not_parse_is_retried_with_its_problems():
    reading = read(v3(rich_json=json.dumps(RF.brief(brief=""))), tiers=MENU)
    assert isinstance(reading.then, AA.Retry) and reading.then.rule == FR.BRIEF_INVALID
    assert reading.then.problems[0].startswith("rich.brief is empty") and reading.then.parsed is None
    assert read(v3(rich_json="{not json"), tiers=MENU).then.problems == ["rich_json is not a JSON object"]


def test_a_rich_answer_carries_its_brief_and_its_quick_figure():
    only = read(v3(), tiers=MENU, sketch=True)
    assert isinstance(only.then, AA.Rich) and (only.then.quick, only.then.dropped) == (None, None)
    assert only.then.brief.brief == RF.brief()["brief"] and only.verdict == ("manim", WHY)
    spec = read(v3(spec_json=json.dumps(flagship(kind="illustrative"))), tiers=MENU, sketch=True)
    assert isinstance(spec.then.quick, AA.Spec) and spec.then.dropped is None
    sketch = read(v3(sketch_json=json.dumps(F.walk())), tiers=MENU, sketch=True)
    assert isinstance(sketch.then.quick, AA.Sketch)
    # A quick sketch with the sketch tier off is not read.
    assert read(v3(sketch_json=json.dumps(F.walk())), tiers=("grammar", "manim")).then.quick is None


def test_a_quick_figure_that_does_not_parse_is_dropped_and_the_brief_stands():
    spec = read(v3(spec_json="{not json"), tiers=MENU, sketch=True)
    assert isinstance(spec.then, AA.Rich) and spec.then.quick is None and spec.then.dropped.startswith("not JSON")
    sketch = read(v3(sketch_json="{not json"), tiers=MENU, sketch=True)
    assert isinstance(sketch.then, AA.Rich) and sketch.then.quick is None and "not JSON" in sketch.then.dropped


def test_a_v3_unsupported_and_a_v3_spec_are_judged_on_the_menu():
    unsupported = read(v3("unsupported", why_this_tier="", rich_json="", unsupported_kind="a 3-D surface",
                          unsupported_reason="no 3-D"), tiers=MENU)
    assert unsupported.then == AA.Unsupported("a 3-D surface", "no 3-D")
    assert unsupported.verdict == ("unsupported", "no 3-D")
    spec = read(v3("spec", rich_json="", spec_json=json.dumps(flagship())), tiers=MENU)
    assert isinstance(spec.then, AA.Spec) and spec.verdict == ("spec", WHY)


def test_a_rich_answer_still_label_like_on_the_last_attempt_keeps_its_brief_without_that_text():
    answer = v3(rich_json=json.dumps(RF.brief(demonstrates="the spiral · checked by LearnLoop")),
                why_this_tier="LearnLoop verified this needs motion")
    first = read(answer, tiers=MENU)
    assert isinstance(first.then, AA.Retry) and first.then.rule == FR.LABEL_TEXT and first.verdict is None
    assert any(problem.startswith("rich_json.demonstrates reads like") for problem in first.then.problems)
    last = read(answer, tiers=MENU, last=True)
    assert isinstance(last.then, AA.Rich) and last.then.brief.demonstrates == ""
    assert last.verdict == ("manim", L.REASON_WITHHELD) and last.notes == (FR.LABEL_TEXT_STRIPPED,)
