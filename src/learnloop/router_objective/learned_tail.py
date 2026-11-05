"""RO6 (spec_router_objective_v1 §10): a learned tail. Pure: features, the fitted Q evaluation, the residual's
learned weight and the partial-history cross-check, each a function of numbers handed in.

**Features** (§10, §4 row 9). Low-dimensional, numbers only (text goes to sensors, never here), the same function at
serve time (over the frozen inputs and RO0's snapshot readers) and at fit time (over the trace and RO0's receipt):

* the belief at the decision (:class:`Belief`): the session's load ``m/m̄``; days to go to the nearest active dated
  goal, as ``exp(−days/H)`` (0 with none; ``H`` the objective's own horizon); pending reports, ``log(1 + n)``; the
  candidates' mastery, the mean ``sigmoid(logit mean)`` and the mean logit variance (RO0 row 9's numbers); the
  cutoff's span ``(C − t)/H`` (at a backup's next state, the earlier decision's ``C``: Codex review F3);
* the candidate (:class:`ActionView`): stop, reading or probe (practice the baseline); its predicted minutes over
  ``m̄``; its topics' AD predictive (mean probability); their FSRS lag ``log(1 + elapsed/S)`` over practised topics
  (monotone in retrievability, free of the FSRS weights); stop and the minutes each times the session's load.

No intercept: with no discount the backup cancels any constant (``Σ_a′ π = 1``), so a level is unidentified by the
data and irrelevant to every decision, which compares candidates at one state.

**The fitted Q evaluation** (:func:`fit`). The logger's value is modelled as the tail's plus a residual,
``Q̂(x, a) = Q_tail(x, a) + ρ(x, a)``, ``ρ = θᵀz(x, a)`` linear in the standardized features. The backup is §10's,
``y_i = R_i + Σ_a′ π_ref(a′|x′_i)·Q̂(x′_i, a′)`` with ``π_ref`` the logger's exact served distribution at ``x′_i`` and
§3.2's carried cutoff: the caller hands in ``Σ π_ref·Q_tail(x′, ·; C)`` evaluated at the decision's own cutoff ``C``
on the next decision's rollouts (their value with the net value past ``C + H`` kept apart and taken off), and the
next state's features with their cutoff span at ``C`` (Codex review F3). The
estimate is FQE's fixed point under a Gaussian prior ``θ ~ N(0, s²)`` (``residual_prior_sd``, labelled), solved in
closed form, ``(ZᵀZ − ZᵀZ̄′ + (σ²/s²)·I)·θ = Zᵀ(R + V̄_tail′ − Q_tail)``, with the noise ``σ²`` the Bellman residuals'
mean square, refined until it settles. **Model class**: Bayesian linear regression (ridge) on fourteen features. One
learner's log is hundreds of decisions a month, one long dependent trajectory; a deep net would fit noise and could
not be read in a trace, where a linear residual's every coefficient and term can be (§8.4's "linear kernel first";
the report's T7 for anything richer). It is **never accepted on its TD fit**: its share of the value is ``ŵ``.

**The residual's weight** (:func:`residual_weight`). ``Ṽ = V_tail + ŵ·V_residual``. ``ŵ`` starts at zero and only
randomized contrasts move it: at a stop-coin decision, ``Ĉ_i = (1[offer]/p − 1[present_next]/p)·Ĝ_i`` (``Ĝ`` the
window's return observed through the randomized checks, §8.7's bracket), unbiased for the realized contrast between
offering stop and presenting the next block. Against it the frozen predicted contrasts of the tail ``ΔV_tail`` and of
the residual ``ΔV_residual`` (stop minus the blocks at their logged shares). **Slope**: the regression
``Ĉ ≈ a·ΔV_tail + b·ΔV_residual`` with ``a`` flat (it absorbs the window being shorter than the cutoff) and
``b ~ N(0, s_w²)`` (``residual_weight_prior_sd``, labelled). **Rank**: Spearman's rank correlation between
``ΔV_residual`` and the forced arms' contrast less the tail's part, read as ``P(rank agreement > 0)`` by its normal
approximation (one half with fewer than three). ``ŵ = clip(E[b], 0, 1) · P(rank > 0)``: the scale it has earned,
times the chance its order is right. No promotion step, threshold or minimum sample: with no contrast ``ŵ = 0``.

**Missing terms** (RO6's landing ruling R1, partial identification). A term of ``Ĝ`` whose measurement can be missing
(an exam result not known as of the window's closure, a use no check could observe, a forced draw with no return) is
carried as missing, never as zero, bounded by its structural range (performance in ``[0, 1]`` times its known
weight; costs are always observed), so each ``Ĉ_i`` lies in an interval. The slope and rank that move ``ŵ`` are
taken at the fill of the missing terms least favourable to the residual: the fill that minimizes ``E[b]`` within
the bounds (Manski's worst-case bounds; ``E[b]`` is linear in ``Ĉ`` at a given noise, so each ``Ĉ_i`` goes to the
end of its interval that lowers it, by the sign of its influence on ``b``), and ``ŵ = clip(E[b]_lower, 0, 1) ·
P(rank > 0 at that fill)``. With no missing term this is the estimate above exactly; as missingness shrinks the
bound tightens by itself. No threshold, minimum sample or observation model. The estimate with the missing terms
left out (the unbounded one) is kept beside it, shown only.

**The measurable target** (RO6's landing ruling R7). The bound applies to terms whose observation is decided after
the coin's draw. A use whose topic had no check support as of the draw (``r = 0`` in the latest check draw known
then, read through RO1's availability predicate) is not a missing outcome but outside the measurable target: it is
left out of both arms' realized return and, where the value decomposes by term (the tail's rollouts keep each
topic's share apart), out of the tail's predicted contrast too. That exclusion is a function only of what was known
before randomization, so it cannot select on the arm. The residual's prediction cannot be restricted to the same
terms: its unrestricted prediction is used, which attenuates the slope toward zero (the record says so). ``ŵ`` is
calibrated on the measurable part of the return only.

**The partial-history cross-check** (:func:`partial_history`, report only): importance weights of the improvement
step (the mix with the numeric policy's argmax taken on ``Q_tail + ρ``) against the logger's served distribution,
one step and over each decision's window, near the logger where the weights stay usable.

A leaf: numpy and the standard library.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import math
from statistics import NormalDist
from typing import Any

import numpy as np

FEATURES_VERSION = "ro6_belief_features_v2"
FIT_VERSION = "ro6_fqe_ridge_v1"
WEIGHT_VERSION = "ro6_residual_weight_slope_rank_v5"
#: ``ŵ``'s bound (RO6's landing ruling R1): the least favourable fill of the missing terms, or none to fill
LEAST_FAVOURABLE = "least_favourable_fill"
NO_BOUND = "none"
CROSS_CHECK_VERSION = "ro6_partial_history_v2"

STATE_FEATURES: tuple[str, ...] = ("session_load", "days_to_go", "pending_reports", "mastery_p", "mastery_var",
                                   "cutoff_span")
ACTION_FEATURES: tuple[str, ...] = ("stop", "reading", "probe", "minutes", "topic_p", "topic_lag", "stop_x_load",
                                    "minutes_x_load")
NAMES: tuple[str, ...] = (*STATE_FEATURES, *ACTION_FEATURES)

#: The noise variance's refinement (numerical resolution, not a judgement): passes and relative tolerance.
_FIT_PASSES = 25
_FIT_TOLERANCE = 1e-6
#: A floor under a variance before a division (numerical only).
_TINY = 1e-18

_NORMAL = NormalDist()

STOP_KIND = "stop"
READING_KIND = "reading"
PROBE_KIND = "probe"


def _sigmoid(x: float) -> float:
    if x >= 0:
        return 1.0 / (1.0 + math.exp(-x))
    e = math.exp(x)
    return e / (1.0 + e)


# -- features ---------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Belief:
    """The decision's state features (module docstring)."""

    session_load: float
    days_to_go: float
    pending_reports: float
    mastery_p: float
    mastery_var: float
    #: ``(C − t)/H``: how far the value's cutoff lies from the state (Codex review F3: the backup evaluates the next
    #: state at the earlier decision's cutoff, so the residual sees that cutoff too)
    cutoff_span: float = 1.0

    def as_tuple(self) -> tuple[float, ...]:
        return (self.session_load, self.days_to_go, self.pending_reports, self.mastery_p, self.mastery_var,
                self.cutoff_span)


