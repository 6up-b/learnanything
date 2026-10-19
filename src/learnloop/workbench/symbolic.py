"""Reader workbench RW2b: symbolic checks of the learner's own written steps (spec_reader_workbench_v1 §5.3, G9, G38).

**"Checked" comes only from the learner's own written step, parsed by code**
(fix round 3, the orchestrator's ruling on F3). The check writer (or a hint's
claim) declares, per step it can classify, ONE transformation kind with its
inputs in sympy syntax. That declaration only picks WHICH check to try. What
is checked is the written text itself: :data:`HARNESS` parses its LaTeX with
sympy's own LaTeX parser on the ``lark`` backend (grouping kept: ``x^{2+1}``
is ``x**3``) into ONE relation, both of its sides, the operator on the left
side and that operator's variable, bounds and evaluation point, and checks
THAT relation. The declared expressions and parameters are never check
inputs: they are compared with the parse, and any disagreement (another
variable, other bounds, another point, another operand or result, another
kind) leaves the step the model's reading.

**Names are never resolved** (fix round 6, the orchestrator's ruling): a text
that applies a name as a function (``f(...)``, ``\\phi(...)``, ``g'(x)``, any
identifier or command written before an argument) or writes a name that the
problem or an earlier step defines (``name(var) = ...``) is the model's
reading, read from the syntax with ``\\alpha`` and ``alpha`` one identifier.
Checks are on explicit expressions only. A name, an ambiguous parse (the
parser's ``_ambig``: ``\\lim_{x \\to 2} x^2`` may be the limit of ``x^2`` or
the square of a limit), prose (a run of letters that is neither a LaTeX
command nor a differential), more than one relation, an operator nested inside
a side, or a kind outside the supported ones keeps the honest label "model's
reading, not checked". Nothing textual can produce "checked": the only regex
here rejects prose before parsing.

The checks are fixed code run in the PF-b sandbox
(``learnloop.content.authoring.pf_sandbox``: bubblewrap, no network, rlimits,
a wall-clock timeout), because sympy evaluates what it parses
(``2^{10^{100}}``). Without bubblewrap the sandbox fails closed and every
verdict stays the model's reading.

Supported kinds (each can be *checked*), as the learner writes them:

* ``equivalence``: ``lhs = rhs`` with no operator on either side
  (``simplify(lhs - rhs) == 0``);
* ``differentiation``: ``\\frac{d}{dx}(...) = rhs`` of an explicit expression;
* ``integration``: ``\\int_a^b ... \\, dx = rhs`` (definite) or
  ``\\int ... \\, dx = rhs`` (an antiderivative, up to a constant);
* ``normalization``: a definite integral equal to ``1``;
* ``limit``: ``\\lim_{x \\to a} (...) = rhs``;
* ``sum``: ``\\sum_{k=a}^{b} ... = rhs``;
* ``solving``: ``x = value`` against the one equation the step before writes
  (for a first step, the problem's only equation in ``x``), when neither has
  any restriction token (a denominator, log, root, or power that is not a
  whole number).

``inequality``, ``boundary`` and ``substitution`` (and ``f'(x)``) stay
declared kinds in the prompt but are never checked (sampling can certify a
false inequality; the parser reads no evaluation bar; names are not
resolved).

Each check is trusted only when its **controls behave**: a negative control
(the right side perturbed) must be rejected and, where sympy computes the
true result, a positive control (that result) accepted. Then a relation sympy
decides exactly is *checked* (``✓`` holds, ``≠`` doesn't follow): it
simplifies to an identity, or the difference is an exact non-zero number. A
difference that still has unknowns never gives ``≠`` (the step may be an
equation to solve, not an identity): the model's reading. One that vanishes
at every sampled point but that sympy cannot prove, or a decimal constant, is
*checked numerically*; one that holds on part of the samples only (an
identity on a domain the step does not state, ``|x| = x``,
``\\sqrt{x^2} = x``) is the model's reading (fix round 1, F2).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Callable

#: The kinds the writer may declare (the prompt's list).
KINDS: tuple[str, ...] = (
    "equivalence", "differentiation", "integration", "substitution", "solving", "limit", "sum", "inequality",
    "boundary", "normalization",
)
#: The kinds a parsed written step can be checked as (module docstring).
CHECKABLE_KINDS: tuple[str, ...] = (
    "equivalence", "differentiation", "integration", "normalization", "limit", "sum", "solving",
)
#: How a verdict was reached (the label beside the marker, W2).
CHECKED, CHECKED_NUMERICALLY, MODEL = "checked", "checked_numerically", "model"
#: Bounds (prompt-size and runtime only, never judgments). Fix round 4,
#: item 1: a claim whose text, earlier steps, problem or declaration exceeds
#: its bound is never sent (never a truncated prefix): the model's reading.
MAX_CHECKS = 12
MAX_EXPRESSION_CHARS = 400
MAX_TEXT_CHARS = 4_000
MAX_EARLIER = 200
MAX_PROBLEM_CHARS = 8_000


@dataclass(frozen=True)
class SymbolicClaim:
    """One declared transformation of one written text.

    ``text`` is what is checked: the learner's step (or a hint claim's own
    statement), parsed from its LaTeX in the sandbox. ``earlier`` are the
    learner's steps before it, in order, and ``problem`` the problem
    statement: only their parsed definitions ``name(var) = expr`` (and, for
    solving, their equation) are read. The declared fields (``kind`` to
    ``relation``) pick the check and are compared with the parse; they are
    never its inputs."""

    index: int
    kind: str
    expression: str
    result: str
    variable: str = ""
    value: str = ""
    lower: str = ""
    upper: str = ""
    relation: str = ""
    text: str = ""
    earlier: tuple[str, ...] = ()
    problem: str = ""
    #: Texts read only for their names (fix round 7): a hint claim's own step.
    names_context: tuple[str, ...] = ()

    def oversized(self) -> str | None:
        """Which bound the claim exceeds (it is then never checked), or None."""

        for name in ("expression", "result", "value", "lower", "upper"):
            if len(str(getattr(self, name) or "")) > MAX_EXPRESSION_CHARS:
                return name
        if len(str(self.variable or "")) > 40 or len(str(self.relation or "")) > 4:
            return "declaration"
        if len(str(self.text or "")) > MAX_TEXT_CHARS:
            return "text"
        if len(self.earlier) > MAX_EARLIER or any(len(str(text or "")) > MAX_TEXT_CHARS for text in self.earlier):
            return "earlier"
        if len(self.names_context) > MAX_EARLIER or any(len(str(text or "")) > MAX_TEXT_CHARS
                                                         for text in self.names_context):
            return "names_context"
        if len(str(self.problem or "")) > MAX_PROBLEM_CHARS:
            return "problem"
        return None

    def payload(self) -> dict[str, Any]:
        """The claim as data, whole (:meth:`oversized` keeps a claim that
        would need clipping out of the sandbox altogether)."""

        return {"index": self.index, "kind": self.kind, "expression": self.expression, "result": self.result,
                "variable": self.variable, "value": self.value, "lower": self.lower, "upper": self.upper,
                "relation": self.relation, "text": self.text, "earlier": [str(text) for text in self.earlier],
                "problem": self.problem, "names_context": [str(text) for text in self.names_context]}


@dataclass(frozen=True)
class SymbolicOutcome:
    """What the sandbox found for one claim. ``method`` is ``checked``,
    ``checked_numerically`` or ``model`` (the text did not parse to one
    supported relation, the declaration disagreed with the parse, the
    controls misbehaved, or the sandbox did not run); ``holds`` is the
    relation's truth only when ``method`` is not ``model``. ``bound`` says
    the written text parsed and the declaration agreed with it, so a verdict
    is about what was written."""

    index: int
    method: str
    holds: bool | None
    reason: str = ""
    bound: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {"index": self.index, "method": self.method, "holds": self.holds, "reason": self.reason}


# The harness: fixed code. Every text arrives as JSON data and is parsed by
# sympy inside the sandbox only.
HARNESS = r'''
import json, random, re, signal, sys
workdir = sys.argv[1]
MARKER = "@@PF-SANDBOX-RESULT@@"


class _Timeout(Exception):
    pass


def _alarm(_signum, _frame):
    raise _Timeout()


signal.signal(signal.SIGALRM, _alarm)


def bounded(seconds, function, *args):
    signal.alarm(seconds)
    try:
        return function(*args)
    finally:
        signal.alarm(0)


import sympy
from sympy.core.function import AppliedUndef
from sympy.parsing.sympy_parser import (convert_xor, implicit_multiplication_application, parse_expr,
                                        standard_transformations)

try:
    from lark import Token, Tree
    from lark.exceptions import VisitError
    from sympy.parsing.latex.lark import LarkLaTeXParser
    from sympy.parsing.latex.lark.transformer import TransformToSymPyExpr
    LATEX = LarkLaTeXParser(transform=False)
    LATEX_PROBLEM = ""
except Exception as exc:  # the lark backend is unusable: nothing is checked
    LATEX = None
    LATEX_PROBLEM = type(exc).__name__
    Token = Tree = type("Missing", (), {})
    TransformToSymPyExpr = object
    VisitError = Exception

TRANSFORMS = standard_transformations + (implicit_multiplication_application, convert_xor)


class NotChecked(Exception):
    """The text cannot be checked as written (the reason is the message)."""


# -- The declaration (sympy syntax; compared with the parse, never checked) --------------------

def parse(text):
    text = str(text or "").strip().replace("$", "")
    if not text:
        raise ValueError("empty expression")
    return parse_expr(text, transformations=TRANSFORMS, evaluate=True)


def declared_equation(text):
    text = str(text or "")
    if "=" in text and "==" not in text and "<" not in text and ">" not in text:
        left, right = text.split("=", 1)
        return parse(left) - parse(right)
    return parse(text)


def agree(declared, parsed, *, equation=False):
    """Whether a declared field means the parsed value (False on any doubt)."""
    try:
        value = declared_equation(declared) if equation else parse(declared)
        if sympy.simplify(value - parsed) == 0:
            return True
        return bool(equation and sympy.simplify(value + parsed) == 0)
    except _Timeout:
        raise
    except Exception:
        return False


# -- The written LaTeX, parsed (sympy's lark backend) -------------------------------------------

class Rel:
    """One relation as written: ``op`` and both sides (never evaluated)."""

    def __init__(self, op, lhs, rhs):
        self.op, self.lhs, self.rhs = op, lhs, rhs

    def same(self, other):
        return isinstance(other, Rel) and (self.op, self.lhs, self.rhs) == (other.op, other.lhs, other.rhs)


def _sympy(value):
    return isinstance(value, sympy.Expr)


class Transform(TransformToSymPyExpr):
    """sympy's LaTeX transformer, except that a relation stays a relation
    (``Eq`` would evaluate ``\\int_0^2 2x\\,dx = 1`` to ``False``) and an
    ambiguous parse is refused (fix round 6: no reading is chosen by names;
    a reading that applies a name as a function refuses)."""

    def __init__(self):
        super().__init__()
        #: What the written text restricts (fix round 4, item 2): every
        #: denominator, log argument, even-root radicand and base of a
        #: negative power, AS WRITTEN (sympy's evaluation may cancel them:
        #: x^2/x is x).
        self.restricted = []

    def SYMBOL(self, token):
        return sympy.Symbol(str(token))

    def _handle_division(self, numerator, denominator):
        self.restricted.append(denominator)
        return super()._handle_division(numerator, denominator)

    def log(self, tokens):
        self.restricted.extend(token for token in tokens if isinstance(token, sympy.Basic))
        return super().log(tokens)

    def square_root(self, tokens):
        if len(tokens) == 3 and tokens[1] != 2:
            # Fix round 4, item 6: an n-th root other than the square root
            # (sympy's principal complex root, not the real one) is not checked.
            raise NotChecked("nth_root")
        self.restricted.append(tokens[-1])
        return super().square_root(tokens)

    def superscript(self, tokens):
        base = tokens[0]
        power = tokens[3] if len(tokens) == 5 else tokens[2] if len(tokens) == 3 else None
        if isinstance(base, sympy.Basic) and isinstance(power, sympy.Basic) and power.is_number:
            if power.is_integer is not True and base.is_nonnegative is not True:
                # Fix round 4, item 6: a fractional power of a base that can be
                # negative (no real-root semantics here).
                raise NotChecked("fractional_power")
            if power.is_integer is not True or power.is_negative:
                self.restricted.append(base)
        return super().superscript(tokens)

    def eq(self, tokens):
        return Rel("=", tokens[0], tokens[2])

    def ne(self, tokens):
        return Rel("!=", tokens[0], tokens[2])

    def lt(self, tokens):
        return Rel("<", tokens[0], tokens[2])

    def lte(self, tokens):
        return Rel("<=", tokens[0], tokens[2])

    def gt(self, tokens):
        return Rel(">", tokens[0], tokens[2])

    def gte(self, tokens):
        return Rel(">=", tokens[0], tokens[2])

    def _ambig(self, options):
        kept = []
        for option in options:
            parts = [option.lhs, option.rhs] if isinstance(option, Rel) else [option]
            if not all(_sympy(part) for part in parts):
                raise NotChecked("ambiguous")
            if any(part.atoms(AppliedUndef) for part in parts):
                # Fix round 6: a reading that applies a name (f(x)) is never checked.
                raise NotChecked("applies_a_name")
            if not any((option.same(other) if isinstance(option, Rel) else option == other) for other in kept):
                kept.append(option)
        if len(kept) != 1:
            raise NotChecked("ambiguous")
        return kept[0]


_COMMAND = re.compile(r"\\[A-Za-z]+")
_LETTERS = re.compile(r"[A-Za-z]{2,}")
_DELIMITERS = (("$$", "$$"), ("\\[", "\\]"), ("\\(", "\\)"), ("$", "$"))


def math_of(text):
    """``text`` as one math expression: one enclosing delimiter pair removed.
    Refused, never guessed, when prose or a second segment is present."""
    text = str(text or "").strip()
    for opening, closing in _DELIMITERS:
        if len(text) > len(opening) + len(closing) and text.startswith(opening) and text.endswith(closing):
            text = text[len(opening):len(text) - len(closing)].strip()
            break
    if not text or "$" in text:
        raise NotChecked("not_one_expression")
    for run in _LETTERS.findall(_COMMAND.sub(" ", text)):
        # A word is prose ("so", "on [0, 1]"): sympy would read it as a
        # product of letters. Only a differential (dx) may stand so.
        if not (len(run) == 2 and run[0] == "d"):
            raise NotChecked("prose")
    return text


def segments(text):
    """The problem statement's delimited math segments, in order."""
    out = []
    for match in re.finditer(r"\$\$(.+?)\$\$|\$(.+?)\$|\\\((.+?)\\\)|\\\[(.+?)\\\]", str(text or ""), re.S):
        out.append(next(group for group in match.groups() if group is not None))
    return out


