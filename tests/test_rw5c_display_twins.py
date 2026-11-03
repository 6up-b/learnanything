"""Reader RW5c (G22's extension): the formatValue and lossless-bound twins, and the derived bounds,
pinned against JavaScript's own answers (``figureDisplayCorpus.json``; the vitest twin reads the same file)."""

from __future__ import annotations

import json
from fractions import Fraction
from pathlib import Path

import pytest

from learnloop.figures import book_math as B
from learnloop.figures import elements as E
from learnloop.figures import spec as S
from learnloop.figures.display_format import format_value, js_string

CORPUS = json.loads((Path(__file__).resolve().parents[1] / "apps" / "learnloop-tauri" / "src" / "screens" / "reader"
                     / "figures" / "figureDisplayCorpus.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize("case", CORPUS["values"], ids=lambda case: str(case["value"]))
def test_the_twins_agree_with_javascript(case):
    value = float(case["value"])
    assert format_value(value) == case["number"]
    assert format_value(value, "percent") == case["percent"]
    assert js_string(value) == case["string"]
    assert format_value(Fraction(value)) == case["number"]


def test_no_value_is_a_dash():
    assert format_value(None) == "—" and format_value(float("nan")) == "—" and format_value(float("inf"), "percent") == "—"
    assert format_value(1e307, "percent") == "—"


@pytest.mark.parametrize("case", CORPUS["bounds"], ids=lambda case: case["name"])
def test_the_derived_bounds_pin_the_evaluator(case):
    compiled = S.parse_spec(case["spec"])
    env = {**compiled.defaults, **case.get("params", {})}
    found = S.derived_bounds(compiled, case["panel"], case["kind"], case["index"], env)
    assert found == case["expected"]


@pytest.mark.parametrize("case", CORPUS["templates"], ids=lambda case: f"{case['kind']}-{case['lhs']}")
def test_the_derived_words_are_the_corpus_s_from_the_book_s_left_hand_side(case):
    """The reader decides what is compound, from KaTeX's tree; the Reader's derivedWords writes the same words (vitest)."""

    relation = B.read_relation(case["lhs"] + "=x")
    assert relation.lhs_compound is case["compound"]
    label = E.BookLabel(relation.lhs, relation.latex, "k", {}, "e", "s", 1, relation.lhs_compound)
    assert label.operand == (case["body_tex"], case["body_plain"])
    template = {"kind": case["kind"], "body_tex": case["body_tex"], "body_plain": case["body_plain"], "variable": "k"}
    assert E.template_words(template, case["bounds"], js_string) == (case["tex"], case["plain"])
