"""Reader RW5c: code reads the book's equation (spec_reader_rw5c_checked_labels_v1 §5.3).

The closed reader of the "matches the book's equation (checked)" claim: one
math segment of a source block becomes one relation, and its right-hand side
becomes the figure grammar's :class:`~learnloop.figures.grammar.Node` values.
Nothing else is ever read: every construct outside the table below makes the
candidate unreadable with a closed reason key (:data:`REASONS`), which the
coverage report counts (§12). No model writes any part of this reading: the
figure author's quote can only point at a segment.

This module is pure: no I/O, and nothing is evaluated (a hand-written
tokenizer and a parser held to the grammar's caps, one Python frame per
nesting level bounded by :data:`~learnloop.figures.grammar.MAX_DEPTH`, as the
grammar's own parser). It is not sympy's lark parser: that reads ``e`` as a
free symbol and refuses common spacing and ``\\begin{cases}`` (§2's probe).

The table (§5.3), each row with an exact translation:

* integers and decimals read exactly (``Fraction(text)``: the harness's rule);
* a Latin letter, or a Greek command under its own canonical name
  (``\\lambda`` is ``lambda``), with one subscript letter or digit
  (``\\mu_1``, ``x_{0}`` are ``mu1``, ``x0``); two book symbols sharing one
  canonical name are unreadable, and so is a name the grammar reserves;
* ``+ - \\cdot \\times``, juxtaposition, unary minus; ``\\frac{a}{b}`` and
  ``a/b``; ``a^{b}`` and ``a^b`` with a one-token exponent;
* ``e^{u}``, ``\\mathrm{e}^{u}``, ``\\exp(u)``; ``e`` is Euler's number only as
  the base of a power or as ``\\mathrm{e}``;
* ``\\sqrt{u}``, ``\\ln(u)``, ``\\sin \\cos \\tan \\arctan``, ``erf`` as
  ``\\operatorname{erf}`` or ``\\mathrm{erf}``, ``|u|`` in its spellings,
  ``\\min``, ``\\max``, ``\\pi``, grouping;
* ``\\begin{cases} u & c \\\\ ... \\end{cases}``: each condition sets one
  symbol against a literal that is exactly a binary64 value, chained
  ``0 \\le x < 1`` included, and the rows are proved to cover the real line
  unless the last says ``\\text{otherwise}``;
* a symbol directly before a bracket is a product only when the same symbol
  also appears elsewhere without one, or is an argument of the left-hand side
  (names are never resolved: RW2b's rule).

Three readings are refused beyond the spec's list because they would be
guesses, each failing closed under its own key: ``a / b c`` and ``a / b / c``
(``ambiguous_slash``; books part on the grouping), ``x^10`` (LaTeX would
superscript only the 1) and ``\\frac{d}{dx}`` (``derivative``: read as a
product it would cancel the ``d``).

The tokens here are the expression's, not TeX's: a numeral is one token here and
one digit per token to TeX, and TeX ignores the spaces this tokenizer parts
digits on. So the forms where the two disagree are refused, whatever they
would parse as, and bookMathRenderCorpus.json pins each against KaTeX: an
unbraced ``\\sqrt16 x`` (the page shows the root of 1, then 6x), a numeral beside
a numeral (``2 3`` is the page's 23, ``1\\,000`` its thousand), and a subscript
after an unbraced exponent (``x^a_1`` is x sub 1 to the a). So is a numeral before
a numeric fraction: ``3\\frac{1}{2}`` is a mixed number, never a product.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from fractions import Fraction

from learnloop.figures import grammar as G

#: The version of this table, recorded on every check row.
READER_VERSION = "book-math-v1"

#: Every reason a candidate is unreadable, as a closed key (§5.3, §12).
REASONS = (
    "ambiguous_e", "ambiguous_slash", "application", "binom", "cases_condition", "cases_cover", "derivative",
    "factorial", "function_arg", "function_power", "gamma", "indicator", "inexact_literal", "integral", "limit",
    "log_base", "matrix", "multiple_relations", "name_collision", "not_equation", "nth_root", "phi", "product",
    "relation", "reserved_name", "set", "subscript", "sum", "syntax", "text", "too_long", "unicode_math",
    "unsupported_command", "unsupported_environment", "unsupported_function",
)

#: Greek commands, under the canonical names ``math_text`` gives them (its
#: GREEK table): a variant is the same canonical name as its letter, which is
#: what makes ``\epsilon`` beside ``\varepsilon`` a collision.
_GREEK = {
    "alpha": "alpha", "beta": "beta", "gamma": "gamma", "delta": "delta", "epsilon": "epsilon",
    "varepsilon": "epsilon", "zeta": "zeta", "eta": "eta", "theta": "theta", "vartheta": "theta", "iota": "iota",
    "kappa": "kappa", "lambda": "lambda", "mu": "mu", "nu": "nu", "xi": "xi", "pi": "pi", "varpi": "pi",
    "rho": "rho", "varrho": "rho", "sigma": "sigma", "varsigma": "sigma", "tau": "tau", "upsilon": "upsilon",
    "phi": "phi", "varphi": "phi", "chi": "chi", "psi": "psi", "omega": "omega",
    "Delta": "Delta", "Theta": "Theta", "Lambda": "Lambda", "Xi": "Xi", "Pi": "Pi", "Sigma": "Sigma",
    "Upsilon": "Upsilon", "Psi": "Psi", "Omega": "Omega",
}
_FUNCTIONS = {"exp": "exp", "ln": "log", "sin": "sin", "cos": "cos", "tan": "tan", "arctan": "atan"}
_EXTREMES = {"min": "min", "max": "max"}
#: Unreadable commands, each with its own key (§5.3's list).
_REFUSED_COMMANDS = {
    "Phi": "phi", "binom": "binom", "choose": "binom", "Gamma": "gamma", "int": "integral", "iint": "integral",
    "oint": "integral", "sum": "sum", "prod": "product", "lim": "limit", "limsup": "limit", "liminf": "limit",
    "partial": "derivative", "nabla": "derivative", "log": "log_base", "lg": "log_base", "mathbb": "indicator",
    "mathbbm": "indicator", "bm": "unsupported_command", "in": "set", "notin": "set", "cup": "set", "cap": "set",
    "subset": "set", "subseteq": "set", "mid": "set", "setminus": "set", "emptyset": "set", "approx": "relation",
    "propto": "relation", "sim": "relation", "equiv": "relation", "neq": "relation", "ne": "relation",
    "le": "relation", "leq": "relation", "ge": "relation", "geq": "relation", "ll": "relation", "gg": "relation",
    "to": "limit", "rightarrow": "limit", "mapsto": "limit", "text": "text", "textrm": "text", "mbox": "text",
}
_IGNORED = {",", ";", "!", "quad", " "}
_RELATION_TOKENS = {"<", ">"}
_OPENERS = {"(": ")", "[": "]", "\\{": "\\}"}
_ENVIRONMENTS_MATRIX = {"matrix", "pmatrix", "bmatrix", "vmatrix", "Vmatrix", "Bmatrix", "array"}
_CONDITION_OPS = {"<": "<", ">": ">", "\\le": "<=", "\\leq": "<=", "\\ge": ">=", "\\geq": ">=",
                  "\\leqslant": "<=", "\\geqslant": ">="}
_CASE_WORDS = {"if", "for"}
_NUMBER = re.compile(r"[0-9]+(?:\.[0-9]+)?|\.[0-9]+")
_COMMAND = re.compile(r"\\(?:[A-Za-z]+|.)", re.DOTALL)
_TEXT_ARG = re.compile(r"\\(?:text|textrm|mbox)\s*\{([^{}]*)\}")
#: The block types whose whole text is the equation when it has no delimiters.
EQUATION_BLOCK_TYPES = frozenset({"equation", "formula", "math"})


class Unreadable(ValueError):
    """A segment outside the table; ``reason`` is one key of :data:`REASONS`."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


