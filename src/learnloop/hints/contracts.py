"""Adaptive hints H2a: the writer's contracts and leak control, checked in code (spec §4.2, §4.6, G-H5, G-H6).

**The seven shared rules** (the Reader's reconciliation contract, generalized;
on the practice screen the work is the answer draft, so rules 1-3 check
quotes against it):

1. It cites the learner: with work, at level 2 and up, it quotes the draft.
2. It continues from a real checkpoint: the placement node is on the named
   route and the quoted work is the learner's; what stands ends before the
   first questionable point.
3. It says what stands, when there is work (unless the first questionable
   point is where the work starts).
4. It keeps the learner's route, unless that route is invalid or the learner
   asked for another; only ``book_way`` places it on the reference route while
   the learner's route is valid.
5. It changes strategy when it isn't working: after a "doesn't connect" reply
   other than "the notation", or a second hint on the same work, its kind or
   strategy slug differs from the earlier hints there. After "the notation" it
   keeps the kind and quotes the learner's symbols.
6. It is placed: with a map, it names its route and target node, and the
   target's distance matches the chosen horizon (or is the last node short of
   the goal when the route is shorter).
7. It obeys its kind's contract (§4.2's table).

**Leak control** (binding here, whatever the map's marks say; H1 friction
notes 4 and 7): every hint at level 3 or lower must pass
``answer_leaks_expected`` (the tutor's check), H1's ``gives_away`` (which
also catches a short numeric answer) and the map's leak nodes: no expression
of a ``leak`` node's state (the goal always is one) and no equivalent of the
exact key. Worked help (levels 4-5) is the learner's to take and may show the
answer.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
import re
from typing import Any

from learnloop.hints.kinds import KINDS, WORKED_LEVELS
from learnloop.hints.maps import exact_key, gives_away, label_leaks, leak_expressions, number_tokens
from learnloop.tutor.tutor_qa import answer_leaks_expected


@dataclass
class Check:
    """The checks' result: rule failures (re-asked, then downgraded) and leak
    flags (re-asked, then withheld)."""

    failures: list[str] = field(default_factory=list)
    leaks: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.failures and not self.leaks

    def fail(self, code: str) -> None:
        if code not in self.failures:
            self.failures.append(code)


@dataclass(frozen=True)
class Target:
    """What the chosen option asks the writer for (and the checks hold it to)."""

    kind: str
    level: int
    horizon_index: int | None = None
    #: The node a level-3 hint must aim at (after a waypoint; ``smaller_step``).
    target_node_id: str | None = None
    #: ``book_way``: the reference route.
    reference_route: bool = False
    request: str = "more"
    shortcut: str | None = None
    #: The hint a reply answers (its kind, strategy and quotes).
    answered: Any = None
    #: Downgrade: a level-3 next step that claims nothing about what stands.
    downgrade: bool = False


# ---------------------------------------------------------------------------
# Map helpers
# ---------------------------------------------------------------------------

def _squash(text: str) -> str:
    return " ".join(str(text or "").split())


def in_work(quote: str, work: str) -> bool:
    """A quote is the learner's when it appears in the draft (spacing ignored)."""

    needle = _squash(quote)
    return bool(needle) and needle in _squash(work)


def nodes_by_id(current: Mapping[str, Any] | None) -> dict[str, dict[str, Any]]:
    return {str(node.get("id")): dict(node) for node in (current or {}).get("nodes") or ()}


def routes_by_id(current: Mapping[str, Any] | None) -> dict[str, dict[str, Any]]:
    return {str(route.get("id")): dict(route) for route in (current or {}).get("routes") or ()}


def reference_route_id(current: Mapping[str, Any] | None) -> str | None:
    for route in (current or {}).get("routes") or ():
        if str(route.get("origin")) == "reference":
            return str(route.get("id"))
    return None


def goal_node_id(current: Mapping[str, Any] | None) -> str | None:
    value = (current or {}).get("goal_node_id")
    return str(value) if value else None


def route_distance(current: Mapping[str, Any] | None, route_id: str, start: str, end: str) -> int | None:
    """Edges from ``start`` to ``end`` along the route, or None when either
    is not on it or ``end`` comes first."""

    route = routes_by_id(current).get(route_id)
    path = [str(node) for node in (route or {}).get("path") or ()]
    if start not in path or end not in path:
        return None
    distance = path.index(end) - path.index(start)
    return distance if distance >= 0 else None


