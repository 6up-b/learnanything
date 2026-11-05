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

Only parameter uncertainty is drawn (θ): a known success probability of .7 still has noisy outcomes, and that
noise is the rollouts' common random numbers, not uncertainty about the value.

The FSRS update here is :mod:`learnloop.scheduling.fsrs`'s, vectorized over draws (``tests/test_ro4_memory.py``
checks it against the scalar one). A leaf: numpy and the standard library; the FSRS weights are handed in.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
import math

import numpy as np

MEMORY_MODEL_VERSION = "fsrs_ad_logistic_v1"
#: The combiner's prior: (a0, aA, aR) means and variances (module docstring). A labelled seed.
COMBINER_PRIOR_MEAN: tuple[float, float, float] = (0.0, 1.0, 0.5)
COMBINER_PRIOR_VARIANCE: tuple[float, float, float] = (0.25, 0.25, 0.25)
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
    """The combination's coefficients (a0, aA, aR): a posterior mean and variance each (diagonal)."""

    mean: tuple[float, float, float] = COMBINER_PRIOR_MEAN
    variance: tuple[float, float, float] = COMBINER_PRIOR_VARIANCE
    n: int = 0
    source: str = "prior"

    def as_dict(self) -> dict[str, object]:
        return {"mean": [round(v, 6) for v in self.mean], "variance": [round(v, 6) for v in self.variance],
                "n": self.n, "source": self.source, "version": MEMORY_MODEL_VERSION}


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


# -- FSRS, vectorized ---------------------------------------------------------------------------------

D_MIN, D_MAX, S_MIN = 1.0, 10.0, 0.001


@dataclass(frozen=True)
class Fsrs:
    """:mod:`learnloop.scheduling.fsrs`'s formulas over arrays (ratings: 1 again, 3 good)."""

    weights: tuple[float, ...]

    def retrievability(self, stability: np.ndarray, elapsed: np.ndarray) -> np.ndarray:
        w = self.weights
        decay = w[20]
        factor = 0.9 ** (1 / -decay) - 1
        s = np.maximum(np.asarray(stability, dtype=np.float64), 1e-12)
        value = (1 + factor * np.maximum(np.asarray(elapsed, dtype=np.float64), 0.0) / s) ** (-decay)
        return np.clip(np.where(np.asarray(stability) > 0, value, 0.0), 0.0, 1.0)

    def _initial_difficulty(self, rating: np.ndarray) -> np.ndarray:
        w = self.weights
        return np.clip(w[4] - np.exp(w[5] * (rating - 1)) + 1, D_MIN, D_MAX)

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
        d = np.clip(w[7] * easy + (1 - w[7]) * next_d, D_MIN, D_MAX)
        s_safe = np.maximum(stability, S_MIN)
        forget = w[11] * d ** (-w[12]) * ((s_safe + 1) ** w[13] - 1) * np.exp((1 - r) * w[14])
        recall = s_safe * (1 + math.exp(w[8]) * (11 - d) * s_safe ** (-w[9]) * (np.exp((1 - r) * w[10]) - 1))
        s = np.maximum(np.where(good, recall, forget), S_MIN)
        return np.where(practiced, d, first_d), np.where(practiced, s, first_s)


__all__ = [
    "COMBINER_PRIOR_MEAN",
    "COMBINER_PRIOR_VARIANCE",
    "Combiner",
    "Fsrs",
    "MEMORY_MODEL_VERSION",
    "features",
    "fit_combiner",
    "logit",
    "perform",
    "sigmoid",
]
