"""RO5 §9 item 1: the stop coin, stop's return model and the hand-over of ``κ0`` from its seed to a posterior.

**The coin.** At a reversible block boundary of the objective's frame (stop in the support beside at least one
block) once the session holds active minutes (landing ruling R4: the session's opening boundary is not a stop
decision, the learner has just chosen to start), before the mix's draw and independent of it (its own seeded
uniform, stream ``stop_coin``), one arm:

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
instrument for where the session ends, with the availability frozen before the session's first coin as covariates
(:func:`fit_return_slope`: one estimating contribution per session, its coins' contrasts summed, and the
Anderson-Rubin likelihood, bounded by the number of sessions so neither a weak first stage nor a few sessions can
make it certain: Codex re-review F8, F9); realized minutes are never treated as randomized, so acceptance and
overrides stay inside the outcome and a busy day that shortens the session and lengthens the gap cancels in the
contrast (the observational form is rejected, T9). Prior ``N(0, return_slope_prior_sd²)``. It enters ``V`` once the coin's
contrast has an observed return; before, it is its prior mean (no effect) and the trace says so. On the rollouts'
daily grid a shift that never changes the day of return has no effect at all: the trace then says the model
dropped out ("attendance near-deterministic").

A leaf: the standard library (numpy for one least-squares fit and the slope's integration); the reads take a
connection.
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
RETURN_VERSION = "return_slope_coin_instrument_v3"
#: The return model's identifying assumption, labelled wherever it is read (the trace's return model, the report):
#: landing ruling R6.
RETURN_ASSUMPTION = "the offer changes the return gap only through the session's minutes (an exclusion restriction)"
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


def eligible(support: Sequence[str], *, session_minutes: float | None) -> bool:
    """A reversible boundary the coin applies at: stop beside at least one block, and the session already holds
    active minutes (landing ruling R4: an offer before any active minute in the session isn't a stop decision, since
    the learner has just chosen to start; unknown minutes are not above zero)."""

    return (STOP in support and any(ref != STOP for ref in support)
            and session_minutes is not None and float(session_minutes) > 0.0)


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
                "version": RETURN_VERSION, "assumption": RETURN_ASSUMPTION}


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
    part of the outcome, removed for precision only (the coin's mean-zero contrast is independent of it). With fewer
    than two residual degrees of freedom the fit would be exact (every residual zero, or float noise): the values
    are only centred then."""

    import numpy as np

    v = np.array(values, dtype=np.float64)
    columns = 1 + (len(design[0]) if design else 0)
    if len(values) - columns < 2:
        return [float(r) for r in v - v.mean()]
    x = np.array([[1.0, *row] for row in design], dtype=np.float64)
    coefficients, *_ = np.linalg.lstsq(x, v, rcond=None)
    return [float(r) for r in v - x @ coefficients]


#: The integration's resolution (numerical, not a judgement; landing ruling R2, Codex final verify F11): nodes over
#: the prior to ``_REACH`` sds, around the likelihood's peak to ``_PEAK_SPREADS`` of its spread, and across the
#: bounds (both peaks and the region between), refined until the moments agree; the bounds widen (at most
#: ``_WIDENINGS`` times) until the tail mass beyond them is below ``_TAIL_TOLERANCE`` of the mass inside.
_REACH = 40.0
_PEAK_SPREADS = 8.0
_PRIOR_NODES = 801
_LOCAL_NODES = 401
_SPAN_NODES = 801
_REFINEMENTS = 6
_WIDENINGS = 40
_TOLERANCE = 1e-6
_TAIL_TOLERANCE = 1e-9
_COLLINEAR = 1e-12


@dataclass(frozen=True)
class _Moments:
    """The session-level sums the Anderson-Rubin statistic needs, ``U_s(b) = A_s − b·B_s``."""

    sessions: int
    sa: float
    sb: float
    saa: float
    sab: float
    sbb: float

    def ar(self, slope: float) -> float:
        """``(Σ_s U_s(b))² / Σ_s U_s(b)²``: bounded by the number of sessions (Cauchy-Schwarz), so a few sessions can
        never make the likelihood certain; 0 where every session's contribution vanishes."""

        numerator = (self.sa - slope * self.sb) ** 2
        denominator = self.saa - 2.0 * slope * self.sab + slope * slope * self.sbb
        if denominator <= 0.0:
            return 0.0
        return min(numerator / denominator, float(self.sessions))


