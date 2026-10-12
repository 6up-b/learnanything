"""Lanes (``spec_daily_loop_v1.md`` §6.1) and the ``legacy_lanes_v1`` source (§6.8).

Each eligible item from the scheduler's ranked list takes the first lane that
matches, in this order:

1. **scheduled checks -> maintain** (a due assumed-known first review, a due
   project probe under ``plan.project_probes_max_per_day``; DL2 adds "Check
   once"). Never new material, whatever their attempt history;
2. **repair**: follow-up tasks and items on LOs with recent errors;
3. **new**: never-attempted items (Phase 6's order), including never-attempted
   learner requests;
4. **maintain**: items whose (effective) due date has passed, and previously
   attempted learner requests;
5. **push**: items on goal frontiers that are not yet due.

An item that matches none stays in the full list as "later". The source then
groups each lane's items by LO in the scheduler's order and packs the groups
into blocks of up to 15 estimated minutes.
"""

from __future__ import annotations

import hashlib
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, replace
from datetime import datetime
from typing import Any

from learnloop.clock import parse_utc
from learnloop.daily_plan.types import (
    BLOCK_MAX_MINUTES,
    BLOCK_MIN_MINUTES,
    LANE_ACTIONS,
    LANES,
    BlockCandidate,
    Lane,
    PlanState,
    ReadingTarget,
)

SOURCE_NAME = "legacy_lanes_v1"
_EPS = 1e-9

#: Scheduler components that mark a follow-up (``_insert_pending_followups``).
FOLLOWUP_COMPONENTS = ("intervention_followup", "negative_surprise_followup")


@dataclass(frozen=True)
class ScheduledCheck:
    """A fixed-date cold check the plan serves in the maintain lane (§6.1 rule 1)."""

    kind: str  # assumed_check | project_probe | check_once
    #: Project probes from diffs labelled automation / all_at_once come first (§6.9).
    priority: int = 0


#: Project understanding M2 registers its due-probe source here (§6.9). It maps
#: an eligible item id to a ScheduledCheck("project_probe"). Nothing on this base
#: produces project probes, so the default registry is empty.
ScheduledCheckProvider = Callable[[Any, Any, Sequence[str]], Mapping[str, ScheduledCheck]]
_CHECK_PROVIDERS: list[ScheduledCheckProvider] = []


def register_scheduled_check_provider(provider: ScheduledCheckProvider) -> None:
    if provider not in _CHECK_PROVIDERS:
        _CHECK_PROVIDERS.append(provider)


def unregister_scheduled_check_provider(provider: ScheduledCheckProvider) -> None:
    if provider in _CHECK_PROVIDERS:
        _CHECK_PROVIDERS.remove(provider)


def scheduled_checks(vault: Any, repository: Any, item_ids: Sequence[str]) -> dict[str, ScheduledCheck]:
    checks: dict[str, ScheduledCheck] = {}
    for provider in list(_CHECK_PROVIDERS):
        for item_id, check in dict(provider(vault, repository, item_ids)).items():
            checks.setdefault(str(item_id), check)
    return checks


@dataclass(frozen=True)
class PoolItem:
    """One eligible item as the plan sees it."""

    practice_item_id: str
    learning_object_id: str
    rank: int
    priority: float
    lane: Lane | None  # None: "later" (stays in the full list)
    reason: str
    est_minutes: float
    never_attempted: bool
    requested: bool = False
    check_kind: str | None = None
    check_priority: int = 0
    followup: bool = False
    due: bool = False
    goal_frontier: bool = False
    deadline: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "practice_item_id": self.practice_item_id,
            "learning_object_id": self.learning_object_id,
            "rank": self.rank,
            "lane": self.lane,
            "reason": self.reason,
            "est_minutes": round(self.est_minutes, 4),
            "never_attempted": self.never_attempted,
            "requested": self.requested,
            "check_kind": self.check_kind,
            "followup": self.followup,
        }


def is_followup(scheduled: Any) -> bool:
    components = getattr(scheduled, "components", {}) or {}
    return getattr(scheduled, "followup_kind", None) is not None or any(
        float(components.get(name, 0.0) or 0.0) > 0.0 for name in FOLLOWUP_COMPONENTS
    )


