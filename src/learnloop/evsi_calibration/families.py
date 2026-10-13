"""Simulator families as true learners over the Eedi 2024 question bank.

Each fitted family (:mod:`.family_fit`) becomes a **truth world** for the
simulation: it draws a learner's latent state, answers a 2024 question, maps
the state to the decision-relevant *needs* (which repairs would be right), and,
for the learning family, moves the state after each answer. Every family also
provides its own **calibrated single-cause system model**: the population
average ``P(option | hypothesis, question)`` and the prior over the
simulation's hypotheses (``knows``, ``mis:<id>``, ``other``) implied by the
family, computed from the family's mean item parameters (the system never
knows a question's own parameters, exactly as in the single-family study).

Transfer from 2020 to 2024 follows the single-family study: a subject with
at least two fitted triples uses its own parameters, the rest the pooled ones.
Item-level parameters cannot transfer (different questions), so a 2024
question takes the parameters of one fitted 2020 item of its subject (or of
the pool), chosen by a seeded hash of the question: real between-item
variation, without inventing a distribution for it.

Families
--------
``lca``  the single-family study's world, unchanged (:mod:`.world`).
``cdm``  a learner is a profile (skill, set of held misconceptions, at most
         two). Needs: every held hypothesis misconception; else ``knows`` with
         the skill, ``other`` without.
``nrm``  a learner is ``(theta, eta_1..eta_K)``. A misconception is *held*
         when its designated distractor is the learner's most likely answer on
         the subject's typical item; ``knows`` when nothing is held and the
         correct answer is more likely than not; else ``other``. Holding is a
         matter of degree, so a holder near the threshold behaves almost like
         a non-holder.
``lta``  the latent class states with the learning family's fitted
         within-session transitions after every answer (history and checks).
         Fitted to Eedi they are close to the identity: within one session
         nobody's state moves measurably.
``lta_reveal``  a stress variant, not a fit: after every answer (the history's
         and the checks') the learner moves at the fitted *between-session*
         rates, as if each answer's reveal taught as much as the days of
         teaching between Eedi sessions.

Instrument strength (``with_strength``): "what if a check were as diagnostic
as consistency ``c``", for truth and system alike. Who holds what does not
change; only the response model does, and holders' mean probability of their
misconception's distractor on a question that targets it becomes ``c``:

* ``lca``/``lta``: :func:`.world.with_truth` (holder correct : other kept);
* ``cdm``: one logit shift of the designated option in the triggered groups of
  every item (the other options rescaled);
* ``nrm``: one logit shift of the held misconception's distractor for holders
  only (status from the typical item); within holders the response still
  rises with the trait.

The shift is found by bisection so that the family's calibrated model, over
the simulation bank itself, puts exactly ``c`` on a held misconception's
distractor on a question that targets it (the quantity the latent class
override sets exactly). False alarms, slips and prevalences do not move.
"""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass, replace
from itertools import combinations
from typing import Any, Mapping, Sequence

import numpy as np

from learnloop.evsi_calibration.eedi import OPTIONS, EediBank, EediQuestion
from learnloop.evsi_calibration.family_fit import FamilyFits, nrm_logits
from learnloop.evsi_calibration.response_fit import ResponseFit, assemble_response_fit, FitSettings
from learnloop.evsi_calibration.world import (
    HYP_KNOWS,
    HYP_OTHER,
    MIS_PREFIX,
    Scenario,
    TrueLearner,
    build_scenarios,
    eedi_row,
    hand_set_row,
    misconception_hypothesis,
    with_truth,
)

FAMILY_NAMES = ("lca", "cdm", "nrm", "lta")
STRESS_FAMILIES = ("lta_reveal",)
POPULATION_SAMPLE = 2000
#: Items and learners the strength calibration of the continuous family averages over.
STRENGTH_ITEMS = 64
STRENGTH_POPULATION = 4000


def _hash_int(*parts: Any) -> int:
    return int(hashlib.sha256("|".join(str(p) for p in parts).encode("utf-8")).hexdigest()[:12], 16)


def _row(values: Mapping[str, float]) -> dict[str, float]:
    total = sum(max(v, 0.0) for v in values.values())
    return {o: max(values.get(o, 0.0), 0.0) / total for o in OPTIONS}


# -- the interface ----------------------------------------------------------------------------------