def _session_moments(rows: Sequence[ReturnRow]) -> tuple[_Moments, int]:
    """One estimating contribution per session (Codex re-review F9). A session's coins share its outcome, so its
    contribution is ``W_s·(ỹ_s − b·z̃_s)`` with ``W_s`` the sum of its coins' contrasts, and ``ỹ_s``, ``z̃_s`` its
    outcomes less their fit on the availability frozen before its first coin (so an offer and a present-next in one
    session cancel in the moment exactly as in its variance). Returns the sums and the sessions with a contrast."""

    order: list[str] = []
    by_session: dict[str, list[ReturnRow]] = {}
    for row in rows:
        if row.session_id not in by_session:
            order.append(row.session_id)
            by_session[row.session_id] = []
        by_session[row.session_id].append(row)
    weights = [sum(row.weight for row in by_session[s]) for s in order]
    first = [by_session[s][0] for s in order]
    design = [row.covariates for row in first]
    ys = _residuals([row.y for row in first], design)
    zs = _residuals([row.z for row in first], design)
    a = [w * y for w, y in zip(weights, ys)]
    b = [w * z for w, z in zip(weights, zs)]
    moments = _Moments(sessions=len(order), sa=sum(a), sb=sum(b), saa=sum(x * x for x in a),
                       sab=sum(x * y for x, y in zip(a, b)), sbb=sum(y * y for y in b))
    return moments, sum(1 for w in weights if w != 0.0)


def _integrate(nodes: Any, log_density: Any) -> tuple[float, float, float]:
    """Trapezoidal log mass, mean and variance of ``exp(log_density)`` over sorted ``nodes`` (an array; unequal
    spacing kept). The log mass is on ``log_density``'s own scale, so it compares with a tail bound on that scale."""

    import numpy as np

    logs = log_density(nodes)
    top = float(np.max(logs))
    f = np.exp(logs - top)
    h = np.diff(nodes)
    mass = float(np.sum(0.5 * h * (f[:-1] + f[1:])))
    xf = nodes * f
    mean = float(np.sum(0.5 * h * (xf[:-1] + xf[1:]))) / mass
    vf = (nodes - mean) ** 2 * f
    variance = float(np.sum(0.5 * h * (vf[:-1] + vf[1:]))) / mass
    return math.log(mass) + top if mass > 0 else -math.inf, mean, variance


def _refine(nodes: Any) -> Any:
    import numpy as np

    out = np.empty(2 * len(nodes) - 1)
    out[0::2] = nodes
    out[1::2] = 0.5 * (nodes[:-1] + nodes[1:])
    return out


def _log_prior_tail(beyond: float, sd: float) -> float:
    """``log ∫_beyond^∞ exp(−x²/(2sd²)) dx``: the posterior's unnormalized density is at most the prior's kernel
    (``AR ≥ 0``), so this bounds the mass the integration leaves out past a bound on the log density's own scale.
    Exact through ``erfc`` while it holds a double, then the Mills bound ``(sd/x)·exp(−x²/2)``."""

    x = beyond / sd
    tail = sd * math.sqrt(math.pi / 2.0) * math.erfc(x / math.sqrt(2.0))
    if tail > 0.0:
        return math.log(tail)
    return math.log(sd / x) - 0.5 * x * x


def _nodes(sd: float, peak: tuple[float, float] | None, low: float, high: float) -> Any:
    """The prior's range, the likelihood's peak neighbourhood and the span between the bounds, merged and sorted."""

    import numpy as np

    parts = [np.linspace(-_REACH * sd, _REACH * sd, _PRIOR_NODES), np.linspace(low, high, _SPAN_NODES)]
    if peak is not None:
        parts.append(np.linspace(peak[0], peak[1], _LOCAL_NODES))
    return np.unique(np.clip(np.concatenate(parts), low, high))


