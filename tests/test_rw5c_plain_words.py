"""Reader RW5c, Sol verify V1: a label's plain text comes from KaTeX's tree, never from its source with the marks dropped."""

from __future__ import annotations

import json
import random
import re

import pytest

from learnloop.content.authoring import pf_sandbox
from learnloop.figures import book_math as B
from learnloop.figures import elements as E
from learnloop.figures import grammar as G
from learnloop.figures import katex_tree as KT
from learnloop.figures import source_check as SC
from learnloop.figures import spec as S
from tests import katex_meaning as M
from tests.figure_fixtures import AuthorFake, build, context
from tests.rw5c_fixtures import EXTRACTION, build_check_vault, plot

sandboxed = pytest.mark.skipif(not pf_sandbox.sandbox_available(), reason="needs bubblewrap")


@pytest.fixture
def trees():
    with KT.Trees() as engine:
        yield engine


def _plain(lhs: str, trees: KT.Trees) -> str:
    return B.read_relation(lhs + "=x", trees=trees).lhs_plain


@pytest.mark.parametrize(("lhs", "plain"), [
    (r"\frac{dF(x)}{dx}", "dF(x)/dx"), (r"\frac{dy}{dx}", "dy/dx"), (r"\frac{d^2y}{dx^2}", "d^2 y/dx^2"),
    (r"\frac{\partial F}{\partial x}", "∂F/∂x"), (r"\frac{1-a}{k}", "(1-a)/k"), (r"\frac{a}{bc}", "a/(bc)"), (r"\frac{a}{dx}", "a/(dx)"),
    (r"\frac{a}{f(x)}", "a/f(x)"), (r"\frac{a}{b(c)d}", "a/(b(c)d)"), (r"\frac{1}{2\pi}", "1/(2 pi)"), (r"\frac{1}{12}", "1/12"),
    (r"\frac{\frac{a}{b}}{c}", "(a/b)/c"), (r"\frac{a}{\frac{b}{c}}", "a/(b/c)"), (r"2\frac{a}{b}", "2(a/b)"), (r"\frac{a}{b}c", "(a/b)c"),
    (r"\frac{a}{b}\frac{c}{d}", "(a/b)(c/d)"), (r"\frac{a}{b}+c", "a/b+c"), (r"-\frac{a}{b}", "-a/b"), (r"\frac{a}{b}^2", "(a/b)^2"),
    (r"\frac{a}{b}!", "(a/b)!"), (r"\binom{n}{k}", "binom(n, k)"), (r"\sqrt{1-k}", "sqrt(1-k)"), (r"e^{-k}", "e^(-k)"), (r"x^{a+b}", "x^(a+b)"),
    (r"x^{10}", "x^10"), (r"x^{ab}", "x^(ab)"), (r"x^\alpha", "x^alpha"), (r"x_{i+1}", "x_(i+1)"), (r"f_{X}(k)", "f_X(k)"), (r"x_1^2", "x_1^2"),
    (r"(x)^2", "(x)^2"), (r"f'(x)", "f'(x)"), (r"f''(x)", "f''(x)"), (r"\alpha\beta", "alpha beta"), (r"\alpha x", "alpha x"), (r"2\alpha", "2 alpha"),
    (r"2 3", "23"), (r"2\,3", "2 3"), (r"ab", "ab"), (r"2x", "2x"), (r"\sin x", "sin x"), (r"\sin(x)", "sin(x)"), (r"\text{Var}(X)", "Var(X)"),
    (r"\text{a or b}", "a or b"), (r"\operatorname{Var}(X)", "Var(X)"), (r"\mathrm{Var}(X)", "Var(X)"), (r"\mathrm{1-F}(k)", "1-F(k)"),
    (r"\mathbf{x}", "bold(x)"), (r"\mathbb{E}[X]", "bb(E)[X]"), (r"\hat{F}(x)", "hat(F)(x)"), (r"\bar{x}", "bar(x)"), (r"P(X = k)", "P(X=k)"),
    (r"P(X \le k)", "P(X<=k)"), (r"P(A \mid B)", "P(A | B)"), (r"P(A \cup B)", "P(A union B)"), (r"F(k)\cdot 2", "F(k)*2"), (r"F(k)\pm 1", "F(k)±1"),
    (r"\lvert x\rvert", "|x|"), (r"|x|", "|x|"), (r"\left(1-F(k)\right)", "(1-F(k))"), (r"\left[x\right]", "[x]"), (r"f(x, y)", "f(x, y)"), (r"n!", "n!"),
    (r"\{1-F\}", "{1-F}"), (r"{1-F(k)}", "1-F(k)"), (r"\sum_{k=0}^{n} a_k", "sum_(k=0)^n a_k"), (r"\ell(\theta)", "ell(theta)"),
])
def test_the_tree_s_structure_is_in_the_words(lhs, plain, trees):
    assert _plain(lhs, trees) == plain


