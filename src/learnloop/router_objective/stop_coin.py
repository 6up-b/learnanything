"""RO5 §9 item 1: the stop coin, stop's return model and the hand-over of ``κ0`` from its seed to a posterior.

**The coin.** At a reversible block boundary of the objective's frame (stop in the support beside at least one
block), before the mix's draw and independent of it (its own seeded uniform, stream ``stop_coin``), one arm:

| Arm | Probability | Served |
|---|---|---|
| ``offer_stop`` | ``p`` (``stop_coin``, 0.05) | the stop offer |
| ``present_next`` | ``p`` | the mix's draw if it is a block; where the mix drew stop, a block drawn from ``μ`` restricted to the blocks (its own uniform) |
| ``policy`` | ``1 − 2p`` | the mix's draw |

So the served distribution is ``P(a) = p·1[a = stop] + p·μ_ns(a) + (1 − 2p)·μ(a)`` with ``μ_ns(a) = μ(a)/(1 − μ(stop))``
off stop, exactly, and logged (:func:`served_distribution`). The randomized action is the **offer**: acceptance
and "keep going" stay in the outcome (RO0's ``stop_response`` and ``end`` rows). The availability the learner
had (the session's minutes, the plan's remembered and offered minutes, the session's availability receipt) is
frozen into the assignment before the coin's uniform is read. A decision whose arm is not ``policy`` carries no
§8.7 score (``stop_coin_forced``): its action was not the mix's; a ``policy`` decision's ``μ`` is the mix's
conditional distribution, exactly, since the coin is independent of it.

**κ0's hand-over** (§8.6, "it ends the daily re-centring"). Until the first randomized offer has a response, ``κ0``
is the daily seed (RO4). From then on it is a posterior the seed is folded into, and the daily re-centring stops:

* the prior is ``log κ0 ~ N(log κ_s, σ²)``, ``κ_s`` the seed in force at the first randomized offer (frozen; it
  never moves again) and ``σ = kappa_prior_log_sd`` (a labelled seed, 0.7: about a factor of two);
* the likelihood is a logistic choice on the log ratio of the next block's forecast gain to its price, Luce's
  form: ``P(continue | offered stop) = G / (G + κ0·c)``, ``G`` the next block's value before its own price minus
  the accepted stop's (from the decision's trace), ``c = ((m + d)² − m²)/(2m̄)`` its price per unit ``κ0``. Every
  offered stop with a response enters (randomized ones and the mix's own: the gain is in the likelihood, so the
  mix's timing is conditioned on), voluntary stops do not (their selection is not identified);
* ``κ0`` serves ``exp(E[log κ0 | data])`` on a log grid: with no observation that is the seed exactly, so the
  hand-over is continuous. No threshold: the regime changes at the first randomized response because that is
  when the posterior first holds randomized evidence; the seed's prior stays folded in for good.

The tail's own attention cost stays at the decision's ``κ0`` in ``G`` (a first-order likelihood, said in the
trace). Availability is logged beside each observation; its coefficient is not fitted at this version.

**The return model.** Stop's return distribution given session minutes: the learner's own gaps (RO4) shifted by
``exp(b·(x − m̄)/m̄)``, ``x`` the session's active minutes at its end, ``b ~ N(b̂, s²)``. ``b`` is identified by the
coin alone (Codex review F3): the randomized offer against present-next, in its logged probabilities, is an
instrument for where the session ends, with the availability frozen before the draw as covariates
(:func:`fit_return_slope`); realized minutes are never treated as randomized, so acceptance and overrides stay
inside the outcome and a busy day that shortens the session and lengthens the gap cancels in the contrast (the
observational form is rejected, T9). Prior ``N(0, return_slope_prior_sd²)``. It enters ``V`` once the coin's
contrast has an observed return; before, it is its prior mean (no effect) and the trace says so. On the rollouts'
daily grid a shift that never changes the day of return has no effect at all: the trace then says the model
dropped out ("attendance near-deterministic").

A leaf: the standard library (numpy for one least-squares fit); the reads take a connection.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime
import json
import math
from typing import Any

from learnloop.router import mixture as mx

VERSION = "ro5_stop_coin_v1"
KAPPA_VERSION = "kappa_posterior_luce_v1"
RETURN_VERSION = "return_slope_coin_instrument_v2"
OFFER_STOP = "offer_stop"
PRESENT_NEXT = "present_next"
POLICY = "policy"
ARMS: tuple[str, ...] = (OFFER_STOP, PRESENT_NEXT, POLICY)
STOP = "stop_for_today"
#: Why a decision carries no §8.7 score: the coin, not the mix, chose what was served.
FORCED = "stop_coin_forced"
#: κ0's regimes.
SEED_REGIME = "seed"
POSTERIOR_REGIME = "posterior"
POSTERIOR = "posterior_from_stop_offers"
#: The κ0 posterior's log grid: multiples of the seed (numerical resolution, not a judgement).
GRID = tuple(math.exp(-4.0 + 8.0 * i / 160) for i in range(161))
_TINY = 1e-12


def arm_probabilities(rate: float) -> dict[str, float]:
    p = float(rate)
    return {OFFER_STOP: p, PRESENT_NEXT: p, POLICY: 1.0 - 2.0 * p}


@dataclass(frozen=True)
class Coin:
    arm: str
    u: float
    rate: float
    #: the arm's exact probability
    propensity: float
    served: str
    #: the exact probability the served action had under the coin and the mix together
    served_propensity: float
    #: the uniform that picked a block where ``present_next`` overrode a drawn stop (None otherwise)
    u_next: float | None = None
    availability: Mapping[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {"version": VERSION, "arm": self.arm, "u": self.u, "rate": self.rate, "propensity": self.propensity,
                "served": self.served, "served_propensity": self.served_propensity, "u_next": self.u_next,
                "availability": dict(self.availability), "arms": arm_probabilities(self.rate)}


def eligible(support: Sequence[str]) -> bool:
    """A reversible boundary the coin applies at: stop beside at least one block."""

    return STOP in support and any(ref != STOP for ref in support)


def served_distribution(mu: Mapping[str, float], rate: float, support: Sequence[str]) -> dict[str, float]:
    """``P(served = a)`` under the coin and the mix together (module docstring), exactly."""

    p = float(rate)
    stop_mass = float(mu.get(STOP, 0.0))
    rest = 1.0 - stop_mass
    out = {}
    for ref in support:
        nonstop = (float(mu.get(ref, 0.0)) / rest) if ref != STOP and rest > 0 else 0.0
        out[ref] = p * (1.0 if ref == STOP else 0.0) + p * nonstop + (1.0 - 2.0 * p) * float(mu.get(ref, 0.0))
    return out


def flip(seed: str, rate: float, *, support: Sequence[str], mu: Mapping[str, float], drawn: str,
         availability: Mapping[str, Any]) -> Coin:
    """The coin for one decision: its arm from its own uniform (never the mix's), and what is served."""

    u = mx.uniform(seed, "stop_coin")
    probabilities = arm_probabilities(rate)
    arm = OFFER_STOP if u < probabilities[OFFER_STOP] else (
        PRESENT_NEXT if u < probabilities[OFFER_STOP] + probabilities[PRESENT_NEXT] else POLICY)
    served, u_next = drawn, None
    if arm == OFFER_STOP:
        served = STOP
    elif arm == PRESENT_NEXT and drawn == STOP:
        blocks = [ref for ref in support if ref != STOP]
        mass = {ref: float(mu.get(ref, 0.0)) for ref in blocks}
        total = sum(mass.values())
        u_next = mx.uniform(seed, "stop_coin_next")
        if total <= 0:  # pragma: no cover - the floor keeps every option positive
            served = blocks[0]
        else:
            served = mx._pick(blocks, {ref: value / total for ref, value in mass.items()}, u_next)
    distribution = served_distribution(mu, rate, support)
    return Coin(arm=arm, u=u, rate=float(rate), propensity=probabilities[arm], served=served,
                served_propensity=distribution[served], u_next=u_next, availability=dict(availability))


def pending_assignment(coin: Coin, *, seed: str, support: Sequence[str]) -> dict[str, Any]:
    """The coin's ``policy_experiment_assignments`` row, frozen on the chooser's record and written with the
    decision (``assignments.record_pending``)."""

    from learnloop.router_objective import assignments as A

    return {"experiment_id": A.STOP_COIN, "variant": coin.arm, "propensity": coin.propensity, "seed": seed,
            "draw": coin.u, "candidate_refs": list(ARMS),
            "detail": {"version": VERSION, "rate": coin.rate, "arms": arm_probabilities(coin.rate),
                       "support": list(support), "served": coin.served, "served_propensity": coin.served_propensity,
                       "u_next": coin.u_next, "availability": dict(coin.availability),
                       "availability_logged": "before_the_draw"}}


# -- κ0's posterior --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Offer:
    """One offered stop with a response, as the likelihood reads it."""

    decision_id: str
    randomized: bool
    continued: bool
    gain: float
    cost_per_kappa: float
    availability: Mapping[str, Any] = field(default_factory=dict)


def offer_log_likelihood(kappa0: float, offers: Sequence[Offer]) -> float:
    """Luce's form: ``P(continue) = G / (G + κ0·c)``; an offer whose forecast gain is not positive carries no
    information about ``κ0`` (the same probability on every grid point) and is skipped."""

    total = 0.0
    for offer in offers:
        if offer.gain <= 0 or offer.cost_per_kappa <= 0:
            continue
        price = kappa0 * offer.cost_per_kappa
        p = offer.gain / (offer.gain + price)
        p = min(max(p, _TINY), 1.0 - _TINY)
        total += math.log(p) if offer.continued else math.log(1.0 - p)
    return total


def kappa_posterior(seed: float, log_sd: float, offers: Sequence[Offer]) -> dict[str, Any]:
    """The posterior over ``log κ0`` on a grid around the frozen seed; serves ``exp(E[log κ0])``."""

    if seed <= 0:
        return {"status": "no_positive_seed", "kappa0": 0.0, "n": len(offers)}
    logs = []
    for multiple in GRID:
        value = seed * multiple
        z = math.log(multiple) / log_sd
        logs.append(-0.5 * z * z + offer_log_likelihood(value, offers))
    top = max(logs)
    weights = [math.exp(value - top) for value in logs]
    norm = sum(weights)
    mean_log = sum(math.log(seed * m) * w for m, w in zip(GRID, weights)) / norm
    var_log = sum((math.log(seed * m) - mean_log) ** 2 * w for m, w in zip(GRID, weights)) / norm
    used = [offer for offer in offers if offer.gain > 0 and offer.cost_per_kappa > 0]
    return {"status": "posterior", "kappa0": math.exp(mean_log), "log_mean": mean_log, "log_sd": math.sqrt(var_log),
            "seed": seed, "prior_log_sd": log_sd, "n": len(offers), "informative": len(used),
            "randomized": sum(1 for offer in offers if offer.randomized), "version": KAPPA_VERSION,
            "label": "preference plus model error"}


def _decision_stop_responses(connection: Any) -> dict[str, str]:
    """Each stop decision's response: ``overridden`` (a stop_response naming it) or ``accepted`` (an end naming
    it, the offered stop taken). A stop with neither is still open."""

    try:
        rows = connection.execute(
            "SELECT stop_decision_id, kind, end_reason FROM session_receipts WHERE stop_decision_id IS NOT NULL "
            "AND kind IN ('stop_response', 'end') ORDER BY created_at, id").fetchall()
    except Exception:  # noqa: BLE001 - below migration 243: no responses
        return {}
    out: dict[str, str] = {}
    for decision_id, kind, reason in rows:
        if kind == "stop_response":
            out[str(decision_id)] = "overridden"
        elif reason == "offered_stop_accepted" and str(decision_id) not in out:
            out[str(decision_id)] = "accepted"
    return out


def _gain(trace: Mapping[str, Any]) -> tuple[float | None, float | None]:
    """The next block's forecast gain before its own price, over the accepted stop, and that price per κ0."""

    candidates = trace.get("candidates") or {}
    stop = candidates.get(STOP) or {}
    accepted = (stop.get("branches") or {}).get("accepted")
    blocks = [(ref, entry) for ref, entry in candidates.items() if ref != STOP and (entry.get("terms") or {}).get("q")
              is not None]
    if accepted is None or not blocks:
        return None, None
    ref, entry = max(blocks, key=lambda pair: float(pair[1]["terms"]["q"]))
    terms = entry["terms"]
    session = trace.get("session") or {}
    m = float(session.get("minutes") or 0.0)
    mbar = max(float(session.get("remembered_minutes") or 1.0), 1e-9)
    d = float(entry.get("minutes") or 0.0)
    gain = float(terms["q"]) + float(terms.get("kappa_integral") or 0.0) - float(accepted)
    return gain, ((m + d) ** 2 - m ** 2) / (2.0 * mbar)


def offers(connection: Any) -> list[Offer]:
    """Every offered stop with a response, from the traces (the decision's forecast) and RO0's receipts."""

    from learnloop.router_objective import assignments as A

    if connection.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'router_objective_traces'"
                          ).fetchone() is None:
        return []
    responses = _decision_stop_responses(connection)
    if not responses:
        return []
    coins = {str(row["unit_id"]): row for row in A.rows(connection, A.STOP_COIN)}
    out = []
    for decision_id, response in responses.items():
        row = connection.execute("SELECT trace_json, chosen_ref FROM router_objective_traces WHERE decision_id = ?",
                                 (decision_id,)).fetchone()
        if row is None or row[1] != STOP:
            continue
        trace = json.loads(row[0])
        gain, cost = _gain(trace)
        if gain is None or cost is None:
            continue
        coin = coins.get(decision_id)
        out.append(Offer(decision_id=decision_id, randomized=bool(coin is not None and coin["variant"] == OFFER_STOP),
                         continued=response == "overridden", gain=gain, cost_per_kappa=cost,
                         availability=(coin or {}).get("detail", {}).get("availability", {}) if coin else {}))
    return out


