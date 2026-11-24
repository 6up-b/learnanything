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

**The job.** The sidecar's status read makes no decision: it reads the facts (recording their receipt
once, as every status read does) and answers ``pending``; the valuation and the decision run in the sidecar's worker
(:func:`run_pending`), off the serial request loop, and a later read shows the decision. The queue is durable with no
table of its own: a factor is waiting (:func:`requested`) while its latest receipt is the router's pending read and no
decision exists on it, so a process that ends before its job ran finds it again at the next start. The job reads the
status again before it decides, so a refusal made meanwhile is honoured, and its own read records the status it found.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import replace
import logging
from typing import Any

from learnloop.clock import Clock, utc_now_iso
from learnloop.diagnosis.learner_probe_proposal import CHANNEL_SOURCE
from learnloop.ids import new_ulid
from learnloop.router.plan_log import NO_PROBE_REF, PROBE_REF, log_learner_probe_decision
from learnloop.router_objective import diagnostic_payload as DP
from learnloop.router_objective import types as OT
from learnloop.router_objective.miss_cause import CLASSES

LOG = logging.getLogger(__name__)

#: The record's policy name for this lane's decisions.
POLICY = "probe_router_learner_v1"
#: The owner's decisions the valuation runs at (``diagnostic_payload.OwnerDecisions``): the values the G2 design
#: recommended, decided by the owner on 2026-11-20 (option f).
OWNER_DECISIONS = replace(DP.DESIGN_RECOMMENDATIONS, status="decided by the owner 2026-11-20 (option f)")
#: The LLM policy's status on this lane: its request is the plan's restraint card, which this lane does not build.
LLM_NOT_ASKED = "not_asked_on_this_lane"


def decide(vault: Any, repository: Any, *, misconception_id: str, session_id: str | None = None,
           clock: Clock | None = None, factor_id: str | None = None, attempt_id: str | None = None) -> Any:
    """The repair status after the router has decided the factor's probe (where it had to): read, decide once if
    ``pending``, read again. Below the tag, or with nothing for the router to decide, the status as read. The factor
    is the one the caller shows (``factor_id``, else the one on ``attempt_id``; ``causal_repair_status``)."""

    from learnloop.diagnosis.causal_orchestrator import causal_repair_status

    from learnloop.algorithm_versions import probe_router_on

    if not probe_router_on(vault.config):
        return causal_repair_status(vault, repository, misconception_id=misconception_id, session_id=session_id,
                                    start_repair=False, clock=clock, factor_id=factor_id, attempt_id=attempt_id)
    # The router's own read records no receipt: the status it serves after deciding records its facts once.
    status = causal_repair_status(vault, repository, misconception_id=misconception_id, session_id=session_id,
                                  start_repair=False, clock=clock, record_receipt=False, factor_id=factor_id,
                                  attempt_id=attempt_id)
    if status.router_state == "pending" and status.proposal is not None:
        decide_proposal(vault, repository, status.proposal, clock=clock)
    return causal_repair_status(vault, repository, misconception_id=misconception_id, session_id=session_id,
                                start_repair=False, clock=clock, factor_id=status.factor_id or factor_id,
                                attempt_id=attempt_id)


def requested(repository: Any) -> list[dict[str, Any]]:
    """The factors waiting on the router's decision, oldest first: an open factor whose latest receipt is the
    router's pending read (``router_decides``, ``needs_disambiguation``) and that has no decision of either lane. Each
    is ``factor_id``, ``misconception_id`` and the ``session_id`` the read was made in."""

    import json

    from learnloop.diagnosis.causal_orchestrator import ROUTER_DECIDES
    from learnloop.router.plan_log import automatic_probe_decision, learner_probe_decision

    latest: dict[str, dict[str, Any]] = {}
    with repository.connection() as connection:
        rows = connection.execute(
            "SELECT r.factor_id, r.misconception_id, r.decision, r.repair_status, r.inputs_json, r.created_at "
            "FROM causal_probe_decision_receipts r JOIN unresolved_cause_factors f ON f.id = r.factor_id "
            "WHERE f.status = 'open' ORDER BY r.created_at, r.rowid").fetchall()
        for row in rows:
            latest[str(row["factor_id"])] = dict(row)
        waiting = []
        for factor_id, row in latest.items():
            if row["decision"] != ROUTER_DECIDES or row["repair_status"] != "needs_disambiguation":
                continue
            if learner_probe_decision(connection, factor_id) or automatic_probe_decision(connection, factor_id):
                continue
            inputs = json.loads(row["inputs_json"] or "{}")
            waiting.append({"factor_id": factor_id, "misconception_id": str(row["misconception_id"] or ""),
                            "session_id": inputs.get("session_id"), "at": str(row["created_at"])})
    return sorted(waiting, key=lambda value: (value["at"], value["factor_id"]))


