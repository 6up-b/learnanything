"""What other test files use from ``tests/test_session_ownership_migration.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations


#: Every schema object 226 adds, and the table it alters: the earlier
#: migrations' "nothing else changed" diffs on the way to head read these.
PR4_ADDED_OBJECTS = frozenset({
    "session_handoffs", "sqlite_autoindex_session_handoffs_1", "idx_session_handoffs_session",
    "session_handoffs_no_update", "session_handoffs_no_delete",
})
PR4_ALTERED_TABLES = frozenset({"sessions"})
