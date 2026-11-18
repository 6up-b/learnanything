"""The objective router's decision trace, assembled: what one decision read, valued and drew, so its terms and its
probabilities recompute from the trace alone. :mod:`learnloop.router_objective.trace` turns the dict into the
``router_objective_traces`` row (``assemble``) and reads it back in plain words (``explain``); this module builds the
dict.

:func:`objective_trace` assembles a block boundary's trace from the choice (:mod:`learnloop.router_objective.choose`)
and the reads the chooser already holds (the numeric policy's answer, the models' results, the weight, the seed, the
LLM's card, the carried valuations); :func:`decision_trace` is its common part, which the mid-block decisions use too.
Each option in the support supplies its own row (:func:`candidate_row`): stop, a block or a lesson offer, told apart by
the option's own fields.

The plan and this module read the same option refs and subtype from ``types``. The numeric answer, the models'
results and the candidates are read by their attributes. It is apart from ``trace`` because the trace's own pieces
(the learned tail's terms, the preferences' values) import ``tail_data``, which imports ``trace``: in one module they
would make an import cycle.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import timedelta
import math
from typing import Any

from learnloop.clock import parse_utc
from learnloop.router import requests as rq
from learnloop.router_objective import mix
from learnloop.router_objective import price as P
from learnloop.router_objective import stop_coin as SC
from learnloop.router_objective import ad_link as ADL
from learnloop.router_objective import objective as OBJ
from learnloop.router_objective import rollouts as ROL
from learnloop.router_objective import types as OT
from learnloop.router_objective.types import LESSON_OFFER_SUBTYPE, STOP_FOR_TODAY
from learnloop.router_objective.choose import ANSWERED, NOT_READY
from learnloop.router_objective_switches import failure_share_to_other_policy_on

#: The source key ``daily_plan.objective_inputs`` uses for the miss-cause sensor.
MISS_CAUSE_SOURCE = "miss_cause"
#: The kinds of option a support holds, as their rows tell them apart.
STOP, LESSON_OFFER, BLOCK = "stop", LESSON_OFFER_SUBTYPE, "block"


def option_kind(ref: str, candidate: Any) -> str | None:
    """Stop, a lesson offer or a block, from the option's own fields; None for a ref with no candidate."""

    if ref == STOP_FOR_TODAY:
        return STOP
    if candidate is None:
        return None
    return LESSON_OFFER if OT.is_offer_subtype(candidate.subtype) else BLOCK


def option_label(kind: str | None, candidate: Any, titles: Mapping[str, str]) -> str | None:
    """The option's plain label in the trace."""

    match kind:
        case "stop":
            return "stop for today"
        case OT.LESSON_OFFER_SUBTYPE:
            topic = ", ".join(dict.fromkeys(titles.get(lo, lo) for lo in candidate.learning_object_ids))
            return f"offer a lesson on {topic} (about {max(1, round(candidate.est_minutes))} min)"
        case "block":
            what = candidate.reading.section_title if candidate.reading is not None else ", ".join(
                dict.fromkeys(titles.get(lo, lo) for lo in candidate.learning_object_ids)) or candidate.lane
            return f"{candidate.lane}: {what} ({max(1, round(candidate.est_minutes))} min)"
    return None