@dataclass(frozen=True)
class Segment:
    """One math segment of a block's text; ``start``/``end`` delimit ``latex``'s place in it."""

    latex: str
    start: int
    end: int


@dataclass(frozen=True)
class Relation:
    """A read equation. ``lhs`` is the book's own left-hand side as a substring
    of the segment; ``args`` the symbols of a ``name(args)`` left-hand side
    (empty otherwise); ``tokens`` each canonical symbol's LaTeX as the book
    writes it."""

    latex: str
    lhs: str
    rhs: G.Node
    args: tuple[str, ...] = ()
    symbols: frozenset[str] = frozenset()
    tokens: dict[str, str] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Segments
# ---------------------------------------------------------------------------

_DELIMITED = re.compile(r"(?<!\\)\$\$(?P<display>.+?)(?<!\\)\$\$|\\\[(?P<bracket>.+?)\\\]|(?<!\\)\$(?P<inline>[^$]+?)(?<!\\)\$",
                        re.DOTALL)


def segments(text: str, block_type: str = "") -> list[Segment]:
    """The math segments of a block's text in reading order (§5.2): ``$...$``,
    ``$$...$$``, ``\\[...\\]``, or the whole text of an equation block.
    Unicode math outside these is never a segment."""

    source = str(text or "")
    found = []
    for match in _DELIMITED.finditer(source):
        name = match.lastgroup or "inline"
        found.append(Segment(match.group(name), match.start(name), match.end(name)))
    if not found and str(block_type or "").lower() in EQUATION_BLOCK_TYPES and source.strip():
        begin = len(source) - len(source.lstrip())
        found.append(Segment(source.strip(), begin, begin + len(source.strip())))
    return found