class ScenarioModel:
    """One family's truth and calibrated system model on one 2024 subject."""

    learns: bool = False

    def __init__(self, scenario: Scenario) -> None:
        self.scenario = scenario
        self.hypotheses = scenario.hypotheses
        self._system_rows: dict[str, dict[str, dict[str, float]]] = {}

    # system side
    def system_prior(self) -> dict[str, float]:
        raise NotImplementedError

    def system_rows(self, question: EediQuestion) -> dict[str, dict[str, float]]:
        cached = self._system_rows.get(question.question_id)
        if cached is None:
            cached = self._compute_system_rows(question)
            self._system_rows[question.question_id] = cached
        return cached

    def _compute_system_rows(self, question: EediQuestion) -> dict[str, dict[str, float]]:
        raise NotImplementedError

    # truth side
    def draw_state(self, rng: np.random.Generator) -> Any:
        raise NotImplementedError

    def row(self, state: Any, question: EediQuestion) -> dict[str, float]:
        raise NotImplementedError

    def needs(self, state: Any) -> tuple[str, ...]:
        raise NotImplementedError

    def transition(self, state: Any, uniform: float) -> Any:
        return state

    def answer(self, state: Any, question: EediQuestion, rng: np.random.Generator) -> str:
        row = self.row(state, question)
        options = list(OPTIONS)
        return str(rng.choice(options, p=[row[o] for o in options]))

    def targeted_consistencies(self) -> list[float]:
        """The system model's P(the misconception's own distractor | it is held)
        on every question that targets it (what ``consistency`` means here)."""

        out: list[float] = []
        for question in self.scenario.questions:
            rows = self.system_rows(question)
            for h in self.hypotheses:
                if h.startswith(MIS_PREFIX):
                    options = question.options_for(h[len(MIS_PREFIX):])
                    if options:
                        out.append(sum(rows[h][o] for o in options))
        return out


def _bisect_strength(consistency_at: Any, target: float, lo: float, hi: float, steps: int = 30) -> float:
    """The smallest-error shift: ``consistency_at`` is increasing in the shift."""

    for _ in range(steps):
        mid = (lo + hi) / 2.0
        if consistency_at(mid) < target:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


class FamilyModel:
    """A simulator family at one instrument strength (``None`` = as fitted)."""

    name: str = ""
    fitted: bool = True
    strength: float | None = None

    @property
    def key(self) -> str:
        return f"{self.name}@{'fitted' if self.strength is None else self.strength}"

    def scenario_model(self, scenario: Scenario) -> ScenarioModel:
        raise NotImplementedError

    def with_strength(self, consistency: float | None) -> "FamilyModel":
        raise NotImplementedError


# -- lca / lta ----------------------------------------------------------------------------------------


class LatentClassScenario(ScenarioModel):
    def __init__(self, scenario: Scenario, prior: Mapping[str, float] | None = None) -> None:
        super().__init__(scenario)
        self._prior = dict(prior) if prior is not None else dict(scenario.prior)
        self._learner = TrueLearner(scenario, HYP_KNOWS, np.random.default_rng(0))

    def system_prior(self) -> dict[str, float]:
        return dict(self._prior)

    def _compute_system_rows(self, question: EediQuestion) -> dict[str, dict[str, float]]:
        return {h: eedi_row(h, question, self.scenario.truth.values) for h in self.hypotheses}

    def draw_state(self, rng: np.random.Generator) -> str:
        hypotheses = list(self.hypotheses)
        return str(rng.choice(hypotheses, p=[self._prior[h] for h in hypotheses]))

    def row(self, state: str, question: EediQuestion) -> dict[str, float]:
        return eedi_row(state, question, self.scenario.truth.values,
                        consistency=self._learner.consistency_for(question))

    def needs(self, state: str) -> tuple[str, ...]:
        return (state,)


@dataclass
class LcaFamily(FamilyModel):
    """The single-family study's world (its scenarios carry the fitted truth)."""

    scenarios_by_subject: Mapping[int, Scenario]
    name: str = "lca"
    fitted: bool = True
    strength: float | None = None

    def scenario_model(self, scenario: Scenario) -> ScenarioModel:
        own = self.scenarios_by_subject[scenario.subject_id]
        if self.strength is not None:
            own = with_truth([own], consistency=self.strength)[0]
        return LatentClassScenario(own)

    def with_strength(self, consistency: float | None) -> "LcaFamily":
        return replace(self, strength=consistency)


