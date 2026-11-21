"""The seen-passages migration: ``reader_seen_spans`` and
``reader_section_ends``.

Two new append-only WORKFLOW tables, refused to adaptive difficulty; nothing else changes. A vault one migration below
the head gains exactly their objects, and every row it already held is as it was: ``reader_section_progress``'s counts
are never turned into passage identities. The number is the migration's file name alone (``MIGRATION``).
"""

from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path

import pytest

from learnloop.adaptive_difficulty.protected_tables import DENIED, ROLES
from learnloop.db.migrate import UPGRADE_TEST_HELPER, applied_versions, apply_migrations, discover_migrations, upgrade_allowance
from learnloop.db.table_roles import TABLE_ROLES, TableRole
from tests.helpers import MIGRATION_HEAD_FIXTURE
from tests.reader_seen_spans_migration_helpers import SECTION_ENDS, SEEN_SPANS, SEEN_SPANS_ADDED_OBJECTS

HEAD = MIGRATION_HEAD_FIXTURE / "state.sqlite"
MIGRATION = next(m for m in discover_migrations() if m.name == "reader_seen_spans")
COLUMNS = {
    SEEN_SPANS: ["extraction_id", "span_id", "section_id", "first_seen_at", "origin"],
    SECTION_ENDS: ["extraction_id", "section_id", "span_id", "first_seen_at", "origin"],
}


def test_both_tables_are_workflow_and_denied_to_adaptive_difficulty():
    # WORKFLOW, as reader_section_progress beside them: never cleared by a rebuild, and outside the dataset
    # export and the adjudication evidence (which take RAW_LEDGER and RECEIPT tables only).
    for table in COLUMNS:
        assert TABLE_ROLES[table] is TableRole.WORKFLOW
        assert ROLES[table] == DENIED


def test_the_head_fixture_holds_both_empty_in_rollback_mode():
    assert HEAD.read_bytes()[18:20] == b"\x01\x01"
    assert MIGRATION.version in applied_versions(HEAD)
    with closing(sqlite3.connect(f"file:{HEAD}?mode=ro", uri=True)) as connection:
        for table, columns in COLUMNS.items():
            assert [row[1] for row in connection.execute(f"PRAGMA table_info({table})")] == columns
            assert connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] == 0


def _downgraded(database: Path) -> None:
    with closing(sqlite3.connect(HEAD)) as source, closing(sqlite3.connect(database)) as target:
        source.backup(target)
    with closing(sqlite3.connect(database)) as connection:
        for table in COLUMNS:
            connection.execute(f"DROP TABLE {table}")  # its index and triggers go with it
        connection.execute("DELETE FROM schema_migrations WHERE version = ?", (MIGRATION.version,))
        connection.commit()


def _rows(connection: sqlite3.Connection, table: str) -> list[tuple]:
    return sorted(tuple(row) for row in connection.execute(f"SELECT * FROM {table}"))


def test_it_adds_the_two_tables_and_changes_nothing_else(tmp_path):
    database = tmp_path / "state.sqlite"
    _downgraded(database)
    with closing(sqlite3.connect(database)) as connection:
        before = {row[0]: row[1] for row in connection.execute("SELECT name, sql FROM sqlite_master")}
        progress_before = _rows(connection, "reader_section_progress")
    with upgrade_allowance(UPGRADE_TEST_HELPER):
        assert [m.version for m in apply_migrations(database)] == [MIGRATION.version]
    with closing(sqlite3.connect(database)) as connection:
        after = {row[0]: row[1] for row in connection.execute("SELECT name, sql FROM sqlite_master")}
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        # No backfill: the counts stay counts, and no passage is made from them.
        assert _rows(connection, "reader_section_progress") == progress_before
        for table in COLUMNS:
            assert connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] == 0
    assert set(after) - set(before) == SEEN_SPANS_ADDED_OBJECTS
    assert {name for name in before if before[name] != after[name]} == set()


def test_both_are_append_only_with_one_row_per_identity_and_a_known_origin(tmp_path):
    database = tmp_path / "state.sqlite"
    with closing(sqlite3.connect(HEAD)) as source, closing(sqlite3.connect(database)) as target:
        source.backup(target)
    with closing(sqlite3.connect(database)) as connection:
        stamp = "2026-11-20T00:00:00+00:00"
        seen = f"INSERT INTO {SEEN_SPANS} VALUES ('e1', ?, 'u1', ?, ?)"
        ends = f"INSERT INTO {SECTION_ENDS} VALUES ('e1', ?, 'b2', ?, ?)"
        connection.execute(seen, ("b1", stamp, "desktop"))
        connection.execute(ends, ("u1", stamp, "phone"))
        for statement, values in ((seen, ("b1", stamp, "phone")), (ends, ("u1", stamp, "desktop"))):
            with pytest.raises(sqlite3.IntegrityError):  # the identity is the primary key
                connection.execute(statement, values)
        for statement, values in ((seen, ("b2", stamp, "restore")), (ends, ("u2", stamp, "mcp"))):
            with pytest.raises(sqlite3.IntegrityError):
                connection.execute(statement, values)
        for table in COLUMNS:
            for statement in (f"UPDATE {table} SET origin = 'phone'", f"DELETE FROM {table}"):
                with pytest.raises(sqlite3.IntegrityError, match="append-only"):
                    connection.execute(statement)
