"""What other test files use from ``tests/test_deliverable_curriculum_migration.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations


#: Every schema object 228 adds (it alters nothing): the earlier migrations' "nothing
#: else changed" diffs on the way to head read these.
C0B_ADDED_OBJECTS = frozenset({
    "deliverable_scope_inputs", "sqlite_autoindex_deliverable_scope_inputs_1", "idx_deliverable_scope_inputs_goal",
    "deliverable_scope_inputs_no_update", "deliverable_scope_inputs_no_delete",
    "deliverable_scope_resolutions", "sqlite_autoindex_deliverable_scope_resolutions_1",
    "idx_deliverable_scope_resolutions_goal", "deliverable_scope_resolutions_no_update",
    "deliverable_scope_resolutions_no_delete",
    "deliverable_path_sections", "sqlite_autoindex_deliverable_path_sections_1",
    "idx_deliverable_path_sections_judged", "idx_deliverable_path_sections_goal",
    "idx_deliverable_path_sections_reading", "deliverable_path_sections_no_update",
    "deliverable_path_sections_no_delete",
})
