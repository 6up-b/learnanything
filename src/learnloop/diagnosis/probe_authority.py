"""Whose decision a probe is: the probe router's dispatch by origin (refactor G2).

A probe the router selected at the probe router's tag is the router's whole decision: the automatic lane's asked probe and the learner lane's offer the router selected both pin the router's
decision on their presentation (``causal_probe.router_decision_id``, written by ``probe_offer.accept_probe_offer``).
No worth gate downstream decides such a probe again: not the scheduler's value admission, not the serving door's value
veto, not a block's continuation or an episode's completion by value, action equivalence or the robust gate. Its
episode is bounded by its count instead (the episode's ``maximum_observations``, as wherever value does not decide),
and its block is the one question the router decided. A probe of any other origin keeps every gate it had, and below
the tag nothing here applies.

Plain reads of stored pins; nothing here writes. The episode-level read is ``probe_episodes.router_selected_episode``
(where the scheduler already reads its episodes).
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from learnloop.algorithm_versions import PROBE_ROUTER_VERSIONS

#: The pin's key naming the router's decision.
ROUTER_DECISION_KEY = "router_decision_id"
#: The arms of a router decision that ask the probe: the automatic lane's ``insert_now``, the learner lane's ``probe``.
PROBE_ARMS = frozenset({"insert_now", "probe"})
#: A presentation that still stands for its decision: committed, served or answered (never one ended unanswered).
LIVE_STATUSES = frozenset({"selected", "served", "submitted"})


def _pin(components: Any) -> Mapping[str, Any] | None:
    pin = components.get("causal_probe") if isinstance(components, Mapping) else None
    return pin if isinstance(pin, Mapping) and pin.get(ROUTER_DECISION_KEY) else None


def router_pin(components: Any) -> bool:
    """Whether a presentation's selection components pin a router decision (whatever tag it was made at)."""

    return _pin(components) is not None


def decision_owns(repository: Any, decision_id: Any) -> bool:
    """Whether the router decision ``decision_id`` is the probe router's: made at its tag (the row's own
    ``algorithm_version``, frozen when it was drawn, never the vault's tag now) and asking the probe. A decision made
    below the tag keeps its predecessor treatment after an upgrade, mid-episode and in replay."""

    if not decision_id:
        return False
    with repository.connection() as connection:
        present = connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'router_decisions'").fetchone()
        row = connection.execute("SELECT algorithm_version, chosen_ref FROM router_decisions WHERE id = ?",
                                 (str(decision_id),)).fetchone() if present else None
    return row is not None and row[0] in PROBE_ROUTER_VERSIONS and str(row[1]) in PROBE_ARMS


def pin_owned(repository: Any, components: Any) -> bool:
    """Whether a presentation's pin names a decision the probe router owns (:func:`decision_owns`)."""

    pin = _pin(components)
    return pin is not None and decision_owns(repository, pin.get(ROUTER_DECISION_KEY))


def router_selected_presentation(repository: Any, presentation: Any) -> bool:
    """Whether this presentation is a probe the probe router selected."""

    if presentation is None:
        return False
    return pin_owned(repository, getattr(presentation, "selection_components", None) or {})


def router_selected_rows(repository: Any, rows: Iterable[Mapping[str, Any]]) -> bool:
    """Whether any of an episode's observation rows (``effective_episode_observations``, which carry their
    presentation's ``selection_components``) answered a probe the probe router selected."""

    return any(pin_owned(repository, row.get("selection_components") or {}) for row in rows)


__all__ = ["LIVE_STATUSES", "PROBE_ARMS", "ROUTER_DECISION_KEY", "decision_owns", "pin_owned", "router_pin",
           "router_selected_presentation", "router_selected_rows"]
