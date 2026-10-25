"""Lanes (``spec_daily_loop_v1.md`` §6.1) and the ``legacy_lanes_v1`` source (§6.8).

Each eligible item from the scheduler's ranked list takes the first lane that
matches, in this order:

1. **scheduled checks -> maintain** (a due assumed-known first review, a due
   project probe under ``plan.project_probes_max_per_day``; DL2 adds "Check
   once"). Never new material, whatever their attempt history;
2. **repair**: follow-up tasks, and previously attempted items on LOs with an
   open diagnosed problem (owner decision 2026-10-12): an unresolved causal
   hypothesis or an open unresolved-cause factor from Slice 1 M2 and Slice 2
   T1 (:func:`learnloop.db.stores.daily_plans.open_diagnosed_problem_learning_object_ids`).
   A recent error alone is not repair. Only while the diagnosis split is off
   (a vault below ``mvp-0.10``, or ``diagnosis.split_enabled = false``) does
   the lane fall back to DL1's recency rule: the scheduler's ``recent_error``
   at or above :data:`REPAIR_MIN_RECENT_ERROR`. A never-attempted item is new
   material even on such an LO, so it stays under §6.3's admission, out of
   re-entry and off with ``plan.new_admission_enabled`` (review F1);
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
import math
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, field, replace
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

#: The repair lane's recency bound (review F1), now ONLY the fallback while
#: the diagnosis split is off (a vault below mvp-0.10, or
#: ``diagnosis.split_enabled = false``): with the split on, repair means an
#: open diagnosed problem (owner decision 2026-10-12; :data:`REPAIR_RULE_DIAGNOSIS`).
#: The scheduler's ``recent_error`` is ``severity x exp(-days / 7)`` over every
#: active learner error on the LO, so it never reaches zero however old the
#: error. In the fallback an item is repair only at or above exp(-2): a
#: full-severity error within the last 14 days (two of the scheduler's 7-day
#: decay constants), a half-severity one within about 9.
REPAIR_MIN_RECENT_ERROR = math.exp(-2.0)

#: Which rule decided the repair lane (recorded on the plan's ``split_json``).
REPAIR_RULE_DIAGNOSIS = "open_diagnosis"
REPAIR_RULE_RECENT_ERROR = "recent_error_fallback"


#: Why an assumed-known LO's first review is in the maintain lane.
ASSUMED_CHECK_REASON = "the first review of a topic assumed known (not tested): this is the check"
#: Learner-text gaps: the scheduler's ``gap_commitment_check`` (a prerequisite
#: created from the learner's question, its one delayed check) and
#: ``gap_sooner_check`` (mvp-0.16: a check a learner's question brought
#: forward), worded as the scheduler's own reasons are.
GAP_COMMITMENT_CHECK_REASON = "the one check on a topic added from your question"
GAP_SOONER_CHECK_REASON = "a check brought forward: your question pointed at this topic"
#: DL2: an attempted item under Learn or Master that is not due yet (§6.1 push).
INTENT_PUSH_REASON = "you chose Learn or Master here, not due yet"


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
    #: mvp-0.21: a due project probe's value-of-information decision (its
    #: forecast), when the plan valued it instead of counting it.
    voi: Mapping[str, Any] | None = field(default=None, compare=False, hash=False)
    #: mvp-0.21: the rank an admitted project probe plans at (the value
    #: order); None means the scheduler's ``rank``.
    plan_rank: int | None = None

    @property
    def order_rank(self) -> int:
        """The rank the plan orders by: ``plan_rank`` when set, else ``rank``."""

        return self.rank if self.plan_rank is None else self.plan_rank

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
            **({"plan_rank": self.plan_rank} if self.plan_rank is not None else {}),
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
    open_problem: bool | None = None,
    probe_value: Mapping[str, Any] | None = None,
    due_override: bool | None = None,
    intent_push: bool = False,
) -> PoolItem:
    """§6.1: the first lane that matches, in order.

    DL2 (intent): ``due_override`` is the item's due test on its effective due
    (§5.3) instead of the stored ``due_at``; ``intent_push`` puts an attempted
    item under Learn or Master that is not yet due in the push lane (§5.4).
    Both default to DL1's behaviour exactly.

    ``probe_value`` (mvp-0.21) is a due project probe's value-of-information
    decision: when given, the probe takes the maintain lane exactly when that
    decision continues (its value pays for its minutes), whatever the count.

    ``open_problem`` says whether the item's LO has an open diagnosed problem
    (owner decision 2026-10-12). ``None`` means the diagnosis split is off and
    the repair lane falls back to the recency rule (:data:`REPAIR_MIN_RECENT_ERROR`).
    """

    components = getattr(scheduled, "components", {}) or {}
    never_attempted = state is None or getattr(state, "last_attempt_at", None) is None
    due_at = parse_utc(getattr(state, "due_at", None)) if state is not None else None
    due = due_at is not None and due_at <= now
    if due_override is not None:
        due = bool(due_override)
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
        if check.kind == "project_probe" and probe_value is not None:
            base["voi"] = dict(probe_value)
            if probe_value.get("decision") != "continue":
                return PoolItem(
                    lane=None,
                    reason=(
                        "a due project probe that does not fit today's minutes"
                        if probe_value.get("reason") == "does_not_fit_plan_minutes"
                        else "a due project probe this plan no longer takes (skipped, answered, or new since it was built)"
                        if probe_value.get("reason") == "not_available_to_this_plan"
                        else "a due project probe whose value does not pay for its minutes today"
                    ),
                    check_kind=check.kind,
                    check_priority=check.priority,
                    **base,
                )
        elif check.kind == "project_probe" and not probe_slot_available:
            return PoolItem(lane=None, reason="a due project probe beyond today's probe limit", check_kind=check.kind, check_priority=check.priority, **base)
        reasons = {
            "assumed_check": ASSUMED_CHECK_REASON,
            "project_probe": "a delayed question about your project's code",
            "check_once": "your one delayed check",
        }
        reason = reasons.get(check.kind, "a scheduled check")
        if check.kind == "assumed_check":
            # Learner-text gaps: the scheduler serves a created prerequisite's
            # one check, and a check a gap brought forward (mvp-0.16), as an
            # assumed check; neither is "assumed known" (honest labels).
            if float(components.get("gap_commitment_check", 0.0) or 0.0) > 0.0:
                reason = GAP_COMMITMENT_CHECK_REASON
            elif float(components.get("gap_sooner_check", 0.0) or 0.0) > 0.0:
                reason = GAP_SOONER_CHECK_REASON
        return PoolItem(lane="maintain", reason=reason, check_kind=check.kind, check_priority=check.priority, **base)
    if followup:
        return PoolItem(lane="repair", reason="a follow-up", **base)
    if open_problem is None:
        recent_error = float(components.get("recent_error", 0.0) or 0.0)
        if not never_attempted and recent_error >= REPAIR_MIN_RECENT_ERROR - _EPS:
            return PoolItem(lane="repair", reason="a recent error on this topic", **base)
    elif open_problem and not never_attempted:
        return PoolItem(lane="repair", reason="an open diagnosed problem on this topic", **base)
    if never_attempted:
        return PoolItem(lane="new", reason="your request" if requested else "new material", **base)
    if due or requested:
        return PoolItem(lane="maintain", reason="your request" if requested and not due else "past its review date", **base)
    if frontier:
        return PoolItem(lane="push", reason="on your goal's frontier, not due yet", **base)
    if intent_push:
        return PoolItem(lane="push", reason=INTENT_PUSH_REASON, **base)
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
    open_problem_learning_object_ids: Iterable[str] | None = None,
    project_probe_admission: (
        Callable[[Sequence[tuple[Any, float]]], Sequence[tuple[str, Mapping[str, Any]]]] | None
    ) = None,
    is_due: Callable[[str, Any], bool] | None = None,
    push_ids: Iterable[str] = (),
) -> list[PoolItem]:
    """Classify the scheduler's ranked list, in rank order (§6.1).

    ``open_problem_learning_object_ids`` are the LOs with an open diagnosed
    problem (the repair lane, owner decision 2026-10-12); ``None`` while the
    diagnosis split is off, when repair falls back to the recency rule.

    ``project_probe_admission`` (mvp-0.21, ``voi_stopping``) values today's
    due project probes together: ``[(scheduled item, its estimated minutes)]``
    in the former cap's order ``-> [(item id, decision)]``, the admitted
    probes first in the order they were admitted (greedily, each valued
    conditionally on those admitted before it, by robust value per minute),
    then the rest. With it there is no count cap: exactly the admitted probes
    take the maintain lane, in that order, and they carry that order in
    ``plan_rank`` so the block source scores and the re-entry order follow it;
    the plan's finite minutes bound how many are planned. Without it the
    former cap (``probe_cap_left``) serves exactly.
    """

    requested = set(requested_ids)
    pushes = set(push_ids)
    open_problems = None if open_problem_learning_object_ids is None else set(open_problem_learning_object_ids)
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
    values: dict[str, Mapping[str, Any]] = {}
    admitted_order: list[str] = []
    if project_probe_admission is not None and probes:
        for item_id, decision in project_probe_admission(
            [(scheduled_items[index], estimate(item_id)) for index, item_id in probes]
        ):
            values[item_id] = decision
            if decision.get("decision") == "continue":
                admitted_order.append(item_id)
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
                open_problem=None if open_problems is None else scheduled.learning_object_id in open_problems,
                probe_value=values.get(item_id),
                due_override=None if is_due is None else is_due(item_id, item_states.get(item_id)),
                intent_push=item_id in pushes,
            )
        )
    if values:
        pool = _order_probes_by_value(pool, admitted_order)
    return pool


def _order_probes_by_value(pool: list[PoolItem], admitted_order: Sequence[str]) -> list[PoolItem]:
    """Admitted project probes take their own positions in admission order
    (the best conditional value per minute first); every other item keeps its
    place. Each admitted probe takes the rank of the position it moves into as
    its ``plan_rank``, so the pool stays in plan-rank order and everything
    that ranks by it (the block source's ``planner_value`` and so the
    chooser's tie-break, the new lane's and the re-entry order) follows the
    value order, not the scheduler's: the best probe per minute is planned
    first and the plan's minutes decide how many fit."""

    position = {item_id: index for index, item_id in enumerate(admitted_order)}
    slots = [
        index
        for index, item in enumerate(pool)
        if item.check_kind == "project_probe" and item.lane is not None and item.practice_item_id in position
    ]
    ordered = sorted((pool[index] for index in slots), key=lambda item: position[item.practice_item_id])
    reordered = list(pool)
    for index, item in zip(slots, ordered):
        reordered[index] = replace(item, plan_rank=pool[index].rank)
    return reordered