def classify_item(
    scheduled: Any,
    *,
    rank: int,
    state: Any,
    requested: bool,
    now: datetime,
    est_minutes: float,
    check: ScheduledCheck | None,
    probe_slot_available: bool,
    deadline: bool = False,
) -> PoolItem:
    """§6.1: the first lane that matches, in order."""

    components = getattr(scheduled, "components", {}) or {}
    never_attempted = state is None or getattr(state, "last_attempt_at", None) is None
    due_at = parse_utc(getattr(state, "due_at", None)) if state is not None else None
    due = due_at is not None and due_at <= now
    frontier = float(components.get("goal_frontier", 0.0) or 0.0) > 0.0
    followup = is_followup(scheduled)
    base = dict(
        practice_item_id=scheduled.practice_item_id,
        learning_object_id=scheduled.learning_object_id,
        rank=rank,
        priority=float(scheduled.priority),
        est_minutes=float(est_minutes),
        never_attempted=never_attempted,
        requested=requested,
        followup=followup,
        due=due,
        goal_frontier=frontier,
        deadline=deadline,
    )
    if float(components.get("assumed_check", 0.0) or 0.0) > 0.0 and (check is None or check.kind != "project_probe"):
        check = ScheduledCheck("assumed_check")
    if check is not None:
        if check.kind == "project_probe" and not probe_slot_available:
            return PoolItem(lane=None, reason="a due project probe beyond today's probe limit", check_kind=check.kind, check_priority=check.priority, **base)
        reasons = {
            "assumed_check": "the first review of a topic assumed known (not tested): this is the check",
            "project_probe": "a delayed question about your project's code",
            "check_once": "your one delayed check",
        }
        return PoolItem(lane="maintain", reason=reasons.get(check.kind, "a scheduled check"), check_kind=check.kind, check_priority=check.priority, **base)
    if followup or float(components.get("recent_error", 0.0) or 0.0) > 0.0:
        return PoolItem(lane="repair", reason="a follow-up" if followup else "a recent error on this topic", **base)
    if never_attempted:
        return PoolItem(lane="new", reason="your request" if requested else "new material", **base)
    if due or requested:
        return PoolItem(lane="maintain", reason="your request" if requested and not due else "past its review date", **base)
    if frontier:
        return PoolItem(lane="push", reason="on your goal's frontier, not due yet", **base)
    return PoolItem(lane=None, reason="later", **base)


def classify_pool(
    scheduled_items: Sequence[Any],
    *,
    item_states: Mapping[str, Any],
    requested_ids: Iterable[str],
    now: datetime,
    estimate: Callable[[str], float],
    checks: Mapping[str, ScheduledCheck],
    probe_cap_left: int,
    deadline_learning_object_ids: Iterable[str] = (),
) -> list[PoolItem]:
    """Classify the scheduler's ranked list, in rank order (§6.1)."""

    requested = set(requested_ids)
    deadline_los = set(deadline_learning_object_ids)
    # Due project probes beyond the cap stay "later"; automation / all_at_once
    # diffs come first (§6.9), then the scheduler's rank.
    probes = sorted(
        (
            (index, scheduled.practice_item_id)
            for index, scheduled in enumerate(scheduled_items)
            if (check := checks.get(scheduled.practice_item_id)) is not None and check.kind == "project_probe"
        ),
        key=lambda pair: (-checks[pair[1]].priority, pair[0]),
    )
    probe_slots = {item_id for _index, item_id in probes[: max(int(probe_cap_left), 0)]}
    pool = []
    for rank, scheduled in enumerate(scheduled_items):
        item_id = scheduled.practice_item_id
        pool.append(
            classify_item(
                scheduled,
                rank=rank,
                state=item_states.get(item_id),
                requested=item_id in requested,
                now=now,
                est_minutes=estimate(item_id),
                check=checks.get(item_id),
                probe_slot_available=item_id in probe_slots,
                deadline=scheduled.learning_object_id in deadline_los,
            )
        )
    return pool


