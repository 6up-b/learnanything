"""The plan's side of AD's slot draw (spec_adaptive_difficulty_v1 §6.1, §10.2; AD2+AD3, switch ``selection``).

When a planned new-material slot comes up to be served, the plan builds the
draw's support here and hands it to ``adaptive_difficulty.serving.decide_slot``
in the serve transaction. AD never builds or reorders blocks (§10.1).

**The candidates**: the slot item and every other never-attempted item of the
slot item's LO at the slot item's capability. **The support** is the
candidates that pass every check, each re-read at the draw, never taken from
the block's admission (the slot item gets no exemption):

0. *still eligible*: in the cell pool now for some facet of the slot item
   (exam reservation, retirement, held-out derivation, pre-exposure, the depth
   envelope re-read); no serving block; outside the exclusions a selector
   outside the scheduler's timing honours (routine exclusions, an open cold
   follow-up's item, a reveal within the cold retrieval delay);
1. *the admission the slot item passed*: under the staged frame (router on)
   the constraint engine admits it on a fresh controller snapshot; with the
   router off, the predecessor's new-lane pool rule; and in both, reversible
   (no open cold check, no reserved assessment surface);
2. not planned in any of today's plans (the slot item: in no slot but its own);
3. fits the block: ``est(i) <= est(slot) + slack``, ``slack = max(0,
   min(BLOCK_MAX - block minutes, plan minutes left, new-lane minutes left))``;
4. adds no admission load the plan did not grant.

The same check-0 and check-1 functions re-read an AD deferral at each
boundary (:func:`deferrals_to_clear`).

**Protection** (A8; Codex verify F22, fix round 8): every item and attempt is
read through AD's material view (``adaptive_difficulty.material_view``),
computed once per slot. A withheld item (held-out material, an exam
reservation) fails check 0 whatever ``goals.held_out_selection`` says: AD's
protection is unconditional. When the held-out predicate, or the routine
exclusions, cannot be computed, AD is unavailable for the slot
(:class:`AdUnavailable`): the plan serves its planned item as the incumbent
does, and no deferral is released.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, replace
from typing import Any

from learnloop.daily_plan.admission import new_item_daily_cost
from learnloop.daily_plan.lanes import PoolItem
from learnloop.daily_plan.types import BLOCK_MAX_MINUTES

_EPS = 1e-9


class AdUnavailable(RuntimeError):
    """AD cannot decide this slot safely (the held-out predicate or the routine exclusions could
    not be computed): the plan serves its planned item as the incumbent does."""


def slot_view(env: Any) -> Any:
    """The slot's material view, computed once (A8). Raises :class:`AdUnavailable` when the
    held-out predicate cannot be computed (fail closed: no AD candidate, never an exception out
    of the serve)."""

    from learnloop.adaptive_difficulty.material_view import material_view

    try:
        view = material_view(env.vault, env.repository)
    except Exception as exc:  # noqa: BLE001 - an unreadable predicate makes AD unavailable, not the serve
        raise AdUnavailable(f"held-out predicate failed: {exc}") from exc
    if not view.available:
        raise AdUnavailable(view.reason or "held-out predicate unavailable")
    return view


def _attempted(env: Any, view: Any) -> set[str]:
    with env.repository.connection() as connection:
        return view.attempted_item_ids(connection)


def _exclusions(env: Any) -> Any:
    from learnloop.attempts.attempts import COLD_FOLLOWUP_TASK_KINDS
    from learnloop.diagnosis.remediation import COLD_RETRIEVAL_DELAY
    from learnloop.scheduling.serving_exclusions import out_of_timing_serving_exclusions

    try:
        return out_of_timing_serving_exclusions(env.vault, env.repository,
                                                cold_followup_kinds=COLD_FOLLOWUP_TASK_KINDS,
                                                reveal_window=COLD_RETRIEVAL_DELAY, clock=env.clock)
    except AdUnavailable:
        raise
    except Exception as exc:  # noqa: BLE001 - the routine exclusions failed: AD is unavailable (F22)
        raise AdUnavailable(f"serving exclusions failed: {exc}") from exc


def eligibility_failures(env: Any, item: Any, *, slot_facets: Iterable[str], capability: str,
                         exclusions: Any, view: Any) -> list[str]:
    """Check 0 for one candidate: why it is not in the cell pool now, or why it may not be served.
    ``view``: the slot's material view; a withheld item fails ``held_out`` unconditionally."""

    from learnloop.adaptive_difficulty import predict as PR
    from learnloop.adaptive_difficulty.selection import within_envelope
    from learnloop.adaptive_difficulty.serve_inputs import pre_exposed
    from learnloop.vault.lifecycle import practice_item_serving_block

    failed: list[str] = []
    facets = set(PR.facet_weights(env.vault, item))
    if PR.capability(item) != capability or not facets & set(slot_facets):
        failed.append("not_in_cell")
    if getattr(item, "status", "active") != "active":
        failed.append("retired")
    if str(item.id) in exclusions.reserved_exam_item_ids:
        failed.append("exam_reserved")
    if str(item.id) in exclusions.held_out_item_ids or (
            str(item.id) not in exclusions.reserved_exam_item_ids and (view.withheld(item.id) or view.covers(item))):
        # AD's own, unconditional protection (Codex verify F22): the routine exclusions' held-out
        # ids follow ``goals.held_out_selection``; the material view never does.
        failed.append("held_out")
    features = dict(item.task_features) if isinstance(getattr(item, "task_features", None), Mapping) else None
    if PR.capability(item) == "coordination" or not within_envelope(features):
        failed.append("envelope")
    try:
        if pre_exposed(env.repository, item, env.now_iso()):
            failed.append("pre_exposed")
    except Exception:  # noqa: BLE001 - an unreadable reveal ledger fails closed
        failed.append("pre_exposed")
    if practice_item_serving_block(env.vault, item) is not None:
        failed.append("serving_block")
    if str(item.id) in exclusions.rung_variant_hold_ids | exclusions.staged_owned_item_ids:
        failed.append("routine_exclusion")
    if str(item.id) in exclusions.cold_check_reserved_item_ids:
        failed.append("cold_check_reserved")
    if str(item.id) in exclusions.revealed_recently_item_ids:
        failed.append("recent_reveal")
    return failed


