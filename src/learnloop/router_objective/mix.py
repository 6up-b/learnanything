"""RO4 §8.3: the served distribution of the two policies' learned mix, exact and logged (G3).

```
μ_i(a) = (1 − k·ε) · [ w_i·π_L^op(a) + (1 − w_i)·π_Q^op(a) ] + ε
```

``π_L^op`` is the LLM policy's distribution if its request completed validly in time, else the staged rule's
one-hot ``π_S``; likewise ``π_Q^op`` for the numeric policy (its argmax, one-hot). Each failure moves only that
policy's share. Where the share goes is the failure rule, logged on every decision drawn under the second one
(``mixture.failure_rule``):

* ``staged`` (mvp-0.54 and below, and the switch off; a record without the key): to ``staged``, so with both failed
  ``μ = (1 − k·ε)·π_S + ε``, the floor kept (owner Q7);
* ``other_policy`` (instruct hand-off IH5, mvp-0.55, ``spec_instruct_handoff_v1`` §7a): with one policy failed the
  other takes the whole mix (``μ = (1 − k·ε)·π_other + ε``); with both failed staged keeps 1.0 as before.

The logged probability is the distribution actually used, after redistribution.

The draw is two-stage, as R2b's (``learnloop.router.mixture``): the first uniform picks the floor's uniform
branch with probability ``k·ε``, else a component by its effective weight; the second picks a candidate from that
component's distribution in support order. The marginal is ``μ``; :func:`recompute` gives it back from the
logged values, and the seed reproduces the draw. A leaf: the standard library and R2b's mixture primitives.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from learnloop.router import mixture as mx

DESIGN = "objective_mixture"
POLICY = "router_objective_v1"
LLM = "llm"
NUMERIC = "numeric"
STAGED = "staged"
COMPONENTS: tuple[str, ...] = (STAGED, LLM, NUMERIC)
POLICIES: tuple[str, ...] = (LLM, NUMERIC)

#: Where a failed policy's share goes (the logged ``mixture.failure_rule``; a record without it is ``STAGED_RULE``).
STAGED_RULE = "staged"
OTHER_POLICY_RULE = "other_policy"
FAILURE_RULES: tuple[str, ...] = (STAGED_RULE, OTHER_POLICY_RULE)


class ObjectiveMixError(ValueError):
    """The mix's inputs cannot give an exact distribution."""


def failure_rule_name(to_other_policy: bool) -> str:
    return OTHER_POLICY_RULE if to_other_policy else STAGED_RULE


def effective_weights(w: float, failed: Sequence[str] | set[str] | frozenset[str], *,
                      to_other_policy: bool = False) -> dict[str, float]:
    """``{staged, llm, numeric}``: ``w`` to the LLM policy and ``1 − w`` to the numeric one, each failed policy's
    share moved to ``staged`` (failure redistribution as §8.3 wrote it). With ``to_other_policy`` (IH5, mvp-0.55,
    spec_instruct_handoff_v1 §7a) a lone failure moves its share to the other policy, so that one takes 1.0; both
    failed still moves both to ``staged``."""

    w = float(w)
    if not 0.0 <= w <= 1.0:
        raise ObjectiveMixError("the weight must lie in [0, 1]")
    out = {STAGED: 0.0, LLM: w, NUMERIC: 1.0 - w}
    lost = {name for name in failed if name in POLICIES}
    if to_other_policy and len(lost) == 1:
        (name,) = lost
        other = NUMERIC if name == LLM else LLM
        out[other] += out[name]
        out[name] = 0.0
        return out
    for name in failed:
        if name in POLICIES:
            out[STAGED] += out[name]
            out[name] = 0.0
    return out


def fallback_label(failed: Sequence[str] | set[str] | frozenset[str]) -> str | None:
    names = {name for name in failed if name in POLICIES}
    if not names:
        return None
    return "both" if names == set(POLICIES) else next(iter(names))


