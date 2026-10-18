"""Adaptive hints H1: the approach map and its validation in code (spec §4.3).

An approach map is a small subgoal graph of one practice item: **nodes**
(a subgoal label, the state established there, what in a learner's work shows
it is reached, the trace-contract or skeleton checkpoint it matches, and
whether its state gives the answer away), **edges** (the technique and
principle that move from one node to the next, with the item's facets they
exercise) and **routes** (node paths from the givens to the goal, each with
its origin: the reference solution, a trace-contract recipe, the PF skeleton,
a source's worked example, the model's own distinct route, or the learner's
own correct solutions).

This module is pure: the wire models the builder's model answers with, the
validator every map passes before it is stored (a map that fails is re-asked
once, then not stored; :mod:`learnloop.hints.map_builder`), and the merge of a
learner's new routes. Nothing here is evidence, and nothing here reaches the
grader (standing constraints H1, H2).

Field names: the spec's ``edges: from; to`` are ``from_node`` / ``to_node``
(``from`` is a Python keyword); a route's ``learner_attempt_ids`` carries the
learner's attempts that took it, so a matching route "gains the attempt id"
(§4.3) without rewriting its origin.
"""

from __future__ import annotations

from collections.abc import Callable, Collection, Mapping, Sequence
from dataclasses import dataclass, field
import json
import re
from typing import Any, Literal

from learnloop.ai.schemas import WireModel
from learnloop.attempts.answer_check import (
    answers_differ,
    answers_equal,
    parse_answer,
    reference_final_answer,
    safe_math_text,
)
from learnloop.tutor.tutor_qa import span_leaks_expected

MAP_SCHEMA_VERSION = "approach_map.v1"

#: Every reason a map can fail validation (the report counts them).
REASONS: tuple[str, ...] = (
    "malformed",
    "cycle",
    "no_route",
    "no_reference_route",
    "route_not_given_to_goal",
    "foreign_facet",
    "empty_label",
    "label_leak",
    "unknown_checkpoint",
    "unknown_origin",
    "goal_mismatch",
    # A seeded learner solution on no route, or on two (Codex review F4).
    "unplaced_attempt",
    # A learner-route merge's own reasons.
    "merge_unknown_attempt",
    "merge_unplaced_attempt",
    "merge_unknown_route",
    "merge_node_collision",
)
#: Origins without a reference list; ``source:`` and ``learner:`` carry ids
#: and ``trace_contract`` may name its recipe (``trace_contract:<recipe id>``).
PLAIN_ORIGINS = frozenset({"reference", "trace_contract", "skeleton", "model"})


class MapNode(WireModel):
    id: str
    role: Literal["given", "step", "goal"]
    #: A subgoal label: short, structural, no answer values.
    label: str
    #: What is established at this point (LaTeX allowed).
    state: str
    #: What in a learner's work shows the node is reached.
    recognizers: list[str]
    #: The trace-contract or skeleton checkpoint it matches, or "".
    checkpoint_id: str
    #: The state contains or gives away the expected answer.
    leak: bool
    #: A step's or given's structured value: the bare expression its state
    #: establishes, or "" (fix round 3, R2: a value equal to the answer marks
    #: the node a leak by code).
    value: str = ""
    #: The goal's structured conclusion: the final answer as a bare
    #: expression, no prose and no units, or "" for a proof; "" on every other
    #: node (fix round 3, R1: the ONLY basis of goal verification).
    conclusion: str = ""
    #: The unit of ``conclusion`` or ``value`` ("m", "cm^2"), or "".
    unit: str = ""


class MapEdge(WireModel):
    from_node: str
    to_node: str
    technique: str
    principle: str
    facet_ids: list[str]


class MapRoute(WireModel):
    id: str
    name: str
    #: Node ids from a given to the goal, each step an edge.
    path: list[str]
    #: reference | trace_contract[:<recipe id>] | skeleton | model |
    #: source:<span refs> | learner:<attempt refs>
    origin: str
    #: The learner's attempts that took this route (refs in a prompt, ids once stored).
    learner_attempt_ids: list[str]


class ApproachMapV1(WireModel):
    nodes: list[MapNode]
    edges: list[MapEdge]
    routes: list[MapRoute]
    goal_node_id: str
    #: The builder's restatement of the final answer, or "" (a proof).
    #: Informational, and a label must not contain it; the goal is verified
    #: only from the goal node's structured ``conclusion`` (fix round 3, R1).
    goal_answer: str


class MergeMatch(WireModel):
    attempt_ref: str
    #: The existing route the attempt took.
    route_id: str


class MergeNewRoute(WireModel):
    id: str
    name: str
    attempt_refs: list[str]
    #: Nodes new to the map (existing node ids may appear in ``path`` and edges).
    nodes: list[MapNode]
    edges: list[MapEdge]
    path: list[str]


class LearnerRouteMergeV1(WireModel):
    """The merge's answer: each new correct attempt either took an existing
    route or opens a new one (origin ``learner:<attempt ids>``)."""

    matches: list[MergeMatch]
    new_routes: list[MergeNewRoute]


