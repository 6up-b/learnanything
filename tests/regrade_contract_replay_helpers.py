"""What other test files use from ``tests/test_regrade_contract_replay.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from learnloop.attempts.attempts import (
    ApplyAttemptInput,
    AttemptDraft,
    ResolvedGrade,
    apply_attempt,
    calculate_rubric_score,
)
from learnloop.attempts.grading import resolved_rubric
from learnloop.attempts.regrade import regrade_attempt
from learnloop.clock import FrozenClock
from learnloop.vault.loader import load_vault
from learnloop.vault.writer import upsert_practice_item

from tests.diagnosis_fakes import ReviewFakeClient
from tests.split_live_helpers import ReadyRuntime
from tests.held_grade_evidence_helpers import _iso
from tests.route_rules_in_grader_helpers import ITEM


#: Another item of the same learning object (``lo_svd``), for "every later
#: regrade on that learning object fails too".
SIBLING_ITEM = "pi_svd_compute_002"


class PointsGrader(ReviewFakeClient):
    """A grader fake that awards exactly ``points`` (criterion -> points),
    attributing no error (every mark-down is assessed: the route is not
    divergent, so no own-route rule applies)."""

    def __init__(self, points: dict[str, float], **kwargs) -> None:
        super().__init__(**kwargs)
        self.points = dict(points)

    def _grade_parts(self, context):
        parts = super()._grade_parts(context)
        parts["evidence"] = [
            {**row, "points_awarded": float(self.points.get(row["criterion_id"], 0.0))}
            for row in parts["evidence"]
        ]
        parts["correct"] = True  # no attribution: the mark-downs are the grade
        return parts


def _set_result_points(paths, points: float) -> None:
    """Rewrite ``result``'s worth on the item (the maximum follows the criteria)."""

    data = load_vault(paths.root).practice_items[ITEM].model_dump(mode="json")
    rubric = data["grading_rubric"]
    rubric["criteria"] = [
        {**criterion, "points": points} if criterion["id"] == "result" else criterion
        for criterion in rubric["criteria"]
    ]
    rubric["max_points"] = int(sum(float(criterion["points"]) for criterion in rubric["criteria"]))
    upsert_practice_item(paths.root, data)


def _self_graded_apply(vault, repository, item_id, points, *, attempt_id, when):
    """A self-graded (tier 1) answer through the shared attempt step."""

    rubric = resolved_rubric(vault, vault.practice_items[item_id])
    return apply_attempt(
        vault,
        repository,
        ApplyAttemptInput(
            draft=AttemptDraft(
                practice_item_id=item_id, learner_answer_md="an answer", attempt_type="independent_attempt",
            ),
            attempt_id=attempt_id,
            grade=ResolvedGrade(
                rubric_score=calculate_rubric_score(rubric, dict(points), []),
                criterion_points=dict(points),
                evidence_rows=[
                    {
                        "id": f"ge_{attempt_id}_{cid}", "criterion_id": cid,
                        "points_awarded": float(value), "evidence": "self", "notes": None,
                        "local_grader_id": "learner", "grader_tier": 1, "created_at": _iso(when),
                    }
                    for cid, value in points.items()
                ],
                error_attributions=[],
                grader_confidence=1.0,
                confidence=3,
                manual_review_reason=None,
                feedback_md="self-graded",
            ),
            grading_source="self",
        ),
        clock=FrozenClock(when),
    )


def _regrade(vault, repository, attempt_id, points, *, when):
    return regrade_attempt(
        vault, repository, repository.fetch_practice_attempt(attempt_id),
        runtime=ReadyRuntime(), client=PointsGrader(points), grading_source="ai",
        clock=FrozenClock(when),
    )


def _grade(repository, attempt_id) -> tuple[int, float]:
    attempt = repository.fetch_practice_attempt(attempt_id)
    return int(attempt["rubric_score"]), float(attempt["correctness"])
