"""Selection-and-stop policies the simulation compares, all on the real modules.

* ``evsi``: :func:`learnloop.scheduling.evsi.rank_feasible` over every
  remaining question (robust EVSI per minute, the LCB stop rule, the ±delta
  stress abstention). No count cap.
* ``eig``: :func:`learnloop.diagnosis.robust_composition.evaluate_selection`
  (robust EIG per second, the ``VALUE_PER_NAT_MINUTES`` stop rule, the 90%
  agreement gate). No count cap.
* ``caps``: today's probe-episode rules: the highest hypothesis-EIG question,
  stopped by ``probe.episode`` defaults (maximum observations, the posterior
  stop and ambiguity thresholds after the minimum independent observations,
  and the action-equivalence stop). The thresholds are read from
  :class:`learnloop.config.schema.ProbeEpisodeConfig`, never copied.
* ``random`` and ``max_entropy``: a random question / the question whose
  predicted answer is most uncertain, under the same caps.

Every policy ends by taking ``loss_table.argmin_action(belief)``.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

import numpy as np

from learnloop.config.schema import ProbeEpisodeConfig
from learnloop.diagnosis import robust_composition as rc
from learnloop.scheduling import action_loss as AL
from learnloop.scheduling import evsi as EV

POLICIES = ("evsi", "eig", "caps", "random", "max_entropy")
#: What-if readings of the same real modules' outputs (no reimplementation):
#: ``evsi_lcb_only`` measures whenever the robust LCB clears the minutes cost,
#: ignoring the flip abstentions; ``eig_no_gate`` measures whenever the robust
#: EIG stop rule says continue, ignoring the 90% agreement gate.
#: ``evsi_lookahead`` (the knowledge-gradient* idea, Frazier et al.) values the
#: best *batch* of the top-k ranked checks (k <= 3) jointly — the real
#: ``evsi_for_conditionals`` over the product table — and measures when some
#: batch's robust value clears k checks' minutes: a single check that cannot
#: change the action alone no longer ends the episode by itself.
VARIANTS = ("evsi_lcb_only", "evsi_lookahead", "eig_no_gate")
ALL_POLICIES = POLICIES + VARIANTS
LOOKAHEAD_MAX = 3

#: The forced-choice grading channel: the recorded option IS the chosen
#: option. Expressed as Dirichlet alphas so the real ensemble builder composes
#: it; the off-diagonal alpha is negligible, never zero (gamma(0) is undefined).
_CHANNEL_HIGH = 1.0e4
_CHANNEL_LOW = 1.0e-3


def identity_channel(options: Sequence[str]) -> dict[str, dict[str, float]]:
    return {z: {e: (_CHANNEL_HIGH if e == z else _CHANNEL_LOW) for e in options} for z in options}


@dataclass(frozen=True)
class PolicySettings:
    """Every hand-set number the policies consume, so a sweep can move one."""

    perturbation_delta: float = EV.PERTURBATION_DELTA
    robust_quantile: float = rc.ROBUST_QUANTILE
    lambda_time: float = rc.LAMBDA_TIME
    burden_cost: float = rc.BURDEN_COST
    value_per_nat_minutes: float = rc.VALUE_PER_NAT_MINUTES
    agreement_threshold: float = rc.ENSEMBLE_ACTION_AGREEMENT_THRESHOLD
    instrument_concentration: float = rc.INSTRUMENT_PERTURBATION_CONCENTRATION
    #: Ensemble draws (live: ROBUST_DRAW_COUNT = 128). Fewer in simulation for
    #: speed; the sweep reports how much the verdicts move with it.
    draw_count: int = 32
    check_minutes: float = 1.0
    repair_minutes: float = AL.DEFAULT_INTERVENTION_MINUTES
    #: Minutes an unresolved misconception costs later (Part C). 0 is today's
    #: minutes-only loss.
    unresolved_minutes: float = 0.0
    max_candidates: int = 12
    safety_bound: int = 25

    def as_dict(self) -> dict[str, Any]:
        return dict(self.__dict__)


@dataclass(frozen=True)
class Decision:
    action: str  # 'measure' | 'stop'
    question_id: str | None
    verdict: str
    reason: str
    #: Forecast of the chosen check, when one was chosen.
    evsi_point: float | None = None
    evsi_lcb: float | None = None
    ranking: tuple[str, ...] = ()


@dataclass
class EpisodeState:
    hypotheses: tuple[str, ...]
    belief: dict[str, float]
    remaining: list[str]
    observations: int
    loss_table: AL.LossTable
    #: question id -> (mean member, all members) under the system model.
    ensembles: Mapping[str, tuple[dict[str, dict[str, float]], tuple[dict[str, dict[str, float]], ...]]]
    ensemble_objects: Mapping[str, rc.Ensemble]
    rng: np.random.Generator
    actions_by_hypothesis: Mapping[str, str] = field(default_factory=dict)


def mixture(member: Mapping[str, Mapping[str, float]], belief: Mapping[str, float]) -> dict[str, float]:
    out: dict[str, float] = {}
    for h, weight in belief.items():
        for e, p in member.get(h, {}).items():
            out[e] = out.get(e, 0.0) + weight * p
    return out


def _entropy(distribution: Mapping[str, float]) -> float:
    return -sum(p * math.log(p) for p in distribution.values() if p > 0)


def _prefilter(state: EpisodeState, settings: PolicySettings) -> list[str]:
    """Bound the candidate set by mean-member EIG (live slates are small)."""

    if len(state.remaining) <= settings.max_candidates:
        return list(state.remaining)
    scored = sorted(
        state.remaining,
        key=lambda q: (-rc.expected_information_gain(state.ensembles[q][0], state.belief), q),
    )
    return scored[: settings.max_candidates]


def decide_evsi(state: EpisodeState, settings: PolicySettings, *, obey_abstention: bool = True) -> Decision:
    candidates = [
        EV.DiagnosticCandidate(
            ref=q,
            members=state.ensembles[q][1],
            prior=dict(state.belief),
            expected_minutes=settings.check_minutes,
            burden_minutes=0.0,
            prior_basis="support_weighted",
        )
        for q in _prefilter(state, settings)
    ]
    result = EV.rank_feasible(
        candidates,
        state.loss_table,
        quantile=settings.robust_quantile,
        lambda_time=settings.lambda_time,
        burden_cost=settings.burden_cost,
        perturbation_delta=settings.perturbation_delta,
    )
    ranking = tuple(r.ref for r in result.ranked)
    measure = result.verdict == "measure" or (
        not obey_abstention and result.verdict == "abstain" and not result.should_stop and result.ranked
    )
    if measure and result.best_ref is not None:
        best = result.ranked[0]
        return Decision("measure", result.best_ref, result.verdict, result.reason,
                        best.evsi.point, best.evsi.lcb, ranking)
    return Decision("stop", None, result.verdict, result.reason, ranking=ranking)


def _joint_member(tables: Sequence[Mapping[str, Mapping[str, float]]], hypotheses: Sequence[str]) -> dict[str, dict[str, float]]:
    """``P(e1, ..., ek | h)`` for conditionally independent checks."""

    joint: dict[str, dict[str, float]] = {}
    for h in hypotheses:
        row: dict[str, float] = {"": 1.0}
        for table in tables:
            nxt: dict[str, float] = {}
            for prefix, p in row.items():
                for e, q in table.get(h, {}).items():
                    if q > 0:
                        nxt[f"{prefix}|{e}" if prefix else e] = p * q
            row = nxt
        joint[h] = row
    return joint


def decide_lookahead(state: EpisodeState, settings: PolicySettings) -> Decision:
    single = decide_evsi(state, settings, obey_abstention=False)
    if single.action == "measure":
        return single
    ranking = single.ranking
    if len(ranking) < 2:
        return single
    hypotheses = [h for h in state.hypotheses if h in state.belief]
    for k in range(2, min(LOOKAHEAD_MAX, len(ranking)) + 1):
        batch = ranking[:k]
        member_count = min(len(state.ensembles[q][1]) for q in batch)
        values = []
        for index in range(member_count):
            joint = _joint_member([state.ensembles[q][1][index] for q in batch], hypotheses)
            values.append(EV.evsi_for_conditionals(joint, state.belief, state.loss_table).evsi)
        robust = rc.robust_quantile(values, settings.robust_quantile)
        cost = k * settings.check_minutes * settings.lambda_time + settings.burden_cost
        if robust > cost:
            return Decision("measure", batch[0], "measure", f"lookahead_{k}", values[0], robust, ranking)
    return single


def decide_eig(state: EpisodeState, settings: PolicySettings, *, obey_gate: bool = True) -> Decision:
    candidates = [
        (q, state.ensemble_objects[q], settings.check_minutes * 60.0) for q in _prefilter(state, settings)
    ]
    decision = rc.evaluate_selection(
        candidates=candidates,
        posterior=dict(state.belief),
        lambda_time=settings.lambda_time,
        burden_cost=settings.burden_cost,
        value_per_nat_minutes=settings.value_per_nat_minutes,
        agreement_threshold=settings.agreement_threshold,
    )
    act = decision.verdict == "act" or (not obey_gate and not decision.should_stop)
    if act and decision.chosen_slot is not None:
        return Decision("measure", decision.chosen_slot, decision.verdict, "robust_eig_act")
    return Decision("stop", None, decision.verdict, "robust_eig_stop" if decision.should_stop else "abstain")


def _cap_stop(state: EpisodeState, config: ProbeEpisodeConfig) -> str | None:
    """Today's probe-episode stop rules (probe_episodes._evaluate_completion)."""

    n = state.observations
    if n >= config.maximum_observations:
        return "observation_budget_exhausted"
    ordered = sorted(state.belief.values(), reverse=True)
    top = ordered[0] if ordered else 0.0
    second = ordered[1] if len(ordered) > 1 else 0.0
    stable = top >= config.posterior_stop_threshold and (top <= 0 or second / top <= config.ambiguity_threshold)
    if stable and n >= config.minimum_independent_observations:
        return "decision_stable"
    if config.action_equivalence_enabled and n >= 1:
        plausible = [h for h, p in state.belief.items() if p >= config.action_equivalence_plausible_threshold]
        if len(plausible) >= 2 and len({state.actions_by_hypothesis[h] for h in plausible}) == 1:
            return "action_equivalent"
    return None


