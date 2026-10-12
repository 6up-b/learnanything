"""Symbolic answer check for the tutor and reader reveal detectors (R2).

Embeddings are never the sole signal for answer equivalence, so a math answer
also goes through this check: every math run in the model's text is compared
with the expected answer by the offline review's comparison (exact normalized
text, exact arithmetic, then SymPy). Model text reaches SymPy only through
``safe_math_text``, whose alphabet excludes anything SymPy's parser could
evaluate as Python; anything else is undecidable, never parsed. A function
application (``sin(x)``, ``sqrt(x)``) is math even without a numeral.

An occurrence of the answer's value is only a shortlist signal: "read page
144", a fraction in an unrelated example or a rejected alternative all contain
it. A match decides a reveal (``judge='verifier'``) only when its link to the
item is established: one equation holds the item's own expression, as written
in the item (up to spacing, brackets and notation), on one side and the
answer in its own form on another, so the text works the item to its answer
(``12 * 12 = 144`` for "Compute 12 * 12"). The relation must hold for the
item: the item's expression is itself verified equal to the answer, so a
different equation sharing a fragment with the item (``x + 1 = 2`` for "Solve
x + 1 = 3") or a wrong one (``12 * 12 = 124``) only shortlists. Equality alone
cannot link, since every expression of a "compute" item equals its answer and
a restatement (``(x+1)^2 = (x+1)(x+1)`` for "Expand (x+1)^2") is not a reveal.
The answer's own form is its normalized text, or for a numeric answer any
plain number equal to it (a rounding). An item whose prompt already states its
answer never links. Each distinct run is compared once, and every equation
reuses that result, so an earlier occurrence ("page 144") never hides a later
worked equation.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import re
from typing import Any, Literal

from learnloop.diagnosis.offline_review.probes import answers_differ, answers_equal, safe_math_text

SYMBOLIC_VERSION = "contamination-symbolic-v3"
#: Bounded work per answer: the first runs in reading order are checked.
MAX_CANDIDATES = 48
#: Bounded item expressions a match may link to.
MAX_LINKS = 16
_ANSWER_KEYS = ("final_answer", "answer", "value", "result")
_FUNCTIONS = ("sqrt", "sin", "cos", "tan", "asin", "acos", "atan", "sinh", "cosh", "tanh", "exp", "log", "ln", "Abs")

_UNICODE = str.maketrans({
    "\u2212": "-", "\u00d7": "*", "\u00b7": "*", "\u22c5": "*", "\u2219": "*",
    "\u00f7": "/", "\u00b2": "^2", "\u00b3": "^3", "\u03c0": " pi ",
})
_FUNCTION_CALL = re.compile(r"(?<![A-Za-z_])(?:" + "|".join(_FUNCTIONS) + r")\s*\(")
_PI = re.compile(r"(?<![A-Za-z_])pi(?![A-Za-z_])")
#: Brackets around one atom, never a function call's: ``(2)/(3)`` is ``2/3``.
_ATOM_BRACKETS = re.compile(r"(?<![A-Za-z_])\(([A-Za-z0-9_.]+)\)")
#: A plain number: an integer, a decimal or a fraction of them.
_VALUE = re.compile(r"^-?(?:\d+(?:\.\d+)?|\.\d+)(?:/(?:\d+(?:\.\d+)?|\.\d+))?$")
_FRAC = re.compile(r"\\[dt]?frac\s*\{([^{}]*)\}\s*\{([^{}]*)\}")
_SQRT = re.compile(r"\\sqrt\s*\{([^{}]*)\}")
_BOXED = re.compile(r"\\boxed\s*\{([^{}]*)\}")
_BRACED_POWER = re.compile(r"\^\s*\{([^{}]*)\}")
_LATEX_WORDS = (
    (r"\cdot", "*"), (r"\times", "*"), (r"\div", "/"), (r"\pi", " pi "),
    (r"\left", " "), (r"\right", " "), (r"\,", " "), (r"\;", " "), (r"\!", ""),
    (r"\(", " "), (r"\)", " "), (r"\[", " "), (r"\]", " "),
)
_LINE_MARKERS = re.compile(r"^[ \t]*(?:[-*+>]|#+|\d+[.)])[ \t]+", re.MULTILINE)
_ASSIGNMENT = re.compile(r"^\s*[A-Za-z]\s*=\s*(.+)$")
_TOKEN = re.compile(
    r"(?P<number>\d+(?:\.\d+)?|\.\d+)"
    r"|(?P<word>[A-Za-z_]+)"
    r"|(?P<op>\*\*|[-+*/^()])"
    r"|(?P<eq>=)"
    r"|(?P<space>[ \t]+)"
    r"|(?P<other>.)",
    re.DOTALL,
)


@dataclass(frozen=True)
class SymbolicResult:
    status: Literal["match", "no_match", "not_math"]
    expected: str | None = None
    matched: str | None = None
    method: str | None = None
    distinctive: bool = False
    checked: int = 0
    #: The item's own expression the matched equation also holds, if any.
    link: str | None = None

    @property
    def linked(self) -> bool:
        return self.link is not None

    @property
    def decides(self) -> bool:
        """A verifier verdict: a match whose link to the item is established."""

        return self.status == "match" and self.linked

    def as_dict(self) -> dict[str, Any]:
        return {**asdict(self), "linked": self.linked, "decides": self.decides, "version": SYMBOLIC_VERSION}


def normalize_math(text: str) -> str:
    """Plain ASCII arithmetic from common LaTeX and Unicode notation."""

    value = (text or "").translate(_UNICODE)
    for _ in range(6):  # innermost first; nested fractions unwind in turns
        updated = _FRAC.sub(r"(\1)/(\2)", value)
        updated = _SQRT.sub(r"sqrt(\1)", updated)
        updated = _BOXED.sub(r"\1", updated)
        updated = _BRACED_POWER.sub(r"^(\1)", updated)
        if updated == value:
            break
        value = updated
    for latex, plain in _LATEX_WORDS:
        value = value.replace(latex, plain)
    value = value.replace("$", " ").replace("{", "(").replace("}", ")")
    return _LINE_MARKERS.sub("", value)


def _has_math(text: str) -> bool:
    return (
        bool(re.search(r"\d", text))
        or bool(re.search(r"[A-Za-z].*[-+*/^]|[-+*/^].*[A-Za-z]", text))
        or bool(_FUNCTION_CALL.search(text)) or bool(_PI.search(text))
    )


def _is_expression(text: str) -> bool:
    """An operation, not a bare value: an item expression a match may link to."""

    return bool(re.search(r"[-+*/^]", text)) or bool(_FUNCTION_CALL.search(text))


def distinctive(text: str) -> bool:
    """Distinctive enough that its presence is not incidental."""

    compact = text.replace(" ", "")
    if "/" in compact or any(f"{name}(" in compact for name in _FUNCTIONS):
        return True
    if re.search(r"[A-Za-z]", compact) and re.search(r"[-+*/^]", compact):
        return True
    significant = re.sub(r"[^0-9]", "", compact).lstrip("0")
    return len(significant) >= 3


def math_answer(expected: str | dict[str, Any] | None) -> str | None:
    """The expected answer as safe math text, or ``None`` when it is not math."""

    if isinstance(expected, dict):
        value = next((expected[key] for key in _ANSWER_KEYS if isinstance(expected.get(key), (str, int, float))
                      and not isinstance(expected.get(key), bool)), None)
        if value is None:
            return None
        expected = str(value)
    if not isinstance(expected, str):
        return None
    text = " ".join(normalize_math(expected).split()).rstrip(".").strip()
    assignment = _ASSIGNMENT.match(text)
    if assignment:
        text = assignment.group(1).strip()
    if not text or not safe_math_text(text) or not _has_math(text):
        return None
    return text


def math_equations(text: str) -> list[list[str]]:
    """The sides of every maximal arithmetic run in ``text``, in reading order.

    A run is numbers, single-letter symbols, function names, operators and
    brackets; prose words, commas and sentence punctuation end it. ``=`` splits
    a run into sides. A side with no math (no digit, operator, function
    application or ``pi``) is dropped, and the total is bounded.
    """

    equations: list[list[str]] = []
    current: list[str] = []
    total = 0

    def flush() -> None:
        nonlocal total
        sides, side = [], []
        for token in current:
            if token == "=":
                sides.append(side)
                side = []
            else:
                side.append(token)
        sides.append(side)
        kept = []
        for parts in sides:
            candidate = "".join(parts).strip()
            if candidate and _has_math(candidate) and total < MAX_CANDIDATES:
                kept.append(candidate)
                total += 1
        if kept:
            equations.append(kept)
        current.clear()

    for match in _TOKEN.finditer(normalize_math(text)):
        kind, value = match.lastgroup, match.group(0)
        if kind == "word" and not (len(value) == 1 or value in _FUNCTIONS or value == "pi"):
            kind = "other"
        if kind in {"number", "word", "op", "eq"} or (kind == "space" and current):
            current.append(value)
        else:
            flush()
        if total >= MAX_CANDIDATES:
            break
    flush()
    return equations


def math_runs(text: str) -> list[str]:
    """Each distinct side of :func:`math_equations`, in reading order."""

    return list(dict.fromkeys(side for sides in math_equations(text) for side in sides))


def _equal(candidate: str, target: str) -> tuple[bool, str | None]:
    """Equal, or a decimal rounding of ``target`` within its stated precision."""

    if len(candidate) > 200:
        return False, None
    equal, method = answers_equal(candidate, target)
    if equal is True:
        return True, method
    differ, method = answers_differ(candidate, target)
    return differ is False, method


def canonical(text: str) -> str:
    """Notation-free text for "as written" comparisons: no spacing, atom brackets or LaTeX."""

    value = re.sub(r"\s+", "", normalize_math(text)).replace("**", "^").rstrip(".")
    for _ in range(6):
        updated = _ATOM_BRACKETS.sub(r"\1", value)
        if updated == value:
            break
        value = updated
    return value


def _item_expressions(prompt: str | None, target: str) -> set[str]:
    """The item's own expressions, as written; none when the prompt states its answer."""

    if not prompt:
        return set()
    runs = math_runs(prompt)
    if canonical(target) in {canonical(side) for side in runs}:
        return set()
    return {canonical(side) for side in [side for side in runs if _is_expression(side)][:MAX_LINKS]}


