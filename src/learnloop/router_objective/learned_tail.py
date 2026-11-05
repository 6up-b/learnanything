"""RO6 (spec_router_objective_v1 §10): a learned tail. Pure: features, the fitted Q evaluation, the residual's
learned weight and the partial-history cross-check, each a function of numbers handed in.

**Features** (§10, §4 row 9). Low-dimensional, numbers only (text goes to sensors, never here), the same function at
serve time (over the frozen inputs and RO0's snapshot readers) and at fit time (over the trace and RO0's receipt):

* the belief at the decision (:class:`Belief`): the session's load ``m/m̄``; days to go to the nearest active dated
  goal, as ``exp(−days/H)`` (0 with none; ``H`` the objective's own horizon); pending reports, ``log(1 + n)``; the
  candidates' mastery, the mean ``sigmoid(logit mean)`` and the mean logit variance (RO0 row 9's numbers);
* the candidate (:class:`ActionView`): stop, reading or probe (practice the baseline); its predicted minutes over
  ``m̄``; its topics' AD predictive (mean probability); their FSRS lag ``log(1 + elapsed/S)`` over practised topics
  (monotone in retrievability, free of the FSRS weights); stop and the minutes each times the session's load.

No intercept: with no discount the backup cancels any constant (``Σ_a′ π = 1``), so a level is unidentified by the
data and irrelevant to every decision, which compares candidates at one state.

**The fitted Q evaluation** (:func:`fit`). The logger's value is modelled as the tail's plus a residual,
``Q̂(x, a) = Q_tail(x, a) + ρ(x, a)``, ``ρ = θᵀz(x, a)`` linear in the standardized features. The backup is §10's,
``y_i = R_i + Σ_a′ π_ref(a′|x′_i)·Q̂(x′_i, a′)`` with ``π_ref`` the logger's exact served distribution at ``x′_i`` and
§3.2's carried cutoff (the caller hands in ``Σ π_ref·Q_tail`` already moved back to the decision's cutoff). The
estimate is FQE's fixed point under a Gaussian prior ``θ ~ N(0, s²)`` (``residual_prior_sd``, labelled), solved in
closed form, ``(ZᵀZ − ZᵀZ̄′ + (σ²/s²)·I)·θ = Zᵀ(R + V̄_tail′ − Q_tail)``, with the noise ``σ²`` the Bellman residuals'
mean square, refined until it settles. **Model class**: Bayesian linear regression (ridge) on thirteen features. One
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

FEATURES_VERSION = "ro6_belief_features_v1"
FIT_VERSION = "ro6_fqe_ridge_v1"
WEIGHT_VERSION = "ro6_residual_weight_slope_rank_v1"
CROSS_CHECK_VERSION = "ro6_partial_history_v1"

STATE_FEATURES: tuple[str, ...] = ("session_load", "days_to_go", "pending_reports", "mastery_p", "mastery_var")
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

    def as_tuple(self) -> tuple[float, ...]:
        return (self.session_load, self.days_to_go, self.pending_reports, self.mastery_p, self.mastery_var)


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
           mastery: Sequence[tuple[float, float]], topics: Sequence[TopicNumbers]) -> Belief:
    """The state features. ``mastery``: RO0's snapshot of the candidates' LOs (logit mean, logit variance); with none
    recorded, the topics' frozen belief numbers stand in (AD's predictive and its variance)."""

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
    return Belief(session_load=load, days_to_go=go, pending_reports=pending, mastery_p=p, mastery_var=var)


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

    def as_dict(self) -> dict[str, Any]:
        return {"w_hat": self.w_hat, "slope_mean": self.slope_mean, "slope_sd": self.slope_sd,
                "tail_slope": self.tail_slope, "n": self.n, "forced": self.forced, "rank": self.rank,
                "p_rank": self.p_rank, "sigma2": self.sigma2, "prior_sd": self.prior_sd, "source": self.source,
                "version": self.version}


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
    y = np.asarray([row.realized for row in rows], dtype=np.float64)
    precision = np.diag([0.0, 1.0 / float(prior_sd) ** 2])
    sigma2 = float(np.mean(y * y)) if np.any(y) else 0.0
    beta = np.zeros(2)
    for _ in range(_FIT_PASSES):
        matrix = x.T @ x + max(sigma2, _TINY) * precision
        beta = np.linalg.pinv(matrix) @ (x.T @ y)
        residual = y - x @ beta
        updated = float(np.mean(residual * residual))
        settled = abs(updated - sigma2) <= _FIT_TOLERANCE * max(sigma2, _TINY)
        sigma2 = updated
        if settled:
            break
    matrix = x.T @ x + max(sigma2, _TINY) * precision
    covariance = max(sigma2, _TINY) * np.linalg.pinv(matrix)
    slope_mean = float(beta[1])
    slope_sd = float(math.sqrt(max(covariance[1, 1], 0.0)))
    tail_slope = float(beta[0]) if np.any(x[:, 0]) else None
    forced = [row for row in rows if row.forced and row.forced_probability > 0]
    partial = [row.forced_probability * row.realized - float(beta[0]) * row.tail for row in forced]
    rank = spearman([row.residual for row in forced], partial) if len(forced) >= 3 else None
    p_rank = _NORMAL.cdf(rank * math.sqrt(len(forced) - 1)) if rank is not None else 0.5
    w_hat = min(max(slope_mean, 0.0), 1.0) * p_rank
    return WeightFit(w_hat=w_hat, slope_mean=slope_mean, slope_sd=slope_sd, tail_slope=tail_slope, n=len(rows),
                     forced=len(forced), rank=rank, p_rank=p_rank, sigma2=sigma2, prior_sd=float(prior_sd),
                     source="randomized_contrasts")


def coin_contrast(arm: str | None, rate: float) -> float:
    """The stop coin's mean-zero contrast in its logged probabilities: ``1[offer]/p − 1[present_next]/p``."""

    if not rate or rate <= 0:
        return 0.0
    if arm == "offer_stop":
        return 1.0 / float(rate)
    if arm == "present_next":
        return -1.0 / float(rate)
    return 0.0


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