def decide_capped(state: EpisodeState, settings: PolicySettings, *, chooser: str) -> Decision:
    config = ProbeEpisodeConfig()
    reason = _cap_stop(state, config)
    if reason is not None:
        return Decision("stop", None, "stop", reason)
    pool = list(state.remaining)
    if not pool:
        return Decision("stop", None, "stop", "no_question_left")
    if chooser == "random":
        return Decision("measure", str(state.rng.choice(sorted(pool))), "measure", "random")
    if chooser == "max_entropy":
        best = max(sorted(pool), key=lambda q: _entropy(mixture(state.ensembles[q][0], state.belief)))
        return Decision("measure", best, "measure", "max_entropy")
    best = max(sorted(pool), key=lambda q: rc.expected_information_gain(state.ensembles[q][0], state.belief))
    return Decision("measure", best, "measure", "hypothesis_eig")


def decide(policy: str, state: EpisodeState, settings: PolicySettings) -> Decision:
    if not state.remaining:
        return Decision("stop", None, "stop", "no_question_left")
    if state.observations >= settings.safety_bound:
        return Decision("stop", None, "stop", "safety_bound")
    if policy == "evsi":
        return decide_evsi(state, settings)
    if policy == "evsi_lcb_only":
        return decide_evsi(state, settings, obey_abstention=False)
    if policy == "evsi_lookahead":
        return decide_lookahead(state, settings)
    if policy == "eig":
        return decide_eig(state, settings)
    if policy == "eig_no_gate":
        return decide_eig(state, settings, obey_gate=False)
    if policy == "caps":
        return decide_capped(state, settings, chooser="eig")
    if policy in ("random", "max_entropy"):
        return decide_capped(state, settings, chooser=policy)
    raise ValueError(f"unknown policy {policy!r}")
