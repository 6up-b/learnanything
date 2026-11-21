"""Frozen pre-SR-3 placement oracle, from f44283f88e.

Only the placement algorithm is frozen; the same real stores and eligibility boundary
are exercised by both journeys. No network or model calls.
"""
from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import Any

from learnloop.router import mixture as mx
from learnloop.router_objective import assignments as A
from learnloop.router_objective.checks import (
    Eligible, Placement, VERSION, _first_session_today, administered, day_record, day_unit,
)


def legacy_place(vault: Any, repository: Any, *, local_date: str, session_id: str | None, pool: Sequence[Any],
          planned: Iterable[str], chooser_items: Sequence[Any], lane: str | None,
          eligible_items: Eligible) -> list[Placement]:
    """The slots this boundary administers (before its decision): the day's undelivered checks, in the day's first
    session only. ``chooser_items`` (none from the engine since Codex re-review F2) are never excluded.
    An item no longer eligible is redrawn among the topic's eligible items in the plan's pool (its own uniform);
    with none, the slot waits for the next block."""

    from dataclasses import replace as dc_replace

    with repository.connection() as connection:
        if not A.present(connection):
            return []
        day = day_record(connection, local_date)
        if day is None or not day.get("slots"):
            return []
        first = _first_session_today(connection, local_date)
        if session_id is not None and first is not None and session_id != first:
            return []
        if session_id is None and first is not None:
            return []
        done = administered(connection)
        slots = {row["unit_id"]: row for row in A.rows(connection, A.CHECK, unit_like=f"{day_unit(local_date)}:%")}
    by_id = {str(item.practice_item_id): item for item in pool}
    # Codex review F2: the reserved item is eligible whatever the chooser picked. The chooser's items are never
    # excluded here: had they been, a check whose drawn item the policy also chose would go unadministered, so the
    # assessment would depend on the action. A collision reclassifies that chooser slot as the check instead.
    taken = set(planned)
    chosen_ids = [str(item.practice_item_id) for item in chooser_items]
    placements: list[Placement] = []
    pending = [slots[key] for key in sorted(slots) if slots[key]["id"] not in done]
    if not pending:
        return []
    topics = [str(row["variant"]) for row in pending]
    still = {lo: list(items) for lo, items in eligible_items(sorted(set(topics)), taken).items()}
    for row in pending:
        slot = row["detail"]
        topic = str(row["variant"])
        candidates = [item for item in still.get(topic, []) if item in by_id]
        chosen, how = None, "drawn"
        if str(slot.get("item_id")) in candidates:
            chosen = str(slot["item_id"])
        elif candidates:
            u = mx.uniform(str(row["seed"]), f"redraw:{slot.get('slot')}:{len(done)}")
            chosen, how = candidates[min(int(u * len(candidates)), len(candidates) - 1)], "redrawn_in_pool"
        if chosen is None:
            continue
        item = by_id[chosen]
        if lane is not None and getattr(item, "lane", None) != lane:
            item = dc_replace(item, lane=lane)
        replaced, collision = None, chosen in chosen_ids
        if collision:
            # The policy's block holds the check's own item: that slot becomes the check (it is the question the
            # embedded check replaces; for a rate check, the check takes it rather than adding a second copy).
            replaced = chosen
        elif bool(slot.get("replaces", True)):
            # An embedded check replaces the block's last chooser item not already replaced or taken by a check
            # (it stays in the pool).
            already = {placement.replaced for placement in placements if placement.replaced}
            free = [item_id for item_id in chosen_ids if item_id not in already
                    and item_id not in {str(p.item.practice_item_id) for p in placements}
                    and item_id not in {str(r["detail"].get("item_id")) for r in pending}]
            if free:
                replaced = free[-1]
        placements.append(Placement(assignment_id=str(row["id"]), slot=slot, item=item, replaced=replaced,
                                    detail={"assignment_id": str(row["id"]), "slot": slot.get("slot"),
                                            "topic": topic, "r": slot.get("r"), "item_how": how,
                                            "replaced": replaced, "collision": collision, "version": VERSION}))
        still[topic] = [item_id for item_id in still.get(topic, []) if item_id != chosen]
    return placements

