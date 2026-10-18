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
    #: The final value or expression the goal establishes, or "" when the
    #: item has no short final answer (a proof).
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

    value = (key or "").strip()
    if not _LONE_DIGIT_KEY.fullmatch(value):
        return False
    pattern = rf"(?<![\w.,/^_]){re.escape(value)}(?![\w]|[.,/]\d)"
    return re.search(pattern, str(text or "")) is not None


# -- one normalisation for both sides (fix round 2, M1/M2) -------------------------------

_DELIMITERS = re.compile(r"\$\$|\$|\\\(|\\\)|\\\[|\\\]")
_LEFT_RIGHT = re.compile(r"\\(?:left|right)(?![A-Za-z])")
_FRAC = re.compile(r"\\[dt]?frac\s*\{([^{}]*)\}\s*\{([^{}]*)\}")
#: ``=`` as an assignment or equation, never inside ``<=``, ``>=``, ``!=`` or ``==``.
_EQUALS = re.compile(r"(?<![<>!=])=(?!=)")
#: A plain number of its own: an integer, decimal or fraction, never part of
#: ``x_4``, ``2^4``, ``14`` or ``4.5`` (the controls F1 ruled on).
_NUMBER_TOKEN = re.compile(r"(?<![\w.^_/\\])[-+]?\d+(?:\.\d+)?(?:\s*/\s*\d+(?:\.\d+)?)?(?![\w^/]|\.\d)")
#: A word that ends an expression in prose ("x^2 on [0, 1]", "4 socks").
_PROSE_WORD = re.compile(r"\s+([A-Za-z]{2,})\b")
_MATH_NAMES = frozenset({"sqrt", "sin", "cos", "tan", "exp", "log", "ln", "pi"})
_SINGLE_SYMBOL = re.compile(r"-?\d|[A-Za-z]")
_CANDIDATE_CHARS = 60


def normalize_math(text: str) -> str:
    """The text with its math delimiters (``$…$``, ``\\(…\\)``, ``\\[…\\]``),
    ``\\left``/``\\right`` removed and ``\\frac{a}{b}`` written ``(a)/(b)``: the
    one form a state, a label, the goal and the expected answer are compared in."""

    value = _LEFT_RIGHT.sub("", _DELIMITERS.sub(" ", str(text or "")))
    previous = None
    while previous != value:
        previous, value = value, _FRAC.sub(r"(\1)/(\2)", value)
    return value


def _clean(expression: str) -> str:
    value = re.sub(r"\s+", " ", expression).strip().rstrip(".,;:").strip()
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
    """The expressions a text states, in the shared form: its numbers, the
    value after each ``=`` and the whole text when it is a short expression."""

    normalized = normalize_math(text)
    found: list[str] = [_clean(match.group(0)) for match in _NUMBER_TOKEN.finditer(normalized)]
    sides = _EQUALS.split(normalized)
    found.extend(_cut_prose(side) for side in sides[1:])
    whole = _clean(normalized)
    if whole and len(whole) <= _CANDIDATE_CHARS and _PROSE_WORD.search(" " + whole) is None:
        found.append(whole)
    return [value for value in dict.fromkeys(found) if value]


def assignment_conclusion(text: str) -> str | None:
    """The value the text's LAST ``=`` assigns ("Therefore y = x^3" -> ``x^3``), or None."""

    sides = _EQUALS.split(normalize_math(text))
    if len(sides) < 2:
        return None
    return _cut_prose(sides[-1]) or None


def states_answer(text: str, key: str | None) -> bool:
    """Whether ``text`` states an expression equivalent to the key, by the
    guarded answer checker on both sides in the shared form (fix round 2,
    M1): ``$4$``, ``\\(4\\)``, ``+4``, ``0.25`` and ``\\frac{1}{4}`` all state
    ``1/4``-style keys they equal. A single-symbol key is a token match
    (word boundary), never a substring."""

    target = normalize_key(key)
    if not target:
        return False
    if _SINGLE_SYMBOL.fullmatch(target):
        if target[-1].isdigit() and _states_short_key(normalize_math(text), target):
            return True
        if target.isalpha():
            return re.search(rf"(?<![\w.,/^_\\]){re.escape(target)}(?!\w)", normalize_math(text)) is not None
    return any(_equal(candidate, target) is True for candidate in answer_candidates(text))


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


def _state_conclusion(goal_state: str) -> str | None:
    """The value the goal node's state concludes with: its last assignment
    after the shared normalisation ("Therefore y = x^3" -> ``x^3``,
    "P = \\frac{3}{4}" -> ``(3)/(4)``; fix round 2, M2), else the state read
    as an exact key is (the state itself when it is a short expression)."""

    return assignment_conclusion(goal_state or "") or exact_key(goal_state or "")


def goal_agreement(goal_answer: str, goal_state: str, expected_answer: str | dict[str, Any]) -> tuple[str, str]:
    """``(verified | unverified | mismatch, basis)``: the goal against the
    expected answer, by exact key where one exists (§4.3).

    Both the builder's declaration (``goal_answer``) and the goal node's own
    conclusion (the state routes reach) are checked, and a contradiction in
    either is a mismatch before anything is verified (Codex review F2).
    Only the goal STATE verifies (fix round 2, M2): its conclusion equals the
    key, or, when it assigns nothing, it states the key. A declaration that
    agrees with a state the checker cannot read stays unverified (the spec's
    "the builder's declaration, stored as unverified"); the map may still be
    stored."""

    key = exact_key(expected_answer)
    if key is None:
        return "unverified", "no_exact_key"
    target = normalize_key(key) or key
    declared = (goal_answer or "").strip()
    concluded = _state_conclusion(goal_state)
    for value, basis in ((declared, "exact_key"), (concluded, "goal_state")):
        if value and (_differ(normalize_key(value) or value, target) is True):
            return "mismatch", basis
    if concluded and _equal(normalize_key(concluded) or concluded, target) is True:
        return "verified", "exact_key"
    if assignment_conclusion(goal_state or "") is None and states_answer(goal_state or "", key):
        return "verified", "exact_key"
    if not declared:
        return "unverified", "no_goal_answer"
    if _equal(normalize_key(declared) or declared, target) is True:
        return "unverified", "goal_state_unchecked"
    return "unverified", "undecidable"


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
        leak = (node.leak or node.id == candidate.goal_node_id or gives_away(node.state, context.expected_answer, key))
        if leak and not node.leak:
            marked.append(node.id)
        normalized_nodes.append(node.model_copy(update={"leak": leak}))
    expressions: set[str] = set()
    for node in normalized_nodes:
        if node.leak:
            expressions |= leak_expressions(node.state)
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
    agreement, basis = goal_agreement(candidate.goal_answer, goal.state if goal else "", context.expected_answer)
    if agreement == "mismatch":
        fail("goal_mismatch", goal_answer=candidate.goal_answer, basis=basis)
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
    "assignment_conclusion",
    "exact_key",
    "gives_away",
    "goal_agreement",
    "label_leaks",
    "leak_expressions",
    "normalize_key",
    "normalize_math",
    "route_counts",
    "states_answer",
    "validate_map",
]