class LearningScenario(LatentClassScenario):
    """Latent class states that move after every answer (the learning family)."""

    learns = True

    def __init__(self, scenario: Scenario, transitions: np.ndarray) -> None:
        super().__init__(scenario)
        self.transitions = np.asarray(transitions, dtype=float)
        self._misconceptions = [h for h in self.hypotheses if h.startswith(MIS_PREFIX)]

    def next_distribution(self, state: str) -> dict[str, float]:
        """The fitted 3x3 chain on the K-misconception state space: a holder can
        resolve (to ``knows``) or lose the misconception (to ``other``); an
        acquisition rate is spread over the subject's misconceptions."""

        T = self.transitions
        K = max(len(self._misconceptions), 1)
        k, h, u = 0, 1, 2
        out: dict[str, float] = {}
        if state == HYP_KNOWS:
            out[HYP_KNOWS] = T[k, k]
            out[HYP_OTHER] = T[k, u]
            for m in self._misconceptions:
                out[m] = T[k, h] / K
        elif state == HYP_OTHER:
            out[HYP_OTHER] = T[u, u]
            out[HYP_KNOWS] = T[u, k]
            for m in self._misconceptions:
                out[m] = T[u, h] / K
        else:
            out[state] = T[h, h]
            out[HYP_KNOWS] = T[h, k]
            out[HYP_OTHER] = T[h, u]
        total = sum(out.values())
        return {s: p / total for s, p in out.items()}

    def transition(self, state: str, uniform: float) -> str:
        cumulative = 0.0
        distribution = self.next_distribution(state)
        for candidate in sorted(distribution):
            cumulative += distribution[candidate]
            if uniform < cumulative:
                return candidate
        return state


@dataclass
class LtaFamily(FamilyModel):
    """The learning family: latent class emissions + fitted transitions."""

    scenarios_by_subject: Mapping[int, Scenario]
    transitions: np.ndarray
    name: str = "lta"
    fitted: bool = True
    strength: float | None = None

    def scenario_model(self, scenario: Scenario) -> ScenarioModel:
        own = self.scenarios_by_subject[scenario.subject_id]
        if self.strength is not None:
            own = with_truth([own], consistency=self.strength)[0]
        return LearningScenario(own, self.transitions)

    def with_strength(self, consistency: float | None) -> "LtaFamily":
        return replace(self, strength=consistency)


# -- cdm ------------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class CdmProfilePrior:
    p_skill: float
    p_hold_no_skill: float
    p_hold_skill: float
    pair_lift: float

    def weights(self, attributes: int) -> list[tuple[tuple[int, tuple[int, ...]], float]]:
        held_sets: list[tuple[int, ...]] = [()]
        for size in (1, 2):
            if size <= attributes:
                held_sets.extend(combinations(range(attributes), size))
        lift = min(max(self.pair_lift if math.isfinite(self.pair_lift) else 1.0, 0.25), 4.0)
        out = []
        for skill in (0, 1):
            p_s = self.p_skill if skill else 1.0 - self.p_skill
            p_h = self.p_hold_skill if skill else self.p_hold_no_skill
            for held in held_sets:
                w = p_s * (p_h ** len(held)) * ((1.0 - p_h) ** (attributes - len(held)))
                if len(held) == 2:
                    w *= lift
                out.append(((skill, held), w))
        total = sum(w for _, w in out)
        return [(profile, w / total) for profile, w in out]


def _cdm_row(phi: np.ndarray, skill: int, triggered: Sequence[str], question: EediQuestion) -> dict[str, float]:
    """``P(option)`` from one item's role-space group rows ``phi`` (4 groups x 4 roles)."""

    row = {o: 0.0 for o in OPTIONS}
    distractors = question.distractors
    if triggered:
        g = phi[2 + skill]
        correct, designated = float(g[0]), float(g[1])
        signature: list[str] = []
        per = designated / len(triggered)
        for misconception in triggered:
            options = question.options_for(misconception)
            for option in options:
                row[option] += per / len(options)
                signature.append(option)
        rest = [d for d in distractors if d not in signature]
        row[question.correct] = correct
        if rest:
            for option in rest:
                row[option] += max(1.0 - correct - designated, 0.0) / len(rest)
        return _row(row)
    g = phi[skill]
    correct, designated, other = float(g[0]), float(g[1]), float((g[2] + g[3]) / 2.0)
    row[question.correct] = correct
    labelled = set(question.misconception_by_option)
    weights = {d: (designated if d in labelled else other) for d in distractors}
    total = sum(weights.values()) or 1.0
    for option, weight in weights.items():
        row[option] = (1.0 - correct) * weight / total
    return _row(row)