def test_cdots_has_plain_words_as_ldots_does(trees):
    """The router objective's follow-up batch, item 8 (reader-rw5c-p1.md's open item: all three fallbacks on the
    owner's books came from it): KaTeX's ``\\@cdots`` reads as ``...``, never the fallback."""

    assert _plain(r"a_1+\cdots+a_n", trees) == _plain(r"a_1+\ldots+a_n", trees)
    assert "..." in _plain(r"a_1+\cdots+a_n", trees) and _plain(r"a_1+\cdots+a_n", trees) != B.PLAIN_FALLBACK


#: The closed list of what has no faithful words (the review file names them): never a guess, and no markup in what is shown.
_NO_WORDS = (
    r"\sqrt[3]{x}", r"\mathfrak{g}(x)", r"\mathscr{L}(x)", r"\mathsf{P}(x)", r"\mathtt{P}(x)", r"\check{x}", r"\breve{x}", r"\mathring{x}", r"\aleph",
    r"\hbar", r"\left\langle x\right\rangle", r"\left\lfloor x\right\rfloor", r"\oint_C f", r"\langle x\rangle", r"\lfloor x\rfloor", r"A\otimes B",
    r"{a+b}^2", r"{ab}^2", r"{}^2 x", r"f'^2", r"\text{a\_b}", r"\sqrt{}", r"\frac{}{b}", r"\genfrac[]{0pt}{}{a}{b}", r"\genfrac{(}{)}{1pt}{}{a}{b}", r"\atop",
)


@pytest.mark.parametrize("lhs", _NO_WORDS)
def test_what_has_no_faithful_words_says_so_in_closed_words(lhs, trees):
    try:
        relation = B.read_relation(lhs + "=x", trees=trees)
    except B.Unreadable:
        return  # refused by the reader outright, which is also no garbling
    assert relation.lhs_plain == B.PLAIN_FALLBACK, lhs


def test_the_fallback_is_written_whole_as_an_operand_with_no_brackets(trees):
    relation = B.read_relation(r"\mathfrak{g}(x)-1=x", trees=trees)
    assert relation.lhs_compound and relation.lhs_plain == B.PLAIN_FALLBACK
    label = E.BookLabel(relation.lhs, relation.latex, "x", {}, "e", "s", 1, relation.lhs_compound, relation.lhs_plain)
    assert label.operand == (r"\left(\mathfrak{g}(x)-1\right)", B.PLAIN_FALLBACK)


@pytest.mark.parametrize(("token", "plain"), [("x", "x"), (r"\alpha", "alpha"), ("x_{1}", "x_1"), (r"\lambda_{i}", "lambda_i"), (r"\varepsilon", "varepsilon")])
def test_a_symbol_token_s_closed_form_is_read_as_a_name(token, plain):
    assert E._token_plain(token) == plain


def _generated(chance: random.Random, depth: int = 0) -> str:
    atom = chance.choice(("a", "b", "x", "y", "2", "3", "12"))
    if depth >= 3:
        return atom
    shape = chance.randrange(11)
    one, other = (lambda: _generated(chance, depth + 1)), (lambda: _generated(chance, depth + 1))
    if shape <= 2:
        return atom
    if shape <= 4:
        return rf"\frac{{{one()}}}{{{other()}}}"
    if shape == 5:
        return rf"\sqrt{{{one()}}}"
    if shape == 6:
        return rf"\left({one()}\right)^{{{other()}}}"
    if shape == 7:
        return f"{chance.choice('abxy')}^{{{one()}}}"
    if shape == 8:
        return f"{one()}{chance.choice(('+', '-'))}{other()}"
    if shape == 9:
        return rf"{one()}\cdot {other()}"
    return f"({one()}){chance.choice('abxy')}"


def _as_grammar(plain: str) -> G.Node:
    """Words read back by the grammar's own parser, juxtaposition written as a product."""

    spaced = re.sub(r"sqrt\(", "S(", plain)
    for _ in range(4):
        spaced = re.sub(r"(?<=[0-9a-z)])(?=[a-zS(])", "*", spaced)
    return G.parse(spaced.replace("S*(", "sqrt(").replace("S(", "sqrt("))