# ---------------------------------------------------------------------------
# Tokens
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class _Token:
    kind: str  # number | letter | command | op | text
    text: str
    start: int
    end: int


def _tokenize(source: str) -> list[_Token]:
    if len(source) > G.MAX_EXPR_CHARS:
        raise Unreadable("too_long")
    tokens: list[_Token] = []
    position = 0
    while position < len(source):
        char = source[position]
        if char in " \t\r\n~":
            position += 1
            continue
        if not char.isascii():
            raise Unreadable("unicode_math")
        if char == "%":
            raise Unreadable("syntax")
        if char.isdigit() or (char == "." and position + 1 < len(source) and source[position + 1].isdigit()):
            match = _NUMBER.match(source, position)
            assert match is not None
            tokens.append(_Token("number", match.group(0), position, match.end()))
            position = match.end()
            continue
        if char.isalpha():
            tokens.append(_Token("letter", char, position, position + 1))
            position += 1
            continue
        if char == "\\":
            text_arg = _TEXT_ARG.match(source, position)
            if text_arg is not None:
                tokens.append(_Token("text", " ".join(text_arg.group(1).split()), position, text_arg.end()))
                position = text_arg.end()
                continue
            match = _COMMAND.match(source, position)
            if match is None:
                raise Unreadable("syntax")
            tokens.append(_Token("command", match.group(0), position, match.end()))
            position = match.end()
            continue
        tokens.append(_Token("op", char, position, position + 1))
        position += 1
    kept = [token for token in tokens if not (token.kind == "command" and token.text[1:] in _IGNORED)]
    # TeX joins digits across a space (2 3 is 23) and \\, spaces a numeral's groups (1\\,000): never a product.
    if any(left.kind == "number" and right.kind == "number" for left, right in zip(kept, kept[1:])):
        raise Unreadable("syntax")
    return kept


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