def run_pending(vault: Any, repository: Any, *, clock: Clock | None = None, max_jobs: int = 100) -> list[str]:
    """The decision job: decide each waiting factor (:func:`requested`) once, reading its status again first.
    Returns the factors it ran. One factor's failure is logged and leaves the rest to run; a factor whose decision
    could not be recorded stays waiting for the next run."""

    from learnloop.diagnosis.causal_reads import CausalRepairError

    ran: list[str] = []
    for request in requested(repository)[:max_jobs]:
        try:
            decide(vault, repository, misconception_id=request["misconception_id"], session_id=request["session_id"],
                   factor_id=request["factor_id"], clock=clock)
        except CausalRepairError:
            continue  # no longer an open factor of its cause: nothing to decide
        except Exception:  # noqa: BLE001 - a job never dies on one factor
            LOG.warning("probe router: the decision job failed for factor %s", request["factor_id"], exc_info=True)
            continue
        ran.append(request["factor_id"])
    return ran


def _cause_class(repository: Any, hypothesis_id: str) -> str:
    row = repository.causal_hypothesis(hypothesis_id)
    scope = str((row or {}).get("cause_scope") or "")
    return scope if scope in CLASSES else DP.UNKNOWN


def _channel(vault: Any, repository: Any, item: Any, hypothesis_set: Any, labels: list[str]) -> DP.Channel | DP.MissingChannel:
    from learnloop.diagnosis.probe_episodes import resolve_instrument
    from learnloop.diagnosis.probe_families import instrument_conditionals
    from learnloop.diagnosis.voi_stopping import label_conditionals

    resolved = resolve_instrument(vault, repository, item, hypothesis_set)
    if resolved is None:
        return DP.MissingChannel("no_instrument_binding")
    instrument, slot_map = resolved
    rows = label_conditionals(instrument_conditionals(instrument), slot_map, labels)
    if any(label not in rows for label in labels):
        return DP.MissingChannel("hypothesis_without_row")
    results = tuple(dict.fromkeys(str(outcome) for label in labels for outcome in rows[label]))
    table = []
    for label in labels:
        row = {str(outcome): float(p) for outcome, p in rows[label].items()}
        total = sum(row.values())
        if total <= 0.0:
            return DP.MissingChannel("row_without_mass")
        # The composed rows are distributions up to float rounding; dividing by the sum keeps them so exactly.
        table.append((label, tuple(row.get(result, 0.0) / total for result in results)))
    version = ":".join(str(part) for part in (instrument.card_id, instrument.card_version,
                                              instrument.family_template_id, instrument.family_template_version,
                                              instrument.compiled_likelihood_hash()))
    return DP.Channel(results=results, rows=tuple(table), version=version,
                      source=f"{CHANNEL_SOURCE}:{instrument.provenance}")


