"""Router objective RO4 (spec_router_objective_v1 §8.2-§8.3, §8.6-§8.8): the objective chooser on Today.

At the tag with ``[router_objective] enabled`` (and the router's mixture serving) each reversible block boundary is
decided by the learned mix of two policies over the staged frame's top-k support, which always holds ``stop for
today`` (§8.2):

```
μ_i(a) = (1 − k·ε) · [ w_i·π_L^op(a) + (1 − w_i)·π_Q^op(a) ] + ε
```

* **π_L**, the frontier LLM's policy: one ``router_llm_choice_v3`` request on the ``router_llm`` route over a
  decision-level variant of RO2's H3 card (:mod:`learnloop.daily_plan.objective_card`), built in the prefetch and
  frozen with the boundary key, with the tail's next action as a non-choosable reference row. It returns a
  probability per option, per-option forecasts and a rationale with evidence ids. The older ``llm`` chooser and its
  limited card are no longer served.
* **π_Q**, the numeric policy: plain argmax of ``Q̄`` (:mod:`learnloop.router_objective.value`), ties within the
  paired precision broken by support order, run as a third job in the prefetch with the prefetch's remaining budget
  as its deadline; a serving step that finds it unfinished treats it as a timeout. With no model set up there is no
  prefetch, so it runs on the calling thread with ``router.timeout_seconds`` as its deadline.
* **Staged and the Decider** are logged as advice; staged is the failure fallback (each failure moves only its
  policy's share to it). Irreversible picks and single-option supports stay deterministic, as before.
* **w_i** is ``ℓ_L + (1 − ℓ_L − ℓ_Q)·p_i`` from the weight's posterior (:mod:`learnloop.router_objective.weight`);
  with no randomized checks before RO5 no score forms and ``w`` stays at its prior, and the trace says so.
* **κ0** is the day's seed (:mod:`learnloop.router_objective.price`), carried from the day's first decision.

The chooser writes nothing: its record and its trace ride on ``BlockChoice.router_record`` to the ``plan_block``
logger, which writes the trace (``router_objective_traces``) in the block's transaction.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field, replace
from datetime import timedelta
import hashlib
import json
import logging
import threading
import time
from typing import Any

from learnloop.clock import parse_utc
from learnloop.daily_plan import objective_inputs as OI
from learnloop.daily_plan.router_chooser import (
    INSERT_NOW,
    MODE as MIXTURE_MODE,
    RestraintGate,
    RestraintOutcome,
    RouterChooser,
    _await,
    _build_card,
    _card_fields,
    _hash,
    _latest_attempt,
    _NoModels,
    _option,
    _payloads,
    _rule_sentence,
    router_settings,
    support_order,
)
from learnloop.daily_plan.router_runtime import (
    ANSWERED,
    DECIDER,
    FAILED,
    INVALID,
    LLM,
    NOT_READY,
    RECEIPT_OWNER,
    TIMEOUT,
    ComponentResult,
    Prefetch,
    RouterRuntime,
    call_decider,
    call_llm,
)
from learnloop.daily_plan.staged_frame import StagedChooser
from learnloop.daily_plan.types import CONTINUE_CURRENT, STOP_FOR_TODAY, STOP_OFFER_MINUTES, BlockCandidate, BlockChoice, PlanState
from learnloop.ids import new_ulid
from learnloop.router import requests as rq
from learnloop.router import why as router_why
from learnloop.router_objective import mix
from learnloop.router_objective import price as P
from learnloop.router_objective import value as V
from learnloop.router_objective import weight as W

LOG = logging.getLogger(__name__)

NUMERIC = "numeric"
MODE = "objective"
KEY_VERSION = 1
WHY_VERSION = "router_why_v3"
#: Per decision: the LLM policy's and the numeric policy's statuses a share can fall back from.
_FAILURES = frozenset({TIMEOUT, FAILED, INVALID, NOT_READY, "spend", "unreachable"})


def objective_settings(config: Any) -> dict[str, Any]:
    section = config.router_objective
    return {key: getattr(section, key) for key in (
        "enabled", "sensors_in_value", "rollout_theta_draws", "rollout_theta_draws_max", "horizon_days",
        "undated_use_density", "dated_use_weight", "session_gap_minutes", "session_guard_minutes",
        "evaluation_window_days", "llm_weight_prior", "llm_min_share", "numeric_min_share", "delta_prior_sd",
        "effect_slope_prior_mean", "effect_slope_prior_variance", "stop_accept_prior_a", "stop_accept_prior_b",
        "llm_card_token_budget", "receipts")}


def _local_date(now_iso: str) -> str:
    moment = parse_utc(now_iso)
    return (moment.astimezone().date().isoformat() if moment is not None else now_iso[:10])


# -- the price, the weight -------------------------------------------------------------------------------


def day_price(repository: Any, inputs: V.Inputs, *, local_date: str, draws: int, seed: str) -> tuple[P.Seeded, dict[str, Any]]:
    """κ0 for this decision (§8.6): the day's first decision computes the seed from the gain curve, later ones
    carry it. Returns the price and the frontier (G against minutes) it came from."""

    from learnloop.db.stores import router_objective as store

    today = None
    last_positive = None
    with repository.connection() as connection:
        if store.table_present(connection, store.TRACES):
            today = connection.execute(
                "SELECT kappa0, decision_id FROM router_objective_traces WHERE local_date = ? AND kappa_how IN (?, ?, ?) "
                "AND decision_kind = 'plan_block' ORDER BY created_at, id LIMIT 1",
                (local_date, P.DAY_SEED, P.FLOORED, P.TAIL_AVERAGE)).fetchone()
            last = connection.execute(
                "SELECT kappa0 FROM router_objective_traces WHERE kappa0 > 0 ORDER BY created_at DESC, id DESC LIMIT 1"
            ).fetchone()
            last_positive = float(last[0]) if last is not None else None
    if today is not None and today[0] is not None:
        return P.Seeded(kappa0=float(today[0]), how=P.CARRIED_DAY, local_date=local_date), {"carried_from": today[1]}
    if not inputs.topics:
        if last_positive is not None:
            return P.Seeded(kappa0=last_positive, how=P.CARRIED_LAST, local_date=local_date), {"status": "no_topics"}
        return P.Seeded(kappa0=0.0, how=P.TAIL_AVERAGE, local_date=local_date), {"status": "no_topics"}
    mbar = float(inputs.price.remembered)
    d = float(inputs.tail_block_minutes)
    points = sorted({0.0, mbar, mbar + d, 2 * mbar})
    curve = V.gain(inputs, points, draws=draws, seed=f"{seed}:frontier")
    kappa0, how = P.seed_from_gain(curve, remembered=mbar, block_minutes=d, last_positive=last_positive)
    frontier = {"points": [{"minutes": m, "gain": curve[m]} for m in points],
                "display": "; ".join(f"{m:.0f} minutes: predicted gain {curve[m]:+.3f}" for m in points if m > 0)
                + " (predictions)"}
    return P.Seeded(kappa0=kappa0, how=how, gain={str(k): v for k, v in curve.items()}, local_date=local_date), frontier


def _randomized_checks_exist(repository: Any) -> bool:
    """Whether any RO5 randomized cold check was ever assigned (none before RO5)."""

    with repository.connection() as connection:
        present = connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'policy_experiment_assignments'").fetchone()
        if present is None:
            return False
        return connection.execute(
            "SELECT 1 FROM policy_experiment_assignments WHERE experiment_id LIKE 'ro5_randomized_check%' LIMIT 1"
        ).fetchone() is not None


def current_weight(repository: Any, config: Any, *, at: str) -> tuple[float, dict[str, Any]]:
    """``w_i`` (§8.7) from the scores whose windows closed before ``at``; with no randomized check, none forms."""

    from learnloop.db.stores import router_objective as store

    seeds = W.Seeds.from_config(config)
    scores: list[W.Scored] = []
    with repository.connection() as connection:
        rows = [row for row in store.traces(connection) if row.get("window_closes_at")
                and str(row["window_closes_at"]) < at] if store.table_present(connection, store.TRACES) else []
    checks = _randomized_checks_exist(repository)
    for row in rows:
        reason = W.NO_RANDOMIZED_USE if not checks else W.PENDING
        if row.get("llm_status") != ANSWERED or row.get("numeric_status") != ANSWERED:
            reason = W.FALLBACK
        scores.append(W.Scored(decision_id=str(row["decision_id"]), decided_at=str(row["created_at"]),
                               window_closes_at=str(row["window_closes_at"]), value=None, reason=reason))
    posterior = W.posterior(scores, seeds, at=at)
    w = W.weight(posterior.p, seeds)
    note = ("no randomized checks exist before RO5, so no score forms and w stays at its prior"
            if posterior.source.startswith("prior") else "w moved on closed scores")
    return w, {"posterior": posterior.as_dict(), "seeds": {"w0": seeds.w0, "ell_l": seeds.ell_l, "ell_q": seeds.ell_q,
                                                           "s0": seeds.s0, "p0": seeds.p0, "m0": seeds.m0},
               "note": note}


# -- the numeric policy ----------------------------------------------------------------------------------


@dataclass
class NumericPolicy:
    """What π_Q computed for one decision (its status, choice, evaluation and the trace's sections)."""

    status: str
    choice: str | None = None
    tie: Mapping[str, Any] = field(default_factory=dict)
    evaluation: V.Evaluation | None = None
    inputs: V.Inputs | None = None
    actions: tuple[V.Action, ...] = ()
    sources: Mapping[str, Any] = field(default_factory=dict)
    price: P.Seeded | None = None
    frontier: Mapping[str, Any] = field(default_factory=dict)
    baselines: Mapping[str, Any] = field(default_factory=dict)
    corrected: bool = False
    latency_ms: int | None = None
    error: str | None = None


def run_numeric(vault: Any, repository: Any, *, state: PlanState, support: Sequence[str],
                candidates: Mapping[str, BlockCandidate], now_iso: str, seed: str, deadline: float | None,
                keep_going: Any = None, forecasts: Any = None, clock: Any = time.monotonic) -> NumericPolicy:
    """π_Q end to end: the frozen inputs, the day's price, ``Q̄`` with common random numbers (more draws while
    ``keep_going()``), then, once the LLM policy's forecasts are in (``forecasts()``: None while out), the effect
    correction; the argmax with the tie rule; the evaluation's baselines."""

    started = clock()
    config = vault.config
    section = config.router_objective
    try:
        inputs, actions, sources = OI.build(vault, repository, state=state, support=support, candidates=candidates,
                                            now_iso=now_iso)
        local_date = _local_date(now_iso)
        # The day's seed is computed once a day, so it takes the most draws (a marginal gain is a small difference
        # of two large sums; at 8 draws its noise is of the order of the signal).
        priced, frontier = day_price(repository, inputs, local_date=local_date,
                                     draws=int(section.rollout_theta_draws_max), seed=seed)
        inputs = replace(inputs, price=replace(inputs.price, kappa0=priced.kappa0, regime=priced.regime))
        draws, ceiling = int(section.rollout_theta_draws), int(section.rollout_theta_draws_max)
        evaluation = V.evaluate(inputs, actions, draws=draws, seed=seed, max_draws=ceiling, keep_going=keep_going,
                                deadline=deadline, clock=clock)
        corrected = False
        if evaluation.complete and forecasts is not None and bool(section.sensors_in_value):
            got = forecasts()
            if got is not None:
                by_ref, reference = got
                if reference is not None and all(action.kind == V.STOP or by_ref.get(action.ref) is not None
                                                 for action in actions):
                    effect = V.EffectSlope(alpha=(0.0, float(section.effect_slope_prior_variance)),
                                           beta=(float(section.effect_slope_prior_mean),
                                                 float(section.effect_slope_prior_variance)))
                    with_llm = replace(inputs, effect=effect, reference_forecast=float(reference))
                    acts = [replace(action, forecast=by_ref.get(action.ref)) for action in actions]
                    again = V.evaluate(with_llm, acts, draws=evaluation.draws, seed=seed, deadline=deadline, clock=clock)
                    if again.complete:
                        evaluation, inputs, actions, corrected = again, with_llm, acts, True
        if not evaluation.complete:
            return NumericPolicy(status=TIMEOUT, inputs=inputs, actions=tuple(actions), sources=sources, price=priced,
                                 frontier=frontier, latency_ms=int(round((clock() - started) * 1000)),
                                 error="no answer within the budget")
        choice, tie = V.numeric_choice(evaluation, support)
        base = V.baselines(inputs, int(section.evaluation_window_days), draws=min(evaluation.draws, 8), seed=seed)
        return NumericPolicy(status=ANSWERED, choice=choice, tie=tie, evaluation=evaluation, inputs=inputs,
                             actions=tuple(actions), sources=sources, price=priced, frontier=frontier, baselines=base,
                             corrected=corrected, latency_ms=int(round((clock() - started) * 1000)))
    except Exception as exc:  # noqa: BLE001 - a failed policy's share goes to the staged rule
        LOG.warning("router objective: the numeric policy failed", exc_info=True)
        return NumericPolicy(status=FAILED, error=f"{type(exc).__name__}: {str(exc)[:200]}",
                             latency_ms=int(round((clock() - started) * 1000)))


# -- the prefetch job --------------------------------------------------------------------------------------


def _reference_description(action: V.Action, titles: Mapping[str, str]) -> str:
    topics = ", ".join(dict.fromkeys(titles.get(lo, lo) for lo in action.item_los)) or "the topics most at risk"
    return (f"The continuation the numeric model assumes next: about {max(1, round(action.minutes))} min of "
            f"practice on {topics}, then a session of the suggested minutes each day.")


def _llm_forecasts(entry: Prefetch) -> Any:
    """The numeric job's view of the LLM policy's forecasts: None while it is out, else ``(per option, reference)``
    (both None when it failed)."""

    event = entry.events.get(LLM)
    if event is not None and not event.is_set():
        return None
    result = entry.components.get(LLM)
    parsed = getattr(result, "parsed", None)
    if result is None or result.status != ANSWERED or not isinstance(parsed, rq.ParsedPolicy):
        return ({}, None)
    by_ref = {ref: values.get("p_cold_7") for ref, values in parsed.forecasts.items()}
    return by_ref, parsed.reference.get("p_cold_7")


def _objective_job(entry: Prefetch, *, runtime: RouterRuntime, vault: Any, sqlite_path: Any, session_id: str | None,
                   plan_id: str | None) -> None:
    import contextvars

    from learnloop.daily_plan.objective_card import decision_card
    from learnloop.db.repositories import Repository

    material = entry.material
    repository = Repository.attach(sqlite_path)
    config = vault.config
    with runtime.spend.metered(repository, config, owner_kind=RECEIPT_OWNER, owner_id=entry.key):
        threads: list[threading.Thread] = []

        def run(name: str, request: Any, parse: Any) -> None:
            with entry.lock:
                entry.started_components.add(name)
            budget = entry.remaining(runtime.clock())
            call = call_decider if name == DECIDER else call_llm
            try:
                result, raw = call(runtime, vault, repository, request, card_hash=material.get("card_hash"), budget=budget)
                if result.status == ANSWERED:
                    try:
                        result.parsed = parse(raw, request)
                    except rq.RouterResponseInvalid as exc:
                        result.status, result.error = INVALID, str(exc)[:300]
            except Exception as exc:  # noqa: BLE001 - a component never takes the job down
                result = ComponentResult(name=name, status=FAILED, error=type(exc).__name__)
            with entry.lock:
                entry.components[name] = result
            entry.events[name].set()

        def start(name: str, request: Any, parse: Any) -> None:
            if runtime.inline:
                run(name, request, parse)
                return
            context = contextvars.copy_context()
            thread = threading.Thread(target=context.run, args=(run, name, request, parse),
                                      name=f"learnloop-objective-{name}", daemon=True)
            thread.start()
            threads.append(thread)

        if DECIDER in entry.events:
            # The Decider: advice and a comparator only, on the learner-state card (v3) and the options.
            request = rq.BoundaryRequest(options=tuple(material["options"]),
                                         state=rq.state_text(material["card_text"], material["options"],
                                                             evidence=material["evidence"]),
                                         evidence=tuple(material["evidence"]))
            start(DECIDER, request, rq.parse_decider_choice)
        if LLM in entry.events:
            try:
                built, actions, _sources = OI.build(vault, repository, state=material["state"],
                                                    support=material["support"], candidates=material["by_id"],
                                                    now_iso=material["decided_at"])
                reference = V._Model(built, 1, "reference").tail_action()
                titles = {lo_id: lo.title for lo_id, lo in vault.learning_objects.items()}
                card = decision_card(vault, repository, [material["by_id"][ref] for ref in material["support"]
                                                         if ref in material["by_id"]],
                                     served_at=material["decided_at"], goals=_sources.get("goals") or {},
                                     session=_sources.get("session") or {},
                                     budget=int(config.router_objective.llm_card_token_budget))
                policy_request = rq.PolicyRequest(
                    options=tuple(material["options"]),
                    reference=rq.BlockOption(V.REFERENCE_REF, _reference_description(reference, titles)),
                    state=json.dumps(card["state"], sort_keys=True, ensure_ascii=False, default=str),
                    evidence=tuple(card["evidence_ids"]))
                entry.material["policy_card"] = {key: card[key] for key in ("evidence_ids", "left_out", "bytes", "items")}
                entry.material["policy_request"] = policy_request
                start(LLM, policy_request, rq.parse_llm_policy)
            except Exception as exc:  # noqa: BLE001 - the card never blocks the plan: the LLM policy fails
                LOG.warning("router objective: the LLM policy's card was not built", exc_info=True)
                with entry.lock:
                    entry.components[LLM] = ComponentResult(name=LLM, status=FAILED, error=f"card: {type(exc).__name__}")
                entry.events[LLM].set()
        with entry.lock:
            entry.started_components.add(NUMERIC)
        numeric = run_numeric(
            vault, repository, state=material["state"], support=material["support"], candidates=material["by_id"],
            now_iso=material["decided_at"], seed=material["numeric_seed"], deadline=entry.deadline,
            keep_going=lambda: LLM in entry.events and not entry.events[LLM].is_set() and runtime.clock() < entry.deadline,
            forecasts=(lambda: _wait_llm(entry, runtime)) if LLM in entry.events else None, clock=runtime.clock)
        with entry.lock:
            entry.components[NUMERIC] = ComponentResult(name=NUMERIC, status=numeric.status, parsed=numeric,  # type: ignore[arg-type]
                                                        latency_ms=numeric.latency_ms, error=numeric.error)
        entry.events[NUMERIC].set()
        for thread in threads:
            thread.join(timeout=entry.remaining(runtime.clock()) + 1.0)


def _wait_llm(entry: Prefetch, runtime: RouterRuntime) -> Any:
    event = entry.events.get(LLM)
    if event is not None and not event.is_set():
        event.wait(entry.remaining(runtime.clock()))
    return _llm_forecasts(entry)


# -- the decision -------------------------------------------------------------------------------------------


def _support_labels(support: Sequence[str], by_id: Mapping[str, BlockCandidate], titles: Mapping[str, str]) -> dict[str, str]:
    out = {}
    for ref in support:
        if ref == STOP_FOR_TODAY:
            out[ref] = "stop for today"
        elif ref in by_id:
            candidate = by_id[ref]
            what = candidate.reading.section_title if candidate.reading is not None else ", ".join(
                dict.fromkeys(titles.get(lo, lo) for lo in candidate.learning_object_ids)) or candidate.lane
            out[ref] = f"{candidate.lane}: {what} ({max(1, round(candidate.est_minutes))} min)"
    return out


def _trace(*, support: Sequence[str], by_id: Mapping[str, BlockCandidate], feasible: Sequence[BlockCandidate],
           titles: Mapping[str, str], numeric: NumericPolicy | None, llm: ComponentResult | None,
           decider: ComponentResult | None, staged_ref: str, weight: tuple[float, Mapping[str, Any]],
           effective: Mapping[str, float], pi: Mapping[str, float], drawn: Any, seed: str, config: Any,
           now_iso: str, guard: Mapping[str, Any], stop_in_support: bool, card_version: str | None) -> dict[str, Any]:
    labels = _support_labels(support, by_id, titles)
    evaluation = numeric.evaluation if numeric is not None else None
    rows = evaluation.by_ref() if evaluation is not None else {}
    v = evaluation.v if evaluation is not None else None
    stop_q = rows[STOP_FOR_TODAY].q if STOP_FOR_TODAY in rows else None
    order = sorted(rows, key=lambda ref: -rows[ref].q)
    top = rows[order[0]] if order else None
    inputs = numeric.inputs if numeric is not None else None
    topic_by_lo = {topic.lo: topic for topic in (inputs.topics if inputs is not None else ())}
    actions = {action.ref: action for action in (numeric.actions if numeric is not None else ())}
    llm_parsed = getattr(llm, "parsed", None) if llm is not None and llm.status == ANSWERED else None
    candidates: dict[str, Any] = {}
    for ref in support:
        valued = rows.get(ref)
        action = actions.get(ref)
        sensors = {}
        for lo in dict.fromkeys(action.item_los if action is not None else ()):
            topic = topic_by_lo.get(lo)
            if topic is None:
                continue
            sensors[lo] = {"ad_eta": topic.eta_mean, "ad_eta_var": topic.eta_var, "fsrs_stability": topic.stability,
                           "fsrs_elapsed_days": topic.elapsed_days, "practiced": topic.practiced,
                           "source": ((numeric.sources if numeric is not None else {}).get("topics") or {}).get(lo),
                           "reached_qbar": True}
        if isinstance(llm_parsed, rq.ParsedPolicy) and ref in llm_parsed.forecasts:
            sensors["llm_forecast"] = {**dict(llm_parsed.forecasts[ref]), "schema": rq.LLM_POLICY_SCHEMA,
                                       "model": getattr(llm, "model", None),
                                       "reached_qbar": bool(numeric is not None and numeric.corrected)}
        terms = None
        if valued is not None:
            terms = {**dict(valued.terms), "q": valued.q,
                     "q_minus_v": (valued.q - v) if v is not None else None,
                     "q_minus_stop": (valued.q - stop_q) if stop_q is not None else None,
                     "paired_se_vs_top": V.paired_standard_error(top, valued) if top is not None and top.ref != ref else 0.0}
        candidates[ref] = {
            "label": labels.get(ref, ref), "kind": action.kind if action is not None else None,
            "minutes": action.minutes if action is not None else None, "sensors": sensors, "terms": terms,
            "split": {"learning": None, "information": (valued.extra.get("information") if valued is not None else None),
                      "return_effect": 0.0, "note": "display only, never added; the return effect is zero until RO5 "
                                                    "fits a return model"},
            "branches": dict(valued.extra.get("branches") or {}) if valued is not None else None,
        }
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
    uses = {
        "topics": [{"lo": topic.lo, "c": topic.undated_density, "m0": (baselines.get("topics") or {}).get(topic.lo)}
                   for topic in (inputs.topics if inputs is not None else ()) if topic.undated_density > 0],
        "dated": [{"goal_id": use.goal_id, "lo": use.lo, "at_days": use.at_days, "omega": use.weight,
                   "m0": (baselines.get("dated") or {}).get(f"{use.goal_id}:{use.lo}")}
                  for use in (inputs.dated if inputs is not None else ()) if use.at_days <= window],
    }
    price = numeric.price.as_dict() if numeric is not None and numeric.price is not None else None
    mbar = inputs.price.remembered if inputs is not None else None
    kappa0 = price["kappa0"] if price else 0.0
    c0 = (window * kappa0 * float(mbar) / 2.0) if mbar else None
    return {
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
                   "epsilon": float(config.router.epsilon_min)},
        "evaluation": {"uses": uses, "window_days": window, "window_closes_at": window_closes, "c0": c0,
                       "c0_basis": "the tail's cost at the remembered minutes (no earlier window of costs at this version)",
                       "objective_version": V.OBJECTIVE_VERSION,
                       "score": "none forms until RO5's randomized checks: no valued use has r > 0"},
        "frontier": dict(numeric.frontier) if numeric is not None else {},
        "inputs_sources": dict(numeric.sources) if numeric is not None else {},
        "versions": {"objective": V.OBJECTIVE_VERSION, "tail": V.TAIL_VERSION, "terminal": V.TERMINAL_VERSION,
                     "horizon_days": float(section.horizon_days), "memory_model": inputs.combiner.as_dict()
                     if inputs is not None else None, "kappa": price,
                     "learning": inputs.learning.source if inputs is not None else None,
                     "card": card_version, "llm_schema": rq.LLM_POLICY_SCHEMA,
                     "goals": {goal_id: {"source": goal.get("source"), "contract": goal.get("contract_version_id")}
                               for goal_id, goal in ((numeric.sources if numeric is not None else {}).get("goals") or {}).items()}},
    }