@dataclass(frozen=True)
class MapContext:
    """What a map is checked against: the item and its seeds."""

    expected_answer: str | dict[str, Any]
    #: The item's facets (canonical ids) and the canonicalizer edges' ids go through.
    facet_ids: frozenset[str]
    canonical_facet: Callable[[str], str] = field(default=lambda value: value)
    #: Trace-contract and skeleton checkpoint ids a node may link to.
    checkpoint_ids: frozenset[str] = frozenset()
    recipe_ids: frozenset[str] = frozenset()
    #: Prompt ref -> stored id for seeded source spans ("s1" -> "ext:span") and attempts ("a1" -> attempt id).
    span_refs: Mapping[str, str] = field(default_factory=dict)
    attempt_refs: Mapping[str, str] = field(default_factory=dict)
    #: The question as the learner reads it: an expression it states is a
    #: given, never a leak (a label may say "evaluate at 1/2").
    public_text: str = ""


@dataclass
class Validation:
    valid: bool
    reasons: list[str]
    details: list[dict[str, Any]]
    verified_goal: bool
    goal_basis: str
    #: The map as stored: refs replaced by ids, code-marked leaks set.
    normalized: ApproachMapV1 | None = None
    leak_marked_by_code: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "valid": self.valid, "reasons": list(self.reasons), "details": list(self.details),
            "verified_goal": self.verified_goal, "goal_basis": self.goal_basis,
            "leak_marked_by_code": list(self.leak_marked_by_code), "schema": MAP_SCHEMA_VERSION,
        }


# ---------------------------------------------------------------------------
# Leak expressions
# ---------------------------------------------------------------------------

_MATH = re.compile(r"\$\$(.+?)\$\$|\$(.+?)\$|\\\((.+?)\\\)|\\\[(.+?)\\\]", re.S)
#: A number a label would leak: fractional, decimal or of two digits or more
#: (a lone digit appears in labels and states by accident).
_NUMBER = re.compile(r"(?<![\w.])-?\d+(?:[.,/]\d+)+|(?<![\w.])-?\d{2,}")
#: A run of non-space characters carrying an operator: an equation or formula.
_FORMULA = re.compile(r"\S*[=^\\]\S*")


def _squash(text: str) -> str:
    return re.sub(r"\s+", "", str(text or "")).replace("$", "").lower()


def leak_expressions(text: str) -> set[str]:
    """The expressions of a leak node's state a label must not contain:
    its math segments, formulas and numbers (normalized, at least two characters)."""

    found: set[str] = set()
    for match in _MATH.finditer(text or ""):
        segment = next(group for group in match.groups() if group is not None)
        found.add(_squash(segment))
    plain = _MATH.sub(" ", text or "")
    found.update(_squash(match.group(0)) for match in _FORMULA.finditer(plain))
    found.update(_squash(match.group(0)) for match in _NUMBER.finditer(text or ""))
    return {expression.strip(".,;:") for expression in found if len(expression.strip(".,;:")) >= 2}


#: An exact key the span-leak check cannot see: a lone digit, optionally
#: signed (``span_leaks_expected`` deliberately ignores one-character tokens,
#: and ``leak_expressions`` keeps two characters or more).
_LONE_DIGIT_KEY = re.compile(r"-?\d")


def _states_short_key(text: str, key: str | None) -> bool:
    """Whether ``text`` states a lone-digit key as a number of its own (Codex
    review F1): "4" in "The count is 4" or "$x = 4$", never inside "14",
    "4.5", "3/4", "x_4" or "2^4"."""

    value = _signs(key).strip()
    if not _LONE_DIGIT_KEY.fullmatch(value):
        return False
    # One tokenizer (fix rounds 3 and 4): a sign stays attached across
    # whitespace ("-4", "- 4" and "−  4" never state 4) and a fraction is
    # one token ("3/4", "3 / 4", "\\frac{3}{4}", "(3)/(4)" state neither 3 nor 4).
    return value in number_tokens(text)


# -- one normalisation for both sides (fix rounds 2 and 3) ---------------------------------
#
# Prose detection here is best-effort defence in depth: the binding leak gate
# is H2's leak control on the written hint text (spec §4.6), run on every
# hint. Structured fields (a node's ``value``, the goal's ``conclusion``) are
# what code relies on; prose that needs algebraic rewriting ("x times x")
# is a known gap.

_MATH_SPAN = re.compile(r"\$\$(.+?)\$\$|\$(.+?)\$|\\\((.+?)\\\)|\\\[(.+?)\\\]", re.S)
_DELIMITERS = re.compile(r"\$\$|\$|\\\(|\\\)|\\\[|\\\]")
_LEFT_RIGHT = re.compile(r"\\(?:left|right)(?![A-Za-z])")
_FRAC = re.compile(r"\\[dt]?frac\s*\{([^{}]*)\}\s*\{([^{}]*)\}")
#: Unicode minus and dash signs written as ASCII (fix round 3, R2).
_SIGNS = str.maketrans({"\u2212": "-", "\u2010": "-", "\u2011": "-", "\u2012": "-", "\u2013": "-",
                        "\u2014": "-", "\ufe63": "-", "\uff0d": "-", "\ufe62": "+", "\uff0b": "+"})
