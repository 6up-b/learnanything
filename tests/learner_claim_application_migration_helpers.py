"""What other test files use from ``tests/test_learner_claim_application_migration.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations


#: What 221 alters: the earlier migrations' "nothing else changed" diffs on the way to head read this.
CLAIM_POINT_ALTERED_TABLES = frozenset({"learner_claims"})