def reentry_order(pool: Sequence[PoolItem], tiers: Mapping[str, int] | None = None) -> list[PoolItem]:
    """§7: assumed-known checks that came due, then intent tier (Master,
    Learn and goals with deadlines; then Keep; then uncommitted), then rank.

    ``tiers`` (DL2) maps an item to its intent tier (``learnloop.scheduling.intent.model``:
    0 Master/Learn, 1 Keep, 2 uncommitted); None is DL1's order exactly
    (deadlines first, then the rest). Light touch is left out by the caller."""

    if tiers is None:
        return sorted(
            pool,
            key=lambda item: (
                0 if item.check_kind == "assumed_check" else 1,
                0 if item.deadline else 1,
                item.order_rank,
            ),
        )
    ordered = sorted(
        pool,
        key=lambda item: (
            0 if item.check_kind == "assumed_check" else 1,
            0 if item.deadline else min(int(tiers.get(item.practice_item_id, 2)), 2),
            item.order_rank,
        ),
    )
    # Codex review F6: the block source scores blocks by ``order_rank``
    # (``planner_value``, the chooser's tie-break), so the intent order is
    # carried into it: each item takes the rank of the position it moves
    # into as its ``plan_rank``, as an admitted project probe does
    # (``_order_probes_by_value``). Otherwise the chooser would undo it.
    ranks = sorted(item.order_rank for item in pool)
    return [replace(item, plan_rank=rank) for item, rank in zip(ordered, ranks)]


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
        if any(item.reason == "an open diagnosed problem on this topic" for item in items):
            return f"repair: {count} item{plural} on {topic}, where a diagnosed problem is still open"
        return f"repair: {count} item{plural} on {topic}, where you made recent errors"
    if lane == "maintain":
        checks = [item for item in items if item.check_kind]
        if checks and len(checks) == count:
            kinds = {item.check_kind for item in checks}
            reasons = {item.reason for item in checks}
            if kinds == {"assumed_check"} and reasons == {ASSUMED_CHECK_REASON}:
                return f"maintain: the check on {topic}, assumed known (not tested)"
            if kinds == {"assumed_check"} and reasons == {GAP_COMMITMENT_CHECK_REASON}:
                return f"maintain: the one check on {topic}, added from your question"
            if kinds == {"assumed_check"} and reasons == {GAP_SOONER_CHECK_REASON}:
                return f"maintain: the check on {topic}, brought forward by your question"
            if kinds == {"check_once"}:
                # DL2 (§5.2, Reader §9.3 item 10): the plan line keeps its
                # purpose before the check; the check itself locates nothing.
                return f"check · on your own · {count} check{plural} you asked for ({topic})"
            return f"maintain: {count} scheduled check{plural} ({topic})"
        return f"maintain: {count} review{plural} past their 90% recall target ({topic})"
    if lane == "new":
        return f"new: {count} new item{plural} on {topic}"
    if any(item.reason == INTENT_PUSH_REASON for item in items) and not any(item.goal_frontier for item in items):
        return f"push: {count} item{plural} on {topic}, which you chose to learn, not due yet"
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

    ``planner_value`` is the source's own score: its rank order (an admitted
    project probe's ``plan_rank``, the value order, at mvp-0.21).
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
            items.sort(key=lambda item: (0 if item.requested else 1, item.order_rank))
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
                        planner_value=1.0 / (1.0 + min(item.order_rank for item in block)),
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
        if target.path_label is not None:
            # RW7b: the reading path chose this section (only then; DL1's
            # reason otherwise, byte for byte).
            reason += f", {target.path_label} on your reading path"
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
    "ASSUMED_CHECK_REASON",
    "FOLLOWUP_COMPONENTS",
    "GAP_COMMITMENT_CHECK_REASON",
    "GAP_SOONER_CHECK_REASON",
    "LegacyLanesSource",
    "PoolItem",
    "REPAIR_MIN_RECENT_ERROR",
    "REPAIR_RULE_DIAGNOSIS",
    "REPAIR_RULE_RECENT_ERROR",
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