_LETTER_TYPES = ("SYMBOL", "MULTI_LETTER_SYMBOL", "GREEK_SYMBOL")


def _is_letter(token):
    kind = str(getattr(token, "type", ""))
    return kind in _LETTER_TYPES or kind.startswith(("LATIN_SYMBOL", "GREEK_SYMBOL"))


def names_in(node):
    """The letters (symbols and names, primes dropped) written in a parse
    (sub)tree: the syntax, before sympy evaluates anything."""
    if isinstance(node, Tree):
        tokens = list(node.scan_values(lambda value: isinstance(value, Token)))
    elif isinstance(node, Token):
        tokens = [node]
    else:
        tokens = []
    return {canonical(str(token)) for token in tokens if _is_letter(token)}


def canonical(name):
    """An identifier as one name whatever its spelling: primes and
    backslashes dropped, so ``\\alpha`` and ``alpha`` are the same (fix round 6)."""
    return str(name).replace("\\", "").rstrip("'").strip()


def _plain_count(node):
    """An exponent written as a plain non-negative whole number (2, {3})."""
    if isinstance(node, Token):
        return str(node.type) == "DIGIT" or str(node).isdigit()
    if isinstance(node, Tree):
        data = str(node.data)
        if data == "number":
            return all(isinstance(child, Token) and str(child).isdigit() for child in node.children)
        if data == "group_curly_parentheses":
            inner = [child for child in node.children if not (isinstance(child, Token) and str(child) in "{}")]
            return len(inner) == 1 and _plain_count(inner[0])
    return False


