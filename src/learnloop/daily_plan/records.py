"""A daily plan as persisted: ``daily_plans`` + its blocks + their event receipts.

Everything the container knows about a plan is reconstructed here from the
rows (§10): which items are planned, served, done, skipped or displaced, each
block's estimate, and the lane ledger (allotments after releases and learner-
pick deductions, and what the chosen blocks spent). Pure reads; the engine
appends the events.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from learnloop.daily_plan.types import LANES, ReadingTarget

_EPS = 1e-9

#: How an item entered a plan.
ORIGIN_CHOOSER = "chooser"
ORIGIN_REQUESTED = "requested"
ORIGIN_FOLLOWUP = "followup"
ORIGIN_LEARNER_PICK = "learner_pick"
#: Items whose estimate the lanes pay for (requests are deducted before the
#: split; learner picks are deducted from the lanes when picked).
LANE_ORIGINS = frozenset({ORIGIN_CHOOSER, ORIGIN_FOLLOWUP})

#: Plan-level receipt rows (``attention_blocks`` rows with a NULL
#: ``plan_ordinal``): decisions that are not blocks (review F6, F10).
RECEIPT_STOP = "stop_for_today"
RECEIPT_OPEN_LIST_PICK = "open_list_pick"


@dataclass
class PlannedItem:
    block_id: str
    position: int
    practice_item_id: str
    learning_object_id: str
    lane: str | None
    est_minutes: float
    origin: str
    planned_at: str
    new_admitted: bool = False
    check_kind: str | None = None
    served_at: str | None = None
    scheduler_candidate_id: str | None = None
    done_at: str | None = None
    attempt_id: str | None = None
    wall_ms: int | None = None
    skipped_at: str | None = None
    displaced_at: str | None = None
    displaced_reason: str | None = None
    #: A mid-plan follow-up's charge to its lane (review F4): the minutes other
    #: lanes released to it when its own lane had too few left, recorded on its
    #: ``item_planned`` event. Applies while the follow-up is not displaced.
    lane_release: dict[str, Any] | None = None

    @property
    def displaced(self) -> bool:
        return self.displaced_at is not None

    @property
    def done(self) -> bool:
        return self.done_at is not None

    @property
    def skipped(self) -> bool:
        return self.skipped_at is not None

    @property
    def resolved(self) -> bool:
        return self.done or self.skipped or self.displaced

    @property
    def state(self) -> str:
        if self.displaced:
            return "displaced"
        if self.done:
            return "done"
        if self.skipped:
            return "skipped"
        if self.served_at is not None:
            return "served"
        return "planned"


@dataclass
class PlannedBlock:
    id: str
    ordinal: int
    lane: str | None
    action: str
    subtype: str | None
    chosen_by: str
    budget_minutes: float
    created_at: str
    session_id: str | None = None
    decision_ref: str | None = None
    reading: dict[str, Any] | None = None
    chosen: dict[str, Any] = field(default_factory=dict)
    items: list[PlannedItem] = field(default_factory=list)
    started_at: str | None = None
    ended_at: str | None = None
    outcome: str | None = None
    reading_progress: tuple[int, int] | None = None
    simulated: bool = False
    #: Router R2c: follow-ups the restraint decided while this block ran,
    #: ``practice_item_id -> "deferred" | "refused"`` (``followup_deferred``,
    #: ``followup_refused`` events).
    followup_decisions: dict[str, str] = field(default_factory=dict)

    @property
    def is_reading(self) -> bool:
        return self.reading is not None

    def deferred_followups(self) -> set[str]:
        """Follow-ups the restraint let wait for the next block (R2c)."""

        return {item for item, kind in self.followup_decisions.items() if kind == "deferred"}

    @property
    def reading_target(self) -> ReadingTarget | None:
        if self.reading is None:
            return None
        return ReadingTarget(
            source_id=str(self.reading.get("source_id") or ""),
            extraction_id=str(self.reading.get("extraction_id") or ""),
            section_id=str(self.reading.get("section_id") or ""),
            section_title=str(self.reading.get("section_title") or ""),
            words_left=int(self.reading.get("words_left") or 0),
            partial=bool(self.reading.get("partial")),
        )

    def est_minutes(self) -> float:
        if self.is_reading:
            return float(self.budget_minutes)
        return sum(item.est_minutes for item in self.items if not item.displaced)

    @property
    def finished(self) -> bool:
        if self.ended_at is not None:
            return True
        if self.is_reading:
            return False
        return all(item.resolved for item in self.items)

    def next_item(self) -> PlannedItem | None:
        """The block's next item to serve: a served-but-unanswered item first
        (resume), then mid-plan follow-ups, then planned order."""

        open_items = [item for item in self.items if not item.resolved]
        if not open_items:
            return None
        served = [item for item in open_items if item.served_at is not None]
        if served:
            return served[0]
        followups = [item for item in open_items if item.origin == ORIGIN_FOLLOWUP]
        if followups:
            return followups[0]
        return sorted(open_items, key=lambda item: item.position)[0]


@dataclass
class PlanRecord:
    row: dict[str, Any]
    blocks: list[PlannedBlock] = field(default_factory=list)
    #: Append-only receipts that are not blocks, oldest first: each stop
    #: decision (a ``block_chosen`` event naming STOP_FOR_TODAY with its
    #: candidate set, chooser and propensity) and each pick served after the
    #: plan closed. They never count toward the plan's minutes or items.
    receipts: list[PlannedBlock] = field(default_factory=list)

    def stops(self) -> list[PlannedBlock]:
        return [receipt for receipt in self.receipts if receipt.action == RECEIPT_STOP]

    @property
    def id(self) -> str:
        return str(self.row["id"])

    @property
    def kind(self) -> str:
        return str(self.row["kind"])

    @property
    def status(self) -> str:
        return str(self.row["status"])

    @property
    def is_open(self) -> bool:
        return self.status == "open"

    @property
    def budget(self) -> float:
        return float(self.row["minutes_budget"])

    @property
    def split(self) -> dict[str, Any]:
        return dict(self.row.get("split") or {})

    @property
    def admission(self) -> dict[str, Any]:
        return dict(self.row.get("admission") or {})

    @property
    def lanes_allowed(self) -> tuple[str, ...]:
        allowed = self.split.get("lanes_allowed") or list(LANES)
        return tuple(lane for lane in LANES if lane in allowed)

    def items(self) -> list[PlannedItem]:
        return [item for block in self.blocks for item in block.items]

    def active_items(self) -> list[PlannedItem]:
        return [item for item in self.items() if not item.displaced]

    def minutes_planned(self) -> float:
        return sum(block.est_minutes() for block in self.blocks)

    def minutes_left(self) -> float:
        return max(self.budget - self.minutes_planned(), 0.0)

    def current_block(self) -> PlannedBlock | None:
        for block in sorted(self.blocks, key=lambda b: b.ordinal):
            if not block.finished:
                return block
        return None

    def next_ordinal(self) -> int:
        return max((block.ordinal for block in self.blocks), default=0) + 1

    def refused_followups(self) -> set[str]:
        """Follow-ups a hard constraint refused in this plan (R2c): never placed again in it."""

        return {
            item for block in self.blocks for item, kind in block.followup_decisions.items() if kind == "refused"
        }

    def planned_ids(self) -> set[str]:
        """Items this plan has taken (displaced items go back to the pool)."""

        return {item.practice_item_id for item in self.items() if not item.displaced}

    def item_count(self) -> int:
        return len(self.active_items())

    def ledger(self) -> tuple[dict[str, float], dict[str, float]]:
        """(allotment, spent) per lane, §6.2 / §6.8 rule 1.

        Allotments start from the split in force (its epoch: the build, or the
        latest minutes change) and move with each later block decision's
        redistribution, each learner pick's deductions and each mid-plan
        follow-up's lane release. Spent is what the chosen blocks' lane-paid
        items (follow-ups included) and reading blocks are estimated at.
        """

        split = self.split
        lanes = split.get("lanes") or {}
        allotment = {lane: float((lanes.get(lane) or {}).get("minutes", 0.0)) for lane in LANES}
        # The split in force applies from this block ordinal on (1 at the build;
        # the next ordinal after a minutes change re-planned the rest).
        epoch = int(split.get("epoch_ordinal") or 1)
        for block in sorted(self.blocks, key=lambda b: b.ordinal):
            if block.ordinal < epoch:
                continue
            redistribution = block.chosen.get("redistribution") or {}
            for release in redistribution.get("released") or []:
                lane = release.get("from")
                if lane in allotment:
                    allotment[lane] -= float(release.get("minutes") or 0.0)
            target = redistribution.get("to")
            if target in allotment:
                allotment[target] += float(redistribution.get("given") or 0.0)
            for lane, minutes in (block.chosen.get("deductions") or {}).items():
                if lane in allotment:
                    allotment[lane] -= float(minutes or 0.0)
        # Follow-ups are inserted into a block already chosen (possibly before
        # the epoch), so their releases are dated by when they were planned.
        epoch_at = split.get("epoch_at")
        for block in self.blocks:
            for item in block.items:
                release = item.lane_release
                if not release or item.displaced or (epoch_at and item.planned_at < str(epoch_at)):
                    continue
                for entry in release.get("released") or []:
                    lane = entry.get("from")
                    if lane in allotment:
                        allotment[lane] -= float(entry.get("minutes") or 0.0)
                target = release.get("to")
                if target in allotment:
                    allotment[target] += float(release.get("given") or 0.0)
        spent = {lane: 0.0 for lane in LANES}
        for block in self.blocks:
            if block.is_reading:
                spent["new"] += block.est_minutes()
                continue
            for item in block.items:
                if item.displaced or item.origin not in LANE_ORIGINS:
                    continue
                if item.lane in spent:
                    spent[item.lane] += item.est_minutes
        return {lane: max(value, 0.0) for lane, value in allotment.items()}, spent

    def lane_left(self) -> dict[str, float]:
        allotment, spent = self.ledger()
        return {lane: max(allotment[lane] - spent[lane], 0.0) for lane in LANES}


def assemble(
    plan_rows: Sequence[Mapping[str, Any]],
    block_rows: Sequence[Mapping[str, Any]],
    event_rows: Sequence[Mapping[str, Any]],
) -> list[PlanRecord]:
    """Fold persisted rows into records (events in ordinal order)."""

    events_by_block: dict[str, list[Mapping[str, Any]]] = {}
    for event in event_rows:
        events_by_block.setdefault(str(event["block_id"]), []).append(event)
    blocks_by_plan: dict[str, list[PlannedBlock]] = {}
    receipts_by_plan: dict[str, list[PlannedBlock]] = {}
    for row in block_rows:
        receipt = row.get("plan_ordinal") is None
        block = PlannedBlock(
            id=str(row["id"]),
            ordinal=int(row["plan_ordinal"] or 0),
            lane=row.get("lane"),
            action=str(row["action"]),
            subtype=row.get("subtype"),
            chosen_by=str(row.get("chosen_by") or ""),
            budget_minutes=float(row["budget_minutes"]),
            created_at=str(row["created_at"]),
            session_id=row.get("session_id"),
            decision_ref=row.get("decision_ref"),
            reading=row.get("reading"),
        )
        by_item: dict[str, PlannedItem] = {}
        for event in sorted(events_by_block.get(block.id, []), key=lambda e: int(e["event_ordinal"])):
            _apply_event(block, by_item, event)
        target = receipts_by_plan if receipt else blocks_by_plan
        target.setdefault(str(row["daily_plan_id"]), []).append(block)
    records = []
    for row in plan_rows:
        blocks = sorted(blocks_by_plan.get(str(row["id"]), []), key=lambda b: b.ordinal)
        receipts = sorted(receipts_by_plan.get(str(row["id"]), []), key=lambda b: (b.created_at, b.id))
        records.append(PlanRecord(row=dict(row), blocks=blocks, receipts=receipts))
    return records


def _apply_event(block: PlannedBlock, by_item: dict[str, PlannedItem], event: Mapping[str, Any]) -> None:
    kind = str(event["kind"])
    detail = dict(event.get("detail") or {})
    created_at = str(event["created_at"])
    item_id = detail.get("practice_item_id")
    if kind == "block_chosen":
        block.chosen = detail
    elif kind == "item_planned" and item_id:
        item = PlannedItem(
            block_id=block.id,
            position=int(detail.get("position") or len(block.items)),
            practice_item_id=str(item_id),
            learning_object_id=str(detail.get("learning_object_id") or ""),
            lane=detail.get("lane"),
            est_minutes=float(detail.get("est_minutes") or 0.0),
            origin=str(detail.get("origin") or ORIGIN_CHOOSER),
            planned_at=created_at,
            new_admitted=bool(detail.get("new_admitted")),
            check_kind=detail.get("check_kind"),
            scheduler_candidate_id=detail.get("scheduler_candidate_id"),
            lane_release=detail.get("lane_release"),
        )
        block.items.append(item)
        by_item[str(item_id)] = item
    elif kind == "item_served" and item_id in by_item:
        item = by_item[item_id]
        if item.served_at is None:
            item.served_at = created_at
        item.scheduler_candidate_id = detail.get("scheduler_candidate_id") or item.scheduler_candidate_id
    elif kind == "item_done" and item_id in by_item:
        item = by_item[item_id]
        item.done_at = str(detail.get("done_at") or created_at)
        item.attempt_id = detail.get("attempt_id")
        item.wall_ms = detail.get("wall_ms")
    elif kind == "item_skipped" and item_id in by_item:
        by_item[item_id].skipped_at = created_at
    elif kind == "item_displaced" and item_id in by_item:
        by_item[item_id].displaced_at = created_at
        by_item[item_id].displaced_reason = detail.get("reason")
    elif kind == "block_started":
        block.started_at = block.started_at or created_at
    elif kind == "block_ended":
        block.ended_at = created_at
        block.outcome = detail.get("outcome")
    elif kind == "reading_progress":
        block.reading_progress = (int(detail.get("spans_seen") or 0), int(detail.get("span_count") or 0))
    elif kind == "followup_deferred" and item_id:
        block.followup_decisions[str(item_id)] = "deferred"
    elif kind == "followup_refused" and item_id:
        block.followup_decisions[str(item_id)] = "refused"


def day_items(records: Iterable[PlanRecord]) -> list[PlannedItem]:
    return [item for record in records for item in record.items()]


__all__ = [
    "LANE_ORIGINS",
    "ORIGIN_CHOOSER",
    "ORIGIN_FOLLOWUP",
    "ORIGIN_LEARNER_PICK",
    "ORIGIN_REQUESTED",
    "PlanRecord",
    "RECEIPT_OPEN_LIST_PICK",
    "RECEIPT_STOP",
    "PlannedBlock",
    "PlannedItem",
    "assemble",
    "day_items",
]
