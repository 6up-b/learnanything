"""The Reader workbench v2 pen-and-ink migration: ``ink_strokes`` (RAW_LEDGER) and ``ink_transcriptions`` (RECEIPT),
both append-only by trigger and empty; nothing else changes. The number is the file name alone (``MIGRATION``)."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path

import pytest

from learnloop.db.migrate import UPGRADE_TEST_HELPER, applied_versions, apply_migrations, discover_migrations, upgrade_allowance
from learnloop.db.table_roles import TABLE_ROLES
from tests.helpers import MIGRATION_HEAD_FIXTURE
from tests.reader_rd8a_migration_helpers import APPEND_ONLY, RD8A_ADDED_OBJECTS, TABLES, undo_267

HEAD = MIGRATION_HEAD_FIXTURE / "state.sqlite"
MIGRATION = next(m for m in discover_migrations() if m.name == "reader_workbench_ink")

_ROWS = {
    "ink_strokes": (
        "INSERT INTO ink_strokes(ink_id, owner_kind, owner_id, kind, encoding, strokes_blob, content_hash, "
        "stroke_count, client_id, created_at) VALUES ('ink_1', 'block', 'blk_1', 'strokes', 'zlib-json-v1', x'00', "
        "'h', 1, 'c', 't')"),
    "ink_transcriptions": (
        "INSERT INTO ink_transcriptions(transcription_id, owner_kind, owner_id, content_hash, latex_md, "
        "confidence_label, task, prompt_version, created_at) VALUES ('it_1', 'block', 'blk_1', 'h', '$x$', "
        "'may_be_wrong', 'ink_transcription', 'v', 't')"),
}


def test_the_tables_have_their_roles():
    assert {table: TABLE_ROLES[table].value for table in TABLES} == TABLES


def test_the_head_fixture_holds_it_empty_in_rollback_mode():
    assert HEAD.read_bytes()[18:20] == b"\x01\x01"
    assert MIGRATION.version in applied_versions(HEAD)
    with closing(sqlite3.connect(f"file:{HEAD}?mode=ro", uri=True)) as connection:
        for table in TABLES:
            assert connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] == 0


def _head_copy(tmp_path: Path) -> Path:
    database = tmp_path / "state.sqlite"
    with closing(sqlite3.connect(HEAD)) as source, closing(sqlite3.connect(database)) as target:
        source.backup(target)
    return database


def test_it_adds_its_objects_and_changes_nothing_else(tmp_path):
    database = _head_copy(tmp_path)
    with closing(sqlite3.connect(database)) as connection:
        undo_267(connection)
        connection.execute("DELETE FROM schema_migrations WHERE version = ?", (MIGRATION.version,))
        connection.commit()
        before = {row[0]: row[1] for row in connection.execute("SELECT name, sql FROM sqlite_master")}
    with upgrade_allowance(UPGRADE_TEST_HELPER):
        assert [m.version for m in apply_migrations(database)] == [MIGRATION.version]
    with closing(sqlite3.connect(database)) as connection:
        after = {row[0]: row[1] for row in connection.execute("SELECT name, sql FROM sqlite_master")}
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
    assert set(after) - set(before) == RD8A_ADDED_OBJECTS
    assert set(before) - set(after) == set()
    assert {name for name in before if before[name] != after[name]} == set()
    with closing(sqlite3.connect(f"file:{HEAD}?mode=ro", uri=True)) as head:
        expected = {row[0]: row[1] for row in head.execute("SELECT name, sql FROM sqlite_master")}
    assert after == expected


@pytest.mark.parametrize("table", APPEND_ONLY)
def test_the_tables_refuse_update_delete_and_a_replacing_insert(tmp_path, table):
    with closing(sqlite3.connect(_head_copy(tmp_path), isolation_level=None)) as connection:
        connection.execute(_ROWS[table])
        before = sorted(tuple(row) for row in connection.execute(f"SELECT * FROM {table}"))
        for statement in (f"UPDATE {table} SET rowid = rowid", f"DELETE FROM {table}",
                          _ROWS[table].replace("INSERT INTO", "INSERT OR REPLACE INTO", 1)):
            with pytest.raises(sqlite3.IntegrityError, match="append-only"):
                connection.execute(statement)
        assert sorted(tuple(row) for row in connection.execute(f"SELECT * FROM {table}")) == before


def test_the_constraints_hold(tmp_path):
    with closing(sqlite3.connect(_head_copy(tmp_path), isolation_level=None)) as connection:
        strokes, readings = _ROWS["ink_strokes"], _ROWS["ink_transcriptions"]
        for bad in (strokes.replace("'block'", "'desk'"), strokes.replace("'strokes'", "'smudge'"),
                    strokes.replace("'zlib-json-v1'", "'raw'"), strokes.replace("'h', 1,", "'h', 0,"),
                    readings.replace("'may_be_wrong'", "'certain'"), readings.replace("'block'", "'pad'")):
            with pytest.raises(sqlite3.IntegrityError, match="CHECK"):
                connection.execute(bad)
        connection.execute(readings)
        with pytest.raises(sqlite3.IntegrityError, match="UNIQUE"):
            # One reading per owner and strokes.
            connection.execute(readings.replace("'it_1'", "'it_2'"))