def spots(tree):
    """Fix round 5, items 1-2: every place the WRITTEN text restricts a
    domain, read from the parse tree before any evaluation (x^2/x stays a
    fraction here): a denominator, a log, a root, and the base of a power
    that is not a plain whole number. Each spot is the set of letters it
    involves."""
    out = []
    for node in tree.iter_subtrees():
        data, children = str(node.data), node.children
        if data in ("fraction", "special_fraction", "div") and len(children) >= 3:
            out.append(names_in(children[2]))
        elif data in ("log", "square_root"):
            out.append(names_in(node))
        elif data == "superscript":
            power = children[2] if len(children) == 3 else None
            if power is not None and not (isinstance(power, Token) and "PRIME" in str(power.type)) \
                    and not _plain_count(power):
                out.append(names_in(children[0]) | names_in(power))
    return out


def read(text):
    """The text's one relation (a :class:`Rel` of sympy sides), with the
    letters it writes (``names``) and its domain restrictions (``spots``),
    both read from the syntax."""
    if LATEX is None:
        raise NotChecked("latex_parser_unavailable:" + LATEX_PROBLEM)
    source = math_of(text)
    try:
        tree = LATEX.doparse(source)
        transformer = Transform()
        value = transformer.transform(tree)
    except VisitError as exc:
        inner = getattr(exc, "orig_exc", None)
        if isinstance(inner, (NotChecked, _Timeout)):
            raise inner
        raise NotChecked("unparsed")
    except (NotChecked, _Timeout):
        raise
    except Exception:
        raise NotChecked("unparsed")
    if not isinstance(value, Rel):
        raise NotChecked("no_relation")
    if not (_sympy(value.lhs) and _sympy(value.rhs)):
        raise NotChecked("not_one_relation")
    value.restricted = list(transformer.restricted)
    value.names = names_in(tree)
    value.spots = spots(tree)
    value.applies = applies_a_name(tree, source)
    return value


