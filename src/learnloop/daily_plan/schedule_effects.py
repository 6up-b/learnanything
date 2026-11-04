"""What a schedule change does to serving: the upgrade's report (router objective RO1, spec §5.5).

A shadow rebuild (``learnloop.substrate.shadow_rebuild``) replays a copy under a candidate config and
returns its schedule projections before and after; :func:`schedule_effects` reads them as serving does:
how many stored due dates moved and by how much, the queue due at an instant, and admission's projected
review load (``learnloop.daily_plan.admission.projected_review_load``). ``learnloop rebuild --shadow``
adds it to its JSON. Report only: nothing serving reads it.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime
from statistics import median
from typing import Any

from learnloop.clock import parse_utc
from learnloop.daily_plan.admission import ReviewItem, projected_review_load


#: Each schedule projection's anchor: the review that set its due date.
_SCHEDULE_ANCHORS = {"practice_item_state": "last_attempt_at", "activity_card_state": "last_eligible_review_at"}


def _days(later: datetime, earlier: datetime) -> float:
    return (later - earlier).total_seconds() / 86400.0


def _spread(values: Sequence[float]) -> dict[str, float] | None:
    if not values:
        return None
    return {"min": round(min(values), 4), "median": round(float(median(values)), 4), "max": round(max(values), 4)}


def schedule_effects(
    before: Mapping[tuple[Any, ...], Mapping[str, Any]],
    after: Mapping[tuple[Any, ...], Mapping[str, Any]],
    *,
    as_of: datetime,
    horizon_days: int,
) -> dict[str, Any]:
    """What a schedule change does to serving, from the two schedule snapshots.

    Per projection (items and activity cards): how many stored due dates moved, by how many days, and
    the ratio of the new interval to the old (both from the review that set the due date); the queue due
    at ``as_of`` before and after, with the rows newly due and no longer due; and, for items, admission's
    projected review load (``daily_plan.admission.projected_review_load``, the plan's own horizon) in
    reviews per day. The plan multiplies each review by the item's estimated minutes, so the minutes
    follow the same ratio item by item; this reads no estimator.
    """

    report: dict[str, Any] = {"as_of": as_of.isoformat().replace("+00:00", "Z"), "horizon_days": horizon_days}
    for projection, anchor_column in _SCHEDULE_ANCHORS.items():
        rows = sorted({key for key in set(before) | set(after) if key[0] == projection}, key=repr)
        shifts: list[float] = []
        ratios: list[float] = []
        moved = 0
        due_before = due_after = newly_due = no_longer_due = 0
        items_before: list[ReviewItem] = []
        items_after: list[ReviewItem] = []
        for key in rows:
            old, new = before.get(key) or {}, after.get(key) or {}
            old_due, new_due = parse_utc(old.get("due_at")), parse_utc(new.get("due_at"))
            was_due = old_due is not None and old_due <= as_of
            is_due = new_due is not None and new_due <= as_of
            due_before += was_due
            due_after += is_due
            newly_due += is_due and not was_due
            no_longer_due += was_due and not is_due
            if projection == "practice_item_state":
                identity = str(key[1:])
                items_before.append(ReviewItem(identity, old.get("due_at"), old.get(anchor_column), 1.0))
                items_after.append(ReviewItem(identity, new.get("due_at"), new.get(anchor_column), 1.0))
            if old_due is None or new_due is None or old_due == new_due:
                continue
            moved += 1
            shifts.append(_days(new_due, old_due))
            anchor = parse_utc(new.get(anchor_column) or old.get(anchor_column))
            if anchor is not None and old_due > anchor:
                ratios.append(_days(new_due, anchor) / _days(old_due, anchor))
        entry: dict[str, Any] = {
            "rows": len(rows),
            "due_dates_moved": moved,
            "shift_days": _spread(shifts),
            "interval_ratio": _spread(ratios),
            "earlier": sum(1 for value in shifts if value < 0),
            "later": sum(1 for value in shifts if value > 0),
            "queue_due": {"before": due_before, "after": due_after, "newly_due": newly_due,
                          "no_longer_due": no_longer_due},
        }
        if projection == "practice_item_state":
            entry["review_load_per_day"] = {
                "before": round(projected_review_load(items_before, now=as_of, horizon_days=horizon_days), 4),
                "after": round(projected_review_load(items_after, now=as_of, horizon_days=horizon_days), 4),
            }
        report[projection] = entry
    return report


__all__ = ["schedule_effects"]