#: ``=`` as an assignment or equation, never inside ``<=``, ``>=``, ``!=`` or ``==``.
_EQUALS = re.compile(r"(?<![<>!=])=(?!=)")
#: A plain number of its own, its sign attached (``-4`` is never ``4``): an
#: integer, decimal or whole fraction, never part of ``x_4``, ``2^4``, ``14``,
#: ``4.5``, ``x-4`` or a fraction's numerator or denominator (``3/4``,
#: ``\frac{3}{4}``, ``(3)/(4)``).
_NUMBER_TOKEN = re.compile(
    # A sign (spaced or not) belongs to the number unless it follows an operand.
    r"(?:(?<![\w.^_/\\{})])[-+]\s*(?=\d)"
    # An unsigned number never follows a sign, a slash (spaced or not) or "/(".
    r"|(?<![\w.^_/\\{\-+])(?<!/\s)(?<!/\s\s)(?<![-+]\s)(?<![-+]\s\s)(?<!/\()(?<!/ \())"
    r"\d+(?:\.\d+)?(?:\s*/\s*[-+]?\s*\d+(?:\.\d+)?)?"
    # ... and is never a numerator of a fraction it is not part of ("4 / x", "(4)/(5)").
    r"(?![\w^/}]|\.\d|,\d|\)\s*/|\s*/)")


def number_tokens(text: str | None) -> list[str]:
    """The standalone numbers of a text, whole: signed (``-4``), decimal or a
    whole fraction, whitespace removed and a leading ``+`` dropped."""

    plain = _LEFT_RIGHT.sub("", _DELIMITERS.sub(" ", _signs(text)))
    # "( 3 ) / ( 4 )" is "(3)/(4)": one fraction, whatever its spacing (U4).
    plain = re.sub(r"\(\s*([-+]?\s*\d+(?:\.\d+)?)\s*\)", lambda match: "(" + re.sub(r"\s+", "", match.group(1)) + ")",
                   plain)
    plain = re.sub(r"\)\s*/\s*\(", ")/(", plain)
    tokens = [re.sub(r"\s+", "", match.group(0)) for match in _NUMBER_TOKEN.finditer(plain)]
    return [token[1:] if token.startswith("+") else token for token in tokens]
#: A word that ends an expression in prose ("x^2 on [0, 1]", "4 socks").
_PROSE_WORD = re.compile(r"\s+([A-Za-z]{2,})\b")
_MATH_NAMES = frozenset({"sqrt", "sin", "cos", "tan", "exp", "log", "ln", "pi"})
_SINGLE_SYMBOL = re.compile(r"-?\d|[A-Za-z]")
#: A number followed by a word: a quantity with its unit ("4 m"), not an expression.
_QUANTITY = re.compile(r"\d\s+[A-Za-z]")
_CANDIDATE_CHARS = 60


def _signs(text: str | None) -> str:
    return str(text or "").translate(_SIGNS)


def normalize_math(text: str) -> str:
    """The text with Unicode signs written ASCII, its math delimiters
    (``$…$``, ``\\(…\\)``, ``\\[…\\]``) and ``\\left``/``\\right`` removed and
    ``\\frac{a}{b}`` written ``(a)/(b)``: the one form a state, a label, a
    structured value and the expected answer are compared in."""

    value = _LEFT_RIGHT.sub("", _DELIMITERS.sub(" ", _signs(text)))
    previous = None
    while previous != value:
        previous, value = value, _FRAC.sub(r"(\1)/(\2)", value)
    return value


def _clean(expression: str) -> str:
    value = re.sub(r"\s+", " ", expression).strip().rstrip(".,;:").strip()
    # A spaced sign is the number's ("- 4" is -4; the checker would read a list bullet; U4).
    value = re.sub(r"^([-+])\s+(?=\d)", r"\1", value)
    return value[1:].strip() if value.startswith("+") else value


def normalize_key(text: str | None) -> str:
    """An answer or key in the shared form: normalised, whitespace and a leading ``+`` stripped."""

    return re.sub(r"\s+", "", _clean(normalize_math(text or "")))


def _cut_prose(expression: str) -> str:
    """An expression up to the first prose word or clause break after it."""

    value = expression
    for match in _PROSE_WORD.finditer(value):
        if match.group(1).lower() not in _MATH_NAMES:
            value = value[: match.start()]
            break
    return _clean(re.split(r"[,;]|\.(?:\s|$)", value)[0])


