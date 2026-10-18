"""Adaptive hints H2a: the kinds, levels, labels and replies (spec §4.2, §4.8).

One table, read by the options, the chooser, the writer's contracts and the
result's labels, so the learner meets one vocabulary everywhere (the Reader's
plain words, UX §5.6). The level is the Reader's ladder: how much of the
solution the help does (1-5). It alone decides evidence (§5): levels 1-3 add
one to ``hints_used``, levels 4-5 set ``primed``. The kind is the form the help
takes at a level; it changes nothing in evidence.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

#: Help that writes part of the solution for the learner (levels 4-5): it is
#: the learner's to take, labelled before it is taken (D17, H5).
WORKED_LEVELS = frozenset({4, 5})
#: The levels a Hint press may serve on a surface without a ladder (D17).
PRESS_LEVELS = (1, 2, 3)
#: The plain-words mark worked help carries before it is taken (§4.8).
WORKED_HELP_MARK = "worked help ◌"
#: The origin labels (§4.8, H5).
AI_WRITTEN = "AI-written"
FROM_THE_ITEM = "from the item"
FROM_THE_BOOK = "from the book"


@dataclass(frozen=True)
class Kind:
    name: str
    levels: tuple[int, ...]
    #: The plain-words label (§4.8; the Reader's, UX §5.6).
    label: str
    #: The label at level 3 where it differs (``discriminating``).
    label_level_3: str | None = None
    #: Offered only with an approach map (§4.5).
    needs_map: bool = False
    #: Offered only when there is work to quote (its contract quotes it).
    needs_work: bool = False

    def label_at(self, level: int) -> str:
        return self.label_level_3 if level == 3 and self.label_level_3 else self.label


KINDS: Mapping[str, Kind] = {
    kind.name: kind
    for kind in (
        Kind("approach_question", (1,), "a question about your approach"),
        Kind("discriminating", (1, 3), "a question that tells apart two explanations",
             label_level_3="a check that tells them apart"),
        Kind("localize", (2,), "where it stops holding", needs_work=True),
        Kind("waypoint", (3,), "a goal to aim for", needs_map=True),
        Kind("subgoal_plan", (3,), "a plan for the rest", needs_map=True),
        Kind("next_step", (3,), "the next step"),
        Kind("error_specific", (3,), "check this part", needs_work=True),
        Kind("worked_parallel", (3,), "the same move on another example"),
        Kind("authored", (3,), "from the item"),
        Kind("continuation", (4,), "the next part, written for you"),
        Kind("worked_chunk", (4,), "a worked piece, from the goal back"),
        Kind("walkthrough", (5,), "the rest, worked through"),
    )
}
#: Every kind, in §4.2's table order (the help_assists CHECK's values).
KIND_NAMES: tuple[str, ...] = tuple(KINDS)

#: A waypoint's horizon in the chooser's ordinal rubric (§4.5): index i is
#: score i. "next step" is a horizon of one, the other end of the same scale.
HORIZON_LEVELS: tuple[str, ...] = (
    "the next step (one step ahead)",
    "two steps ahead",
    "the end of the current subgoal",
    "the goal itself",
)
#: Horizon labels under a waypoint (§4.8), by the rubric index drawn.
HORIZON_LABELS: Mapping[int, str] = {
    0: "the next step", 1: "about two steps ahead", 2: "at the end of this part", 3: "the goal itself",
}

#: The requests a hint answers (§4.1; ``help_assists.request``).
REQUESTS = ("more", "feedback", "book_way", "smaller_step")
#: The four "doesn't connect" shortcuts (§4.2, D15).
SHORTCUTS = ("not_where_stuck", "too_big", "learner_route", "notation")
#: The fallback order at each level (§4.5, practice surface): after a reply,
#: the first kind of this list the reply allows; under a taken level, the
#: first of that level's list (the Reader's fixed rung kinds, §4.5).
FALLBACK_ORDER: Mapping[int, tuple[str, ...]] = {
    1: ("approach_question", "discriminating"),
    2: ("localize",),
    3: ("next_step", "error_specific", "waypoint", "subgoal_plan", "worked_parallel"),
    4: ("continuation", "worked_chunk"),
    5: ("walkthrough",),
}
#: "Too big a jump" asks for a finer kind at the same level (§4.2): a kind is
#: offered after it only when it is finer than the one answered.
GRAIN: Mapping[str, int] = {
    "subgoal_plan": 0, "worked_parallel": 1, "waypoint": 2, "authored": 2, "error_specific": 3,
    "next_step": 4, "approach_question": 0, "discriminating": 0, "localize": 0,
    "worked_chunk": 0, "continuation": 1, "walkthrough": 0,
}

#: The withheld-hint wording (§4.6, leak control).
WITHHELD_MESSAGE = "this hint would give the answer away; take a worked piece instead? (worked help ◌)"
#: The why lines of a discriminating question with no positive EIG (§4.2).
NO_SEPARATING_QUESTION = {
    1: "No question separates these readings; here is a question about your approach.",
    3: "No question separates these readings; here is the next step.",
}
#: The first-move wording of an approach question asked before any work (§4.8).
FIRST_MOVE_LABEL = "your first move?"

#: Words a learner-facing hint label or line never uses (G-H12's wording lint).
FORBIDDEN_WORDING = ("you don't understand", "you struggle", "weak")


def option_id(kind: str, level: int) -> str:
    """A chooser option's name: ``<kind>@L<level>``."""

    return f"{kind}@L{level}"


