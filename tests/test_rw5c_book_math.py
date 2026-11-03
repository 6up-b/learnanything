"""Reader RW5c: code reads the book's equation through a closed table (spec §5.3)."""

from __future__ import annotations

import random

import pytest

from learnloop.figures import book_math as B
from learnloop.figures import grammar as G


def rhs(latex: str) -> G.Node:
    return B.read_relation(latex).rhs


def same(latex: str, grammar: str) -> None:
    """The book's right-hand side is the grammar tree of ``grammar``, node for node (literals by their exact text)."""

    def shape(node: G.Node):
        return (node.kind, node.text, node.op, tuple(shape(child) for child in node.args))

    assert shape(rhs(latex)) == shape(G.parse(grammar)), latex


@pytest.mark.parametrize("latex, grammar", [
    (r"y = 2", "2"),
    (r"y = 0.5", "0.5"),
    (r"y = x", "x"),
    (r"y = \lambda", "lambda"),
    (r"y = \mu_1", "mu1"),
    (r"y = x_{0}", "x0"),
    (r"y = a + b - c", "a + b - c"),
    (r"y = -a", "-a"),
    (r"y = a \cdot b", "a*b"),
    (r"y = a \times b", "a*b"),
    (r"y = a b", "a*b"),
    (r"y = 2x", "2*x"),
    (r"y = \frac{a}{b}", "a/b"),
    (r"y = a/b", "a/b"),
    (r"y = a^{b}", "a^b"),
    (r"y = a^b", "a^b"),
    (r"y = a^2", "a^2"),
    (r"y = a^{1+1}", "a^(1+1)"),
    (r"y = e^{x}", "exp(x)"),
    (r"y = e^x", "exp(x)"),
    (r"y = \mathrm{e}^{x}", "exp(x)"),
    (r"y = \mathrm{e}", "e"),
    (r"y = \exp(x)", "exp(x)"),
    (r"y = \exp\left(x\right)", "exp(x)"),
    (r"y = \sqrt{x}", "sqrt(x)"),
    (r"y = \ln(x)", "log(x)"),
    (r"y = \sin(x)", "sin(x)"),
    (r"y = \cos(x)", "cos(x)"),
    (r"y = \tan(x)", "tan(x)"),
    (r"y = \arctan(x)", "atan(x)"),
    (r"y = \operatorname{erf}(x)", "erf(x)"),
    (r"y = \mathrm{erf}(x)", "erf(x)"),
    (r"y = \lvert x\rvert", "abs(x)"),
    (r"y = \left| x \right|", "abs(x)"),
    (r"y = |x|", "abs(x)"),
    (r"y = \min(a, b)", "min(a, b)"),
    (r"y = \max\{a, b\}", "max(a, b)"),
    (r"y = \pi", "pi"),
    (r"y = (a + b)[c] \{d\}", "(a + b)*c*d"),
    (r"y = \left(a\right)\, b \; c \! \quad d", "a*b*c*d"),
    (r"y = \sin x \cos x", "sin(x)*cos(x)"),
    (r"y = \lambda (1-p) + \lambda", "lambda*(1-p) + lambda"),
    (r"f(x) = x(1-x)", "x*(1-x)"),
    (r"y := x", "x"),
    (r"y = x,", "x"),
    (r"y = x.", "x"),
])
def test_each_row_translates_exactly(latex, grammar):
    same(latex, grammar)


@pytest.mark.parametrize("latex, reason", [
    (r"y = \Phi(x)", "phi"),
    (r"y = \binom{n}{k}", "binom"),
    (r"y = n!", "factorial"),
    (r"y = 3!", "factorial"),
    (r"y = \Gamma(x)", "gamma"),
    (r"y = \int_0^1 x", "integral"),
    (r"y = \sum_{k} k", "sum"),
    (r"y = \prod_{k} k", "product"),
    (r"y = \lim_{x \to 0} x", "limit"),
    (r"y = \frac{d}{dx} x", "derivative"),
    (r"y = \frac{dy}{dx}", "derivative"),
    (r"y = \partial x", "derivative"),
    (r"y = \begin{pmatrix} 1 & 2 \end{pmatrix}", "matrix"),
    (r"y = \mathbb{1}", "indicator"),
    (r"y = x \in A", "set"),
    (r"y = \log(x)", "log_base"),
    (r"y = \text{half of } x", "text"),
    ("y = 𝜆", "unicode_math"),
    ("y = λ", "unicode_math"),
    (r"y < x", "relation"),
    (r"y \approx x", "relation"),
    (r"y \propto x", "relation"),
    (r"x + 1", "not_equation"),
    (r"y = x = z", "multiple_relations"),
    (r"y = g(1-p)", "application"),
    (r"y = e", "ambiguous_e"),
    (r"y = e + e^x", "ambiguous_e"),
    (r"y = \epsilon + \varepsilon", "name_collision"),
    (r"y = \sqrt[3]{x}", "nth_root"),
    (r"y = x_{12}", "subscript"),
    (r"y = \sin^2 x", "function_power"),
    (r"y = \sin 2x", "function_arg"),
    (r"y = 1 / 2 x", "ambiguous_slash"),
    (r"y = 1 / 2 / x", "ambiguous_slash"),
    (r"y = x^10", "syntax"),
    (r"y = \frac12", "syntax"),
    (r"y = \begin{aligned} x \end{aligned}", "unsupported_environment"),
    (r"y = \operatorname{sinc}(x)", "unsupported_function"),
    (r"y = \hat{x}", "unsupported_command"),
    (r"y = " + "x+" * 1200 + "x", "too_long"),
])
def test_each_unreadable_construct_has_its_reason(latex, reason):
    with pytest.raises(B.Unreadable) as caught:
        B.read_relation(latex)
    assert caught.value.reason == reason


