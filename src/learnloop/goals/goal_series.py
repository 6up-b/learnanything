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
from learnloop.goals.goal_series_store import prune_rows
from learnloop.goals.goal_projection import (
    goal_report,
    projected_ready_mean_at,
    resolve_goal_scope,
)
from learnloop.substrate.replay import rebuild_derived_state
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
    demonstrated_count: int = 0
    ready_mean: float | None = None
    projected_ready_mean: float | None = None
    projection: bool = False
    decay_estimated: int = 0
    held_flat: int = 0

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
            "demonstrated_count": self.demonstrated_count,
            "ready_mean": self.ready_mean,
            "projected_ready_mean": self.projected_ready_mean,
            "projection": self.projection,
            "decay_estimated": self.decay_estimated,
            "held_flat": self.held_flat,
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
        demonstrated_count=report.demonstrated_count,
        ready_mean=report.ready_current_mean,
        decay_estimated=report.decay_estimated_count,
        held_flat=report.held_flat_count,
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
    points: list[GoalSeriesPoint] = []
    # Hundreds of small reads per checkpoint: pin one connection for the walk.
    with repository.pinned():
        scope_los = sorted(resolve_goal_scope(vault, goal, repository))
        points.extend(_historical_points(vault, repository, goal, scope_los, checkpoints[:-1]))
        live = goal_report(vault, repository, goal, clock=FrozenClock(checkpoints[-1]))
        points.append(_point_from_report(checkpoints[-1], live))
        due = parse_utc(goal.due_at)
        if due is not None and due > now:
            cursor = now + timedelta(days=1)
            while cursor < due:
                points.append(_decay_point(vault, repository, goal, live, cursor, now))
                cursor += timedelta(days=1)
            points.append(_decay_point(vault, repository, goal, live, due, now))
    return points


def _decay_point(vault, repository, goal, live, at: datetime, now: datetime) -> GoalSeriesPoint:
    projected, estimated, held = projected_ready_mean_at(
        vault, repository, goal, at, clock=FrozenClock(now)
    )
    return GoalSeriesPoint(
        at=at,
        on_track_count=live.on_track_count,
        total=live.total,
        certified_count=live.certified_count,
        examined_count=live.examined_count,
        attainment_fraction=live.attainment_fraction,
        predicted_recall_mean=live.predicted_recall_mean,
        demonstrated_count=live.demonstrated_count,
        ready_mean=None,
        projected_ready_mean=projected,
        projection=True,
        decay_estimated=estimated,
        held_flat=held,
    )


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


def _historical_points(
    vault: LoadedVault,
    repository: Repository,
    goal: Goal,
    scope_los: list[str],
    checkpoints: list[datetime],
) -> list[GoalSeriesPoint]:
    """Replay-backed points, sharing one replay across checkpoints that match.

    Attempts only ever accumulate, so two checkpoints that survive the same
    *number* of attempts survive the same *set* of them, and the derived state a
    replay produces is identical (replay clocks off each attempt, not off the
    checkpoint). Consecutive matches — an idle stretch with no practice — are
    therefore replayed once and reported per checkpoint clock.
    """

    counts = _attempt_counts(repository, checkpoints)
    points: list[GoalSeriesPoint] = []
    start = 0
    while start < len(checkpoints):
        end = start
        while end + 1 < len(checkpoints) and counts[end + 1] == counts[start]:
            end += 1
        run = checkpoints[start : end + 1]
        points.extend(_replayed_run(vault, repository, goal, scope_los, run))
        start = end + 1
    return points


def _attempt_counts(repository: Repository, checkpoints: list[datetime]) -> list[int]:
    with repository.connection() as connection:
        return [
            connection.execute(
                "SELECT COUNT(*) FROM practice_attempts WHERE created_at <= ?",
                (checkpoint.strftime("%Y-%m-%dT%H:%M:%SZ"),),
            ).fetchone()[0]
            for checkpoint in checkpoints
        ]


def _replayed_run(
    vault: LoadedVault,
    repository: Repository,
    goal: Goal,
    scope_los: list[str],
    checkpoints: list[datetime],
) -> list[GoalSeriesPoint]:
    with tempfile.TemporaryDirectory(prefix="learnloop-goal-series-") as scratch:
        scratch_path = Path(scratch) / "state.sqlite"
        shutil.copyfile(repository.sqlite_path, scratch_path)
        scratch_repo = Repository.attach(scratch_path, read_only=False)
        with scratch_repo.pinned():
            return _replay_and_report(vault, scratch_repo, goal, scope_los, checkpoints)


def _replay_and_report(
    vault: LoadedVault,
    scratch_repo: Repository,
    goal: Goal,
    scope_los: list[str],
    checkpoints: list[datetime],
) -> list[GoalSeriesPoint]:
    checkpoint = checkpoints[0]
    checkpoint_iso = checkpoint.strftime("%Y-%m-%dT%H:%M:%SZ")
    with scratch_repo.connection() as connection:
        # Attempts are the raw log; everything else the report reads is derived
        # and rebuilt below. Rows referencing dropped attempts are cleared by
        # reset_learning_object_derived_state during replay.
        doomed = [
            row[0]
            for row in connection.execute(
                "SELECT id FROM practice_attempts WHERE created_at > ?", (checkpoint_iso,)
            )
        ]
        prune_rows(connection, "practice_attempts", "id", doomed)
        connection.commit()
    rebuild_derived_state(
        vault,
        scratch_repo,
        learning_object_ids=scope_los,
        clock=FrozenClock(checkpoint),
    )
    return [
        _point_from_report(at, goal_report(vault, scratch_repo, goal, clock=FrozenClock(at)))
        for at in checkpoints
    ]
