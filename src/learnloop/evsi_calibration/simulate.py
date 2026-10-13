"""Run simulated diagnostic episodes and record every forecast against what happened.

One simulated learner = one flagged diagnostic episode. The learner's true
hypothesis is drawn from the scenario's population prior; the learner answers
questions until one answer is wrong (the trigger, as a live episode opens after
an error); the system's belief starts at its own posterior after **every**
answer so far, the correct ones included (the live system knows the learner's
earlier attempts; conditioning on the error alone would bias the starting
belief against ``knows``). Then the policy chooses checks among the questions
not yet answered until it stops, and the system acts on
``loss_table.argmin_action(belief)``.

Common random numbers: learner ``i`` has the same truth, the same trigger, and
the same answer to any given question under every policy and every swept
setting, so differences between arms are paired, not noise.
"""

from __future__ import annotations

import hashlib
import math
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass, field, replace
from typing import Any, Mapping, Sequence

import numpy as np

from learnloop.diagnosis import robust_composition as rc
from learnloop.evsi_calibration import policies as P
from learnloop.evsi_calibration.eedi import OPTIONS
from learnloop.evsi_calibration.world import (
    HYP_KNOWS,
    Scenario,
    TrueLearner,
    entropy,
    route_for,
    system_rows,
)
from learnloop.scheduling import action_loss as AL
from learnloop.scheduling import evsi as EV

SIMULATION_VERSION = "evsi_calibration_sim_v1"
#: Quantiles of the per-member EVSI recorded for each administered check, so
#: the robust-quantile choice can be calibrated after the fact.
MEMBER_QUANTILES = (0.05, 0.10, 0.25, 0.50)


@dataclass(frozen=True)
class SimulationSettings:
    learners: int = 400
    seed: int = 20261012
    policies: tuple[str, ...] = P.ALL_POLICIES
    system_model: str = "hand_set"
    policy: P.PolicySettings = field(default_factory=P.PolicySettings)
    #: What leaving a misconception unresolved truly costs in this world
    #: (minutes). 0 = the minutes-only world today's loss assumes.
    truth_unresolved_minutes: float = 0.0
    #: What a repair and a check truly cost in this world, when they differ
    #: from what the system assumes (a sweep of the system's belief must hold
    #: the world fixed). None: the same as the system's PolicySettings.
    truth_repair_minutes: float | None = None
    truth_check_minutes: float | None = None
    max_trigger_tries: int = 20
    workers: int = 1

    def as_dict(self) -> dict[str, Any]:
        payload = dict(self.__dict__)
        payload["policy"] = self.policy.as_dict()
        payload["policies"] = list(self.policies)
        return payload


@dataclass(frozen=True)
class CheckRecord:
    policy: str
    learner: int
    step: int
    question_id: str
    predicted: Mapping[str, float]
    realized: str
    eig_nats: float
    entropy_drop: float
    truth_log_gain: float
    p_action_change: float
    action_changed: bool
    evsi_point: float
    evsi_member_quantiles: Mapping[str, float]
    realized_value: float


@dataclass(frozen=True)
class EpisodeRecord:
    policy: str
    learner: int
    subject_id: int
    truth: str
    checks: int
    check_minutes: float
    final_action: str
    correct_action: bool
    identified: bool
    regret_minutes: float
    total_minutes: float
    wasted_check_minutes: float
    stop_verdict: str
    stop_reason: str
    first_ranking: tuple[str, ...]
    steps_to_identify: int | None


@dataclass(frozen=True)
class LearnerSpec:
    index: int
    scenario_index: int
    truth: str
    trigger_question: str
    trigger_option: str
    #: Every (question, option) answered up to and including the trigger.
    history: tuple[tuple[str, str], ...] = ()


def _seed(*parts: Any) -> int:
    return int(hashlib.sha256("|".join(str(p) for p in parts).encode("utf-8")).hexdigest()[:12], 16)


def loss_table_for(scenario: Scenario, settings: P.PolicySettings, *, unresolved: float) -> AL.LossTable:
    """The minutes loss over the scenario's routes (real ``build_loss_table``)."""

    routes = [{"reason": h, "first_intervention": route_for(h)} for h in scenario.hypotheses]
    durations = {route_for(h): (0.0 if h == HYP_KNOWS else settings.repair_minutes) for h in scenario.hypotheses}
    extra = None
    if unresolved > 0:
        extra = {
            h: {"minutes": unresolved, "provenance": "simulation_setting"}
            for h in scenario.hypotheses
            if h != HYP_KNOWS
        }
    return AL.build_loss_table(
        routes=routes,
        hypotheses=scenario.hypotheses,
        duration_overrides=durations,
        calibration_label="simulation",
        scope=f"eedi_subject:{scenario.subject_id}",
        unresolved_minutes=extra,
    )


