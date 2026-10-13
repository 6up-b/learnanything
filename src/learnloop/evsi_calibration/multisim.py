"""Diagnostic episodes against any simulator family (stage ``evsi-multisim``).

The single-family loop (:mod:`.simulate`) generalized to a truth world from
:mod:`.families`: the learner is a family state, not a hypothesis string; the
right action is read from the state's **needs** (a cognitive diagnosis learner
may hold two misconceptions; repairing one leaves the other); and in the
learning family the state moves after every answer, so the truth the final
action is scored against is the state at the end of the episode.

Everything else is unchanged and shared: the same policies on the same real
selectors (:mod:`.policies`), the same ensembles, the same metrics
(:mod:`.metrics`, which read :class:`.simulate.CheckRecord` and
:class:`.simulate.EpisodeRecord`). For the latent class family the loop
reproduces :func:`.simulate.run_learner` exactly (tested).

The system's model is one of:

* ``family``: the truth family's own calibrated single-cause model;
* ``hand_set``: today's vocabulary rows (prior: the truth family's);
* another family's name: that family's calibrated model (RankCert rotation:
  the system calibrated to one structure, the world another).

Loss of an action ``a`` for needs ``N`` (minutes; for one need it is exactly
:func:`learnloop.scheduling.action_loss.build_loss_table`'s cell)::

    L(N, a) = [a addresses no need] * minutes(a)
              + sum over needs n not addressed by a, n != knows: minutes(route(n)) + U
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
from learnloop.evsi_calibration.families import FamilyModel, ScenarioModel
from learnloop.evsi_calibration.simulate import (
    CheckRecord,
    EpisodeRecord,
    _member_quantiles,
    loss_table_for,
)
from learnloop.evsi_calibration.world import (
    ACTION_CONTINUE,
    HYP_KNOWS,
    Scenario,
    entropy,
    hand_set_row,
    route_for,
)
from learnloop.scheduling import evsi as EV

MULTISIM_VERSION = "evsi_multisim_v1"
SYSTEM_FAMILY = "family"
SYSTEM_HAND_SET = "hand_set"


def _seed(*parts: Any) -> int:
    return int(hashlib.sha256("|".join(str(p) for p in parts).encode("utf-8")).hexdigest()[:12], 16)


@dataclass(frozen=True)
class MultiSimSettings:
    learners: int = 400
    seed: int = 20261012
    policies: tuple[str, ...] = P.ALL_POLICIES + P.SUCCESSOR_POLICIES
    #: ``family`` | ``hand_set`` | another family's name (a cross system).
    system: str = SYSTEM_FAMILY
    policy: P.PolicySettings = field(default_factory=P.PolicySettings)
    truth_unresolved_minutes: float = 0.0
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
class World:
    """A truth family over the bank's scenarios, and the families a system may be."""

    truth: FamilyModel
    scenarios: tuple[Scenario, ...]
    #: Calibrated families available as cross systems (same strength as the truth).
    systems: Mapping[str, FamilyModel] = field(default_factory=dict)


@dataclass(frozen=True)
class FamilyLearner:
    index: int
    scenario_index: int
    #: The family state when the episode opens (after the history's answers).
    state: Any
    needs: tuple[str, ...]
    history: tuple[tuple[str, str], ...]


class _Models:
    """Per-process cache of scenario models (truth and systems)."""

    def __init__(self, world: World) -> None:
        self.world = world
        self._cache: dict[tuple[str, int], ScenarioModel] = {}

    def get(self, family: FamilyModel, scenario_index: int) -> ScenarioModel:
        key = (family.key, scenario_index)
        model = self._cache.get(key)
        if model is None:
            model = family.scenario_model(self.world.scenarios[scenario_index])
            self._cache[key] = model
        return model