@dataclass(frozen=True)
class TopicNumbers:
    """One topic's belief numbers as the decision froze them (the trace's sensors, the value's ``Topic``)."""

    eta: float
    eta_var: float
    practiced: bool = False
    stability: float = 0.0
    elapsed_days: float = 0.0


def belief(*, session_minutes: float | None, remembered: float | None, nearest_goal_days: float | None,
           horizon_days: float, pending_reports: int | float | None,
           mastery: Sequence[tuple[float, float]], topics: Sequence[TopicNumbers],
           cutoff_days: float | None = None) -> Belief:
    """The state features. ``mastery``: RO0's snapshot of the candidates' LOs (logit mean, logit variance); with none
    recorded, the topics' frozen belief numbers stand in (AD's predictive and its variance). ``cutoff_days``: the
    value's cutoff in days from the state (``C − t``; None: ``H``, the cutoff with no goal past the horizon)."""

    mbar = max(float(remembered or 0.0), 1.0)
    load = max(float(session_minutes or 0.0), 0.0) / mbar
    go = (math.exp(-max(float(nearest_goal_days), 0.0) / max(float(horizon_days), 1.0))
          if nearest_goal_days is not None else 0.0)
    pending = math.log1p(max(float(pending_reports or 0.0), 0.0))
    pairs = list(mastery) or [(topic.eta, topic.eta_var) for topic in topics]
    if pairs:
        p = sum(_sigmoid(float(mean)) for mean, _var in pairs) / len(pairs)
        var = sum(max(float(v), 0.0) for _mean, v in pairs) / len(pairs)
    else:
        p, var = 0.5, 0.0
    horizon = max(float(horizon_days), 1.0)
    span = (float(cutoff_days) / horizon) if cutoff_days is not None else float(horizon_days) / horizon
    return Belief(session_load=load, days_to_go=go, pending_reports=pending, mastery_p=p, mastery_var=var,
                  cutoff_span=span)


