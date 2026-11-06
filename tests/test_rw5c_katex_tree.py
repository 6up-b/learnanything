"""Reader RW5c: the source equation is read from KaTeX's own parse tree (spec §5.3).

The vendored KaTeX is pinned to the Reader's lock; the sealed engine fails closed; and the shared
test: real source strings go through the reader and through the KaTeX the page uses, and whatever
reads as ``checked``-eligible must mean what the rendering means. ``bookMathRender.test.ts`` runs the
same corpus through the Reader's real pipeline.
"""

from __future__ import annotations

import hashlib
import json
import random
from pathlib import Path

import pytest

from learnloop.figures import book_math as B
from learnloop.figures import grammar as G
from learnloop.figures import katex_tree as KT
from learnloop.figures import sketch_engine as SE
from tests import katex_meaning as M

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "apps" / "learnloop-tauri"
LOCK = json.loads((APP / "sketch-engine" / "engine.lock.json").read_text(encoding="utf-8"))
VARIANT = LOCK["variants"]["book-math"]
PACKAGE_LOCK = json.loads((APP / "package-lock.json").read_text(encoding="utf-8"))
CORPUS = json.loads((APP / "src" / "screens" / "reader" / "figures" / "bookMathRenderCorpus.json").read_text(encoding="utf-8"))


# -- the pins ---------------------------------------------------------------------------------------------

def test_the_vendored_katex_is_the_one_the_reader_locks():
    locked = PACKAGE_LOCK["packages"]["node_modules/katex"]
    assert KT.KATEX_VERSION == locked["version"] == VARIANT["katex"]["version"]
    assert VARIANT["katex"]["npm_integrity"] == locked["integrity"]
    assert hashlib.sha256(KT.KATEX_PATH.read_bytes()).hexdigest() == KT.KATEX_SHA256 == VARIANT["katex"]["sha256"]
    # One KaTeX on the page: rehype-katex and figureLabels resolve the same package.
    others = [path for path in PACKAGE_LOCK["packages"] if path.endswith("/katex") and path != "node_modules/katex"
              and "@types" not in path]
    assert others == []


def test_the_vendored_file_is_byte_for_byte_the_installed_package_when_installed():
    installed = APP / "node_modules" / "katex"
    if not installed.exists():
        pytest.skip("node_modules is not installed here; the lock's version and integrity are pinned above")
    assert json.loads((installed / "package.json").read_text(encoding="utf-8"))["version"] == KT.KATEX_VERSION
    assert (installed / "dist" / "katex.min.js").read_bytes() == KT.KATEX_PATH.read_bytes()


def test_a_katex_or_markdown_bump_moves_the_reader_version_and_needs_a_certification_bump():
    from learnloop.figures import source_check as SC

    assert KT.KATEX_VERSION in B.READER_VERSION and KT.MARKDOWN_SHA256[:12] in B.READER_VERSION
    # A new KaTeX or markdown can read a stored equation otherwise: bump CERTIFICATION_VERSION with it, then this tuple.
    assert (SC.CERTIFICATION_VERSION, KT.KATEX_VERSION, KT.MARKDOWN_SHA256[:12]) == (7, "0.16.47", "29fd5be75b4e")


def test_the_vendored_markdown_is_the_page_pipeline_the_reader_locks():
    """The digest, every bundled package at the version package-lock.json locks, and each one's licence
    named in the notice. bookMathRender's build test rebuilds the bytes from the source and these packages."""

    lock = json.loads((KT.MARKDOWN_PATH.parent / "page-markdown.lock.json").read_text(encoding="utf-8"))
    data = KT.MARKDOWN_PATH.read_bytes()
    assert hashlib.sha256(data).hexdigest() == KT.MARKDOWN_SHA256 == lock["sha256"]
    assert len(data) == lock["bytes"] and b"\0" not in data and data.isascii()
    notice = (KT.MARKDOWN_PATH.parent / "LICENSES.txt").read_text(encoding="utf-8")
    for name, version in lock["packages"].items():
        assert PACKAGE_LOCK["packages"][f"node_modules/{name}"]["version"] == version
        assert f"--- {name} {version} (" in notice
        # One copy: react-markdown and the bundle resolve the same package.
        assert not [path for path in PACKAGE_LOCK["packages"] if path.endswith(f"/node_modules/{name}")]
    # What makes it the page's: the parser, the plugins MarkdownMath passes, and remark-rehype.
    assert {"remark-gfm", "remark-math", "remark-rehype", "micromark", "unified"} <= set(lock["packages"])