def answer_candidates(text: str) -> list[str]:
    """The expressions a text states, in the shared form: the whole content
    of every math span (taken before its delimiters are stripped; fix round
    3, R2), its standalone signed numbers and whole fractions, the value after
    each ``=``, and the whole text when it is a short expression."""

    signed = _signs(text)
    found: list[str] = []
    for match in _MATH_SPAN.finditer(signed):
        content = next(group for group in match.groups() if group is not None)
        found.append(_clean(normalize_math(content)))
    plain = _LEFT_RIGHT.sub("", _DELIMITERS.sub(" ", signed))
    found.extend(number_tokens(plain))
    normalized = normalize_math(signed)
    found.extend(_cut_prose(side) for side in _EQUALS.split(normalized)[1:])
    whole = _clean(normalized)
    if whole and len(whole) <= _CANDIDATE_CHARS and _PROSE_WORD.search(" " + whole) is None:
        found.append(whole)
    return [value for value in dict.fromkeys(found) if value]


def structured_expression(text: str | None, unit: str | None = "") -> str | None:
    """A structured field (a node's ``value``, the goal's ``conclusion``) as an
    expression the guarded checker reads, or None: empty, prose, a quantity
    with its unit still attached ("4 m"), an equation, or not parseable.
    A declared ``unit`` written after the expression is dropped first."""

    raw = _signs(text).strip()
    suffix = (unit or "").strip()
    if suffix and raw.endswith(suffix) and raw[: -len(suffix)].strip():
        raw = raw[: -len(suffix)].strip()
    plain = normalize_math(raw)
    if not plain.strip() or _QUANTITY.search(plain) or _EQUALS.search(plain) or re.search(r"[<>]|!=", plain):
        return None
    if any(word.lower() not in _MATH_NAMES for word in re.findall(r"[A-Za-z]{2,}", plain)):
        return None
    expression = normalize_key(raw)
    try:
        parses = parse_answer(expression) is not None or safe_math_text(expression)
    except Exception:  # noqa: BLE001 - a checker failure is "unparsed", never a verdict
        return None
    return expression if parses else None


def states_answer(text: str, key: str | None) -> bool:
    """Whether ``text`` states an expression equivalent to the key, by the
    guarded answer checker on both sides in the shared form (best-effort
    prose detection; fix rounds 2 and 3). A single-symbol key is a token
    match (word boundary), never a substring."""

    target = normalize_key(key)
    if not target:
        return False
    if _SINGLE_SYMBOL.fullmatch(target):
        if target[-1].isdigit() and _states_short_key(text, target):
            return True
        if target.isalpha():
            return re.search(rf"(?<![\w.,/^_\\]){re.escape(target)}(?!\w)", normalize_math(text)) is not None
    return any(_equal(candidate, target) is True for candidate in answer_candidates(text))


#: A unit as written after a number: letters (or µ, Ω, °, %), then letters,
#: digits and ^ / * · . (``m``, ``cm^2``, ``m/s``, ``kg m/s^2``).
_UNIT = r"[A-Za-z\u00b5\u03bc\u03a9\u00b0%][A-Za-z0-9\u00b5\u03bc\u03a9\u00b0%^/*\u00b7.]*"
_QUANTITY_NUMBER = r"[-+]?\s*\d+(?:\.\d+)?(?:\s*/\s*\d+(?:\.\d+)?)?"
#: "4 m": a number, a space, a unit (unambiguous).
_SPACED_QUANTITY = re.compile(rf"({_QUANTITY_NUMBER})\s+({_UNIT}(?:\s+{_UNIT})*)")
#: "4m": a number with letters attached; a unit or a product (ambiguous).
_ATTACHED_QUANTITY = re.compile(rf"({_QUANTITY_NUMBER})({_UNIT})")
_UNIT_MARKUP = re.compile(r"\\(?:text|mathrm|mbox|operatorname)\s*\{([^{}]*)\}")
_LATEX_SPACE = re.compile(r"\\[,;:! ]|~")


def _unit_text(text: str | None) -> str:
    """``\\text{m}``-style markup and LaTeX spaces as plain text."""

    return _LATEX_SPACE.sub(" ", _UNIT_MARKUP.sub(r" \1", _signs(text)))


def normalize_unit(unit: str | None) -> str:
    """A unit compared as a string (fix round 4, U1): markup, delimiters and
    whitespace removed, ``²``/``³`` and ``^{2}`` written ``^2``; case kept (mm is not Mm)."""

    value = normalize_math(_unit_text(unit)).replace("\u00b2", "^2").replace("\u00b3", "^3")
    value = re.sub(r"\^\{([^{}]*)\}", r"^\1", value)
    return re.sub(r"\s+", "", value)


@dataclass(frozen=True)
class Quantity:
    """An answer read as a number and its unit (fix round 4, U1): one
    reading for the reference and for the structured fields. ``number`` is
    the expression without its unit; ``whole`` the expression read
    algebraically (None when a unit was split off); ``ambiguous`` when a
    number has letters attached ("4m": four metres, or 4 times m)."""

    number: str | None
    unit: str | None
    whole: str | None
    ambiguous: bool = False


