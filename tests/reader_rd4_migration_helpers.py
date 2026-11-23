"""What earlier migrations' upgrade diffs use from the Reader workbench v2 scratchpads migration
(``tests/test_reader_rd4_migration.py``), kept here because a test file never imports another
(``tests/test_test_layout.py``)."""

from __future__ import annotations

import sqlite3

#: The five tables and their roles (spec §15.1).
TABLES = {
    "pad_block_submissions": "raw_ledger",
    "carried_questions": "workflow",
    "carried_question_events": "raw_ledger",
    "pad_proposals": "receipt",
    "proposal_labels": "raw_ledger",
}
#: The append-only ones, each refusing UPDATE, DELETE and a replacing INSERT by trigger.
APPEND_ONLY = ("pad_block_submissions", "carried_question_events", "pad_proposals", "proposal_labels")
#: Their indexes and triggers.
OBJECTS = frozenset(TABLES) | {
    "idx_pad_block_submissions_block", "idx_carried_questions_state", "idx_carried_question_events_carried",
    "idx_pad_proposals_pad", "idx_proposal_labels_proposal",
} | {f"{table}_no_{verb}" for table in APPEND_ONLY for verb in ("update", "delete", "replace")}
#: Every table's TEXT primary key carries an autoindex; pad_proposals' unique block version a second one.
RD4_ADDED_OBJECTS = OBJECTS | {f"sqlite_autoindex_{table}_1" for table in TABLES} | {
    "sqlite_autoindex_pad_proposals_2"}
#: The three tables the migration rebuilds to widen a CHECK (their indexes and triggers come back unchanged).
RD4_REBUILT = ("learner_text_gaps", "learner_text_gap_jobs", "learner_text_gap_reversals")
#: What earlier migrations' "nothing else changed" diffs on the way to head subtract.
RD4_ALTERED_TABLES = frozenset(RD4_REBUILT)

_SOURCE_KIND = ",\n    'lesson', 'external_chat', 'pad_text'"
_REVERSAL = ", 'superseded', 'retracted'"


def undo_266(connection: sqlite3.Connection) -> None:
    """Take a head copy back to before 266: its five tables dropped and the three rebuilt tables' CHECKs as they
    were (rows, indexes and triggers kept), so an earlier migration's own downgrade can start from 265's schema.
    The caller removes 266's ``schema_migrations`` row with its own."""

    connection.execute("PRAGMA foreign_keys = OFF")
    for table in ("carried_question_events", "carried_questions", "proposal_labels", "pad_proposals",
                  "pad_block_submissions"):
        connection.execute(f"DROP TABLE IF EXISTS {table}")
    for table in RD4_REBUILT:
        sql = connection.execute("SELECT sql FROM sqlite_master WHERE type = 'table' AND name = ?",
                                 (table,)).fetchone()[0]
        old = sql.replace(_SOURCE_KIND, ",\n    'lesson', 'external_chat'").replace(
            "(\n    'undo_edge', 'undo_creation', 'not_this_belief', 'unlinked'" + _REVERSAL + "\n  ))",
            "('undo_edge', 'undo_creation', 'not_this_belief', 'unlinked'))")
        assert old != sql, table
        dependents = [row[0] for row in connection.execute(
            "SELECT sql FROM sqlite_master WHERE tbl_name = ? AND type IN ('index', 'trigger') AND sql IS NOT NULL",
            (table,))]
        # The migration's own order (new table, copy, drop, rename the new one): renaming the old table away
        # would rewrite the foreign keys that name it.
        connection.execute(old.replace(f'CREATE TABLE "{table}"', f"CREATE TABLE {table}__undo", 1))
        connection.execute(f"INSERT INTO {table}__undo SELECT * FROM {table}")
        connection.execute(f"DROP TABLE {table}")
        connection.execute(f"ALTER TABLE {table}__undo RENAME TO {table}")
        for statement in dependents:
            connection.execute(statement)