def test_the_vendored_file_is_text_with_its_licence_beside_it():
    data = KT.KATEX_PATH.read_bytes()
    assert b"\0" not in data
    data.decode("utf-8")
    notice = (KT.KATEX_PATH.parent / "LICENSE").read_text(encoding="utf-8")
    assert "MIT License" in notice and "Khan Academy" in notice
    assert "katex/LICENSE" in (APP / "sketch-engine" / "LICENSES.txt").read_text(encoding="utf-8")


def test_the_engine_variant_is_pinned_and_differs_from_the_sketch_engine_by_its_defines():
    assert VARIANT["defines"] == ["-DSK_WITH_REGEXP", f"-DSK_TICKS_PER_CALL={KT.BOOK_MATH_TICKS_PER_CALL}u"]
    assert SE.artifact_digest(KT.KATEX_ENGINE_PATH) == KT.KATEX_ENGINE_SHA256 == VARIANT["output"]["sha256"]
    # The sketch tier's artifact and its pin did not move; a sketch still has no regular expression.
    assert SE.artifact_digest() == SE.ENGINE_SHA256 == LOCK["output"]["sha256"]
    with SE.SketchEngine() as sketch:
        with pytest.raises(SE.SketchRunError, match="RegExp are not supported"):
            sketch.load("var r = /a/; function view() { return 0; }")


def test_the_variant_runs_under_the_sketch_engines_caps_but_its_own_work_budget():
    with SE.SketchEngine(path=KT.KATEX_ENGINE_PATH, expected=KT.KATEX_ENGINE_SHA256) as engine:
        limits = engine.limits()
    assert limits["memory_bytes"] == SE.SKETCH_MEMORY_BYTES
    assert limits["ticks_per_call"] == KT.BOOK_MATH_TICKS_PER_CALL
    assert limits["serialize_ticks"] == SE.SKETCH_SERIALIZE_TICKS


# -- fail closed ---------------------------------------------------------------------------------------------

def _reason(latex: str, **kwargs) -> str:
    with pytest.raises(B.Unreadable) as caught:
        B.read_relation(latex, **kwargs)
    return caught.value.reason


def test_a_missing_engine_is_unreadable_never_a_fallback(tmp_path):
    missing = KT.Trees(path=tmp_path / "gone.wasm")
    assert _reason("y = x", trees=missing) == "engine_unavailable"


def test_a_wrong_engine_digest_is_unreadable():
    assert _reason("y = x", trees=KT.Trees(expected="0" * 64)) == "engine_unavailable"


def test_a_changed_katex_file_is_unreadable(tmp_path):
    changed = tmp_path / "katex.min.js"
    changed.write_text(KT.KATEX_PATH.read_text(encoding="utf-8") + "\n//", encoding="utf-8")
    assert _reason("y = x", trees=KT.Trees(source=changed)) == "engine_unavailable"


def test_a_changed_markdown_bundle_is_unreadable(tmp_path):
    changed = tmp_path / "page-markdown.js"
    changed.write_text(KT.MARKDOWN_PATH.read_text(encoding="utf-8") + "\n//", encoding="utf-8")
    assert _reason("y = x", trees=KT.Trees(markdown=changed)) == "engine_unavailable"
    with pytest.raises(B.Unreadable) as caught:
        B.segments("$y = x$", trees=KT.Trees(markdown=changed))
    assert caught.value.reason == "engine_unavailable"


def test_with_no_engine_a_block_has_no_segments_never_a_fallback(tmp_path):
    with pytest.raises(B.Unreadable) as caught:
        B.segments("$y = x$", trees=KT.Trees(path=tmp_path / "gone.wasm"))
    assert caught.value.reason == "engine_unavailable"


