"""What other test files use from ``tests/test_router_r2a_serving.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from learnloop.db.repositories import Repository
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.registry import METHOD_REGISTRY


FROZEN = datetime(2026, 10, 12, 9, 30, tzinfo=UTC)


def _call(ctx, name, params):
    spec = METHOD_REGISTRY[name]
    return spec.handler(ctx, spec.params_model.model_validate(params))


def _hold_cold_check(env, item_id: str) -> None:
    """An open cold retry holds ``item_id``: serving it spends the check."""

    from learnloop.attempts.attempts import COLD_FOLLOWUP_TASK_KINDS

    assert "cold_retry" in COLD_FOLLOWUP_TASK_KINDS
    with env.repository.connection() as connection:
        connection.execute(
            "INSERT INTO followup_tasks(id, kind, case_kind, case_ref, not_before, status, selected_item_id, "
            "created_at, updated_at) VALUES ('task_cold', 'cold_retry', 'misconception', 'case_1', "
            "'2026-10-12T08:00:00Z', 'pending', ?, '2026-10-12T08:00:00Z', '2026-10-12T08:00:00Z')",
            (item_id,),
        )
        connection.commit()


def _strip_ids(detail: dict) -> dict:
    return {key: value for key, value in detail.items() if key not in ("decision_ref",)}


def _plan_trace(root: Path) -> list[tuple]:
    ctx = SidecarContext()
    ctx.load(root)
    ctx.grading_provider_override = "manual"
    # A fixed session id: the scheduler's seeded exploration hashes it, so two
    # copies compare only when they serve the same session.
    session_id = "s_g8"
    with Repository(root / "state.sqlite").connection() as connection:
        # An owner copy keeps the owner's own planned blocks (built at their versions, by
        # their router): the trace is the blocks this serve builds, not those.
        earlier = {row[0] for row in connection.execute("SELECT id FROM attention_blocks")}
        connection.execute("UPDATE sessions SET ended_at = ? WHERE ended_at IS NULL", ("2026-10-12T09:00:00Z",))
        connection.execute(
            "INSERT INTO sessions(id, started_at, available_minutes) VALUES (?, '2026-10-12T09:30:00Z', 25)",
            (session_id,),
        )
        connection.commit()
    trace = []
    for _ in range(4):
        result = _call(ctx, "next_plan_item", {"sessionId": session_id, "serve": True})
        step = result["step"]
        if step["kind"] != "item":
            break
        _call(ctx, "next_plan_item", {"sessionId": session_id, "skipPracticeItemId": step["practiceItemId"]})
    vault, repository = ctx.require_vault()
    with repository.connection() as connection:
        for row in connection.execute(
            "SELECT b.id, b.lane, b.chosen_by, e.detail_json FROM attention_blocks b "
            "JOIN attention_block_events e ON e.block_id = b.id AND e.kind = 'block_chosen' "
            "WHERE b.daily_plan_id IS NOT NULL ORDER BY b.created_at, b.plan_ordinal"
        ):
            if row["id"] in earlier:
                continue
            items = [
                json.loads(event["detail_json"])["practice_item_id"]
                for event in connection.execute(
                    "SELECT detail_json FROM attention_block_events WHERE block_id = ? AND kind = 'item_planned' "
                    "ORDER BY event_ordinal", (row["id"],)
                )
            ]
            trace.append((row["lane"], row["chosen_by"], tuple(items), _strip_ids(json.loads(row["detail_json"]))))
    return trace
