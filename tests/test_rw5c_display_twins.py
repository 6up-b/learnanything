"""Reader RW5c (G22's extension): the formatValue and lossless-bound twins, and the derived bounds,
pinned against JavaScript's own answers (``figureDisplayCorpus.json``; the vitest twin reads the same file)."""

from __future__ import annotations

import json
from fractions import Fraction
from pathlib import Path

import pytest

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
