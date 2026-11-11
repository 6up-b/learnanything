"""What other test files use from ``tests/test_facet_evidence_timeline.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from learnloop.clock import FrozenClock

from tests.helpers import NOW


def _attempt(vault, repository, item_id, criterion, *, hints_used=0, clock=None):
    from learnloop.attempts.attempts import (
        AttemptDraft,
        SelfGradeInput,
        complete_self_graded_attempt,
    )

    return complete_self_graded_attempt(
        vault,
        repository,
        AttemptDraft(
            practice_item_id=item_id,
            learner_answer_md="An answer.",
            attempt_type="independent_attempt",
            hints_used=hints_used,
        ),
        SelfGradeInput(criterion_points={"c1": criterion}, fatal_errors=[], confidence=4),
        clock=clock or FrozenClock(NOW),
    )
