"""What other test files use from ``tests/test_mobile_jobs_migration.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations


#: What 239 adds (its table, its autoindexes, its indexes).
M2A_ADDED_OBJECTS = frozenset({
    "mobile_jobs", "sqlite_autoindex_mobile_jobs_1", "sqlite_autoindex_mobile_jobs_2",
    "mobile_jobs_request", "mobile_jobs_open",
})