def _answer_form(side: str, target: str) -> bool:
    """``side`` (already equal to ``target``) is the answer itself, not an expression of it."""

    written, answer = canonical(side), canonical(target)
    return written == answer or bool(_VALUE.match(written) and _VALUE.match(answer))


def symbolic_check(
    answer_text: str, expected: str | dict[str, Any] | None, *, prompt: str | None = None,
) -> SymbolicResult:
    """Does ``answer_text`` contain an expression equal to the expected answer?

    Equality is exact (text, arithmetic or SymPy), or a decimal rounding of the
    expected value within its own stated precision. ``prompt`` is the item's
    own question text; a match links (and so decides) only as the module
    docstring describes."""

    target = math_answer(expected)
    if target is None:
        return SymbolicResult("not_math")
    links: set[str] | None = None
    first: SymbolicResult | None = None
    # Each distinct side is compared once, but every equation sees every
    # result: an earlier "page 144" must not hide a later "12 * 12 = 144".
    results: dict[str, tuple[bool, str | None]] = {}
    for sides in math_equations(answer_text):
        for side in sides:
            if side not in results:
                results[side] = _equal(side, target)
        matched = [(side, results[side][1]) for side in sides if results[side][0]]
        if not matched:
            continue
        if first is None:
            side, method = matched[0]
            first = SymbolicResult(
                "match", expected=target, matched=side, method=method,
                distinctive=distinctive(target) and distinctive(side),
            )
        if links is None:
            links = _item_expressions(prompt, target)
        if not links:
            continue
        equal_sides = {side for side, _method in matched}
        for side, method in matched:
            if not _answer_form(side, target):
                continue
            # The relation must hold for the item: the item's expression is
            # itself verified equal to the answer. A shared fragment of a
            # different equation (``x + 1 = 2`` for "Solve x + 1 = 3") is not.
            link = next((canonical(other) for other in sides
                         if other != side and other in equal_sides and canonical(other) in links), None)
            if link is not None:
                return SymbolicResult(
                    "match", expected=target, matched=side, method=method,
                    distinctive=distinctive(target) and distinctive(side), checked=len(results), link=link,
                )
    if first is not None:
        return SymbolicResult(
            "match", expected=first.expected, matched=first.matched, method=first.method,
            distinctive=first.distinctive, checked=len(results),
        )
    return SymbolicResult("no_match", expected=target, checked=len(results))