class _Reader:
    def __init__(self, tokens: list[_Token], source: str, *, args: tuple[str, ...] = ()) -> None:
        self.tokens = tokens
        self.source = source
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
    def peek(self, offset: int = 0) -> _Token | None:
        index = self.position + offset
        return self.tokens[index] if index < len(self.tokens) else None

    def take(self) -> _Token:
        token = self.peek()
        if token is None:
            raise Unreadable("syntax")
        self.position += 1
        return token

    def at(self, text: str, kind: str | None = None) -> bool:
        token = self.peek()
        return token is not None and token.text == text and (kind is None or token.kind == kind)

    def expect(self, text: str) -> None:
        token = self.take()
        if token.text != text or token.kind in ("letter", "number", "text"):
            raise Unreadable("syntax")

    def node(self, kind: str, depth: int, **values: object) -> G.Node:
        self.nodes += 1
        if self.nodes > G.MAX_NODES or depth > G.MAX_DEPTH:
            raise Unreadable("too_long")
        return G.Node(kind, **values)  # type: ignore[arg-type]

    # -- expressions ------------------------------------------------------------
    def expression(self, depth: int) -> G.Node:
        if depth > G.MAX_DEPTH:
            raise Unreadable("too_long")
        if self.at("-", "op"):
            self.take()
            node = self.node("neg", depth, args=(self.term(depth + 1),))
        else:
            node = self.term(depth + 1)
        while self.peek() is not None and self.peek().kind == "op" and self.peek().text in "+-":  # type: ignore[union-attr]
            op = self.take().text
            node = self.node("bin", depth, op=op, args=(node, self.term(depth + 1)))
        return node

    def term(self, depth: int) -> G.Node:
        node = self.factor(depth + 1)
        while True:
            token = self.peek()
            if token is None:
                return node
            if (token.kind == "op" and token.text == "*") or token.text in ("\\cdot", "\\times"):
                self.take()
                node = self.node("bin", depth, op="*", args=(node, self.factor(depth + 1)))
            elif token.kind == "op" and token.text == "/":
                self.take()
                node = self.node("bin", depth, op="/", args=(node, self.factor(depth + 1)))
                following = self.peek()
                # a / b c and a / b / c: books part on the grouping, so neither is read.
                if following is not None and (self.starts_factor(following) or following.text == "/"):
                    raise Unreadable("ambiguous_slash")
            elif self.starts_factor(token):
                node = self.node("bin", depth, op="*", args=(node, self.factor(depth + 1)))
            else:
                return node

    def starts_factor(self, token: _Token) -> bool:
        if token.kind in ("number", "letter"):
            return True
        if token.kind == "text":
            raise Unreadable("text")
        if token.kind == "op":
            if token.text == "|":
                return self.bars == 0
            return token.text in ("(", "[")
        if token.kind != "command":
            return False
        name = token.text[1:]
        if name in _REFUSED_COMMANDS:
            raise Unreadable(_REFUSED_COMMANDS[name])
        return (name in _GREEK or name in _FUNCTIONS or name in _EXTREMES or name in (
            "frac", "sqrt", "mathrm", "operatorname", "lvert", "left", "begin", "{"))

    def factor(self, depth: int) -> G.Node:
        if depth > G.MAX_DEPTH:
            raise Unreadable("too_long")
        base = self.atom(depth + 1)
        if self.at("^", "op"):
            self.take()
            base = self.node("bin", depth, op="^", args=(base, self.exponent(depth + 1)))
            if self.at("^", "op"):
                raise Unreadable("syntax")
        return base

    def exponent(self, depth: int) -> G.Node:
        token = self.peek()
        if token is None:
            raise Unreadable("syntax")
        if token.kind == "op" and token.text == "{":
            self.take()
            saved, self.bars = self.bars, 0
            node = self.expression(depth + 1)
            self.bars = saved
            self.expect("}")
            return node
        if token.kind == "number":
            # x^10 superscripts only the 1 in LaTeX: refused, never guessed.
            if len(token.text) != 1:
                raise Unreadable("syntax")
            self.take()
            return self.node("num", depth, text=token.text, value=float(token.text))
        if token.kind == "letter" or (token.kind == "command" and token.text[1:] in _GREEK):
            # x^a_1 subscripts the base in TeX: x sub 1 to the a, never x to the a1.
            if self.at_offset(1, "_"):
                raise Unreadable("subscript")
            return self.symbol(depth + 1, in_exponent=True)
        raise Unreadable("syntax")

    def atom(self, depth: int) -> G.Node:
        token = self.peek()
        if token is None:
            raise Unreadable("syntax")
        if token.kind == "number":
            self.take()
            following = self.peek()
            if following is not None and following.kind == "op" and following.text == "!":
                raise Unreadable("factorial")
            if float(token.text) == float("inf"):
                raise Unreadable("too_long")
            return self.node("num", depth, text=token.text, value=float(token.text))
        if token.kind == "letter":
            return self.symbol(depth)
        if token.kind == "text":
            raise Unreadable("text")
        if token.kind == "op":
            if token.text in _OPENERS:
                return self.group(depth, _OPENERS[token.text])
            if token.text == "|":
                if self.bars:
                    raise Unreadable("syntax")
                return self.bar_group(depth, "|")
            if token.text == "!":
                raise Unreadable("factorial")
            if token.text == "'":
                raise Unreadable("derivative")
            raise Unreadable("syntax")
        name = token.text[1:]
        if name in _REFUSED_COMMANDS:
            raise Unreadable(_REFUSED_COMMANDS[name])
        if name in _GREEK:
            return self.symbol(depth)
        if name == "{":
            return self.group(depth, "\\}")
        if name == "left":
            return self.left_group(depth)
        if name == "lvert":
            return self.bar_group(depth, "\\rvert")
        if name == "frac":
            return self.fraction(depth)
        if name == "sqrt":
            return self.square_root(depth)
        if name == "mathrm":
            return self.mathrm(depth)
        if name == "operatorname":
            return self.operatorname(depth)
        if name == "begin":
            return self.environment(depth)
        if name in _FUNCTIONS:
            self.take()
            return self.node("call", depth, text=_FUNCTIONS[name], args=(self.function_argument(depth + 1),))
        if name in _EXTREMES:
            return self.extreme(depth, _EXTREMES[name])
        raise Unreadable("unsupported_command")

    def symbol(self, depth: int, *, in_exponent: bool = False) -> G.Node:
        token = self.take()
        raw = token.text
        canonical = _GREEK[raw[1:]] if token.kind == "command" else raw
        end = token.end
        subscript = False
        if self.at("_", "op"):
            self.take()
            sub = self.peek()
            if sub is None:
                raise Unreadable("subscript")
            if sub.kind == "op" and sub.text == "{":
                inner = self.peek(1)
                if inner is None or inner.kind not in ("letter", "number") or len(inner.text) != 1 \
                        or not self.at_offset(2, "}"):
                    raise Unreadable("subscript")
                self.position += 3
                canonical += inner.text
                end = self.tokens[self.position - 1].end
            elif sub.kind in ("letter", "number") and len(sub.text) == 1:
                self.position += 1
                canonical += sub.text
                end = sub.end
            else:
                raise Unreadable("subscript")
            subscript = True
        latex = self.source[token.start:end]
        if token.kind == "letter" and raw == "e" and not subscript:
            if not in_exponent and self.at("^", "op"):
                self.take()
                return self.node("call", depth, text="exp", args=(self.exponent(depth + 1),))
            raise Unreadable("ambiguous_e")
        if canonical == "pi" and raw == "\\pi":
            self.note_use(canonical)
            return self.node("name", depth, text="pi")
        if canonical in G.RESERVED or not G.is_name(canonical):
            raise Unreadable("reserved_name")
        self.record(canonical, latex)
        self.note_use(canonical)
        return self.node("name", depth, text=canonical)

    def at_offset(self, offset: int, text: str) -> bool:
        token = self.peek(offset)
        return token is not None and token.text == text

    def note_use(self, canonical: str) -> None:
        following = self.peek()
        applied = following is not None and ((following.kind == "op" and following.text in _OPENERS)
                                             or following.text == "\\{"
                                             or (following.text == "\\left" and not self.left_bar(1)))
        (self.applied if applied else self.plain).add(canonical)

    def left_bar(self, offset: int) -> bool:
        token = self.peek(offset)
        return token is not None and token.text in ("|", "\\lvert")

    def record(self, canonical: str, latex: str) -> None:
        spelled = "".join(latex.split()).replace("{", "").replace("}", "")
        known = self.spellings.setdefault(canonical, set())
        known.add(spelled)
        if len(known) > 1:
            raise Unreadable("name_collision")
        self.first.setdefault(canonical, latex)

    def group(self, depth: int, closer: str) -> G.Node:
        self.take()
        saved, self.bars = self.bars, 0
        node = self.expression(depth + 1)
        self.bars = saved
        self.expect(closer)
        return node

    def left_group(self, depth: int) -> G.Node:
        self.take()
        opener = self.peek()
        if opener is None:
            raise Unreadable("syntax")
        closers = {"(": ")", "[": "]", "\\{": "\\}", "|": "|", "\\lvert": "\\rvert"}
        if opener.text not in closers:
            raise Unreadable("syntax")
        self.take()
        saved, self.bars = self.bars, 0
        inner = self.expression(depth + 1)
        self.bars = saved
        self.expect("\\right")
        self.expect(closers[opener.text])
        if opener.text in ("|", "\\lvert"):
            return self.node("call", depth, text="abs", args=(inner,))
        return inner

    def bar_group(self, depth: int, closer: str) -> G.Node:
        self.take()
        self.bars += 1
        inner = self.expression(depth + 1)
        self.bars -= 1
        self.expect(closer)
        return self.node("call", depth, text="abs", args=(inner,))

    def braced(self, depth: int) -> G.Node:
        if not self.at("{", "op"):
            raise Unreadable("syntax")
        self.take()
        saved, self.bars = self.bars, 0
        node = self.expression(depth + 1)
        self.bars = saved
        self.expect("}")
        return node

    def fraction(self, depth: int) -> G.Node:
        before = self.tokens[self.position - 1] if self.position else None
        self.take()
        numerator_start = self.peek(1)
        numerator = self.braced(depth + 1)
        following = self.peek(1)
        # \frac{d}{dx}, \frac{dy}{dx}: a derivative, never the product it would parse as.
        if numerator_start is not None and numerator_start.text == "d" \
                and following is not None and following.text == "d":
            raise Unreadable("derivative")
        denominator = self.braced(depth + 1)
        # 3\\frac{1}{2} on a page is a mixed number, 3.5; the product it would parse as is 1.5.
        if before is not None and before.kind == "number" and numerator.kind == denominator.kind == "num":
            raise Unreadable("syntax")
        return self.node("bin", depth, op="/", args=(numerator, denominator))

    def square_root(self, depth: int) -> G.Node:
        self.take()
        if self.at("[", "op"):
            raise Unreadable("nth_root")
        # Only \\sqrt{u} (§5.3): TeX takes one token, the 1 of \\sqrt16, where this tokenizer has a numeral.
        if not self.at("{", "op"):
            raise Unreadable("function_arg")
        return self.node("call", depth, text="sqrt", args=(self.braced(depth + 1),))

    def word(self) -> str:
        """The letters of a ``{word}`` argument."""

        self.expect("{")
        letters = []
        while not self.at("}", "op"):
            token = self.take()
            if token.kind != "letter":
                raise Unreadable("unsupported_command")
            letters.append(token.text)
        self.take()
        return "".join(letters)

    def mathrm(self, depth: int) -> G.Node:
        self.take()
        word = self.word()
        if word == "e":
            if self.at("^", "op"):
                self.take()
                return self.node("call", depth, text="exp", args=(self.exponent(depth + 1),))
            return self.node("name", depth, text="e")
        if word == "erf":
            return self.node("call", depth, text="erf", args=(self.function_argument(depth + 1),))
        if word == "d":
            raise Unreadable("derivative")
        raise Unreadable("unsupported_command")

    def operatorname(self, depth: int) -> G.Node:
        self.take()
        word = self.word()
        if word != "erf":
            raise Unreadable("unsupported_function")
        return self.node("call", depth, text="erf", args=(self.function_argument(depth + 1),))

    def function_argument(self, depth: int) -> G.Node:
        """``\\sin(u)``, or a bare one-token argument with nothing juxtaposed after it."""

        if self.at("^", "op"):
            raise Unreadable("function_power")
        token = self.peek()
        if token is None:
            raise Unreadable("function_arg")
        if token.kind == "op" and token.text in _OPENERS:
            return self.group(depth, _OPENERS[token.text])
        if token.text == "\\{":
            return self.group(depth, "\\}")
        if token.text == "\\left":
            return self.left_group(depth)
        inner = self.bare_argument(depth)
        if self.at("^", "op"):
            raise Unreadable("function_arg")
        following = self.peek()
        if following is not None and self.starts_factor(following) and not (
                following.kind == "command" and following.text[1:] in _FUNCTIONS):
            raise Unreadable("function_arg")
        return inner

    def bare_argument(self, depth: int) -> G.Node:
        token = self.peek()
        if token is None:
            raise Unreadable("function_arg")
        if token.kind == "number":
            self.take()
            return self.node("num", depth, text=token.text, value=float(token.text))
        if token.kind == "letter" or (token.kind == "command" and token.text[1:] in _GREEK):
            return self.symbol(depth)
        raise Unreadable("function_arg")

    def extreme(self, depth: int, name: str) -> G.Node:
        self.take()
        token = self.peek()
        if token is None:
            raise Unreadable("syntax")
        left = token.text == "\\left"
        if left:
            self.take()
            token = self.peek()
            if token is None:
                raise Unreadable("syntax")
        closers = {"(": ")", "[": "]", "\\{": "\\}"}
        if token.text not in closers:
            raise Unreadable("syntax")
        closer = closers[token.text]
        self.take()
        saved, self.bars = self.bars, 0
        args = [self.expression(depth + 1)]
        while self.at(",", "op"):
            self.take()
            args.append(self.expression(depth + 1))
        self.bars = saved
        if left:
            self.expect("\\right")
        self.expect(closer)
        low, high = G.FUNCTIONS[name]
        if len(args) < low or (high is not None and len(args) > high):
            raise Unreadable("syntax")
        return self.node("call", depth, text=name, args=tuple(args))

    # -- cases -----------------------------------------------------------------
    def environment(self, depth: int) -> G.Node:
        self.take()
        name = self.word_environment()
        if name in _ENVIRONMENTS_MATRIX:
            raise Unreadable("matrix")
        if name != "cases":
            raise Unreadable("unsupported_environment")
        rows: list[tuple[G.Node, G.Node | None, tuple[str, list[tuple[str, Fraction]]] | None]] = []
        while True:
            if self.at("\\end"):
                break
            value = self.expression(depth + 1)
            self.row_end_punctuation()
            # A row with no condition column names no condition: only the word
            # "otherwise" may stand for the rest of the line.
            if not self.at("&", "op"):
                raise Unreadable("cases_cover")
            self.take()
            condition, shape = self.condition(depth + 1)
            self.row_end_punctuation()
            rows.append((value, condition, shape))
            if self.at("\\\\"):
                self.take()
                continue
            break
        self.expect("\\end")
        if self.word_environment() != "cases":
            raise Unreadable("syntax")
        if not rows:
            raise Unreadable("cases_cover")
        return self.cases_node(rows, depth)

    def word_environment(self) -> str:
        self.expect("{")
        letters = []
        while not self.at("}", "op"):
            token = self.take()
            if token.kind != "letter":
                if token.text == "*":
                    letters.append("*")
                    continue
                raise Unreadable("unsupported_environment")
            letters.append(token.text)
        self.take()
        return "".join(letters)

    def row_end_punctuation(self) -> None:
        while self.peek() is not None and self.peek().kind == "op" and self.peek().text in ",.":  # type: ignore[union-attr]
            self.take()

    def condition(self, depth: int) -> tuple[G.Node | None, tuple[str, list[tuple[str, Fraction]]] | None]:
        """A condition column: ``\\text{otherwise}`` (None), or one symbol
        against exact literals, an optional ``\\text{if }`` before it."""

        token = self.peek()
        if token is not None and token.kind == "text":
            self.take()
            words = token.text.strip().rstrip(",.:").strip()
            if words == "otherwise":
                return None, None
            if words not in _CASE_WORDS:
                raise Unreadable("text")
        chain: list[object] = [self.condition_side()]
        ops: list[str] = []
        while True:
            token = self.peek()
            if token is None or token.text not in _CONDITION_OPS:
                break
            self.take()
            ops.append(_CONDITION_OPS[token.text])
            chain.append(self.condition_side())
        if len(chain) not in (2, 3):
            following = self.peek()
            if following is not None and following.kind == "command" and following.text[1:] in _REFUSED_COMMANDS:
                raise Unreadable(_REFUSED_COMMANDS[following.text[1:]])
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

    def condition_side(self) -> object:
        token = self.peek()
        if token is None:
            raise Unreadable("cases_condition")
        sign = 1
        if token.kind == "op" and token.text == "-":
            self.take()
            sign = -1
            token = self.peek()
            if token is None:
                raise Unreadable("cases_condition")
        if token.kind == "number":
            self.take()
            if not binary64_exact(token.text):
                raise Unreadable("inexact_literal")
            return sign * Fraction(token.text)
        if token.text == "\\frac":
            self.take()
            self.expect("{")
            top = self.take()
            self.expect("}")
            self.expect("{")
            bottom = self.take()
            self.expect("}")
            if top.kind != "number" or bottom.kind != "number" or not Fraction(bottom.text):
                raise Unreadable("cases_condition")
            value = Fraction(top.text) / Fraction(bottom.text)
            if Fraction(float(value)) != value:
                raise Unreadable("inexact_literal")
            return sign * value
        if sign < 0:
            raise Unreadable("cases_condition")
        if token.kind == "letter" or (token.kind == "command" and token.text[1:] in _GREEK):
            node = self.symbol(0)
            return node.text
        if token.kind == "command" and token.text[1:] in _REFUSED_COMMANDS:
            raise Unreadable(_REFUSED_COMMANDS[token.text[1:]])
        raise Unreadable("cases_condition")

    def literal_node(self, value: Fraction, depth: int) -> G.Node:
        text = _dyadic_text(abs(value))
        literal = self.node("num", depth, text=text, value=float(abs(value)))
        return self.node("neg", depth, args=(literal,)) if value < 0 else literal

    def cases_node(self, rows: list[tuple[G.Node, G.Node | None, tuple[str, list[tuple[str, Fraction]]] | None]],
                   depth: int) -> G.Node:
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