def _units_are_math(unit: str) -> bool:
    return any(word.lower() in _MATH_NAMES for word in re.findall(r"[A-Za-z]{2,}", unit))


def read_quantity(text: str | None, unit: str | None = "") -> Quantity:
    """``text`` (and a declared ``unit``) as a :class:`Quantity`, by the one
    helper both sides use: a declared unit written after the expression is
    dropped; "4 m" splits into 4 and m; "4m" is ambiguous; anything else is
    an expression with the declared unit, if any."""

    declared = normalize_unit(unit) or None
    raw = _unit_text(text).strip()
    suffix = (unit or "").strip()
    if suffix and raw.endswith(suffix) and raw[: -len(suffix)].strip():
        raw = raw[: -len(suffix)].strip()
    plain = _clean(normalize_math(raw))
    spaced = _SPACED_QUANTITY.fullmatch(plain)
    if spaced and not _units_are_math(spaced.group(2)):
        written = normalize_unit(spaced.group(2))
        number = structured_expression(spaced.group(1))
        if declared is not None and written != declared:
            return Quantity(number, None, None, ambiguous=True)  # two units: not interpretable
        return Quantity(number, written, None)
    attached = _ATTACHED_QUANTITY.fullmatch(plain)
    if attached and declared is None and not _units_are_math(attached.group(2)):
        return Quantity(structured_expression(attached.group(1)), normalize_unit(attached.group(2)),
                        structured_expression(plain), ambiguous=True)
    expression = structured_expression(raw)
    return Quantity(expression, declared, expression if declared is None else None)


def _decide(left: str | None, right: str | None) -> bool | None:
    if not left or not right:
        return None
    if _equal(left, right) is True:
        return True
    if _differ(left, right) is True:
        return False
    return None


def _as_quantity(reference: Quantity, given: Quantity) -> bool | None:
    if reference.unit is not None and given.unit is not None and reference.unit != given.unit:
        return None
    return _decide(reference.number, given.number)


def compare_quantities(reference: Quantity, given: Quantity) -> tuple[bool | None, str]:
    """``(True | False | None, basis)``: the given quantity against the
    reference (fix round 4, U1). Equal units, no unit on either side, or a
    unit on one side only against an unambiguous reference: the numbers
    decide (``answers_equal`` / ``answers_differ``). Units that differ, or a
    unit that cannot be interpreted, decide nothing (None, never a
    mismatch). An ambiguous "4m" decides only when its readings agree: as a
    product and as a quantity (a unit on one side only against an ambiguous
    reference decides nothing)."""

    if reference.ambiguous or given.ambiguous:
        algebraic = _decide(reference.whole, given.whole) if (reference.whole and given.whole) else None
        one_sided = (reference.unit is None) != (given.unit is None)
        as_quantity = None if (reference.ambiguous and one_sided) else _as_quantity(reference, given)
        if algebraic is not None and algebraic == as_quantity:
            return algebraic, "exact_key"
        if algebraic is None and not reference.ambiguous and as_quantity is not None:
            return as_quantity, "exact_key"
        return None, "unit_ambiguous"
    if reference.unit is not None and given.unit is not None and reference.unit != given.unit:
        return None, "unit_differs"
    verdict = _decide(reference.number, given.number)
    return verdict, "exact_key" if verdict is not None else "undecidable"


def value_states_answer(value: str | None, unit: str | None, key: str | None) -> bool:
    """A structured ``value`` equivalent to the key under the guarded checker
    (R2), its unit read the way the goal's is (U1)."""

    if not (value or "").strip() or not key:
        return False
    return compare_quantities(read_quantity(key), read_quantity(value, unit))[0] is True


def gives_away(text: str, expected_answer: str | dict[str, Any], key: str | None = None) -> bool:
    """Whether ``text`` contains or gives away the expected answer: the
    tutor's span-leak check against the whole answer and, where the answer
    has an exact key (a worked solution's final value), against the key; a
    lone-digit key, which the span check ignores, by its own number token;
    and any stated expression equivalent to the key (fix round 2, M1)."""

    if span_leaks_expected(text, expected_answer):
        return True
    if not key:
        return False
    return span_leaks_expected(text, str(key)) or _states_short_key(text, key) or states_answer(text, key)


def label_leaks(label: str, expressions: Collection[str], expected_answer: str | dict[str, Any], *,
                public_text: str = "") -> bool:
    squashed = _squash(label)
    if any(expression and expression in squashed for expression in expressions):
        return True
    if not label.strip():
        return False
    key = exact_key(expected_answer)
    if span_leaks_expected(label, expected_answer) or (key and (span_leaks_expected(label, str(key))
                                                                or _states_short_key(label, key))):
        return True
    # An equivalent of the answer in the label (fix round 2, M1), unless the
    # question itself states the answer: what the question states is a given.
    return bool(key) and states_answer(label, key) and not states_answer(public_text, key)


