"""What earlier migrations' upgrade diffs use from the lifecycle-inputs migration
(``tests/test_attempt_lifecycle_inputs_migration.py``), kept here because a test file never imports another
(``tests/test_test_layout.py``)."""

from __future__ import annotations


LIFECYCLE_INPUTS = "attempt_lifecycle_inputs"
#: What the migration adds (the table and its TEXT primary key's autoindex): earlier migrations' "nothing else
#: changed" diffs on the way to head read this.
LIFECYCLE_INPUTS_ADDED_OBJECTS = frozenset({LIFECYCLE_INPUTS, f"sqlite_autoindex_{LIFECYCLE_INPUTS}_1"})
