"""The plan's side of AD's slot draw (spec_adaptive_difficulty_v1 §6.1, §10.2; AD2+AD3, switch ``selection``).

When a planned new-material slot comes up to be served, the plan and AD take
turns in the serve transaction (the final round: inversion, owner decision
2026-10-24; ``engine._ad_slot_serve``):

* phase 1, AD (:func:`open_slot`, a read-only AD operation): the candidates its
  material view shows, its estimates, and the view's item states and withheld
  reveals (:class:`~learnloop.daily_plan.slot_facts_schema.SlotInputs`);
* phase 2, the plan (``daily_plan.slot_facts``), outside any AD operation: its
  verdicts, as a JSON facts record of ids, codes and numbers;
* phase 3, AD (:func:`decide`, an AD operation on its projected vault and
  repository): the facts decoded against the schema, the support's checks and
  ``adaptive_difficulty.serving.decide_slot``;
* phase 4, the plan: AD's choice re-checked against the facts; a choice it
  would not admit is rolled back and the planned item served.

AD never receives the plan's objects (``env``, the plan record, the pool, the
block) and never runs the plan's code. AD never builds or reorders blocks (§10.1).

**The candidates**: the slot item and the other never-attempted items of the
slot item's LO at its capability that are MEMBERS of the plan's admitted pool
at this boundary (``engine.admitted_new_material_ids``: the output of the build
the plan used, after every stage of it, including the scheduler's teach-back
value admission and caps and the plan's Keep and Light-touch new-material rule;
the compose fix round 2). AD reorders or chooses within the plan's own pool and
never adds to it; its own sibling enumeration only intersects with it. **The
support** is the candidates that pass every check, each re-read at the draw,
never taken from the block's admission (the slot item gets no exemption):

0. *still eligible*: in the cell pool now for some facet of the slot item
   (exam reservation, retirement, held-out derivation, pre-exposure, the depth
   envelope re-read); no serving block; outside the exclusions a selector
   outside the scheduler's timing honours (routine exclusions, an open cold
   follow-up's item, a reveal within the cold retrieval delay);
1. *the admission the slot item passed*: under the staged frame (router on)
   the constraint engine admits it on a fresh controller snapshot; and in both
   router settings, reversible (no open cold check, no reserved assessment
   surface) and admitted by the plan pool's own per-item predicate
   (``scheduler.pool_admission``: the routine gate, DL2's intent gate, the
   build's gates);
2. not planned in any of today's plans (the slot item: in no slot but its own);
3. fits the block: ``est(i) <= est(slot) + slack``, ``slack = max(0,
   min(BLOCK_MAX - block minutes, plan minutes left, new-lane minutes left))``;
4. adds no admission load the plan did not grant.

The same phases re-read the AD deferrals at each boundary
(:func:`open_deferrals`, :func:`deferrals_cleared`).

**Protection** (A8; Codex verify F22, fix round 8): every item and attempt is
read through AD's material view (``adaptive_difficulty.material_view``),
computed once per slot. A withheld item (held-out material, an exam
reservation) fails check 0 whatever ``goals.held_out_selection`` says: AD's
protection is unconditional. When the held-out predicate, or the routine
exclusions, cannot be computed, AD is unavailable for the slot
(:class:`AdUnavailable`, carrying only a code): the plan serves its planned item
as the incumbent does, and no deferral is released.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from learnloop.daily_plan.admission import new_item_daily_cost
from learnloop.daily_plan.slot_facts_schema import SlotFacts, SlotFactsError, SlotInputs, decode, exclusion_sets

_EPS = 1e-9


class AdUnavailable(RuntimeError):
    """AD cannot decide this slot safely (the held-out predicate, the guard or the facts): the plan
    serves its planned item as the incumbent does. Its only argument is a code."""


class SlotNotAdmitted(AdUnavailable):
    """The slot's own item is no longer in the plan's admitted pool (the facts' ``slot_admitted``):
    AD refuses the slot and the incumbent's own handling decides (the compose fix round 3)."""


@dataclass(frozen=True)
class SlotSession:
    """Phase 1's result: what AD hands the plan (``inputs``), and the view phase 3 reuses."""

    inputs: SlotInputs
    view: Any
    visible: frozenset[str]


def _unavailable(code: str) -> AdUnavailable:
    return AdUnavailable(code)


def _guarded(run: Any) -> Any:
    """Run an AD phase; any failure becomes :class:`AdUnavailable` carrying only a code, raised
    OUTSIDE the ``except`` clause (no cause, no context, no inner frames: the final round's codec)."""

    from learnloop.adaptive_difficulty.operation import is_denial

    code = None
    try:
        return run()
    except AdUnavailable as exc:
        code = str(exc.args[0]) if exc.args and isinstance(exc.args[0], str) and len(exc.args[0]) < 64 else "unavailable"
    except Exception as exc:  # noqa: BLE001 - every failure of AD's own phase: AD is unavailable
        code = "guard_denied" if is_denial(exc) else f"error:{type(exc).__name__}"
    raise _unavailable(code)


def _estimator(vault: Any, repository: Any, view: Any) -> Any:
    """AD's candidate estimates (Codex verify F28): the plan's estimator rule on duration evidence
    read through the slot's material view, so a withheld answer's latency never moves a
    candidate's estimate or its block-budget check. The plan's own estimates are untouched."""

    from learnloop.daily_plan.estimates import Estimator, load_duration_evidence

    config = vault.config.plan
    with repository.connection() as connection:
        rows = view.attempts(connection)
        events = view.plan_feedback_events(connection)
    evidence = load_duration_evidence(repository, latency_cap_minutes=float(config.latency_cap_minutes),
                                      attempt_rows=rows, event_rows=events)
    return Estimator(evidence=evidence, read_words_per_minute=int(config.read_words_per_minute))


def _inputs(vault: Any, repository: Any, view: Any, items: Sequence[Any], *, slot_visible: bool = True) -> SlotInputs:
    estimator = _estimator(vault, repository, view)
    with repository.connection() as connection:
        states = view.item_states(connection)
        withheld = view.withheld_reveal_ids(connection)
    return SlotInputs(
        candidate_ids=tuple(str(item.id) for item in items),
        learning_objects={str(item.id): str(item.learning_object_id) for item in items},
        est_minutes={str(item.id): float(estimator.item_minutes(vault, str(item.id))) for item in items},
        item_states=dict(states),
        withheld_reveal_ids=frozenset(str(i) for i in withheld),
        slot_visible=slot_visible,
    )


def open_slot(vault: Any, repository: Any, *, slot_item_id: str) -> SlotSession:
    """Phase 1 for a slot: the slot item and its never-attempted visible siblings at its capability."""

    from learnloop.adaptive_difficulty import predict as PR
    from learnloop.adaptive_difficulty.operation import ad_operation

    def run() -> SlotSession:
        with ad_operation(vault, repository, savepoint=True) as op:
            view = op.view
            if not view.available:
                raise AdUnavailable("predicate_unavailable")
            slot_item = view.item(slot_item_id)
            if slot_item is None:
                # Not in the vault, or withheld (A8): no AD candidate; phase 3 displaces the slot.
                return SlotSession(_inputs(op.vault, op.repository, view, (), slot_visible=False), view, frozenset())
            capability = PR.capability(slot_item)
            with op.repository.connection() as connection:
                attempted = view.attempted_item_ids(connection)
            siblings = [item for item in view.items(learning_object_id=slot_item.learning_object_id)
                        if str(item.id) != str(slot_item.id) and str(item.id) not in attempted
                        and PR.capability(item) == capability]
            items = [slot_item, *siblings]
            visible = frozenset(str(item.id) for item in view.items())
            return SlotSession(_inputs(op.vault, op.repository, view, items), view, visible)

    return _guarded(run)


def decide(vault: Any, repository: Any, wire: str, *, session: SlotSession) -> Any:
    """Phase 3 for a slot: the facts decoded against the schema (ids projected onto AD's view), the
    support's checks 0-4 from the facts and AD's own view, and the draw (``decide_slot``, which
    writes the ``ad_selections`` row). Returns ``(decision, request)``."""

    from learnloop.adaptive_difficulty import predict as PR
    from learnloop.adaptive_difficulty.operation import ad_operation
    from learnloop.adaptive_difficulty.serving import SlotCandidate, SlotRequest, decide_slot

    def run() -> Any:
        try:
            facts = decode(wire, visible=session.visible | set(session.inputs.candidate_ids),
                           learning_objects=set(session.inputs.learning_objects.values()))
        except SlotFactsError:
            facts = None
        if facts is None or facts.kind != "slot":
            raise AdUnavailable("facts_refused")
        with ad_operation(vault, repository, savepoint=True, protected=session.view) as op:
            view = op.view
            if view.epoch != session.view.epoch:
                raise AdUnavailable("epoch_changed")
            request = _request(op.vault, op.repository, view, facts, session)
            decision = decide_slot(op.vault, op.repository, request, view=view)
            return decision, request

    return _guarded(run)


def _request(vault: Any, repository: Any, view: Any, facts: SlotFacts, session: SlotSession) -> Any:
    from learnloop.adaptive_difficulty import predict as PR
    from learnloop.adaptive_difficulty.serving import SlotCandidate, SlotRequest

    slot_id = str(facts.slot_item_id or "")
    slot_item = view.item(slot_id) if session.inputs.slot_visible and slot_id else None
    if slot_item is None:
        return SlotRequest(facts.plan_id, facts.block_id, facts.position, slot_id, facts.slot_learning_object_id, (),
                           now=facts.now)
    exclusions = exclusion_sets(facts)
    capability = PR.capability(slot_item)
    slot_facets = tuple(PR.facet_weights(vault, slot_item))
    # AD's own enumeration intersected with the plan's admitted pool (round 2): the members only.
    members = set(facts.members)
    items = [slot_item, *(view.item(item_id) for item_id in session.inputs.candidate_ids
                          if item_id != slot_id and item_id in members)]
    items = [item for item in items if item is not None]
    est = dict(session.inputs.est_minutes)
    est[slot_id] = float(facts.slot_est_minutes or est.get(slot_id, 0.0))
    failures = {str(item.id): eligibility_failures(vault, repository, facts.now, item, slot_facets=slot_facets,
                                                    capability=capability, exclusions=exclusions, view=view)
                for item in items}
    for item in items:
        item_id = str(item.id)
        failures[item_id].extend(facts.refusals.get(item_id, ()))
        if facts.cold_items is None or item_id in facts.cold_items:
            failures[item_id].append("open_cold_check")
        if item_id in facts.reserved_items:
            failures[item_id].append("reserved_surface")
        # Check 2: planned in any of today's plans (the slot item: in no slot but its own).
        if facts.planned_counts.get(item_id, 0) > 0:
            failures[item_id].append("planned_elsewhere")
    budget = facts.budget
    # Check 3: fits the block.
    slack = float(budget.get("slack_minutes", 0.0))
    for item in items:
        item_id = str(item.id)
        if item_id != slot_id and est.get(item_id, 0.0) > est[slot_id] + slack + _EPS:
            failures[item_id].append("over_block_budget")
    # Check 4: no admission load the plan did not grant.
    horizon = int(budget.get("horizon_days", 14))
    reviews = int(budget.get("reviews_per_new_item", 3))
    slot_cost = new_item_daily_cost(est[slot_id], reviews=reviews, horizon_days=horizon)
    ceiling = float(budget.get("ceiling_minutes", 0.0))
    load = float(budget.get("load_per_day", 0.0))
    floor_or_override = bool(budget.get("floor_or_override", False))
    for item in items:
        item_id = str(item.id)
        if item_id == slot_id:
            continue
        cost = new_item_daily_cost(est.get(item_id, 0.0), reviews=reviews, horizon_days=horizon)
        if cost <= slot_cost + _EPS:
            continue
        if floor_or_override or load - slot_cost + cost > ceiling + _EPS:
            failures[item_id].append("admission_load")
    candidates = tuple(SlotCandidate(str(item.id), tuple(dict.fromkeys(failures[str(item.id)])),
                                     float(est.get(str(item.id), 0.0))) for item in items)
    # The cell pool P_c: never-attempted servable items with the slot's primary facet at its capability.
    primary = sorted(PR.facet_weights(vault, slot_item).items(), key=lambda kv: (-kv[1], kv[0]))[0][0] \
        if slot_facets else None
    cell_pool = []
    if primary is not None:
        with repository.connection() as connection:
            attempted = view.attempted_item_ids(connection)
        for item in view.items():
            if str(item.id) in attempted or PR.capability(item) != capability:
                continue
            if PR.facet_weights(vault, item).get(primary, 0.0) <= 0:
                continue
            reasons = eligibility_failures(vault, repository, facts.now, item, slot_facets=(primary,),
                                           capability=capability, exclusions=exclusions, view=view)
            if not [r for r in reasons if r not in ("serving_block", "routine_exclusion", "cold_check_reserved",
                                                     "recent_reveal")]:
                cell_pool.append(str(item.id))
    return SlotRequest(facts.plan_id, facts.block_id, int(facts.position or 0), slot_id,
                       str(slot_item.learning_object_id), candidates, tuple(cell_pool),
                       router_decision_id=facts.router_decision_id, router_propensity=facts.router_propensity,
                       now=facts.now)


def open_deferrals(vault: Any, repository: Any, deferral_ids: Iterable[str]) -> SlotSession:
    """Phase 1 for the boundary's AD deferrals: the deferred items AD's view shows."""

    from learnloop.adaptive_difficulty.operation import ad_operation

    def run() -> SlotSession:
        with ad_operation(vault, repository, savepoint=True) as op:
            view = op.view
            if not view.available:
                raise AdUnavailable("predicate_unavailable")
            items = [item for item in (view.item(item_id) for item_id in sorted(set(deferral_ids))) if item is not None]
            visible = frozenset(str(item.id) for item in view.items())
            return SlotSession(_inputs(op.vault, op.repository, view, items), view, visible)

    return _guarded(run)


def deferrals_cleared(vault: Any, repository: Any, wire: str, *, session: SlotSession) -> list[str]:
    """Phase 3 for deferrals: the deferred members whose check 0 (pre-exposure aside) and the plan's
    verdicts all pass now."""

    from learnloop.adaptive_difficulty import predict as PR
    from learnloop.adaptive_difficulty.operation import ad_operation

    def run() -> list[str]:
        try:
            facts = decode(wire, visible=session.visible | set(session.inputs.candidate_ids),
                           learning_objects=set(session.inputs.learning_objects.values()))
        except SlotFactsError:
            facts = None
        if facts is None or facts.kind != "deferrals":
            raise AdUnavailable("facts_refused")
        with ad_operation(vault, repository, savepoint=True, protected=session.view) as op:
            view = op.view
            exclusions = exclusion_sets(facts)
            cleared = []
            for item_id in session.inputs.candidate_ids:
                item = view.item(item_id)
                if item is None or item_id not in facts.members:
                    continue
                failed = eligibility_failures(op.vault, op.repository, facts.now, item,
                                              slot_facets=tuple(PR.facet_weights(op.vault, item)),
                                              capability=PR.capability(item), exclusions=exclusions, view=view)
                failed = [f for f in failed if f != "pre_exposed"] + list(facts.refusals.get(item_id, ()))
                if facts.cold_items is None or item_id in facts.cold_items:
                    failed.append("open_cold_check")
                if item_id in facts.reserved_items:
                    failed.append("reserved_surface")
                if not failed:
                    cleared.append(item_id)
            return cleared

    return _guarded(run)


def eligibility_failures(vault: Any, repository: Any, now_iso: str, item: Any, *, slot_facets: Iterable[str],
                         capability: str, exclusions: Any, view: Any) -> list[str]:
    """Check 0 for one candidate: why it is not in the cell pool now, or why it may not be served.
    ``vault`` and ``repository``: the operation's projected ones; ``exclusions``: the plan's routine
    exclusions from its facts; ``view``: the slot's material view (a withheld item fails
    ``held_out`` unconditionally)."""

    from learnloop.adaptive_difficulty import predict as PR
    from learnloop.adaptive_difficulty.selection import within_envelope
    from learnloop.adaptive_difficulty.serve_inputs import pre_exposed
    from learnloop.vault.lifecycle import practice_item_serving_block

    failed: list[str] = []
    facets = set(PR.facet_weights(vault, item))
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
    denied = False
    try:
        if pre_exposed(repository, item, now_iso, view=view):
            failed.append("pre_exposed")
    except Exception as exc:  # noqa: BLE001 - an unreadable reveal ledger fails closed
        from learnloop.adaptive_difficulty.operation import is_denial

        # The guard's refusal is not a candidate's exclusion: AD is unavailable for the slot.
        denied = is_denial(exc)
        if not denied:
            failed.append("pre_exposed")
    if denied:
        # Raised outside the except clause: no cause, no context (the final round's codec).
        raise AdUnavailable("guard_denied")
    if practice_item_serving_block(vault, item) is not None:
        failed.append("serving_block")
    if str(item.id) in exclusions.rung_variant_hold_ids | exclusions.staged_owned_item_ids:
        failed.append("routine_exclusion")
    if str(item.id) in exclusions.cold_check_reserved_item_ids:
        failed.append("cold_check_reserved")
    if str(item.id) in exclusions.revealed_recently_item_ids:
        failed.append("recent_reveal")
    return failed


__all__ = ["AdUnavailable", "SlotNotAdmitted", "SlotSession", "decide", "deferrals_cleared", "eligibility_failures",
           "open_deferrals", "open_slot"]
