"""Router R2b: the logged model mixture (``model_mixture``) and its exact propensities.

docs/specs/plan_router_r2_v1.md §3.3 and spec_action_router_v1 §7.3. Over the
top-k reversible candidates (the support), three components each put a
distribution:

* ``staged``: all its mass on the staged rule's own pick (``lane_quota_v1``
  over the staged-feasible set, owner Q1);
* ``decider``: the Decider's ``choose_block`` probabilities;
* ``llm``: the LLM's ``choose_block`` probabilities, renormalized by the
  client over the support.

The served choice is sampled from

    pi = (1 - k * eps) * (w_s * staged + w_d * decider + w_l * llm) + eps

with ``k`` the support's size and ``eps`` = ``router.epsilon_min`` (D1: 0.02),
so every candidate of the support keeps at least ``eps`` and the propensity is
exact. A component that timed out, failed, was refused for spend or is not set
up gives its weight to ``staged`` for that decision (G7); with both models
down the floor stays (owner Q7, 2026-10-13: the epsilon floor is kept on a
full fallback). The randomization layer's dormant 0.05 floor never clips this
design: ``model_mixture`` documents its own (``eps``).

**The two-stage draw** (so the "why" can say which draw chose the block): the
seed (``seed_for(boundary key, decision id)``) gives two uniforms. The first
picks the uniform component with probability ``k * eps``, otherwise a
component by weight; the second picks a candidate from that component's
distribution, in support order. The marginal of the two stages is ``pi``, and
the logged propensity is ``pi(chosen)``. G3 recomputes it from the logged
weights and distributions (:func:`recompute`), and the seed reproduces the
draw (:func:`draw`).

A leaf module: the standard library only, no clock, no randomness of its own.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import hashlib
import math
from typing import Any

DESIGN = "model_mixture"
POLICY = "router_mixture_v1"
#: The deterministic staged rule's policy name (R2a's ``staged_v1``).
STAGED_POLICY = "staged_v1"
COMPONENTS: tuple[str, ...] = ("staged", "decider", "llm")
MODEL_COMPONENTS: tuple[str, ...] = ("decider", "llm")
#: The display-only name of the first stage's uniform branch (the eps floor).
UNIFORM = "uniform"
#: A propensity within this of 1 is deterministic (``propensity_kind``).
DETERMINISTIC_TOLERANCE = 1e-12


class MixtureError(ValueError):
    """The mixture's inputs cannot give an exact distribution."""


def effective_weights(weights: Mapping[str, float], failed: Sequence[str] | set[str] | frozenset[str]) -> dict[str, float]:
    """The configured weights, normalized, with each failed model's weight moved to staged."""

    raw = {name: float(weights.get(name, 0.0) or 0.0) for name in COMPONENTS}
    if any(value < 0 or not math.isfinite(value) for value in raw.values()):
        raise MixtureError("mixture weights must be finite and nonnegative")
    total = sum(raw.values())
    if total <= 0:
        raise MixtureError("mixture weights must not all be zero")
    out = {name: value / total for name, value in raw.items()}
    for name in failed:
        if name in MODEL_COMPONENTS:
            out["staged"] += out[name]
            out[name] = 0.0
    return out


def fallback_label(failed: Sequence[str] | set[str] | frozenset[str]) -> str | None:
    """``decider`` | ``llm`` | ``both`` (the receipt's ``fallback``), or None."""

    names = {name for name in failed if name in MODEL_COMPONENTS}
    if not names:
        return None
    if names == set(MODEL_COMPONENTS):
        return "both"
    return next(iter(names))


def normalized(distribution: Mapping[str, float] | None, support: Sequence[str]) -> dict[str, float] | None:
    """A component's distribution over ``support`` (missing refs are 0), renormalized."""

    if distribution is None:
        return None
    values = {}
    for ref in support:
        value = distribution.get(ref, 0.0)
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)) or value < 0:
            raise MixtureError(f"probability of {ref!r} is not a finite nonnegative number")
        values[ref] = float(value)
    total = sum(values.values())
    if total <= 0:
        raise MixtureError("a component put no mass on the support")
    return {ref: value / total for ref, value in values.items()}


