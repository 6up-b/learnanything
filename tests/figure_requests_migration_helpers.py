"""What other test files use from ``tests/test_figure_requests_migration.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations


#: Every schema object 224 adds, and the table it rebuilds: the earlier
#: migrations' "nothing else changed" diffs on the way to head read these.
RW5D_ADDED_OBJECTS = frozenset({
    "figure_requests", "sqlite_autoindex_figure_requests_1", "idx_figure_requests_figure",
    "idx_figure_requests_created", "figure_requests_no_delete", "figure_requests_figure_once",
    "idx_interactive_figures_request",
})
RW5D_ALTERED_TABLES = frozenset({"interactive_figures"})