# ---------------------------------------------------------------------------
# The goal check
# ---------------------------------------------------------------------------

def exact_key(expected_answer: str | dict[str, Any]) -> str | None:
    """The expected answer's exact key: the answer itself when it is a short
    parseable expression (in the shared form when only that parses:
    ``$\\frac{1}{4}$``), else the numeric conclusion a worked solution ends
    with (``answer_check``, on the text or its shared form), else None (a
    proof, a description)."""

    reference = expected_answer if isinstance(expected_answer, str) else json.dumps(expected_answer, sort_keys=True)
    if not reference.strip():
        return None
    try:
        quantity = read_quantity(reference)
        if quantity.unit is not None and quantity.number is not None and not quantity.ambiguous:
            return reference.strip()  # "4 m", "4\\,\\text{m}": read by read_quantity on both sides (U1)
        if parse_answer(reference) is not None:
            return reference.strip()
        normalized = normalize_key(reference)
        if normalized and parse_answer(normalized) is not None:
            return normalized
        return reference_final_answer(reference) or reference_final_answer(normalize_math(reference))
    except Exception:  # noqa: BLE001 - a checker failure means no key, never a verdict
        return None


def _equal(left: str, right: str) -> bool | None:
    try:
        return answers_equal(left, right)[0]
    except Exception:  # noqa: BLE001
        return None


def _differ(left: str, right: str) -> bool | None:
    try:
        return answers_differ(left, right)[0]
    except Exception:  # noqa: BLE001
        return None


def goal_agreement(conclusion: str, expected_answer: str | dict[str, Any], unit: str = "") -> tuple[str, str]:
    """``(verified | unverified | mismatch, basis)``: the goal node's
    structured ``conclusion`` against the expected answer's exact key (§4.3;
    fix round 3, R1). Nothing else decides it: no prose state, no token
    presence, no declaration.

    * ``verified`` only when the conclusion parses and the guarded checker
      (``answer_check.answers_equal``) holds against the key;
    * ``mismatch`` only when it parses and decidably differs;
    * otherwise ``unverified``, with the reason: ``no_exact_key``,
      ``no_conclusion``, ``conclusion_unparsed`` or ``undecidable``. An
      unverified goal never rejects a map (the spec's "stored as unverified")."""

    key = exact_key(expected_answer)
    if key is None:
        return "unverified", "no_exact_key"
    if not (conclusion or "").strip():
        return "unverified", "no_conclusion"
    given = read_quantity(conclusion, unit)
    if given.number is None and given.whole is None:
        return "unverified", "conclusion_unparsed"
    # The reference and the conclusion are read by the same helper (fix
    # round 4, U1): "4 m" against 4 with unit m is verified, never 4m != 4.
    verdict, basis = compare_quantities(read_quantity(key), given)
    if verdict is True:
        return "verified", "exact_key"
    if verdict is False:
        return "mismatch", "conclusion"
    return "unverified", basis


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def _has_cycle(node_ids: Sequence[str], edges: Sequence[MapEdge]) -> bool:
    incoming = {node: 0 for node in node_ids}
    outgoing: dict[str, list[str]] = {node: [] for node in node_ids}
    for edge in edges:
        outgoing[edge.from_node].append(edge.to_node)
        incoming[edge.to_node] += 1
    ready = [node for node, count in incoming.items() if count == 0]
    seen = 0
    while ready:
        node = ready.pop()
        seen += 1
        for target in outgoing[node]:
            incoming[target] -= 1
            if incoming[target] == 0:
                ready.append(target)
    return seen != len(node_ids)


def _origin(origin: str, context: MapContext, reasons: list[str], details: list[dict[str, Any]],
            route_id: str) -> str:
    """The stored origin (refs replaced by ids), recording an unknown one."""

    value = (origin or "").strip()
    kind, _, rest = value.partition(":")
    if value in PLAIN_ORIGINS:
        return value
    if kind == "trace_contract" and rest in context.recipe_ids:
        return value
    if kind in ("source", "learner") and rest:
        refs = [ref.strip() for ref in rest.split(",") if ref.strip()]
        table = context.span_refs if kind == "source" else context.attempt_refs
        resolved = [table.get(ref) or (ref if ref in table.values() else None) for ref in refs]
        if refs and all(resolved):
            return f"{kind}:" + ",".join(dict.fromkeys(str(ref) for ref in resolved))
    reasons.append("unknown_origin")
    details.append({"reason": "unknown_origin", "route_id": route_id, "origin": value})
    return value


