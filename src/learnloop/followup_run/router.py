"""The router's decision for one workflow, before any item exists (spec §5, §5.1).

The router decides whether and when; the orchestrator keeps the measurement. The value
checks log and do not decide on this lane (the Nov 2 decision that the nat-scale rule stop
deciding): the repair classes and, where they settle it, the repair lane's verdict are on the
row; where they don't, the verdict is recorded as absent, since no instrument exists yet. What still refuses is hard:
a learner's own "Not now", pending machine checks, and an episode that is already measuring.

The decision is appended to the immutable ``router_decisions``, naming the workflow; a
separate binding links it to the generated item and both presentations, and receipts,
outcome joins and data capture's measurement follow that binding.

**No plan** (§5.1): there is no ``plan_interrupt`` timing decision, classic Today still logs
its ``today_offer``, and the probe goes first. No ``no_intervention`` draw is made (the
spec's default, recorded in the review file).

Every decision, logged or not, leaves one ``followup_gate`` decision record (refactor B5;
``refusal_records``): the arm, the rule, the arms' probabilities, the components' statuses
(their answers by reference, on the ``router_decisions`` row), and whether the value checks
failed. A logged one is written in the decision's own transaction.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field, replace
import logging
from typing import Any

from learnloop import refusal_records
from learnloop.algorithm_versions import probe_router_on
from learnloop.clock import Clock, utc_now_iso
from learnloop.db.repositories import Repository
from learnloop.db.stores import followup_serve as store
from learnloop.followup_serve.gates import SERVING_SURFACE
from learnloop.plan_refs import LESSON_OFFER_PREFIX

LOG = logging.getLogger(__name__)

ASK_NOW = "insert_now"
WAIT = "continue_current"
NO_INTERVENTION = "no_intervention"
DECLINE = "decline"

#: How the screen names each arm (§6.4).
ARM_LABELS: Mapping[str, str] = {
    ASK_NOW: "ask now", WAIT: "wait", NO_INTERVENTION: "no question", DECLINE: "can't ask",
}


@dataclass(frozen=True)
class FollowupDecision:
    chosen_ref: str
    reason: str
    decided_by: str
    propensity: float = 1.0
    decision_id: str | None = None
    #: The plan's block it was decided against (None: no plan).
    block_id: str | None = None
    refusals: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    record: dict[str, Any] = field(default_factory=dict)
    why: str = ""
    wait_feasible: bool = True
    observational: dict[str, Any] = field(default_factory=dict)
    plan_id: str | None = None
    plan_kind: str | None = None
    local_date: str | None = None
    #: IH2 (spec_instruct_handoff_v1 §5 item 3): what a drawn lesson offer needs to become the plan's next step, in the
    #: decision's transaction: ``(env, record id, candidate)``. None: no offer was drawn, or this is a recorded decision.
    offer_placement: Any = None
    #: Why the logged value checks failed (``observational`` is then ``{}``): only the gate's decision record keeps
    #: its class and frame (the map's S14); the router's row is unchanged.
    value_check_error: BaseException | None = field(default=None, compare=False, repr=False)

    @property
    def lesson_offer(self) -> bool:
        return self.chosen_ref.startswith(LESSON_OFFER_PREFIX)

    @property
    def refused(self) -> bool:
        return self.chosen_ref == DECLINE

    @property
    def no_intervention(self) -> bool:
        return self.chosen_ref == NO_INTERVENTION

    @property
    def wait(self) -> bool:
        return self.chosen_ref == WAIT

    def for_author(self) -> dict[str, Any]:
        return {"chosen": ARM_LABELS.get(self.chosen_ref, self.chosen_ref),
                "timing": "at the start of the next block" if self.wait else "as the next question"}


def hard_refusal(vault: Any, repository: Repository, row: Mapping[str, Any], *, factor_id: str) -> str | None:
    """§5: what still refuses, in the orchestrator's own terms, before anything is spent."""

    from learnloop.diagnosis.probe_hard_stops import learner_preference, probe_episode_conflict
    from learnloop.diagnosis.machine_checks import pending_machine_checks_for_factor

    preference = learner_preference(
        repository, factor_id=factor_id, session_id=row.get("session_id"),
        learning_object_id=str(row["learning_object_id"]),
    )
    if preference != "allow":
        return f"learner_{preference}"
    # The factor's checks and those on the whole learning object, which name no factor.
    if pending_machine_checks_for_factor(repository, factor_id=factor_id,
                                         learning_object_id=str(row["learning_object_id"])):
        return "pending_machine_checks"
    # The repair lane's own check (one copy, K9-9): another episode owns the learning object and has measured.
    reason = probe_episode_conflict(repository, factor_id=factor_id, learning_object_id=str(row["learning_object_id"]))
    return str(reason) if reason is not None else None


