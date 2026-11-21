"""The topic-work migration: ``reader_topic_question_work``.

One new WORKFLOW table, refused to adaptive difficulty; nothing else changes and nothing is backfilled (section jobs
queued before it are indexed by the code that claims, not here). One claim per topic and purpose. The number is the
migration's file name alone (``MIGRATION``).
"""

from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path

import pytest

from learnloop.adaptive_difficulty.protected_tables import DENIED, ROLES
from learnloop.db.migrate import UPGRADE_TEST_HELPER, applied_versions, apply_migrations, discover_migrations, upgrade_allowance
from learnloop.db.table_roles import TABLE_ROLES, TableRole
from tests.helpers import MIGRATION_HEAD_FIXTURE
from tests.reader_topic_question_work_migration_helpers import TOPIC_WORK, TOPIC_WORK_ADDED_OBJECTS

HEAD = MIGRATION_HEAD_FIXTURE / "state.sqlite"
MIGRATION = next(m for m in discover_migrations() if m.name == "reader_topic_question_work")
COLUMNS = [
    "id", "learning_object_id", "purpose", "owner", "source_id", "extraction_id", "section_id", "trigger_event",
    "passage_ids_json", "source_refs_json", "requested_count", "model_settings_json", "work_key", "batch_id",
    "job_id", "proposal_ids_json", "state", "error", "claimed_at", "updated_at",
]
NOW = "2026-11-21T00:00:00+00:00"


def test_the_table_is_workflow_and_denied_to_adaptive_difficulty():
    # WORKFLOW, as reader_section_progress whose stamp points at it: never cleared by a rebuild, and outside the
    # dataset export and the adjudication evidence.
    assert TABLE_ROLES[TOPIC_WORK] is TableRole.WORKFLOW
    assert ROLES[TOPIC_WORK] == DENIED


def test_the_head_fixture_holds_it_empty_in_rollback_mode():
    assert HEAD.read_bytes()[18:20] == b"\x01\x01"
    assert MIGRATION.version in applied_versions(HEAD)
    with closing(sqlite3.connect(f"file:{HEAD}?mode=ro", uri=True)) as connection:
        assert [row[1] for row in connection.execute(f"PRAGMA table_info({TOPIC_WORK})")] == COLUMNS
        assert connection.execute(f"SELECT COUNT(*) FROM {TOPIC_WORK}").fetchone()[0] == 0


def _downgraded(database: Path) -> None:
    with closing(sqlite3.connect(HEAD)) as source, closing(sqlite3.connect(database)) as target:
        source.backup(target)
    with closing(sqlite3.connect(database)) as connection:
        connection.execute(f"DROP TABLE {TOPIC_WORK}")  # its indexes go with it
        connection.execute("DELETE FROM schema_migrations WHERE version = ?", (MIGRATION.version,))
        connection.commit()


def _rows(connection: sqlite3.Connection, table: str) -> list[tuple]:
    return sorted(tuple(row) for row in connection.execute(f"SELECT * FROM {table}"))


def test_it_adds_the_table_and_changes_nothing_else(tmp_path):
    database = tmp_path / "state.sqlite"
    _downgraded(database)
    with closing(sqlite3.connect(database)) as connection:
        before = {row[0]: row[1] for row in connection.execute("SELECT name, sql FROM sqlite_master")}
        kept = {table: _rows(connection, table) for table in ("reader_section_progress", "ingest_jobs")}
    with upgrade_allowance(UPGRADE_TEST_HELPER):
        assert [m.version for m in apply_migrations(database)] == [MIGRATION.version]
    with closing(sqlite3.connect(database)) as connection:
        after = {row[0]: row[1] for row in connection.execute("SELECT name, sql FROM sqlite_master")}
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        # No backfill, and no section stamp or queued job is touched.
        assert {table: _rows(connection, table) for table in kept} == kept
        assert connection.execute(f"SELECT COUNT(*) FROM {TOPIC_WORK}").fetchone()[0] == 0
    assert set(after) - set(before) == TOPIC_WORK_ADDED_OBJECTS
    assert {name for name in before if before[name] != after[name]} == set()


def _insert(connection, work_id, topic, *, owner="topic", state="queued", trigger="section_finished",
            work_key="key", batch_id="batch_1", purpose="reader_first_set"):
    connection.execute(
        f"INSERT INTO {TOPIC_WORK}(id, learning_object_id, purpose, owner, trigger_event, work_key, batch_id, state, "
        "claimed_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (work_id, topic, purpose, owner, trigger, work_key, batch_id, state, NOW, NOW))


def test_one_claim_per_topic_and_only_the_known_purposes_triggers_and_states(tmp_path):
    database = tmp_path / "state.sqlite"
    with closing(sqlite3.connect(HEAD)) as source, closing(sqlite3.connect(database)) as target:
        source.backup(target)
    with closing(sqlite3.connect(database)) as connection:
        _insert(connection, "w1", "lo_a")
        _insert(connection, "w2", "lo_b", trigger="part_read")
        _insert(connection, "w3", "lo_c", owner="section_job", state="legacy", trigger=None, work_key=None)
        refused = [
            dict(work_id="w4", topic="lo_a"),  # the topic is claimed already
            dict(work_id="w5", topic="lo_d", purpose="more_questions"),
            dict(work_id="w6", topic="lo_d", trigger="scrolled"),
            dict(work_id="w7", topic="lo_d", state="done"),
            dict(work_id="w8", topic="lo_d", owner="section_job"),  # a section job's topic is legacy
            dict(work_id="w9", topic="lo_d", state="legacy"),  # and only a section job's
            dict(work_id="w10", topic="lo_d", trigger=None),  # topic work says what claimed it,
            dict(work_id="w11", topic="lo_d", work_key=None),  # its checkpoint scope
            dict(work_id="w12", topic="lo_d", batch_id=None),  # and the batch queued with the claim
        ]
        for fields in refused:
            with pytest.raises(sqlite3.IntegrityError):
                _insert(connection, **fields)
        assert [row[0] for row in connection.execute(f"SELECT learning_object_id FROM {TOPIC_WORK} ORDER BY id")] == [
            "lo_a", "lo_b", "lo_c"]
