"""Selection-and-stop policies the simulation compares, all on the real modules.

* ``evsi``: :func:`learnloop.scheduling.evsi.rank_feasible` over every
  remaining question (robust EVSI per minute, the LCB stop rule, the ±delta
  stress abstention). No count cap.
* ``eig``: :func:`learnloop.diagnosis.robust_composition.evaluate_selection`
  (robust EIG per second, the ``VALUE_PER_NAT_MINUTES`` stop rule, the 90%
  agreement gate). No count cap.
* ``incumbent``: today's serving probe episode: the highest hypothesis-EIG
  question, stopped as ``probe_episodes._evaluate_completion`` stops it, in its
  order: the observation budget; on an unstable posterior the action
  equivalence stop, then (from the minimum independent observations on) the
  mvp-0.8 robust completion gate, which ends the episode when
  ``robust_composition.evaluate_selection`` over the remaining instruments
  abstains (``couldnt_reliably_distinguish``); on a stable one the decision
  stable stop after the minimum, else action equivalence. The thresholds are
  read from :class:`learnloop.config.schema.ProbeEpisodeConfig`, never copied.
* ``caps_only``: a simplified cap-only comparator: the same chooser and caps
  WITHOUT the robust completion gate (what a legacy, unpinned episode does).
  It is not today's serving.
* ``random`` and ``max_entropy``: a random question / the question whose
  predicted answer is most uncertain, under the cap-only rules.

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

POLICIES = ("evsi", "eig", "incumbent", "caps_only", "random", "max_entropy")
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
#: Stage evsi-multisim: the value-of-information successor (branch
#: ``serving/voi-stopping``, mvp-0.17) as built, and the package of changes
#: the multi-family study proposes for it. Not in ``ALL_POLICIES``, so the
#: single-family study's arms are unchanged.
#:
#: ``voi_successor`` (the branch at ``086c24c0``, after its review fixes):
#: today's per-episode stops (``probe_episodes._evaluate_completion``: decision
#: stable, action equivalent, the robust completion gate) with the episode's
#: ``maximum_observations`` lifted onto value (``episode_maximum_binds`` is
#: false while the site is on), and, on every next observation, the
#: successor's value gate (``voi_stopping.value_candidates``): where the
#: hypotheses with posterior mass route to two or more repairs (review F6:
#: the whole support, not the plausible ones), ``rank_feasible``'s robust EVSI
#: stop; where it abstains on a flip, or no decision is at stake, the robust
#: EIG times ``VALUE_PER_NAT_MINUTES`` against the minutes. It serves the
#: incumbent's highest-EIG instrument when that one pays, else the best paying
#: one (:func:`_serve_paying`).
#: ``voi_proposed``: the successor's structure with exactly the three changes
#: this study proposes: the robust completion gate dropped, a flip abstention
#: never handed to the nat scale (the robust LCB decides), and the 2-3 check
#: lookahead when no single check pays. Everything else is the successor's:
#: the episode maximum lifted, the stability stops, and the serving rule
#: (review F1: the package serves the successor's choice among the paying
#: checks, so it is the successor plus three changes and nothing else).
#: Leave-one-out ablations of ``voi_proposed`` (:func:`decide_package`), each
#: putting back one piece of the successor as built: ``voi_p_with_gate`` (the
#: robust completion gate), ``voi_p_with_fallback`` (the successor's whole
#: value gate: a flip abstention, or nothing at stake, handed to the robust EIG
#: times ``VALUE_PER_NAT_MINUTES``) and ``voi_p_one_step`` (no lookahead). With
#: all three put back the package IS the successor (tested decision for
#: decision).
#: ``voi_p_top_value``: the package serving ``rank_feasible``'s top-ranked
#: paying check (or the paying batch's first) instead of the successor's
#: choice: the serving change the first multisim run measured unawares (review
#: F1), now its own arm so it is ablated on its own.
SUCCESSOR_ABLATIONS = ("voi_p_with_gate", "voi_p_with_fallback", "voi_p_one_step")
SUCCESSOR_VARIANTS = ("voi_p_top_value",)
SUCCESSOR_POLICIES = ("voi_successor", "voi_proposed") + SUCCESSOR_ABLATIONS + SUCCESSOR_VARIANTS
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
    #: A count bound on any policy's episode (``None``: none, the default of
    #: both studies). The bank is finite, so an episode always ends by its rule
    #: or when the subject's questions run out, and a bound censors exactly the
    #: episodes whose cost a value rule is judged on (multi-family review F4).
    #: The single-family study ran with 25 until stage
    #: ``evsi-single-family-unbounded`` (2026-10-13); a bound stays available as
    #: an explicit option (``learnloop evsi simulate --safety-bound N``).
    safety_bound: int | None = None

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


def _paying_batch(state: EpisodeState, settings: PolicySettings,
                  ranking: Sequence[str]) -> tuple[tuple[str, ...], float, list[float]] | None:
    """The knowledge-gradient* step: the smallest batch of the top-k ranked
    checks (2 <= k <= ``LOOKAHEAD_MAX``) whose joint robust value clears k
    checks' minutes, as ``(batch, robust value, member values)``; ``None`` when
    none does."""

    if len(ranking) < 2:
        return None
    hypotheses = [h for h in state.hypotheses if h in state.belief]
    for k in range(2, min(LOOKAHEAD_MAX, len(ranking)) + 1):
        batch = tuple(ranking[:k])
        member_count = min(len(state.ensembles[q][1]) for q in batch)
        values = []
        for index in range(member_count):
            joint = _joint_member([state.ensembles[q][1][index] for q in batch], hypotheses)
            values.append(EV.evsi_for_conditionals(joint, state.belief, state.loss_table).evsi)
        robust = rc.robust_quantile(values, settings.robust_quantile)
        cost = k * settings.check_minutes * settings.lambda_time + settings.burden_cost
        if robust > cost:
            return batch, robust, values
    return None


def decide_lookahead(state: EpisodeState, settings: PolicySettings) -> Decision:
    single = decide_evsi(state, settings, obey_abstention=False)
    if single.action == "measure":
        return single
    found = _paying_batch(state, settings, single.ranking)
    if found is None:
        return single
    batch, robust, values = found
    return Decision("measure", batch[0], "measure", f"lookahead_{len(batch)}", values[0], robust, single.ranking)


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


def _stable(state: EpisodeState, config: ProbeEpisodeConfig) -> bool:
    ordered = sorted(state.belief.values(), reverse=True)
    top = ordered[0] if ordered else 0.0
    second = ordered[1] if len(ordered) > 1 else 0.0
    return top >= config.posterior_stop_threshold and (top <= 0 or second / top <= config.ambiguity_threshold)


def _action_equivalent(state: EpisodeState, config: ProbeEpisodeConfig) -> bool:
    if not config.action_equivalence_enabled or state.observations < 1:
        return False
    plausible = [h for h, p in state.belief.items() if p >= config.action_equivalence_plausible_threshold]
    return len(plausible) >= 2 and len({state.actions_by_hypothesis[h] for h in plausible}) == 1


def _cap_stop(state: EpisodeState, config: ProbeEpisodeConfig, *, budget: bool = True) -> str | None:
    """The cap-only stop rules (``_evaluate_completion`` without the robust gate).
    ``budget=False``: the episode maximum lifted onto value (mvp-0.17)."""

    n = state.observations
    if budget and n >= config.maximum_observations:
        return "observation_budget_exhausted"
    if _stable(state, config) and n >= config.minimum_independent_observations:
        return "decision_stable"
    if _action_equivalent(state, config):
        return "action_equivalent"
    return None


def _robust_gate_abstains(state: EpisodeState, settings: PolicySettings) -> bool:
    """``probe_episodes._robust_completion_override``: the robust selector over
    the remaining instruments abstains (the episode-pinned channel here is the
    simulation's identity channel)."""

    candidates = [
        (q, state.ensemble_objects[q], settings.check_minutes * 60.0) for q in _prefilter(state, settings)
    ]
    if not candidates:
        return False
    decision = rc.evaluate_selection(
        candidates=candidates,
        posterior=dict(state.belief),
        lambda_time=settings.lambda_time,
        burden_cost=settings.burden_cost,
        value_per_nat_minutes=settings.value_per_nat_minutes,
        agreement_threshold=settings.agreement_threshold,
    )
    return bool(decision.abstained)


def _incumbent_stop(state: EpisodeState, settings: PolicySettings, config: ProbeEpisodeConfig, *,
                    budget: bool = True) -> str | None:
    """``probe_episodes._evaluate_completion`` in its own order (review F8).
    ``budget=False``: the episode maximum lifted onto value (mvp-0.17)."""

    n = state.observations
    if budget and n >= config.maximum_observations:
        return "observation_budget_exhausted"
    if not _stable(state, config):
        if _action_equivalent(state, config):
            return "action_equivalent"
        if n >= config.minimum_independent_observations and _robust_gate_abstains(state, settings):
            return "couldnt_reliably_distinguish"
        return None
    if n >= config.minimum_independent_observations:
        return "decision_stable"
    if _action_equivalent(state, config):
        return "action_equivalent"
    return None


def decide_capped(
    state: EpisodeState, settings: PolicySettings, *, chooser: str, robust_gate: bool = False
) -> Decision:
    config = ProbeEpisodeConfig()
    reason = _incumbent_stop(state, settings, config) if robust_gate else _cap_stop(state, config)
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


def _rank(state: EpisodeState, settings: PolicySettings, refs: Sequence[str]) -> EV.RankResult:
    candidates = [
        EV.DiagnosticCandidate(ref=q, members=state.ensembles[q][1], prior=dict(state.belief),
                               expected_minutes=settings.check_minutes, burden_minutes=0.0,
                               prior_basis="support_weighted")
        for q in refs
    ]
    return EV.rank_feasible(candidates, state.loss_table, quantile=settings.robust_quantile,
                            lambda_time=settings.lambda_time, burden_cost=settings.burden_cost,
                            perturbation_delta=settings.perturbation_delta)


def _lcb_paying(result: EV.RankResult) -> dict[str, float]:
    """The ranked checks whose robust LCB clears their minutes cost."""

    return {ranked.ref: ranked.evsi.lcb for ranked in result.ranked if ranked.evsi.lcb > ranked.stop_threshold}


@dataclass(frozen=True)
class ValueGate:
    """What a value rule says about the next observation: the paying checks
    (ref -> robust value in minutes), the method that valued them, and
    ``rank_feasible``'s ranking when it decided (the lookahead's batch order)."""

    paying: dict[str, float]
    method: str
    ranking: tuple[str, ...] = ()
    #: ``rank_feasible``'s top-ranked check (the ``voi_p_top_value`` variant's pick).
    top: str | None = None
    #: False when the robust LCB did not decide (a flip abstention or nothing at
    #: stake handed to the nat scale): the lookahead then does not run.
    lcb_decided: bool = True


def _successor_value_gate(state: EpisodeState, settings: PolicySettings) -> ValueGate:
    """``voi_stopping.value_candidates`` on this episode."""

    # Review F6 on the successor: a decision is at stake when the hypotheses
    # with posterior MASS (the support, not the plausible ones) route to two
    # or more repairs; EVSI then weighs the whole posterior.
    support = [h for h, p in state.belief.items() if p > 0]
    at_stake = len({state.actions_by_hypothesis[h] for h in support}) >= 2
    refs = _prefilter(state, settings)
    method = "eig_value"
    if at_stake and refs:
        result = _rank(state, settings, refs)
        ranking = tuple(r.ref for r in result.ranked)
        if result.verdict != "abstain":
            paying = _lcb_paying(result) if result.verdict == "measure" else {}
            return ValueGate(paying, "robust_evsi", ranking, result.best_ref)
        method = f"eig_value:evsi_{result.reason}"
    return ValueGate(_eig_value_paying(state, settings, refs), method, lcb_decided=False)


def _lcb_value_gate(state: EpisodeState, settings: PolicySettings) -> ValueGate:
    """The proposed rule: ``rank_feasible``'s robust LCB decides, a flip
    abstention included (it never reaches the nat scale)."""

    result = _rank(state, settings, _prefilter(state, settings))
    return ValueGate(_lcb_paying(result), "robust_lcb", tuple(r.ref for r in result.ranked), result.best_ref)


def _eig_value_paying(state: EpisodeState, settings: PolicySettings, refs: Sequence[str]) -> dict[str, float]:
    """``value_candidates``' EIG path: each candidate's robust EIG (the members'
    ``robust_quantile``) times ``VALUE_PER_NAT_MINUTES``, kept where it clears
    ``lambda_time * minutes + burden``."""

    cost = settings.lambda_time * settings.check_minutes + settings.burden_cost
    paying: dict[str, float] = {}
    for q in refs:
        eigs = [rc.expected_information_gain(member, state.belief) for member in state.ensembles[q][1]]
        robust = settings.value_per_nat_minutes * rc.robust_quantile(eigs, settings.robust_quantile)
        if robust > cost:
            paying[q] = robust
    return paying


def _highest_eig(state: EpisodeState) -> str:
    """The incumbent's instrument: the highest hypothesis-EIG remaining check."""

    return max(sorted(state.remaining), key=lambda q: rc.expected_information_gain(state.ensembles[q][0], state.belief))


def _serve_paying(state: EpisodeState, paying: Mapping[str, float], method: str) -> Decision:
    """The successor's serving choice: the incumbent's highest-EIG instrument
    when it pays, else the best paying one; stop when none pays."""

    if not paying:
        return Decision("stop", None, "stop", f"value_of_information_stop:{method}")
    chosen = _highest_eig(state)
    if chosen in paying:
        return Decision("measure", chosen, "measure", f"value_pays:{method}")
    best = max(sorted(paying), key=lambda q: paying[q])
    return Decision("measure", best, "measure", f"value_pays_other:{method}")


def decide_successor(state: EpisodeState, settings: PolicySettings) -> Decision:
    config = ProbeEpisodeConfig()
    reason = _incumbent_stop(state, settings, config, budget=False)
    if reason is not None:
        return Decision("stop", None, "stop", reason)
    if not state.remaining:
        return Decision("stop", None, "stop", "no_question_left")
    gate = _successor_value_gate(state, settings)
    return _serve_paying(state, gate.paying, gate.method)


def decide_package(state: EpisodeState, settings: PolicySettings, *, gate: bool = False, fallback: bool = False,
                   lookahead: bool = True, top_value: bool = False) -> Decision:
    """The proposed package (``voi_proposed``: every switch at its default), its
    leave-one-out ablations and its serving variant, each inside the
    successor's structure (the episode maximum lifted, the stability stops
    kept, the successor's serving rule):

    ``gate``: keep today's robust completion gate (``_incumbent_stop``).
    ``fallback``: keep the successor's whole value gate
    (``_successor_value_gate``: a flip abstention, or nothing at stake, is
    decided by the robust EIG times ``VALUE_PER_NAT_MINUTES``); else the robust
    LCB decides every time (``_lcb_value_gate``).
    ``lookahead``: when no single check pays and the robust LCB decided, value
    the best 2-3 ranked checks jointly; a paying batch's checks all pay.
    ``top_value``: serve ``rank_feasible``'s top-ranked paying check (a
    batch's first) instead of the successor's choice.

    With ``gate``, ``fallback`` and not ``lookahead`` (and not ``top_value``)
    this is :func:`decide_successor`, decision for decision.
    """

    config = ProbeEpisodeConfig()
    reason = (_incumbent_stop(state, settings, config, budget=False) if gate
              else _cap_stop(state, config, budget=False))
    if reason is not None:
        return Decision("stop", None, "stop", reason)
    if not state.remaining:
        return Decision("stop", None, "stop", "no_question_left")
    value = _successor_value_gate(state, settings) if fallback else _lcb_value_gate(state, settings)
    if not value.paying and lookahead and value.lcb_decided:
        found = _paying_batch(state, settings, value.ranking)
        if found is not None:
            # The batch pays jointly and its order does not change its value, so
            # every check in it pays: the successor's rule serves the highest-EIG
            # instrument when it is in the batch, else the batch's top-ranked one.
            batch, _robust, _values = found
            method = f"{value.method}:lookahead_{len(batch)}"
            chosen = _highest_eig(state)
            if top_value or chosen not in batch:
                kind = "value_pays_top" if top_value else "value_pays_other"
                return Decision("measure", batch[0], "measure", f"{kind}:{method}", ranking=value.ranking)
            return Decision("measure", chosen, "measure", f"value_pays:{method}", ranking=value.ranking)
    if top_value and value.paying:
        chosen = value.top if value.top in value.paying else max(sorted(value.paying), key=lambda q: value.paying[q])
        return Decision("measure", chosen, "measure", f"value_pays_top:{value.method}", ranking=value.ranking)
    return _serve_paying(state, value.paying, value.method)


def decide(policy: str, state: EpisodeState, settings: PolicySettings) -> Decision:
    if not state.remaining:
        return Decision("stop", None, "stop", "no_question_left")
    if settings.safety_bound is not None and state.observations >= settings.safety_bound:
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
    if policy == "incumbent":
        return decide_capped(state, settings, chooser="eig", robust_gate=True)
    if policy == "caps_only":
        return decide_capped(state, settings, chooser="eig")
    if policy in ("random", "max_entropy"):
        return decide_capped(state, settings, chooser=policy)
    if policy == "voi_successor":
        return decide_successor(state, settings)
    if policy == "voi_proposed":
        return decide_package(state, settings)
    if policy == "voi_p_with_gate":
        return decide_package(state, settings, gate=True)
    if policy == "voi_p_with_fallback":
        return decide_package(state, settings, fallback=True)
    if policy == "voi_p_one_step":
        return decide_package(state, settings, lookahead=False)
    if policy == "voi_p_top_value":
        return decide_package(state, settings, top_value=True)
    raise ValueError(f"unknown policy {policy!r}")