def observational(repository: Repository, factor_id: str) -> dict[str, Any]:
    """§5 item 5: the checks that stopped deciding on this lane, still on the record."""

    return _observe(repository, factor_id)[0]


#: Why the logged verdict is absent when the repair classes leave the question open: the gain, the change
#: probability and the burden are facts about an instrument, and this lane authors its probe after deciding.
VERDICT_ABSENT_NO_INSTRUMENT = "no_instrument_before_authoring"


def _observe(repository: Repository, factor_id: str) -> tuple[dict[str, Any], BaseException | None]:
    """The value checks' answer, or ``{}`` and the exception that stopped them (which never decides).

    The repair-lane verdict is logged only where the repair classes settle it; otherwise its absence and the reason.
    A verdict computed from zeros put in for the instrument's facts would read like a finding and is not one.
    """

    from learnloop.diagnosis.causal_probe_coherence import repair_class_need_for_factor
    from learnloop.diagnosis.probe_facts import settled_by_repair_classes

    try:
        need = repair_class_need_for_factor(repository, factor_id)
        classes = list(need.get("repair_class_ids") or [])
        covers = bool(need.get("common_repair_covers"))
        # `need`'s classes are already distinct, non-empty and sorted, so more than one means different repairs.
        settled = settled_by_repair_classes(common_repair_covers=covers, different_repairs=len(classes) > 1)
        verdict = (
            {"decide_probe": settled[0]} if settled is not None
            else {"decide_probe_absent": VERDICT_ABSENT_NO_INSTRUMENT}
        )
        return {
            **verdict,
            "repair_class_ids": classes,
            "repair_class_divergence": bool(need.get("repair_class_divergence")),
            "common_repair_covers": covers,
        }, None
    except Exception as exc:  # noqa: BLE001 - what is only logged never decides
        LOG.warning("follow-up value checks not logged for %s", factor_id, exc_info=True)
        return {}, exc


def _card_facts(vault: Any, repository: Repository, choice: Any, seen: Mapping[str, Any]) -> list[str]:
    statements = [
        str((repository.causal_hypothesis(hypothesis_id) or {}).get("statement") or "")
        for hypothesis_id in choice.hypothesis_ids
    ]
    facts = ["Possible causes of the miss: " + "; ".join(value for value in statements if value)]
    if seen and not seen.get("repair_class_divergence"):
        # §5 item 5: a fact on the card, since minutes may be spent on improving the model.
        facts.append("These causes share one repair, so the answer would not change what is taught next.")
    return facts


def _plan_context(vault: Any, repository: Repository, row: Mapping[str, Any], *, clients: Any, clock: Clock | None) -> Any:
    """The session's standing plan and its router gate, or None (no plan, no timing decision)."""

    from learnloop.daily_plan.engine import PlanEnv, get_or_create_today, plan_active
    from learnloop.daily_plan.policy import mixture_active, objective_active, policy_for, router_active

    session_id = row.get("session_id")
    if not session_id or not plan_active(vault):
        return None
    runtime = getattr(clients, "runtime", None)
    policy = policy_for(vault, repository, session_id=str(session_id), clock=clock, runtime=runtime, serve=True)
    env = PlanEnv(vault=vault, repository=repository, clock=clock, session_id=str(session_id), policy=policy)
    record = get_or_create_today(env, create=False)
    if record is None or not record.is_open:
        return None
    if not (router_active(vault) and mixture_active(vault)) or policy.restraint is None:
        # §5: the restraint off means the plan never waits, as DL1's rules.
        return env, record, None
    from learnloop.daily_plan.router_chooser import FollowupGate
    gate_class: Any = FollowupGate
    if objective_active(vault):
        # Router objective RO5 (spec §8.3): with the objective serving, the follow-up's decision is the two-policy
        # mix's; with the objective off, FG1's gate as before.
        from learnloop.daily_plan.objective_chooser import ObjectiveFollowupGate

        gate_class = ObjectiveFollowupGate
    gate = gate_class(
        vault, repository, policy.restraint.runtime, frame=policy.restraint.frame,
        card_builder=policy.restraint.card_builder, session_id=str(session_id), clock=clock, may_defer=False,
    )
    return env, record, gate