def one_hot(support: Sequence[str], ref: str) -> dict[str, float]:
    if ref not in support:
        raise ObjectiveMixError(f"{ref!r} is not in the support")
    return {option: (1.0 if option == ref else 0.0) for option in support}


def components(support: Sequence[str], staged_ref: str, *, llm: Mapping[str, float] | None,
               numeric_ref: str | None) -> dict[str, dict[str, float]]:
    """Every live component's distribution over the support (a failed policy's is absent)."""

    out = {STAGED: one_hot(support, staged_ref)}
    if llm is not None:
        distribution = mx.normalized(llm, support)
        assert distribution is not None
        out[LLM] = distribution
    if numeric_ref is not None:
        out[NUMERIC] = one_hot(support, numeric_ref)
    return out


def mu(support: Sequence[str], parts: Mapping[str, Mapping[str, float]], weights: Mapping[str, float],
       epsilon: float) -> dict[str, float]:
    k = len(support)
    if k == 0:
        raise ObjectiveMixError("the support is empty")
    if epsilon < 0 or k * epsilon >= 1.0:
        raise ObjectiveMixError("epsilon must be nonnegative with k * epsilon below one")
    scale = 1.0 - k * epsilon
    return {ref: scale * sum(weights.get(name, 0.0) * parts[name][ref] for name in COMPONENTS
                             if weights.get(name, 0.0) > 0) + epsilon for ref in support}


def draw(support: Sequence[str], parts: Mapping[str, Mapping[str, float]], weights: Mapping[str, float],
         epsilon: float, seed: str) -> mx.Draw:
    """The two-stage draw (its marginal is :func:`mu`)."""

    u1, u2 = mx.uniform(seed, "component"), mx.uniform(seed, "candidate")
    pi = mu(support, parts, weights, epsilon)
    k = len(support)
    floor = k * epsilon
    if u1 < floor:
        component = mx.UNIFORM
        chosen = support[min(int(u2 * k), k - 1)]
    else:
        v = (u1 - floor) / (1.0 - floor)
        live = [name for name in COMPONENTS if weights.get(name, 0.0) > 0]
        component = mx._pick(live, {name: weights[name] for name in live}, v)
        chosen = mx._pick(support, parts[component], u2)
    return mx.Draw(chosen=chosen, component=component, propensity=pi[chosen], pi=pi, u1=u1, u2=u2)


def seed_for(boundary_key: str, decision_id: str) -> str:
    import hashlib

    return hashlib.sha256(f"{DESIGN}:{boundary_key}:{decision_id}".encode("utf-8")).hexdigest()


def recompute(record: Mapping[str, Any]) -> dict[str, float]:
    """G3: ``μ`` over the support from a logged decision's own values (``support``, ``staged_ref``, ``epsilon``,
    ``w``, ``failed``, ``llm_distribution``, ``numeric_choice``, and ``failure_rule`` when present)."""

    support = list(record["support"])
    failed = list(record.get("failed") or ())
    # A record without ``failure_rule`` was drawn before IH5 (or with its switch off): staged's rule.
    rule = record.get("failure_rule") or STAGED_RULE
    if rule not in FAILURE_RULES:
        raise ObjectiveMixError(f"unknown failure rule {rule!r}")
    weights = effective_weights(float(record["w"]), failed, to_other_policy=rule == OTHER_POLICY_RULE)
    parts = components(support, str(record["staged_ref"]),
                       llm=None if LLM in failed else record.get("llm_distribution"),
                       numeric_ref=None if NUMERIC in failed else record.get("numeric_choice"))
    return mu(support, parts, weights, float(record["epsilon"]))


__all__ = [
    "COMPONENTS", "DESIGN", "FAILURE_RULES", "LLM", "NUMERIC", "ObjectiveMixError", "OTHER_POLICY_RULE", "POLICIES",
    "POLICY", "STAGED", "STAGED_RULE", "components", "draw", "effective_weights", "failure_rule_name",
    "fallback_label", "mu", "one_hot", "recompute", "seed_for",
]
