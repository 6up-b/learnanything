"""Synthetic learners, vaults with known structure and synthetic readers (spec_adaptive_difficulty_v1 §14).

The simulation gates of AD2+AD3 (G-AD2-7, 8, 14, 18; G-AD3-6, 7, 8, 11, 15)
drive the real model (:mod:`learnloop.adaptive_difficulty.model` and
:mod:`~learnloop.adaptive_difficulty.state`) and the real selection rule
(:mod:`~learnloop.adaptive_difficulty.selection`) on simulated learners whose
true parameters are known. Every constant, scenario and threshold is
pre-registered in ``docs/reviews/adaptive-difficulty-ad23.md`` §1.5-1.9; nothing
here was tuned on a run.

**Learners** are vectorized: a bank holds ``groups`` learners times its grid
points, every learner answering the same cell at the same step (the scenarios
are scripted per LO and cell) and each drawing its own feature point from its
own posterior. **The truth** is drawn from ``ad_priors_v1`` (or from the
scenario's stated structure): a subject level, facet and cell offsets,
capability offsets, feature effects ``β``, the origin weight ``α_origin`` (pool
items are generated, ``z_origin = 1``), each learner's own learning rate, and a
residual ``ε ~ N(0, τ0²)`` per item. **Items** are pools of 8 per feature point,
each used once; items at one point are exchangeable to AD (same features and
signals), so a draw is over points and serves the point's next unused item.

**Common random numbers**: within a scenario every arm meets the same truth,
the same item residuals (by point and index) and the same outcome uniforms (by
answer index), so arms differ only in what they choose.

Pure numerics: no vault, repository, connection or model client, and nothing
is written (A1, A2).
"""

from __future__ import annotations

import hashlib
import math
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from learnloop.adaptive_difficulty import model as M
from learnloop.adaptive_difficulty import monitoring as MON
from learnloop.adaptive_difficulty import priors as P
from learnloop.adaptive_difficulty import selection as S
from learnloop.adaptive_difficulty.relatedness import VaultStructure
from learnloop.adaptive_difficulty.state import ItemSpec, View
from learnloop.config import MasteryConfig
from learnloop.curriculum.depth_rungs import DEFAULT_TRAJECTORY, UNCERTAIN_EVIDENCE_COUNT, UNCERTAIN_OPTIMISM_STEPS
from learnloop.learner.mastery import MasteryObservation, display_mastery, initial_mastery_state, update_mastery
from learnloop.scheduling.randomization_layer import draw_from, reading_dose_propensities

ITEMS_PER_POINT = 8
SUBJECT = "s"
BAND = (0.70, 0.80)
TRIVIAL = 0.95
BETA = P.BETA_NAMES
WAYPOINT_SLUGS = ("recall", "interpret", "execute", "select_method")


def rng_for(text: str) -> np.random.Generator:
    """A generator from a seed string (the pre-registered ``g-ad2-18:<scenario>:<i>`` form)."""

    return np.random.default_rng(int.from_bytes(hashlib.sha256(text.encode("utf-8")).digest()[:8], "big"))


# -- feature points --------------------------------------------------------------------------

def coding(point: Mapping[str, Any] | None) -> np.ndarray:
    """``φ(x)`` over :data:`BETA` (cumulative dummy coding relative to ``x_ref``)."""

    values = P.feature_coding(point)
    return np.array([values.get(name, 0.0) for name in BETA], dtype=np.float64)


def waypoint_points() -> list[dict[str, Any]]:
    """The default trajectory's four waypoint tuples (the incumbent ladder's points)."""

    return [{**dict(w.features), "tools": ["closed_book"]} for w in DEFAULT_TRAJECTORY]


def pool_points(capability: str, *, waypoints: bool = False) -> list[dict[str, Any]]:
    """``X_c`` of the capability's default ladder (§6.1), with the incumbent's waypoints when asked
    (amendment A4: the incumbent comparator serves its waypoints' items)."""

    points = {S.point_key(p): p for p in S.commission_candidates(capability)}
    if waypoints:
        for point in waypoint_points():
            points.setdefault(S.point_key(point), point)
    return [points[key] for key in sorted(points)]


def true_success(eta_e: np.ndarray) -> np.ndarray:
    """The family-expected success: ``ε`` integrated, lapse (guess 0)."""

    return M.residual_success(np.asarray(eta_e, dtype=np.float64), 0.0)


def sample_category(eta: np.ndarray, u: np.ndarray) -> np.ndarray:
    """§5.4's graded response at the realized ``η`` (residual included), from uniforms ``u``."""

    p2 = (1.0 - P.LAPSE) * M.sigmoid(eta)
    p1 = (1.0 - P.LAPSE) * M.sigmoid(eta + P.KAPPA)
    return np.where(u < p2, 2, np.where(u < p1, 1, 0))


def cell_spec(lo: str, facet: str, capability: str, *, loadings: Mapping[str, float] | None = None,
              subject: str = SUBJECT) -> ItemSpec:
    """A generated pool item at the reference tuple of a cell (``z_origin = 1``)."""

    return ItemSpec(f"{lo}:{capability}", lo, subject, capability, {facet: 1.0}, features=None,
                    signals={"z_origin": 1.0}, loadings=dict(loadings or {}))


# -- the truth -------------------------------------------------------------------------------------

@dataclass
class Truth:
    """``n`` learners' true parameters (known to the simulation, never to AD)."""

    n: int
    subject: np.ndarray
    beta: np.ndarray
    alpha_origin: np.ndarray
    gamma: np.ndarray
    facet: dict[str, np.ndarray] = field(default_factory=dict)
    cell: dict[tuple[str, str], np.ndarray] = field(default_factory=dict)
    psi: dict[str, np.ndarray] = field(default_factory=dict)
    #: True loadings: item cell (lo, capability) -> {facet: w̃} (own facet included).
    weights: dict[tuple[str, str], dict[str, float]] = field(default_factory=dict)
    #: Learning transfers: facet -> [(other facet, share of the increment)].
    transfer: dict[str, list[tuple[str, float]]] = field(default_factory=dict)

    def ability(self, facet: str, capability: str) -> np.ndarray:
        return (self.subject + self.facet[facet] + self.psi.get(capability, np.zeros(self.n))
                + self.cell[(facet, capability)])

    def item_ability(self, lo: str, facet: str, capability: str) -> np.ndarray:
        weights = self.weights.get((lo, capability)) or {facet: 1.0}
        return sum(w * self.ability(f, capability) for f, w in weights.items())

    def demand(self, codings: np.ndarray) -> np.ndarray:
        """``β·φ(x) + α_origin`` per learner (``codings`` ``(n, len(BETA))``)."""

        return np.einsum("nj,nj->n", self.beta, codings) + self.alpha_origin

    def learn(self, lo: str, facet: str, capability: str, *, rows: np.ndarray | None = None) -> None:
        weights = self.weights.get((lo, capability)) or {facet: 1.0}
        mask = np.ones(self.n) if rows is None else rows.astype(np.float64)
        for f, w in weights.items():
            increment = self.gamma * w * mask
            self.cell[(f, capability)] = self.cell[(f, capability)] + increment
            for other, share in self.transfer.get(f, ()):
                key = (other, capability)
                if key in self.cell:
                    self.cell[key] = self.cell[key] + share * increment


def draw_truth(rng: np.random.Generator, n: int, *, facets: Sequence[str], capabilities: Sequence[str],
               split: float = P.LO_VIEW_SPLIT, gamma_sd: float = 0.1) -> Truth:
    """Independent truths from ``ad_priors_v1`` at the split (the learner's own ``γ`` floored at 0)."""

    offset = P.offset_variance(split)
    beta = np.stack([rng.normal(mean, math.sqrt(var), n) for _name, mean, var in P.BETA_PRIORS], axis=1)
    truth = Truth(n=n, subject=rng.normal(0.0, math.sqrt(split), n), beta=beta,
                  alpha_origin=rng.normal(P.ALPHA_PRIORS[2][1], math.sqrt(P.ALPHA_PRIORS[2][2]), n),
                  gamma=np.maximum(rng.normal(P.GAMMA_PRIOR[1], gamma_sd, n), 0.0))
    for capability in capabilities:
        prior = P.PSI_PRIORS.get(capability)
        truth.psi[capability] = np.zeros(n) if prior is None else rng.normal(prior[0], math.sqrt(prior[1]), n)
    for facet in facets:
        truth.facet[facet] = rng.normal(0.0, math.sqrt(offset), n)
        for capability in capabilities:
            truth.cell[(facet, capability)] = rng.normal(0.0, math.sqrt(offset), n)
    return truth