#: At the probe router's tag, who decided where no plan's router could: the probe coin alone (no plan, or the router
#: switched off). The decision is logged, as every other decision of the router.
PROBE_COIN_NO_PLAN = "probe_coin_no_plan"
PROBE_COIN_ROUTER_OFF = "probe_coin_router_off"


def _coin_decision(vault: Any, row: Mapping[str, Any], *, decided_by: str, observational: dict[str, Any],
                   value_check_error: BaseException | None, **plan_fields: Any) -> FollowupDecision:
    """The probe router's tag with no plan or no router to draw: the probe is not written yet, so no policy can value it
    (G2 design decision 1); no intervention, unless the probe coin asks it now (``probe_coin``), with its exact
    propensity and its own assignment row. Below the tag the probe is asked now, deterministically."""

    from learnloop.ids import new_ulid
    from learnloop.router_objective import probe_coin as PC

    support = [ASK_NOW, NO_INTERVENTION]
    # The coin's boundary: this workflow's decision of this kind (the coin's seed adds the decision's own id).
    key = f"{decided_by}:{row.get('id')}"
    decision_id = new_ulid()
    record: dict[str, Any] = {"mode": "probe_router", "policy": PC.VERSION, "decided_by": decided_by,
                              "decision_id": decision_id, "mix_support": [NO_INTERVENTION],
                              "objective_followup": {"support": support, "mix_support": [NO_INTERVENTION],
                                                     "workflow_id": row.get("id"), "version": PC.VERSION,
                                                     "probe": "unwritten_no_information_credit"}}
    rate = PC.share(vault.config)
    if not PC.applies(rate):
        record["served_pi"] = {NO_INTERVENTION: 1.0}
        return FollowupDecision(NO_INTERVENTION, decided_by, decided_by, decision_id=decision_id, record=record,
                                observational=observational, value_check_error=value_check_error, **plan_fields)
    seed = PC.seed_for(key, decision_id)
    coin = PC.flip(seed, rate, probe_ref=ASK_NOW, mu={NO_INTERVENTION: 1.0}, drawn=NO_INTERVENTION, boundary_key=key)
    record.update(probe_coin=coin.as_dict(),
                  served_pi=PC.served_distribution({NO_INTERVENTION: 1.0}, rate, probe_ref=ASK_NOW),
                  ro5_assignments=[PC.pending_assignment(coin, seed=seed, support=support)])
    return FollowupDecision(coin.served, decided_by, decided_by, propensity=coin.served_propensity,
                            decision_id=decision_id, record=record, observational=observational,
                            value_check_error=value_check_error, **plan_fields)


def decide(vault: Any, repository: Repository, row: Mapping[str, Any], *, choice: Any, clients: Any,
           clock: Clock | None) -> FollowupDecision:
    factor_id = str(choice.factor_id)
    seen, seen_error = _observe(repository, factor_id)
    refusal = hard_refusal(vault, repository, row, factor_id=factor_id)
    if refusal is not None:
        return FollowupDecision(DECLINE, refusal, "refused", refusals=({"reason": refusal, "constraint_key": refusal},),
                                observational=seen, value_check_error=seen_error)
    context = _plan_context(vault, repository, row, clients=clients, clock=clock)
    probe_router = probe_router_on(vault.config)
    if context is None:
        if probe_router:
            return _coin_decision(vault, row, decided_by=PROBE_COIN_NO_PLAN, observational=seen,
                                  value_check_error=seen_error)
        return FollowupDecision(ASK_NOW, "no_plan", "no_plan", observational=seen, value_check_error=seen_error)
    env, record, gate = context
    current = record.current_block()
    block = current if current is not None and not current.is_reading else None
    plan_fields = {
        "plan_id": record.id, "plan_kind": record.kind, "local_date": str(record.row.get("local_date") or ""),
        "block_id": block.id if block is not None else None,
    }
    if gate is None:
        if probe_router:
            return _coin_decision(vault, row, decided_by=PROBE_COIN_ROUTER_OFF, observational=seen,
                                  value_check_error=seen_error, **plan_fields)
        return FollowupDecision(ASK_NOW, "router_off", "staged", observational=seen, value_check_error=seen_error,
                                **plan_fields)
    # Waiting is a choice only when there is a block to finish and room after it (Codex review F8's rule).
    remaining = sum(entry.est_minutes for entry in block.items if not entry.resolved) if block is not None else 0.0
    wait_feasible = block is not None and record.minutes_left() - remaining > 0
    # IH2 (spec_instruct_handoff_v1 §5 item 3): a lesson available is one more arm of this decision. The phone serves no
    # lesson until V6, so a miss on the phone's surface decides as before.
    offer = None
    if str(row.get("surface") or SERVING_SURFACE) == SERVING_SURFACE:
        from learnloop.daily_plan.engine import interrupt_offer

        offer = interrupt_offer(env, record, block)
    outcome = gate.decide_followup(record, block, row, wait_feasible=wait_feasible,
                                   facts=_card_facts(vault, repository, choice, seen),
                                   **({"offer": offer} if offer is not None else {}))
    placement = (env, record.id, offer.candidate) if outcome.chosen_ref.startswith(LESSON_OFFER_PREFIX) else None
    return FollowupDecision(
        outcome.chosen_ref, outcome.chosen_ref, str(outcome.record.get("decided_by") or "mixture"),
        propensity=float(outcome.propensity), record=dict(outcome.record), why=outcome.why,
        wait_feasible=outcome.wait_feasible, decision_id=outcome.record.get("decision_id"), observational=seen,
        offer_placement=placement, value_check_error=seen_error, **plan_fields,
    )