@dataclass(frozen=True)
class ActionView:
    """One candidate's features' inputs."""

    ref: str
    kind: str
    minutes: float
    topics: tuple[TopicNumbers, ...] = ()


def kind_group(kind: str | None) -> str:
    if kind == STOP_KIND:
        return STOP_KIND
    if kind == READING_KIND:
        return READING_KIND
    if kind == PROBE_KIND:
        return PROBE_KIND
    return "practice"


def vector(state: Belief, action: ActionView, *, remembered: float | None) -> tuple[float, ...]:
    """φ(x, a) in :data:`NAMES` order."""

    mbar = max(float(remembered or 0.0), 1.0)
    group = kind_group(action.kind)
    stop = 1.0 if group == STOP_KIND else 0.0
    minutes = 0.0 if stop else max(float(action.minutes or 0.0), 0.0) / mbar
    topics = action.topics if not stop else ()
    topic_p = (sum(_sigmoid(topic.eta) for topic in topics) / len(topics)) if topics else 0.0
    practiced = [topic for topic in topics if topic.practiced and topic.stability > 0]
    lag = (sum(math.log1p(max(topic.elapsed_days, 0.0) / topic.stability) for topic in practiced) / len(practiced)
           if practiced else 0.0)
    return (*state.as_tuple(), stop, 1.0 if group == READING_KIND else 0.0, 1.0 if group == PROBE_KIND else 0.0,
            minutes, topic_p, lag, stop * state.session_load, minutes * state.session_load)


# -- the fitted Q evaluation ------------------------------------------------------------------------------


@dataclass(frozen=True)
class Transition:
    """One logged step of a frozen logger version, ready for the backup.

    ``phi``: φ(x_i, A_i) of the served action. ``next_phi``: ``Σ_a′ π_ref(a′|x′)·φ(x′, a′)``. ``reward``: ``R_i``
    over ``(t_i, t_{i+1}]``. ``q_taken``: ``Q_tail(x_i, A_i)``. ``next_v_tail``: ``Σ_a′ π_ref(a′|x′)·Q_tail(x′, a′)``
    at the decision's own cutoff (§3.2)."""

    decision_id: str
    generator: str
    decided_at: str
    phi: tuple[float, ...]
    next_phi: tuple[float, ...]
    reward: float
    q_taken: float
    next_v_tail: float
    detail: Mapping[str, Any] = field(default_factory=dict)

    @property
    def target(self) -> float:
        """The residual's part of the backup with no residual at ``x′``: ``R + V̄_tail′ − Q_tail``."""

        return self.reward + self.next_v_tail - self.q_taken


@dataclass(frozen=True)
class Fit:
    """A fitted residual ``ρ = θᵀ((φ − mean)/sd)`` for one generator version (or the prior, ``θ = 0``)."""

    generator: str | None
    names: tuple[str, ...]
    mean: tuple[float, ...]
    sd: tuple[float, ...]
    coef: tuple[float, ...]
    n: int
    prior_sd: float
    sigma2: float | None = None
    condition: float | None = None
    passes: int = 0
    source: str = "prior"
    version: str = FIT_VERSION
    features_version: str = FEATURES_VERSION

    def value(self, phi: Sequence[float]) -> float:
        z = [(float(x) - m) / s for x, m, s in zip(phi, self.mean, self.sd)]
        return float(sum(c * v for c, v in zip(self.coef, z)))

    def as_dict(self) -> dict[str, Any]:
        return {"version": self.version, "features_version": self.features_version, "generator": self.generator,
                "names": list(self.names), "mean": list(self.mean), "sd": list(self.sd), "coef": list(self.coef),
                "n": self.n, "prior_sd": self.prior_sd, "sigma2": self.sigma2, "condition": self.condition,
                "passes": self.passes, "source": self.source}

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "Fit":
        return cls(generator=data.get("generator"), names=tuple(data["names"]),
                   mean=tuple(float(v) for v in data["mean"]), sd=tuple(float(v) for v in data["sd"]),
                   coef=tuple(float(v) for v in data["coef"]), n=int(data.get("n") or 0),
                   prior_sd=float(data.get("prior_sd") or 0.0), sigma2=data.get("sigma2"),
                   condition=data.get("condition"), passes=int(data.get("passes") or 0),
                   source=str(data.get("source") or "prior"), version=str(data.get("version") or FIT_VERSION),
                   features_version=str(data.get("features_version") or FEATURES_VERSION))


