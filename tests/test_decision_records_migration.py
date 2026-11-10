"""Refactor B1, migration 253 (ADR-017): ``decision_records`` and ``model_call_receipts.trace_id``.

One new RECEIPT table, append-only by two triggers, and one nullable column with a partial index; nothing else changes.
A vault at 252 gains exactly those, and every row it already held is as it was (every receipt's ``trace_id`` NULL). The
number is the migration's file name alone (``MIGRATION``).
"""

from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path

import pytest

from learnloop.db.migrate import UPGRADE_TEST_HELPER, applied_versions, apply_migrations, discover_migrations, upgrade_allowance
from learnloop.db.table_roles import TABLE_ROLES, TableRole
from tests.helpers import MIGRATION_HEAD_FIXTURE

HEAD = MIGRATION_HEAD_FIXTURE / "state.sqlite"
TABLE = "decision_records"
MIGRATION = next(m for m in discover_migrations() if m.name == "decision_records")
OBJECTS = frozenset({TABLE, "decision_records_trace", "decision_records_subject", "decision_records_parent",
                     "decision_records_kind", "decision_records_no_update", "decision_records_no_delete",
                     "model_call_receipts_trace"})
#: What 253 adds (with the table's own autoindex): earlier migrations' "nothing else changed" diffs on the way to head read this.
B1_ADDED_OBJECTS = OBJECTS | {f"sqlite_autoindex_{TABLE}_1"}
#: What 253 alters (one nullable column on a receipt table): the same diffs read this.
B1_ALTERED_TABLES = frozenset({"model_call_receipts"})
COLUMNS = ["id", "trace_id", "parent_id", "kind", "status", "subject_kind", "subject_id", "chosen_ref", "decided_by", "rule",
           "alternatives_json", "facts_json", "versions_json", "detail_table", "detail_id", "error_type", "error_where",
           "created_at"]


def test_the_table_is_a_receipt():
    assert TABLE_ROLES[TABLE] is TableRole.RECEIPT


def test_the_head_fixture_holds_it_in_rollback_mode_with_every_trace_null():
    assert HEAD.read_bytes()[18:20] == b"\x01\x01"
    assert MIGRATION.version in applied_versions(HEAD)
    with closing(sqlite3.connect(f"file:{HEAD}?mode=ro", uri=True)) as connection:
        assert [row[1] for row in connection.execute(f"PRAGMA table_info({TABLE})")] == COLUMNS
        assert connection.execute(f"SELECT COUNT(*) FROM {TABLE}").fetchone()[0] == 0
        assert connection.execute("SELECT COUNT(*) FROM model_call_receipts WHERE trace_id IS NOT NULL").fetchone()[0] == 0


def _downgraded(database: Path) -> None:
    with closing(sqlite3.connect(HEAD)) as source, closing(sqlite3.connect(database)) as target:
        source.backup(target)
    with closing(sqlite3.connect(database)) as connection:
        connection.execute(f"DROP TABLE {TABLE}")  # its indexes and triggers go with it
        connection.execute("DROP INDEX model_call_receipts_trace")
        connection.execute("ALTER TABLE model_call_receipts DROP COLUMN trace_id")
        connection.execute("DELETE FROM schema_migrations WHERE version = ?", (MIGRATION.version,))
        connection.commit()


def _rows(connection: sqlite3.Connection, table: str) -> list[tuple]:
    return sorted(tuple(row) for row in connection.execute(f"SELECT * FROM {table}"))


def test_it_adds_the_table_and_the_column_and_changes_nothing_else(tmp_path):
    database = tmp_path / "state.sqlite"
    _downgraded(database)
    with closing(sqlite3.connect(database)) as connection:
        before = {row[0]: row[1] for row in connection.execute("SELECT name, sql FROM sqlite_master")}
        receipts_before = _rows(connection, "model_call_receipts")
        attempts_before = _rows(connection, "practice_attempts")
    with upgrade_allowance(UPGRADE_TEST_HELPER):
        assert [m.version for m in apply_migrations(database)] == [MIGRATION.version]
    with closing(sqlite3.connect(database)) as connection:
        after = {row[0]: row[1] for row in connection.execute("SELECT name, sql FROM sqlite_master")}
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        assert [row[:-1] for row in _rows(connection, "model_call_receipts")] == receipts_before
        assert {row[-1] for row in _rows(connection, "model_call_receipts")} <= {None}
        assert _rows(connection, "practice_attempts") == attempts_before
    assert set(after) - set(before) == B1_ADDED_OBJECTS
    assert {name for name in before if before[name] != after[name]} == B1_ALTERED_TABLES


def test_the_receipt_refuses_update_delete_bad_json_and_an_unknown_status(tmp_path):
    database = tmp_path / "state.sqlite"
    with closing(sqlite3.connect(HEAD)) as source, closing(sqlite3.connect(database)) as target:
        source.backup(target)
    with closing(sqlite3.connect(database)) as connection:
        insert = (f"INSERT INTO {TABLE} (id, trace_id, kind, status, facts_json, created_at) "
                  "VALUES (?, 'tr', 'slate', ?, ?, '2026-11-10T00:00:00+00:00')")
        connection.execute(insert, ("r1", "chosen", "{}"))
        defaults = connection.execute(
            f"SELECT alternatives_json, facts_json, versions_json FROM {TABLE} WHERE id = 'r1'").fetchone()
        assert defaults == ("[]", "{}", "{}")
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(insert, ("r2", "maybe", "{}"))
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(insert, ("r3", "chosen", "not json"))
        for statement in (f"UPDATE {TABLE} SET rule = 'x'", f"DELETE FROM {TABLE}"):
            with pytest.raises(sqlite3.IntegrityError, match="append-only"):
                connection.execute(statement)
