"""RO4 §3.2, §8.1: the objective's value estimator ``Q̄``, a pure function of a frozen belief.

At one decision every candidate is valued at **one shared cutoff** ``C = max(t + H, latest active goal date)``,
carried through every rollout:

```
Q(a) = R(t, σ]  +  V_tail(σ → C)  +  T_C          σ = min(t + τ_a, C)
R(t, σ]  = −κ integral of the action's active minutes + dated uses crossed during it (scored at their date,
           on the state before the action's effect) + undated uses during it
V_tail   = the tail's valued uses minus its attention cost from the end of the action to C
T_C      = the net value of continuing the same tail a further H past C (valued uses minus attention cost,
           evaluated once, never recursively)
```

The **tail** (the seed continuation ``π_Q`` values actions under, §8.1): flat total load at the remembered minutes
``m̄`` per day, one session a day, with topic allocation adaptive to the belief (each session ranks the valued
topics by their remaining use weight times the believed chance of failing, and practises the top ones), so
information can matter. A session ends when today's active minutes reach ``m̄``; the next one begins after a
return gap drawn from this learner's own gaps (next day with none), a fresh draw from the same distribution after
every session's end (one common-random-number column per session), so the return effect is zero until RO5 fits
one, and the trace says so.

**One clock** (Codex review F3): an action is a chronological sequence of segments (one, or a probe and its repair,
or a mid-block alternative's ordered sub-actions). Each segment charges its minutes from the session minutes it
starts at, earns the undated uses over its own interval and every dated use it crosses, both on the state before
its effect, and only then applies its effect; the tail starts at the last segment's end, and no interval before it
(on any day) and no session before it is counted again. Every draw keeps its own clock through the tail (never a
batch's maximum), and a tail session's blocks land at their ends the same way: a dated use a block's end crosses is
scored on the state before that block (Codex re-review F12).

**Sampling** (§8.1). ``K`` parameter draws θ (AD's posterior on each topic's ability, the combiner's and the
effect slope's posteriors, AD's learning increments, the stop offer's acceptance), each shared across every
candidate, with **common random numbers** for outcomes, durations, uptake and return. ``Q̄`` is the mean over
draws; :func:`paired_standard_error` is the precision of the top two's difference. Everything is vectorized over
the draws.

**Action interfaces** (§8.1's table): review, new practice, repair and teach-back are practice opportunities
(AD's ``γ`` at their evidence mass, FSRS's update over the rating distribution from AD's predictive, a graded
attempt that updates the belief); reading is AD's dose curve and no FSRS effect (the firewall), observing
nothing; a probe is scored **as a bundle**: on each result, the repair or no repair, whichever ``Q̄`` on the
posterior right after the probe prefers, then the tail (the branch is in the trace). Each branch's ``Q̄`` is
averaged over the belief's own world before the two are compared (every draw there from the same post-probe belief:
ability drawn from it, the believed parameters, noise independent of the true world's), so the choice is one per
result, integrates over the repair's possible outcomes and never sees the simulated repair's result or the true
path's noise (Codex review F2, re-review); the chosen repair is simulated afterwards. A lesson is AD's ``γ`` at the
lesson's learned mass;
an offer-type action is valued accepted and declined **as branches**, ``Q = p·E[R+V | acc] + (1−p)·E[R+V | dec]``;
the stop offer is two branches, accepted (no more today; the next session after a drawn return gap) and
overridden (the tail's next non-stop block at the same session minutes, so its value is never defined in terms
of itself), with ``p_accept`` drawn from its Beta posterior. Durations are sampled, never averaged: with the
quadratic cost, ``E[C(m, D)] = C(m, E[D]) + κ0/(2m̄)·Var(D)``.

**The effect correction** (§8.4): ``ΔG = α_v + β_v·f(a)`` on the logit scale, ``f(a)`` the LLM's forecast
probability for ``a`` minus its forecast probability for the tail's next action (the reference row; a difference
of probabilities, never of logits: Codex review F6), added to the action's topics after its
own effect: a correction to the memory rollout's learning effect, never a replacement. It applies only when every
candidate and the reference have a forecast; a missing one drops it for the decision.

A leaf: numpy and the standard library; every number it reads is in :class:`Inputs`, handed in frozen.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field, replace
import hashlib
import math
import time
from typing import Any

import numpy as np

from learnloop.router_objective.memory import Combiner, Fsrs, perform, sigmoid

OBJECTIVE_VERSION = "router_objective_v1"
TAIL_VERSION = "flat_load_adaptive_v1"
TERMINAL_VERSION = "net_continuation_v1"

#: Action kinds (§8.1's table).
REVIEW = "review"
NEW_PRACTICE = "new_practice"
READING = "reading"
PROBE = "probe"
REPAIR = "repair"
TEACH_BACK = "teach_back"
LESSON = "lesson"
STOP = "stop"
#: An ordered sequence of sub-actions (a mid-block alternative, §8.3): each step keeps its own kind, duration,
#: observation and effect, valued one after another on the one clock (Codex review F5).
SEQUENCE = "sequence"
PRACTICE_KINDS = frozenset({REVIEW, NEW_PRACTICE, REPAIR, TEACH_BACK})
KINDS = frozenset({REVIEW, NEW_PRACTICE, READING, PROBE, REPAIR, TEACH_BACK, LESSON, STOP, SEQUENCE})
#: The reference row's ref: the tail's next action, sent to the LLM policy as a non-choosable row.
REFERENCE_REF = "tail_next"
MINUTES_PER_DAY = 1440.0


@dataclass(frozen=True)
class Topic:
    """One valued topic (an LO) as the decision believed it."""

    lo: str
    #: AD's predictive on the logit scale and its posterior variance (θ draws from it).
    eta_mean: float
    eta_var: float
    #: FSRS state of the LO's practiced items (aggregate); ``practiced`` False: no memory yet.
    practiced: bool = False
    difficulty: float = 5.0
    stability: float = 0.0
    elapsed_days: float = 0.0
    #: ``c_L`` per day (§8.5): 0 for a topic not enrolled in any undated use.
    undated_density: float = 0.0
    #: AD's reading-dose count on the LO (the dose curve's position).
    reading_count: float = 0.0


@dataclass(frozen=True)
class DatedUse:
    goal_id: str
    lo: str
    #: days from the decision to the goal's date
    at_days: float
    #: ``ω_{g,L}`` (§8.5)
    weight: float


@dataclass(frozen=True)
class Learning:
    """AD's learning parameters (posterior mean, variance): ``γ`` per practice opportunity, the reading dose
    curve's ``ḡ_1, ḡ_2`` on scales ``h_1, h_2``."""

    gamma: tuple[float, float] = (0.2, 0.01)
    gbar: tuple[tuple[float, float], tuple[float, float]] = ((0.10, 0.0049), (0.20, 0.01))
    dose_scales: tuple[float, float] = (1.0, 4.0)
    source: str = "adaptive_difficulty.priors"


