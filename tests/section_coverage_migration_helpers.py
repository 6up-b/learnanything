"""What other test files use from ``tests/test_section_coverage_migration.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations


#: Every schema object 222 adds: the earlier migrations' "nothing else" diffs on the way to head read this.
C0A_ADDED_OBJECTS = frozenset({
    "section_coverage", "sqlite_autoindex_section_coverage_1", "idx_section_coverage_judged",
    "idx_section_coverage_section", "idx_section_coverage_lo", "section_coverage_no_update",
    "section_coverage_no_delete",
})