def candidate_row(ref: str, candidate: Any, *, titles: Mapping[str, str], valued: Any, action: Any, numeric: Any,
                  topic_by_lo: Mapping[str, Any], miss_cause: Mapping[str, Any] | None,
                  miss_topics: Mapping[str, Any], llm: Any, llm_parsed: Any, v: float | None, stop_q: float | None,
                  top: Any, residual_applied: bool) -> dict[str, Any]:
    """One option's row: its label, the numeric policy's action and terms for it, the sensors those read, the LLM's
    forecast for it, and, for a lesson offer, the offer's own section (:func:`_offer_trace`)."""

    kind = option_kind(ref, candidate)
    label = option_label(kind, candidate, titles)
    sensors = {}
    for lo in dict.fromkeys(action.item_los if action is not None else ()):
        topic = topic_by_lo.get(lo)
        if topic is None:
            continue
        sensors[lo] = {"ad_eta": topic.eta_mean, "ad_eta_var": topic.eta_var, "fsrs_stability": topic.stability,
                       "fsrs_elapsed_days": topic.elapsed_days, "practiced": topic.practiced,
                       "source": ((numeric.sources if numeric is not None else {}).get("topics") or {}).get(lo),
                       "reached_qbar": True}
        if lo in miss_topics:
            # The miss's cause, beside the topic's other sensors. It reaches Q̄ only with the cause in the value and a
            # diagnosis in force (the split's record, ``miss_cause.in_value``, says how).
            sensors[lo]["miss_cause"] = {
                **dict(miss_topics[lo]),
                "reached_qbar": bool((miss_cause or {}).get("in_value"))
                and lo in (((miss_cause or {}).get("in_value") or {}).get("topics") or {})}
    if isinstance(llm_parsed, rq.ParsedPolicy) and ref in llm_parsed.forecasts:
        sensors["llm_forecast"] = {**dict(llm_parsed.forecasts[ref]), "schema": rq.LLM_POLICY_SCHEMA,
                                   "model": getattr(llm, "model", None),
                                   "reached_qbar": bool(numeric is not None and numeric.corrected)}
    terms = None
    if valued is not None:
        terms = {**dict(valued.terms), "q": valued.q,
                 "q_minus_v": (valued.q - v) if v is not None else None,
                 "q_minus_stop": (valued.q - stop_q) if stop_q is not None else None,
                 "paired_se_vs_top": OBJ.paired_standard_error(top, valued) if top is not None and top.ref != ref else 0.0}
        if residual_applied:
            # The learned tail's ŵ, V_tail (the tail's Q̄ above), V_residual and Ṽ for this option.
            from learnloop.router_objective import tail_serve

            terms.update(tail_serve.candidate_terms(numeric.residual, ref, valued.q))  # type: ignore[union-attr, arg-type]
    row: dict[str, Any] = {
        "label": label if label is not None else ref, "kind": action.kind if action is not None else None,
        # The option's main topic, the one the LLM policy's forecasts are about (§8.9's binding).
        "main_lo": (action.item_los[0] if action is not None and action.item_los else None),
        "minutes": action.minutes if action is not None else None, "sensors": sensors, "terms": terms,
        "split": ({"learning": None, "information": valued.extra.get("information"),
                   "return_effect": valued.extra["return_effect"], "return_model": valued.extra.get("return_model"),
                   "note": "display only, never added: the return effect is the return model's difference to "
                           "stopping now, inside the accepted branch's transition"}
                  if valued is not None and "return_effect" in valued.extra else
                  {"learning": None, "information": (valued.extra.get("information") if valued is not None else None),
                   "return_effect": 0.0, "note": "display only, never added; the return effect is zero until RO5 "
                                                 "fits a return model"}),
        "branches": dict(valued.extra.get("branches") or {}) if valued is not None else None,
    }
    if kind == LESSON_OFFER:
        # A lesson offer's own section: its sensors, its branches' terms and the split.
        row["offer"] = _offer_trace(candidate, valued, action, numeric.inputs if numeric is not None else None,
                                    topic_by_lo, row.get("terms"))
    return row


def _serving_switches(config: Any) -> dict[str, Any]:
    """The trace's ``versions.serving_switches`` (landing ruling R8), or nothing below the batch's tag."""

    from learnloop.router_objective_switches import followup_generator_switches

    switches = followup_generator_switches(config) if config is not None else None
    return {"serving_switches": switches} if switches is not None else {}


def _score_note(config: Any) -> str:
    from learnloop.router_objective_switches import CHECKS_OFF, check_mode

    if check_mode(config)[0] != CHECKS_OFF:
        return ("forms when the window closes, from the randomized checks it holds (r = the day's assignment "
                "probability x the running completion rate)")
    return "none forms until RO5's randomized checks: no valued use has r > 0"


