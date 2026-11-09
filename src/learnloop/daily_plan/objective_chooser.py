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

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field, replace
from datetime import timedelta
import hashlib
import json
import logging
import math
import threading
import time
from typing import Any

from learnloop.clock import parse_utc
from learnloop.daily_plan import objective_inputs as OI
from learnloop.daily_plan.router_chooser import (
    INSERT_NOW,
    MODE as MIXTURE_MODE,
    NO_INTERVENTION,
    FollowupGate,
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
from learnloop.daily_plan.types import (
    CONTINUE_CURRENT,
    LESSON_OFFER_SUBTYPE,
    STOP_FOR_TODAY,
    STOP_OFFER_MINUTES,
    BlockCandidate,
    BlockChoice,
    DecisionPending,
    PlanState,
)
from learnloop.ids import new_ulid
from learnloop.router import requests as rq
from learnloop.router import why as router_why
from learnloop.router_objective import mix
from learnloop.router_objective import price as P
from learnloop.router_objective import stop_coin as SC
from learnloop.router_objective import value as V
from learnloop.router_objective import weight as W
from learnloop.router_objective_switches import stop_coin_rate

LOG = logging.getLogger(__name__)

NUMERIC = "numeric"
#: The prefetch material's key for the numeric policy's latest complete uncorrected answer (F1): a serve that finds
#: the job still waiting on the LLM policy's forecasts uses it instead of a timeout.
PUBLISHED = "numeric_published"
#: RO6's landing ruling R12: the prefetch material's key for the residual record with the carried valuation, set by
#: the job after the answer released the serve's wait; a serve that comes first censors that backup.
CARRIED = "numeric_carried_valuation"
#: The follow-up batch's item 4 (``carried_in_prefetch``): a decision's carried valuation deferred to the next
#: boundary's prefetch travels with the served answer (``NumericPolicy.carried``; Codex review F3), is registered at
#: the serve, run there, off the serving path, and recorded in a later trace.
#: ``keep`` (a resource bound): the most deferred carried valuations kept per database; past it the oldest is dropped
#: and its backup stays censored ``cutoff_unmatched``.
CARRY_LIMIT = 32
_CARRY_LOCK = threading.Lock()
_CARRY: dict[str, list[dict[str, Any]]] = {}
MODE = "objective"
KEY_VERSION = 1
WHY_VERSION = "router_why_v3"
#: Per decision: the LLM policy's and the numeric policy's statuses a share can fall back from.
_FAILURES = frozenset({TIMEOUT, FAILED, INVALID, NOT_READY, "spend", "unreachable"})


def objective_settings(config: Any) -> dict[str, Any]:
    """The settings a prefetch boundary key names. At the follow-up batch's tag also its switches as they serve
    (landing ruling R12, ``followup_switch_snapshot``), so a flip between a prefetch and its serve starts a new job;
    below the tag the key keeps its predecessor's bytes."""

    from learnloop.router_objective_switches import followup_switch_snapshot

    section = config.router_objective
    out = {key: getattr(section, key) for key in (
        "enabled", "sensors_in_value", "rollout_theta_draws", "rollout_theta_draws_max", "horizon_days",
        "undated_use_density", "dated_use_weight", "session_gap_minutes", "session_guard_minutes",
        "evaluation_window_days", "llm_weight_prior", "llm_min_share", "numeric_min_share", "delta_prior_sd",
        "effect_slope_prior_mean", "effect_slope_prior_variance", "stop_accept_prior_a", "stop_accept_prior_b",
        "llm_card_token_budget", "receipts")}
    snapshot = followup_switch_snapshot(config)
    if snapshot is not None:
        out["followup_switches"] = snapshot
    return out


def _local_date(now_iso: str) -> str:
    moment = parse_utc(now_iso)
    return (moment.astimezone().date().isoformat() if moment is not None else now_iso[:10])


# -- the price, the weight -------------------------------------------------------------------------------


def _merged(config: Any) -> bool:
    """The follow-up batch's item 3 (Codex review F2): the rollouts' merged tail sessions serve only at the batch's
    tag with ``[router_objective] merged_sessions``. The values of a fixed number of draws are the same either way,
    but a faster draw lets a deadline-bound evaluation complete more of them, so below the tag, or off, every
    rollout runs mvp-0.49's per-block loop (the same time per draw)."""

    if config is None:
        return False
    from learnloop.router_objective_switches import followup_on

    return followup_on(config, "merged_sessions")


def _consistent_draw(config: Any) -> bool:
    """The follow-up batch's landing ruling R1: the rollouts draw a practised topic's practice outcome from the memory
    model's own ``P(perform)`` (``value.REVIEW_DRAW_VERSION``) only at the batch's tag with ``[router_objective]
    consistent_review_draw``; below the tag, or off, mvp-0.49's draw from AD's predictive, draw for draw."""

    if config is None:
        return False
    from learnloop.router_objective_switches import followup_on

    return followup_on(config, "consistent_review_draw")


def _held_link(config: Any) -> bool:
    """Router speed, item 1 (Codex review F1): R9's link values held per role in the rollouts
    (``value.Inputs.ad_link``'s ``held_ad_link``) only at the follow-up batch's tag with ``[router_objective]
    held_ad_link``; off, the batch's landing code (the same values per draw, at the landing's time per draw, so a
    deadline-bound evaluation completes the draws it completed then)."""

    if config is None:
        return False
    from learnloop.router_objective_switches import followup_on

    return followup_on(config, "held_ad_link")


def _serving_switches(config: Any) -> dict[str, Any]:
    """The trace's ``versions.serving_switches`` (landing ruling R8), or nothing below the batch's tag."""

    from learnloop.router_objective_switches import followup_generator_switches

    switches = followup_generator_switches(config) if config is not None else None
    return {"serving_switches": switches} if switches is not None else {}


def _rollout_options(config: Any) -> dict[str, bool]:
    """The rollouts' serving options, for every rollout of one decision (its evaluation and refinement, the
    correction, the carried valuation, the baselines and the day's gain curve) or for none: one place."""

    return {"merged_sessions": _merged(config), "consistent_review_draw": _consistent_draw(config),
            "held_ad_link": _held_link(config)}


def _frontier(inputs: V.Inputs, *, draws: int, seed: str, **rollout: bool
              ) -> tuple[dict[float, float], dict[str, Any]]:
    mbar = float(inputs.price.remembered)
    d = float(inputs.tail_block_minutes)
    points = sorted({0.0, mbar, mbar + d, 2 * mbar})
    curve = V.gain(inputs, points, draws=draws, seed=f"{seed}:frontier", **rollout)
    return curve, {"points": [{"minutes": m, "gain": curve[m]} for m in points],
                   "display": "; ".join(f"{m:.0f} minutes: predicted gain {curve[m]:+.3f}" for m in points if m > 0)
                   + " (predictions)"}


def _posterior_price(repository: Any, inputs: V.Inputs, config: Any, *, local_date: str, draws: int,
                     seed: str) -> tuple[P.Seeded, dict[str, Any]] | None:
    """RO5 §9 item 1: once a randomized stop offer has a response, κ0 is the posterior the seed is folded into
    (:mod:`learnloop.router_objective.stop_coin`) and the daily re-centring ends; the frontier is still drawn once a
    day, for display. None in the seed regime (the coin off, or no randomized response yet)."""

    from learnloop.db.stores import router_objective as store
    from learnloop.router_objective import stop_coin as SC
    from learnloop.router_objective_switches import stop_coin_rate

    if config is None or stop_coin_rate(config) <= 0:
        return None
    with repository.connection() as connection:
        posterior = SC.handed_over(connection, config)
        if posterior is None or float(posterior.get("kappa0") or 0.0) <= 0:
            return None
        today = connection.execute(
            "SELECT decision_id FROM router_objective_traces WHERE local_date = ? AND kappa_how = ? "
            "AND decision_kind = 'plan_block' ORDER BY created_at, id LIMIT 1", (local_date, SC.POSTERIOR)
        ).fetchone() if store.table_present(connection, store.TRACES) else None
    if today is not None or not inputs.topics:
        frontier: dict[str, Any] = {"carried_from": today[0]} if today is not None else {"status": "no_topics"}
        gain: dict[str, float] = {}
    else:
        curve, frontier = _frontier(inputs, draws=draws, seed=seed, **_rollout_options(config))
        gain = {str(k): v for k, v in curve.items()}
    return P.Seeded(kappa0=float(posterior["kappa0"]), how=SC.POSTERIOR, regime=SC.POSTERIOR_REGIME, gain=gain,
                    local_date=local_date, posterior=posterior), frontier


def day_price(repository: Any, inputs: V.Inputs, *, local_date: str, draws: int, seed: str,
              config: Any = None) -> tuple[P.Seeded, dict[str, Any]]:
    """κ0 for this decision (§8.6): the day's first decision computes the seed from the gain curve, later ones
    carry it. Returns the price and the frontier (G against minutes) it came from. At RO5's tag with the stop coin
    on, the posterior from offered stops once a randomized one has a response (:func:`_posterior_price`)."""

    from learnloop.db.stores import router_objective as store

    handed = _posterior_price(repository, inputs, config, local_date=local_date, draws=draws, seed=seed)
    if handed is not None:
        return handed
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
    curve = V.gain(inputs, points, draws=draws, seed=f"{seed}:frontier", **_rollout_options(config))
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


def _seed_record(seeds: W.Seeds) -> dict[str, float]:
    return {"w0": seeds.w0, "ell_l": seeds.ell_l, "ell_q": seeds.ell_q, "s0": seeds.s0, "p0": seeds.p0,
            "m0": seeds.m0}


def current_weight(repository: Any, config: Any, *, at: str) -> tuple[float, dict[str, Any]]:
    """``w_i`` (§8.7) from the scores whose windows closed before ``at``; with no randomized check, none forms."""

    from learnloop.db.stores import router_objective as store

    seeds = W.Seeds.from_config(config)
    from learnloop.router_objective_switches import calibrated_weight_on, objective_scores_on

    # Codex review F5: RO5's scores move w only while the check arm is on (its switch, not the tag and history):
    # with check_rate "off" the weight is RO4's calculation exactly, whatever checks were assigned before.
    if calibrated_weight_on(config) and _randomized_checks_exist(repository):
        # RO5 (§9 item 2): the randomized checks observe the uses, so closed windows form scores and w can move.
        if not objective_scores_on(config):
            posterior = W.posterior([], seeds, at=at)
            return W.weight(posterior.p, seeds), {
                "posterior": posterior.as_dict(), "seeds": _seed_record(seeds),
                "note": "RO0's receipts are off: no comparison score is formed, so w stays at its prior"}
        from learnloop.router_objective import scores as S

        with repository.connection() as connection:
            details = S.scores(connection, config, at=at)
        posterior = W.posterior([detail.scored for detail in details], seeds, at=at)
        unique = W.unique_assessments((key, detail.scored.decision_id) for detail in details
                                      for key in detail.assessments)
        note = ("w moved on closed scores from randomized checks" if posterior.source == "posterior" else
                f"randomized checks exist; w stays at its prior ({posterior.source}: {posterior.n} closed scores)")
        return W.weight(posterior.p, seeds), {"posterior": posterior.as_dict(), "seeds": _seed_record(seeds),
                                              "note": note, "unique_assessments": unique,
                                              "scores_version": S.VERSION}
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
    #: ``final`` (the job's last answer), or ``published_uncorrected`` (served from the job's earlier publication
    #: while it was still waiting on the LLM policy's forecasts: F1)
    stage: str = "final"
    #: RO6 (§10): the learned tail's residual record (:mod:`learnloop.router_objective.tail_serve`); None below the
    #: tag, with the switch off, or on a decision it does not value (a mid-block follow-up)
    residual: Mapping[str, Any] | None = None
    #: The follow-up batch's item 4 (Codex review F3): this answer's own carried valuation, frozen to the inputs it
    #: used (``compute(deadline=...)``), when its residual is pending; whichever answer serves (an early publication
    #: or the final one) hands its own to the next boundary's prefetch. Never serialized.
    carried: Callable[..., dict[str, Any]] | None = field(default=None, repr=False, compare=False)
    #: Landing ruling R12: the follow-up batch's generator switches this answer was computed under (frozen at the
    #: job's start), which the trace records, never the serving config's; None below the batch's tag.
    switches: Mapping[str, bool] | None = None


def generator_now(config: Any, objective: str | None = None) -> str:
    """RO6: the generator version a decision made now is logged under (``tail_data.generator`` over its trace).
    ``objective``: the hash of the objective the decision values (``tail_data.objective_hash`` over its goals and
    horizon; landing ruling R2). At the follow-up batch's tag its serving switches are part of it (its landing
    ruling R8), as the trace records them (``versions.serving_switches``)."""

    from learnloop.router_objective import tail_data as TD
    from learnloop.router_objective_switches import followup_generator_switches

    seeds = W.Seeds.from_config(config)
    return TD.generator_key(TD.generator_payload(
        algorithm_version=str(config.algorithms.algorithm_version), objective=V.OBJECTIVE_VERSION,
        tail=V.TAIL_VERSION, terminal=V.TERMINAL_VERSION, horizon_days=float(config.router_objective.horizon_days),
        llm_schema=rq.LLM_POLICY_SCHEMA, seeds=_seed_record(seeds), epsilon=float(config.router.epsilon_min),
        objective_definition=objective, switches=followup_generator_switches(config),
        # Teacher TE3b: the features version served (its ``lesson`` indicator: a change point once, at its tag).
        features=TD.features_version(config)))


def run_numeric(vault: Any, repository: Any, *, state: PlanState, support: Sequence[str],
                candidates: Mapping[str, BlockCandidate], now_iso: str, seed: str, deadline: float | None,
                keep_going: Any = None, forecasts: Any = None, clock: Any = time.monotonic, publish: Any = None,
                sequences: Mapping[str, Sequence[BlockCandidate]] | None = None,
                learned_tail: bool = False, tail_snapshot: Mapping[str, Any] | None = None,
                carried_valuation: bool = True,
                defer_carried: Callable[[Callable[[], dict[str, Any]]], None] | None = None) -> NumericPolicy:
    """π_Q end to end: the frozen inputs, the day's price, ``Q̄`` with common random numbers (more draws while
    ``keep_going()``), then, once the LLM policy's forecasts are in (``forecasts()``: None while out), the effect
    correction; the argmax with the tie rule; the evaluation's baselines.

    ``publish(policy)`` receives each complete uncorrected answer as soon as it exists, before any wait on the LLM
    policy, so the numeric policy's availability never depends on the LLM's (Codex review F1); the correction is
    applied opportunistically after. ``sequences``: candidates valued as ordered sub-actions (§8.3's mid-block
    alternatives, F5).

    ``learned_tail`` (RO6, §10; a ``plan_block`` decision): at the tag with the switch on, the argmax and its tie
    rule run on ``Ṽ = V_tail + ŵ·V_residual`` (:mod:`learnloop.router_objective.tail_serve`), computed before the
    rollouts; ``Q̄`` and every term stay the tail's. ``tail_snapshot``: the residual's mutable inputs read at the
    decision's moment (:func:`learnloop.router_objective.tail_serve.snapshot`, taken by the caller before any
    asynchronous work: Codex review of RO6, F4). ``carried_valuation``: the second valuation at the latest earlier
    decision's cutoff runs after the answer is published (the prefetch job's, after ``publish``); False where the
    answer is served at once with nothing to publish into (the no-model branch): it is not run on the learner's
    serving path and the transition into this decision is censored ``cutoff_unmatched`` (RO6's landing ruling R3).
    ``defer_carried`` (the prefetch job; RO6's landing ruling R12): the answer returns with the carried valuation
    pending and ``defer_carried(compute)`` receives it, run by the job only after the answer is released to the
    serve; a serve that takes the answer first censors the backup (``cutoff_unmatched``)."""

    started = clock()
    config = vault.config
    section = config.router_objective
    try:
        inputs, actions, sources = OI.build(vault, repository, state=state, support=support, candidates=candidates,
                                            now_iso=now_iso, sequences=sequences)
        residual_record: Mapping[str, Any] | None = None
        unmeasured: frozenset[str] | None = None
        from learnloop.router_objective_switches import learned_tail_on

        if learned_tail and learned_tail_on(config):
            from learnloop.router_objective import tail_data as TD
            from learnloop.router_objective import tail_serve

            # Landing ruling R2: the objective this decision values (its goals as the trace freezes them, and the
            # horizon) is hashed into the trace and is part of the generator key.
            # Landing ruling R11: and §8.7's population with its effective densities (the retention scope and the
            # densities outside goals), read as the trace freezes it (evaluation.uses.topics).
            # The follow-up batch's item 5: at its tag, the retention scope read by its density (a scope extension).
            extension = TD.scope_extension_on(config)
            objective = TD.objective_hash(sources.get("goals") or {}, float(section.horizon_days),
                                          (sources.get("population") or {}).get("los") or {},
                                          scope_extension=extension)
            residual_record = tail_serve.residual(repository, config, inputs=inputs, actions=actions, now_iso=now_iso,
                                                  generator_now=generator_now(config, objective), frozen=tail_snapshot,
                                                  clock=clock)
            residual_record = {**residual_record,
                               "objective": {"hash": objective,
                                             "version": (TD.OBJECTIVE_DEFINITION_EXTENSION_VERSION if extension
                                                         else TD.OBJECTIVE_DEFINITION_VERSION)}}
            # Landing ruling R7: the topics no check could measure as of the draw; their share of each Q̄ is kept
            # apart on the same rollouts (terms.unmeasured_reward), so the tail's predicted contrast can be
            # restricted to the measurable terms; Q̄ and the choice are unchanged.
            measurable = tail_serve.measurable(tail_snapshot, inputs, now_iso=now_iso)
            if measurable is not None:
                unmeasured = frozenset(measurable["unmeasured"])
                residual_record = {**residual_record, "measurable": measurable}
        local_date = _local_date(now_iso)
        # The day's seed is computed once a day, so it takes the most draws (a marginal gain is a small difference
        # of two large sums; at 8 draws its noise is of the order of the signal).
        priced, frontier = day_price(repository, inputs, local_date=local_date,
                                     draws=int(section.rollout_theta_draws_max), seed=seed, config=config)
        inputs = replace(inputs, price=replace(inputs.price, kappa0=priced.kappa0, regime=priced.regime))
        draws, ceiling = int(section.rollout_theta_draws), int(section.rollout_theta_draws_max)
        cached: dict[str, Any] = {}
        # The follow-up batch's item 3 (Codex review F2) and landing ruling R1: every rollout of this decision, or
        # none, merged; every one, or none, with the memory model's own review draw.
        rollout = _rollout_options(config)
        # Landing ruling R12: the generator switches this job computes under, frozen with its answers (the trace
        # records these, not the serving config's; the residual's generator above was read from the same config).
        from learnloop.router_objective_switches import followup_generator_switches

        frozen_switches = followup_generator_switches(config)

        def answered(evaluation: V.Evaluation, used: V.Inputs, acts: Sequence[V.Action], corrected: bool) -> NumericPolicy:
            if residual_record is not None and residual_record.get("status") == "applied":
                from learnloop.router_objective import tail_serve

                choice, tie = V.numeric_choice(tail_serve.shifted(evaluation, residual_record), support)
                tie = {**tie, "on": "v_tilde = v_tail + w_hat * v_residual",
                       "tail_argmax": V.numeric_choice(evaluation, support)[1]["argmax"]}
            else:
                choice, tie = V.numeric_choice(evaluation, support)
            if "baselines" not in cached:
                # The pre-action belief under the tail: no action and no correction enters it.
                cached["baselines"] = V.baselines(used, int(section.evaluation_window_days),
                                                  draws=min(evaluation.draws, 8), seed=seed, **rollout)
            return NumericPolicy(status=ANSWERED, choice=choice, tie=tie, evaluation=evaluation, inputs=used,
                                 actions=tuple(acts), sources=sources, price=priced, frontier=frontier,
                                 baselines=cached["baselines"], corrected=corrected,
                                 latency_ms=int(round((clock() - started) * 1000)), residual=residual_record,
                                 switches=frozen_switches)

        def carried_compute(record: Mapping[str, Any], at_inputs: V.Inputs, at_actions: Sequence[V.Action],
                            at_cutoff: float) -> Callable[..., dict[str, Any]]:
            """The carried valuation of one answer, frozen to the inputs it used (R12; item 4)."""

            at_draws, at_deadline = draws, deadline

            def compute(record: Mapping[str, Any] = record, deadline: float | None = None) -> dict[str, Any]:
                from learnloop.router_objective import tail_serve as TS

                # ``deadline``: a later prefetch's own, when the valuation was deferred to it (the follow-up
                # batch's item 4); else this job's.
                at_previous = V.evaluate(at_inputs, at_actions, draws=at_draws, seed=seed,
                                         deadline=at_deadline if deadline is None else deadline,
                                         clock=clock, cutoff=at_cutoff, **rollout)
                return TS.with_carried_values(record, at_previous)

            return compute

        # The follow-up batch's item 4 (Codex review F3): at its tag, an early publication is an answer that can
        # serve (``published_uncorrected``) before the job installs anything, so it carries its own pending carried
        # valuation, frozen to its own (uncorrected) inputs; off, or below the tag, RO6's publication exactly.
        early_carry: float | None = None
        if publish is not None and defer_carried is not None and residual_record is not None and _carry_on(config):
            from learnloop.router_objective import tail_serve

            early_carry = tail_serve.carried_cutoff(residual_record)
        on_complete = None
        if publish is not None:
            def on_complete(evaluation: V.Evaluation) -> None:
                policy = answered(evaluation, inputs, actions, False)
                if early_carry is not None and residual_record is not None:
                    pending_early = tail_serve.pending_after_the_answer(residual_record)
                    policy = replace(policy, residual=pending_early,
                                     carried=carried_compute(pending_early, inputs, tuple(actions), early_carry))
                publish(policy)
        # (``unmeasured`` only at RO6's tag with the learned tail on; None leaves the evaluation as mvp-0.48's)
        measured = {"unmeasured": unmeasured} if unmeasured is not None else {}
        evaluation = V.evaluate(inputs, actions, draws=draws, seed=seed, max_draws=ceiling, keep_going=keep_going,
                                deadline=deadline, clock=clock, on_complete=on_complete, **rollout,
                                **measured)
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
                    again = V.evaluate(with_llm, acts, draws=evaluation.draws, seed=seed, deadline=deadline, clock=clock,
                                       **rollout, **measured)
                    if again.complete:
                        evaluation, inputs, actions, corrected = again, with_llm, acts, True
        if not evaluation.complete:
            return NumericPolicy(status=TIMEOUT, inputs=inputs, actions=tuple(actions), sources=sources, price=priced,
                                 frontier=frontier, latency_ms=int(round((clock() - started) * 1000)),
                                 error="no answer within the budget", switches=frozen_switches)
        own_carry: Callable[..., dict[str, Any]] | None = None
        if residual_record is not None:
            from learnloop.router_objective import tail_serve

            carried = tail_serve.carried_cutoff(residual_record)
            if carried is not None and not carried_valuation:
                # Landing ruling R3: never on the learner's serving path; the backup into it is censored.
                residual_record = tail_serve.not_on_the_serving_path(residual_record)
            elif carried is not None and defer_carried is not None:
                # Landing ruling R12: the answer is released first; the carried valuation runs after it (the
                # prefetch job calls ``compute`` once the numeric policy's completion event is set).
                pending = tail_serve.pending_after_the_answer(residual_record)
                compute = carried_compute(pending, inputs, tuple(actions), carried)
                defer_carried(compute)
                residual_record = pending
                if _carry_on(config):
                    # The follow-up batch's item 4: the answer carries its own (Codex review F3).
                    own_carry = compute
            elif carried is not None:
                # RO6 (Codex re-review F3): the candidates valued again with every rollout at the latest earlier
                # decision's cutoff, on the inputs the answer used, for that decision's backup only (a regression
                # target, so the first batch's draws: its noise averages out in the fit, and no refinement is paid).
                at_previous = V.evaluate(inputs, actions, draws=draws, seed=seed, deadline=deadline, clock=clock,
                                         cutoff=carried, **rollout)
                residual_record = tail_serve.with_carried_values(residual_record, at_previous)
        final = answered(evaluation, inputs, actions, corrected)
        return replace(final, carried=own_carry) if own_carry is not None else final
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
    # Router speed, item 2: the card's build and the numeric policy's share one read of the combiner's fit while no
    # write is committed between them (OI.decision_reads; Codex review F2).
    with runtime.spend.metered(repository, config, owner_kind=RECEIPT_OWNER, owner_id=entry.key), OI.decision_reads():
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

        def publish(policy: NumericPolicy) -> None:
            with entry.lock:
                entry.material[PUBLISHED] = policy

        deferred: list[Callable[[], dict[str, Any]]] = []

        numeric = run_numeric(
            vault, repository, state=material["state"], support=material["support"], candidates=material["by_id"],
            now_iso=material["decided_at"], seed=material["numeric_seed"], deadline=entry.deadline,
            keep_going=lambda: LLM in entry.events and not entry.events[LLM].is_set() and runtime.clock() < entry.deadline,
            forecasts=(lambda: _wait_llm(entry, runtime)) if LLM in entry.events else None, clock=runtime.clock,
            publish=publish, learned_tail=True, tail_snapshot=material.get("tail_snapshot"),
            defer_carried=deferred.append)
        with entry.lock:
            entry.components[NUMERIC] = ComponentResult(name=NUMERIC, status=numeric.status, parsed=numeric,  # type: ignore[arg-type]
                                                        latency_ms=numeric.latency_ms, error=numeric.error)
        # Landing ruling R12: the answer releases the serve's wait; the carried valuation runs only after it, and a
        # serve that has already taken the answer censors that backup (``_decide_objective``).
        carry = _carry_on(config)
        # The follow-up batch's item 4: this decision's own carried valuation waits for the next boundary's prefetch;
        # each answer that can serve (the final one above, an early publication) carries its own (``carried``,
        # Codex review F3), so the serve registers it whichever comes first.
        entry.events[NUMERIC].set()
        if carry:
            # ... and this job runs the ones earlier decisions left, now that its own answer is out.
            _drain_carry(sqlite_path, deadline=entry.deadline)
            deferred = []
        for compute in deferred:
            try:
                carried_record = compute()
            except Exception:  # noqa: BLE001 - the backup's value never fails the decision: it is censored
                LOG.warning("router objective: the carried valuation failed", exc_info=True)
                continue
            with entry.lock:
                entry.material[CARRIED] = carried_record
        for thread in threads:
            thread.join(timeout=entry.remaining(runtime.clock()) + 1.0)


def _with_carried(numeric: "NumericPolicy | None", entry: Any) -> "NumericPolicy | None":
    """Landing ruling R12: the served answer's residual with the carried valuation if the job had it before this
    serve (``CARRIED``), else marked valued too late (``not_valued_before_the_serve``: the backup into this
    decision is censored ``cutoff_unmatched``). An answer with nothing pending is returned as it is."""

    from learnloop.router_objective import tail_serve

    if numeric is None or not tail_serve.is_pending(numeric.residual):
        return numeric
    lock = getattr(entry, "lock", None)
    material = getattr(entry, "material", {}) or {}
    if lock is not None:
        with lock:
            carried = material.get(CARRIED)
    else:
        carried = material.get(CARRIED)
    if isinstance(carried, Mapping):
        return replace(numeric, residual=carried)
    return replace(numeric, residual=tail_serve.not_before_the_serve(numeric.residual))


def _carry_on(config: Any) -> bool:
    # One predicate for the serving side and the reading side (tail_data.logged; Codex review F1).
    from learnloop.router_objective import tail_data as TD

    return TD.carried_in_prefetch_on(config)


def _register_carry(sqlite_path: Any, decision_id: str, compute: Callable[[], dict[str, Any]]) -> None:
    """The follow-up batch's item 4: a decision served before its carried valuation existed leaves the valuation
    (its own frozen inputs, in ``compute``) to the next boundary's prefetch."""

    with _CARRY_LOCK:
        waiting = _CARRY.setdefault(str(sqlite_path), [])
        waiting.append({"decision_id": decision_id, "compute": compute, "record": None, "carriers": []})
        del waiting[:-CARRY_LIMIT]


def _drain_carry(sqlite_path: Any, *, deadline: float | None = None) -> int:
    """Run every deferred carried valuation of this database not yet run (a prefetch job's, after its own answer
    released the serve's wait; the no-model branch's thread, after its serve), each by ``deadline`` (the runner's
    own). Never the serving thread's work. Returns how many ran."""

    with _CARRY_LOCK:
        todo = [entry for entry in _CARRY.get(str(sqlite_path), []) if entry["record"] is None
                and not entry.get("running")]
        for entry in todo:
            entry["running"] = True
    ran = 0
    for entry in todo:
        try:
            record = entry["compute"](deadline=deadline)
        except Exception:  # noqa: BLE001 - the backup stays censored; the decision is untouched
            LOG.warning("router objective: a deferred carried valuation failed", exc_info=True)
            record = {"previous": {"q_status": "not_valued_in_the_next_prefetch"}}
        with _CARRY_LOCK:
            entry["record"] = record
            entry["running"] = False
        ran += 1
    return ran


def _carried_for(repository: Any, decision_id: str) -> list[dict[str, Any]]:
    """The deferred carried valuations ready to be recorded in this decision's trace (``carried_for``). Each stays
    waiting until a trace that holds it is known to be written (a choice computed and never logged writes nothing),
    then is dropped, so a record is carried until one carrier is in the log."""

    key = str(repository.sqlite_path)
    with _CARRY_LOCK:
        waiting = list(_CARRY.get(key, []))
    carriers = sorted({carrier for entry in waiting for carrier in entry["carriers"]})
    written: set[str] = set()
    if carriers:
        marks = ",".join("?" for _ in carriers)
        with repository.connection() as connection:
            written = {str(row[0]) for row in connection.execute(
                f"SELECT decision_id FROM router_objective_traces WHERE decision_id IN ({marks})", carriers)}
    out: list[dict[str, Any]] = []
    with _CARRY_LOCK:
        kept = []
        for entry in _CARRY.get(key, []):
            if written & set(entry["carriers"]):
                continue
            record = entry["record"]
            valued = (isinstance(record, Mapping) and isinstance(record.get("previous"), Mapping)
                      and record["previous"].get("q_status") == "valued")
            if record is not None and not valued:
                continue  # it ran and found no value (deadline, failure): nothing to carry
            kept.append(entry)
            if valued:
                entry["carriers"].append(decision_id)
                out.append({"decision_id": entry["decision_id"], "previous": dict(record["previous"]),
                            "basis": "the decision's own frozen inputs, valued at its earlier decision's cutoff in a "
                                     "later boundary's prefetch (off the serving path)"})
        _CARRY[key] = kept
    return out


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
        elif ref in by_id and by_id[ref].subtype == LESSON_OFFER_SUBTYPE:
            # Teacher TE3b: the offer card, in plain words.
            candidate = by_id[ref]
            topic = ", ".join(dict.fromkeys(titles.get(lo, lo) for lo in candidate.learning_object_ids))
            out[ref] = f"offer a lesson on {topic} (about {max(1, round(candidate.est_minutes))} min)"
        elif ref in by_id:
            candidate = by_id[ref]
            what = candidate.reading.section_title if candidate.reading is not None else ", ".join(
                dict.fromkeys(titles.get(lo, lo) for lo in candidate.learning_object_ids)) or candidate.lane
            out[ref] = f"{candidate.lane}: {what} ({max(1, round(candidate.est_minutes))} min)"
    return out


def _score_note(config: Any) -> str:
    from learnloop.router_objective_switches import CHECKS_OFF, check_mode

    if check_mode(config)[0] != CHECKS_OFF:
        return ("forms when the window closes, from the randomized checks it holds (r = the day's assignment "
                "probability x the running completion rate)")
    return "none forms until RO5's randomized checks: no valued use has r > 0"


def _goal_dates(numeric: "NumericPolicy | None") -> dict[str, Any]:
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


def _offer_option(candidate: BlockCandidate, titles: Mapping[str, str]) -> rq.BlockOption:
    """Teacher TE3b: the lesson offer as one more option of the LLM policy's existing request (and the Decider's
    advice): its target, its reason, its minutes and ``P(accept)`` (spec §15.1a; no new request)."""

    record = dict((candidate.annotations or {}).get("lesson_offer") or {})
    topic = ", ".join(dict.fromkeys(titles.get(lo, lo) for lo in candidate.learning_object_ids))
    p_accept = (record.get("p_accept") or {}).get("mean")
    return rq.BlockOption(ref=candidate.candidate_id, description=rq.lesson_offer_description(
        topic=topic, why=candidate.reason, est_minutes=candidate.est_minutes,
        p_accept=float(p_accept) if p_accept is not None else None))


def _offer_trace(candidate: BlockCandidate, valued: Any, action: Any, inputs: Any,
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
                         "updates": (record.get("model") or {}).get("updates")},
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
    # Landing ruling R12: the generator switches the numeric answer was computed under (frozen with it); with no
    # numeric answer, the serving config's (R8's ``followup_generator_switches``; None below the batch's tag).
    served_switches = (numeric.switches if numeric is not None and numeric.switches is not None
                       else _serving_switches(config).get("serving_switches"))
    topic_by_lo = {topic.lo: topic for topic in (inputs.topics if inputs is not None else ())}
    actions = {action.ref: action for action in (numeric.actions if numeric is not None else ())}
    llm_parsed = getattr(llm, "parsed", None) if llm is not None and llm.status == ANSWERED else None
    residual_record = numeric.residual if numeric is not None else None
    residual_applied = bool(residual_record) and residual_record.get("status") == "applied"  # type: ignore[union-attr]
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
            if residual_applied:
                # RO6 (§10): ŵ, V_tail (the tail's Q̄ above), V_residual and Ṽ per candidate.
                from learnloop.router_objective import tail_serve

                terms.update(tail_serve.candidate_terms(numeric.residual, ref, valued.q))  # type: ignore[union-attr, arg-type]
        candidates[ref] = {
            "label": labels.get(ref, ref), "kind": action.kind if action is not None else None,
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
        if ref in by_id and by_id[ref].subtype == LESSON_OFFER_SUBTYPE:
            # Teacher TE3b (spec_teacher_v1 rev 5 §15.1a): the offer's sensors, its branches' terms and the split.
            candidates[ref]["offer"] = _offer_trace(by_id[ref], valued, action, inputs, topic_by_lo,
                                                    candidates[ref].get("terms"))
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
    # §8.7's population, frozen from the goals and retention commitments alone (F11): a candidate-only topic is
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
        # RO6 (§10): the learned tail's record, frozen (ŵ with its slope and rank, the fit, each candidate's features,
        # V_tail, V_residual and Ṽ), so the terms recompute from the trace alone.
        section_record = dict(residual_record)
        if residual_applied:
            from learnloop.router_objective import tail_serve

            section_record["candidates"] = {
                ref: {**dict(entry), **tail_serve.candidate_terms(residual_record, ref,
                                                                    rows[ref].q if ref in rows else None)}
                for ref, entry in (residual_record.get("candidates") or {}).items()}
        extra["residual"] = section_record
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
                   "epsilon": float(config.router.epsilon_min)},
        "evaluation": {"uses": uses, "window_days": window, "window_closes_at": window_closes, "c0": c0,
                       "c0_basis": "the tail's cost at the remembered minutes (no earlier window of costs at this version)",
                       "objective_version": V.OBJECTIVE_VERSION,
                       "score": _score_note(config)},
        "frontier": dict(numeric.frontier) if numeric is not None else {},
        "inputs_sources": {key: value for key, value in sources.items() if key != "population"},
        "versions": {"objective": V.OBJECTIVE_VERSION, "tail": V.TAIL_VERSION, "terminal": V.TERMINAL_VERSION,
                     "horizon_days": float(section.horizon_days), "memory_model": inputs.combiner.as_dict()
                     if inputs is not None else None, "kappa": price,
                     "learning": inputs.learning.source if inputs is not None else None,
                     "card": card_version, "llm_schema": rq.LLM_POLICY_SCHEMA,
                     "goals": {goal_id: {"source": goal.get("source"), "contract": goal.get("contract_version_id")}
                               for goal_id, goal in ((numeric.sources if numeric is not None else {}).get("goals") or {}).items()},
                     # The follow-up batch's landing ruling R1: the rollouts' review draw, named only when it serves
                     # (below the tag, or off, the trace keeps mvp-0.49's bytes).
                     **({"review_draw": V.REVIEW_DRAW_VERSION}
                        if served_switches is not None and served_switches.get("consistent_review_draw") else {}),
                     # Landing ruling R9: AD's own predictive in the rollouts, named only when it serves.
                     **({"ad_link": V.AD_LINK_VERSION}
                        if inputs is not None and inputs.ad_link is not None else {}),
                     # Landing ruling R8: the batch's serving switches as they served, part of the generator
                     # payload (``tail_data.generator``); only at the batch's tag. R12: the numeric answer's own.
                     **({"serving_switches": dict(served_switches)} if served_switches is not None else {})},
    }