#: LaTeX commands that are functions of the parser, not names a learner defines.
_MATH_COMMANDS = frozenset((
    "sin", "cos", "tan", "csc", "sec", "cot", "arcsin", "arccos", "arctan", "arccsc", "arcsec", "arccot",
    "sinh", "cosh", "tanh", "arsinh", "arcosh", "artanh", "exp", "log", "ln", "lg", "sqrt", "frac", "dfrac",
    "tfrac", "int", "sum", "prod", "lim", "left", "right", "min", "max", "cdot", "times", "div", "to",
))
#: An identifier (a letter, or a command) applied to an argument: f(x), f\left(x, \phi(x).
_APPLIED = re.compile(r"(?:(?<![\\A-Za-z])[A-Za-z]|\\([A-Za-z]+))'*\s*(?:\\left\s*)?\(")
#: Greek letters: identifiers, never names of the parser.
_GREEK = frozenset((
    "alpha", "beta", "gamma", "delta", "epsilon", "varepsilon", "zeta", "eta", "theta", "vartheta", "iota", "kappa",
    "lambda", "mu", "nu", "xi", "pi", "varpi", "rho", "varrho", "sigma", "varsigma", "tau", "upsilon", "phi",
    "varphi", "chi", "psi", "omega", "Gamma", "Delta", "Theta", "Lambda", "Xi", "Pi", "Sigma", "Upsilon", "Phi",
    "Psi", "Omega",
))
#: The only commands a checked text may write (fix round 7): the parser's
#: functions, relations and operators, and Greek letters. Any other command
#: (\mathrm, \operatorname, \text, \mathbf, \prime, ...) refuses.
_ALLOWED_COMMANDS = _MATH_COMMANDS | _GREEK | frozenset((
    "infty", "pm", "mp", "le", "ge", "leq", "geq", "ne", "neq", "lt", "gt", "approx",
))
_IDENT = r"(?:(?<![\\A-Za-z])([A-Za-z])|\\([A-Za-z]+))"
_SUBSCRIPT = r"(?:\s*_\s*(?:\{[^{}]*\}|\\[A-Za-z]+|[A-Za-z0-9]))?"
#: An identifier (subscript allowed) applied to an argument, or primed: a NAME.
_NAME_USE = re.compile(_IDENT + _SUBSCRIPT + r"(?:\s*(?:'|\\prime|\^\s*\{?\s*\\prime\s*\}?))*"
                       r"\s*(?:\\left\s*)?\(|" + _IDENT + _SUBSCRIPT + r"\s*(?:'|\^\s*\{?\s*\\prime)")
_WRAPPER = re.compile(r"\\([A-Za-z]+)\s*\{([^{}]*)\}")
_SUBSCRIPTED = re.compile(_IDENT + r"'*\s*_")


def _unwrapped(text):
    """``text`` with formatting wrappers taken off (``\\mathrm{f}`` is ``f``),
    so a formatted name is still the name (fix round 7)."""
    text = str(text or "")
    for _ in range(8):
        new = _WRAPPER.sub(lambda match: match.group(2) if match.group(1) not in _ALLOWED_COMMANDS
                           else match.group(0), text)
        if new == text:
            break
        text = new
    return text


def scan_names(texts):
    """Fix round 7: every NAME in ``texts``: any identifier written directly
    before ``(`` (whitespace, ``\\left``, a subscript or primes between) or
    with a prime, canonical (formatting off, ``\\alpha`` is ``alpha``, the
    subscript dropped to its base). Conservative: an extra name only costs a
    check. The parser's built-in functions are excepted."""
    out = set()
    for text in texts:
        for match in _NAME_USE.finditer(_unwrapped(text)):
            groups = [group for group in match.groups() if group]
            name = groups[0] if groups else None
            if name and name not in _MATH_COMMANDS:
                out.add(canonical(name))
    return out


