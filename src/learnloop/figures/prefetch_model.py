"""Reader RW5d P5: the prefetch decision model (spec_reader_show_me_figures_v1 §10b.3, §10b.5, §15).

Whether to build a candidate figure ahead of need is a learned decision,
never a threshold. For a candidate ``i``::

    EU_i = P(open_i | built, cue) * W_tier(i) * u.minute  -  C_i

* ``P(open | built, cue)``: a logistic model,
  ``logit P = beta_kind[trigger] + alpha * logit(p_open_content) + beta_src[source]``,
  its coefficients latent with seeded, labelled priors and updated by
  assumed-density filtering (:func:`learnloop.adf_numeric.adf_update`, AD's
  step) from the ledger's closed, built decisions (``opened`` = 1,
  ``neither`` = 0, in time order). ``beta_kind[k] = m + d_k``: a shared level
  ``m`` (prior N(0, 1.5^2), basis ``legacy``, debt) and per-trigger
  deviations ``d_k ~ N(0, tau^2)``, partially pooled, with ``tau`` a
  posterior over the a-priori grid :data:`POOLING_GRID` (AD's ``ad_hyper_v1``
  mechanism: each grid point's filter accumulates its log normalizer and the
  grid weights are the normalized likelihoods). ``beta_src[s] ~ N(0,
  sigma^2)``, shrunk to 0, ``sigma`` on the same grid. ``alpha`` has prior
  N(1, 1^2), basis ``llm_content``: believe the judge's stated probability
  until the data say otherwise. A candidate the judge gave no probability
  (an offer, a lesson node) has no ``alpha`` term.
* ``W_tier``: the wait a prebuild saves, in learner minutes: the log-normal
  mean of the measured pressed build latency of each tier (rich tiers: the
  pressed request to its stored figure; the quick tiers: the author call's
  measured duration), mixed by the tier mix measured for this trigger kind
  (else the pressed tier mix; with no mix measured yet, the author call's
  measured duration, the wait every press has at least). No measured
  tier: no estimate, and the candidate waits (structural: no data, no
  prebuild).
* ``C_i``: what the build can take from foreground use. On the plan the money
  is zero; the cost is ``P(usage-limit pause | today's plan load + this
  build's expected requests) * E[foreground minutes blocked by a pause]``. The
  pause probability is a logistic in the standardized day's plan load
  (:meth:`PausePosterior.load`: the day's requests with the known tokens in
  them, a request with no reported tokens counting as one measured average
  request; Codex review F14), priors centre -3 and slope 1.5, each sd 2, basis
  ``legacy`` (debt), filtered from ``plan_usage_pauses`` and the days' loads;
  a build's expected requests are measured (:class:`Incremental`: the author
  calls per authored request, plus the rich calls per rich job times the
  trigger kind's measured rich share);
  the blocked minutes are measured (pressed requests that failed inside past
  pauses, times the measured call latency). Nothing measured: no cost.
* ``u.minute``: one learner minute, the unit both terms are in (LP §6: an
  owner preference, not fitted). It scales both terms alike, so the sign of
  EU (the decision) never depends on it; stored values are minutes.
* **Thompson sampling.** One draw of every coefficient from the posterior
  decides; the logged propensity is the share of :data:`POSTERIOR_DRAWS`
  draws (Monte Carlo resolution: ``keep``) that would build. No epsilon, no
  margin: the posterior's own uncertainty explores.

Pure numerics over rows the caller read: no vault, repository, model client
or clock. Posteriors are never stored (spec §13.2b): recomputed at decision
time from the ledger, a pure read over a few hundred rows. Predicts opening
behaviour, never knowledge; outside the learner model (SM8), never evidence.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from learnloop.adf_numeric import adf_update, normalized_log_weights

MODEL_VERSION = "prefetch_decision_v1"
TRIGGER_KINDS: tuple[str, ...] = ("plan", "section", "offer", "lesson", "gap")
RICH_TIERS: tuple[str, ...] = ("js_animation", "manim")
QUICK_TIERS: tuple[str, ...] = ("grammar", "sketch")

# -- the seeded priors (spec §15's learn rows; each registered in params/parameter_registry.py) ----------
#: alpha (judge-trust slope): the identity map as the centre, basis llm_content.
ALPHA_PRIOR_MEAN = 1.0
ALPHA_PRIOR_SD = 1.0
#: beta_kind's shared level: no population data, so LP §3.0's widest un-sourced prior, basis legacy (debt).
KIND_PRIOR_MEAN = 0.0
KIND_PRIOR_SD = 1.5
#: The a-priori grid of the pooling scales (tau for the per-trigger deviations, sigma for the
#: per-source offsets), uniform: a structural form, the resolution of the scale's posterior.
POOLING_GRID: tuple[float, ...] = (0.25, 0.5, 1.0, 1.5, 2.0)
#: The pause-risk logistic's intercept and slope (per standardized unit of plan load), basis legacy (debt).
PAUSE_INTERCEPT_PRIOR_MEAN = -3.0
PAUSE_INTERCEPT_PRIOR_SD = 2.0
PAUSE_SLOPE_PRIOR_MEAN = 1.5
PAUSE_SLOPE_PRIOR_SD = 2.0
#: keep (numerical): Monte Carlo resolution of the logged propensity (spec §15: 64).
POSTERIOR_DRAWS = 64
#: Clip of the judge's probability before its logit (numerical: a stated 0 or 1 stays finite).
P_CONTENT_CLIP = 1e-4


def _logit(p: float) -> float:
    p = min(max(float(p), P_CONTENT_CLIP), 1.0 - P_CONTENT_CLIP)
    return math.log(p / (1.0 - p))


def _sigmoid(x: float) -> float:
    if x >= 0:
        return 1.0 / (1.0 + math.exp(-x))
    z = math.exp(x)
    return z / (1.0 + z)


def _log_lik(y: int):
    def log_likelihood(eta: np.ndarray) -> np.ndarray:
        eta = np.clip(eta, -700.0, 700.0)
        return -np.logaddexp(0.0, -eta) if y else -np.logaddexp(0.0, eta)
    return log_likelihood


# ---------------------------------------------------------------------------
# The opening model
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Observation:
    """One closed, built decision: its trigger, source, judge probability and whether it was opened."""

    trigger_kind: str
    source: str | None
    p_open_content: float | None
    opened: bool


@dataclass
class _Filter:
    mean: np.ndarray
    cov: np.ndarray
    log_z: float = 0.0


@dataclass
class OpenPosterior:
    """A mixture over the pooling grid of Gaussian posteriors on the opening coefficients."""

    sources: tuple[str, ...]
    grid: tuple[tuple[float, float], ...]
    weights: np.ndarray
    means: list[np.ndarray]
    covs: list[np.ndarray]
    observations: int

    # State layout: [alpha, m, d_plan..d_gap, src_0..src_{S-1}].
    def _index(self, kind: str) -> int:
        return 2 + TRIGGER_KINDS.index(kind)

    def features(self, trigger_kind: str, source: str | None, p_open_content: float | None) -> np.ndarray:
        h = np.zeros(2 + len(TRIGGER_KINDS) + len(self.sources))
        if p_open_content is not None:
            h[0] = _logit(p_open_content)
        h[1] = 1.0
        h[self._index(trigger_kind)] = 1.0
        if source is not None and source in self.sources:
            h[2 + len(TRIGGER_KINDS) + self.sources.index(source)] = 1.0
        return h

    def summary(self) -> dict[str, Any]:
        """Prior to posterior on alpha and beta_kind (LP §3.3 contraction), for the report."""

        mean = sum(w * m for w, m in zip(self.weights, self.means))
        second = sum(w * (c + np.outer(m, m)) for w, m, c in zip(self.weights, self.means, self.covs))
        cov = second - np.outer(mean, mean)

        def entry(index: int, prior_mean: float, prior_sd: float) -> dict[str, Any]:
            return {"prior": {"mean": prior_mean, "sd": prior_sd},
                    "posterior": {"mean": round(float(mean[index]), 4),
                                  "sd": round(math.sqrt(max(float(cov[index, index]), 0.0)), 4)}}

        kinds: dict[str, Any] = {}
        for kind in TRIGGER_KINDS:
            h = np.zeros(len(mean))
            h[1] = 1.0
            h[self._index(kind)] = 1.0
            kind_sd = math.sqrt(KIND_PRIOR_SD ** 2 + sum(
                (1.0 / len(self.grid)) * tau ** 2 for tau, _ in self.grid))
            kinds[kind] = {"prior": {"mean": KIND_PRIOR_MEAN, "sd": round(kind_sd, 4)},
                           "posterior": {"mean": round(float(h @ mean), 4),
                                         "sd": round(math.sqrt(max(float(h @ cov @ h), 0.0)), 4)}}
        return {"observations": self.observations, "alpha": entry(0, ALPHA_PRIOR_MEAN, ALPHA_PRIOR_SD),
                "beta_kind": kinds,
                "pooling_grid": [{"tau": tau, "sigma": sigma, "weight": round(float(w), 4)}
                                 for (tau, sigma), w in zip(self.grid, self.weights)]}

    def sample(self, rng: np.random.Generator) -> np.ndarray:
        index = int(rng.choice(len(self.weights), p=self.weights))
        return rng.multivariate_normal(self.means[index], self.covs[index], method="cholesky")


def _prior(sources: Sequence[str], tau: float, sigma: float) -> _Filter:
    size = 2 + len(TRIGGER_KINDS) + len(sources)
    mean = np.zeros(size)
    mean[0] = ALPHA_PRIOR_MEAN
    mean[1] = KIND_PRIOR_MEAN
    variances = np.full(size, sigma ** 2)
    variances[0] = ALPHA_PRIOR_SD ** 2
    variances[1] = KIND_PRIOR_SD ** 2
    variances[2:2 + len(TRIGGER_KINDS)] = tau ** 2
    return _Filter(mean, np.diag(variances))


def open_posterior(observations: Iterable[Observation]) -> OpenPosterior:
    """Filter the closed, built decisions (in the order given: time order) on every grid point."""

    rows = [row for row in observations if row.trigger_kind in TRIGGER_KINDS]
    sources = tuple(sorted({row.source for row in rows if row.source}))
    grid = tuple((tau, sigma) for tau in POOLING_GRID for sigma in POOLING_GRID)
    filters = [_prior(sources, tau, sigma) for tau, sigma in grid]
    probe = OpenPosterior(sources, grid, np.ones(len(grid)) / len(grid), [], [], 0)
    for row in rows:
        h = probe.features(row.trigger_kind, row.source, row.p_open_content)
        for state in filters:
            state.mean, state.cov, update = adf_update(state.mean, state.cov, h, _log_lik(1 if row.opened else 0))
            state.log_z += update.log_z
    weights = normalized_log_weights(np.array([state.log_z for state in filters]))
    return OpenPosterior(sources, grid, weights, [state.mean for state in filters],
                         [state.cov for state in filters], len(rows))


# ---------------------------------------------------------------------------
# The pause-risk model and the blocked minutes
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class PlanDay:
    """One past local day with plan activity: its load and whether a usage-limit pause was hit.
    ``tokens`` are the known tokens, reported by ``requests_with_tokens`` of the requests."""

    requests: int
    tokens: int
    paused: bool
    requests_with_tokens: int = 0


def tokens_per_request(days: Iterable[PlanDay]) -> float | None:
    """The measured mean tokens of a request that reported them, or None (none reported)."""

    rows = list(days)
    reported = sum(day.requests_with_tokens for day in rows)
    tokens = sum(day.tokens for day in rows if day.requests_with_tokens)
    return tokens / reported if reported and tokens > 0 else None


@dataclass
class PausePosterior:
    mean: np.ndarray
    cov: np.ndarray
    load_mean: float
    load_sd: float
    days: int
    pauses: int
    #: The measured mean tokens per reporting request (None: no tokens reported yet).
    per_request: float | None = None

    def standardized(self, load: float) -> float:
        return 0.0 if self.load_sd <= 0 else (float(load) - self.load_mean) / self.load_sd

    def load(self, day: PlanDay) -> float:
        return plan_load(day, self.per_request)

    def summary(self) -> dict[str, Any]:
        return {"days": self.days, "pauses": self.pauses,
                "intercept": {"prior": {"mean": PAUSE_INTERCEPT_PRIOR_MEAN, "sd": PAUSE_INTERCEPT_PRIOR_SD},
                              "posterior": {"mean": round(float(self.mean[0]), 4),
                                            "sd": round(math.sqrt(max(float(self.cov[0, 0]), 0.0)), 4)}},
                "slope": {"prior": {"mean": PAUSE_SLOPE_PRIOR_MEAN, "sd": PAUSE_SLOPE_PRIOR_SD},
                          "posterior": {"mean": round(float(self.mean[1]), 4),
                                        "sd": round(math.sqrt(max(float(self.cov[1, 1]), 0.0)), 4)}}}


def plan_load(day: PlanDay | Mapping[str, Any], per_request: float | None = None) -> float:
    """A day's plan load in requests, with the known tokens in it (spec §10b.3: "the day's plan
    requests, plus tokens where known"; Codex review F14). Tokens are reported for some routes
    only, so missingness is explicit: a request that reported its tokens counts as its tokens
    over the measured mean tokens per reporting request (``per_request``), and a request that
    reported none counts as one average request. With no tokens ever reported the load is the
    requests."""

    if isinstance(day, Mapping):
        day = PlanDay(int(day.get("requests") or 0), int(day.get("tokens") or 0), bool(day.get("paused")),
                      int(day.get("requests_with_tokens") or 0))
    reported = min(int(day.requests_with_tokens), int(day.requests))
    if not per_request or reported <= 0:
        return float(day.requests)
    return float(day.requests - reported) + float(day.tokens) / float(per_request)


def pause_posterior(days: Sequence[PlanDay]) -> PausePosterior:
    per_request = tokens_per_request(days)
    loads = [plan_load(day, per_request) for day in days]
    load_mean = float(np.mean(loads)) if loads else 0.0
    load_sd = float(np.std(loads)) if len(loads) >= 2 else 0.0
    mean = np.array([PAUSE_INTERCEPT_PRIOR_MEAN, PAUSE_SLOPE_PRIOR_MEAN])
    cov = np.diag([PAUSE_INTERCEPT_PRIOR_SD ** 2, PAUSE_SLOPE_PRIOR_SD ** 2])
    posterior = PausePosterior(mean, cov, load_mean, load_sd, len(days), sum(1 for day in days if day.paused),
                               per_request)
    for day, load in zip(days, loads):
        h = np.array([1.0, posterior.standardized(load)])
        posterior.mean, posterior.cov, _update = adf_update(posterior.mean, posterior.cov, h,
                                                            _log_lik(1 if day.paused else 0))
    return posterior


# ---------------------------------------------------------------------------
# W_tier: the measured wait
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Waits:
    """Per tier, the log-normal mean of the measured pressed build latency (minutes), and the tier mixes."""

    minutes: Mapping[str, float]
    counts: Mapping[str, int]
    pressed_mix: Mapping[str, float]
    mix_by_kind: Mapping[str, Mapping[str, float]] = field(default_factory=dict)

    def expected(self, trigger_kind: str) -> float | None:
        """The expected minutes a prebuild for this trigger kind saves, or None (no measured tier)."""

        mix = self.mix_by_kind.get(trigger_kind) or self.pressed_mix
        if not mix:
            # No tier mix measured yet: the author's call, which every build makes and every press
            # waits for, is the wait a prebuild saves at least (the quick tiers' measured duration).
            quick = [self.minutes[tier] for tier in QUICK_TIERS if tier in self.minutes]
            return min(quick) if quick else None
        known = {tier: share for tier, share in mix.items() if tier in self.minutes and share > 0}
        if not known:
            return None
        total = sum(known.values())
        return sum(self.minutes[tier] * share / total for tier, share in known.items())

    def summary(self) -> dict[str, Any]:
        return {"minutes_by_tier": {tier: round(value, 3) for tier, value in sorted(self.minutes.items())},
                "measured_builds_by_tier": dict(sorted(self.counts.items())),
                "pressed_tier_mix": {tier: round(value, 4) for tier, value in sorted(self.pressed_mix.items())},
                "tier_mix_by_trigger": {kind: {tier: round(value, 4) for tier, value in sorted(mix.items())}
                                        for kind, mix in sorted(self.mix_by_kind.items())}}


def lognormal_mean(minutes: Sequence[float]) -> float | None:
    values = [math.log(value) for value in minutes if value and value > 0]
    if not values:
        return None
    mu = float(np.mean(values))
    var = float(np.var(values)) if len(values) >= 2 else 0.0
    return math.exp(mu + var / 2.0)


def _mix(tiers: Iterable[str]) -> dict[str, float]:
    found = [tier for tier in tiers if tier]
    if not found:
        return {}
    return {tier: found.count(tier) / len(found) for tier in sorted(set(found))}


def waits(latencies: Mapping[str, Sequence[float]], pressed_tiers: Sequence[str],
          prefetch_tiers_by_kind: Mapping[str, Sequence[str]] | None = None) -> Waits:
    minutes: dict[str, float] = {}
    counts: dict[str, int] = {}
    for tier, values in latencies.items():
        mean = lognormal_mean(values)
        if mean is not None:
            minutes[tier] = mean
            counts[tier] = len([value for value in values if value and value > 0])
    by_kind = {kind: _mix(tiers) for kind, tiers in (prefetch_tiers_by_kind or {}).items() if tiers}
    return Waits(minutes, counts, _mix(pressed_tiers), by_kind)


# ---------------------------------------------------------------------------
# The decision
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Incremental:
    """What one prebuild adds to the plan's load, measured (Codex review F14): the figure author's
    calls per authored request (a repair is a second call), and the rich author's calls per
    rich job. None: not measured yet, so the structural minimum, one call."""

    author_calls: float | None = None
    rich_calls: float | None = None

    def expected(self, rich_share: float) -> float:
        return (self.author_calls or 1.0) + max(0.0, float(rich_share)) * (self.rich_calls or 1.0)


@dataclass(frozen=True)
class Candidate:
    trigger_kind: str
    source: str | None
    p_open_content: float | None
    #: The build's expected plan requests (:meth:`Model.expected_requests`, measured).
    expected_requests: float = 1.0


@dataclass(frozen=True)
class Decision:
    build: bool
    sampled_eu: float | None
    propensity: float
    w_minutes: float | None
    cost_minutes: float | None
    p_open: float | None
    reason: str


@dataclass
class Model:
    """Everything a decision reads, recomputed from the ledger."""

    opening: OpenPosterior
    pause: PausePosterior
    waits: Waits
    #: Measured foreground minutes a pause blocked, per pause (None: none measured).
    blocked_minutes: float | None
    #: Today's plan load so far (:meth:`PausePosterior.load`: requests with the known tokens).
    load_today: float
    #: What a prebuild adds to the load, measured.
    incremental: Incremental = field(default_factory=Incremental)

    def expected_requests(self, trigger_kind: str) -> float:
        """The plan requests a prebuild for this trigger kind is expected to make: the author's
        measured calls, plus the rich calls times the kind's measured rich share (else the
        pressed builds' share)."""

        mix = self.waits.mix_by_kind.get(trigger_kind) or self.waits.pressed_mix
        return self.incremental.expected(sum(share for tier, share in mix.items() if tier in RICH_TIERS))

    def digest(self) -> str:
        """The posterior's identity, so an audit can recompute a decision."""

        payload = {
            "version": MODEL_VERSION,
            "opening": {"sources": list(self.opening.sources), "weights": [round(float(w), 10) for w in self.opening.weights],
                        "means": [[round(float(v), 10) for v in mean] for mean in self.opening.means],
                        "observations": self.opening.observations},
            "pause": {"mean": [round(float(v), 10) for v in self.pause.mean], "days": self.pause.days,
                      "load": [self.pause.load_mean, self.pause.load_sd]},
            "waits": self.waits.summary(), "blocked_minutes": self.blocked_minutes, "load_today": self.load_today,
            "incremental": [self.incremental.author_calls, self.incremental.rich_calls],
            "per_request": self.pause.per_request,
        }
        return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()

    def _draw(self, rng: np.random.Generator, candidate: Candidate, wait: float) -> tuple[float, float, float]:
        coefficients = self.opening.sample(rng)
        h = self.opening.features(candidate.trigger_kind, candidate.source, candidate.p_open_content)
        p_open = _sigmoid(float(h @ coefficients))
        cost = 0.0
        if self.blocked_minutes:
            pause = rng.multivariate_normal(self.pause.mean, self.pause.cov, method="cholesky")
            z = self.pause.standardized(self.load_today + candidate.expected_requests)
            cost = _sigmoid(float(pause[0] + pause[1] * z)) * self.blocked_minutes
        return p_open * wait - cost, p_open, cost

    def decide(self, candidate: Candidate, rng: np.random.Generator) -> Decision:
        """One Thompson draw decides (build iff its EU > 0); the propensity is the share of
        :data:`POSTERIOR_DRAWS` further draws that would build."""

        wait = self.waits.expected(candidate.trigger_kind)
        if wait is None:
            return Decision(False, None, 0.0, None, None, None, "no measured build latency for this kind yet")
        eu, p_open, cost = self._draw(rng, candidate, wait)
        builds = sum(1 for _ in range(POSTERIOR_DRAWS) if self._draw(rng, candidate, wait)[0] > 0)
        return Decision(eu > 0, eu, builds / POSTERIOR_DRAWS, p_open * wait, cost, p_open,
                        "sampled EU positive" if eu > 0 else "sampled EU not positive")


__all__ = [
    "ALPHA_PRIOR_MEAN",
    "ALPHA_PRIOR_SD",
    "KIND_PRIOR_MEAN",
    "KIND_PRIOR_SD",
    "MODEL_VERSION",
    "PAUSE_INTERCEPT_PRIOR_MEAN",
    "PAUSE_INTERCEPT_PRIOR_SD",
    "PAUSE_SLOPE_PRIOR_MEAN",
    "PAUSE_SLOPE_PRIOR_SD",
    "POOLING_GRID",
    "POSTERIOR_DRAWS",
    "P_CONTENT_CLIP",
    "QUICK_TIERS",
    "RICH_TIERS",
    "TRIGGER_KINDS",
    "Candidate",
    "Decision",
    "Incremental",
    "Model",
    "Observation",
    "OpenPosterior",
    "PausePosterior",
    "PlanDay",
    "Waits",
    "lognormal_mean",
    "open_posterior",
    "pause_posterior",
    "plan_load",
    "tokens_per_request",
    "waits",
]
