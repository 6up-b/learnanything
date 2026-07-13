"""Historical goal-progress series, derived by replay (no snapshot tables).

The design invariant is evidence-not-mastery: derived state is always
rebuildable from the attempts log. So the goal trajectory ("how many facets
were on track N weeks ago") is *computed*, not recorded: for each checkpoint
the SQLite state is copied to a scratch file, attempts after the checkpoint
are dropped, derived state is replayed for the goal's LOs, and
``goal_report`` runs against that historical posterior with a frozen clock.

Cost is checkpoints x per-LO replay, which is fine at current vault sizes;
callers (the sidecar) should cache on (goal_id, checkpoint, attempt count).
"""

from __future__ import annotations

import shutil
import tempfile
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from learnloop.clock import Clock, FrozenClock, SystemClock, parse_utc
from learnloop.db.repositories import Repository
from learnloop.services.goal_projection import goal_report, resolve_goal_scope
from learnloop.services.replay import rebuild_derived_state
from learnloop.vault.models import Goal, LoadedVault

DEFAULT_INTERVAL_DAYS = 7
DEFAULT_MAX_POINTS = 26


@dataclass(frozen=True)
class GoalSeriesPoint:
    at: datetime
    on_track_count: int
    total: int
    certified_count: int
    examined_count: int
    attainment_fraction: float | None
    predicted_recall_mean: float | None

    def as_dict(self) -> dict[str, Any]:
        return {
            "at": self.at.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "on_track_count": self.on_track_count,
            "total": self.total,
            "on_track_fraction": (self.on_track_count / self.total) if self.total else None,
            "certified_count": self.certified_count,
            "examined_count": self.examined_count,
            "attainment_fraction": self.attainment_fraction,
            "predicted_recall_mean": self.predicted_recall_mean,
        }


def _point_from_report(at: datetime, report) -> GoalSeriesPoint:
    return GoalSeriesPoint(
        at=at,
        on_track_count=report.on_track_count,
        total=report.total,
        certified_count=report.certified_count,
        examined_count=report.examined_count,
        attainment_fraction=report.attainment_fraction,
        predicted_recall_mean=report.predicted_recall_mean,
    )


def goal_report_series(
    vault: LoadedVault,
    repository: Repository,
    goal: Goal,
    *,
    clock: Clock | None = None,
    interval_days: int = DEFAULT_INTERVAL_DAYS,
    max_points: int = DEFAULT_MAX_POINTS,
) -> list[GoalSeriesPoint]:
    """Weekly on-track counts from goal creation to now (last point is live).

    Historical points replay a scratch copy of the DB truncated to the
    checkpoint; the final point reads the live repository directly.
    """

    now = (clock or SystemClock()).now().astimezone(UTC)
    created = parse_utc(goal.created_at) or now
    checkpoints = _checkpoints(created, now, interval_days=interval_days, max_points=max_points)
    scope_los = sorted(resolve_goal_scope(vault, goal, repository))
    points: list[GoalSeriesPoint] = []
    for checkpoint in checkpoints[:-1]:
        points.append(_historical_point(vault, repository, goal, scope_los, checkpoint))
    live = goal_report(vault, repository, goal, clock=FrozenClock(checkpoints[-1]))
    points.append(_point_from_report(checkpoints[-1], live))
    return points


def _checkpoints(
    created: datetime,
    now: datetime,
    *,
    interval_days: int,
    max_points: int,
) -> list[datetime]:
    interval = timedelta(days=max(interval_days, 1))
    checkpoints: list[datetime] = []
    at = created
    while at < now and len(checkpoints) < max_points - 1:
        checkpoints.append(at)
        at += interval
    checkpoints.append(now)
    # Keep the most recent window when the goal's history exceeds max_points.
    return checkpoints[-max_points:]


def _historical_point(
    vault: LoadedVault,
    repository: Repository,
    goal: Goal,
    scope_los: list[str],
    checkpoint: datetime,
) -> GoalSeriesPoint:
    checkpoint_iso = checkpoint.strftime("%Y-%m-%dT%H:%M:%SZ")
    with tempfile.TemporaryDirectory(prefix="learnloop-goal-series-") as scratch:
        scratch_path = Path(scratch) / "state.sqlite"
        shutil.copyfile(repository.sqlite_path, scratch_path)
        scratch_repo = Repository(scratch_path)
        with scratch_repo.connection() as connection:
            # Attempts are the raw log; everything else the report reads is
            # derived and rebuilt below. Rows referencing dropped attempts are
            # cleared by reset_learning_object_derived_state during replay.
            connection.execute(
                "DELETE FROM practice_attempts WHERE created_at > ?", (checkpoint_iso,)
            )
            connection.commit()
        rebuild_derived_state(
            vault,
            scratch_repo,
            learning_object_ids=scope_los,
            clock=FrozenClock(checkpoint),
        )
        report = goal_report(vault, scratch_repo, goal, clock=FrozenClock(checkpoint))
        return _point_from_report(checkpoint, report)
