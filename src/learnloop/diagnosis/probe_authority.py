"""Whose decision a probe is: the probe router's dispatch by origin (refactor G2).

At the probe router's tag (``algorithm_versions.probe_router_on``) a probe the router selected is the router's whole
decision: the automatic lane's asked probe and the learner lane's offer the router selected both pin the router's
decision on their presentation (``causal_probe.router_decision_id``, written by ``probe_offer.accept_probe_offer``).
No worth gate downstream decides such a probe again: not the scheduler's value admission, not the serving door's value
veto, not a block's continuation or an episode's completion by value, action equivalence or the robust gate. Its
episode is bounded by its count instead (the episode's ``maximum_observations``, as wherever value does not decide),
and its block is the one question the router decided. A probe of any other origin keeps every gate it had, and below
the tag nothing here applies.

Plain reads of stored pins; nothing here writes.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from learnloop.algorithm_versions import probe_router_on

#: The pin's key naming the router's decision.
ROUTER_DECISION_KEY = "router_decision_id"


def router_pin(components: Any) -> bool:
    """Whether a presentation's selection components pin a router decision."""

    pin = components.get("causal_probe") if isinstance(components, Mapping) else None
    return isinstance(pin, Mapping) and bool(pin.get(ROUTER_DECISION_KEY))


def router_selected_presentation(vault: Any, presentation: Any) -> bool:
    """At the tag, whether this presentation is a probe the router selected."""

    if presentation is None or not probe_router_on(vault.config):
        return False
    return router_pin(getattr(presentation, "selection_components", None) or {})


def router_selected_rows(vault: Any, rows: Iterable[Mapping[str, Any]]) -> bool:
    """At the tag, whether any of an episode's observation rows (``effective_episode_observations``, which carry
    their presentation's ``selection_components``) answered a probe the router selected."""

    if not probe_router_on(vault.config):
        return False
    return any(router_pin(row.get("selection_components") or {}) for row in rows)


def router_selected_episode(vault: Any, repository: Any, episode: Any) -> bool:
    """At the tag, whether any presentation of this episode is a probe the router selected: the episode's
    continuation and completion are then no worth gate's."""

    if episode is None or not probe_router_on(vault.config):
        return False
    return any(router_pin(presentation.selection_components or {})
               for presentation in repository.probe_presentations_for_episode(str(episode.id)))


__all__ = ["ROUTER_DECISION_KEY", "router_pin", "router_selected_episode", "router_selected_presentation",
           "router_selected_rows"]
