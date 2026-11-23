"""The lifecycle-inputs migration: ``attempt_lifecycle_inputs``.

One new RAW_LEDGER table (DENIED to adaptive difficulty: the incumbent's grade-application input); nothing else
changes and nothing is backfilled (the upgrade to the tag reconstructs the legacy rows, not the migration). The number
is the migration's file name alone (``MIGRATION``).
"""

from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path

import pytest

from learnloop.adaptive_difficulty.column_classes import CLASSES as AD_COLUMN_CLASSES
from learnloop.adaptive_difficulty.protected_tables import DENIED, ROLES
from learnloop.db.migrate import UPGRADE_TEST_HELPER, applied_versions, apply_migrations, discover_migrations, upgrade_allowance
from learnloop.db.table_roles import TABLE_ROLES, TableRole
from tests.attempt_lifecycle_inputs_migration_helpers import LIFECYCLE_INPUTS, LIFECYCLE_INPUTS_ADDED_OBJECTS
from tests.helpers import MIGRATION_HEAD_FIXTURE

HEAD = MIGRATION_HEAD_FIXTURE / "state.sqlite"
MIGRATION = next(m for m in discover_migrations() if m.name == "attempt_lifecycle_inputs")
COLUMNS = ["attempt_id", "learning_object_id", "required_facets_json", "basis", "policy_version", "recorded_at"]


def test_the_table_is_a_raw_ledger_denied_to_adaptive_difficulty():
    # A RAW_LEDGER table: no rebuild clears it (replay reads it and never writes it). Adaptive difficulty never reads
    # it: it is read from every item's lifecycle, the protected items' included.
    assert TABLE_ROLES[LIFECYCLE_INPUTS] is TableRole.RAW_LEDGER
    assert ROLES[LIFECYCLE_INPUTS] == DENIED
    assert set(AD_COLUMN_CLASSES[LIFECYCLE_INPUTS]) == set(COLUMNS)


def test_the_head_fixture_holds_it_empty_in_rollback_mode():
    assert HEAD.read_bytes()[18:20] == b"\x01\x01"
    assert MIGRATION.version in applied_versions(HEAD)
    with closing(sqlite3.connect(f"file:{HEAD}?mode=ro", uri=True)) as connection:
        assert [row[1] for row in connection.execute(f"PRAGMA table_info({LIFECYCLE_INPUTS})")] == COLUMNS
        assert connection.execute(f"SELECT COUNT(*) FROM {LIFECYCLE_INPUTS}").fetchone()[0] == 0


def _downgraded(database: Path) -> None:
    with closing(sqlite3.connect(HEAD)) as source, closing(sqlite3.connect(database)) as target:
        source.backup(target)
    with closing(sqlite3.connect(database)) as connection:
        connection.execute(f"DROP TABLE {LIFECYCLE_INPUTS}")
        connection.execute("DELETE FROM schema_migrations WHERE version = ?", (MIGRATION.version,))
        connection.commit()


def _rows(connection: sqlite3.Connection, table: str) -> list[tuple]:
    return sorted(tuple(row) for row in connection.execute(f"SELECT * FROM {table}"))


def test_it_adds_the_table_and_changes_nothing_else(tmp_path):
    database = tmp_path / "state.sqlite"
    _downgraded(database)
    with closing(sqlite3.connect(database)) as connection:
        before = {row[0]: row[1] for row in connection.execute("SELECT name, sql FROM sqlite_master")}
        kept = {table: _rows(connection, table) for table in ("practice_attempts", "practice_item_state")}
    with upgrade_allowance(UPGRADE_TEST_HELPER):
        assert [m.version for m in apply_migrations(database)] == [MIGRATION.version]
    with closing(sqlite3.connect(database)) as connection:
        after = {row[0]: row[1] for row in connection.execute("SELECT name, sql FROM sqlite_master")}
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        assert {table: _rows(connection, table) for table in kept} == kept
        assert connection.execute(f"SELECT COUNT(*) FROM {LIFECYCLE_INPUTS}").fetchone()[0] == 0
    assert set(after) - set(before) == LIFECYCLE_INPUTS_ADDED_OBJECTS
    assert {name for name in before if before[name] != after[name]} == set()


def test_one_row_per_existing_attempt_with_a_known_basis(tmp_path):
    database = tmp_path / "state.sqlite"
    with closing(sqlite3.connect(HEAD)) as source, closing(sqlite3.connect(database)) as target:
        source.backup(target)
    insert = (
        f"INSERT INTO {LIFECYCLE_INPUTS}(attempt_id, learning_object_id, required_facets_json, basis, policy_version, "
        "recorded_at) VALUES (?, 'lo', '[]', ?, 'active_item_evidence_facets_v1', '2026-11-22T00:00:00Z')"
    )
    with closing(sqlite3.connect(database, isolation_level=None)) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        first, second = (row[0] for row in connection.execute("SELECT id FROM practice_attempts ORDER BY id LIMIT 2"))
        with pytest.raises(sqlite3.IntegrityError, match="FOREIGN KEY"):
            connection.execute(insert, ("not-an-attempt", "captured_at_application"))
        connection.execute(insert, (first, "captured_at_application"))
        with pytest.raises(sqlite3.IntegrityError, match="UNIQUE"):
            connection.execute(insert, (first, "legacy_reconstructed"))
        with pytest.raises(sqlite3.IntegrityError, match="CHECK"):
            connection.execute(insert, (second, "guessed"))
        connection.execute(insert, (second, "legacy_reconstructed"))
