"""The router's decision for one workflow, before any item exists (spec §5, §5.1).

The router decides whether and when; the orchestrator keeps the measurement. The value
checks log and do not decide on this lane (the Nov 2 decision that the nat-scale rule stop
deciding): ``decide_probe`` runs and its answer is on the row. What still refuses is hard:
a learner's own "Not now", pending machine checks, and an episode that is already measuring.

The decision is appended to the immutable ``router_decisions``, naming the workflow; a
separate binding links it to the generated item and both presentations, and receipts,
outcome joins and data capture's measurement follow that binding.

**No plan** (§5.1): there is no ``plan_interrupt`` timing decision, classic Today still logs
its ``today_offer``, and the probe goes first. No ``no_intervention`` draw is made (the
spec's default, recorded in the review file).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
import logging
from typing import Any

from learnloop.clock import Clock, utc_now_iso
from learnloop.db.repositories import Repository
from learnloop.db.stores import followup_serve as store

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

    from learnloop.diagnosis.causal_orchestrator import (
        _causal_origin,
        episode_conflict_reason,
        learner_preference,
        pending_machine_checks_for_factor,
    )

    preference = learner_preference(
        repository, factor_id=factor_id, session_id=row.get("session_id"),
        learning_object_id=str(row["learning_object_id"]),
    )
    if preference != "allow":
        return f"learner_{preference}"
    if pending_machine_checks_for_factor(repository, factor_id=factor_id):
        return "pending_machine_checks"
    existing = repository.open_probe_episode(str(row["learning_object_id"]))
    if existing is not None and str(existing.origin or "") != _causal_origin(factor_id):
        reason = episode_conflict_reason(repository, existing)
        if reason is not None:
            return str(reason)
    return None


def observational(repository: Repository, factor_id: str) -> dict[str, Any]:
    """§5 item 5: the checks that stopped deciding on this lane, still on the record."""

    from learnloop.diagnosis.causal_probe_coherence import decide_probe, repair_class_need_for_factor

    try:
        need = repair_class_need_for_factor(repository, factor_id)
        check = decide_probe(
            repair_class_ids=list(need.get("repair_class_ids") or []),
            common_repair_covers=bool(need.get("common_repair_covers")),
            # No instrument exists yet, so the orchestrator's own pinned fallback.
            expected_information_gain=0.0,
            probability_information_changes_repair=0.0,
            probe_burden_minutes=0.0,
            avoided_overteaching_minutes=0.0,
            repository=repository,
        )
        return {
            "decide_probe": check.decision,
            "repair_class_ids": list(need.get("repair_class_ids") or []),
            "repair_class_divergence": bool(need.get("repair_class_divergence")),
            "common_repair_covers": bool(need.get("common_repair_covers")),
        }
    except Exception:  # noqa: BLE001 - what is only logged never decides
        LOG.warning("follow-up value checks not logged for %s", factor_id, exc_info=True)
        return {}


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
    from learnloop.daily_plan.policy import mixture_active, policy_for, router_active

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

    gate = FollowupGate(
        vault, repository, policy.restraint.runtime, frame=policy.restraint.frame,
        card_builder=policy.restraint.card_builder, session_id=str(session_id), clock=clock, may_defer=False,
    )
    return env, record, gate


def decide(vault: Any, repository: Repository, row: Mapping[str, Any], *, choice: Any, clients: Any,
           clock: Clock | None) -> FollowupDecision:
    factor_id = str(choice.factor_id)
    seen = observational(repository, factor_id)
    refusal = hard_refusal(vault, repository, row, factor_id=factor_id)
    if refusal is not None:
        return FollowupDecision(DECLINE, refusal, "refused", refusals=({"reason": refusal, "constraint_key": refusal},),
                                observational=seen)
    context = _plan_context(vault, repository, row, clients=clients, clock=clock)
    if context is None:
        return FollowupDecision(ASK_NOW, "no_plan", "no_plan", observational=seen)
    env, record, gate = context
    current = record.current_block()
    block = current if current is not None and not current.is_reading else None
    plan_fields = {
        "plan_id": record.id, "plan_kind": record.kind, "local_date": str(record.row.get("local_date") or ""),
        "block_id": block.id if block is not None else None,
    }
    if gate is None:
        return FollowupDecision(ASK_NOW, "router_off", "staged", observational=seen, **plan_fields)
    # Waiting is a choice only when there is a block to finish and room after it (Codex review F8's rule).
    remaining = sum(entry.est_minutes for entry in block.items if not entry.resolved) if block is not None else 0.0
    wait_feasible = block is not None and record.minutes_left() - remaining > 0
    outcome = gate.decide_followup(record, block, row, wait_feasible=wait_feasible,
                                   facts=_card_facts(vault, repository, choice, seen))
    return FollowupDecision(
        outcome.chosen_ref, outcome.chosen_ref, str(outcome.record.get("decided_by") or "mixture"),
        propensity=float(outcome.propensity), record=dict(outcome.record), why=outcome.why,
        wait_feasible=outcome.wait_feasible, decision_id=outcome.record.get("decision_id"), observational=seen,
        **plan_fields,
    )


def record_decision(vault: Any, repository: Repository, row: Mapping[str, Any], decision: FollowupDecision, *,
                    clock: Clock | None) -> FollowupDecision:
    """Log it, with its objective frozen, and name it on the workflow. Logging never blocks
    the learner's plan; with no plan there is no decision to log (§5.1)."""

    from dataclasses import replace

    from learnloop.daily_plan import measurement as objectives
    from learnloop.data_capture.gates import serving_on
    from learnloop.followup_serve import workflow as wf
    from learnloop.router.plan_log import log_followup_decision

    if decision.decided_by == "no_plan":
        wf.set_fields(repository, str(row["id"]), chosen_ref=decision.chosen_ref, clock=clock)
        return decision
    decision_id: str | None = None
    now = utc_now_iso(clock)
    try:
        with repository.atomic(), repository.connection() as connection:
            decision_id = log_followup_decision(connection, {
                "plan_id": decision.plan_id, "plan_kind": decision.plan_kind, "local_date": decision.local_date,
                "block_id": decision.block_id, "session_id": row.get("session_id"),
                "workflow": {"id": row["id"], "learning_object_id": row["learning_object_id"],
                             "source_attempt_id": row["source_attempt_id"], "factor_id": row.get("factor_id")},
                "chosen_ref": decision.chosen_ref, "propensity": decision.propensity,
                "refused": {"reasons": list(decision.refusals)} if decision.refusals else {},
                "wait_feasible": decision.wait_feasible, "router_record": decision.record, "why": decision.why,
                "observational": decision.observational, "decided_at": now, "config": vault.config,
            })
            if decision_id is not None and serving_on(vault.config) and not decision.refused:
                support = [ASK_NOW, *([WAIT] if decision.wait_feasible else []), NO_INTERVENTION]
                arm = {WAIT: objectives.ARM_WAIT, NO_INTERVENTION: objectives.ARM_NO_INTERVENTION}.get(
                    decision.chosen_ref, objectives.ARM_INSERT)
                objectives.record(
                    vault, repository, connection, decision_id=decision_id, decision_kind="plan_interrupt",
                    frozen=objectives.freeze_followup(str(row["learning_object_id"]), support=support), arm=arm,
                    clock=clock, exclude=set(),
                )
    except Exception:  # noqa: BLE001 - logging never blocks the learner's plan
        LOG.warning("follow-up decision not logged for %s", row["id"], exc_info=True)
    wf.set_fields(repository, str(row["id"]), chosen_ref=decision.chosen_ref, decision_id=decision_id, clock=clock)
    return replace(decision, decision_id=decision_id)


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
    "bind_plan_presentation", "decide", "hard_refusal", "observational", "record_decision", "record_outcome",
]