def diagnostic_payload(vault: Any, repository: Any, proposal: Any) -> DP.DiagnosticProbe | str:
    """The probe's diagnostic payload, or why none can be built (a string): the locked set's hypotheses at its prior,
    each with its cause class; the instrument's channel or its typed absence; one repair option per repair class,
    covering the hypotheses mapped to it. The repairs' and the probe's durations are set by the router, which reads
    the vault's duration spread."""

    from learnloop.diagnosis.probes import HypothesisSet

    chosen = proposal.chosen
    lo = proposal.learning_object_id
    if not lo or not chosen.get("hypothesis_set_id") or not proposal.practice_item_id:
        return "no_locked_set_or_item"
    record = repository.fetch_hypothesis_set(str(chosen["hypothesis_set_id"]))
    if record is None:
        return "locked_set_missing"
    hypothesis_set = HypothesisSet.from_record(record)
    item = vault.practice_items.get(proposal.practice_item_id)
    if item is None:
        return "probe_item_missing_from_vault"
    labels = [str(h.label) for h in hypothesis_set.hypotheses]
    prior = {str(key): float(value) for key, value in hypothesis_set.prior.items()}
    hypotheses = tuple(DP.Hypothesis(label, max(prior.get(label, 0.0), 0.0), _cause_class(repository, label))
                       for label in labels)
    if sum(h.prior for h in hypotheses) <= 0.0:
        return "locked_prior_without_mass"
    classes = sorted({str(value) for value in proposal.repair_class_by_hypothesis.values() if value})
    # Each repair's own minutes, with their source (authored, pooled latency, else the seeded default), never one
    # fallback for every class.
    from learnloop.diagnosis.causal_diagnostic_selector import duration_estimates_for_repair_classes

    durations = duration_estimates_for_repair_classes(repository, classes)
    repairs = []
    for repair_class in classes:
        covers = frozenset(h for h, value in proposal.repair_class_by_hypothesis.items()
                           if value == repair_class and h in labels)
        if not covers:
            continue
        estimate = durations.get(repair_class) or {}
        minutes = float(estimate.get("minutes") or proposal.repair_minutes)
        action = OT.Action(ref=repair_class, kind=OT.REPAIR, item_los=(lo,), minutes=minutes)
        repairs.append(DP.RepairOption(repair_class, action, covers,
                                       source=f"cause_set_repair_class; minutes: "
                                              f"{estimate.get('source') or 'orchestrator_default'}"))
    return DP.DiagnosticProbe(
        topic=lo,
        hypotheses=hypotheses,
        prior_basis=proposal.reads.prior_basis or "locked_set_prior",
        channel=_channel(vault, repository, item, hypothesis_set, labels),
        repairs=tuple(repairs),
        source=(("attempt", str(proposal.attempt_id or "")), ("factor", proposal.factor_id),
                ("candidate", str(chosen.get("id") or "")), ("item", proposal.practice_item_id),
                ("origin", "learner_lane")),
        facts=tuple(sorted(proposal.facts().items())),
    )


def value(vault: Any, repository: Any, proposal: Any, *, now_iso: str, seed_identity: Mapping[str, Any]
          ) -> tuple[Any, dict[str, Any]]:
    """``(valuation, record)``: :func:`evaluate_probe`'s valuation of the proposal's probe against repairing now, or
    ``(None, record)`` with the reason none could be made (no topic, no payload, an error)."""

    from learnloop.daily_plan import objective_chooser as OC
    from learnloop.daily_plan import objective_inputs as OI
    from learnloop.daily_plan.types import BlockCandidate, PlanState
    from learnloop.diagnosis.learner_probe_proposal import PROBE_ACTION_REF
    from learnloop.router_objective.diagnostic_value import evaluate_probe

    from learnloop.diagnosis.probe_episodes import known_exposure

    payload = diagnostic_payload(vault, repository, proposal)
    if isinstance(payload, str):
        return None, {"status": "no_payload", "reason": payload}
    lo = payload.topic
    # Known exposure at the decision, with the answer admission's own scope (the item and its learning object): an
    # answer that admission will refuse separates no cause, so the probe earns no information.
    exposed_by = known_exposure(vault, repository, practice_item_id=str(proposal.practice_item_id),
                                learning_object_id=lo, at=now_iso)
    payload = replace(payload, exposed=exposed_by is not None)
    exposure = {"exposed": exposed_by is not None, "reason": exposed_by, "scope": "item_and_learning_object",
                "at": now_iso}
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
    # The chooser's own rollout options, for the probe's valuation as for the day's price.
    options = OC.rollout_options(config)
    draws = int(section.rollout_theta_draws)
    valuation = evaluate_probe(inputs, probe, decisions=OWNER_DECISIONS, draws=draws, seed=seed, wait_feasible=True,
                               **options)
    # Frozen for replay: the whole unrounded inputs and the probe action as valued, the seed, the draw count and the
    # options; ``replay`` is the lossless payload :func:`revalue` values again from the stored row alone, the rest
    # its readable view.
    from dataclasses import asdict

    from learnloop.router_objective import check_replay

    replay = check_replay.record(inputs, (probe,), seed=seed, draws=draws, first_draws=draws, max_draws=draws,
                                 as_of=now_iso, options=options,
                                 versions={"policy": valuation.record.get("version"), "lane": POLICY},
                                 sensors={})
    return valuation, {"status": "valued", "exposure": exposure, "price": {"kappa0": priced.kappa0, "how": priced.how},
                       "topics": len(inputs.topics), "topic_sources": sources.get("topics", {}).get(lo),
                       "frozen": {"inputs": asdict(inputs), "probe_minutes": probe.minutes,
                                  "probe_minutes_log_sd": probe.minutes_log_sd, "payload": payload.summary(),
                                  "seed": seed, "draws": draws, "rollout_options": dict(options),
                                  "policy_version": valuation.record.get("version"), "replay": replay}}


