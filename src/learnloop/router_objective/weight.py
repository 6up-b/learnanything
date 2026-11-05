"""RO4 §8.7: learning the weight ``w`` between the two policies from one common return, frozen before the draw.

For decision ``i`` the uses ``𝒰_i`` (topic-days ``(L, d)`` in scope of any active goal or retention commitment at
``t_i``, ``d`` in ``(t_i, t_i + B]``, plus every dated use with its date in the window), their weights ``v_iu``,
the baselines ``m⁰_iu`` (the pre-action memory forecast under the tail) and ``C⁰_i`` are frozen in the trace
before the draw. With ``d_i(a) = π_L,i(a) − π_Q,i(a)``:

```
D̂_i = (d_i(A_i) / μ_i(A_i)) · [ Σ_u v_iu·(R_iu / r_iu)·(Y_iu − m⁰_iu) − (C_i − C⁰_i) ]
```

``Σ_a d_i(a) = 0``, so the baselines only reduce variance and do not change the target (``tests/test_ro4_weight.py``
checks the invariance). No action-specific model prediction enters it: ``π_Q`` maximizes ``Q̄``, so scoring with
``Q̄`` would make it win by construction, and an unchecked use contributes nothing.

**What carries no score**: a window holding no valued use with ``r > 0`` (effort alone would favour whichever
policy recommends less study); a decision where either policy fell back to the staged rule (its own report row);
a decision where the policies agree (``d = 0``). Until RO5's randomized checks exist no window holds an ``r > 0``
use, so **no score forms and ``w`` stays at its prior**, and the trace says so.

**The posterior over Δ**: one global Gaussian, prior ``N(m₀, s₀²)`` with ``p₀ = (w₀ − ℓ_L)/(1 − ℓ_L − ℓ_Q)``,
``m₀ = Φ⁻¹(p₀)·s₀``; scores grouped in consecutive ``2B``-day bins by decision time for the variance; with fewer
than two bins holding scores the posterior stays at its prior. ``w_i`` reads only scores whose windows closed
before ``t_i`` (no peeking), so ``μ_i`` never depends on outcomes inside its own window.

A leaf: the standard library only.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from statistics import NormalDist
import math
from typing import Any

WEIGHT_VERSION = "posterior_matching_v1"
#: Why a decision carries no score.
NO_RANDOMIZED_USE = "no_valued_use_with_r_positive"
FALLBACK = "a_policy_fell_back"
AGREE = "policies_agree"
PENDING = "window_open"
NO_RESULT = "no_result"

_NORMAL = NormalDist()


@dataclass(frozen=True)
class Seeds:
    w0: float = 0.8
    ell_l: float = 0.1
    ell_q: float = 0.1
    s0: float = 0.01
    window_days: int = 14

    @classmethod
    def from_config(cls, config: Any) -> "Seeds":
        section = getattr(config, "router_objective", None)
        return cls(w0=float(getattr(section, "llm_weight_prior", 0.8)),
                   ell_l=float(getattr(section, "llm_min_share", 0.1)),
                   ell_q=float(getattr(section, "numeric_min_share", 0.1)),
                   s0=float(getattr(section, "delta_prior_sd", 0.01)),
                   window_days=int(getattr(section, "evaluation_window_days", 14)))

    @property
    def p0(self) -> float:
        return (self.w0 - self.ell_l) / (1.0 - self.ell_l - self.ell_q)

    @property
    def m0(self) -> float:
        return _NORMAL.inv_cdf(self.p0) * self.s0


@dataclass(frozen=True)
class Use:
    """One frozen use of a decision's common return."""

    key: str              # "L:<lo>:<day>" or "G:<goal>:<lo>"
    weight: float         # v_iu
    baseline: float       # m⁰_iu
    #: the observation probability r_iu (0: no randomized check can observe it)
    r: float = 0.0
    #: the realized outcome Y_iu and whether it was observed (R_iu)
    observed: bool = False
    outcome: float | None = None


@dataclass(frozen=True)
class Scored:
    decision_id: str
    decided_at: str
    window_closes_at: str
    value: float | None
    reason: str | None = None