def handed_over(connection: Any, config: Any) -> dict[str, Any] | None:
    """κ0's posterior once a randomized offer has a response, else None (the daily seed stands)."""

    found = offers(connection)
    if not any(offer.randomized for offer in found):
        return None
    from learnloop.router_objective import assignments as A

    first = None
    for row in A.rows(connection, A.STOP_COIN):
        if row["variant"] == OFFER_STOP and any(o.decision_id == str(row["unit_id"]) and o.randomized for o in found):
            first = str(row["unit_id"])
            break
    seed_row = connection.execute("SELECT kappa0 FROM router_objective_traces WHERE decision_id = ?",
                                  (first,)).fetchone() if first else None
    seed = float(seed_row[0]) if seed_row is not None and seed_row[0] is not None else 0.0
    sd = float(getattr(config.router_objective, "kappa_prior_log_sd", 0.7))
    posterior = kappa_posterior(seed, sd, found)
    posterior["frozen_seed_from"] = first
    return posterior


# -- the return model ------------------------------------------------------------------------------------


@dataclass(frozen=True)
class ReturnSlope:
    """``b``'s posterior: the log return gap per remembered session of extra minutes."""

    mean: float = 0.0
    variance: float = 0.25
    n: int = 0
    source: str = "prior"

    def as_dict(self) -> dict[str, Any]:
        return {"mean": self.mean, "variance": self.variance, "n": self.n, "source": self.source,
                "version": RETURN_VERSION}