@dataclass
class ObjectiveChooser(RouterChooser):
    """``router_objective_v1``: the two policies' learned mix over the staged frame's support."""

    name: str = mix.POLICY

    def _seed(self, key: str, decision_id: str) -> str:
        return self.runtime.seed(key, decision_id) if self.runtime.seed is not None else mix.seed_for(key, decision_id)

    def choose(self, state: PlanState, feasible: Sequence[BlockCandidate]) -> BlockChoice:
        staged = StagedChooser(card_builder=None).choose(state, feasible)
        config = self.vault.config
        settings = router_settings(config)
        record: dict[str, Any] = {**dict(staged.router_record or {}), "mode": MODE, "why_version": WHY_VERSION}
        by_id = {candidate.candidate_id: candidate for candidate in feasible}
        staged_candidate = by_id.get(staged.candidate_id)

        def deterministic(decided_by: str) -> BlockChoice:
            card = _build_card(self.card_builder, state, feasible)
            record.update(policy="staged_v1", decided_by=decided_by, **_card_fields(card))
            return replace(staged, router_record=record)

        if staged_candidate is None:
            return deterministic("single_option")
        if not (staged_candidate.annotations or {}).get("reversible", True):
            return deterministic("irreversible")
        support = support_order(state, feasible, staged.candidate_id, k=settings["k"], stop_offered=True,
                                ties_only=settings["ties_only"])
        if len(support) <= 1:
            return deterministic("single_option")
        # The staged rule's own pick: its lane-quota choice, or stop once the plan's minutes are used (§8.2: the
        # minutes are a suggestion the failure fallback keeps).
        staged_ref = STOP_FOR_TODAY if state.minutes_left < STOP_OFFER_MINUTES else staged.candidate_id
        readiness = self.runtime.readiness(self.vault)
        ready = tuple(name for name in (DECIDER, LLM) if readiness.get(name) is None)
        key = _hash({
            "v": KEY_VERSION, "kind": "objective_block", "plan_id": state.plan_id,
            "state": {"minutes_left": round(state.minutes_left, 3), "items_left": state.items_left,
                      "lanes": {lane: round(value, 3) for lane, value in sorted(state.lane_minutes_left.items())},
                      "kind": state.kind},
            "support": [by_id[ref].log_row() if ref in by_id else ref for ref in support],
            "staged": staged_ref, "as_of": _latest_attempt(self.repository),
            "version": config.algorithms.algorithm_version, "settings": settings,
            "objective": objective_settings(config), "ready": ready,
        })
        now_iso = self._now_iso()
        if ready:
            entry = self.runtime.lookup(self.scope, key)
            if entry is None:
                entry = self._start_objective(key, state, feasible, support, by_id, ready, now_iso)
            _await(self.runtime, entry, may_defer=self.may_defer, timeout=float(config.router.timeout_seconds))
        else:
            card = _build_card(self.card_builder, state, feasible)
            numeric = run_numeric(self.vault, self.repository, state=state, support=support, candidates=by_id,
                                  now_iso=now_iso, seed=_hash({"numeric": key}),
                                  deadline=self.runtime.clock() + float(config.router.timeout_seconds),
                                  clock=self.runtime.clock)
            entry = _NoModels(key, {"card": card, "evidence": list(rq.evidence_from_card(card.json)),
                                    "decided_at": now_iso, "numeric": numeric}, self.runtime.clock())
        self._freeze_objective(record, staged, feasible, support)
        return self._decide_objective(entry, state, staged, staged_ref, record, support, by_id, feasible, readiness,
                                      settings, now_iso)

    def _start_objective(self, key: str, state: PlanState, feasible: Sequence[BlockCandidate], support: Sequence[str],
                         by_id: Mapping[str, BlockCandidate], ready: tuple[str, ...], now_iso: str) -> Prefetch:
        from functools import partial

        config = self.vault.config
        card = _build_card(self.card_builder, state, feasible)
        titles = {lo_id: lo.title for lo_id, lo in self.vault.learning_objects.items()}
        options = [_option(by_id[ref], titles) if ref in by_id else rq.BlockOption(ref=ref, description=rq.STOP_OFFER_DESCRIPTION)
                   for ref in support]
        material = {
            "card": card, "card_hash": card.card_hash, "card_text": card.text, "card_json": card.json,
            "options": options, "evidence": list(rq.evidence_from_card(card.json)), "decided_at": now_iso,
            "state": state, "support": list(support), "by_id": dict(by_id), "numeric_seed": _hash({"numeric": key}),
        }
        return self.runtime.start(
            self.scope, key, kind="plan_block", budget=float(config.router.prefetch_timeout_seconds),
            material=material, components=(*ready, NUMERIC),
            job=partial(_objective_job, runtime=self.runtime, vault=self.vault, sqlite_path=self.repository.sqlite_path,
                        session_id=self.session_id, plan_id=state.plan_id),
        )

    def _decide_objective(self, entry: Any, state: PlanState, staged: BlockChoice, staged_ref: str,
                          record: dict[str, Any], support: Sequence[str], by_id: Mapping[str, BlockCandidate],
                          feasible: Sequence[BlockCandidate], readiness: Mapping[str, str | None],
                          settings: Mapping[str, Any], now_iso: str) -> BlockChoice:
        config = self.vault.config
        material = entry.material
        card = material["card"]
        results = entry.results()
        for name in (DECIDER, LLM):
            if name not in results:
                results[name] = ComponentResult(name=name, status=NOT_READY, error=str(readiness.get(name) or "not_ready"))
        numeric_result = results.get(NUMERIC)
        numeric: NumericPolicy | None = material.get("numeric")
        if numeric is None and numeric_result is not None:
            numeric = numeric_result.parsed if isinstance(numeric_result.parsed, NumericPolicy) else NumericPolicy(
                status=numeric_result.status, error=numeric_result.error)
        llm = results[LLM]
        llm_dist = (dict(llm.parsed.distribution) if llm.status == ANSWERED and isinstance(llm.parsed, rq.ParsedPolicy)
                    else None)
        numeric_ok = numeric is not None and numeric.status == ANSWERED and numeric.choice in support
        failed = [name for name, ok in ((mix.LLM, llm_dist is not None), (mix.NUMERIC, numeric_ok)) if not ok]
        w, weight_record = current_weight(self.repository, config, at=now_iso)
        effective = mix.effective_weights(w, failed)
        parts = mix.components(list(support), staged_ref, llm=llm_dist,
                               numeric_ref=numeric.choice if numeric_ok and numeric is not None else None)
        decision_id = new_ulid()
        seed = self._seed(entry.key, decision_id)
        drawn = mix.draw(list(support), parts, effective, float(settings["epsilon_min"]), seed)
        chosen = by_id.get(drawn.chosen)
        code, rule = _rule_sentence(chosen, state) if chosen is not None else ("stop_offer", router_why.sentence("stop_offer"))
        titles = {lo_id: lo.title for lo_id, lo in self.vault.learning_objects.items()}
        rationale = getattr(llm.parsed, "rationale", None) if llm_dist is not None else None
        cited = tuple(getattr(llm.parsed, "evidence_ids", ()) or ()) if llm_dist is not None else ()
        favoured = max(llm_dist, key=lambda ref: llm_dist[ref]) if llm_dist else None
        policy_card = material.get("policy_card") or {}
        guard_known = set(policy_card.get("evidence_ids") or ())
        guard = router_why.rationale_guard(rationale, cited, guard_known) if rationale is not None else "absent"
        if guard is None and drawn.component == mix.LLM and drawn.chosen != favoured:
            guard = "another_option"
        shown = drawn.component == mix.LLM and guard is None
        why, why_kind = router_why.objective_why(drawn.component, rule, option_count=len(support), rationale=rationale,
                                                 rationale_shown=shown)
        session_minutes = numeric.inputs.session_minutes if numeric is not None and numeric.inputs is not None else None
        mbar = numeric.inputs.price.remembered if numeric is not None and numeric.inputs is not None else None
        guard_at = P.guard_minutes(config, float(mbar)) if mbar else None
        guard_state = {"guard_minutes": guard_at, "guard_crossed": bool(guard_at and session_minutes is not None
                                                                         and session_minutes >= guard_at)}
        trace = _trace(support=support, by_id=by_id, feasible=feasible, titles=titles, numeric=numeric, llm=llm,
                       decider=results.get(DECIDER), staged_ref=staged_ref, weight=(w, weight_record),
                       effective=effective, pi=drawn.pi, drawn=drawn, seed=seed, config=config, now_iso=now_iso,
                       guard=guard_state, stop_in_support=STOP_FOR_TODAY in support, card_version=card.version)
        decider = results.get(DECIDER)
        decider_dist = (dict(decider.parsed.distribution) if decider is not None and decider.status == ANSWERED
                        and getattr(decider, "parsed", None) is not None else None)
        latencies = [r.latency_ms for r in results.values() if r.latency_ms is not None]
        costs = [r.cost_usd for r in results.values() if r.cost_usd is not None]
        policy_request = material.get("policy_request")
        payloads = _payloads({name: result for name, result in results.items() if name != NUMERIC})
        record.update(
            policy=mix.POLICY, decided_by=MODE if entry.__class__.__name__ != "_NoModels" else "objective_no_models",
            decision_id=decision_id, design=mix.DESIGN, seed=seed, why_code=code or None,
            drawn_component=drawn.component, option_count=len(support), fallback=mix.fallback_label(failed),
            fallback_reasons={name: (llm.status if name == mix.LLM else (numeric.status if numeric else NOT_READY))
                              for name in failed},
            rationale_hidden=bool(drawn.component == mix.LLM and not shown),
            evidence_labels=[ref for ref in cited if ref in guard_known] if shown else [],
            mixture={
                "boundary_key": entry.key, "support": list(support), "staged_ref": staged_ref, "k": settings["k"],
                "epsilon": settings["epsilon_min"], "ties_only": settings["ties_only"], "effective_weights": effective,
                "w": w, "failed": failed, "llm_distribution": llm_dist,
                "numeric_choice": numeric.choice if numeric_ok and numeric is not None else None,
                "drawn_component": drawn.component, "u1": drawn.u1, "u2": drawn.u2, "pi": dict(drawn.pi),
                "models": {name: result.summary() for name, result in sorted(results.items())},
                "rationale": {"text": rationale, "guard": guard, "shown": shown, "evidence_ids": list(cited),
                              "about": favoured},
                "prefetched_at": material.get("decided_at"),
                "waited_ms": int(round(max(self.runtime.clock() - entry.started, 0.0) * 1000)),
            },
            mixture_weights={"configured": {"w": w, "ell_l": config.router_objective.llm_min_share,
                                            "ell_q": config.router_objective.numeric_min_share},
                             "effective": effective},
            model_distributions={"llm": llm_dist, "numeric": parts.get(mix.NUMERIC), "decider": decider_dist},
            question_set_version=getattr(policy_request, "question_set_version", None),
            model_ids={"decider": results[DECIDER].model, "llm": llm.model, "llm_schema_version": rq.LLM_POLICY_SCHEMA},
            latency_ms=max(latencies) if latencies else None,
            cost_usd=round(sum(costs), 8) if costs else 0.0,
            payloads=payloads,
            objective_trace=trace,
            **_card_fields(card),
        )
        return BlockChoice(
            candidate_id=drawn.chosen, chosen_by="mixture",
            propensity=1.0 if drawn.deterministic else drawn.propensity,
            why=why or staged.why, why_kind=why_kind,  # type: ignore[arg-type]
            router_record=record,
        )


