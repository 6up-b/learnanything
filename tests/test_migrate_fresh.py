from __future__ import annotations

from pathlib import Path

from learnloop.db.migrate import applied_versions, apply_migrations, discover_migrations


def _write_migrations(root: Path) -> Path:
    migrations = root / "migrations"
    migrations.mkdir()
    (migrations / "001_initial.sql").write_text(
        "CREATE TABLE schema_migrations (version INTEGER PRIMARY KEY, name TEXT, applied_at TEXT);\n"
        "CREATE TABLE t1 (id TEXT PRIMARY KEY);\n",
        encoding="utf-8",
    )
    (migrations / "002_second.sql").write_text(
        "CREATE TABLE t2 (id TEXT PRIMARY KEY);\n", encoding="utf-8"
    )
    return migrations


def test_fresh_database_applies_all_migrations_atomically(tmp_path):
    migrations_dir = _write_migrations(tmp_path)
    db = tmp_path / "state.sqlite"

    applied = apply_migrations(db, migrations_dir)

    assert [migration.version for migration in applied] == [1, 2]
    assert db.exists()
    # No temp artifact remains after the atomic rename.
    assert not (tmp_path / "state.sqlite.tmp").exists()
    assert applied_versions(db) == {1, 2}

    # Idempotent: nothing to apply on re-run.
    assert apply_migrations(db, migrations_dir) == []


def test_existing_database_upgrades_incrementally(tmp_path):
    migrations_dir = _write_migrations(tmp_path)
    db = tmp_path / "state.sqlite"
    apply_migrations(db, migrations_dir)

    (migrations_dir / "003_third.sql").write_text(
        "CREATE TABLE t3 (id TEXT PRIMARY KEY);\n", encoding="utf-8"
    )
    applied = apply_migrations(db, migrations_dir)

    assert [migration.version for migration in applied] == [3]
    assert applied_versions(db) == {1, 2, 3}


def test_real_migration_set_builds_fresh(tmp_path):
    db = tmp_path / "state.sqlite"
    applied = apply_migrations(db)
    assert len(applied) == len(discover_migrations())
    assert applied_versions(db) == {migration.version for migration in applied}


def test_stale_tmp_from_a_crashed_creation_is_replaced(tmp_path):
    migrations_dir = _write_migrations(tmp_path)
    db = tmp_path / "state.sqlite"
    (tmp_path / "state.sqlite.tmp").write_bytes(b"garbage from a crashed run")

    applied = apply_migrations(db, migrations_dir)

    assert [migration.version for migration in applied] == [1, 2]
    assert not (tmp_path / "state.sqlite.tmp").exists()