def identifiers(text):
    """The identifiers a text writes, canonical: Greek commands and single letters."""
    plain = _unwrapped(text)
    out = {name for name in re.findall(r"\\([A-Za-z]+)", plain) if name in _GREEK}
    out |= set(re.findall(r"[A-Za-z]", re.sub(r"\\[A-Za-z]+", " ", plain)))
    return out


def name_rule(text, names):
    """Fix round 7, rule 1: the reason ``text`` may not be checked, or ''.
    Refused: any command outside :data:`_ALLOWED_COMMANDS` (formatting
    included), any subscript on an identifier, and any identifier that is a
    NAME (:func:`scan_names`)."""
    raw = str(text or "")
    if not raw.isascii():
        # Fix round 8, rule 2: the checked text is ASCII only.
        return "not_ascii"
    if re.search(r"\\[^A-Za-z]", raw) or "~" in raw:
        # Fix round 8, rule 2: no spacing (\\, \\! \\; ...) or symbol command.
        return "spacing_or_symbol_command"
    for command in re.findall(r"\\([A-Za-z]+)", raw):
        if command not in _ALLOWED_COMMANDS:
            return "formatting_or_command"
    if _SUBSCRIPTED.search(raw):
        for match in _SUBSCRIPTED.finditer(raw):
            command = match.group(2)
            if command is None or command in _GREEK:
                return "subscript"
    if identifiers(raw) & names:
        return "names_a_name"
    return ""


_SPACING = re.compile(r"\\[!,;:> ]|\\qquad(?![A-Za-z])|\\quad(?![A-Za-z])|~")
_FORMAT_COMMANDS = re.compile(
    r"\\(?:mathrm|operatorname|text|textrm|textit|textbf|textsf|texttt|textnormal|mathbf|mathit|mathsf|mathtt|"
    r"mathcal|mathbb|mathfrak|mathscr|mathnormal|boldsymbol|bm|mbox|hbox|rm|it|bf|sf|tt|cal|displaystyle|"
    r"textstyle|scriptstyle)(?![A-Za-z])")
_SIZED = r"\\(?:left|right|bigl|bigr|Bigl|Bigr|biggl|biggr|Biggl|Biggr|big|Big|bigg|Bigg)(?![A-Za-z])"
_NOTATION_TOKEN = re.compile(r"\\[A-Za-z]+|\\.|.", re.S)
_NOTATION_NEXT = ("(", "[", "'", "\\prime")


def normalised(text):
    """Fix round 8, rule 1: a text reduced so no spelling hides function
    notation: spacing commands and ``~`` out, all whitespace out, formatting
    commands out (their argument kept), every brace out, ``\\left.`` and
    ``\\right.`` out, and ``\\left``/``\\right`` before any other delimiter
    out (the delimiter kept, so ``f\\left(x\\right)`` is ``f(x)``)."""
    out = _SPACING.sub("", str(text or ""))
    out = re.sub(r"\s+", "", out)
    out = _FORMAT_COMMANDS.sub("", out)
    out = out.replace("{", "").replace("}", "")
    out = re.sub(_SIZED + r"\.", "", out)
    return re.sub(_SIZED, "", out)


def function_notation(text):
    """Fix round 8, rule 1: whether a (normalised) text uses function
    notation: any letter (Unicode ``str.isalpha``) or command, other than the
    parser's built-ins, immediately followed by ``(``, ``[``, ``'``,
    ``\\prime`` or ``^\\prime``. Over-matching is intended: prose such as
    "f (x)" or "on [0, 1]" counts."""
    tokens = _NOTATION_TOKEN.findall(normalised(text))
    for index, token in enumerate(tokens[:-1]):
        after = tokens[index + 1]
        primed = after == "^" and index + 2 < len(tokens) and tokens[index + 2] == "\\prime"
        if after not in _NOTATION_NEXT and not primed:
            continue
        if token.startswith("\\") and len(token) > 1 and token[1:].isalpha():
            if token[1:] not in _MATH_COMMANDS:
                return True
        elif len(token) == 1 and token.isalpha():
            return True
    return False


def applies_a_name(tree, source):
    """Fix round 6: whether the written text applies a name as a function
    (``f(...)``, ``\\phi(...)``, ``g'(x)``), read from the syntax: the parse
    tree's function applications and primes, and any identifier or command
    (other than the parser's own functions) written before an argument."""
    for node in tree.iter_subtrees():
        if str(node.data) in ("function_applied", "symbol_prime", "matrix_prime"):
            return True
    for token in tree.scan_values(lambda value: isinstance(value, Token)):
        if str(token.type) in ("PRIMES", "PRIMES_VIA_CMD", "CMD_PRIME") or "'" in str(token):
            return True
    for match in _APPLIED.finditer(source):
        command = match.group(1)
        if command is None or command not in _MATH_COMMANDS:
            return True
    return False


def explicit(expression):
    """``expression`` when it names no function (fix round 6: definitions
    are never resolved), else refused."""
    if expression.atoms(AppliedUndef):
        raise NotChecked("applies_a_name")
    for symbol in expression.atoms(sympy.Symbol):
        if "'" in symbol.name:
            raise NotChecked("applies_a_name")
    return expression


OPERATORS = (sympy.Derivative, sympy.Integral, sympy.Limit, sympy.Sum)


def has_operator(expression):
    return any(expression.has(kind) for kind in OPERATORS)


def _operand(expression):
    operand = explicit(expression)
    if has_operator(operand):
        raise NotChecked("nested_operator")
    return operand


