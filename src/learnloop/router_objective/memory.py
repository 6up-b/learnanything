"""RO4 §8.4: the memory model the objective's rollouts read, vectorized over parameter draws.

``P(perform_L | path)`` for a topic ``L`` combines two sensors on the logit scale:

* **AD's predictive** ``η_L``: adaptive difficulty's expected success on an unseen item of the LO's main cell
  (``p̄``), on the logit scale. Practice moves it by AD's learning increment ``γ`` and reading by AD's dose
  curve (``adaptive_difficulty.priors``: ``GAMMA_PRIOR``, ``READING_PRIORS``, ``DOSE_SCALES``);
* **FSRS** retrievability ``R_L(s)`` of the LO's practiced items at the use's lag, under FSRS's own update.

The combination is a Bayesian logistic regression of the realized cold outcome on the frozen sensor values,
``logit P = a0 + aA·η + aR·(logit R − η)·[practiced]``, so predictions stay in ``[0, 1]`` and an unpractised
topic reads AD's predictive alone. Its prior (:data:`COMBINER_PRIOR`) is a seed chosen by judgment and labelled:
AD's predictive as the baseline (``aA = 1``), FSRS's item memory moving it half its gap (``aR = 0.5``), no
offset; each coefficient's prior variance 0.25. :func:`fit_combiner` is the posterior (a Laplace fit, damped
Newton) on whatever (sensor, outcome) pairs exist; with none it is the prior, and the trace says so.

At the follow-up batch's tag (landing ruling R6) the combiner is **monotone in ability by construction**
(:data:`FORM_MONOTONE`): ``η``'s two slopes (``aA`` unpractised, ``aA − aR`` practised) are log-normal, in the prior
(moment-matched to the linear one) and in the fit, so no draw predicts lower performance for higher ability.

Only parameter uncertainty is drawn (θ): a known success probability of .7 still has noisy outcomes, and that
noise is the rollouts' common random numbers, not uncertainty about the value.

The FSRS update here is :mod:`learnloop.scheduling.fsrs`'s, vectorized over draws (``tests/test_ro4_memory.py``
checks it against the scalar one). A leaf: numpy and the standard library; the FSRS weights are handed in.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
import math
from typing import Any

import numpy as np

MEMORY_MODEL_VERSION = "fsrs_ad_logistic_v1"
#: The follow-up batch's fit (item 2): the randomized checks' rows and the traces' sensors joined to resolved cold
#: outcomes (``router_objective.combiner_data``), under the same prior and form.
COMBINER_FIT_VERSION = "combiner_fit_v2:checks+trace_outcomes"
#: The combiner's prior: (a0, aA, aR) means and variances (module docstring). A labelled seed.
COMBINER_PRIOR_MEAN: tuple[float, float, float] = (0.0, 1.0, 0.5)
COMBINER_PRIOR_VARIANCE: tuple[float, float, float] = (0.25, 0.25, 0.25)

#: The combiner's parametrizations. ``linear_v1`` (RO4 to mvp-0.49): the Gaussian above on ``(a0, aA, aR)``.
#: ``monotone_v1`` (the follow-up batch's landing ruling R6, at mvp-0.50): ``P(perform)`` cannot fall as ``η`` rises.
#: ``η``'s slope is ``aA`` for an unpractised topic and ``aA − aR`` for a practised one, so both are kept positive:
#: the parameters are ``(a0, log aA, log b)`` with ``b = aA − aR``, a diagonal Gaussian there (so each slope is
#: log-normal), and ``aR = aA − b`` is derived (either sign: FSRS may move the forecast either way of AD's).
FORM_LINEAR = "linear_v1"
FORM_MONOTONE = "monotone_v1"


def _log_normal(mean: float, variance: float) -> tuple[float, float]:
    """The ``(μ, σ²)`` of the log-normal with this mean and variance (moment matching)."""

    s2 = math.log1p(variance / mean ** 2)
    return math.log(mean) - s2 / 2.0, s2


#: ``monotone_v1``'s labelled prior, moment-matched to ``linear_v1``'s: ``a0`` as before; ``aA`` log-normal with
#: ``linear_v1``'s mean 1 and variance 0.25; ``b = aA − aR`` log-normal with ``linear_v1``'s mean 0.5 and variance
#: 0.5 (the two independent variances of 0.25 add; sd 0.71). A seed by judgment, labelled, as the linear one.
_AA = _log_normal(COMBINER_PRIOR_MEAN[1], COMBINER_PRIOR_VARIANCE[1])
_B = _log_normal(COMBINER_PRIOR_MEAN[1] - COMBINER_PRIOR_MEAN[2], COMBINER_PRIOR_VARIANCE[1] + COMBINER_PRIOR_VARIANCE[2])
MONOTONE_PRIOR_MEAN: tuple[float, float, float] = (COMBINER_PRIOR_MEAN[0], _AA[0], _B[0])
MONOTONE_PRIOR_VARIANCE: tuple[float, float, float] = (COMBINER_PRIOR_VARIANCE[0], _AA[1], _B[1])
#: Retrievability is kept inside (0, 1) before its logit: numerical only (an exact 1 right after a review).
_R_CLIP = 1e-4
#: Newton's iterations and tolerance for the combiner's Laplace fit (numerical resolution, not a judgement).
_FIT_ITERATIONS = 50
_FIT_TOLERANCE = 1e-9


def sigmoid(x: np.ndarray | float) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-np.asarray(x, dtype=np.float64)))


def logit(p: np.ndarray | float) -> np.ndarray:
    p = np.clip(np.asarray(p, dtype=np.float64), _R_CLIP, 1.0 - _R_CLIP)
    return np.log(p) - np.log1p(-p)


@dataclass(frozen=True)
class Combiner:
    """The combination's coefficients: a posterior mean and variance each (diagonal), on ``form``'s parameters:
    ``(a0, aA, aR)`` for :data:`FORM_LINEAR`, ``(a0, log aA, log(aA − aR))`` for :data:`FORM_MONOTONE`."""

    mean: tuple[float, float, float] = COMBINER_PRIOR_MEAN
    variance: tuple[float, float, float] = COMBINER_PRIOR_VARIANCE
    n: int = 0
    source: str = "prior"
    #: The follow-up batch (item 2): how many rows each source gave the fit (the randomized checks, the traces'
    #: joined outcomes) and the join's counts; None before it, so the trace keeps its predecessor's bytes.
    sources: Mapping[str, Any] | None = None
    form: str = FORM_LINEAR

    def as_dict(self) -> dict[str, object]:
        out: dict[str, object] = {"mean": [round(v, 6) for v in self.mean],
                                  "variance": [round(v, 6) for v in self.variance],
                                  "n": self.n, "source": self.source, "version": MEMORY_MODEL_VERSION}
        if self.sources is not None:
            out["sources"] = dict(self.sources)
            out["fit_version"] = COMBINER_FIT_VERSION
        if self.form != FORM_LINEAR:
            # Landing ruling R6: the parameters' meaning, and the slopes' posterior means on their own scale.
            point = self.at_mean().coefficients(np.zeros((1, 3)))[0]
            out["form"] = self.form
            out["coefficients_at_mean"] = {"a0": round(float(point[0]), 6), "aA": round(float(point[1]), 6),
                                           "aR": round(float(point[2]), 6)}
        return out

    def coefficients(self, z: np.ndarray) -> np.ndarray:
        """``(a0, aA, aR)`` per row of standard normal draws ``z`` shaped ``(K, 3)``: the posterior's draws."""

        m = np.array(self.mean, dtype=np.float64)
        sd = np.sqrt(np.maximum(np.array(self.variance, dtype=np.float64), 0.0))
        theta = m[None, :] + sd[None, :] * z
        if self.form == FORM_LINEAR:
            return theta
        a_eta = np.exp(theta[:, 1])
        b = np.exp(theta[:, 2])
        return np.stack([theta[:, 0], a_eta, a_eta - b], axis=1)

    def at_mean(self) -> "Combiner":
        """No parameter uncertainty, each coefficient at its posterior mean (the belief's own world): a log-normal
        slope's mean is ``exp(μ + σ²/2)``, not its median."""

        if self.form == FORM_LINEAR:
            return replace(self, variance=(0.0, 0.0, 0.0))
        m, v = self.mean, self.variance
        return replace(self, mean=(m[0], m[1] + v[1] / 2.0, m[2] + v[2] / 2.0), variance=(0.0, 0.0, 0.0))


