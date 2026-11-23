"""What earlier migrations' upgrade diffs use from the Reader workbench v2 guards migration
(``tests/test_reader_rd0_guards_migration.py``), kept here because a test file never imports another
(``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

INITIALIZATIONS = "projection_initializations"
GUARDS = frozenset({
    "desk_op_receipts_no_replace", "pad_op_receipts_no_replace", "pad_block_versions_no_replace",
    "pad_block_anchors_no_replace", "companion_exchange_context_no_replace",
})
INDEX = "idx_interaction_events_reader_answer_question"
OBJECTS = GUARDS | {INDEX, INITIALIZATIONS, "projection_initializations_no_update",
                    "projection_initializations_no_delete", "projection_initializations_no_replace"}
#: What the migration adds (with the receipt table's autoindex): earlier migrations' "nothing else changed"
#: diffs on the way to head read this.
RD0_GUARDS_ADDED_OBJECTS = OBJECTS | {f"sqlite_autoindex_{INITIALIZATIONS}_1"}
