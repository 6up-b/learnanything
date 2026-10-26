"""The query student's decisions, as expected utility (spec_local_contextual_retrieval_v1 §9.1, §9.3, §9.5; P2).

Functional core: numpy only, no I/O, deterministic for a seed. The P2 driver
(``source_retrieval.query_student``) and the resolver call it.

No fixed margin decides anything here (owner, 2026-10-24). Every decision is

``U(a) = q(a) + b(a) - lambda * m(a) - mu * p_late(a) - nu * h(a)``

over posterior draws, acted on by ``argmax E[U]`` with ``P(a is best)`` and the
expected loss of acting now reported (spec §9.1). The terms:

* ``q`` - posterior expected Complete Evidence@10 on the labelled bank
  (:func:`bank_quality_draws`), or on development the teacher's bank quality
  times the student's teacher agreement (:func:`dev_quality_draws`);
* ``m`` - measured monthly dollars (receipts); ``h`` - GPU-hours the action
  costs (a teacher session's residency, another training round);
* ``p_late`` - the probability of missing the existing time box, a Jeffreys
  posterior on measured timings (:func:`late_draws`);
* ``lambda`` (quality per dollar) and ``nu`` (quality per GPU-hour) - learned
  from the owner's choices by a Bayesian logistic choice model on a log grid
  (:class:`ExchangeRate`), seeded from recorded owner decisions;
* ``mu`` - the quality lost when a query misses the box: the bank posterior
  of the dense arm against keyword-only when the bank has R0, else its upper
  bound (the dense arm's whole quality); ``b`` - the owner's preference
  beyond quality and money (seeded from the 2026-10-24 decision: 0, see
  :data:`PRIOR_BASIS`).

The cold-start wait (spec §5.1 item 3) is the same rule specialized: waiting
for a starting student is worth it only when ``P(in time) * w * mu`` beats
``(1 - P(in time)) * mu``, i.e. ``P(in time) > 1 / (1 + w)`` with ``w`` the
student list's weight share (:func:`should_wait`): the rule has no constant of
its own.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
import math
from typing import Any

import numpy as np

DECISION_VERSION = "student-decision-eu-v1"
#: keep (computation budget): posterior draws behind every expected utility (Monte Carlo
#: standard error of P(best) at most 0.5 / sqrt(4096) < 0.008).
DRAWS = 4096
#: keep (numerical): the log-grid resolution of an exchange-rate posterior.
RATE_GRID_POINTS = 401
#: structural: the grid spans this many prior standard deviations each side.
RATE_GRID_SPAN_SD = 6.0

#: The recorded owner decisions that seed lambda (quality per dollar): each is a spend the owner
#: approved for an experiment whose stake was the 5-point bar it was testing (E0 $25 raised to
#: $40, E1 $5). Weak, legacy; every later costed owner choice updates it.
LAMBDA_SEED_DECISIONS = ({"stake": 0.05, "usd": 25.0, "what": "E0 cap $25"},
                         {"stake": 0.05, "usd": 40.0, "what": "E0 cap raised to $40"},
                         {"stake": 0.05, "usd": 5.0, "what": "E1 cap $5"})

PRIOR_BASIS = {
    "family_pooling": "empirical: empirical Bayes (method of moments across families) per arm, the "
                      "concentration capped by the arm's own question count (structural: never pooled "
                      "harder than the data)",
    "family_rate_hyperprior": "published: Beta(1/2, 1/2) (Jeffreys) when an arm has a single family",
    "unknown_labels": "structural: imputed from the arm's own family posterior (latent, never a miss)",
    "late": "published: Jeffreys Beta(1/2, 1/2) on the measured late/in-time counts",
    "in_time": "published: Krichevsky-Trofimov estimate (count + 1/2) / (n + 1) of the measured start "
               "times within the remaining time box",
    "lambda": "legacy (weak): log-normal at the mean of the log rates the owner's recorded budget "
              "decisions imply (LAMBDA_SEED_DECISIONS), their log spread as the prior sd; updated by "
              "every costed owner choice",
    "nu": "legacy (weak): log-normal at mu / the P2 GPU-hours budget (the owner allotted at most 6 GPU-hours "
          "for all the quality a dense query encoder can bring), lambda's log spread by analogy; updated "
          "by every owner choice about GPU time",
    "mu": "legacy: the bank posterior q(dense) - q(keyword) when the bank carries R0, else its upper "
          "bound q(dense) (R0's CE@10 is not in a committed aggregate)",
    "b_local": "legacy: the smallest preference that makes the 2026-10-24 local choice optimal at E1's "
               "posterior; local costs less than Qwen at an even posterior, so it is 0",
    "choice_noise": "structural: the decision's own posterior sd of the utility difference",
    "learning_curve": "structural: log-linear in the budget between the last two measured budgets (it "
                      "over-predicts a saturating curve, so it errs toward training more)",
    "dev_quality": "structural: the student keeps the teacher's bank quality in proportion to its "
                   "teacher top-10 agreement; agreement a Jeffreys Beta on the soft counts",
}


def _rng(seed: int) -> np.random.Generator:
    return np.random.default_rng(int(seed) & 0xFFFFFFFF)


# -- probabilities from measured timings ----------------------------------------------------
def in_time_probability(start_seconds: Sequence[float], remaining_s: float) -> float:
    """P(a cold start answers within ``remaining_s``), KT-estimated from measured starts."""

    samples = [float(value) for value in start_seconds if value is not None and math.isfinite(float(value))]
    hits = sum(1 for value in samples if value <= remaining_s)
    return (hits + 0.5) / (len(samples) + 1.0)


def should_wait(start_seconds: Sequence[float], remaining_s: float, weight_share: float) -> tuple[bool, float]:
    """Spec §5.1 item 3: wait for a starting student iff ``P(in time) > 1 / (1 + w)``.

    Waiting gains ``P * w * mu`` (the student list's share of the dense
    quality, delivered in time) and risks ``(1 - P) * mu`` (the whole query
    misses the box); ``mu`` cancels, so the rule has no constant. With no
    weight on the student (``w = 0``) it never waits: the start continues in
    the background for the next query."""

    p = in_time_probability(start_seconds, remaining_s) if remaining_s > 0 else 0.0
    w = min(max(float(weight_share), 0.0), 1.0)
    return (w > 0.0 and p > 1.0 / (1.0 + w)), p


def late_draws(late: int, total: int, *, draws: int = DRAWS, seed: int = 0) -> np.ndarray:
    """Draws of ``p_late`` from measured counts (Jeffreys)."""

    late, total = int(late), int(total)
    if late < 0 or total < late:
        raise ValueError("late must be between 0 and total")
    return _rng(seed).beta(late + 0.5, total - late + 0.5, size=draws)


# -- the bank posterior ----------------------------------------------------------------------
@dataclass(frozen=True)
class ArmOutcomes:
    """One arm's per-question outcomes on the bank: ``{question: value}``, value 1 (complete
    evidence in the top 10), 0, a soft label in [0, 1] (a label-noise model's probability), or
    None (unknown: latent). ``families`` maps each question to its source family."""

    name: str
    outcomes: Mapping[str, float | None]
    families: Mapping[str, str]


def _family_counts(arm: ArmOutcomes) -> dict[str, tuple[float, int, int]]:
    """``family -> (soft successes, known count, unknown count)``."""

    counts: dict[str, list[float]] = {}
    for question, value in arm.outcomes.items():
        family = str(arm.families.get(question) or "unknown_family")
        row = counts.setdefault(family, [0.0, 0, 0])
        if value is None:
            row[2] += 1
        else:
            v = float(value)
            if not 0.0 <= v <= 1.0:
                raise ValueError(f"{arm.name}: outcome {v} of {question} is outside [0, 1]")
            row[0] += v
            row[1] += 1
    return {family: (row[0], int(row[1]), int(row[2])) for family, row in counts.items()}


def _pooling(counts: Mapping[str, tuple[float, int, int]]) -> tuple[float, float]:
    """``(m, kappa)``: the pooled rate and the Beta concentration, by method of moments."""

    k = sum(row[0] for row in counts.values())
    n = sum(row[1] for row in counts.values())
    if n == 0:
        return 0.5, 1.0
    m = min(max(k / n, 1e-6), 1 - 1e-6)
    known = [(row[0], row[1]) for row in counts.values() if row[1] > 0]
    if len(known) < 2:
        return m, 1.0  # one family: Jeffreys-strength hyperprior (Beta(m, 1-m) ~ Beta(1/2, 1/2) at m = 1/2)
    rates = np.array([kf / nf for kf, nf in known])
    sizes = np.array([nf for _kf, nf in known], dtype=float)
    between = float(np.average((rates - m) ** 2, weights=sizes))
    sampling = m * (1 - m) * float(np.mean(1.0 / sizes))
    excess = between - sampling
    ceiling = float(n)  # structural: never pooled harder than the data
    if excess <= 0:
        return m, ceiling
    return m, float(min(max(m * (1 - m) / excess - 1.0, 1e-3), ceiling))


def bank_quality_draws(arm: ArmOutcomes, *, draws: int = DRAWS, seed: int = 0) -> np.ndarray:
    """Posterior draws of an arm's population CE@10: family rates partially pooled, unknown
    labels imputed from their family's posterior, families weighted by their question counts."""

    counts = _family_counts(arm)
    if not counts:
        raise ValueError(f"{arm.name}: no outcomes")
    m, kappa = _pooling(counts)
    rng = _rng(seed)
    total = sum(row[1] + row[2] for row in counts.values())
    quality = np.zeros(draws)
    for family, (k, n, unknown) in sorted(counts.items()):
        theta = rng.beta(m * kappa + k, (1 - m) * kappa + (n - k), size=draws)
        if unknown:
            # Latent labels: imputed, then the family rate is redrawn with them (one data-augmentation sweep).
            imputed = rng.binomial(unknown, theta)
            theta = rng.beta(m * kappa + k + imputed, (1 - m) * kappa + (n - k) + (unknown - imputed))
        quality += theta * (n + unknown) / total
    return quality


def aggregate_arm(name: str, per_family: Mapping[str, tuple[float, int]]) -> ArmOutcomes:
    """An arm known only by per-family aggregates (rate, n), such as a committed report's table:
    expanded into soft outcomes so the same model applies (unpaired, wider)."""

    outcomes: dict[str, float | None] = {}
    families: dict[str, str] = {}
    for family, (rate, n) in sorted(per_family.items()):
        for index in range(int(n)):
            key = f"{family}#{index}"
            outcomes[key] = float(rate)
            families[key] = family
    return ArmOutcomes(name, outcomes, families)


def dev_quality_draws(agreements: Sequence[float], teacher_quality: np.ndarray, *, seed: int = 0) -> np.ndarray:
    """Development quality of a student run: its mean teacher top-10 agreement (a Jeffreys Beta
    on the soft counts) times the teacher's bank quality draws (:data:`PRIOR_BASIS`)."""

    values = [min(max(float(a), 0.0), 1.0) for a in agreements]
    hits = sum(values)
    rng = _rng(seed)
    recall = rng.beta(hits + 0.5, len(values) - hits + 0.5, size=len(teacher_quality))
    return recall * np.asarray(teacher_quality, dtype=float)


# -- exchange rates learned from the owner's choices ----------------------------------------
@dataclass
class ExchangeRate:
    """A log-grid posterior over a positive rate (quality per dollar, or per GPU-hour).

    Each owner choice between a costed option and its alternative is an
    observation: ``P(accept) = sigma((dq - rate * cost) / s)`` with ``s`` the
    decision's own posterior sd of ``dq`` (structural)."""

    name: str
    log_mean: float
    log_sd: float
    basis: str
    observations: list[dict[str, Any]] = field(default_factory=list)

    def grid(self) -> tuple[np.ndarray, np.ndarray]:
        logs = np.linspace(self.log_mean - RATE_GRID_SPAN_SD * self.log_sd,
                           self.log_mean + RATE_GRID_SPAN_SD * self.log_sd, RATE_GRID_POINTS)
        log_post = -0.5 * ((logs - self.log_mean) / self.log_sd) ** 2
        rates = np.exp(logs)
        for item in self.observations:
            z = (float(item["dq"]) - rates * float(item["cost"])) / max(float(item["s"]), 1e-9)
            p = 1.0 / (1.0 + np.exp(-np.clip(z, -60, 60)))
            log_post += np.log(np.clip(p if item["accepted"] else 1.0 - p, 1e-300, 1.0))
        weights = np.exp(log_post - log_post.max())
        return rates, weights / weights.sum()

    def mean(self) -> float:
        rates, weights = self.grid()
        return float(rates @ weights)

    def draws(self, count: int = DRAWS, *, seed: int = 0) -> np.ndarray:
        rates, weights = self.grid()
        return _rng(seed).choice(rates, size=count, p=weights)

    def observe(self, *, dq: float, cost: float, s: float, accepted: bool, what: str = "") -> None:
        self.observations.append({"dq": float(dq), "cost": float(cost), "s": float(s), "accepted": bool(accepted),
                                  "what": what})

    def as_dict(self) -> dict[str, Any]:
        return {"name": self.name, "log_mean": self.log_mean, "log_sd": self.log_sd, "basis": self.basis,
                "posterior_mean": self.mean(), "observations": list(self.observations)}

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "ExchangeRate":
        return cls(str(value["name"]), float(value["log_mean"]), float(value["log_sd"]), str(value["basis"]),
                   [dict(item) for item in value.get("observations") or []])


def seeded_lambda() -> ExchangeRate:
    logs = np.log([item["stake"] / item["usd"] for item in LAMBDA_SEED_DECISIONS])
    return ExchangeRate("lambda", float(logs.mean()), float(max(logs.std(ddof=1), 1e-3)), PRIOR_BASIS["lambda"])


def seeded_nu(mu: float, cap_hours: float, lam: ExchangeRate | None = None) -> ExchangeRate:
    lam = lam or seeded_lambda()
    return ExchangeRate("nu", float(math.log(max(mu, 1e-6) / max(cap_hours, 1e-6))), lam.log_sd, PRIOR_BASIS["nu"])


# -- the decision ------------------------------------------------------------------------------
@dataclass(frozen=True)
class Action:
    """One action's terms: quality draws plus its measured costs."""

    name: str
    quality: np.ndarray
    monthly_usd: float = 0.0
    late: np.ndarray | float = 0.0
    gpu_hours: float = 0.0
    preference: float = 0.0


def decide(actions: Sequence[Action], *, lam: np.ndarray | float, mu: np.ndarray | float,
           nu: np.ndarray | float = 0.0) -> dict[str, Any]:
    """``argmax E[U]`` with ``P(best)``, each action's ``E[U]`` and the expected loss of acting now."""

    if not actions:
        raise ValueError("no action to decide among")
    size = min(len(action.quality) for action in actions)
    utilities = []
    for action in actions:
        late = np.broadcast_to(np.asarray(action.late, dtype=float), (size,)) if np.ndim(action.late) == 0 \
            else np.asarray(action.late, dtype=float)[:size]
        utility = (np.asarray(action.quality, dtype=float)[:size] + action.preference
                   - np.broadcast_to(np.asarray(lam, dtype=float), (size,)) * action.monthly_usd
                   - np.broadcast_to(np.asarray(mu, dtype=float), (size,)) * late
                   - np.broadcast_to(np.asarray(nu, dtype=float), (size,)) * action.gpu_hours)
        utilities.append(utility)
    matrix = np.stack(utilities)
    expected = matrix.mean(axis=1)
    best = matrix.argmax(axis=0)
    chosen = int(np.argmax(expected))
    loss = float(matrix.max(axis=0).mean() - expected.max())
    return {"version": DECISION_VERSION, "chosen": actions[chosen].name,
            "expected_utility": {action.name: round(float(value), 6) for action, value in zip(actions, expected)},
            "p_best": {action.name: round(float(np.mean(best == index)), 4) for index, action in enumerate(actions)},
            "expected_quality": {action.name: round(float(np.mean(action.quality)), 6) for action in actions},
            "expected_loss_now": round(loss, 6), "draws": int(size)}


def difference_sd(a: np.ndarray, b: np.ndarray) -> float:
    size = min(len(a), len(b))
    return float(np.std(np.asarray(a, dtype=float)[:size] - np.asarray(b, dtype=float)[:size]))


# -- the learning curve ----------------------------------------------------------------------------
def next_round_gain(points: Sequence[tuple[int, float, float]], next_budget: int, *, draws: int = DRAWS,
                    seed: int = 0) -> np.ndarray:
    """Draws of the agreement gain at ``next_budget`` from ``(budget, mean, se)`` points, log-linear
    between the last two measured budgets (:data:`PRIOR_BASIS`). One point: no gain is predictable."""

    ordered = sorted((int(n), float(m), float(se)) for n, m, se in points)
    if len(ordered) < 2 or next_budget <= ordered[-1][0]:
        return np.zeros(draws)
    (n1, m1, s1), (n2, m2, s2) = ordered[-2], ordered[-1]
    rng = _rng(seed)
    a = rng.normal(m1, max(s1, 1e-9), size=draws)
    b = rng.normal(m2, max(s2, 1e-9), size=draws)
    slope = (b - a) / math.log(n2 / n1)
    return slope * math.log(next_budget / n2)


def continue_training(points: Sequence[tuple[int, float, float]], next_budget: int, *, hours: float,
                      hours_left: float, teacher_quality: float, nu: float, seed: int = 0) -> dict[str, Any]:
    """Spec §9.3: train another round iff its expected quality gain beats its GPU-hours, inside the cap."""

    gain = next_round_gain(points, next_budget, seed=seed)
    expected = float(np.mean(gain)) * float(teacher_quality)
    cost = float(nu) * float(hours)
    within = hours <= hours_left
    return {"continue": bool(within and expected > cost), "expected_quality_gain": round(expected, 6),
            "gpu_hours": round(float(hours), 4), "cost_in_quality": round(cost, 6), "within_cap": within,
            "basis": PRIOR_BASIS["learning_curve"]}


__all__ = ["Action", "ArmOutcomes", "DECISION_VERSION", "DRAWS", "ExchangeRate", "LAMBDA_SEED_DECISIONS",
           "PRIOR_BASIS", "aggregate_arm", "bank_quality_draws", "continue_training", "decide",
           "dev_quality_draws", "difference_sd", "in_time_probability", "late_draws", "next_round_gain",
           "seeded_lambda", "seeded_nu", "should_wait"]
