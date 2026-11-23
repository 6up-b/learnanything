"""What earlier migrations' upgrade diffs use from the Reader workbench v2 video chapters migration
(``tests/test_reader_rd10_migration.py``), kept here because a test file never imports another
(``tests/test_test_layout.py``)."""

from __future__ import annotations

import sqlite3

#: The table and its role (spec §15.1's ``video_chapters``).
TABLES = {"video_chapters": "workflow"}
#: Its index and its two triggers (a decision made once; a decided chapter kept).
OBJECTS = frozenset(TABLES) | {"idx_video_chapters_reading", "video_chapters_decide_once", "video_chapters_keep_decided"}
#: The TEXT primary key's autoindex.
RD10_ADDED_OBJECTS = OBJECTS | {"sqlite_autoindex_video_chapters_1"}


def undo_268(connection: sqlite3.Connection) -> None:
    """Take a head copy back to before 268: its table dropped. The caller removes 268's ``schema_migrations`` row
    with its own."""

    for table in TABLES:
        connection.execute(f"DROP TABLE IF EXISTS {table}")