class CdmScenario(ScenarioModel):
    def __init__(self, scenario: Scenario, pool: np.ndarray, prior: CdmProfilePrior) -> None:
        super().__init__(scenario)
        self.pool = pool
        self.mean_phi = pool.mean(axis=0)
        self.misconceptions = [h[len(MIS_PREFIX):] for h in self.hypotheses if h.startswith(MIS_PREFIX)]
        self.profiles = prior.weights(len(self.misconceptions))
        self._prior: dict[str, float] | None = None

    def _held(self, profile: tuple[int, tuple[int, ...]]) -> list[str]:
        return [self.misconceptions[k] for k in profile[1]]

    def _primary_weights(self, profile: tuple[int, tuple[int, ...]]) -> dict[str, float]:
        held = self._held(profile)
        if held:
            return {misconception_hypothesis(m): 1.0 / len(held) for m in held}
        return {HYP_KNOWS if profile[0] else HYP_OTHER: 1.0}

    def system_prior(self) -> dict[str, float]:
        if self._prior is None:
            prior = {h: 0.0 for h in self.hypotheses}
            for profile, weight in self.profiles:
                for h, share in self._primary_weights(profile).items():
                    prior[h] += weight * share
            total = sum(prior.values())
            self._prior = {h: v / total for h, v in prior.items()}
        return dict(self._prior)

    def _profile_row(self, profile: tuple[int, tuple[int, ...]], question: EediQuestion, phi: np.ndarray) -> dict[str, float]:
        triggered = [m for m in self._held(profile) if question.options_for(m)]
        return _cdm_row(phi, profile[0], triggered, question)

    def _compute_system_rows(self, question: EediQuestion) -> dict[str, dict[str, float]]:
        sums = {h: {o: 0.0 for o in OPTIONS} for h in self.hypotheses}
        mass = {h: 0.0 for h in self.hypotheses}
        for profile, weight in self.profiles:
            row = self._profile_row(profile, question, self.mean_phi)
            for h, share in self._primary_weights(profile).items():
                mass[h] += weight * share
                for o in OPTIONS:
                    sums[h][o] += weight * share * row[o]
        return {h: _row(sums[h]) if mass[h] > 0 else _row({o: 1.0 for o in OPTIONS}) for h in self.hypotheses}

    def draw_state(self, rng: np.random.Generator) -> tuple[int, tuple[int, ...]]:
        profiles = [p for p, _ in self.profiles]
        index = int(rng.choice(len(profiles), p=[w for _, w in self.profiles]))
        return profiles[index]

    def _item(self, question: EediQuestion) -> np.ndarray:
        return self.pool[_hash_int(self.scenario.subject_id, question.question_id) % self.pool.shape[0]]

    def row(self, state: tuple[int, tuple[int, ...]], question: EediQuestion) -> dict[str, float]:
        return self._profile_row(state, question, self._item(question))

    def needs(self, state: tuple[int, tuple[int, ...]]) -> tuple[str, ...]:
        held = self._held(state)
        if held:
            return tuple(misconception_hypothesis(m) for m in held)
        return (HYP_KNOWS,) if state[0] else (HYP_OTHER,)


def _logit(p: np.ndarray) -> np.ndarray:
    p = np.clip(p, 1e-6, 1 - 1e-6)
    return np.log(p / (1 - p))


def _shift_designated(phi: np.ndarray, delta: float) -> np.ndarray:
    """Shift the designated role's logit by ``delta`` in the triggered groups."""

    out = phi.copy()
    for g in (2, 3):
        d = phi[..., g, 1]
        new_d = 1.0 / (1.0 + np.exp(-(_logit(d) + delta)))
        scale = (1.0 - new_d) / np.clip(1.0 - d, 1e-9, None)
        for r in (0, 2, 3):
            out[..., g, r] = phi[..., g, r] * scale
        out[..., g, 1] = new_d
    return out


