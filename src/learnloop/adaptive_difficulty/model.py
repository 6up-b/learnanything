"""AD's model: a bank of Gaussian filters over one event skeleton (spec_adaptive_difficulty_v1 §5).

The functional core: pure numerics over numpy arrays, no vault, repository,
connection or model client. The replayer (:mod:`.replay`), the selection rule
(:mod:`.selection`), the harness arms and the simulations (``learnloop.sim``)
drive it.

**A bank.** ``B`` filters that receive the same events in the same order: the
subject view's grid points ``ξ`` (one filter per point of ``ad_hyper_v1``,
§5.6), or a simulation's learners times grid points. Every filter has the same
coordinates (they are created by the same events), with its own mean, its own
covariance and its own a-priori covariance (the coupling regression reads it,
§5.10); a row's hyperparameters ``(σ_G², χ_C, χ_Q)`` change its numbers, never
its coordinates. Rows are grouped (``groups`` x ``points``): the hyperparameter
weights ``W(ξ)`` are normalized within a group.

**The state** (§5.2): a subject level ``G:<j>``, capability offsets
``psi:<j>:<k>`` (retrieval ≡ 0), facet offsets ``F:<f>``, cell offsets
``E:<f>:<k>``, the feature effects ``β``, the signal weights ``α``, the
learning increment ``γ``, the warmth shift ``ζ`` and, in the subject view, each
reading kind's dose-curve coefficients and the verdict term. Subject, facet and
cell coordinates are created lazily, when first observed or asked about; in the
subject view a facet's or cell's topic-specific coordinate is created by
regression on its coupled facets' existing coordinates (§5.10).

**The update** (§5.6 step 4): one joint factor per attempt on the linear
projection ``η_e = ũᵀs``, with the item residual ``ε`` folded into the
``η`` quadrature (32 probabilists' Gauss-Hermite nodes), exact moment matching
of the non-Gaussian likelihood, then linear-Gaussian back-projection. Learning,
reading and verdict transitions are linear maps, so the covariance propagates
exactly. Nothing here is a hand-set weight (A5): the priors are
:mod:`.priors`'s, versioned.

Never evidence (A2, A12): nothing in this module, or anything it returns,
writes evidence, mastery, facet recall, FSRS or certification.
"""

from __future__ import annotations

import math
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from statistics import NormalDist
from typing import Any

import numpy as np

from learnloop.adaptive_difficulty import priors as P

_NORMAL = NormalDist()

#: The censored category ("not an unassisted success", §5.3).
CENSORED = -1
CATEGORIES = (0, 1, 2)


def _gauss_hermite(n: int) -> tuple[np.ndarray, np.ndarray]:
    nodes, weights = np.polynomial.hermite_e.hermegauss(n)
    return nodes.astype(np.float64), (weights / weights.sum()).astype(np.float64)


X32, W32 = _gauss_hermite(32)
X24, W24 = _gauss_hermite(24)
X5, W5 = _gauss_hermite(5)


def sigmoid(x: np.ndarray | float) -> np.ndarray:
    x = np.asarray(x, dtype=np.float64)
    return 1.0 / (1.0 + np.exp(-np.clip(x, -700.0, 700.0)))


def category_likelihood(eta: np.ndarray, guess: np.ndarray, category: np.ndarray) -> np.ndarray:
    """``P(Y = category | η)`` (§5.4's graded response), broadcasting over trailing nodes.

    ``guess`` and ``category`` have the batch shape; ``eta`` has one more
    trailing axis (nodes). ``CENSORED`` reads ``P(Y ≤ 1 | η)``."""

    guess = np.asarray(guess, dtype=np.float64)[..., None]
    category = np.asarray(category)[..., None]
    scale = 1.0 - guess - P.LAPSE
    p2 = guess + scale * sigmoid(eta)
    p1 = guess + scale * sigmoid(eta + P.KAPPA)
    return np.where(
        category == 2, p2,
        np.where(category == 1, p1 - p2, np.where(category == 0, 1.0 - p1, 1.0 - p2)),
    )


def category_probabilities(m: np.ndarray, v_total: np.ndarray, guess: np.ndarray) -> np.ndarray:
    """``P(Y = 0, 1, 2)`` with ``η ~ N(m, v_total)`` (the residual already in ``v_total``)."""

    eta = np.asarray(m)[..., None] + np.sqrt(np.maximum(v_total, 0.0))[..., None] * X32
    guess = np.asarray(guess, dtype=np.float64)[..., None]
    scale = 1.0 - guess - P.LAPSE
    p2 = (W32 * (guess + scale * sigmoid(eta))).sum(-1)
    p1 = (W32 * (guess + scale * sigmoid(eta + P.KAPPA))).sum(-1)
    return np.stack([1.0 - p1, p1 - p2, p2], axis=-1)


