"""The job-progress migration: ``ingest_job_progress``.

One new WORKFLOW table beside ``ingest_jobs`` (NEUTRAL to adaptive difficulty, as the job rows); nothing else changes
and nothing is backfilled. The number is the migration's file name alone (``MIGRATION``).
"""

from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path

from learnloop.adaptive_difficulty.protected_tables import NEUTRAL, ROLES
from learnloop.db.migrate import UPGRADE_TEST_HELPER, applied_versions, apply_migrations, discover_migrations, upgrade_allowance
from learnloop.db.table_roles import TABLE_ROLES, TableRole
from tests.helpers import MIGRATION_HEAD_FIXTURE
from tests.ingest_job_progress_migration_helpers import JOB_PROGRESS, JOB_PROGRESS_ADDED_OBJECTS

HEAD = MIGRATION_HEAD_FIXTURE / "state.sqlite"
MIGRATION = next(m for m in discover_migrations() if m.name == "ingest_job_progress")
COLUMNS = [
    "job_id", "attempt_count", "try_number", "try_started_at", "step", "drafted_topics", "reused", "output_call_id",
    "output_events", "last_output_at", "updated_at",
]


def test_the_table_is_workflow_and_neutral_to_adaptive_difficulty():
    # WORKFLOW, as the job rows beside it: never cleared by a rebuild, outside the dataset export; it holds steps,
    # counts and times, no protected material.
    assert TABLE_ROLES[JOB_PROGRESS] is TableRole.WORKFLOW
    assert ROLES[JOB_PROGRESS] == NEUTRAL


def test_the_head_fixture_holds_it_empty_in_rollback_mode():
    assert HEAD.read_bytes()[18:20] == b"\x01\x01"
    assert MIGRATION.version in applied_versions(HEAD)
    with closing(sqlite3.connect(f"file:{HEAD}?mode=ro", uri=True)) as connection:
        assert [row[1] for row in connection.execute(f"PRAGMA table_info({JOB_PROGRESS})")] == COLUMNS
        assert connection.execute(f"SELECT COUNT(*) FROM {JOB_PROGRESS}").fetchone()[0] == 0


def _downgraded(database: Path) -> None:
    with closing(sqlite3.connect(HEAD)) as source, closing(sqlite3.connect(database)) as target:
        source.backup(target)
    with closing(sqlite3.connect(database)) as connection:
        connection.execute(f"DROP TABLE {JOB_PROGRESS}")
        connection.execute("DELETE FROM schema_migrations WHERE version = ?", (MIGRATION.version,))
        connection.commit()


def _rows(connection: sqlite3.Connection, table: str) -> list[tuple]:
    return sorted(tuple(row) for row in connection.execute(f"SELECT * FROM {table}"))


def test_it_adds_the_table_and_changes_nothing_else(tmp_path):
    database = tmp_path / "state.sqlite"
    _downgraded(database)
    with closing(sqlite3.connect(database)) as connection:
        before = {row[0]: row[1] for row in connection.execute("SELECT name, sql FROM sqlite_master")}
        kept = {table: _rows(connection, table) for table in ("ingest_jobs", "model_call_receipts")}
    with upgrade_allowance(UPGRADE_TEST_HELPER):
        assert [m.version for m in apply_migrations(database)] == [MIGRATION.version]
    with closing(sqlite3.connect(database)) as connection:
        after = {row[0]: row[1] for row in connection.execute("SELECT name, sql FROM sqlite_master")}
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        assert {table: _rows(connection, table) for table in kept} == kept
        assert connection.execute(f"SELECT COUNT(*) FROM {JOB_PROGRESS}").fetchone()[0] == 0
    assert set(after) - set(before) == JOB_PROGRESS_ADDED_OBJECTS
    assert {name for name in before if before[name] != after[name]} == set()
