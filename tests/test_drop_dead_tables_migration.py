"""The dead-table drop (refactor step J2): five tables no code reads or writes go, and a database in which any of
them holds a row is refused unchanged instead of being emptied.

The number is the migration's file name alone (``MIGRATION``).
"""

from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path

import pytest

from learnloop.adaptive_difficulty.protected_tables import ROLES
from learnloop.db import migrate
from learnloop.db.migrate import UPGRADE_TEST_HELPER, applied_versions, apply_migrations, discover_migrations, upgrade_allowance
from learnloop.db.table_roles import TABLE_ROLES
from tests.drop_dead_tables_migration_helpers import J2_DROPPED_OBJECTS, J2_DROPPED_TABLES
from tests.helpers import MIGRATION_HEAD_FIXTURE

HEAD = MIGRATION_HEAD_FIXTURE / "state.sqlite"
MIGRATION = next(m for m in discover_migrations() if m.name == "drop_dead_tables")


def test_no_list_names_a_dropped_table():
    assert J2_DROPPED_TABLES.isdisjoint(TABLE_ROLES)
    assert J2_DROPPED_TABLES.isdisjoint(ROLES)


def test_the_head_fixture_holds_it_in_rollback_mode_without_the_tables():
    assert HEAD.read_bytes()[18:20] == b"\x01\x01"
    assert MIGRATION.version in applied_versions(HEAD)
    with closing(sqlite3.connect(f"file:{HEAD}?mode=ro", uri=True)) as connection:
        names = {row[0] for row in connection.execute("SELECT name FROM sqlite_master")}
    assert names.isdisjoint(J2_DROPPED_OBJECTS)


def _migrations_through(tmp_path: Path, version: int) -> Path:
    through = tmp_path / f"through_{version}"
    through.mkdir()
    for migration in discover_migrations():
        if migration.version <= version:
            (through / migration.path.name).write_text(migration.path.read_text(encoding="utf-8"), encoding="utf-8")
    return through


def _database_before(tmp_path: Path, version: int) -> Path:
    database = tmp_path / "state.sqlite"
    apply_migrations(database, migrations_dir=_migrations_through(tmp_path, version))
    assert max(applied_versions(database)) == version
    return database


def _schema(database: Path) -> dict[str, str]:
    with closing(sqlite3.connect(database)) as connection:
        return {name: sql or "" for name, sql in connection.execute("SELECT name, sql FROM sqlite_master")}


def _insert_one_row(database: Path, table: str) -> None:
    # Every NOT NULL column without a default gets a value its type and CHECKs accept; no foreign key is enforced on a
    # bare connection, and the one in the family (angle_inventories.family_version_id) is nullable anyway.
    with closing(sqlite3.connect(database)) as connection:
        columns = [
            (row[1], "0" if row[2].upper() in {"INTEGER", "REAL"} else "'x'")
            for row in connection.execute(f"PRAGMA table_info({table})")
            if row[3] and row[4] is None
        ]
        connection.execute(
            f"INSERT INTO {table}({', '.join(name for name, _ in columns)}) "
            f"VALUES ({', '.join(value for _, value in columns)})"
        )
        connection.commit()


def test_an_empty_family_is_dropped_and_nothing_else_changes(tmp_path):
    database = _database_before(tmp_path, MIGRATION.version - 1)
    before = _schema(database)
    assert J2_DROPPED_OBJECTS <= set(before)
    # Through this migration only: a later migration's objects are its own test's.
    with upgrade_allowance(UPGRADE_TEST_HELPER):
        applied = apply_migrations(database, migrations_dir=_migrations_through(tmp_path, MIGRATION.version))
        assert [m.version for m in applied] == [MIGRATION.version]
    after = _schema(database)
    assert set(before) - set(after) == J2_DROPPED_OBJECTS
    assert set(after) - set(before) == set()
    assert {name for name in after if before[name] != after[name]} == set()
    with closing(sqlite3.connect(database)) as connection:
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []


@pytest.mark.parametrize("table", sorted(J2_DROPPED_TABLES))
def test_a_row_in_any_family_table_refuses_the_upgrade_and_leaves_the_file_byte_identical(tmp_path, table):
    database = _database_before(tmp_path, MIGRATION.version - 1)
    _insert_one_row(database, table)
    original = database.read_bytes()
    with upgrade_allowance(UPGRADE_TEST_HELPER), pytest.raises(migrate.NonEmptyDropError) as refused:
        apply_migrations(database)
    assert refused.value.version == MIGRATION.version
    assert refused.value.row_counts == {table: 1}
    assert f"{table} (1 row)" in str(refused.value)
    assert "Nothing was changed and no row was deleted" in str(refused.value)
    assert database.read_bytes() == original
    assert [path.name for path in tmp_path.iterdir() if path.name.startswith("state.sqlite")] == ["state.sqlite"]


def test_an_older_database_with_a_row_is_refused_before_any_earlier_migration_applies(tmp_path):
    # The check reads every pending migration before the first one writes: refusing at the drop itself would leave the
    # migrations below it committed and the database at neither its old nor its new head.
    database = _database_before(tmp_path, MIGRATION.version - 2)
    _insert_one_row(database, "learner_theta")
    _insert_one_row(database, "controller_prequential_reports")
    original = database.read_bytes()
    with upgrade_allowance(UPGRADE_TEST_HELPER), pytest.raises(migrate.NonEmptyDropError) as refused:
        apply_migrations(database)
    assert refused.value.row_counts == {"controller_prequential_reports": 1, "learner_theta": 1}
    assert database.read_bytes() == original
    assert max(applied_versions(database)) == MIGRATION.version - 2