def test_a_block_past_the_work_cap_or_nested_past_the_stack_is_unreadable_and_the_engine_still_reads():
    with KT.Trees() as trees:
        for text in ("$a = 1$ word " * 40_000, "> " * 5_000 + "$a = 1$", "[" * 20_000 + "$a = 1$"):
            with pytest.raises(B.Unreadable) as caught:
                found = B.segments(text, trees=trees)
                pytest.fail(f"read {len(found)} segments")
            assert caught.value.reason in ("too_long", "not_rendered")
        assert [segment.latex for segment in B.segments("$y = x$", trees=trees)] == ["y = x"]


def test_a_long_paragraph_of_a_book_fits_the_work_budget():
    """Measured on the coverage corpus (review file): its longest block with math is 5,879 characters."""

    text = "The density is $f(x) = x + 1$ for every word of this sentence, as above. " * 81
    assert len(text) > 5_879
    with KT.Trees() as trees:
        assert len(B.segments(text, trees=trees)) == 81


def test_a_segment_over_the_work_cap_is_unreadable_and_the_engine_still_reads():
    with KT.Trees() as trees:
        assert _reason("y = " + "x+" * 990 + "x", trees=trees) == "too_long"
        assert B.read_relation("y = x", trees=trees).lhs == "y"


def test_a_segment_nested_past_every_cap_is_unreadable_not_a_crash():
    with KT.Trees() as trees:
        for source in ("y = " + "{" * 900 + "x" + "}" * 900, "y = " + "\\sqrt{" * 300 + "x" + "}" * 300,
                       "y = " + "(" * 900 + "x" + ")" * 900):
            assert _reason(source, trees=trees) in B.REASONS
        assert B.read_relation("y = x", trees=trees).lhs == "y"


# -- what KaTeX decides ----------------------------------------------------------------------------------------

@pytest.mark.parametrize("definition", [
    r"\def\a{1}", r"\gdef\a{1}", r"\edef\a{1}", r"\xdef\a{1}", r"\let\a=b", r"\futurelet\a\b\c", r"\global\def\a{1}",
    r"\long\def\a{1}", r"\newcommand{\a}{1}", r"\newcommand\a{1}", r"\renewcommand{\sin}{\cos}", r"\providecommand{\a}{1}",
    r"{\def\a{1}}", r"x^{\def\a{1}2}",
])
def test_any_macro_definition_anywhere_is_unreadable(definition):
    assert _reason(definition + r"f(x)=x") == "macro_definition"
    assert _reason(r"f(x)=x + " + definition) == "macro_definition"


def test_a_definition_never_reaches_another_parse_in_one_engine():
    """The page calls KaTeX once per math element with fresh settings; the engine must match it, reused."""

    with KT.Trees() as trees:
        trees.parse(r"\def\foo{1}\foo")
        with pytest.raises(KT.TreeRefused) as caught:
            trees.parse(r"\foo")
        assert caught.value.reason == "not_rendered"
        with pytest.raises(KT.TreeRefused) as caught:
            trees.parse(r"\gdef\foo{1}\foo")
        assert caught.value.reason == "macro_definition"
        with pytest.raises(KT.TreeRefused):
            trees.parse(r"\foo")


@pytest.mark.parametrize("latex", [r"y = x_1^a", r"y = \begin{cases} a & x < 0 \\ b & x \ge 0 \end{cases}", r"y = \frac{1}{2}"])
def test_display_mode_does_not_change_a_readable_tree(latex):
    """``$$`` in a paragraph is inline on the page and alone on a line display: either way the same reading."""

    with KT.Trees() as trees:
        inline = B.read_relation(latex, display=False, trees=trees)
        display = B.read_relation(latex, display=True, trees=trees)
    assert inline.rhs == display.rhs and inline.lhs == display.lhs


