"""The rollouts' link to adaptive difficulty: AD's own predicted success as a function of its latent ability
(:class:`AdLink`), and AD's lesson dose curve as the decision read it (:class:`LessonCurve`).

The caller hands in AD's constants and the curve's posterior (``daily_plan/objective_inputs.py`` reads them through
AD's read-only entry points), so this module imports nothing of adaptive difficulty. :mod:`types` holds both as
fields of the frozen inputs; :mod:`rollouts` reads them by attribute. This module imports only :mod:`memory`.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
import math

import numpy as np

from learnloop.router_objective.memory import sigmoid

#: The follow-up batch's landing ruling R9 (:class:`AdLink`, :attr:`Inputs.ad_link`).
AD_LINK_VERSION = "ad_predictive_link_v1"


@dataclass(frozen=True)
class AdLink:
    """Landing ruling R9: AD's own predicted success ``F(η) = g + (1 − g − λ)·E_ε[σ(η − a·τ0·ε)]``
    (``adaptive_difficulty.model.residual_success``), with ``g = 0`` (a valued topic's unseen constructed item),
    lapse ``λ``, and ``ε`` integrated by AD's own Gauss-Hermite rule; the caller hands in AD's constants, so this
    module stays a leaf. With it the rollouts' ``η`` is AD's latent ability (practice's ``γ``, reading's dose and a
    lesson add where AD adds them), and wherever the rollouts read AD's predictive (an unpractised topic, a probe,
    the combiner's ``η`` input, which is ``logit p̄``) they read ``F(η)``, not ``σ(η)``.

    Landing ruling R10: the rollouts start from AD's own latent posterior (``Topic.eta_latent``: its mean and
    variance, read through AD's read-only entry point); where only ``p̄`` and a variance exist, the mean is the inverse
    of the **variance-integrated** predictive (:meth:`p_integrated`), so the draws' predictive is ``p̄`` again."""

    lapse: float
    spread: float
    nodes: tuple[float, ...]
    weights: tuple[float, ...]
    version: str = AD_LINK_VERSION

    def __post_init__(self) -> None:
        # The quadrature's arrays and constants, built once (the rollouts call F per day, topic and draw).
        object.__setattr__(self, "_shift", self.spread * np.asarray(self.nodes, dtype=np.float64))
        object.__setattr__(self, "_w", np.asarray(self.weights, dtype=np.float64))
        object.__setattr__(self, "_keep", 1.0 - self.lapse)

    def quadrature(self, eta: np.ndarray, *, slope: bool = True) -> tuple[np.ndarray, np.ndarray | None]:
        """``F(η)`` and (``slope``) ``dF/dη`` from **one** evaluation of the quadrature's sigmoids, elementwise over
        any array of ``η`` (router speed, item 1: a caller stacks every ``η`` it needs, the draws' and the belief's,
        into one array). The same operations, in the same order, as :meth:`p` and :meth:`slope` each did alone, so
        every element's bits are theirs."""

        with np.errstate(over="ignore"):  # σ of a far-left node is 0 (the log-space path covers what underflows)
            s = sigmoid(np.asarray(eta, dtype=np.float64)[..., None] - self._shift)
        f = self._keep * (self._w * s).sum(-1)
        return f, (self._keep * (self._w * s * (1.0 - s)).sum(-1) if slope else None)

    def p(self, eta: np.ndarray) -> np.ndarray:
        return self.quadrature(eta, slope=False)[0]

    def slope(self, eta: np.ndarray) -> np.ndarray:
        """``dF/dη``."""

        return self.quadrature(eta)[1]  # type: ignore[return-value]

    def p_integrated(self, mean: np.ndarray, variance: np.ndarray) -> np.ndarray:
        """``E[F(η)]`` for ``η ~ N(mean, variance)``: ``F`` with the residual's spread widened to
        ``√(a²τ0² + variance)``, AD's own ``expected_success`` (R10). ``variance`` 0 is :meth:`p`."""

        mean = np.asarray(mean, dtype=np.float64)
        scale = np.sqrt(self.spread ** 2 + np.maximum(np.asarray(variance, dtype=np.float64), 0.0)) / self.spread
        e = mean[..., None] - scale[..., None] * self._shift
        return (1.0 - self.lapse) * (self._w * sigmoid(e)).sum(-1)

    def inverse(self, p: np.ndarray, variance: np.ndarray | float = 0.0) -> np.ndarray:
        """The mean whose variance-integrated predictive is ``p`` (``F⁻¹(p)`` at variance 0), by bisection on AD's
        range (a ``p`` at or past ``1 − λ`` is held just inside it)."""

        top = (1.0 - self.lapse) * (1.0 - 1e-9)
        target = np.clip(np.asarray(p, dtype=np.float64), 1e-9, top)
        var = np.broadcast_to(np.asarray(variance, dtype=np.float64), target.shape)
        low, high = np.full_like(target, -60.0), np.full_like(target, 60.0)
        for _ in range(200):
            mid = 0.5 * (low + high)
            below = self.p_integrated(mid, var) < target
            low, high = np.where(below, mid, low), np.where(below, high, mid)
            if float(np.max(high - low, initial=0.0)) < 1e-12:
                break
        return 0.5 * (low + high)

    def logit_and_slope(self, eta: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """``logit F(η)`` (AD's predictive on the combiner's scale) and its derivative in ``η``, never clipped
        (landing ruling R11: the combiner's own probability-logit, not FSRS's), the derivative the one of the
        transformation applied, ``F'/F + F'/(1 − F)``. ``1 − F ≥ λ``, so ``log(1 − F)`` loses nothing computed
        directly; ``log F`` is direct while ``F`` is a normal float, and in log space (log-sum-exp over the
        quadrature) where it underflows (``η`` below about −700)."""

        f, df = self.quadrature(eta)
        return self.logit_and_slope_from(eta, f, df)  # type: ignore[arg-type]

    def logit_and_slope_from(self, eta: np.ndarray, f: np.ndarray, df: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """:meth:`logit_and_slope` from ``F(η)`` and ``dF/dη`` already computed (:meth:`quadrature`)."""

        tiny = ~(f > 1e-300)
        safe = np.where(tiny, 1.0, f)
        out = np.log(safe) - np.log1p(-safe)
        slope = df / safe + df / (1.0 - safe)
        if np.any(tiny):
            log_out, log_slope = self._logit_and_slope_logspace(np.asarray(eta, dtype=np.float64)[tiny])
            out = np.array(out, copy=True)
            slope = np.array(slope, copy=True)
            out[tiny], slope[tiny] = log_out, log_slope
        return out, slope

    def logit_p(self, eta: np.ndarray) -> np.ndarray:
        """``logit F(η)`` alone, as :meth:`logit_and_slope` computes it (the rollouts' forecast path)."""

        return self.logit_p_from(eta, self.p(eta))

    def logit_p_from(self, eta: np.ndarray, f: np.ndarray) -> np.ndarray:
        """:meth:`logit_p` from ``F(η)`` already computed (:meth:`quadrature`)."""

        tiny = ~(f > 1e-300)
        safe = np.where(tiny, 1.0, f)
        out = np.log(safe) - np.log1p(-safe)
        if np.any(tiny):
            out = np.array(out, copy=True)
            out[tiny] = self._logit_and_slope_logspace(np.asarray(eta, dtype=np.float64)[tiny])[0]
        return out

    def _logit_and_slope_logspace(self, eta: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """The same in log space: ``log F``, ``log(1 − F) = log(λ + (1 − λ)·E[σ(−e)])`` and ``log F'``."""

        e = eta[..., None] - self._shift
        log_s = -np.logaddexp(0.0, -e)
        log_c = -np.logaddexp(0.0, e)
        lw = np.log(self._w)
        log_keep = math.log1p(-self.lapse)
        log_f = log_keep + _logsumexp(lw + log_s)
        log_q = np.logaddexp(math.log(self.lapse), log_keep + _logsumexp(lw + log_c))
        log_df = log_keep + _logsumexp(lw + log_s + log_c)
        return log_f - log_q, np.exp(log_df - log_f) + np.exp(log_df - log_q)


def _logsumexp(x: np.ndarray) -> np.ndarray:
    """``log Σ exp(x)`` over the last axis, stably."""

    top = np.max(x, axis=-1)
    return top + np.log(np.exp(x - top[..., None]).sum(-1))


@dataclass(frozen=True)
class LessonCurve:
    """Teacher TE3a (spec_teacher_v1 rev 5 §14.2): AD's ``lesson`` dose curve per ``landed`` dose, as the decision
    read it (``readiness.decision_state_fields``' ``lesson_curve``): its two coefficients' posterior mean and
    covariance on :attr:`Learning.dose_scales`, their seeded prior's (``prior_mean``, ``prior_cov``; None: the
    posterior's, so nothing is learned), and each topic's position ``n`` on it (its lessons since its last graded
    attempt).

    The objective values a lesson as RO4's placeholder plus what lessons have taught this curve beyond its prior
    (Codex review F2): one dose's shift at the topic's position, ``Δμ(n) = Σ_m b_m'(n)·(μ_m − μ⁰_m)``, and the change
    in that step's variance, ``Δv(n) = s(n)ᵀ(Σ − Σ⁰)s(n)`` (``s(n)`` the two scales' increments). So at the seeded
    prior the lesson is the placeholder exactly, at fitted ``γ``, at the lesson's learned mass and at any position, and
    no decision moves until lessons inform the curve."""

    mean: tuple[float, float]
    cov: tuple[tuple[float, float], tuple[float, float]]
    positions: Mapping[str, float] = field(default_factory=dict)
    version: str = "ad_lesson_priors_v1"
    source: str = "adaptive_difficulty subject view"
    prior_mean: tuple[float, float] | None = None
    prior_cov: tuple[tuple[float, float], tuple[float, float]] | None = None

    def deviation(self, n: np.ndarray, scales: tuple[float, float]) -> tuple[np.ndarray, np.ndarray]:
        """``(Δμ(n), Δv(n))`` per draw at positions ``n``: zero (exactly) while the curve is at its prior."""

        h1, h2 = scales
        n = np.asarray(n, dtype=np.float64)
        s1 = np.exp(-n / h1) - np.exp(-(n + 1.0) / h1)
        s2 = np.exp(-n / h2) - np.exp(-(n + 1.0) / h2)
        mean0 = self.prior_mean if self.prior_mean is not None else self.mean
        cov0 = self.prior_cov if self.prior_cov is not None else self.cov
        shift = s1 * (self.mean[0] - mean0[0]) + s2 * (self.mean[1] - mean0[1])
        dc = [[self.cov[i][j] - cov0[i][j] for j in (0, 1)] for i in (0, 1)]
        dvar = s1 * s1 * dc[0][0] + s1 * s2 * (dc[0][1] + dc[1][0]) + s2 * s2 * dc[1][1]
        return shift, dvar


__all__ = ["AD_LINK_VERSION", "AdLink", "LessonCurve"]
