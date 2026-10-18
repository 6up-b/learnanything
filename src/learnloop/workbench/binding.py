"""Reader workbench RW2b: whether a declared transformation is the learner's own assertion.

A check (or a hint's claim) declares a transformation in sympy syntax; the
sandbox decides whether it holds. That verdict may speak for the learner's
step only when the transformation IS what the step asserts (fix round 1, F3;
re-review F3): a textual match of a fragment is not enough, because
``x + x = 2x + 1`` contains ``x + x`` and ``2x`` and a checked ``x+x → 2x``
would then promote a wrong step to *valid, checked*.

So the step's text is read as relations (pure code, no model): it is split at
separators outside brackets (line breaks, ``;``, ``:``, ``, ``, a sentence's
``.``, ``⇒``, connectives such as *so*, *and*, *or*, and qualifiers such as
*on*, *for*, *where*, whose conditions become relations of their own), then at
relations (``=``, ``<``, ``≤``, ...). A step binds a transformation only when:

* it asserts exactly ONE relation that the problem or an earlier step did not
  already state (a restatement asserts nothing new; any other relation is
  unchecked, so the step keeps the model's reading);
* that relation is the transformation's: ``=`` (an inequality's own relation),
  its right side the WHOLE result (``1`` for a normalization);
* its left side is the WHOLE input: equal to it (equivalence, inequality), the
  whole operand of the kind's operator (``d/dx(...)``, ``\\int ... dx``,
  ``\\lim``, ``\\sum``, ``[...]_a^b``), or a name (``F(x)``, ``f'(x)``,
  ``P(X ≤ 1/2)``) standing for a whole side the problem or an earlier step
  wrote. A step that starts with ``=`` continues the step before it: its left
  side is that step's last side;
* for solving, the relation is ``variable = result`` and the equation solved
  is written whole in the problem, an earlier step or this one.

Matching is textual after normalization (case, spacing, LaTeX grouping, ``**``
against ``^``, an implicit product); anything this reading cannot place stays
the model's reading, never a wrong *checked*.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
import re

_NORMAL_SWAPS = (("\\left", ""), ("\\right", ""), ("**", "^"), ("\\cdot", "*"), ("\\times", "*"), ("·", "*"),
                 ("×", "*"), ("≤", "<="), ("≥", ">="), ("\\leq", "<="), ("\\geq", ">="), ("\\le", "<="),
                 ("\\ge", ">="), ("−", "-"), ("\\,", ""), ("\\!", ""), ("\\;", ""), ("$", ""), ("{", ""),
                 ("}", ""))


def normal(text: str) -> str:
    """Text reduced for matching a declared expression to the learner's
    writing: case, spacing, LaTeX grouping, ``**`` against ``^`` and an
    implicit product do not matter (``2*x**2`` matches ``2x^2``); a product
    of two numbers keeps its sign (``6*7`` never matches ``67``)."""

    out = str(text or "").lower()
    for old, new in _NORMAL_SWAPS:
        out = out.replace(old, new)
    out = re.sub(r"\s+", "", out)
    return re.sub(r"(?<!\d)\*|\*(?!\d)", "", out)


def _unwrap(text: str) -> str:
    """``text`` without brackets that enclose all of it."""

    while len(text) >= 2 and (text[0], text[-1]) in (("(", ")"), ("[", "]")):
        depth = 0
        for index, char in enumerate(text):
            depth += char in "([{"
            depth -= char in ")]}"
            if depth == 0 and index < len(text) - 1:
                return text
        text = text[1:-1]
    return text


def same(left: str, right: str) -> bool:
    """Whether two expressions are written the same (:func:`normal`, outer brackets aside)."""

    a, b = _unwrap(normal(left)), _unwrap(normal(right))
    return bool(a) and a == b


# -- Reading a text as relations ---------------------------------------------------------------

_CLEAN = (("\\left", ""), ("\\right", ""), ("\\(", " "), ("\\)", " "), ("\\[", " "), ("\\]", " "), ("$", " "))
_RELATIONS = {":=": "=", "\\leq": "<=", "\\geq": ">=", "\\neq": "!=", "\\le": "<=", "\\ge": ">=", "\\ne": "!=",
              "<=": "<=", ">=": ">=", "!=": "!=", "≤": "<=", "≥": ">=", "≠": "!=", "=": "=", "<": "<", ">": ">",
              "\\approx": "≈", "≈": "≈"}
_WORDS = ("so", "thus", "hence", "therefore", "then", "and", "or", "giving", "gives", "we have", "we get",
          "i get", "which is", "on", "for", "over", "where", "when", "whenever", "if", "with", "since",
          "because", "at")
_TOKEN = re.compile(
    r"(?P<sep><=>|<->|⇔|\\iff(?![A-Za-z])|\\Leftrightarrow|=>|⇒|⟹|\\Rightarrow|\\implies|\\therefore|->|→"
    r"|\\to(?![A-Za-z])|\n|(?<!\\);|(?<!\\):(?!=)|(?<!\\),\s|\.(?=\s|$)"
    r"|(?<![A-Za-z\\])(?:" + "|".join(word.replace(" ", r"\s+") for word in _WORDS) + r")(?![A-Za-z]))"
    r"|(?P<rel>:=|\\leq|\\geq|\\neq|\\le(?![A-Za-z])|\\ge(?![A-Za-z])|\\ne(?![A-Za-z])|\\approx"
    r"|<=|>=|!=|≤|≥|≠|≈|=|<|>)",
    re.IGNORECASE)


@dataclass(frozen=True)
class Relation:
    """``left op right`` as written (raw sides; :func:`normal` compares them)."""

    left: str
    op: str
    right: str

    def key(self) -> tuple[str, str, str]:
        return (_unwrap(normal(self.left)), self.op, _unwrap(normal(self.right)))


@dataclass(frozen=True)
class Reading:
    """A text's relations, its sides, and its last side (a following ``= ...`` continues it)."""

    relations: tuple[Relation, ...]
    sides: tuple[str, ...]
    last: str