def classify(relation, declared_kind):
    """The parsed relation as a check: its kind, the operand, the variable,
    and the bounds or point, on explicit expressions only (fix round 6)."""
    if relation.op != "=":
        raise NotChecked("unsupported_relation")
    lhs = relation.lhs
    rhs = explicit(relation.rhs)
    if has_operator(rhs):
        raise NotChecked("operator_on_the_right")
    out = {"rhs": rhs}
    if isinstance(lhs, sympy.Derivative):
        if len(lhs.variable_count) != 1 or lhs.variable_count[0][1] != 1:
            raise NotChecked("unsupported_derivative")
        out.update(kind="differentiation", operand=_operand(lhs.expr), variable=lhs.variable_count[0][0])
        return out
    if isinstance(lhs, sympy.Integral):
        if len(lhs.limits) != 1:
            raise NotChecked("unsupported_integral")
        limit = lhs.limits[0]
        out.update(operand=_operand(lhs.function), variable=limit[0])
        if len(limit) == 3:
            out.update(lower=_operand(limit[1]), upper=_operand(limit[2]), definite=True)
            out["kind"] = "normalization" if declared_kind == "normalization" and rhs == 1 else "integration"
        elif len(limit) == 1:
            out.update(definite=False, kind="integration")
        else:
            raise NotChecked("unsupported_integral")
        return out
    if isinstance(lhs, sympy.Limit):
        out.update(kind="limit", operand=_operand(lhs.args[0]), variable=lhs.args[1],
                   point=_operand(lhs.args[2]), direction=str(lhs.args[3]))
        return out
    if isinstance(lhs, sympy.Sum):
        if len(lhs.limits) != 1 or len(lhs.limits[0]) != 3:
            raise NotChecked("unsupported_sum")
        index, lower, upper = lhs.limits[0]
        out.update(kind="sum", operand=_operand(lhs.function), variable=index,
                   lower=_operand(lower), upper=_operand(upper))
        return out
    resolved = _operand(lhs)
    if declared_kind == "solving":
        if not isinstance(resolved, sympy.Symbol) or rhs.has(resolved):
            raise NotChecked("not_a_solution")
        out.update(kind="solving", variable=resolved)
        return out
    out.update(kind="equivalence", lhs=resolved)
    return out


def solved_equation(claim, variable, names):
    """For ``x = value`` (fix rounds 7-8): the equation it solves, as a
    residual, read ONLY from the immediately preceding learner step (never
    an older one, never the problem: a first step is not checked). That text
    must be exactly one relation, pass the name rule, and have no
    restriction token in its written text (a denominator, log, root, or a
    power that is not a whole number). Otherwise nothing is checked."""

    def equation_of(text):
        if name_rule(text, names):
            raise NotChecked("equation_names")
        relation = read(text)
        if relation.op != "=":
            raise NotChecked("no_equation")
        if relation.applies:
            raise NotChecked("applies_a_name")
        if relation.spots or relation.restricted:
            raise NotChecked("restricted_domain")
        lhs, rhs = explicit(relation.lhs), explicit(relation.rhs)
        if has_operator(lhs) or has_operator(rhs):
            raise NotChecked("no_equation")
        residual = lhs - rhs
        if sympy.denom(sympy.together(residual)).has(variable):
            raise NotChecked("restricted_domain")
        if not residual.has(variable) or sympy.simplify(residual) == 0:
            raise NotChecked("no_equation")
        return residual

    earlier = list(claim.get("earlier") or [])
    if earlier:
        return equation_of(earlier[-1])
    # Fix round 8, rule 3: a first step that solves is never checked (no
    # equation of the problem is ever selected).
    raise NotChecked("first_step_solve")


def compare(claim, parsed):
    """Every declared field that is set must mean what was written, and the
    declared expression is required. Returns the disagreeing field, or ''."""
    kind = parsed["kind"]
    if claim.get("kind") != kind:
        return "kind"
    if not str(claim.get("expression") or "").strip():
        return "expression"
    relation = str(claim.get("relation") or "").strip()
    if relation and relation not in ("=", "=="):
        return "relation"
    if kind == "solving":
        if not agree(claim["expression"], parsed["equation"], equation=True):
            return "expression"
    elif kind == "equivalence":
        if not agree(claim["expression"], parsed["lhs"]):
            return "expression"
    elif not agree(claim["expression"], parsed["operand"]):
        return "expression"
    result = str(claim.get("result") or "").strip()
    if result and not agree(result, parsed["rhs"]):
        return "result"
    variable = str(claim.get("variable") or "").strip()
    if variable and "variable" in parsed and variable != parsed["variable"].name:
        return "variable"
    value = str(claim.get("value") or "").strip()
    if kind == "limit":
        if value and not agree(value, parsed["point"]):
            return "value"
    elif value:
        return "value"
    lower, upper = str(claim.get("lower") or "").strip(), str(claim.get("upper") or "").strip()
    if kind == "integration" and bool(lower and upper) != parsed["definite"]:
        return "bounds"
    if parsed.get("lower") is not None:
        if lower and not agree(lower, parsed["lower"]):
            return "lower"
        if upper and not agree(upper, parsed["upper"]):
            return "upper"
    elif lower or upper:
        return "bounds"
    return ""


# -- Deciding zero (fix round 1, F2) ------------------------------------------------------------

EXACT, NUMERIC = "exact", "numeric"


def _floats(expression):
    return bool(expression.atoms(sympy.Float))


def _value(expression, point=None):
    """A complex value at ``point`` (30 digits), or None when it has none."""
    try:
        number = complex(sympy.N(expression.subs(point) if point else expression, 30))
    except (TypeError, ValueError, ZeroDivisionError, OverflowError):
        return None
    if number != number or abs(number) == float("inf"):
        return None
    return number