def parse_option(option: str) -> tuple[str, int]:
    kind, _, level = option.partition("@L")
    if kind not in KINDS or not level.isdigit() or int(level) not in KINDS[kind].levels:
        raise ValueError(f"not a hint option: {option!r}")
    return kind, int(level)


def labels_for(kind: str, level: int, *, origin: str, has_work: bool = True,
               horizon_index: int | None = None, source_origin: str | None = None) -> dict[str, object]:
    """The labels a hint carries (§4.8, H5, G-H12): where it came from, its
    kind in plain words, a waypoint's horizon, and *worked help ◌* for levels
    4-5 (which the panel shows before the help is taken, too)."""

    spec = KINDS[kind]
    kind_label = spec.label_at(level)
    if kind == "approach_question" and not has_work:
        kind_label = FIRST_MOVE_LABEL
    if kind == "worked_parallel":
        kind_label = f"{kind_label} ({FROM_THE_BOOK if source_origin == 'book' else AI_WRITTEN})"
    labels: dict[str, object] = {
        "origin": origin,
        "kind": kind_label,
        "worked_help": WORKED_HELP_MARK if level in WORKED_LEVELS else None,
        "horizon": HORIZON_LABELS.get(horizon_index) if kind == "waypoint" and horizon_index is not None else None,
    }
    return labels


def worked_help_picks() -> list[dict[str, object]]:
    """The hint panel's two worked-help picks, each labelled before it is
    taken (§4.8, D17): a Hint press alone never serves them."""

    return [
        {"level": 4, "label": "work a piece of it for me", "worked_help": WORKED_HELP_MARK,
         "consequence": "Counts as worked help: this answer will not count as done on your own."},
        {"level": 5, "label": "show me the worked answer", "worked_help": WORKED_HELP_MARK,
         "consequence": "Counts as worked help: this answer will not count as done on your own."},
    ]


__all__ = [
    "AI_WRITTEN",
    "FALLBACK_ORDER",
    "FIRST_MOVE_LABEL",
    "FORBIDDEN_WORDING",
    "FROM_THE_BOOK",
    "FROM_THE_ITEM",
    "GRAIN",
    "HORIZON_LABELS",
    "HORIZON_LEVELS",
    "KINDS",
    "KIND_NAMES",
    "Kind",
    "NO_SEPARATING_QUESTION",
    "PRESS_LEVELS",
    "REQUESTS",
    "SHORTCUTS",
    "WITHHELD_MESSAGE",
    "WORKED_HELP_MARK",
    "WORKED_LEVELS",
    "labels_for",
    "option_id",
    "parse_option",
    "worked_help_picks",
]