# -- the success curve F_x and its inverse (§5.7) -----------------------------------------

def residual_success(eta_e: np.ndarray | float, guess: float = 0.0) -> np.ndarray:
    """``F_x(η_e) = E_ε[g + (1 - g - λ)σ(η_e - aε)]``: success given the epistemic state."""

    eta_e = np.asarray(eta_e, dtype=np.float64)
    nodes = eta_e[..., None] - P.A * P.TAU0 * X32
    return guess + (1.0 - guess - P.LAPSE) * (W32 * sigmoid(nodes)).sum(-1)


_INVERSE_CACHE: dict[tuple[float, float], float] = {}


def success_inverse(p: float, guess: float = 0.0) -> float:
    """``F_x⁻¹(p)``: ±inf outside ``F_x``'s range ``(g, 1 - λ)`` (a band edge it cannot reach)."""

    key = (round(float(p), 12), round(float(guess), 12))
    cached = _INVERSE_CACHE.get(key)
    if cached is not None:
        return cached
    if p <= guess:
        value = -math.inf
    elif p >= 1.0 - P.LAPSE:
        value = math.inf
    else:
        low, high = -60.0, 60.0
        for _ in range(200):
            mid = 0.5 * (low + high)
            if float(residual_success(mid, guess)) < p:
                low = mid
            else:
                high = mid
            if high - low < 1e-12:
                break
        value = 0.5 * (low + high)
    _INVERSE_CACHE[key] = value
    return value


def _erfc(x: np.ndarray) -> np.ndarray:
    """``erfc`` by the Chebyshev fit of Numerical Recipes (fractional error < 1.2e-7 everywhere)."""

    z = np.abs(x)
    t = 1.0 / (1.0 + 0.5 * z)
    poly = -z * z - 1.26551223 + t * (1.00002368 + t * (0.37409196 + t * (0.09678418 + t * (
        -0.18628806 + t * (0.27886807 + t * (-1.13520398 + t * (1.48851587 + t * (-0.82215223 + t * 0.17087277))))))))
    ans = t * np.exp(poly)
    return np.where(x >= 0, ans, 2.0 - ans)


def normal_cdf(x: np.ndarray | float) -> np.ndarray:
    """``Φ(x)``, vectorized (see :func:`_erfc`)."""

    x = np.asarray(x, dtype=np.float64)
    return 0.5 * _erfc(-x / math.sqrt(2.0))


def _phi(x: np.ndarray) -> np.ndarray:
    return normal_cdf(x)


def band_probability(m: np.ndarray, v_e: np.ndarray, guess: float, band: tuple[float, float]) -> np.ndarray:
    """``P_band = P(p_θ ∈ band)``, exact because ``F_x`` is monotone (§5.7)."""

    m = np.asarray(m, dtype=np.float64)
    sd = np.sqrt(np.maximum(np.asarray(v_e, dtype=np.float64), 1e-300))
    upper, lower = success_inverse(band[1], guess), success_inverse(band[0], guess)

    def cdf(edge: float) -> np.ndarray:
        if edge == math.inf:
            return np.ones_like(m)
        if edge == -math.inf:
            return np.zeros_like(m)
        return _phi((edge - m) / sd)

    return np.clip(cdf(upper) - cdf(lower), 0.0, 1.0)


def expected_success(m: np.ndarray, v_e: np.ndarray, guess: float) -> np.ndarray:
    """``p̄``: the posterior predictive unassisted success, ``η ~ N(m, v_e + a²τ0²)``."""

    return category_probabilities(np.asarray(m), np.asarray(v_e) + (P.A * P.TAU0) ** 2, np.full(np.shape(m), guess))[..., 2]


# -- the bank -----------------------------------------------------------------------------

@dataclass(frozen=True)
class Regression:
    """How a new topic-specific coordinate is created (§5.10): its regressors and raw weights."""

    regressors: tuple[str, ...] = ()
    raw: tuple[float, ...] = ()
    total_strength: float = 0.0


class Structure:
    """The relatedness a bank reads when it creates a coordinate: none (the LO view, uniform sharing)."""

    def facet_regression(self, facet: str, existing: Callable[[str], bool]) -> Regression:
        return Regression()

    def cell_regression(self, facet: str, capability: str, existing: Callable[[str], bool]) -> Regression:
        return Regression()

    def coupled_facets(self, facet: str) -> tuple[str, ...]:
        return ()


