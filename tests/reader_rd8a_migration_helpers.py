"""What earlier migrations' upgrade diffs use from the Reader workbench v2 pen-and-ink migration
(``tests/test_reader_rd8a_migration.py``), kept here because a test file never imports another
(``tests/test_test_layout.py``)."""

from __future__ import annotations

import sqlite3

#: The two tables and their roles (spec §15.1's ``ink_strokes``; ``ink_transcriptions`` keeps each reading).
TABLES = {"ink_strokes": "raw_ledger", "ink_transcriptions": "receipt"}
#: Both append-only, each refusing UPDATE, DELETE and a replacing INSERT by trigger.
APPEND_ONLY = tuple(TABLES)
#: Their indexes and triggers.
OBJECTS = frozenset(TABLES) | {"idx_ink_strokes_owner"} | {
    f"{table}_no_{verb}" for table in APPEND_ONLY for verb in ("update", "delete", "replace")}
#: Every table's TEXT primary key carries an autoindex; the readings' unique owner and strokes a second one.
RD8A_ADDED_OBJECTS = OBJECTS | {f"sqlite_autoindex_{table}_1" for table in TABLES} | {
    "sqlite_autoindex_ink_transcriptions_2"}


def undo_267(connection: sqlite3.Connection) -> None:
    """Take a head copy back to before 267: its two tables dropped. The caller removes 267's ``schema_migrations``
    row with its own."""

    for table in TABLES:
        connection.execute(f"DROP TABLE IF EXISTS {table}")


#: The replacing-INSERT guard of ``ink_transcriptions`` as 267 wrote it (the primary key alone); 270 widened it.
GUARD_267 = "WHEN EXISTS (SELECT 1 FROM ink_transcriptions WHERE transcription_id = NEW.transcription_id)"


def undo_270(connection: sqlite3.Connection) -> None:
    """Take a head copy back to before 270: the guard as 267 wrote it. The caller removes 270's ``schema_migrations``
    row with its own."""

    connection.execute("DROP TRIGGER IF EXISTS ink_transcriptions_no_replace")
    connection.execute(
        "CREATE TRIGGER ink_transcriptions_no_replace\nBEFORE INSERT ON ink_transcriptions\n" + GUARD_267
        + "\nBEGIN\n    SELECT RAISE(ABORT, 'ink_transcriptions is append-only');\nEND")
