"""What earlier migrations' upgrade diffs use from refactor K3.5's migration 255 (``tests/test_apply_recovery.py``),
kept here because a test file never imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations


#: What 255 alters (``apply_intents`` rebuilt with two more statuses and three nullable columns; its index is recreated
#: with the same definition): earlier migrations' "nothing else changed" diffs on the way to head read this.
K35_ALTERED_TABLES = frozenset({"apply_intents"})