@dataclass(frozen=True)
class EffectSlope:
    """``ΔG = α_v + β_v·f(a)`` (§8.4): each coefficient's posterior mean and variance."""

    alpha: tuple[float, float] = (0.0, 0.04)
    beta: tuple[float, float] = (0.2, 0.04)
    n: int = 0
    version: str = "effect_slope_v1:prior"


@dataclass(frozen=True)
class Price:
    """The attention price at this decision (§8.6): ``κ(x) = κ0·x/m̄`` on session minutes."""

    kappa0: float
    remembered: float
    remembered_source: str = "unknown"
    regime: str = "seed"


@dataclass(frozen=True)
class Action:
    """One candidate as the value estimator sees it."""

    ref: str
    kind: str
    #: one LO per practice opportunity (or per reading dose, or the probe's topic)
    item_los: tuple[str, ...] = ()
    #: the predicted active minutes (the duration distribution's median)
    minutes: float = 0.0
    #: the duration's spread on the log scale (0: fixed)
    minutes_log_sd: float = 0.0
    #: evidence mass on ``γ`` (teach-back, lesson)
    mass: float = 1.0
    #: an offer-type action's uptake ``Beta(a, b)`` (None: not an offer)
    accept: tuple[float, float] | None = None
    #: a probe's repair branch (a practice block on the same topic)
    repair: "Action | None" = None
    #: the LLM policy's forecast for this option (a probability), the effect correction's input
    forecast: float | None = None
    choosable: bool = True
    #: a :data:`SEQUENCE`'s ordered sub-actions (none of them a sequence, a stop or an offer)
    steps: tuple["Action", ...] = ()

    def __post_init__(self) -> None:
        if self.kind not in KINDS:
            raise ValueError(f"unknown action kind {self.kind!r}")
        if (self.kind == SEQUENCE) != bool(self.steps):
            raise ValueError("a sequence (and only a sequence) has steps")
        if any(step.kind in (SEQUENCE, STOP) or step.accept is not None for step in self.steps):
            raise ValueError("a sequence's steps are plain actions")


@dataclass(frozen=True)
class Inputs:
    """The frozen belief one decision values its candidates on (every number the trace reports)."""

    topics: tuple[Topic, ...]
    dated: tuple[DatedUse, ...]
    session_minutes: float
    price: Price
    #: the tail's block: minutes and practice opportunities (the support's means)
    tail_block_minutes: float
    tail_block_items: int
    horizon_days: float
    fsrs_weights: tuple[float, ...]
    return_gaps_days: tuple[float, ...] = ()
    stop_accept: tuple[float, float] = (1.0, 1.0)
    combiner: Combiner = field(default_factory=Combiner)
    learning: Learning = field(default_factory=Learning)
    #: None: the effect correction is off by hand, or a forecast is missing
    effect: EffectSlope | None = None
    reference_forecast: float | None = None
    #: the trace's sources (where each number came from)
    sources: Mapping[str, Any] = field(default_factory=dict)

    @property
    def cutoff(self) -> float:
        """``C`` in days from the decision (§3.2): carried through every rollout."""

        latest = max((use.at_days for use in self.dated), default=0.0)
        return max(float(self.horizon_days), latest)


def cutoff_for(horizon_days: float, dated: Sequence[DatedUse]) -> float:
    return max(float(horizon_days), max((use.at_days for use in dated), default=0.0))


# -- common random numbers -----------------------------------------------------------------------------


def _seed_int(seed: str, stream: str) -> int:
    return int.from_bytes(hashlib.sha256(f"{seed}:{stream}".encode("utf-8")).digest()[:8], "big")


class _Streams:
    """Counter-free common random numbers: each stream is a fixed array, the same for every candidate."""

    def __init__(self, seed: str, draws: int, topics: int, days: int, slots: int) -> None:
        self.seed = seed

        def gen(name: str) -> np.random.Generator:
            return np.random.default_rng(_seed_int(seed, name))

        self.eta_z = gen("theta:eta").standard_normal((draws, topics))
        self.coef_z = gen("theta:combiner").standard_normal((draws, 3))
        self.gamma_z = gen("theta:gamma").standard_normal(draws)
        self.gbar_z = gen("theta:gbar").standard_normal((draws, 2))
        self.effect_z = gen("theta:effect").standard_normal((draws, 2))
        self.accept_u = gen("theta:stop_accept").random(draws)
        self.offer_u = gen("theta:offer_accept").random(draws)
        self.duration_z = gen("noise:duration").standard_normal((draws, 4))
        # One return gap per session end (column j: the gap after the j-th session's end; F4).
        self.return_u = gen("noise:return").random((draws, days + 2))
        # Outcomes: one uniform per (day, slot) for the tail, and per slot for the action itself.
        self.outcome_u = gen("noise:outcome").random((draws, days + 1, slots))
        self.action_u = gen("noise:action_outcome").random((draws, 4, 64))


def _beta_draw(u: np.ndarray, a: float, b: float) -> np.ndarray:
    """A Beta(a, b) quantile at ``u`` (inverse CDF by bisection on the regularized incomplete beta): the same
    uniform gives the same draw for every candidate."""

    if a == 1.0 and b == 1.0:
        return u.copy()
    lo = np.zeros_like(u)
    hi = np.ones_like(u)
    for _ in range(40):
        mid = (lo + hi) / 2
        cdf = np.array([_betainc(a, b, float(x)) for x in mid])
        lo = np.where(cdf < u, mid, lo)
        hi = np.where(cdf < u, hi, mid)
    return (lo + hi) / 2


def _betainc(a: float, b: float, x: float) -> float:
    """The regularized incomplete beta ``I_x(a, b)`` (Lentz's continued fraction)."""

    if x <= 0:
        return 0.0
    if x >= 1:
        return 1.0
    log_front = math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b) + a * math.log(x) + b * math.log1p(-x)
    if x > (a + 1) / (a + b + 2):
        return 1.0 - _betainc(b, a, 1.0 - x)
    tiny = 1e-300
    c, d = 1.0, 1.0 - (a + b) * x / (a + 1)
    d = 1.0 / (d if abs(d) > tiny else tiny)
    h = d
    for m in range(1, 300):
        for numerator in ((m * (b - m) * x) / ((a + 2 * m - 1) * (a + 2 * m)),
                          -((a + m) * (a + b + m) * x) / ((a + 2 * m) * (a + 2 * m + 1))):
            d = 1.0 + numerator * d
            d = 1.0 / (d if abs(d) > tiny else tiny)
            c = 1.0 + numerator / c
            c = c if abs(c) > tiny else tiny
            h *= d * c
        if abs(d * c - 1.0) < 1e-12:
            break
    return float(min(max(math.exp(log_front) * h / a, 0.0), 1.0))


# -- the simulation state ------------------------------------------------------------------------------


@dataclass
class _Theta:
    eta: np.ndarray          # (K, N) true ability under the draw
    coef: np.ndarray         # (K, 3)
    gamma: np.ndarray        # (K,)
    gbar: np.ndarray         # (K, 2)
    effect: np.ndarray       # (K, 2) alpha, beta
    stop_accept: np.ndarray  # (K,)
    return_days: np.ndarray  # (K, S) whole days to the next session after the j-th session's end


