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
