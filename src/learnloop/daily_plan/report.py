"""``learnloop plan show | report`` (``spec_daily_loop_v1.md`` §12, the DL1 checkpoint).

Read-only aggregates over the persisted plans: days active, plan starts and
completions, estimated vs actual minutes, the keep-going rate and the
open-to-first-item time. They answer Q0 at the owner's two-week checkpoint.
Never the streak as a success measure (intentions §15). No model calls.
"""

from __future__ import annotations

from collections import defaultdict
from statistics import median
from typing import Any

from learnloop.clock import parse_utc
from learnloop.daily_plan.records import PlanRecord


def _quantile(values: list[float], q: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = min(int(round(q * (len(ordered) - 1))), len(ordered) - 1)
    return ordered[index]


def plan_report(records: list[PlanRecord]) -> dict[str, Any]:
    by_day: dict[str, list[PlanRecord]] = defaultdict(list)
    for record in records:
        by_day[str(record.row["local_date"])].append(record)
    days_with_plans = sorted(by_day)
    active_days = sorted(
        day
        for day, plans in by_day.items()
        if any(item.done for plan in plans for item in plan.items())
        or any(block.is_reading and block.ended_at for plan in plans for block in plan.blocks)
    )
    started = [
        record
        for record in records
        if any(block.started_at for block in record.blocks)
    ]
    kinds = defaultdict(int)
    statuses = defaultdict(int)
    for record in records:
        kinds[record.kind] += 1
        statuses[record.status] += 1
    base_plans = [record for record in records if record.kind in ("normal", "reentry")]
    base_complete = [record for record in base_plans if record.status == "complete"]
    keep_going = [record for record in records if record.kind == "keep_going"]
    done_items = [item for record in records for item in record.items() if item.done]
    est_total = sum(item.est_minutes for item in done_items)
    timed = [item for item in done_items if item.wall_ms is not None]
    actual_total = sum(int(item.wall_ms or 0) for item in timed) / 60000.0
    est_timed = sum(item.est_minutes for item in timed)
    ratios = [
        (int(item.wall_ms or 0) / 60000.0) / item.est_minutes
        for item in timed
        if item.est_minutes > 0
    ]
    open_to_first: list[float] = []
    for day, plans in by_day.items():
        first_plan = min(plans, key=lambda record: str(record.row["created_at"]))
        opened = parse_utc(str(first_plan.row["created_at"]))
        served = [
            parse_utc(item.served_at)
            for plan in plans
            for item in plan.items()
            if item.served_at is not None
        ]
        served = [moment for moment in served if moment is not None]
        if opened is not None and served:
            open_to_first.append(max((min(served) - opened).total_seconds(), 0.0))
    stop_reasons = defaultdict(int)
    for record in records:
        if record.row.get("stop_reason"):
            stop_reasons[str(record.row["stop_reason"])] += 1
    chosen_by = defaultdict(int)
    fallbacks = 0
    stop_decisions = 0
    open_list_picks = 0
    for record in records:
        for block in record.blocks:
            chosen_by[block.chosen_by] += 1
            fallbacks += 1 if block.chosen.get("fallback") else 0
        for receipt in record.receipts:
            # Stop decisions are decisions too (§6.8 rule 6).
            fallbacks += 1 if receipt.chosen.get("fallback") else 0
        stop_decisions += len(record.stops())
        open_list_picks += len(record.receipts) - len(record.stops())
    return {
        "plans": len(records),
        "days_with_plans": len(days_with_plans),
        "days_active": len(active_days),
        "first_day": days_with_plans[0] if days_with_plans else None,
        "last_day": days_with_plans[-1] if days_with_plans else None,
        "plan_kinds": dict(kinds),
        "plan_statuses": dict(statuses),
        "plan_starts": len(started),
        "plan_completions": len(base_complete),
        "completion_rate": (len(base_complete) / len(base_plans)) if base_plans else None,
        "keep_going_plans": len(keep_going),
        "keep_going_rate": (len(keep_going) / len(base_complete)) if base_complete else None,
        "items_done": len(done_items),
        "estimated_minutes_done": round(est_total, 3),
        "timed_items": len(timed),
        "estimated_minutes_timed": round(est_timed, 3),
        "actual_minutes_timed": round(actual_total, 3),
        "actual_over_estimate_median": round(median(ratios), 4) if ratios else None,
        "open_to_first_item_seconds_median": round(median(open_to_first), 1) if open_to_first else None,
        "open_to_first_item_seconds_p90": round(_quantile(open_to_first, 0.9) or 0.0, 1) if open_to_first else None,
        "stop_reasons": dict(stop_reasons),
        "blocks_by_chooser": dict(chosen_by),
        "stop_decisions": stop_decisions,
        "open_list_picks_after_plan": open_list_picks,
        "chooser_fallbacks": fallbacks,
    }


def plan_show(record: PlanRecord, vault: Any) -> dict[str, Any]:
    """One persisted plan, as stored (no queue build, no projection)."""

    return {
        "id": record.id,
        "local_date": record.row["local_date"],
        "kind": record.kind,
        "status": record.status,
        "stop_reason": record.row.get("stop_reason"),
        "minutes_budget": record.budget,
        "remembered_minutes": record.row["remembered_minutes"],
        "minutes_source": record.row["minutes_source"],
        "minutes_planned": round(record.minutes_planned(), 4),
        "split_line": (record.split or {}).get("line"),
        "split": {lane: (row or {}).get("minutes") for lane, row in ((record.split or {}).get("lanes") or {}).items()},
        "admission": {
            key: (record.admission or {}).get(key)
            for key in ("rule", "review_load_per_day", "ceiling_minutes", "stopped_by", "floor_applied", "admitted_minutes")
        },
        "blocks": [
            {
                "ordinal": block.ordinal,
                "lane": block.lane,
                "chosen_by": block.chosen_by,
                "why": block.chosen.get("why"),
                "fallback": bool(block.chosen.get("fallback")),
                "est_minutes": round(block.est_minutes(), 4),
                "outcome": block.outcome,
                "reading": (block.reading or {}).get("section_title") if block.reading else None,
                "items": [
                    {
                        "practice_item_id": item.practice_item_id,
                        "learning_object": (
                            vault.learning_objects[item.learning_object_id].title
                            if item.learning_object_id in vault.learning_objects
                            else item.learning_object_id
                        ),
                        "est_minutes": round(item.est_minutes, 3),
                        "state": item.state,
                        "origin": item.origin,
                    }
                    for item in block.items
                ],
            }
            for block in record.blocks
        ],
        # Decisions that are not blocks, append-only (stops, picks after close).
        "receipts": [
            {
                "kind": receipt.action,
                "at": receipt.created_at,
                "chosen_by": receipt.chosen_by,
                "propensity": receipt.chosen.get("propensity"),
                "why": receipt.chosen.get("why"),
                "fallback": bool(receipt.chosen.get("fallback")),
                "practice_item_id": receipt.chosen.get("practice_item_id"),
            }
            for receipt in record.receipts
        ],
    }


__all__ = ["plan_report", "plan_show"]