@dataclass
class _State:
    eta: np.ndarray        # (K, N) true
    bel: np.ndarray        # (K, N) believed mean
    bel_var: np.ndarray    # (K, N)
    d: np.ndarray          # (K, N) FSRS difficulty
    s: np.ndarray          # (K, N) FSRS stability
    practiced: np.ndarray  # (K, N) bool
    last: np.ndarray       # (K, N) time of the last review (days)
    reading: np.ndarray    # (K, N)

    def copy(self) -> "_State":
        return _State(*(np.array(getattr(self, name), copy=True) for name in
                        ("eta", "bel", "bel_var", "d", "s", "practiced", "last", "reading")))

    def select(self, mask: np.ndarray, other: "_State") -> "_State":
        """Per draw: this state where ``mask``, else ``other``'s."""

        m = mask[:, None]
        return _State(*(np.where(m, getattr(self, name), getattr(other, name)) for name in
                        ("eta", "bel", "bel_var", "d", "s", "practiced", "last", "reading")))


_LEDGER_FIELDS = ("crossed", "undated_action", "kappa_action", "tail_reward", "tail_cost", "terminal_reward",
                  "terminal_cost")


@dataclass
class _Ledger:
    """Per draw: the terms of one path (§8.8's per-candidate terms)."""

    crossed: np.ndarray        # dated uses crossed during the action
    undated_action: np.ndarray  # undated uses during the action
    kappa_action: np.ndarray    # the action's κ integral (a cost, positive)
    tail_reward: np.ndarray     # valued uses from the action's end to C
    tail_cost: np.ndarray       # the tail's attention cost to C
    terminal_reward: np.ndarray  # valued uses past C (T_C's reward)
    terminal_cost: np.ndarray    # attention cost past C (T_C's cost)

    @classmethod
    def zeros(cls, k: int) -> "_Ledger":
        return cls(*(np.zeros(k) for _ in range(7)))

    def copy(self) -> "_Ledger":
        return _Ledger(*(np.array(getattr(self, name), copy=True) for name in _LEDGER_FIELDS))

    @property
    def q(self) -> np.ndarray:
        return (self.crossed + self.undated_action - self.kappa_action + self.tail_reward - self.tail_cost
                + self.terminal_reward - self.terminal_cost)

    @property
    def terminal(self) -> np.ndarray:
        return self.terminal_reward - self.terminal_cost

    @property
    def after(self) -> np.ndarray:
        """``E[V(x′)]``: the tail from the action's end, ``T_C`` included."""

        return self.tail_reward - self.tail_cost + self.terminal

    @staticmethod
    def mix(p: np.ndarray, a: "_Ledger", b: "_Ledger") -> "_Ledger":
        names = ("crossed", "undated_action", "kappa_action", "tail_reward", "tail_cost", "terminal_reward",
                 "terminal_cost")
        return _Ledger(*(p * getattr(a, n) + (1 - p) * getattr(b, n) for n in names))

    @staticmethod
    def select(mask: np.ndarray, a: "_Ledger", b: "_Ledger") -> "_Ledger":
        names = ("crossed", "undated_action", "kappa_action", "tail_reward", "tail_cost", "terminal_reward",
                 "terminal_cost")
        return _Ledger(*(np.where(mask, getattr(a, n), getattr(b, n)) for n in names))