def score(*, d_taken: float, mu_taken: float, uses: Sequence[Use], cost: float, cost_baseline: float) -> float:
    """``D̂_i`` for one decision whose window has closed (module docstring)."""

    if mu_taken <= 0:
        raise ValueError("the taken action's probability must be positive")
    total = 0.0
    for use in uses:
        if use.observed and use.r > 0 and use.outcome is not None:
            total += use.weight * (1.0 / use.r) * (float(use.outcome) - use.baseline)
    return (d_taken / mu_taken) * (total - (cost - cost_baseline))


def carries_score(*, uses: Sequence[Use], failed: Sequence[str], d_taken: float, d_all: Mapping[str, float]) -> str | None:
    """None when the decision carries a score, else why not (§8.7 "What carries no score")."""

    if failed:
        return FALLBACK
    if all(abs(value) <= 1e-15 for value in d_all.values()):
        return AGREE
    if not any(use.r > 0 for use in uses):
        return NO_RANDOMIZED_USE
    return None


@dataclass(frozen=True)
class Posterior:
    mean: float
    sd: float
    n: int
    bins: int
    p: float
    source: str
    censored: Mapping[str, int] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {"mean": self.mean, "sd": self.sd, "n": self.n, "bins": self.bins, "p": self.p, "source": self.source,
                "censored": dict(self.censored), "version": WEIGHT_VERSION}


def _parse(stamp: str) -> datetime:
    return datetime.fromisoformat(str(stamp).replace("Z", "+00:00"))


def posterior(scores: Iterable[Scored], seeds: Seeds, *, at: str | None = None) -> Posterior:
    """The Gaussian posterior over ``Δ`` from the closed scores (those whose window closed before ``at``)."""

    closed: list[Scored] = []
    censored: dict[str, int] = {}
    cut = _parse(at) if at else None
    for entry in scores:
        if entry.value is None:
            censored[entry.reason or "unknown"] = censored.get(entry.reason or "unknown", 0) + 1
            continue
        if cut is not None and _parse(entry.window_closes_at) >= cut:
            censored[PENDING] = censored.get(PENDING, 0) + 1
            continue
        closed.append(entry)
    m0, s0 = seeds.m0, seeds.s0
    prior = Posterior(mean=m0, sd=s0, n=len(closed), bins=0, p=_NORMAL.cdf(m0 / s0), source="prior", censored=censored)
    if not closed:
        return prior
    n = len(closed)
    mean = sum(entry.value for entry in closed) / n  # type: ignore[misc]
    start = min(_parse(entry.decided_at) for entry in closed)
    width = timedelta(days=2 * seeds.window_days)
    groups: dict[int, float] = {}
    for entry in closed:
        index = int((_parse(entry.decided_at) - start) / width)
        groups[index] = groups.get(index, 0.0) + (float(entry.value) - mean)  # type: ignore[arg-type]
    if len(groups) < 2:
        return Posterior(mean=m0, sd=s0, n=n, bins=len(groups), p=prior.p, source="prior_fewer_than_two_bins",
                         censored=censored)
    v_hat = sum(total ** 2 for total in groups.values()) / (n * n)
    if v_hat <= 0:
        return Posterior(mean=m0, sd=s0, n=n, bins=len(groups), p=prior.p, source="prior_zero_variance",
                         censored=censored)
    precision = 1.0 / s0 ** 2 + 1.0 / v_hat
    post_mean = (m0 / s0 ** 2 + mean / v_hat) / precision
    post_sd = math.sqrt(1.0 / precision)
    return Posterior(mean=post_mean, sd=post_sd, n=n, bins=len(groups), p=_NORMAL.cdf(post_mean / post_sd),
                     source="posterior", censored=censored)


def unique_assessments(links: Iterable[tuple[str, str]]) -> int:
    """The report's count of unique completed assessments: one check linked to several decisions counts once
    (``links``: ``(assessment id, decision id)``)."""

    return len({assessment for assessment, _decision in links})


def weight(p: float, seeds: Seeds) -> float:
    """``w_i = ℓ_L + (1 − ℓ_L − ℓ_Q)·p_i``: posterior probability matching at the policy level."""

    return seeds.ell_l + (1.0 - seeds.ell_l - seeds.ell_q) * float(p)


__all__ = [
    "AGREE", "FALLBACK", "NO_RANDOMIZED_USE", "NO_RESULT", "PENDING", "Posterior", "Scored", "Seeds", "Use",
    "WEIGHT_VERSION", "carries_score", "posterior", "score", "unique_assessments", "weight",
]