@pytest.mark.parametrize("latex, reason", [
    (r"\color{red}f(x)=x", "not_equation"),
    (r"\textcolor{red}{f}(x)=x", "unsupported_command"),
    (r"\href{http://x}{f}=x", "unsupported_command"),
    (r"\phantom{g}f(x)=x", "unsupported_command"),
    (r"f\kern9em(x)=x", "unsupported_command"),
    (r"\raisebox{1em}{f}=x", "unsupported_command"),
    (r"\htmlClass{a}{f}=x", "unsupported_command"),
    (r"\begin{matrix}a\end{matrix}=x", "unsupported_command"),
    (r"a\over b=c", "not_equation"),
    (r"\bf y=x", "not_equation"),
    (r"\displaystyle y=x", "not_equation"),
])
def test_a_left_hand_side_outside_the_label_table_is_unreadable(latex, reason):
    assert _reason(latex) == reason


@pytest.mark.parametrize("latex, lhs, args", [
    (r"  f(x) = x", "f(x)", ("x",)),
    (r"f_X(x) := x", "f_X(x)", ("x",)),
    (r"\hat{y} = x", r"\hat{y}", ()),
    (r"P(X = k) = k", "P(X = k)", ()),
    (r"\frac{y}{2} = x", r"\frac{y}{2}", ()),
    (r"\text{Var}(X) = x", r"\text{Var}(X)", ()),
    (r"f\left(x\right) = x", r"f\left(x\right)", ("x",)),
])
def test_the_left_hand_side_is_the_books_substring_and_the_left_of_the_parse(latex, lhs, args):
    relation = B.read_relation(latex)
    assert relation.lhs == lhs and relation.args == args


def test_the_left_hand_side_is_refused_when_alone_it_would_not_be_the_left_of_the_parse():
    """``\\left(`` balanced across the = never splits; a substring KaTeX reads otherwise never labels."""

    with KT.Trees() as trees:
        tree = trees.parse(r"y^2 = x")
        with pytest.raises(B.Unreadable):
            B._left_hand_side("z^2 = x", tree, 1, trees=trees, display=False)
        assert B._left_hand_side(r"y^2 = x", tree, 1, trees=trees, display=False) == "y^2"


@pytest.mark.parametrize("latex", [
    r"y = {a+b}c",           # braces show nothing: the page says a + bc
    r"y = \sin{x+1}",        # the page says sin x + 1
    r"y = a +^2 b",          # a script on an operator
    r"y = a {}^2 b",
    r"y = (a)_1",
    r"y = 2_1",
    r"y = \begin{cases} a & x^2 < 1 \\ b & \text{otherwise} \end{cases}",   # a condition's power is not dropped
    r"y = \begin{cases} a & 2^3 < x \\ b & \text{otherwise} \end{cases}",
    r"y = \mathrm{e\hat{x}}",  # never the constant e
    r"y = \left(1\,000\right)",
    r"y = 2\,3",
    r"y = \frac{1}{2}3",
    r"y = |a|b|c|",          # |a|·b·|c| or |a·|b|·c|
    r"y = |a||b|",
    r"\, = x",               # nothing to label
])
def test_what_a_tree_shows_that_no_row_covers_is_refused_never_dropped(latex):
    assert _reason(latex) in B.REASONS


# -- the shared corpus --------------------------------------------------------------------------------------------

@pytest.fixture(scope="module")
def renderer():
    with M.Renderer() as rendering:
        yield rendering


def _shape(node: G.Node):
    return (node.kind, node.text, node.op, tuple(_shape(child) for child in node.args))


@pytest.mark.parametrize("case", CORPUS["read"], ids=lambda case: case["rhs"])
def test_each_read_form_has_the_pages_mathml_and_means_it(case, renderer):
    assert renderer.mathml(case["rhs"]) == case["mathml"]
    source = "y = " + case["rhs"]
    relation = B.read_relation(source)
    assert _shape(relation.rhs) == _shape(G.parse(case["grammar"]))
    meaning = M.right_hand_side(renderer.mathml(source))
    assert M.same_value(relation.rhs, meaning, _points(relation.rhs, meaning))