class _Model:
    """One decision's rollouts: the frozen inputs, the draws, and the streams."""

    def __init__(self, inputs: Inputs, draws: int, seed: str) -> None:
        self.inputs = inputs
        self.seed = seed
        self._belief: "_Model | None" = None
        self.k = int(draws)
        self.index = {topic.lo: i for i, topic in enumerate(inputs.topics)}
        self.n = len(inputs.topics)
        self.fsrs = Fsrs(tuple(inputs.fsrs_weights))
        self.cutoff = inputs.cutoff
        self.end = self.cutoff + float(inputs.horizon_days)
        self.days = int(math.ceil(self.end))
        self.slots = max(int(inputs.tail_block_items), 1) * max(self._blocks_per_session(), 1) + 64
        self.streams = _Streams(seed, self.k, max(self.n, 1), self.days, self.slots)
        self.c = np.array([topic.undated_density for topic in inputs.topics], dtype=np.float64)
        self.mbar = max(float(inputs.price.remembered), 1e-9)
        self.kappa0 = float(inputs.price.kappa0)
        self.theta = self._draw_theta()
        self.dated = sorted(inputs.dated, key=lambda use: use.at_days)
        self.dated_weight = np.zeros(self.n)
        self.effect_on = inputs.effect is not None

    # θ ---------------------------------------------------------------------------------------------
    def _blocks_per_session(self) -> int:
        d = max(float(self.inputs.tail_block_minutes), 1e-9)
        return max(int(round(float(self.inputs.price.remembered) / d)), 1)

    def _draw_theta(self) -> _Theta:
        inputs, st = self.inputs, self.streams
        mean = np.array([t.eta_mean for t in inputs.topics], dtype=np.float64)
        sd = np.sqrt(np.maximum(np.array([t.eta_var for t in inputs.topics], dtype=np.float64), 0.0))
        eta = mean[None, :] + sd[None, :] * st.eta_z[:, : self.n]
        cm = np.array(inputs.combiner.mean, dtype=np.float64)
        csd = np.sqrt(np.maximum(np.array(inputs.combiner.variance, dtype=np.float64), 0.0))
        coef = cm[None, :] + csd[None, :] * st.coef_z
        gm, gv = inputs.learning.gamma
        gamma = gm + math.sqrt(max(gv, 0.0)) * st.gamma_z
        gbar = np.stack([inputs.learning.gbar[i][0] + math.sqrt(max(inputs.learning.gbar[i][1], 0.0)) * st.gbar_z[:, i]
                         for i in (0, 1)], axis=1)
        effect = np.zeros((self.k, 2))
        if inputs.effect is not None:
            (am, av), (bm, bv) = inputs.effect.alpha, inputs.effect.beta
            effect[:, 0] = am + math.sqrt(max(av, 0.0)) * st.effect_z[:, 0]
            effect[:, 1] = bm + math.sqrt(max(bv, 0.0)) * st.effect_z[:, 1]
        a, b = inputs.stop_accept
        accept = _beta_draw(st.accept_u, float(a), float(b))
        gaps = np.array(sorted(max(float(g), 1.0) for g in inputs.return_gaps_days) or [1.0], dtype=np.float64)
        picks = np.minimum((st.return_u * len(gaps)).astype(int), len(gaps) - 1)
        return_days = np.ceil(gaps[picks])
        return _Theta(eta=eta, coef=coef, gamma=gamma, gbar=gbar, effect=effect, stop_accept=accept,
                      return_days=return_days)

    def initial(self) -> _State:
        inputs = self.inputs
        k, n = self.k, self.n

        def column(values: Sequence[float]) -> np.ndarray:
            return np.broadcast_to(np.asarray(values, dtype=np.float64)[None, :], (k, n)).copy()

        topics = inputs.topics
        return _State(
            eta=self.theta.eta.copy(),
            bel=column([t.eta_mean for t in topics]),
            bel_var=column([max(t.eta_var, 1e-12) for t in topics]),
            d=column([t.difficulty for t in topics]),
            s=column([t.stability for t in topics]),
            practiced=np.broadcast_to(np.array([t.practiced for t in topics], dtype=bool)[None, :], (k, n)).copy(),
            last=column([-t.elapsed_days for t in topics]),
            reading=column([t.reading_count for t in topics]),
        )

    # the memory forecast ---------------------------------------------------------------------------
    def performance(self, state: _State, at: float | np.ndarray, *, belief: bool = False) -> np.ndarray:
        """``P(perform)`` per draw and topic at time ``at`` (a scalar, or one time per draw)."""

        when = np.asarray(at, dtype=np.float64)
        if when.ndim == 1:
            when = when[:, None]
        r = self.fsrs.retrievability(state.s, when - state.last)
        eta = state.bel if belief else state.eta
        return perform(self.theta.coef, eta, r, state.practiced)

    def cost(self, start: np.ndarray, minutes: np.ndarray) -> np.ndarray:
        """``∫[m, m+d] κ(u) du = κ0·((m+d)² − m²)/(2m̄)``."""

        return self.kappa0 * ((start + minutes) ** 2 - start ** 2) / (2.0 * self.mbar)

    # effects ---------------------------------------------------------------------------------------
    def _practice(self, state: _State, lo: int, at: np.ndarray, u: np.ndarray, mask: np.ndarray, mass: float) -> None:
        """One practice opportunity on topic ``lo`` for the draws in ``mask``: a graded attempt."""

        p_true = sigmoid(state.eta[:, lo])
        good = u < p_true
        d, s = self.fsrs.review(state.d[:, lo], state.s[:, lo], state.practiced[:, lo], at - state.last[:, lo], good)
        gm = float(self.inputs.learning.gamma[0])
        # The belief observes the graded attempt (a one-step Laplace update), then learns as the model predicts.
        p_bel = sigmoid(state.bel[:, lo])
        var = 1.0 / (1.0 / state.bel_var[:, lo] + p_bel * (1 - p_bel))
        bel = state.bel[:, lo] + var * (good.astype(np.float64) - p_bel)
        state.d[:, lo] = np.where(mask, d, state.d[:, lo])
        state.s[:, lo] = np.where(mask, s, state.s[:, lo])
        state.practiced[:, lo] = np.where(mask, True, state.practiced[:, lo])
        state.last[:, lo] = np.where(mask, at, state.last[:, lo])
        state.eta[:, lo] = np.where(mask, state.eta[:, lo] + self.theta.gamma * mass, state.eta[:, lo])
        state.bel[:, lo] = np.where(mask, bel + gm * mass, state.bel[:, lo])
        state.bel_var[:, lo] = np.where(mask, var, state.bel_var[:, lo])

    def _observe(self, state: _State, lo: int, u: np.ndarray, mask: np.ndarray,
                 observed: np.ndarray | None = None) -> np.ndarray:
        """A probe's observation: the belief's update, nothing direct. Returns the result per draw (``observed``:
        the result given, for valuing the branches on one result)."""

        good = u < sigmoid(state.eta[:, lo]) if observed is None else np.asarray(observed, dtype=bool)
        p_bel = sigmoid(state.bel[:, lo])
        var = 1.0 / (1.0 / state.bel_var[:, lo] + p_bel * (1 - p_bel))
        bel = state.bel[:, lo] + var * (good.astype(np.float64) - p_bel)
        state.bel[:, lo] = np.where(mask, bel, state.bel[:, lo])
        state.bel_var[:, lo] = np.where(mask, var, state.bel_var[:, lo])
        return good

    def _read(self, state: _State, lo: int, mask: np.ndarray, dose: float = 1.0) -> None:
        h1, h2 = self.inputs.learning.dose_scales
        n = state.reading[:, lo]
        inc1 = np.exp(-n / h1) - np.exp(-(n + dose) / h1)
        inc2 = np.exp(-n / h2) - np.exp(-(n + dose) / h2)
        true = self.theta.gbar[:, 0] * inc1 + self.theta.gbar[:, 1] * inc2
        believed = self.inputs.learning.gbar[0][0] * inc1 + self.inputs.learning.gbar[1][0] * inc2
        state.eta[:, lo] = np.where(mask, state.eta[:, lo] + true, state.eta[:, lo])
        state.bel[:, lo] = np.where(mask, state.bel[:, lo] + believed, state.bel[:, lo])
        state.reading[:, lo] = np.where(mask, n + dose, n)

    def apply(self, state: _State, action: Action, at: np.ndarray, mask: np.ndarray, *, stream: int = 0,
              correction: np.ndarray | None = None) -> None:
        """An action's effect at time ``at`` (per draw) for the draws in ``mask`` (a probe's observation is
        :meth:`_observe`, done by the caller)."""

        u = self.streams.action_u[:, stream % 4, :]
        los = [self.index[lo] for lo in action.item_los if lo in self.index]
        if action.kind in PRACTICE_KINDS:
            for slot, lo in enumerate(los):
                self._practice(state, lo, at, u[:, slot % u.shape[1]], mask, float(action.mass))
        elif action.kind == LESSON:
            gm = float(self.inputs.learning.gamma[0])
            for lo in dict.fromkeys(los):
                state.eta[:, lo] = np.where(mask, state.eta[:, lo] + self.theta.gamma * action.mass, state.eta[:, lo])
                state.bel[:, lo] = np.where(mask, state.bel[:, lo] + gm * action.mass, state.bel[:, lo])
        elif action.kind == READING:
            for lo in los:
                self._read(state, lo, mask)
        if correction is not None:
            for lo in dict.fromkeys(los):
                state.eta[:, lo] = np.where(mask, state.eta[:, lo] + correction, state.eta[:, lo])

    # the tail --------------------------------------------------------------------------------------
    def _priority(self, state: _State, at: float | np.ndarray) -> np.ndarray:
        """Each topic's remaining use weight times the believed chance of failing, at ``at`` (a scalar, or one
        time per draw: every draw keeps its own clock, Codex re-review F12)."""

        when = np.broadcast_to(np.asarray(at, dtype=np.float64), (self.k,))
        remaining = np.maximum(self.end - when, 0.0)
        weight = self.c[None, :] * remaining[:, None]
        for use in self.dated:
            if use.lo in self.index:
                weight[:, self.index[use.lo]] += np.where(use.at_days > when, use.weight, 0.0)
        fail = 1.0 - self.performance(state, when, belief=True)
        return weight * fail

    def _practice_batch(self, state: _State, cols: np.ndarray, at: np.ndarray, u: np.ndarray,
                        active: np.ndarray) -> None:
        """Practice opportunities at ``(draw, cols[draw, j])`` where ``active``, at each draw's own time ``at``:
        each row's topics are distinct, so the updates are one vectorized step (:meth:`_practice`'s, elementwise)."""

        rows = np.broadcast_to(np.arange(self.k)[:, None], cols.shape)
        r, c = rows[active], cols[active]
        if r.size == 0:
            return
        when = np.broadcast_to(np.asarray(at, dtype=np.float64), (self.k,))[r]
        eta = state.eta[r, c]
        good = u[active] < sigmoid(eta)
        d, s = self.fsrs.review(state.d[r, c], state.s[r, c], state.practiced[r, c], when - state.last[r, c], good)
        p_bel = sigmoid(state.bel[r, c])
        var = 1.0 / (1.0 / state.bel_var[r, c] + p_bel * (1 - p_bel))
        bel = state.bel[r, c] + var * (good.astype(np.float64) - p_bel)
        gm = float(self.inputs.learning.gamma[0])
        state.d[r, c] = d
        state.s[r, c] = s
        state.practiced[r, c] = True
        state.last[r, c] = when
        state.eta[r, c] = eta + self.theta.gamma[r]
        state.bel[r, c] = bel + gm
        state.bel_var[r, c] = var

    def _session(self, state: _State, ledger: _Ledger, at: np.ndarray, mask: np.ndarray, start: np.ndarray, day: int,
                 *, past_cutoff: bool, target: float | None = None,
                 before_block: Callable[[np.ndarray, np.ndarray], None] | None = None) -> None:
        """A tail session from ``start`` session minutes to ``m̄`` (or ``target``: today's, for ``G``), in blocks
        of ``d̄`` with ``ī`` practice opportunities each, for the draws in ``mask``, each draw on its own clock from
        ``at`` (days, per draw; never a batch's maximum, Codex re-review F12). The session's topics are ranked once
        on the belief at its start (adaptive to the belief), the top ones practised in turn; its cost is the κ
        integral from ``start`` over its blocks' minutes. Each block's effect lands at its end, as a segment's
        does, and ``before_block(end, active)`` runs first, so a dated use the block's end crosses is scored on
        the state before it."""

        d = float(self.inputs.tail_block_minutes)
        if d <= 0 or self.n == 0:
            return
        when = np.broadcast_to(np.asarray(at, dtype=np.float64), (self.k,))
        goal = self.mbar if target is None else float(target)
        blocks = np.where(mask, np.ceil(np.maximum(goal - start, 0.0) / d - 1e-9), 0.0)
        blocks = np.maximum(blocks, 0.0)
        if not (blocks > 0).any():
            return
        cost = np.where(blocks > 0, self.cost(start, blocks * d), 0.0)
        if past_cutoff:
            ledger.terminal_cost += cost
        else:
            ledger.tail_cost += cost
        items = max(int(self.inputs.tail_block_items), 1)
        priority = self._priority(state, when)
        order = np.argsort(-priority, axis=1, kind="stable")
        u = self.streams.outcome_u[:, min(day, self.days), :]
        for block in range(int(blocks.max())):
            active = blocks > block
            end = when + (block + 1) * d / MINUTES_PER_DAY
            if before_block is not None:
                before_block(end, active)
            # The block's slots, in chunks that never repeat a topic within a row (the ranking taken cyclically).
            slot, stop = block * items, (block + 1) * items
            while slot < stop:
                offset = slot % self.n
                width = min(self.n - offset, stop - slot)
                cols = order[:, offset:offset + width]
                slots = (slot + np.arange(width)) % u.shape[1]
                self._practice_batch(state, cols, end, u[:, slots], np.broadcast_to(active[:, None], cols.shape))
                slot += width

    def _score_dated(self, state: _State, ledger: _Ledger, use: DatedUse, mask: np.ndarray | None = None
                     ) -> np.ndarray | None:
        """Score ``use`` at its date on ``state`` for the draws in ``mask``; returns ``P(perform)`` per draw."""

        lo = self.index.get(use.lo)
        if lo is None:
            return None
        p = self.performance(state, use.at_days)[:, lo]
        ledger.tail_reward += p * use.weight if mask is None else np.where(mask, p * use.weight, 0.0)
        return p

    def run_tail(self, state: _State, ledger: _Ledger, *, today_minutes: np.ndarray | None, after: np.ndarray,
                 dated_done: np.ndarray, today_target: float | None = None,
                 recorder: dict[str, Any] | None = None) -> None:
        """The tail from the action's end ``after`` (per draw): today's session continues to ``m̄`` unless
        ``today_minutes`` is None (the session ended), then a session after each return gap until ``C + H``, a
        fresh gap from the learner's own distribution after every session's end (F4). Nothing before ``after`` is
        counted on any day, and no session starts before it (F3). ``dated_done``: per draw and dated use, whether
        it was already scored (crossed during the action)."""

        k = self.k
        after = np.broadcast_to(np.asarray(after, dtype=np.float64), (k,)).copy()
        done = np.array(dated_done, dtype=bool, copy=True)
        # Each draw's P(perform) at a dated use's date, on the state it was scored on (the recorder's m⁰).
        scored = np.full((k, len(self.dated)), np.nan)

        def score(index: int, use: DatedUse, mask: np.ndarray) -> None:
            p = self._score_dated(state, ledger, use, mask)
            if p is not None:
                scored[:, index] = np.where(mask, p, scored[:, index])
            done[:, index] |= mask

        def before_block(end: np.ndarray, active: np.ndarray) -> None:
            # A dated use the block's end crosses is scored on the state before the block (F12).
            for index, use in enumerate(self.dated):
                crossed = active & ~done[:, index] & (use.at_days <= end + 1e-12)
                if crossed.any():
                    score(index, use, crossed)

        if today_minutes is not None:
            today = after < 1.0
            if today.any():
                self._session(state, ledger, after, today, today_minutes, 0, past_cutoff=False, target=today_target,
                              before_block=before_block)
        rows = np.arange(k)
        gaps = self.theta.return_days
        # The session that ended at the action's end (today's) is the 0th; its gap is column 0.
        ended = np.zeros(k, dtype=int)
        next_session = np.floor(after) + gaps[:, 0]
        pending = list(enumerate(self.dated))
        boundaries = sorted({0.0, self.cutoff, self.end, *[float(j) for j in range(1, self.days + 1)]})
        boundaries = [b for b in boundaries if b <= self.end + 1e-12]
        for day in range(0, self.days + 1):
            day_start = float(day)
            if day >= 1:
                mask = (next_session <= day_start + 1e-9) & (after <= day_start + 1e-9)
                if mask.any():
                    self._session(state, ledger, np.full(k, day_start), mask, np.zeros(k), day,
                                  past_cutoff=day_start >= self.cutoff - 1e-12, before_block=before_block)
                    ended = np.where(mask, np.minimum(ended + 1, gaps.shape[1] - 1), ended)
                    next_session = np.where(mask, day_start + gaps[rows, ended], next_session)
            day_end = min(day_start + 1.0, self.end)
            # Dated uses on this day that no block crossed, after its session, on the state then.
            for index, use in list(pending):
                if use.at_days < day_end or (use.at_days <= self.end and day_end >= self.end):
                    todo = ~done[:, index]
                    if todo.any():
                        score(index, use, todo)
                    if recorder is not None and use.lo in self.index:
                        now = self.performance(state, use.at_days)[:, self.index[use.lo]]
                        recorder.setdefault("dated", {})[f"{use.goal_id}:{use.lo}"] = float(
                            np.where(np.isnan(scored[:, index]), now, scored[:, index]).mean())
                    pending.remove((index, use))
            # Undated uses over this day's pieces (split at C), from the action's end on every day.
            cuts = [b for b in boundaries if day_start < b < day_end]
            edges = [day_start, *cuts, day_end]
            for a, b in zip(edges[:-1], edges[1:]):
                width = np.maximum(b - np.maximum(after, a), 0.0)
                if not (width > 0).any():
                    continue
                p = self.performance(state, (a + b) / 2)
                reward = (p * self.c[None, :]).sum(axis=1) * width
                if a >= self.cutoff - 1e-12:
                    ledger.terminal_reward += reward
                else:
                    ledger.tail_reward += reward
            if recorder is not None and 1 <= day <= int(recorder.get("days", 0)):
                recorder.setdefault("daily", {})[day] = self.performance(state, day_start + 0.5).mean(axis=0)
            if day_end >= self.end:
                break

    # one action ------------------------------------------------------------------------------------
    def _effect_correction(self, action: Action) -> np.ndarray | None:
        if not self.effect_on or action.kind == STOP:
            return None
        ref = self.inputs.reference_forecast
        if action.forecast is None or ref is None:
            return None
        # §8.4: f(a) is the difference of the two forecast probabilities; ΔG = α + β·f is on the logit scale.
        f = float(action.forecast) - float(ref)
        return self.theta.effect[:, 0] + self.theta.effect[:, 1] * f

    def _durations(self, action: Action, stream: int = 0) -> np.ndarray:
        z = self.streams.duration_z[:, stream % 4]
        return float(action.minutes) * np.exp(float(action.minutes_log_sd) * z)

    def _segment(self, state: _State, ledger: _Ledger, action: Action, *, start: np.ndarray, spent: np.ndarray,
                 minutes: np.ndarray, dated_done: np.ndarray, stream: int,
                 correction: np.ndarray | None = None,
                 observed: np.ndarray | None = None) -> tuple[np.ndarray, np.ndarray, np.ndarray | None]:
        """One segment of an action on the one clock, from ``start`` (days, per draw) at ``spent`` minutes into the
        action: its κ integral (minutes past ``C`` are ``T_C``'s), the undated uses over its interval and every
        dated use it crosses, both on the state **before** its effect, then its effect at its end (a probe's: the
        observation). Returns its end, the minutes spent after it, and a probe's result per draw."""

        m = float(self.inputs.session_minutes)
        tau = minutes / MINUTES_PER_DAY
        end = start + tau
        within = np.clip((self.cutoff - start) * MINUTES_PER_DAY, 0.0, minutes)
        ledger.kappa_action += self.cost(m + spent, within)
        ledger.terminal_cost += self.cost(m + spent + within, minutes - within)
        rate = (self.performance(state, start) * self.c[None, :]).sum(axis=1)
        ledger.undated_action += rate * np.maximum(np.minimum(end, self.cutoff) - start, 0.0)
        ledger.terminal_reward += rate * np.maximum(np.minimum(end, self.end) - np.maximum(start, self.cutoff), 0.0)
        for index, use in enumerate(self.dated):
            crossed = ~dated_done[:, index] & (use.at_days <= end + 1e-12)
            if crossed.any() and use.lo in self.index:
                p = self.performance(state, use.at_days)[:, self.index[use.lo]] * use.weight
                ledger.crossed += np.where(crossed, p, 0.0)
            dated_done[:, index] |= crossed
        everyone = np.ones(self.k, dtype=bool)
        good = None
        if action.kind == PROBE:
            lo = self.index.get(action.item_los[0]) if action.item_los else None
            if lo is not None:
                good = self._observe(state, lo, self.streams.action_u[:, stream % 4, 0], everyone, observed)
        else:
            self.apply(state, action, end, everyone, stream=stream, correction=correction)
        return end, spent + minutes, good

    def _steps(self, action: Action, stream: int) -> list[tuple[Action, int]]:
        """An action's segments with their noise streams: a sequence's steps each keep the stream of their place
        in the sorted refs, so the same step draws the same outcomes and duration in either order (common random
        numbers across orders)."""

        if not action.steps:
            return [(action, stream)]
        order = sorted(step.ref for step in action.steps)
        return [(step, order.index(step.ref) % 4) for step in action.steps]

    def _do(self, action: Action, *, stream: int = 0) -> tuple[_Ledger, _State, np.ndarray]:
        """The action from the decision's state: its segments in order on one clock, then the tail. Returns the
        ledger, the state after the action's effect (before the tail) and its minutes per draw."""

        k = self.k
        ledger = _Ledger.zeros(k)
        state = self.initial()
        at, spent = np.zeros(k), np.zeros(k)
        dated_done = np.zeros((k, len(self.dated)), dtype=bool)
        correction = None if action.steps else self._effect_correction(action)
        for step, step_stream in self._steps(action, stream):
            at, spent, _good = self._segment(state, ledger, step, start=at, spent=spent,
                                             minutes=self._durations(step, step_stream), dated_done=dated_done,
                                             stream=step_stream, correction=correction)
        effect_state = state.copy()
        self.run_tail(state, ledger, today_minutes=float(self.inputs.session_minutes) + spent, after=at,
                      dated_done=dated_done)
        return ledger, effect_state, spent

    def _stop_accepted(self) -> _Ledger:
        k = self.k
        ledger = _Ledger.zeros(k)
        state = self.initial()
        self.run_tail(state, ledger, today_minutes=None, after=np.zeros(k), dated_done=np.zeros((k, len(self.dated)),
                                                                                                    dtype=bool))
        return ledger

    def tail_action(self, ref: str = REFERENCE_REF) -> Action:
        """The tail's next non-stop block at the decision: its practice opportunities on the top topics."""

        if self.n == 0:
            return Action(ref=ref, kind=REVIEW, item_los=(), minutes=float(self.inputs.tail_block_minutes),
                          choosable=False, forecast=self.inputs.reference_forecast)
        state = self.initial()
        priority = self._priority(state, 0.0).mean(axis=0)
        order = np.argsort(-priority, kind="stable")
        items = max(int(self.inputs.tail_block_items), 1)
        los = tuple(self.inputs.topics[int(order[j % self.n])].lo for j in range(items))
        practiced = self.inputs.topics[int(order[0])].practiced
        return Action(ref=ref, kind=REVIEW if practiced else NEW_PRACTICE, item_los=los,
                      minutes=float(self.inputs.tail_block_minutes), choosable=False,
                      forecast=self.inputs.reference_forecast)

    def value(self, action: Action) -> tuple[_Ledger, dict[str, Any]]:
        """``Q`` per draw for one action, with its branch record."""

        extra: dict[str, Any] = {}
        if action.kind == STOP:
            accepted = self._stop_accepted()
            overridden, _state, _minutes = self._do(self.tail_action(), stream=1)
            p = self.theta.stop_accept
            extra["branches"] = {"accepted": float(accepted.q.mean()), "overridden": float(overridden.q.mean()),
                                 "p_accept": float(p.mean())}
            return _Ledger.mix(p, accepted, overridden), extra
        if action.accept is not None:
            a, b = action.accept
            p = _beta_draw(self.streams.offer_u, float(a), float(b))
            accepted, _state, _minutes = self._do(replace(action, accept=None))
            declined, _s2, _m2 = self._do(self.tail_action(), stream=1) if float(self.inputs.session_minutes) < self.mbar \
                else (self._stop_accepted(), None, None)
            extra["branches"] = {"accepted": float(accepted.q.mean()), "declined": float(declined.q.mean()),
                                 "p_accept": float(p.mean())}
            return _Ledger.mix(p, accepted, declined), extra
        if action.kind == PROBE:
            return self._probe(action)
        ledger, _state, _minutes = self._do(action)
        return ledger, extra

    def _belief_model(self) -> "_Model":
        """The belief's own world for a probe's branch choice: the believed parameters (each posterior's mean, no
        parameter draw), and noise streams of its own, independent of the true world's, so a choice made in it
        integrates over outcomes it cannot know (F2)."""

        if self._belief is None:
            inputs, learning = self.inputs, self.inputs.learning
            believed = replace(
                inputs,
                combiner=replace(inputs.combiner, variance=(0.0, 0.0, 0.0)),
                learning=replace(learning, gamma=(learning.gamma[0], 0.0),
                                 gbar=((learning.gbar[0][0], 0.0), (learning.gbar[1][0], 0.0))),
                effect=None, stop_accept=(1.0, 1.0))
            self._belief = _Model(believed, self.k, f"{self.seed}:belief")
        return self._belief

    def _probe_choice(self, probe: Action, repair: Action, result: bool | None) -> dict[str, Any]:
        """§8.1: on the probe's ``result`` (None: a probe that observes no valued topic), whether ``Q̄`` on the
        updated posterior prefers the repair. Both branches are averaged over the belief's own world before they
        are compared (Codex re-review F2): every draw there starts from the same post-probe belief, its ability
        drawn from that belief, the repair's outcomes, the probe's and the repair's durations and the tail's noise
        drawn there, independent of the true path's. So the choice is a function of the result alone, and nothing
        the true path draws after the probe enters it."""

        world = self._belief_model()
        k = world.k
        state, ledger = world.initial(), _Ledger.zeros(k)
        done = np.zeros((k, len(world.dated)), dtype=bool)
        observed = None if result is None else np.full(k, bool(result))
        at, spent, _good = world._segment(state, ledger, probe, start=np.zeros(k), spent=np.zeros(k),
                                          minutes=world._durations(probe), dated_done=done, stream=0,
                                          observed=observed)
        # The ability the post-probe belief implies (the prior's for every topic the probe did not observe).
        state.eta = state.bel + np.sqrt(np.maximum(state.bel_var, 0.0)) * world.streams.eta_z[:, : self.n]
        means: dict[str, float] = {}
        for branch in ("none", "repair"):
            path, terms, path_done = state.copy(), ledger.copy(), done.copy()
            end, used = at, spent
            if branch == "repair":
                end, used, _g = world._segment(path, terms, repair, start=end, spent=used,
                                               minutes=world._durations(repair, stream=2), dated_done=path_done,
                                               stream=2)
            world.run_tail(path, terms, today_minutes=float(self.inputs.session_minutes) + used, after=end,
                           dated_done=path_done)
            means[branch] = float(terms.q.mean())
        return {"repair": bool(means["repair"] > means["none"]), "q_none": means["none"],
                "q_repair": means["repair"]}

    def _probe(self, action: Action) -> tuple[_Ledger, dict[str, Any]]:
        """§8.1: the probe, then on its result the repair or no repair, whichever ``Q̄`` on the posterior right after
        the probe prefers (:meth:`_probe_choice`, one choice per result), then the tail. The probe's own segment is
        shared by both branches; the chosen repair is simulated afterwards on the true path, on the same clock."""

        k = self.k
        repair = action.repair or Action(ref=f"{action.ref}:repair", kind=REPAIR, item_los=action.item_los[:1],
                                         minutes=action.minutes)
        state = self.initial()
        ledger = _Ledger.zeros(k)
        dated_done = np.zeros((k, len(self.dated)), dtype=bool)
        at, spent, good = self._segment(state, ledger, action, start=np.zeros(k), spent=np.zeros(k),
                                        minutes=self._durations(action), dated_done=dated_done, stream=0)
        if good is None:
            on_result = {"none": self._probe_choice(action, repair, None)}
            choose_repair = np.full(k, on_result["none"]["repair"])
        else:
            on_result = {"success": self._probe_choice(action, repair, True),
                         "miss": self._probe_choice(action, repair, False)}
            choose_repair = np.where(good, on_result["success"]["repair"], on_result["miss"]["repair"])
        results: dict[str, _Ledger] = {}
        for branch in ("none", "repair"):
            path, terms, done = state.copy(), ledger.copy(), dated_done.copy()
            end, used = at, spent
            if branch == "repair":
                end, used, _good = self._segment(path, terms, repair, start=end, spent=used,
                                                 minutes=self._durations(repair, stream=2), dated_done=done, stream=2)
            self.run_tail(path, terms, today_minutes=float(self.inputs.session_minutes) + used, after=end,
                          dated_done=done)
            results[branch] = terms
        chosen = _Ledger.select(choose_repair, results["repair"], results["none"])
        fixed = max(float(results["none"].q.mean()), float(results["repair"].q.mean()))
        missed = ~good if good is not None else np.zeros(k, dtype=bool)
        succeeded = good if good is not None else np.zeros(k, dtype=bool)
        extra = {"branches": {"none": float(results["none"].q.mean()), "repair": float(results["repair"].q.mean()),
                              "repair_share": float(choose_repair.mean()),
                              "repair_after_miss": float(choose_repair[missed].mean()) if missed.any() else None,
                              "repair_after_success": float(choose_repair[succeeded].mean()) if succeeded.any()
                              else None,
                              "on_result": on_result,
                              "choice": "per result: Q̄ on the posterior after the probe, averaged in the belief's "
                                        "own world before the branches are compared"},
                 "information": float(chosen.q.mean()) - fixed}
        return chosen, extra


