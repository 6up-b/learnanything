"""The application-order migration: ``attempt_application_order``.

One new RAW_LEDGER table (PROTECTED to adaptive difficulty, by the attempt it names); nothing else changes and nothing
is backfilled (the upgrade to the tag ranks legacy attempts, not the migration). The number is the migration's file
name alone (``MIGRATION``).
"""

from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path

import pytest

from learnloop.adaptive_difficulty.protected_tables import COLUMNS as AD_COLUMNS
from learnloop.adaptive_difficulty.protected_tables import PROTECTED, ROLES
from learnloop.db.migrate import UPGRADE_TEST_HELPER, applied_versions, apply_migrations, discover_migrations, upgrade_allowance
from learnloop.db.table_roles import TABLE_ROLES, TableRole
from tests.attempt_application_order_migration_helpers import APPLICATION_ORDER, APPLICATION_ORDER_ADDED_OBJECTS
from tests.helpers import MIGRATION_HEAD_FIXTURE

HEAD = MIGRATION_HEAD_FIXTURE / "state.sqlite"
MIGRATION = next(m for m in discover_migrations() if m.name == "attempt_application_order")
COLUMNS = ["sequence", "attempt_id", "basis", "algorithm_version", "recorded_at"]


def test_the_table_is_a_raw_ledger_and_protected_by_its_attempt():
    # A RAW_LEDGER table: no rebuild clears it (replay folds by it and never writes it). To adaptive difficulty a row
    # stands or falls with the attempt it names.
    assert TABLE_ROLES[APPLICATION_ORDER] is TableRole.RAW_LEDGER
    assert ROLES[APPLICATION_ORDER] == PROTECTED
    assert AD_COLUMNS[APPLICATION_ORDER]["attempt_id"] == "attempt"


def test_the_head_fixture_holds_it_empty_in_rollback_mode():
    assert HEAD.read_bytes()[18:20] == b"\x01\x01"
    assert MIGRATION.version in applied_versions(HEAD)
    with closing(sqlite3.connect(f"file:{HEAD}?mode=ro", uri=True)) as connection:
        assert [row[1] for row in connection.execute(f"PRAGMA table_info({APPLICATION_ORDER})")] == COLUMNS
        assert connection.execute(f"SELECT COUNT(*) FROM {APPLICATION_ORDER}").fetchone()[0] == 0


def _downgraded(database: Path) -> None:
    with closing(sqlite3.connect(HEAD)) as source, closing(sqlite3.connect(database)) as target:
        source.backup(target)
    with closing(sqlite3.connect(database)) as connection:
        connection.execute(f"DROP TABLE {APPLICATION_ORDER}")
        connection.execute("DELETE FROM schema_migrations WHERE version = ?", (MIGRATION.version,))
        connection.commit()


def _rows(connection: sqlite3.Connection, table: str) -> list[tuple]:
    return sorted(tuple(row) for row in connection.execute(f"SELECT * FROM {table}"))


def test_it_adds_the_table_and_changes_nothing_else(tmp_path):
    database = tmp_path / "state.sqlite"
    _downgraded(database)
    with closing(sqlite3.connect(database)) as connection:
        before = {row[0]: row[1] for row in connection.execute("SELECT name, sql FROM sqlite_master")}
        kept = {table: _rows(connection, table) for table in ("practice_attempts", "grading_evidence")}
    with upgrade_allowance(UPGRADE_TEST_HELPER):
        assert [m.version for m in apply_migrations(database)] == [MIGRATION.version]
    with closing(sqlite3.connect(database)) as connection:
        after = {row[0]: row[1] for row in connection.execute("SELECT name, sql FROM sqlite_master")}
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        assert {table: _rows(connection, table) for table in kept} == kept
        assert connection.execute(f"SELECT COUNT(*) FROM {APPLICATION_ORDER}").fetchone()[0] == 0
    assert set(after) - set(before) == APPLICATION_ORDER_ADDED_OBJECTS
    assert {name for name in before if before[name] != after[name]} == set()


def _upgraded(tmp_path) -> Path:
    database = tmp_path / "state.sqlite"
    with closing(sqlite3.connect(HEAD)) as source, closing(sqlite3.connect(database)) as target:
        source.backup(target)
    return database


def test_the_foreign_key_is_checked_at_commit_so_a_reservation_may_precede_its_attempt(tmp_path):
    database = _upgraded(tmp_path)
    with closing(sqlite3.connect(database, isolation_level=None)) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        attempt_id = connection.execute("SELECT id FROM practice_attempts LIMIT 1").fetchone()[0]
        connection.execute("BEGIN")
        connection.execute(
            f"INSERT INTO {APPLICATION_ORDER}(attempt_id, basis, algorithm_version, recorded_at) "
            "VALUES ('not-yet-written', 'applied', 'mvp-0.65', '2026-11-22T00:00:00Z')"
        )
        # Inside the transaction the dangling reference stands; the commit refuses it.
        with pytest.raises(sqlite3.IntegrityError, match="FOREIGN KEY"):
            connection.execute("COMMIT")
        connection.execute("ROLLBACK")
        connection.execute("BEGIN")
        connection.execute(
            f"INSERT INTO {APPLICATION_ORDER}(attempt_id, basis, algorithm_version, recorded_at) "
            "VALUES (?, 'applied', 'mvp-0.65', '2026-11-22T00:00:00Z')", (attempt_id,)
        )
        connection.execute("COMMIT")
        with pytest.raises(sqlite3.IntegrityError, match="UNIQUE"):
            connection.execute(
                f"INSERT INTO {APPLICATION_ORDER}(attempt_id, basis, algorithm_version, recorded_at) "
                "VALUES (?, 'applied', 'mvp-0.65', '2026-11-22T00:00:01Z')", (attempt_id,)
            )
        with pytest.raises(sqlite3.IntegrityError, match="CHECK"):
            connection.execute(
                f"INSERT INTO {APPLICATION_ORDER}(attempt_id, basis, algorithm_version, recorded_at) "
                "SELECT id, 'guessed', 'mvp-0.65', '2026-11-22T00:00:01Z' FROM practice_attempts "
                "WHERE id != ? LIMIT 1", (attempt_id,)
            )
