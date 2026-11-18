"""The objective router's seeds, in one place: what each depends on, and why they differ.

* **The numeric seed** (:func:`numeric_seed`): the numeric policy's rollouts at one boundary. It depends on the
  boundary's identity alone, never on a decision id, so the prefetch that starts a boundary's job and the serve that
  takes its answer value the boundary on the same draws; and on that identity less what it names only so a flip or a
  new mark starts a new job (the seed-neutral switches and keys, the miss-cause sensor), so those change no draw.
* **The mix's seed** (:func:`mix_seed`): the two policies' mix at one decision. It depends on the boundary key and the
  decision's fresh id, so two decisions at the same boundary (a deferred read and its serve, or a repeat) draw anew;
  a runtime that pins a seed (tests, scripted runs) replaces it.
* **The stop coin** has no seed of its own: ``stop_coin.flip`` draws its uniforms from the mix's seed under its own
  stage names (``stop_coin``, ``stop_coin_next``), which the mix's two uniforms (``component``, ``candidate``) never
  use, so flipping the coin leaves the mix's draw and ``μ`` as they are.

The chooser looks :func:`numeric_seed` up as its own module attribute at each call, and :func:`mix_seed` calls
``mix.seed_for`` through its module, so a replacement of either attribute reaches every decision.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from learnloop.daily_plan.router_chooser import _hash
from learnloop.router_objective import mix


def numeric_seed(identity: Mapping[str, Any]) -> str:
    """The numeric policy's random seed for one boundary (router speed stage 2, landing ruling R2): derived from the
    boundary identity the prefetch key hashes, less ``SEED_NEUTRAL_SWITCHES`` in its switch snapshot. Those switches
    change no value at a fixed draw count, so whatever they are the draws are main's (with both off, main's exactly);
    they stay in the key itself, the generator payload and ``serving_switches``."""

    from learnloop.router_objective_switches import (
        SEED_NEUTRAL_IDENTITY_KEYS,
        SEED_NEUTRAL_OBJECTIVE_KEYS,
        SEED_NEUTRAL_SWITCHES,
    )

    objective = identity.get("objective")
    switches = objective.get("followup_switches") if isinstance(objective, Mapping) else None
    if isinstance(switches, Mapping):
        objective = {**objective, "followup_switches": {
            key: value for key, value in switches.items() if key not in SEED_NEUTRAL_SWITCHES}}
        identity = {**identity, "objective": objective}
    # IH4: what the key names only so a preference or a flip starts a new job (no value moves with it).
    if isinstance(objective, Mapping) and any(key in objective for key in SEED_NEUTRAL_OBJECTIVE_KEYS):
        identity = {**identity, "objective": {key: value for key, value in objective.items()
                                              if key not in SEED_NEUTRAL_OBJECTIVE_KEYS}}
    if any(key in identity for key in SEED_NEUTRAL_IDENTITY_KEYS):
        identity = {key: value for key, value in identity.items() if key not in SEED_NEUTRAL_IDENTITY_KEYS}
    identity = _without_miss_cause(identity)
    return _hash({"numeric": _hash(dict(identity))})


def _without_miss_cause(identity: Mapping[str, Any]) -> Mapping[str, Any]:
    """Slip or gap: the identity less what it names only so a flip or a changed sensor starts a new job (both switches,
    the sensor's mark, the sensor on an offer's card record): a decision is valued on the same draws whatever they are
    (``router_objective_switches.COMMON_DRAW_OBJECTIVE_KEYS``). Below the tag, or with nothing of it present, the
    identity itself (so the seed keeps the predecessor's bytes)."""

    from learnloop.router_objective_switches import (
        COMMON_DRAW_IDENTITY_KEYS,
        COMMON_DRAW_OBJECTIVE_KEYS,
        MISS_CAUSE_OFFER_KEY,
    )

    def bare_row(row: Any) -> Any:
        annotations = row.get("annotations") if isinstance(row, Mapping) else None
        offer = annotations.get("lesson_offer") if isinstance(annotations, Mapping) else None
        if not (isinstance(offer, Mapping) and MISS_CAUSE_OFFER_KEY in offer):
            return row
        bare = {key: value for key, value in offer.items() if key != MISS_CAUSE_OFFER_KEY}
        return {**row, "annotations": {**annotations, "lesson_offer": bare}}

    objective = identity.get("objective")
    if isinstance(objective, Mapping) and any(key in objective for key in COMMON_DRAW_OBJECTIVE_KEYS):
        identity = {**identity, "objective": {key: value for key, value in objective.items()
                                              if key not in COMMON_DRAW_OBJECTIVE_KEYS}}
    if any(key in identity for key in COMMON_DRAW_IDENTITY_KEYS):
        identity = {key: value for key, value in identity.items() if key not in COMMON_DRAW_IDENTITY_KEYS}
    if isinstance(identity.get("support"), list):
        support = [bare_row(row) for row in identity["support"]]
        if support != identity["support"]:
            identity = {**identity, "support": support}
    if isinstance(identity.get("offer"), Mapping):
        offer = bare_row(identity["offer"])
        if offer is not identity["offer"]:
            identity = {**identity, "offer": offer}
    return identity


def mix_seed(runtime: Any, boundary_key: str, decision_id: str) -> str:
    """The seed of one decision's mix (and of its stop coin): the runtime's own when it pins one, else
    ``mix.seed_for(boundary_key, decision_id)``."""

    return runtime.seed(boundary_key, decision_id) if runtime.seed is not None else mix.seed_for(boundary_key,
                                                                                                 decision_id)


__all__ = ["mix_seed", "numeric_seed"]
