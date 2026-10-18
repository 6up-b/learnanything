"""Adaptive hints H2a: the (kind, level) options a request allows (spec §4.2, §4.5).

Options whose preconditions fail are absent, never offered and then refused:
``discriminating`` without two open rivals or once one was answered at this
placement; ``waypoint`` and ``subgoal_plan`` without a map; ``worked_parallel``
without a worked example from the learner's own source (T6's passages, as
the map consumed them) or another instance (a family sibling); ``localize``
and ``error_specific`` with no work to quote. On the practice screen a Hint
press offers levels 1-3 only; levels 4-5 are offered only for a level the
learner took (the panel's worked-help picks, D17), and then only that level's
kinds. The learner's replies and picks constrain the options (§4.2); none is a
rule about what helps:

* **More** (the default): levels 1-3. After a waypoint, every level-3 option
  aims at the waypoint's target and ``next_step`` toward it is among them.
* **feedback** (a "doesn't connect" reply) keeps the answered hint's level:
  ``notation`` keeps its kind (the one reply exempt from rule 5); ``too_big``
  asks for a smaller step (after a waypoint a shorter horizon toward the same
  target, down to ``next_step``; otherwise a finer kind); ``not_where_stuck``
  and ``learner_route`` keep every kind of the level (their contracts move
  the placement or keep the learner's route).
* **book_way**: the next hint on the reference route at the same level and
  kind; **smaller_step** (under a waypoint): ``next_step`` toward the same
  target at the same level. Both are the learner's pick.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from learnloop.hints.kinds import GRAIN, KINDS, PRESS_LEVELS, WORKED_LEVELS, option_id
from learnloop.hints.state import EarlierHint, HintState

#: The kinds the chooser may offer: ``authored`` is served by the fallback,
#: or by the writer verbatim when one fits (§4.7), never drawn.
OFFERABLE = tuple(name for name in KINDS if name != "authored")


@dataclass(frozen=True)
class Option:
    kind: str
    level: int

    @property
    def id(self) -> str:
        return option_id(self.kind, self.level)


@dataclass
class OptionSet:
    """What a request may be served, and why the rest is absent."""

    options: list[Option]
    #: ``offered``: the chooser picks the level; ``learner_pick``: the learner took it.
    level_source: str = "offered"
    taken_level: int | None = None
    #: ``book_way`` | ``smaller_step``: the learner's pick fixes the option (no propensity).
    learner_pick: str | None = None
    #: Level-3 options aim here (after a waypoint; ``smaller_step``).
    target_node_id: str | None = None
    #: ``too_big`` after a waypoint: the horizon must be shorter than this.
    max_horizon: int | None = None
    #: ``book_way``: the hint goes on the reference route.
    reference_route: bool = False
    answered: EarlierHint | None = None
    excluded: dict[str, str] = field(default_factory=dict)

    @property
    def ids(self) -> list[str]:
        return [option.id for option in self.options]

    def has(self, kind: str, level: int | None = None) -> bool:
        return any(option.kind == kind and (level is None or option.level == level) for option in self.options)

    def record(self) -> dict[str, Any]:
        return {"options": self.ids, "level_source": self.level_source, "taken_level": self.taken_level,
                "learner_pick": self.learner_pick, "target_node_id": self.target_node_id,
                "max_horizon": self.max_horizon, "reference_route": self.reference_route,
                "answered_assist_id": self.answered.assist_id if self.answered else None,
                "excluded": dict(self.excluded)}


def precondition(kind: str, state: HintState) -> str | None:
    """Why ``kind`` cannot be offered for this state, or None."""

    spec = KINDS[kind]
    if spec.needs_map and state.map is None:
        return "no_map"
    if spec.needs_work and not state.has_work:
        return "no_work"
    if kind == "discriminating":
        if len(state.rivals) < 2:
            return "fewer_than_two_rivals"
        if state.answered_discriminating_here():
            return "answered_here"
    if kind == "worked_parallel" and not (state.worked_example_at_hand or state.another_instance_at_hand):
        return "no_example"
    return None


def _offer(levels: tuple[int, ...], state: HintState, excluded: dict[str, str],
           kinds: tuple[str, ...] = OFFERABLE) -> list[Option]:
    options: list[Option] = []
    for level in levels:
        for kind in kinds:
            if level not in KINDS[kind].levels:
                continue
            reason = precondition(kind, state)
            if reason is not None:
                excluded[option_id(kind, level)] = reason
                continue
            options.append(Option(kind, level))
    return options


def build_options(state: HintState, *, request: str, answered: EarlierHint | None = None,
                  shortcut: str | None = None, taken_level: int | None = None) -> OptionSet:
    """The options for one request (the caller has validated ``answered``)."""

    excluded: dict[str, str] = {}
    if request == "smaller_step":
        assert answered is not None
        return OptionSet([Option("next_step", 3)], level_source="offered", learner_pick="smaller_step",
                         target_node_id=answered.target_node_id, answered=answered)
    if request == "book_way":
        assert answered is not None
        level = int(answered.level or 3)
        kind = str(answered.hint_kind or "next_step")
        if kind not in OFFERABLE or level not in KINDS[kind].levels or precondition(kind, state) is not None:
            # The book's way at the same level: its own kind where that still
            # applies, else the level's plain form.
            kind = {1: "approach_question", 2: "localize", 3: "next_step", 4: "continuation",
                    5: "walkthrough"}[level]
            if precondition(kind, state) is not None:
                kind, level = "next_step", 3
        return OptionSet([Option(kind, level)], level_source="offered", learner_pick="book_way",
                         reference_route=True, answered=answered,
                         taken_level=level if level in WORKED_LEVELS else None)
    if taken_level is not None:
        return OptionSet(_offer((taken_level,), state, excluded), level_source="learner_pick",
                         taken_level=taken_level, excluded=excluded)
    if request == "feedback":
        assert answered is not None
        level = int(answered.level or 3)
        answered_kind = str(answered.hint_kind or "next_step")
        options = _offer((level,), state, excluded)
        target, max_horizon = None, None
        if shortcut == "notation":
            same = [option for option in options if option.kind == answered_kind]
            options = same or options
        elif shortcut == "too_big":
            if answered_kind == "waypoint":
                target = answered.target_node_id
                max_horizon = int(answered.horizon or 2)
                options = [option for option in options
                           if option.kind == "next_step" or (option.kind == "waypoint" and max_horizon > 2)]
            else:
                finer = [option for option in options if GRAIN.get(option.kind, 0) > GRAIN.get(answered_kind, 0)]
                other = [option for option in options if option.kind != answered_kind]
                options = finer or other or options
            for option in _offer((level,), state, {}):
                if option not in options:
                    excluded.setdefault(option.id, "too_big")
        return OptionSet(options, level_source="learner_pick" if level in WORKED_LEVELS else "offered",
                         taken_level=level if level in WORKED_LEVELS else None, answered=answered,
                         target_node_id=target, max_horizon=max_horizon, excluded=excluded)
    # "More": a Hint press never serves worked help here (D17).
    options = _offer(PRESS_LEVELS, state, excluded)
    last = state.shown_hints[-1] if state.shown_hints else None
    target = last.target_node_id if last is not None and last.hint_kind == "waypoint" else None
    return OptionSet(options, level_source="offered", target_node_id=target, excluded=excluded)


__all__ = ["OFFERABLE", "Option", "OptionSet", "build_options", "precondition"]