def prior_fit(prior_sd: float, generator: str | None = None) -> Fit:
    """No transition: the prior, a residual of zero."""

    width = len(NAMES)
    return Fit(generator=generator, names=NAMES, mean=(0.0,) * width, sd=(1.0,) * width, coef=(0.0,) * width, n=0,
               prior_sd=float(prior_sd), source="prior: no transition of this version")


def fit(transitions: Sequence[Transition], *, prior_sd: float, generator: str | None = None) -> Fit:
    """FQE's fixed point for one frozen logger version under the labelled Gaussian prior (module docstring)."""

    rows = list(transitions)
    if not rows:
        return prior_fit(prior_sd, generator)
    phi = np.asarray([row.phi for row in rows], dtype=np.float64)
    nxt = np.asarray([row.next_phi for row in rows], dtype=np.float64)
    b = np.asarray([row.target for row in rows], dtype=np.float64)
    mean = phi.mean(axis=0)
    sd = phi.std(axis=0)
    # A feature constant over the version's transitions is left unscaled (its column's row in the system is
    # then fixed by the prior alone where no transition moves it).
    sd = np.where(sd > 0, sd, 1.0)
    z = (phi - mean) / sd
    zn = (nxt - mean) / sd
    a0 = z.T @ (z - zn)
    c = z.T @ b
    width = z.shape[1]
    sigma2 = float(np.mean(b * b))
    theta = np.zeros(width)
    passes = 0
    for passes in range(1, _FIT_PASSES + 1):
        lam = max(sigma2, _TINY) / (float(prior_sd) ** 2)
        matrix = a0 + lam * np.eye(width)
        try:
            theta = np.linalg.solve(matrix, c)
        except np.linalg.LinAlgError:
            theta = np.linalg.lstsq(matrix, c, rcond=None)[0]
        residual = b - (z - zn) @ theta
        updated = float(np.mean(residual * residual))
        settled = abs(updated - sigma2) <= _FIT_TOLERANCE * max(sigma2, _TINY)
        sigma2 = updated
        if settled:
            break
    lam = max(sigma2, _TINY) / (float(prior_sd) ** 2)
    condition = float(np.linalg.cond(a0 + lam * np.eye(width)))
    return Fit(generator=generator, names=NAMES, mean=tuple(float(v) for v in mean), sd=tuple(float(v) for v in sd),
               coef=tuple(float(v) for v in theta), n=len(rows), prior_sd=float(prior_sd), sigma2=sigma2,
               condition=condition if math.isfinite(condition) else None, passes=passes,
               source="fqe_fixed_point_with_prior")


# -- the residual's learned weight ------------------------------------------------------------------------


@dataclass(frozen=True)
class Contrast:
    """One randomized stop-coin decision's realized and frozen predicted contrasts (offer stop vs the next block)."""

    decision_id: str
    decided_at: str
    window_closes_at: str
    #: ``Ĉ_i``: the coin's contrast times the window's observed return (0 on the coin's ``policy`` arm)
    realized: float
    #: the tail's and the residual's frozen predicted contrasts
    tail: float
    residual: float
    #: whether the coin forced its arm (offer stop or present the next block), and P(forced) (twice its rate)
    forced: bool = False
    forced_probability: float = 0.0
    #: R1: the interval ``realized`` lies in with its window's missing terms at their bounds (None: no missing term,
    #: the interval is ``realized`` itself), and how many terms were missing
    realized_lo: float | None = None
    realized_hi: float | None = None
    missing: int = 0
    #: R7: the window's terms no check could measure as of the draw, left out of ``realized`` (outside the target)
    excluded: int = 0

    @property
    def bounds(self) -> tuple[float, float]:
        lo = self.realized if self.realized_lo is None else self.realized_lo
        hi = self.realized if self.realized_hi is None else self.realized_hi
        return float(lo), float(hi)


@dataclass(frozen=True)
class WeightFit:
    w_hat: float
    slope_mean: float
    slope_sd: float
    tail_slope: float | None
    n: int
    forced: int
    rank: float | None
    p_rank: float
    sigma2: float | None
    prior_sd: float
    source: str
    version: str = WEIGHT_VERSION
    #: R1: the bound used (:data:`LEAST_FAVOURABLE`, or :data:`NO_BOUND` with no missing term), the contrasts and
    #: terms missing, and the estimate with the missing terms left out beside it (shown only; never served)
    bound: str = NO_BOUND
    missing_contrasts: int = 0
    missing_terms: int = 0
    unbounded: Mapping[str, Any] | None = None
    #: R7: the terms left out as unsupported at the draw (outside the measurable target), and where
    excluded_contrasts: int = 0
    excluded_terms: int = 0

    def as_dict(self) -> dict[str, Any]:
        own = {"w_hat": self.w_hat, "slope_mean": self.slope_mean, "slope_sd": self.slope_sd,
               "tail_slope": self.tail_slope, "rank": self.rank, "p_rank": self.p_rank, "sigma2": self.sigma2}
        return {**own, "n": self.n, "forced": self.forced, "prior_sd": self.prior_sd, "source": self.source,
                "version": self.version, "bound": self.bound,
                "missing": {"contrasts": self.missing_contrasts, "terms": self.missing_terms},
                "excluded": {"contrasts": self.excluded_contrasts, "terms": self.excluded_terms},
                "target": "the measurable part of the return only (terms a check could measure as of the draw)",
                "unbounded": dict(self.unbounded) if self.unbounded is not None else dict(own)}