def _tolerance(expression):
    """Zero within rounding: tight for exact numbers, relative to the
    magnitudes written for decimals (0.1 + 0.2 = 0.3)."""
    if not _floats(expression):
        return 1e-20
    scale = max([1.0] + [abs(float(atom)) for atom in expression.atoms(sympy.Float)])
    return 1e-12 * scale


def zero(value):
    """Whether ``value`` is identically zero, and how that was decided:
    ``(True, EXACT)`` when sympy simplifies it to zero; ``(False, EXACT)`` when
    an exact number is not zero, or when it is non-zero at every sampled point
    on BOTH sides of zero; ``(True, NUMERIC)`` when it vanishes at every
    sampled point on both sides but sympy could not prove it; ``(False,
    NUMERIC)`` for a decimal constant off zero; ``(None, None)`` when it
    cannot tell (zero on part of the samples only: an identity on a domain,
    such as ``Abs(x) = x``, which the step does not state; an operator sympy
    could not evaluate; or too few points evaluate). Fix round 1, F2."""
    simplified = sympy.simplify(value)
    if simplified == 0:
        return True, EXACT
    if has_operator(simplified):
        return None, None
    free = sorted(simplified.free_symbols, key=lambda s: s.name)
    if not free:
        if not _floats(simplified):
            if simplified.is_zero is False:
                return False, EXACT
            if simplified.is_zero is True:
                return True, EXACT
        number = _value(simplified)
        if number is None:
            return None, None
        return abs(number) <= _tolerance(simplified), NUMERIC
    rng = random.Random(11)
    tolerance = _tolerance(simplified)
    zeros = nonzeros = 0
    for index in range(16):
        # Both signs for every variable: the first point all positive, the
        # second all negative, the rest mixed.
        if index == 0:
            signs = {s: 1 for s in free}
        elif index == 1:
            signs = {s: -1 for s in free}
        else:
            signs = {s: rng.choice((-1, 1)) for s in free}
        point = {s: sympy.Rational(rng.randint(30, 270), 100) * signs[s] for s in free}
        number = _value(simplified, point)
        if number is None:
            continue
        if abs(number) <= tolerance:
            zeros += 1
        else:
            nonzeros += 1
    if zeros + nonzeros < 6:
        return None, None
    if nonzeros == 0:
        return True, NUMERIC
    if zeros == 0:
        return False, EXACT if not _floats(simplified) else NUMERIC
    return None, None


# -- The checks on the parsed relation ----------------------------------------------------------

def residual(parsed, result):
    """What must vanish for the parsed relation to hold with ``result`` as
    its right side."""
    kind = parsed["kind"]
    if kind == "equivalence":
        return parsed["lhs"] - result
    variable = parsed.get("variable")
    if kind == "differentiation":
        return sympy.diff(parsed["operand"], variable) - result
    if kind in ("integration", "normalization"):
        if parsed["definite"]:
            return sympy.integrate(parsed["operand"], (variable, parsed["lower"], parsed["upper"])) - result
        # An antiderivative, up to a constant.
        return sympy.diff(result, variable) - parsed["operand"]
    if kind == "limit":
        return sympy.limit(parsed["operand"], variable, parsed["point"], parsed["direction"]) - result
    if kind == "sum":
        return sympy.summation(parsed["operand"], (variable, parsed["lower"], parsed["upper"])) - result
    if kind == "solving":
        return parsed["equation"].subs(variable, result)
    raise NotChecked("unsupported_kind")


def truth(parsed):
    """The true right side where sympy computes one (the positive control)."""
    kind = parsed["kind"]
    if kind == "equivalence":
        return parsed["lhs"]
    variable = parsed.get("variable")
    if kind == "differentiation":
        value = sympy.diff(parsed["operand"], variable)
    elif kind in ("integration", "normalization"):
        if parsed["definite"]:
            value = sympy.integrate(parsed["operand"], (variable, parsed["lower"], parsed["upper"]))
        else:
            value = sympy.integrate(parsed["operand"], variable)
    elif kind == "limit":
        value = sympy.limit(parsed["operand"], variable, parsed["point"], parsed["direction"])
    elif kind == "sum":
        value = sympy.summation(parsed["operand"], (variable, parsed["lower"], parsed["upper"]))
    elif kind == "solving":
        roots = sympy.solve(parsed["equation"], variable)
        value = roots[0] if roots else None
    else:
        value = None
    return None if value is None or has_operator(value) else value


def perturbed(parsed, value):
    """A wrong right side the check must reject: one more, and for an
    antiderivative (equal up to a constant) one more times the variable; for
    solving, the first of one, two or three more that is not itself a root."""
    if parsed["kind"] == "solving":
        for offset in (1, 2, 3):
            if sympy.simplify(parsed["equation"].subs(parsed["variable"], value + offset)) != 0:
                return value + offset
        return value + 1
    out = value + 1
    if parsed["kind"] == "integration" and not parsed["definite"]:
        out = out + parsed["variable"]
    return out


def model(reason, bound=False):
    return {"method": "model", "holds": None, "reason": reason, "bound": bound}