@dataclass
class ObjectiveChooser(RouterChooser):
    """``router_objective_v1``: the two policies' learned mix over the staged frame's support."""

    name: str = mix.POLICY

    def _seed(self, key: str, decision_id: str) -> str:
        return self.runtime.seed(key, decision_id) if self.runtime.seed is not None else mix.seed_for(key, decision_id)

    def choose(self, state: PlanState, feasible: Sequence[BlockCandidate]) -> BlockChoice:
        # Teacher TE3b (spec_teacher_v1 rev 5 §15.1a): a lesson offer the boundary added is never the staged rule's
        # pick nor in staged's top-k order: it joins the support beside them (one offer a decision). With none, the
        # predecessor's decision exactly.
        offers = [candidate for candidate in feasible if candidate.subtype == LESSON_OFFER_SUBTYPE]
        if offers:
            feasible = [candidate for candidate in feasible if candidate.subtype != LESSON_OFFER_SUBTYPE]
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
        if offers:
            # The offer joins the support after the blocks and before stop (ties go to staged's order first).
            offer = offers[0]
            by_id[offer.candidate_id] = offer
            at = support.index(STOP_FOR_TODAY) if STOP_FOR_TODAY in support else len(support)
            support = [*support[:at], offer.candidate_id, *support[at:]]
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
        if self.start_only:
            if ready and self.runtime.lookup(self.scope, key) is None:
                self._start_objective(key, state, feasible, support, by_id, ready, now_iso)
            raise DecisionPending(key)
        if ready:
            entry = self.runtime.lookup(self.scope, key)
            if entry is None:
                entry = self._start_objective(key, state, feasible, support, by_id, ready, now_iso)
            _await(self.runtime, entry, may_defer=self.may_defer, timeout=float(config.router.timeout_seconds))
        else:
            card = _build_card(self.card_builder, state, feasible)
            # The follow-up batch's item 4: at its tag the carried valuation is deferred (run after the serve, off
            # its path); below it, R3: no second valuation at all here.
            no_model_deferred: list[Callable[..., dict[str, Any]]] = []
            carry = _carry_on(config)
            numeric = run_numeric(self.vault, self.repository, state=state, support=support, candidates=by_id,
                                  now_iso=now_iso, seed=_hash({"numeric": key}),
                                  deadline=self.runtime.clock() + float(config.router.timeout_seconds),
                                  clock=self.runtime.clock, learned_tail=True,
                                  tail_snapshot=self._tail_snapshot(now_iso),
                                  # R3: the answer is served at once here; no second valuation on the serving path.
                                  carried_valuation=carry,
                                  defer_carried=no_model_deferred.append if carry else None)
            # (the answer carries its own carried valuation, ``numeric.carried``, when one is pending)
            entry = _NoModels(key, {"card": card, "evidence": list(rq.evidence_from_card(card.json)),
                                    "decided_at": now_iso, "numeric": numeric}, self.runtime.clock())
        self._freeze_objective(record, staged, feasible, support)
        return self._decide_objective(entry, state, staged, staged_ref, record, support, by_id, feasible, readiness,
                                      settings, now_iso)

    def _defer_carry(self, numeric: "NumericPolicy", entry: Any, decision_id: str) -> "NumericPolicy":
        """The follow-up batch's item 4 (RO6's open items 1 and 3): a decision served before its carried valuation
        existed hands it to the next boundary's prefetch (the no-model branch, which has none, to a thread of its own
        started after this decision), off the serving path; a later decision's trace records it. The decision's own
        record says where its value went.

        The valuation is the served answer's own (``numeric.carried``, frozen to that answer's inputs: Codex review
        F3), so an early publication served before the job completes hands over its own, and a final answer its."""

        from learnloop.router_objective import tail_serve

        residual = numeric.residual if isinstance(numeric.residual, Mapping) else None
        previous = (residual or {}).get("previous")
        if not isinstance(previous, Mapping) or previous.get("q_status") != tail_serve.NOT_BEFORE_THE_SERVE:
            return numeric
        if numeric.carried is None:
            return numeric
        _register_carry(self.repository.sqlite_path, decision_id, numeric.carried)
        no_models = entry.__class__.__name__ == "_NoModels"
        if no_models:
            deadline = self.runtime.clock() + float(self.vault.config.router.timeout_seconds)
            thread = threading.Thread(target=_drain_carry, args=(self.repository.sqlite_path,),
                                      kwargs={"deadline": deadline}, name="learnloop-objective-carried", daemon=True)
            thread.start()
        return replace(numeric, residual={**dict(residual or {}), "previous": {
            **dict(previous), "deferred_to": "own_thread_after_the_serve" if no_models else "next_prefetch"}})

    def _tail_snapshot(self, now_iso: str) -> Mapping[str, Any] | None:
        """RO6: the residual's mutable inputs read now, in the decision's own thread at its moment (F4); None below
        the tag or with the switch off (nothing read, the predecessor's path), or when it cannot be read (the
        residual is then left out and the trace says so)."""

        from learnloop.router_objective_switches import learned_tail_on

        if not learned_tail_on(self.vault.config):
            return None
        from learnloop.router_objective import tail_serve

        try:
            return tail_serve.snapshot(self.repository, now_iso=now_iso)
        except Exception:  # noqa: BLE001 - the residual never blocks the numeric policy
            LOG.warning("router objective: the learned tail's snapshot was not read", exc_info=True)
            return None

    def _start_objective(self, key: str, state: PlanState, feasible: Sequence[BlockCandidate], support: Sequence[str],
                         by_id: Mapping[str, BlockCandidate], ready: tuple[str, ...], now_iso: str) -> Prefetch:
        from functools import partial

        config = self.vault.config
        card = _build_card(self.card_builder, state, feasible)
        titles = {lo_id: lo.title for lo_id, lo in self.vault.learning_objects.items()}
        options = [_offer_option(by_id[ref], titles) if ref in by_id and by_id[ref].subtype == LESSON_OFFER_SUBTYPE
                   else _option(by_id[ref], titles) if ref in by_id
                   else rq.BlockOption(ref=ref, description=rq.STOP_OFFER_DESCRIPTION)
                   for ref in support]
        material = {
            "card": card, "card_hash": card.card_hash, "card_text": card.text, "card_json": card.json,
            "options": options, "evidence": list(rq.evidence_from_card(card.json)), "decided_at": now_iso,
            "state": state, "support": list(support), "by_id": dict(by_id), "numeric_seed": _hash({"numeric": key}),
        }
        frozen = self._tail_snapshot(now_iso)
        if frozen is not None:
            material["tail_snapshot"] = frozen
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
            lock = getattr(entry, "lock", None)
            if lock is not None:
                with lock:
                    published = material.get(PUBLISHED)
            else:
                published = material.get(PUBLISHED)
            if isinstance(numeric_result.parsed, NumericPolicy):
                numeric = numeric_result.parsed
            elif numeric_result.status == TIMEOUT and isinstance(published, NumericPolicy):
                # F1: the job answered and is still waiting on the LLM policy's forecasts for its optional
                # correction; its uncorrected answer serves, labelled.
                numeric = replace(published, stage="published_uncorrected")
                results[NUMERIC] = ComponentResult(name=NUMERIC, status=ANSWERED, parsed=numeric,  # type: ignore[arg-type]
                                                   latency_ms=numeric.latency_ms)
            else:
                numeric = NumericPolicy(status=numeric_result.status, error=numeric_result.error)
        numeric = _with_carried(numeric, entry)
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
        carry = _carry_on(config)
        if carry and numeric is not None:
            numeric = self._defer_carry(numeric, entry, decision_id)
        seed = self._seed(entry.key, decision_id)
        drawn = mix.draw(list(support), parts, effective, float(settings["epsilon_min"]), seed)
        # RO5 §9 item 1: the stop coin, on its own uniform, never the mix's; the availability it is frozen with is
        # read before that uniform. ``policy`` serves the mix's draw.
        coin = None
        rate = stop_coin_rate(config)
        # Landing ruling R4: the coin skips the session's opening boundary (no active minute yet: not a stop
        # decision); the minutes are the serving clock's at this decision, read before the coin's uniform.
        coin_minutes = self._session_minutes(now_iso) if rate > 0 and SC.STOP in support else None
        if rate > 0 and SC.eligible(support, session_minutes=coin_minutes):
            coin = SC.flip(seed, rate, support=list(support), mu=drawn.pi, drawn=drawn.chosen,
                           availability={**self._availability(state, numeric), "session_minutes": coin_minutes})
        served_ref = coin.served if coin is not None else drawn.chosen
        chosen = by_id.get(served_ref)
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
        if coin is not None and served_ref != drawn.chosen:
            # The coin, not the mix, chose what is served: no model's rationale is shown for it.
            shown = False
        why, why_kind = router_why.objective_why(drawn.component if served_ref == drawn.chosen else mix.STAGED, rule,
                                                 option_count=len(support), rationale=rationale, rationale_shown=shown)
        session_minutes = numeric.inputs.session_minutes if numeric is not None and numeric.inputs is not None else None
        mbar = numeric.inputs.price.remembered if numeric is not None and numeric.inputs is not None else None
        guard_at = P.guard_minutes(config, float(mbar)) if mbar else None
        guard_state = {"guard_minutes": guard_at, "guard_crossed": bool(guard_at and session_minutes is not None
                                                                         and session_minutes >= guard_at)}
        trace = _trace(support=support, by_id=by_id, feasible=feasible, titles=titles, numeric=numeric, llm=llm,
                       decider=results.get(DECIDER), staged_ref=staged_ref, weight=(w, weight_record),
                       effective=effective, pi=drawn.pi, drawn=drawn, seed=seed, config=config, now_iso=now_iso,
                       guard=guard_state, stop_in_support=STOP_FOR_TODAY in support, card_version=card.version)
        from learnloop.router_objective_switches import calibration_tag

        if calibration_tag(config):
            # RO5 §9 item 3 (Codex review F7): every active dated goal's frozen forecast, for the goal-date read,
            # whatever its distance; the policy comparison's uses keep only the window's.
            trace["goal_dates"] = _goal_dates(numeric)
        if carry:
            # The follow-up batch's item 4: earlier decisions' carried valuations a later prefetch ran, recorded
            # here (read as of this trace's own time; the transition into each is then no longer censored).
            carried_for = _carried_for(self.repository, decision_id)
            if carried_for:
                trace["carried_for"] = carried_for
        pending_assignments: list[dict[str, Any]] = []
        if coin is not None:
            # RO5: what was served and its exact probability under the coin and the mix together; the mix's own
            # draw and μ stay beside it (a ``policy`` decision's score reads μ, exact given the independent coin).
            trace["mixing"].update(drawn_chosen=drawn.chosen, chosen=served_ref, propensity=coin.served_propensity)
            trace["stop_coin"] = coin.as_dict()
            if coin.arm != SC.POLICY:
                trace["evaluation"]["score"] = f"none: {SC.FORCED} (the coin chose what was served)"
            pending_assignments.append(SC.pending_assignment(coin, seed=seed, support=support))
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
        if coin is not None:
            # The router's ledger logs each candidate's probability of being served: under the coin, the served
            # distribution (exact); the mix's own μ stays beside it.
            record["mixture"]["stop_coin"] = coin.as_dict()
            record["mixture"]["served"] = served_ref
            record["mixture"]["mix_pi"] = dict(drawn.pi)
            record["mixture"]["pi"] = SC.served_distribution(drawn.pi, coin.rate, list(support))
            record["ro5_assignments"] = pending_assignments
            return BlockChoice(candidate_id=served_ref, chosen_by="mixture", propensity=coin.served_propensity,
                               why=why or staged.why, why_kind=why_kind,  # type: ignore[arg-type]
                               router_record=record)
        return BlockChoice(
            candidate_id=drawn.chosen, chosen_by="mixture",
            propensity=1.0 if drawn.deterministic else drawn.propensity,
            why=why or staged.why, why_kind=why_kind,  # type: ignore[arg-type]
            router_record=record,
        )

    def _session_minutes(self, now_iso: str) -> float | None:
        """The objective session's active minutes at ``now_iso`` on the serving clock (``price.session_active_minutes``,
        the price's own construction), or None where they cannot be read (the coin is then not drawn)."""

        try:
            with self.repository.connection() as connection:
                minutes, _start, _basis = P.session_active_minutes(
                    connection, now=now_iso, gap_minutes=float(self.vault.config.router_objective.session_gap_minutes),
                    lessons=OI._lessons_on(self.vault.config))
            return float(minutes)
        except Exception:  # noqa: BLE001 - unknown minutes are not above zero: no coin, never a blocked plan
            LOG.warning("router objective RO5: the session's minutes were not read for the stop coin", exc_info=True)
            return None

    def _availability(self, state: PlanState, numeric: "NumericPolicy | None") -> dict[str, Any]:
        """RO5 §9 item 1: what the learner had when the coin was drawn, read before its uniform: the session's active
        minutes, the plan's remembered, budgeted and remaining minutes, and the session's availability receipt (RO0
        row 8: the minutes offered and their source)."""

        inputs = numeric.inputs if numeric is not None else None
        out: dict[str, Any] = {
            "session_minutes": inputs.session_minutes if inputs is not None else None,
            "remembered_minutes": inputs.price.remembered if inputs is not None else None,
            "minutes_budget": round(float(state.minutes_budget), 4), "minutes_left": round(float(state.minutes_left), 4),
            "session_id": self.session_id, "receipt": None,
        }
        if self.session_id:
            try:
                from learnloop.db.stores import router_objective as store

                with self.repository.connection() as connection:
                    if store.table_present(connection, store.SESSION_RECEIPTS):
                        found = store.session_receipt(connection, str(self.session_id), "availability")
                        if found is not None:
                            out["receipt"] = {key: found.get(key) for key in (
                                "id", "minutes_offered", "minutes_source", "local_time", "time_zone", "device")}
            except Exception:  # noqa: BLE001 - availability is recorded as missing, never blocks the coin
                out["receipt"] = "unreadable"
        return out


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
        config = self.vault.config
        settings = router_settings(config)
        state, candidates = self._state(record, current, item)
        if not wait_feasible:
            return self._no_room(state, candidates)
        readiness = self.runtime.readiness(self.vault)
        ready = tuple(name for name in (DECIDER, LLM) if readiness.get(name) is None)
        key = _hash({"v": KEY_VERSION, "kind": "objective_interrupt", "plan_id": record.id, "block": current.id,
                     "item": item.practice_item_id, "as_of": _latest_attempt(self.repository),
                     "version": config.algorithms.algorithm_version, "settings": settings,
                     "objective": objective_settings(config), "ready": ready})
        titles = {lo_id: lo.title for lo_id, lo in self.vault.learning_objects.items()}
        topic = titles.get(item.learning_object_id, item.learning_object_id)
        options = [rq.BlockOption(INSERT_NOW, f"Ask the follow-up on {topic} now, inside the current block."),
                   rq.BlockOption(CONTINUE_CURRENT, "Finish the current block first; the follow-up then opens the next block.")]
        extra = [f"A follow-up question on {topic} came out of the learner's last answer."]
        return self._mixed(state, candidates, key=key, readiness=readiness, ready=ready, topic=topic, options=options,
                           extra=extra)

    def _no_room(self, state: PlanState, candidates: list[BlockCandidate]) -> RestraintOutcome:
        """``wait_feasible = False``: waiting would drop the follow-up from today's plan, so it joins now,
        deterministically, and no model is asked (Codex review F8's rule, kept by §8.3)."""

        base: dict[str, Any] = {"mode": MODE, "why_version": WHY_VERSION}
        card = _build_card(self.card_builder, state, candidates)
        base.update(policy="staged_v1", decided_by="no_room_to_wait", **_card_fields(card))
        return RestraintOutcome(INSERT_NOW, 1.0, base, why="", wait_feasible=False)

    def _mixed(self, state: PlanState, candidates: list[BlockCandidate], *, key: str, readiness: Mapping[str, Any],
               ready: tuple[str, ...], topic: str, options: Sequence[Any], extra: Sequence[str],
               valued: Mapping[str, BlockCandidate] | None = None,
               support: Sequence[str] = (INSERT_NOW, CONTINUE_CURRENT),
               sequences: Mapping[str, Sequence[BlockCandidate]] | None = None, start: Any = None,
               llm_schema: str = rq.LLM_POLICY_RESTRAINT_SCHEMA) -> RestraintOutcome:
        """The two-policy mix over ``support`` (§8.3; by default ``{insert_now, continue_current}``), drawn and
        traced. ``candidates`` are what the cards show; ``valued`` (default: the same) what ``π_Q`` values, as
        ``sequences`` where given (default: the two orders). ``llm_schema``: the restraint's ``intervene_now``
        (two options) or ``router_llm_choice_v3`` (a probability per option, FG1's three at RO5's tag, ruling R8)."""

        base: dict[str, Any] = {"mode": MODE, "why_version": WHY_VERSION}
        config = self.vault.config
        settings = router_settings(config)
        support = list(support)
        by_id = {candidate.candidate_id: candidate for candidate in candidates}
        now_iso = __import__("learnloop.clock", fromlist=["utc_now_iso"]).utc_now_iso(self.clock)
        # π_Q: the follow-up now (a repair block before the rest) or after the rest (at the next boundary).
        values = dict(valued) if valued is not None else by_id
        if sequences is None:
            insert, cont = values[INSERT_NOW], values[CONTINUE_CURRENT]
            numeric = self._numeric_restraint(state, insert, cont, now_iso, key)
        else:
            numeric = run_numeric(self.vault, self.repository, state=state, support=support,
                                  candidates={ref: values[ref] for ref in support}, now_iso=now_iso,
                                  seed=_hash({"numeric": key}),
                                  deadline=self.runtime.clock() + float(config.router.timeout_seconds),
                                  clock=self.runtime.clock, sequences=sequences)
        if ready:
            entry = self.runtime.lookup(self.scope, key)
            if entry is None:
                entry = (start or self._start_policy)(key, state, candidates, topic, options, extra, ready)
            from learnloop.daily_plan.router_chooser import _await as await_entry

            await_entry(self.runtime, entry, may_defer=self.may_defer, timeout=float(config.router.timeout_seconds))
            results = entry.results()
        else:
            entry = _NoModels(key, {"card": _build_card(self.card_builder, state, candidates)}, self.runtime.clock())
            results = {}
        for name in (DECIDER, LLM):
            results.setdefault(name, ComponentResult(name=name, status=NOT_READY, error=str(readiness.get(name) or "not_ready")))
        llm = results[LLM]
        rationale = llm.rationale
        if llm_schema == rq.LLM_POLICY_SCHEMA:
            parsed = llm.parsed if llm.status == ANSWERED else None
            llm_dist = ({ref: float(parsed.distribution[ref]) for ref in support}
                        if isinstance(parsed, rq.ParsedPolicy) and set(parsed.distribution) == set(support)
                        and all(float(value) > 0.0 for value in parsed.distribution.values()) else None)
            rationale = parsed.rationale if isinstance(parsed, rq.ParsedPolicy) else None
        else:
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
        trace = _trace(support=support, by_id={**by_id, **(dict(valued) if valued is not None else {})},
                       feasible=candidates, titles=titles, numeric=numeric, llm=None,
                       decider=None, staged_ref=INSERT_NOW, weight=(w, weight_record), effective=effective,
                       pi=drawn.pi, drawn=drawn, seed=seed, config=config, now_iso=now_iso, guard={},
                       stop_in_support=False, card_version=card.version)
        trace["policies"]["llm"] = {"status": llm.status, "distribution": llm_dist, "rationale": rationale,
                                    "schema": llm_schema, "model": llm.model}
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
                     "rationale": {"text": rationale}},
            mixture_weights={"configured": {"w": w}, "effective": effective},
            model_distributions={"llm": llm_dist, "numeric": parts.get(mix.NUMERIC),
                                 "decider": ({INSERT_NOW: decider.p_yes, CONTINUE_CURRENT: 1 - decider.p_yes}
                                             if decider is not None and decider.status == ANSWERED and decider.p_yes is not None
                                             else None)},
            question_set_version=rq.RESTRAINT_QUESTION_SET,
            model_ids={"decider": results[DECIDER].model, "llm": llm.model, "llm_schema_version": llm_schema},
            latency_ms=max(latencies) if latencies else None, cost_usd=round(sum(costs), 8) if costs else 0.0,
            payloads=_payloads(results), objective_trace=trace, **_card_fields(card),
        )
        why = router_why.FOLLOWUP_WAITS if drawn.chosen == CONTINUE_CURRENT else ""
        return RestraintOutcome(drawn.chosen, 1.0 if drawn.deterministic else drawn.propensity, base, why=why)

    def _numeric_restraint(self, state: PlanState, insert: BlockCandidate, cont: BlockCandidate, now_iso: str,
                           key: str) -> NumericPolicy:
        """π_Q on the two orders, each an ordered sequence of the two blocks (the follow-up, then the remaining
        questions; or the reverse), every step valued with its own kind, duration, observation and effect on one
        clock; one cutoff, the same draws, each step its own noise in either order (F5)."""

        return run_numeric(self.vault, self.repository, state=state, support=[INSERT_NOW, CONTINUE_CURRENT],
                           candidates={INSERT_NOW: insert, CONTINUE_CURRENT: cont}, now_iso=now_iso,
                           seed=_hash({"numeric": key}),
                           deadline=self.runtime.clock() + float(self.vault.config.router.timeout_seconds),
                           clock=self.runtime.clock,
                           sequences={INSERT_NOW: (insert, cont), CONTINUE_CURRENT: (cont, insert)})

    def _start_policy(self, key: str, state: PlanState, candidates: list[BlockCandidate], topic: str,
                      options: Sequence[Any], extra: Sequence[str], ready: tuple[str, ...]) -> Prefetch:
        """The two models' prefetch: the Decider's R2c restraint request (advice) and the LLM policy's v3 one."""

        config = self.vault.config
        card = _build_card(self.card_builder, state, candidates)
        options = list(options)
        state_text = rq.state_text(card.text, options, evidence=rq.evidence_from_card(card.json), extra=list(extra))
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


