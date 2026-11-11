"""What other test files use from ``tests/test_t1_batch_origin_migration.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations


#: What 218 alters: the earlier migrations' "nothing else changed" diffs on the way to head read this.
T1_ALTERED_TABLES = frozenset({"ingest_batches"})
