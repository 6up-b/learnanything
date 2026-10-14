"""The block-chooser interface (``spec_daily_loop_v1.md`` §6.8).

The plan container owns minutes, lanes, finiteness, re-entry and the streak. A
**source** proposes block candidates and a **chooser** picks one at each block
boundary. DL1's pair is deterministic (``legacy_lanes_v1`` and
``lane_quota_v1``); router R2 replaces both through this interface (the staged
frame as the source, the logged mixture as the chooser), so nothing here may
depend on how DL1's pair works.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, field
from typing import Any, Literal, Protocol

Lane = Literal["repair", "maintain", "new", "push"]

#: Lane order for ties (lane_quota_v1) and for display.
LANES: tuple[Lane, ...] = ("repair", "maintain", "new", "push")
#: §6.2 step 4: unused and released minutes flow to maintenance overflow, then
#: repair overflow, then push; new receives flowed minutes only up to its
#: admitted new-material minutes, so it comes last.
FLOW_ORDER: tuple[Lane, ...] = ("maintain", "repair", "push", "new")
#: §6.1: a learner pick's estimate comes out of these lanes, in this order.
PICK_DEDUCTION_ORDER: tuple[Lane, ...] = ("push", "new", "repair", "maintain")
#: The lanes a re-entry plan uses (§7).
REENTRY_LANES: tuple[Lane, ...] = ("repair", "maintain")
#: The lane tie order of the plan for the day's remaining minutes after a
#: re-entry plan (owner decision 2026-10-12): re-entry stays repair and
#: maintain only, and "keep going" after it leads with new material.
AFTER_REENTRY_LANE_PRIORITY: tuple[Lane, ...] = ("new", "repair", "maintain", "push")

#: Canonical actions per lane (§6.1; ``controller_actions``).
LANE_ACTIONS: Mapping[str, tuple[str, str | None]] = {
    "repair": ("practice", "completion_or_repair"),
    "maintain": ("maintain", None),
    "new": ("instruct", None),
    "push": ("practice", "fluency"),
}

PlanKind = Literal["normal", "reentry", "keep_going"]
ChosenBy = Literal["lane_quota", "staged", "mixture", "learner_pick"]
WhyKind = Literal["computed", "model_written", "model_no_rationale"]

CONTINUE_CURRENT = "continue_current"  # offered while a block is in progress
STOP_FOR_TODAY = "stop_for_today"  # offered when minutes_left < 5 or nothing feasible

#: §6.8 rule 4: STOP_FOR_TODAY is offered below this many minutes left.
STOP_OFFER_MINUTES = 5.0
#: §6.1: a block aims for 5-15 estimated minutes (the staged policy's bounds).
BLOCK_MAX_MINUTES = 15.0
BLOCK_MIN_MINUTES = 5.0


@dataclass(frozen=True)
class IntentView:
    """An LO's intent as the chooser may read it (§5).

    DL1 has no intent control (DL2 builds it), so every LO is uncommitted:
    today's behaviour at the 0.90 recall target. Deadlines come from active
    goals that have a due date.
    """

    choice: str = "uncommitted"
    disposition: str = "active"
    recall_target: float = 0.90
    deadline: str | None = None


@dataclass(frozen=True)
class PlanState:
    """Everything a chooser may read (§6.8)."""

    plan_id: str
    kind: PlanKind
    minutes_budget: float
    #: budget - estimates of all chosen blocks (finished and current).
    minutes_left: float
    #: each lane's allotment - its chosen blocks, after redistribution (rule 1).
    lane_minutes_left: Mapping[str, float]
    days_since_last_activity: int
    streak_days: int
    current_block_id: str | None
    intents: Mapping[str, IntentView] = field(default_factory=dict)
    #: A re-entry plan's remaining item allowance (§7, D11); None otherwise.
    items_left: int | None = None
    #: each lane's allotment after redistribution (the share's denominator).
    lane_minutes_allotted: Mapping[str, float] = field(default_factory=dict)
    #: the lane order ties go in (``lane_quota_v1``); new first in the plan
    #: after a re-entry plan (:data:`AFTER_REENTRY_LANE_PRIORITY`).
    lane_priority: tuple[str, ...] = LANES


@dataclass(frozen=True)
class ReadingTarget:
    """A reading block's section (§6.10)."""

    source_id: str
    extraction_id: str
    section_id: str
    section_title: str
    #: section words x (1 - spans_seen / span_count)
    words_left: int
    #: the block covers only part of what is left
    partial: bool = False

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class BlockCandidate:
    candidate_id: str
    lane: Lane
    action: str
    subtype: str | None
    learning_object_ids: tuple[str, ...]
    #: planned items, in within-block order; empty for reading
    item_ids: tuple[str, ...]
    #: set only for a reading block (lane "new")
    reading: ReadingTarget | None
    est_minutes: float
    #: the source's own score, logged and shown
    planner_value: float
    #: plain-language reason from the source
    reason: str
    #: per-item estimates, aligned with ``item_ids`` (the container stores them
    #: on each item's plan event, §6.4).
    item_minutes: tuple[float, ...] = ()
    #: the reading section's full estimate when ``reading.partial`` (display).
    reading_full_minutes: float | None = None
    #: Router R2a: the staged frame's annotations (the P4 ladder rungs its
    #: learning objects are eligible for, whether serving it is reversible,
    #: the plain reason code). Empty from DL1's source, and then absent from
    #: the logged row, so DL1's receipts are unchanged.
    annotations: Mapping[str, Any] = field(default_factory=dict, compare=False, hash=False)

    def log_row(self) -> dict[str, Any]:
        row = {
            "candidate_id": self.candidate_id,
            "lane": self.lane,
            "item_ids": list(self.item_ids),
            "learning_object_ids": list(self.learning_object_ids),
            "reading": self.reading.as_dict() if self.reading is not None else None,
            "est_minutes": round(self.est_minutes, 4),
            "planner_value": round(self.planner_value, 6),
        }
        if self.annotations:
            row["annotations"] = dict(self.annotations)
        return row


