"""What other test files use from ``tests/test_help_assist_work_md_migration.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations


#: The table 230 alters (it adds no object): the earlier migrations' "nothing
#: else changed" diffs on the way to head read this.
DR2_ALTERED_TABLES = frozenset({"help_assists"})