def partial_history(rows: Sequence[WeightedRow], *, window_days: int) -> dict[str, Any]:
    """Report only: importance-weighted estimates of the improvement step minus the logger on the window's return,
    one step (``(ρ_i − 1)·Ĝ_i``) and over each decision's window (the product of the ratios of the decisions in
    it), each with its standard error and effective sample size. Near the logger the weights stay usable; far from
    it they do not, and the effective sample size says so."""

    ordered = sorted(rows, key=lambda row: (row.decided_at, row.decision_id))
    if not ordered:
        return {"version": CROSS_CHECK_VERSION, "n": 0, "status": "no closed window with a logged probability"}

    def summary(weights: list[float]) -> dict[str, Any]:
        values = [(w - 1.0) * row.realized for w, row in zip(weights, ordered)]
        n = len(values)
        mean = sum(values) / n
        se = (math.sqrt(sum((v - mean) ** 2 for v in values) / (n - 1)) / math.sqrt(n)) if n > 1 else None
        total, squares = sum(weights), sum(w * w for w in weights)
        return {"estimate": mean, "se": se, "ess": (total * total / squares) if squares > 0 else None,
                "max_weight": max(weights), "n": n}

    one = [row.ratio for row in ordered]
    span = timedelta(days=int(window_days))
    stamps = [_parse(row.decided_at) for row in ordered]
    window: list[float] = []
    for i, start in enumerate(stamps):
        product = 1.0
        for j in range(i, len(ordered)):
            if stamps[j] - start >= span:
                break
            product *= ordered[j].ratio
        window.append(product)
    return {"version": CROSS_CHECK_VERSION, "n": len(ordered), "one_step": summary(one),
            "window": summary(window), "window_days": int(window_days),
            "label": "importance-weighted, near the logger; the window's observed return, not the cutoff's value"}


__all__ = [
    "ACTION_FEATURES", "ActionView", "Belief", "CROSS_CHECK_VERSION", "Contrast", "FEATURES_VERSION", "FIT_VERSION",
    "Fit", "NAMES", "STATE_FEATURES", "TopicNumbers", "Transition", "WEIGHT_VERSION", "WeightFit", "WeightedRow",
    "belief", "coin_contrast", "fit", "kind_group", "partial_history", "predicted_contrast", "prior_fit",
    "residual_weight", "spearman", "vector",
]