def horizon_distance(current: Mapping[str, Any] | None, route_id: str, start: str, horizon_index: int) -> int | None:
    """The edges the chosen horizon asks for from ``start`` on the route:
    index 0 one, index 1 two, index 2 the end of the current subgoal (the
    next node with a checkpoint, else two), index 3 the goal. The last node
    short of the goal when the route is shorter (rule 6)."""

    route = routes_by_id(current).get(route_id)
    path = [str(node) for node in (route or {}).get("path") or ()]
    if start not in path:
        return None
    position = path.index(start)
    remaining = len(path) - 1 - position
    if remaining <= 0:
        return 0
    if horizon_index >= 3:
        return remaining
    if horizon_index == 2:
        nodes = nodes_by_id(current)
        for offset in range(1, remaining + 1):
            if str(nodes.get(path[position + offset], {}).get("checkpoint_id") or ""):
                return offset
        return min(2, remaining)
    wanted = horizon_index + 1
    return wanted if wanted < remaining else max(1, remaining - 1) if remaining > 1 else remaining


def later_expressions(current: Mapping[str, Any] | None, route_id: str | None, start: str | None,
                      work: str, public_text: str = "") -> set[str]:
    """Expressions of the states after the placement on the route (and every
    leak node's), minus those the learner has written: what a hint that names
    no step content must not carry."""

    nodes = nodes_by_id(current)
    route = routes_by_id(current).get(route_id or "") if route_id else None
    path = [str(node) for node in (route or {}).get("path") or ()]
    later: list[str] = []
    if path and start in path:
        later = path[path.index(start) + 1:]
    later += [node_id for node_id, node in nodes.items() if node.get("leak") or node_id == goal_node_id(current)]
    expressions: set[str] = set()
    for node_id in later:
        state = str(nodes.get(node_id, {}).get("state") or "")
        expressions |= leak_expressions(state)
    seen = _squash_math(work) + "\n" + _squash_math(public_text)
    return {expression for expression in expressions if expression and expression not in seen}


def leak_node_expressions(current: Mapping[str, Any] | None, public_text: str = "") -> set[str]:
    """The expressions of every leak node's state (the goal's always), less
    what the question itself states: a given is never a leak (H1's rule for
    labels, deviation 5 there)."""

    nodes = nodes_by_id(current)
    goal = goal_node_id(current)
    found: set[str] = set()
    for node_id, node in nodes.items():
        if node.get("leak") or node_id == goal:
            found |= leak_expressions(str(node.get("state") or ""))
    public = _squash_math(public_text)
    return {expression for expression in found if expression not in public}


def _squash_math(text: str) -> str:
    return re.sub(r"\s+", "", str(text or "")).replace("$", "").lower()


# ---------------------------------------------------------------------------
# Leak control
# ---------------------------------------------------------------------------

def leak_flags(texts: Sequence[str], *, item: Any, current: Mapping[str, Any] | None,
               level: int) -> list[str]:
    """Why any of ``texts`` would give the answer away (empty: it does not).
    Worked help (levels 4-5) is not checked: it is the learner's to take."""

    if level in WORKED_LEVELS:
        return []
    flags: list[str] = []
    expected = item.expected_answer
    key = exact_key(expected)
    leak_nodes = leak_node_expressions(current, item.prompt)
    for text in texts:
        if not str(text or "").strip():
            continue
        if answer_leaks_expected(text, expected):
            flags.append("answer_overlap")
        if gives_away(text, expected, key):
            flags.append("gives_away")
        if leak_nodes and label_leaks(text, leak_nodes, expected, public_text=item.prompt):
            flags.append("leak_node")
    return list(dict.fromkeys(flags))


# ---------------------------------------------------------------------------
# The rules
# ---------------------------------------------------------------------------

def _earlier_at_placement(state: Any) -> list[Any]:
    """Shown hints of this attempt on the same work (the same placement on the
    practice screen)."""

    return [hint for hint in state.shown_hints if hint.work_hash == state.work_hash]


