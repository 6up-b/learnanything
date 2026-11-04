"""What a schedule change does to serving: the upgrade's report (router objective RO1, spec §5.5).

A shadow rebuild (``learnloop.substrate.shadow_rebuild``) replays a copy under a candidate config and
returns its schedule projections before and after; with :func:`serving_schedule` as its observer it
also returns what serving reads of each side at an instant. :func:`schedule_effects` reports how many
stored due dates moved and by how much, and, from serving's own reads, the queue due at that instant
and admission's projected review load (``learnloop.daily_plan.admission.projected_review_load``).
``learnloop rebuild --shadow`` adds it to its JSON. Report only: nothing serving reads it.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from statistics import median
from typing import Any

from learnloop.clock import parse_utc
from learnloop.daily_plan.admission import ReviewItem, projected_review_load


#: Each schedule projection's fallback anchor: the stored column a review writes. An item's interval
#: runs from the review that set its due date (:attr:`ServingSchedule.anchors`), which a primed retry
#: or a held grade does not move; ``last_attempt_at`` is only the fallback for an item with no such
#: review (imported state), as ``IntentServing.last_review_at`` reads it.
_SCHEDULE_ANCHORS = {"practice_item_state": "last_attempt_at", "activity_card_state": "last_eligible_review_at"}


@dataclass(frozen=True, slots=True)
class ServingSchedule:
    """What serving reads of the item schedule at one instant (codex review F2, F3).

    ``population``: admission's review-load population (``engine.review_population``, with the
    build's own intent view): active, servable items in an intent that is not excluded, each at its
    effective due and from the review its interval runs from, at one minute each. ``anchors``: per
    item, the latest review that wrote its schedule (FSRS-eligible and not held for review; the
    recall-target anchor, ``scheduling.intent.recall_targets.load_anchors``).
    """

    population: Mapping[str, ReviewItem]
    anchors: Mapping[str, str]


def serving_schedule(vault: Any, repository: Any, *, as_of: datetime) -> ServingSchedule:
    """Serving's read of ``repository``'s schedule at ``as_of`` (a shadow rebuild's observer)."""

    from learnloop.daily_plan.engine import review_population
    from learnloop.scheduling.intent.recall_targets import load_anchors
    from learnloop.scheduling.intent.serving import intent_serving

    intent = intent_serving(vault, repository, now=as_of)
    population = review_population(vault, repository, intent, minutes=lambda _item_id: 1.0)
    with repository.connection() as connection:
        anchors = {item_id: anchor for item_id, (anchor, _attempt_id) in load_anchors(connection).items()}
    return ServingSchedule(population={item.practice_item_id: item for item in population}, anchors=anchors)


def _days(later: datetime, earlier: datetime) -> float:
    return (later - earlier).total_seconds() / 86400.0


def _spread(values: Sequence[float]) -> dict[str, float] | None:
    if not values:
        return None
    return {"min": round(min(values), 4), "median": round(float(median(values)), 4), "max": round(max(values), 4)}


def _queue_due(before: ServingSchedule, after: ServingSchedule, as_of: datetime) -> dict[str, int]:
    def due(view: ServingSchedule) -> set[str]:
        out = set()
        for item_id, item in view.population.items():
            at = parse_utc(item.due_at)
            if at is not None and at <= as_of:
                out.add(item_id)
        return out

    was, now = due(before), due(after)
    return {"before": len(was), "after": len(now), "newly_due": len(now - was), "no_longer_due": len(was - now)}


def schedule_effects(
    before: Mapping[tuple[Any, ...], Mapping[str, Any]],
    after: Mapping[tuple[Any, ...], Mapping[str, Any]],
    *,
    as_of: datetime,
    horizon_days: int,
    serving_before: ServingSchedule,
    serving_after: ServingSchedule,
) -> dict[str, Any]:
    """What a schedule change does to serving, from the two schedule snapshots and serving's reads.

    Per projection (items and activity cards): how many stored due dates moved, by how many days, and
    the ratio of the new interval to the old, both from the review that set the due date. For items,
    from serving's own reads of each side (``serving_before``, ``serving_after``): the queue due at
    ``as_of`` before and after, with the rows newly due and no longer due, and admission's projected
    review load (the plan's own horizon) in reviews per day. The plan multiplies each review by the
    item's estimated minutes, so the minutes follow the same ratio item by item; this reads no
    estimator. No serving surface reads an activity card's due date, so cards report no queue.
    """

    report: dict[str, Any] = {"as_of": as_of.isoformat().replace("+00:00", "Z"), "horizon_days": horizon_days}
    for projection, anchor_column in _SCHEDULE_ANCHORS.items():
        rows = sorted({key for key in set(before) | set(after) if key[0] == projection}, key=repr)
        shifts: list[float] = []
        ratios: list[float] = []
        moved = 0
        for key in rows:
            old, new = before.get(key) or {}, after.get(key) or {}
            old_due, new_due = parse_utc(old.get("due_at")), parse_utc(new.get("due_at"))
            if old_due is None or new_due is None or old_due == new_due:
                continue
            moved += 1
            shifts.append(_days(new_due, old_due))
            anchor_at = None
            if projection == "practice_item_state":
                item_id = str(key[1])
                anchor_at = serving_after.anchors.get(item_id) or serving_before.anchors.get(item_id)
            anchor = parse_utc(anchor_at or new.get(anchor_column) or old.get(anchor_column))
            if anchor is not None and old_due > anchor:
                ratios.append(_days(new_due, anchor) / _days(old_due, anchor))
        entry: dict[str, Any] = {
            "rows": len(rows),
            "due_dates_moved": moved,
            "shift_days": _spread(shifts),
            "interval_ratio": _spread(ratios),
            "earlier": sum(1 for value in shifts if value < 0),
            "later": sum(1 for value in shifts if value > 0),
        }
        if projection == "practice_item_state":
            entry["queue_due"] = _queue_due(serving_before, serving_after, as_of)
            entry["review_load_per_day"] = {
                "before": round(projected_review_load(list(serving_before.population.values()), now=as_of,
                                                      horizon_days=horizon_days), 4),
                "after": round(projected_review_load(list(serving_after.population.values()), now=as_of,
                                                     horizon_days=horizon_days), 4),
            }
        report[projection] = entry
    return report


__all__ = ["ServingSchedule", "schedule_effects", "serving_schedule"]
