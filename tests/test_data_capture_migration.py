"""Data capture: migration 240, five append-only RECEIPT tables (docs/reviews/data-capture-a1-a6.md).

Additive: no existing object changes, no row is written, nothing replay reads. The head fixture is at 240
in rollback mode with empty tables. Earlier migrations' "nothing else changed" diffs on the way to head
read ``DATA_CAPTURE_ADDED_OBJECTS``.
"""

from __future__ import annotations

from contextlib import closing
from pathlib import Path
import sqlite3

import pytest

from tests.followup_migration_helpers import FOLLOWUP_ADDED_OBJECTS
from tests.hypothesis_marks_migration_helpers import MARKS_ADDED_OBJECTS
from tests.router_objective_migration_helpers import RO0_ADDED_OBJECTS
from tests.ro2_history_migration_helpers import RO2_ADDED_OBJECTS
from tests.ro4_traces_migration_helpers import RO4_ADDED_OBJECTS
from tests.teacher_te2log_migration_helpers import TE2LOG_ADDED_OBJECTS
from tests.ih3_migration_helpers import IH3_ADDED_OBJECTS
from tests.decision_records_migration_helpers import B1_ADDED_OBJECTS
from learnloop.db.migrate import UPGRADE_TEST_HELPER, applied_versions, apply_migrations, discover_migrations, upgrade_allowance
from learnloop.db.table_roles import TABLE_ROLES, TableRole
from tests.helpers import MIGRATION_HEAD_FIXTURE
from tests.data_capture_migration_helpers import DATA_CAPTURE_ADDED_OBJECTS, TABLES

HEAD = MIGRATION_HEAD_FIXTURE / "state.sqlite"


def _names(connection: sqlite3.Connection) -> set[str]:
    return {row[0] for row in connection.execute("SELECT name FROM sqlite_master")}


def test_240_is_the_head_and_its_tables_are_receipts():
    names = {migration.version: migration.path.name for migration in discover_migrations()}
    assert names[240] == "240_data_capture.sql"
    for table in TABLES:
        assert TABLE_ROLES[table] is TableRole.RECEIPT


def test_the_head_fixture_is_at_240_in_rollback_mode_with_empty_tables():
    assert HEAD.read_bytes()[18:20] == b"\x01\x01"
    assert max(applied_versions(HEAD)) >= 240
    with closing(sqlite3.connect(HEAD)) as connection:
        assert DATA_CAPTURE_ADDED_OBJECTS <= _names(connection)
        for table in TABLES:
            assert connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] == 0


def _downgraded(database: Path) -> None:
    with closing(sqlite3.connect(HEAD)) as source, closing(sqlite3.connect(database)) as target:
        source.backup(target)
    with closing(sqlite3.connect(database)) as connection:
        for table in reversed(TABLES):
            connection.execute(f"DROP TABLE {table}")
        connection.execute("DELETE FROM schema_migrations WHERE version = 240")
        connection.commit()


def test_240_adds_exactly_its_objects_and_changes_nothing_else(tmp_path):
    database = tmp_path / "state.sqlite"
    _downgraded(database)
    with closing(sqlite3.connect(database)) as connection:
        before = {row[0]: row[1] for row in connection.execute("SELECT name, sql FROM sqlite_master")}
    with upgrade_allowance(UPGRADE_TEST_HELPER):
        applied = apply_migrations(database)
    assert [migration.version for migration in applied] == [240]
    with closing(sqlite3.connect(database)) as connection:
        after = {row[0]: row[1] for row in connection.execute("SELECT name, sql FROM sqlite_master")}
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
    assert set(after) - set(before) - FOLLOWUP_ADDED_OBJECTS - MARKS_ADDED_OBJECTS - RO0_ADDED_OBJECTS - RO2_ADDED_OBJECTS - RO4_ADDED_OBJECTS - TE2LOG_ADDED_OBJECTS - IH3_ADDED_OBJECTS - B1_ADDED_OBJECTS == set(DATA_CAPTURE_ADDED_OBJECTS)
    assert all(after[name] == sql for name, sql in before.items())


@pytest.mark.durability
def test_240_on_the_durability_lane(tmp_path):
    database = tmp_path / "state.sqlite"
    _downgraded(database)
    with upgrade_allowance(UPGRADE_TEST_HELPER):
        assert [migration.version for migration in apply_migrations(database)] == [240]
    with closing(sqlite3.connect(database)) as connection:
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"


@pytest.mark.parametrize("table, values, statement", [
    ("prefilter_payloads", ("h", "gates", b"{}", 2, 2, "t"), "UPDATE prefilter_payloads SET raw_bytes = 3"),
    ("prefilter_payloads", ("h", "gates", b"{}", 2, 2, "t"), "DELETE FROM prefilter_payloads"),
])
def test_the_receipts_are_append_only(tmp_path, table, values, statement):
    database = tmp_path / "state.sqlite"
    with closing(sqlite3.connect(HEAD)) as source, closing(sqlite3.connect(database)) as target:
        source.backup(target)
    with closing(sqlite3.connect(database)) as connection:
        connection.execute(f"INSERT INTO {table} VALUES ({','.join('?' for _ in values)})", values)
        with pytest.raises(sqlite3.IntegrityError, match="append-only"):
            connection.execute(statement)