@dataclass
class UpdateRecord:
    """One factor's trace (§5.6 step 6), per row."""

    prior_mean: np.ndarray
    prior_var: np.ndarray
    post_mean: np.ndarray
    post_var: np.ndarray
    category_probabilities: np.ndarray
    log_z: np.ndarray
    information: np.ndarray


def facet_name(facet: str) -> str:
    return f"F:{facet}"


def cell_name(facet: str, capability: str) -> str:
    return f"E:{facet}:{capability}"


def subject_name(subject: str) -> str:
    return f"G:{subject}"


def capability_name(subject: str, capability: str) -> str:
    return f"psi:{subject}:{capability}"


class Bank:
    """``B = groups x len(points)`` filters sharing one event skeleton (see the module docstring)."""

    def __init__(self, points: Sequence[P.HyperPoint], *, groups: int = 1, structure: Structure | None = None,
                 reading: bool = False, verdict: bool = False, rating: bool = False, timing: bool = False,
                 outside: bool = False, capacity: int = 64) -> None:
        self.points = tuple(points)
        self.groups = int(groups)
        self.P = len(self.points)
        self.B = self.groups * self.P
        self.split = np.tile(np.array([p.split for p in self.points], dtype=np.float64), self.groups)
        self.coupling = np.tile(np.array([p.coupling for p in self.points], dtype=np.float64), self.groups)
        self.implication = np.tile(np.array([p.implication for p in self.points], dtype=np.float64), self.groups)
        self.structure = structure or Structure()
        self.names: list[str] = []
        self.index: dict[str, int] = {}
        self.d = 0
        self._cap = 0
        self.mu = np.zeros((self.B, 0))
        self.S = np.zeros((self.B, 0, 0))
        self.S0 = np.zeros((self.B, 0, 0))
        self.log_w = np.zeros(self.B)
        self.last_update: dict[str, float] = {}
        self.created_at: dict[str, float] = {}
        self.topic: set[str] = set()
        self.flags = {"reading": reading, "verdict": verdict, "rating": rating, "timing": timing,
                      "outside": outside}
        self._reserve(capacity)
        shared = list(P.BETA_PRIORS) + list(P.ALPHA_PRIORS)
        if outside:
            shared.append(P.ALPHA_V1_PRIOR)
        shared += [P.GAMMA_PRIOR, P.ZETA_PRIOR]
        if reading:
            shared += list(P.READING_PRIORS)
        if verdict:
            shared += list(P.VERDICT_PRIORS)
        if rating:
            shared += list(P.RATING_PRIORS)
        if timing:
            shared += list(P.TIMING_PRIORS)
        for name, mean, var in shared:
            self._append(name, np.full(self.B, mean), np.full(self.B, var))

    # -- storage ------------------------------------------------------------------------

    def _reserve(self, capacity: int) -> None:
        if capacity <= self._cap:
            return
        mu = np.zeros((self.B, capacity))
        S = np.zeros((self.B, capacity, capacity))
        S0 = np.zeros((self.B, capacity, capacity))
        if self.d:
            mu[:, :self.d] = self.mu[:, :self.d]
            S[:, :self.d, :self.d] = self.S[:, :self.d, :self.d]
            S0[:, :self.d, :self.d] = self.S0[:, :self.d, :self.d]
        self._mu_store, self._S_store, self._S0_store = mu, S, S0
        self._cap = capacity
        self._views()

    def _views(self) -> None:
        self.mu = self._mu_store[:, :self.d]
        self.S = self._S_store[:, :self.d, :self.d]
        self.S0 = self._S0_store[:, :self.d, :self.d]

    def _append(self, name: str, mean: np.ndarray, var: np.ndarray, *, cov: np.ndarray | None = None,
                s0_row: np.ndarray | None = None, s0_var: np.ndarray | None = None, topic: bool = False) -> int:
        if name in self.index:
            raise ValueError(f"coordinate exists: {name}")
        if self.d + 1 > self._cap:
            self._reserve(max(2 * self._cap, self.d + 1))
        i = self.d
        self._mu_store[:, i] = mean
        self._S_store[:, i, :] = 0.0
        self._S_store[:, :, i] = 0.0
        self._S0_store[:, i, :] = 0.0
        self._S0_store[:, :, i] = 0.0
        if cov is not None:
            self._S_store[:, i, :i] = cov
            self._S_store[:, :i, i] = cov
        self._S_store[:, i, i] = var
        if topic:
            if s0_row is not None:
                self._S0_store[:, i, :i] = s0_row
                self._S0_store[:, :i, i] = s0_row
            self._S0_store[:, i, i] = var if s0_var is None else s0_var
            self.topic.add(name)
        self.names.append(name)
        self.index[name] = i
        self.d += 1
        self._views()
        return i

    def has(self, name: str) -> bool:
        return name in self.index

    def copy(self) -> "Bank":
        clone = object.__new__(Bank)
        clone.__dict__.update(self.__dict__)
        clone._mu_store = self._mu_store.copy()
        clone._S_store = self._S_store.copy()
        clone._S0_store = self._S0_store.copy()
        clone.log_w = self.log_w.copy()
        clone.names = list(self.names)
        clone.index = dict(self.index)
        clone.last_update = dict(self.last_update)
        clone.created_at = dict(self.created_at)
        clone.topic = set(self.topic)
        clone._views()
        return clone

    def marginalize(self, names: Iterable[str]) -> None:
        """Drop coordinates (exact for a Gaussian); only for coordinates no later event touches (sims)."""

        drop = {self.index[name] for name in names if name in self.index}
        if not drop:
            return
        keep = [i for i in range(self.d) if i not in drop]
        mu = self.mu[:, keep].copy()
        S = self.S[:, keep][:, :, keep].copy()
        S0 = self.S0[:, keep][:, :, keep].copy()
        names_kept = [self.names[i] for i in keep]
        self.d = 0
        self._mu_store[:] = 0.0
        self.d = len(keep)
        self._mu_store[:, :self.d] = mu
        self._S_store[:, :self.d, :self.d] = S
        self._S0_store[:, :self.d, :self.d] = S0
        self.names = names_kept
        self.index = {name: i for i, name in enumerate(names_kept)}
        for name in list(self.last_update):
            if name not in self.index:
                del self.last_update[name]
        self.topic = {name for name in self.topic if name in self.index}
        self._views()

    # -- lazy coordinates (§5.2, §5.10) -------------------------------------------------

    def ensure_subject(self, subject: str, at: float | None = None) -> int:
        name = subject_name(subject)
        if name in self.index:
            return self.index[name]
        self.created_at[name] = at if at is not None else 0.0
        return self._append(name, np.zeros(self.B), self.split.copy())

    def ensure_capability(self, subject: str, capability: str) -> int | None:
        prior = P.PSI_PRIORS.get(capability)
        if prior is None:
            return None
        name = capability_name(subject, capability)
        if name in self.index:
            return self.index[name]
        return self._append(name, np.full(self.B, prior[0]), np.full(self.B, prior[1]))

    def _regressed(self, name: str, regression: Regression) -> int:
        variance = (P.COLD_START_VARIANCE - self.split) / 2.0
        idx = [self.index[r] for r in regression.regressors if r in self.index]
        raw = np.array([w for r, w in zip(regression.regressors, regression.raw) if r in self.index], dtype=np.float64)
        share = (self.coupling ** 2) * min(1.0, float(regression.total_strength))
        if not idx or float(regression.total_strength) <= 0.0 or not np.any(share > 0):
            return self._append(name, np.zeros(self.B), variance, topic=True)
        S0_rr = self.S0[:, idx][:, :, idx]
        q = np.einsum("i,bij,j->b", raw, S0_rr, raw)
        scale = np.where((q > 0) & (share > 0), np.sqrt(np.where(q > 0, share * variance / np.where(q > 0, q, 1.0), 0.0)), 0.0)
        coef = scale[:, None] * raw[None, :]
        mean = np.einsum("bi,bi->b", coef, self.mu[:, idx])
        cov = np.einsum("bi,bij->bj", coef, self.S[:, idx, :])
        own = variance * (1.0 - share)
        var = np.einsum("bi,bij,bj->b", coef, self.S[:, idx][:, :, idx], coef) + own
        s0_row = np.einsum("bi,bij->bj", coef, self.S0[:, idx, :])
        return self._append(name, mean, var, cov=cov, s0_row=s0_row, s0_var=variance, topic=True)

    def ensure_facet(self, facet: str, at: float | None = None) -> int:
        name = facet_name(facet)
        if name in self.index:
            return self.index[name]
        self.created_at[name] = at if at is not None else 0.0
        return self._regressed(name, self.structure.facet_regression(facet, self.has))

    def ensure_cell(self, facet: str, capability: str, at: float | None = None) -> int:
        name = cell_name(facet, capability)
        if name in self.index:
            return self.index[name]
        self.created_at[name] = at if at is not None else 0.0
        self.last_update[name] = at if at is not None else 0.0
        return self._regressed(name, self.structure.cell_regression(facet, capability, self.has))

    def virtual(self, name: str, regression: Regression | None, *, mean: float = 0.0,
                variance: np.ndarray | None = None) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """A coordinate that does not exist yet, as it would be created now, without creating it:
        ``(coefficients over existing coordinates (B, d), mean (B,), own variance (B,))``."""

        base_var = (P.COLD_START_VARIANCE - self.split) / 2.0 if variance is None else variance
        coef_full = np.zeros((self.B, self.d))
        if regression is None:
            return coef_full, np.full(self.B, mean), base_var
        idx = [self.index[r] for r in regression.regressors if r in self.index]
        raw = np.array([w for r, w in zip(regression.regressors, regression.raw) if r in self.index], dtype=np.float64)
        share = (self.coupling ** 2) * min(1.0, float(regression.total_strength))
        if not idx or float(regression.total_strength) <= 0.0 or not np.any(share > 0):
            return coef_full, np.full(self.B, mean), base_var
        S0_rr = self.S0[:, idx][:, :, idx]
        q = np.einsum("i,bij,j->b", raw, S0_rr, raw)
        scale = np.where((q > 0) & (share > 0), np.sqrt(np.where(q > 0, share * base_var / np.where(q > 0, q, 1.0), 0.0)), 0.0)
        coef_full[:, idx] = scale[:, None] * raw[None, :]
        return coef_full, np.full(self.B, mean), base_var * (1.0 - share)

    def corr0(self, a: str, b: str) -> np.ndarray:
        """The a-priori correlation a coupling set between two topic coordinates (§5.10's ``corr₀``)."""

        if a not in self.index or b not in self.index:
            return np.zeros(self.B)
        i, j = self.index[a], self.index[b]
        denom = np.sqrt(self.S0[:, i, i] * self.S0[:, j, j])
        return np.where(denom > 0, self.S0[:, i, j] / np.where(denom > 0, denom, 1.0), 0.0)

    # -- transitions ---------------------------------------------------------------------

    def add_linear(self, target: str, coefficients: Mapping[str, np.ndarray | float]) -> None:
        """``s_target ← s_target + Σ c_j s_j`` (a linear map: the covariance propagates exactly)."""

        t = self.index[target]
        c = np.zeros((self.B, self.d))
        for name, value in coefficients.items():
            j = self.index[name]
            if j == t:
                raise ValueError("a transition may not read its own target")
            c[:, j] += np.broadcast_to(np.asarray(value, dtype=np.float64), (self.B,))
        if not np.any(c):
            return
        r = np.einsum("bij,bj->bi", self.S, c)
        q = np.einsum("bi,bi->b", r, c)
        self.mu[:, t] += np.einsum("bi,bi->b", c, self.mu)
        self.S[:, t, :] += r
        self.S[:, :, t] += r
        self.S[:, t, t] += q

    def drift(self, name: str, at: float) -> None:
        """§5.6 step 3: ``Var(e_{f,k}) += σ²_drift · Δdays`` since the cell's last update."""

        last = self.last_update.get(name, at)
        days = max(float(at) - float(last), 0.0)
        if days > 0 and name in self.index:
            i = self.index[name]
            self.S[:, i, i] += P.DRIFT_PER_DAY * days
        self.last_update[name] = max(float(at), float(last))

    def reanchor_mean(self, name: str, mean: np.ndarray | float, prior_variance: np.ndarray | float) -> None:
        """A claim moves a mean and never shrinks a variance (§5.5, Claims)."""

        i = self.index[name]
        self.mu[:, i] = np.broadcast_to(np.asarray(mean, dtype=np.float64), (self.B,))
        floor = np.broadcast_to(np.asarray(prior_variance, dtype=np.float64), (self.B,))
        self.S[:, i, i] = np.maximum(self.S[:, i, i], floor)

    # -- the factor (§5.6 step 4) --------------------------------------------------------

    def moments(self, u: np.ndarray, extra_mean: np.ndarray | None = None,
                extra_var: np.ndarray | None = None) -> tuple[np.ndarray, np.ndarray]:
        """``(m, v_e)`` of ``η_e = ũᵀs`` (plus a virtual coordinates' contribution)."""

        u = np.broadcast_to(u, (self.B, self.d))
        m = np.einsum("bi,bi->b", u, self.mu)
        v = np.einsum("bi,bij,bj->b", u, self.S, u)
        if extra_mean is not None:
            m = m + extra_mean
        if extra_var is not None:
            v = v + extra_var
        return m, np.maximum(v, 0.0)

    def update(self, u: np.ndarray, category: np.ndarray | int, guess: np.ndarray | float = 0.0,
               *, rows: np.ndarray | None = None) -> UpdateRecord:
        """One base-arm factor: §5.3's category (or the censored ``{0, 1}``) on ``η_e = ũᵀs``.

        ``rows`` (bool, ``(B,)``): the rows this event applies to (a simulation's learners
        that answered); the others are untouched."""

        u = np.array(np.broadcast_to(u, (self.B, self.d)), dtype=np.float64)
        category = np.broadcast_to(np.asarray(category), (self.B,))
        guess = np.broadcast_to(np.asarray(guess, dtype=np.float64), (self.B,))
        K = np.einsum("bij,bj->bi", self.S, u)
        m = np.einsum("bi,bi->b", u, self.mu)
        v = np.maximum(np.einsum("bi,bi->b", u, K), 0.0)
        v_total = v + (P.A * P.TAU0) ** 2
        eta = m[:, None] + np.sqrt(v_total)[:, None] * X32[None, :]
        likelihood = np.maximum(category_likelihood(eta, guess, category), 1e-300)
        z = (W32 * likelihood).sum(1)
        mean_eta = (W32 * likelihood * eta).sum(1) / z
        var_eta = np.maximum((W32 * likelihood * eta * eta).sum(1) / z - mean_eta ** 2, 0.0)
        ratio = np.where(v_total > 0, v / v_total, 0.0)
        post_m = m + ratio * (mean_eta - m)
        post_v = np.maximum(v * (1.0 - ratio) + ratio * ratio * var_eta, 0.0)
        probs = category_probabilities(m, v_total, guess)
        active = v > 1e-14
        if rows is not None:
            active = active & rows
        gain_m = np.where(active, (post_m - m) / np.where(active, v, 1.0), 0.0)
        gain_v = np.where(active, (post_v - v) / np.where(active, v * v, 1.0), 0.0)
        self.mu += gain_m[:, None] * K
        self.S += gain_v[:, None, None] * np.einsum("bi,bj->bij", K, K)
        log_z = np.log(z)
        if rows is not None:
            log_z = np.where(rows, log_z, 0.0)
        self.log_w += log_z
        info = np.where(active, 0.5 * (post_v / np.where(v > 0, v, 1.0) + (post_m - m) ** 2 / np.where(v > 0, v, 1.0)
                                        - 1.0 - np.log(np.where(post_v > 0, post_v, 1.0) / np.where(v > 0, v, 1.0))), 0.0)
        return UpdateRecord(m, v, post_m, post_v, probs, log_z, info)

    def update_joint(self, u: np.ndarray, *, category: int, guess: float = 0.0, rating: str | None = None,
                     log_latency_ratio: float | None = None) -> UpdateRecord:
        """The joint factor with the sub-arms (§5.4, §5.6 step 4): outcome, rating and timing share
        ``η`` and the residual, integrated once by tensor quadrature (32 nodes on ``η``, 5 per link).

        Censored attempts drop the rating and timing factors; timing applies to unassisted
        successes only. Rows are processed one at a time (harness arms; small banks)."""

        use_rating = self.flags["rating"] and rating is not None and category != CENSORED
        use_timing = self.flags["timing"] and log_latency_ratio is not None and category == 2
        links: list[str] = []
        if use_rating:
            links += [name for name, _m, _v in P.RATING_PRIORS]
        if use_timing:
            links += [name for name, _m, _v in P.TIMING_PRIORS]
        if not links:
            return self.update(u, category, guess)
        u = np.array(np.broadcast_to(u, (self.B, self.d)), dtype=np.float64)
        k = 1 + len(links)
        records = []
        for b in range(self.B):
            U = np.zeros((k, self.d))
            U[0] = u[b]
            for row, name in enumerate(links, start=1):
                U[row, self.index[name]] = 1.0
            mu_u = U @ self.mu[b]
            S_u = U @ self.S[b] @ U.T
            S_q = S_u.copy()
            S_q[0, 0] += (P.A * P.TAU0) ** 2
            moments = _joint_moments(mu_u, S_q, links, category=category, guess=guess, rating=rating,
                                     log_latency_ratio=log_latency_ratio)
            z, mean_q, cov_q = moments
            gain = S_u @ np.linalg.inv(S_q)
            mean_u = mu_u + gain @ (mean_q - mu_u)
            cov_u = S_u - gain @ S_u + gain @ cov_q @ gain.T
            inv_u = np.linalg.inv(S_u)
            back = self.S[b] @ U.T @ inv_u
            self.mu[b] = self.mu[b] + back @ (mean_u - mu_u)
            self.S[b] = self.S[b] + back @ (cov_u - S_u) @ back.T
            self.S[b] = 0.5 * (self.S[b] + self.S[b].T)
            self.log_w[b] += math.log(z)
            records.append((mu_u[0], S_u[0, 0], mean_u[0], cov_u[0, 0], math.log(z)))
        arr = np.array(records)
        probs = category_probabilities(arr[:, 0], arr[:, 1] + (P.A * P.TAU0) ** 2, np.full(self.B, guess))
        return UpdateRecord(arr[:, 0], arr[:, 1], arr[:, 2], arr[:, 3], probs, arr[:, 4], np.zeros(self.B))

    # -- reading the bank -----------------------------------------------------------------

    def weights(self) -> np.ndarray:
        """``W(ξ)``, normalized within each group: shape ``(groups, points)``."""

        logw = self.log_w.reshape(self.groups, self.P)
        logw = logw - logw.max(axis=1, keepdims=True)
        w = np.exp(logw)
        return w / w.sum(axis=1, keepdims=True)

    def restricted_weights(self, mask: np.ndarray) -> np.ndarray:
        """Weights renormalized over the points where ``mask`` (``(points,)``) holds."""

        logw = self.log_w.reshape(self.groups, self.P).copy()
        logw[:, ~mask] = -np.inf
        logw = logw - logw.max(axis=1, keepdims=True)
        w = np.where(mask[None, :], np.exp(logw), 0.0)
        return w / w.sum(axis=1, keepdims=True)

    def mean(self, name: str) -> np.ndarray:
        return self.mu[:, self.index[name]].copy()

    def variance(self, name: str) -> np.ndarray:
        i = self.index[name]
        return self.S[:, i, i].copy()

    def state_hash(self) -> str:
        import hashlib

        digest = hashlib.sha256()
        digest.update(",".join(self.names).encode())
        digest.update(np.ascontiguousarray(self.mu).tobytes())
        digest.update(np.ascontiguousarray(self.S).tobytes())
        digest.update(np.ascontiguousarray(self.log_w).tobytes())
        return digest.hexdigest()