@dataclass
class CdmFamily(FamilyModel):
    pools: Mapping[int, np.ndarray]  # subject -> (items, 4, 4)
    priors: Mapping[int, CdmProfilePrior]
    pooled_pool: np.ndarray
    pooled_prior: CdmProfilePrior
    #: Holders' share with the skill (weights the two triggered groups).
    triggered_skill_share: float
    #: The simulation bank, on which a strength is calibrated exactly.
    calibration_scenarios: tuple[Scenario, ...] = ()
    name: str = "cdm"
    fitted: bool = True
    strength: float | None = None
    delta: float = 0.0

    def _pool(self, subject: int) -> np.ndarray:
        pool = self.pools.get(subject)
        if pool is None:
            pool = self.pooled_pool
        return _shift_designated(pool, self.delta) if self.delta else pool

    def scenario_model(self, scenario: Scenario) -> ScenarioModel:
        return CdmScenario(scenario, self._pool(scenario.subject_id),
                           self.priors.get(scenario.subject_id, self.pooled_prior))

    def holder_consistency(self, delta: float = 0.0) -> float:
        phi = _shift_designated(self.pooled_pool, delta) if delta else self.pooled_pool
        s = self.triggered_skill_share
        return float(((1 - s) * phi[:, 2, 1] + s * phi[:, 3, 1]).mean())

    def with_strength(self, consistency: float | None) -> "CdmFamily":
        if consistency is None:
            return replace(self, strength=None, delta=0.0)
        if not self.calibration_scenarios:
            delta = _bisect_strength(self.holder_consistency, consistency, -12.0, 12.0, steps=60)
            return replace(self, strength=consistency, delta=delta)
        base = replace(self, strength=None, delta=0.0)
        models = [base.scenario_model(scenario) for scenario in self.calibration_scenarios]

        def implied(delta: float) -> float:
            values: list[float] = []
            for model in models:
                assert isinstance(model, CdmScenario)
                model.mean_phi = _shift_designated(model.pool, delta).mean(axis=0) if delta else model.pool.mean(axis=0)
                model._system_rows.clear()
                values.extend(model.targeted_consistencies())
            return float(np.mean(values))

        return replace(self, strength=consistency, delta=_bisect_strength(implied, consistency, -12.0, 12.0))


# -- nrm --------------------------------------------------------------------------------------------------


def nrm_threshold(typical: np.ndarray, theta: np.ndarray) -> np.ndarray:
    """The trait value above which the designated distractor is a learner's most
    likely answer on the typical item, given ability ``theta``."""

    a_c, b_c, a_d, b_d, lam, a_o, b_o = (float(v) for v in typical)
    top = np.maximum(np.maximum(a_c * theta + b_c, a_o * theta + b_o), 0.0)
    return (top - a_d * theta - b_d) / max(lam, 1e-6)