def _ranks(values: Sequence[float]) -> list[float]:
    order = sorted(range(len(values)), key=lambda i: values[i])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
            j += 1
        average = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            ranks[order[k]] = average
        i = j + 1
    return ranks


def spearman(x: Sequence[float], y: Sequence[float]) -> float | None:
    """Spearman's rank correlation (average ranks for ties); None where either side has no spread."""

    if len(x) < 2:
        return None
    rx, ry = np.asarray(_ranks(x)), np.asarray(_ranks(y))
    sx, sy = rx.std(), ry.std()
    if sx <= 0 or sy <= 0:
        return None
    return float(np.mean((rx - rx.mean()) * (ry - ry.mean())) / (sx * sy))


def _parse(stamp: str) -> datetime:
    return datetime.fromisoformat(str(stamp).replace("Z", "+00:00"))


def residual_weight(contrasts: Sequence[Contrast], *, prior_sd: float, at: str | None = None) -> WeightFit:
    """``ŵ`` from the randomized contrasts whose windows closed before ``at`` (no peeking; module docstring)."""

    cut = _parse(at) if at else None
    rows = [row for row in contrasts if cut is None or _parse(row.window_closes_at) < cut]
    if not rows:
        return WeightFit(w_hat=0.0, slope_mean=0.0, slope_sd=float(prior_sd), tail_slope=None, n=0, forced=0,
                         rank=None, p_rank=0.5, sigma2=None, prior_sd=float(prior_sd),
                         source="prior: no randomized contrast with a frozen residual")
    x = np.asarray([[row.tail, row.residual] for row in rows], dtype=np.float64)
    precision = np.diag([0.0, 1.0 / float(prior_sd) ** 2])
    forced = [i for i, row in enumerate(rows) if row.forced and row.forced_probability > 0]
    point = np.asarray([row.realized for row in rows], dtype=np.float64)
    bounds = np.asarray([row.bounds for row in rows], dtype=np.float64)
    lo, hi = bounds[:, 0], bounds[:, 1]
    open_rows = [i for i, row in enumerate(rows) if row.missing > 0 and hi[i] > lo[i]]
    unbounded = _slope_and_rank(rows, x, point, precision, forced)
    if not open_rows:
        estimate, source, bound = unbounded, "randomized_contrasts", NO_BOUND
    else:
        # R1: the fill least favourable to the residual. At a given noise E[b] is linear in Ĉ, so the fill that
        # minimizes it sends each open Ĉ_i to the end of its interval against the sign of its influence on b;
        # the noise is then refit at that fill, until the fill and the noise settle.
        y = point.copy()
        sigma2 = float(unbounded["sigma2"])
        for _ in range(_FIT_PASSES):
            influence = (np.linalg.pinv(x.T @ x + max(sigma2, _TINY) * precision) @ x.T)[1]
            filled = point.copy()
            filled[open_rows] = np.where(influence[open_rows] > 0, lo[open_rows], hi[open_rows])
            updated, _beta = _noise(x, filled, precision, sigma2)
            settled = bool(np.array_equal(filled, y)) and abs(updated - sigma2) <= _FIT_TOLERANCE * max(sigma2, _TINY)
            y, sigma2 = filled, updated
            if settled:
                break
        # The slope and rank at that fill, by the same estimator as with no missing term.
        estimate = _slope_and_rank(rows, x, y, precision, forced)
        source, bound = "randomized_contrasts at the least favourable fill of the missing terms", LEAST_FAVOURABLE
    w_hat = min(max(estimate["slope_mean"], 0.0), 1.0) * estimate["p_rank"]
    shown = {**unbounded, "w_hat": min(max(unbounded["slope_mean"], 0.0), 1.0) * unbounded["p_rank"]}
    return WeightFit(w_hat=w_hat, slope_mean=estimate["slope_mean"], slope_sd=estimate["slope_sd"],
                     tail_slope=estimate["tail_slope"], n=len(rows), forced=len(forced), rank=estimate["rank"],
                     p_rank=estimate["p_rank"], sigma2=estimate["sigma2"], prior_sd=float(prior_sd), source=source,
                     bound=bound, missing_contrasts=sum(1 for row in rows if row.missing > 0),
                     missing_terms=sum(int(row.missing) for row in rows),
                     unbounded=shown if open_rows else None,
                     excluded_contrasts=sum(1 for row in rows if row.excluded > 0),
                     excluded_terms=sum(int(row.excluded) for row in rows))