def test_generated_words_read_back_to_the_value_katex_s_own_mathml_means():
    """Fractions, roots, scripts and signs, nested: the words mean what the page shows (MathML read independently of the tree)."""

    chance = random.Random(20261103)
    compared = 0
    points = [{"a": 1.25, "b": 0.75, "x": 1.5, "y": 0.625}, {"a": 2.5, "b": 1.5, "x": 0.875, "y": 2.25}]
    with KT.Trees() as trees, M.Renderer() as renderer:
        for _ in range(1200):
            lhs = _generated(chance)
            try:
                relation = B.read_relation(lhs + "=z", trees=trees)
                shown = renderer.mathml("z=" + lhs)
                meaning = M.right_hand_side(shown) if shown is not None else None
            except (B.Unreadable, AssertionError, ValueError, G.GrammarError):
                continue
            if meaning is None:
                continue
            assert relation.lhs_plain != B.PLAIN_FALLBACK, lhs
            assert M.same_value(_as_grammar(relation.lhs_plain), meaning, points), (lhs, relation.lhs_plain)
            compared += 1
    assert compared > 300


def test_the_comparison_above_has_teeth():
    """The garbled words V1 found, and a fraction read without its brackets, fail the same comparison."""

    points = [{"a": 1.25, "k": 0.75}]
    with M.Renderer() as renderer:
        meaning = M.right_hand_side(renderer.mathml(r"z=\frac{1-a}{k}"))
    assert M.same_value(_as_grammar("(1-a)/k"), meaning, points)
    assert not M.same_value(_as_grammar("1-a/k"), meaning, points)


@sandboxed
def test_v1_the_radio_buttons_and_the_labels_through_the_real_build(tmp_path):
    """Sol's case: \\frac{dF(x)}{dx}=2x comes back checked, and an area prediction's choices hold the fraction."""

    spec = plot("2*x", shades=[{"series": "the book's curve", "from": "0", "to": "0.5", "label": "the model's area"}])
    spec["predictions"] = [{"prompt": "which?", "observe": {"kind": "area", "expr": "integral(f, x, 0, 0.5)"}}]
    paths, _repository = build_check_vault(tmp_path / "vault", [("a", "Text", r"The density is $\frac{dF(x)}{dx}=2x$.")])
    figure = build(context(paths.root, author=AuthorFake([spec])), {"extractionId": EXTRACTION, "spanIds": ["a"]})["figure"]
    assert figure["sourceCheck"]["status"] == "checked"
    elements = {element["id"]: element for element in figure["elements"]}
    assert elements["panels.0.series.0"]["tex"] == r"\frac{dF(x)}{dx}" and elements["panels.0.series.0"]["plain"] == "dF(x)/dx"
    assert figure["predictions"][0]["choices"] == [{"value": "panels.0.shade.0", "label": "area under dF(x)/dx from 0 to 0.5"}]
    assert "frac" not in json.dumps([element["plain"] for element in figure["elements"]])


@sandboxed
def test_v1_a_bar_series_grouped_label_through_the_real_check(tmp_path):
    """Sol's other case: bars labelled \\frac{1-a}{k}: the accessible description holds (1-a)/k, in every template that writes it."""

    from learnloop.vault.loader import load_vault

    spec = plot("2^(-k)", name="tail", variable="k", low=0.0, high=2.0, label="tail")
    spec["panels"] = [{"kind": "pmf_bars", "k": {"var": "k", "min": 0, "max": 2}, "series": [{"expr": "tail", "label": "tail"}],
                       "highlight": {"from": "0", "to": "1", "label": "first"}},
                      {"kind": "readout", "label": "total", "expr": "sum(tail, k, 0, 2)"}]
    paths, repository = build_check_vault(tmp_path / "vault", [("a", "Text", r"The tail is $\frac{1-a}{k}=2^{-k}$.")])
    result = SC.check_figure(load_vault(paths.root), repository, S.parse_spec(spec), spans=[(EXTRACTION, "a", "a")], grounding="anchor")
    assert result.outcome == SC.CHECKED
    elements = {element["id"]: element for element in result.elements}
    assert elements["panels.0.series.0"]["plain"] == "(1-a)/k"
    assert elements["panels.0.highlight"]["plain"] == "sum for k from 0 to 1 of (1-a)/k"
    assert elements["panels.1"]["plain"] == "sum for k from 0 to 2 of (1-a)/k"
    assert elements["panels.1"]["template"]["body_plain"] == "(1-a)/k"


def test_stored_labels_regenerate():
    # A stored version-5 "checked" holds the old words: it is not delivered, and a recheck writes the new ones.
    # (7: \cdots gained its words, the follow-up batch's item 8; a version-6 label is read again the same way.)
    assert SC.CERTIFICATION_VERSION == 7
