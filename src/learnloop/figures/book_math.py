"""Reader RW5c: code reads the book's equation (spec_reader_rw5c_checked_labels_v1 §5.3).

The closed reader of the "matches the book's equation (checked)" claim. One math
segment of a source block becomes one relation, and its right-hand side the figure
grammar's :class:`~learnloop.figures.grammar.Node` values, in three steps:

1. **The page's own markdown pipeline finds the segments** (:func:`segments`,
   :mod:`.katex_tree`): only math elements it would hand to KaTeX, and their text as it
   would hand it. No Markdown is parsed here, so a reference definition, a link title, a
   code span or an unreferenced footnote cannot hold a candidate.
2. **KaTeX parses the whole segment** (:mod:`.katex_tree`), the same KaTeX under the
   same settings as the page. If it refuses, or no engine runs, or a cap is hit, the
   segment is unreadable: what code reads is what the page shows, or nothing. No TeX is
   tokenized here. So TeX's grouping needs no rule of ours: ``x^a_1`` is ``x₁`` to the
   ``a``, ``\\sqrt16`` the root of 1 then a 6, ``2 3`` the numeral 23, and ``e^x^2`` an error.
3. **A closed translator** turns KaTeX's tree into the grammar: an allowlist of tree
   node kinds and exact symbols; anything else is unreadable with a closed reason key
   (:data:`REASONS`), which the coverage report counts (§12). No model writes any part
   of this: the figure author's quote can only point at a segment.

What remains here are the readings KaTeX cannot decide, because they are mathematics
and not TeX, each failing closed under its own key:

* ``e`` is Euler's number only as the base of a power or as ``\\mathrm{e}`` (``ambiguous_e``);
* a symbol directly before a bracket is a product only when the same symbol also
  appears elsewhere without one, or is an argument of the left-hand side
  (``application``; names are never resolved: RW2b's rule);
* ``n!`` (``factorial``), ``\\frac{d}{dx}`` and a prime (``derivative``), ``\\sin^2 x``
  (``function_power``), ``\\log`` and ``\\ln_2`` (``log_base``), ``\\sin 2x`` (``function_arg``);
* ``3\\frac{1}{2}`` is a mixed number on a page (``syntax``); ``a / b c`` and ``a / b / c``
  part books on the grouping (``ambiguous_slash``), and ``|a|b|c|`` too (``syntax``); a numeral directly
  after a factor (``x^10``, ``\\sqrt16 x``, ``x 2``) is what the page shows and rarely what its author meant (``syntax``);
* ``{a+b}c``: braces group for TeX and show nothing, so a bare brace group is not a
  grouping (``syntax``). A bracket, a fraction, a radical or an exponent shows its group;
* the rows of ``cases`` are proved to cover the real line unless the last says
  ``\\text{otherwise}``, and each condition sets one symbol against a literal that is exactly a binary64 value.

Any macro definition anywhere in the segment is unreadable (``macro_definition``), before
KaTeX is asked: KaTeX's tree would show the expansion, but no label may rest on a
definition. A definition in another segment or block cannot reach this one: the page
calls KaTeX once per math element with fresh settings (``test_rw5c_katex_tree.py`` pins it).

The left-hand side is the book's own substring, kept only when KaTeX reads that
substring alone as exactly the left of the same parse, and only from the label allowlist.

Nothing is evaluated. The translator is pure over the tree and held to the grammar's
caps (one Python frame per nesting level, bounded by :data:`~learnloop.figures.grammar.MAX_DEPTH`).
"""

from __future__ import annotations

import re
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass, field, replace
from fractions import Fraction
from typing import Any

from learnloop.figures import grammar as G
from learnloop.figures import katex_tree as KT

#: The version of this table and of the KaTeX and markdown behind it, recorded on every check row.
READER_VERSION = f"book-math-v4+katex-{KT.KATEX_VERSION}+markdown-{KT.MARKDOWN_SHA256[:12]}"

#: Every reason a candidate is unreadable, as a closed key (§5.3, §12).
REASONS = (
    "ambiguous_e", "ambiguous_slash", "application", "binom", "cases_condition", "cases_cover", "derivative",
    "engine_unavailable", "factorial", "function_arg", "function_power", "gamma", "indicator", "inexact_literal",
    "integral", "limit", "log_base", "macro_definition", "matrix", "multiple_relations", "name_collision",
    "not_equation", "not_rendered", "nth_root", "phi", "product", "relation", "reserved_name", "set", "subscript",
    "sum", "syntax", "text", "too_long", "unicode_math", "unsupported_command", "unsupported_environment",
    "unsupported_function",
)

