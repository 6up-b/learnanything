"""Teacher TE1: migration 234 (spec_teacher_v1 §18.1; 230 on its branch, renumbered 234 at landing).

Nine tables (the lesson ledger, its receipts and the DERIVED weight state), each classified for rebuild
and for AD (DENIED: AD reads none of them), and ``source_tool_calls`` rebuilt so its ``caller_kind`` CHECK
admits ``teacher``, every row and id kept. The head fixture is at 234 in rollback mode with empty lesson
tables. The earlier migrations' "nothing else changed" diffs on the way to head read
``TE1_ADDED_OBJECTS`` and ``TE1_ALTERED_TABLES``.
"""

from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path

import pytest

from learnloop.adaptive_difficulty import protected_tables as PT
from learnloop.db.migrate import UPGRADE_TEST_HELPER, apply_migrations, discover_migrations, upgrade_allowance
from learnloop.db.table_roles import role_for_table
from tests.helpers import MIGRATION_HEAD_FIXTURE
from tests.teacher_te1_migration_helpers import TE1_ADDED_OBJECTS, TE1_TABLES

HEAD = MIGRATION_HEAD_FIXTURE / "state.sqlite"


def test_234_is_te1s_migration_and_every_table_is_classified():
    names = {migration.version: migration.path.name for migration in discover_migrations()}
    assert names[234] == "234_teacher_lessons.sql"
    for table, role in TE1_TABLES.items():
        assert role_for_table(table) == role, table
        # Teacher TE3a (spec_teacher_v1 rev 5 §14.2) moved the lesson, its plan and its receipt to READING
        # (PROTECTED, read by the rules only); every other lesson table stays DENIED.
        expected = PT.PROTECTED if table in ("lessons", "lesson_plans", "lesson_receipts") else PT.DENIED
        assert PT.role(table) == expected, table


def _upgrade(tmp_path: Path) -> Path:
    """Every migration through 233 (main's head at the landing), then 234."""

    database = tmp_path / "state.sqlite"
    with upgrade_allowance(UPGRADE_TEST_HELPER):
        apply_migrations(database)
    return database


def test_the_head_fixture_is_at_234_in_rollback_mode_with_empty_lesson_tables():
    assert HEAD.read_bytes()[18:20] == b"\x01\x01"
    with closing(sqlite3.connect(f"file:{HEAD}?mode=ro", uri=True)) as connection:
        names = {row[0] for row in connection.execute("SELECT name FROM sqlite_master")}
        assert TE1_ADDED_OBJECTS <= names
        for table in TE1_TABLES:
            assert connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] == 0


def _check(database: Path) -> None:
    with closing(sqlite3.connect(database)) as connection:
        sql = connection.execute("SELECT sql FROM sqlite_master WHERE name = 'source_tool_calls'").fetchone()[0]
        assert "'teacher'" in sql
        connection.execute(
            "INSERT INTO source_tool_calls(id, row_kind, created_at, caller_kind, context_json, policy, tool, "
            "arguments_json, status) VALUES ('stc_1', 'request', '2026-11-01T00:00:00Z', 'teacher', '{}', 'reading', "
            "'find_sources', '{}', 'requested')")
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                "INSERT INTO source_tool_calls(id, row_kind, created_at, caller_kind, context_json, policy, tool, "
                "arguments_json, status) VALUES ('stc_2', 'request', '2026-11-01T00:00:00Z', 'nobody', '{}', "
                "'reading', 'find_sources', '{}', 'requested')")
        with pytest.raises(sqlite3.IntegrityError, match="append-only"):
            connection.execute("UPDATE source_tool_calls SET status = 'refused' WHERE id = 'stc_1'")
        connection.execute(
            "INSERT INTO lessons(id, driver, origin, entry, goal_text, goal_json, learning_object_ids_json, "
            "doctrine_version, brief_version, algorithm_version, opened_at) VALUES ('les_1', 'desktop', "
            "'learner_pick', 'learning_object', 'g', '{}', '[]', 'd', 'b', 'mvp-0.41', '2026-11-01T00:00:00Z')")
        connection.execute("UPDATE lessons SET closed_at = '2026-11-01T01:00:00Z', close_reason = 'goal_reached' "
                           "WHERE id = 'les_1'")
        with pytest.raises(sqlite3.IntegrityError, match="once"):
            connection.execute("UPDATE lessons SET close_reason = 'learner_stop' WHERE id = 'les_1'")
        with pytest.raises(sqlite3.IntegrityError, match="ledger"):
            connection.execute("DELETE FROM lessons WHERE id = 'les_1'")
        # Ruling R1: a lesson whose protection state changed since its brief was built closes protection_changed.
        connection.execute(
            "INSERT INTO lessons(id, driver, origin, entry, goal_text, goal_json, learning_object_ids_json, "
            "doctrine_version, brief_version, algorithm_version, opened_at) VALUES ('les_2', 'desktop', "
            "'learner_pick', 'learning_object', 'g', '{}', '[]', 'd', 'b', 'mvp-0.41', '2026-11-01T00:00:00Z')")
        connection.execute("UPDATE lessons SET closed_at = '2026-11-01T01:00:00Z', close_reason = 'protection_changed' "
                           "WHERE id = 'les_2'")
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                "INSERT INTO lessons(id, driver, origin, entry, goal_text, goal_json, learning_object_ids_json, "
                "doctrine_version, brief_version, algorithm_version, opened_at, closed_at, close_reason) VALUES "
                "('les_3', 'desktop', 'learner_pick', 'learning_object', 'g', '{}', '[]', 'd', 'b', 'mvp-0.41', "
                "'2026-11-01T00:00:00Z', '2026-11-01T01:00:00Z', 'redacted')")


def test_234_widens_the_caller_check_and_keeps_the_ledgers_append_only(tmp_path):
    _check(_upgrade(tmp_path))


@pytest.mark.durability
def test_234_on_the_durability_lane(tmp_path):
    database = _upgrade(tmp_path)
    with closing(sqlite3.connect(database)) as connection:
        assert connection.execute("PRAGMA journal_mode").fetchone()[0] == "wal"
    _check(database)


def test_234_keeps_every_source_tool_call_row(tmp_path):
    """From the head (a backup copy) with a recorded tool call: the rebuild keeps it, id and all."""

    from learnloop.db.copies import backup_database

    database = tmp_path / "head.sqlite"
    backup_database(HEAD, database)
    with closing(sqlite3.connect(database)) as connection:
        connection.execute(
            "INSERT INTO source_tool_calls(id, row_kind, created_at, caller_kind, context_json, policy, tool, "
            "arguments_json, status) VALUES ('stc_keep', 'request', '2026-11-01T00:00:00Z', 'tutor', '{}', "
            "'reading', 'find_sources', '{}', 'requested')")
        connection.commit()
        rows = connection.execute("SELECT id, caller_kind FROM source_tool_calls").fetchall()
    assert rows == [("stc_keep", "tutor")]
