"""What other test files use from ``tests/test_ih3_migration.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations


TABLE = "router_learner_preferences"
OBJECTS = frozenset({TABLE, "router_learner_preferences_decision", "router_learner_preferences_session",
                     "router_learner_preferences_served", "router_learner_preferences_no_update",
                     "router_learner_preferences_no_delete"})
#: What 251 adds (with the table's own autoindex): earlier migrations' "nothing else changed" diffs on the way to head read this.
IH3_ADDED_OBJECTS = OBJECTS | {f"sqlite_autoindex_{TABLE}_1"}