# -- the public evaluation -----------------------------------------------------------------------------


@dataclass(frozen=True)
class Valued:
    """One candidate's value (§8.8's terms)."""

    ref: str
    kind: str
    q_draws: tuple[float, ...]
    terms: Mapping[str, float]
    extra: Mapping[str, Any]
    choosable: bool

    @property
    def q(self) -> float:
        return float(np.mean(self.q_draws)) if self.q_draws else 0.0


@dataclass(frozen=True)
class Evaluation:
    valued: tuple[Valued, ...]
    draws: int
    cutoff: float
    seed: str
    elapsed_ms: int
    complete: bool
    reference: Valued | None = None

    def by_ref(self) -> dict[str, Valued]:
        return {v.ref: v for v in self.valued}

    @property
    def v(self) -> float:
        """``V = Σ_a π_tail(a)·Q(a)``: the tail's next action is deterministic, so ``V`` is its row's ``Q``."""

        return self.reference.q if self.reference is not None else 0.0


def _terms(ledger: _Ledger) -> dict[str, float]:
    return {
        "crossed_date_reward": float(ledger.crossed.mean()),
        "undated_reward": float(ledger.undated_action.mean()),
        "kappa_integral": float(ledger.kappa_action.mean()),
        "after": float(ledger.after.mean()),
        "tail_reward": float(ledger.tail_reward.mean()),
        "tail_cost": float(ledger.tail_cost.mean()),
        "terminal": float(ledger.terminal.mean()),
    }


