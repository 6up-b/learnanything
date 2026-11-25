"""The rows the attempt door records for a live grade that gives criterion points and no evidence rows."""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from learnloop.ids import new_ulid

# The provenance of evidence rows the door records for a live grade that gave criterion points and no rows. Tier 0 is
# no grader's tier (self 1, deterministic 2, model 3, adjudication 4), so these rows are never counted as model-graded
# or superseded as a self-grade, and the local grader id names the door.
GIVEN_POINTS_LOCAL_GRADER_ID = "given_points"
GIVEN_POINTS_GRADER_TIER = 0


def given_points_as_evidence(attempt: Any, now_iso: str) -> Any:
    """A live grade that reaches the door with criterion points and no evidence rows gets the given points recorded as
    its rows. Replay reads a grade from ``grading_evidence``; without rows it saw no
    criterion and applied a different observation than live did. Every grader door writes its own rows, so this
    records only what a caller handed in (a simulator, a test double): one row per given criterion, its points as
    given, ``local_grader_id`` ``given_points`` and ``grader_tier`` 0, no agent run and no learner confidence. The rows
    are then stamped with the contract, revision and observation ids like any grader's."""

    grade = attempt.grade
    if attempt.replace_existing or grade.evidence_rows or not grade.criterion_points:
        return attempt
    rows: list[dict[str, object]] = [
        {
            "id": new_ulid(),
            "criterion_id": criterion_id,
            "points_awarded": float(points),
            "evidence": "Points given with the grade; no grader wrote evidence.",
            "notes": None,
            "agent_run_id": None,
            "local_grader_id": GIVEN_POINTS_LOCAL_GRADER_ID,
            "grader_tier": GIVEN_POINTS_GRADER_TIER,
            "learner_confidence": None,
            "created_at": now_iso,
        }
        for criterion_id, points in grade.criterion_points.items()
    ]
    return replace(attempt, grade=replace(grade, evidence_rows=rows))
