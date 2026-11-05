"""RO4 §8.6: the attention price ``κ(x) = κ0·x/m̄`` on session minutes, its daily seed, guard and posterior.

* **Session minutes** (owner's decision): active minutes in this session, where a session ends after a gap of at
  least ``[router_objective] session_gap_minutes`` (``keep``, 60), so short restarts cannot reset the price. A new
  session starts at zero. Active minutes are attempts' latency and Reader visits' active seconds (RO0's clock, two
  clocks never blended with elapsed time).
* **``m̄``** is the plan's remembered minutes; the trace records where it came from.
* **The seed** (until RO5's randomized stop offers): at the day's first decision ``κ0 = (G(m̄ + d̄) − G(m̄)) / d̄``
  from the tail rollout (the day's forecast marginal gain per minute at ``m̄``), so one unusual day does not set
  the price; later decisions that day carry it. With no frontier on a day it carries the last value; with none
  ever it starts from the seed tail's average marginal gain per minute, ``(G(m̄) − G(0))/m̄``. A vanishing forecast
  gain cannot collapse it: the price is floored at the last positive value. **Until RO5, κ is the seed**, and the
  trace says so; in practice ``m̄`` acts as a soft budget.
* **The runaway guard**: past ``session_guard_minutes`` (``keep``, ``3·m̄`` by default) a stop offer is forced into
  the support and every crossing is reported. A numerical safeguard, not a budget: the learner can continue.
* **Learning** (built, fed only by what exists): a grid posterior over ``κ0`` with a stated likelihood, a logistic
  choice between continuing and stopping given the forecast gain and the price, from frontier choices (an offered
  stop the learner took or overrode). Voluntary stops enter as censored inequalities whose selection term is not
  identified before RO5, so ``κ`` is labelled preference plus model error, and it serves no decision before RO5.

A leaf: the standard library only; the reads take a connection.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import math
from typing import Any

PRICE_VERSION = "kappa_rising_v1"
SEED = "seed"
#: How κ0 was set at a decision.
DAY_SEED = "day_seed"          # the day's first decision computed it
CARRIED_DAY = "carried_today"  # a later decision today carried the day's seed
CARRIED_LAST = "carried_last"  # no frontier today: the last value
TAIL_AVERAGE = "tail_average"  # none ever: the seed tail's average marginal gain per minute
FLOORED = "floored_at_last_positive"
#: The runaway guard's default multiple of ``m̄`` (spec §8.6, ``keep``).
GUARD_MULTIPLE = 3.0
#: The posterior grid: multiples of the seed, log-spaced (numerical resolution, not a judgement).
GRID_MULTIPLES: tuple[float, ...] = tuple(round(2 ** (i / 4), 6) for i in range(-16, 17))
_STAMP = "%Y-%m-%dT%H:%M:%SZ"


def _parse(stamp: str) -> datetime:
    return datetime.fromisoformat(str(stamp).replace("Z", "+00:00"))


def session_active_minutes(connection: Any, *, now: str, gap_minutes: float) -> tuple[float, str | None, dict[str, Any]]:
    """The active minutes of the current objective session: activity (attempts at their completion with their
    latency, Reader visits over their interval) walked back from ``now`` until a gap of ``gap_minutes``. Returns the
    minutes, the session's start and how it was read."""

    end = _parse(now)
    since = (end - timedelta(days=2)).strftime(_STAMP)
    spans: list[tuple[datetime, datetime, float]] = []
    for created, latency in connection.execute(
            "SELECT created_at, COALESCE(latency_seconds, 0) FROM practice_attempts WHERE created_at >= ? AND created_at <= ?",
            (since, now)):
        finish = _parse(created)
        seconds = max(float(latency or 0), 0.0)
        spans.append((finish - timedelta(seconds=seconds), finish, seconds))
    for row in connection.execute(
            "SELECT COALESCE(occurred_at, created_at), json_extract(payload_json, '$.active_seconds'), "
            "json_extract(payload_json, '$.idle_seconds') FROM interaction_events "
            "WHERE kind = 'reader_view_closed' AND created_at >= ?", (since,)):
        active, idle = row[1], row[2]
        if not isinstance(active, (int, float)) or active <= 0:
            continue
        closed = _parse(row[0])
        if closed > end:
            continue
        spent = float(active) + (float(idle) if isinstance(idle, (int, float)) and idle > 0 else 0.0)
        spans.append((closed - timedelta(seconds=spent), closed, float(active)))
    spans.sort(key=lambda span: span[1], reverse=True)
    gap = timedelta(minutes=float(gap_minutes))
    cursor = end
    seconds = 0.0
    start: datetime | None = None
    for began, finished, active in spans:
        if cursor - finished >= gap:
            break
        seconds += active
        cursor = min(cursor, began)
        start = began if start is None or began < start else start
    return seconds / 60.0, (start.strftime(_STAMP) if start else None), {
        "basis": "attempt_latency_plus_reader_active_seconds", "gap_minutes": float(gap_minutes), "spans": len(spans)}