def goal_dates(numeric: Any) -> dict[str, Any]:
    """RO5 §9 item 3's sensor input: each active dated goal's uses with the memory model's frozen forecast at the
    goal's date (``m⁰``, from the pre-action belief under the tail, the same number the policy comparison logs) and
    the goal's absolute ``due_at``, for every dated goal the rollouts value, beyond the evaluation window too
    (Codex review F7). A date past the tail's horizon has no forecast and says so."""

    inputs = numeric.inputs if numeric is not None else None
    if inputs is None:
        return {"uses": [], "status": "no_inputs"}
    baselines = (numeric.baselines or {}).get("dated") or {} if numeric is not None else {}
    goals = (numeric.sources or {}).get("goals") or {} if numeric is not None else {}
    uses = []
    for use in inputs.dated:
        m0 = baselines.get(f"{use.goal_id}:{use.lo}")
        uses.append({"goal_id": use.goal_id, "lo": use.lo, "at_days": use.at_days,
                     "due_at": (goals.get(use.goal_id) or {}).get("due_at"), "m0": m0,
                     **({} if m0 is not None else {"status": "no_forecast_beyond_horizon"})})
    return {"uses": uses, "horizon_days": float(inputs.horizon_days),
            "basis": "the pre-action belief under the tail, at each goal's date (sensor for the goal-date read)"}


def _offer_trace(candidate: Any, valued: Any, action: Any, inputs: Any,
                 topic_by_lo: Mapping[str, Any], terms: Mapping[str, Any] | None) -> dict[str, Any]:
    """Teacher TE3b (spec_teacher_v1 rev 5 §15.1a, "what the trace records"): for a lesson offer, its sensors
    (``P(accept)`` with its posterior mean and sd and the priors version, the reason, AD's ``p̄`` for the target, the
    lesson curve's moments and version or ``placeholder``, the lesson-check mass posterior, the duration and its
    source), its terms (each branch's ``Q̄``, ``p``, the accepted branch's κ integral of the lesson's minutes, its
    ``E[V(x′)]`` with the delayed checks and ``T_C``, ``Q̄ − Q̄(stop)``, the residual's ``V_residual``) and the
    split (display only). The binding (decision → response → lesson → receipt → delayed checks) is a read over
    existing ids at print time (``learnloop router trace``)."""

    record = dict((candidate.annotations or {}).get("lesson_offer") or {})
    lo = str(record.get("learning_object_id") or (candidate.learning_object_ids or ("",))[0])
    topic = topic_by_lo.get(lo)
    curve = inputs.learning.lesson if inputs is not None else None
    extra = dict(getattr(valued, "extra", None) or {})
    branches = dict(extra.get("branches") or {})
    branch_terms = dict(extra.get("branch_terms") or {})
    accepted = dict(branch_terms.get("accepted") or {})
    declined = dict(branch_terms.get("declined") or {})
    p_bar = (1.0 / (1.0 + math.exp(-float(topic.eta_mean)))) if topic is not None else None
    return {
        "version": record.get("version"),
        "sensors": {
            "p_accept": {**dict(record.get("p_accept") or {}), "priors_version": record.get("priors_version"),
                         "updates": (record.get("model") or {}).get("updates"),
                         # IH4: how many of those were requests with no offer on screen (only when any were).
                         **({"unprompted_updates": (record.get("model") or {})["unprompted_updates"]}
                            if (record.get("model") or {}).get("unprompted_updates") else {})},
            "reason": record.get("reason"), "context": record.get("context"),
            "ad_p_bar": p_bar,
            "lesson_curve": ({"version": curve.version, "mean": list(curve.mean), "cov": [list(r) for r in curve.cov],
                              "position": dict(curve.positions).get(lo, 0.0)} if curve is not None
                             else "placeholder"),
            "check_mass": record.get("mass"), "duration": record.get("duration"), "checks": record.get("checks"),
            "ceiling": record.get("ceiling"),
        },
        "terms": {
            "q_accepted": branches.get("accepted"), "q_declined": branches.get("declined"),
            "p": branches.get("p_accept"), "p_sd": branch_terms.get("p_accept_sd"),
            "kappa_integral_accepted": accepted.get("kappa_integral"),
            "after_accepted": accepted.get("after"), "terminal_accepted": accepted.get("terminal"),
            "after_declined": declined.get("after"),
            "q_minus_stop": (terms or {}).get("q_minus_stop"), "v_residual": (terms or {}).get("v_residual"),
        },
        "split": {"learning": None, "information": None, "return_effect": 0.0,
                  "note": "display only, never added: the accepted branch's learning and its checks' information are "
                          "inside its E[V(x')]"},
        "alternatives": [entry.get("ref") for entry in list((record.get("card") or {}).get("candidates") or [])[1:]],
        "action": {"minutes": getattr(action, "minutes", None), "minutes_log_sd": getattr(action, "minutes_log_sd", None),
                   "mass": getattr(action, "mass", None), "accept": list(getattr(action, "accept", None) or ()),
                   "commitments": [list(c) for c in getattr(action, "commitments", ()) or ()]},
    }


