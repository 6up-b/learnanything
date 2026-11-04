"""Migration 242: FG1c's additive tables, the head fixture holding them, and their roles.

Additive: no existing object changes, no row is written, nothing replay reads. Earlier migrations'
additivity tests downgrade the head, so they read ``MARKS_ADDED_OBJECTS``.
"""

from __future__ import annotations

from contextlib import closing
from pathlib import Path
import sqlite3

import pytest

from learnloop.db.migrate import UPGRADE_TEST_HELPER, applied_versions, apply_migrations, discover_migrations, upgrade_allowance
from learnloop.db.table_roles import TABLE_ROLES, TableRole

HEAD = Path(__file__).resolve().parents[1] / "fixtures" / "migration_head_242" / "state.sqlite"
ROLES = {
    "hypothesis_list_exposures": TableRole.RECEIPT,
    "hypothesis_exposure_probe_links": TableRole.RECEIPT,
    "hypothesis_marks": TableRole.RAW_LEDGER,
}
MARKS_ADDED_OBJECTS = frozenset({
    *ROLES,
    "hypothesis_list_exposures_attempt", "hypothesis_list_exposures_no_update", "hypothesis_list_exposures_no_delete",
    "hypothesis_exposure_probe_links_attempt", "hypothesis_exposure_probe_links_no_update",
    "hypothesis_exposure_probe_links_no_delete",
    "hypothesis_marks_attempt", "hypothesis_marks_learning_object", "hypothesis_marks_no_update", "hypothesis_marks_no_delete",
    # Autoindexes of the primary keys and the link's UNIQUE.
    "sqlite_autoindex_hypothesis_list_exposures_1", "sqlite_autoindex_hypothesis_exposure_probe_links_1",
    "sqlite_autoindex_hypothesis_exposure_probe_links_2", "sqlite_autoindex_hypothesis_marks_1",
})


def _downgraded(database: Path) -> None:
    with closing(sqlite3.connect(HEAD)) as source, closing(sqlite3.connect(database)) as target:
        source.backup(target)
    with closing(sqlite3.connect(database)) as connection:
        for table in ("hypothesis_exposure_probe_links", "hypothesis_list_exposures", "hypothesis_marks"):
            connection.execute(f"DROP TABLE {table}")
        connection.execute("DELETE FROM schema_migrations WHERE version = 242")
        connection.commit()


def test_242_is_the_head_and_its_tables_have_their_roles():
    names = {migration.version: migration.path.name for migration in discover_migrations()}
    assert names[242] == "242_hypothesis_marks.sql" and max(names) == 242
    for table, role in ROLES.items():
        assert TABLE_ROLES[table] is role


def test_the_head_fixture_is_at_242_in_rollback_mode_with_empty_tables():
    assert HEAD.read_bytes()[18:20] == b"\x01\x01"
    assert max(applied_versions(HEAD)) == 242
    with closing(sqlite3.connect(HEAD)) as connection:
        names = {row[0] for row in connection.execute("SELECT name FROM sqlite_master")}
        assert MARKS_ADDED_OBJECTS <= names
        for table in ROLES:
            assert connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] == 0


def test_242_adds_exactly_its_objects_and_changes_nothing_else(tmp_path):
    database = tmp_path / "state.sqlite"
    _downgraded(database)
    with closing(sqlite3.connect(database)) as connection:
        before = {row[0]: row[1] for row in connection.execute("SELECT name, sql FROM sqlite_master")}
    with upgrade_allowance(UPGRADE_TEST_HELPER):
        assert [migration.version for migration in apply_migrations(database)] == [242]
    with closing(sqlite3.connect(database)) as connection:
        after = {row[0]: row[1] for row in connection.execute("SELECT name, sql FROM sqlite_master")}
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
    assert set(after) - set(before) == set(MARKS_ADDED_OBJECTS)
    assert all(after[name] == sql for name, sql in before.items())


@pytest.mark.durability
def test_242_on_the_durability_lane(tmp_path):
    database = tmp_path / "state.sqlite"
    _downgraded(database)
    with upgrade_allowance(UPGRADE_TEST_HELPER):
        assert [migration.version for migration in apply_migrations(database)] == [242]
    with closing(sqlite3.connect(database)) as connection:
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"


@pytest.mark.parametrize("insert, statement", [
    ("INSERT INTO hypothesis_list_exposures (id, attempt_id, surface, hypothesis_version_ids_json, probe_answered, "
     "shown_at, created_at) VALUES ('e', 'a', 'why', '[]', 0, 't', 't')", "UPDATE hypothesis_list_exposures SET probe_answered = 1"),
    ("INSERT INTO hypothesis_list_exposures (id, attempt_id, surface, hypothesis_version_ids_json, probe_answered, "
     "shown_at, created_at) VALUES ('e', 'a', 'why', '[]', 0, 't', 't')", "DELETE FROM hypothesis_list_exposures"),
    ("INSERT INTO hypothesis_marks (id, attempt_id, learning_object_id, mark, display_order_json, surface, probe_answered, "
     "created_at) VALUES ('m', 'a', 'lo', 'none_of_these', '[]', 's', 0, 't')", "UPDATE hypothesis_marks SET mark = 'cleared'"),
    ("INSERT INTO hypothesis_marks (id, attempt_id, learning_object_id, mark, display_order_json, surface, probe_answered, "
     "created_at) VALUES ('m', 'a', 'lo', 'none_of_these', '[]', 's', 0, 't')", "DELETE FROM hypothesis_marks"),
])
def test_the_records_are_append_only(tmp_path, insert, statement):
    database = tmp_path / "state.sqlite"
    with closing(sqlite3.connect(HEAD)) as source, closing(sqlite3.connect(database)) as target:
        source.backup(target)
    with closing(sqlite3.connect(database)) as connection:
        connection.execute(insert)
        with pytest.raises(sqlite3.IntegrityError, match="append-only"):
            connection.execute(statement)


@pytest.mark.parametrize("values", [
    # A cause mark needs a cause; None of these names none; only None of these takes words.
    "('m', 'a', 'lo', NULL, 'my_gap', NULL)",
    "('m', 'a', 'lo', 'h', 'none_of_these', NULL)",
    "('m', 'a', 'lo', 'h', 'partly', 'because')",
    "('m', 'a', 'lo', 'h', 'certainly', NULL)",
])
def test_the_ledger_refuses_a_mark_that_makes_no_sense(tmp_path, values):
    database = tmp_path / "state.sqlite"
    with closing(sqlite3.connect(HEAD)) as source, closing(sqlite3.connect(database)) as target:
        source.backup(target)
    with closing(sqlite3.connect(database)) as connection, pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            "INSERT INTO hypothesis_marks (id, attempt_id, learning_object_id, hypothesis_version_id, mark, free_text, "
            f"display_order_json, surface, probe_answered, created_at) SELECT *, '[]', 's', 0, 't' FROM (VALUES {values})"
        )