# -- an arm: one of AD's views over n learners --------------------------------------------------

class Arm:
    """``n`` learners' AD filters (``n`` x grid points rows) of one view, with its draws."""

    def __init__(self, name: str, n: int, points: Sequence[P.HyperPoint], *, subject_view: bool = True,
                 structure: Any = None, reading: bool = False, verdicts: bool = False, updates: bool = True,
                 constants: S.SelectionConstants = S.SelectionConstants()) -> None:
        self.name = name
        self.n = n
        self.points = tuple(points)
        self.P = len(self.points)
        bank = M.Bank(self.points, groups=n, structure=structure or M.Structure(), reading=reading or verdicts,
                      verdict=verdicts, capacity=96)
        self.view = View(bank, subject_view=subject_view, reading=reading, verdicts=verdicts)
        self.updates = updates
        self.constants = constants

    @property
    def bank(self) -> M.Bank:
        return self.view.bank

    def rows(self, values: np.ndarray) -> np.ndarray:
        return np.repeat(np.asarray(values), self.P, axis=0)

    def weights(self) -> np.ndarray:
        return self.bank.weights()

    def mix(self, values: np.ndarray, weights: np.ndarray | None = None) -> np.ndarray:
        """Mixture over each learner's grid points: ``(n*P, ...) -> (n, ...)``."""

        w = self.weights() if weights is None else weights
        shaped = np.asarray(values).reshape((self.n, self.P) + np.shape(values)[1:])
        return np.einsum("np,np...->n...", w, shaped)

    def ensure(self, spec: ItemSpec, at: float = 0.0) -> None:
        self.view.ensure(spec, at)

    def score(self, spec: ItemSpec, codings: np.ndarray, *, information: bool = False,
              weights: np.ndarray | None = None) -> tuple[np.ndarray, np.ndarray, np.ndarray | None]:
        """``(P_band, p̄, I_c)`` of each learner at each point, ``(n, K)`` (mixtures, §5.7)."""

        self.ensure(spec)
        m, v = self.view.point_moments(spec, codings, BETA)
        band = M.band_probability(m, v, 0.0, self.constants.band)
        p_bar = M.expected_success(m, v, 0.0)
        info = None
        if information:
            cov, var_c = self.view.point_cell_covariance(spec, codings, BETA)
            K = codings.shape[0]
            flat = M.cell_information(m.ravel(), v.ravel(), cov.ravel(), np.repeat(var_c, K), 0.0)
            info = self.mix(flat.reshape(m.shape), weights)
        return self.mix(band, weights), self.mix(p_bar, weights), info

    def predict(self, spec: ItemSpec, codings_rows: np.ndarray, weights: np.ndarray | None = None) -> np.ndarray:
        """``p̄`` of each learner's own served point (``codings_rows`` ``(n, len(BETA))``)."""

        self.ensure(spec)
        u, _m, _v = self.view.projection(spec, 0.0)
        idx = [self.bank.index[name] for name in BETA]
        u[:, idx] -= self.rows(codings_rows)
        m, v = self.bank.moments(u)
        return self.mix(M.expected_success(m, v, 0.0), weights)

    def draw(self, spec: ItemSpec, codings: np.ndarray, available: np.ndarray, keys: Sequence[str]
             ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Each learner's draw (``ad_select_v1``) over the points it still has items at:
        ``(chosen point index, band mode, propensity)``."""

        band, p_bar, _info = self.score(spec, codings)
        calibrate = np.array([np.max(np.where(available[i], band[i], -1.0)) < self.constants.calibrate_below
                              for i in range(self.n)])
        info = None
        if calibrate.any():
            # The calibrate rule reads I_c only on the overlap set (§6.2): compute it there.
            low, high = self.constants.overlap
            columns = np.flatnonzero(((p_bar >= low) & (p_bar <= high) & available)[calibrate].any(axis=0))
            info = np.zeros_like(band)
            if len(columns):
                info[:, columns] = self.score(spec, codings[columns], information=True)[2]
        chosen = np.zeros(self.n, dtype=int)
        propensity = np.zeros(self.n)
        for i in range(self.n):
            scored = [S.Scored(str(k), float(band[i, k]), float(p_bar[i, k]),
                               float(info[i, k]) if info is not None else 0.0)
                      for k in range(codings.shape[0]) if available[i, k]]
            result = S.draw(scored, key=keys[i], constants=self.constants)
            chosen[i] = int(result.chosen)
            propensity[i] = result.propensity
        return chosen, ~calibrate, propensity

    def observe(self, spec: ItemSpec, coding_rows: np.ndarray, category: np.ndarray, at: float,
                active: np.ndarray | None = None) -> None:
        if not self.updates:
            return
        rows = None if active is None else self.rows(active)
        self.view.observe_points(spec, self.rows(coding_rows), BETA, self.rows(category), at, rows=rows)


# -- the incumbent waypoint ladder (depth_rungs.select_rung on the production mastery EKF) ---------

class Incumbent:
    """``select_rung``'s band ladder and optimism step on the mastery EKF, per LO; uniform among the
    waypoint's items. Difficulty-blind (no item difficulty label: ``b = difficulty_default``)."""

    name = "incumbent"

    def __init__(self, n: int) -> None:
        self.n = n
        self.config = MasteryConfig()
        self.states: dict[str, list[Any]] = {}

    def _state(self, lo: str) -> list[Any]:
        if lo not in self.states:
            self.states[lo] = [initial_mastery_state(lo, "sim", "2026-10-01T00:00:00Z",
                                                     logit_variance=float(self.config.cold_start_prior_logit_variance))
                               for _ in range(self.n)]
        return self.states[lo]

    def waypoint(self, lo: str) -> np.ndarray:
        out = np.zeros(self.n, dtype=int)
        developing = float(self.config.display_developing_threshold)
        strong = float(self.config.display_strong_threshold)
        for i, state in enumerate(self._state(lo)):
            ability = display_mastery(state).mastery_mean
            slug = 0 if ability < developing else 1 if ability < strong else 2 if ability < 0.75 else 3
            if state.evidence_count < UNCERTAIN_EVIDENCE_COUNT:
                slug = min(slug + UNCERTAIN_OPTIMISM_STEPS, 3)
            out[i] = slug
        return out

    def observe(self, lo: str, category: np.ndarray, at_index: int) -> None:
        from datetime import UTC, datetime, timedelta

        states = self._state(lo)
        when = datetime(2026, 10, 1, tzinfo=UTC) + timedelta(minutes=3 * at_index)
        for i in range(self.n):
            score = {2: 4, 1: 2, 0: 0}[int(category[i])]
            observation = MasteryObservation(rubric_score=score, max_points=4, evidence_coverage=1.0,
                                             hint_dampening=1.0, grader_confidence=1.0,
                                             attempt_type="independent_attempt", observed_at=when,
                                             attempt_evidence_mass=1.0)
            states[i] = update_mastery(states[i], observation, self.config, "sim", item_a=1.0,
                                       item_b=float(self.config.irt.difficulty_default))


# -- item pools -------------------------------------------------------------------------------

@dataclass
class Pool:
    """Each learner's items at each point of one cell: 8 a point, used once."""

    points: list[dict[str, Any]]
    eps: np.ndarray  # (n, K, ITEMS_PER_POINT)
    used: np.ndarray  # (n, K) items used

    @classmethod
    def build(cls, rng: np.random.Generator, n: int, points: Sequence[Mapping[str, Any]]) -> "Pool":
        points = [dict(p) for p in points]
        return cls(points, rng.normal(0.0, P.TAU0, (n, len(points), ITEMS_PER_POINT)),
                   np.zeros((n, len(points)), dtype=int))

    def copy(self) -> "Pool":
        return Pool(self.points, self.eps, self.used.copy())

    @property
    def codings(self) -> np.ndarray:
        return np.stack([coding(p) for p in self.points])

    def available(self) -> np.ndarray:
        return self.used < ITEMS_PER_POINT

    def take(self, chosen: np.ndarray) -> np.ndarray:
        """Serve each learner the next unused item at its chosen point; its residual."""

        rows = np.arange(len(chosen))
        index = np.minimum(self.used[rows, chosen], ITEMS_PER_POINT - 1)
        eps = self.eps[rows, chosen, index]
        self.used[rows, chosen] += 1
        return eps


@dataclass
class StepLog:
    """One answer per learner: what was served and how it went."""

    lo: str
    cell: tuple[str, str]
    band_mode: np.ndarray
    hit: np.ndarray
    true_success: np.ndarray
    category: np.ndarray
    p_bar: np.ndarray | None = None
    #: Whether any of the cell's pool points was in the band for the learner (an oracle's bound).
    reachable: np.ndarray | None = None


def serve_step(arm: Arm | Incumbent, truth: Truth, pool: Pool, *, lo: str, facet: str, capability: str,
               keys: Sequence[str], uniforms: np.ndarray, at: float, loadings: Mapping[str, float] | None = None,
               predict_with: Sequence[Arm] = ()) -> StepLog:
    """One answer per learner: the arm's draw (or the incumbent's waypoint), the outcome under the
    truth, the arm's update and the truth's learning."""

    spec = cell_spec(lo, facet, capability, loadings=loadings)
    codings = pool.codings
    if isinstance(arm, Incumbent):
        waypoint = arm.waypoint(lo)
        keys_wp = [S.point_key(p) for p in waypoint_points()]
        index = {S.point_key(p): k for k, p in enumerate(pool.points)}
        chosen = np.array([index[keys_wp[w]] for w in waypoint])
        band_mode = np.zeros(arm.n, dtype=bool)
    else:
        chosen, band_mode, _pi = arm.draw(spec, codings, pool.available(), keys)
    rows = codings[chosen]
    ability = truth.item_ability(lo, facet, capability)
    eta_e = ability - truth.demand(rows)
    success = true_success(eta_e)
    every = true_success(ability[:, None] - (truth.beta @ codings.T) - truth.alpha_origin[:, None])
    reachable = ((every >= BAND[0]) & (every <= BAND[1])).any(axis=1)
    eps = pool.take(chosen)
    category = sample_category(eta_e - P.A * eps, uniforms)
    p_bar = None
    if predict_with:
        p_bar = np.stack([other.predict(spec, rows) for other in predict_with])
    if isinstance(arm, Incumbent):
        arm.observe(lo, category, int(at * 1440 / 3))
    else:
        arm.observe(spec, rows, category, at)
    truth.learn(lo, facet, capability)
    return StepLog(lo, (facet, capability), band_mode, (success >= BAND[0]) & (success <= BAND[1]), success,
                   category, p_bar, reachable)


def copy_truth(truth: Truth) -> Truth:
    return Truth(truth.n, truth.subject.copy(), truth.beta.copy(), truth.alpha_origin.copy(), truth.gamma.copy(),
                 {k: v.copy() for k, v in truth.facet.items()}, {k: v.copy() for k, v in truth.cell.items()},
                 {k: v.copy() for k, v in truth.psi.items()}, {k: dict(v) for k, v in truth.weights.items()},
                 {k: list(v) for k, v in truth.transfer.items()})


# -- G-AD2-18: time to usable (§5.9; pre-registration §1.5) ---------------------------------------------

@dataclass
class UsableResult:
    scenario: str
    arms: dict[str, list[StepLog]]

    def band_hit_rate(self, arm: str, start: int = 16, end: int = 30, *, mask: Callable[[StepLog], bool] | None = None
                      ) -> float:
        logs = [log for t, log in enumerate(self.arms[arm], start=1) if start <= t <= end and (mask is None or mask(log))]
        return float(np.mean([log.hit.mean() for log in logs])) if logs else float("nan")

    def reachable_rate(self, arm: str, start: int = 16, end: int = 30) -> float:
        """An oracle's bound on the band-hit rate: some pool point was in the band."""

        logs = [log for t, log in enumerate(self.arms[arm], start=1) if start <= t <= end]
        return float(np.mean([log.reachable.mean() for log in logs]))

    def engaged_by(self, arm: str, t: int = 15) -> float:
        logs = self.arms[arm][:t]
        engaged = np.zeros(len(logs[0].band_mode), dtype=bool)
        for log in logs:
            engaged |= log.band_mode
        return float(engaged.mean())

    def trivial_success_rate(self, arm: str) -> float:
        successes = trivial = 0
        for log in self.arms[arm]:
            won = log.category == 2
            successes += int(won.sum())
            trivial += int((won & (log.true_success > TRIVIAL)).sum())
        return trivial / successes if successes else 0.0


def time_to_usable(scenario: str, *, n: int = 200, answers: int = 30, seed: str = "g-ad2-18") -> UsableResult:
    """G-AD2-18's three scenarios (``one_cell``, ``wrong_prior``, ``plan_flow``)."""

    rng = rng_for(f"{seed}:{scenario}")
    uniform_points = P.uniform_points(P.hyper_grid())
    if scenario in ("one_cell", "wrong_prior"):
        truth = draw_truth(rng, n, facets=["f1"], capabilities=["retrieval"])
        if scenario == "wrong_prior":
            truth.subject = np.where(np.arange(n) < n // 2, 1.5, -1.5).astype(np.float64)
        pool = Pool.build(rng, n, pool_points("retrieval"))
        uniforms = rng.random((answers, n))
        arm = Arm("ad_threshold@subject", n, uniform_points)
        logs = []
        for t in range(answers):
            logs.append(serve_step(arm, truth, pool, lo="L1", facet="f1", capability="retrieval",
                                   keys=[f"{seed}:{scenario}:{i}:{t}" for i in range(n)], uniforms=uniforms[t],
                                   at=t * 3.0 / 1440))
        return UsableResult(scenario, {arm.name: logs})
    if scenario != "plan_flow":
        raise ValueError(scenario)
    los = ("L1", "L2", "L3")
    capabilities = ("retrieval", "schema_interpretation")
    truth = draw_truth(rng, n, facets=[f"f{i}" for i in (1, 2, 3)], capabilities=capabilities)
    pools = {(lo, cap): Pool.build(rng, n, pool_points(cap, waypoints=True)) for lo in los for cap in capabilities}
    uniforms = rng.random((answers, n))
    blocks = [("L1", "retrieval"), ("L2", "schema_interpretation"), ("L3", "retrieval"),
              ("L1", "schema_interpretation"), ("L2", "retrieval"), ("L3", "schema_interpretation")]
    arms: dict[str, Any] = {
        "ad_threshold@subject": Arm("ad_threshold@subject", n, uniform_points),
        "ad_no_update": Arm("ad_no_update", n, uniform_points, updates=False),
        "incumbent": Incumbent(n),
    }
    lo_views = {lo: Arm(f"ad_threshold@lo:{lo}", n, (P.LO_VIEW_POINT,), subject_view=False) for lo in los}
    logs: dict[str, list[StepLog]] = {name: [] for name in [*arms, "ad_threshold@lo"]}
    truths = {name: copy_truth(truth) for name in logs}
    own_pools = {name: {key: pool.copy() for key, pool in pools.items()} for name in logs}
    for t in range(answers):
        lo, capability = blocks[(t // 5) % len(blocks)]
        facet = f"f{lo[1]}"
        keys = [f"{seed}:{scenario}:{i}:{t}" for i in range(n)]
        for name, arm in arms.items():
            logs[name].append(serve_step(arm, truths[name], own_pools[name][(lo, capability)], lo=lo, facet=facet,
                                         capability=capability, keys=keys, uniforms=uniforms[t], at=t * 3.0 / 1440))
        logs["ad_threshold@lo"].append(serve_step(
            lo_views[lo], truths["ad_threshold@lo"], own_pools["ad_threshold@lo"][(lo, capability)], lo=lo,
            facet=facet, capability=capability, keys=keys, uniforms=uniforms[t], at=t * 3.0 / 1440))
    return UsableResult(scenario, logs)


def own_answers_before_band(logs: Sequence[StepLog], cell: tuple[str, str]) -> np.ndarray:
    """Per learner, the own answers a cell needed before its first band-mode draw (inf: never)."""

    count = None
    first = None
    for log in logs:
        if log.cell != cell:
            continue
        if count is None:
            count = np.zeros(len(log.band_mode))
            first = np.full(len(log.band_mode), np.inf)
        newly = log.band_mode & np.isinf(first)
        first = np.where(newly, count, first)
        count = count + 1
    return first if first is not None else np.array([])


# -- G-AD2-7 / G-AD2-8: confound and recovery (§5.8) -------------------------------------------------

def feature_time_correlation(points: Sequence[Mapping[str, Any]]) -> dict[str, dict[str, Any]]:
    """§5.8's first diagnostic on a served sequence (the report's own function)."""

    from learnloop.adaptive_difficulty.report import feature_time_correlation as diagnostic

    return diagnostic(points)


@dataclass
class RecoveryResult:
    beta_true: np.ndarray
    beta_mean: np.ndarray
    beta_sd: np.ndarray
    prior_dependent: list[set[str]]
    served: list[list[dict[str, Any]]]


def recovery(*, policy: str, n: int = 200, answers: int = 60, seed: str = "g-ad2-8",
             no_feature_effect: bool = False) -> RecoveryResult:
    """One cell, the LO view, 60 answers; ``policy`` ``ad_select_v1`` (live draw) or ``monotone``
    (the ladder's points in ascending prior demand, one step every answers/len points)."""

    from learnloop.adaptive_difficulty.report import aliased_coordinates

    rng = rng_for(f"{seed}:{policy}")
    truth = draw_truth(rng, n, facets=["f1"], capabilities=["retrieval"])
    if no_feature_effect:
        truth.beta[:] = 0.0
    pool = Pool.build(rng, n, pool_points("retrieval"))
    uniforms = rng.random((answers, n))
    arm = Arm("ad_threshold@lo", n, (P.LO_VIEW_POINT,), subject_view=False)
    served: list[list[dict[str, Any]]] = [[] for _ in range(n)]
    keys = [S.point_key(p) for p in pool.points]
    rungs = [keys.index(S.point_key(rung)) for rung in S.ladder("retrieval")]
    spec = cell_spec("L1", "f1", "retrieval")
    for t in range(answers):
        if policy == "monotone":
            # The default ladder's rungs in order, equal time on each: every dimension the walk
            # raises rises with time (§5.8's confound by design).
            position = min(int(t * len(rungs) / answers), len(rungs) - 1)
            chosen = np.full(n, rungs[position])
        else:
            chosen, _mode, _pi = arm.draw(spec, pool.codings, pool.available(),
                                          [f"{seed}:{policy}:{i}:{t}" for i in range(n)])
        rows = pool.codings[chosen]
        for i in range(n):
            served[i].append(pool.points[chosen[i]])
        eta_e = truth.item_ability("L1", "f1", "retrieval") - truth.demand(rows)
        # A fresh item each answer (a monotone schedule outruns a pool of 8 per point).
        eps = rng.normal(0.0, P.TAU0, n) if policy == "monotone" else pool.take(chosen)
        category = sample_category(eta_e - eps, uniforms[t])
        arm.observe(spec, rows, category, t * 3.0 / 1440)
        truth.learn("L1", "f1", "retrieval")
    bank = arm.bank
    idx = [bank.index[name] for name in BETA]
    mean = bank.mu[:, idx]
    sd = np.sqrt(np.maximum(np.einsum("bii->bi", bank.S[:, idx][:, :, idx]), 0.0))
    names = list(BETA) + [name for name, _m, _v in P.ALPHA_PRIORS]
    prior = {name: var for name, _m, var in list(P.BETA_PRIORS) + list(P.ALPHA_PRIORS)}
    full = [bank.index[name] for name in names]
    dependent = [aliased_coordinates(bank.S[b][np.ix_(full, full)], [prior[name] for name in names], names)
                 for b in range(bank.B)]
    return RecoveryResult(truth.beta, mean, sd, dependent, served)


# -- G-AD2-14: help and reveal censored, not dropped (§5.3) ---------------------------------------------

@dataclass
class CensoringResult:
    predicted: np.ndarray  # (n, 10)
    sd: np.ndarray
    true: np.ndarray
    dropped: np.ndarray


def censoring(*, n: int = 200, answers: int = 60, seed: str = "g-ad2-14") -> CensoringResult:
    """Help with probability ``σ(-m - 1)``, a reveal with ``σ(-m - 2)`` (``m`` the item's true margin,
    residual included), at uniformly drawn ladder points (amendment A8); AD's censored update against a
    filter that drops every assisted attempt."""

    rng = rng_for(seed)
    truth = draw_truth(rng, n, facets=["f1"], capabilities=["retrieval"])
    pool = Pool.build(rng, n, pool_points("retrieval"))
    K = len(pool.points)
    ad = Arm("censored", n, (P.LO_VIEW_POINT,), subject_view=False)
    drop = Arm("dropped", n, (P.LO_VIEW_POINT,), subject_view=False)
    spec = cell_spec("L1", "f1", "retrieval")
    for t in range(answers):
        chosen = rng.integers(0, K, n)
        available = pool.available()
        for i in range(n):
            if not available[i, chosen[i]]:
                chosen[i] = int(np.flatnonzero(available[i])[0])
        rows = pool.codings[chosen]
        eta_e = truth.item_ability("L1", "f1", "retrieval") - truth.demand(rows)
        eps = pool.take(chosen)
        margin = eta_e - eps
        u_help, u_reveal, u_answer = rng.random(n), rng.random(n), rng.random(n)
        helped = u_help < M.sigmoid(-margin - 1.0)
        revealed = ~helped & (u_reveal < M.sigmoid(-margin - 2.0))
        category = sample_category(margin, u_answer)
        # Help with unknown timing: a success is censored {0, 1}, anything less a fail (§5.3);
        # an answer revealed during the presentation is censored whatever its correctness.
        observed = np.where(revealed, M.CENSORED, np.where(helped, np.where(category == 2, M.CENSORED, 0), category))
        ad.observe(spec, rows, observed, t / 1440)
        drop.observe(spec, rows, category, t / 1440, active=~(helped | revealed))
        truth.learn("L1", "f1", "retrieval")
    evaluation = [pool.points[k] for k in np.linspace(0, K - 1, 10).round().astype(int)]
    codings = np.stack([coding(p) for p in evaluation])
    predicted, sd = _predictive_with_sd(ad, spec, codings)
    dropped, _sd = _predictive_with_sd(drop, spec, codings)
    ability = truth.item_ability("L1", "f1", "retrieval")
    true = np.zeros((n, len(evaluation)))
    for k in range(len(evaluation)):
        eta_e = ability - truth.demand(np.tile(codings[k], (n, 1)))
        margin = eta_e[:, None] - P.TAU0 * M.X32[None, :]
        unassisted = (1.0 - M.sigmoid(-margin - 1.0)) * (1.0 - M.sigmoid(-margin - 2.0)) * (1.0 - P.LAPSE) \
            * M.sigmoid(margin)
        true[:, k] = (M.W32[None, :] * unassisted).sum(1)
    return CensoringResult(predicted, sd, true, dropped)


def _predictive_with_sd(arm: Arm, spec: ItemSpec, codings: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """``p̄`` at each point and the posterior sd of ``p_θ`` (``ε`` integrated, state uncertain)."""

    m, v = arm.view.point_moments(spec, codings, BETA)
    p_bar = M.expected_success(m, v, 0.0)
    nodes = m[..., None] + np.sqrt(v)[..., None] * M.X32
    values = M.residual_success(nodes, 0.0)
    mean = (M.W32 * values).sum(-1)
    var = np.maximum((M.W32 * values ** 2).sum(-1) - mean ** 2, 0.0)
    return arm.mix(p_bar), np.sqrt(arm.mix(var))


# -- vaults with known structure (G-AD3-6, G-AD3-7; pre-registration §1.6, §1.8) -------------------------

@dataclass(frozen=True)
class Cluster:
    """A vault of clusters of three LOs (A, B, C), one facet each, capability retrieval."""

    clusters: int

    @property
    def los(self) -> list[str]:
        return [f"{k}{c}" for c in range(1, self.clusters + 1) for k in "ABC"]

    def facet(self, lo: str) -> str:
        return f"f_{lo}"

    def cluster_of(self, lo: str) -> int:
        return int(lo[1:])

    def mates(self, lo: str) -> list[str]:
        c = self.cluster_of(lo)
        return [f"{k}{c}" for k in "ABC" if f"{k}{c}" != lo]

    def maps(self) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
        return ({self.facet(lo): [lo] for lo in self.los}, {lo: [self.facet(lo)] for lo in self.los})

    def true_loadings(self, lo: str) -> dict[str, float]:
        """B's items load 0.5 onto A's facet, C's onto B's (the true implication structure)."""

        c = self.cluster_of(lo)
        if lo.startswith("B"):
            return {self.facet(f"A{c}"): 0.5}
        if lo.startswith("C"):
            return {self.facet(f"B{c}"): 0.5}
        return {}


def proposal(vault: Cluster, kind: str, rng: np.random.Generator | None = None
             ) -> tuple[dict[str, dict[str, float]], dict[str, dict[str, float]]]:
    """The simulated proposal (``correct``, ``noisy``, ``wrong``): couplings LO -> {LO: C} and
    loadings by LO (frozen per item) -> {facet: Q}."""

    los = vault.los
    correct_pairs = {(lo, mate) for lo in los for mate in vault.mates(lo)}
    correct_loadings = {lo: vault.true_loadings(lo) for lo in los if vault.true_loadings(lo)}
    if kind == "correct":
        pairs, loadings = correct_pairs, correct_loadings
    else:
        across = sorted({tuple(sorted((a, b))) for a in los for b in los
                         if vault.cluster_of(a) != vault.cluster_of(b)})
        rng = rng or rng_for(f"proposal:{kind}")
        if kind == "wrong":
            pairs = _across_pairs(vault, rng)
            loadings = {lo: {vault.facet(other): 0.5} for lo, other in _across_partner(vault, rng).items()
                        if lo[0] in "BC"}
        elif kind == "noisy":
            pairs = set()
            unique = sorted({tuple(sorted(p)) for p in correct_pairs})
            keep = rng.random(len(unique)) < 0.5
            for (a, b), kept in zip(unique, keep):
                if kept:
                    pairs |= {(a, b), (b, a)}
                else:
                    x, y = across[int(rng.integers(0, len(across)))]
                    pairs |= {(x, y), (y, x)}
            partners = _across_partner(vault, rng)
            loadings = {}
            for lo, values in correct_loadings.items():
                loadings[lo] = values if rng.random() < 0.5 else {vault.facet(partners[lo]): 0.5}
        else:
            raise ValueError(kind)
    couplings: dict[str, dict[str, float]] = {}
    for a, b in sorted(pairs):
        couplings.setdefault(a, {})
        if len(couplings[a]) < P.MAX_COUPLED:
            couplings[a][b] = 1.0
    return couplings, loadings


def _across_partner(vault: Cluster, rng: np.random.Generator) -> dict[str, str]:
    los = vault.los
    out = {}
    for lo in los:
        others = [o for o in los if vault.cluster_of(o) != vault.cluster_of(lo)]
        out[lo] = others[int(rng.integers(0, len(others)))]
    return out


def _across_pairs(vault: Cluster, rng: np.random.Generator, *, order: Sequence[str] | None = None) -> set[tuple[str, str]]:
    """Every pair across clusters: each LO names two partners of other clusters (near it in ``order``
    when given, so a long vault's live coordinates stay few)."""

    los = list(order or vault.los)
    pairs: set[tuple[str, str]] = set()
    for index, lo in enumerate(los):
        candidates = [o for o in los[index + 1:index + 8] if vault.cluster_of(o) != vault.cluster_of(lo)]
        if order is None:
            candidates = [o for o in los if vault.cluster_of(o) != vault.cluster_of(lo)]
            rng.shuffle(candidates)
        for other in candidates[:2]:
            pairs |= {(lo, other), (other, lo)}
    return pairs


def structure_for(vault: Cluster, couplings: Mapping[str, Mapping[str, float]], loadings_by_lo: Mapping[str, Mapping[str, float]]
                  ) -> VaultStructure:
    facet_los, lo_facets = vault.maps()
    return VaultStructure.fixed(facet_los=facet_los, lo_facets=lo_facets, couplings=couplings,
                                loadings={f"rev:{lo}": dict(v) for lo, v in loadings_by_lo.items()})


def cluster_truth(rng: np.random.Generator, n: int, vault: Cluster, *, correlation: float = 0.8,
                  transfer: float = 0.8) -> Truth:
    """G-AD3-7's truth: subject level N(0, 1.5); facet and cell offsets N(0, 0.75) correlated 0.8
    within a cluster and 0 across; true loadings (implication 0.5); learning transferring to
    cluster mates at 0.8 of the increment."""

    truth = draw_truth(rng, n, facets=[], capabilities=["retrieval"])
    cov = 0.75 * (np.full((3, 3), correlation) + (1.0 - correlation) * np.eye(3))
    chol = np.linalg.cholesky(cov)
    for c in range(1, vault.clusters + 1):
        members = [f"{k}{c}" for k in "ABC"]
        facets = chol @ rng.normal(size=(3, n))
        cells = chol @ rng.normal(size=(3, n))
        for row, lo in enumerate(members):
            truth.facet[vault.facet(lo)] = facets[row]
            truth.cell[(vault.facet(lo), "retrieval")] = cells[row]
    for lo in vault.los:
        loadings = vault.true_loadings(lo)
        q_plus = sum(loadings.values())
        weights = {vault.facet(lo): 1.0 - 0.5 * q_plus}
        for g, q in loadings.items():
            weights[g] = 0.5 * q
        truth.weights[(lo, "retrieval")] = weights
        truth.transfer[vault.facet(lo)] = [(vault.facet(m), transfer) for m in vault.mates(lo)]
    return truth


@dataclass
class RelatedResult:
    flow: str
    proposal: str
    arms: dict[str, list[StepLog]]
    mates: tuple[str, ...]
    unrelated: str

    def first_attempt_loss(self, arm: str, lo: str) -> np.ndarray:
        log = next(log for log in self.arms[arm] if log.lo == lo)
        p = np.clip(log.p_bar[0], *MON.CLIP)
        y = (log.category == 2).astype(np.float64)
        return -(y * np.log(p) + (1 - y) * np.log(1 - p))

    def own_answers_before_band(self, arm: str, lo: str) -> np.ndarray:
        return own_answers_before_band([log for log in self.arms[arm] if log.lo == lo],
                                       (Cluster(4).facet(lo), "retrieval"))

    def band_hit_rate(self, arm: str, lo: str) -> float:
        logs = [log for log in self.arms[arm] if log.lo == lo][:15]
        return float(np.mean([log.hit.mean() for log in logs]))


def related_topics(*, flow: str, proposal_kind: str, n: int = 200, seed: str = "g-ad3-7",
                   own: int = 15, chunk: int = 50) -> RelatedResult:
    """G-AD3-7: 15 answers on cluster 1's A (``practice``) or 5 sections read on it (``reading``),
    then its never-seen mates B and C, then cluster 2's A, each up to 15 own answers; under
    ``@subject`` (the 36-point mixture with the proposal) and ``@subject_uniform``, common random numbers."""

    vault = Cluster(4)
    logs: dict[str, list[StepLog]] = {"ad_threshold@subject": [], "ad_threshold@subject_uniform": []}
    for start in range(0, n, chunk):
        size = min(chunk, n - start)
        part = _related_chunk(vault, flow, proposal_kind, size, seed, start, own)
        for name, entries in part.items():
            if not logs[name]:
                logs[name] = entries
            else:
                logs[name] = [_join(a, b) for a, b in zip(logs[name], entries)]
    return RelatedResult(flow, proposal_kind, logs, ("B1", "C1"), "A2")


def _join(a: StepLog, b: StepLog) -> StepLog:
    return StepLog(a.lo, a.cell, np.concatenate([a.band_mode, b.band_mode]), np.concatenate([a.hit, b.hit]),
                   np.concatenate([a.true_success, b.true_success]), np.concatenate([a.category, b.category]),
                   None if a.p_bar is None else np.concatenate([a.p_bar, b.p_bar], axis=1),
                   None if a.reachable is None else np.concatenate([a.reachable, b.reachable]))


def _related_chunk(vault: Cluster, flow: str, proposal_kind: str, n: int, seed: str, start: int, own: int
                   ) -> dict[str, list[StepLog]]:
    rng = rng_for(f"{seed}:{flow}:{proposal_kind}:{start}")
    truth = cluster_truth(rng, n, vault)
    couplings, loadings = proposal(vault, proposal_kind, rng_for(f"{seed}:proposal:{proposal_kind}:{start}"))
    structure = structure_for(vault, couplings, loadings)
    points = pool_points("retrieval")
    pools = {lo: Pool.build(rng, n, points) for lo in vault.los}
    schedule: list[tuple[str, str]] = []
    if flow == "practice":
        schedule += [("answer", "A1")] * own
    elif flow == "reading":
        schedule += [("read", "A1")] * 5
    else:
        raise ValueError(flow)
    schedule += [("answer", "B1")] * own + [("answer", "C1")] * own + [("answer", "A2")] * own
    uniforms = rng.random((len(schedule), n))
    arms = {
        "ad_threshold@subject": Arm("ad_threshold@subject", n, P.hyper_grid(), structure=structure, reading=True),
        "ad_threshold@subject_uniform": Arm("ad_threshold@subject_uniform", n, P.uniform_points(P.hyper_grid()),
                                            reading=True),
    }
    out: dict[str, list[StepLog]] = {name: [] for name in arms}
    for name, arm in arms.items():
        own_truth = copy_truth(truth)
        own_pools = {lo: pool.copy() for lo, pool in pools.items()}
        for t, (action, lo) in enumerate(schedule):
            facet = vault.facet(lo)
            at = t * 3.0 / 1440
            if action == "read":
                arm.view.reading(SUBJECT, "reading", {facet: np.ones(arm.bank.B)}, at)
                own_truth.facet[facet] = own_truth.facet[facet] + 0.3
                for other, share in own_truth.transfer.get(facet, ()):
                    own_truth.facet[other] = own_truth.facet[other] + share * 0.3
                continue
            frozen = {g: q for g, q in structure.loadings(f"rev:{lo}").items()} if name.endswith("@subject") else {}
            out[name].append(serve_step(arm, own_truth, own_pools[lo], lo=lo, facet=facet, capability="retrieval",
                                        keys=[f"{seed}:{flow}:{proposal_kind}:{start + i}:{t}" for i in range(n)],
                                        uniforms=uniforms[t], at=at, loadings=frozen, predict_with=(arm,)))
    return out


def wrong_proposal_shrinks(*, proposal_kind: str, n: int = 200, seed: str = "g-ad3-7:shrink", chunk: int = 25,
                           first_attempts: int = 200) -> dict[str, np.ndarray]:
    """70 clusters of three (210 LOs): 15 answers on one LO, then one first attempt on each never-seen
    LO in a fixed shuffled order at a fixed mid-ladder point. Per learner: the first attempt at which
    the weight on ``χ_C = 0`` reaches 0.5, and the first at which the coupling flag fires (inf: never)."""

    vault = Cluster(70)
    order_rng = rng_for(f"{seed}:order")
    clusters = list(range(1, 71))
    order_rng.shuffle(clusters)
    order = [f"{k}{c}" for c in clusters for k in "ABC"]
    first, rest = order[0], order[1:]
    if proposal_kind == "correct":
        couplings = {lo: {m: 1.0 for m in vault.mates(lo)} for lo in vault.los}
    else:
        pairs = _across_pairs(vault, order_rng, order=order)
        couplings = {}
        for a, b in sorted(pairs):
            couplings.setdefault(a, {})
            if len(couplings[a]) < P.MAX_COUPLED:
                couplings[a][b] = 1.0
    facet_los, lo_facets = vault.maps()
    structure = VaultStructure.fixed(facet_los=facet_los, lo_facets=lo_facets, couplings=couplings)
    # χ_Q has no effect without loadings: the 12 (split, coupling) points are the grid exactly.
    grid = tuple(p for p in P.hyper_grid() if p.implication == 0.0)
    zero = np.array([p.coupling == 0.0 for p in grid])
    uniform_mask = np.array([p.uniform for p in grid])
    mid = S.ladder("retrieval")[len(S.ladder("retrieval")) // 2]
    mid_coding = coding(mid)
    reach = np.full(n, np.inf)
    fires = np.full(n, np.inf)
    last_needed = _last_needed(order, couplings)
    for begin in range(0, n, chunk):
        size = min(chunk, n - begin)
        rng = rng_for(f"{seed}:{proposal_kind}:{begin}")
        truth = cluster_truth(rng, size, vault)
        truth.weights = {}
        arm = Arm("ad_threshold@subject", size, grid, structure=structure)
        pool = Pool.build(rng, size, pool_points("retrieval"))
        spec = cell_spec(first, vault.facet(first), "retrieval")
        for t in range(15):
            serve_step(arm, truth, pool, lo=first, facet=vault.facet(first), capability="retrieval",
                       keys=[f"{seed}:{begin + i}:{t}" for i in range(size)], uniforms=rng.random(size),
                       at=t * 3.0 / 1440)
        differences: list[list[float]] = [[] for _ in range(size)]
        ranges: list[list[tuple[float, float]]] = [[] for _ in range(size)]
        for index, lo in enumerate(rest[:first_attempts]):
            facet = vault.facet(lo)
            spec = cell_spec(lo, facet, "retrieval")
            arm.ensure(spec)
            rows = np.tile(mid_coding, (size, 1))
            u, _m, _v = arm.view.projection(spec, 0.0)
            idx = [arm.bank.index[name] for name in BETA]
            u[:, idx] -= arm.rows(rows)
            m, v = arm.bank.moments(u)
            p_rows = M.expected_success(m, v, 0.0)
            p_subject = arm.mix(p_rows)
            p_uniform = arm.mix(p_rows, arm.bank.restricted_weights(uniform_mask))
            eta_e = truth.item_ability(lo, facet, "retrieval") - truth.demand(rows)
            category = sample_category(eta_e - rng.normal(0.0, P.TAU0, size), rng.random(size))
            y = (category == 2).astype(np.float64)
            for i in range(size):
                value, bounds = MON.log_loss_difference(p_subject[i], p_uniform[i], y[i])
                differences[i].append(value)
                ranges[i].append(bounds)
            arm.observe(spec, rows, category, (15 + index) * 3.0 / 1440)
            truth.learn(lo, facet, "retrieval")
            weight_zero = (arm.weights() * zero[None, :]).sum(1)
            for i in range(size):
                g = begin + i
                if np.isinf(reach[g]) and weight_zero[i] >= 0.5:
                    reach[g] = index + 1
                if np.isinf(fires[g]) and MON.comparison_flag("coupling_worse_than_uniform", differences[i],
                                                                     ranges[i]).fires:
                    fires[g] = index + 1
            done = [name for lo_done, names in last_needed.items() if lo_done == lo for name in names]
            if done:
                arm.bank.marginalize(done)
    return {"weight_zero_reaches_half": reach, "flag_fires": fires}


def _last_needed(order: Sequence[str], couplings: Mapping[str, Mapping[str, float]]) -> dict[str, list[str]]:
    """After which LO's first attempt each LO's coordinates are read no more (exact marginalization:
    no later observation, and every LO that couples to it exists)."""

    position = {lo: i for i, lo in enumerate(order)}
    partners: dict[str, set[str]] = {lo: set() for lo in order}
    for a, values in couplings.items():
        for b in values:
            partners.setdefault(a, set()).add(b)
            partners.setdefault(b, set()).add(a)
    out: dict[str, list[str]] = {}
    for lo in order[1:]:
        last = max([position[lo]] + [position[p] for p in partners.get(lo, ()) if p in position])
        out.setdefault(order[last], []).extend([M.facet_name(f"f_{lo}"), M.cell_name(f"f_{lo}", "retrieval")])
    return out


def hyperparameters_learned(point: P.HyperPoint, *, seeds: int = 25, answers: int = 300,
                            seed: str = "g-ad3-6") -> np.ndarray:
    """G-AD3-6: per seed, the posterior weight on the generating point and its grid neighbours
    (Chebyshev distance 1) after 300 first-surface answers over the 12 LOs of the cluster vault
    (correct proposal), the truth drawn from the model at that point (amendment A9: every LO's
    coordinates created in LO order up front, at ladder points drawn uniformly)."""

    vault = Cluster(4)
    couplings, loadings = proposal(vault, "correct")
    structure = structure_for(vault, couplings, loadings)
    grid = P.hyper_grid()
    neighbours = np.array([_chebyshev(point, other) <= 1 for other in grid])
    rng = rng_for(f"{seed}:{point.key()}")
    truth_bank = M.Bank((point,), groups=1, structure=structure)
    truth_view = View(truth_bank, subject_view=True)
    specs = {lo: cell_spec(lo, vault.facet(lo), "retrieval", loadings=structure.loadings(f"rev:{lo}"))
             for lo in vault.los}
    for lo in vault.los:
        truth_view.ensure(specs[lo], 0.0)
    names = truth_bank.names
    chol = np.linalg.cholesky(truth_bank.S[0] + 1e-12 * np.eye(truth_bank.d))
    draws = truth_bank.mu[0][None, :] + rng.normal(size=(seeds, truth_bank.d)) @ chol.T
    arm = Arm("ad_threshold@subject", seeds, grid, structure=structure)
    for lo in vault.los:
        arm.ensure(specs[lo])
    if arm.bank.names != names[:len(arm.bank.names)] and set(names) - set(arm.bank.names):
        raise AssertionError("the truth and the filter create different coordinates")
    pool_pts = pool_points("retrieval")
    codings = np.stack([coding(p) for p in pool_pts])
    order = [vault.los[i % 12] for i in rng.permutation(answers)]
    index = {name: i for i, name in enumerate(names)}
    gamma = draws[:, index["gamma"]]
    state = draws.copy()
    for t, lo in enumerate(order):
        spec = specs[lo]
        chosen = rng.integers(0, len(pool_pts), seeds)
        rows = codings[chosen]
        u_truth, _m, _v = truth_view.projection(spec, 0.0)
        u_truth = u_truth[0].copy()
        eta_e = state @ u_truth - np.einsum("nj,nj->n", state[:, [index[b] for b in BETA]], rows)
        category = sample_category(eta_e - rng.normal(0.0, P.TAU0, seeds), rng.random(seeds))
        arm.observe(spec, rows, category, t * 3.0 / 1440)
        # The truth learns as the model does: w̃·γ on each facet's cell, and corr₀ along couplings.
        for facet, weight in truth_view._extended_weights(spec).items():
            target = M.cell_name(facet, "retrieval")
            state[:, index[target]] += float(weight[0]) * gamma
            for other in structure.coupled_facets(facet):
                coupled = M.cell_name(other, "retrieval")
                if coupled != target and coupled in index:
                    state[:, index[coupled]] += float(truth_bank.corr0(target, coupled)[0]) * float(weight[0]) * gamma
    return (arm.weights() * neighbours[None, :]).sum(1)


def _chebyshev(a: P.HyperPoint, b: P.HyperPoint) -> int:
    def step(values: Sequence[float], x: float, y: float) -> int:
        return abs(list(values).index(x) - list(values).index(y))

    return max(step(P.SPLITS, a.split, b.split), step(P.COUPLINGS, a.coupling, b.coupling),
               step(P.IMPLICATIONS, a.implication, b.implication))


# -- synthetic readers (G-AD3-8, G-AD3-11, G-AD3-15; pre-registration §1.7, §1.8) -------------------------

KINDS = P.READING_KINDS
MINUTES = {"reading": 6.0, "reader_tutor_exchange": 3.0, "worked_example": 4.0, "in_passage_question": 2.0}
PRACTICE_MINUTES = 3.0
BASE_CURVES = {"reading": (0.15, 0.10), "reader_tutor_exchange": (0.25, 0.0), "worked_example": (0.0, 0.35),
               "in_passage_question": (0.0, 0.0)}
DOWNTURN = (0.5, -0.3)
OFFER_KIND = {"extra_worked_example": "worked_example", "extra_question": "in_passage_question"}


def true_curve(c: tuple[float, float], n: float) -> float:
    b1, b2 = M.dose_basis(n)
    return c[0] * b1 + c[1] * b2


@dataclass
class ReaderResult:
    """Per reader: the fitted coefficient moments, the offers, visits and the prequential log."""

    curves: dict[str, tuple[float, float]]
    mean: dict[str, np.ndarray]  # kind -> (n, 2)
    cov: dict[str, np.ndarray]  # kind -> (n, 2, 2)
    gamma: np.ndarray
    offers: list[list[Any]]
    visits: list[list[dict[str, Any]]]
    view: View
    records: dict[str, list[list[float]]] = field(default_factory=dict)
    verdict_mean: np.ndarray | None = None
    verdict_sd: np.ndarray | None = None


def readers(*, scenario: str, n: int = 200, los: int = 1250, windows: int = 4, floor: float = 0.10,
            seed: str = "g-ad3-11", reading_only: bool = False, rise: float | None = None,
            verdicts: str | None = None, arms: Sequence[str] = ("on",)) -> ReaderResult:
    """Synthetic readers working through ``los`` LOs, one facet each, ``windows`` windows per LO.

    Each window: reading events (a section read w.p. 0.8; tutor exchanges ~ Binomial(3, 0.3);
    worked examples uniform on 0..4; in-passage questions uniform on 0..3), the dose arm's offer at
    the section boundary (taken w.p. 0.7), then one first-surface answer a day later at the entry
    point (amendment A5). ``scenario``: ``base``, ``downturn`` or ``confounding`` (no true effect,
    each count +1 after a failed window). ``reading_only``: one section read per window and nothing
    else, with a true rise of ``rise`` per section (G-AD3-8). ``verdicts``: ``none`` or ``missed``
    (G-AD3-15: one judged question per window, its verdict carrying no signal, or misses predicting
    cold failure at ``λ_missed = -0.4``). ``arms``: ``on`` (reading on) and ``off`` (reading off)
    scored prequentially on the same answers."""

    rng = rng_for(f"{seed}:{scenario}:{floor}:{verdicts}:{rise}")
    curves = dict(BASE_CURVES)
    if scenario == "downturn":
        curves["worked_example"] = DOWNTURN
    if scenario == "confounding" or reading_only or verdicts is not None:
        curves = {kind: (0.0, 0.0) for kind in KINDS}
    point = (P.hyper_grid()[[p.key() for p in P.hyper_grid()].index("1.5/0/0")],)
    banks = {}
    for name in arms:
        bank = M.Bank(point, groups=n, reading=True, verdict=True, capacity=64)
        banks[name] = View(bank, subject_view=True, reading=name == "on", verdicts=name == "on")
    truth_subject = rng.normal(0.0, math.sqrt(1.5), n)
    truth_beta_origin = rng.normal(0.0, 0.5, n)
    gamma = np.full(n, 0.2)
    offers: list[list[Any]] = [[] for _ in range(n)]
    visits: list[list[dict[str, Any]]] = [[] for _ in range(n)]
    records: dict[str, list[list[float]]] = {name: [[] for _ in range(n)] for name in arms}
    records["y"] = [[] for _ in range(n)]
    failed = np.zeros(n, dtype=bool)
    lam_true = {"self_check:matched": 0.0, "self_check:missed": -0.4 if verdicts == "missed" else 0.0}
    from learnloop.adaptive_difficulty.dose_report import OfferOutcome

    at = 0.0
    spec_cache: dict[str, ItemSpec] = {}
    for j in range(los):
        lo, facet = f"L{j}", f"f{j}"
        spec = spec_cache.setdefault(lo, cell_spec(lo, facet, "retrieval"))
        theta = truth_subject + rng.normal(0.0, math.sqrt(0.75), n) + rng.normal(0.0, math.sqrt(0.75), n)
        for view in banks.values():
            view.ensure(spec, at)
        for w in range(windows):
            counts = {kind: np.zeros(n) for kind in KINDS}
            if verdicts is not None:
                counts["in_passage_question"] = np.ones(n)  # one judged question a window
            elif reading_only:
                counts["reading"] = np.ones(n)
            else:
                counts["reading"] = (rng.random(n) < 0.8).astype(np.float64)
                counts["reader_tutor_exchange"] = rng.binomial(3, 0.3, n).astype(np.float64)
                counts["worked_example"] = rng.integers(0, 5, n).astype(np.float64)
                counts["in_passage_question"] = rng.integers(0, 4, n).astype(np.float64)
                if scenario == "confounding":
                    for kind in KINDS:
                        counts[kind] = counts[kind] + failed
            offer_rows: list[tuple[str, dict[str, float], int, float]] = []
            if not reading_only and verdicts is None:
                forecast = _predict_reference(banks[arms[0]], spec)
                for i in range(n):
                    pi = reading_dose_propensities(("none", "extra_worked_example", "extra_question"), {"none": 1.0},
                                                   floor)
                    variant = draw_from(pi, float(rng.random()))
                    dose_before = 0
                    if variant != "none":
                        kind = OFFER_KIND[variant]
                        dose_before = int(counts[kind][i])
                        if rng.random() < 0.7:
                            counts[kind][i] += 1
                    offer_rows.append((variant, pi, dose_before, float(forecast[i])))
            # The truth: each kind's dose curve over the window, then the answer.
            shift = sum(np.array([true_curve(curves[kind], c) for c in counts[kind]]) for kind in KINDS)
            if reading_only and rise:
                shift = rise * counts["reading"]
            verdict_class = None
            if verdicts is not None:
                missed = rng.random(n) < 0.5
                verdict_class = np.where(missed, "self_check:missed", "self_check:matched")
                shift = shift + np.where(missed, lam_true["self_check:missed"], lam_true["self_check:matched"])
            theta = theta + shift
            for name, view in banks.items():
                for kind in KINDS:
                    if counts[kind].any():
                        view.reading(SUBJECT, kind, {facet: np.repeat(counts[kind], 1)}, at)
                if verdict_class is not None:
                    for klass in ("self_check:matched", "self_check:missed"):
                        mask = (verdict_class == klass).astype(np.float64)
                        if mask.any():
                            view.verdict(SUBJECT, klass, {facet: mask}, at)
            at += 1.0
            eta_e = theta - truth_beta_origin
            category = sample_category(eta_e - rng.normal(0.0, P.TAU0, n), rng.random(n))
            y = (category == 2).astype(np.float64)
            for name, view in banks.items():
                p = _predict_reference(view, spec)
                for i in range(n):
                    records[name][i].append(float(p[i]))
            for i in range(n):
                records["y"][i].append(float(y[i]))
                if offer_rows:
                    variant, pi, dose_before, forecast_i = offer_rows[i]
                    band = "below_50" if forecast_i < 0.5 else "50_80" if forecast_i <= 0.8 else "above_80"
                    offers[i].append(OfferOutcome(variant, pi, float(y[i]), dose_before, band))
                visits[i].append({"active_minutes": float(sum(MINUTES[k] * counts[k][i] for k in KINDS)
                                                          + max(rng.normal(1.0, 0.5), 0.0)),
                                  "counts": {k: int(counts[k][i]) for k in KINDS}})
            for name, view in banks.items():
                view.observe(spec, category, at, rows=None)
                view.close_windows((facet,))
            theta = theta + gamma
            failed = category < 2
        for view in banks.values():
            view.bank.marginalize([M.facet_name(facet), M.cell_name(facet, "retrieval")])
    view = banks[arms[0]]
    bank = view.bank
    mean, cov = {}, {}
    for kind in KINDS:
        names = [("gbar:1", f"delta:{kind}:1"), ("gbar:2", f"delta:{kind}:2")]
        A = np.zeros((2, bank.d))
        for row, pair in enumerate(names):
            for name in pair:
                A[row, bank.index[name]] = 1.0
        mean[kind] = bank.mu @ A.T
        cov[kind] = np.einsum("ri,bij,sj->brs", A, bank.S, A)
    result = ReaderResult(curves, mean, cov, bank.mu[:, bank.index["gamma"]].copy(), offers, visits, view, records)
    if verdicts is not None:
        result.verdict_mean = bank.mu[:, [bank.index["lam:matched"], bank.index["lam:missed"]]].copy()
        result.verdict_sd = np.sqrt(np.stack([bank.S[:, bank.index["lam:matched"], bank.index["lam:matched"]],
                                              bank.S[:, bank.index["lam:missed"], bank.index["lam:missed"]]], 1))
    return result


def fitted_useful_dose(result: ReaderResult, kind: str, reader: int, *, draws: int = 400,
                       seed: str = "ad-dose-v1") -> dict[str, Any]:
    """The report's useful dose for one reader (``dose_report.useful_dose``): posterior draws of the
    kind's coefficients and of ``γ``, the kind's minutes by NNLS on the reader's visits."""

    from learnloop.adaptive_difficulty import dose_report as DR

    bank = result.view.bank
    names = [f"gbar:1", f"delta:{kind}:1", "gbar:2", f"delta:{kind}:2", "gamma"]
    idx = [bank.index[name] for name in names]
    mu = bank.mu[reader, idx]
    cov = bank.S[reader][np.ix_(idx, idx)]
    rng = rng_for(f"{seed}:{reader}:{kind}")
    sample = rng.multivariate_normal(mu, 0.5 * (cov + cov.T) + 1e-12 * np.eye(len(idx)), size=draws)
    c1, c2, gamma = sample[:, 0] + sample[:, 1], sample[:, 2] + sample[:, 3], sample[:, 4]
    visits = result.visits[reader]
    X = np.array([[1.0] + [float(v["counts"].get(k, 0)) for k in KINDS] for v in visits])
    y = np.array([float(v["active_minutes"]) for v in visits])
    minutes = float(DR.nnls(X, y)[1 + list(KINDS).index(kind)])
    reference = DR.points_gain(gamma) / PRACTICE_MINUTES
    return DR.useful_dose(c1, c2, minutes, reference) | {"minutes": minutes}


def _predict_reference(view: View, spec: ItemSpec) -> np.ndarray:
    m, v = view.prediction(spec, 0.0)
    return M.expected_success(m, v, 0.0)


def true_useful_dose(curve: tuple[float, float], minutes: float, *, gamma: float = 0.2,
                     practice_minutes: float = PRACTICE_MINUTES) -> int:
    """``n*`` of a true curve: the largest dose whose own event still adds at least one more practice
    question's gain per minute (both at the band's centre, warmth 0)."""

    from learnloop.adaptive_difficulty.dose_report import MAX_DOSE, points_gain

    reference = float(points_gain(gamma)) / practice_minutes
    best = 0
    for n in range(1, MAX_DOSE + 1):
        step = float(points_gain(true_curve(curve, n) - true_curve(curve, n - 1)))
        if step / minutes >= reference:
            best = n
    return best


__all__ = [
    "Arm",
    "BASE_CURVES",
    "CensoringResult",
    "Cluster",
    "DOWNTURN",
    "Incumbent",
    "KINDS",
    "MINUTES",
    "Pool",
    "ReaderResult",
    "RecoveryResult",
    "RelatedResult",
    "StepLog",
    "Truth",
    "UsableResult",
    "cell_spec",
    "censoring",
    "cluster_truth",
    "coding",
    "draw_truth",
    "feature_time_correlation",
    "fitted_useful_dose",
    "hyperparameters_learned",
    "own_answers_before_band",
    "pool_points",
    "proposal",
    "readers",
    "recovery",
    "related_topics",
    "rng_for",
    "sample_category",
    "serve_step",
    "time_to_usable",
    "true_curve",
    "true_success",
    "true_useful_dose",
    "waypoint_points",
    "wrong_proposal_shrinks",
]
