"""What other test files use from ``tests/test_rw2d_receipts_migration.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations


#: What 219 adds: the earlier migrations' "nothing else changed" diffs on the way to head read this.
RW2D_ADDED_OBJECTS = frozenset({
    "field_signal_receipts", "field_signal_receipts_lo", "field_signal_receipts_no_update",
    "field_signal_receipts_no_delete", "sqlite_autoindex_field_signal_receipts_1",
    "sqlite_autoindex_field_signal_receipts_2",
})
#: What 219 alters: one added column (the earlier migrations' "nothing else changed" diffs read this).
RW2D_ALTERED_TABLES = frozenset({"workbench_sessions"})
