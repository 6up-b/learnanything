"""E1 grader probes (Slice 1 §13, added 2026-10-11).

* **Valid-alternative false rejection.** The generator writes a CORRECT
  derivation by a different method from the reference. A deterministic check
  of the SUBMITTED derivation (the text the grader sees) admits it only when
  the answer its concluding line ASSERTS (parsed from that line, never found
  as a token in it) is the declared final answer and equals the reference
  (exact normalized match, exact arithmetic, else SymPy equality), and EVERY
  relation in the derivation was checked and holds: an equation the checker
  cannot decide, or any other relation (``<``, ``\\neq``, ...), excludes the
  draft rather than being skipped. Prose steps are not machine-checkable; the
  spec accepts the exact key for them. The blind grader then grades it with
  the reference in context; a score below the maximum is a false rejection.
  Unverified alternatives are excluded from the denominator, never counted.
* **Real-vs-synthetic gap.** The generator writes an answer that is correct
  except for ONE planted error that changes the final answer. Its outcome is
  established independently of the generator's declaration: the answer its
  concluding line asserts must be the declared one and be decidably
  different from the reference (exact arithmetic, polynomial normal form or
  SymPy), so the answer cannot deserve full marks. Only that verified outcome
  is known; the declared criterion is kept as a label, never as ground truth.
  The blind grader's miss rate on these (full marks for a verified-wrong
  answer) is compared with its error rate on the owner's real answers where
  the owner adjudicated the grade.
* **Grade flip under paraphrase.** The generator rewords a real answer without
  changing its content; a pass/fail change between the two blind grades is a
  flip.

The relation checker (:func:`check_relations`) is deliberately narrow. It
tokenizes the whole text, takes every maximal run of math tokens that holds a
relation, and decides an equation chain only when each side parses as plain
arithmetic over numbers and single-letter symbols (``+ - * / ^``, brackets,
unary signs, implicit products such as ``2x``) into an exact polynomial normal
form. ``Let x = 1`` style definitions bind a symbol; constant sides are
compared exactly (to the stated precision for rounded decimals); identities
hold when the normal forms match. A chain next to a prose word that is not a
plain connective (``3 times 2 = 2``), a comma-joined tuple (``x, y = 2, 1``),
LaTeX, functions or a conditional equation is "unchecked".
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from fractions import Fraction
from typing import Any

from pydantic import Field

from learnloop.ai.schemas import WireModel
from learnloop.ai.transport import OperationClient, execute_structured_operation, render_structured_prompt
from learnloop.attempts.grading import resolved_rubric
from learnloop.vault.models import LoadedVault, PracticeItem

PROBE_PROMPT_VERSION = "grader-probes-v3"
PROBES = ("valid_alternative", "synthetic_error", "paraphrase")
_WS = re.compile(r"\s+")
#: Model text reaches SymPy (whose parser evaluates Python) only inside this
#: alphabet: digits, operators, brackets, single-letter symbols and a short
#: list of math function names. Anything else is "unverifiable", never parsed.
_SAFE_MATH = re.compile(r"^[0-9A-Za-z_+\-*/^().,\s]+$")
_SAFE_NAMES = frozenset(
    {"sqrt", "sin", "cos", "tan", "asin", "acos", "atan", "sinh", "cosh", "tanh", "exp", "log", "ln", "pi", "oo", "Abs"}
)
_NAME = re.compile(r"[A-Za-z_][A-Za-z_0-9]*")
_SAFE_MAX_LENGTH = 200


class ValidAlternativeDraft(WireModel):
    method_note: str = Field(description="One sentence: how this method differs from the reference.")
    derivation_md: str
    final_answer: str = Field(description="The final answer alone, in the reference's notation.")


class SyntheticErrorDraft(WireModel):
    planted_criterion_id: str
    error_description: str
    answer_md: str
    final_answer: str = Field(
        default="",
        description="The (wrong) final answer the planted error leads to, alone, in the reference's notation.",
    )


class ParaphraseDraft(WireModel):
    answer_md: str


def _item_payload(vault: LoadedVault, item: PracticeItem) -> dict[str, Any]:
    rubric = resolved_rubric(vault, item)
    expected = item.expected_answer
    return {
        "practice_item_id": item.id,
        "prompt": item.prompt,
        "reference_solution": expected if isinstance(expected, str) else json.dumps(expected, sort_keys=True),
        "rubric": [{"id": criterion.id, "points": criterion.points, "description": criterion.description} for criterion in rubric.criteria],
    }


_CHECKABLE_STEPS = (
    "Write every equation in plain ASCII arithmetic (digits, + - * / ^, parentheses and "
    "single-letter variables), one equation chain per sentence, so that a checker can "
    "verify each step."
)


def valid_alternative_prompt(vault: LoadedVault, item: PracticeItem) -> str:
    return render_structured_prompt(
        "learnloop grader probe: valid alternative",
        PROBE_PROMPT_VERSION,
        {
            "task": (
                "Write a COMPLETE and CORRECT solution to this item by a method that "
                "genuinely differs from the reference solution (a different route, "
                "decomposition or representation), written as a strong learner would. "
                f"{_CHECKABLE_STEPS} It must reach the reference's final answer, and "
                "its LAST line must be `Final answer: <answer>` stating only that "
                "answer. Put the same answer alone in `final_answer`, in the "
                "reference's notation."
            ),
            "context": _item_payload(vault, item),
        },
    )


def synthetic_error_prompt(vault: LoadedVault, item: PracticeItem) -> str:
    return render_structured_prompt(
        "learnloop grader probe: synthetic planted error",
        PROBE_PROMPT_VERSION,
        {
            "task": (
                "Write a learner answer that is fully correct EXCEPT for exactly one "
                "error that loses all of ONE rubric criterion's points and nothing else. "
                "The error must change the final answer: the LAST line of `answer_md` "
                "must be `Final answer: <answer>` stating only that (wrong) final "
                "answer, and `final_answer` must hold the same answer alone, in the "
                "reference's notation. Name the criterion in `planted_criterion_id` "
                "(one of the rubric ids) and describe the error. Write it like real "
                "learner work, with no hint that an error was planted."
            ),
            "context": _item_payload(vault, item),
        },
    )


def paraphrase_prompt(vault: LoadedVault, item: PracticeItem, answer: str) -> str:
    return render_structured_prompt(
        "learnloop grader probe: paraphrase",
        PROBE_PROMPT_VERSION,
        {
            "task": (
                "Reword this learner answer without changing its content: keep every "
                "step, claim, error and the final answer exactly as they are, change "
                "only wording, ordering of sentences where harmless, and formatting. "
                "Do not fix or add anything."
            ),
            "context": {**_item_payload(vault, item), "learner_answer_md": answer},
        },
    )


def request_valid_alternative(client: OperationClient, prompt: str) -> ValidAlternativeDraft:
    return execute_structured_operation(client, purpose="diagnosis_valid_alternative", prompt=prompt, result_model=ValidAlternativeDraft, isolated=True)


def request_synthetic_error(client: OperationClient, prompt: str) -> SyntheticErrorDraft:
    return execute_structured_operation(client, purpose="diagnosis_synthetic_error", prompt=prompt, result_model=SyntheticErrorDraft, isolated=True)


def request_paraphrase(client: OperationClient, prompt: str) -> ParaphraseDraft:
    return execute_structured_operation(client, purpose="diagnosis_paraphrase", prompt=prompt, result_model=ParaphraseDraft, isolated=True)


def _normalized(value: str) -> str:
    return _WS.sub(" ", value.strip().strip("$").strip()).casefold()


# ---------------------------------------------------------------------------
# SymPy, only on bounded safe text
# ---------------------------------------------------------------------------

_POWER_OPERAND = re.compile(r"-?(\d+|[A-Za-z]\w*|\([^()]*\))")


def _bounded_powers(text: str) -> bool:
    """No power towers or computed exponents (SymPy would build huge integers)."""

    compact = text.replace(" ", "").replace("**", "^")
    for index, char in enumerate(compact):
        if char != "^":
            continue
        rest = compact[index + 1 :]
        operand = _POWER_OPERAND.match(rest)
        if operand is None:
            return False
        value = operand.group(0)
        if "^" in value or re.search(r"[*/]", value) or any(len(number) > 3 for number in re.findall(r"\d+", value)):
            return False
        if rest[operand.end() :].startswith("^"):
            return False
    return True


def safe_math_text(text: str) -> bool:
    """Whether ``text`` may be handed to SymPy (its parser evaluates Python)."""

    if not text or len(text) > _SAFE_MAX_LENGTH or not _SAFE_MATH.match(text) or "__" in text:
        return False
    if re.search(r"\.\s*[A-Za-z_]", text):  # attribute access, e.g. pi.n(...)
        return False
    if not all(len(name) == 1 or name in _SAFE_NAMES for name in _NAME.findall(text)):
        return False
    return _bounded_powers(text)


def _sympy_equal(left: str, right: str) -> bool | None:
    """True/False when SymPy decides equality of two safe texts, else None.

    ``False`` needs a proof of difference (``Expr.equals`` finding a nonzero
    value), never just a simplification that did not reach zero.
    """

    left, right = left.strip().strip("$").strip(), right.strip().strip("$").strip()
    if not (safe_math_text(left) and safe_math_text(right)):
        return None
    try:
        import sympy
    except ImportError:  # pragma: no cover - sympy is a core dependency
        return None
    names: dict[str, Any] = {name: sympy.Symbol(name) for name in set(_NAME.findall(f"{left} {right}")) if len(name) == 1}
    names["ln"] = sympy.log
    try:
        difference = sympy.simplify(sympy.sympify(left, locals=names) - sympy.sympify(right, locals=names))
        if difference == 0:
            return True
        verdict = difference.equals(0)
    except Exception:  # noqa: BLE001 - any parse/eval failure is "undecidable"
        return None
    if verdict is True:
        return True
    if verdict is False:
        return False
    return None


# ---------------------------------------------------------------------------
# Exact arithmetic: tokens, a small parser, polynomial normal forms
# ---------------------------------------------------------------------------


class _Unchecked(Exception):
    """The text is not plain arithmetic the exact checker can decide."""


#: Connectives that may sit directly before / after an equation chain. Any
#: other adjacent prose word could be an operator in English ("3 times 2 = 2",
#: "1 + 1 = 2 squared"), so the chain is left unchecked.
_LEAD_WORDS = frozenset(
    {
        "let", "then", "so", "thus", "hence", "therefore", "since", "because", "we", "get", "gets",
        "have", "has", "obtain", "obtains", "find", "finds", "compute", "computing", "check", "checking",
        "note", "notice", "that", "where", "when", "if", "now", "next", "finally", "also", "gives",
        "giving", "yields", "is", "are", "becomes", "means", "set", "setting", "with", "substituting",
        "using", "for", "at", "start", "from", "clearly",
    }
)
_TRAIL_WORDS = frozenset({"so", "thus", "hence", "therefore", "since", "because", "which", "then", "giving", "gives", "where", "when", "as"})
_LATEX_RELATIONS = frozenset(
    {
        "neq", "ne", "leq", "le", "geq", "ge", "lt", "gt", "approx", "equiv", "implies", "iff", "to",
        "rightarrow", "Rightarrow", "leftarrow", "Leftarrow", "leftrightarrow", "Leftrightarrow", "sim",
        "simeq", "cong", "propto", "mapsto", "in", "subset", "subseteq", "ll", "gg", "longrightarrow",
    }
)
_LATEX_OPERATORS = {"cdot": "*", "times": "*", "div": "/"}
_LATEX_SPACES = frozenset({"left", "right", "quad", "qquad"})
_UNICODE = str.maketrans(
    {"\u2212": "-", "\u00d7": "*", "\u00b7": "*", "\u22c5": "*", "\u2219": "*", "\u00f7": "/", "\u00b2": "^2", "\u00b3": "^3", "`": " ", "$": " "}
)
_LATEX_DELIMITERS = re.compile(r"\\[()\[\]]|\\[,;:! ]")
#: Markdown bold markers (``**``) that are not a power between two operands.
_BOLD = re.compile(r"(?<![\w)])\*\*|\*\*(?![\w(])")
_LINE_MARKERS = re.compile(r"^[ \t]*(?:[-*+>]|#+|\d+[.)])[ \t]+", re.MULTILINE)
_TOKEN = re.compile(
    r"(?P<space>[ \t\r\f\v]+)"
    r"|(?P<newline>\n)"
    r"|(?P<command>\\[A-Za-z]+)"
    r"|(?P<number>\d+(?:\.\d+)?|\.\d+)"
    r"|(?P<word>[A-Za-z]+)"
    r"|(?P<relation><=|>=|!=|==|=>|<|>|[\u2260\u2264\u2265\u2248\u2261\u2192\u21d2\u21d4\u221d\u223c])"
    r"|(?P<eq>=)"
    r"|(?P<power>\*\*|\^)"
    r"|(?P<op>[+\-*/()])"
    r"|(?P<stop>[.:;!?](?=\s|$))"
    r"|(?P<comma>,)"
    r"|(?P<other>.)",
    re.DOTALL,
)
#: Token kinds that belong to a math run; everything else breaks a run.
_MATH_KINDS = frozenset({"num", "sym", "func", "eq", "rel", "pow", "op", "other"})
_MAX_TERMS = 256
_MAX_EXPONENT = 32
_MAX_BITS = 4096


@dataclass(frozen=True)
class _Token:
    kind: str
    text: str
    spaced: bool  # whitespace directly before it


def _normalize_math_text(text: str) -> str:
    text = (text or "").translate(_UNICODE)
    text = _LATEX_DELIMITERS.sub(" ", text)
    text = _BOLD.sub(" ", text)
    return _LINE_MARKERS.sub("", text)


def _tokens(text: str) -> list[_Token]:
    tokens: list[_Token] = []
    spaced = True
    for match in _TOKEN.finditer(_normalize_math_text(text)):
        kind, value = match.lastgroup or "other", match.group(0)
        if kind == "space":
            spaced = True
            continue
        if kind == "newline":
            tokens.append(_Token("stop", value, spaced))
            spaced = True
            continue
        if kind == "command":
            name = value[1:]
            if name in _LATEX_SPACES:
                spaced = True
                continue
            if name in _LATEX_OPERATORS:
                kind, value = "op", _LATEX_OPERATORS[name]
            else:
                kind = "rel" if name in _LATEX_RELATIONS else "other"
        elif kind == "number":
            kind = "num"
        elif kind == "word":
            kind = "sym" if len(value) == 1 else ("func" if value in _SAFE_NAMES else "prose")
        elif kind == "relation":
            kind = "rel"
        elif kind == "power":
            kind = "pow"
        tokens.append(_Token(kind, value, spaced))
        spaced = False
    return tokens


Poly = dict[tuple[tuple[str, int], ...], Fraction]


def _guard(poly: Poly) -> Poly:
    if len(poly) > _MAX_TERMS:
        raise _Unchecked("too many terms")
    for coefficient in poly.values():
        if coefficient.numerator.bit_length() > _MAX_BITS or coefficient.denominator.bit_length() > _MAX_BITS:
            raise _Unchecked("coefficient too large")
    return poly


def _const(value: Fraction) -> Poly:
    return {(): value} if value else {}


def _add(left: Poly, right: Poly, sign: int = 1) -> Poly:
    out = dict(left)
    for key, value in right.items():
        total = out.get(key, Fraction(0)) + sign * value
        if total:
            out[key] = total
        else:
            out.pop(key, None)
    return _guard(out)


def _mul(left: Poly, right: Poly) -> Poly:
    out: Poly = {}
    for key_a, value_a in left.items():
        for key_b, value_b in right.items():
            powers = dict(key_a)
            for name, exponent in key_b:
                powers[name] = powers.get(name, 0) + exponent
            key = tuple(sorted(powers.items()))
            total = out.get(key, Fraction(0)) + value_a * value_b
            if total:
                out[key] = total
            else:
                out.pop(key, None)
        if len(out) > _MAX_TERMS:
            raise _Unchecked("too many terms")
    return _guard(out)


def _constant_of(poly: Poly) -> Fraction | None:
    if not poly:
        return Fraction(0)
    if set(poly) == {()}:
        return poly[()]
    return None


def _power(base: Poly, exponent: Poly) -> Poly:
    value = _constant_of(exponent)
    if value is None or value.denominator != 1 or abs(value) > _MAX_EXPONENT:
        raise _Unchecked("exponent is not a small integer")
    n = int(value)
    if n < 0:
        constant = _constant_of(base)
        if not constant:
            raise _Unchecked("negative power of a non-constant or zero")
        return _guard(_const(constant**n))
    result = _const(Fraction(1))
    for _ in range(n):
        result = _mul(result, base)
    return result


class _Parser:
    """Recursive descent over one side: + - * / ^, unary signs, brackets."""

    def __init__(self, tokens: list[_Token], bindings: dict[str, Fraction]) -> None:
        self.tokens = self._with_implicit_products(tokens)
        self.bindings = bindings
        self.position = 0

    @staticmethod
    def _with_implicit_products(tokens: list[_Token]) -> list[_Token]:
        out: list[_Token] = []
        for token in tokens:
            if out and not token.spaced:
                previous = out[-1]
                left = previous.kind in {"num", "sym"} or previous.text == ")"
                right = token.kind == "sym" or token.text == "("
                if previous.kind == "sym" and token.text == "(":
                    raise _Unchecked("f(x) or x(y): ambiguous")
                if left and right:
                    out.append(_Token("op", "*", False))
            out.append(token)
        return out

    def _peek(self) -> _Token | None:
        return self.tokens[self.position] if self.position < len(self.tokens) else None

    def _take(self) -> _Token:
        token = self._peek()
        if token is None:
            raise _Unchecked("unexpected end")
        self.position += 1
        return token

    def parse(self) -> Poly:
        value = self._expression()
        if self._peek() is not None:
            raise _Unchecked("trailing tokens")
        return value

    def _expression(self) -> Poly:
        value = self._term()
        while (token := self._peek()) is not None and token.kind == "op" and token.text in "+-":
            self._take()
            value = _add(value, self._term(), 1 if token.text == "+" else -1)
        return value

    def _term(self) -> Poly:
        value = self._factor()
        while (token := self._peek()) is not None and token.kind == "op" and token.text in "*/":
            self._take()
            right = self._factor()
            if token.text == "*":
                value = _mul(value, right)
            else:
                divisor = _constant_of(right)
                if not divisor:
                    raise _Unchecked("division by zero or by a non-constant")
                value = _guard({key: coefficient / divisor for key, coefficient in value.items()})
        return value

    def _factor(self) -> Poly:
        token = self._peek()
        if token is not None and token.kind == "op" and token.text in "+-":
            self._take()
            value = self._factor()
            return value if token.text == "+" else _add({}, value, -1)
        return self._power()

    def _power(self) -> Poly:
        base = self._atom()
        token = self._peek()
        if token is not None and token.kind == "pow":
            self._take()
            return _power(base, self._factor())
        return base

    def _atom(self) -> Poly:
        token = self._take()
        if token.kind == "num":
            return _const(Fraction(token.text))
        if token.kind == "sym":
            if token.text in self.bindings:
                return _const(self.bindings[token.text])
            return {((token.text, 1),): Fraction(1)}
        if token.kind == "op" and token.text == "(":
            value = self._expression()
            closing = self._take()
            if closing.text != ")":
                raise _Unchecked("unbalanced bracket")
            return value
        raise _Unchecked(f"not arithmetic: {token.text!r}")


def _decimals(tokens: list[_Token]) -> int:
    return max((len(token.text.split(".", 1)[1]) for token in tokens if token.kind == "num" and "." in token.text), default=0)


def _tolerance(places: int) -> Fraction:
    """Half a unit in the last stated decimal place (0 for exact values)."""

    return Fraction(1, 2 * 10**places) if places else Fraction(0)


@dataclass
class RelationCheck:
    """What :func:`check_relations` decided about every relation in a text."""

    checked: int = 0
    false: list[str] = field(default_factory=list)
    unchecked: list[str] = field(default_factory=list)


def _runs(tokens: list[_Token]) -> list[tuple[int, int]]:
    runs: list[tuple[int, int]] = []
    start: int | None = None
    for index, token in enumerate(tokens):
        if token.kind in _MATH_KINDS:
            if start is None:
                start = index
        elif start is not None:
            runs.append((start, index))
            start = None
    if start is not None:
        runs.append((start, len(tokens)))
    return runs


def _bounded(tokens: list[_Token], runs: list[tuple[int, int]], has_relation: list[bool], position: int) -> bool:
    """Whether a relation run is cleanly delimited on both sides.

    A neighbouring prose word must be a plain connective; a comma must not
    join it to a math run that is not itself a relation (a tuple such as
    ``x, y = 2, 1`` or ``f(1, 2) = 3``).
    """

    start, end = runs[position]
    before = tokens[start - 1] if start > 0 else None
    after = tokens[end] if end < len(tokens) else None
    if before is not None:
        if before.kind == "prose" and before.text.casefold() not in _LEAD_WORDS:
            return False
        if before.kind == "comma" and position > 0 and runs[position - 1][1] == start - 1 and not has_relation[position - 1]:
            return False
    if after is not None:
        if after.kind == "prose" and after.text.casefold() not in _TRAIL_WORDS:
            return False
        if after.kind == "comma" and position + 1 < len(runs) and runs[position + 1][0] == end + 1 and not has_relation[position + 1]:
            return False
    return True


def _compare(left: Poly, right: Poly, places: int) -> str:
    """``holds``, ``false`` or ``unchecked`` for one adjacent pair of sides."""

    a, b = _constant_of(left), _constant_of(right)
    if a is not None and b is not None:
        return "holds" if abs(a - b) <= _tolerance(places) else "false"
    return "holds" if left == right else "unchecked"


def _check_chain(sides: list[list[_Token]], bindings: dict[str, Fraction]) -> str:
    """``holds``/``defined``/``false``/``unchecked`` for one equation chain."""

    first = sides[0]
    if len(first) == 1 and first[0].kind == "sym" and first[0].text not in bindings:
        # A definition: ``x = <constant> [= <constant> ...]`` binds x.
        values = [_Parser(side, bindings).parse() for side in sides[1:]]
        constants = [_constant_of(value) for value in values]
        if any(value is None for value in constants):
            return "unchecked"
        for (left_side, left), (right_side, right) in zip(zip(sides[1:], values), list(zip(sides[1:], values))[1:]):
            if _compare(left, right, max(_decimals(left_side), _decimals(right_side))) == "false":
                return "false"
        bindings[first[0].text] = constants[0]  # type: ignore[assignment]
        return "defined"
    values = [_Parser(side, bindings).parse() for side in sides]
    verdicts = [
        _compare(left, right, max(_decimals(left_side), _decimals(right_side)))
        for (left_side, left), (right_side, right) in zip(zip(sides, values), list(zip(sides, values))[1:])
    ]
    if "false" in verdicts:
        return "false"
    return "unchecked" if "unchecked" in verdicts else "holds"


def check_relations(text: str) -> RelationCheck:
    """Decide every relation in ``text``; nothing is skipped.

    Each maximal run of math tokens that holds a relation is one chain: it is
    ``checked`` (an identity, a true numeric equation or a definition),
    ``false`` (constant sides that differ beyond the stated precision) or
    ``unchecked`` (anything the exact checker cannot decide).
    """

    result = RelationCheck()
    tokens = _tokens(text)
    runs = _runs(tokens)
    has_relation = [any(token.kind in {"eq", "rel"} for token in tokens[start:end]) for start, end in runs]
    bindings: dict[str, Fraction] = {}
    for position, (start, end) in enumerate(runs):
        run = tokens[start:end]
        if not has_relation[position]:
            continue
        label = " ".join(token.text for token in run)
        if any(token.kind in {"rel", "other", "func"} for token in run) or not _bounded(tokens, runs, has_relation, position):
            result.unchecked.append(label)
            continue
        sides: list[list[_Token]] = [[]]
        for token in run:
            if token.kind == "eq":
                sides.append([])
            else:
                sides[-1].append(token)
        if any(not side for side in sides):
            result.unchecked.append(label)
            continue
        try:
            verdict = _check_chain(sides, bindings)
        except (_Unchecked, ZeroDivisionError, OverflowError, ValueError):
            verdict = "unchecked"
        if verdict == "false":
            result.false.append(label)
        elif verdict == "unchecked":
            result.unchecked.append(label)
        else:
            result.checked += 1
    return result


def _parse_expression(text: str) -> tuple[Poly, int] | None:
    """An answer as an exact polynomial (and its stated decimals), else None."""

    tokens = _tokens(text)
    if not tokens or any(token.kind not in {"num", "sym", "op", "pow"} for token in tokens):
        return None
    try:
        return _Parser(tokens, {}).parse(), _decimals(tokens)
    except (_Unchecked, ZeroDivisionError, OverflowError, ValueError):
        return None


# ---------------------------------------------------------------------------
# The asserted conclusion and answer comparison
# ---------------------------------------------------------------------------

_ANSWER_IS = re.compile(r"(?:final\s+answer|answer)\s*(?:is\b|:|=)\s*", re.IGNORECASE)
_CONCLUSION_LEAD = re.compile(r"^(?:so|thus|hence|therefore)\b[\s,:]*", re.IGNORECASE)
_ASSIGNMENT = re.compile(r"^[A-Za-z]\s*=\s*(.+)$")
_BOXED = re.compile(r"\\boxed\{([^{}]*)\}")


def asserted_conclusion(text: str) -> str | None:
    """The answer the LAST line asserts, parsed from that line's structure.

    ``Final answer: X`` / ``... the answer is X`` -> ``X``; ``Therefore X``
    -> ``X``; otherwise the whole line. The remainder is the assertion as
    written: ``2, not 3`` asserts ``2, not 3``, which is neither 2 nor 3.
    """

    lines = [line for line in (text or "").splitlines() if line.strip()]
    if not lines:
        return None
    line = _BOXED.sub(r"\1", lines[-1]).replace("$", " ")
    line = _LINE_MARKERS.sub("", _BOLD.sub(" ", line)).strip()
    matches = list(_ANSWER_IS.finditer(line))
    answer = line[matches[-1].end() :] if matches else _CONCLUSION_LEAD.sub("", line, count=1)
    answer = answer.strip().rstrip(".").strip()
    return answer or None


def _answers_equal(left: str, right: str) -> tuple[bool | None, str]:
    """(True/False/None, method): exact text, exact arithmetic, then SymPy."""

    if _normalized(left) == _normalized(right):
        return True, "exact_match"
    parsed_left, parsed_right = _parse_expression(left), _parse_expression(right)
    if parsed_left is not None and parsed_right is not None:
        return parsed_left[0] == parsed_right[0], "exact_arithmetic"
    return _sympy_equal(left, right), "symbolic_equality"


def _answers_differ(left: str, right: str) -> tuple[bool | None, str]:
    """(True when decidably different, False when equal, None undecidable)."""

    if _normalized(left) == _normalized(right):
        return False, "exact_match"
    parsed_left, parsed_right = _parse_expression(left), _parse_expression(right)
    if parsed_left is not None and parsed_right is not None:
        (poly_left, places_left), (poly_right, places_right) = parsed_left, parsed_right
        places = max(places_left, places_right)
        a, b = _constant_of(poly_left), _constant_of(poly_right)
        if a is not None and b is not None:
            # A rounded decimal within its stated precision is not "wrong".
            return abs(a - b) > _tolerance(places), "exact_arithmetic"
        if places:
            return None, "exact_arithmetic"
        return poly_left != poly_right, "polynomial_normal_form"
    equal = _sympy_equal(left, right)
    return (None if equal is None else not equal), "symbolic_equality"


def answers_equal(left: str, right: str) -> tuple[bool | None, str]:
    """Public face of the answer comparison: (True/False/None, method).

    Exact normalized text, then exact arithmetic, then SymPy on safe text
    only. ``None`` means undecidable; model text never reaches SymPy unless
    :func:`safe_math_text` admits it."""

    return _answers_equal(left, right)


def answers_differ(left: str, right: str) -> tuple[bool | None, str]:
    """(True when decidably different, False when equal, None undecidable).

    Unlike :func:`answers_equal`, a rounded decimal within its stated
    precision is not different (``0.667`` vs ``2/3``)."""

    return _answers_differ(left, right)


def _asserted_answer(text: str, declared: str) -> str | None:
    """The concluding line's assertion when it IS the declared answer."""

    asserted = asserted_conclusion(text)
    if asserted is None:
        return None
    candidates = [asserted]
    assignment = _ASSIGNMENT.match(asserted)
    if assignment:
        candidates.append(assignment.group(1).strip())
    for candidate in candidates:
        if _answers_equal(candidate, declared)[0] is True:
            return candidate
    return None