def reentry_order(pool: Sequence[PoolItem]) -> list[PoolItem]:
    """§7: assumed-known checks that came due, then intent tier (goals with
    deadlines; then the rest: DL1 has no Keep or Light touch yet), then rank."""

    return sorted(
        pool,
        key=lambda item: (
            0 if item.check_kind == "assumed_check" else 1,
            0 if item.deadline else 1,
            item.rank,
        ),
    )


def _candidate_id(lane: str, item_ids: Sequence[str], reading: ReadingTarget | None) -> str:
    material = "|".join(item_ids) if reading is None else f"{reading.extraction_id}|{reading.section_id}"
    digest = hashlib.sha256(f"{lane}|{material}".encode("utf-8")).hexdigest()[:16]
    return f"{lane}:{digest}"


def _group_by_lo(items: Sequence[PoolItem]) -> list[list[PoolItem]]:
    groups: dict[str, list[PoolItem]] = {}
    for item in items:
        groups.setdefault(item.learning_object_id, []).append(item)
    return list(groups.values())


def _lane_reason(lane: str, items: Sequence[PoolItem], titles: Mapping[str, str]) -> str:
    count = len(items)
    los = []
    for item in items:
        title = titles.get(item.learning_object_id, item.learning_object_id)
        if title not in los:
            los.append(title)
    topic = los[0] if len(los) == 1 else f"{los[0]} and {len(los) - 1} more"
    plural = "s" if count != 1 else ""
    if lane == "repair":
        followups = sum(1 for item in items if item.followup)
        if followups:
            return f"repair: {count} item{plural} following up recent mistakes on {topic}"
        return f"repair: {count} item{plural} on {topic}, where you made recent errors"
    if lane == "maintain":
        checks = [item for item in items if item.check_kind]
        if checks and len(checks) == count:
            kinds = {item.check_kind for item in checks}
            if kinds == {"assumed_check"}:
                return f"maintain: the check on {topic}, assumed known (not tested)"
            return f"maintain: {count} scheduled check{plural} ({topic})"
        return f"maintain: {count} review{plural} past their 90% recall target ({topic})"
    if lane == "new":
        return f"new: {count} new item{plural} on {topic}"
    return f"push: {count} item{plural} toward your goal on {topic}, not due yet"


