"""What other test files use from ``tests/test_te3a_migration.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations


TABLE = "ad_reading_opportunities"
#: What 249 alters (its table's text: the kind list): earlier migrations' "alters nothing else" diffs read this.
TE3A_ALTERED_TABLES = frozenset({TABLE})
