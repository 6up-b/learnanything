"""What earlier migrations' upgrade diffs use from the Reader workbench v2 inline checks migration
(``tests/test_reader_rd7a_migration.py``), kept here because a test file never imports another
(``tests/test_test_layout.py``)."""

from __future__ import annotations

import sqlite3

from learnloop.db.migrate import discover_migrations

#: The fix round's migration (its number is its file name's).
FIX_VERSION = next(m for m in discover_migrations() if m.name == "reader_workbench_inline_checks_fix").version

#: The tables and their roles (spec §15's ``check_administrations`` and ``check_veil_sets``).
TABLES = {"check_administrations": "workflow", "check_veil_sets": "receipt"}
#: Their indexes and triggers, and the video chapters' replacement guard (RD10's review, finding 10).
OBJECTS = frozenset(TABLES) | {
    "idx_check_administrations_one_open", "idx_check_administrations_commitment",
    "check_administrations_closed_final", "check_administrations_kept",
    "check_veil_sets_no_update", "check_veil_sets_no_delete", "check_veil_sets_no_replace",
    "video_chapters_no_replace_decided",
}
#: The fix round's migration (272) adds one object on these tables: the administrations' replacing-insert guard. An
#: earlier migration's upgrade diff runs both, so it subtracts both.
FIX_OBJECTS = frozenset({"check_administrations_no_replace"})
#: The TEXT primary keys' and UNIQUE columns' autoindexes, and the fix round's object.
RD7A_ADDED_OBJECTS = OBJECTS | FIX_OBJECTS | {
    "sqlite_autoindex_check_administrations_1", "sqlite_autoindex_check_administrations_2",
    "sqlite_autoindex_check_administrations_3", "sqlite_autoindex_check_veil_sets_1",
    "sqlite_autoindex_check_veil_sets_2",
}


def undo_270(connection: sqlite3.Connection) -> None:
    """Take a head copy back to before 270 and its fix round (272): their tables and the video chapters' guard
    dropped, and 272's ``schema_migrations`` row removed (it altered 270's tables, so it is applied again after 270).
    The caller removes 270's row with its own."""

    connection.execute("DELETE FROM schema_migrations WHERE version = ?", (FIX_VERSION,))

    connection.execute("DROP TRIGGER IF EXISTS video_chapters_no_replace_decided")
    for table in ("check_veil_sets", "check_administrations"):
        connection.execute(f"DROP TABLE IF EXISTS {table}")
