"""The plan's verdicts on adaptive difficulty's slot, and its re-check of AD's choice (the final round).

Incumbent code (it imports nothing from ``learnloop.adaptive_difficulty`` or ``daily_plan.ad_slot``).
The plan computes these itself, in the serve transaction and OUTSIDE any AD operation, with no AD
frame on the stack, exactly as it would with AD off (owner decision 2026-10-24, the inversion):

* phase 2, :func:`for_slot` / :func:`for_deferrals`: the plan's admitted pool at this boundary
  (``engine.admitted_new_material_ids``, classified with the item states AD's view reads: fix round
  12's rule and round 2's A8 result), the staged frame's admission and the pool's per-item predicate
  for the members, the routine exclusions, and the plan's numbers for AD's checks 2-4; returned as a
  :class:`~learnloop.daily_plan.slot_facts_schema.SlotFacts` record of ids, codes and numbers;
* phase 4, :func:`accept` / :func:`accept_cleared`: the plan re-checks AD's choice against those
  facts before it serves; a choice it would not admit raises :class:`ChoiceRejected`, the caller
  rolls back AD's row and serves the planned item.

The caller (``engine``) catches every exception from here and logs only its type and a code.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import replace
from typing import Any

from learnloop.daily_plan.lanes import PoolItem
from learnloop.daily_plan.slot_facts_schema import EXCLUSION_NAMES, SlotFacts, SlotInputs
from learnloop.daily_plan.types import BLOCK_MAX_MINUTES

#: The engine's log code when phase 2 fails (owner Q3: the type and this code at the default level).
FACTS_FAILED = "incumbent_facts_failed"
#: The engine's log code when phase 4 rejects AD's choice.
CHOICE_REJECTED = "ad_choice_rejected"


class ChoiceRejected(RuntimeError):
    """AD's choice is not one the plan admits now (phase 4): roll back and serve the planned item."""


def _pool_item(item_id: str, learning_object_id: str, est_minutes: float, existing: PoolItem | None) -> PoolItem:
    if existing is not None:
        return replace(existing, lane=existing.lane or "new")
    return PoolItem(practice_item_id=item_id, learning_object_id=learning_object_id, rank=10**6, priority=0.0,
                    lane="new", reason="an AD candidate", est_minutes=float(est_minutes), never_attempted=True)


def _verdicts(env: Any, record: Any, built: Any, inputs: SlotInputs, *, slot_item_id: str | None,
              released: Iterable[str]) -> dict[str, Any]:
    from learnloop.attempts.attempts import COLD_FOLLOWUP_TASK_KINDS
    from learnloop.daily_plan.engine import admitted_new_material_ids
    from learnloop.daily_plan.policy import router_active
    from learnloop.daily_plan.staged_frame import StagedFrame
    from learnloop.diagnosis.remediation import COLD_RETRIEVAL_DELAY
    from learnloop.scheduling.scheduler import pool_admission
    from learnloop.scheduling.serving_exclusions import out_of_timing_serving_exclusions

    states = dict(inputs.item_states)
    exclusions = out_of_timing_serving_exclusions(
        env.vault, env.repository, cold_followup_kinds=COLD_FOLLOWUP_TASK_KINDS, reveal_window=COLD_RETRIEVAL_DELAY,
        clock=env.clock, exclude_reveal_ids=frozenset(inputs.withheld_reveal_ids))
    unclaimed = (slot_item_id,) if slot_item_id is not None else ()
    admitted = admitted_new_material_ids(env, record, scheduled=built.scheduled, item_states=states,
                                         released=released, unclaimed=unclaimed)
    members = [item_id for item_id in inputs.candidate_ids if item_id in admitted]
    pool = {item.practice_item_id: item for item in built.pool}
    candidates = [_pool_item(item_id, str(inputs.learning_objects.get(item_id) or ""),
                             float(inputs.est_minutes.get(item_id, 0.0)), pool.get(item_id)) for item_id in members]
    material = StagedFrame(env.vault, env.repository, clock=env.clock, item_states=lambda: states).material(candidates)
    refuse = pool_admission(env.vault, env.repository, now=env.now(), item_states=states)
    staged = router_active(env.vault)
    refusals: dict[str, tuple[str, ...]] = {}
    for item_id in members:
        codes = []
        if staged:
            for reason in material.refusals.get(item_id, ()):
                key = reason.get("constraint_key") or reason.get("constraint") or reason.get("key") or "refused"
                codes.append(f"constraint:{key}")
        pooled = refuse(item_id)
        if pooled is not None:
            codes.append(f"pool:{pooled}")
        refusals[item_id] = tuple(codes)
    cold = material.cold_items
    return {
        "admitted": admitted,
        "members": tuple(members),
        "refusals": refusals,
        "cold_items": None if cold is None else tuple(sorted(str(i) for i in cold)),
        "reserved_items": tuple(sorted(str(i) for i in material.reserved_items)),
        "exclusions": {name: tuple(sorted(str(i) for i in getattr(exclusions, name))) for name in EXCLUSION_NAMES},
    }