@dataclass(frozen=True)
class ReturnRow:
    """One randomized coin with its session's outcome, as the return model reads it (Codex review F3).

    ``weight`` is the coin's contrast in its logged probabilities, ``1[offer_stop]/p − 1[present_next]/p`` (0 for
    ``policy``), so its mean over draws is exactly zero whatever came before the draw; ``covariates`` are the
    availability frozen before the draw (the session's minutes and the minutes offered, each over ``m̄``); ``z`` is
    the session's final active minutes ``(x − m̄)/m̄`` and ``y`` the log return gap: both outcomes, acceptance and
    "keep going" inside them."""

    decision_id: str
    session_id: str
    arm: str
    weight: float
    covariates: tuple[float, ...]
    z: float
    y: float


def _residuals(values: Sequence[float], design: Sequence[Sequence[float]]) -> list[float]:
    """``values`` less their least-squares fit on the pre-draw ``design`` (with an intercept): availability's own
    part of the outcome, removed for precision only (the coin's mean-zero contrast is independent of it)."""

    import numpy as np

    x = np.array([[1.0, *row] for row in design], dtype=np.float64)
    v = np.array(values, dtype=np.float64)
    coefficients, *_ = np.linalg.lstsq(x, v, rcond=None)
    return [float(r) for r in v - x @ coefficients]


