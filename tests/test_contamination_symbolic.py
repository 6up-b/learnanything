"""Slice 2 T4: the symbolic answer check behind the reveal detectors (R2)."""
from __future__ import annotations

import pytest

from learnloop.ops.contamination.symbolic import (
    distinctive, math_answer, math_runs, normalize_math, symbolic_check,
)


@pytest.mark.parametrize(("answer", "expected", "is_distinctive"), [
    (r"So the probability is $\frac{2}{3}$.", "2/3", True),
    ("Rounded, that is 0.667 overall.", "2/3", True),
    ("We get x^2 + 2x + 1 after expanding.", "(x+1)^2", True),
    (r"The length is \sqrt{2} units.", "sqrt(2)", True),
    ("Hence p = 3/4", {"final_answer": "3/4"}, True),
    ("x = 144", "144", True),
    # A one-decimal rounding or a small integer also appears in innocent
    # explanations; distinctiveness is reported, never a decision by itself.
    ("About 0.7 of the mass.", "2/3", False),
    ("Step 2 is the key.", "2", False),
])
def test_equivalent_forms_match(answer, expected, is_distinctive):
    result = symbolic_check(answer, expected)
    assert result.status == "match", result
    assert result.distinctive is is_distinctive
    # No item prompt, no established link: an occurrence alone never decides.
    assert result.decides is False


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


# --- Codex review fixes ------------------------------------------------------


@pytest.mark.parametrize(("answer", "expected", "prompt"), [
    # F2: an occurrence of the answer's value with no established link to it.
    ("Read page 144 for the method.", "144", "Compute 12 * 12."),
    ("In an unrelated example, 1/2 + 1/6 = 2/3.", "2/3", "Two of three balls are red. P(red)?"),
    ("It's not x = 144; recheck the carry.", "144", "Compute 12 * 12."),
    # A restatement: equal to the answer, but not the answer's own form.
    ("Start from (x+1)^2 = (x+1)(x+1).", "x^2 + 2x + 1", "Expand (x+1)^2."),
    # Equal values in another computation are not the item's expression.
    ("Compare 6 * 24 = 144.", "144", "Compute 12 * 12."),
    # The prompt already states its answer: restating it reveals nothing.
    ("Indeed 1/2 + 1/2 = 1.", "1", "Show that 1/2 + 1/2 = 1."),
])
def test_an_occurrence_without_a_link_to_the_item_shortlists_but_never_decides(answer, expected, prompt):
    result = symbolic_check(answer, expected, prompt=prompt)
    assert result.status == "match", result
    assert result.linked is False and result.decides is False


@pytest.mark.parametrize(("answer", "expected", "prompt"), [
    (r"Just multiply: $12 \times 12 = 144$.", "144", "Compute 12 * 12."),
    (r"Add them: 1/3 + 1/3 = \frac{2}{3}.", "2/3", r"Compute $\frac{1}{3} + \frac{1}{3}$."),
    ("Here 3/4 + 1/6 = 9/12 + 2/12 = 11/12 exactly.", "11/12", "Compute 3/4 + 1/6."),
    ("So 2 + 2 = 4.", "4", "What is 2 + 2?"),
    ("Note sin(pi/2 - x) = cos(x) here.", "cos(x)", "Simplify sin(pi/2 - x)."),
    ("Expanding, (x+1)^2 = x^2 + 2x + 1.", "x^2 + 2x + 1", "Expand (x + 1)^2."),
    ("Roughly 1/3 + 1/3 = 0.667.", "2/3", "Compute 1/3 + 1/3."),
])
def test_working_the_items_own_expression_to_its_answer_decides(answer, expected, prompt):
    result = symbolic_check(answer, expected, prompt=prompt)
    assert result.status == "match" and result.linked and result.decides, result
    assert result.as_dict()["link"]


@pytest.mark.parametrize(("answer", "expected"), [
    # F5: function applications are math without digits or operators.
    ("The answer is sin(x).", "sin(x)"),
    ("So we get cos(x) in the end.", "sin(x + pi/2)"),
    (r"It reduces to $\sqrt{x}$.", "sqrt(x)"),
    ("Take exp(t) as the solution.", "exp(t)"),
])
def test_function_answers_without_numerals_are_checked(answer, expected):
    assert math_answer(expected) is not None
    result = symbolic_check(answer, expected)
    assert result.status == "match", result
    assert result.checked >= 1


def test_function_runs_are_candidates():
    assert math_runs("We get cos(x) here, or log(y).") == ["cos(x)", "log(y)"]
    assert symbolic_check("Then cos(x) follows.", "tan(x)").status == "no_match"


# --- Codex re-review fixes ---------------------------------------------------


@pytest.mark.parametrize(("answer", "expected", "prompt"), [
    # F8: a different equation shares a fragment with the item. ``x + 1`` is
    # the item's expression, but it is not equal to the answer, so ``x + 1 = 2``
    # works some other equation, not this item.
    ("For comparison, x + 1 = 2 would give x = 1. Now solve your own equation.", "2", "Solve x + 1 = 3"),
    ("If it were 2*x + 4 = 3 instead, you would get a fraction.", "3", "Solve 2*x + 4 = 10."),
    ("Suppose x^2 - 4 = 2; that is a different problem.", "2", "Find the positive root of x^2 - 4 = 0."),
    # A wrong relation that holds the item's expression is not a verified one.
    ("A common slip is 12 * 12 = 124, not 144.", "144", "Compute 12 * 12."),
])
def test_a_relation_that_does_not_hold_for_the_item_never_decides(answer, expected, prompt):
    result = symbolic_check(answer, expected, prompt=prompt)
    assert result.status == "match", result
    assert result.linked is False and result.decides is False


@pytest.mark.parametrize(("answer", "expected", "prompt"), [
    # F9: an earlier occurrence of the answer must not hide the worked equation.
    ("Read page 144. Then 12 * 12 = 144.", "144", "Compute 12 * 12."),
    ("Not 2/3 yet. Add them: 1/3 + 1/3 = 2/3.", "2/3", "Compute 1/3 + 1/3."),
    # The item's expression seen earlier, alone, still links in the later equation.
    ("Look at 12 * 12 first. Indeed 12 * 12 = 144.", "144", "Compute 12 * 12."),
])
def test_an_earlier_occurrence_does_not_hide_a_later_worked_equation(answer, expected, prompt):
    result = symbolic_check(answer, expected, prompt=prompt)
    assert result.status == "match" and result.linked and result.decides, result


def test_repeated_sides_are_compared_once(monkeypatch):
    from learnloop.ops.contamination import symbolic

    calls = []
    original = symbolic._equal
    monkeypatch.setattr(symbolic, "_equal", lambda side, target: calls.append(side) or original(side, target))
    result = symbolic_check("Read page 144. Then 12 * 12 = 144, and 144 again.", "144", prompt="Compute 12 * 12.")
    assert result.decides
    assert sorted(calls) == ["12 * 12", "144"] and result.checked == 2
