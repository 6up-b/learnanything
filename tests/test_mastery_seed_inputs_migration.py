"""The mastery-seed migration: ``mastery_seed_inputs``.

One new RAW_LEDGER table (DENIED to adaptive difficulty: the incumbent's mastery input); nothing else changes and
nothing is backfilled (the upgrade to the tag reconstructs the legacy rows, not the migration). The number is the
migration's file name alone (``MIGRATION``).
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
from tests.helpers import MIGRATION_HEAD_FIXTURE
from tests.mastery_seed_inputs_migration_helpers import MASTERY_SEED, MASTERY_SEED_ADDED_OBJECTS

HEAD = MIGRATION_HEAD_FIXTURE / "state.sqlite"
MIGRATION = next(m for m in discover_migrations() if m.name == "mastery_seed_inputs")
COLUMNS = [
    "learning_object_id", "claims_made_json", "selected_claim_id", "materialized_at", "basis", "policy_version",
    "recorded_at",
]


def test_the_table_is_a_raw_ledger_denied_to_adaptive_difficulty():
    # A RAW_LEDGER table: no rebuild clears it (replay seeds from it). Adaptive difficulty never reads it: it is the
    # incumbent's mastery input, and AD's own claim policy reads the claims itself.
    assert TABLE_ROLES[MASTERY_SEED] is TableRole.RAW_LEDGER
    assert ROLES[MASTERY_SEED] == DENIED
    assert set(AD_COLUMN_CLASSES[MASTERY_SEED]) == set(COLUMNS)


def test_the_head_fixture_holds_it_empty_in_rollback_mode():
    assert HEAD.read_bytes()[18:20] == b"\x01\x01"
    assert MIGRATION.version in applied_versions(HEAD)
    with closing(sqlite3.connect(f"file:{HEAD}?mode=ro", uri=True)) as connection:
        assert [row[1] for row in connection.execute(f"PRAGMA table_info({MASTERY_SEED})")] == COLUMNS
        assert connection.execute(f"SELECT COUNT(*) FROM {MASTERY_SEED}").fetchone()[0] == 0


def _downgraded(database: Path) -> None:
    with closing(sqlite3.connect(HEAD)) as source, closing(sqlite3.connect(database)) as target:
        source.backup(target)
    with closing(sqlite3.connect(database)) as connection:
        connection.execute(f"DROP TABLE {MASTERY_SEED}")
        connection.execute("DELETE FROM schema_migrations WHERE version = ?", (MIGRATION.version,))
        connection.commit()


def _rows(connection: sqlite3.Connection, table: str) -> list[tuple]:
    return sorted(tuple(row) for row in connection.execute(f"SELECT * FROM {table}"))


def test_it_adds_the_table_and_changes_nothing_else(tmp_path):
    database = tmp_path / "state.sqlite"
    _downgraded(database)
    with closing(sqlite3.connect(database)) as connection:
        before = {row[0]: row[1] for row in connection.execute("SELECT name, sql FROM sqlite_master")}
        kept = {table: _rows(connection, table) for table in ("learning_object_mastery", "learner_claims")}
    with upgrade_allowance(UPGRADE_TEST_HELPER):
        assert [m.version for m in apply_migrations(database)] == [MIGRATION.version]
    with closing(sqlite3.connect(database)) as connection:
        after = {row[0]: row[1] for row in connection.execute("SELECT name, sql FROM sqlite_master")}
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        assert {table: _rows(connection, table) for table in kept} == kept
        assert connection.execute(f"SELECT COUNT(*) FROM {MASTERY_SEED}").fetchone()[0] == 0
    assert set(after) - set(before) == MASTERY_SEED_ADDED_OBJECTS
    assert {name for name in before if before[name] != after[name]} == set()


def test_one_row_per_learning_object_with_a_known_basis(tmp_path):
    database = tmp_path / "state.sqlite"
    with closing(sqlite3.connect(HEAD)) as source, closing(sqlite3.connect(database)) as target:
        source.backup(target)
    insert = (
        f"INSERT INTO {MASTERY_SEED}(learning_object_id, claims_made_json, selected_claim_id, materialized_at, basis, "
        "policy_version, recorded_at) VALUES (?, '[]', NULL, ?, ?, 'covering_claims_seed_v1', '2026-11-22T00:00:00Z')"
    )
    with closing(sqlite3.connect(database, isolation_level=None)) as connection:
        connection.execute(insert, ("lo_a", "2026-11-22T00:00:00Z", "captured_at_materialization"))
        with pytest.raises(sqlite3.IntegrityError, match="UNIQUE"):
            connection.execute(insert, ("lo_a", None, "legacy_reconstructed"))
        with pytest.raises(sqlite3.IntegrityError, match="CHECK"):
            connection.execute(insert, ("lo_b", None, "guessed"))
        # A legacy reconstruction does not know when the row was first persisted.
        connection.execute(insert, ("lo_b", None, "legacy_reconstructed"))
        with pytest.raises(sqlite3.IntegrityError, match="NOT NULL"):
            connection.execute(
                f"INSERT INTO {MASTERY_SEED}(learning_object_id, claims_made_json, basis, policy_version, recorded_at) "
                "VALUES ('lo_c', NULL, 'legacy_reconstructed', 'covering_claims_seed_v1', '2026-11-22T00:00:00Z')"
            )