def _noise(x: np.ndarray, y: np.ndarray, precision: np.ndarray, sigma2: float) -> tuple[float, np.ndarray]:
    """The regression's noise at ``y``, refined from ``sigma2`` until it settles, and the coefficients of its last
    pass."""

    beta = np.zeros(x.shape[1])
    for _ in range(_FIT_PASSES):
        beta = np.linalg.pinv(x.T @ x + max(sigma2, _TINY) * precision) @ (x.T @ y)
        residual = y - x @ beta
        updated = float(np.mean(residual * residual))
        settled = abs(updated - sigma2) <= _FIT_TOLERANCE * max(sigma2, _TINY)
        sigma2 = updated
        if settled:
            break
    return sigma2, beta


def _slope_and_rank(rows: Sequence[Contrast], x: np.ndarray, y: np.ndarray, precision: np.ndarray,
                    forced: Sequence[int]) -> dict[str, Any]:
    """The slope (posterior mean and sd of ``b``, the tail's ``a``) and the rank at the contrasts ``y``, the noise
    refined from ``y``'s mean square (module docstring)."""

    sigma2, beta = _noise(x, y, precision, float(np.mean(y * y)) if np.any(y) else 0.0)
    matrix = x.T @ x + max(sigma2, _TINY) * precision
    covariance = max(sigma2, _TINY) * np.linalg.pinv(matrix)
    partial = [rows[i].forced_probability * float(y[i]) - float(beta[0]) * rows[i].tail for i in forced]
    rank = spearman([rows[i].residual for i in forced], partial) if len(forced) >= 3 else None
    return {"slope_mean": float(beta[1]), "slope_sd": float(math.sqrt(max(covariance[1, 1], 0.0))),
            "tail_slope": float(beta[0]) if np.any(x[:, 0]) else None, "rank": rank,
            "p_rank": _NORMAL.cdf(rank * math.sqrt(len(forced) - 1)) if rank is not None else 0.5,
            "sigma2": sigma2}


def coin_contrast(arm: str | None, rate: float) -> float:
    """The stop coin's mean-zero contrast in its logged probabilities: ``1[offer]/p − 1[present_next]/p``."""

    if not rate or rate <= 0:
        return 0.0
    if arm == "offer_stop":
        return 1.0 / float(rate)
    if arm == "present_next":
        return -1.0 / float(rate)
    return 0.0


@dataclass(frozen=True)
class CoinDraw:
    """One randomized stop-coin decision of the cohort (chosen on what was fixed before the coin: a frozen residual,
    stop in the support, a closed window) with its window's return: ``value`` the observed terms (None: no return at
    all, and why), ``[value + lo, value + hi]`` with its ``missing`` terms at their bounds (RO6's landing ruling R1)."""

    decision_id: str
    decided_at: str
    window_closes_at: str
    arm: str | None
    rate: float
    value: float | None
    reason: str | None
    tail: float
    residual: float
    lo: float = 0.0
    hi: float = 0.0
    missing: int = 0
    #: R7: the window's terms left out as unsupported at the draw (outside the measurable target)
    excluded: int = 0


OFFER_STOP = "offer_stop"
PRESENT_NEXT = "present_next"
UNIDENTIFIED = "unidentified"