def _flip(op: str) -> str:
    return {"<": ">", "<=": ">=", ">": "<", ">=": "<="}[op]


def _compare(point: Fraction, op: str, value: Fraction) -> bool:
    return {"<": point < value, "<=": point <= value, ">": point > value, ">=": point >= value}[op]


# ---------------------------------------------------------------------------
# One relation
# ---------------------------------------------------------------------------

_LHS_APPLICATION = re.compile(r"\A\s*(?:\\?[A-Za-z]+)(?:_\{?[A-Za-z0-9]\}?)?\s*(?:\\left\s*)?\((?P<args>.*)(?:\\right\s*)?\)\s*\Z", re.DOTALL)


def _split_relation(tokens: list[_Token]) -> tuple[int, int]:
    """Where the one top-level ``=`` or ``:=`` is, as ``(lhs_end, rhs_start)``
    token indices: a segment must hold exactly one."""

    depth = 0
    found: list[tuple[int, int]] = []
    other = False
    for index, token in enumerate(tokens):
        text = token.text
        if token.kind == "op" and text in "([{":
            depth += 1
        elif token.kind == "op" and text in ")]}":
            depth -= 1
        elif text in ("\\{", "\\left", "\\begin"):
            depth += 1
        elif text in ("\\}", "\\right", "\\end"):
            depth -= 1
        elif depth == 0 and token.kind == "op" and text == "=":
            start = index - 1 if index and tokens[index - 1].text == ":" else index
            found.append((start, index + 1))
        elif depth == 0 and (text in _RELATION_TOKENS or text[1:] in (
                "approx", "propto", "sim", "equiv", "le", "leq", "ge", "geq", "neq", "ne", "ll", "gg")):
            other = True
    if other:
        raise Unreadable("relation")
    if not found:
        raise Unreadable("not_equation")
    if len(found) > 1:
        raise Unreadable("multiple_relations")
    return found[0]