@dataclass
class LegacyLanesSource:
    """``legacy_lanes_v1``: deterministic block candidates from the lanes (§6.8).

    Built per block boundary from the classified pool (items already planned
    removed). For each lane it groups items by LO in rank order and packs them
    into blocks of up to 15 estimated minutes, never larger than the lane's or
    the plan's remaining minutes:

    - in ``maintain`` and ``repair`` an LO group under five minutes merges, in
      rank order, with the lane's next groups up to the bound (interleaved
      review is coherent there);
    - in ``new`` and ``push`` a block stays on one LO and may be short;
    - there is no minimum: one due item, a lane's last items, or the plan's last
      minutes are a complete block.

    ``planner_value`` is the source's own score: its rank order.
    """

    pool: Sequence[PoolItem]
    lanes_allowed: Sequence[str] = LANES
    #: new-lane items the plan admitted (§6.3); other never-attempted items wait.
    admitted_new_ids: frozenset[str] = frozenset()
    reading: ReadingTarget | None = None
    reading_full_minutes: float | None = None
    titles: Mapping[str, str] | None = None
    max_candidates_per_lane: int = 3
    name: str = SOURCE_NAME

    def lane_items(self, lane: str) -> list[PoolItem]:
        items = [item for item in self.pool if item.lane == lane]
        if lane == "new":
            items = [item for item in items if item.practice_item_id in self.admitted_new_ids]
            # Never-attempted learner requests take the first new-lane slots (§6.3).
            items.sort(key=lambda item: (0 if item.requested else 1, item.rank))
        return items

    def candidates(self, state: PlanState) -> list[BlockCandidate]:
        titles = self.titles or {}
        out: list[BlockCandidate] = []
        for lane in LANES:
            if lane not in self.lanes_allowed:
                continue
            limit = min(
                BLOCK_MAX_MINUTES,
                float(state.lane_minutes_left.get(lane, 0.0)),
                float(state.minutes_left),
            )
            if limit <= _EPS:
                continue
            blocks = _pack(
                self.lane_items(lane),
                lane=lane,
                limit=limit,
                items_left=state.items_left,
                merge_small=lane in ("maintain", "repair"),
                max_blocks=self.max_candidates_per_lane,
            )
            for block in blocks:
                action, subtype = LANE_ACTIONS[lane]
                ids = tuple(item.practice_item_id for item in block)
                out.append(
                    BlockCandidate(
                        candidate_id=_candidate_id(lane, ids, None),
                        lane=lane,  # type: ignore[arg-type]
                        action=action,
                        subtype=subtype,
                        learning_object_ids=tuple(dict.fromkeys(item.learning_object_id for item in block)),
                        item_ids=ids,
                        reading=None,
                        est_minutes=sum(item.est_minutes for item in block),
                        planner_value=1.0 / (1.0 + min(item.rank for item in block)),
                        reason=_lane_reason(lane, block, titles),
                        item_minutes=tuple(item.est_minutes for item in block),
                    )
                )
            if lane == "new" and self.reading is not None:
                reading = self._reading_candidate(limit)
                if reading is not None:
                    out.append(reading)
        return out

    def _reading_candidate(self, limit: float) -> BlockCandidate | None:
        assert self.reading is not None
        full = float(self.reading_full_minutes or 0.0)
        if full <= _EPS:
            return None
        est = min(full, limit)
        if est < 1.0 - _EPS and full > est + _EPS:
            # Less than a minute of a longer section is not worth opening.
            return None
        partial = est + 1e-6 < full
        target = replace(self.reading, partial=partial)
        action, subtype = LANE_ACTIONS["new"]
        title = target.section_title
        reason = (
            f"new: continue reading {title} (about {round(est)} min of about {round(full)})"
            if partial
            else f"new: continue reading {title}"
        )
        return BlockCandidate(
            candidate_id=_candidate_id("new", (), target),
            lane="new",
            action=action,
            subtype=subtype,
            learning_object_ids=(),
            item_ids=(),
            reading=target,
            est_minutes=est,
            # Reading follows the admitted new items in the source's order.
            planner_value=0.0,
            reason=reason,
            item_minutes=(),
            reading_full_minutes=full,
        )


def _pack(
    items: Sequence[PoolItem],
    *,
    lane: str,
    limit: float,
    items_left: int | None,
    merge_small: bool,
    max_blocks: int,
) -> list[list[PoolItem]]:
    """Greedy, rank-ordered packing of LO groups into blocks under ``limit``."""

    groups = _group_by_lo(items)
    blocks: list[list[PoolItem]] = []
    used: set[str] = set()
    cap_items = None if items_left is None else max(int(items_left), 0)
    if cap_items == 0:
        return blocks
    index = 0
    while index < len(groups) and len(blocks) < max_blocks:
        block: list[PoolItem] = []
        total = 0.0
        while index < len(groups):
            for item in groups[index]:
                if item.practice_item_id in used:
                    continue
                if cap_items is not None and len(block) >= cap_items:
                    break
                if total + item.est_minutes <= limit + _EPS:
                    block.append(item)
                    used.add(item.practice_item_id)
                    total += item.est_minutes
            leftover = any(item.practice_item_id not in used for item in groups[index])
            if leftover:
                if block:
                    # The group did not fit whole: the rest goes in a later block.
                    break
                # Nothing of this group fits under the limit: skip it.
                index += 1
                continue
            index += 1
            if not merge_small or total >= BLOCK_MIN_MINUTES - _EPS:
                break
            if cap_items is not None and len(block) >= cap_items:
                break
        if block:
            blocks.append(block)
    return blocks


__all__ = [
    "FOLLOWUP_COMPONENTS",
    "LegacyLanesSource",
    "PoolItem",
    "SOURCE_NAME",
    "ScheduledCheck",
    "classify_item",
    "classify_pool",
    "is_followup",
    "register_scheduled_check_provider",
    "reentry_order",
    "scheduled_checks",
    "unregister_scheduled_check_provider",
]
