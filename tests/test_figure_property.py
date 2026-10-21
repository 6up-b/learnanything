"""The figure grammar's differential property test (reader workbench RW5a, fix round 3).

This is the parity contract from fix round 3 on (``tests/figure_property_corpus.py``):

* the corpus file is exactly what the seeded generator builds (so the
  Python evaluator's verdicts and values in it are today's);
* no value either evaluator shows is -0;
* SymPy's reading (``grammar.to_sympy``) of every accepted expression the
  source match may check (``grammar.sympy_problem`` is None) has the
  evaluator's value wherever that value is finite;
* ``figureGrammar.test.ts`` holds the TypeScript evaluator to the same file.

Two kinds of disagreement are not semantic and are set aside, each by a
measured rule, never by case id:

* a comparison or a sum bound the evaluator's rounding decides (its operands
  within 1e-9 relative of each other, a bound within 1e-9 of an integer
  boundary), a cancellation (a sum or difference 1e-6 smaller than its
  operands), and an infinite or NaN subexpression of a finite value (IEEE's
  1/0, which SymPy has as zoo), where exact and floating-point arithmetic
  part by design, on sets of measure zero;
* the book's decimals: ``to_sympy`` writes ``0.1`` as the exact decimal
  1/10 for the check against the book, so this test reads each literal as
  the double the evaluator uses (``Rational(<the double's exact value>)``).
"""

from __future__ import annotations

import json
import math
import re
from fractions import Fraction

import pytest

from learnloop.figures import grammar as G
from tests import figure_property_corpus as FP

CORPUS = json.loads(FP.CORPUS_PATH.read_text(encoding="utf-8"))
CASES = CORPUS["cases"]


def _decode(value):
    if isinstance(value, str):
        return {"nan": math.nan, "inf": math.inf, "-inf": -math.inf}[value]
    return value


def test_the_property_corpus_is_the_generator_output():
    assert FP.CORPUS_PATH.read_text(encoding="utf-8") == FP.render()


def test_the_corpus_covers_its_families():
    ids = [case["id"] for case in CASES]
    assert len(ids) == len(set(ids)) and sum(1 for case_id in ids if case_id.startswith("random_")) == FP.RANDOM_CASES
    for family in ("signed_zero", "sum_range", "reserved", "comparison", "magnitude"):
        assert any(case_id.startswith(family) for case_id in ids), family
    # Every reserved-looking identifier is refused, in both parsers.
    assert all(not case["accepted"] for case in CASES
               if case["id"].startswith("reserved") and case["expr"] not in ("x2 + 1",))
    accepted = [case for case in CASES if case["accepted"]]
    assert len(accepted) > 2500
    assert any(case["expected"] == "nan" for case in accepted)
    assert sum(1 for case in accepted if "sum(" in case["expr"]) > 200
    assert sum(1 for case in accepted if "piecewise(" in case["expr"]) > 300


def test_no_value_is_negative_zero():
    for case in CASES:
        if case["accepted"] and isinstance(case["expected"], float) and case["expected"] == 0:
            assert math.copysign(1.0, case["expected"]) > 0, case


# ---------------------------------------------------------------------------
# SymPy's reading equals the evaluator's value
# ---------------------------------------------------------------------------

class _Boundaries:
    """Where the evaluator's rounding decides: comparisons whose operands are
    within 1e-9 relative, sum bounds within 1e-9 of an integer boundary."""

    def __init__(self, monkeypatch):
        self.touched = False
        truth, exact_sum = G._truth, G.exact_sum

        def watched_truth(node, env, definitions):
            if node.kind == "cmp":
                left = G.evaluate(node.args[0], env, definitions)
                right = G.evaluate(node.args[1], env, definitions)
                if not (math.isfinite(left) and math.isfinite(right)) or \
                        abs(left - right) <= 1e-9 * max(1.0, abs(left), abs(right)):
                    self.touched = True
            return truth(node, env, definitions)

        def watched_sum(function, a, b):
            for bound in (a - 1e-9, b + 1e-9):
                if math.isfinite(bound) and abs(bound - round(bound)) <= 1e-9 * max(1.0, abs(bound)):
                    self.touched = True
            return exact_sum(function, a, b)

        monkeypatch.setattr(G, "_truth", watched_truth)
        monkeypatch.setattr(G, "exact_sum", watched_sum)


def _outside(node):
    """Every subexpression that reads no bound variable: a sum's or an
    integral's bounds, not its body; a condition's operands, not the condition."""

    if node.kind not in ("cmp", "and", "or"):
        yield node
    if node.kind in ("integral", "sum"):
        yield from _outside(node.args[1])
        yield from _outside(node.args[2])
        return
    for child in node.args:
        yield from _outside(child)