def coin_contrasts(draws: Sequence[CoinDraw]) -> tuple[list[Contrast], dict[str, Any]]:
    """The randomized cohort's contrasts, every draw kept (Codex review of RO6, F1; RO6's landing ruling R1).

    The cohort is chosen before the coin, and every draw stays: ``Ĉ_i = (1[offer]/p − 1[present_next]/p)·Ĝ_i``, the
    ``policy`` arm's zero whatever its return. A return that goes unobserved after the coin can go so for reasons tied
    to the arm and to anything about the decision (a pre-coin feature, the return itself), so no observation model is
    assumed: every term of ``Ĝ_i`` whose measurement is missing is carried as missing, bounded by its structural
    range (the reader's :class:`learnloop.router_objective.scores.Bounded`), and each forced ``Ĉ_i`` becomes an
    interval (:attr:`Contrast.bounds`) that :func:`residual_weight` reads at the fill least favourable to the
    residual. A forced draw with no return at all has no known range (an unbounded missing term, at whose least
    favourable fill the slope is unbounded below): the contrast is then **unidentified** and no contrast is returned
    (``ŵ`` stays at zero), said by arm and reason. The record lists each forced window's missing terms with their
    bounds."""

    assigned: dict[str, int] = {OFFER_STOP: 0, PRESENT_NEXT: 0}
    observed: dict[str, int] = {OFFER_STOP: 0, PRESENT_NEXT: 0}
    reasons: dict[str, dict[str, int]] = {}
    notes: dict[str, dict[str, int]] = {}
    windows: list[dict[str, Any]] = []
    for draw in draws:
        if draw.arm in assigned:
            assigned[draw.arm] += 1
            if draw.value is not None:
                observed[draw.arm] += 1
                if draw.missing or draw.excluded:
                    windows.append({"decision_id": draw.decision_id, "arm": draw.arm, "missing": int(draw.missing),
                                    "lo": float(draw.lo), "hi": float(draw.hi), "excluded": int(draw.excluded)})
        into = reasons if draw.value is None else notes
        if draw.value is None or draw.reason:
            by_arm = into.setdefault(str(draw.arm), {})
            for reason in str(draw.reason).split(";"):  # draws by reason (the terms are counted in "missing")
                key = reason.split(":")[0]
                by_arm[key] = by_arm.get(key, 0) + 1
    record: dict[str, Any] = {"cohort": len(draws), "assigned": dict(assigned), "observed": dict(observed),
                              "unobserved": reasons, "notes": notes,
                              "missing": {"windows": sum(1 for entry in windows if entry["missing"]),
                                          "terms": sum(entry["missing"] for entry in windows),
                                          "by_window": windows},
                              # R7: unsupported at the draw, outside the measurable target (forced windows)
                              "excluded": {"windows": sum(1 for entry in windows if entry["excluded"]),
                                           "terms": sum(entry["excluded"] for entry in windows)},
                              "assumption": "no observation model: each missing term bounded by its structural range "
                                            "(performance in [0, 1] times its weight; costs observed), w^ read at "
                                            "the least favourable fill"}
    unbounded = [arm for arm in assigned if observed[arm] < assigned[arm]]
    if unbounded:
        record["status"] = UNIDENTIFIED
        record["why"] = (f"{sum(assigned[a] - observed[a] for a in unbounded)} forced draw(s) with no return at all on "
                         f"the {', '.join(unbounded)} arm: an unbounded missing term, so the contrast is not "
                         f"identified")
        return [], record
    record["status"] = "identified"
    out: list[Contrast] = []
    for draw in draws:
        weight = coin_contrast(draw.arm, draw.rate)
        forced = draw.arm in assigned
        if weight == 0.0 or draw.value is None:
            realized, ends, missing, excluded = 0.0, None, 0, 0
        else:
            realized = weight * float(draw.value)
            ends = sorted((weight * (float(draw.value) + float(draw.lo)), weight * (float(draw.value) + float(draw.hi))))
            missing, excluded = int(draw.missing), int(draw.excluded)
        out.append(Contrast(decision_id=draw.decision_id, decided_at=draw.decided_at,
                            window_closes_at=draw.window_closes_at, realized=realized, tail=draw.tail,
                            residual=draw.residual, forced=forced, forced_probability=2.0 * float(draw.rate),
                            realized_lo=ends[0] if ends and missing else None,
                            realized_hi=ends[1] if ends and missing else None, missing=missing, excluded=excluded))
    return out, record


CALIBRATION_SUMMARY_VERSION = "ro6_calibration_summary_v1"


def contrasts_hash(contrasts: Sequence[Contrast], record: Mapping[str, Any]) -> str:
    """RO6's landing ruling R9: the hash of what calibrated ``ŵ`` (every contrast's realized value, interval,
    predictions, forcing, missing and excluded counts, and the cohort's status), exact (each float's ``repr``), so a
    trace's summary is checked against a recomputation from the ledger as of the trace's time."""

    import hashlib
    import json

    rows = [[row.decision_id, row.window_closes_at, repr(float(row.realized)), *(repr(v) for v in row.bounds),
             repr(float(row.tail)), repr(float(row.residual)), bool(row.forced), repr(float(row.forced_probability)),
             int(row.missing), int(row.excluded)] for row in contrasts]
    content = json.dumps({"status": record.get("status"), "rows": rows}, separators=(",", ":"))
    return hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]


def calibration_summary(contrasts: Sequence[Contrast], record: Mapping[str, Any], *, at: str) -> dict[str, Any]:
    """RO6's landing ruling R9: what a trace keeps of ``ŵ``'s calibration, of a size that does not grow with the
    log: the contrasts' count and status, the cohort's counts by arm, the missing and excluded counts, the
    predictions' restriction counts and the hash of its inputs (:func:`contrasts_hash`), as of ``at``. ``ŵ`` itself,
    its bound slope and rank and the unbounded estimate are the trace's ``weight``. The per-window bounds recompute
    from the ledger as of ``at`` (``tail_data.contrasts``)."""

    missing = record.get("missing") or {}
    excluded = record.get("excluded") or {}
    return {"version": CALIBRATION_SUMMARY_VERSION, "at": at, "n": len(contrasts), "status": record.get("status"),
            "cohort": record.get("cohort"), "assigned": dict(record.get("assigned") or {}),
            "observed": dict(record.get("observed") or {}),
            "missing": {"windows": missing.get("windows", 0), "terms": missing.get("terms", 0)},
            "excluded": {"windows": excluded.get("windows", 0), "terms": excluded.get("terms", 0)},
            "prediction": {key: value for key, value in (record.get("prediction") or {}).items() if key != "note"},
            "before_coin": dict(record.get("before_coin") or {}),
            "inputs_hash": contrasts_hash(contrasts, record)}


