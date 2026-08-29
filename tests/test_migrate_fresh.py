from __future__ import annotations

import sqlite3
import shutil
from pathlib import Path

import pytest

from learnloop.db.connection import connect
from learnloop.db.migrate import (
    Migration,
    _apply_incremental_migration,
    applied_versions,
    apply_migrations,
    discover_migrations,
)


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


def test_incremental_migration_and_ledger_receipt_roll_back_together(tmp_path):
    migrations_dir = _write_migrations(tmp_path)
    db = tmp_path / "state.sqlite"
    apply_migrations(db, migrations_dir)
    migration_path = migrations_dir / "003_atomic.sql"
    migration_path.write_text(
        "CREATE TABLE partially_applied (id TEXT PRIMARY KEY);\n"
        "INSERT INTO table_that_does_not_exist(id) VALUES ('boom');\n",
        encoding="utf-8",
    )

    with pytest.raises(sqlite3.OperationalError):
        apply_migrations(db, migrations_dir)

    with connect(db) as connection:
        assert connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'partially_applied'"
        ).fetchone() is None
    assert applied_versions(db) == {1, 2}

    migration_path.write_text(
        "CREATE TABLE partially_applied (id TEXT PRIMARY KEY);\n",
        encoding="utf-8",
    )
    assert [migration.version for migration in apply_migrations(db, migrations_dir)] == [3]
    assert applied_versions(db) == {1, 2, 3}


def test_fk_toggle_migration_is_atomic_and_restores_enforcement(tmp_path):
    migrations_dir = _write_migrations(tmp_path)
    db = tmp_path / "state.sqlite"
    apply_migrations(db, migrations_dir)
    migration_path = migrations_dir / "003_fk_rebuild.sql"
    migration_path.write_text(
        "PRAGMA foreign_keys = OFF;\n"
        "CREATE TABLE parents (id TEXT PRIMARY KEY);\n"
        "CREATE TABLE children (parent_id TEXT REFERENCES parents(id));\n"
        "INSERT INTO children(parent_id) VALUES ('missing-parent');\n"
        "PRAGMA foreign_keys = ON;\n",
        encoding="utf-8",
    )
    migration = Migration(version=3, name="fk_rebuild", path=migration_path)

    with connect(db) as connection:
        assert connection.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        with pytest.raises(RuntimeError, match="failed foreign_key_check"):
            _apply_incremental_migration(connection, migration, clock=None)
        assert connection.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        assert connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'children'"
        ).fetchone() is None
        assert connection.execute(
            "SELECT 1 FROM schema_migrations WHERE version = 3"
        ).fetchone() is None


def test_real_fk_rebuild_153_rolls_back_on_interruption(tmp_path, monkeypatch):
    """Exercise the transactional FK-toggle path on the actual table rebuild."""

    import learnloop.db.migrate as migrate_module

    repository_root = Path(__file__).resolve().parents[1]
    db = tmp_path / "state.sqlite"
    shutil.copy2(repository_root / "fixtures" / "arxiv" / "state.sqlite", db)
    with connect(db) as connection:
        before_count = connection.execute(
            "SELECT COUNT(*) FROM practice_attempts"
        ).fetchone()[0]
        before_schema = connection.execute(
            "SELECT sql FROM sqlite_master "
            "WHERE type = 'table' AND name = 'practice_attempts'"
        ).fetchone()[0]

    original_iterator = migrate_module._iter_sql_statements

    def interrupt_after_attempt_swap(sql: str):
        for statement in original_iterator(sql):
            yield statement
            if "ALTER TABLE practice_attempts_new RENAME TO practice_attempts" in statement:
                raise RuntimeError("injected migration interruption")

    monkeypatch.setattr(migrate_module, "_iter_sql_statements", interrupt_after_attempt_swap)
    with pytest.raises(RuntimeError, match="injected migration interruption"):
        apply_migrations(db)

    with connect(db) as connection:
        assert connection.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        assert connection.execute(
            "SELECT COUNT(*) FROM practice_attempts"
        ).fetchone()[0] == before_count
        assert connection.execute(
            "SELECT sql FROM sqlite_master "
            "WHERE type = 'table' AND name = 'practice_attempts'"
        ).fetchone()[0] == before_schema
        assert connection.execute(
            "SELECT 1 FROM sqlite_master "
            "WHERE type = 'table' AND name = 'practice_attempts_new'"
        ).fetchone() is None
        assert connection.execute(
            "SELECT 1 FROM schema_migrations WHERE version = 153"
        ).fetchone() is None

    monkeypatch.setattr(migrate_module, "_iter_sql_statements", original_iterator)
    apply_migrations(db)
    assert max(applied_versions(db)) == 156
    with connect(db) as connection:
        assert connection.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []


def test_incremental_statement_parser_preserves_trigger_bodies(tmp_path):
    migrations_dir = _write_migrations(tmp_path)
    db = tmp_path / "state.sqlite"
    apply_migrations(db, migrations_dir)
    (migrations_dir / "003_trigger.sql").write_text(
        "CREATE TABLE trigger_log (value TEXT NOT NULL);\n"
        "CREATE TRIGGER log_t1 AFTER INSERT ON t1 BEGIN\n"
        "  INSERT INTO trigger_log(value) VALUES (NEW.id);\n"
        "  INSERT INTO trigger_log(value) VALUES (NEW.id || '-again');\n"
        "END;\n",
        encoding="utf-8",
    )

    apply_migrations(db, migrations_dir)

    with connect(db) as connection:
        connection.execute("INSERT INTO t1(id) VALUES ('row')")
        values = [
            row["value"]
            for row in connection.execute("SELECT value FROM trigger_log ORDER BY rowid")
        ]
    assert values == ["row", "row-again"]