def fit_return_slope(rows: Sequence[ReturnRow], prior_sd: float) -> ReturnSlope:
    """``b``, the log return gap per remembered session of extra minutes, identified by the randomized coin alone
    (Codex review F3): the coin is an instrument for where the session ends. With ``w`` each coin's mean-zero
    contrast and ``ỹ``, ``z̃`` the outcomes less their fit on the pre-draw availability,

    ``mean(w·ỹ) − b·mean(w·z̃) ~ N(0, V(b))``  (the offer's effect on the return gap is ``b`` times its effect on
    the session's minutes)

    the Anderson-Rubin form, valid however weakly the offer moves the minutes: ``V(b)`` is the pooled residual
    variance of ``ỹ − b·z̃`` over every coin times ``Σ_s (Σ_{i∈s} w_i)² / n²`` (one session's coins share its
    outcome). The posterior over ``b`` is that likelihood times the prior ``N(0, prior_sd²)`` on a grid; it serves
    its mean and variance. Realized minutes are never the treatment: a learner's busy day that shortens the session
    and lengthens the gap moves both outcomes equally under every arm, so it cancels in the contrast. With no
    randomized contrast (no offer or present-next coin in two sessions, or one that moved no minutes) the
    posterior is the prior, and an offer that barely moves minutes leaves it near the prior. Assumption, labelled:
    the offer moves the return only through the session's minutes."""

    prior = ReturnSlope(mean=0.0, variance=float(prior_sd) ** 2, n=len(rows), source="prior")
    contrasted = [row for row in rows if row.weight != 0.0]
    if len(rows) < 2 or len({row.session_id for row in contrasted}) < 2:
        return prior
    design = [row.covariates for row in rows]
    ys = _residuals([row.y for row in rows], design)
    zs = _residuals([row.z for row in rows], design)
    n = len(rows)
    a = sum(row.weight * y for row, y in zip(rows, ys)) / n
    b = sum(row.weight * z for row, z in zip(rows, zs)) / n
    if b == 0.0:
        return ReturnSlope(mean=0.0, variance=prior.variance, n=n, source="prior_no_first_stage")
    sums: dict[str, float] = {}
    for row in rows:
        sums[row.session_id] = sums.get(row.session_id, 0.0) + row.weight
    spread = sum(value * value for value in sums.values()) / (n * n)
    dof = max(n - len(design[0]) - 2, 1)  # the intercept, the covariates and b

    def variance_at(slope: float) -> float:
        return max(sum((y - slope * z) ** 2 for y, z in zip(ys, zs)) / dof * spread, _TINY)

    # The grid spans the prior and the ratio estimate with its first-order spread (numerical resolution only).
    sd = math.sqrt(prior.variance)
    wald = a / b
    wald_sd = math.sqrt(variance_at(wald)) / abs(b)
    low, high = min(-6.0 * sd, wald - 6.0 * wald_sd), max(6.0 * sd, wald + 6.0 * wald_sd)
    grid = [low + (high - low) * j / 400 for j in range(401)]
    logs = []
    for slope in grid:
        v = variance_at(slope)
        logs.append(-0.5 * (slope / sd) ** 2 - 0.5 * math.log(v) - 0.5 * (a - slope * b) ** 2 / v)
    top = max(logs)
    weights = [math.exp(value - top) for value in logs]
    norm = sum(weights)
    mean = sum(slope * w for slope, w in zip(grid, weights)) / norm
    variance = sum((slope - mean) ** 2 * w for slope, w in zip(grid, weights)) / norm
    return ReturnSlope(mean=mean, variance=variance, n=n, source="posterior_randomized_coin")