class NrmScenario(ScenarioModel):
    """The continuous family on one subject.

    Strength (``holder_shift``): a holder's logit for the distractor of the
    misconception they hold gains ``holder_shift``; nobody else's response
    changes (as in every family). Within holders the response still rises
    with the trait. ``holder_shift = 0`` is the fit."""

    def __init__(self, scenario: Scenario, pool: np.ndarray, typical: np.ndarray,
                 holder_shift: float = 0.0) -> None:
        super().__init__(scenario)
        self.pool = pool
        self.mean_params = pool.mean(axis=0)
        self.typical = typical
        self.holder_shift = holder_shift
        self.misconceptions = [h[len(MIS_PREFIX):] for h in self.hypotheses if h.startswith(MIS_PREFIX)]
        rng = np.random.default_rng(_hash_int("nrm-population", scenario.subject_id))
        K = len(self.misconceptions)
        self.population = rng.standard_normal((POPULATION_SAMPLE, 1 + K))
        self._population_needs = self._needs_batch(self.population)
        index = {h: i for i, h in enumerate(self.hypotheses)}
        #: (S, H): each sampled learner's weight on each hypothesis (its needs, split).
        self._weights = np.zeros((POPULATION_SAMPLE, len(self.hypotheses)))
        for row, needs in enumerate(self._population_needs):
            for h in needs:
                self._weights[row, index[h]] += 1.0 / len(needs)
        self._prior: dict[str, float] | None = None

    def _needs_batch(self, states: np.ndarray) -> list[tuple[str, ...]]:
        theta = states[:, 0]
        threshold = nrm_threshold(self.typical, theta)
        held = states[:, 1:1 + len(self.misconceptions)] > threshold[:, None]
        z0 = nrm_logits(self.typical, theta, np.zeros_like(theta))
        z0 = np.exp(z0 - z0.max(axis=1, keepdims=True))
        knows = z0[:, 0] / z0.sum(axis=1) >= 0.5
        out: list[tuple[str, ...]] = []
        for s in range(states.shape[0]):
            ks = np.flatnonzero(held[s])
            if ks.size:
                out.append(tuple(misconception_hypothesis(self.misconceptions[k]) for k in ks))
            else:
                out.append((HYP_KNOWS,) if knows[s] else (HYP_OTHER,))
        return out

    def _logits(self, params: np.ndarray, theta: np.ndarray, eta: np.ndarray, question: EediQuestion) -> np.ndarray:
        """(S, 4 options) logits for states (theta, eta per misconception) on ``question``.

        ``eta`` is (S, K); labelled distractors of a hypothesis misconception
        read that trait, other labelled ones the trait's mean (0)."""

        roles = nrm_logits(params, theta, np.zeros_like(theta))  # (S, 4): correct, designated@eta0, other_a, ref
        lam = float(params[4])
        threshold = nrm_threshold(self.typical, theta) if self.holder_shift else None
        out = np.zeros((theta.shape[0], 4))
        unlabelled_slot = 0
        for index, option in enumerate(OPTIONS):
            if option == question.correct:
                out[:, index] = roles[:, 0]
                continue
            misconception = question.misconception_by_option.get(option)
            if misconception is not None:
                out[:, index] = roles[:, 1]
                if misconception in self.misconceptions:
                    trait = eta[:, self.misconceptions.index(misconception)]
                    out[:, index] += lam * trait
                    if threshold is not None:
                        out[:, index] += self.holder_shift * (trait > threshold)
                continue
            out[:, index] = roles[:, 2] if unlabelled_slot == 0 else roles[:, 3]
            unlabelled_slot += 1
        return out

    def _probabilities(self, params: np.ndarray, states: np.ndarray, question: EediQuestion) -> np.ndarray:
        z = self._logits(params, states[:, 0], states[:, 1:], question)
        z = z - z.max(axis=1, keepdims=True)
        e = np.exp(z)
        return e / e.sum(axis=1, keepdims=True)

    def system_prior(self) -> dict[str, float]:
        if self._prior is None:
            mass = self._weights.sum(axis=0)
            total = float(mass.sum())
            self._prior = {h: float(mass[i]) / total for i, h in enumerate(self.hypotheses)}
        return dict(self._prior)

    def _compute_system_rows(self, question: EediQuestion) -> dict[str, dict[str, float]]:
        probabilities = self._probabilities(self.mean_params, self.population, question)  # (S, 4)
        sums = self._weights.T @ probabilities  # (H, 4)
        out: dict[str, dict[str, float]] = {}
        for i, h in enumerate(self.hypotheses):
            total = float(sums[i].sum())
            vector = sums[i] / total if total > 0 else np.full(4, 0.25)
            out[h] = _row({o: float(vector[k]) for k, o in enumerate(OPTIONS)})
        return out

    def draw_state(self, rng: np.random.Generator) -> tuple[float, ...]:
        return tuple(float(x) for x in rng.standard_normal(1 + len(self.misconceptions)))

    def row(self, state: tuple[float, ...], question: EediQuestion) -> dict[str, float]:
        params = self.pool[_hash_int(self.scenario.subject_id, question.question_id) % self.pool.shape[0]]
        p = self._probabilities(params, np.asarray([state]), question)[0]
        return _row({o: float(p[i]) for i, o in enumerate(OPTIONS)})

    def needs(self, state: tuple[float, ...]) -> tuple[str, ...]:
        return self._needs_batch(np.asarray([state], dtype=float))[0]


def nrm_holder_rates(items: np.ndarray, typical: np.ndarray, population: np.ndarray,
                     holder_shift: float = 0.0) -> tuple[float, float]:
    """Holders' and non-holders' mean P(designated) on a targeted question.

    Holder status comes from the typical item (it does not change with the
    instrument); the response from ``items`` with the holders' shift."""

    theta, eta = population[:, 0], population[:, 1]
    holder = eta > nrm_threshold(typical, theta)
    z = nrm_logits(items[:, None, :], theta[None, :], eta[None, :])  # (items, S, 4)
    z[..., 1] += holder_shift * holder[None, :]
    z = z - z.max(axis=2, keepdims=True)
    e = np.exp(z)
    p = e[..., 1] / e.sum(axis=2)  # (items, S)
    holders = float(p[:, holder].mean()) if holder.any() else float("nan")
    others = float(p[:, ~holder].mean())
    return holders, others


