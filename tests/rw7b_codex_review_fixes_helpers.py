"""What other test files use from ``tests/test_rw7b_codex_review_fixes.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from tests.reading_path_fixtures import call


LABELS = {"sec_eigen": "enrichment", "sec_spectral": "prerequisite"}


def _blocks(repository):
    with repository.connection() as connection:
        blocks = [dict(row) for row in connection.execute(
            "SELECT id, action, reading_json FROM attention_blocks ORDER BY rowid")]
        events = [dict(row) for row in connection.execute(
            "SELECT block_id, kind, detail_json FROM attention_block_events ORDER BY rowid")]
    return blocks, events


def _stage_reading(ctx, session_id):
    """Skip the plan's items (prefetch only) until its reading block is the
    current, staged and unstarted block."""

    for _ in range(20):
        step = call(ctx, "next_plan_item", {"sessionId": session_id, "serve": False})["step"]
        if step["kind"] == "reading":
            return step
        assert step["kind"] == "item", step
        call(ctx, "next_plan_item", {"sessionId": session_id, "skipPracticeItemId": step["practiceItemId"],
                                     "serve": False})
    raise AssertionError("no reading step")