def _lhs_args(lhs: str) -> tuple[tuple[str, ...], dict[str, set[str]], dict[str, str]]:
    """The symbols of a ``name(args)`` left-hand side, with how the book spells
    them; empty for ``P(X = k)``, ``E[X]`` or a bare name."""

    nothing: tuple[tuple[str, ...], dict[str, set[str]], dict[str, str]] = ((), {}, {})
    match = _LHS_APPLICATION.match(lhs)
    if match is None:
        return nothing
    inner = re.sub(r"\\right\s*\Z", "", match.group("args").strip())
    args: list[str] = []
    spellings: dict[str, set[str]] = {}
    first: dict[str, str] = {}
    for part in inner.split(","):
        try:
            tokens = _tokenize(part.strip())
        except Unreadable:
            return nothing
        if not tokens:
            return nothing
        reader = _Reader(tokens, part.strip())
        token = tokens[0]
        if not (token.kind == "letter" or (token.kind == "command" and token.text[1:] in _GREEK)):
            return nothing
        try:
            node = reader.symbol(0, in_exponent=True)
        except Unreadable:
            return nothing
        if reader.position != len(tokens) or node.kind != "name":
            return nothing
        args.append(node.text)
        for name, spelled in reader.spellings.items():
            spellings.setdefault(name, set()).update(spelled)
        first.update(reader.first)
    return tuple(args), spellings, first


