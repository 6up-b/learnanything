"""Synthetic-only ADM experiment; design values: docs/reviews/adm0-preregistration.md.

No vault/config reads, writes, selection changes or model calls. The old
ad_synthetic scenarios are untouched. Effects are positive easiness in eta;
all their covariance with shared state is retained by the real AD Bank.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field, replace
from statistics import NormalDist

import numpy as np

from learnloop.adaptive_difficulty import model as M
from learnloop.adaptive_difficulty import priors as P
from learnloop.adaptive_difficulty.state import ItemSpec, View
from learnloop.scheduling.fsrs import (
    FSRS6_DEFAULT_WEIGHTS, MemoryState, Rating, apply_review, retrievability_array,
)
from learnloop.sim.ad_synthetic import rng_for, sample_category

SEEDS = tuple(f"adm0-v1:{i}" for i in range(8))
LEARNERS = 8
RHO_SUPPORTS = ((.5,), (0., .5, 1.), (0., .25, .5, .75, 1.))
LADDERS = ((6.,), (1.5, 6., 24.), (.375, 1.5, 6., 24., 96.))
CURVE_HOURS = (0., .375, 1.5, 6., 24., 96.)
Z95 = NormalDist().inv_cdf(.975)
CLIP = 1e-9


@dataclass(frozen=True)
class Candidate:
    rhos: tuple[float, ...] = RHO_SUPPORTS[1]
    ladder: tuple[float, ...] = LADDERS[1]
    item_mean: float = .5
    family_mean: float = 0.
    item_var: float = .25
    family_var: float = .25
    extra_mean: float = 0.
    extra_var: float = .25
    effect_scale: float = 1.


def candidates(subject: bool) -> dict[str, Candidate]:
    out = {}
    supports = RHO_SUPPORTS if subject else ((0.,), (.5,), (1.,))
    for j, support in enumerate(supports):
        for k, ladder in enumerate(LADDERS):
            out[f"{'R' + str(len(support)) if subject else 'rho' + str(j / 2)}-H{len(ladder)}"] = Candidate(
                rhos=support, ladder=ladder)
    reference = Candidate(rhos=RHO_SUPPORTS[1] if subject else (.5,))
    for name in ("item_var", "family_var", "extra_var", "effect_scale"):
        for factor in (.25, 4.):
            out[f"{name}x{factor:g}"] = replace(reference, **{name: getattr(reference, name) * factor})
    for name in ("item_mean", "family_mean", "extra_mean"):
        for delta in (-.5, .5):
            out[f"{name}{delta:+g}"] = replace(reference, **{name: getattr(reference, name) + delta})
    return out


@dataclass(frozen=True)
class Event:
    index: int
    at: float  # days since the registered UTC origin
    item: str
    family: str
    stratum: str
    singleton: bool = False
    delay_source: str = "assigned"
    warmth_hours: float = math.inf

    @property
    def spec(self) -> ItemSpec:
        return ItemSpec(self.item, "lo", "subject", "retrieval", {"facet": 1.})


def schedule() -> tuple[Event, ...]:
    offsets = (0., 1 / 24, .25, 1., 3., 7., 30., 31., 32., 33., 34., 35.)
    events = []
    for block in range(4):
        family = f"family:{block}"
        singleton = f"singleton:{block}"
        for j, offset in enumerate(offsets):
            if j < 7:
                item, group, kind = f"anchor:{block}", family, "first_surface" if j == 0 else "same_item"
            elif j < 9:
                item, group, kind = f"sibling:{block}:{j}", family, "unseen_sibling"
            elif j < 11:
                item, group, kind = singleton, f"item:{singleton}", "singleton_first" if j == 9 else "same_item"
            else:
                item, group, kind = f"novel:{block}", f"novel-family:{block}", "novel_after_drilling"
            at = block * 36 + offset
            hours = (at - events[-1].at) * 24 if events else math.inf
            events.append(Event(len(events), at, item, group, kind, j in (9, 10),
                                "assigned" if block % 2 == 0 else "natural", hours))
    return tuple(events)


@dataclass(frozen=True)
class MemoryInputs:
    item_r: np.ndarray | None = None
    family_r: np.ndarray | None = None
    item_delay: float | None = None


class ReviewFold:
    """Synthetic resolved reviews only; strict pre-serve lookups, even with ties/future rows."""

    def __init__(self, n: int):
        self.n = n
        self.history: dict[str, list[tuple[float, list[MemoryState]]]] = {}

    def previous(self, key: str, at: float) -> tuple[float, list[MemoryState]] | None:
        eligible = [row for row in self.history.get(key, ()) if row[0] < at]
        return max(eligible, key=lambda row: row[0]) if eligible else None

    def inputs(self, event: Event, *, multiplier: float = 1.) -> MemoryInputs:
        item = self.previous(f"i:{event.item}", event.at)
        family = None if event.singleton else self.previous(f"f:{event.family}", event.at)

        def recall(previous):
            if previous is None:
                return None
            at, states = previous
            return retrievability_array(np.array([s.stability for s in states]) * multiplier,
                                        event.at - at, FSRS6_DEFAULT_WEIGHTS)

        return MemoryInputs(recall(item), recall(family), None if item is None else event.at - item[0])

    def append(self, event: Event, categories: np.ndarray) -> None:
        keys = [f"i:{event.item}"] + ([] if event.singleton else [f"f:{event.family}"])
        for key in keys:
            previous = self.previous(key, event.at)
            old = [None] * self.n if previous is None else previous[1]
            elapsed = 0. if previous is None else event.at - previous[0]
            states = [apply_review(state, (Rating.AGAIN, Rating.HARD, Rating.GOOD)[int(category)], elapsed)
                      for state, category in zip(old, categories, strict=True)]
            self.history.setdefault(key, []).append((event.at, states))


def logit(p: np.ndarray) -> np.ndarray:
    p = np.clip(p, CLIP, 1 - CLIP)
    return np.log(p) - np.log1p(-p)


@dataclass(frozen=True)
class World:
    rho: float
    item_weight: float = .5
    family_weight: float = 0.
    ladder: tuple[float, ...] = LADDERS[0]
    warmth: tuple[float, ...] = (1.,)
    stability_multiplier: float = 1.


WORLDS = {
    "independent": World(0.), "balanced": World(.5), "shared": World(1.),
    "no_memory": World(.5, item_weight=0.),
    "family_memory": World(.5, 1., .5, LADDERS[1], (.5, 1., -.5)),
    "slow_retention": World(.5, 1., .5, LADDERS[2], (.5, 0., 1., 0., .5), math.exp(.5)),
}


@dataclass
class Dataset:
    world: World
    events: tuple[Event, ...]
    initial_ability: np.ndarray
    gamma: np.ndarray
    family_effect: dict[str, np.ndarray]
    item_effect: dict[str, np.ndarray]
    uniforms: np.ndarray
    categories: np.ndarray
    eta: np.ndarray
    ability_after: np.ndarray
    inputs: list[MemoryInputs]

    @property
    def n(self) -> int:
        return len(self.initial_ability)


def generate(world: str, seed: str, *, n: int = LEARNERS) -> Dataset:
    truth = WORLDS[world]
    rng = rng_for(seed)  # deliberately no world/arm name: common normals and uniforms
    events = schedule()
    ability = rng.normal(0., math.sqrt(P.COLD_START_VARIANCE), n)
    initial = ability.copy()
    gamma = rng.normal(P.GAMMA_PRIOR[1], math.sqrt(P.GAMMA_PRIOR[2]), n)
    families = {e.family: rng.normal(size=n) for e in events if e.family not in {x.family for x in events[:e.index]}}
    items = {e.item: rng.normal(size=n) for e in events if e.item not in {x.item for x in events[:e.index]}}
    families = {k: v * math.sqrt(truth.rho) for k, v in families.items()}
    singletons = {e.item for e in events if e.singleton}
    items = {k: v * (1. if k in singletons else math.sqrt(1 - truth.rho)) for k, v in items.items()}
    uniforms = rng.random((len(events), n))
    fold = ReviewFold(n)
    seen = set()
    eta, categories, after, inputs = [], [], [], []
    for event in events:
        warm = sum(w * math.exp(-event.warmth_hours / h) for h, w in zip(truth.ladder, truth.warmth, strict=True))
        base = ability + items[event.item] + (0. if event.singleton else families[event.family]) + warm
        inputs.append(fold.inputs(event))
        memory = fold.inputs(event, multiplier=truth.stability_multiplier)
        value = base.copy()
        if memory.item_r is not None:
            value += truth.item_weight * (logit(memory.item_r) - base)
        if memory.family_r is not None:
            value += truth.family_weight * (logit(memory.family_r) - base)
        category = sample_category(value, uniforms[event.index])
        eta.append(value)
        categories.append(category)
        if event.family not in seen:
            ability = ability + gamma
            seen.add(event.family)
        after.append(ability.copy())
        fold.append(event, category)
    return Dataset(truth, events, initial, gamma, families, items, uniforms, np.array(categories),
                   np.array(eta), np.array(after), inputs)


def family_name(family: str) -> str:
    return f"adm-family:{family}"


def item_name(item: str) -> str:
    return f"adm-item:{item}"


@dataclass
class Prediction:
    mean: np.ndarray
    variance: np.ndarray
    residual: np.ndarray
    probabilities: np.ndarray  # per learner, three categories
    x_item: np.ndarray
    x_family: np.ndarray
    u: np.ndarray


class MemoryArm:
    """Real AD bank with candidate coordinates; no production configuration is changed."""

    def __init__(self, n: int, *, subject: bool, candidate: Candidate | None, full_grid: bool = False):
        self.candidate = candidate
        self.n = n
        self.rhos = (0.,) if candidate is None else candidate.rhos
        base = (P.hyper_grid() if full_grid else P.uniform_points(P.hyper_grid())) if subject else (P.LO_VIEW_POINT,)
        points = tuple(point for point in base for _ in self.rhos)
        self.bank = M.Bank(points, groups=n)
        self.view = View(self.bank, subject_view=subject)
        self.rho = np.tile(self.rhos, n * len(base))
        self.seen: set[str] = set()
        self.learning_count = 0
        self.last_learned = False
        self.last_learning_delta = np.zeros(self.bank.B)
        if candidate is not None:
            self.append_coordinate("adm-memory:item", candidate.item_mean, candidate.item_var)
            self.append_coordinate("adm-memory:family", candidate.family_mean, candidate.family_var)
            for h in candidate.ladder:
                if h != P.WARMTH_HOURS:
                    self.append_coordinate(f"adm-warmth:{h:g}", candidate.extra_mean, candidate.extra_var)

    def append_coordinate(self, name: str, mean: float, variance: float | np.ndarray) -> None:
        # The simulation uses the bank's existing lazy append primitive; no new persisted type.
        self.bank._append(name, np.full(self.bank.B, mean), np.broadcast_to(variance, (self.bank.B,)).copy())

    def rows(self, values: np.ndarray) -> np.ndarray:
        return np.repeat(values, self.bank.P, axis=0)

    def mix(self, values: np.ndarray) -> np.ndarray:
        shaped = values.reshape((self.n, self.bank.P) + values.shape[1:])
        return np.einsum("np,np...->n...", self.bank.weights(), shaped)

    def mixture_moments(self, mean: np.ndarray, var: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        m = self.mix(mean)
        return m, np.maximum(self.mix(var + mean ** 2) - m ** 2, 0.)

    def prepare(self, event: Event) -> None:
        self.view.ensure(event.spec, event.at)

    def base_projection(self, event: Event) -> tuple[np.ndarray, np.ndarray]:
        u, _, _ = self.view.projection(event.spec, math.exp(-event.warmth_hours / P.WARMTH_HOURS))
        residual = np.full(self.bank.B, (P.A * P.TAU0) ** 2)
        c = self.candidate
        if c is None:
            return u, residual
        residual *= c.effect_scale
        for h in c.ladder:
            if h != P.WARMTH_HOURS:
                u[:, self.bank.index[f"adm-warmth:{h:g}"]] = math.exp(-event.warmth_hours / h)
        if self.bank.has(item_name(event.item)):
            u[:, self.bank.index[item_name(event.item)]] = 1.
            residual[:] = 0.
        elif not event.singleton and self.bank.has(family_name(event.family)):
            residual *= 1 - self.rho
        if not event.singleton and self.bank.has(family_name(event.family)):
            u[:, self.bank.index[family_name(event.family)]] = 1.
        return u, residual

    def predict(self, event: Event, inputs: MemoryInputs) -> Prediction:
        self.prepare(event)
        u, residual = self.base_projection(event)
        base, _ = self.bank.moments(u)
        xi, xf = np.zeros(self.bank.B), np.zeros(self.bank.B)
        if self.candidate is not None:
            if inputs.item_r is not None:
                xi = self.rows(logit(inputs.item_r)) - base
            if inputs.family_r is not None and not event.singleton:
                xf = self.rows(logit(inputs.family_r)) - base
            u[:, self.bank.index["adm-memory:item"]] = xi
            u[:, self.bank.index["adm-memory:family"]] = xf
        m, v = self.bank.moments(u)
        probabilities = self.mix(M.category_probabilities(m, v + residual, np.zeros(self.bank.B)))
        return Prediction(m, v, residual, probabilities, xi, xf, u)

    def observe(self, event: Event, prediction: Prediction, category: np.ndarray, *, eligible: bool = True,
                learning: bool = True) -> None:
        first = event.family not in self.seen
        self.seen.add(event.family)  # consume even an ineligible first graded surface
        self.last_learned = False
        self.last_learning_delta = np.zeros(self.bank.B)
        if not eligible:
            return
        c = self.candidate
        if c is None:
            if first:
                self.view.observe(event.spec, self.rows(category), event.at,
                                  warmth=math.exp(-event.warmth_hours / P.WARMTH_HOURS), learn=False)
        else:
            # Match View.observe's transition boundary: the served prediction
            # precedes drift, measurement and learning. Effects drift at that
            # same boundary; future time is never added to a frozen forecast.
            self.bank.drift(M.cell_name("facet", "retrieval"), event.at)
            for name in (family_name(event.family), item_name(event.item)):
                if self.bank.has(name):
                    self.bank.drift(name, event.at)
            if not event.singleton and not self.bank.has(family_name(event.family)):
                self.append_coordinate(family_name(event.family), 0., self.rho * c.effect_scale)
                self.bank.last_update[family_name(event.family)] = event.at
            if not self.bank.has(item_name(event.item)):
                self.append_coordinate(item_name(event.item), 0., c.effect_scale * (1. if event.singleton else 1 - self.rho))
                self.bank.last_update[item_name(event.item)] = event.at
            u, _ = self.base_projection(event)
            # Frozen at prediction, before the current category or coordinate update.
            u[:, self.bank.index["adm-memory:item"]] = prediction.x_item
            u[:, self.bank.index["adm-memory:family"]] = prediction.x_family
            self.bank.update(u, self.rows(category), residual_variance=0.)
        if first and learning:
            before = self.bank.mean(M.cell_name("facet", "retrieval"))
            self.view.learn(event.spec)
            self.last_learning_delta = self.bank.mean(M.cell_name("facet", "retrieval")) - before
            self.last_learned = True
            self.learning_count += 1

    def step(self, event: Event, inputs: MemoryInputs, category: np.ndarray, *, eligible: bool = True) -> Prediction:
        prediction = self.predict(event, inputs)
        self.observe(event, prediction, category, eligible=eligible)
        return prediction

    def coordinate_moments(self, name: str) -> tuple[np.ndarray, np.ndarray]:
        return self.mixture_moments(self.bank.mean(name), self.bank.variance(name))

    def ability_moments(self) -> tuple[np.ndarray, np.ndarray]:
        vector = self.view.cell_vector("subject", "facet", "retrieval")
        return self.mixture_moments(*self.bank.moments(vector))

    def curve_moments(self, hours: float) -> tuple[np.ndarray, np.ndarray]:
        u = np.zeros(self.bank.d)
        u[self.bank.index["zeta"]] = math.exp(-hours / 6)
        if self.candidate:
            for h in self.candidate.ladder:
                if h != 6:
                    u[self.bank.index[f"adm-warmth:{h:g}"]] = math.exp(-hours / h)
        return self.mixture_moments(*self.bank.moments(u))


def recovery_snapshot(data: Dataset, arm: MemoryArm, index: int) -> dict:
    moments = {"ability": arm.ability_moments()}
    truths = {"ability": data.ability_after[index]}
    prior = {"ability": np.full(data.n, P.COLD_START_VARIANCE)}
    c = arm.candidate
    if c is not None:
        event = data.events[0]
        for name, coordinate, truth, var in (
            ("family", family_name(event.family), data.family_effect[event.family], np.mean(c.rhos) * c.effect_scale),
            ("item", item_name(event.item), data.item_effect[event.item], (1 - np.mean(c.rhos)) * c.effect_scale),
            ("memory_item", "adm-memory:item", data.world.item_weight, c.item_var),
            ("memory_family", "adm-memory:family", data.world.family_weight, c.family_var),
        ):
            moments[name] = arm.coordinate_moments(coordinate)
            truths[name] = np.broadcast_to(truth, (data.n,))
            prior[name] = np.full(data.n, var)
    for h in CURVE_HOURS:
        key = f"warmth@{h:g}h"
        moments[key] = arm.curve_moments(h)
        truth = sum(w * math.exp(-h / scale) for scale, w in zip(data.world.ladder, data.world.warmth, strict=True))
        truths[key] = np.full(data.n, truth)
        variance = P.ZETA_PRIOR[2] * math.exp(-2 * h / 6)
        if c is not None:
            variance += sum(c.extra_var * math.exp(-2 * h / scale) for scale in c.ladder if scale != 6)
        prior[key] = np.full(data.n, variance)
    out = {}
    for key, (mean, var) in moments.items():
        error = mean - truths[key]
        out[key] = {"mse": float(np.mean(error ** 2)), "bias": float(np.mean(error)),
                    "coverage": float(np.mean(np.abs(error) <= Z95 * np.sqrt(var))),
                    "variance_ratio": float(np.mean(var / prior[key])) if np.all(prior[key] > 0) else None}
    return out


@dataclass
class ReplayResult:
    probabilities: np.ndarray
    covered: np.ndarray
    categories: np.ndarray
    uniforms: np.ndarray
    recovery: dict = field(default_factory=dict)
    rho_weights: list[float] = field(default_factory=list)


def replay(data: Dataset, arm: MemoryArm) -> ReplayResult:
    probabilities, covered, recovery = [], [], {}
    for event, inputs, category in zip(data.events, data.inputs, data.categories, strict=True):
        pred = arm.predict(event, inputs)
        mean, var = arm.mixture_moments(pred.mean, pred.variance + pred.residual)
        probabilities.append(pred.probabilities[:, 2])
        covered.append(np.abs(data.eta[event.index] - mean) <= Z95 * np.sqrt(var))
        arm.observe(event, pred, category)
        if event.index in (11, 47):
            recovery[str(event.index + 1)] = recovery_snapshot(data, arm, event.index)
    weights = arm.bank.weights().reshape(data.n, -1, len(arm.rhos)).sum(axis=1).mean(axis=0)
    return ReplayResult(np.array(probabilities), np.array(covered), data.categories, data.uniforms,
                        recovery, weights.tolist())


def variance_floor(*, effect_scale: float = 1., steps: int = 512) -> dict:
    arm = MemoryArm(1, subject=False, candidate=Candidate(rhos=(.5,), ladder=(6.,), effect_scale=effect_scale))
    event = schedule()[0]
    minimum = P.COLD_START_VARIANCE
    for index in range(steps):
        pred = arm.predict(event, MemoryInputs())
        arm.observe(event, pred, np.array([2 if index % 2 else 0]), learning=False)
        minimum = min(minimum, float(arm.ability_moments()[1][0]))
    ability = arm.view.cell_vector("subject", "facet", "retrieval")
    effect = np.zeros(arm.bank.d)
    effect[arm.bank.index[family_name(event.family)]] = 1
    effect[arm.bank.index[item_name(event.item)]] = 1
    sibling = arm.predict(replace(schedule()[7], at=0, warmth_hours=math.inf), MemoryInputs())
    novel = arm.predict(replace(schedule()[11], at=0, warmth_hours=math.inf), MemoryInputs())
    return {"steps": steps, "effect_variance": effect_scale,
            "floor": P.COLD_START_VARIANCE * effect_scale / (P.COLD_START_VARIANCE + effect_scale),
            "minimum_ability_variance": minimum, "final_ability_variance": float(arm.ability_moments()[1][0]),
            "ability_effect_covariance": float(ability @ arm.bank.S[0] @ effect),
            "sibling_variance": float((sibling.variance + sibling.residual)[0]),
            "novel_variance": float((novel.variance + novel.residual)[0])}


def warmth_check(ladder: tuple[float, ...], hours: float) -> dict:
    event = replace(schedule()[0], warmth_hours=hours)
    old = MemoryArm(1, subject=False, candidate=None).predict(event, MemoryInputs())
    new = MemoryArm(1, subject=False, candidate=Candidate(rhos=(.5,), ladder=ladder)).predict(event, MemoryInputs())
    return {"hours": hours, "ladder": list(ladder), "old_mean": float(old.mean[0]), "mean": float(new.mean[0]),
            "old_variance": float(old.variance[0]), "variance": float(new.variance[0]),
            "added_variance": sum(.25 * math.exp(-2 * hours / h) for h in ladder if h != 6),
            "old_success": float(old.probabilities[0, 2]), "success": float(new.probabilities[0, 2]),
            "old_band": float(M.band_probability(old.mean, old.variance, 0., (.7, .8))[0]),
            "band": float(M.band_probability(new.mean, new.variance, 0., (.7, .8))[0])}