def validate_map(candidate: ApproachMapV1, context: MapContext) -> Validation:
    """Every rule of §4.3's "validation in code"; failures by reason."""

    reasons: list[str] = []
    details: list[dict[str, Any]] = []

    def fail(reason: str, **detail: Any) -> None:
        reasons.append(reason)
        details.append({"reason": reason, **detail})

    nodes = {node.id: node for node in candidate.nodes}
    if not candidate.nodes or len(nodes) != len(candidate.nodes):
        fail("malformed", problem="no nodes or duplicate node ids")
    goal = nodes.get(candidate.goal_node_id)
    goals = [node.id for node in candidate.nodes if node.role == "goal"]
    if goal is None or goals != [candidate.goal_node_id]:
        fail("malformed", problem="the goal must be exactly one node with role goal")
    if not any(node.role == "given" for node in candidate.nodes):
        fail("malformed", problem="no given node")
    dangling = [(edge.from_node, edge.to_node) for edge in candidate.edges
                if edge.from_node not in nodes or edge.to_node not in nodes]
    if dangling:
        fail("malformed", problem="edges name unknown nodes", edges=dangling[:5])
    edges = [edge for edge in candidate.edges if edge.from_node in nodes and edge.to_node in nodes]
    if any(edge.from_node == edge.to_node for edge in edges) or _has_cycle(list(nodes), edges):
        fail("cycle")
    pairs = {(edge.from_node, edge.to_node) for edge in edges}
    # Routes: a given to the goal, every step an edge.
    route_ids = [route.id for route in candidate.routes]
    if not candidate.routes:
        fail("no_route")
    elif len(set(route_ids)) != len(route_ids):
        fail("malformed", problem="duplicate route ids")
    normalized_routes: list[MapRoute] = []
    for route in candidate.routes:
        path = list(route.path)
        ok = (len(path) >= 2 and len(set(path)) == len(path) and all(node in nodes for node in path)
              and nodes[path[0]].role == "given" and path[-1] == candidate.goal_node_id
              and all((left, right) in pairs for left, right in zip(path, path[1:])))
        if not ok:
            fail("route_not_given_to_goal", route_id=route.id)
        origin = _origin(route.origin, context, reasons, details, route.id)
        attempts = []
        for ref in route.learner_attempt_ids:
            resolved = context.attempt_refs.get(ref) or (ref if ref in context.attempt_refs.values() else None)
            if resolved is None:
                fail("unknown_origin", route_id=route.id, attempt=ref)
            else:
                attempts.append(resolved)
        normalized_routes.append(route.model_copy(update={"origin": origin,
                                                          "learner_attempt_ids": list(dict.fromkeys(attempts))}))
    if candidate.routes and not any(route.origin.strip() == "reference" for route in candidate.routes):
        fail("no_reference_route")
    # Every seeded learner solution is on exactly one route (Codex review F4):
    # the map's route assignments are what later merges treat as mined, so a
    # solution left off every route would never be placed.
    placements: dict[str, int] = {}
    for route in normalized_routes:
        for attempt in route.learner_attempt_ids:
            placements[attempt] = placements.get(attempt, 0) + 1
    seeded = list(dict.fromkeys(str(value) for value in context.attempt_refs.values()))
    unplaced = [attempt for attempt in seeded if placements.get(attempt, 0) == 0]
    twice = [attempt for attempt, count in placements.items() if count > 1]
    if unplaced:
        fail("unplaced_attempt", attempts=unplaced[:10])
    if twice:
        fail("unplaced_attempt", problem="an attempt on two routes", attempts=twice[:10])
    # Facets: every edge's facets belong to the item.
    for edge in edges:
        foreign = [facet for facet in edge.facet_ids if context.canonical_facet(facet) not in context.facet_ids]
        if foreign:
            fail("foreign_facet", edge=[edge.from_node, edge.to_node], facets=foreign)
    # Checkpoint links resolve.
    for node in candidate.nodes:
        if node.checkpoint_id.strip() and node.checkpoint_id.strip() not in context.checkpoint_ids:
            fail("unknown_checkpoint", node_id=node.id, checkpoint_id=node.checkpoint_id)
    # Leaks: code marks every node whose state gives the answer away, and the goal.
    marked: list[str] = []
    normalized_nodes: list[MapNode] = []
    key = exact_key(context.expected_answer)
    for node in candidate.nodes:
        leak = (node.leak or node.id == candidate.goal_node_id or gives_away(node.state, context.expected_answer, key)
                or value_states_answer(node.value, node.unit, key))
        if leak and not node.leak:
            marked.append(node.id)
        normalized_nodes.append(node.model_copy(update={"leak": leak}))
    expressions: set[str] = set()
    for node in normalized_nodes:
        if node.leak:
            expressions |= leak_expressions(node.state)
            for field_value in (node.value, node.conclusion):
                if field_value.strip():
                    expressions |= leak_expressions(field_value) | {_squash(normalize_math(field_value))}
    if candidate.goal_answer.strip():
        expressions |= leak_expressions(candidate.goal_answer) | {_squash(candidate.goal_answer)}
    public = _squash(context.public_text)
    expressions = {expression for expression in expressions if len(expression) >= 2 and expression not in public}
    for node in normalized_nodes:
        if not node.label.strip():
            fail("empty_label", node_id=node.id)
        elif label_leaks(node.label, expressions, context.expected_answer, public_text=context.public_text):
            fail("label_leak", node_id=node.id)
    # The goal agrees with the expected answer by exact key where one exists.
    agreement, basis = goal_agreement(goal.conclusion if goal else "", context.expected_answer,
                                      goal.unit if goal else "")
    if agreement == "mismatch":
        fail("goal_mismatch", conclusion=goal.conclusion if goal else "", basis=basis)
    ordered = list(dict.fromkeys(reasons))
    normalized = candidate.model_copy(update={"nodes": normalized_nodes, "routes": normalized_routes})
    return Validation(valid=not ordered, reasons=ordered, details=details,
                      verified_goal=agreement == "verified", goal_basis=basis,
                      normalized=normalized if not ordered else None, leak_marked_by_code=marked)


