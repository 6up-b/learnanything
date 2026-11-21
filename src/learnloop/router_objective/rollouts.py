"""How a block is simulated: the rollouts that estimate each candidate's value ``Q̄`` under the router's objective
(spec_router_objective_v1 §3.2, §8.1), a pure function of a frozen belief.

What is optimized (the terms of a path, their sum and how a value is reported) is :mod:`objective`; this module
computes it. It imports :mod:`objective` (every path is accumulated into its ``_Ledger``, and inside one candidate's
simulation branches are compared by the ledger's ``q``) and :mod:`types` (the frozen inputs and the actions); neither
imports it. :func:`evaluate`, :func:`baselines` and :func:`gain` are the entry points: each builds a :class:`_Model`.

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

**One clock**: an action is a chronological sequence of segments (one, or a probe and its repair, or a mid-block
alternative's ordered sub-actions). Each segment charges its minutes from the session minutes it starts at, earns
the undated uses over its own interval and every dated use it crosses, both on the state before its effect, and
only then applies its effect; the tail starts at the last segment's end, and no interval before it (on any day) and
no session before it is counted again. Every draw keeps its own clock through the tail (never a batch's maximum),
and a tail session's blocks land at their ends the same way: a dated use a block's end crosses is scored on the
state before that block.

**Sampling** (§8.1). ``K`` parameter draws θ (AD's posterior on each topic's ability, the combiner's and the
effect slope's posteriors, AD's learning increments, the stop offer's acceptance), each shared across every
candidate, with **common random numbers** for outcomes, durations, uptake and return. ``Q̄`` is the mean over
draws; :func:`objective.paired_standard_error` is the precision of the top two's difference. Everything is
vectorized over the draws.

**Action interfaces** (§8.1's table): review, new practice, repair and teach-back are practice opportunities
(AD's ``γ`` at their evidence mass, FSRS's update over the rating distribution from AD's predictive, a graded
attempt that updates the belief); reading is AD's dose curve and no FSRS effect (the firewall), observing
nothing; a probe is scored **as a bundle**: on each result, the repair or no repair, whichever ``Q̄`` on the
posterior right after the probe prefers, then the tail (the branch is in the trace). Each branch's ``Q̄`` is
averaged over the belief's own world before the two are compared (every draw there from the same post-probe belief:
ability drawn from it, the believed parameters, noise independent of the true world's), so the choice is one per
result, integrates over the repair's possible outcomes and never sees the simulated repair's result or the true
path's noise; the chosen repair is simulated afterwards. A lesson is AD's ``γ`` at the lesson's learned mass (RO4's
placeholder), plus what lessons have taught AD's lesson curve beyond its seeded prior at the topic's place on its
lesson window (:class:`ad_link.LessonCurve`; zero at the prior, so the placeholder exactly until lesson data
arrive); an offer-type action is valued accepted and declined **as branches**,
``Q = p·E[R+V | acc] + (1−p)·E[R+V | dec]``; the stop offer is two branches, accepted (no more today; the next
session after a drawn return gap) and overridden (the tail's next non-stop block at the same session minutes, so
its value is never defined in terms of itself), with ``p_accept`` drawn from its Beta posterior. Durations are
sampled, never averaged: with the quadratic cost, ``E[C(m, D)] = C(m, E[D]) + κ0/(2m̄)·Var(D)``.

**The effect correction** (§8.4): ``ΔG = α_v + β_v·f(a)`` on the logit scale, ``f(a)`` the LLM's forecast
probability for ``a`` minus its forecast probability for the tail's next action (the reference row; a difference
of probabilities, never of logits), added to the action's topics after its own effect: a correction to the memory
rollout's learning effect, never a replacement. It applies only when every candidate and the reference have a
forecast; a missing one drops it for the decision.

A leaf beside numpy and the standard library: every number it reads is in :class:`types.Inputs`, handed in frozen.
"""

from __future__ import annotations

from collections.abc import Callable, Collection, Sequence
from dataclasses import dataclass, replace
import hashlib
import math
import time
from typing import Any

import numpy as np

from learnloop.router_objective.memory import Fsrs, logit, perform, sigmoid
from learnloop.router_objective.objective import Evaluation, Valued, _Ledger, _terms
from learnloop.router_objective.types import (
    LESSON,
    NEW_PRACTICE,
    PRACTICE_KINDS,
    PROBE,
    READING,
    REPAIR,
    REVIEW,
    STOP,
    Action,
    DatedUse,
    Inputs,
)
from learnloop.scheduling.fsrs import retrievability_array

TAIL_VERSION = "flat_load_adaptive_v1"
#: The reference row's ref: the tail's next action, sent to the LLM policy as a non-choosable row.
REFERENCE_REF = "tail_next"
MINUTES_PER_DAY = 1440.0
#: The follow-up batch (item 3): with ``merged_sessions`` (:func:`evaluate`, :func:`baselines`, :func:`gain`; the
#: caller passes ``[router_objective] merged_sessions`` at the batch's tag), a tail session with no repeated topic and
#: no crossable dated use is one vectorized step over its blocks' cells (:meth:`_Model._session`); off (the default,
#: below the tag), the per-block loop. The same cells, in the same order, each at its own block's end, so a fixed
#: number of draws gives the same values; but an evaluation refined until a deadline completes more draws when each
#: is faster, which can change ``Q̄`` and the tie rule (Codex review F2), so it changes serving and has its switch.
#: The follow-up batch's landing ruling R1 (``consistent_review_draw``; the caller passes ``[router_objective]
#: consistent_review_draw`` at the batch's tag): a practised topic's practice outcome is drawn from the memory model's
#: own ``P(perform)`` at that moment (the combiner over the draw's ``η`` and FSRS's ``R`` at the elapsed lag, §8.4),
#: and the belief observes it under the same likelihood, so a review FSRS calls a lapse is one the model expects. Off
#: (the default, below the tag), mvp-0.49's draw from AD's predictive alone, draw for draw. An unpractised topic's
#: first attempt and a probe's observation read AD's predictive either way (the combiner has no ``R`` for them).
REVIEW_DRAW_VERSION = "review_draw_memory_model_v1"
#: Router speed, item 1 (``held_ad_link``; the caller passes ``[router_objective] held_ad_link`` at the follow-up
#: batch's tag): R9's link evaluated once per array, its values held per role and recomputed only where the state's
#: bits changed (:meth:`_Model._linked_logit`, :meth:`_Model._link_cells`). Off (the default here, and the landing's
#: code), every read computes its own quadratures. Like ``merged_sessions``: a fixed number of draws gives the same
#: values bit for bit, but a deadline-bound evaluation completes more draws when each is faster, which can change
#: ``Q̄`` and the choice (Codex review F1 on router speed), so it changes serving, has its switch, and the switch is
#: in RO6's generator payload and the prefetch key (``router_objective_switches.FOLLOWUP_GENERATOR_SWITCHES``).


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
        # Teacher TE3b: a lesson's committed delayed checks' outcomes (their own stream: no other draw moves).
        self.commit_u = gen("noise:commitments").random((draws, 8))


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
    #: RO5: the gaps before rounding up to whole days, and the return model's slope per draw (None: no model)
    return_raw: np.ndarray | None = None
    return_b: np.ndarray | None = None


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
    #: Teacher TE3a (Codex review F3): each topic's lesson window (lessons since its last graded attempt), AD's
    #: ``(lesson, facet)`` window: a lesson advances it, a graded attempt (practice, a probe) resets it.
    lesson: np.ndarray     # (K, N)

    def copy(self) -> "_State":
        return _State(*(np.array(getattr(self, name), copy=True) for name in _STATE_FIELDS))

    def select(self, mask: np.ndarray, other: "_State") -> "_State":
        """Per draw: this state where ``mask``, else ``other``'s."""

        m = mask[:, None]
        return _State(*(np.where(m, getattr(self, name), getattr(other, name)) for name in _STATE_FIELDS))