def _joint_moments(mu_q: np.ndarray, S_q: np.ndarray, links: Sequence[str], *, category: int, guess: float,
                   rating: str | None, log_latency_ratio: float | None) -> tuple[float, np.ndarray, np.ndarray]:
    """``Z`` and the posterior moments of ``q = (η, links)`` by tensor Gauss-Hermite quadrature."""

    k = len(mu_q)
    L = np.linalg.cholesky(S_q + 1e-15 * np.eye(k))
    grids = [X32] + [X5] * (k - 1)
    weights = [W32] + [W5] * (k - 1)
    mesh = np.meshgrid(*grids, indexing="ij")
    wmesh = np.meshgrid(*weights, indexing="ij")
    z = np.stack([g.ravel() for g in mesh], axis=1)
    w = np.prod(np.stack([g.ravel() for g in wmesh], axis=1), axis=1)
    q = mu_q[None, :] + z @ L.T
    eta = q[:, 0]
    lik = category_likelihood(eta[None, :], np.array([guess]), np.array([category]))[0]
    names = list(links)
    if rating is not None and "rating:rho_t" in names:
        rho = np.exp(q[:, 1 + names.index("rating:rho_t")])
        c1 = q[:, 1 + names.index("rating:c1")]
        c2 = c1 + np.exp(q[:, 1 + names.index("rating:d_t")])
        lik = lik * rating_likelihood(eta, rho, c1, c2, rating)
    if log_latency_ratio is not None and "timing:nu" in names:
        nu = q[:, 1 + names.index("timing:nu")]
        omega = np.exp(q[:, 1 + names.index("timing:omega_t")])
        resid = (log_latency_ratio - (nu - omega * eta)) / P.SIGMA_LATENCY
        lik = lik * np.exp(-0.5 * resid * resid) / (math.sqrt(2.0 * math.pi) * P.SIGMA_LATENCY)
    lik = np.maximum(lik, 1e-300)
    Z = float((w * lik).sum())
    mean = (w * lik) @ q / Z
    centred = q - mean[None, :]
    cov = (centred * (w * lik)[:, None]).T @ centred / Z
    return Z, mean, cov


