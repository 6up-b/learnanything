"""Assumed-density filtering primitives shared by adaptive difficulty and the lesson-check weight.

Factored out of ``adaptive_difficulty.model`` (spec_teacher_v1 §12.1: "the ADF
and grid code is factored out ... into a neutral numeric module that both
import"), so the evidence-side lesson-check weight reuses AD's machinery without
importing AD (A2: AD never writes evidence or mastery, and nothing on the
evidence side reaches into AD).

* :func:`gauss_hermite`: probabilists' Gauss-Hermite nodes with weights
  normalized to 1 (the quadrature AD's filter uses);
* :func:`sigmoid`: the clipped logistic AD's filter uses;
* :func:`adf_update`: one non-Gaussian factor on a one-dimensional linear
  projection ``eta = h . x`` of a Gaussian state: exact moment matching of the
  tilted distribution by quadrature, then linear-Gaussian back-projection to
  the state (AD §5.6's step), returning the factor's log normalizer
  (``log Z``, the grid weights' increment ``W_t(xi) ∝ W_{t-1}(xi) Z_t(xi)``);
* :func:`normalized_log_weights` and :func:`gaussian_sigmoid_mean`.

Pure numerics over numpy arrays: no vault, repository or model client. The
node counts are numerical resolution (§18.4: "AD's quadrature nodes:
numerical resolution, not modelling choices").
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import numpy as np


def gauss_hermite(n: int) -> tuple[np.ndarray, np.ndarray]:
    """``n`` probabilists' Gauss-Hermite nodes and their weights, normalized to sum to 1."""

    nodes, weights = np.polynomial.hermite_e.hermegauss(n)
    return nodes.astype(np.float64), (weights / weights.sum()).astype(np.float64)


#: The quadrature of a one-dimensional factor (AD's ``X32``/``W32``).
NODES, WEIGHTS = gauss_hermite(32)


def sigmoid(x: np.ndarray | float) -> np.ndarray:
    x = np.asarray(x, dtype=np.float64)
    return 1.0 / (1.0 + np.exp(-np.clip(x, -700.0, 700.0)))


def logit(p: float) -> float:
    p = min(max(float(p), 1e-12), 1.0 - 1e-12)
    return float(np.log(p / (1.0 - p)))


@dataclass(frozen=True)
class FactorUpdate:
    """One factor's effect: the projection's moments before and after, and ``log Z``."""

    m: float
    v: float
    post_m: float
    post_v: float
    log_z: float


def adf_update(mean: np.ndarray, cov: np.ndarray, h: np.ndarray,
               log_likelihood: Callable[[np.ndarray], np.ndarray]) -> tuple[np.ndarray, np.ndarray, FactorUpdate]:
    """One factor ``exp(log_likelihood(eta))`` on ``eta = h . x`` with ``x ~ N(mean, cov)``.

    Returns the moment-matched Gaussian ``(mean', cov')`` and the factor's record.
    ``log_likelihood`` maps an array of ``eta`` values to log-likelihoods."""

    mean = np.asarray(mean, dtype=np.float64)
    cov = np.asarray(cov, dtype=np.float64)
    h = np.asarray(h, dtype=np.float64)
    k = cov @ h
    m = float(h @ mean)
    v = max(float(h @ k), 0.0)
    eta = m + np.sqrt(v) * NODES
    log_l = np.asarray(log_likelihood(eta), dtype=np.float64)
    shift = float(np.max(log_l))
    lik = np.exp(log_l - shift)
    z = float((WEIGHTS * lik).sum())
    if z <= 0.0 or v <= 1e-14:
        return mean.copy(), cov.copy(), FactorUpdate(m, v, m, v, float(np.log(max(z, 1e-300)) + shift))
    post_m = float((WEIGHTS * lik * eta).sum() / z)
    post_v = max(float((WEIGHTS * lik * eta * eta).sum() / z) - post_m * post_m, 0.0)
    gain_m = (post_m - m) / v
    gain_v = (post_v - v) / (v * v)
    new_mean = mean + gain_m * k
    new_cov = cov + gain_v * np.outer(k, k)
    new_cov = 0.5 * (new_cov + new_cov.T)
    return new_mean, new_cov, FactorUpdate(m, v, post_m, post_v, float(np.log(z) + shift))


def normalized_log_weights(log_w: np.ndarray) -> np.ndarray:
    """Grid weights ``exp(log_w)`` normalized to sum to 1."""

    log_w = np.asarray(log_w, dtype=np.float64)
    w = np.exp(log_w - np.max(log_w))
    return w / w.sum()


def gaussian_sigmoid_mean(m: float, v: float) -> float:
    """``E[sigmoid(eta)]`` for ``eta ~ N(m, v)``, by the same quadrature."""

    return float((WEIGHTS * sigmoid(m + np.sqrt(max(v, 0.0)) * NODES)).sum())


__all__ = [
    "FactorUpdate",
    "NODES",
    "WEIGHTS",
    "adf_update",
    "gauss_hermite",
    "gaussian_sigmoid_mean",
    "logit",
    "normalized_log_weights",
    "sigmoid",
]