@pytest.mark.parametrize("case", CORPUS["refused"], ids=lambda case: case["rhs"])
def test_each_refused_form_has_the_pages_mathml_and_its_reason(case, renderer):
    assert renderer.mathml(case["rhs"]) == case["mathml"]
    assert _reason("y = " + case["rhs"]) == case["reason"]


@pytest.mark.parametrize("case", CORPUS["not_rendered"], ids=lambda case: case["rhs"])
def test_what_the_page_cannot_render_is_never_read(case, renderer):
    assert renderer.mathml(case["rhs"]) is None
    assert _reason("y = " + case["rhs"]) == "not_rendered"


@pytest.mark.parametrize("case", CORPUS["whole"], ids=lambda case: case["latex"])
def test_each_whole_segment_has_its_reason(case, renderer):
    assert renderer.mathml(case["latex"]) == case["mathml"]
    assert _reason(case["latex"]) == case["reason"]


@pytest.mark.parametrize("case", CORPUS["blocks"], ids=lambda case: case["block"])
def test_a_blocks_segments_are_the_ones_the_page_has(case):
    found = B.segments(case["block"])
    assert [" ".join(segment.latex.split()) for segment in found] == case["segments"]
    # What the page shows as an error, the sealed KaTeX refuses too; the reader never reads it.
    if case.get("page") == []:
        assert found
        for segment in found:
            assert _reason(segment.latex, display=segment.display) == "not_rendered"


# -- the generated differential ------------------------------------------------------------------------------------

def _points(*nodes: G.Node) -> list[dict[str, float]]:
    names = sorted(set().union(*(G.free_names(node) for node in nodes)))
    return [{name: start + step * index for index, name in enumerate(names)}
            for start, step in ((0.37, 0.61), (1.7, 0.29), (-0.9, 0.43), (3.0, 1.0))]


LETTERS = ["x", "y", "a", "b", "p", r"\lambda", r"\mu", r"\theta", r"\mu_1", "x_{0}", "x_a", r"\Delta"]
NUMBERS = ["2", "12", "0.5", ".25", "3", "2 3", "10"]


def _expression(chance: random.Random, depth: int = 0) -> str:
    """A book-style right-hand side, in the spellings books use, braces or none."""

    def inner() -> str:
        return _expression(chance, depth + 1)

    def atom() -> str:
        return chance.choice(LETTERS + NUMBERS + [r"\pi", r"e^{x}", r"e^x", r"\mathrm{e}^{x}", r"\mathrm{e}"])

    if depth >= 3:
        return atom()
    shape = chance.randrange(32)
    if shape >= 30:
        return "{" + inner() + "}" + chance.choice(["", " ", atom(), "^2"])
    if shape < 6:
        return atom()
    if shape < 9:
        return f"{inner()} {chance.choice(['+', '-'])} {inner()}"
    if shape < 12:
        return f"{inner()} {chance.choice(['', ' ', r'\cdot ', r'\times ', r'\,'])}{atom()}"
    if shape < 14:
        return rf"\frac{{{inner()}}}{{{inner()}}}"
    if shape == 14:
        return chance.choice([r"\frac12", r"\frac{1}{4}", r"\frac1x", r"\frac{1}{2}x"])
    if shape == 15:
        return f"{atom()}/{atom()}"
    if shape < 18:
        return f"{chance.choice(['x', 'a', '2', r'\lambda', 'x_1'])}^{chance.choice(['2', 'a', '{' + inner() + '}', r'\alpha', '{-1}'])}"
    if shape == 18:
        return chance.choice(["x^a_1", "x_1^a", r"x^\alpha_1", "a^2_b", "12^x", "0.5^2", "x^10", "x^{10}"])
    if shape < 21:
        left, right = chance.choice([("(", ")"), ("[", "]"), (r"\{", r"\}"), (r"\left(", r"\right)"), (r"\left[", r"\right]")])
        return f"{left}{inner()}{right}{chance.choice(['', '^2', '^{x}'])}"
    if shape < 23:
        name = chance.choice([r"\sin", r"\cos", r"\tan", r"\arctan", r"\ln", r"\exp", r"\operatorname{erf}", r"\mathrm{erf}"])
        return f"{name}{chance.choice(['(' + inner() + ')', r'\left(' + inner() + r'\right)', ' x', r' \theta', ' 2', '(' + inner() + ')^2'])}"
    if shape == 23:
        return rf"\sqrt{chance.choice(['{' + inner() + '}', ' x', '16 x', '2'])}"
    if shape == 24:
        left, right = chance.choice([("|", "|"), (r"\lvert ", r"\rvert"), (r"\left|", r"\right|")])
        return f"{left}{inner()}{right}{chance.choice(['', '^2'])}"
    if shape == 25:
        left, right = chance.choice([("(", ")"), (r"\{", r"\}"), (r"\left(", r"\right)")])
        return f"{chance.choice([r'\min', r'\max'])}{left}{inner()}, {inner()}{right}"
    if shape == 26:
        return "-" + inner()
    if shape == 27:
        return rf"\begin{{cases}} {inner()} & x < 0 \\ {inner()} & {chance.choice([r'x \ge 0', r'\text{otherwise}', r'0 \le x'])} \end{{cases}}"
    if shape == 28:
        # Where TeX's grouping and a reader's could part: every one must be refused or read as the page shows it.
        return chance.choice([r"{" + inner() + "}" + atom(), r"\sqrt16 x", r"1\,000", r"3\frac12", r"3\frac{1}{2}", r"2.5.5",
                              r"x^2 3", r"\frac{1}{2} 3", r"\sqrt{x}2", r"a/b c", r"a/b/c", r"e", r"e x", r"x'", r"n!"])
    return f"{inner()}{chance.choice([',', '.', r'\,', ' '])}"