@dataclass
class NrmFamily(FamilyModel):
    pools: Mapping[int, np.ndarray]  # subject -> (items, 7)
    pooled_pool: np.ndarray
    typical_by_subject: Mapping[int, np.ndarray]
    pooled_typical: np.ndarray
    #: The simulation bank, on which a strength is calibrated exactly.
    calibration_scenarios: tuple[Scenario, ...] = ()
    name: str = "nrm"
    fitted: bool = True
    strength: float | None = None
    holder_shift: float = 0.0

    def scenario_model(self, scenario: Scenario) -> ScenarioModel:
        pool = self.pools.get(scenario.subject_id)
        return NrmScenario(scenario, self.pooled_pool if pool is None else pool,
                           self.typical_by_subject.get(scenario.subject_id, self.pooled_typical),
                           holder_shift=self.holder_shift)

    def _population(self) -> np.ndarray:
        return np.random.default_rng(_hash_int("nrm-strength")).standard_normal((STRENGTH_POPULATION, 2))

    def _calibration_items(self) -> np.ndarray:
        pool = self.pooled_pool
        if pool.shape[0] <= STRENGTH_ITEMS:
            return pool
        rng = np.random.default_rng(_hash_int("nrm-strength-items"))
        return pool[np.sort(rng.choice(pool.shape[0], STRENGTH_ITEMS, replace=False))]

    def holder_rates(self, holder_shift: float = 0.0) -> tuple[float, float]:
        return nrm_holder_rates(self._calibration_items(), self.pooled_typical, self._population(), holder_shift)

    def with_strength(self, consistency: float | None) -> "NrmFamily":
        if consistency is None:
            return replace(self, strength=None, holder_shift=0.0)
        if not self.calibration_scenarios:
            population = self._population()
            items = self._calibration_items()

            def pooled(shift: float) -> float:
                return nrm_holder_rates(items, self.pooled_typical, population, shift)[0]

            return replace(self, strength=consistency,
                           holder_shift=_bisect_strength(pooled, consistency, -15.0, 15.0, steps=50))
        base = replace(self, strength=None, holder_shift=0.0)
        models = [base.scenario_model(scenario) for scenario in self.calibration_scenarios]

        def implied(shift: float) -> float:
            values: list[float] = []
            for model in models:
                assert isinstance(model, NrmScenario)
                model.holder_shift = shift
                model._system_rows.clear()
                values.extend(model.targeted_consistencies())
            return float(np.mean(values))

        return replace(self, strength=consistency, holder_shift=_bisect_strength(implied, consistency, -15.0, 15.0))


# -- building the families from the fits ---------------------------------------------------------------


def lta_response_fit(fits: FamilyFits) -> ResponseFit:
    triples = [fits.lta.triple_fit(index) for index in sorted(fits.lta.start)]
    return assemble_response_fit(triples, settings=FitSettings(seed=fits.settings.seed),
                                 source={"family": "lta", "note": "the learning family's emissions and start mix"})


