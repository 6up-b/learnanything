"""The probe router's learner lane: the router decides whether the feedback screen offers the quick check.

At the probe router's tag (``algorithm_versions.probe_router_on``) the repair status is a read of facts
(``causal_orchestrator._routed``); when the facts leave an executable probe and no decision exists for the factor, its
status is ``pending`` and carries a :class:`learner_probe_proposal.Proposal`. :func:`decide` makes the factor's one
decision and records it (``router_decisions``, ``plan_interrupt`` on the ``causal_repair`` surface, receipt key the
factor's), then reads the status again, which now reads the decision back. A remount, a second read and the repair
entry all read the same decision: nothing is redrawn.

**The decision.** The probe is priced by :func:`router_objective.diagnostic_value.evaluate_probe` with the existing
instrument's channel, against repairing now, in the router objective's own terms, at the owner's decisions of
2026-11-20 (option f: decision 1 the conservative value, decision 2 the cause-class slopes for a covering repair and
practice's slope for an uncovered one, decision 3 no forced probe). The probe is **learned** when its information
value is positive at the learned slopes (the policy after its answer differs from the policy without it, and is worth
more): then it is an option of the mix, as any learned action, and the mix (the numeric policy's choice, the LLM policy
not asked on this lane so its share goes where a failed policy's goes, the exploration floor) draws between offering
it and not. **Unlearned** (no information at the learned slopes, a missing channel, or no valuation), it is no option
of the mix, which then has one option, and the same probe coin as the automatic lane's (``router_objective.probe_coin``:
its own seed, its own assignment row, the stop coin's rate) offers it on its share, with the served distribution
logged exactly.

The router's valuation reads the vault's frozen objective inputs (``objective_inputs.build``) with no plan needed:
the decision is the learner's, made where the learner reads the feedback.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import replace
import logging
from typing import Any

from learnloop.clock import Clock, utc_now_iso
from learnloop.ids import new_ulid
from learnloop.router.plan_log import NO_PROBE_REF, PROBE_REF, log_learner_probe_decision
from learnloop.router_objective import diagnostic_payload as DP

LOG = logging.getLogger(__name__)

#: The record's policy name for this lane's decisions.
POLICY = "probe_router_learner_v1"
#: The owner's decisions the valuation runs at (``diagnostic_payload.OwnerDecisions``): the values the G2 design
#: recommended, decided by the owner on 2026-11-20 (option f).
OWNER_DECISIONS = replace(DP.DESIGN_RECOMMENDATIONS, status="decided by the owner 2026-11-20 (option f)")
#: The LLM policy's status on this lane: its request is the plan's restraint card, which this lane does not build.
LLM_NOT_ASKED = "not_asked_on_this_lane"


def decide(vault: Any, repository: Any, *, misconception_id: str, session_id: str | None = None,
           clock: Clock | None = None) -> Any:
    """The repair status after the router has decided the factor's probe (where it had to): read, decide once if
    ``pending``, read again. Below the tag, or with nothing for the router to decide, the status as read."""

    from learnloop.diagnosis.causal_orchestrator import causal_repair_status

    status = causal_repair_status(vault, repository, misconception_id=misconception_id, session_id=session_id,
                                  start_repair=False, clock=clock)
    if status.router_state != "pending" or status.proposal is None:
        return status
    decide_proposal(vault, repository, status.proposal, clock=clock)
    return causal_repair_status(vault, repository, misconception_id=misconception_id, session_id=session_id,
                                start_repair=False, clock=clock)


def value(vault: Any, repository: Any, proposal: Any, *, now_iso: str, seed_identity: Mapping[str, Any]
          ) -> tuple[Any, dict[str, Any]]:
    """``(valuation, record)``: :func:`evaluate_probe`'s valuation of the proposal's probe against repairing now, or
    ``(None, record)`` with the reason none could be made (no topic, no payload, an error)."""

    from learnloop.daily_plan import objective_chooser as OC
    from learnloop.daily_plan import objective_inputs as OI
    from learnloop.daily_plan.types import BlockCandidate, PlanState
    from learnloop.diagnosis.learner_probe_proposal import PROBE_ACTION_REF, diagnostic_payload
    from learnloop.router_objective import types as OT
    from learnloop.router_objective.diagnostic_value import evaluate_probe

    payload = diagnostic_payload(vault, repository, proposal)
    if isinstance(payload, str):
        return None, {"status": "no_payload", "reason": payload}
    lo = payload.topic
    # The repair block the valuation's topics and duration spread are read for; the plan is not needed (no plan id:
    # the remembered minutes are "missing", as on any decision outside a plan).
    repair = BlockCandidate(candidate_id="repair", lane="repair", action="practice", subtype="completion_or_repair",
                            learning_object_ids=(lo,), item_ids=(), reading=None,
                            est_minutes=float(proposal.repair_minutes), planner_value=0.0,
                            reason="the repair the cause set names", annotations={})
    state = PlanState(plan_id="", kind="normal", minutes_budget=0.0, minutes_left=0.0, lane_minutes_left={},
                      days_since_last_activity=0, streak_days=0, current_block_id=None)
    config = vault.config
    section = config.router_objective
    seed = OC.numeric_seed(seed_identity)
    inputs, actions, sources = OI.build(vault, repository, state=state, support=["repair"],
                                       candidates={"repair": repair}, now_iso=now_iso)
    spread = float(actions[0].minutes_log_sd) if actions else 0.0
    priced, _frontier = OC.day_price(repository, inputs, local_date=OC._local_date(now_iso),
                                     draws=int(section.rollout_theta_draws_max), seed=seed, config=config)
    inputs = replace(inputs, price=replace(inputs.price, kappa0=priced.kappa0, regime=priced.regime))
    payload = replace(payload, repairs=tuple(replace(option, action=replace(option.action, minutes_log_sd=spread))
                                             for option in payload.repairs))
    probe = OT.Action(ref=PROBE_ACTION_REF, kind=OT.PROBE, item_los=(lo,),
                      minutes=float(proposal.reads.probe_burden_minutes), minutes_log_sd=spread, diagnostic=payload)
    valuation = evaluate_probe(inputs, probe, decisions=OWNER_DECISIONS, draws=int(section.rollout_theta_draws),
                               seed=seed, wait_feasible=True)
    return valuation, {"status": "valued", "price": {"kappa0": priced.kappa0, "how": priced.how},
                       "topics": len(inputs.topics), "topic_sources": sources.get("topics", {}).get(lo)}


def information(valuation: Any) -> float:
    """The probe's information value at the learned slopes: the policy after its answer against the prior's choice
    after the same probe (``evaluate_probe``'s ``values.information``; 0 when no result changes the choice)."""

    if valuation is None:
        return 0.0
    return float((valuation.record.get("values") or {}).get("information") or 0.0)


def decide_proposal(vault: Any, repository: Any, proposal: Any, *, clock: Clock | None = None) -> str | None:
    """Decide the proposal's probe once and record it; returns the factor's decision id (an earlier one when a
    concurrent read recorded it first)."""

    from learnloop.daily_plan import objective_chooser as OC
    from learnloop.diagnosis.learner_probe_proposal import PROBE_ACTION_REF
    from learnloop.router_objective import choose as C
    from learnloop.router_objective import mix
    from learnloop.router_objective import probe_coin as PC
    from learnloop.router_objective_switches import failure_share_to_other_policy_on

    config = vault.config
    now_iso = utc_now_iso(clock)
    decision_id = new_ulid()
    key = f"learner_probe:{proposal.factor_id}"
    identity = {"kind": "learner_probe", "factor": proposal.factor_id, "candidate": proposal.chosen.get("id"),
                "version": config.algorithms.algorithm_version}
    try:
        valuation, value_record = value(vault, repository, proposal, now_iso=now_iso, seed_identity=identity)
    except Exception as exc:  # the decision still stands: a probe the router could not value is unlearned
        LOG.warning("probe router: the learner lane's valuation failed for factor %s", proposal.factor_id,
                    exc_info=True)
        valuation, value_record = None, {"status": "failed", "error": type(exc).__name__}
    gained = information(valuation)
    learned = gained > 0.0
    detail: dict[str, Any] = {
        "factor_id": proposal.factor_id, "misconception_id": proposal.misconception_id,
        "candidate_id": proposal.chosen.get("id"), "learning_object_id": proposal.learning_object_id,
        "policy": POLICY, "learned": learned, "information": gained, "valuation": value_record,
        "facts": proposal.facts(), "support": [NO_PROBE_REF, PROBE_REF],
    }
    if valuation is not None:
        detail["evaluation"] = {key_: valuation.record.get(key_) for key_ in
                                ("version", "decisions", "values", "choice", "results", "prior_choice",
                                 "policy_changes_with_result", "channel_use", "excluded", "cost")}
        detail["evaluation"]["numeric_choice"] = valuation.choice
    pending: list[dict[str, Any]] = []
    if learned:
        # A learned probe is an option of the mix like any learned action.
        numeric = PROBE_REF if valuation.choice == PROBE_ACTION_REF else NO_PROBE_REF
        w, weight_record = OC.current_weight(repository, config, at=now_iso)
        to_other = failure_share_to_other_policy_on(config)
        seed = mix.seed_for(key, decision_id)
        epsilon = float(config.router.epsilon_min)
        choice = C.post_miss_choice(C.PostMissInputs(
            support=(NO_PROBE_REF, PROBE_REF), staged_ref=NO_PROBE_REF, wait_ref=NO_PROBE_REF, per_option=True,
            llm_status=LLM_NOT_ASKED, llm_options=None, llm_option_rationale=None, llm_p_yes=None, llm_rationale=None,
            numeric_status=C.ANSWERED, numeric_choice=numeric, w=w, to_other_policy=to_other, epsilon=epsilon,
            seed=seed))
        served, propensity, served_pi = choice.drawn.chosen, choice.propensity, dict(choice.drawn.pi)
        detail["mixture"] = {"design": mix.DESIGN, "policy": mix.POLICY, "seed": seed, "boundary_key": key,
                             "support": [NO_PROBE_REF, PROBE_REF], "staged_ref": NO_PROBE_REF, "epsilon": epsilon,
                             "w": w, "weight": weight_record, "effective_weights": dict(choice.effective),
                             "failed": list(choice.failed), "fallback": mix.fallback_label(choice.failed),
                             "fallback_reasons": {name: LLM_NOT_ASKED for name in choice.failed},
                             "failure_rule": mix.failure_rule_name(to_other), "numeric_choice": choice.numeric_choice,
                             "drawn_component": choice.drawn.component, "u1": choice.drawn.u1, "u2": choice.drawn.u2,
                             "pi": served_pi}
    else:
        # An unlearned probe is no option of the mix: the mix has one option (no probe), and the probe coin offers
        # the probe on its share.
        mu = {NO_PROBE_REF: 1.0}
        rate = PC.share(config)
        served, propensity, served_pi = NO_PROBE_REF, 1.0, dict(mu)
        if PC.applies(rate):
            coin_seed = PC.seed_for(key, decision_id)
            coin = PC.flip(coin_seed, rate, probe_ref=PROBE_REF, mu=mu, drawn=NO_PROBE_REF, boundary_key=key)
            served, propensity = coin.served, coin.served_propensity
            served_pi = PC.served_distribution(mu, rate, probe_ref=PROBE_REF)
            detail["probe_coin"] = coin.as_dict()
            pending.append(PC.pending_assignment(coin, seed=coin_seed, support=[PROBE_REF, NO_PROBE_REF]))
    detail["served_pi"] = served_pi
    with repository.atomic(), repository.connection() as connection:
        recorded = log_learner_probe_decision(connection, {
            "decision_id": decision_id, "factor_id": proposal.factor_id, "chosen_ref": served,
            "propensity": propensity, "served_pi": served_pi, "practice_item_id": proposal.practice_item_id,
            "learning_object_id": proposal.learning_object_id, "session_id": proposal.session_id,
            "policy": POLICY, "mode": "probe_router", "detail": detail, "decided_at": now_iso, "config": config,
        })
        if recorded == decision_id and pending:
            from learnloop.router_objective import assignments as ro5_assignments

            ro5_assignments.record_pending(connection, pending, unit_id=decision_id, at=now_iso)
    return recorded


__all__ = ["LLM_NOT_ASKED", "OWNER_DECISIONS", "POLICY", "decide", "decide_proposal", "information", "value"]