#: Greek commands, under the canonical names ``math_text`` gives them (its GREEK
#: table): a variant is the same canonical name as its letter, which is what makes
#: ``\epsilon`` beside ``\varepsilon`` a collision.
_GREEK = {
    "alpha": "alpha", "beta": "beta", "gamma": "gamma", "delta": "delta", "epsilon": "epsilon",
    "varepsilon": "epsilon", "zeta": "zeta", "eta": "eta", "theta": "theta", "vartheta": "theta", "iota": "iota",
    "kappa": "kappa", "lambda": "lambda", "mu": "mu", "nu": "nu", "xi": "xi", "pi": "pi", "varpi": "pi",
    "rho": "rho", "varrho": "rho", "sigma": "sigma", "varsigma": "sigma", "tau": "tau", "upsilon": "upsilon",
    "phi": "phi", "varphi": "phi", "chi": "chi", "psi": "psi", "omega": "omega",
    "Delta": "Delta", "Theta": "Theta", "Lambda": "Lambda", "Xi": "Xi", "Pi": "Pi", "Sigma": "Sigma",
    "Upsilon": "Upsilon", "Psi": "Psi", "Omega": "Omega",
}
_FUNCTIONS = {r"\exp": "exp", r"\ln": "log", r"\sin": "sin", r"\cos": "cos", r"\tan": "tan", r"\arctan": "atan"}
_EXTREMES = {r"\min": "min", r"\max": "max"}
#: What each outside-the-table symbol is called in the report. Only a label: what is
#: readable is decided by the allowlists; anything else falls to ``unsupported_command``.
_LABELS = {
    r"\Phi": "phi", r"\Gamma": "gamma", r"\int": "integral", r"\iint": "integral", r"\iiint": "integral",
    r"\oint": "integral", r"\sum": "sum", r"\prod": "product", r"\lim": "limit", r"\to": "limit", r"\rightarrow": "limit",
    r"\mapsto": "limit", r"\partial": "derivative", r"\nabla": "derivative", r"\prime": "derivative",
    r"\log": "log_base", r"\lg": "log_base", r"\in": "set", r"\notin": "set", r"\cup": "set", r"\cap": "set",
    r"\subset": "set", r"\subseteq": "set", r"\mid": "set", r"\setminus": "set", r"\emptyset": "set",
    r"\approx": "relation", r"\propto": "relation", r"\sim": "relation", r"\equiv": "relation", r"\le": "relation",
    r"\leq": "relation", r"\ge": "relation", r"\geq": "relation", r"\ll": "relation", r"\gg": "relation",
    "<": "relation", ">": "relation",
}
_CONDITION_OPS = {"<": "<", ">": ">", r"\le": "<=", r"\leq": "<=", r"\ge": ">=", r"\geq": ">=",
                  r"\leqslant": "<=", r"\geqslant": ">="}
_CASE_WORDS = {"if", "for"}
_NUMBER = re.compile(r"[0-9]+(?:\.[0-9]+)?|\.[0-9]+")
#: ``\,  \:  \;  \!  \quad  \qquad``; any other kern is outside the table.
_KERNS = {(3, "mu"), (4, "mu"), (5, "mu"), (-3, "mu"), (1, "em"), (2, "em")}
_SPACES = {r"\ ", r"\nobreakspace", r"\space"}
#: Every way TeX defines a macro; a control word ends at anything but a letter or ``@``, as in KaTeX's lexer.
_MACRO_DEFINITION = re.compile(
    r"\\(?:def|gdef|edef|xdef|let|futurelet|global|long|newcommand|renewcommand|providecommand)(?![A-Za-z@])")
#: What a left-hand side may hold: it becomes a label, and must not paint, hide, link or move anything.
_LABEL_NODES = frozenset({"accent", "atom", "font", "genfrac", "kern", "leftright", "mathord", "op", "operatorname",
                          "ordgroup", "spacing", "sqrt", "supsub", "text", "textord"})
#: Label nodes drawn as one term whatever they hold: they bracket, stack or cover their contents, or are one name or a gap.
_ONE_TERM_NODES = frozenset({"accent", "genfrac", "kern", "leftright", "mathord", "op", "operatorname", "spacing", "sqrt"})


