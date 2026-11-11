"""What other test files use from ``tests/test_figure_prefetch_migration.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from learnloop.db.table_roles import TableRole


P5_TABLES = {"figure_prefetch_decisions": TableRole.RAW_LEDGER, "plan_usage_pauses": TableRole.RAW_LEDGER}
#: What 237 adds (its tables, their indexes and autoindexes, the triggers, the figure_requests index).
P5_ADDED_OBJECTS = frozenset({
    *P5_TABLES,
    "figure_prefetch_decisions_no_delete", "figure_prefetch_decisions_set_once",
    "idx_figure_prefetch_decisions_created", "idx_figure_prefetch_decisions_key", "idx_figure_prefetch_decisions_open",
    "idx_figure_requests_prefetch_decision", "plan_usage_pauses_no_delete", "plan_usage_pauses_no_update",
    "sqlite_autoindex_figure_prefetch_decisions_1", "sqlite_autoindex_plan_usage_pauses_1",
    "sqlite_autoindex_plan_usage_pauses_2",
})
