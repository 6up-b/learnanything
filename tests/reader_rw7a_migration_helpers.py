"""What other test files use from ``tests/test_reader_rw7a_migration.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations


#: What 217 adds: the earlier migrations' "nothing else changed" diffs on the
#: way to head read these.
RW7A_ADDED_OBJECTS = frozenset({
    "reader_path_sections", "idx_reader_path_sections_judged", "idx_reader_path_sections_reading",
    "reader_path_sections_no_update", "reader_path_sections_no_delete", "sqlite_autoindex_reader_path_sections_1",
    "reader_path_depths", "idx_reader_path_depths_source", "reader_path_depths_no_update",
    "reader_path_depths_no_delete", "sqlite_autoindex_reader_path_depths_1",
})