def for_slot(env: Any, record: Any, block: Any, slot: Any, built: Any, day: Sequence[Any],
             inputs: SlotInputs) -> SlotFacts:
    """Phase 2 for one new-material slot."""

    slot_item_id = str(slot.practice_item_id)
    verdicts = _verdicts(env, record, built, inputs, slot_item_id=slot_item_id, released=())
    # Check 2's input: planned in any of today's plans (the slot item: in no slot but its own).
    planned: dict[str, int] = {}
    for plan in [record, *[p for p in day if p.id != record.id]]:
        for planned_item in plan.items():
            if not planned_item.displaced:
                planned[planned_item.practice_item_id] = planned.get(planned_item.practice_item_id, 0) + 1
    planned_counts = {item_id: planned.get(item_id, 0) - (1 if item_id == slot_item_id else 0)
                      for item_id in verdicts["members"]}
    # Checks 3 and 4's inputs: the block's slack and the plan's admission.
    lefts = record.lane_left()
    slack = max(0.0, min(BLOCK_MAX_MINUTES - block.est_minutes(), record.minutes_left(), lefts.get("new", 0.0)))
    admission = record.admission
    budget = {
        "slack_minutes": float(slack),
        "horizon_days": int(admission.get("horizon_days") or 14),
        "reviews_per_new_item": int(admission.get("reviews_per_new_item") or 3),
        "ceiling_minutes": float(admission.get("ceiling_minutes") or 0.0),
        "load_per_day": float(admission.get("review_load_per_day") or 0.0)
        + float(admission.get("added_load_per_day") or 0.0),
        "floor_or_override": bool(admission.get("floor_applied")) or admission.get("override") is not None,
    }
    propensity = (block.chosen or {}).get("propensity")
    return SlotFacts(
        kind="slot", now=env.now_iso(), plan_id=str(record.id), members=verdicts["members"],
        refusals=verdicts["refusals"], cold_items=verdicts["cold_items"], reserved_items=verdicts["reserved_items"],
        exclusions=verdicts["exclusions"], slot_admitted=slot_item_id in verdicts["admitted"],
        block_id=str(block.id), position=int(slot.position), slot_item_id=slot_item_id,
        slot_learning_object_id=str(slot.learning_object_id), slot_est_minutes=float(slot.est_minutes),
        planned_counts=planned_counts, budget=budget,
        router_decision_id=None if block.decision_ref is None else str(block.decision_ref),
        router_propensity=float(propensity) if propensity is not None else 1.0,
    )


def for_deferrals(env: Any, record: Any, built: Any, inputs: SlotInputs, deferrals: Iterable[str]) -> SlotFacts:
    """Phase 2 for the boundary's AD deferrals (each judged were it released)."""

    verdicts = _verdicts(env, record, built, inputs, slot_item_id=None, released=tuple(deferrals))
    return SlotFacts(
        kind="deferrals", now=env.now_iso(), plan_id=str(record.id), members=verdicts["members"],
        refusals=verdicts["refusals"], cold_items=verdicts["cold_items"], reserved_items=verdicts["reserved_items"],
        exclusions=verdicts["exclusions"],
    )


def _admissible(facts: SlotFacts, item_id: str) -> bool:
    return (item_id in facts.members and not facts.refusals.get(item_id)
            and facts.cold_items is not None and item_id not in facts.cold_items
            and item_id not in facts.reserved_items
            and not any(item_id in facts.exclusions.get(name, ()) for name in EXCLUSION_NAMES))


def accept(facts: SlotFacts, action: str, chosen_item_id: str | None) -> None:
    """Phase 4: AD's slot decision re-checked by the plan. A substitute must be a member with no
    refusal, held by no cold check or reserved surface, outside the routine exclusions and planned
    nowhere else; serving or displacing the slot item is the plan's own slot."""

    if action != "substitute":
        return
    item_id = str(chosen_item_id or "")
    if item_id == facts.slot_item_id or not _admissible(facts, item_id) or facts.planned_counts.get(item_id, 0) > 0:
        raise ChoiceRejected(CHOICE_REJECTED)


def accept_cleared(facts: SlotFacts, cleared: Iterable[str]) -> list[str]:
    """Phase 4 for deferrals: every cleared item must be a member with no refusal (else none is)."""

    out = sorted({str(item_id) for item_id in cleared})
    if any(not _admissible(facts, item_id) for item_id in out):
        raise ChoiceRejected(CHOICE_REJECTED)
    return out


__all__ = ["CHOICE_REJECTED", "ChoiceRejected", "FACTS_FAILED", "accept", "accept_cleared", "for_deferrals",
           "for_slot"]
