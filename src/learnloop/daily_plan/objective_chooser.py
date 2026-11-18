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
* **π_Q**, the numeric policy: plain argmax of ``Q̄`` (:mod:`learnloop.router_objective.objective`), ties within the
  paired precision broken by support order, run as a third job in the prefetch with the prefetch's remaining budget
  as its deadline; a serving step that finds it unfinished treats it as a timeout. With no model set up there is no
  prefetch, so it runs on the calling thread with ``router.timeout_seconds`` as its deadline.
* **Staged and the Decider** are logged as advice; staged is the failure fallback (each failure moves only its
  policy's share to it). Irreversible picks and single-option supports stay deterministic, as before.
* **w_i** is ``ℓ_L + (1 − ℓ_L − ℓ_Q)·p_i`` from the weight's posterior (:mod:`learnloop.router_objective.weight`);
  with no randomized checks before RO5 no score forms and ``w`` stays at its prior, and the trace says so.
* **κ0** is the day's seed (:mod:`learnloop.router_objective.price`), carried from the day's first decision.
* **Preferences** (instruct hand-off IH4, :mod:`learnloop.router_objective.preferences`): frozen as a sensor in each trace,
  entering ``π_Q`` through ``w_pref`` only as far as randomized draws support (0 until then, nothing shifted), and on the
  LLM's card as the learner's own statements. Staged reads nothing.

The chooser writes nothing: its record and its trace ride on ``BlockChoice.router_record`` to the ``plan_block``
logger, which writes the trace (``router_objective_traces``) in the block's transaction.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, replace
from functools import partial
import json
import logging
import math
import threading
import time
from typing import Any

from learnloop.clock import parse_utc, utc_now_iso
from learnloop.daily_plan import objective_inputs as OI
from learnloop.daily_plan import objective_job as J
from learnloop.daily_plan.objective_job import NUMERIC, NumericPolicy
from learnloop.daily_plan.objective_seeds import mix_seed, numeric_seed
from learnloop.daily_plan.router_chooser import (
    INSERT_NOW,
    NO_INTERVENTION,
    FollowupGate,
    RestraintGate,
    RestraintOutcome,
    RouterChooser,
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
    seen,
)
from learnloop.daily_plan.staged_frame import StagedChooser
from learnloop.daily_plan.types import (
    CONTINUE_CURRENT,
    FOLLOWUP_CONTEST_NOTE,
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
from learnloop.router_objective import choose as C
from learnloop.router_objective import mix
from learnloop.router_objective import price as P
from learnloop.router_objective import stop_coin as SC
from learnloop.router_objective import trace_assembly as T
from learnloop.router_objective import objective as OBJ
from learnloop.router_objective import rollouts as ROL
from learnloop.router_objective import types as OT
from learnloop.router_objective import weight as W
from learnloop.router_objective_switches import failure_share_to_other_policy_on, stop_coin_rate

LOG = logging.getLogger(__name__)

MODE = C.MODE
KEY_VERSION = 1
WHY_VERSION = C.WHY_VERSION
#: Per decision: the LLM policy's and the numeric policy's statuses a share can fall back from.
_FAILURES = frozenset({TIMEOUT, FAILED, INVALID, NOT_READY, "spend", "unreachable"})


def objective_settings(config: Any) -> dict[str, Any]:
    """The settings a prefetch boundary key names, the follow-up batch's switches as they serve among them
    (landing ruling R12, ``followup_switch_snapshot``), so a flip between a prefetch and its serve starts a new job."""

    from learnloop.router_objective_switches import (
        failure_share_to_other_policy_on,
        followup_switch_snapshot,
        lessons_compete_with_followups_on,
        miss_cause_in_value_on,
        miss_cause_sensor_on,
        preferences_inform_router_on,
    )

    section = config.router_objective
    out = {key: getattr(section, key) for key in (
        "enabled", "sensors_in_value", "rollout_theta_draws", "rollout_theta_draws_max", "horizon_days",
        "undated_use_density", "dated_use_weight", "session_gap_minutes", "session_guard_minutes",
        "evaluation_window_days", "llm_weight_prior", "llm_min_share", "numeric_min_share", "delta_prior_sd",
        "effect_slope_prior_mean", "effect_slope_prior_variance", "stop_accept_prior_a", "stop_accept_prior_b",
        "llm_card_token_budget", "receipts")}
    out["followup_switches"] = followup_switch_snapshot(config)
    # IH5: where a failed policy's share goes serves at the decision, but the key names it too, so a flip between a
    # prefetch and its serve starts a new job.
    out["failure_share_to_other_policy"] = failure_share_to_other_policy_on(config)
    # IH2: which decisions hold a lesson offer, likewise.
    out["lessons_compete_with_followups"] = lessons_compete_with_followups_on(config)
    # IH4: named only while it serves, so off the key keeps its bytes (a flip still starts a new job).
    if preferences_inform_router_on(config):
        out["preferences_inform_router"] = True
    # Slip or gap: both switches as they serve, so a flip starts a new job. Never in the numeric policy's seed
    # (``COMMON_DRAW_OBJECTIVE_KEYS``, :func:`numeric_seed`).
    out["miss_cause_sensor"] = miss_cause_sensor_on(config)
    out["miss_cause_in_value"] = miss_cause_in_value_on(config)
    return out


def _miss_cause_mark(repository: Any, config: Any, candidates: Sequence[Any], now_iso: str) -> dict[str, Any]:
    """Slip or gap: what a boundary's identity names so a change in a candidate topic's miss sensor (a diagnosis landing,
    a probe answered) starts a new job (``miss_cause.mark``). Nothing off, or below the tag."""

    from learnloop.router_objective_switches import miss_cause_in_value_on, miss_cause_sensor_on

    if not miss_cause_sensor_on(config):
        return {}
    from learnloop.router_objective import miss_cause as MC

    los = [lo for candidate in candidates for lo in (getattr(candidate, "learning_object_ids", ()) or ())]
    with repository.connection() as connection:
        marked: dict[str, Any] = {"topics": MC.mark(MC.sensor(connection, config, los, now_iso))}
        if miss_cause_in_value_on(config):
            # SG2's fits read every topic's misses, diagnoses and lessons (Codex F1): their ledgers' revision too.
            marked["ledgers"] = MC.ledger_mark(connection)
    return {"miss_cause": marked}


def _preference_mark(repository: Any, config: Any) -> dict[str, Any]:
    """IH4: what a boundary's identity names so a new preference starts a new job (``preferences.mark``), read on the
    caller's connection, which a read-only prefetch can do. Nothing with the switch off or none on record."""

    from learnloop.router_objective.preferences import mark

    with repository.connection() as connection:
        return mark(connection, config)


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


def _rollout_options(config: Any) -> dict[str, bool]:
    """The rollouts' serving options, for every rollout of one decision (its evaluation and refinement, the
    correction, the carried valuation, the baselines and the day's gain curve) or for none: one place."""

    return {"merged_sessions": _merged(config), "consistent_review_draw": _consistent_draw(config),
            "held_ad_link": _held_link(config)}


def _frontier(inputs: OT.Inputs, *, draws: int, seed: str, **rollout: bool
              ) -> tuple[dict[float, float], dict[str, Any]]:
    mbar = float(inputs.price.remembered)
    d = float(inputs.tail_block_minutes)
    points = sorted({0.0, mbar, mbar + d, 2 * mbar})
    curve = ROL.gain(inputs, points, draws=draws, seed=f"{seed}:frontier", **rollout)
    return curve, {"points": [{"minutes": m, "gain": curve[m]} for m in points],
                   "display": "; ".join(f"{m:.0f} minutes: predicted gain {curve[m]:+.3f}" for m in points if m > 0)
                   + " (predictions)"}


def _posterior_price(repository: Any, inputs: OT.Inputs, config: Any, *, local_date: str, draws: int,
                     seed: str) -> tuple[P.Seeded, dict[str, Any]] | None:
    """RO5 §9 item 1: once a randomized stop offer has a response, κ0 is the posterior the seed is folded into
    (:mod:`learnloop.router_objective.stop_coin`) and the daily re-centring ends; the frontier is still drawn once a
    day, for display. None in the seed regime (the coin off, or no randomized response yet)."""

    from learnloop.db.stores import router_objective as store
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


def day_price(repository: Any, inputs: OT.Inputs, *, local_date: str, draws: int, seed: str,
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
    curve = ROL.gain(inputs, points, draws=draws, seed=f"{seed}:frontier", **_rollout_options(config))
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


def generator_now(config: Any, objective: str | None = None) -> str:
    """RO6: the generator version a decision made now is logged under (``tail_data.generator`` over its trace).
    ``objective``: the hash of the objective the decision values (``tail_data.objective_hash`` over its goals and
    horizon; landing ruling R2). At the follow-up batch's tag its serving switches are part of it (its landing
    ruling R8), as the trace records them (``versions.serving_switches``)."""

    from learnloop.router_objective import tail_data as TD
    from learnloop.router_objective_switches import followup_generator_switches

    seeds = W.Seeds.from_config(config)
    return TD.generator_key(TD.generator_payload(
        algorithm_version=str(config.algorithms.algorithm_version), objective=OBJ.OBJECTIVE_VERSION,
        tail=ROL.TAIL_VERSION, terminal=OBJ.TERMINAL_VERSION, horizon_days=float(config.router_objective.horizon_days),
        llm_schema=rq.LLM_POLICY_SCHEMA, seeds=_seed_record(seeds), epsilon=float(config.router.epsilon_min),
        objective_definition=objective, switches=followup_generator_switches(config),
        # Teacher TE3b: the features version served (its ``lesson`` indicator: a change point once, at its tag).
        features=TD.features_version(config)))


def _preferences_move(record: Mapping[str, Any] | None) -> bool:
    from learnloop.router_objective.preferences import moves_the_value

    return moves_the_value(record)


def _preference_record(repository: Any, config: Any, *, state: PlanState, support: Sequence[str],
                       candidates: Mapping[str, BlockCandidate], now_iso: str) -> Mapping[str, Any] | None:
    """IH4: a ``plan_block`` decision's choice-model sensor and ``w_pref``, from each candidate's kind. With the switch
    off, or nothing on record, None: nothing is read past the switch and the trace gains no key. ``w_pref`` follows RO6's
    machinery, so it is fitted only with the learned tail on."""

    from learnloop.router_objective_switches import learned_tail_on, preferences_inform_router_on

    if not preferences_inform_router_on(config):
        return None
    from learnloop.router_objective import preferences as PF

    kinds: dict[str, str] = {}
    for ref in support:
        candidate = candidates.get(ref)
        kinds[ref] = PF.STOP if ref == STOP_FOR_TODAY else PF.kind_of(
            reading=getattr(candidate, "reading", None), subtype=getattr(candidate, "subtype", None),
            lane=getattr(candidate, "lane", None))
    return PF.record(repository, config, kinds=kinds, minutes_left=float(state.minutes_left), now_iso=now_iso,
                     fit=learned_tail_on(config))


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
        preference_record = _preference_record(repository, config, state=state, support=support, candidates=candidates,
                                               now_iso=now_iso) if learned_tail else None
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

        def answered(evaluation: OBJ.Evaluation, used: OT.Inputs, acts: Sequence[OT.Action], corrected: bool) -> NumericPolicy:
            if residual_record is not None and residual_record.get("status") == "applied":
                from learnloop.router_objective import tail_serve

                choice, tie = OBJ.numeric_choice(tail_serve.shifted(evaluation, residual_record), support)
                tie = {**tie, "on": "v_tilde = v_tail + w_hat * v_residual",
                       "tail_argmax": OBJ.numeric_choice(evaluation, support)[1]["argmax"]}
            else:
                choice, tie = OBJ.numeric_choice(evaluation, support)
            if _preferences_move(preference_record):
                # IH4: only once w_pref has moved; at 0 nothing above changes, bit for bit.
                from learnloop.router_objective import preferences as PF
                from learnloop.router_objective import tail_serve

                base = (tail_serve.shifted(evaluation, residual_record) if residual_record is not None
                        and residual_record.get("status") == "applied" else evaluation)
                before = tie["argmax"]
                choice, moved = OBJ.numeric_choice(PF.shifted(base, preference_record,
                                                              tail={row.ref: row.q for row in evaluation.valued}), support)
                tie = {**tie, **moved, "on": "v_tail + w_hat * v_residual + w_pref * v_pref",
                       "before_preferences_argmax": before}
            if "baselines" not in cached:
                # The pre-action belief under the tail: no action and no correction enters it.
                cached["baselines"] = ROL.baselines(used, int(section.evaluation_window_days),
                                                    draws=min(evaluation.draws, 8), seed=seed, **rollout)
            return NumericPolicy(status=ANSWERED, choice=choice, tie=tie, evaluation=evaluation, inputs=used,
                                 actions=tuple(acts), sources=sources, price=priced, frontier=frontier,
                                 baselines=cached["baselines"], corrected=corrected,
                                 latency_ms=int(round((clock() - started) * 1000)), residual=residual_record,
                                 switches=frozen_switches, preference=preference_record)

        def carried_compute(record: Mapping[str, Any], at_inputs: OT.Inputs, at_actions: Sequence[OT.Action],
                            at_cutoff: float) -> Callable[..., dict[str, Any]]:
            """The carried valuation of one answer, frozen to the inputs it used (R12; item 4)."""

            at_draws, at_deadline = draws, deadline

            def compute(record: Mapping[str, Any] = record, deadline: float | None = None,
                        stop: threading.Event | None = None) -> dict[str, Any]:
                from learnloop.router_objective import tail_serve as TS

                # ``deadline``: a later prefetch's own, when the valuation was deferred to it (the follow-up
                # batch's item 4); else this job's. ``stop`` (its session closed or its plan was replaced) ends it at
                # the rollouts' next deadline check, as the deadline would: once set, the clock reads just past it
                # (a finite reading, so the evaluation's elapsed time stays a number).
                until = at_deadline if deadline is None else deadline
                timed = clock if stop is None or until is None else (
                    lambda: max(clock(), math.nextafter(until, math.inf)) if stop.is_set() else clock())
                at_previous = ROL.evaluate(at_inputs, at_actions, draws=at_draws, seed=seed, deadline=until,
                                           clock=timed, cutoff=at_cutoff, **rollout)
                return TS.with_carried_values(record, at_previous)

            return compute

        # The follow-up batch's item 4 (Codex review F3): at its tag, an early publication is an answer that can
        # serve (``published_uncorrected``) before the job installs anything, so it carries its own pending carried
        # valuation, frozen to its own (uncorrected) inputs; off, or below the tag, RO6's publication exactly.
        early_carry: float | None = None
        if publish is not None and defer_carried is not None and residual_record is not None and J.carry_on(config):
            from learnloop.router_objective import tail_serve

            early_carry = tail_serve.carried_cutoff(residual_record)
        on_complete = None
        if publish is not None:
            def on_complete(evaluation: OBJ.Evaluation) -> None:
                policy = answered(evaluation, inputs, actions, False)
                if early_carry is not None and residual_record is not None:
                    pending_early = tail_serve.pending_after_the_answer(residual_record)
                    policy = replace(policy, residual=pending_early,
                                     carried=carried_compute(pending_early, inputs, tuple(actions), early_carry))
                publish(policy)
        # (``unmeasured`` only at RO6's tag with the learned tail on; None leaves the evaluation as mvp-0.48's)
        measured = {"unmeasured": unmeasured} if unmeasured is not None else {}
        evaluation = ROL.evaluate(inputs, actions, draws=draws, seed=seed, max_draws=ceiling, keep_going=keep_going,
                                  deadline=deadline, clock=clock, on_complete=on_complete, **rollout,
                                  **measured)
        corrected = False
        if evaluation.complete and forecasts is not None and bool(section.sensors_in_value):
            got = forecasts()
            if got is not None:
                by_ref, reference = got
                if reference is not None and all(action.kind == OT.STOP or by_ref.get(action.ref) is not None
                                                 for action in actions):
                    effect = OT.EffectSlope(alpha=(0.0, float(section.effect_slope_prior_variance)),
                                            beta=(float(section.effect_slope_prior_mean),
                                                  float(section.effect_slope_prior_variance)))
                    with_llm = replace(inputs, effect=effect, reference_forecast=float(reference))
                    acts = [replace(action, forecast=by_ref.get(action.ref)) for action in actions]
                    again = ROL.evaluate(with_llm, acts, draws=evaluation.draws, seed=seed, deadline=deadline, clock=clock,
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
                if J.carry_on(config):
                    # The follow-up batch's item 4: the answer carries its own (Codex review F3).
                    own_carry = compute
            elif carried is not None:
                # RO6 (Codex re-review F3): the candidates valued again with every rollout at the latest earlier
                # decision's cutoff, on the inputs the answer used, for that decision's backup only (a regression
                # target, so the first batch's draws: its noise averages out in the fit, and no refinement is paid).
                at_previous = ROL.evaluate(inputs, actions, draws=draws, seed=seed, deadline=deadline, clock=clock,
                                           cutoff=carried, **rollout)
                residual_record = tail_serve.with_carried_values(residual_record, at_previous)
        final = answered(evaluation, inputs, actions, corrected)
        return replace(final, carried=own_carry) if own_carry is not None else final
    except Exception as exc:  # noqa: BLE001 - a failed policy's share goes to the staged rule
        LOG.warning("router objective: the numeric policy failed", exc_info=True)
        return NumericPolicy(status=FAILED, error=f"{type(exc).__name__}: {str(exc)[:200]}",
                             latency_ms=int(round((clock() - started) * 1000)))


# -- the prefetch job --------------------------------------------------------------------------------------


def _reference_description(action: OT.Action, titles: Mapping[str, str]) -> str:
    topics = ", ".join(dict.fromkeys(titles.get(lo, lo) for lo in action.item_los)) or "the topics most at risk"
    return (f"The continuation the numeric model assumes next: about {max(1, round(action.minutes))} min of "
            f"practice on {topics}, then a session of the suggested minutes each day.")


def _policy_request(vault: Any, repository: Any, entry: Prefetch) -> rq.PolicyRequest:
    """The LLM policy's request for one boundary, built on its job's thread (:mod:`learnloop.daily_plan.objective_job`)
    inside the job's reads: the decision card over the support, the tail's next action as the reference row. The
    card's record and the request are left on the job's material, where the decision reads them."""

    from learnloop.daily_plan.objective_card import decision_card

    material = entry.material
    config = vault.config
    built, actions, _sources = OI.build(vault, repository, state=material["state"],
                                        support=material["support"], candidates=material["by_id"],
                                        now_iso=material["decided_at"])
    reference = ROL._Model(built, 1, "reference").tail_action()
    titles = {lo_id: lo.title for lo_id, lo in vault.learning_objects.items()}
    card = decision_card(vault, repository, [material["by_id"][ref] for ref in material["support"]
                                             if ref in material["by_id"]],
                         served_at=material["decided_at"], goals=_sources.get("goals") or {},
                         session=_sources.get("session") or {},
                         budget=int(config.router_objective.llm_card_token_budget))
    policy_request = rq.PolicyRequest(
        options=tuple(material["options"]),
        reference=rq.BlockOption(ROL.REFERENCE_REF, _reference_description(reference, titles)),
        state=json.dumps(card["state"], sort_keys=True, ensure_ascii=False, default=str),
        evidence=tuple(card["evidence_ids"]))
    entry.material["policy_card"] = {key: card[key] for key in ("evidence_ids", "left_out", "bytes", "items")}
    if card.get("statements"):
        entry.material["policy_card"]["statements"] = {
            "card": card["state"]["card"], "entries": card["statements"],
            "left_out": dict((card.get("left_out") or {}).get("learner_statements") or {})}
    entry.material["policy_request"] = policy_request
    return policy_request


# -- the decision -------------------------------------------------------------------------------------------


def _offer_option(candidate: BlockCandidate, titles: Mapping[str, str]) -> rq.BlockOption:
    """Teacher TE3b: the lesson offer as one more option of the LLM policy's existing request (and the Decider's
    advice): its target, its reason, its minutes and ``P(accept)`` (spec §15.1a; no new request)."""

    record = dict((candidate.annotations or {}).get("lesson_offer") or {})
    topic = ", ".join(dict.fromkeys(titles.get(lo, lo) for lo in candidate.learning_object_ids))
    p_accept = (record.get("p_accept") or {}).get("mean")
    return rq.BlockOption(ref=candidate.candidate_id, description=rq.lesson_offer_description(
        topic=topic, why=candidate.reason, est_minutes=candidate.est_minutes,
        p_accept=float(p_accept) if p_accept is not None else None))


def _is_contest(candidate: BlockCandidate) -> bool:
    return bool((candidate.annotations or {}).get(FOLLOWUP_CONTEST_NOTE))


def _option_facts(candidate: BlockCandidate) -> C.OptionFacts:
    """What the choice's rule sentence reads of a candidate (``router_chooser._rule_sentence``'s annotations)."""

    notes = dict(candidate.annotations or {})
    return C.OptionFacts(reason_code=str(notes.get("reason_code") or ""), topic=notes.get("topic"),
                         section=notes.get("section"))


def _contest_option(candidate: BlockCandidate, titles: Mapping[str, str]) -> rq.BlockOption:
    """IH2 (spec_instruct_handoff_v1 §5 item 2): the boundary's follow-ups, as the LLM policy reads them beside the offer."""

    topic = ", ".join(dict.fromkeys(titles.get(lo, lo) for lo in candidate.learning_object_ids))
    return rq.BlockOption(ref=candidate.candidate_id, description=(
        f"Ask the follow-up question now, on {topic}, from the learner's last answer (about "
        f"{max(1, round(candidate.est_minutes))} min). If the lesson is chosen instead, this question stays for later."))


@dataclass
class ObjectiveChooser(RouterChooser):
    """``router_objective_v1``: the two policies' learned mix over the staged frame's support."""

    name: str = mix.POLICY

    def choose(self, state: PlanState, feasible: Sequence[BlockCandidate]) -> BlockChoice:
        # Teacher TE3b (spec_teacher_v1 rev 5 §15.1a): a lesson offer the boundary added is never the staged rule's
        # pick nor in staged's top-k order: it joins the support beside them (one offer a decision). With none, the
        # predecessor's decision exactly.
        offers = [candidate for candidate in feasible if OT.is_offer_subtype(candidate.subtype)]
        if offers:
            feasible = [candidate for candidate in feasible if not OT.is_offer_subtype(candidate.subtype)]
        # IH2 (spec_instruct_handoff_v1 §5 item 2): follow-ups against a lesson offer: these two are the decision.
        contest = next((candidate for candidate in feasible if _is_contest(candidate)), None)
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
        support = ([contest.candidate_id] if contest is not None else
                   support_order(state, feasible, staged.candidate_id, k=settings["k"], stop_offered=True,
                                 ties_only=settings["ties_only"]))
        if len(support) <= 1 and not (contest is not None and offers):
            return deterministic("single_option")
        if offers:
            # The offer joins the support after the blocks and before stop (ties go to staged's order first).
            offer = offers[0]
            by_id[offer.candidate_id] = offer
            at = support.index(STOP_FOR_TODAY) if STOP_FOR_TODAY in support else len(support)
            support = [*support[:at], offer.candidate_id, *support[at:]]
        # The staged rule's own pick: its lane-quota choice, or stop once the plan's minutes are used (§8.2: the
        # minutes are a suggestion the failure fallback keeps).
        staged_ref = (contest.candidate_id if contest is not None else
                      STOP_FOR_TODAY if state.minutes_left < STOP_OFFER_MINUTES else staged.candidate_id)
        readiness = self.runtime.readiness(self.vault)
        ready = tuple(name for name in (DECIDER, LLM) if readiness.get(name) is None)
        identity = {
            "v": KEY_VERSION, "kind": "objective_block", "plan_id": state.plan_id,
            "state": {"minutes_left": round(state.minutes_left, 3), "items_left": state.items_left,
                      "lanes": {lane: round(value, 3) for lane, value in sorted(state.lane_minutes_left.items())},
                      "kind": state.kind},
            "support": [by_id[ref].log_row() if ref in by_id else ref for ref in support],
            "staged": staged_ref, "as_of": _latest_attempt(self.repository),
            "version": config.algorithms.algorithm_version, "settings": settings,
            "objective": objective_settings(config), "ready": ready,
            # IH4: the card reads preferences, so a new one starts a new job; no value moves with it (numeric_seed).
            **_preference_mark(self.repository, config),
            # Slip or gap: the candidate topics' miss sensors, likewise (never in the seed).
            **_miss_cause_mark(self.repository, config, [by_id[ref] for ref in support if ref in by_id],
                               self._now_iso()),
        }
        key = _hash(identity)
        # Landing ruling R2: the numeric policy's seed from the identity less the seed-neutral speed switches.
        seed = numeric_seed(identity)
        now_iso = self._now_iso()
        if self.start_only:
            if ready and self.runtime.lookup(self.scope, key) is None:
                self._start_objective(key, state, feasible, support, by_id, ready, now_iso, numeric_seed=seed)
            raise DecisionPending(key)
        if ready:
            entry = self.runtime.lookup(self.scope, key)
            if entry is None:
                entry = self._start_objective(key, state, feasible, support, by_id, ready, now_iso,
                                              numeric_seed=seed)
            J.await_job(self.runtime, entry, may_defer=self.may_defer, config=config)
        else:
            card = _build_card(self.card_builder, state, feasible)
            entry = J.answer_without_models(
                self.runtime, key, config=config, card=card, now_iso=now_iso,
                numeric=partial(run_numeric, self.vault, self.repository, state=state, support=support,
                                candidates=by_id, now_iso=now_iso, seed=seed, learned_tail=True),
                tail_snapshot=partial(self._tail_snapshot, now_iso))

        def decided() -> BlockChoice:
            self._freeze_objective(record, staged, feasible, support)
            return self._decide_objective(entry, state, staged, staged_ref, record, support, by_id, feasible,
                                          readiness, settings, now_iso)

        computed = entry.material.get("numeric")
        return self._noting(entry, decided, extra={NUMERIC: {
            "status": computed.status, "latency_ms": computed.latency_ms}} if computed is not None else None,
            as_of=identity["as_of"])

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
                         by_id: Mapping[str, BlockCandidate], ready: tuple[str, ...], now_iso: str, *,
                         numeric_seed: str) -> Prefetch:
        card = _build_card(self.card_builder, state, feasible)
        titles = {lo_id: lo.title for lo_id, lo in self.vault.learning_objects.items()}
        options = [_offer_option(by_id[ref], titles) if ref in by_id and OT.is_offer_subtype(by_id[ref].subtype)
                   else _contest_option(by_id[ref], titles) if ref in by_id and _is_contest(by_id[ref])
                   else _option(by_id[ref], titles) if ref in by_id
                   else rq.BlockOption(ref=ref, description=rq.STOP_OFFER_DESCRIPTION)
                   for ref in support]
        material = {
            "card": card, "card_hash": card.card_hash, "card_text": card.text, "card_json": card.json,
            "options": options, "evidence": list(rq.evidence_from_card(card.json)), "decided_at": now_iso,
            "state": state, "support": list(support), "by_id": dict(by_id), "numeric_seed": numeric_seed,
        }
        frozen = self._tail_snapshot(now_iso)
        if frozen is not None:
            material["tail_snapshot"] = frozen
        return J.start_job(self.runtime, self.scope, key, vault=self.vault, sqlite_path=self.repository.sqlite_path,
                           session_id=self.session_id, plan_id=state.plan_id, material=material, ready=ready,
                           reads=OI.decision_reads, build_policy_request=_policy_request, numeric_policy=run_numeric)

    def _decide_objective(self, entry: Any, state: PlanState, staged: BlockChoice, staged_ref: str,
                          record: dict[str, Any], support: Sequence[str], by_id: Mapping[str, BlockCandidate],
                          feasible: Sequence[BlockCandidate], readiness: Mapping[str, str | None],
                          settings: Mapping[str, Any], now_iso: str) -> BlockChoice:
        """The boundary's decision in three parts: the reads gathered into ``ChoiceInputs``, the choice
        (:func:`learnloop.router_objective.choose.choose`, pure), then what the decision writes from it (its trace,
        the router's record and the served block). Nothing between the reads and the writes decides."""

        config = self.vault.config
        material = entry.material
        card = material["card"]
        # -- the reads --------------------------------------------------------------------------------------
        results, results_at, numeric = J.job_answers(entry, readiness)
        llm = results[LLM]
        parsed = llm.parsed if llm.status == ANSWERED and isinstance(llm.parsed, rq.ParsedPolicy) else None
        llm_dist = dict(parsed.distribution) if parsed is not None else None
        rationale = getattr(parsed, "rationale", None) if parsed is not None else None
        cited = tuple(getattr(parsed, "evidence_ids", ()) or ()) if parsed is not None else ()
        w, weight_record = current_weight(self.repository, config, at=now_iso)
        to_other = failure_share_to_other_policy_on(config)
        decision_id = new_ulid()
        carry = J.carry_on(config)
        # The served answer's carried valuation is registered here, before the choice, which never reads it: it
        # needs only the answer and the decision's id, and it leaves the answer's status and choice as they were.
        if carry and numeric is not None:
            numeric = J.defer_carry(numeric, entry, decision_id, runtime=self.runtime,
                                    sqlite_path=self.repository.sqlite_path, config=config,
                                    session_id=self.session_id, plan_id=state.plan_id)
        seed = mix_seed(self.runtime, entry.key, decision_id)
        # What the stop coin is frozen with is read before its uniform: the session's minutes on the serving clock
        # at this decision (the coin skips the session's opening boundary, where no stop is being decided), then
        # the availability, only where the coin applies.
        rate = stop_coin_rate(config)
        coin_minutes = self._session_minutes(now_iso) if C.coin_reads_minutes(rate, support) else None
        availability = ({**self._availability(state, numeric), "session_minutes": coin_minutes}
                        if C.coin_applies(rate, support, coin_minutes) else None)
        policy_card = material.get("policy_card") or {}
        policy_request = material.get("policy_request")
        # -- the choice -------------------------------------------------------------------------------------
        choice = C.choose(C.ChoiceInputs(
            support=tuple(support), staged_ref=staged_ref,
            options={ref: _option_facts(by_id[ref]) for ref in support if ref in by_id},
            llm_status=llm.status, llm_distribution=llm_dist, rationale=rationale, cited=cited,
            card_evidence_ids=frozenset(policy_card.get("evidence_ids") or ()),
            numeric_status=numeric.status if numeric is not None else None,
            numeric_choice=numeric.choice if numeric is not None else None,
            w=w, to_other_policy=to_other, epsilon=float(settings["epsilon_min"]), seed=seed,
            stop_rate=rate, session_minutes=coin_minutes, availability=availability, staged_why=staged.why,
            no_models=isinstance(entry, _NoModels), boundary_key=entry.key,
            algorithm_version=config.algorithms.algorithm_version,
            question_set_version=getattr(policy_request, "question_set_version", None),
            llm_schema_version=rq.LLM_POLICY_SCHEMA,
        ))
        # -- the writes -------------------------------------------------------------------------------------
        drawn, coin = choice.drawn, choice.coin
        titles = {lo_id: lo.title for lo_id, lo in self.vault.learning_objects.items()}
        contested = next((ref for ref in support if ref in by_id and _is_contest(by_id[ref])), None)
        # Earlier decisions' carried valuations a later prefetch ran, recorded in this trace (read as of the trace's
        # own time; the transition into each is then no longer censored).
        carried_for = (J.carried_for(self.repository, decision_id, session_id=self.session_id, plan_id=state.plan_id)
                       if carry else [])
        trace = T.objective_trace(choice, support=support, by_id=by_id, feasible=feasible, titles=titles,
                                  numeric=numeric, llm=llm, decider=results.get(DECIDER), staged_ref=staged_ref,
                                  weight=(w, weight_record), seed=seed, config=config, now_iso=now_iso,
                                  card_version=card.version, policy_card=policy_card, contested=contested,
                                  carried_for=carried_for)
        decider = results.get(DECIDER)
        decider_dist = (dict(decider.parsed.distribution) if decider is not None and decider.status == ANSWERED
                        and getattr(decider, "parsed", None) is not None else None)
        latencies = [r.latency_ms for r in results.values() if r.latency_ms is not None]
        costs = [r.cost_usd for r in results.values() if r.cost_usd is not None]
        payloads = _payloads({name: result for name, result in results.items() if name != NUMERIC})
        record.update(
            policy=mix.POLICY, decided_by=choice.decided_by,
            decision_id=decision_id, design=mix.DESIGN, seed=seed, why_code=choice.rule_code or None,
            drawn_component=drawn.component, option_count=len(support), fallback=choice.fallback,
            fallback_reasons=dict(choice.fallback_reasons),
            rationale_hidden=choice.rationale_hidden,
            evidence_labels=list(choice.evidence_labels),
            mixture={
                "boundary_key": entry.key, "support": list(support), "staged_ref": staged_ref, "k": settings["k"],
                "epsilon": settings["epsilon_min"], "ties_only": settings["ties_only"],
                "effective_weights": choice.effective, "w": w, "failed": list(choice.failed), "llm_distribution": llm_dist,
                **T.failure_rule_field(to_other),
                "numeric_choice": choice.numeric_choice,
                "drawn_component": drawn.component, "u1": drawn.u1, "u2": drawn.u2, "pi": dict(drawn.pi),
                "models": {name: result.summary() for name, result in sorted(results.items())},
                "rationale": {"text": rationale, "guard": choice.guard, "shown": choice.shown,
                              "evidence_ids": list(cited), "about": choice.favoured},
                "prefetched_at": material.get("decided_at"),
                "waited_ms": int(round(max(self.runtime.clock() - entry.started, 0.0) * 1000)),
            },
            mixture_weights={"configured": {"w": w, "ell_l": config.router_objective.llm_min_share,
                                            "ell_q": config.router_objective.numeric_min_share},
                             "effective": choice.effective},
            model_distributions={"llm": llm_dist, "numeric": choice.components.get(mix.NUMERIC), "decider": decider_dist},
            question_set_version=getattr(policy_request, "question_set_version", None),
            model_ids={"decider": results[DECIDER].model, "llm": llm.model, "llm_schema_version": rq.LLM_POLICY_SCHEMA},
            latency_ms=max(latencies) if latencies else None,
            cost_usd=round(sum(costs), 8) if costs else 0.0,
            payloads=payloads,
            objective_trace=trace,
            **_card_fields(card),
        )
        provenance = seen(entry, may_defer=self.may_defer, decided_wall=results_at)
        if coin is not None:
            # The router's ledger logs each candidate's probability of being served: under the coin, the served
            # distribution (exact); the mix's own μ stays beside it.
            record["mixture"]["stop_coin"] = coin.as_dict()
            record["mixture"]["served"] = choice.served
            record["mixture"]["mix_pi"] = dict(drawn.pi)
            record["mixture"]["pi"] = dict(choice.pi)
            record["ro5_assignments"] = list(choice.assignments)
        return BlockChoice(candidate_id=choice.served, chosen_by="mixture", propensity=choice.propensity,
                           why=choice.why, why_kind=choice.why_kind,  # type: ignore[arg-type]
                           router_record=record, provenance=provenance, decision_record=choice.record)

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

    def decide(self, record: Any, current: Any, item: Any, *, wait_feasible: bool = True,
               offer: Any = None) -> RestraintOutcome:
        """``offer`` (IH2, spec_instruct_handoff_v1 §5 item 3): the lesson offer this decision may hold (``offer.candidate``
        None: none available, and ``offer.record`` says why). None: the predecessor's decision exactly."""

        refusals = self._refusals(item)
        if refusals:
            return self.declined(refusals)
        config = self.vault.config
        settings = router_settings(config)
        state, candidates = self._state(record, current, item)
        lesson = getattr(offer, "candidate", None)
        if lesson is not None:
            return _with_offer_record(self._decide_with_lesson(record, current, item, state, candidates, lesson,
                                                               wait_feasible=wait_feasible), offer)
        if not wait_feasible:
            return _with_offer_record(self._no_room(state, candidates), offer)
        readiness = self.runtime.readiness(self.vault)
        ready = tuple(name for name in (DECIDER, LLM) if readiness.get(name) is None)
        identity = {"v": KEY_VERSION, "kind": "objective_interrupt", "plan_id": record.id, "block": current.id,
                    "item": item.practice_item_id, "as_of": _latest_attempt(self.repository),
                    "version": config.algorithms.algorithm_version, "settings": settings,
                    "objective": objective_settings(config), "ready": ready,
                    **_preference_mark(self.repository, config),
                    **_miss_cause_mark(self.repository, config, candidates,
                                       utc_now_iso(self.clock))}
        key = _hash(identity)
        titles = {lo_id: lo.title for lo_id, lo in self.vault.learning_objects.items()}
        topic = titles.get(item.learning_object_id, item.learning_object_id)
        options = [rq.BlockOption(INSERT_NOW, f"Ask the follow-up on {topic} now, inside the current block."),
                   rq.BlockOption(CONTINUE_CURRENT, "Finish the current block first; the follow-up then opens the next block.")]
        extra = [f"A follow-up question on {topic} came out of the learner's last answer."]
        return _with_offer_record(self._mixed(state, candidates, key=key, seed=numeric_seed(identity), readiness=readiness,
                                              ready=ready, topic=topic, options=options, extra=extra), offer)

    def _decide_with_lesson(self, record: Any, current: Any, item: Any, state: PlanState,
                            candidates: list[BlockCandidate], lesson: BlockCandidate, *,
                            wait_feasible: bool) -> RestraintOutcome:
        """The need path's arms with the offer among them: a probability per option, the follow-up valued as its item
        says (a probe's bundle, or a repair), the offer's "Not now" leading to the follow-up, which stays available."""

        config = self.vault.config
        settings = router_settings(config)
        readiness = self.runtime.readiness(self.vault)
        ready = tuple(name for name in (DECIDER, LLM) if readiness.get(name) is None)
        insert, cont = candidates
        support = [INSERT_NOW, *([CONTINUE_CURRENT] if wait_feasible else []), lesson.candidate_id]
        identity = {"v": KEY_VERSION, "kind": "objective_interrupt_lesson", "plan_id": record.id, "block": current.id,
                    "item": item.practice_item_id, "as_of": _latest_attempt(self.repository),
                    "offer": lesson.log_row(), "support": support, "version": config.algorithms.algorithm_version,
                    "settings": settings, "objective": objective_settings(config), "ready": ready,
                    **_preference_mark(self.repository, config),
                    **_miss_cause_mark(self.repository, config, [insert, cont, lesson],
                                       utc_now_iso(self.clock))}
        key = _hash(identity)
        titles = {lo_id: lo.title for lo_id, lo in self.vault.learning_objects.items()}
        topic = titles.get(item.learning_object_id, item.learning_object_id)
        options = [rq.BlockOption(INSERT_NOW, f"Ask the follow-up on {topic} now, inside the current block."),
                   *([rq.BlockOption(CONTINUE_CURRENT, "Finish the current block first; the follow-up then opens the "
                                                       "next block.")] if wait_feasible else []),
                   _offer_option(lesson, titles)]
        rest = (cont,) if cont.item_ids else ()
        sequences = {INSERT_NOW: (insert, *rest), CONTINUE_CURRENT: (*rest, insert),
                     OI.OFFER_DECLINED_STEPS: (*rest, insert)}
        return self._mixed(state, candidates, key=key, seed=numeric_seed(identity), readiness=readiness, ready=ready,
                           topic=topic, options=options,
                           extra=[f"A follow-up question on {topic} came out of the learner's last answer."],
                           valued={INSERT_NOW: insert, CONTINUE_CURRENT: cont, lesson.candidate_id: lesson},
                           support=support, sequences=sequences, start=self._start_choice,
                           llm_schema=rq.LLM_POLICY_SCHEMA)

    def _no_room(self, state: PlanState, candidates: list[BlockCandidate]) -> RestraintOutcome:
        """``wait_feasible = False``: waiting would drop the follow-up from today's plan, so it joins now,
        deterministically, and no model is asked (Codex review F8's rule, kept by §8.3)."""

        base: dict[str, Any] = {"mode": MODE, "why_version": WHY_VERSION}
        card = _build_card(self.card_builder, state, candidates)
        base.update(policy="staged_v1", decided_by="no_room_to_wait", **_card_fields(card))
        return RestraintOutcome(INSERT_NOW, 1.0, base, why="", wait_feasible=False)

    def _mixed(self, state: PlanState, candidates: list[BlockCandidate], *, key: str, seed: str,
               readiness: Mapping[str, Any], ready: tuple[str, ...], topic: str, options: Sequence[Any],
               extra: Sequence[str],
               valued: Mapping[str, BlockCandidate] | None = None,
               support: Sequence[str] = (INSERT_NOW, CONTINUE_CURRENT),
               sequences: Mapping[str, Sequence[BlockCandidate]] | None = None, start: Any = None,
               llm_schema: str = rq.LLM_POLICY_RESTRAINT_SCHEMA) -> RestraintOutcome:
        """The two-policy mix over ``support`` (§8.3; by default ``{insert_now, continue_current}``), drawn and
        traced. ``candidates`` are what the cards show; ``valued`` (default: the same) what ``π_Q`` values, as
        ``sequences`` where given (default: the two orders). ``llm_schema``: the restraint's ``intervene_now``
        (two options) or ``router_llm_choice_v3`` (a probability per option, FG1's three at RO5's tag, ruling R8).
        ``seed``: the numeric policy's (:func:`numeric_seed` of the boundary's identity; router speed stage 2's R2)."""

        base: dict[str, Any] = {"mode": MODE, "why_version": WHY_VERSION}
        config = self.vault.config
        settings = router_settings(config)
        support = list(support)
        by_id = {candidate.candidate_id: candidate for candidate in candidates}
        now_iso = utc_now_iso(self.clock)
        # π_Q: the follow-up now (a repair block before the rest) or after the rest (at the next boundary).
        values = dict(valued) if valued is not None else by_id
        if sequences is None:
            insert, cont = values[INSERT_NOW], values[CONTINUE_CURRENT]
            numeric = self._numeric_restraint(state, insert, cont, now_iso, seed)
        else:
            numeric = run_numeric(self.vault, self.repository, state=state, support=support,
                                  candidates={ref: values[ref] for ref in support}, now_iso=now_iso,
                                  seed=seed,
                                  deadline=self.runtime.clock() + float(config.router.timeout_seconds),
                                  clock=self.runtime.clock, sequences=sequences)
        if ready:
            entry = self.runtime.lookup(self.scope, key)
            if entry is None:
                # SG1: an offer among the valued arms (never on the shared card) gets its miss's cause on the LLM's state.
                offers = [part for part in values.values() if OT.is_offer_subtype(getattr(part, "subtype", None))]
                entry = (start or self._start_policy)(key, state, candidates, topic, options, extra, ready,
                                                      **({"offers": offers} if offers else {}))
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
        to_other = failure_share_to_other_policy_on(config)
        effective = mix.effective_weights(w, failed, to_other_policy=to_other)
        parts = mix.components(support, INSERT_NOW, llm=llm_dist, numeric_ref=numeric.choice if numeric_ok else None)
        decision_id = new_ulid()
        seed = mix_seed(self.runtime, entry.key, decision_id)
        drawn = mix.draw(support, parts, effective, float(settings["epsilon_min"]), seed)
        card = entry.material["card"]
        decider = results.get(DECIDER)
        titles = {lo_id: lo.title for lo_id, lo in self.vault.learning_objects.items()}
        trace = T.decision_trace(support=support, by_id={**by_id, **(dict(valued) if valued is not None else {})},
                                 feasible=candidates, titles=titles, numeric=numeric, llm=None,
                                 decider=None, staged_ref=INSERT_NOW, weight=(w, weight_record),
                                 effective=effective, pi=drawn.pi, drawn=drawn, seed=seed, config=config,
                                 now_iso=now_iso, guard={}, stop_in_support=False, card_version=card.version)
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
                     **T.failure_rule_field(to_other), "llm_distribution": llm_dist, "numeric_choice": numeric.choice if numeric_ok else None,
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
        offer_drawn = values.get(drawn.chosen)
        if offer_drawn is not None and OT.is_offer_subtype(offer_drawn.subtype):
            # IH2 (spec_instruct_handoff_v1 §5 item 3): the offer page's words for this draw, under the block's guard.
            _code, rule = _rule_sentence(offer_drawn, state)
            cited = tuple(getattr(llm.parsed, "evidence_ids", ()) or ()) if llm_dist is not None else ()
            guard = (router_why.rationale_guard(rationale, cited, {ref.attempt_id for ref in rq.evidence_from_card(card.json)})
                     if rationale is not None else "absent")
            if guard is None and drawn.component == mix.LLM and max(llm_dist, key=lambda ref: llm_dist[ref]) != drawn.chosen:
                guard = "another_option"
            why, why_kind = router_why.objective_why(drawn.component, rule, option_count=len(support), rationale=rationale,
                                                     rationale_shown=drawn.component == mix.LLM and guard is None)
            base["offer_why_kind"] = why_kind
            base["lesson_offer_card"] = dict((offer_drawn.annotations or {}).get("lesson_offer") or {})
        return RestraintOutcome(drawn.chosen, 1.0 if drawn.deterministic else drawn.propensity, base, why=why)

    def _numeric_restraint(self, state: PlanState, insert: BlockCandidate, cont: BlockCandidate, now_iso: str,
                           seed: str) -> NumericPolicy:
        """π_Q on the two orders, each an ordered sequence of the two blocks (the follow-up, then the remaining
        questions; or the reverse), every step valued with its own kind, duration, observation and effect on one
        clock; one cutoff, the same draws, each step its own noise in either order (F5)."""

        return run_numeric(self.vault, self.repository, state=state, support=[INSERT_NOW, CONTINUE_CURRENT],
                           candidates={INSERT_NOW: insert, CONTINUE_CURRENT: cont}, now_iso=now_iso,
                           seed=seed,
                           deadline=self.runtime.clock() + float(self.vault.config.router.timeout_seconds),
                           clock=self.runtime.clock,
                           sequences={INSERT_NOW: (insert, cont), CONTINUE_CURRENT: (cont, insert)})

    def _policy_state(self, card: Any, options: Sequence[Any], extra: Sequence[str], state_text: str,
                      candidates: Sequence[Any] = ()) -> str:
        """The LLM policy's state on a mid-block decision: the shared state, plus (IH4, §7 item 6) the learner's own
        statements and (slip or gap SG1, §3 item 3) the last miss's cause on the follow-up's and any offer's topic
        (``candidates``), for the LLM alone: the Decider's request keeps ``state_text``. None of either: ``state_text``
        itself."""

        from learnloop.clock import utc_now_iso
        from learnloop.daily_plan.objective_card import miss_cause_lines, statement_lines

        config = self.vault.config
        budget = int(config.router_objective.llm_card_token_budget)
        try:
            lines = statement_lines(self.vault, self.repository, served_at=utc_now_iso(self.clock), budget=budget)
        except Exception:  # noqa: BLE001 - context never blocks the decision: the LLM reads what it read before
            LOG.warning("router objective: the learner's statements were not read", exc_info=True)
            lines = []
        try:
            # One budget for both additions (Codex F9): the causes get what the statements left.
            left = budget - len("\n".join(lines).encode("utf-8"))
            causes = miss_cause_lines(self.vault, self.repository, candidates, served_at=utc_now_iso(self.clock),
                                      budget=left) if candidates else []
        except Exception:  # noqa: BLE001 - likewise: the request is the predecessor's without them
            LOG.warning("router objective: the miss causes were not read", exc_info=True)
            causes = []
        if not lines and not causes:
            return state_text
        return rq.state_text(card.text, options, evidence=rq.evidence_from_card(card.json),
                             extra=[*extra, *lines, *causes])

    def _start_policy(self, key: str, state: PlanState, candidates: list[BlockCandidate], topic: str,
                      options: Sequence[Any], extra: Sequence[str], ready: tuple[str, ...],
                      offers: Sequence[BlockCandidate] = ()) -> Prefetch:
        """The two models' prefetch: the Decider's R2c restraint request (advice) and the LLM policy's v3 one."""

        config = self.vault.config
        card = _build_card(self.card_builder, state, candidates)
        options = list(options)
        state_text = rq.state_text(card.text, options, evidence=rq.evidence_from_card(card.json), extra=list(extra))
        material = {"card": card, "card_hash": card.card_hash, "topic": topic, "state": state_text}
        policy_state = self._policy_state(card, options, extra, state_text, [*candidates, *offers])

        def job(entry: Prefetch) -> None:
            from learnloop.daily_plan.router_chooser import _run_components
            from learnloop.db.repositories import Repository

            repository = Repository.attach(self.repository.sqlite_path)
            with self.runtime.spend.metered(repository, config, owner_kind=RECEIPT_OWNER, owner_id=entry.key):
                decider_request = rq.RestraintRequest(topic=topic, state=state_text)
                policy_request = rq.PolicyRequest(options=tuple(options), reference=options[1], state=policy_state,
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


    def _start_choice(self, key: str, state: PlanState, candidates: list[BlockCandidate], topic: str,
                      options: Sequence[Any], extra: Sequence[str], ready: tuple[str, ...],
                      offers: Sequence[BlockCandidate] = ()) -> Prefetch:
        """The two models' prefetch for the three arms: the Decider's R2c restraint request (advice, ``P(yes)``) and
        the LLM policy's ``router_llm_choice_v3`` (a probability per option; the reference row is the current
        block's rest, the continuation ``π_Q``'s tail assumes)."""

        config = self.vault.config
        card = _build_card(self.card_builder, state, candidates)
        options = list(options)
        state_text = rq.state_text(card.text, options, evidence=rq.evidence_from_card(card.json), extra=list(extra))
        material = {"card": card, "card_hash": card.card_hash, "topic": topic, "state": state_text}
        policy_state = self._policy_state(card, options, extra, state_text, [*candidates, *offers])
        reference = rq.BlockOption(ROL.REFERENCE_REF, "the current block's remaining questions, then the plan's usual "
                                                    "next step, with no follow-up question")

        def job(entry: Prefetch) -> None:
            from learnloop.daily_plan.router_chooser import _run_components
            from learnloop.db.repositories import Repository

            repository = Repository.attach(self.repository.sqlite_path)
            with self.runtime.spend.metered(repository, config, owner_kind=RECEIPT_OWNER, owner_id=entry.key):
                decider_request = rq.RestraintRequest(topic=topic, state=state_text)
                policy_request = rq.PolicyRequest(options=tuple(options), reference=reference, state=policy_state,
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


def _with_offer_record(outcome: RestraintOutcome, offer: Any) -> RestraintOutcome:
    """IH2: the boundary's offer on the decision's record: its sensors, or why there was none (a ceiling bind logged)."""

    if offer is not None and getattr(offer, "record", None):
        outcome.record["lesson_offers"] = dict(offer.record)
    return outcome


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
                        facts: Sequence[str] = (), offer: Any = None) -> RestraintOutcome:
        """``offer`` (IH2, spec_instruct_handoff_v1 §5 item 3): the lesson offer this decision may hold; with one, the
        support gains it, and no room to wait no longer makes the decision deterministic: ``{insert_now, lesson}``, a real
        draw, before anything is generated. None, or no candidate in it: the predecessor's decision exactly."""

        state, candidates = self._followup_state(record, current, workflow)
        support = [INSERT_NOW, CONTINUE_CURRENT, NO_INTERVENTION]
        lesson = getattr(offer, "candidate", None)
        offered = {"support": support if wait_feasible else [INSERT_NOW],
                   "workflow_id": workflow.get("id"), "version": "ro5_followup_objective_v2"}
        if lesson is not None:
            support = [*(support if wait_feasible else [INSERT_NOW]), lesson.candidate_id]
            offered["support"] = support
        if not wait_feasible and lesson is None:
            outcome = _with_offer_record(self._no_room(state, candidates), offer)
            outcome.record["objective_followup"] = offered
            return outcome
        config = self.vault.config
        settings = router_settings(config)
        readiness = self.runtime.readiness(self.vault)
        ready = tuple(name for name in (DECIDER, LLM) if readiness.get(name) is None)
        identity = {"v": KEY_VERSION, "kind": "objective_followup", "plan_id": record.id,
                    "workflow": workflow.get("id"), "block": current.id if current is not None else None,
                    "version": config.algorithms.algorithm_version, "settings": settings,
                    "objective": objective_settings(config), "ready": ready,
                    # IH2: only with an offer in the support, so every other key keeps its bytes.
                    **({"offer": lesson.log_row(), "as_of": _latest_attempt(self.repository)} if lesson is not None
                       else {}),
                    **_preference_mark(self.repository, config),
                    **_miss_cause_mark(self.repository, config, [*candidates, *([lesson] if lesson is not None else [])],
                                       utc_now_iso(self.clock))}
        key = _hash(identity)
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
        if lesson is not None:
            options = [option for option in options if option.ref in support] + [_offer_option(lesson, titles)]
            # IH2 §5 item 4: against a lesson the question that doesn't exist yet is valued by RO §8.1's probe bundle, on
            # its LO (the kind and its terms are in the trace; no new number). A "Not now" leads back to it.
            probe = replace(probe, annotations={**dict(probe.annotations or {}), OI.FOLLOWUP_PROBE_NOTE: True})
            left = (cont,) if cont.item_ids else ()
            valued = {INSERT_NOW: probe, lesson.candidate_id: lesson,
                      **({CONTINUE_CURRENT: cont, NO_INTERVENTION: rest} if wait_feasible else {})}
            sequences = {**({INSERT_NOW: (probe, *left)} if left else {}),
                         **({CONTINUE_CURRENT: (cont, probe), NO_INTERVENTION: (rest,)} if wait_feasible else {}),
                         OI.OFFER_DECLINED_STEPS: (*left, probe)}
        outcome = self._mixed(state, candidates, key=key, seed=numeric_seed(identity), readiness=readiness,
                              ready=ready, topic=topic, options=options, extra=extra, valued=valued, support=support,
                              sequences=sequences, start=self._start_choice, llm_schema=rq.LLM_POLICY_SCHEMA)
        outcome = _with_offer_record(outcome, offer)
        outcome.record["objective_followup"] = offered
        return replace(outcome, wait_feasible=wait_feasible)

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