def draw_family_learners(world: World, settings: MultiSimSettings) -> list[FamilyLearner]:
    """Flagged learners: a family state, then answers until the first wrong one.

    Seeds are per learner, so the subject is common to every family and every
    strength; the state and answers follow the world. For the latent class
    family the sequence of draws is :func:`.simulate.draw_learners`'s."""

    models = _Models(world)
    specs: list[FamilyLearner] = []
    attempts = 0
    index = 0
    scenarios = world.scenarios
    while len(specs) < settings.learners and attempts < settings.learners * 10:
        attempts += 1
        rng = np.random.default_rng(_seed(settings.seed, "learner", index))
        scenario_index = int(rng.integers(len(scenarios)))
        scenario = scenarios[scenario_index]
        model = models.get(world.truth, scenario_index)
        state = model.draw_state(rng)
        order = [scenario.questions[int(k)] for k in rng.permutation(len(scenario.questions))]
        trigger = False
        history: list[tuple[str, str]] = []
        for position, question in enumerate(order[: settings.max_trigger_tries]):
            option = model.answer(state, question, rng)
            history.append((question.question_id, option))
            if model.learns:
                uniform = float(np.random.default_rng(_seed(settings.seed, "learn", index, "history", position)).random())
                state = model.transition(state, uniform)
            if option != question.correct:
                trigger = True
                break
        if trigger:
            specs.append(FamilyLearner(index, scenario_index, state, model.needs(state), tuple(history)))
        index += 1
    return specs


def true_loss(needs: Sequence[str], action: str, *, repair_minutes: float, unresolved: float) -> float:
    def minutes(route: str) -> float:
        return 0.0 if route == ACTION_CONTINUE else repair_minutes

    routes = [route_for(n) for n in needs]
    loss = 0.0 if action in routes else minutes(action)
    for need, route in zip(needs, routes):
        if route == action or need == HYP_KNOWS:
            continue
        loss += minutes(route) + unresolved
    return loss


def _mass(belief: Mapping[str, float], needs: Sequence[str]) -> float:
    return max(sum(float(belief.get(h, 0.0)) for h in needs), 1e-12)


def run_family_learner(
    world: World,
    spec: FamilyLearner,
    settings: MultiSimSettings,
    models: _Models,
) -> tuple[list[CheckRecord], list[EpisodeRecord]]:
    ps = settings.policy
    scenario = world.scenarios[spec.scenario_index]
    truth_model = models.get(world.truth, spec.scenario_index)
    if settings.system == SYSTEM_HAND_SET:
        prior = truth_model.system_prior()

        def rows_for(question: Any) -> dict[str, dict[str, float]]:
            return {h: hand_set_row(h, question) for h in scenario.hypotheses}
    else:
        system_family = world.truth if settings.system == SYSTEM_FAMILY else world.systems[settings.system]
        system_model = models.get(system_family, spec.scenario_index)
        prior = system_model.system_prior()
        rows_for = system_model.system_rows
    system_loss = loss_table_for(scenario, ps, unresolved=ps.unresolved_minutes)
    repair_truth = ps.repair_minutes if settings.truth_repair_minutes is None else settings.truth_repair_minutes
    check_cost = ps.check_minutes if settings.truth_check_minutes is None else settings.truth_check_minutes
    unresolved_truth = settings.truth_unresolved_minutes

    def loss(needs: Sequence[str], action: str) -> float:
        return true_loss(needs, action, repair_minutes=repair_truth, unresolved=unresolved_truth)

    answered = {question_id for question_id, _option in spec.history}
    channel = P.identity_channel(OPTIONS)
    ensembles: dict[str, tuple[dict[str, dict[str, float]], tuple[dict[str, dict[str, float]], ...]]] = {}
    objects: dict[str, rc.Ensemble] = {}
    for question in scenario.questions:
        if question.question_id in answered:
            continue
        ensemble = rc.build_ensemble(
            joint_alpha=channel,
            instrument_rows=rows_for(question),
            # The single-family study's label for a calibrated system, so the
            # latent class family reproduces its ensembles draw for draw.
            calibration_model_hash=f"sim:{'eedi_fitted' if settings.system == SYSTEM_FAMILY else settings.system}:"
                                   f"{scenario.subject_id}",
            decision_context_hash=f"{settings.seed}:{spec.index}:{question.question_id}",
            draw_count=ps.draw_count,
            quantile=ps.robust_quantile,
            perturbation_concentration=ps.instrument_concentration,
        )
        objects[question.question_id] = ensemble
        ensembles[question.question_id] = (ensemble.mean_member, tuple(ensemble.members))
    start = dict(prior)
    for question_id, option in spec.history:
        start = rc.observed_update(rows_for(scenario.question(question_id)), start, option)
    actions = {h: route_for(h) for h in scenario.hypotheses}
    checks: list[CheckRecord] = []
    episodes: list[EpisodeRecord] = []
    for policy in settings.policies:
        state_truth = spec.state
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
            needs_now = truth_model.needs(state_truth)
            answer_rng = np.random.default_rng(_seed(settings.seed, "answer", spec.index, question_id))
            realized = truth_model.answer(state_truth, question, answer_rng)
            if truth_model.learns:
                uniform = float(np.random.default_rng(_seed(settings.seed, "learn", spec.index, "episode", step)).random())
                state_truth = truth_model.transition(state_truth, uniform)
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
                    truth_log_gain=math.log(_mass(posterior, needs_now)) - math.log(_mass(belief, needs_now)),
                    p_action_change=p_change,
                    action_changed=action_after != action_before,
                    evsi_point=member_values[0],
                    evsi_member_quantiles=_member_quantiles(member_values),
                    realized_value=loss(needs_now, action_before) - loss(needs_now, action_after),
                )
            )
            state.belief = posterior
            state.remaining = [q for q in state.remaining if q != question_id]
            state.observations += 1
            action_history.append(action_after)
            map_history.append(max(posterior, key=lambda h: (posterior[h], h)))
            step += 1
        final_action = system_loss.argmin_action(state.belief)
        needs_final = truth_model.needs(state_truth)
        n = state.observations
        last_change = 0
        for k in range(1, len(action_history)):
            if action_history[k] != action_history[k - 1]:
                last_change = k
        steps_to_identify = None
        if map_history[-1] in needs_final:
            steps_to_identify = 0
            for k in range(len(map_history) - 1, -1, -1):
                if map_history[k] not in needs_final:
                    steps_to_identify = k + 1
                    break
        regret = loss(needs_final, final_action)
        episodes.append(
            EpisodeRecord(
                policy=policy,
                learner=spec.index,
                subject_id=scenario.subject_id,
                truth=needs_final[0],
                checks=n,
                check_minutes=n * check_cost,
                final_action=final_action,
                correct_action=final_action in {route_for(h) for h in needs_final},
                identified=map_history[-1] in needs_final,
                regret_minutes=regret,
                total_minutes=n * check_cost + regret,
                wasted_check_minutes=(n - last_change) * check_cost,
                stop_verdict=decision.verdict if decision is not None else "stop",
                stop_reason=decision.reason if decision is not None else "",
                first_ranking=first_ranking,
                steps_to_identify=steps_to_identify,
            )
        )
    return checks, episodes


