"""What other test files use from ``tests/test_re0_capture.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations


#: What 252 alters (one column on a ledger table): earlier migrations' "nothing else changed" diffs on the way to head read this.
RE0_ALTERED_TABLES = frozenset({"practice_attempts"})