def test_every_reason_key_is_in_the_closed_list():
    assert len(set(B.REASONS)) == len(B.REASONS)


def test_the_e_rule_reads_only_a_power_or_mathrm():
    assert rhs(r"y = e^{x} e^{-x}").kind == "bin"
    with pytest.raises(B.Unreadable):
        B.read_relation(r"y = e x")
    # e_1 is a symbol, never Euler's number.
    assert G.free_names(rhs(r"y = e_1")) == {"e1"}


def test_the_product_rule_never_resolves_a_name():
    assert B.read_relation(r"y = \lambda(1-p) \lambda").rhs.kind == "bin"
    with pytest.raises(B.Unreadable):
        B.read_relation(r"y = \lambda(1-p)")
    assert B.read_relation(r"f(\lambda) = \lambda(1-p)").args == ("lambda",)


def test_the_left_hand_side_is_kept_as_the_books_substring_with_its_arguments():
    relation = B.read_relation(r"f_X(x) = x")
    assert relation.lhs == "f_X(x)" and relation.args == ("x",)
    assert B.read_relation(r"P(X = k) = k").lhs == "P(X = k)"
    assert B.read_relation(r"P(X = k) = k").args == ()
    assert B.read_relation(r"E[X] = 2").args == ()
    assert B.read_relation(r"f\left(x\right) = x").args == ("x",)
    assert B.read_relation(r"g(x, \mu) = x \mu").args == ("x", "mu")
    assert B.read_relation(r"y = \lambda x").tokens == {"lambda": r"\lambda", "x": "x"}


def _cases(*rows: str) -> str:
    return r"y = \begin{cases} " + r" \\ ".join(rows) + r" \end{cases}"


def test_cases_with_and_without_otherwise():
    same(_cases("a & x < 0", r"b & \text{otherwise}"), "piecewise((x < 0, a), b)")
    same(_cases("a & x < 0", r"b & x \ge 0"), "piecewise((x < 0, a), b)")
    same(_cases(r"a, & \text{if } x < 0,", r"b, & \text{for } x \geq 0."), "piecewise((x < 0, a), b)")
    assert rhs(_cases(r"a & 0 \le x < 1", r"b & \text{otherwise}")).args[0].kind == "and"
    same(_cases(r"a & x < \frac{1}{2}", r"b & x \ge \frac{1}{2}"), "piecewise((x < 0.5, a), b)")
    same(_cases("a & x < -1", r"b & x \ge -1"), "piecewise((x < -1, a), b)")


@pytest.mark.parametrize("rows, reason", [
    (("a & x < 0", "b & x > 0"), "cases_cover"),          # 0 is in no row
    (("a & x < 1", "b & x > 0"), "cases_cover"),          # (0, 1) is in two rows
    (("a & x < 0", r"b & \text{else}"), "text"),
    (("a & x < 0", "b"), "cases_cover"),                  # a row with no condition column
    (("a & x < 0.3", r"b & \text{otherwise}"), "inexact_literal"),
    (("a & x < y + 1", r"b & \text{otherwise}"), "cases_condition"),
    (("a & x < y", r"b & \text{otherwise}"), "cases_condition"),
    (("a & x < 0", r"b & y < 0", r"c & \text{otherwise}"), "cases_condition"),
    ((r"a & x \in A", r"b & \text{otherwise}"), "set"),
])
def test_cases_refusals(rows, reason):
    with pytest.raises(B.Unreadable) as caught:
        B.read_relation(_cases(*rows))
    assert caught.value.reason == reason


def test_segments_find_only_delimited_latex_or_an_equation_block():
    assert [s.latex for s in B.segments(r"see $a = 1$ and $$b = 2$$ and \[c = 3\] done")] == ["a = 1", "b = 2", "c = 3"]
    assert [s.latex for s in B.segments("y = x", "Equation")] == ["y = x"]
    assert B.segments("y = x", "Text") == []
    assert B.segments("y = 𝜆x", "Text") == []
    text = r"before $a = 1$"
    found = B.segments(text)[0]
    assert text[found.start:found.end] == "a = 1"


def test_caps_and_a_seeded_fuzz_never_raise_outside_the_reasons():
    assert_never = random.Random(20261102)
    alphabet = list("xyzpq0123456789+-*/^_(){}[]|=<>,.& ") + [
        r"\frac", r"\sqrt", r"\begin{cases}", r"\end{cases}", r"\\", r"\left", r"\right", r"\lambda", "e", r"\text{if }",
        r"\min", r"\exp", r"\mathrm{e}", r"\operatorname{erf}", r"\cdot", "λ"]
    for _ in range(3000):
        text = "".join(assert_never.choice(alphabet) for _ in range(assert_never.randrange(1, 40)))
        try:
            relation = B.read_relation("y = " + text)
        except B.Unreadable as refused:
            assert refused.reason in B.REASONS
        else:
            assert relation.rhs.kind
    with pytest.raises(B.Unreadable) as caught:
        B.read_relation("y = " + "(" * 60 + "x" + ")" * 60)
    assert caught.value.reason == "too_long"
    with pytest.raises(B.Unreadable) as caught:
        B.read_relation("y = " + "x" * 450)
    assert caught.value.reason == "too_long"


@pytest.mark.parametrize("text, exact", [("0", True), ("1", True), ("0.5", True), ("0.375", True), ("0.3", False),
                                         ("0.1", False), ("10000000000000001", False), ("1234567890123456789012345678901", False)])
def test_literals_are_exact_binary64_or_nothing(text, exact):
    assert B.binary64_exact(text) is exact