def draw_learners(scenarios: Sequence[Scenario], settings: SimulationSettings) -> list[LearnerSpec]:
    """Flagged learners (common across policies): truth, then a wrong trigger answer."""

    specs: list[LearnerSpec] = []
    attempts = 0
    index = 0
    while len(specs) < settings.learners and attempts < settings.learners * 10:
        attempts += 1
        rng = np.random.default_rng(_seed(settings.seed, "learner", index))
        scenario_index = int(rng.integers(len(scenarios)))
        scenario = scenarios[scenario_index]
        hypotheses = list(scenario.hypotheses)
        truth = str(rng.choice(hypotheses, p=[scenario.prior[h] for h in hypotheses]))
        learner = TrueLearner(scenario, truth, rng)
        order = [scenario.questions[int(k)] for k in rng.permutation(len(scenario.questions))]
        trigger = None
        history: list[tuple[str, str]] = []
        for question in order[: settings.max_trigger_tries]:
            option = learner.answer(question)
            history.append((question.question_id, option))
            if option != question.correct:
                trigger = (question.question_id, option)
                break
        if trigger is not None:
            specs.append(LearnerSpec(index, scenario_index, truth, trigger[0], trigger[1], tuple(history)))
        index += 1
    return specs


def _member_quantiles(values: Sequence[float]) -> dict[str, float]:
    return {f"q{int(q * 100):02d}": round(rc.robust_quantile(values, q), 6) for q in MEMBER_QUANTILES}


def run_learner(
    scenario: Scenario,
    spec: LearnerSpec,
    settings: SimulationSettings,
) -> tuple[list[CheckRecord], list[EpisodeRecord]]:
    ps = settings.policy
    system_loss = loss_table_for(scenario, ps, unresolved=ps.unresolved_minutes)
    truth_ps = replace(
        ps,
        repair_minutes=ps.repair_minutes if settings.truth_repair_minutes is None else settings.truth_repair_minutes,
    )
    truth_loss = loss_table_for(scenario, truth_ps, unresolved=settings.truth_unresolved_minutes)
    check_cost = ps.check_minutes if settings.truth_check_minutes is None else settings.truth_check_minutes
    history = spec.history or ((spec.trigger_question, spec.trigger_option),)
    answered = {question_id for question_id, _option in history}
    channel = P.identity_channel(OPTIONS)
    ensembles: dict[str, tuple[dict[str, dict[str, float]], tuple[dict[str, dict[str, float]], ...]]] = {}
    objects: dict[str, rc.Ensemble] = {}
    for question in scenario.questions:
        if question.question_id in answered:
            continue
        ensemble = rc.build_ensemble(
            joint_alpha=channel,
            instrument_rows=system_rows(settings.system_model, scenario, question),
            calibration_model_hash=f"sim:{settings.system_model}:{scenario.subject_id}",
            decision_context_hash=f"{settings.seed}:{spec.index}:{question.question_id}",
            draw_count=ps.draw_count,
            quantile=ps.robust_quantile,
            perturbation_concentration=ps.instrument_concentration,
        )
        objects[question.question_id] = ensemble
        ensembles[question.question_id] = (ensemble.mean_member, tuple(ensemble.members))
    start = dict(scenario.prior)
    for question_id, option in history:
        rows = system_rows(settings.system_model, scenario, scenario.question(question_id))
        start = rc.observed_update(rows, start, option)
    actions = {h: route_for(h) for h in scenario.hypotheses}
    checks: list[CheckRecord] = []
    episodes: list[EpisodeRecord] = []
    for policy in settings.policies:
        state = P.EpisodeState(
            hypotheses=scenario.hypotheses,
            belief=dict(start),
            remaining=sorted(ensembles),
            observations=0,
            loss_table=system_loss,
            ensembles=ensembles,
            ensemble_objects=objects,
            rng=np.random.default_rng(_seed(settings.seed, "policy", policy, spec.index)),
            actions_by_hypothesis=actions,
        )
        first_ranking: tuple[str, ...] = ()
        action_history = [system_loss.argmin_action(state.belief)]
        map_history = [max(state.belief, key=lambda h: (state.belief[h], h))]
        decision = None
        step = 0
        while True:
            decision = P.decide(policy, state, ps)
            if step == 0:
                first_ranking = decision.ranking
            if decision.action != "measure" or decision.question_id is None:
                break
            question_id = decision.question_id
            question = scenario.question(question_id)
            mean, members = ensembles[question_id]
            belief = state.belief
            predicted = P.mixture(mean, belief)
            # The same answer to the same question under every policy (CRN).
            answer_rng = np.random.default_rng(_seed(settings.seed, "answer", spec.index, question_id))
            learner = TrueLearner(scenario, spec.truth, answer_rng)
            realized = learner.answer(question)
            posterior = rc.observed_update(mean, belief, realized)
            action_before = system_loss.argmin_action(belief)
            action_after = system_loss.argmin_action(posterior)
            p_change = 0.0
            for emission, p in predicted.items():
                if p <= 0:
                    continue
                post_e = rc.observed_update(mean, belief, emission)
                if system_loss.argmin_action(post_e) != action_before:
                    p_change += p
            member_values = [EV.evsi_for_conditionals(m, belief, system_loss).evsi for m in members]
            truth_before = max(float(belief.get(spec.truth, 0.0)), 1e-12)
            truth_after = max(float(posterior.get(spec.truth, 0.0)), 1e-12)
            checks.append(
                CheckRecord(
                    policy=policy,
                    learner=spec.index,
                    step=step,
                    question_id=question_id,
                    predicted={k: round(v, 6) for k, v in predicted.items()},
                    realized=realized,
                    eig_nats=rc.expected_information_gain(mean, belief),
                    entropy_drop=entropy(belief) - entropy(posterior),
                    truth_log_gain=math.log(truth_after) - math.log(truth_before),
                    p_action_change=p_change,
                    action_changed=action_after != action_before,
                    evsi_point=member_values[0],
                    evsi_member_quantiles=_member_quantiles(member_values),
                    realized_value=truth_loss.loss(spec.truth, action_before)
                    - truth_loss.loss(spec.truth, action_after),
                )
            )
            state.belief = posterior
            state.remaining = [q for q in state.remaining if q != question_id]
            state.observations += 1
            action_history.append(action_after)
            map_history.append(max(posterior, key=lambda h: (posterior[h], h)))
            step += 1
        final_action = system_loss.argmin_action(state.belief)
        n = state.observations
        # Checks after the last change of the chosen action changed nothing.
        last_change = 0
        for k in range(1, len(action_history)):
            if action_history[k] != action_history[k - 1]:
                last_change = k
        wasted_checks = n - last_change
        steps_to_identify = None
        if map_history[-1] == spec.truth:
            steps_to_identify = 0
            for k in range(len(map_history) - 1, -1, -1):
                if map_history[k] != spec.truth:
                    steps_to_identify = k + 1
                    break
        regret = truth_loss.loss(spec.truth, final_action)
        episodes.append(
            EpisodeRecord(
                policy=policy,
                learner=spec.index,
                subject_id=scenario.subject_id,
                truth=spec.truth,
                checks=n,
                check_minutes=n * check_cost,
                final_action=final_action,
                correct_action=final_action == route_for(spec.truth),
                identified=map_history[-1] == spec.truth,
                regret_minutes=regret,
                total_minutes=n * check_cost + regret,
                wasted_check_minutes=wasted_checks * check_cost,
                stop_verdict=decision.verdict if decision is not None else "stop",
                stop_reason=decision.reason if decision is not None else "",
                first_ranking=first_ranking,
                steps_to_identify=steps_to_identify,
            )
        )
    return checks, episodes