def _expected_text(item: PracticeItem) -> str:
    return item.expected_answer if isinstance(item.expected_answer, str) else json.dumps(item.expected_answer, sort_keys=True)


def verify_alternative(item: PracticeItem, draft: ValidAlternativeDraft) -> dict[str, Any]:
    """A deterministic check of the SUBMITTED derivation; never the model's word.

    ``verified`` needs all three: the concluding line asserts the declared
    final answer, that answer equals the reference, and every relation in
    the derivation was checked and holds (none false, none undecided).
    Anything else is excluded from E1's denominator.
    """

    asserted = _asserted_answer(draft.derivation_md, draft.final_answer)
    if asserted is None:
        return {
            "status": "unverified",
            "reason": "concluding_line_does_not_assert_the_final_answer",
            "asserted_answer": asserted_conclusion(draft.derivation_md),
        }
    equal, method = _answers_equal(asserted, _expected_text(item))
    if equal is not True:
        return {"status": "unverified", "method": method, "reason": "final_answer_not_shown_equal_to_reference", "asserted_answer": asserted}
    relations = check_relations(draft.derivation_md)
    if relations.false:
        return {"status": "unverified", "method": method, "reason": "false_equation", "false_equations": len(relations.false), "asserted_answer": asserted}
    if relations.unchecked:
        return {"status": "unverified", "method": method, "reason": "unchecked_relation", "unchecked_relations": len(relations.unchecked), "asserted_answer": asserted}
    return {
        "status": "verified",
        "method": f"{method}+asserted_conclusion+every_relation_checked",
        "asserted_answer": asserted,
        "relations_checked": relations.checked,
    }


