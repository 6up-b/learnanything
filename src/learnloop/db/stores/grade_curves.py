"""Immutable inputs of the lesson-weight fit. All writes use the caller's transaction."""

from __future__ import annotations

import json
import math
import sqlite3
from collections.abc import Callable, Mapping
from dataclasses import asdict, dataclass

from learnloop.grading_epochs import GradingEpoch, current_epoch, group_epochs


@dataclass(frozen=True)
class GradeCurve:
    attempt_id: str
    epoch_key: str
    grading_revision: int | None
    item_a: float | None
    item_b: float | None
    algorithm_version: str | None
    provenance: str

    def trace(self) -> dict:
        return asdict(self)


def _epochs(connection: sqlite3.Connection, attempt_id: str) -> list[dict]:
    return [dict(row) for row in connection.execute(
        "SELECT id, created_at, grading_revision, superseded_at FROM grading_evidence WHERE attempt_id = ?",
        (attempt_id,))]


def _key(epoch: GradingEpoch | None) -> tuple[str, int | None]:
    # An attempt without criterion evidence has no grading revision to attribute to it.
    return (epoch.key, epoch.revision) if epoch else ("no_evidence", None)


def current_curve(connection: sqlite3.Connection, attempt_id: str) -> GradeCurve:
    key, revision = _key(current_epoch(_epochs(connection, attempt_id)))
    row = connection.execute(
        "SELECT item_a, item_b, algorithm_version, provenance FROM attempt_grade_curves "
        "WHERE attempt_id = ? AND epoch_key = ?", (attempt_id, key)).fetchone()
    if row is None:
        return GradeCurve(attempt_id, key, revision, None, None, None, "missing_capture")
    return GradeCurve(attempt_id, key, revision, *row)


def _insert(connection: sqlite3.Connection, attempt_id: str, key: str, revision: int | None,
            a: float | None, b: float | None, version: str, provenance: str) -> None:
    connection.execute(
        "INSERT INTO attempt_grade_curves(attempt_id, epoch_key, grading_revision, item_a, item_b, "
        "algorithm_version, provenance) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (attempt_id, key, revision, a, b, version, provenance))


def capture_grade_curve(connection: sqlite3.Connection, attempt_id: str,
                        prediction: Mapping[str, float], version: str) -> None:
    """The curve the current epoch's grade was applied with. An epoch keeps the curve it was first applied with: a
    later application of the same epoch (a held grade released without a new revision, a code path below the grading
    revisions' tag) records nothing new."""

    key, revision = _key(current_epoch(_epochs(connection, attempt_id)))
    if connection.execute("SELECT 1 FROM attempt_grade_curves WHERE attempt_id = ? AND epoch_key = ?",
                          (attempt_id, key)).fetchone() is not None:
        return
    _insert(connection, attempt_id, key, revision, prediction["a"], prediction["b"], version, "graded")


def _historical_pair(payload: str | None) -> tuple[float | None, float | None]:
    try:
        dist = json.loads(payload) if payload else None
        if isinstance(dist, dict):
            a, b = dist.get("a"), dist.get("b")
            if all(type(v) in (int, float) and math.isfinite(v) for v in (a, b)):
                return a, b
    except (ValueError, OverflowError, TypeError):
        pass
    return None, None


def _applied_current(observed_json: str | None, correctness: float | None, score_bucket: Callable[[float], str]) -> bool:
    """Whether the surprise row can describe the current epoch: its observed score bucket is the current grade's. The
    surprise row carries no revision, and an evidence-only adjudication (the CLI below the grade channel fixes wrote
    one without replaying) leaves it describing the epoch before. An attempt without a resolved score
    has no grade to disagree with."""

    if correctness is None:
        return True
    try:
        observed = json.loads(observed_json) if observed_json else None
    except ValueError:
        return False
    return isinstance(observed, dict) and observed.get("score_bucket") == score_bucket(float(correctness))


def snapshot_grade_curves(connection: sqlite3.Connection, predecessor: str, *,
                          score_bucket: Callable[[float], str]) -> bool:
    """Fill uncovered epochs, returning whether any first snapshots need to commit. ``score_bucket``: the surprise
    row's bucketing of a score fraction (``attempts.surprise.score_bucket``, which this layer cannot import)."""
    inserted = False
    for attempt_id, payload, version, observed, correctness in connection.execute(
        "SELECT a.id, s.predicted_score_dist_json, s.algorithm_version, s.observed_joint_bucket_json, a.correctness "
        "FROM practice_attempts a LEFT JOIN attempt_surprise s ON s.attempt_id = a.id ORDER BY a.id"
    ):
        rows = _epochs(connection, attempt_id)
        current = _key(current_epoch(rows))
        keys = [_key(epoch) for epoch in group_epochs(rows)] or [current]
        existing = {r[0] for r in connection.execute(
            "SELECT epoch_key FROM attempt_grade_curves WHERE attempt_id = ?", (attempt_id,))}
        applied = _applied_current(observed, correctness, score_bucket)
        for key, revision in keys:
            if key in existing:
                continue
            a, b = _historical_pair(payload) if (key, revision) == current and applied else (None, None)
            provenance = "missing_at_upgrade" if a is None else "reconstructed_at_upgrade"
            source_version = version if a is not None and version else predecessor
            _insert(connection, attempt_id, key, revision, a, b, source_version, provenance)
            inserted = True
    return inserted