def evaluate(inputs: Inputs, actions: Sequence[Action], *, draws: int, seed: str, max_draws: int | None = None,
             keep_going: Callable[[], bool] | None = None, deadline: float | None = None,
             clock: Callable[[], float] = time.monotonic,
             on_complete: Callable[[Evaluation], None] | None = None) -> Evaluation:
    """``Q`` for every action (and the reference row) under ``draws`` θ draws, adding batches of ``draws`` more
    while ``keep_going()`` holds, up to ``max_draws``, and never past ``deadline`` (``clock``'s). An evaluation
    that could not finish its first batch by the deadline is ``complete = False``; a refinement the deadline cuts
    short returns the latest complete batch (F7). ``on_complete`` sees each complete batch as it finishes."""

    started = clock()
    total = int(draws)
    limit = int(max_draws or draws)
    model = _Model(inputs, total, seed)
    latest: Evaluation | None = None
    while True:
        rows: list[Valued] = []
        complete = True
        reference_action = model.tail_action()
        for action in [*actions, reference_action]:
            if deadline is not None and clock() > deadline:
                complete = False
                break
            ledger, extra = model.value(action)
            rows.append(Valued(ref=action.ref, kind=action.kind, q_draws=tuple(float(v) for v in ledger.q),
                               terms=_terms(ledger), extra=extra, choosable=action.choosable))
        if not complete:
            break
        latest = Evaluation(valued=tuple(row for row in rows if row.ref != REFERENCE_REF), draws=model.k,
                            cutoff=model.cutoff, seed=seed, elapsed_ms=int(round((clock() - started) * 1000)),
                            complete=True, reference=next((row for row in rows if row.ref == REFERENCE_REF), None))
        if on_complete is not None:
            on_complete(latest)
        more = keep_going() if keep_going is not None else False
        if not more or total >= limit or (deadline is not None and clock() > deadline):
            break
        total = min(total * 2, limit)
        model = _Model(inputs, total, seed)
    if latest is not None:
        return replace(latest, elapsed_ms=int(round((clock() - started) * 1000)))
    return Evaluation(valued=(), draws=model.k, cutoff=model.cutoff, seed=seed,
                      elapsed_ms=int(round((clock() - started) * 1000)), complete=False, reference=None)