# ---------------------------------------------------------------------------
# The learner-route merge
# ---------------------------------------------------------------------------

def apply_merge(current: ApproachMapV1, merge: LearnerRouteMergeV1, *,
                attempt_refs: Mapping[str, str]) -> tuple[ApproachMapV1, list[str], list[dict[str, Any]]]:
    """The current map with the learner's new routes (§4.3 "approach mining").

    A matching route gains the attempt id; an attempt on no existing route
    opens a route with origin ``learner:<attempt ids>``. Every new attempt
    must be placed once, and only on routes and nodes that exist or are added.
    Returns the merged map and the merge's own failure reasons (the merged
    map then still goes through :func:`validate_map`)."""

    reasons: list[str] = []
    details: list[dict[str, Any]] = []
    routes = {route.id: route.model_copy(deep=True) for route in current.routes}
    node_ids = {node.id for node in current.nodes}
    placed: list[str] = []
    for match in merge.matches:
        attempt = attempt_refs.get(match.attempt_ref)
        if attempt is None:
            reasons.append("merge_unknown_attempt")
            details.append({"reason": "merge_unknown_attempt", "attempt": match.attempt_ref})
            continue
        route = routes.get(match.route_id)
        if route is None:
            reasons.append("merge_unknown_route")
            details.append({"reason": "merge_unknown_route", "route_id": match.route_id})
            continue
        route.learner_attempt_ids = list(dict.fromkeys([*route.learner_attempt_ids, attempt]))
        placed.append(attempt)
    nodes = [node.model_copy(deep=True) for node in current.nodes]
    edges = [edge.model_copy(deep=True) for edge in current.edges]
    for new in merge.new_routes:
        attempts = [attempt_refs.get(ref) for ref in new.attempt_refs]
        if not attempts or not all(attempts):
            reasons.append("merge_unknown_attempt")
            details.append({"reason": "merge_unknown_attempt", "route_id": new.id})
            continue
        if new.id in routes or any(node.id in node_ids for node in new.nodes):
            reasons.append("merge_node_collision")
            details.append({"reason": "merge_node_collision", "route_id": new.id})
            continue
        nodes.extend(new.nodes)
        node_ids.update(node.id for node in new.nodes)
        edges.extend(new.edges)
        ids = [str(attempt) for attempt in attempts]
        routes[new.id] = MapRoute(id=new.id, name=new.name, path=list(new.path),
                                  origin="learner:" + ",".join(dict.fromkeys(ids)), learner_attempt_ids=ids)
        placed.extend(ids)
    unplaced = [attempt for attempt in attempt_refs.values() if attempt not in placed]
    if unplaced:
        reasons.append("merge_unplaced_attempt")
        details.append({"reason": "merge_unplaced_attempt", "attempts": unplaced})
    if len(placed) != len(set(placed)):
        reasons.append("malformed")
        details.append({"reason": "malformed", "problem": "an attempt placed on two routes"})
    merged = current.model_copy(update={"nodes": nodes, "edges": edges, "routes": list(routes.values())})
    return merged, list(dict.fromkeys(reasons)), details


def route_counts(map_payload: Mapping[str, Any]) -> dict[str, int]:
    """Routes by origin kind (reference, trace_contract, skeleton, source, model, learner)."""

    counts: dict[str, int] = {}
    for route in map_payload.get("routes") or ():
        kind = str(route.get("origin") or "").partition(":")[0] or "unknown"
        counts[kind] = counts.get(kind, 0) + 1
    return counts


__all__ = [
    "MAP_SCHEMA_VERSION",
    "PLAIN_ORIGINS",
    "REASONS",
    "ApproachMapV1",
    "LearnerRouteMergeV1",
    "MapContext",
    "MapEdge",
    "MapNode",
    "MapRoute",
    "MergeMatch",
    "MergeNewRoute",
    "Validation",
    "answer_candidates",
    "apply_merge",
    "exact_key",
    "gives_away",
    "goal_agreement",
    "label_leaks",
    "leak_expressions",
    "normalize_key",
    "normalize_math",
    "route_counts",
    "Quantity",
    "compare_quantities",
    "normalize_unit",
    "number_tokens",
    "read_quantity",
    "states_answer",
    "structured_expression",
    "value_states_answer",
    "validate_map",
]
