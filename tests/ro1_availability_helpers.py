"""What other test files use from ``tests/test_ro1_availability.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations


NEW_COLUMNS = {"practice_attempts": {"received_at", "received_at_source"},
               "derived_state_rebuilds": {"projection_switches_json"}}
#: What 244 alters (no object is added): earlier migrations' "nothing else changed" diffs on the way to head
#: read this.
RO1_ALTERED_TABLES = frozenset(NEW_COLUMNS)
