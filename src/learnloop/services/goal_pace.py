"""Pace read-model for a goal: work rate vs. work remaining vs. time left.

Pure read (no state writes). The attempts-remaining figure comes from the
goal report's evidence-mass inversion (see ``goal_projection``); this module
adds the learner's observed cadence so the banner can say "need ~6/day,
you're averaging 4.2/day".
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC
from typing import Any

from learnloop.clock import Clock, SystemClock, parse_utc
from learnloop.db.repositories import Repository
from learnloop.services.goal_projection import GoalReport, resolve_goal_scope
from learnloop.vault.models import Goal, LoadedVault

PACE_WINDOW_DAYS = 14


@dataclass(frozen=True)
class GoalPace:
    attempts_per_day: float          # mean over the trailing window, idle days included
    attempts_last_14d: int
    days_left: float | None          # None for open-ended goals
    attempts_remaining: int | None   # from the report inversion; None when total is unknowable
    needed_per_day: float | None     # attempts_remaining spread over the days left
    on_pace: bool | None             # None when either rate is undefined
    attempts_logged: int             # lifetime attempts on the goal's scope LOs

    def as_dict(self) -> dict[str, Any]:
        return {
            "attempts_per_day": round(self.attempts_per_day, 2),
            "attempts_last_14d": self.attempts_last_14d,
            "days_left": round(self.days_left, 2) if self.days_left is not None else None,
            "attempts_remaining": self.attempts_remaining,
            "needed_per_day": (
                round(self.needed_per_day, 2) if self.needed_per_day is not None else None
            ),
            "on_pace": self.on_pace,
            "attempts_logged": self.attempts_logged,
        }


def compute_goal_pace(
    vault: LoadedVault,
    repository: Repository,
    goal: Goal,
    report: GoalReport,
    *,
    clock: Clock | None = None,
) -> GoalPace:
    clock = clock or SystemClock()
    now = clock.now().astimezone(UTC)

    daily = repository.daily_attempt_counts(days=PACE_WINDOW_DAYS, clock=clock)
    attempts_last_14d = sum(daily.values())
    attempts_per_day = attempts_last_14d / max(len(daily), 1)

    due_at = parse_utc(goal.due_at)
    days_left = max((due_at - now).total_seconds() / 86400, 0.0) if due_at is not None else None

    attempts_remaining: int | None = report.attempts_remaining
    if report.attempts_remaining_is_partial and attempts_remaining == 0:
        # Every at-risk facet lacks supporting items: the total is unknowable,
        # not zero — surface None rather than a false "done".
        attempts_remaining = None

    needed_per_day: float | None = None
    if attempts_remaining is not None and days_left is not None:
        needed_per_day = attempts_remaining / max(days_left, 1.0)

    on_pace: bool | None = None
    if needed_per_day is not None:
        on_pace = attempts_per_day >= needed_per_day

    scope_los = sorted(resolve_goal_scope(vault, goal, repository))
    attempts_logged = repository.attempt_count_for_learning_objects(scope_los)

    return GoalPace(
        attempts_per_day=attempts_per_day,
        attempts_last_14d=attempts_last_14d,
        days_left=days_left,
        attempts_remaining=attempts_remaining,
        needed_per_day=needed_per_day,
        on_pace=on_pace,
        attempts_logged=attempts_logged,
    )