def verify_synthetic_error(vault: LoadedVault, item: PracticeItem, draft: SyntheticErrorDraft) -> dict[str, Any]:
    """Establish a synthetic answer's outcome independently of its generator.

    ``verified_wrong`` means the answer's concluding line asserts the
    declared final answer and that answer is deterministically NOT the
    reference, so it cannot deserve full marks (``known_full_marks`` False).
    The declared criterion is recorded as a label only; how many points the
    planted error should cost is not known.
    """

    rubric = resolved_rubric(vault, item)
    points = {criterion.id: float(criterion.points) for criterion in rubric.criteria}
    maximum = float(rubric.max_points)
    if draft.planted_criterion_id not in points:
        return {"status": "invalid_criterion", "planted_criterion_id": draft.planted_criterion_id}
    declared = {
        "planted_criterion_id": draft.planted_criterion_id,
        "declared_known_score": max(0.0, maximum - points[draft.planted_criterion_id]),
    }
    asserted = _asserted_answer(draft.answer_md, draft.final_answer)
    if asserted is None:
        return {
            "status": "unverified",
            "reason": "concluding_line_does_not_assert_the_declared_answer",
            "asserted_answer": asserted_conclusion(draft.answer_md),
            **declared,
        }
    differ, method = _answers_differ(asserted, _expected_text(item))
    if differ is False:
        return {"status": "not_wrong", "method": method, "reason": "final_answer_equals_reference", "asserted_answer": asserted, **declared}
    if differ is None:
        return {"status": "unverified", "method": method, "reason": "final_answer_not_decidable", "asserted_answer": asserted, **declared}
    return {
        "status": "verified_wrong",
        "method": method,
        "known_full_marks": False,
        "max_points": maximum,
        "asserted_answer": asserted,
        **declared,
    }


def is_reference_bearing(item: PracticeItem) -> bool:
    expected = item.expected_answer
    text = expected if isinstance(expected, str) else json.dumps(expected, sort_keys=True)
    return bool(text.strip())


__all__ = [
    "PROBES",
    "PROBE_PROMPT_VERSION",
    "ParaphraseDraft",
    "RelationCheck",
    "SyntheticErrorDraft",
    "ValidAlternativeDraft",
    "asserted_conclusion",
    "check_relations",
    "is_reference_bearing",
    "paraphrase_prompt",
    "request_paraphrase",
    "request_synthetic_error",
    "request_valid_alternative",
    "safe_math_text",
    "synthetic_error_prompt",
    "valid_alternative_prompt",
    "verify_alternative",
    "verify_synthetic_error",
]