def guard_minutes(config: Any, remembered: float) -> float:
    section = getattr(config, "router_objective", None)
    explicit = getattr(section, "session_guard_minutes", None)
    return float(explicit) if explicit is not None else GUARD_MULTIPLE * float(remembered)


@dataclass(frozen=True)
class Seeded:
    kappa0: float
    how: str
    regime: str = SEED
    gain: Mapping[str, float] = field(default_factory=dict)
    local_date: str | None = None

    #: RO5: the posterior κ0 was handed to (None in the seed regime)
    posterior: Mapping[str, Any] | None = None

    def as_dict(self) -> dict[str, Any]:
        out = {"kappa0": self.kappa0, "how": self.how, "regime": self.regime, "gain": dict(self.gain),
               "local_date": self.local_date, "version": PRICE_VERSION,
               "note": "until RO5's randomized stop offers, kappa is the seed (re-centred daily)"}
        if self.posterior is not None:
            # RO5 §9 item 1: the daily re-centring has ended; the seed is folded into the prior.
            out["posterior"] = dict(self.posterior)
            out["note"] = ("kappa is the posterior from offered stops (randomized ones included); the seed in force at "
                           "the first randomized offer is its prior's centre, and the daily re-centring has ended")
        return out


def seed_from_gain(gain: Mapping[float, float], *, remembered: float, block_minutes: float,
                   last_positive: float | None) -> tuple[float, str]:
    """``κ0`` from the day's gain curve: the marginal gain per minute at ``m̄``, floored at the last positive value;
    with none ever and no positive marginal, the tail's average marginal gain per minute."""

    d = max(float(block_minutes), 1e-9)
    m = float(remembered)
    marginal = (gain[m + d] - gain[m]) / d
    if marginal > 0:
        return marginal, DAY_SEED
    if last_positive is not None and last_positive > 0:
        return float(last_positive), FLOORED
    average = (gain[m] - gain[0.0]) / max(m, 1e-9)
    return max(average, 0.0), TAIL_AVERAGE


def choice_log_likelihood(kappa0: float, observations: Iterable[Mapping[str, float]]) -> float:
    """The stated likelihood: ``P(continue) = σ(gain − price)`` per frontier choice, the price at that choice's
    session minutes (``κ0·x/m̄`` over the block); a stop says only that the forecast gain was below the price."""

    total = 0.0
    for obs in observations:
        price = kappa0 * float(obs["block_cost_per_kappa0"])
        z = float(obs["gain"]) - price
        p = 1.0 / (1.0 + math.exp(-z / max(float(obs.get("scale", 1.0)), 1e-12)))
        p = min(max(p, 1e-12), 1 - 1e-12)
        total += math.log(p) if obs["continued"] else math.log(1 - p)
    return total


def grid_posterior(seed: float, observations: Sequence[Mapping[str, float]]) -> dict[str, Any]:
    """The grid posterior over ``κ0``: a log-uniform grid around the seed, prior uniform on it. With no
    observations it is the prior and says so; it serves no decision before RO5."""

    if seed <= 0:
        return {"status": "no_positive_seed", "n": len(observations)}
    grid = [seed * multiple for multiple in GRID_MULTIPLES]
    logs = [choice_log_likelihood(value, observations) for value in grid]
    top = max(logs)
    weights = [math.exp(value - top) for value in logs]
    norm = sum(weights)
    mean = sum(value * weight for value, weight in zip(grid, weights)) / norm
    return {"status": "posterior" if observations else "prior", "n": len(observations), "mean": mean,
            "grid": len(grid), "serves": False, "label": "preference plus model error"}


__all__ = [
    "CARRIED_DAY", "CARRIED_LAST", "DAY_SEED", "FLOORED", "GRID_MULTIPLES", "GUARD_MULTIPLE", "PRICE_VERSION", "SEED",
    "Seeded", "TAIL_AVERAGE", "choice_log_likelihood", "grid_posterior", "guard_minutes", "seed_from_gain",
    "session_active_minutes",
]