# -- FG1's generated probe on the mix (RO4's open item 1, landing ruling R5 (1)) ------------------------------

#: The valued insert's stand-in item: the probe does not exist yet when the gate decides, so ``π_Q`` values one
#: question on the workflow's LO (no vault item has this id, so the rollouts read the candidate's LO).
FOLLOWUP_PLACEHOLDER_PREFIX = "followup:"


@dataclass
class ObjectiveFollowupGate(ObjectiveRestraintGate, FollowupGate):
    """§8.3 for FG1's generated probe at RO5's tag: the follow-up's ``plan_interrupt`` decision, made before its item
    exists, on the same two-policy mix as every mid-block follow-up, with its trace and ``μ`` recomputable
    (``mix.recompute``). Its support is ``{insert_now, continue_current, no_intervention}`` (landing ruling R8: the
    owner's FG1 decision of Nov 3, the router may choose no intervention for weak cases). ``π_L`` is the LLM policy's
    probability per option (``router_llm_choice_v3`` over the three, a reference row for the block's rest; R2b's
    ``RouterLLMAnswerV1`` request is not sent); ``π_Q`` values the three as one repair question on the workflow's LO
    before the current block's remaining questions, after them, or none at all (no probe served, the workflow's
    hypotheses left as they are). The Decider's ``P(yes)`` (the restraint request) is advice.
    ``wait_feasible = False`` asks now deterministically, no model asked; FG1's hard
    refusals come first (``followup_run.router.hard_refusal``), and its serve-at-once and single-use rules follow
    the chosen arm as before. Below the tag, or with ``[router_objective] enabled = false``, FG1's
    :class:`~learnloop.daily_plan.router_chooser.FollowupGate` serves exactly as before
    (``followup_run.router._plan_context``)."""

    def decide_followup(self, record: Any, current: Any, workflow: Mapping[str, Any], *, wait_feasible: bool,
                        facts: Sequence[str] = ()) -> RestraintOutcome:
        state, candidates = self._followup_state(record, current, workflow)
        support = [INSERT_NOW, CONTINUE_CURRENT, NO_INTERVENTION]
        offered = {"support": support if wait_feasible else [INSERT_NOW],
                   "workflow_id": workflow.get("id"), "version": "ro5_followup_objective_v2"}
        if not wait_feasible:
            outcome = self._no_room(state, candidates)
            outcome.record["objective_followup"] = offered
            return outcome
        config = self.vault.config
        settings = router_settings(config)
        readiness = self.runtime.readiness(self.vault)
        ready = tuple(name for name in (DECIDER, LLM) if readiness.get(name) is None)
        key = _hash({"v": KEY_VERSION, "kind": "objective_followup", "plan_id": record.id,
                     "workflow": workflow.get("id"), "block": current.id if current is not None else None,
                     "version": config.algorithms.algorithm_version, "settings": settings,
                     "objective": objective_settings(config), "ready": ready})
        titles = {lo_id: lo.title for lo_id, lo in self.vault.learning_objects.items()}
        lo = str(workflow["learning_object_id"])
        topic = titles.get(lo, lo)
        insert, cont = candidates
        options = [
            rq.BlockOption(INSERT_NOW, f"Ask a new follow-up question on {topic} now, written to tell the possible "
                                       "causes apart."),
            rq.BlockOption(CONTINUE_CURRENT, (
                f"Finish the current block first ({len(cont.item_ids)} questions left, about "
                f"{max(1, round(cont.est_minutes))} min); the new question then opens the next block, and the "
                "learner sees the answer now, so it can no longer settle the cause.")),
            rq.BlockOption(NO_INTERVENTION, rq.NO_INTERVENTION_DESCRIPTION),
        ]
        extra = [f"A question on {topic} was just missed.", *facts]
        probe = replace(insert, item_ids=(f"{FOLLOWUP_PLACEHOLDER_PREFIX}{workflow.get('id')}",),
                        est_minutes=self._followup_minutes(workflow, current))
        rest = replace(cont, candidate_id=NO_INTERVENTION, reason="the current block's remaining questions, no "
                                                                  "follow-up question")
        valued = {INSERT_NOW: probe, CONTINUE_CURRENT: cont, NO_INTERVENTION: rest}
        sequences = {INSERT_NOW: (probe, cont), CONTINUE_CURRENT: (cont, probe), NO_INTERVENTION: (rest,)}
        outcome = self._mixed(state, candidates, key=key, readiness=readiness, ready=ready, topic=topic,
                              options=options, extra=extra, valued=valued, support=support, sequences=sequences,
                              start=self._start_choice, llm_schema=rq.LLM_POLICY_SCHEMA)
        outcome.record["objective_followup"] = offered
        return replace(outcome, wait_feasible=True)

    def _start_choice(self, key: str, state: PlanState, candidates: list[BlockCandidate], topic: str,
                      options: Sequence[Any], extra: Sequence[str], ready: tuple[str, ...]) -> Prefetch:
        """The two models' prefetch for the three arms: the Decider's R2c restraint request (advice, ``P(yes)``) and
        the LLM policy's ``router_llm_choice_v3`` (a probability per option; the reference row is the current
        block's rest, the continuation ``π_Q``'s tail assumes)."""

        config = self.vault.config
        card = _build_card(self.card_builder, state, candidates)
        options = list(options)
        state_text = rq.state_text(card.text, options, evidence=rq.evidence_from_card(card.json), extra=list(extra))
        material = {"card": card, "card_hash": card.card_hash, "topic": topic, "state": state_text}
        reference = rq.BlockOption(V.REFERENCE_REF, "the current block's remaining questions, then the plan's usual "
                                                    "next step, with no follow-up question")

        def job(entry: Prefetch) -> None:
            from learnloop.daily_plan.router_chooser import _run_components
            from learnloop.db.repositories import Repository

            repository = Repository.attach(self.repository.sqlite_path)
            with self.runtime.spend.metered(repository, config, owner_kind=RECEIPT_OWNER, owner_id=entry.key):
                decider_request = rq.RestraintRequest(topic=topic, state=state_text)
                policy_request = rq.PolicyRequest(options=tuple(options), reference=reference, state=state_text,
                                                  evidence=tuple(rq.evidence_from_card(card.json)))
                entry.request = decider_request

                class _Both:
                    """The Decider reads the R2c restraint request; the LLM policy its v3 choice over three."""

                    question_set_version = decider_request.question_set_version
                    llm_schema_version = policy_request.llm_schema_version
                    decider_questions = decider_request.decider_questions
                    llm_prompt = policy_request.llm_prompt
                    state = state_text

                _run_components(self.runtime, entry, self.vault, repository, _Both(),
                                {DECIDER: lambda raw, _request: rq.parse_decider_restraint(raw),
                                 LLM: lambda raw, _request: rq.parse_llm_policy(raw, policy_request)},
                                card.card_hash)

        return self.runtime.start(self.scope, key, kind="plan_interrupt", budget=float(config.router.prefetch_timeout_seconds),
                                  material=material, components=ready, job=job)

    def _followup_minutes(self, workflow: Mapping[str, Any], current: Any) -> float:
        """The generated question's minutes for ``π_Q``: the missed question's own estimate (the probe is written on
        its LO, after it), else the mean of the LO's items', else the current block's mean question."""

        items = getattr(self.vault, "practice_items", {}) or {}
        source = None
        attempt_id = workflow.get("source_attempt_id")
        if attempt_id:
            try:
                with self.repository.connection() as connection:
                    found = connection.execute("SELECT practice_item_id FROM practice_attempts WHERE id = ?",
                                               (str(attempt_id),)).fetchone()
                source = items.get(str(found[0])) if found is not None else None
            except Exception:  # noqa: BLE001 - the next estimate stands in
                source = None
        if source is not None and float(getattr(source, "est_minutes", 0) or 0) > 0:
            return float(source.est_minutes)
        lo = str(workflow["learning_object_id"])
        same = [float(item.est_minutes) for item in items.values()
                if getattr(item, "learning_object_id", None) == lo and float(getattr(item, "est_minutes", 0) or 0) > 0]
        if same:
            return sum(same) / len(same)
        entries = [float(entry.est_minutes) for entry in (current.items if current is not None else ())
                   if float(getattr(entry, "est_minutes", 0) or 0) > 0]
        return sum(entries) / len(entries) if entries else 1.0


__all__ = ["FOLLOWUP_PLACEHOLDER_PREFIX", "NUMERIC", "NumericPolicy", "ObjectiveChooser", "ObjectiveFollowupGate",
           "ObjectiveRestraintGate", "current_weight", "day_price", "objective_settings", "run_numeric"]