def rating_likelihood(eta: np.ndarray, rho: np.ndarray, c1: np.ndarray, c2: np.ndarray, rating: str) -> np.ndarray:
    """``+rating``'s ordinal link (§5.4): valid for every value of ``(c_1, d̃, ρ̃)``."""

    at_least = sigmoid(rho * eta - c1)
    easy = sigmoid(rho * eta - c2)
    if rating == "easy":
        return easy
    if rating == "about_right":
        return np.maximum(at_least - easy, 0.0)
    return 1.0 - at_least


def rating_probabilities(eta: float, rho_t: float, c1: float, d_t: float) -> dict[str, float]:
    rho, c2 = math.exp(rho_t), c1 + math.exp(d_t)
    at_least = float(sigmoid(rho * eta - c1))
    easy = float(sigmoid(rho * eta - c2))
    return {"hard": 1.0 - at_least, "about_right": at_least - easy, "easy": easy}


# -- psi-marginal information about one cell (§5.7) ----------------------------------------

def cell_information(m: np.ndarray, v_e: np.ndarray, cov_c: np.ndarray, var_c: np.ndarray,
                     guess: float = 0.0, *, chunk: int = 4096) -> np.ndarray:
    """``I(θ_c; Y | x)`` per row: 24 outer nodes over ``θ_c``, 24 inner over the rest plus ``ε``
    (the pre-registered rule, ``docs/reviews/adaptive-difficulty-ad23.md`` §1.1)."""

    m = np.asarray(m, dtype=np.float64).ravel()
    out = np.empty(m.shape)
    v_e = np.broadcast_to(np.asarray(v_e, dtype=np.float64).ravel(), m.shape)
    cov_c = np.broadcast_to(np.asarray(cov_c, dtype=np.float64).ravel(), m.shape)
    var_c = np.broadcast_to(np.maximum(np.asarray(var_c, dtype=np.float64).ravel(), 1e-300), m.shape)
    scale = 1.0 - guess - P.LAPSE
    for start in range(0, len(m), chunk):
        sl = slice(start, start + chunk)
        slope = cov_c[sl] / var_c[sl]
        cond_sd = np.sqrt(np.maximum(v_e[sl] - cov_c[sl] ** 2 / var_c[sl], 0.0) + (P.A * P.TAU0) ** 2)
        # θ_c - μ_c = sqrt(var_c) * z: the outer node shifts η's conditional mean by slope·sqrt(var_c)·z.
        cond_mean = m[sl, None] + (slope * np.sqrt(var_c[sl]))[:, None] * X24[None, :]
        eta = cond_mean[:, :, None] + cond_sd[:, None, None] * X24[None, None, :]
        p2 = guess + scale * (W24 * sigmoid(eta)).sum(-1)
        p1 = guess + scale * (W24 * sigmoid(eta + P.KAPPA)).sum(-1)
        probs = np.clip(np.stack([1.0 - p1, p1 - p2, p2], axis=-1), 1e-15, 1.0)
        marginal = (W24[None, :, None] * probs).sum(1)
        h_marginal = -(marginal * np.log(marginal)).sum(-1)
        h_cond = -(W24[None, :] * (probs * np.log(probs)).sum(-1)).sum(1)
        out[sl] = np.maximum(h_marginal - h_cond, 0.0)
    return out


