"""What other test files use from ``tests/test_router_objective_migration.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations


TABLES = ("session_receipts", "decision_state_receipts", "goal_lifecycle_events")
RO0_ADDED_OBJECTS = frozenset({
    *TABLES,
    "session_receipts_once", "session_receipts_created", "decision_state_receipts_created", "goal_lifecycle_events_goal",
    "sqlite_autoindex_session_receipts_1", "sqlite_autoindex_decision_state_receipts_1",
    "sqlite_autoindex_decision_state_receipts_2", "sqlite_autoindex_goal_lifecycle_events_1",
    *(f"{table}_no_{verb}" for table in TABLES for verb in ("update", "delete")),
})