def read_relation(latex: str) -> Relation:
    """One math segment read as one relation, or :class:`Unreadable`."""

    source = str(latex or "")
    tokens = _tokenize(source)
    while tokens and tokens[-1].kind == "op" and tokens[-1].text in ",.":
        tokens = tokens[:-1]
    if not tokens:
        raise Unreadable("not_equation")
    lhs_end, rhs_start = _split_relation(tokens)
    if lhs_end == 0 or rhs_start >= len(tokens):
        raise Unreadable("not_equation")
    lhs = source[tokens[0].start:tokens[lhs_end - 1].end].strip()
    args, spellings, first = _lhs_args(lhs)
    reader = _Reader(tokens[rhs_start:], source, args=args)
    # \\varepsilon on the left and \\epsilon on the right are two book symbols sharing one name.
    reader.spellings = {name: set(spelled) for name, spelled in spellings.items()}
    reader.first = dict(first)
    rhs = reader.expression(1)
    if reader.position != len(reader.tokens):
        token = reader.peek()
        if token is not None and token.kind == "command" and token.text[1:] in _REFUSED_COMMANDS:
            raise Unreadable(_REFUSED_COMMANDS[token.text[1:]])
        if token is not None and token.kind == "text":
            raise Unreadable("text")
        if token is not None and token.text == "!":
            raise Unreadable("factorial")
        if token is not None and token.text == "'":
            raise Unreadable("derivative")
        raise Unreadable("syntax")
    # Names are never resolved: g(1-p) is a product only when g also stands alone.
    if any(name not in reader.plain and name not in reader.args for name in reader.applied):
        raise Unreadable("application")
    if G.node_count(rhs, {}) > G.MAX_EXPANDED_NODES:
        raise Unreadable("too_long")
    return Relation(latex=source, lhs=lhs, rhs=rhs, args=args, symbols=frozenset(G.free_names(rhs)),
                    tokens=dict(reader.first))


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
