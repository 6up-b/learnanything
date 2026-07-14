"""Decay-pressure fallback (spec §4.5, package F7).

When there is no active goal but FSRS history exists, Today's hero becomes a
decay-pressure list: facets whose projected retrievability crosses the target
threshold soonest, each with a "crosses target in ~N days" column. Facets held
flat for lack of FSRS history carry no decay information and are excluded from
the confident list (they are counted separately, surfaced as "not enough
history").

Deterministic: clock via ``clock.py``; the do-nothing projection is the shared
``facet_projections_at`` retention machinery stepped one day at a time until the
crossing (recall is monotone non-increasing under do-nothing decay, so the first
day below target is the crossing). No belief writes, no LLM.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, timedelta
from typing import Any

from learnloop.clock import Clock, SystemClock
from learnloop.db.repositories import Repository
from learnloop.services.goal_projection import facet_projections_at
from learnloop.vault.models import Goal, LoadedVault


@dataclass(frozen=True)
class DecayPressureFacet:
    learning_object_id: str
    learning_object_title: str
    facet_id: str
    ready_now: float
    crosses_in_days: int | None  # None = does not cross within the search horizon
    has_history: bool

    def as_dict(self) -> dict[str, Any]:
        return {
            "learning_object_id": self.learning_object_id,
            "learning_object_title": self.learning_object_title,
            "facet_id": self.facet_id,
            "ready_now": self.ready_now,
            "crosses_in_days": self.crosses_in_days,
            "has_history": self.has_history,
        }


@dataclass(frozen=True)
class DecayPressure:
    has_history: bool  # at least one facet carries FSRS decay information
    facets: list[DecayPressureFacet] = field(default_factory=list)
    held_flat_count: int = 0  # facets excluded for lack of FSRS history

    def as_dict(self) -> dict[str, Any]:
        return {
            "has_history": self.has_history,
            "facets": [facet.as_dict() for facet in self.facets],
            "held_flat_count": self.held_flat_count,
        }


def _all_concepts_goal(vault: LoadedVault, target_recall: float) -> Goal:
    """A transient whole-vault goal so the projection covers every active LO."""

    concepts = sorted(
        {
            lo.concept
            for lo in vault.learning_objects.values()
            if lo.status == "active" and lo.concept
        }
    )
    return Goal(
        id="goal_transient_decay_pressure",
        title="(decay pressure)",
        target_recall=target_recall,
        due_at=None,
        facet_scope={"concepts": concepts, "facets": []},
        created_at="1970-01-01T00:00:00Z",
        updated_at="1970-01-01T00:00:00Z",
    )


def decay_pressure(
    vault: LoadedVault,
    repository: Repository,
    *,
    goal: Goal | None = None,
    clock: Clock | None = None,
    target: float | None = None,
    horizon_days: int | None = None,
    max_facets: int | None = None,
) -> DecayPressure:
    """Facets ranked by soonest projected target crossing (§4.5).

    ``goal`` scopes the projection when supplied; otherwise a whole-vault
    transient goal is used and ``target`` falls back to the configured
    ``decay_pressure_target_recall``.
    """

    cfg = vault.config.hypothesis
    if target is None:
        target = goal.target_recall if goal is not None else cfg.decay_pressure_target_recall
    if horizon_days is None:
        horizon_days = cfg.decay_pressure_horizon_days
    scope_goal = goal if goal is not None else _all_concepts_goal(vault, target)

    now = (clock or SystemClock()).now().astimezone(UTC)
    now_facets = facet_projections_at(vault, repository, scope_goal, now, clock=clock)

    # Seed per-facet state from the "at now" projection.
    crossing: dict[tuple[str, str], int | None] = {}
    ready_now: dict[tuple[str, str], float] = {}
    decay_estimated: dict[tuple[str, str], bool] = {}
    for facet in now_facets:
        key = (facet.learning_object_id, facet.facet_id)
        ready_now[key] = facet.ready
        decay_estimated[key] = facet.decay_estimated
        # Already below target now -> crosses immediately (0 days).
        crossing[key] = 0 if facet.decay_estimated and facet.ready < target else None

    # Step day-by-day; the first day a facet dips below target is its crossing.
    pending = {
        key for key, est in decay_estimated.items() if est and crossing[key] is None
    }
    day = 1
    while pending and day <= horizon_days:
        at = now + timedelta(days=day)
        for facet in facet_projections_at(vault, repository, scope_goal, at, clock=clock):
            key = (facet.learning_object_id, facet.facet_id)
            if key in pending and facet.ready < target:
                crossing[key] = day
                pending.discard(key)
        day += 1

    facets: list[DecayPressureFacet] = []
    held_flat = 0
    for facet in now_facets:
        key = (facet.learning_object_id, facet.facet_id)
        if not decay_estimated[key]:
            held_flat += 1
            continue
        lo = vault.learning_objects.get(facet.learning_object_id)
        facets.append(
            DecayPressureFacet(
                learning_object_id=facet.learning_object_id,
                learning_object_title=lo.title if lo is not None else facet.learning_object_id,
                facet_id=facet.facet_id,
                ready_now=ready_now[key],
                crosses_in_days=crossing[key],
                has_history=True,
            )
        )

    # Soonest crossing first; non-crossing (None) facets sink to the bottom.
    facets.sort(key=lambda f: (f.crosses_in_days is None, f.crosses_in_days or 0, -f.ready_now))
    if max_facets is not None:
        facets = facets[:max_facets]
    return DecayPressure(
        has_history=any(decay_estimated.values()),
        facets=facets,
        held_flat_count=held_flat,
    )