def _run_chunk(payload: tuple[Sequence[Scenario], Sequence[LearnerSpec], SimulationSettings]) -> tuple[list[CheckRecord], list[EpisodeRecord]]:
    scenarios, specs, settings = payload
    checks: list[CheckRecord] = []
    episodes: list[EpisodeRecord] = []
    for spec in specs:
        c, e = run_learner(scenarios[spec.scenario_index], spec, settings)
        checks.extend(c)
        episodes.extend(e)
    return checks, episodes


@dataclass
class SimulationRun:
    settings: SimulationSettings
    learners: list[LearnerSpec]
    checks: list[CheckRecord]
    episodes: list[EpisodeRecord]


def run_simulation(
    scenarios: Sequence[Scenario],
    settings: SimulationSettings,
    *,
    learners: Sequence[LearnerSpec] | None = None,
) -> SimulationRun:
    specs = list(learners) if learners is not None else draw_learners(scenarios, settings)
    if settings.workers <= 1 or len(specs) < 8:
        checks, episodes = _run_chunk((scenarios, specs, settings))
    else:
        size = max(1, math.ceil(len(specs) / (settings.workers * 4)))
        chunks = [specs[i : i + size] for i in range(0, len(specs), size)]
        checks, episodes = [], []
        with ProcessPoolExecutor(max_workers=settings.workers) as pool:
            for c, e in pool.map(_run_chunk, [(scenarios, chunk, settings) for chunk in chunks]):
                checks.extend(c)
                episodes.extend(e)
    checks.sort(key=lambda r: (r.policy, r.learner, r.step))
    episodes.sort(key=lambda r: (r.policy, r.learner))
    return SimulationRun(settings=settings, learners=specs, checks=checks, episodes=episodes)


def with_policy(settings: SimulationSettings, **changes: Any) -> SimulationSettings:
    return replace(settings, policy=replace(settings.policy, **changes))
