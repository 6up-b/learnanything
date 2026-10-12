"""The split (``spec_daily_loop_v1.md`` §6.2, P3): rule ``split_v1``.

The system sets the split, shows it, and asks nothing. With M the budget minus
the estimates of the requested items already placed in the first block:

1. repair   = min(repair load, repair_max_share x M)
2. maintain = min(due maintenance load, maintain_max_share x M)
3. the rest goes to new and push: new = min(admitted new-material minutes,
   half the rest if push candidates exist, else all of it); push takes the
   remainder up to its load.
4. unused minutes flow on: to maintenance overflow, then repair overflow, then
   push. New never receives flowed minutes beyond its admitted minutes.

Re-entry plans use only repair and maintain (§7). The container repeats step 4
at every block boundary (:func:`redistribute`, §6.8 rule 1).
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from math import floor
from typing import Any

from learnloop.daily_plan.types import FLOW_ORDER, LANES

SPLIT_RULE = "split_v1"
_EPS = 1e-9


@dataclass(frozen=True)
class LaneSplit:
    lane: str
    minutes: float
    load: float
    cap: float | None
    reason: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "lane": self.lane,
            "minutes": round(self.minutes, 4),
            "load": round(self.load, 4),
            "cap": None if self.cap is None else round(self.cap, 4),
            "reason": self.reason,
        }


@dataclass(frozen=True)
class Split:
    rule: str
    budget: float
    requested_minutes: float
    m: float
    lanes: Mapping[str, LaneSplit]
    flowed: tuple[dict[str, Any], ...] = ()
    lanes_allowed: tuple[str, ...] = LANES

    def minutes(self, lane: str) -> float:
        entry = self.lanes.get(lane)
        return entry.minutes if entry is not None else 0.0

    def display_minutes(self) -> dict[str, int]:
        return display_lane_minutes({lane: self.minutes(lane) for lane in self.lanes_allowed})

    def line(self) -> str:
        return split_line(self.budget, self.display_minutes())

    def as_dict(self) -> dict[str, Any]:
        return {
            "rule": self.rule,
            "budget": round(self.budget, 4),
            "requested_minutes": round(self.requested_minutes, 4),
            "m": round(self.m, 4),
            "lanes_allowed": list(self.lanes_allowed),
            "lanes": {lane: entry.as_dict() for lane, entry in self.lanes.items()},
            "flowed": [dict(entry) for entry in self.flowed],
            "display": self.display_minutes(),
            "line": self.line(),
        }


def display_lane_minutes(minutes: Mapping[str, float]) -> dict[str, int]:
    """Whole minutes per lane whose sum is the rounded total (largest remainder).

    The line and the "why" show these numbers; the engine enforces the exact
    values they round, so every shown number is the plan's own (G3).
    """

    total = round(sum(max(value, 0.0) for value in minutes.values()))
    floors = {lane: floor(max(value, 0.0) + _EPS) for lane, value in minutes.items()}
    remainder = total - sum(floors.values())
    order = sorted(
        minutes,
        key=lambda lane: (-(max(minutes[lane], 0.0) - floors[lane]), LANES.index(lane) if lane in LANES else 99),
    )
    result = dict(floors)
    for lane in order:
        if remainder <= 0:
            break
        result[lane] += 1
        remainder -= 1
    return result


def split_line(budget: float, display: Mapping[str, int]) -> str:
    """"25 min · maintain 13 · repair 4 · new 4 · push 4" (§6.2; zero lanes omitted)."""

    parts = [f"{_minutes_text(budget)} min"]
    for lane in ("maintain", "repair", "new", "push"):
        value = display.get(lane, 0)
        if value > 0:
            parts.append(f"{lane} {value}")
    return " · ".join(parts)


def _minutes_text(value: float) -> str:
    return str(int(round(value))) if abs(value - round(value)) < 0.05 else f"{value:.1f}"


def split_v1(
    *,
    budget: float,
    requested_minutes: float,
    loads: Mapping[str, float],
    admitted_new_minutes: float,
    push_candidates: bool,
    repair_max_share: float,
    maintain_max_share: float,
    lanes_allowed: Sequence[str] = LANES,
    new_first: bool = False,
) -> Split:
    """Compute the split. ``new_first`` is "more new material" (§6.3): the
    labelled override gives new its admitted minutes before the other lanes."""

    allowed = tuple(lane for lane in LANES if lane in set(lanes_allowed))
    m = max(float(budget) - float(requested_minutes), 0.0)
    load = {lane: max(float(loads.get(lane, 0.0)), 0.0) if lane in allowed else 0.0 for lane in LANES}
    admitted_new = max(float(admitted_new_minutes), 0.0) if "new" in allowed else 0.0
    minutes = {lane: 0.0 for lane in LANES}
    caps: dict[str, float | None] = {lane: None for lane in LANES}
    remaining = m
    if new_first and "new" in allowed:
        minutes["new"] = min(admitted_new, remaining)
        remaining -= minutes["new"]
    if "repair" in allowed:
        caps["repair"] = repair_max_share * m
        minutes["repair"] = min(load["repair"], caps["repair"], remaining)
        remaining -= minutes["repair"]
    if "maintain" in allowed:
        caps["maintain"] = maintain_max_share * m
        minutes["maintain"] = min(load["maintain"], caps["maintain"], remaining)
        remaining -= minutes["maintain"]
    rest = max(remaining, 0.0)
    if not new_first:
        if "new" in allowed:
            half = rest / 2.0 if (push_candidates and "push" in allowed) else rest
            caps["new"] = admitted_new
            minutes["new"] = min(admitted_new, half)
        if "push" in allowed:
            minutes["push"] = min(load["push"], rest - minutes["new"])
    elif "push" in allowed:
        minutes["push"] = min(load["push"], rest)
    if "new" in allowed:
        caps["new"] = admitted_new
    unused = m - sum(minutes.values())
    flowed: list[dict[str, Any]] = []
    # Step 4: unused minutes flow to maintenance overflow, then repair
    # overflow, then push, each up to its load; new only up to admitted.
    for lane in FLOW_ORDER:
        if unused <= _EPS or lane not in allowed:
            continue
        ceiling = admitted_new if lane == "new" else load[lane]
        room = max(ceiling - minutes[lane], 0.0)
        give = min(room, unused)
        if give > _EPS:
            minutes[lane] += give
            unused -= give
            flowed.append({"to": lane, "minutes": round(give, 4)})
    lanes = {
        lane: LaneSplit(
            lane=lane,
            minutes=minutes[lane],
            load=load[lane],
            cap=caps[lane],
            reason=_reason(lane, minutes[lane], load[lane], caps[lane], m, repair_max_share, maintain_max_share),
        )
        for lane in allowed
    }
    return Split(
        rule=SPLIT_RULE,
        budget=float(budget),
        requested_minutes=float(requested_minutes),
        m=m,
        lanes=lanes,
        flowed=tuple(flowed),
        lanes_allowed=allowed,
    )


def _reason(
    lane: str,
    minutes: float,
    load: float,
    cap: float | None,
    m: float,
    repair_share: float,
    maintain_share: float,
) -> str:
    if lane == "new":
        if (cap or 0.0) <= 0.01:
            return "new: no new material admitted today"
        return f"new: about {cap or 0:.0f} min of new material admitted for today's review load"
    if load <= 0.01:
        return {
            "repair": "repair: nothing to repair today",
            "maintain": "maintain: no reviews due",
            "push": "push: nothing toward a goal waiting",
        }[lane]
    load_text = f"about {load:.0f} min of work"
    if lane == "repair":
        return f"repair: {load_text}; capped at {round(repair_share * 100)}% of today ({cap or 0:.0f} min)"
    if lane == "maintain":
        return (
            f"maintain: {load_text} due; capped at {round(maintain_share * 100)}% of today "
            f"({cap or 0:.0f} min) so reviews never take the whole day"
        )
    return f"push: {load_text} toward your goals that is not due yet"


@dataclass
class LaneLedger:
    """The container's lane accounting at one block boundary (§6.8 rule 1)."""

    allotment: dict[str, float]
    spent: dict[str, float] = field(default_factory=dict)

    def left(self, lane: str) -> float:
        return max(self.allotment.get(lane, 0.0) - self.spent.get(lane, 0.0), 0.0)

    def lefts(self, lanes: Sequence[str] = LANES) -> dict[str, float]:
        return {lane: self.left(lane) for lane in lanes}


