"""Slice 2 T4: the symbolic answer check behind the reveal detectors (R2)."""
from __future__ import annotations

import pytest

from learnloop.ops.contamination.symbolic import (
    distinctive, math_answer, math_runs, normalize_math, symbolic_check,
)


@pytest.mark.parametrize(("answer", "expected", "decides"), [
    (r"So the probability is $\frac{2}{3}$.", "2/3", True),
    ("Rounded, that is 0.667 overall.", "2/3", True),
    ("We get x^2 + 2x + 1 after expanding.", "(x+1)^2", True),
    (r"The length is \sqrt{2} units.", "sqrt(2)", True),
    ("Hence p = 3/4", {"final_answer": "3/4"}, True),
    ("x = 144", "144", True),
    # A one-decimal rounding or a small integer also appears in innocent
    # explanations: it shortlists the pair but never decides.
    ("About 0.7 of the mass.", "2/3", False),
    ("Step 2 is the key.", "2", False),
])
def test_equivalent_forms_match(answer, expected, decides):
    result = symbolic_check(answer, expected)
    assert result.status == "match", result
    assert result.decides is decides


def test_different_values_and_prose_answers_do_not_match():
    assert symbolic_check("The answer is 3/5.", "2/3").status == "no_match"
    assert symbolic_check("Use the spectral theorem.", "2/3").status == "no_match"
    assert symbolic_check("anything at all", "A matrix factorization into U, Sigma and V^T.").status == "not_math"
    assert symbolic_check("anything", {"steps": ["a", "b"]}).status == "not_math"
    assert symbolic_check("anything", None).status == "not_math"


def test_unsafe_text_never_reaches_sympy(monkeypatch):
    import sympy

    calls = []
    original = sympy.sympify
    monkeypatch.setattr(sympy, "sympify", lambda *a, **k: calls.append(a) or original(*a, **k))
    hostile = "__import__('os').system('echo pwned') = 2/3 and (lambda: 1)()"
    assert math_answer("__import__('os').system('x')") is None
    result = symbolic_check(hostile, "2/3")
    # The arithmetic run "2/3" still matches exactly, without SymPy; nothing
    # with a dunder, quote or attribute access is ever handed to the parser.
    assert result.status == "match" and result.matched == "2/3"
    assert all("__" not in str(arg) and "'" not in str(arg) for call in calls for arg in call)


def test_runs_split_on_prose_and_equals_and_normalize_latex():
    assert normalize_math(r"\frac{1}{\frac{2}{3}} \cdot x^{2}").split() == ["(1)/((2)/(3))", "*", "x^(2)"]
    assert math_runs("Let x = 2/3, so y equals 4.5 here.") == ["2/3", "4.5"]
    assert math_runs("- 7 is listed") == ["7"]


@pytest.mark.parametrize(("text", "expected"), [
    ("2/3", True), ("0.667", True), ("144", True), ("x^2+1", True), ("sqrt(2)", True),
    ("0.7", False), ("17", False), ("x", False), ("007", False),
])
def test_distinctiveness(text, expected):
    assert distinctive(text) is expected