class BlockSource(Protocol):
    name: str

    def candidates(self, state: PlanState) -> list[BlockCandidate]: ...


@dataclass(frozen=True)
class BlockChoice:
    #: a candidate id, CONTINUE_CURRENT or STOP_FOR_TODAY
    candidate_id: str
    chosen_by: ChosenBy
    #: exact for sampled choices; 1.0 deterministic; None for a learner pick
    propensity: float | None
    why: str
    why_kind: WhyKind
    #: router_decisions.id from R2
    decision_ref: str | None = None
    #: Router R2a: what the router's chooser recorded for this decision (its
    #: mode and policy, the learner-state card it built and the card's hash,
    #: the "why" code, a staged controller decision it persisted). The
    #: container copies it to the ``plan_block`` logger, which writes it with
    #: the block, in the block's transaction; the chooser never writes rows.
    router_record: Mapping[str, Any] | None = field(default=None, compare=False, hash=False)


class BlockChooser(Protocol):
    name: str

    def choose(self, state: PlanState, feasible: Sequence[BlockCandidate]) -> BlockChoice: ...


class DecisionPending(Exception):
    """Router R2b: a chooser that may not wait (a read, a prefetch) found the
    decision's models still out. Nothing is decided or written; the boundary
    stays open, and the next call (or a serving step, which waits) decides it."""

    def __init__(self, key: str = "") -> None:
        super().__init__(f"the decision {key[:12]} is waiting for its models")
        self.key = key


__all__ = [
    "AFTER_REENTRY_LANE_PRIORITY",
    "BLOCK_MAX_MINUTES",
    "BLOCK_MIN_MINUTES",
    "BlockCandidate",
    "BlockChoice",
    "BlockChooser",
    "BlockSource",
    "CONTINUE_CURRENT",
    "ChosenBy",
    "DecisionPending",
    "FLOW_ORDER",
    "IntentView",
    "LANES",
    "LANE_ACTIONS",
    "Lane",
    "PICK_DEDUCTION_ORDER",
    "PlanKind",
    "PlanState",
    "REENTRY_LANES",
    "ReadingTarget",
    "STOP_FOR_TODAY",
    "STOP_OFFER_MINUTES",
    "WhyKind",
]
