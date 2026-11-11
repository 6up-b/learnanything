"""What other test files use from ``tests/test_mobile_v3_migration.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations


TABLE = "help_assists"
#: What 250 alters (its table's text: the surface list): earlier migrations' "alters nothing else" diffs read this.
V3_ALTERED_TABLES = frozenset({TABLE})