def _pool_item(item: Any, *, est_minutes: float, existing: PoolItem | None) -> PoolItem:
    if existing is not None:
        return replace(existing, lane=existing.lane or "new")
    return PoolItem(practice_item_id=str(item.id), learning_object_id=str(item.learning_object_id), rank=10**6,
                    priority=0.0, lane="new", reason="an AD candidate", est_minutes=float(est_minutes),
                    never_attempted=True)


def admission_failures(env: Any, items: Sequence[Any], *, pool: Mapping[str, PoolItem],
                       est: Mapping[str, float]) -> dict[str, list[str]]:
    """Check 1: the admission the slot passed, on a fresh snapshot, plus reversibility."""

    from learnloop.daily_plan.policy import router_active
    from learnloop.daily_plan.staged_frame import StagedFrame

    candidates = [_pool_item(item, est_minutes=est.get(str(item.id), 0.0), existing=pool.get(str(item.id)))
                  for item in items]
    failed: dict[str, list[str]] = {str(item.id): [] for item in items}
    material = StagedFrame(env.vault, env.repository, clock=env.clock).material(candidates)
    staged = router_active(env.vault)
    for item in items:
        item_id = str(item.id)
        if staged:
            for reason in material.refusals.get(item_id, ()):
                failed[item_id].append(f"constraint:{reason.get('constraint') or reason.get('key') or 'refused'}")
        else:
            existing = pool.get(item_id)
            if existing is None or existing.lane != "new" or not existing.never_attempted:
                failed[item_id].append("not_new_lane")
        cold = material.cold_items
        if cold is None or item_id in cold:
            failed[item_id].append("open_cold_check")
        if item_id in material.reserved_items:
            failed[item_id].append("reserved_surface")
    return failed


@dataclass(frozen=True)
class SlotSupport:
    request: Any
    est: Mapping[str, float]


