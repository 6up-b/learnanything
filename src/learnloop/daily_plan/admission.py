"""New-material pace (``spec_daily_loop_v1.md`` §6.3, Q11).

Load-based admission with a hard cap and a floor:

- **Review load.** L = the projected mean daily review minutes over the next
  H = ``plan.load_horizon_days`` days: the estimate of every item with memory
  state whose (effective) due date falls in the horizon, times
  ``ceil(H / interval)`` reviews, divided by H.
- **Cost of a new item:** est x (1 + ``plan.new_item_reviews_14d``) / H a day.
- **Admission.** New items are admitted in Phase 6's order (the scheduler's
  order) while L + the admitted cost stays <= ``plan.load_ceiling`` x M; at
  most ``plan.max_new_items_per_day`` a day across the day's plans; at least
  ``plan.min_new_items_per_day`` when new material exists and the plan is not
  re-entry. DL1 has no intent, so every item is uncommitted (DL2 orders Learn
  and Master first and admits none from Keep and Light touch).
- **Exempt (L3):** learner requests take the first new-lane slots, outside the
  ceiling and the cap. Scheduled checks are not new material at all.
- **"More new material"** bypasses the ceiling and the cap once (labelled).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime
from math import ceil
from typing import Any

from learnloop.clock import parse_utc

ADMISSION_RULE = "load_admission_v1"


@dataclass(frozen=True)
class NewCandidate:
    practice_item_id: str
    est_minutes: float
    requested: bool = False


@dataclass(frozen=True)
class Admission:
    rule: str
    enabled: bool
    override: str | None
    review_load_per_day: float
    ceiling_minutes: float
    horizon_days: int
    reviews_per_new_item: int
    cap_per_day: int
    planned_today: int
    floor_per_day: int
    admitted: tuple[NewCandidate, ...] = ()
    exempt: tuple[NewCandidate, ...] = ()
    floor_applied: bool = False
    stopped_by: str | None = None
    added_load_per_day: float = 0.0
    #: What the ceiling is 0.80 of: the plan's own minutes M, or, for a "keep
    #: going" extension and the plan after re-entry, the day's remembered
    #: budget (review F9; L is a daily load, so it is held to the daily budget).
    ceiling_basis: str = "plan_minutes"

    @property
    def admitted_ids(self) -> tuple[str, ...]:
        return tuple(c.practice_item_id for c in (*self.exempt, *self.admitted))

    @property
    def admitted_minutes(self) -> float:
        return sum(c.est_minutes for c in (*self.exempt, *self.admitted))

    def as_dict(self) -> dict[str, Any]:
        return {
            "rule": self.rule,
            "enabled": self.enabled,
            "override": self.override,
            "review_load_per_day": round(self.review_load_per_day, 4),
            "ceiling_minutes": round(self.ceiling_minutes, 4),
            "ceiling_basis": self.ceiling_basis,
            "horizon_days": self.horizon_days,
            "reviews_per_new_item": self.reviews_per_new_item,
            "cap_per_day": self.cap_per_day,
            "planned_today": self.planned_today,
            "floor_per_day": self.floor_per_day,
            "floor_applied": self.floor_applied,
            "stopped_by": self.stopped_by,
            "added_load_per_day": round(self.added_load_per_day, 4),
            "admitted": [
                {"practice_item_id": c.practice_item_id, "est_minutes": round(c.est_minutes, 4)}
                for c in self.admitted
            ],
            "exempt_requests": [
                {"practice_item_id": c.practice_item_id, "est_minutes": round(c.est_minutes, 4)}
                for c in self.exempt
            ],
            "admitted_minutes": round(self.admitted_minutes, 4),
        }


@dataclass(frozen=True)
class ReviewItem:
    """One item with memory state, for the review-load projection."""

    practice_item_id: str
    due_at: str | None
    last_review_at: str | None
    est_minutes: float


def projected_review_load(
    items: Sequence[ReviewItem], *, now: datetime, horizon_days: int
) -> float:
    """L: mean daily review minutes over the horizon (§6.3).

    Each item whose due date falls before ``now + H`` counts ``ceil(H /
    interval)`` reviews, where its interval is the gap between the review that
    set its due date and that due date (at least one day). Items without a due
    date carry no review load. Display and admission only; never persisted
    state.
    """

    horizon = max(int(horizon_days), 1)
    total = 0.0
    for item in items:
        due = parse_utc(item.due_at)
        if due is None:
            continue
        if (due - now).total_seconds() > horizon * 86400:
            continue
        last = parse_utc(item.last_review_at)
        interval_days = 1.0
        if last is not None:
            interval_days = max((due - last).total_seconds() / 86400.0, 1.0)
        reviews = ceil(horizon / interval_days)
        total += item.est_minutes * reviews
    return total / horizon


def new_item_daily_cost(est_minutes: float, *, reviews: int, horizon_days: int) -> float:
    return float(est_minutes) * (1 + int(reviews)) / max(int(horizon_days), 1)


def admit_new_material(
    candidates: Sequence[NewCandidate],
    *,
    review_load_per_day: float,
    m: float,
    load_ceiling: float,
    horizon_days: int,
    reviews_per_new_item: int,
    cap_per_day: int,
    floor_per_day: int,
    planned_today: int,
    enabled: bool = True,
    reentry: bool = False,
    override: str | None = None,
    ceiling_basis: str = "plan_minutes",
) -> Admission:
    """Admit new material for one plan (or one "more new material" extension).

    ``candidates`` are never-attempted new-lane items in the scheduler's order
    (Phase 6's order). Requested ones are exempt and come first. ``override``
    ("more_new") bypasses the ceiling and the cap once.
    """

    ceiling = float(load_ceiling) * max(float(m), 0.0)
    exempt = tuple(c for c in candidates if c.requested)
    ordinary = [c for c in candidates if not c.requested]
    admitted: list[NewCandidate] = []
    floor_applied = False
    stopped_by: str | None = None
    added = 0.0
    if reentry:
        stopped_by = "reentry"
    elif not enabled:
        stopped_by = "admission_disabled"
    else:
        cap_left = max(int(cap_per_day) - int(planned_today), 0)
        load = float(review_load_per_day)
        for candidate in ordinary:
            cost = new_item_daily_cost(candidate.est_minutes, reviews=reviews_per_new_item, horizon_days=horizon_days)
            if override is None:
                if len(admitted) >= cap_left:
                    stopped_by = "daily_cap"
                    break
                if load + added + cost > ceiling + 1e-9:
                    stopped_by = "load_ceiling"
                    break
            admitted.append(candidate)
            added += cost
        if (
            override is None
            and not admitted
            and ordinary
            and int(planned_today) < int(floor_per_day)
            and cap_left > 0
        ):
            # The floor: at least one new item a day when new material exists.
            first = ordinary[0]
            admitted.append(first)
            added += new_item_daily_cost(first.est_minutes, reviews=reviews_per_new_item, horizon_days=horizon_days)
            floor_applied = True
    return Admission(
        rule=ADMISSION_RULE,
        enabled=bool(enabled),
        override=override,
        review_load_per_day=float(review_load_per_day),
        ceiling_minutes=ceiling,
        horizon_days=int(horizon_days),
        reviews_per_new_item=int(reviews_per_new_item),
        cap_per_day=int(cap_per_day),
        planned_today=int(planned_today),
        floor_per_day=int(floor_per_day),
        admitted=tuple(admitted),
        exempt=exempt,
        floor_applied=floor_applied,
        stopped_by=stopped_by,
        added_load_per_day=added,
        ceiling_basis=ceiling_basis,
    )


def more_new_tradeoff(
    candidates: Sequence[NewCandidate], *, reviews_per_new_item: int, horizon_days: int
) -> float:
    """"adds about N min/day of reviews for two weeks" (§6.3)."""

    return sum(
        new_item_daily_cost(c.est_minutes, reviews=reviews_per_new_item, horizon_days=horizon_days)
        for c in candidates
    )


@dataclass(frozen=True)
class AdmissionContext:
    """What the engine hands the admission (kept for the plan's receipt)."""

    review_items: tuple[ReviewItem, ...] = ()
    extra: Mapping[str, Any] = field(default_factory=dict)


__all__ = [
    "ADMISSION_RULE",
    "Admission",
    "AdmissionContext",
    "NewCandidate",
    "ReviewItem",
    "admit_new_material",
    "more_new_tradeoff",
    "new_item_daily_cost",
    "projected_review_load",
]
