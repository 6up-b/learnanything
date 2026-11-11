"""What other test files use from ``tests/test_hypothesis_marks.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from learnloop.followup_serve import workflow as wf

from tests.followup_journey_helpers import _answer, _call, _generate


MARKS_OFF = "\n[followup]\nhypothesis_marks = false\n"


def _rows(repository, table):
    with repository.connection() as connection:
        return [dict(row) for row in connection.execute(f"SELECT * FROM {table} ORDER BY created_at, id")]


def _serve_and_answer(ctx, repository, attempt_id, outcome, *, points=None):
    """The ready probe, opened through its doors and answered."""

    row = wf.get(repository, outcome.workflow_id)
    _call(ctx, "followup_status", {"attemptId": attempt_id})  # this process's vault reads the new item
    _call(ctx, "open_queue_item", {"practiceItemId": row["practice_item_id"]})
    _call(ctx, "get_probe_contract", {"practiceItemId": row["practice_item_id"]})
    return _answer(ctx, repository, row, points=points or {"fact_0": 0, "fact_1": 2}), row


def _released(ctx, repository, outcome, result):
    """Show anyway: the list on the attempt's own bundle."""

    _generate(ctx, repository)
    _call(ctx, "followup_show_anyway", {"attemptId": result.attempt_id})
    return _call(ctx, "get_feedback", {"attemptId": result.attempt_id})["hypothesisMarks"]


def _mark(ctx, attempt_id, mark, version=None, **extra):
    return _call(ctx, "record_hypothesis_mark", {"attemptId": attempt_id, "mark": mark, "hypothesisVersionId": version, **extra})