def revalue(replay: Mapping[str, Any]) -> Any:
    """The decision's probe valued again from its stored replay payload alone (``frozen.replay``): the same inputs,
    probe, seed, draws and options, at the owner's decisions the lane values with. No vault, repository or config is
    read, so a decision's numbers can be checked after any later recalibration."""

    from learnloop.router_objective import check_replay
    from learnloop.router_objective.diagnostic_value import evaluate_probe

    body = check_replay.read(replay)
    (probe,) = body["proposed_actions"]
    return evaluate_probe(body["inputs"], probe, decisions=OWNER_DECISIONS, draws=int(body["draws"]),
                          seed=str(body["seed"]), wait_feasible=True, **dict(body["options"]))


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

    from learnloop.router.plan_log import automatic_probe_decision

    with repository.connection() as connection:
        automatic = automatic_probe_decision(connection, proposal.factor_id)
    if automatic is not None:
        # The automatic lane decided this factor's probe since the status was read: its decision is
        # the factor's one decision, and no second draw is made.
        return str(automatic["id"])
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
                                ("version", "decisions", "given", "values", "choice", "results", "prior_choice",
                                 "policy_changes_with_result", "channel_use", "excluded", "cost")}
        detail["evaluation"]["numeric_choice"] = valuation.choice
    pending: list[dict[str, Any]] = []
    if learned:
        # A learned probe is an option of the mix like any learned action.
        numeric = PROBE_REF if valuation.choice == PROBE_ACTION_REF else NO_PROBE_REF
        w, weight_record = OC.current_weight(repository, config, at=now_iso)
        to_other = failure_share_to_other_policy_on(config)
        # Seeded by the factor, not the decision's id: a retry after a crash, or a concurrent read, draws the same
        #.
        seed = mix.seed_for(key, "learner_probe")
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
            coin_seed = PC.seed_for(key, "learner_probe")
            coin = PC.flip(coin_seed, rate, probe_ref=PROBE_REF, mu=mu, drawn=NO_PROBE_REF, boundary_key=key)
            served, propensity = coin.served, coin.served_propensity
            served_pi = PC.served_distribution(mu, rate, probe_ref=PROBE_REF)
            detail["probe_coin"] = coin.as_dict()
            pending.append(PC.pending_assignment(coin, seed=coin_seed, support=[PROBE_REF, NO_PROBE_REF]))
    detail["served_pi"] = served_pi
    try:
        with repository.atomic(), repository.connection() as connection:
            recorded = log_learner_probe_decision(connection, {
                "decision_id": decision_id, "factor_id": proposal.factor_id, "chosen_ref": served,
                "propensity": propensity, "served_pi": served_pi, "practice_item_id": proposal.practice_item_id,
                "learning_object_id": proposal.learning_object_id, "session_id": proposal.session_id,
                "policy": POLICY, "mode": "probe_router", "detail": detail, "decided_at": now_iso, "config": config,
            })
            if recorded is None:
                raise RuntimeError("the decision was not logged")
            if recorded == decision_id and pending:
                from learnloop.router_objective import assignments as ro5_assignments

                written = ro5_assignments.record_pending(connection, pending, unit_id=decision_id, at=now_iso)
                if len(written) != len(pending):
                    # The decision and its coin's assignment commit together or not at all.
                    raise RuntimeError("the probe coin's assignment was not written")
            if recorded == decision_id and proposal.learning_object_id:
                # One outcome target for both arms, frozen before either is executed: the factor's
                # learning object, whichever was drawn, as the automatic lane's decision freezes its own. The probe
                # arm's own answer is still bound only by an acceptance's pin.
                from learnloop.daily_plan import measurement as objectives

                support = [ref for ref in (NO_PROBE_REF, PROBE_REF) if float(served_pi.get(ref, 0.0)) > 0.0]
                objectives.record(vault, repository, connection, decision_id=decision_id, decision_kind="plan_interrupt",
                                  frozen=objectives.freeze_followup(str(proposal.learning_object_id), support=support),
                                  arm=objectives.ARM_INSERT if served == PROBE_REF else objectives.ARM_NO_INTERVENTION,
                                  clock=clock, exclude=set())
    except Exception:  # noqa: BLE001 - an unrecorded decision offers nothing: the status stays pending
        LOG.warning("probe router: the learner lane's decision was not recorded for factor %s", proposal.factor_id,
                    exc_info=True)
        return None
    return recorded


__all__ = ["LLM_NOT_ASKED", "OWNER_DECISIONS", "POLICY", "decide", "decide_proposal", "diagnostic_payload", "information",
           "requested", "revalue", "run_pending", "value"]