_STATE_FIELDS = ("eta", "bel", "bel_var", "d", "s", "practiced", "last", "reading", "lesson")


class _Model:
    """One decision's rollouts: the frozen inputs, the draws, and the streams."""

    def __init__(self, inputs: Inputs, draws: int, seed: str, cutoff: float | None = None,
                 unmeasured: Collection[str] | None = None, merged_sessions: bool = False,
                 consistent_review_draw: bool = False, held_ad_link: bool = False) -> None:
        self.inputs = inputs
        self.seed = seed
        #: the follow-up batch's item 3 (module constant's note above): the tail's sessions merged when they can be
        self.merged = bool(merged_sessions)
        #: router speed, item 1 (the module's ``held_ad_link`` note): R9's link values held per role; off, every read
        #: computes its own quadratures (the follow-up batch's landing code)
        self.held = bool(held_ad_link)
        #: the follow-up batch's landing ruling R1 (:data:`REVIEW_DRAW_VERSION`'s note): a practised topic's outcome
        #: drawn from the memory model's own ``P(perform)``
        self.consistent = bool(consistent_review_draw)
        #: RO6's landing ruling R7: topics whose undated uses no randomized check could measure as of the decision;
        #: their share of the undated reward is kept apart on the same paths (``_Ledger.unmeasured``). None: not kept.
        self.unmeasured = frozenset(unmeasured) if unmeasured is not None else None
        #: RO6 (Codex re-review F3): a cutoff carried from an earlier decision (days from this one), in place of the
        #: inputs' own: every rollout (the tail's ranking, a probe's branch choice in the belief's world, the
        #: quadrature's boundaries, the end ``C + H``) then runs at it. None: the inputs' own cutoff (RO4's model).
        self.carried = float(cutoff) if cutoff is not None else None
        self._belief: "_Model | None" = None
        self.k = int(draws)
        self.index = {topic.lo: i for i, topic in enumerate(inputs.topics)}
        self.n = len(inputs.topics)
        self.fsrs = Fsrs(tuple(inputs.fsrs_weights))
        #: Landing ruling R9: AD's own predictive (None: ``σ`` on ``logit p̄``, mvp-0.49's), and each topic's ``η``
        #: mean on the scale the rollouts move it on (AD's latent ``F⁻¹(p̄)`` with the link; ``logit p̄`` without).
        self.link = inputs.ad_link
        #: router speed, item 1: the last ``(η, logit F(η))`` per role (the draws' ``η``, the belief's), compared bit
        #: for bit (:meth:`_linked_logit`); one model's, never shared across threads or decisions
        self._logit_held: dict[str, tuple[np.ndarray, np.ndarray]] = {}
        self.eta_means: list[float] = [t.eta_mean for t in inputs.topics]
        self.eta_vars: list[float] = [t.eta_var for t in inputs.topics]
        if self.link is not None and inputs.topics:
            # R10: AD's latent posterior where it was read; else the mean whose variance-integrated predictive is
            # p̄ (never a point inverse with the variance added again).
            rebuilt = self.link.inverse(sigmoid(np.array(self.eta_means)), np.array(self.eta_vars))
            self.eta_means = [float(t.eta_latent[0]) if t.eta_latent is not None else float(m)
                              for t, m in zip(inputs.topics, rebuilt, strict=True)]
            self.eta_vars = [float(t.eta_latent[1]) if t.eta_latent is not None else float(t.eta_var)
                             for t in inputs.topics]
        self.cutoff = inputs.cutoff if self.carried is None else self.carried
        self.end = self.cutoff + float(inputs.horizon_days)
        self.days = int(math.ceil(self.end))
        self.slots = max(int(inputs.tail_block_items), 1) * max(self._blocks_per_session(), 1) + 64
        self.streams = _Streams(seed, self.k, max(self.n, 1), self.days, self.slots)
        self.c = np.array([topic.undated_density for topic in inputs.topics], dtype=np.float64)
        self.c_unmeasured = (np.array([topic.undated_density if topic.lo in self.unmeasured else 0.0
                                       for topic in inputs.topics], dtype=np.float64)
                             if self.unmeasured is not None else None)
        self.mbar = max(float(inputs.price.remembered), 1e-9)
        self.kappa0 = float(inputs.price.kappa0)
        self.theta = self._draw_theta()
        self.dated = sorted(inputs.dated, key=lambda use: use.at_days)
        self.dated_weight = np.zeros(self.n)
        self.effect_on = inputs.effect is not None
        #: SG2: γ_slip's residual stream, drawn on first use (:meth:`_cause_gain`)
        self._slip_z: np.ndarray | None = None
        #: SG2: each diagnosed topic's index -> its calibrated (p_gap, p_slip, p_unknown); empty with no split
        causes = inputs.learning.causes
        self.cause_weights: dict[int, tuple[float, ...]] = (
            {self.index[lo]: tuple(float(p) for p in split) for lo, split in causes.weights.items()
             if lo in self.index} if causes is not None else {})
        #: RO5: whether the return model moved any draw's day of return (False: it dropped out of V), and a
        #: switch the stop branch's return-effect display turns it off with.
        self.return_days_moved = False
        self._return_model_off = False

    # θ ---------------------------------------------------------------------------------------------
    def _blocks_per_session(self) -> int:
        d = max(float(self.inputs.tail_block_minutes), 1e-9)
        return max(int(round(float(self.inputs.price.remembered) / d)), 1)

    def _draw_theta(self) -> _Theta:
        inputs, st = self.inputs, self.streams
        mean = np.array(self.eta_means, dtype=np.float64)
        sd = np.sqrt(np.maximum(np.array(self.eta_vars, dtype=np.float64), 0.0))
        eta = mean[None, :] + sd[None, :] * st.eta_z[:, : self.n]
        # The combiner's draws on (a0, aA, aR), in its own form's parameters (landing ruling R6: monotone at the tag)
        coef = inputs.combiner.coefficients(st.coef_z)
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
        return_b = None
        if inputs.return_slope is not None:
            # RO5: the return model's slope, a parameter draw (its own stream, so no other draw moves).
            bm, bv = inputs.return_slope
            z = np.random.default_rng(_seed_int(self.seed, "theta:return_slope")).standard_normal(self.k)
            return_b = float(bm) + math.sqrt(max(float(bv), 0.0)) * z
        return _Theta(eta=eta, coef=coef, gamma=gamma, gbar=gbar, effect=effect, stop_accept=accept,
                      return_days=return_days, return_raw=gaps[picks], return_b=return_b)

    def initial(self) -> _State:
        inputs = self.inputs
        k, n = self.k, self.n

        def column(values: Sequence[float]) -> np.ndarray:
            return np.broadcast_to(np.asarray(values, dtype=np.float64)[None, :], (k, n)).copy()

        topics = inputs.topics
        return _State(
            eta=self.theta.eta.copy(),
            bel=column(self.eta_means),
            bel_var=column([max(v, 1e-12) for v in self.eta_vars]),
            d=column([t.difficulty for t in topics]),
            s=column([t.stability for t in topics]),
            practiced=np.broadcast_to(np.array([t.practiced for t in topics], dtype=bool)[None, :], (k, n)).copy(),
            last=column([-t.elapsed_days for t in topics]),
            reading=column([t.reading_count for t in topics]),
            lesson=column([float(inputs.learning.lesson.positions.get(t.lo, 0.0)) if inputs.learning.lesson
                           is not None else 0.0 for t in topics]),
        )

    # the memory forecast ---------------------------------------------------------------------------
    def performance(self, state: _State, at: float | np.ndarray, *, belief: bool = False) -> np.ndarray:
        """``P(perform)`` per draw and topic at time ``at`` (a scalar, or one time per draw)."""

        when = np.asarray(at, dtype=np.float64)
        if when.ndim == 1:
            when = when[:, None]
        r = retrievability_array(state.s, when - state.last, self.fsrs.weights)
        eta = state.bel if belief else state.eta
        if self.link is not None:
            # R9: the combiner's η input is AD's predictive on the logit scale, logit F(η) (``logit p̄`` at the start),
            # R11: its own stable logit, not FSRS's clipped one
            eta = self._linked_logit(eta, "bel" if belief else "eta") if self.held else self.link.logit_p(eta)
        return perform(self.theta.coef, eta, r, state.practiced)

    def _link_compute(self, x: np.ndarray, slope: bool) -> tuple[np.ndarray, np.ndarray | None, np.ndarray]:
        """``F(η)``, ``dF/dη`` (``slope``) and ``logit F(η)`` elementwise, from one quadrature."""

        assert self.link is not None
        f, df = self.link.quadrature(x, slope=slope)
        return f, df, self.link.logit_p_from(x, f)

    def _linked_logit(self, eta: np.ndarray, role: str) -> np.ndarray:
        """``logit F(η)`` elementwise (:meth:`AdLink.logit_p`), recomputed only where ``η`` changed since this role's
        last call (router speed, item 1). The tail reads ``P(perform)`` several times a day on a state its sessions
        change in a few cells, so the quadrature runs on the changed cells alone; the comparison is of the bits,
        so every element is exactly what the full call gives (the function is elementwise), whatever state, copy or
        candidate the call is on. The role's ``F`` (and the belief's ``F'``) are held too, for :meth:`_link_cells`."""

        x = np.asarray(eta, dtype=np.float64)
        slope = role == "bel"
        held = self._logit_held.get(role)
        if held is None or held[0].shape != x.shape:
            f, df, out = self._link_compute(x, slope)
        else:
            changed = x.view(np.int64) != held[0].view(np.int64)
            if not changed.any():
                return held[3]
            f, df, out = (np.array(part, copy=True) if part is not None else None for part in held[1:])
            f[changed], part_df, out[changed] = self._link_compute(x[changed], slope)
            if df is not None:
                df[changed] = part_df
        for part in (f, df, out):
            if part is not None:
                part.flags.writeable = False
        self._logit_held[role] = (np.array(x, copy=True), f, df, out)
        return out

    def _link_cells(self, x: np.ndarray, role: str, cells: tuple[Any, Any] | None, slope: bool
                    ) -> tuple[np.ndarray, np.ndarray | None, np.ndarray]:
        """``F``, ``F'`` (``slope``) and ``logit F`` at the cells ``(rows, cols)`` whose ``η`` is ``x``: the role's held
        values where the cell's bits are the ones held (:meth:`_linked_logit`'s), one quadrature over the rest. A
        merged session practises cells its ranking just read, so it computes nothing here (router speed, item 1)."""

        held = self._logit_held.get(role)
        if cells is None or held is None or (slope and held[2] is None):
            return self._link_compute(x, slope)
        hit = held[0][cells].view(np.int64) == x.view(np.int64)
        f, out = held[1][cells], held[3][cells]
        df = held[2][cells] if slope else None
        miss = ~hit
        if miss.any():
            f_miss, df_miss, out_miss = self._link_compute(x[miss], slope)
            f[miss], out[miss] = f_miss, out_miss
            if df is not None:
                df[miss] = df_miss
        return f, df, out

    def cost(self, start: np.ndarray, minutes: np.ndarray) -> np.ndarray:
        """``∫[m, m+d] κ(u) du = κ0·((m+d)² − m²)/(2m̄)``."""

        return self.kappa0 * ((start + minutes) ** 2 - start ** 2) / (2.0 * self.mbar)

    # effects ---------------------------------------------------------------------------------------
    def _graded(self, eta: np.ndarray, bel: np.ndarray, bel_var: np.ndarray, stability: np.ndarray,
                practiced: np.ndarray, elapsed: np.ndarray, coef: np.ndarray, u: np.ndarray,
                cells: tuple[Any, Any] | None = None) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """A graded attempt, elementwise (``coef``: each element's combiner draw, shaped ``(M, 3)``): its result,
        then the belief's one-step Laplace update on it (mean, variance; before the learning increment).

        mvp-0.49 (``consistent`` off): the result is drawn from AD's predictive ``σ(η)`` and the belief predicts it
        with ``σ(bel)``. Landing ruling R1 (on): a practised topic's result is drawn from the memory model's own
        ``P(perform)`` at this moment, ``σ(a0 + aA·η + aR·(logit R − η))`` with ``R`` FSRS's at the elapsed lag
        (:func:`memory.perform`'s formula), and the belief observes it under the same likelihood (its prediction at
        ``bel``, its slope in ``η`` ``aA − aR``), so the belief does not read a memory effect as ability.

        Landing ruling R9 (``self.link``): AD's predictive is ``F(η)``, so ``η`` enters as ``logit F(η)`` and every
        slope carries its derivative (:meth:`_graded_linked`; ``cells``: where in the state the elements are, which
        only that path reads, to reuse what :meth:`performance` computed on the same bits)."""

        if self.link is not None:
            return self._graded_linked(eta, bel, bel_var, stability, practiced, elapsed, coef, u, cells)
        if not self.consistent:
            good = u < sigmoid(eta)
            p_bel = sigmoid(bel)
            var = 1.0 / (1.0 / bel_var + p_bel * (1 - p_bel))
            return good, bel + var * (good.astype(np.float64) - p_bel), var
        a0, a_eta, a_r = coef[:, 0], coef[:, 1], coef[:, 2]
        lr = logit(retrievability_array(stability, elapsed, self.fsrs.weights))
        p_true = np.where(practiced, sigmoid(a0 + a_eta * eta + a_r * (lr - eta)), sigmoid(eta))
        p_bel = np.where(practiced, sigmoid(a0 + a_eta * bel + a_r * (lr - bel)), sigmoid(bel))
        slope = np.where(practiced, a_eta - a_r, 1.0)
        good = u < p_true
        var = 1.0 / (1.0 / bel_var + slope * slope * p_bel * (1 - p_bel))
        return good, bel + var * slope * (good.astype(np.float64) - p_bel), var

    def _graded_linked(self, eta: np.ndarray, bel: np.ndarray, bel_var: np.ndarray, stability: np.ndarray,
                       practiced: np.ndarray, elapsed: np.ndarray, coef: np.ndarray, u: np.ndarray,
                       cells: tuple[Any, Any] | None = None) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """:meth:`_graded` with AD's own predictive (R9): ``ẽ = logit F(η)`` where ``σ(η)`` stood. Without R1's draw,
        every result is drawn from ``F(η)``; with it, a practised topic's from the combiner over ``ẽ`` and ``R``.
        The belief's Laplace step uses the same prediction at ``bel`` and its slope in ``η`` (``dẽ/dη``, times
        ``aA − aR`` for a practised topic under R1's draw). Landing ruling R11: AD's own probability is drawn from
        directly (``F(η)``, never ``σ`` of a clipped logit); only the combiner reads ``ẽ``, its stable logit; FSRS's
        retrievability keeps FSRS's clip.

        Router speed, item 1: ``cells`` (the ``(rows, cols)`` of the state the elements are, or None) lets the
        quadrature be read from the values :meth:`performance` already computed on the same bits (:meth:`_link_cells`);
        it was four quadratures a call, each element's ``F``, ``F'`` and logit the bits those gave. With
        ``held_ad_link`` off, those four quadratures (the landing's code)."""

        assert self.link is not None
        if self.held:
            eta, bel = np.asarray(eta, dtype=np.float64), np.asarray(bel, dtype=np.float64)
            f_true, _df, e = self._link_cells(eta, "eta", cells, False)
            f_bel, df_bel, _eb = self._link_cells(bel, "bel", cells, True)
            assert df_bel is not None
            eb, deb = self.link.logit_and_slope_from(bel, f_bel, df_bel)
        else:
            f_true, f_bel = self.link.p(eta), self.link.p(bel)
            eb, deb = self.link.logit_and_slope(bel)
            if self.consistent:
                e, _de = self.link.logit_and_slope(eta)
        if self.consistent:
            a0, a_eta, a_r = coef[:, 0], coef[:, 1], coef[:, 2]
            lr = logit(retrievability_array(stability, elapsed, self.fsrs.weights))
            p_true = np.where(practiced, sigmoid(a0 + a_eta * e + a_r * (lr - e)), f_true)
            p_bel = np.where(practiced, sigmoid(a0 + a_eta * eb + a_r * (lr - eb)), f_bel)
            slope = np.where(practiced, (a_eta - a_r) * deb, deb)
        else:
            p_true, p_bel, slope = f_true, f_bel, deb
        good = u < p_true
        var = 1.0 / (1.0 / bel_var + slope * slope * p_bel * (1 - p_bel))
        return good, bel + var * slope * (good.astype(np.float64) - p_bel), var

    def _cause_gain(self, lo: int, mass: float) -> tuple[np.ndarray, float] | None:
        """SG2: a lesson's or a repair's learning on topic ``lo`` at evidence mass ``mass``, per draw and as believed,
        when the topic's miss has a diagnosis: ``(p_gap·γ_gap + p_slip·γ_slip + p_unknown·γ)·mass``, the slopes drawn
        from their joint posterior (:class:`CauseSplit`). None: the topic keeps ``γ`` (the predecessor's expression,
        untouched)."""

        split = self.cause_weights.get(lo)
        causes = self.inputs.learning.causes
        if split is None or causes is None:
            return None
        p_gap, p_slip, p_unknown = split
        z = self.streams.gamma_z
        gap_var, slip_var = max(causes.gap[1], 0.0), max(causes.slip[1], 0.0)
        gap = causes.gap[0] + math.sqrt(gap_var) * z
        if self._slip_z is None:
            # γ_slip's own stream (a parameter draw; no other stream moves), drawn once per model.
            self._slip_z = np.random.default_rng(_seed_int(self.seed, "theta:gamma_slip")).standard_normal(self.k)
        regression = causes.cov / gap_var if gap_var else 0.0
        residual = math.sqrt(max(slip_var - regression * causes.cov, 0.0))
        slip = causes.slip[0] + regression * (gap - causes.gap[0]) + residual * self._slip_z
        true = (p_gap * gap + p_slip * slip + p_unknown * self.theta.gamma) * mass
        believed = (p_gap * causes.gap[0] + p_slip * causes.slip[0]
                    + p_unknown * float(self.inputs.learning.gamma[0])) * mass
        return true, believed

    def _practice(self, state: _State, lo: int, at: np.ndarray, u: np.ndarray, mask: np.ndarray, mass: float,
                  gain: tuple[np.ndarray, float] | None = None) -> None:
        """One practice opportunity on topic ``lo`` for the draws in ``mask``: a graded attempt. ``gain`` (SG2, a
        repair on a diagnosed topic): its learning per draw and as believed, in place of ``γ·mass``."""

        elapsed = at - state.last[:, lo]
        # The belief observes the graded attempt (a one-step Laplace update), then learns as the model predicts.
        good, bel, var = self._graded(state.eta[:, lo], state.bel[:, lo], state.bel_var[:, lo], state.s[:, lo],
                                      state.practiced[:, lo], elapsed, self.theta.coef, u,
                                      cells=(np.arange(self.k), lo))
        d, s = self.fsrs.review(state.d[:, lo], state.s[:, lo], state.practiced[:, lo], elapsed, good)
        gm = float(self.inputs.learning.gamma[0])
        state.d[:, lo] = np.where(mask, d, state.d[:, lo])
        state.s[:, lo] = np.where(mask, s, state.s[:, lo])
        state.practiced[:, lo] = np.where(mask, True, state.practiced[:, lo])
        state.last[:, lo] = np.where(mask, at, state.last[:, lo])
        if gain is None:
            state.eta[:, lo] = np.where(mask, state.eta[:, lo] + self.theta.gamma * mass, state.eta[:, lo])
            state.bel[:, lo] = np.where(mask, bel + gm * mass, state.bel[:, lo])
        else:
            state.eta[:, lo] = np.where(mask, state.eta[:, lo] + gain[0], state.eta[:, lo])
            state.bel[:, lo] = np.where(mask, bel + gain[1], state.bel[:, lo])
        state.bel_var[:, lo] = np.where(mask, var, state.bel_var[:, lo])
        state.lesson[:, lo] = np.where(mask, 0.0, state.lesson[:, lo])  # a graded attempt closes the lesson window

    def _observe(self, state: _State, lo: int, u: np.ndarray, mask: np.ndarray,
                 observed: np.ndarray | None = None) -> np.ndarray:
        """A probe's observation: the belief's update, nothing direct. Returns the result per draw (``observed``:
        the result given, for valuing the branches on one result). With R9's link, AD's own ``F``."""

        if self.link is not None and not self.held:
            # ``held_ad_link`` off: the landing's code, a quadrature per read
            _eb, deb = self.link.logit_and_slope(state.bel[:, lo])
            good = (u < self.link.p(state.eta[:, lo]) if observed is None
                    else np.asarray(observed, dtype=bool))
            p_bel = self.link.p(state.bel[:, lo])
            var = 1.0 / (1.0 / state.bel_var[:, lo] + deb * deb * p_bel * (1 - p_bel))
            bel = state.bel[:, lo] + var * deb * (good.astype(np.float64) - p_bel)
            state.bel[:, lo] = np.where(mask, bel, state.bel[:, lo])
            state.bel_var[:, lo] = np.where(mask, var, state.bel_var[:, lo])
            state.lesson[:, lo] = np.where(mask, 0.0, state.lesson[:, lo])  # TE3a: a probe is a graded attempt too
            return good
        if self.link is not None:
            # Router speed, item 1: the quadratures read from what performance() computed on the same bits where it
            # can (each element's bits as before).
            cells = (np.arange(self.k), lo)
            f_true, _df, _e = self._link_cells(np.asarray(state.eta[:, lo], dtype=np.float64), "eta", cells, False)
            p_bel, df_bel, _l = self._link_cells(np.asarray(state.bel[:, lo], dtype=np.float64), "bel", cells, True)
            assert df_bel is not None
            _eb, deb = self.link.logit_and_slope_from(state.bel[:, lo], p_bel, df_bel)
            good = (u < f_true if observed is None else np.asarray(observed, dtype=bool))
            var = 1.0 / (1.0 / state.bel_var[:, lo] + deb * deb * p_bel * (1 - p_bel))
            bel = state.bel[:, lo] + var * deb * (good.astype(np.float64) - p_bel)
            state.bel[:, lo] = np.where(mask, bel, state.bel[:, lo])
            state.bel_var[:, lo] = np.where(mask, var, state.bel_var[:, lo])
            state.lesson[:, lo] = np.where(mask, 0.0, state.lesson[:, lo])  # TE3a: a probe is a graded attempt too
            return good
        good = u < sigmoid(state.eta[:, lo]) if observed is None else np.asarray(observed, dtype=bool)
        p_bel = sigmoid(state.bel[:, lo])
        var = 1.0 / (1.0 / state.bel_var[:, lo] + p_bel * (1 - p_bel))
        bel = state.bel[:, lo] + var * (good.astype(np.float64) - p_bel)
        state.bel[:, lo] = np.where(mask, bel, state.bel[:, lo])
        state.bel_var[:, lo] = np.where(mask, var, state.bel_var[:, lo])
        state.lesson[:, lo] = np.where(mask, 0.0, state.lesson[:, lo])  # a probe is a graded attempt too
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
                # SG2: a repair on a diagnosed topic learns by the miss's cause (None everywhere else).
                gain = self._cause_gain(lo, float(action.mass)) if action.kind == REPAIR else None
                self._practice(state, lo, at, u[:, slot % u.shape[1]], mask, float(action.mass), gain)
        elif action.kind == LESSON:
            # RO4's placeholder: AD's γ at the lesson's learned mass (as the decision read both).
            gm, gv = float(self.inputs.learning.gamma[0]), float(self.inputs.learning.gamma[1])
            curve = self.inputs.learning.lesson
            for lo in dict.fromkeys(los):
                split = self._cause_gain(lo, float(action.mass))
                if split is None:
                    true = self.theta.gamma * action.mass
                    believed = gm * action.mass
                else:
                    # SG2: the slope by the miss's cause, at the same mass (TE3a's learned shift then adds as before).
                    true, believed = split
                if curve is not None:
                    # Teacher TE3a (Codex review F2, F3): plus what lessons taught AD's lesson curve beyond its
                    # seeded prior, one landed dose from the topic's place on its lesson window (carried through
                    # the rollout): the step's mean shift on both, and its variance change on the draw's spread
                    # along γ's stream. At the prior both are exactly zero: the placeholder, draw for draw. With the
                    # follow-up batch's AD link (R9, R10) ``η`` is AD's own latent ability, the scale the curve is
                    # fitted on, so the shift adds where AD adds it; without it, on ``logit p̄``, TE3a's own read.
                    n = state.lesson[:, lo]
                    shift, dvar = curve.deviation(n, self.inputs.learning.dose_scales)
                    base = max(gv, 0.0) * float(action.mass) ** 2
                    spread = np.sqrt(np.maximum(base + dvar, 0.0)) - math.sqrt(base)
                    true = true + shift + spread * self.streams.gamma_z
                    believed = believed + shift
                    state.lesson[:, lo] = np.where(mask, n + 1.0, n)
                state.eta[:, lo] = np.where(mask, state.eta[:, lo] + true, state.eta[:, lo])
                state.bel[:, lo] = np.where(mask, state.bel[:, lo] + believed, state.bel[:, lo])
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
        """Practice opportunities at ``(draw, cols[draw, j])`` where ``active``, at each draw's own time ``at`` (one
        per draw, or one per cell, shaped as ``cols``): each row's topics are distinct, so the updates are one
        vectorized step (:meth:`_practice`'s, elementwise)."""

        rows = np.broadcast_to(np.arange(self.k)[:, None], cols.shape)
        r, c = rows[active], cols[active]
        if r.size == 0:
            return
        times = np.asarray(at, dtype=np.float64)
        when = times[active] if times.ndim == 2 else np.broadcast_to(times, (self.k,))[r]
        eta = state.eta[r, c]
        elapsed = when - state.last[r, c]
        good, bel, var = self._graded(eta, state.bel[r, c], state.bel_var[r, c], state.s[r, c], state.practiced[r, c],
                                      elapsed, self.theta.coef[r], u[active], cells=(r, c))
        d, s = self.fsrs.review(state.d[r, c], state.s[r, c], state.practiced[r, c], elapsed, good)
        gm = float(self.inputs.learning.gamma[0])
        state.d[r, c] = d
        state.s[r, c] = s
        state.practiced[r, c] = True
        state.last[r, c] = when
        state.eta[r, c] = eta + self.theta.gamma[r]
        state.bel[r, c] = bel + gm
        state.bel_var[r, c] = var
        state.lesson[r, c] = 0.0

    def _session(self, state: _State, ledger: _Ledger, at: np.ndarray, mask: np.ndarray, start: np.ndarray, day: int,
                 *, past_cutoff: bool, target: float | None = None,
                 before_block: Callable[[np.ndarray, np.ndarray], None] | None = None,
                 crosses: Callable[[np.ndarray, np.ndarray], bool] | None = None) -> None:
        """A tail session from ``start`` session minutes to ``m̄`` (or ``target``: today's, for ``G``), in blocks
        of ``d̄`` with ``ī`` practice opportunities each, for the draws in ``mask``, each draw on its own clock from
        ``at`` (days, per draw; never a batch's maximum, Codex re-review F12). The session's topics are ranked once
        on the belief at its start (adaptive to the belief), the top ones practised in turn; its cost is the κ
        integral from ``start`` over its blocks' minutes. Each block's effect lands at its end, as a segment's
        does, and ``before_block(end, active)`` runs first, so a dated use the block's end crosses is scored on
        the state before it. ``crosses(last_end, active)``: whether a dated use ``before_block`` scores could be
        crossed by any block's end up to ``last_end`` (None: ``before_block`` scores nothing)."""

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
        total = int(blocks.max())
        if (self.merged and total * items <= self.n
                and (crosses is None or not crosses(when + blocks * d / MINUTES_PER_DAY, blocks > 0))):
            # The follow-up batch (item 3): with no topic repeated in the session (the ranking taken once, its
            # slots fewer than the topics) and no dated use any block's end could cross, the blocks touch distinct
            # cells and ``before_block`` scores nothing, so the session is one vectorized step over every block's
            # cells, each at its own block's end: the per-block loop below, cell for cell.
            slots = np.arange(total * items)
            block_of = slots // items
            cols = order[:, :total * items]
            ends = when[:, None] + (block_of[None, :] + 1) * d / MINUTES_PER_DAY
            self._practice_batch(state, cols, ends, u[:, slots % u.shape[1]], blocks[:, None] > block_of[None, :])
            return
        for block in range(total):
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
                 recorder: dict[str, Any] | None = None,
                 commitments: Sequence[tuple[int, np.ndarray]] = (),
                 on_return: Callable[[int, np.ndarray, Callable[[np.ndarray, np.ndarray], None]],
                                     tuple[np.ndarray, np.ndarray]] | None = None) -> None:
        """The tail from the action's end ``after`` (per draw): today's session continues to ``m̄`` unless
        ``today_minutes`` is None (the session ended), then a session after each return gap until ``C + H``, a
        fresh gap from the learner's own distribution after every session's end (F4). Nothing before ``after`` is
        counted on any day, and no session starts before it (F3). ``dated_done``: per draw and dated use, whether
        it was already scored (crossed during the action).

        ``commitments`` (teacher TE3b): ``(topic index, due time per draw)`` of a lesson's delayed checks, each a
        graded attempt on its topic at the first day boundary at or past its due time, before that day's session
        (none: the tail as before, draw for draw).

        ``on_return(day, returning, before_block)`` (the check-credit path, :mod:`check_value`; None everywhere else):
        on each day some draws return, what happens at the start of their session before the tail's blocks; it returns
        the session minutes and the time (per draw) the blocks then start at. None: they start at minute 0 of the day,
        as before."""

        k = self.k
        after = np.broadcast_to(np.asarray(after, dtype=np.float64), (k,)).copy()
        done = np.array(dated_done, dtype=bool, copy=True)
        checks = [(int(lo), np.broadcast_to(np.asarray(due, dtype=np.float64), (k,)), np.zeros(k, dtype=bool))
                  for lo, due in commitments]
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

        def crosses(last_end: np.ndarray, active: np.ndarray) -> bool:
            # Whether before_block could score anything in a session whose blocks end by last_end (per draw).
            return any(bool((active & ~done[:, index] & (use.at_days <= last_end + 1e-12)).any())
                       for index, use in enumerate(self.dated))

        if today_minutes is not None:
            today = after < 1.0
            if today.any():
                self._session(state, ledger, after, today, today_minutes, 0, past_cutoff=False, target=today_target,
                              before_block=before_block, crosses=crosses)
        rows = np.arange(k)
        gaps = self.theta.return_days
        # The session that ended at the action's end (today's) is the 0th; its gap is column 0.
        ended = np.zeros(k, dtype=int)
        first_gap = gaps[:, 0]
        if self.theta.return_b is not None and not self._return_model_off:
            # RO5 §9 item 1: today's session's gap follows its length (the tail's later sessions run m̄ minutes,
            # where the shift is one).
            if today_minutes is None:
                ended_at = np.full(k, float(self.inputs.session_minutes))
            else:
                start = np.broadcast_to(np.asarray(today_minutes, dtype=np.float64), (k,))
                d = float(self.inputs.tail_block_minutes)
                goal = self.mbar if today_target is None else float(today_target)
                ended_at = start + (np.ceil(np.maximum(goal - start, 0.0) / d - 1e-9) * d if d > 0 and self.n else 0.0)
            shift = np.exp(self.theta.return_b * (ended_at - self.mbar) / self.mbar)
            first_gap = np.maximum(np.ceil(self.theta.return_raw[:, 0] * shift - 1e-9), 1.0)
            self.return_days_moved = bool(np.any(first_gap != gaps[:, 0])) or self.return_days_moved
        next_session = np.floor(after) + first_gap
        pending = list(enumerate(self.dated))
        boundaries = sorted({0.0, self.cutoff, self.end, *[float(j) for j in range(1, self.days + 1)]})
        boundaries = [b for b in boundaries if b <= self.end + 1e-12]
        for day in range(0, self.days + 1):
            day_start = float(day)
            for slot, (lo, due, taken) in enumerate(checks):
                # TE3b: a committed delayed check, answered at the first day boundary at or past its date.
                hit = ~taken & (due <= day_start + 1e-9) if day >= 1 else np.zeros(k, dtype=bool)
                if hit.any():
                    self._practice(state, lo, np.full(k, day_start), self.streams.commit_u[:, slot % 8], hit, 1.0)
                    taken |= hit
            if day >= 1:
                mask = (next_session <= day_start + 1e-9) & (after <= day_start + 1e-9)
                if mask.any():
                    start, began = ((np.zeros(k), np.full(k, day_start)) if on_return is None
                                    else on_return(day, mask, before_block))
                    self._session(state, ledger, began, mask, start, day,
                                  past_cutoff=day_start >= self.cutoff - 1e-12, before_block=before_block,
                                  crosses=crosses)
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
            for a, b in zip(edges[:-1], edges[1:], strict=False):
                width = np.maximum(b - np.maximum(after, a), 0.0)
                if not (width > 0).any():
                    continue
                p = self.performance(state, (a + b) / 2)
                reward = (p * self.c[None, :]).sum(axis=1) * width
                if a >= self.cutoff - 1e-12:
                    ledger.terminal_reward += reward
                else:
                    ledger.tail_reward += reward
                if self.c_unmeasured is not None:
                    ledger.unmeasured += (p * self.c_unmeasured[None, :]).sum(axis=1) * width
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
        performance = self.performance(state, start)
        rate = (performance * self.c[None, :]).sum(axis=1)
        ledger.undated_action += rate * np.maximum(np.minimum(end, self.cutoff) - start, 0.0)
        ledger.terminal_reward += rate * np.maximum(np.minimum(end, self.end) - np.maximum(start, self.cutoff), 0.0)
        if self.c_unmeasured is not None:
            ledger.unmeasured += (performance * self.c_unmeasured[None, :]).sum(axis=1) * (
                np.maximum(np.minimum(end, self.cutoff) - start, 0.0)
                + np.maximum(np.minimum(end, self.end) - np.maximum(start, self.cutoff), 0.0))
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
        self._tail(state, ledger, action, at=at, spent=spent, dated_done=dated_done)
        return ledger, effect_state, spent

    def _tail(self, state: _State, ledger: _Ledger, action: Action, *, at: np.ndarray, spent: np.ndarray,
              dated_done: np.ndarray) -> None:
        """The tail after an action's last segment, with the action's committed checks."""

        if action.checks:
            raise ValueError(_TYPED_CHECKS)
        # TE3b: a lesson's delayed checks, each at its date after the action's end (none: the tail as before).
        commitments = [(self.index[lo], at + float(days)) for lo, days in action.commitments if lo in self.index]
        self.run_tail(state, ledger, today_minutes=float(self.inputs.session_minutes) + spent, after=at,
                      dated_done=dated_done, commitments=commitments)

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

        self._screen(action)
        extra: dict[str, Any] = {}
        if action.kind == STOP:
            self.return_days_moved = False
            accepted = self._stop_accepted()
            moved = self.return_days_moved
            overridden, _state, _minutes = self._do(self.tail_action(), stream=1)
            self.return_days_moved = moved
            p = self.theta.stop_accept
            extra["branches"] = {"accepted": float(accepted.q.mean()), "overridden": float(overridden.q.mean()),
                                 "p_accept": float(p.mean())}
            if self.theta.return_b is not None:
                # RO5 §9 item 1: the return effect, the return model's difference to stopping now (display only:
                # it is already inside the accepted branch's transition, never added).
                self._return_model_off = True
                try:
                    without = self._stop_accepted()
                finally:
                    self._return_model_off = False
                extra["return_effect"] = float(accepted.q.mean() - without.q.mean())
                extra["return_model"] = ("active" if self.return_days_moved else
                                         "dropped: the day of return is the same under every draw (attendance "
                                         "near-deterministic on the daily grid)")
            return _Ledger.mix(p, accepted, overridden), extra
        if action.accept is not None:
            a, b = action.accept
            p = _beta_draw(self.streams.offer_u, float(a), float(b))
            accepted, _state, _minutes = self._do(replace(action, accept=None))
            if action.declined is not None:
                declined, _s2, _m2 = self._do(action.declined, stream=1)
            else:
                declined, _s2, _m2 = self._do(self.tail_action(), stream=1) \
                    if float(self.inputs.session_minutes) < self.mbar else (self._stop_accepted(), None, None)
            extra["branches"] = {"accepted": float(accepted.q.mean()), "declined": float(declined.q.mean()),
                                 "p_accept": float(p.mean())}
            if action.kind == LESSON:
                # TE3b (spec_teacher_v1 rev 5 §15.1a): each branch's own terms for the trace (the accepted branch's
                # κ integral of the lesson's minutes, E[V(x′)] with its delayed checks, T_C); display, never added.
                extra["branch_terms"] = {"accepted": _terms(accepted, self), "declined": _terms(declined, self),
                                         "p_accept_sd": float(p.std())}
            return _Ledger.mix(p, accepted, declined), extra
        if action.kind == PROBE:
            return self._probe(action)
        ledger, _state, _minutes = self._do(action)
        return ledger, extra

    def _screen(self, action: Action) -> None:
        """Refuse what this path does not price."""

        if _carries_diagnostic(action):
            # Priced here it would be a binary-ability probe with its hypotheses ignored, a value no caller can tell
            # from the right one.
            raise ValueError("a diagnostic payload is priced by diagnostic_value.evaluate_probe, not the rollouts")
        if _carries(action, lambda part: bool(part.checks)):
            # Priced here the checks would vanish (this path reads only the untyped commitments): a lesson worth less
            # than its committed checks, silently.
            raise ValueError(_TYPED_CHECKS)

    def _belief_model(self) -> "_Model":
        """The belief's own world for a probe's branch choice: the believed parameters (each posterior's mean, no
        parameter draw), and noise streams of its own, independent of the true world's, so a choice made in it
        integrates over outcomes it cannot know (F2)."""

        if self._belief is None:
            inputs, learning = self.inputs, self.inputs.learning
            zero = ((0.0, 0.0), (0.0, 0.0))
            # TE3a: the lesson curve's means only (no variance change on a draw-free spread).
            lesson = (replace(learning.lesson, cov=zero, prior_cov=zero) if learning.lesson is not None else None)
            believed = replace(
                inputs,
                combiner=inputs.combiner.at_mean(),
                learning=replace(learning, gamma=(learning.gamma[0], 0.0),
                                 gbar=((learning.gbar[0][0], 0.0), (learning.gbar[1][0], 0.0)), lesson=lesson,
                                 # SG2: the cause slopes' means only, as γ's (None stays None).
                                 causes=learning.causes.at_mean() if learning.causes is not None else None),
                effect=None, stop_accept=(1.0, 1.0))
            self._belief = _Model(believed, self.k, f"{self.seed}:belief", cutoff=self.carried,
                                  merged_sessions=self.merged, consistent_review_draw=self.consistent,
                                  held_ad_link=self.held)
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