# -- reading dose curves (§5.11) ----------------------------------------------------------

def dose_basis(n: float) -> tuple[float, float]:
    return tuple(1.0 - math.exp(-float(n) / h) for h in P.DOSE_SCALES)  # type: ignore[return-value]


def dose_increments(n: np.ndarray, dose: np.ndarray) -> np.ndarray:
    """:func:`dose_increment` per row, vectorized: ``(B, 2)``."""

    n = np.asarray(n, dtype=np.float64)
    after = n + np.asarray(dose, dtype=np.float64)
    scales = np.asarray(P.DOSE_SCALES, dtype=np.float64)
    return np.exp(-n[:, None] / scales[None, :]) - np.exp(-after[:, None] / scales[None, :])


def dose_increment(n: float, dose: float) -> tuple[float, float]:
    """``b_m(n + D) - b_m(n)`` for both scales: the known weights of a reading transition."""

    before, after = dose_basis(n), dose_basis(n + dose)
    return (after[0] - before[0], after[1] - before[1])


__all__ = [
    "Bank",
    "CENSORED",
    "Regression",
    "Structure",
    "UpdateRecord",
    "band_probability",
    "capability_name",
    "category_likelihood",
    "category_probabilities",
    "cell_information",
    "cell_name",
    "dose_basis",
    "dose_increment",
    "dose_increments",
    "expected_success",
    "facet_name",
    "normal_cdf",
    "rating_likelihood",
    "rating_probabilities",
    "residual_success",
    "sigmoid",
    "subject_name",
    "success_inverse",
]
