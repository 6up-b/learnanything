from __future__ import annotations

import math
from typing import Sequence


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def sigmoid(x: float) -> float:
    if x >= 0:
        return 1.0 / (1.0 + math.exp(-x))
    z = math.exp(x)
    return z / (1.0 + z)


def empirical_quantile(values: Sequence[float], q: float) -> float:
    """Linear-interpolation empirical quantile (matches numpy's 'linear' method)."""
    if not values:
        raise ValueError("empirical_quantile requires at least one value")
    if not 0.0 <= q <= 1.0:
        raise ValueError(f"quantile must be in [0, 1], got {q}")
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    position = q * (len(ordered) - 1)
    lower = math.floor(position)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = position - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * fraction


def percentiles(
    values: Sequence[float], qs: Sequence[float] = (0.10, 0.25, 0.50, 0.75, 0.90)
) -> dict[float, float]:
    if not values:
        return {}
    ordered = sorted(values)
    return {q: empirical_quantile(ordered, q) for q in qs}


def beta_mean(alpha: float, beta: float) -> float:
    """Mean of a Beta(alpha, beta) distribution."""
    total = alpha + beta
    if total <= 0.0:
        return 0.0
    return alpha / total


def regularized_incomplete_beta(x: float, a: float, b: float) -> float:
    """Regularized incomplete beta function I_x(a, b) = Beta CDF at x.

    Lentz's continued-fraction evaluation (Numerical Recipes §6.4), stdlib-only.
    Accurate to ~1e-10 across the range relevant to Beta posteriors here.
    """

    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    ln_beta = math.lgamma(a) + math.lgamma(b) - math.lgamma(a + b)
    bt = math.exp(math.log(x) * a + math.log1p(-x) * b - ln_beta)
    # The continued fraction converges fast only for x < (a+1)/(a+b+2);
    # otherwise evaluate the symmetric complement (swap a<->b, x<->1-x). No
    # recursion: the boundary case x == (a+1)/(a+b+2) would otherwise loop.
    if x < (a + 1.0) / (a + b + 2.0):
        return bt * _beta_continued_fraction(x, a, b) / a
    return 1.0 - bt * _beta_continued_fraction(1.0 - x, b, a) / b


def _beta_continued_fraction(x: float, a: float, b: float) -> float:
    """Lentz continued fraction for the incomplete beta (NR §6.4, betacf)."""

    tiny = 1e-30
    max_iterations = 300
    epsilon = 1e-14
    qab = a + b
    qap = a + 1.0
    qam = a - 1.0
    c = 1.0
    d = 1.0 - qab * x / qap
    if abs(d) < tiny:
        d = tiny
    d = 1.0 / d
    result = d
    for m in range(1, max_iterations + 1):
        m2 = 2 * m
        # Even step.
        numerator = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + numerator * d
        if abs(d) < tiny:
            d = tiny
        c = 1.0 + numerator / c
        if abs(c) < tiny:
            c = tiny
        d = 1.0 / d
        result *= d * c
        # Odd step.
        numerator = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + numerator * d
        if abs(d) < tiny:
            d = tiny
        c = 1.0 + numerator / c
        if abs(c) < tiny:
            c = tiny
        d = 1.0 / d
        delta = d * c
        result *= delta
        if abs(delta - 1.0) < epsilon:
            break
    return result


def beta_quantile(q: float, alpha: float, beta: float) -> float:
    """Inverse Beta CDF (ppf) by bisection on the monotone regularized I_x.

    Deterministic and dependency-free; ~50 bisection steps give ~1e-15
    resolution on [0, 1], which is far tighter than the CDF's own accuracy.
    """

    if not 0.0 <= q <= 1.0:
        raise ValueError(f"quantile must be in [0, 1], got {q}")
    if alpha <= 0.0 or beta <= 0.0:
        raise ValueError("alpha and beta must be positive")
    if q <= 0.0:
        return 0.0
    if q >= 1.0:
        return 1.0
    low, high = 0.0, 1.0
    for _ in range(200):
        mid = 0.5 * (low + high)
        if regularized_incomplete_beta(mid, alpha, beta) < q:
            low = mid
        else:
            high = mid
        if high - low < 1e-15:
            break
    return 0.5 * (low + high)


def binomial_two_sided_p(successes: int, trials: int, p: float = 0.5) -> float:
    """Exact two-sided binomial tail probability under ``p`` (small ``trials``).

    Used where a rate's NULL value equals the threshold it is compared against —
    a coin-flip control whose observed share is meaningless without asking how
    surprising it is. Exact rather than normal-approximated because the counts
    these callers work with are tens, not thousands, and an approximation is
    least trustworthy exactly where the decision is closest.

    Returns 1.0 for ``trials <= 0`` (nothing observed is not evidence of
    anything), and is symmetric in the sense that it sums every outcome at most
    as probable as the observed one.
    """

    from math import comb

    if trials <= 0:
        return 1.0
    p = min(max(float(p), 0.0), 1.0)

    def pmf(k: int) -> float:
        return comb(trials, k) * (p**k) * ((1.0 - p) ** (trials - k))

    observed = pmf(successes)
    # Floating-point slack so an outcome exactly as probable as the observed one
    # (the mirror image, under p=0.5) is included rather than dropped.
    tolerance = observed * 1e-9
    return min(1.0, sum(pmf(k) for k in range(trials + 1) if pmf(k) <= observed + tolerance))