def paired_standard_error(a: Valued, b: Valued) -> float:
    """The standard error of ``Q̄(a) − Q̄(b)`` over the shared draws (common random numbers)."""

    x = np.asarray(a.q_draws) - np.asarray(b.q_draws)
    if x.size < 2:
        return 0.0
    return float(np.std(x, ddof=1) / math.sqrt(x.size))


def numeric_choice(evaluation: Evaluation, support: Sequence[str]) -> tuple[str, dict[str, Any]]:
    """``π_Q`` (§8.3): plain argmax of ``Q̄``; candidates within the paired precision of the maximum are broken
    by support order (staged's pick first). Returns the choice and the record of the tie rule."""

    rows = evaluation.by_ref()
    ranked = [ref for ref in support if ref in rows]
    if not ranked:
        raise ValueError("no valued candidate in the support")
    best = max(ranked, key=lambda ref: rows[ref].q)
    tied = [ref for ref in ranked
            if ref == best or rows[best].q - rows[ref].q <= paired_standard_error(rows[best], rows[ref]) + 1e-15]
    chosen = next(ref for ref in ranked if ref in tied)
    order = sorted(ranked, key=lambda ref: -rows[ref].q)
    top_two = order[:2]
    precision = paired_standard_error(rows[top_two[0]], rows[top_two[1]]) if len(top_two) == 2 else 0.0
    return chosen, {"argmax": best, "tied": tied, "chosen": chosen, "top_two": top_two,
                    "paired_se_top_two": precision, "rule": "argmax_qbar_ties_within_paired_se_by_support_order"}