def check_output(output: Any, *, target: Target, state: Any, item: Any) -> Check:
    """Every shared rule and the kind's contract for one writer answer (the
    discriminating kind's question is checked by the service after its EIG
    ranking; its fallback hint is checked as its own kind)."""

    check = Check()
    work = state.work_md
    has_work = state.has_work
    current = state.map
    placement = output.placement
    quotes = [quote for quote in placement.quotes if str(quote).strip()]
    kind, level = target.kind, target.level
    # Rule 1: it cites the learner.
    if has_work and level >= 2 and not target.downgrade:
        if not quotes:
            check.fail("rule1_no_citation")
    if any(not in_work(quote, work) for quote in quotes):
        # A "quote" the draft does not contain is a claim about the work
        # that is not the learner's (§4.6 rules 1-2).
        check.fail("rule1_quote_not_in_work")
    # Rule 2: it continues from a real checkpoint.
    questionable = str(placement.first_questionable_quote or "").strip()
    stands = str(placement.stands_quote or "").strip()
    if questionable and not in_work(questionable, work):
        check.fail("rule2_questionable_not_in_work")
    if stands and not in_work(stands, work):
        check.fail("rule2_stands_not_in_work")
    if stands and questionable and _squash(questionable) in _squash(stands):
        check.fail("rule2_past_first_questionable")
    if current is not None and placement.reached_node_id and placement.route_id != "new_route":
        if route_distance(current, placement.route_id, placement.reached_node_id,
                          placement.reached_node_id) is None:
            check.fail("rule2_placement_off_route")
    # Rule 3: it says what stands (none when the work is questionable from its start).
    if has_work and not target.downgrade and not stands and not questionable and level >= 2:
        check.fail("rule3_nothing_stands")
    if target.downgrade and stands and not in_work(stands, work):
        check.fail("rule3_unverified_claim")
    # Rule 4: it keeps the learner's route.
    reference = reference_route_id(current)
    if current is not None and reference is not None and output.route_id:
        learner_route = placement.route_id or reference
        if target.reference_route:
            if output.route_id != reference:
                check.fail("rule4_not_reference_route")
        elif learner_route != reference and placement.work_valid_so_far and output.route_id == reference:
            check.fail("rule4_left_learner_route")
        if target.shortcut == "learner_route" and learner_route != reference and output.route_id == reference:
            check.fail("rule4_left_learner_route")
        if target.shortcut == "learner_route" and has_work and not quotes:
            check.fail("rule4_no_work_named")
    # Rule 5: it changes strategy when it isn't working.
    earlier = _earlier_at_placement(state)
    replied = target.request == "feedback"
    if target.shortcut == "notation":
        answered_kind = getattr(target.answered, "hint_kind", None)
        if answered_kind and kind != answered_kind:
            check.fail("rule5_notation_changed_kind")
        if has_work and not quotes:
            check.fail("rule5_notation_no_symbols")
    elif (replied or earlier) and not target.downgrade:
        compared = list(earlier)
        if replied and target.answered is not None and target.answered not in compared:
            compared.append(target.answered)
        for hint in compared:
            if hint.hint_kind == kind and str(hint.strategy or "") == str(output.strategy or ""):
                check.fail("rule5_same_kind_and_strategy")
                break
    if target.shortcut == "not_where_stuck" and target.answered is not None:
        before = (getattr(target.answered, "placement", None) or {}).get("first_questionable_quote")
        if before and questionable and _squash(before) == _squash(questionable):
            check.fail("rule5_repeated_localization")
    # Rule 6: it is placed.
    placed_kinds = {"waypoint", "subgoal_plan", "next_step", "continuation"}
    if current is not None and kind in placed_kinds:
        routes = routes_by_id(current)
        route_ok = output.route_id in routes or output.route_id == "new_route"
        if not route_ok:
            check.fail("rule6_unknown_route")
        elif output.route_id != "new_route":
            start = placement.reached_node_id or _first_node(current, output.route_id)
            distance = route_distance(current, output.route_id, start, output.target_node_id) if start else None
            if distance is None:
                check.fail("rule6_target_off_route")
            elif kind == "waypoint" and target.horizon_index is not None:
                wanted = horizon_distance(current, output.route_id, start, target.horizon_index)
                if wanted is not None and distance != wanted:
                    check.fail("rule6_horizon_mismatch")
            elif kind == "next_step" and distance != 1 and not _route_done(current, output.route_id, start):
                check.fail("rule6_next_step_not_adjacent")
    if target.target_node_id and level == 3 and kind in placed_kinds and output.target_node_id != target.target_node_id:
        check.fail("rule6_not_the_waypoint_target")
    # Rule 7: the kind's contract.
    _kind_contract(check, output, target=target, state=state, item=item, quotes=quotes)
    # Leak control.
    texts = [output.hint_md, *[label.label for label in output.plan_labels]]
    check.leaks = leak_flags(texts, item=item, current=current, level=level)
    return check


def _first_node(current: Mapping[str, Any], route_id: str) -> str | None:
    path = (routes_by_id(current).get(route_id) or {}).get("path") or ()
    return str(path[0]) if path else None


def _route_done(current: Mapping[str, Any], route_id: str, start: str | None) -> bool:
    path = [str(node) for node in (routes_by_id(current).get(route_id) or {}).get("path") or ()]
    return bool(path) and start == path[-1]


_TRIVIAL_NUMBERS = frozenset({"0", "1", "2"})