def _run_chunk(payload: tuple[World, Sequence[FamilyLearner], MultiSimSettings]) -> tuple[list[CheckRecord], list[EpisodeRecord]]:
    world, specs, settings = payload
    models = _Models(world)
    checks: list[CheckRecord] = []
    episodes: list[EpisodeRecord] = []
    for spec in specs:
        c, e = run_family_learner(world, spec, settings, models)
        checks.extend(c)
        episodes.extend(e)
    return checks, episodes


@dataclass
class MultiSimRun:
    settings: MultiSimSettings
    learners: list[FamilyLearner]
    checks: list[CheckRecord]
    episodes: list[EpisodeRecord]


def run_family_simulation(
    world: World,
    settings: MultiSimSettings,
    *,
    learners: Sequence[FamilyLearner] | None = None,
    pool: ProcessPoolExecutor | None = None,
) -> MultiSimRun:
    specs = list(learners) if learners is not None else draw_family_learners(world, settings)
    if (settings.workers <= 1 and pool is None) or len(specs) < 8:
        checks, episodes = _run_chunk((world, specs, settings))
    else:
        workers = settings.workers if pool is None else max(settings.workers, 1)
        size = max(1, math.ceil(len(specs) / (workers * 4)))
        chunks = [specs[i : i + size] for i in range(0, len(specs), size)]
        checks, episodes = [], []
        payloads = [(world, chunk, settings) for chunk in chunks]
        if pool is not None:
            results = list(pool.map(_run_chunk, payloads))
        else:
            with ProcessPoolExecutor(max_workers=workers) as own:
                results = list(own.map(_run_chunk, payloads))
        for c, e in results:
            checks.extend(c)
            episodes.extend(e)
    checks.sort(key=lambda r: (r.policy, r.learner, r.step))
    episodes.sort(key=lambda r: (r.policy, r.learner))
    return MultiSimRun(settings=settings, learners=specs, checks=checks, episodes=episodes)


def with_policy(settings: MultiSimSettings, **changes: Any) -> MultiSimSettings:
    return replace(settings, policy=replace(settings.policy, **changes))


__all__ = [
    "MULTISIM_VERSION",
    "FamilyLearner",
    "MultiSimRun",
    "MultiSimSettings",
    "World",
    "draw_family_learners",
    "run_family_simulation",
    "true_loss",
    "with_policy",
]
