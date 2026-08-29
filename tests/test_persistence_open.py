from __future__ import annotations

import sqlite3

import pytest

import learnloop.db.repositories as repositories
from learnloop.db.connection import connect
from learnloop.db.migrate import apply_migrations
from learnloop.db.repositories import Repository


def _minimal_migrations(tmp_path):
    migrations_dir = tmp_path / "migrations"
    migrations_dir.mkdir()
    (migrations_dir / "001_initial.sql").write_text(
        "CREATE TABLE schema_migrations ("
        "version INTEGER PRIMARY KEY, name TEXT NOT NULL, applied_at TEXT NOT NULL);\n"
        "CREATE TABLE records (id TEXT PRIMARY KEY);\n",
        encoding="utf-8",
    )
    return migrations_dir


def test_read_only_connect_does_not_create_a_missing_database_or_parent(tmp_path):
    sqlite_path = tmp_path / "missing-parent" / "state.sqlite"

    with pytest.raises(sqlite3.OperationalError):
        connect(sqlite_path, read_only=True)

    assert not sqlite_path.exists()
    assert not sqlite_path.parent.exists()


def test_connection_centralizes_busy_timeout(tmp_path):
    sqlite_path = tmp_path / "state.sqlite"

    with connect(sqlite_path) as connection:
        assert connection.execute("PRAGMA busy_timeout").fetchone()[0] == 5000


def test_repository_attach_skips_migrations_and_can_be_physically_read_only(
    tmp_path,
    monkeypatch,
):
    sqlite_path = tmp_path / "state.sqlite"
    apply_migrations(sqlite_path, _minimal_migrations(tmp_path))

    def unexpected_migration(*_args, **_kwargs):
        raise AssertionError("Repository.attach() must not apply migrations")

    monkeypatch.setattr(repositories, "apply_migrations", unexpected_migration)
    repository = Repository.attach(sqlite_path, read_only=True)

    with repository.connection() as connection:
        assert connection.execute(
            "SELECT COUNT(*) AS count FROM records"
        ).fetchone()["count"] == 0
        with pytest.raises(sqlite3.OperationalError):
            connection.execute("INSERT INTO records(id) VALUES ('write')")


def test_repository_attach_can_open_a_writable_scratch_copy(tmp_path, monkeypatch):
    sqlite_path = tmp_path / "state.sqlite"
    apply_migrations(sqlite_path, _minimal_migrations(tmp_path))

    def unexpected_migration(*_args, **_kwargs):
        raise AssertionError("Repository.attach() must not apply migrations")

    monkeypatch.setattr(repositories, "apply_migrations", unexpected_migration)

    repository = Repository.attach(sqlite_path, read_only=False)
    with repository.connection() as connection:
        connection.execute("INSERT INTO records(id) VALUES ('scratch-write')")
        connection.commit()

    with connect(sqlite_path, read_only=True) as connection:
        assert connection.execute(
            "SELECT id FROM records"
        ).fetchone()["id"] == "scratch-write"