def _carries_diagnostic(action: Action | None) -> bool:
    if action is None:
        return False
    return (action.diagnostic is not None or _carries_diagnostic(action.repair) or _carries_diagnostic(action.declined)
            or any(_carries_diagnostic(step) for step in action.steps))


def _carries(action: Action | None, test: Callable[[Action], bool]) -> bool:
    """Whether ``action``, its repair, its declined branch or any of its steps passes ``test``."""

    if action is None:
        return False
    return (test(action) or _carries(action.repair, test) or _carries(action.declined, test)
            or any(_carries(step, test) for step in action.steps))


_TYPED_CHECKS = "typed committed checks are priced by check_value.evaluate, not the rollouts"


# -- the public evaluation -----------------------------------------------------------------------------


def evaluate(inputs: Inputs, actions: Sequence[Action], *, draws: int, seed: str, max_draws: int | None = None,
             keep_going: Callable[[], bool] | None = None, deadline: float | None = None,
             clock: Callable[[], float] = time.monotonic,
             on_complete: Callable[[Evaluation], None] | None = None,
             cutoff: float | None = None, unmeasured: Collection[str] | None = None,
             merged_sessions: bool = False, consistent_review_draw: bool = False,
             held_ad_link: bool = False) -> Evaluation:
    """``Q`` for every action (and the reference row) under ``draws`` θ draws, adding batches of ``draws`` more
    while ``keep_going()`` holds, up to ``max_draws``, and never past ``deadline`` (``clock``'s). An evaluation
    that could not finish its first batch by the deadline is ``complete = False``; a refinement the deadline cuts
    short returns the latest complete batch (F7). ``on_complete`` sees each complete batch as it finishes.

    ``cutoff`` (RO6; None: the inputs' own ``C``): the cutoff every rollout runs at, in days from the decision, for
    the value of this state at an earlier decision's carried cutoff (§3.2; Codex re-review F3). ``unmeasured``
    (RO6's landing ruling R7; None: not kept): topics whose share of each ``Q`` is kept apart on the same paths
    (``terms.unmeasured_reward``), so the measurable part ``q − unmeasured_reward`` decomposes by term exactly;
    ``q`` itself is unchanged. ``merged_sessions`` (the follow-up batch's item 3; False: mvp-0.49's per-block loop):
    the tail's sessions merged where they can be, faster, so a deadline admits more refinement batches.
    ``consistent_review_draw`` (the batch's landing ruling R1; False: mvp-0.49's draw): a practised topic's practice
    outcome drawn from the memory model's own ``P(perform)`` (:data:`REVIEW_DRAW_VERSION`). ``held_ad_link`` (router
    speed, item 1; False: the landing's quadratures): R9's link values held per role, the same values per draw, faster,
    so a deadline admits more refinement batches."""

    options = {"merged_sessions": merged_sessions, "consistent_review_draw": consistent_review_draw,
               "held_ad_link": held_ad_link}
    return _evaluate(lambda total: _Model(inputs, total, seed, cutoff=cutoff, unmeasured=unmeasured, **options),
                     actions, draws=draws, seed=seed, max_draws=max_draws, keep_going=keep_going, deadline=deadline,
                     clock=clock, on_complete=on_complete)


