"""Welcome-back diff (spec §4.4, package F7).

When the gap since the last session end exceeds the configured threshold, the
re-entry panel opens Today ordered survival-first: how many facets are *still
solid*, how many *slipped below target* while away (top few named by blueprint
weight), and a suggested refresher count. Never leads with losses; never
mentions the streak.

Deterministic: clock via ``clock.py``; the same FSRS retention machinery as the
goal report (``facet_projections_at``), projected to the last session end and to
now. Held-flat facets (no FSRS history) carry no decay information and are
excluded from the confident solid/slipped copy.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC
from typing import Any

from learnloop.clock import Clock, SystemClock, parse_utc
from learnloop.db.repositories import Repository
from learnloop.services.goal_projection import facet_projections_at, goal_report
from learnloop.services.overconfidence import blueprint_weight_by_facet
from learnloop.vault.models import Goal, LoadedVault


@dataclass(frozen=True)
class SlippedFacet:
    learning_object_id: str
    learning_object_title: str
    facet_id: str
    blueprint_weight: float

    def as_dict(self) -> dict[str, Any]:
        return {
            "learning_object_id": self.learning_object_id,
            "learning_object_title": self.learning_object_title,
            "facet_id": self.facet_id,
            "blueprint_weight": self.blueprint_weight,
        }


@dataclass(frozen=True)
class ReentrySummary:
    show: bool
    gap_days: int
    threshold_days: int
    last_ended_at: str | None
    solid_count: int = 0
    slipped_count: int = 0
    refresher_count: int = 0
    slipped_top: list[SlippedFacet] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "show": self.show,
            "gap_days": self.gap_days,
            "threshold_days": self.threshold_days,
            "last_ended_at": self.last_ended_at,
            "solid_count": self.solid_count,
            "slipped_count": self.slipped_count,
            "refresher_count": self.refresher_count,
            "slipped_top": [facet.as_dict() for facet in self.slipped_top],
        }


def reentry_summary(
    vault: LoadedVault,
    repository: Repository,
    goal: Goal,
    *,
    clock: Clock | None = None,
    gap_days: int | None = None,
    top_n: int = 3,
) -> ReentrySummary:
    """Welcome-back diff for ``goal`` (§4.4). ``show`` gates the whole panel."""

    if gap_days is None:
        gap_days = vault.config.hypothesis.reentry_gap_days
    now = (clock or SystemClock()).now().astimezone(UTC)
    last_ended_iso = repository.most_recent_ended_at()
    last_ended = parse_utc(last_ended_iso) if last_ended_iso else None
    if last_ended is None:
        return ReentrySummary(
            show=False, gap_days=0, threshold_days=gap_days, last_ended_at=None
        )

    elapsed_days = int((now - last_ended).total_seconds() // 86400)
    if elapsed_days <= gap_days:
        return ReentrySummary(
            show=False,
            gap_days=elapsed_days,
            threshold_days=gap_days,
            last_ended_at=last_ended_iso,
        )

    target = goal.target_recall
    proj_now = {
        (f.learning_object_id, f.facet_id): f
        for f in facet_projections_at(vault, repository, goal, now, clock=clock)
    }
    proj_last = {
        (f.learning_object_id, f.facet_id): f
        for f in facet_projections_at(vault, repository, goal, last_ended, clock=clock)
    }
    report = goal_report(vault, repository, goal, clock=clock)
    weights = blueprint_weight_by_facet(vault, report)

    solid_count = 0
    slipped: list[SlippedFacet] = []
    for key, now_facet in proj_now.items():
        if not now_facet.decay_estimated:
            continue  # held flat — no decay information, excluded from confident copy
        last_facet = proj_last.get(key)
        ready_now = now_facet.ready
        ready_last = last_facet.ready if last_facet is not None else ready_now
        if ready_now >= target:
            solid_count += 1
        elif ready_last >= target:
            lo = vault.learning_objects.get(now_facet.learning_object_id)
            slipped.append(
                SlippedFacet(
                    learning_object_id=now_facet.learning_object_id,
                    learning_object_title=(
                        lo.title if lo is not None else now_facet.learning_object_id
                    ),
                    facet_id=now_facet.facet_id,
                    blueprint_weight=weights.get(
                        (now_facet.learning_object_id, vault.canonical_facet_id(now_facet.facet_id)),
                        1.0,
                    ),
                )
            )

    slipped.sort(key=lambda f: (f.blueprint_weight, f.facet_id), reverse=True)
    return ReentrySummary(
        show=True,
        gap_days=elapsed_days,
        threshold_days=gap_days,
        last_ended_at=last_ended_iso,
        solid_count=solid_count,
        slipped_count=len(slipped),
        refresher_count=len(slipped),
        slipped_top=slipped[:top_n],
    )
