from __future__ import annotations

from learnloop.db.connection import connect
from learnloop.db.migrate import apply_migrations, applied_versions, discover_migrations


def test_discover_finds_initial_migration():
    migrations = discover_migrations()
    versions = [migration.version for migration in migrations]
    assert versions == sorted(versions)
    assert 1 in versions


def test_fresh_db_applies_all_migrations(tmp_path):
    sqlite_path = tmp_path / "state.sqlite"
    applied = apply_migrations(sqlite_path)

    assert [migration.version for migration in applied] == [m.version for m in discover_migrations()]
    assert 1 in applied_versions(sqlite_path)

    with connect(sqlite_path) as connection:
        tables = {
            row["name"]
            for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
        }
    for required in {"practice_attempts", "learning_object_mastery", "proposed_patches", "hypothesis_sets"}:
        assert required in tables


def test_migrations_are_idempotent(tmp_path):
    sqlite_path = tmp_path / "state.sqlite"
    apply_migrations(sqlite_path)
    second = apply_migrations(sqlite_path)
    assert second == []


def test_existing_db_migrates_cleanly(tmp_path):
    sqlite_path = tmp_path / "state.sqlite"
    apply_migrations(sqlite_path)
    # Re-running against an existing, already-migrated DB is a no-op and keeps the
    # recorded version set stable.
    before = applied_versions(sqlite_path)
    apply_migrations(sqlite_path)
    assert applied_versions(sqlite_path) == before