def _parse(stamp: str) -> datetime:
    return datetime.fromisoformat(str(stamp).replace("Z", "+00:00"))


def _contrast(arm: str, detail: Mapping[str, Any], propensity: float) -> float:
    """The coin's mean-zero contrast in its logged probabilities (offer against present-next)."""

    arms = detail.get("arms") or {}
    if arm == OFFER_STOP:
        p = float(arms.get(OFFER_STOP, propensity) or 0.0)
        return 1.0 / p if p > 0 else 0.0
    if arm == PRESENT_NEXT:
        p = float(arms.get(PRESENT_NEXT, propensity) or 0.0)
        return -1.0 / p if p > 0 else 0.0
    return 0.0


def return_rows(connection: Any, *, gap_minutes: float) -> list[ReturnRow]:
    """Every coin drawn in a session whose return is observed: its arm's contrast, the availability frozen before
    its draw, and its session's final minutes and return gap (:class:`ReturnRow`)."""

    from learnloop.router_objective import assignments as A
    from learnloop.router_objective import price as P

    coins = A.rows(connection, A.STOP_COIN)
    if not coins:
        return []
    sessions: dict[str, tuple[float, float] | None] = {}
    out = []
    for coin in coins:
        trace = connection.execute(
            "SELECT session_id, remembered_minutes FROM router_objective_traces WHERE decision_id = ?",
            (coin["unit_id"],)).fetchone()
        session_id = trace[0] if trace is not None else None
        if not session_id:
            continue
        mbar = max(float(trace[1] or 1.0), 1e-9)
        session_id = str(session_id)
        if session_id not in sessions:
            sessions[session_id] = None
            session = connection.execute("SELECT started_at, ended_at FROM sessions WHERE id = ?",
                                         (session_id,)).fetchone()
            later = connection.execute("SELECT MIN(started_at) FROM sessions WHERE started_at >= ? AND id != ?",
                                       (session[1], session_id)).fetchone() if session is not None and session[1] else None
            if later is not None and later[0]:
                gap_days = (_parse(later[0]) - _parse(session[1])).total_seconds() / 86400.0
                if gap_days > 0:
                    minutes, _start, _basis = P.session_active_minutes(connection, now=str(session[1]),
                                                                       gap_minutes=gap_minutes)
                    sessions[session_id] = (minutes, math.log(gap_days))
        outcome = sessions[session_id]
        if outcome is None:
            continue
        detail = coin.get("detail") or {}
        availability = detail.get("availability") or {}
        receipt = availability.get("receipt") if isinstance(availability.get("receipt"), Mapping) else {}
        offered = (receipt or {}).get("minutes_offered")
        if offered is None:
            offered = availability.get("minutes_budget")
        covariates = (float(availability.get("session_minutes") or 0.0) / mbar, float(offered or 0.0) / mbar)
        out.append(ReturnRow(decision_id=str(coin["unit_id"]), session_id=session_id, arm=str(coin["variant"]),
                             weight=_contrast(str(coin["variant"]), detail, float(coin["propensity"])),
                             covariates=covariates, z=(outcome[0] - mbar) / mbar, y=outcome[1]))
    return out


__all__ = [
    "ARMS", "Coin", "FORCED", "KAPPA_VERSION", "OFFER_STOP", "Offer", "POLICY", "POSTERIOR", "POSTERIOR_REGIME",
    "PRESENT_NEXT", "RETURN_VERSION", "ReturnRow", "ReturnSlope", "SEED_REGIME", "VERSION", "arm_probabilities", "eligible",
    "fit_return_slope", "flip", "handed_over", "kappa_posterior", "offer_log_likelihood", "offers",
    "pending_assignment", "return_rows", "served_distribution",
]