def build_request(env: Any, record: Any, block: Any, slot: Any, built: Any, *, day: Sequence[Any],
                  router_propensity: float | None, view: Any) -> Any:
    """The slot's :class:`~learnloop.adaptive_difficulty.serving.SlotRequest`, every check re-read now,
    every item read through ``view`` (the slot's material view, :func:`slot_view`)."""

    from learnloop.adaptive_difficulty import predict as PR
    from learnloop.adaptive_difficulty.serving import SlotCandidate, SlotRequest

    vault = env.vault
    exclusions = _exclusions(env)
    slot_item = view.item(slot.practice_item_id)
    if slot_item is None:
        # Not in the vault, or withheld (A8): no AD candidate, so the slot is displaced as ineligible.
        return SlotRequest(record.id, block.id, slot.position, slot.practice_item_id, slot.learning_object_id, (),
                           now=env.now_iso())
    capability = PR.capability(slot_item)
    slot_facets = tuple(PR.facet_weights(vault, slot_item))
    attempted = _attempted(env, view)
    others = [item for item in view.items(learning_object_id=slot_item.learning_object_id)
              if str(item.id) != str(slot_item.id) and str(item.id) not in attempted
              and PR.capability(item) == capability]
    items = [slot_item, *others]
    pool = {item.practice_item_id: item for item in built.pool}
    est = {str(item.id): float(built.estimator.item_minutes(vault, str(item.id))) for item in items}
    est[str(slot_item.id)] = float(slot.est_minutes)
    failures = {str(item.id): eligibility_failures(env, item, slot_facets=slot_facets, capability=capability,
                                                    exclusions=exclusions, view=view) for item in items}
    for item_id, extra in admission_failures(env, items, pool=pool, est=est).items():
        failures[item_id].extend(extra)
    # Check 2: planned in any of today's plans (the slot item: in no slot but its own).
    planned: dict[str, int] = {}
    for plan in [record, *[p for p in day if p.id != record.id]]:
        for planned_item in plan.items():
            if not planned_item.displaced:
                planned[planned_item.practice_item_id] = planned.get(planned_item.practice_item_id, 0) + 1
    for item in items:
        item_id = str(item.id)
        count = planned.get(item_id, 0) - (1 if item_id == str(slot_item.id) else 0)
        if count > 0:
            failures[item_id].append("planned_elsewhere")
    # Check 3: fits the block.
    lefts = record.lane_left()
    slack = max(0.0, min(BLOCK_MAX_MINUTES - block.est_minutes(), record.minutes_left(), lefts.get("new", 0.0)))
    for item in items:
        item_id = str(item.id)
        if item_id != str(slot_item.id) and est[item_id] > est[str(slot_item.id)] + slack + _EPS:
            failures[item_id].append("over_block_budget")
    # Check 4: no admission load the plan did not grant.
    admission = record.admission
    horizon = int(admission.get("horizon_days") or 14)
    reviews = int(admission.get("reviews_per_new_item") or 3)
    slot_cost = new_item_daily_cost(est[str(slot_item.id)], reviews=reviews, horizon_days=horizon)
    ceiling = float(admission.get("ceiling_minutes") or 0.0)
    load = float(admission.get("review_load_per_day") or 0.0) + float(admission.get("added_load_per_day") or 0.0)
    floor_or_override = bool(admission.get("floor_applied")) or admission.get("override") is not None
    for item in items:
        item_id = str(item.id)
        if item_id == str(slot_item.id):
            continue
        cost = new_item_daily_cost(est[item_id], reviews=reviews, horizon_days=horizon)
        if cost <= slot_cost + _EPS:
            continue
        if floor_or_override or load - slot_cost + cost > ceiling + _EPS:
            failures[item_id].append("admission_load")
    candidates = tuple(SlotCandidate(str(item.id), tuple(dict.fromkeys(failures[str(item.id)])), est[str(item.id)])
                       for item in items)
    # The cell pool P_c: never-attempted servable items with the slot's primary facet at its capability.
    primary = sorted(PR.facet_weights(vault, slot_item).items(), key=lambda kv: (-kv[1], kv[0]))[0][0] \
        if slot_facets else None
    cell_pool = []
    if primary is not None:
        for item in view.items():
            if str(item.id) in attempted or PR.capability(item) != capability:
                continue
            if PR.facet_weights(vault, item).get(primary, 0.0) <= 0:
                continue
            reasons = eligibility_failures(env, item, slot_facets=(primary,), capability=capability,
                                           exclusions=exclusions, view=view)
            if not [r for r in reasons if r not in ("serving_block", "routine_exclusion", "cold_check_reserved",
                                                     "recent_reveal")]:
                cell_pool.append(str(item.id))
    return SlotRequest(record.id, block.id, int(slot.position), str(slot_item.id), str(slot_item.learning_object_id),
                       candidates, tuple(cell_pool), router_decision_id=block.decision_ref,
                       router_propensity=router_propensity, now=env.now_iso())


def deferrals_to_clear(env: Any, deferrals: Mapping[str, Mapping[str, Any]], *, built: Any) -> list[str]:
    """§6.1 step 0: the AD deferrals whose failed checks all pass now (check 0's sources and check 1
    on a fresh snapshot). Pre-exposure is never a deferral reason."""

    from learnloop.adaptive_difficulty import predict as PR

    if not deferrals:
        return []
    try:
        view = slot_view(env)
        exclusions = _exclusions(env)
    except AdUnavailable:
        # Fail closed: with AD unavailable no deferral is released (nothing is re-admitted).
        return []
    pool = {item.practice_item_id: item for item in built.pool}
    items = [view.item(item_id) for item_id in sorted(deferrals)]
    present = [item for item in items if item is not None]
    est = {str(item.id): float(built.estimator.item_minutes(env.vault, str(item.id))) for item in present}
    admission = admission_failures(env, present, pool=pool, est=est) if present else {}
    cleared = []
    for item in present:
        failed = eligibility_failures(env, item, slot_facets=tuple(PR.facet_weights(env.vault, item)),
                                      capability=PR.capability(item), exclusions=exclusions, view=view)
        failed = [f for f in failed if f != "pre_exposed"] + [f for f in admission.get(str(item.id), [])
                                                               if f != "not_new_lane"]
        if not failed:
            cleared.append(str(item.id))
    return cleared


def router_propensity(record: Any, block: Any) -> float:
    """The block's logged router propensity ``π_router`` (spec §10.1): the mixture's exact
    propensity where the router drew the block, else 1 (DL1's chooser or the staged rule is
    deterministic)."""

    value = (block.chosen or {}).get("propensity")
    return float(value) if value is not None else 1.0


__all__ = ["AdUnavailable", "admission_failures", "build_request", "deferrals_to_clear", "eligibility_failures",
           "router_propensity", "slot_view"]