def fit_return_slope(rows: Sequence[ReturnRow], prior_sd: float) -> ReturnSlope:
    """``b``, the log return gap per remembered session of extra minutes, identified by the randomized coin alone
    (Codex review F3): the coin is an instrument for where the session ends. Per session ``s``, with ``W_s`` the sum
    of its coins' mean-zero contrasts and ``ỹ_s``, ``z̃_s`` its outcomes less their fit on the availability frozen
    before its first coin, ``U_s(b) = W_s·(ỹ_s − b·z̃_s)`` has mean zero at the true ``b`` (the offer's effect on
    the return gap is ``b`` times its effect on the session's minutes).

    The likelihood is the Anderson-Rubin statistic's, ``exp(−AR(b)/2)`` with ``AR(b) = (Σ_s U_s(b))² / Σ_s U_s(b)²``
    (Codex re-review F9: the variance is the sessions' own estimating contributions, never a pooled residual times
    the weights): valid however weakly the offer moves the minutes, and bounded by the number of sessions, so a
    vanishing first stage leaves a flat likelihood (Codex re-review F8: the prior stands, never a certain slope) and
    a few sessions move the prior only by what they can carry. The posterior is that likelihood times the prior
    ``N(0, prior_sd²)``, integrated on nodes adapted to it (landing ruling R2, Codex final verify F11): the prior's
    range to ``_REACH`` sds, the likelihood's peak (the ratio estimate) to ``_PEAK_SPREADS`` of its spread wherever
    it falls, and the span between bounds that start past both and widen until the mass beyond them (bounded by the
    prior's kernel, since ``AR ≥ 0``) is below ``_TAIL_TOLERANCE`` of the mass inside; then refined until the mean
    and variance agree. Convergence needs both; one that does not converge serves the prior and says so
    (``prior_integration_unconverged``).

    Realized minutes are never the treatment: a learner's busy day that shortens the session and lengthens the gap
    moves both outcomes under every arm, so it cancels in the contrast. With no randomized contrast (sessions whose
    coins carry no net contrast in fewer than two sessions, or one that moved no minutes) the posterior is the prior.
    Assumption, labelled: the offer moves the return only through the session's minutes."""

    prior = ReturnSlope(mean=0.0, variance=float(prior_sd) ** 2, n=len(rows), source="prior")
    if len(rows) < 2 or prior_sd <= 0:
        return prior
    moments, contrasted = _session_moments(rows)
    if contrasted < 2:
        return prior
    if moments.sb == 0.0:
        return ReturnSlope(mean=0.0, variance=prior.variance, n=len(rows), source="prior_no_first_stage")
    if moments.saa * moments.sbb - moments.sab ** 2 <= _COLLINEAR * moments.saa * moments.sbb:
        # Every session's contribution is proportional (two sessions, centred, always are): the statistic is the same
        # at every slope but one point, so the sessions carry no information about b and the prior stands.
        return ReturnSlope(mean=0.0, variance=prior.variance, n=len(rows), source="prior_no_information")
    sd = float(prior_sd)
    unconverged = ReturnSlope(mean=0.0, variance=prior.variance, n=len(rows), source="prior_integration_unconverged")

    def log_density(slope: Any) -> Any:
        import numpy as np

        numerator = (moments.sa - slope * moments.sb) ** 2
        denominator = moments.saa - 2.0 * slope * moments.sab + slope * slope * moments.sbb
        safe = np.where(denominator > 0.0, denominator, 1.0)
        ar = np.where(denominator > 0.0, np.minimum(numerator / safe, float(moments.sessions)), 0.0)
        return -0.5 * (slope / sd) ** 2 - 0.5 * ar

    # Landing ruling R2 (Codex final verify F11): the grid covers the prior's peak (0), the likelihood's (the ratio
    # estimate, where AR is 0) and the region between; its bounds start past both and widen until the mass they leave
    # out is negligible against the mass inside, and convergence needs both that and the refinement's agreement.
    wald = moments.sa / moments.sb
    spread = math.sqrt(max(moments.saa - 2.0 * wald * moments.sab + wald * wald * moments.sbb, 0.0)) / abs(moments.sb)
    peak = ((wald - _PEAK_SPREADS * spread, wald + _PEAK_SPREADS * spread)
            if math.isfinite(wald) and math.isfinite(spread) and spread > 0 else None)
    low, high = -_REACH * sd, _REACH * sd
    if peak is not None:
        low, high = min(low, peak[0]), max(high, peak[1])
    log_tolerance = math.log(_TAIL_TOLERANCE)
    for _attempt in range(_WIDENINGS + 1):
        grid = _nodes(sd, peak, low, high)
        log_mass, mean, variance = _integrate(grid, log_density)
        left, right = _log_prior_tail(-low, sd), _log_prior_tail(high, sd)
        if max(left, right) - log_mass > log_tolerance - math.log(2.0):
            # Too much may lie past a bound: widen that side by half the span (the coarse grid's mass suffices
            # for the comparison; the refinement below decides the moments).
            span = high - low
            if left - log_mass > log_tolerance - math.log(2.0):
                low -= 0.5 * span
            if right - log_mass > log_tolerance - math.log(2.0):
                high += 0.5 * span
            continue
        for _ in range(_REFINEMENTS):
            grid = _refine(grid)
            log_mass, finer_mean, finer_variance = _integrate(grid, log_density)
            scale = math.sqrt(max(finer_variance, 0.0)) or sd
            if (abs(finer_mean - mean) <= _TOLERANCE * scale
                    and abs(finer_variance - variance) <= _TOLERANCE * scale ** 2):
                tail = max(_log_prior_tail(-low, sd), _log_prior_tail(high, sd)) + math.log(2.0)
                if tail - log_mass > log_tolerance:  # pragma: no cover - the coarse mass already passed
                    return unconverged
                return ReturnSlope(mean=finer_mean, variance=finer_variance, n=len(rows),
                                   source="posterior_randomized_coin")
            mean, variance = finer_mean, finer_variance
        return unconverged
    return unconverged


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
    "PRESENT_NEXT", "RETURN_ASSUMPTION", "RETURN_VERSION", "ReturnRow", "ReturnSlope", "SEED_REGIME", "VERSION", "arm_probabilities", "eligible",
    "fit_return_slope", "flip", "handed_over", "kappa_posterior", "offer_log_likelihood", "offers",
    "pending_assignment", "return_rows", "served_distribution",
]
