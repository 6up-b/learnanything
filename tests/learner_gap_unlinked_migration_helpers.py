"""What other test files use from ``tests/test_learner_gap_unlinked_migration.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations


#: The object 235 redefines (rebuilt in place, same name; it adds nothing): the earlier
#: migrations' "nothing else changed" diffs on the way to head read it.
UNLINKED_ALTERED_TABLES = frozenset({"learner_text_gap_reversals"})
