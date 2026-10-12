"""Goal-optional re-entry (``spec_daily_loop_v1.md`` §7, P6, Q13).

- **Trigger.** Days since the learner's last real activity (F1:
  ``Repository.most_recent_ended_at``) exceed ``hypothesis.reentry_gap_days``.
  No goal is needed.
- **The plan** is kind ``reentry``: min(remembered minutes,
  ``plan.reentry_minutes``) minutes, at most ``plan.reentry_max_items`` items,
  repair and maintain lanes only, ordered assumed-known checks first, then goals
  with deadlines, then the scheduler's rank.
- **The panel** stays survival-first: still solid, slipped below target (named),
  and today's short re-entry. Solid and slipped are computed over active LOs in
  non-excluded intents (DL1: all of them, uncommitted, target 0.90), comparing
  current retrievability with that target. With an active goal the slipped
  facets are still named in blueprint-weight order, as today. No overdue count,
  no streak, and no due date is rewritten.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from learnloop.clock import parse_utc
from learnloop.params.fitted_params import resolve_fsrs_weights
from learnloop.scheduling.fsrs import forgetting_curve

UNCOMMITTED_RECALL_TARGET = 0.90


@dataclass(frozen=True)
class ReentryGap:
    due: bool
    gap_days: int
    threshold_days: int
    last_activity_at: str | None


def reentry_gap(repository: Any, *, now: datetime, threshold_days: int) -> ReentryGap:
    last = repository.most_recent_ended_at()
    last_at = parse_utc(last) if last else None
    if last_at is None:
        return ReentryGap(False, 0, int(threshold_days), None)
    gap = int((now - last_at).total_seconds() // 86400)
    return ReentryGap(gap > int(threshold_days), gap, int(threshold_days), last)


def retrievability(stability: float | None, last_review: str | None, at: datetime, weights: Any) -> float | None:
    if stability is None:
        return None
    last = parse_utc(last_review)
    if last is None:
        return None
    elapsed = max((at - last).total_seconds() / 86400.0, 0.0)
    return float(forgetting_curve(float(stability), elapsed, weights))


@dataclass(frozen=True)
class ReentryPanel:
    gap_days: int
    solid_count: int
    slipped_count: int
    slipped_names: tuple[str, ...] = ()
    named_by: str = "retrievability"
    target: float = UNCOMMITTED_RECALL_TARGET
    extra: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "gap_days": self.gap_days,
            "solid_count": self.solid_count,
            "slipped_count": self.slipped_count,
            "slipped_names": list(self.slipped_names),
            "named_by": self.named_by,
            "target": self.target,
        }


def reentry_panel(
    vault: Any,
    repository: Any,
    *,
    now: datetime,
    gap: ReentryGap,
    goal: Any | None = None,
    top_n: int = 3,
    clock: Any | None = None,
) -> ReentryPanel:
    """Solid and slipped LOs since the last real activity (§7)."""

    weights = resolve_fsrs_weights(repository)
    last_at = parse_utc(gap.last_activity_at) or now
    now_by_lo: dict[str, list[float]] = defaultdict(list)
    then_by_lo: dict[str, list[float]] = defaultdict(list)
    for item_id, state in repository.practice_item_states().items():
        item = vault.practice_items.get(item_id)
        if item is None or item.status != "active" or not state.active:
            continue
        learning_object = vault.learning_object_for_item(item)
        if learning_object is None or learning_object.status != "active":
            continue
        current = retrievability(state.stability, state.last_attempt_at, now, weights)
        if current is None:
            continue
        previous = retrievability(state.stability, state.last_attempt_at, last_at, weights)
        now_by_lo[learning_object.id].append(current)
        then_by_lo[learning_object.id].append(previous if previous is not None else current)
    target = UNCOMMITTED_RECALL_TARGET
    solid = 0
    slipped: list[tuple[float, str]] = []
    for lo_id, values in now_by_lo.items():
        current = sum(values) / len(values)
        previous_values = then_by_lo.get(lo_id) or values
        previous = sum(previous_values) / len(previous_values)
        if current >= target:
            solid += 1
        elif previous >= target:
            slipped.append((previous - current, lo_id))
    slipped.sort(key=lambda pair: (-pair[0], pair[1]))
    names = tuple(
        (vault.learning_objects[lo_id].title if lo_id in vault.learning_objects else lo_id)
        for _drop, lo_id in slipped[:top_n]
    )
    named_by = "retrievability"
    if goal is not None:
        # With an active goal, the slipped facets are named in blueprint-weight
        # order, as the welcome-back panel always did.
        from learnloop.scheduling.reentry_summary import reentry_summary

        summary = reentry_summary(vault, repository, goal, clock=clock)
        if summary.show and summary.slipped_top:
            names = tuple(dict.fromkeys(facet.learning_object_title for facet in summary.slipped_top))
            named_by = "goal_blueprint_weight"
    return ReentryPanel(
        gap_days=gap.gap_days,
        solid_count=solid,
        slipped_count=len(slipped),
        slipped_names=names,
        named_by=named_by,
        target=target,
    )


__all__ = [
    "ReentryGap",
    "ReentryPanel",
    "UNCOMMITTED_RECALL_TARGET",
    "reentry_gap",
    "reentry_panel",
    "retrievability",
]