def monotone_prior(**fields: Any) -> Combiner:
    """Landing ruling R6's labelled prior (:data:`FORM_MONOTONE`)."""

    return Combiner(mean=MONOTONE_PRIOR_MEAN, variance=MONOTONE_PRIOR_VARIANCE, form=FORM_MONOTONE, **fields)


def features(eta: np.ndarray, retrievability: np.ndarray | None, practiced: np.ndarray) -> np.ndarray:
    """The combiner's design columns ``(1, η, (logit R − η)·[practiced])``, stacked on the last axis."""

    eta = np.asarray(eta, dtype=np.float64)
    gap = np.zeros_like(eta)
    if retrievability is not None:
        gap = np.where(practiced, logit(retrievability) - eta, 0.0)
    return np.stack([np.ones_like(eta), eta, gap], axis=-1)


def perform(coefficients: np.ndarray, eta: np.ndarray, retrievability: np.ndarray, practiced: np.ndarray) -> np.ndarray:
    """``P(perform)``: ``coefficients`` shaped ``(K, 3)`` against ``(K, N)`` sensors."""

    a0 = coefficients[:, 0:1]
    a_eta = coefficients[:, 1:2]
    a_r = coefficients[:, 2:3]
    gap = np.where(practiced, logit(retrievability) - eta, 0.0)
    return sigmoid(a0 + a_eta * eta + a_r * gap)


