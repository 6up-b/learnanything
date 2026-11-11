"""What other test files use from ``tests/test_learner_claim_superseded_migration.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations


#: What 225 alters: the earlier migrations' "nothing else changed" diffs on the way to head read this.
SUPERSEDED_ALTERED_TABLES = frozenset({"learner_claims"})
