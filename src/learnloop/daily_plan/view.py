"""The plan DTO (``spec_daily_loop_v1.md`` §6.7, G3).

Every count and minute figure Start, Today, the done screen and the re-entry
panel show is read from this payload: the split line, each lane's minutes,
block estimates ("about"), the items done and the minutes taken. The upcoming
blocks after the current one are a projection, labelled as such: "Block 2 of
about 3". It runs the policy's source with its deterministic projection
chooser (``lane_quota_v1`` by default), forward and without logging; the live
chooser (router R2's sampled or model-backed mixture) is never called from a
read (review F3).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from learnloop.clock import parse_utc
from learnloop.daily_plan.engine import (
    PlanEnv,
    PlanPolicy,
    PoolContext,
    day_records,
    simulate_blocks,
)
from learnloop.daily_plan.records import (
    PlanRecord,
    PlannedBlock,
    PlannedItem,
)
from learnloop.daily_plan.split import display_lane_minutes, split_line
from learnloop.daily_plan.types import LANES

MAX_PROJECTED_BLOCKS = 12


def project_blocks(
    record: PlanRecord, context: PoolContext | None, policy: PlanPolicy, *, max_blocks: int = MAX_PROJECTED_BLOCKS
) -> list[dict[str, Any]]:
    """The blocks after the chosen ones, if nothing changes: a projection only.

    Always with ``policy.projection()``: the policy's deterministic projection
    chooser, never its live chooser (review F3).
    """

    if context is None or not record.is_open:
        return []
    return [
        {
            "ordinal": block.ordinal,
            "lane": block.lane,
            "est_minutes": round(block.est_minutes(), 4),
            "item_count": len(block.items),
            "learning_object_titles": [
                context.titles.get(lo, lo) for lo in dict.fromkeys(item.learning_object_id for item in block.items)
            ],
            "reading_title": (block.reading or {}).get("section_title") if block.reading else None,
            "why": decision.choice.why,
        }
        for decision, block in simulate_blocks(record, context, policy, max_blocks=max_blocks)
    ]


def _item_row(env: PlanEnv, item: PlannedItem) -> dict[str, Any]:
    vault = env.vault
    learning_object = vault.learning_objects.get(item.learning_object_id)
    practice_item = vault.practice_items.get(item.practice_item_id)
    prompt = str(getattr(practice_item, "prompt", "") or "")
    return {
        "practice_item_id": item.practice_item_id,
        "learning_object_id": item.learning_object_id,
        "learning_object_title": learning_object.title if learning_object is not None else item.learning_object_id,
        "practice_mode": getattr(practice_item, "practice_mode", None),
        "prompt_preview": prompt[:140],
        "lane": item.lane,
        "est_minutes": round(item.est_minutes, 4),
        "state": item.state,
        "origin": item.origin,
        "served_at": item.served_at,
        "done_at": item.done_at,
    }


def _block_row(env: PlanEnv, record: PlanRecord, block: PlannedBlock, current_id: str | None) -> dict[str, Any]:
    status = "done" if block.finished else ("current" if block.id == current_id else "upcoming")
    reading = dict(block.reading) if block.reading else None
    if reading is not None and block.reading_progress is not None:
        reading["spans_seen"], reading["span_count"] = block.reading_progress
    return {
        "id": block.id,
        "ordinal": block.ordinal,
        "lane": block.lane,
        "action": block.action,
        "subtype": block.subtype,
        "chosen_by": block.chosen_by,
        "why": str(block.chosen.get("why") or ""),
        "why_kind": block.chosen.get("why_kind"),
        "fallback": bool(block.chosen.get("fallback")),
        "est_minutes": round(block.est_minutes(), 4),
        "status": status,
        "started_at": block.started_at,
        "ended_at": block.ended_at,
        "outcome": block.outcome,
        "reading": reading,
        "learning_object_titles": [
            env.vault.learning_objects[lo].title if lo in env.vault.learning_objects else lo
            for lo in dict.fromkeys(item.learning_object_id for item in block.items if not item.displaced)
        ],
        "items": [_item_row(env, item) for item in block.items if not item.displaced],
        "displaced_count": sum(1 for item in block.items if item.displaced),
    }


def _actual_minutes(records: list[PlanRecord]) -> float:
    total_ms = 0
    for record in records:
        for block in record.blocks:
            if block.is_reading:
                started = parse_utc(block.started_at) if block.started_at else None
                ended = parse_utc(block.ended_at) if block.ended_at else None
                if started is not None and ended is not None and ended >= started:
                    total_ms += int((ended - started).total_seconds() * 1000)
                continue
            for item in block.items:
                if item.done and item.wall_ms is not None:
                    total_ms += int(item.wall_ms)
    return total_ms / 60000.0


def _totals(records: list[PlanRecord]) -> dict[str, Any]:
    items = [item for record in records for item in record.items()]
    reading_blocks = [block for record in records for block in record.blocks if block.is_reading]
    done = [item for item in items if item.done]
    return {
        "planned_minutes": round(sum(record.minutes_planned() for record in records), 4),
        "planned_items": sum(1 for item in items if not item.displaced),
        "done_items": len(done),
        "skipped_items": sum(1 for item in items if item.skipped and not item.done),
        "displaced_items": sum(1 for item in items if item.displaced),
        "reading_blocks": len(reading_blocks),
        "reading_blocks_ended": sum(1 for block in reading_blocks if block.ended_at is not None),
        "est_minutes_done": round(
            sum(item.est_minutes for item in done)
            + sum(block.est_minutes() for block in reading_blocks if block.ended_at is not None),
            4,
        ),
        "actual_minutes": round(_actual_minutes(records), 4),
    }


def _reentry_numbers(
    record: PlanRecord, panel: dict[str, Any] | None, projected: list[dict[str, Any]]
) -> dict[str, Any] | None:
    """"Today: a short re-entry, about 12 min, 7 items": the chosen blocks plus
    the projected ones, the same figures the plan view shows (G3)."""

    if panel is None:
        return None
    return {
        **panel,
        "plan_minutes": round(record.minutes_planned() + sum(row["est_minutes"] for row in projected), 4),
        "plan_items": record.item_count() + sum(int(row["item_count"]) for row in projected),
    }


def minute_choices(presets: list[int], remembered: int) -> list[int]:
    return sorted({*presets, int(remembered)})


def plan_view(
    env: PlanEnv,
    record: PlanRecord,
    *,
    context: PoolContext | None,
    next_step: dict[str, Any] | None,
    reentry_panel: dict[str, Any] | None = None,
    streak: dict[str, Any] | None = None,
) -> dict[str, Any]:
    split = record.split
    lanes = split.get("lanes") or {}
    allowed = [lane for lane in LANES if lane in (split.get("lanes_allowed") or LANES)]
    lane_minutes = {lane: float((lanes.get(lane) or {}).get("minutes", 0.0)) for lane in allowed}
    display = display_lane_minutes(lane_minutes)
    current = record.current_block()
    current_id = current.id if current is not None else None
    projected = project_blocks(record, context, env.policy)
    plan_blocks = [_block_row(env, record, block, current_id) for block in record.blocks]
    day = day_records(env)
    first = current if current is not None else (record.blocks[0] if record.blocks else None)
    first_row = None
    if first is not None:
        row = _block_row(env, record, first, current_id)
        first_row = {
            "title": (row["reading"] or {}).get("section_title") if row["reading"] else ", ".join(row["learning_object_titles"][:2]),
            "lane": row["lane"],
            "item_count": len(row["items"]),
            "est_minutes": row["est_minutes"],
            "reading": row["reading"] is not None,
        }
    admission = record.admission
    payload = {
        "id": record.id,
        "local_date": record.row["local_date"],
        "kind": record.kind,
        "status": record.status,
        "stop_reason": record.row.get("stop_reason"),
        "parent_plan_id": record.row.get("parent_plan_id"),
        "minutes_budget": round(record.budget, 4),
        "remembered_minutes": int(record.row["remembered_minutes"]),
        "minutes_source": record.row["minutes_source"],
        "minute_choices": minute_choices(list(env.plan_config.minutes_presets), int(record.row["remembered_minutes"])),
        "minutes_left": round(record.minutes_left(), 4),
        "split": {
            "rule": split.get("rule"),
            "line": split_line(record.budget, display),
            "lanes_allowed": allowed,
            "requested_minutes": round(float(split.get("requested_minutes") or 0.0), 4),
            "lanes": [
                {
                    "lane": lane,
                    "minutes": round(lane_minutes[lane], 4),
                    "display_minutes": display.get(lane, 0),
                    "load": (lanes.get(lane) or {}).get("load"),
                    "cap": (lanes.get(lane) or {}).get("cap"),
                    "reason": (lanes.get(lane) or {}).get("reason"),
                }
                for lane in allowed
            ],
        },
        "admission": {
            "admitted_count": len(admission.get("admitted") or []),
            "exempt_requests": len(admission.get("exempt_requests") or []),
            "stopped_by": admission.get("stopped_by"),
            "floor_applied": bool(admission.get("floor_applied")),
            "review_load_per_day": admission.get("review_load_per_day"),
            "ceiling_minutes": admission.get("ceiling_minutes"),
            "override": admission.get("override"),
        },
        "blocks": plan_blocks,
        "current_block_id": current_id,
        "projected": projected,
        "block_count_estimate": len(record.blocks) + len(projected),
        "first_block": first_row,
        "next_step": next_step,
        "totals": _totals([record]),
        "reentry": _reentry_numbers(record, reentry_panel, projected),
        "source": record.row.get("source"),
        "chooser": record.row.get("chooser"),
        "estimator_version": record.row.get("estimator_version"),
        "algorithm_version": record.row.get("algorithm_version"),
    }
    return {
        "enabled": True,
        "headline_enabled": bool(env.plan_config.headline),
        "local_date": env.today(),
        "plan": payload,
        "day": {
            "plans": len(day),
            "kinds": [r.kind for r in day],
            "complete": bool(day) and all(not r.is_open for r in day),
            **_totals(day),
        },
        "streak": streak,
    }


def disabled_view(vault: Any, *, reason: str) -> dict[str, Any]:
    return {
        "enabled": False,
        "reason": reason,
        "algorithm_version": vault.config.algorithms.algorithm_version,
        "plan": None,
    }


def now_payload(moment: datetime) -> str:
    return moment.isoformat()


__all__ = ["MAX_PROJECTED_BLOCKS", "disabled_view", "minute_choices", "plan_view", "project_blocks"]
