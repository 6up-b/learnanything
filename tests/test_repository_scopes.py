from __future__ import annotations

import sqlite3

import pytest
pytestmark = pytest.mark.durability

from learnloop.db.connection import connect
from learnloop.db.repositories import Repository


def test_atomic_scope_rolls_back_nested_commits_and_serializes_writers(tmp_path):
    path = tmp_path / "state.sqlite"
    raw = connect(path)
    raw.execute("CREATE TABLE scope_test (value INTEGER)")
    raw.execute("INSERT INTO scope_test VALUES (1)")
    raw.commit()
    raw.close()
    repository = Repository.attach(path)
    observer = connect(path)
    observer.execute("PRAGMA busy_timeout=0")
    try:
        with pytest.raises(ValueError, match="interrupted"):
            with repository.atomic():
                with repository.connection() as connection:
                    connection.execute("DELETE FROM scope_test")
                    connection.commit()
                connection = repository.connection()
                connection.isolation_level = None
                connection.execute("BEGIN IMMEDIATE")
                connection.execute("INSERT INTO scope_test VALUES (2)")
                connection.execute("COMMIT")
                cursor = connection.cursor()
                cursor.execute("BEGIN IMMEDIATE")
                cursor.execute("INSERT INTO scope_test VALUES (99)")
                cursor.execute("COMMIT")
                cursor.close()
                connection.close()
                assert observer.execute("SELECT value FROM scope_test").fetchone()[0] == 1
                with pytest.raises(sqlite3.OperationalError, match="locked"):
                    observer.execute("INSERT INTO scope_test VALUES (3)")
                observer.rollback()
                raise ValueError("interrupted")
        assert [r[0] for r in observer.execute("SELECT value FROM scope_test")] == [1]
        with repository.pinned(), repository.atomic():
            with repository.connection() as connection:
                connection.execute("INSERT INTO scope_test VALUES (4)")
            with pytest.raises(ValueError):
                with repository.atomic():
                    with repository.connection() as connection:
                        connection.execute("INSERT INTO scope_test VALUES (5)")
                    raise ValueError("nested failure")
        assert [r[0] for r in observer.execute("SELECT value FROM scope_test")] == [1, 4]
    finally:
        observer.close()


def test_unpinned_repository_connection_closes_after_context(tmp_path):
    repository = Repository.attach(tmp_path / "state.sqlite")
    with repository.connection() as connection:
        connection.execute("SELECT 1")
    with pytest.raises(sqlite3.ProgrammingError, match="closed"):
        connection.execute("SELECT 1")


class _CommitFailsWhenArmed(sqlite3.Connection):
    """A connection whose next COMMIT fails the way a busy database does.

    SQLite leaves the transaction open when COMMIT returns SQLITE_BUSY; raising
    before the real commit reproduces exactly that state.
    """

    fail_next_commit = False

    def commit(self) -> None:
        if self.fail_next_commit:
            self.fail_next_commit = False
            raise sqlite3.OperationalError("database is locked")
        super().commit()


def _scope_table_repository(path, monkeypatch) -> Repository:
    raw = connect(path)
    raw.execute("CREATE TABLE scope_test (value INTEGER)")
    raw.commit()
    raw.close()

    def connect_with_armable_commit(sqlite_path, *, read_only=False):
        connection = sqlite3.connect(sqlite_path, factory=_CommitFailsWhenArmed)
        connection.row_factory = sqlite3.Row
        return connection

    monkeypatch.setattr("learnloop.db.repositories.connect", connect_with_armable_commit)
    return Repository.attach(path)


def _committed_values(path) -> list[int]:
    observer = sqlite3.connect(path)
    try:
        return [row[0] for row in observer.execute("SELECT value FROM scope_test ORDER BY value")]
    finally:
        observer.close()


def test_atomic_inside_pin_rolls_back_when_its_commit_fails(tmp_path, monkeypatch):
    path = tmp_path / "state.sqlite"
    repository = _scope_table_repository(path, monkeypatch)
    with repository.pinned():
        pinned_raw = repository.connection()._connection
        with pytest.raises(sqlite3.OperationalError, match="locked"):
            with repository.atomic():
                with repository.connection() as connection:
                    connection.execute("INSERT INTO scope_test VALUES (1)")
                pinned_raw.fail_next_commit = True
        assert not pinned_raw.in_transaction
        # A later, unrelated write on the same pinned connection commits only
        # its own work, never the scope that reported failure.
        with repository.connection() as connection:
            connection.execute("INSERT INTO scope_test VALUES (2)")
    assert _committed_values(path) == [2]


def test_pin_rolls_back_uncommitted_work_when_its_block_raises(tmp_path, monkeypatch):
    path = tmp_path / "state.sqlite"
    repository = _scope_table_repository(path, monkeypatch)
    with pytest.raises(ValueError, match="interrupted"):
        with repository.pinned():
            with repository.connection() as connection:
                connection.execute("INSERT INTO scope_test VALUES (1)")
            repository.connection().execute("INSERT INTO scope_test VALUES (2)")
            raise ValueError("interrupted")
    assert _committed_values(path) == [1]
