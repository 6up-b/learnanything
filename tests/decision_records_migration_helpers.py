"""What other test files use from ``tests/test_decision_records_migration.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations


TABLE = "decision_records"
OBJECTS = frozenset({TABLE, "decision_records_trace", "decision_records_subject", "decision_records_parent",
                     "decision_records_kind", "decision_records_no_update", "decision_records_no_delete",
                     "model_call_receipts_trace"})
#: What 253 adds (with the table's own autoindex): earlier migrations' "nothing else changed" diffs on the way to head read this.
B1_ADDED_OBJECTS = OBJECTS | {f"sqlite_autoindex_{TABLE}_1"}
#: What 253 alters (one nullable column on a receipt table): the same diffs read this.
B1_ALTERED_TABLES = frozenset({"model_call_receipts"})
