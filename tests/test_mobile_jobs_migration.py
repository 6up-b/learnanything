"""Mobile M2a: migration 239, ``mobile_jobs`` (spec_mobile_tailnet_v1 §6.3, §8).

A workflow table, never evidence. The head fixture is in rollback mode with an empty
table. Earlier migrations' "nothing else changed" diffs on the way to head read
``M2A_ADDED_OBJECTS``.
"""

from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path

import pytest

from learnloop.db.migrate import UPGRADE_TEST_HELPER, apply_migrations, applied_versions, discover_migrations, upgrade_allowance
from learnloop.db.table_roles import TableRole, role_for_table

HEAD = Path(__file__).resolve().parents[1] / "fixtures" / "migration_head_240" / "state.sqlite"
#: What 239 adds (its table, its autoindexes, its indexes).
M2A_ADDED_OBJECTS = frozenset({
    "mobile_jobs", "sqlite_autoindex_mobile_jobs_1", "sqlite_autoindex_mobile_jobs_2",
    "mobile_jobs_request", "mobile_jobs_open",
})


def _names(connection: sqlite3.Connection) -> set[str]:
    return {row[0] for row in connection.execute("SELECT name FROM sqlite_master")}


def test_239_is_named_and_the_table_is_classified():
    names = {migration.version: migration.path.name for migration in discover_migrations()}
    assert names[239] == "239_mobile_jobs.sql"
    assert role_for_table("mobile_jobs") == TableRole.WORKFLOW


def test_the_head_fixture_is_at_head_in_rollback_mode_with_an_empty_table():
    assert HEAD.read_bytes()[18:20] == b"\x01\x01"
    assert max(applied_versions(HEAD)) == max(migration.version for migration in discover_migrations()) == 239
    with closing(sqlite3.connect(HEAD)) as connection:
        assert M2A_ADDED_OBJECTS <= _names(connection)
        assert connection.execute("SELECT COUNT(*) FROM mobile_jobs").fetchone()[0] == 0


@pytest.fixture
def database(tmp_path: Path) -> Path:
    from learnloop.db.copies import backup_database

    target = tmp_path / "state.sqlite"
    backup_database(HEAD, target)
    return target


def test_a_database_at_238_gets_it_and_nothing_else_changes(database: Path):
    with closing(sqlite3.connect(database)) as connection:
        connection.execute("DROP TABLE mobile_jobs")
        connection.execute("DELETE FROM schema_migrations WHERE version = 239")
        connection.commit()
        before = _names(connection)
    with upgrade_allowance(UPGRADE_TEST_HELPER):
        applied = apply_migrations(database)
    assert [migration.version for migration in applied] == [239]
    with closing(sqlite3.connect(database)) as connection:
        assert _names(connection) - before == M2A_ADDED_OBJECTS
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []


def test_one_row_per_device_and_request(database: Path):
    insert = ("INSERT INTO mobile_jobs(id,device_id,request_id,method,params_json,params_sha256,state,host_boot_id,accepted_at) "
              "VALUES (?,?,?,?,?,?,?,?,?)")
    with closing(sqlite3.connect(database)) as connection:
        connection.execute(insert, ("j1", "d1", "r1", "submit_attempt", "{}", "h", "accepted", "b", "t"))
        connection.execute(insert, ("j2", "d2", "r1", "submit_attempt", "{}", "h", "accepted", "b", "t"))
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(insert, ("j3", "d1", "r1", "submit_attempt", "{}", "h", "accepted", "b", "t"))
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(insert, ("j4", "d3", "r1", "submit_attempt", "{}", "h", "lost", "b", "t"))
