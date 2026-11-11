"""Mobile v2 stage V3, migration 250: ``help_assists.surface`` gains ``'phone_practice'`` (V2's landing ruling R5).

The table is rebuilt temp-then-rename with every row and id preserved: the same columns, CHECKs (the surface list
widened by one value), indexes and append-only triggers. Nothing else in the schema changes. An item's own hint
revealed on the phone then records the phone's surface; the desktop's stays ``practice``.
"""

from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path

import pytest

from learnloop.db.migrate import UPGRADE_TEST_HELPER, apply_migrations, discover_migrations, upgrade_allowance
from learnloop.db.table_roles import TABLE_ROLES, TableRole
from tests.helpers import MIGRATION_HEAD_FIXTURE
from tests.mobile_v3_migration_helpers import TABLE, V3_ALTERED_TABLES

HEAD = MIGRATION_HEAD_FIXTURE / "state.sqlite"
#: The objects 250 drops and recreates (same names and definitions).
V3_REBUILT_OBJECTS = frozenset({
    TABLE, "sqlite_autoindex_help_assists_1", "idx_help_assists_session_item", "idx_help_assists_attempt",
    "idx_help_assists_submission", "idx_help_assists_workbench", "idx_help_assists_requested", "idx_help_assists_figure",
    "help_assists_no_delete", "help_assists_identity_fixed",
})
_OLD = "CHECK (surface IN ('practice', 'workbench', 'guided_redo', 'tutor'))"
_NEW = "CHECK (surface IN ('practice', 'workbench', 'guided_redo', 'tutor', 'phone_practice'))"
_ROW = ("INSERT INTO help_assists (id, surface, assist_kind, practice_item_id, chooser, shown, requested_at) "
        "VALUES (?, ?, 'hint', 'pi_1', 'none', 1, '2026-11-07T09:00:00Z')")


def test_250_is_the_head_and_help_assists_stays_a_raw_ledger():
    names = {migration.version: migration.path.name for migration in discover_migrations()}
    assert names[250] == "250_help_assists_phone_surface.sql"
    assert TABLE_ROLES[TABLE] is TableRole.RAW_LEDGER


def test_the_head_fixture_holds_250_in_rollback_mode():
    assert HEAD.read_bytes()[18:20] == b"\x01\x01"
    with closing(sqlite3.connect(f"file:{HEAD}?mode=ro", uri=True)) as connection:
        sql = connection.execute("SELECT sql FROM sqlite_master WHERE name = ?", (TABLE,)).fetchone()[0]
        assert _NEW in sql and _OLD not in sql


def _downgraded(database: Path) -> None:
    """The head as it stood at 249: the table rebuilt with 232's surface list, 250's row removed."""

    with closing(sqlite3.connect(HEAD)) as source, closing(sqlite3.connect(database)) as target:
        source.backup(target)
    with closing(sqlite3.connect(database)) as connection:
        objects = connection.execute("SELECT sql FROM sqlite_master WHERE tbl_name = ? AND sql IS NOT NULL "
                                     "AND type != 'table'", (TABLE,)).fetchall()
        table_sql = connection.execute("SELECT sql FROM sqlite_master WHERE name = ?", (TABLE,)).fetchone()[0]
        connection.execute("PRAGMA foreign_keys = OFF")
        connection.execute(f"DROP TABLE {TABLE}")
        connection.execute(table_sql.replace(_NEW, _OLD))
        for (sql,) in objects:
            connection.execute(sql)
        connection.execute("DELETE FROM schema_migrations WHERE version = 250")
        connection.commit()


def test_250_widens_the_surface_and_keeps_every_row_index_and_trigger(tmp_path):
    database = tmp_path / "state.sqlite"
    _downgraded(database)
    with closing(sqlite3.connect(database)) as connection:
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(_ROW, ("ha_0", "phone_practice"))
        connection.execute(_ROW, ("ha_1", "practice"))
        connection.execute(_ROW, ("ha_2", "tutor"))
        connection.commit()
        before = {row[0]: row[1] for row in connection.execute("SELECT name, sql FROM sqlite_master")}
        rows_before = connection.execute("SELECT * FROM help_assists ORDER BY id").fetchall()
    with upgrade_allowance(UPGRADE_TEST_HELPER):
        assert [migration.version for migration in apply_migrations(database)] == [250]
    with closing(sqlite3.connect(database)) as connection:
        after = {row[0]: row[1] for row in connection.execute("SELECT name, sql FROM sqlite_master")}
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        # Every object keeps its name and definition; only the table's own text changed (its surface list).
        assert set(after) == set(before)
        assert {name for name in after if after[name] != before[name]} == V3_ALTERED_TABLES
        assert V3_REBUILT_OBJECTS <= set(after)
        assert connection.execute("SELECT * FROM help_assists ORDER BY id").fetchall() == rows_before
        connection.execute(_ROW, ("ha_3", "phone_practice"))
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(_ROW, ("ha_4", "phone_queue"))
        connection.commit()
        with pytest.raises(sqlite3.IntegrityError, match="append-only"):
            connection.execute("DELETE FROM help_assists WHERE id = 'ha_3'")
        with pytest.raises(sqlite3.IntegrityError, match="fixed"):
            connection.execute("UPDATE help_assists SET surface = 'practice' WHERE id = 'ha_3'")