# -- the restraint (plan_interrupt) ---------------------------------------------------------------------------


@dataclass
class ObjectiveRestraintGate(RestraintGate):
    """§8.3's mid-block follow-ups: the same two-policy mix over ``{insert_now, continue_current}``. ``π_L`` from the
    LLM policy's ``intervene_now``; ``π_Q`` from ``Q̄`` of the two candidates :meth:`_state` builds, valued as a repair
    block now and as the current block's remaining questions with the follow-up at the next boundary. The Decider's
    ``P(yes)`` is logged as advice; refusals and ``wait_feasible = False`` stay deterministic."""

    def decide(self, record: Any, current: Any, item: Any, *, wait_feasible: bool = True) -> RestraintOutcome:
        refusals = self._refusals(item)
        if refusals:
            return self.declined(refusals)
        base: dict[str, Any] = {"mode": MODE, "why_version": WHY_VERSION}
        config = self.vault.config
        settings = router_settings(config)
        state, candidates = self._state(record, current, item)
        if not wait_feasible:
            card = _build_card(self.card_builder, state, candidates)
            base.update(policy="staged_v1", decided_by="no_room_to_wait", **_card_fields(card))
            return RestraintOutcome(INSERT_NOW, 1.0, base, why="", wait_feasible=False)
        support = [INSERT_NOW, CONTINUE_CURRENT]
        by_id = {candidate.candidate_id: candidate for candidate in candidates}
        readiness = self.runtime.readiness(self.vault)
        ready = tuple(name for name in (DECIDER, LLM) if readiness.get(name) is None)
        key = _hash({"v": KEY_VERSION, "kind": "objective_interrupt", "plan_id": record.id, "block": current.id,
                     "item": item.practice_item_id, "as_of": _latest_attempt(self.repository),
                     "version": config.algorithms.algorithm_version, "settings": settings,
                     "objective": objective_settings(config), "ready": ready})
        now_iso = __import__("learnloop.clock", fromlist=["utc_now_iso"]).utc_now_iso(self.clock)
        # π_Q: the follow-up now (a repair block before the rest) or after the rest (at the next boundary).
        insert, cont = by_id[INSERT_NOW], by_id[CONTINUE_CURRENT]
        numeric = self._numeric_restraint(state, insert, cont, now_iso, key)
        if ready:
            entry = self.runtime.lookup(self.scope, key)
            if entry is None:
                entry = self._start(key, state, candidates, item, ready)
            from learnloop.daily_plan.router_chooser import _await as await_entry

            await_entry(self.runtime, entry, may_defer=self.may_defer, timeout=float(config.router.timeout_seconds))
            results = entry.results()
        else:
            entry = _NoModels(key, {"card": _build_card(self.card_builder, state, candidates)}, self.runtime.clock())
            results = {}
        for name in (DECIDER, LLM):
            results.setdefault(name, ComponentResult(name=name, status=NOT_READY, error=str(readiness.get(name) or "not_ready")))
        llm = results[LLM]
        llm_dist = ({INSERT_NOW: float(llm.p_yes), CONTINUE_CURRENT: 1.0 - float(llm.p_yes)}
                    if llm.status == ANSWERED and llm.p_yes is not None and 0.0 < float(llm.p_yes) < 1.0 else None)
        numeric_ok = numeric.status == ANSWERED and numeric.choice in support
        failed = [name for name, ok in ((mix.LLM, llm_dist is not None), (mix.NUMERIC, numeric_ok)) if not ok]
        w, weight_record = current_weight(self.repository, config, at=now_iso)
        effective = mix.effective_weights(w, failed)
        parts = mix.components(support, INSERT_NOW, llm=llm_dist, numeric_ref=numeric.choice if numeric_ok else None)
        decision_id = new_ulid()
        seed = self.runtime.seed(entry.key, decision_id) if self.runtime.seed is not None else mix.seed_for(entry.key, decision_id)
        drawn = mix.draw(support, parts, effective, float(settings["epsilon_min"]), seed)
        card = entry.material["card"]
        decider = results.get(DECIDER)
        titles = {lo_id: lo.title for lo_id, lo in self.vault.learning_objects.items()}
        trace = _trace(support=support, by_id=by_id, feasible=candidates, titles=titles, numeric=numeric, llm=None,
                       decider=None, staged_ref=INSERT_NOW, weight=(w, weight_record), effective=effective,
                       pi=drawn.pi, drawn=drawn, seed=seed, config=config, now_iso=now_iso, guard={},
                       stop_in_support=False, card_version=card.version)
        trace["policies"]["llm"] = {"status": llm.status, "distribution": llm_dist, "rationale": llm.rationale,
                                    "schema": rq.LLM_POLICY_RESTRAINT_SCHEMA, "model": llm.model}
        trace["policies"]["decider"] = {"status": decider.status if decider is not None else NOT_READY,
                                        "advice": ({"intervene_now": decider.p_yes} if decider is not None and
                                                   decider.status == ANSWERED else None)}
        latencies = [r.latency_ms for r in results.values() if r.latency_ms is not None]
        costs = [r.cost_usd for r in results.values() if r.cost_usd is not None]
        base.update(
            policy=mix.POLICY, decided_by=MODE if ready else "objective_no_models", decision_id=decision_id,
            design=mix.DESIGN, seed=seed, drawn_component=drawn.component, fallback=mix.fallback_label(failed),
            fallback_reasons={name: (llm.status if name == mix.LLM else numeric.status) for name in failed},
            mixture={"boundary_key": entry.key, "support": support, "staged_ref": INSERT_NOW, "k": len(support),
                     "epsilon": settings["epsilon_min"], "effective_weights": effective, "w": w, "failed": failed,
                     "llm_distribution": llm_dist, "numeric_choice": numeric.choice if numeric_ok else None,
                     "drawn_component": drawn.component, "u1": drawn.u1, "u2": drawn.u2, "pi": dict(drawn.pi),
                     "models": {name: result.summary() for name, result in sorted(results.items())},
                     "rationale": {"text": llm.rationale}},
            mixture_weights={"configured": {"w": w}, "effective": effective},
            model_distributions={"llm": llm_dist, "numeric": parts.get(mix.NUMERIC),
                                 "decider": ({INSERT_NOW: decider.p_yes, CONTINUE_CURRENT: 1 - decider.p_yes}
                                             if decider is not None and decider.status == ANSWERED and decider.p_yes is not None
                                             else None)},
            question_set_version=rq.RESTRAINT_QUESTION_SET,
            model_ids={"decider": results[DECIDER].model, "llm": llm.model, "llm_schema_version": rq.LLM_POLICY_RESTRAINT_SCHEMA},
            latency_ms=max(latencies) if latencies else None, cost_usd=round(sum(costs), 8) if costs else 0.0,
            payloads=_payloads(results), objective_trace=trace, **_card_fields(card),
        )
        why = router_why.FOLLOWUP_WAITS if drawn.chosen == CONTINUE_CURRENT else ""
        return RestraintOutcome(drawn.chosen, 1.0 if drawn.deterministic else drawn.propensity, base, why=why)

    def _numeric_restraint(self, state: PlanState, insert: BlockCandidate, cont: BlockCandidate, now_iso: str,
                           key: str) -> NumericPolicy:
        """π_Q on the two orders, valued as two blocks each; one cutoff, the same draws."""

        follow_minutes = float(insert.est_minutes)
        now_first = replace(insert, item_ids=(*insert.item_ids, *cont.item_ids),
                            est_minutes=follow_minutes + float(cont.est_minutes),
                            learning_object_ids=tuple(dict.fromkeys((*insert.learning_object_ids, *cont.learning_object_ids))))
        later = replace(cont, item_ids=(*cont.item_ids, *insert.item_ids),
                        est_minutes=follow_minutes + float(cont.est_minutes),
                        learning_object_ids=tuple(dict.fromkeys((*cont.learning_object_ids, *insert.learning_object_ids))))
        return run_numeric(self.vault, self.repository, state=state, support=[INSERT_NOW, CONTINUE_CURRENT],
                           candidates={INSERT_NOW: now_first, CONTINUE_CURRENT: later}, now_iso=now_iso,
                           seed=_hash({"numeric": key}),
                           deadline=self.runtime.clock() + float(self.vault.config.router.timeout_seconds),
                           clock=self.runtime.clock)

    def _start(self, key: str, state: PlanState, candidates: list[BlockCandidate], item: Any,
               ready: tuple[str, ...]) -> Prefetch:
        from functools import partial

        config = self.vault.config
        card = _build_card(self.card_builder, state, candidates)
        titles = {lo_id: lo.title for lo_id, lo in self.vault.learning_objects.items()}
        topic = titles.get(item.learning_object_id, item.learning_object_id)
        options = [rq.BlockOption(INSERT_NOW, f"Ask the follow-up on {topic} now, inside the current block."),
                   rq.BlockOption(CONTINUE_CURRENT, "Finish the current block first; the follow-up then opens the next block.")]
        state_text = rq.state_text(card.text, options, evidence=rq.evidence_from_card(card.json),
                                   extra=[f"A follow-up question on {topic} came out of the learner's last answer."])
        material = {"card": card, "card_hash": card.card_hash, "topic": topic, "state": state_text}

        def job(entry: Prefetch) -> None:
            from learnloop.daily_plan.router_chooser import _run_components
            from learnloop.db.repositories import Repository

            repository = Repository.attach(self.repository.sqlite_path)
            with self.runtime.spend.metered(repository, config, owner_kind=RECEIPT_OWNER, owner_id=entry.key):
                decider_request = rq.RestraintRequest(topic=topic, state=state_text)
                policy_request = rq.PolicyRequest(options=tuple(options), reference=options[1], state=state_text,
                                                  restraint_topic=topic)
                entry.request = decider_request

                class _Both:
                    """The Decider reads the R2c restraint request; the LLM policy its v3 one."""

                    question_set_version = decider_request.question_set_version
                    llm_schema_version = policy_request.llm_schema_version
                    decider_questions = decider_request.decider_questions
                    llm_prompt = policy_request.llm_prompt
                    state = state_text

                def parse_llm(raw: Any, _request: Any) -> tuple[float, str | None]:
                    p_yes, rationale, _evidence = rq.parse_llm_policy_restraint(raw)
                    return p_yes, rationale

                _run_components(self.runtime, entry, self.vault, repository, _Both(),
                                {DECIDER: lambda raw, _request: rq.parse_decider_restraint(raw), LLM: parse_llm},
                                card.card_hash)

        return self.runtime.start(self.scope, key, kind="plan_interrupt", budget=float(config.router.prefetch_timeout_seconds),
                                  material=material, components=ready, job=job)


__all__ = ["NUMERIC", "NumericPolicy", "ObjectiveChooser", "ObjectiveRestraintGate", "current_weight", "day_price",
           "objective_settings", "run_numeric"]