SOUP = list("xyzpq0123456789+-*/^_(){}[]|=,.& ") + [
    r"\frac", r"\sqrt", r"\begin{cases}", r"\end{cases}", r"\\", r"\left", r"\right", r"\lambda", "e", r"\text{if }",
    r"\min", r"\exp", r"\mathrm{e}", r"\operatorname{erf}", r"\cdot", r"\,", r"\sin", r"\lvert", r"\rvert", r"\{", r"\}", r"\mathrm"]


def _agrees(trees: KT.Trees, renderer: M.Renderer, source: str) -> bool | None:
    """None: refused. Otherwise whether the reader's meaning is the rendering's."""

    try:
        relation = B.read_relation(source, trees=trees)
    except B.Unreadable as refused:
        assert refused.reason in B.REASONS
        return None
    mathml = renderer.mathml(source)
    assert mathml is not None, f"read, but the page refuses: {source}"
    meaning = M.right_hand_side(mathml)
    assert meaning is not None, source
    agreed = M.same_value(relation.rhs, meaning, _points(relation.rhs, meaning))
    assert agreed, (source, relation.rhs, meaning)
    return agreed


def test_whatever_reads_means_what_katex_renders(renderer):
    chance = random.Random(20261102)
    read = 0
    total = 3000
    with KT.Trees() as trees:
        for _ in range(total):
            read += _agrees(trees, renderer, "y = " + _expression(chance)) is not None
    # A differential that refuses everything proves nothing.
    assert read > total * 0.25, read


def test_whatever_reads_from_token_soup_means_what_katex_renders(renderer):
    chance = random.Random(20261103)
    read = 0
    with KT.Trees() as trees:
        for _ in range(4000):
            read += _agrees(trees, renderer, "y = " + "".join(chance.choice(SOUP) for _ in range(chance.randrange(1, 14)))) is not None
    assert read > 100, read


def test_the_reader_words_every_closed_reason():
    """The Reader drops a key it does not know, so a new reason without words would vanish from the figure."""

    from learnloop.figures import source_check as SC

    words = (APP / "src" / "screens" / "reader" / "figures" / "FigureInline.tsx").read_text(encoding="utf-8")
    # "differs" has its own state (the failed line and rebuild), never a reason's words.
    assert [reason for reason in SC.REASONS if f"  {reason}: " not in words and reason != "differs"] == []
