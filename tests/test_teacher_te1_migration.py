"""Teacher TE1: migration 230 (spec_teacher_v1 §18.1).

Nine tables (the lesson ledger, its receipts and the DERIVED weight state), each classified for rebuild
and for AD (DENIED: AD reads none of them), and ``source_tool_calls`` rebuilt so its ``caller_kind`` CHECK
admits ``teacher``, every row and id kept. The head fixture is at 230 in rollback mode with empty lesson
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
from learnloop.db.table_roles import TableRole, role_for_table

HEAD = Path(__file__).resolve().parents[1] / "fixtures" / "migration_head_230" / "state.sqlite"
TE1_TABLES = {
    "lessons": TableRole.RAW_LEDGER, "lesson_turns": TableRole.RAW_LEDGER, "lesson_plans": TableRole.RAW_LEDGER,
    "lesson_turn_payloads": TableRole.WORKFLOW, "lesson_checks": TableRole.RECEIPT,
    "lesson_receipts": TableRole.RECEIPT, "lesson_weight_state": TableRole.DERIVED,
    "lesson_weight_trace": TableRole.DERIVED, "confidence_calibration_state": TableRole.DERIVED,
}
TE1_ADDED_OBJECTS = frozenset({
    *TE1_TABLES,
    "idx_lesson_checks_lesson", "idx_lesson_checks_lo", "idx_lesson_turn_payloads_lesson",
    "idx_lesson_weight_trace_check", "idx_lessons_opened",
    "lesson_checks_no_delete", "lesson_checks_no_update", "lesson_plans_no_delete", "lesson_plans_no_update",
    "lesson_receipts_no_delete", "lesson_receipts_no_update", "lesson_turns_no_delete", "lesson_turns_no_update",
    "lessons_close_once", "lessons_no_delete",
    "sqlite_autoindex_confidence_calibration_state_1", "sqlite_autoindex_lesson_checks_1",
    "sqlite_autoindex_lesson_checks_2", "sqlite_autoindex_lesson_plans_1", "sqlite_autoindex_lesson_plans_2",
    "sqlite_autoindex_lesson_receipts_1", "sqlite_autoindex_lesson_turn_payloads_1",
    "sqlite_autoindex_lesson_turns_1", "sqlite_autoindex_lesson_turns_2", "sqlite_autoindex_lesson_weight_state_1",
    "sqlite_autoindex_lesson_weight_trace_1", "sqlite_autoindex_lesson_weight_trace_2", "sqlite_autoindex_lessons_1",
})
#: 230 rebuilds this table (its caller_kind CHECK gains 'teacher'); its objects keep their names.
TE1_ALTERED_TABLES = frozenset({"source_tool_calls"})


def test_230_is_te1s_migration_and_every_table_is_classified():
    names = {migration.version: migration.path.name for migration in discover_migrations()}
    assert names[230] == "230_teacher_lessons.sql"
    for table, role in TE1_TABLES.items():
        assert role_for_table(table) == role, table
        assert PT.role(table) == PT.DENIED, table


def _upgrade(tmp_path: Path) -> Path:
    """Main's 229 head (its sanitized fixture's schema, rebuilt from the migrations) then 230."""

    database = tmp_path / "state.sqlite"
    with upgrade_allowance(UPGRADE_TEST_HELPER):
        apply_migrations(database)
    return database


def test_the_head_fixture_is_at_230_in_rollback_mode_with_empty_lesson_tables():
    assert HEAD.read_bytes()[18:20] == b"\x01\x01"
    with closing(sqlite3.connect(f"file:{HEAD}?mode=ro", uri=True)) as connection:
        assert connection.execute("SELECT MAX(version) FROM schema_migrations").fetchone()[0] == 230
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


def test_230_widens_the_caller_check_and_keeps_the_ledgers_append_only(tmp_path):
    _check(_upgrade(tmp_path))


@pytest.mark.durability
def test_230_on_the_durability_lane(tmp_path):
    database = _upgrade(tmp_path)
    with closing(sqlite3.connect(database)) as connection:
        assert connection.execute("PRAGMA journal_mode").fetchone()[0] == "wal"
    _check(database)


def test_230_keeps_every_source_tool_call_row(tmp_path):
    """From the 229 head (a backup copy) with a recorded tool call: the rebuild keeps it, id and all."""

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