def component_distributions(
    support: Sequence[str], staged_ref: str, models: Mapping[str, Mapping[str, float] | None]
) -> dict[str, dict[str, float]]:
    """Every component's distribution over the support (a failed model's is absent)."""

    if staged_ref not in support:
        raise MixtureError("the staged pick is not in the support")
    out = {"staged": {ref: (1.0 if ref == staged_ref else 0.0) for ref in support}}
    for name in MODEL_COMPONENTS:
        distribution = normalized(models.get(name), support)
        if distribution is not None:
            out[name] = distribution
    return out


def mixture(
    support: Sequence[str],
    components: Mapping[str, Mapping[str, float]],
    weights: Mapping[str, float],
    epsilon: float,
) -> dict[str, float]:
    """``pi`` over the support (exact; sums to one)."""

    k = len(support)
    if k == 0:
        raise MixtureError("the support is empty")
    if not 0.0 <= epsilon or k * epsilon >= 1.0:
        raise MixtureError("epsilon must be nonnegative with k * epsilon below one")
    scale = 1.0 - k * epsilon
    pi = {}
    for ref in support:
        mixed = sum(weights.get(name, 0.0) * components[name][ref] for name in COMPONENTS if weights.get(name, 0.0) > 0)
        pi[ref] = scale * mixed + epsilon
    return pi


def seed_for(boundary_key: str, decision_id: str) -> str:
    """The decision's seed: a hash of its boundary key and its id."""

    return hashlib.sha256(f"{DESIGN}:{boundary_key}:{decision_id}".encode("utf-8")).hexdigest()


def uniform(seed: str, stage: str) -> float:
    """A uniform in [0, 1) from the seed (53 bits of a SHA-256)."""

    digest = hashlib.sha256(f"{seed}:{stage}".encode("utf-8")).digest()
    return (int.from_bytes(digest[:8], "big") >> 11) / float(1 << 53)


@dataclass(frozen=True)
class Draw:
    chosen: str
    #: ``staged`` | ``decider`` | ``llm`` | ``uniform`` (display only)
    component: str
    propensity: float
    pi: Mapping[str, float]
    u1: float
    u2: float

    @property
    def deterministic(self) -> bool:
        return self.propensity >= 1.0 - DETERMINISTIC_TOLERANCE


def _pick(order: Sequence[str], distribution: Mapping[str, float], u: float) -> str:
    cumulative = 0.0
    last = None
    for ref in order:
        mass = distribution.get(ref, 0.0)
        if mass <= 0:
            continue
        last = ref
        cumulative += mass
        if u < cumulative:
            return ref
    if last is None:
        raise MixtureError("nothing to pick")
    return last


def draw(
    support: Sequence[str],
    components: Mapping[str, Mapping[str, float]],
    weights: Mapping[str, float],
    epsilon: float,
    seed: str,
) -> Draw:
    """The two-stage draw; its marginal is :func:`mixture`."""

    pi = mixture(support, components, weights, epsilon)
    k = len(support)
    u1, u2 = uniform(seed, "component"), uniform(seed, "candidate")
    floor = k * epsilon
    if u1 < floor:
        component = UNIFORM
        chosen = support[min(int(u2 * k), k - 1)]
    else:
        v = (u1 - floor) / (1.0 - floor)
        live = [name for name in COMPONENTS if weights.get(name, 0.0) > 0]
        component = _pick(live, {name: weights[name] for name in live}, v)
        chosen = _pick(support, components[component], u2)
    return Draw(chosen=chosen, component=component, propensity=pi[chosen], pi=pi, u1=u1, u2=u2)


def recompute(record: Mapping[str, Any]) -> float:
    """G3: ``pi(chosen)`` from a logged decision's own components.

    ``record`` holds ``support``, ``staged_ref``, ``chosen``, ``epsilon``,
    ``effective_weights`` and ``distributions`` (the models' renormalized
    distributions over the support, absent for a failed one)."""

    support = list(record["support"])
    components = component_distributions(support, str(record["staged_ref"]), record.get("distributions") or {})
    pi = mixture(support, components, record["effective_weights"], float(record["epsilon"]))
    return pi[str(record["chosen"])]


__all__ = [
    "COMPONENTS",
    "DESIGN",
    "DETERMINISTIC_TOLERANCE",
    "Draw",
    "MODEL_COMPONENTS",
    "MixtureError",
    "POLICY",
    "STAGED_POLICY",
    "UNIFORM",
    "component_distributions",
    "draw",
    "effective_weights",
    "fallback_label",
    "mixture",
    "normalized",
    "recompute",
    "seed_for",
    "uniform",
]
