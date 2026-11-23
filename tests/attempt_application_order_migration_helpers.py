"""What earlier migrations' upgrade diffs use from the application-order migration
(``tests/test_attempt_application_order_migration.py``), kept here because a test file never imports another
(``tests/test_test_layout.py``)."""

from __future__ import annotations


APPLICATION_ORDER = "attempt_application_order"
#: What the migration adds (the table and its ``attempt_id`` UNIQUE constraint's autoindex; the INTEGER PRIMARY KEY has
#: none): earlier migrations' "nothing else changed" diffs on the way to head read this.
APPLICATION_ORDER_ADDED_OBJECTS = frozenset({APPLICATION_ORDER, f"sqlite_autoindex_{APPLICATION_ORDER}_1"})