def failure_rule_field(to_other: bool) -> dict[str, str]:
    """IH5: the failure rule a decision was drawn under, logged only where it is not staged's (a record without the
    key was drawn before the tag, or with the switch off, and replays under staged's rule: ``mix.recompute``)."""

    return {"failure_rule": mix.OTHER_POLICY_RULE} if to_other else {}


def decision_trace(*, support: Sequence[str], by_id: Mapping[str, Any], feasible: Sequence[Any],
                   titles: Mapping[str, str], numeric: Any, llm: Any, decider: Any, staged_ref: str,
                   weight: tuple[float, Mapping[str, Any]], effective: Mapping[str, float], pi: Mapping[str, float],
                   drawn: Any, seed: str, config: Any, now_iso: str, guard: Mapping[str, Any], stop_in_support: bool,
                   card_version: str | None) -> dict[str, Any]:
    """The trace's common part for one decision (a block boundary's or a mid-block one's): every option's row
    (:func:`candidate_row`), the numeric policy's evaluation, both policies, the mix and its draw, the evaluation's
    uses and window, and the versions it was valued under. ``numeric``: the numeric policy's answer
    (``objective_job.NumericPolicy``) or None; ``llm``, ``decider``: the models' results or None."""

    evaluation = numeric.evaluation if numeric is not None else None
    rows = evaluation.by_ref() if evaluation is not None else {}
    v = evaluation.v if evaluation is not None else None
    stop_q = rows[STOP_FOR_TODAY].q if STOP_FOR_TODAY in rows else None
    order = sorted(rows, key=lambda ref: -rows[ref].q)
    top = rows[order[0]] if order else None
    inputs = numeric.inputs if numeric is not None else None
    # The generator switches the numeric answer was computed under (frozen with it), not the serving config's, which
    # may have changed since the job started; with no numeric answer, the serving config's (None below their tag).
    served_switches = (numeric.switches if numeric is not None and numeric.switches is not None
                       else _serving_switches(config).get("serving_switches"))
    topic_by_lo = {topic.lo: topic for topic in (inputs.topics if inputs is not None else ())}
    actions = {action.ref: action for action in (numeric.actions if numeric is not None else ())}
    llm_parsed = getattr(llm, "parsed", None) if llm is not None and llm.status == ANSWERED else None
    residual_record = numeric.residual if numeric is not None else None
    residual_applied = bool(residual_record) and residual_record.get("status") == "applied"  # type: ignore[union-attr]
    # The miss-cause sensor the numeric policy's inputs read (absent off, or below its tag: no key anywhere).
    miss_cause = ((numeric.sources if numeric is not None else {}) or {}).get(MISS_CAUSE_SOURCE)
    miss_topics = dict((miss_cause or {}).get("topics") or {})
    candidates: dict[str, Any] = {}
    for ref in support:
        candidates[ref] = candidate_row(
            ref, by_id.get(ref), titles=titles, valued=rows.get(ref), action=actions.get(ref), numeric=numeric,
            topic_by_lo=topic_by_lo, miss_cause=miss_cause, miss_topics=miss_topics, llm=llm, llm_parsed=llm_parsed,
            v=v, stop_q=stop_q, top=top, residual_applied=residual_applied)
    filtered = {candidate.candidate_id: ("beyond_top_k" if (candidate.annotations or {}).get("reversible", True)
                                         else "irreversible")
                for candidate in feasible if candidate.candidate_id not in support}
    llm_dist = dict(llm_parsed.distribution) if isinstance(llm_parsed, rq.ParsedPolicy) else None
    favoured = max(llm_dist, key=lambda ref: llm_dist[ref]) if llm_dist else None
    section = config.router_objective
    window = int(section.evaluation_window_days)
    decided = parse_utc(now_iso)
    window_closes = (decided + timedelta(days=window)).strftime("%Y-%m-%dT%H:%M:%SZ") if decided is not None else None
    baselines = numeric.baselines if numeric is not None else {}
    sources = dict(numeric.sources) if numeric is not None else {}
    # The scored population, frozen from the goals and retention commitments alone: a candidate-only topic is
    # valued in the rollouts but is not one of the uses either policy is scored on.
    population = (sources.get("population") or {}).get("los") or {}
    uses = {
        "topics": [{"lo": lo, "c": c, "m0": (baselines.get("topics") or {}).get(lo)}
                   for lo, c in population.items() if c > 0],
        "population_basis": (sources.get("population") or {}).get("basis"),
        "dated": [{"goal_id": use.goal_id, "lo": use.lo, "at_days": use.at_days, "omega": use.weight,
                   "m0": (baselines.get("dated") or {}).get(f"{use.goal_id}:{use.lo}")}
                  for use in (inputs.dated if inputs is not None else ()) if use.at_days <= window],
    }
    price = numeric.price.as_dict() if numeric is not None and numeric.price is not None else None
    mbar = inputs.price.remembered if inputs is not None else None
    kappa0 = price["kappa0"] if price else 0.0
    c0 = (window * kappa0 * float(mbar) / 2.0) if mbar else None
    extra: dict[str, Any] = {}
    if residual_record is not None:
        # The learned tail's record, frozen (ŵ with its slope and rank, the fit, each candidate's features, V_tail,
        # V_residual and Ṽ), so the terms recompute from the trace alone.
        section_record = dict(residual_record)
        if residual_applied:
            from learnloop.router_objective import tail_serve

            section_record["candidates"] = {
                ref: {**dict(entry), **tail_serve.candidate_terms(residual_record, ref,
                                                                    rows[ref].q if ref in rows else None)}
                for ref, entry in (residual_record.get("candidates") or {}).items()}
        extra["residual"] = section_record
    if miss_cause is not None:
        # The whole miss-cause sensor and, with the cause in the value, beta's fit, each topic's calibration and the
        # cause slopes.
        extra["miss_cause"] = dict(miss_cause)
    preference_record = numeric.preference if numeric is not None else None
    if preference_record is not None:
        # The preferences' choice model: its sensor and w_pref, frozen, with V_pref at this Q̄.
        from learnloop.router_objective import preferences as PF

        extra["preference"] = (PF.with_values(preference_record, {ref: rows[ref].q for ref in rows})
                               if preference_record.get("status") == "applied" else dict(preference_record))
    return {
        **extra,
        "candidates": candidates,
        "reference": ({"ref": evaluation.reference.ref, "q": evaluation.reference.q,
                       "terms": dict(evaluation.reference.terms)} if evaluation is not None and evaluation.reference else None),
        "v": v, "cutoff_days": evaluation.cutoff if evaluation is not None else None,
        "precision": {"draws": evaluation.draws if evaluation is not None else 0,
                      "paired_se_top_two": (numeric.tie or {}).get("paired_se_top_two") if numeric else None},
        "filtered": filtered,
        "stop_in_support": stop_in_support,
        "session": {"minutes": inputs.session_minutes if inputs is not None else None, "remembered_minutes": mbar,
                    "remembered_source": inputs.price.remembered_source if inputs is not None else None, **dict(guard)},
        "policies": {
            "llm": {"status": llm.status if llm is not None else NOT_READY, "distribution": llm_dist,
                    "favoured": favoured, "rationale": getattr(llm_parsed, "rationale", None),
                    "evidence_ids": list(getattr(llm_parsed, "evidence_ids", ()) or ()),
                    "reference_forecast": dict(llm_parsed.reference) if isinstance(llm_parsed, rq.ParsedPolicy) else None,
                    "model": getattr(llm, "model", None) if llm is not None else None,
                    "latency_ms": getattr(llm, "latency_ms", None) if llm is not None else None,
                    "cost_usd": getattr(llm, "cost_usd", None) if llm is not None else None,
                    "error": getattr(llm, "error", None) if llm is not None else None},
            "numeric": {"status": numeric.status if numeric is not None else NOT_READY,
                        "choice": numeric.choice if numeric is not None else None,
                        "tie": dict(numeric.tie) if numeric is not None else None,
                        "corrected_by_llm_forecasts": bool(numeric.corrected) if numeric is not None else False,
                        "stage": numeric.stage if numeric is not None else None,
                        "latency_ms": numeric.latency_ms if numeric is not None else None,
                        "error": numeric.error if numeric is not None else None},
            "staged": {"advice": staged_ref},
            "decider": {"status": decider.status if decider is not None else NOT_READY,
                        "advice": (dict(decider.parsed.distribution) if decider is not None and decider.status == ANSWERED
                                   and getattr(decider, "parsed", None) is not None else None)},
        },
        "mixing": {"posterior": weight[1].get("posterior"), "seeds": weight[1].get("seeds"),
                   "weight_note": weight[1].get("note"), "w": weight[0], "effective": dict(effective),
                   "mu": dict(pi), "seed": seed, "chosen": drawn.chosen, "drawn_component": drawn.component,
                   "propensity": drawn.propensity, "u1": drawn.u1, "u2": drawn.u2,
                   "epsilon": float(config.router.epsilon_min),
                   **failure_rule_field(failure_share_to_other_policy_on(config))},
        "evaluation": {"uses": uses, "window_days": window, "window_closes_at": window_closes, "c0": c0,
                       "c0_basis": "the tail's cost at the remembered minutes (no earlier window of costs at this version)",
                       "objective_version": OBJ.OBJECTIVE_VERSION,
                       "score": _score_note(config)},
        "frontier": dict(numeric.frontier) if numeric is not None else {},
        "inputs_sources": {key: value for key, value in sources.items()
                           if key not in ("population", MISS_CAUSE_SOURCE)},
        "versions": {"objective": OBJ.OBJECTIVE_VERSION, "tail": ROL.TAIL_VERSION, "terminal": OBJ.TERMINAL_VERSION,
                     "horizon_days": float(section.horizon_days), "memory_model": inputs.combiner.as_dict()
                     if inputs is not None else None, "kappa": price,
                     "learning": inputs.learning.source if inputs is not None else None,
                     "card": card_version, "llm_schema": rq.LLM_POLICY_SCHEMA,
                     "goals": {goal_id: {"source": goal.get("source"), "contract": goal.get("contract_version_id")}
                               for goal_id, goal in ((numeric.sources if numeric is not None else {}).get("goals") or {}).items()},
                     # The rollouts' review draw, named only when it serves (below its tag, or off, the trace keeps
                     # the predecessor's bytes).
                     **({"review_draw": ROL.REVIEW_DRAW_VERSION}
                        if served_switches is not None and served_switches.get("consistent_review_draw") else {}),
                     # AD's own predictive in the rollouts, named only when it serves.
                     **({"ad_link": ADL.AD_LINK_VERSION}
                        if inputs is not None and inputs.ad_link is not None else {}),
                     # The serving switches the numeric answer was computed under, part of the generator payload
                     # (``tail_data.generator``); only at their tag.
                     **({"serving_switches": dict(served_switches)} if served_switches is not None else {})},
    }