class Unreadable(ValueError):
    """A segment outside the table; ``reason`` is one key of :data:`REASONS`."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


@dataclass(frozen=True)
class Segment:
    """One math element the page shows for a block's text. ``latex`` is what the page gives
    KaTeX. ``start``/``end`` delimit its place in the text (the whole element, delimiters
    too, when a container's markers interrupt it). ``display`` is how the page renders it."""

    latex: str
    start: int
    end: int
    display: bool = False


@dataclass(frozen=True)
class Relation:
    """A read equation. ``lhs`` is the book's own left-hand side as a substring
    of the segment; ``args`` the symbols of a ``name(args)`` left-hand side
    (empty otherwise); ``tokens`` each canonical symbol's LaTeX."""

    latex: str
    lhs: str
    rhs: G.Node
    args: tuple[str, ...] = ()
    symbols: frozenset[str] = frozenset()
    tokens: dict[str, str] = field(default_factory=dict)
    #: Whether ``lhs`` needs grouping as an operand (:func:`_compound`). Grouped unless read otherwise.
    lhs_compound: bool = True


# ---------------------------------------------------------------------------
# Segments
# ---------------------------------------------------------------------------

def segments(text: str, *, trees: KT.Trees | None = None) -> list[Segment]:
    """The equations the page shows for a block's text (§5.2), found by the page's own
    pipeline (:meth:`.katex_tree.Trees.page_math`), or :class:`Unreadable`. ``trees``: the
    check's loaded engine. ``bookMathRenderCorpus.json``'s ``blocks`` pin them against
    the real ``MarkdownMath``. Unicode math is never one, nor a block with no math element."""

    source = str(text or "")
    # All the page's math starts from one of these (normalizeMathDelimiters makes \[ and \( into $), so a block without any costs no engine.
    if "$" not in source and "\\[" not in source and "\\(" not in source:
        return []
    if trees is None:
        with KT.Trees() as own:
            return segments(source, trees=own)
    try:
        found = trees.page_math(source)
    except KT.TreeRefused as refused:
        raise Unreadable(refused.reason) from refused
    return [Segment(str(item["latex"]), int(item["start"]), int(item["end"]), bool(item["display"])) for item in found]


# ---------------------------------------------------------------------------
# KaTeX's tree as a flat run of items
# ---------------------------------------------------------------------------

Tree = Mapping[str, Any]


@dataclass(frozen=True)
class _Item:
    """One thing in reading order. KaTeX's list is flat where the source was, and a
    script belongs to the node before it: ``(x)^2`` is ``(``, ``x``, ``)`` with a
    superscript, and ``12^x`` is ``1``, then ``2`` with one. So numerals are joined here,
    and a script stays on its item for the factor it closes."""

    kind: str  # num | sym | op | rel | open | close | bar | func | extreme | frac | sqrt | const | cases | text | punct | bang
    text: str = ""
    node: Tree | None = None
    sup: Tree | None = None
    sub: Tree | None = None
    absolute: bool = False


def _body(node: Tree) -> Sequence[Tree]:
    return node.get("body") or () if node.get("type") == "ordgroup" else (node,)


def _word(nodes: Sequence[Tree]) -> str | None:
    """The letters of ``\\mathrm{...}`` or ``\\operatorname{...}``, if letters are all it holds."""

    kept = [node for node in nodes if node.get("type") != "kern"]
    if any(node.get("type") not in ("mathord", "textord") for node in kept):
        return None
    return "".join(str(node.get("text")) for node in kept)


#: The allowlist of KaTeX's atoms, by family and exact symbol (``_CONDITION_OPS`` holds the relations).
_ATOMS = {
    ("bin", "+"): _Item("op", "+"), ("bin", "-"): _Item("op", "-"), ("bin", "*"): _Item("op", "*"),
    ("bin", r"\cdot"): _Item("op", "*"), ("bin", r"\times"): _Item("op", "*"), ("punct", ","): _Item("punct", ","),
    ("open", "("): _Item("open", ")"), ("open", "["): _Item("open", "]"), ("open", r"\{"): _Item("open", r"\}"),
    ("open", r"\lvert"): _Item("open", r"\rvert", absolute=True), ("close", ")"): _Item("close", ")"),
    ("close", "]"): _Item("close", "]"), ("close", r"\}"): _Item("close", r"\}"), ("close", r"\rvert"): _Item("close", r"\rvert"),
    ("close", "!"): _Item("bang", "!"),
}
#: Tree nodes outside the table, by what the report calls them (the default is ``unsupported_command``).
_NODE_REASONS = {"ordgroup": "syntax", "cr": "syntax", "htmlmathml": "relation"}


def _is_table_space(node: Tree) -> bool:
    dimension = node.get("dimension") or {}
    return node.get("text") in _SPACES or (dimension.get("number"), dimension.get("unit")) in _KERNS


def _refuse_symbol(text: str) -> Unreadable:
    return Unreadable(_LABELS.get(text, "unsupported_command"))


def _items(nodes: Sequence[Tree]) -> list[_Item]:
    out: list[_Item] = []
    gap = False
    for node in nodes:
        kind = node.get("type")
        if kind in ("kern", "spacing"):
            if not _is_table_space(node):
                raise Unreadable("unsupported_command")
            gap = True
            continue
        base, sup, sub = node, None, None
        if kind == "supsub":
            base, sup, sub = node.get("base"), node.get("sup"), node.get("sub")
            if base is None:
                raise Unreadable("syntax")
        made = _base_items(base)
        if sup is not None or sub is not None:
            last = made[-1]
            # A script on +, =, a comma or \text: the page shows it, and no reading has a place for it.
            if last.kind in ("op", "rel", "punct", "bang", "text", "extreme"):
                raise Unreadable("syntax")
            if last.kind == "func":
                raise Unreadable("function_power" if sup is not None else "log_base")
            if sub is not None and last.kind != "sym":
                raise Unreadable("subscript")
            made[-1] = replace(last, sup=sup, sub=sub)
        if len(made) == 1 and made[0].kind == "num" and not gap and out and out[-1].kind == "num" and out[-1].sup is None:
            # TeX's digits are one token each; the page's numeral is the run (and a script is on its last digit).
            out[-1] = _Item("num", out[-1].text + made[0].text, sup=made[0].sup)
        else:
            out.extend(made)
        gap = False
    for item in out:
        if item.kind == "num" and not _NUMBER.fullmatch(item.text):
            raise Unreadable("syntax")
    return out


def _base_items(base: Tree) -> list[_Item]:
    kind = base.get("type")
    text = str(base.get("text") or "")
    if kind == "textord":
        if text.isdigit() or text == ".":
            return [_Item("num", text)]
        if text == "/":
            return [_Item("op", "/")]
        if text == "|":
            return [_Item("bar", "|")]
        if text[1:] in _GREEK:
            return [_Item("sym", text)]
        raise _refuse_symbol(text)
    if kind == "mathord":
        if (len(text) == 1 and text.isascii() and text.isalpha()) or text[1:] in _GREEK:
            return [_Item("sym", text)]
        raise _refuse_symbol(text)
    if kind == "atom":
        return [_atom_item(base, text)]
    if kind == "leftright":
        return _leftright_items(base)
    if kind == "op":
        name = str(base.get("name") or "")
        if name in _FUNCTIONS:
            return [_Item("func", _FUNCTIONS[name])]
        if name in _EXTREMES:
            return [_Item("extreme", _EXTREMES[name])]
        raise _refuse_symbol(name)
    if kind == "operatorname":
        word = _word(base.get("body") or ())
        if word in ("limsup", "liminf"):
            raise Unreadable("limit")
        if word != "erf":
            raise Unreadable("unsupported_function")
        return [_Item("func", "erf")]
    if kind == "font":
        return [_font_item(base)]
    if kind == "genfrac":
        if not base.get("hasBarLine"):
            raise Unreadable("binom" if base.get("leftDelim") else "unsupported_command")
        if base.get("leftDelim") or base.get("rightDelim"):
            raise Unreadable("unsupported_command")
        return [_Item("frac", node=base)]
    if kind == "sqrt":
        if base.get("index") is not None:
            raise Unreadable("nth_root")
        return [_Item("sqrt", node=base)]
    if kind == "text":
        return [_Item("text", node=base)]
    if kind == "array":
        raise Unreadable("unsupported_environment" if base.get("colSeparationType") or base.get("addJot") else "matrix")
    raise Unreadable(_NODE_REASONS.get(str(kind), "unsupported_command"))


def _atom_item(base: Tree, text: str) -> _Item:
    family = base.get("family")
    found = _ATOMS.get((family, text))
    if found is not None:
        return found
    if family == "rel" and text in _CONDITION_OPS:
        return _Item("rel", text)
    raise _refuse_symbol(text) if text in _LABELS else Unreadable("syntax" if family in ("punct", "rel") else "unsupported_command")


def _leftright_items(base: Tree) -> list[_Item]:
    left, right = base.get("left"), base.get("right")
    body = base.get("body") or ()
    arrays = [node for node in body if node.get("type") == "array"]
    if arrays:
        if left != r"\{" or right != "." or len(body) != 1:
            raise Unreadable("matrix" if left in ("(", "[", "|", r"\|") else "unsupported_environment")
        columns = arrays[0].get("cols") or ()
        if arrays[0].get("colSeparationType") or [column.get("align") for column in columns] != ["l", "l"]:
            raise Unreadable("unsupported_environment")
        return [_Item("cases", node=arrays[0])]
    closers = {"(": ")", "[": "]", r"\{": r"\}", "|": "|", r"\lvert": r"\rvert"}
    if closers.get(str(left)) != right:
        raise Unreadable("syntax")
    return [_Item("open", str(right), absolute=left in ("|", r"\lvert")), *_items(body),
            _Item("close", str(right))]


def _font_item(base: Tree) -> _Item:
    font, body = base.get("font"), base.get("body") or {}
    if font == "mathbb":
        raise Unreadable("indicator")
    if font != "mathrm":
        raise Unreadable("unsupported_command")
    word = _word(_body(body))
    if word == "e":
        return _Item("const", "e")
    if word == "erf":
        return _Item("func", "erf")
    if word == "d":
        raise Unreadable("derivative")
    raise Unreadable("unsupported_command")


def _starts_with_d(node: Tree) -> bool:
    """Whether a fraction's side begins with a differential's ``d``."""

    first = next(iter(_body(node)), None)
    if first is None:
        return False
    if first.get("type") == "supsub" and first.get("base") is not None:
        first = first["base"]
    if first.get("type") == "font":
        return _word(_body(first.get("body") or {})) == "d"
    return first.get("type") == "mathord" and first.get("text") == "d"


# ---------------------------------------------------------------------------
# The right-hand side
# ---------------------------------------------------------------------------

def _dyadic_text(value: Fraction) -> str:
    """A dyadic rational's exact decimal, which reads back as the same fraction."""

    sign = "-" if value < 0 else ""
    value = abs(value)
    denominator = value.denominator
    digits = 0
    while denominator > 1:
        denominator >>= 1
        digits += 1
    if not digits:
        return f"{sign}{value.numerator}"
    scaled = value.numerator * 5 ** digits
    text = str(scaled).rjust(digits + 1, "0")
    return f"{sign}{text[:-digits]}.{text[-digits:]}"


def binary64_exact(text: str) -> bool:
    """Whether a decimal's exact value is a binary64 value: no made-up bound,
    no ``Decimal`` context (§6.1): 0, 1, 0.5, 0.375, never 0.3."""

    try:
        value = float(text)
        return Fraction(text) == Fraction(value)
    except (ValueError, OverflowError, ZeroDivisionError):
        return False


Rows = list[tuple[G.Node, G.Node | None, tuple[str, list[tuple[str, Fraction]]] | None]]


class _Reader:
    def __init__(self, items: list[_Item], *, args: tuple[str, ...] = ()) -> None:
        self.items = items
        self.position = 0
        self.nodes = 0
        self.bars = 0
        self.args = set(args)
        #: canonical name -> the LaTeX spellings the book uses for it.
        self.spellings: dict[str, set[str]] = {}
        self.first: dict[str, str] = {}
        self.applied: set[str] = set()
        self.plain: set[str] = set()

    # -- helpers ---------------------------------------------------------------
    def peek(self, offset: int = 0) -> _Item | None:
        index = self.position + offset
        return self.items[index] if index < len(self.items) else None

    def take(self) -> _Item:
        item = self.peek()
        if item is None:
            raise Unreadable("syntax")
        self.position += 1
        return item

    def closes(self, kind: str, text: str) -> _Item:
        item = self.take()
        if item.kind != kind or item.text != text:
            raise self.leftover(item)
        return item

    def node(self, kind: str, depth: int, **values: object) -> G.Node:
        self.nodes += 1
        if self.nodes > G.MAX_NODES or depth > G.MAX_DEPTH:
            raise Unreadable("too_long")
        return G.Node(kind, **values)  # type: ignore[arg-type]

    @staticmethod
    def leftover(item: _Item | None) -> Unreadable:
        """What stopped a read: an item the grammar has no place for here."""

        if item is not None and item.kind == "text":
            return Unreadable("text")
        if item is not None and item.kind == "bang":
            return Unreadable("factorial")
        return Unreadable("syntax")

    def inner(self, node: Tree | Sequence[Tree], depth: int) -> G.Node:
        """A group the page shows as one (an exponent, a fraction's side, a radicand, a row's cell)."""

        if depth > G.MAX_DEPTH:
            raise Unreadable("too_long")
        items = _items(_body(node) if isinstance(node, Mapping) else node)
        saved = self.items, self.position, self.bars
        self.items, self.position, self.bars = items, 0, 0
        value = self.expression(depth + 1)
        if self.position != len(self.items):
            raise self.leftover(self.peek())
        self.items, self.position, self.bars = saved
        return value

    # -- expressions ------------------------------------------------------------
    def expression(self, depth: int) -> G.Node:
        if depth > G.MAX_DEPTH:
            raise Unreadable("too_long")
        following = self.peek()
        if following is not None and following.kind == "op" and following.text == "-":
            self.take()
            node = self.node("neg", depth, args=(self.term(depth + 1),))
        else:
            node = self.term(depth + 1)
        while (following := self.peek()) is not None and following.kind == "op" and following.text in "+-":
            self.take()
            node = self.node("bin", depth, op=following.text, args=(node, self.term(depth + 1)))
        return node

    def term(self, depth: int) -> G.Node:
        barred = (first := self.peek()) is not None and first.kind == "bar"
        node = self.factor(depth + 1)
        while (item := self.peek()) is not None:
            if item.kind == "op" and item.text == "*":
                self.take()
                node = self.node("bin", depth, op="*", args=(node, self.factor(depth + 1)))
            elif item.kind == "op" and item.text == "/":
                self.take()
                node = self.node("bin", depth, op="/", args=(node, self.factor(depth + 1)))
                following = self.peek()
                # a / b c and a / b / c: books part on the grouping, so neither is read.
                if following is not None and (self.starts_factor(following) or (following.kind == "op" and following.text == "/")):
                    raise Unreadable("ambiguous_slash")
            elif self.starts_factor(item):
                # x^10, \sqrt16 x, x 2, 1\,000: what the page shows, and rarely what its author meant.
                if item.kind == "num":
                    raise Unreadable("syntax")
                # 3\frac{1}{2} on a page is a mixed number, 3.5; the product it would parse as is 1.5.
                if item.kind == "frac" and self.items[self.position - 1].kind == "num" and None not in _numeric_sides(item):
                    raise Unreadable("syntax")
                # |a|b|c| is |a|·b·|c| or |a·|b|·c|: the page does not say which.
                if item.kind == "bar" and barred:
                    raise Unreadable("syntax")
                barred = barred or item.kind == "bar"
                node = self.node("bin", depth, op="*", args=(node, self.factor(depth + 1)))
            else:
                return node
        return node

    def starts_factor(self, item: _Item) -> bool:
        if item.kind == "text":
            raise Unreadable("text")
        if item.kind == "bang":
            raise Unreadable("factorial")
        if item.kind == "bar":
            return self.bars == 0
        return item.kind in ("num", "sym", "open", "func", "extreme", "frac", "sqrt", "const", "cases")

    def factor(self, depth: int) -> G.Node:
        if depth > G.MAX_DEPTH:
            raise Unreadable("too_long")
        base, sup = self.atom(depth + 1)
        if sup is not None:
            base = self.node("bin", depth, op="^", args=(base, self.inner(sup, depth + 1)))
        return base

    def atom(self, depth: int) -> tuple[G.Node, Tree | None]:
        """A factor before its power, and the superscript KaTeX put on its last node."""

        item = self.take()
        kind = item.kind
        if kind == "num":
            if float(item.text) == float("inf"):
                raise Unreadable("too_long")
            return self.node("num", depth, text=item.text, value=float(item.text)), item.sup
        if kind == "sym":
            return self.symbol(item, depth)
        if kind == "const":
            if item.sup is not None:
                return self.node("call", depth, text="exp", args=(self.inner(item.sup, depth + 1),)), None
            return self.node("name", depth, text="e"), None
        if kind == "open":
            return self.group(item, depth)
        if kind == "bar":
            if self.bars or item.sup is not None:
                raise Unreadable("syntax")
            self.bars += 1
            inner = self.expression(depth + 1)
            self.bars -= 1
            return self.node("call", depth, text="abs", args=(inner,)), self.closes("bar", "|").sup
        if kind == "frac":
            return self.fraction(item, depth), item.sup
        if kind == "sqrt":
            assert item.node is not None
            return self.node("call", depth, text="sqrt", args=(self.inner(item.node["body"], depth + 1),)), item.sup
        if kind == "func":
            return self.function(item, depth)
        if kind == "extreme":
            return self.extreme(item, depth)
        if kind == "cases":
            return self.cases(item, depth), item.sup
        raise self.leftover(item)

    def symbol(self, item: _Item, depth: int) -> tuple[G.Node, Tree | None]:
        raw = item.text
        canonical = _GREEK[raw[1:]] if raw.startswith("\\") else raw
        latex = raw
        if item.sub is not None:
            sub = _body(item.sub)
            first = sub[0] if len(sub) == 1 else {}
            letter = str(first.get("text") or "")
            if first.get("type") not in ("mathord", "textord") or len(letter) != 1 or not (letter.isascii() and letter.isalnum()):
                raise Unreadable("subscript")
            canonical += letter
            latex = f"{raw}_{{{letter}}}"
        elif raw == "e":
            if item.sup is None:
                raise Unreadable("ambiguous_e")
            return self.node("call", depth, text="exp", args=(self.inner(item.sup, depth + 1),)), None
        if not (canonical == "pi" and raw == r"\pi"):
            if canonical in G.RESERVED or not G.is_name(canonical):
                raise Unreadable("reserved_name")
            known = self.spellings.setdefault(canonical, set())
            known.add(latex)
            if len(known) > 1:
                raise Unreadable("name_collision")
            self.first.setdefault(canonical, latex)
        following = self.peek()
        applied = following is not None and following.kind == "open" and not following.absolute
        (self.applied if applied else self.plain).add(canonical)
        return self.node("name", depth, text=canonical), item.sup

    def group(self, opening: _Item, depth: int) -> tuple[G.Node, Tree | None]:
        if opening.sup is not None:
            raise Unreadable("syntax")
        saved, self.bars = self.bars, 0
        inner = self.expression(depth + 1)
        self.bars = saved
        closing = self.closes("close", opening.text)
        if opening.absolute:
            inner = self.node("call", depth, text="abs", args=(inner,))
        return inner, closing.sup

    def fraction(self, item: _Item, depth: int) -> G.Node:
        assert item.node is not None
        numerator, denominator = item.node["numer"], item.node["denom"]
        # \frac{d}{dx}, \frac{dy}{dx}: a derivative, never the product it would parse as.
        if _starts_with_d(numerator) and _starts_with_d(denominator):
            raise Unreadable("derivative")
        return self.node("bin", depth, op="/", args=(self.inner(numerator, depth + 1), self.inner(denominator, depth + 1)))

    def function(self, item: _Item, depth: int) -> tuple[G.Node, Tree | None]:
        """``\\sin(u)``, or a bare one-token argument with nothing juxtaposed after it."""

        argument = self.peek()
        if argument is None:
            raise Unreadable("function_arg")
        if argument.kind == "open" and not argument.absolute:
            self.take()
            inner, sup = self.group(argument, depth + 1)
            return self.node("call", depth, text=item.text, args=(inner,)), sup
        if argument.kind not in ("num", "sym") or argument.sup is not None:
            raise Unreadable("function_arg")
        inner = self.atom(depth + 1)[0]
        following = self.peek()
        if following is not None and self.starts_factor(following) and following.kind != "func":
            raise Unreadable("function_arg")
        return self.node("call", depth, text=item.text, args=(inner,)), None

    def extreme(self, item: _Item, depth: int) -> tuple[G.Node, Tree | None]:
        opening = self.take()
        if opening.kind != "open" or opening.absolute:
            raise Unreadable("syntax")
        saved, self.bars = self.bars, 0
        args = [self.expression(depth + 1)]
        while (following := self.peek()) is not None and following.kind == "punct":
            self.take()
            args.append(self.expression(depth + 1))
        self.bars = saved
        closing = self.closes("close", opening.text)
        low, high = G.FUNCTIONS[item.text]
        if len(args) < low or (high is not None and len(args) > high):
            raise Unreadable("syntax")
        return self.node("call", depth, text=item.text, args=tuple(args)), closing.sup

    # -- cases -----------------------------------------------------------------
    def cases(self, item: _Item, depth: int) -> G.Node:
        assert item.node is not None
        rows: Rows = []
        for row in item.node.get("body") or ():
            # A row with no condition column names no condition: only the word
            # "otherwise" may stand for the rest of the line.
            if len(row) != 2:
                raise Unreadable("cases_cover")
            value = self.inner(_without_end_punctuation(_cell(row[0])), depth + 1)
            condition, shape = self.condition(_cell(row[1]), depth + 1)
            rows.append((value, condition, shape))
        if not rows:
            raise Unreadable("cases_cover")
        return self.cases_node(rows, depth)

    def condition(self, nodes: Sequence[Tree], depth: int) -> tuple[G.Node | None, tuple[str, list[tuple[str, Fraction]]] | None]:
        """A condition column: ``\\text{otherwise}`` (None), or one symbol
        against exact literals, an optional ``\\text{if }`` before it."""

        saved = self.items, self.position
        self.items, self.position = _items(_without_end_punctuation(nodes)), 0
        try:
            first = self.peek()
            if first is not None and first.kind == "text":
                assert first.node is not None
                self.take()
                words = _text_words(first.node)
                if words == "otherwise" and self.peek() is None:
                    return None, None
                if words not in _CASE_WORDS:
                    raise Unreadable("text")
            chain: list[object] = [self.condition_side()]
            ops: list[str] = []
            while (item := self.peek()) is not None and item.kind == "rel":
                self.take()
                ops.append(_CONDITION_OPS[item.text])
                chain.append(self.condition_side())
            if self.peek() is not None:
                raise self.leftover(self.peek()) if self.peek().kind in ("text", "bang") else Unreadable("cases_condition")  # type: ignore[union-attr]
            if len(chain) not in (2, 3):
                raise Unreadable("cases_condition")
            pairs: list[tuple[str, Fraction]]
            if len(chain) == 3:
                low, symbol, high = chain
                if not (isinstance(symbol, str) and isinstance(low, Fraction) and isinstance(high, Fraction)):
                    raise Unreadable("cases_condition")
                if ops[0] not in ("<", "<=") or ops[1] not in ("<", "<="):
                    raise Unreadable("cases_condition")
                pairs = [(_flip(ops[0]), low), (ops[1], high)]
            else:
                left, right = chain
                if isinstance(left, str) and isinstance(right, Fraction):
                    symbol, pairs = left, [(ops[0], right)]
                elif isinstance(left, Fraction) and isinstance(right, str):
                    symbol, pairs = right, [(_flip(ops[0]), left)]
                else:
                    raise Unreadable("cases_condition")
            compared = [self.node("cmp", depth, op=op, args=(self.node("name", depth, text=symbol),
                                                             self.literal_node(value, depth))) for op, value in pairs]
            node = compared[0] if len(compared) == 1 else self.node("and", depth, args=tuple(compared))
            return node, (symbol, pairs)
        finally:
            self.items, self.position = saved

    def condition_side(self) -> object:
        item = self.take() if self.peek() is not None else None
        if item is None:
            raise Unreadable("cases_condition")
        sign = 1
        if item.kind == "op" and item.text == "-":
            sign = -1
            item = self.take() if self.peek() is not None else None
            if item is None:
                raise Unreadable("cases_condition")
        if item.sup is not None:
            raise Unreadable("cases_condition")
        if item.kind == "num":
            if not binary64_exact(item.text):
                raise Unreadable("inexact_literal")
            return sign * Fraction(item.text)
        if item.kind == "frac":
            top, bottom = _numeric_sides(item)
            if top is None or not bottom:
                raise Unreadable("cases_condition")
            value = top / bottom
            if Fraction(float(value)) != value:
                raise Unreadable("inexact_literal")
            return sign * value
        if sign < 0 or item.kind != "sym":
            raise Unreadable("cases_condition")
        return self.symbol(item, 0)[0].text

    def literal_node(self, value: Fraction, depth: int) -> G.Node:
        text = _dyadic_text(abs(value))
        literal = self.node("num", depth, text=text, value=float(abs(value)))
        return self.node("neg", depth, args=(literal,)) if value < 0 else literal

    def cases_node(self, rows: Rows, depth: int) -> G.Node:
        """``piecewise``: the rows proved not to overlap, and to cover the real
        line unless an "otherwise" row ends them (§5.3; the interval method of §6.3)."""

        otherwise = rows[-1][1] is None
        conditioned = rows[:-1] if otherwise else rows
        if any(row[1] is None for row in conditioned) or not conditioned:
            raise Unreadable("cases_cover")
        symbols = {row[2][0] for row in conditioned if row[2] is not None}
        if len(symbols) != 1:
            raise Unreadable("cases_condition")
        cuts = sorted({value for row in conditioned if row[2] is not None for _op, value in row[2][1]})
        points = [cuts[0] - 1, *cuts, *[(left + right) / 2 for left, right in zip(cuts, cuts[1:])], cuts[-1] + 1]
        for point in points:
            holds = sum(1 for row in conditioned if row[2] is not None and all(
                _compare(point, op, value) for op, value in row[2][1]))
            if holds > 1 or (not otherwise and holds != 1):
                raise Unreadable("cases_cover")
        args: list[G.Node] = []
        branches = conditioned if otherwise else conditioned[:-1]
        for value, condition, _shape in branches:
            args += [condition, value]  # type: ignore[list-item]
        args.append(rows[-1][0])
        return self.node("piecewise", depth, args=tuple(args))


def _numeric_side(node: Tree) -> Fraction | None:
    """One side of a fraction as a number, when it is one numeral."""

    try:
        found = _items(_body(node))
    except Unreadable:
        return None
    return Fraction(found[0].text) if len(found) == 1 and found[0].kind == "num" and found[0].sup is None else None


def _numeric_sides(item: _Item) -> tuple[Fraction | None, Fraction | None]:
    assert item.node is not None
    return _numeric_side(item.node["numer"]), _numeric_side(item.node["denom"])


def _cell(cell: Tree) -> Sequence[Tree]:
    """A cell of an array: KaTeX wraps its contents in a style and a group."""

    inner = cell.get("body") or ()
    if cell.get("type") != "styling" or len(inner) != 1 or inner[0].get("type") != "ordgroup":
        raise Unreadable("syntax")
    return inner[0].get("body") or ()


def _text_words(node: Tree) -> str:
    """A ``\\text{...}``'s words: its characters as KaTeX lists them."""

    letters = []
    for child in node.get("body") or ():
        if child.get("type") == "spacing":
            letters.append(" ")
        elif child.get("type") in ("textord", "mathord"):
            letters.append(str(child.get("text")))
        else:
            return "?"
    return " ".join("".join(letters).split()).rstrip(",.:").strip()


def _without_end_punctuation(nodes: Sequence[Tree]) -> Sequence[Tree]:
    """Without the ``,`` or ``.`` a sentence or a row ends on."""

    while nodes and (_is_atom(nodes[-1], "punct", ",") or (nodes[-1].get("type") == "textord" and nodes[-1].get("text") == ".")):
        nodes = nodes[:-1]
    return nodes


def _flip(op: str) -> str:
    return {"<": ">", "<=": ">=", ">": "<", ">=": "<="}[op]


def _compare(point: Fraction, op: str, value: Fraction) -> bool:
    return {"<": point < value, "<=": point <= value, ">": point > value, ">=": point >= value}[op]


# ---------------------------------------------------------------------------
# One relation
# ---------------------------------------------------------------------------

def _is_atom(node: Tree, family: str, text: str | None = None) -> bool:
    return node.get("type") == "atom" and node.get("family") == family and (text is None or node.get("text") == text)


def _split_relation(nodes: Sequence[Tree]) -> tuple[int, int]:
    """Where the one top-level ``=`` or ``:=`` of KaTeX's list is, as ``(lhs_end,
    rhs_start)`` indices: a segment must hold exactly one. A bracket's contents are
    in the same list, so its ``=`` (``P(X = k)``) is counted out by depth."""

    depth = 0
    found: list[tuple[int, int]] = []
    other: str | None = None
    for index, node in enumerate(nodes):
        current = node.get("base") if node.get("type") == "supsub" else node
        if current is None:
            continue
        if _is_atom(current, "open"):
            depth += 1
        elif _is_atom(current, "close") and current.get("text") not in ("!", "?"):
            depth -= 1
        elif depth == 0 and _is_atom(current, "rel", "="):
            colon = index > 0 and _is_atom(nodes[index - 1], "rel", ":")
            found.append((index - 1 if colon else index, index + 1))
        elif depth == 0 and _is_atom(current, "rel") and _LABELS.get(str(current.get("text")), "relation") == "relation" \
                and current.get("text") != ":":
            other = other or "relation"
        elif depth == 0 and current.get("type") == "htmlmathml":
            other = other or "relation"
    if other is not None:
        raise Unreadable(other)
    if not found:
        raise Unreadable("not_equation")
    if len(found) > 1:
        raise Unreadable("multiple_relations")
    return found[0]


def _compound(nodes: Sequence[Tree]) -> bool:
    """Whether a left-hand side, in KaTeX's list, is more than one term to a reader: an operator written
    before it (``\\sum``, ``\\int``) would seem to reach only its first. A binary sign, a relation or
    a comma outside every bracket makes it so, as does a slash or a spaced word; braces and fonts draw
    nothing, so they are looked through. A kind not named here is grouped: an extra pair of brackets
    says nothing false."""

    depth = 0
    for node in nodes:
        current = node.get("base") if node.get("type") == "supsub" else node
        if current is None:
            continue
        kind = current.get("type")
        if kind == "atom":
            family = current.get("family")
            if family == "open":
                depth += 1
            elif family == "close":
                # n! and n? close nothing (as in _split_relation).
                if current.get("text") not in ("!", "?"):
                    depth -= 1
                if depth < 0:
                    return True
            elif depth == 0:
                return True
        elif depth > 0 or kind in _ONE_TERM_NODES:
            continue
        elif kind == "textord":
            if current.get("text") == "/":
                return True
        elif kind == "ordgroup":
            if _compound(current.get("body") or ()):
                return True
        elif kind == "font":
            if _compound((current["body"],)):
                return True
        elif kind == "text":
            if any(item.get("type") == "spacing" for item in current.get("body") or ()):
                return True
        else:
            return True
    return depth != 0


def _lhs_args(nodes: Sequence[Tree]) -> tuple[tuple[str, ...], dict[str, set[str]], dict[str, str]]:
    """The symbols of a ``name(args)`` left-hand side, with how the book spells
    them; empty for ``P(X = k)``, ``E[X]`` or a bare name."""

    nothing: tuple[tuple[str, ...], dict[str, set[str]], dict[str, str]] = ((), {}, {})
    kept = [node for node in nodes if node.get("type") not in ("kern", "spacing")]
    if not kept:
        return nothing
    if kept[-1].get("type") == "leftright" and kept[-1].get("left") == "(" and kept[-1].get("right") == ")":
        head, inner = kept[:-1], kept[-1].get("body") or ()
    else:
        opening = next((index for index, node in enumerate(kept) if _is_atom(node, "open", "(")), None)
        if opening is None or not _is_atom(kept[-1], "close", ")"):
            return nothing
        head, inner = kept[:opening], kept[opening + 1:-1]
    if not head or not all(node.get("type") in ("mathord", "op", "supsub", "textord") and "sup" not in node for node in head):
        return nothing
    try:
        items = _items(inner)
        # sym, sym, sym: each argument one symbol, no script but its subscript.
        if len(items) % 2 == 0 or any(item.kind != ("punct" if index % 2 else "sym") or item.sup is not None
                                      for index, item in enumerate(items)):
            return nothing
        reader = _Reader(items)
        args = []
        while (following := reader.peek()) is not None:
            if following.kind == "punct":
                reader.take()
            else:
                args.append(reader.symbol(reader.take(), 0)[0].text)
    except Unreadable:
        return nothing
    return tuple(args), reader.spellings, reader.first


def _walk(value: Any) -> Iterator[Tree]:
    """Every node under ``value``, whatever field holds it."""

    if isinstance(value, Mapping):
        if "type" in value:
            yield value
        for child in value.values():
            yield from _walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk(child)


def _without_places(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _without_places(child) for key, child in value.items() if key != "at"}
    if isinstance(value, list):
        return [_without_places(child) for child in value]
    return value


def _parse(trees: KT.Trees, source: str, display: bool) -> list[Tree]:
    try:
        return trees.parse(source, display=display)
    except KT.TreeRefused as refused:
        raise Unreadable(refused.reason) from refused


def _left_hand_side(source: str, tree: Sequence[Tree], lhs_end: int, *, trees: KT.Trees, display: bool) -> str:
    """The book's own substring, kept only when KaTeX reads it alone as the left of this parse."""

    start = (tree[lhs_end].get("at") or (None,))[0]
    if start is None:
        raise Unreadable("syntax")
    lhs = source[:start].strip()
    left = tree[:lhs_end]
    for node in _walk(list(left)):
        if node.get("type") not in _LABEL_NODES or (node.get("type") == "kern" and not _is_table_space(node)):
            raise Unreadable("unsupported_command")
    if _without_places(_parse(trees, lhs, display)) != _without_places(list(left)):
        raise Unreadable("syntax")
    return lhs


def read_relation(latex: str, *, display: bool = False, trees: KT.Trees | None = None) -> Relation:
    """One math segment read as one relation, or :class:`Unreadable`. ``trees``: the
    check's loaded engine (one is opened for this call without it)."""

    if trees is None:
        with KT.Trees() as own:
            return read_relation(latex, display=display, trees=own)
    source = str(latex or "")
    if len(source) > G.MAX_EXPR_CHARS:
        raise Unreadable("too_long")
    if not source.isascii():
        raise Unreadable("unicode_math")
    # A comment ends at a newline, and the page's markdown may have made that a space.
    if "%" in source:
        raise Unreadable("syntax")
    if _MACRO_DEFINITION.search(source):
        raise Unreadable("macro_definition")
    try:
        return _translate(source, _parse(trees, source, display), trees=trees, display=display)
    except RecursionError as exc:
        raise Unreadable("too_long") from exc


def _translate(source: str, tree: Sequence[Tree], *, trees: KT.Trees, display: bool) -> Relation:
    nodes = _without_end_punctuation(tree)
    if not nodes:
        raise Unreadable("not_equation")
    lhs_end, rhs_start = _split_relation(nodes)
    if rhs_start >= len(nodes) or all(node.get("type") in ("kern", "spacing") for node in nodes[:lhs_end]):
        raise Unreadable("not_equation")
    lhs = _left_hand_side(source, nodes, lhs_end, trees=trees, display=display)
    args, spellings, first = _lhs_args(nodes[:lhs_end])
    reader = _Reader(_items(nodes[rhs_start:]), args=args)
    # \varepsilon on the left and \epsilon on the right are two book symbols sharing one name.
    reader.spellings = {name: set(spelled) for name, spelled in spellings.items()}
    reader.first = dict(first)
    rhs = reader.expression(1)
    if reader.position != len(reader.items):
        raise reader.leftover(reader.peek())
    # Names are never resolved: g(1-p) is a product only when g also stands alone.
    if any(name not in reader.plain and name not in reader.args for name in reader.applied):
        raise Unreadable("application")
    if G.node_count(rhs, {}) > G.MAX_EXPANDED_NODES:
        raise Unreadable("too_long")
    return Relation(latex=source, lhs=lhs, rhs=rhs, args=args, symbols=frozenset(G.free_names(rhs)),
                    tokens=dict(reader.first), lhs_compound=_compound(nodes[:lhs_end]))


__all__ = [
    "READER_VERSION",
    "REASONS",
    "Relation",
    "Segment",
    "Unreadable",
    "binary64_exact",
    "read_relation",
    "segments",
]
