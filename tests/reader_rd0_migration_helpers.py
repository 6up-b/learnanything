"""What earlier migrations' upgrade diffs use from the Reader workbench v2 migration
(``tests/test_reader_rd0_migration.py``), kept here because a test file never imports another
(``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations


#: The ten tables and their roles (spec §15.1).
TABLES = {
    "desks": "workflow",
    "desk_windows": "workflow",
    "desk_op_receipts": "receipt",
    "pads": "workflow",
    "pad_block_versions": "raw_ledger",
    "pad_block_anchors": "raw_ledger",
    "pad_op_receipts": "receipt",
    "companion_exchange_context": "raw_ledger",
    "question_event_spans": "derived",
    "learner_text_gap_spans": "derived",
}
#: Their indexes and triggers.
OBJECTS = frozenset(TABLES) | {
    "idx_desk_windows_desk", "desk_op_receipts_no_update", "desk_op_receipts_no_delete", "idx_pads_home_desk",
    "idx_pad_block_versions_one_child", "idx_pad_block_versions_one_root", "idx_pad_block_versions_pad",
    "pad_block_versions_same_block", "pad_block_versions_no_update", "pad_block_versions_no_delete",
    "idx_pad_block_anchors_span", "idx_pad_block_anchors_block", "pad_block_anchors_no_update",
    "pad_block_anchors_no_delete", "pad_op_receipts_no_update", "pad_op_receipts_no_delete",
    "idx_companion_exchange_context_desk", "companion_exchange_context_no_update",
    "companion_exchange_context_no_delete", "idx_question_event_spans_row", "idx_question_event_spans_span",
    "idx_learner_text_gap_spans_row", "idx_learner_text_gap_spans_span",
}
#: The tables with a primary key that is not a rowid alias carry an autoindex each.
_AUTOINDEXED = ("desks", "desk_windows", "desk_op_receipts", "pads", "pad_block_versions", "pad_block_anchors",
                "pad_op_receipts", "companion_exchange_context")
#: What the migration adds: earlier migrations' "nothing else changed" diffs on the way to head read this.
RD0_ADDED_OBJECTS = OBJECTS | {f"sqlite_autoindex_{table}_1" for table in _AUTOINDEXED}
