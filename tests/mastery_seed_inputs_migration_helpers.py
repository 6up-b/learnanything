"""What earlier migrations' upgrade diffs use from the mastery-seed migration
(``tests/test_mastery_seed_inputs_migration.py``), kept here because a test file never imports another
(``tests/test_test_layout.py``)."""

from __future__ import annotations


MASTERY_SEED = "mastery_seed_inputs"
#: What the migration adds (the table and its TEXT primary key's autoindex): earlier migrations' "nothing else
#: changed" diffs on the way to head read this.
MASTERY_SEED_ADDED_OBJECTS = frozenset({MASTERY_SEED, f"sqlite_autoindex_{MASTERY_SEED}_1"})