def fit_combiner(rows: Sequence[tuple[float, float | None, int]], prior: Combiner | None = None) -> Combiner:
    """The posterior of the combiner on ``(η, R or None, outcome 0/1)`` rows: a Laplace approximation by damped
    Newton on the log posterior (diagonal Gaussian prior). With no rows, the prior itself."""

    prior = prior or Combiner()
    if not rows:
        return prior
    eta = np.array([row[0] for row in rows], dtype=np.float64)
    practiced = np.array([row[1] is not None for row in rows])
    r = np.array([row[1] if row[1] is not None else 0.5 for row in rows], dtype=np.float64)
    y = np.array([float(row[2]) for row in rows], dtype=np.float64)
    if prior.form == FORM_MONOTONE:
        return _fit_monotone(eta, r, practiced, y, prior)
    x = features(eta, r, practiced)
    m0 = np.array(prior.mean, dtype=np.float64)
    p0 = 1.0 / np.array(prior.variance, dtype=np.float64)
    beta = m0.copy()

    def objective(b: np.ndarray) -> float:
        z = x @ b
        return float(np.sum(y * z - np.logaddexp(0.0, z)) - 0.5 * np.sum(p0 * (b - m0) ** 2))

    current = objective(beta)
    for _ in range(_FIT_ITERATIONS):
        p = sigmoid(x @ beta)
        gradient = x.T @ (y - p) - p0 * (beta - m0)
        hessian = -(x.T * (p * (1 - p))) @ x - np.diag(p0)
        step = np.linalg.solve(hessian, -gradient)
        scale = 1.0
        while scale > 1e-6:
            candidate = beta + scale * step
            value = objective(candidate)
            if value >= current:
                break
            scale /= 2.0
        beta, previous = beta + scale * step, current
        current = objective(beta)
        if abs(current - previous) < _FIT_TOLERANCE:
            break
    p = sigmoid(x @ beta)
    precision = (x.T * (p * (1 - p))) @ x + np.diag(p0)
    covariance = np.linalg.inv(precision)
    return Combiner(mean=tuple(float(v) for v in beta), variance=tuple(float(max(v, 1e-12)) for v in np.diag(covariance)),
                    n=len(rows), source="laplace_fit")