def redistribute(
    lane_left: Mapping[str, float],
    *,
    has_candidate: Callable[[str, float], bool],
    new_room: float,
    lanes_allowed: Sequence[str] = LANES,
) -> tuple[dict[str, float], list[dict[str, Any]]]:
    """§6.8 rule 1: released lane minutes flow on before every choice.

    A lane releases its remaining minutes when it has no candidate under them:
    it has no candidates left, or even its smallest remaining candidate is
    larger than its remaining minutes. The released minutes are pooled and flow
    in §6.2 step 4's order (maintain, repair, push, then new) to the first lane
    that has a candidate under its own minutes plus the pool;
    ``has_candidate(lane, minutes)`` asks the source. New receives at most
    ``new_room`` (its admitted new-material minutes not yet allotted). Minutes
    no lane can use stay unallotted (recorded with ``to = None``). Returns the
    new lane minutes and the release records.
    """

    left = {lane: max(float(lane_left.get(lane, 0.0)), 0.0) for lane in LANES}
    allowed = [lane for lane in LANES if lane in set(lanes_allowed)]
    releases: list[dict[str, Any]] = []
    released = 0.0
    own_released: dict[str, float] = {}
    for lane in allowed:
        if left[lane] <= _EPS:
            continue
        if not has_candidate(lane, left[lane]):
            released += left[lane]
            own_released[lane] = left[lane]
            releases.append({"from": lane, "minutes": round(left[lane], 4)})
            left[lane] = 0.0
    if released <= _EPS:
        return left, releases
    # New may take back what it released itself, plus its admitted room.
    room_new = max(float(new_room), 0.0) + own_released.get("new", 0.0)
    chosen: str | None = None
    give = 0.0
    for lane in FLOW_ORDER:
        if lane not in allowed:
            continue
        offer = min(released, room_new) if lane == "new" else released
        if offer <= _EPS:
            continue
        if has_candidate(lane, left[lane] + offer):
            chosen, give = lane, offer
            break
    for record in releases:
        record["to"] = chosen
    if chosen is None:
        return left, releases
    left[chosen] += give
    if give + _EPS < released:
        releases.append(
            {"from": "pool", "minutes": round(released - give, 4), "to": None,
             "why": "new never receives more than its admitted minutes"}
        )
    return left, releases


__all__ = [
    "LaneLedger",
    "LaneSplit",
    "SPLIT_RULE",
    "Split",
    "display_lane_minutes",
    "redistribute",
    "split_line",
    "split_v1",
]
