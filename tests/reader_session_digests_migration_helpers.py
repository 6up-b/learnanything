"""What other test files use from ``tests/test_reader_session_digests_migration.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations


#: Every schema object 227 adds: the earlier migrations' "nothing else
#: changed" diffs on the way to head read these.
RW6B_ADDED_OBJECTS = frozenset({
    "reader_session_digests", "sqlite_autoindex_reader_session_digests_1",
    "sqlite_autoindex_reader_session_digests_2", "idx_reader_session_digests_extraction",
    "idx_reader_session_digests_ended",
})