def _fit_monotone(eta: np.ndarray, r: np.ndarray, practiced: np.ndarray, y: np.ndarray, prior: Combiner) -> Combiner:
    """Landing ruling R6: the Laplace fit on :data:`FORM_MONOTONE`'s parameters ``θ = (a0, log aA, log b)``.

    ``logit P = a0 + aA·u + b·v`` with ``(u, v) = (logit R, η − logit R)`` for a practised row and ``(η, 0)`` for an
    unpractised one: :func:`perform`'s form with ``aR = aA − b``. Damped Newton on the log posterior (Fisher scoring
    where the observed Hessian is not negative definite); the posterior's variance from the observed Hessian at the
    mode (Fisher's if that one is not), so the fitted slopes are log-normal and positive in every draw."""

    lr = logit(r)
    u = np.where(practiced, lr, eta)
    v = np.where(practiced, eta - lr, 0.0)
    m0 = np.array(prior.mean, dtype=np.float64)
    p0 = 1.0 / np.array(prior.variance, dtype=np.float64)

    def z_of(t: np.ndarray) -> np.ndarray:
        return t[0] + math.exp(t[1]) * u + math.exp(t[2]) * v

    def objective(t: np.ndarray) -> float:
        z = z_of(t)
        return float(np.sum(y * z - np.logaddexp(0.0, z)) - 0.5 * np.sum(p0 * (t - m0) ** 2))

    def derivatives(t: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        p = sigmoid(z_of(t))
        jac = np.stack([np.ones_like(u), math.exp(t[1]) * u, math.exp(t[2]) * v], axis=1)
        gradient = jac.T @ (y - p) - p0 * (t - m0)
        fisher = -(jac.T * (p * (1 - p))) @ jac - np.diag(p0)
        curvature = np.diag([0.0, float(np.sum((y - p) * jac[:, 1])), float(np.sum((y - p) * jac[:, 2]))])
        return gradient, fisher, fisher + curvature

    def negative_definite(h: np.ndarray) -> bool:
        return bool(np.all(np.linalg.eigvalsh((h + h.T) / 2.0) < 0))

    theta = m0.copy()
    current = objective(theta)
    for _ in range(_FIT_ITERATIONS):
        gradient, fisher, hessian = derivatives(theta)
        step = np.linalg.solve(hessian if negative_definite(hessian) else fisher, -gradient)
        scale = 1.0
        while scale > 1e-6:
            if objective(theta + scale * step) >= current:
                break
            scale /= 2.0
        theta, previous = theta + scale * step, current
        current = objective(theta)
        if abs(current - previous) < _FIT_TOLERANCE:
            break
    _gradient, fisher, hessian = derivatives(theta)
    covariance = np.linalg.inv(-(hessian if negative_definite(hessian) else fisher))
    return Combiner(mean=tuple(float(v) for v in theta),
                    variance=tuple(float(max(v, 1e-12)) for v in np.diag(covariance)), n=len(y),
                    source="laplace_fit", form=FORM_MONOTONE)


# -- FSRS, vectorized ---------------------------------------------------------------------------------

D_MIN, D_MAX, S_MIN = 1.0, 10.0, 0.001


@dataclass(frozen=True)
class Fsrs:
    """:mod:`learnloop.scheduling.fsrs`'s formulas over arrays (ratings: 1 again, 3 good)."""

    weights: tuple[float, ...]

    # ``np.minimum(np.maximum(x, lo), hi)`` is ``np.clip(x, lo, hi)`` exactly, without its per-call overhead (the
    # follow-up batch, item 3: the tail calls these on small arrays hundreds of thousands of times a decision).

    def retrievability(self, stability: np.ndarray, elapsed: np.ndarray) -> np.ndarray:
        w = self.weights
        decay = w[20]
        factor = 0.9 ** (1 / -decay) - 1
        raw = np.asarray(stability, dtype=np.float64)
        s = np.maximum(raw, 1e-12)
        value = (1 + factor * np.maximum(np.asarray(elapsed, dtype=np.float64), 0.0) / s) ** (-decay)
        return np.minimum(np.maximum(np.where(raw > 0, value, 0.0), 0.0), 1.0)

    def _initial_difficulty(self, rating: np.ndarray) -> np.ndarray:
        w = self.weights
        return np.minimum(np.maximum(w[4] - np.exp(w[5] * (rating - 1)) + 1, D_MIN), D_MAX)

    def review(self, difficulty: np.ndarray, stability: np.ndarray, practiced: np.ndarray, elapsed: np.ndarray,
               good: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """``apply_review`` for each element: a first review where ``practiced`` is False."""

        w = self.weights
        rating = np.where(good, 3.0, 1.0)
        first_s = np.maximum(np.where(good, w[2], w[0]), S_MIN)
        first_d = self._initial_difficulty(rating)
        r = self.retrievability(stability, elapsed)
        delta = w[6] * (rating - 3)
        next_d = difficulty - delta
        easy = float(np.clip(w[4] - math.exp(w[5] * 3) + 1, D_MIN, D_MAX))
        d = np.minimum(np.maximum(w[7] * easy + (1 - w[7]) * next_d, D_MIN), D_MAX)
        s_safe = np.maximum(stability, S_MIN)
        forget = w[11] * d ** (-w[12]) * ((s_safe + 1) ** w[13] - 1) * np.exp((1 - r) * w[14])
        recall = s_safe * (1 + math.exp(w[8]) * (11 - d) * s_safe ** (-w[9]) * (np.exp((1 - r) * w[10]) - 1))
        s = np.maximum(np.where(good, recall, forget), S_MIN)
        return np.where(practiced, d, first_d), np.where(practiced, s, first_s)


__all__ = [
    "COMBINER_PRIOR_MEAN",
    "COMBINER_PRIOR_VARIANCE",
    "Combiner",
    "FORM_LINEAR",
    "FORM_MONOTONE",
    "Fsrs",
    "MEMORY_MODEL_VERSION",
    "MONOTONE_PRIOR_MEAN",
    "MONOTONE_PRIOR_VARIANCE",
    "features",
    "fit_combiner",
    "logit",
    "monotone_prior",
    "perform",
    "sigmoid",
]