def run(claim, checkable):
    if claim.get("kind") not in checkable:
        return model("kind_not_checked")
    try:
        # Fix rounds 6-7 (the orchestrator's rulings): names are never
        # resolved. Every NAME in the problem, the earlier steps and the text
        # itself, by a blunt token scan; a text that formats, subscripts or
        # writes one is never checked.
        context = [claim.get("problem")] + list(claim.get("earlier") or []) + list(claim.get("names_context") or [])
        if any(function_notation(text) for text in context):
            # Fix round 8, rule 1 (the orchestrator's ruling): function
            # notation anywhere in the problem (prose included) or an earlier
            # step disables every check on this problem.
            raise NotChecked("function_notation")
        names = scan_names(context + [claim.get("text")])
        refused = name_rule(claim.get("text"), names)
        if refused:
            raise NotChecked(refused)
        relation = read(claim.get("text"))
        if relation.applies:
            raise NotChecked("applies_a_name")
        parsed = classify(relation, claim.get("kind"))
        if parsed["kind"] == "solving" and (relation.spots or relation.restricted):
            # Any restriction token in the step's own text (fix round 6).
            raise NotChecked("restricted_domain")
        if parsed["kind"] == "solving":
            parsed["equation"] = solved_equation(claim, parsed["variable"], names)
        disagreement = compare(claim, parsed)
    except NotChecked as exc:
        return model(str(exc)[:120])
    if disagreement:
        return model("declaration_disagrees:" + disagreement)
    written = parsed["rhs"]
    true = truth(parsed)
    if true is not None:
        # The controls are taken around the TRUE result (sympy's): it must be
        # accepted, and a perturbed one rejected; only then does the verdict
        # on what was written mean anything.
        if zero(residual(parsed, true))[0] is not True:
            return model("the positive control was rejected", True)
        if zero(residual(parsed, perturbed(parsed, true)))[0] is not False:
            return model("the negative control was accepted", True)
    elif zero(residual(parsed, perturbed(parsed, written)))[0] is not False:
        return model("the negative control was accepted", True)
    difference = residual(parsed, written)
    verdict, how = zero(difference)
    if verdict is None:
        return model("holds only on part of the domain, or undecided", True)
    if verdict is False and sympy.simplify(difference).free_symbols:
        # Not an identity, but it still has unknowns: the step may be an
        # equation to solve, so "doesn't follow" is not ours to say.
        return model("not an identity; may be an equation", True)
    if how == EXACT:
        return {"method": "checked", "holds": bool(verdict), "reason": "", "bound": True}
    return {"method": "checked_numerically", "holds": bool(verdict), "reason": "sampled points on both signs",
            "bound": True}


with open(workdir + "/input.json", encoding="utf-8") as handle:
    payload = json.load(handle)
checkable = set(payload.get("checkable") or [])
results = []
for claim in payload["claims"]:
    entry = {"index": claim["index"]}
    try:
        entry.update(bounded(payload.get("per_check_seconds", 5), run, claim, checkable))
    except BaseException as exc:
        entry.update(model(type(exc).__name__))
    results.append(entry)
sys.stdout.write(MARKER + json.dumps({"results": results}, sort_keys=True, default=str))
sys.stdout.flush()
'''


def sandbox_ready() -> bool:
    from learnloop.content.authoring.pf_sandbox import sandbox_available

    return sandbox_available()


def run_checks(claims: Sequence[SymbolicClaim], *, limits: Any = None,
               run: Callable[..., Any] | None = None) -> tuple[list[SymbolicOutcome], str | None]:
    """Run the declared claims in the sandbox; ``(outcomes, problem)``.
    ``problem`` names why nothing ran (``sandbox_unavailable``,
    ``sandbox_failed``); every outcome is then the model's reading. A
    verdict counts only when the harness says the written text parsed and
    the declaration agreed with it (``bound``)."""

    from learnloop.content.authoring.pf_sandbox import SandboxLimits, SandboxUnavailable, run_sandboxed_python

    declared = [claim for claim in claims if claim.kind in KINDS][:MAX_CHECKS]
    if not declared:
        return [], None
    fallback = [SymbolicOutcome(claim.index, MODEL, None, "not checked") for claim in declared]
    # Fix round 4, item 1: a claim that would need clipping is not checked.
    too_long = {claim.index: SymbolicOutcome(claim.index, MODEL, None, f"too_long:{reason}")
                for claim in declared if (reason := claim.oversized()) is not None}
    sent = [claim for claim in declared if claim.index not in too_long]
    if not sent:
        return [too_long[claim.index] for claim in declared], None
    kwargs: dict[str, Any] = {"limits": limits or SandboxLimits(cpu_seconds=20, wall_seconds=30)}
    if run is not None:
        kwargs["run"] = run
    try:
        result = run_sandboxed_python(HARNESS, {"claims": [claim.payload() for claim in sent],
                                                "checkable": list(CHECKABLE_KINDS),
                                                "per_check_seconds": 5}, **kwargs)
    except SandboxUnavailable:
        return fallback, "sandbox_unavailable"
    if not result.ok or not isinstance(result.output, Mapping):
        return fallback, "sandbox_failed"
    found: dict[int, SymbolicOutcome] = {}
    for entry in result.output.get("results") or ():
        try:
            index = int(entry.get("index"))
        except (TypeError, ValueError):
            continue
        bound = entry.get("bound") is True
        method = str(entry.get("method") or MODEL)
        if method not in (CHECKED, CHECKED_NUMERICALLY) or not bound:
            method = MODEL
        value = entry.get("holds")
        found[index] = SymbolicOutcome(index, method, bool(value) if method != MODEL and isinstance(value, bool)
                                       else None, str(entry.get("reason") or "")[:200], bound=bound)
    found.update(too_long)
    return [found.get(claim.index, SymbolicOutcome(claim.index, MODEL, None, "no result")) for claim in declared], None


__all__ = [
    "CHECKABLE_KINDS",
    "CHECKED",
    "CHECKED_NUMERICALLY",
    "HARNESS",
    "KINDS",
    "MODEL",
    "SymbolicClaim",
    "SymbolicOutcome",
    "run_checks",
    "sandbox_ready",
]