def build_families(bank: EediBank, fits: FamilyFits) -> dict[str, FamilyModel]:
    """Every family (fitted and stress) as a truth world over the bank."""

    bank_scenarios = tuple(build_scenarios(bank, fits.lca))
    lca_scenarios = {s.subject_id: s for s in bank_scenarios}
    lta_fit = lta_response_fit(fits)
    lta_scenarios = {}
    for scenario in build_scenarios(bank, lta_fit):
        # The learning family's system prior is its start mix (as fitted).
        lta_scenarios[scenario.subject_id] = scenario

    # cdm: item pools and profile priors per subject (>= 2 triples), else pooled.
    cdm_pools: dict[int, np.ndarray] = {}
    cdm_priors: dict[int, CdmProfilePrior] = {}
    all_phi, summaries = [], []
    for subject, fit in sorted(fits.cdm.items()):
        all_phi.append(fit.phi)
        summary = fit.summary()
        summaries.append(summary)
        if fit.attributes >= 2:
            cdm_pools[subject] = fit.phi
            cdm_priors[subject] = CdmProfilePrior(summary["p_skill"], summary["p_hold_given_no_skill"],
                                                  summary["p_hold_given_skill"], summary["pair_lift"])

    def median(name: str) -> float:
        values = [s[name] for s in summaries if math.isfinite(s[name])]
        return float(np.median(values)) if values else float("nan")

    pooled_phi = np.concatenate(all_phi) if all_phi else np.zeros((0, 4, 4))
    cdm = CdmFamily(
        pools=cdm_pools,
        priors=cdm_priors,
        pooled_pool=pooled_phi,
        pooled_prior=CdmProfilePrior(median("p_skill"), median("p_hold_given_no_skill"),
                                     median("p_hold_given_skill"), median("pair_lift")),
        triggered_skill_share=median("triggered_skill_share"),
        calibration_scenarios=bank_scenarios,
    )

    nrm_by_subject: dict[int, list[np.ndarray]] = {}
    for fit in fits.nrm.values():
        nrm_by_subject.setdefault(fit.subject_id, []).append(fit.params)
    nrm_pools = {s: np.concatenate(v) for s, v in nrm_by_subject.items() if len(v) >= 2}
    all_nrm = np.concatenate([f.params for f in fits.nrm.values()]) if fits.nrm else np.zeros((0, 7))
    nrm = NrmFamily(
        pools=nrm_pools,
        pooled_pool=all_nrm,
        typical_by_subject={s: np.median(p, axis=0) for s, p in nrm_pools.items()},
        pooled_typical=np.median(all_nrm, axis=0) if all_nrm.size else np.zeros(7),
        calibration_scenarios=bank_scenarios,
    )
    return {
        "lca": LcaFamily(lca_scenarios),
        "cdm": cdm,
        "nrm": nrm,
        "lta": LtaFamily(lta_scenarios, fits.lta.transitions[0]),
        "lta_reveal": LtaFamily(lta_scenarios, fits.lta.transitions[1], name="lta_reveal", fitted=False),
    }


@dataclass
class HandSetSystem:
    """Today's vocabulary as the system's rows (prior: the truth family's)."""

    name: str = "hand_set"

    def rows(self, scenario: Scenario, question: EediQuestion) -> dict[str, dict[str, float]]:
        return {h: hand_set_row(h, question) for h in scenario.hypotheses}


def implied_quantities(family: FamilyModel, scenarios: Sequence[Scenario]) -> dict[str, Any]:
    """The family's calibrated system model, summarized in the latent class
    model's terms over the simulation bank: consistency on targeted questions,
    false alarm, knower slip, unsure success and the hypothesis prevalences."""

    consistency, holder_correct, false_alarm, slip, unsure_correct = [], [], [], [], []
    prevalence = {"knows": [], "holds": [], "other": [], "multi_need_share": []}
    for scenario in scenarios:
        model = family.scenario_model(scenario)
        prior = model.system_prior()
        prevalence["knows"].append(prior.get(HYP_KNOWS, 0.0))
        prevalence["other"].append(prior.get(HYP_OTHER, 0.0))
        prevalence["holds"].append(sum(v for h, v in prior.items() if h.startswith(MIS_PREFIX)))
        rng = np.random.default_rng(_hash_int("implied", family.key, scenario.subject_id))
        states = [model.draw_state(rng) for _ in range(200)]
        prevalence["multi_need_share"].append(float(np.mean([len(model.needs(s)) > 1 for s in states])))
        for question in scenario.questions:
            rows = model.system_rows(question)
            slip.append(1.0 - rows[HYP_KNOWS][question.correct])
            unsure_correct.append(rows[HYP_OTHER][question.correct])
            labelled = list(question.misconception_by_option)
            if labelled:
                false_alarm.append(float(np.mean([rows[HYP_OTHER][o] for o in labelled])))
            for h in scenario.hypotheses:
                if h.startswith(MIS_PREFIX):
                    options = question.options_for(h[len(MIS_PREFIX):])
                    if options:
                        consistency.append(sum(rows[h][o] for o in options))
                        holder_correct.append(rows[h][question.correct])

    def summary(values: Sequence[float]) -> float | None:
        return round(float(np.mean(values)), 4) if values else None

    return {
        "consistency": summary(consistency),
        "holder_correct": summary(holder_correct),
        "false_alarm": summary(false_alarm),
        "knower_slip": summary(slip),
        "unsure_correct": summary(unsure_correct),
        "prevalence": {k: summary(v) for k, v in prevalence.items()},
    }


__all__ = [
    "FAMILY_NAMES",
    "STRESS_FAMILIES",
    "CdmFamily",
    "FamilyModel",
    "HandSetSystem",
    "LcaFamily",
    "LtaFamily",
    "NrmFamily",
    "ScenarioModel",
    "build_families",
    "implied_quantities",
]