def read(text: str, *, continues: str = "") -> Reading:
    """``text`` as relations (module docstring); ``continues`` is the side a
    leading ``=`` continues (the step before's last side)."""

    clean = str(text or "")
    for old, new in _CLEAN:
        clean = clean.replace(old, new)
    segments: list[tuple[list[str], list[str]]] = []
    sides: list[str] = []
    ops: list[str] = []
    buffer: list[str] = []
    depth, index = 0, 0
    while index < len(clean):
        char = clean[index]
        if char in "([{":
            depth += 1
        elif char in ")]}":
            depth = max(0, depth - 1)
        elif depth == 0:
            match = _TOKEN.match(clean, index)
            if match is not None:
                if match.lastgroup == "rel":
                    sides.append("".join(buffer).strip())
                    ops.append(_RELATIONS[match.group("rel").lower() if match.group("rel").startswith("\\")
                                          else match.group("rel")])
                else:
                    segments.append((sides + ["".join(buffer).strip()], ops))
                    sides, ops = [], []
                buffer = []
                index = match.end()
                continue
        buffer.append(char)
        index += 1
    segments.append((sides + ["".join(buffer).strip()], ops))
    relations: list[Relation] = []
    every: list[str] = []
    last = continues
    for parts, operators in segments:
        if not operators:
            if parts[0]:
                every.append(parts[0])
                last = parts[0]
            continue
        if not parts[0]:
            parts = [last] + parts[1:]
        for position, op in enumerate(operators):
            relations.append(Relation(parts[position], op, parts[position + 1]))
        every.extend(part for part in parts if part)
        last = parts[-1] or last
    return Reading(relations=tuple(relations), sides=tuple(every), last=last)


# -- The kinds' operators ----------------------------------------------------------------------