def decide_once(vault: Any, repository: Repository, row: Mapping[str, Any], *, choice: Any, clients: Any,
                clock: Clock | None) -> FollowupDecision:
    """The workflow's one decision (§5 item 2): the one it already recorded, else a new one.

    A retry or a lease recovery after a failed generation keeps the arm, the propensity
    and the outcome binding the first draw committed; no model is asked again. The draw
    doesn't outrank what came after it: a retry that would still generate asks the hard
    refusals again, and one that holds now is this decision's outcome, on the same row.
    """

    if row.get("chosen_ref"):
        recorded = FollowupDecision(str(row["chosen_ref"]), "recorded", "recorded",
                                    decision_id=row.get("decision_id") or None)
        if recorded.chosen_ref not in {ASK_NOW, WAIT}:
            return recorded
        refusal = hard_refusal(vault, repository, row, factor_id=str(choice.factor_id))
        if refusal is None:
            return recorded
        refused = replace(recorded, chosen_ref=DECLINE, reason=refusal, decided_by="refused",
                          refusals=({"reason": refusal, "constraint_key": refusal},))
        # The retry's refusal is a decision of its own (the row keeps the first draw): only its record says so.
        refusal_records.write(repository, refusal_records.FOLLOWUP_GATE,
                              lambda: refusal_records.followup_gate_record(row, refused, logged=False, retry=True))
        return replace(refused, decided_by=recorded.decided_by)
    decision = decide(vault, repository, row, choice=choice, clients=clients, clock=clock)
    return record_decision(vault, repository, row, decision, clock=clock)


def _gate_record(row: Mapping[str, Any], decision: FollowupDecision, *, logged: bool) -> Any:
    return refusal_records.followup_gate_record(row, decision, logged=logged,
                                                value_check_error=decision.value_check_error)


class _Unlogged(Exception):
    """The probe router's tag: the decision or its coin's assignment could not be committed; nothing it chose is
    served (G2-R4)."""


