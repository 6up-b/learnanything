"""What other test files use from ``tests/test_rw7b_fix_round2.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from tests.reading_path_fixtures import call


def _plan_row(repository) -> dict:
    with repository.connection() as connection:
        [row] = connection.execute(
            "SELECT status, stop_reason, completed_at FROM daily_plans ORDER BY created_at, id").fetchall()
    return dict(row)


def _skip_to_done(ctx, session_id) -> dict:
    """Skip every practice item the plan serves until it has nothing left."""

    for _ in range(40):
        step = call(ctx, "next_plan_item", {"sessionId": session_id, "serve": False})["step"]
        if step["kind"] == "done":
            return step
        assert step["kind"] == "item", step
        call(ctx, "next_plan_item", {"sessionId": session_id, "skipPracticeItemId": step["practiceItemId"],
                                     "serve": False})
    raise AssertionError("the plan never finished")