def _evaluate(model_for: Callable[[int], _Model], actions: Sequence[Action], *, draws: int, seed: str,
              max_draws: int | None, keep_going: Callable[[], bool] | None, deadline: float | None,
              clock: Callable[[], float], on_complete: Callable[[Evaluation], None] | None) -> Evaluation:
    """:func:`evaluate`'s loop over the model ``model_for(draws)`` builds (each refinement a fresh one)."""

    started = clock()
    total = int(draws)
    limit = int(max_draws or draws)
    model = model_for(total)
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
                               terms=_terms(ledger, model), extra=extra, choosable=action.choosable))
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
        model = model_for(total)
    if latest is not None:
        return replace(latest, elapsed_ms=int(round((clock() - started) * 1000)))
    return Evaluation(valued=(), draws=model.k, cutoff=model.cutoff, seed=seed,
                      elapsed_ms=int(round((clock() - started) * 1000)), complete=False, reference=None)


def baselines(inputs: Inputs, window_days: int, *, draws: int, seed: str,
              merged_sessions: bool = False, consistent_review_draw: bool = False,
              held_ad_link: bool = False) -> dict[str, Any]:
    """§8.7's ``m⁰``: the memory forecast of each use in the evaluation window from the pre-action belief under the
    tail (the path the pre-action ``V`` values): per topic, the mean ``P(perform)`` on days ``1..B``, and each dated
    use's at its date."""

    model = _Model(inputs, draws, seed, merged_sessions=merged_sessions, consistent_review_draw=consistent_review_draw,
                   held_ad_link=held_ad_link)
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


def gain(inputs: Inputs, session_lengths: Sequence[float], *, draws: int, seed: str,
         merged_sessions: bool = False, consistent_review_draw: bool = False,
         held_ad_link: bool = False) -> dict[float, float]:
    """``G(x)`` (§8.6): the forecast valued uses (no attention cost) when today's session runs ``x`` minutes from
    the start under the tail, then the tail; for the price's daily seed and the frontier."""

    out: dict[float, float] = {}
    model = _Model(replace(inputs, session_minutes=0.0), draws, seed, merged_sessions=merged_sessions,
                   consistent_review_draw=consistent_review_draw, held_ad_link=held_ad_link)
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
    "MINUTES_PER_DAY", "REFERENCE_REF", "REVIEW_DRAW_VERSION", "TAIL_VERSION", "baselines", "evaluate", "gain",
]
