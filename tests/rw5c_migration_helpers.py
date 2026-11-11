"""What other test files use from ``tests/test_rw5c_migration.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations


#: What 238 adds (its table, its autoindex, its index and triggers).
RW5C_ADDED_OBJECTS = frozenset({
    "figure_source_checks", "sqlite_autoindex_figure_source_checks_1", "idx_figure_source_checks_figure",
    "figure_source_checks_no_update", "figure_source_checks_no_delete",
})
