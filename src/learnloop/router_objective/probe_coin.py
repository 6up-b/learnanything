"""G2: the probe coin, the randomized share of probes the router asks while it cannot value them.

At the probe router's tag (``algorithm_versions.probe_router_on``) a probe the router cannot value yet earns no
information credit (the automatic lane decides before the probe is written; ``docs/reviews/refactor-g2-design.md``
decision 1), so it is not an option of either policy: the mix decides over the rest of the post-miss support. So that
the data which would teach the router to value probes keeps arriving (the owner's option f of 2026-11-20), the coin
asks the probe, now and with the miss's feedback held, on a small randomized share of eligible misses:

| Arm | Probability | Served |
|---|---|---|
| ``ask_probe`` | ``r`` (:func:`share`) | the probe, asked now |
| ``policy`` | ``1 − r`` | the mix's draw |

So the served distribution is ``P(probe) = r`` and ``P(a) = (1 − r)·μ(a)`` for every option ``a`` of the mix, exactly
(:func:`served_distribution`), logged as the decision's propensities. The coin is independent of the mix: its uniform
comes from its own seed (:func:`seed_for`, never the mix's or the stop coin's), and its assignment is its own row in
``policy_experiment_assignments`` (``assignments.PROBE_COIN``). A ``policy`` decision's ``μ`` is the mix's conditional
distribution, exactly, since the coin is independent of it.

**The share is the stop coin's rate.** The owner ruled on 2026-11-23 that the share is derived from an existing
randomized arm's rate, not a new constant; the orchestrator chose the stop coin (``router_objective.stop_coin``): the
same mechanism (a coin beside the mix, with an exact propensity, for an action the policies value below another) and
the same family of declared prices for information. One config field now prices two arms: changing ``stop_coin`` moves
the probe share with it, and ``0`` turns both off. :func:`share` is the one place the rate is read. Kept as
alternatives in the record (``docs/reviews/algorithm-probe-router.md``): ``pick_open_share`` and ``router.epsilon_min``.

A leaf: the router's mixture helpers and the standard library.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import hashlib
from typing import Any

from learnloop.router import mixture as mx

VERSION = "g2_probe_coin_v1"
#: The coin's uniform's stage name (the stop coin's is ``stop_coin``).
STAGE = "probe_coin"
ASK = "ask_probe"
POLICY = "policy"
ARMS: tuple[str, ...] = (ASK, POLICY)
#: Where the rate is read, as the record names it.
RATE_SOURCE = "router_objective.stop_coin"


def share(config: Any) -> float:
    """The share of eligible misses the coin asks the probe on: the stop coin's rate (module docstring)."""

    return float(config.router_objective.stop_coin)


def applies(rate: float) -> bool:
    """Whether the coin is flipped: a positive share. At zero no probe is asked and no assignment written."""

    return float(rate) > 0.0


def seed_for(boundary_key: str, decision_id: str) -> str:
    """The coin's own seed for one decision: a function of the boundary and the decision, never the mix's seed."""

    return hashlib.sha256(f"{VERSION}|{boundary_key}|{decision_id}".encode("utf-8")).hexdigest()[:32]


def draw_uniform(seed: str) -> float:
    """The coin's uniform, from its own seed."""

    return mx.uniform(seed, STAGE)


def arm_probabilities(rate: float) -> dict[str, float]:
    p = float(rate)
    return {ASK: p, POLICY: 1.0 - p}


def served_distribution(mu: Mapping[str, float], rate: float, *, probe_ref: str) -> dict[str, float]:
    """``P(served = a)`` under the coin and the mix together, exactly: the probe at ``rate``, every option of the mix at
    ``(1 − rate)·μ``. The probe is never in the mix's own support (it would then be valued and picked twice)."""

    if probe_ref in mu:
        raise ValueError("the probe is asked only by the coin, never by the mix")
    p = float(rate)
    return {probe_ref: p, **{ref: (1.0 - p) * float(value) for ref, value in mu.items()}}


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
    seed: str
    boundary_key: str

    def as_dict(self) -> dict[str, Any]:
        return {"version": VERSION, "arm": self.arm, "u": self.u, "rate": self.rate, "rate_source": RATE_SOURCE,
                "propensity": self.propensity, "served": self.served, "served_propensity": self.served_propensity,
                "seed": self.seed, "boundary_key": self.boundary_key, "arms": arm_probabilities(self.rate)}


def flip(seed: str, rate: float, *, probe_ref: str, mu: Mapping[str, float], drawn: str,
         boundary_key: str = "") -> Coin:
    """The coin for one decision: its arm from its own uniform, and what is served (the probe, or the mix's draw)."""

    u = draw_uniform(seed)
    probabilities = arm_probabilities(rate)
    arm = ASK if u < probabilities[ASK] else POLICY
    served = probe_ref if arm == ASK else drawn
    distribution = served_distribution(mu, rate, probe_ref=probe_ref)
    return Coin(arm=arm, u=u, rate=float(rate), propensity=probabilities[arm], served=served,
                served_propensity=distribution[served], seed=seed, boundary_key=boundary_key)


def pending_assignment(coin: Coin, *, seed: str, support: Sequence[str]) -> dict[str, Any]:
    """The coin's ``policy_experiment_assignments`` row, frozen on the decision's record and written with the decision
    (``assignments.record_pending``)."""

    from learnloop.router_objective import assignments as A

    return {"experiment_id": A.PROBE_COIN, "variant": coin.arm, "propensity": coin.propensity, "seed": seed,
            "draw": coin.u, "candidate_refs": list(ARMS),
            "detail": {"version": VERSION, "rate": coin.rate, "rate_source": RATE_SOURCE,
                       "arms": arm_probabilities(coin.rate), "support": list(support), "served": coin.served,
                       "served_propensity": coin.served_propensity, "boundary_key": coin.boundary_key}}


__all__ = ["ARMS", "ASK", "Coin", "POLICY", "RATE_SOURCE", "STAGE", "VERSION", "applies", "arm_probabilities",
           "draw_uniform", "flip", "pending_assignment", "seed_for", "served_distribution", "share"]