def objective_trace(choice: Any, *, support: Sequence[str], by_id: Mapping[str, Any], feasible: Sequence[Any],
                    titles: Mapping[str, str], numeric: Any, llm: Any, decider: Any, staged_ref: str,
                    weight: tuple[float, Mapping[str, Any]], seed: str, config: Any, now_iso: str,
                    card_version: str | None, policy_card: Mapping[str, Any], contested: str | None,
                    carried_for: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """A block boundary's trace, from its choice (``choose.Choice``) and what the chooser read for it: the numeric
    policy's answer, the two models' results, the weight, the mix's seed, the LLM's card (``policy_card``), the IH2
    contest's follow-up (``contested``) and the carried valuations this trace records (``carried_for``)."""

    drawn, coin = choice.drawn, choice.coin
    session_minutes = numeric.inputs.session_minutes if numeric is not None and numeric.inputs is not None else None
    mbar = numeric.inputs.price.remembered if numeric is not None and numeric.inputs is not None else None
    guard_at = P.guard_minutes(config, float(mbar)) if mbar else None
    guard_state = {"guard_minutes": guard_at, "guard_crossed": bool(guard_at and session_minutes is not None
                                                                     and session_minutes >= guard_at)}
    trace = decision_trace(support=support, by_id=by_id, feasible=feasible, titles=titles, numeric=numeric, llm=llm,
                           decider=decider, staged_ref=staged_ref, weight=weight, effective=choice.effective,
                           pi=drawn.pi, drawn=drawn, seed=seed, config=config, now_iso=now_iso, guard=guard_state,
                           stop_in_support=STOP_FOR_TODAY in support, card_version=card_version)
    if policy_card.get("statements"):
        # Which statements card the LLM read, its entries and what the budget left out of them.
        trace["learner_statements"] = dict(policy_card["statements"])
    if contested is not None:
        # A lesson offer against the boundary's follow-up: the offer's declined branch is the follow-up.
        trace["followup_contest"] = {"candidate_id": contested, "item_ids": list(by_id[contested].item_ids),
                                     "offer_declined_branch": "the follow-up (it stays available)"}
    # Every active dated goal's frozen forecast, for the goal-date read, whatever its distance; the policy
    # comparison's uses keep only the window's, so a goal past the window would otherwise have no forecast.
    trace["goal_dates"] = goal_dates(numeric)
    if carried_for:
        # Earlier decisions' carried valuations a later job ran, recorded here (read as of this trace's own time;
        # the transition into each is then no longer censored).
        trace["carried_for"] = carried_for
    if coin is not None:
        # What was served and its exact probability under the coin and the mix together; the mix's own draw and μ
        # stay beside it (a ``policy`` decision's score reads μ, exact given the independent coin).
        trace["mixing"].update(drawn_chosen=drawn.chosen, chosen=choice.served, propensity=coin.served_propensity)
        trace["stop_coin"] = coin.as_dict()
        if coin.arm != SC.POLICY:
            trace["evaluation"]["score"] = f"none: {SC.FORCED} (the coin chose what was served)"
    return trace


__all__ = ["LESSON_OFFER_SUBTYPE", "MISS_CAUSE_SOURCE", "STOP_FOR_TODAY", "candidate_row", "decision_trace",
           "failure_rule_field", "goal_dates", "objective_trace", "option_kind", "option_label"]