def baselines(inputs: Inputs, window_days: int, *, draws: int, seed: str) -> dict[str, Any]:
    """§8.7's ``m⁰``: the memory forecast of each use in the evaluation window from the pre-action belief under the
    tail (the path the pre-action ``V`` values): per topic, the mean ``P(perform)`` on days ``1..B``, and each dated
    use's at its date."""

    model = _Model(inputs, draws, seed)
    ledger = _Ledger.zeros(model.k)
    state = model.initial()
    recorder: dict[str, Any] = {"days": int(window_days)}
    session = np.full(model.k, float(inputs.session_minutes))
    model.run_tail(state, ledger, today_minutes=session if float(inputs.session_minutes) < model.mbar else None,
                   after=np.zeros(model.k), dated_done=np.zeros((model.k, len(model.dated)), dtype=bool),
                   recorder=recorder)
    daily = recorder.get("daily") or {}
    per_topic = {topic.lo: [float(daily[day][i]) if day in daily else None for day in range(1, int(window_days) + 1)]
                 for i, topic in enumerate(inputs.topics)}
    return {"topics": per_topic, "dated": dict(recorder.get("dated") or {})}


def gain(inputs: Inputs, session_lengths: Sequence[float], *, draws: int, seed: str) -> dict[float, float]:
    """``G(x)`` (§8.6): the forecast valued uses (no attention cost) when today's session runs ``x`` minutes from
    the start under the tail, then the tail; for the price's daily seed and the frontier."""

    out: dict[float, float] = {}
    model = _Model(replace(inputs, session_minutes=0.0), draws, seed)
    for length in session_lengths:
        ledger = _Ledger.zeros(model.k)
        state = model.initial()
        if length > 0:
            model.run_tail(state, ledger, today_minutes=np.zeros(model.k), after=np.zeros(model.k),
                           dated_done=np.zeros((model.k, len(model.dated)), dtype=bool), today_target=float(length))
        else:
            model.run_tail(state, ledger, today_minutes=None, after=np.zeros(model.k),
                           dated_done=np.zeros((model.k, len(model.dated)), dtype=bool))
        # Only today's session length differs; later sessions keep the remembered minutes' load.
        out[float(length)] = float((ledger.tail_reward + ledger.terminal_reward).mean())
    return out


__all__ = [
    "Action", "baselines", "DatedUse", "EffectSlope", "Evaluation", "Inputs", "KINDS", "LESSON", "Learning", "NEW_PRACTICE",
    "OBJECTIVE_VERSION", "PRACTICE_KINDS", "PROBE", "Price", "READING", "REFERENCE_REF", "REPAIR", "REVIEW", "SEQUENCE", "STOP",
    "TAIL_VERSION", "TEACH_BACK", "TERMINAL_VERSION", "Topic", "Valued", "cutoff_for", "evaluate", "gain",
    "numeric_choice", "paired_standard_error",
]