def record_decision(vault: Any, repository: Repository, row: Mapping[str, Any], decision: FollowupDecision, *,
                    clock: Clock | None) -> FollowupDecision:
    """Log it, with its objective frozen, and name it on the workflow, in one transaction, so
    a crash leaves both or neither. Logging never blocks the learner's plan; with no plan
    there is no decision to log (§5.1). A receipt already logged is the decision: what the
    row says stands, and nothing is written twice."""

    from learnloop.adaptive_difficulty.readiness import decision_state_fields
    from learnloop.ids import new_ulid
    from learnloop.daily_plan import measurement as objectives
    from learnloop.followup_serve import workflow as wf
    from learnloop.router_objective import decision_state
    from learnloop.scheduling.fsrs import retrievability
    from learnloop.router.plan_log import existing_followup_decision, log_followup_decision

    if decision.decided_by == "no_plan":
        wf.set_fields(repository, str(row["id"]), chosen_ref=decision.chosen_ref, clock=clock)
        refusal_records.write(repository, refusal_records.FOLLOWUP_GATE,
                              lambda: _gate_record(row, decision, logged=False))
        return decision
    decision_id: str | None = None
    now = utc_now_iso(clock)
    probe_router = probe_router_on(vault.config)
    # IH2: a follow-up that lost to a lesson is decided again later, on a receipt of its own naming that decision.
    redraw_of = wf.lost_offer_decision(repository, str(row["id"]))
    offer_block_id = new_ulid() if decision.lesson_offer else None
    # RO0 rows 9 and 13: the follow-up's LO, read before the transaction opens.
    from learnloop.diagnosis.probe_episodes import effective_posterior_reader

    state = decision_state.prepare(
        vault, repository, candidates=[{"learning_object_ids": [row["learning_object_id"]]}], session_id=row.get("session_id"),
        ad_fields=lambda los: decision_state_fields(vault, repository, list(los)), retrievability=retrievability,
        clock=clock, effective_posterior=effective_posterior_reader(vault, repository))
    try:
        with repository.atomic(), repository.connection() as connection:
            logged = existing_followup_decision(connection, block_id=decision.block_id, workflow_id=str(row["id"]),
                                                redraw_of=redraw_of)
            if logged is not None:
                decision = replace(decision, chosen_ref=str(logged["chosen_ref"]), propensity=float(logged["propensity"]))
                store.update_workflow(connection, str(row["id"]), at=now, chosen_ref=decision.chosen_ref,
                                      decision_id=str(logged["id"]))
                return replace(decision, decision_id=str(logged["id"]))
            decision_id = log_followup_decision(connection, {
                "plan_id": decision.plan_id, "plan_kind": decision.plan_kind, "local_date": decision.local_date,
                "block_id": decision.block_id, "session_id": row.get("session_id"),
                "workflow": {"id": row["id"], "learning_object_id": row["learning_object_id"],
                             "source_attempt_id": row["source_attempt_id"], "factor_id": row.get("factor_id")},
                "chosen_ref": decision.chosen_ref, "propensity": decision.propensity,
                "refused": {"reasons": list(decision.refusals)} if decision.refusals else {},
                "wait_feasible": decision.wait_feasible, "router_record": decision.record, "why": decision.why,
                "observational": decision.observational, "decided_at": now, "config": vault.config,
                **({"redraw_of": redraw_of} if redraw_of else {}),
                **({"offer_block_id": offer_block_id} if offer_block_id else {}),
            })
            if decision_id is not None:
                decision_state.record(connection, decision_id=decision_id, decision_kind="plan_interrupt", material=state,
                                      config=vault.config, at=now)
                # RO5 landing ruling R5 (1): at the tag the objective's decision carries its trace (none below it,
                # where the record holds no ``objective_trace``: nothing is written).
                from learnloop.router_objective import trace as objective_trace

                objective_trace.record(connection, decision_id=decision_id, decision_kind="plan_interrupt",
                                       router_record=decision.record, config=vault.config,
                                       local_date=str(decision.local_date or ""), session_id=row.get("session_id"),
                                       at=now)
            if probe_router and decision_id is None:
                # The probe router's tag: no arm is served without its committed decision (G2-R4).
                raise _Unlogged("the decision was not logged")
            if decision_id is not None and (decision.record or {}).get("ro5_assignments"):
                # The probe router's tag: the probe coin's assignment, with the decision it belongs to; both commit or
                # neither does (G2-R4).
                from learnloop.router_objective import assignments as ro5_assignments

                pending = decision.record["ro5_assignments"]
                written = ro5_assignments.record_pending(connection, pending, unit_id=decision_id, at=now)
                if probe_router and len(written) != len(pending):
                    raise _Unlogged("the probe coin's assignment was not written")
            if decision_id is not None and decision.offer_placement is not None:
                from learnloop.daily_plan.engine import place_interrupt_offer

                env, record_id, candidate = decision.offer_placement
                place_interrupt_offer(env, connection, record_id, candidate, decision_id=decision_id,
                                      block_id=str(offer_block_id), why=decision.why,
                                      why_kind=(decision.record or {}).get("offer_why_kind"),
                                      propensity=decision.propensity)
            if decision_id is not None and not decision.refused and not decision.lesson_offer:
                offered = (decision.record or {}).get("objective_followup")
                # At the tag the frozen support is the objective decision's own (R5 (1), R8: the three arms, or
                # ask-now alone with no room to wait); below it, FG1's arms as before.
                support = (list(offered["support"]) if isinstance(offered, Mapping) and offered.get("support")
                           else [ASK_NOW, *([WAIT] if decision.wait_feasible else []), NO_INTERVENTION])
                arm = {WAIT: objectives.ARM_WAIT, NO_INTERVENTION: objectives.ARM_NO_INTERVENTION}.get(
                    decision.chosen_ref, objectives.ARM_INSERT)
                objectives.record(
                    vault, repository, connection, decision_id=decision_id, decision_kind="plan_interrupt",
                    frozen=objectives.freeze_followup(str(row["learning_object_id"]), support=support), arm=arm,
                    clock=clock, exclude=set(),
                )
            store.update_workflow(connection, str(row["id"]), at=now, chosen_ref=decision.chosen_ref,
                                  decision_id=decision_id)
            logged = replace(decision, decision_id=decision_id)
            # The gate's record, in the decision's own transaction (after the decision, holding the lock it took).
            refusal_records.write_on(connection, refusal_records.FOLLOWUP_GATE,
                                     lambda: _gate_record(row, logged, logged=decision_id is not None))
            return logged
    except Exception:  # noqa: BLE001 - logging never blocks the learner's plan
        LOG.warning("follow-up decision not logged for %s", row["id"], exc_info=True)
    if probe_router and not decision.refused:
        # The probe router's tag: an unlogged decision serves the predecessor-safe arm, no intervention: never a probe
        # asked without its decision and assignment, and never another arm in a drawn lesson's place (G2-R4).
        decision = replace(decision, chosen_ref=NO_INTERVENTION, offer_placement=None, propensity=1.0)
    elif decision.lesson_offer:
        # IH2: with no receipt there is no offer to answer, so the rules' pick, the follow-up, stands.
        decision = replace(decision, chosen_ref=ASK_NOW, offer_placement=None)
    wf.set_fields(repository, str(row["id"]), chosen_ref=decision.chosen_ref, decision_id=None, clock=clock)
    unlogged = replace(decision, decision_id=None)
    refusal_records.write(repository, refusal_records.FOLLOWUP_GATE, lambda: _gate_record(row, unlogged, logged=False))
    return unlogged