def predicted_contrast(values: Mapping[str, float], mu: Mapping[str, float], stop_ref: str) -> float | None:
    """A frozen value's contrast between the coin's arms: stop minus the blocks at the mix's shares among them (what
    ``present_next`` serves where the mix drew stop, and the mix's own block elsewhere)."""

    if stop_ref not in values:
        return None
    blocks = {ref: float(mu.get(ref, 0.0)) for ref in values if ref != stop_ref}
    total = sum(blocks.values())
    if total <= 0:
        return None
    return float(values[stop_ref]) - sum(share / total * float(values[ref]) for ref, share in blocks.items())


# -- the partial-history cross-check --------------------------------------------------------------------


@dataclass(frozen=True)
class WeightedRow:
    """One decision's importance ratio (the improvement step's probability of the served action over the logger's)
    and the window's observed return."""

    decision_id: str
    decided_at: str
    ratio: float
    realized: float
    #: the window's end (the trace's ``window_closes_at``); None: ``decided_at`` plus the window's days
    window_closes_at: str | None = None


@dataclass(frozen=True)
class Ratio:
    """One decision of the whole logged sequence and its importance ratio (None: not computable, e.g. a decision
    with no frozen residual), whether or not its own window has closed."""

    decision_id: str
    decided_at: str
    ratio: float | None


INCOMPLETE_HISTORY = "incomplete_history"


def partial_history(rows: Sequence[WeightedRow], *, window_days: int,
                    sequence: Sequence[Ratio] | None = None) -> dict[str, Any]:
    """Report only: importance-weighted estimates of the improvement step minus the logger on the window's return,
    one step (``(ρ_i − 1)·Ĝ_i``) and over each decision's window (the product of the ratios of **every** decision in
    it), each with its standard error and effective sample size. Near the logger the weights stay usable; far from
    it they do not, and the effective sample size says so.

    ``rows`` are the windows that can be evaluated (closed, their return observed); ``sequence`` is the complete
    sequence of logged decisions with their ratios (Codex review of RO6, F6: a decision inside an evaluated window
    whose own window is still open is one of its factors). A window holding a decision whose ratio is unknown is
    censored ``incomplete_history``, never a product with a factor left out. With no ``sequence``, ``rows`` are
    their own sequence."""

    ordered = sorted(rows, key=lambda row: (row.decided_at, row.decision_id))
    if not ordered:
        return {"version": CROSS_CHECK_VERSION, "n": 0, "status": "no closed window with a logged probability"}
    steps = sorted(sequence if sequence is not None else
                   [Ratio(row.decision_id, row.decided_at, row.ratio) for row in ordered],
                   key=lambda step: (step.decided_at, step.decision_id))

    def summary(weights: list[float], realized: list[float]) -> dict[str, Any] | None:
        if not weights:
            return None
        values = [(w - 1.0) * value for w, value in zip(weights, realized)]
        n = len(values)
        mean = sum(values) / n
        se = (math.sqrt(sum((v - mean) ** 2 for v in values) / (n - 1)) / math.sqrt(n)) if n > 1 else None
        total, squares = sum(weights), sum(w * w for w in weights)
        return {"estimate": mean, "se": se, "ess": (total * total / squares) if squares > 0 else None,
                "max_weight": max(weights), "n": n}

    span = timedelta(days=int(window_days))
    stamps = [_parse(step.decided_at) for step in steps]
    window: list[float] = []
    window_realized: list[float] = []
    censored = 0
    for row in ordered:
        start = _parse(row.decided_at)
        end = _parse(row.window_closes_at) if row.window_closes_at else start + span
        product: float | None = 1.0
        for stamp, step in zip(stamps, steps):
            if stamp < start or stamp >= end:
                continue
            if step.ratio is None:
                product = None
                break
            product *= float(step.ratio)
        if product is None:
            censored += 1
            continue
        window.append(product)
        window_realized.append(row.realized)
    return {"version": CROSS_CHECK_VERSION, "n": len(ordered),
            "one_step": summary([row.ratio for row in ordered], [row.realized for row in ordered]),
            "window": summary(window, window_realized), "window_censored": {INCOMPLETE_HISTORY: censored},
            "window_days": int(window_days),
            "label": "importance-weighted, near the logger; the window's observed return, not the cutoff's value"}


__all__ = [
    "ACTION_FEATURES", "ActionView", "Belief", "CROSS_CHECK_VERSION", "CoinDraw", "Contrast", "FEATURES_VERSION",
    "FIT_VERSION", "Fit", "INCOMPLETE_HISTORY", "NAMES", "OFFER_STOP", "PRESENT_NEXT", "Ratio", "STATE_FEATURES",
    "TopicNumbers", "Transition", "UNIDENTIFIED", "WEIGHT_VERSION", "WeightFit", "WeightedRow", "coin_contrasts",
    "belief", "coin_contrast", "fit", "kind_group", "partial_history", "predicted_contrast", "prior_fit",
    "residual_weight", "spearman", "vector",
]