_BOUND = r"(?:\{[^{}]*\}|[^\s{}])"
_OPERANDS: dict[str, tuple[re.Pattern[str], ...]] = {
    "differentiation": (
        re.compile(r"^\\frac\{d\}\{d\s*[A-Za-z]\}\s*(?P<body>.+)$"),
        re.compile(r"^\\frac\{\\mathrm\{d\}\}\{\\mathrm\{d\}\s*[A-Za-z]\}\s*(?P<body>.+)$"),
        re.compile(r"^d\s*/\s*d\s*[A-Za-z]\s*(?P<body>.+)$"),
        re.compile(r"^\((?P<body>.+)\)\s*'$"),
    ),
    "integration": (
        re.compile(r"^\\int(?:_" + _BOUND + r"\^" + _BOUND + r")?\s*(?P<body>.+?)\s*(?:\\[,;!:]\s*)*"
                   r"(?:\\mathrm\{d\}|d)\s*[A-Za-z]$"),
    ),
    "limit": (re.compile(r"^\\lim_\{[^{}]*\}\s*(?P<body>.+)$"),),
    "sum": (re.compile(r"^\\sum_" + _BOUND + r"\^" + _BOUND + r"\s*(?P<body>.+)$"),),
    "boundary": (
        re.compile(r"^\[(?P<body>.+)\]_" + _BOUND + r"\^" + _BOUND + r"$"),
        re.compile(r"^(?P<body>.+?)\s*\\?\|_" + _BOUND + r"(?:\^" + _BOUND + r")?$"),
    ),
}
_OPERANDS["normalization"] = _OPERANDS["integration"]
_OPERANDS["substitution"] = _OPERANDS["boundary"]
#: A name that stands for a side written elsewhere: one letter, an optional
#: subscript, primes, and optionally one bracket of arguments.
_NAME = re.compile(r"^[a-z](?:_[a-z0-9]+)?'*(?:\([^()]*\))?$")


def _operand(kind: str, left: str) -> str | None:
    for pattern in _OPERANDS.get(kind, ()):
        match = pattern.match(left.strip())
        if match is not None:
            return match.group("body")
    return None


def binds(*, kind: str, expression: str, result: str, variable: str = "", relation: str = "", step: str,
          earlier: Sequence[str] = (), problem: str = "") -> bool:
    """Whether a declared transformation is what ``step`` asserts (module
    docstring); ``earlier`` are the steps before it, in order."""

    if not normal(expression):
        return False
    elsewhere = [read(problem)]
    last = ""
    for text in earlier:
        reading = read(text, continues=last)
        elsewhere.append(reading)
        last = reading.last
    here = read(step, continues=last)
    stated = {relation_.key() for reading in elsewhere for relation_ in reading.relations}
    sides = {_unwrap(normal(side)) for reading in elsewhere for side in reading.sides}
    sides.discard("")
    new = [relation_ for relation_ in here.relations if relation_.key() not in stated]
    if kind == "solving":
        equation = read(expression).relations
        solved = equation[0].key() if len(equation) == 1 else (_unwrap(normal(expression)), "=", "0")
        written = stated | {relation_.key() for relation_ in here.relations}
        new = [relation_ for relation_ in new if relation_.key() != solved]
        if solved not in written or len(new) != 1:
            return False
        [asserted] = new
        named = same(asserted.left, variable) if variable else bool(re.fullmatch(r"[a-z]", normal(asserted.left)))
        return asserted.op == "=" and named and same(asserted.right, result)
    if len(new) != 1:
        return False
    [asserted] = new
    wanted = (_RELATIONS.get(relation.strip(), relation.strip()) if kind == "inequality" else "=")
    if asserted.op != wanted or not same(asserted.right, "1" if kind == "normalization" else result):
        return False
    if kind in ("equivalence", "inequality") and same(asserted.left, expression):
        return True
    operand = _operand(kind, asserted.left)
    if operand is not None:
        return same(operand, expression)
    return bool(_NAME.match(normal(asserted.left))) and _unwrap(normal(expression)) in sides


__all__ = ["Reading", "Relation", "binds", "normal", "read", "same"]