def _non_finite_inside(node, env) -> bool:
    """A subexpression is infinite or NaN although the value is finite (1/0
    inside a comparison, atan(1/0)): IEEE's infinities, which SymPy's exact
    arithmetic has as zoo and nan."""

    return any(not math.isfinite(G.evaluate(sub, env)) for sub in _outside(node))


def _cancels(node, env) -> bool:
    for sub in _outside(node):
        if sub.kind == "bin" and sub.op in "+-":
            a, b = G.evaluate(sub.args[0], env), G.evaluate(sub.args[1], env)
            value = G.evaluate(sub, env)
            if all(math.isfinite(v) for v in (a, b, value)) and max(abs(a), abs(b)) > 0 \
                    and abs(value) <= 1e-6 * max(abs(a), abs(b)):
                return True
    return False


def _exact_text(value: float) -> str:
    """A double exactly: an integer as an Integer (so 0^0 is 1, as in IEEE),
    anything else as a 60-digit Float holding its exact binary value."""

    fraction = Fraction(value)
    if fraction.denominator == 1 and abs(fraction.numerator) < 10 ** 20:
        return str(fraction.numerator)
    return f"Float(Rational({fraction.numerator}, {fraction.denominator}), 60)"


_RATIONAL = re.compile(r"Rational\('([^']+)'\)")


def _as_doubles(text: str) -> str:
    def exact(match: re.Match) -> str:
        return _exact_text(float(match.group(1)))

    return _RATIONAL.sub(exact, text)


def _sympy_value(node, env):
    import sympy

    symbols = {name: sympy.Symbol(name, real=True) for name in (*FP.KNOWN, *FP.BOUND)}
    expression = sympy.sympify(_as_doubles(G.to_sympy(node, {})), locals=symbols)
    # Each double exactly, at 60 digits (200 bits): SymPy evaluates in high
    # precision rather than exactly, so a huge power or a sine of 1e300 stays fast.
    values = {symbols[name]: sympy.sympify(_exact_text(value)) for name, value in env.items()}
    result = sympy.N(expression.subs(values), 30)
    if not result.is_number or not result.is_real:
        return None
    return float(result)


def _translatable() -> list[dict]:
    # A grammar with no sympy_problem (before fix round 3) claims to translate everything.
    problem = getattr(G, "sympy_problem", lambda _node, _definitions: None)
    chosen = []
    for case in CASES:
        if not case["accepted"] or not isinstance(case["expected"], float) or not math.isfinite(case["expected"]):
            continue
        node = G.parse(case["expr"])
        if problem(node, {}) is None:
            chosen.append(case)
    return chosen


def test_sympy_reads_every_translatable_case_as_the_evaluator_does(monkeypatch):
    boundaries = _Boundaries(monkeypatch)
    checked, set_aside, mismatches = 0, 0, []
    for case in _translatable():
        node = G.parse(case["expr"])
        env = case["env"]
        boundaries.touched = False
        value = G.evaluate(node, env)
        if boundaries.touched or _cancels(node, env) or _non_finite_inside(node, env):
            set_aside += 1
            continue
        try:
            reference = _sympy_value(node, env)
        except (TypeError, ValueError, ZeroDivisionError) as exc:
            reference = f"{type(exc).__name__}: {exc}"[:120]
        tolerance = (FP.INTEGRAL if case["integral"] else FP.RELATIVE) * max(1.0, abs(value), case["scale"])
        if not isinstance(reference, float) or not abs(reference - value) <= tolerance:
            mismatches.append((case["id"], case["expr"], value, reference))
        checked += 1
    assert not mismatches, mismatches[:10]
    assert checked > 1500, (checked, set_aside)


@pytest.mark.parametrize("expr, value", [("sum(1, k, 2, 0)", 0.0), ("sum(1, k, 0.5, 2.5)", 2.0),
                                         ("sum(k, k, -0.5, 0.5)", 0.0), ("sum(k^2, k, -2.5, -0.5)", 5.0)])
def test_the_sum_rule_is_one_rule(expr, value):
    import sympy

    node = G.parse(expr)
    assert G.evaluate(node, {}) == value
    assert float(sympy.N(sympy.sympify(G.to_sympy(node, {})).doit())) == value


@pytest.mark.parametrize("expr", ["piecewise((x == 0, 1), 2)", "piecewise((x != 1, 1), 2)", "floor(x)*2"])
def test_equality_and_floor_are_not_source_verifiable(expr):
    assert G.sympy_problem(G.parse(expr), {}) is not None
