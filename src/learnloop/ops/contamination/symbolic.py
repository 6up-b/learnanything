"""Symbolic answer check for the tutor and reader reveal detectors (R2).

Embeddings are never the sole signal for answer equivalence, so a math answer
also goes through this check: every math run in the model's text is compared
with the expected answer by the offline review's comparison (exact normalized
text, exact arithmetic, then SymPy). Model text reaches SymPy only through
``safe_math_text``, whose alphabet excludes anything SymPy's parser could
evaluate as Python; anything else is undecidable, never parsed.

A match decides a reveal (``judge='verifier'``) only when both the expected
answer and the matched expression are distinctive: a fraction, at least three
significant digits, a function call, or a symbolic expression. A small
integer or a one-decimal rounding also appears in innocent explanations, so
such a match only shortlists the pair for the judge.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import re
from typing import Any, Literal

from learnloop.diagnosis.offline_review.probes import answers_differ, answers_equal, safe_math_text

SYMBOLIC_VERSION = "contamination-symbolic-v1"
#: Bounded work per answer: the first runs in reading order are checked.
MAX_CANDIDATES = 48
_ANSWER_KEYS = ("final_answer", "answer", "value", "result")
_FUNCTIONS = ("sqrt", "sin", "cos", "tan", "asin", "acos", "atan", "sinh", "cosh", "tanh", "exp", "log", "ln", "Abs")

_UNICODE = str.maketrans({
    "\u2212": "-", "\u00d7": "*", "\u00b7": "*", "\u22c5": "*", "\u2219": "*",
    "\u00f7": "/", "\u00b2": "^2", "\u00b3": "^3", "\u03c0": " pi ",
})
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

    @property
    def decides(self) -> bool:
        """A verifier verdict: a match where both sides are distinctive."""

        return self.status == "match" and self.distinctive

    def as_dict(self) -> dict[str, Any]:
        return {**asdict(self), "decides": self.decides, "version": SYMBOLIC_VERSION}


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
    return bool(re.search(r"\d", text)) or bool(re.search(r"[A-Za-z].*[-+*/^]|[-+*/^].*[A-Za-z]", text))


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


def math_runs(text: str) -> list[str]:
    """Each side of every maximal arithmetic run in ``text``, in reading order.

    A run is numbers, single-letter symbols, function names, operators and
    brackets; prose words, commas and sentence punctuation end it. ``=`` splits
    a run into sides. A side with no digit and no operator is not a candidate.
    """

    candidates: list[str] = []
    seen: set[str] = set()
    current: list[str] = []

    def flush() -> None:
        sides, side = [], []
        for token in current:
            if token == "=":
                sides.append(side)
                side = []
            else:
                side.append(token)
        sides.append(side)
        for parts in sides:
            candidate = "".join(parts).strip()
            if candidate and _has_math(candidate) and candidate not in seen:
                seen.add(candidate)
                candidates.append(candidate)
        current.clear()

    for match in _TOKEN.finditer(normalize_math(text)):
        kind, value = match.lastgroup, match.group(0)
        if kind == "word" and not (len(value) == 1 or value in _FUNCTIONS or value == "pi"):
            kind = "other"
        if kind in {"number", "word", "op", "eq"} or (kind == "space" and current):
            current.append(value)
        else:
            flush()
        if len(candidates) >= MAX_CANDIDATES:
            break
    flush()
    return candidates[:MAX_CANDIDATES]


def symbolic_check(answer_text: str, expected: str | dict[str, Any] | None) -> SymbolicResult:
    """Does ``answer_text`` contain an expression equal to the expected answer?

    Equality is exact (text, arithmetic or SymPy), or a decimal rounding of the
    expected value within its own stated precision."""

    target = math_answer(expected)
    if target is None:
        return SymbolicResult("not_math")
    checked = 0
    for candidate in math_runs(answer_text):
        if len(candidate) > 200:
            continue
        checked += 1
        equal, method = answers_equal(candidate, target)
        if equal is not True:
            differ, method = answers_differ(candidate, target)
            if differ is not False:
                continue
        return SymbolicResult(
            "match", expected=target, matched=candidate, method=method,
            distinctive=distinctive(target) and distinctive(candidate), checked=checked,
        )
    return SymbolicResult("no_match", expected=target, checked=checked)