def _kind_contract(check: Check, output: Any, *, target: Target, state: Any, item: Any,
                   quotes: Sequence[str]) -> None:
    kind = target.kind
    current = state.map
    work = state.work_md
    placement = output.placement
    later = later_expressions(current, placement.route_id or reference_route_id(current),
                              placement.reached_node_id or None, work, item.prompt) if current is not None else set()
    hint = output.hint_md
    if not str(hint or "").strip():
        check.fail("empty_hint")
    if kind == "approach_question":
        if output.asks_about not in ("approach", "assumption", "goal", "first_move"):
            check.fail("approach_question_declares_nothing")
        if later and label_leaks(hint, later, item.expected_answer, public_text=item.prompt):
            check.fail("approach_question_states_solution")
    elif kind == "localize":
        if not str(placement.first_questionable_quote or "").strip():
            check.fail("localize_no_quote")
        if later and label_leaks(hint, later, item.expected_answer, public_text=item.prompt):
            check.fail("localize_contains_correction")
    elif kind == "waypoint":
        nodes = nodes_by_id(current)
        node = nodes.get(output.target_node_id)
        if node is None:
            check.fail("waypoint_no_target_node")
        elif output.target_node_id == goal_node_id(current):
            # "The goal itself" is a horizon (§4.5): the goal node is always a
            # leak node (H1 marks it), so its state never reaches the text
            # (leak control below); only the horizon may name it.
            if target.horizon_index != 3:
                check.fail("waypoint_targets_leak_node")
        elif node.get("leak"):
            check.fail("waypoint_targets_leak_node")
        if current is not None and placement.reached_node_id and output.route_id in routes_by_id(current):
            techniques = _techniques_between(current, output.route_id, placement.reached_node_id,
                                             output.target_node_id)
            if any(technique.lower() in str(hint).lower() for technique in techniques):
                check.fail("waypoint_names_transformation")
    elif kind == "subgoal_plan":
        nodes = nodes_by_id(current)
        if not output.plan_labels:
            check.fail("subgoal_plan_no_labels")
        if any(label.node_id not in nodes for label in output.plan_labels):
            check.fail("subgoal_plan_label_not_on_map")
        if sum(1 for label in output.plan_labels if label.current) != 1:
            check.fail("subgoal_plan_current_not_marked")
        if output.label_register not in ("concrete", "abstract"):
            check.fail("subgoal_plan_no_register")
        if later and any(label_leaks(label.label, later, item.expected_answer, public_text=item.prompt)
                         for label in output.plan_labels):
            check.fail("subgoal_plan_label_carries_later_state")
    elif kind == "error_specific":
        if not str(placement.first_questionable_quote or "").strip():
            check.fail("error_specific_no_quote")
        if not str(output.principle or "").strip():
            check.fail("error_specific_no_principle")
        if later and label_leaks(hint, later, item.expected_answer, public_text=item.prompt):
            check.fail("error_specific_contains_correction")
    elif kind == "worked_parallel":
        own = {token for token in number_tokens(item.prompt) if token not in _TRIVIAL_NUMBERS}
        if own & set(number_tokens(hint)):
            check.fail("worked_parallel_uses_item_values")
        if output.source_origin not in ("book", "ai"):
            check.fail("worked_parallel_no_origin")
        if output.source_origin == "book":
            passages = getattr(state, "worked_example_texts", None) or []
            quote = str(output.source_quote or "").strip()
            if not quote or not any(in_work(quote, passage) for passage in passages):
                check.fail("worked_parallel_unverified_source")
    elif kind == "continuation":
        if current is not None:
            goal = goal_node_id(current)
            if not output.end_node_id or output.end_node_id == goal:
                check.fail("continuation_reaches_goal")
            start = placement.reached_node_id or _first_node(current, output.route_id or "")
            if start and output.route_id in routes_by_id(current) and route_distance(
                    current, output.route_id, start, output.end_node_id) in (None, 0):
                check.fail("continuation_off_route")
    elif kind == "worked_chunk":
        if not output.pieces:
            check.fail("worked_chunk_no_pieces")
        if any(not (piece.establishes.strip() and piece.how.strip() and piece.why.strip())
               for piece in output.pieces):
            check.fail("worked_chunk_piece_missing_what_how_why")
        if not str(output.gap or "").strip():
            check.fail("worked_chunk_leaves_no_gap")
    if kind not in KINDS:
        check.fail("unknown_kind")


def _techniques_between(current: Mapping[str, Any], route_id: str, start: str, end: str) -> list[str]:
    path = [str(node) for node in (routes_by_id(current).get(route_id) or {}).get("path") or ()]
    if start not in path or end not in path:
        return []
    segment = path[path.index(start):path.index(end) + 1]
    pairs = set(zip(segment, segment[1:]))
    return [str(edge.get("technique") or "") for edge in (current.get("edges") or ())
            if (str(edge.get("from_node")), str(edge.get("to_node"))) in pairs
            and len(str(edge.get("technique") or "")) >= 4]


__all__ = [
    "Check",
    "Target",
    "check_output",
    "goal_node_id",
    "horizon_distance",
    "in_work",
    "leak_flags",
    "reference_route_id",
    "route_distance",
]