def record_outcome(repository: Repository, row: Mapping[str, Any], decision: FollowupDecision, *, outcome: str,
                   clock: Clock | None) -> None:
    """Generation failure, skip and abandonment are distinct outcomes (§5 item 2)."""

    if decision.decision_id:
        append_outcome(repository, str(decision.decision_id), str(row["id"]), outcome=outcome, clock=clock)


def append_outcome(repository: Repository, decision_id: str, workflow_id: str, *, outcome: str, clock: Clock | None) -> None:
    with repository.atomic(), repository.connection() as connection:
        store.append_binding(connection, decision_id=decision_id, workflow_id=workflow_id, binding_kind="outcome",
                             outcome=outcome, at=utc_now_iso(clock))


def bind_item(repository: Repository, row: Mapping[str, Any], decision: FollowupDecision, admitted: Any, *,
              clock: Clock | None) -> None:
    """The appended binding: decision -> generated item and its probe presentation."""

    if not decision.decision_id:
        return
    with repository.atomic(), repository.connection() as connection:
        store.append_binding(
            connection, decision_id=str(decision.decision_id), workflow_id=str(row["id"]), binding_kind="item",
            practice_item_id=admitted.practice_item_id, probe_presentation_id=admitted.presentation_id,
            at=utc_now_iso(clock),
        )


def bind_plan_presentation(repository: Repository, row: Mapping[str, Any], *, plan_presentation_id: str,
                           clock: Clock | None) -> None:
    """The second presentation: the plan's own, once Next served it."""

    if not row.get("decision_id"):
        return
    with repository.atomic(), repository.connection() as connection:
        store.append_binding(
            connection, decision_id=str(row["decision_id"]), workflow_id=str(row["id"]),
            binding_kind="plan_presentation", practice_item_id=row.get("practice_item_id"),
            plan_presentation_id=plan_presentation_id, at=utc_now_iso(clock),
        )


__all__ = [
    "ARM_LABELS", "ASK_NOW", "DECLINE", "FollowupDecision", "NO_INTERVENTION", "WAIT", "append_outcome", "bind_item",
    "bind_plan_presentation", "decide", "decide_once", "hard_refusal", "observational", "record_decision", "record_outcome",
]
