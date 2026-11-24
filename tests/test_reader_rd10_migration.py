"""The Reader workbench v2 video chapters migration: ``video_chapters`` (WORKFLOW), empty; a chapter is decided once and
a decided chapter is kept; nothing else changes. The number is the file name alone (``MIGRATION``)."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path

import pytest

from learnloop.db.migrate import UPGRADE_TEST_HELPER, applied_versions, apply_migrations, discover_migrations, upgrade_allowance
from learnloop.db.table_roles import TABLE_ROLES
from tests.helpers import MIGRATION_HEAD_FIXTURE
from tests.reader_rd10_migration_helpers import RD10_ADDED_OBJECTS, TABLES, undo_268

HEAD = MIGRATION_HEAD_FIXTURE / "state.sqlite"
MIGRATION = next(m for m in discover_migrations() if m.name == "reader_workbench_video_chapters")

_ROW = ("INSERT INTO video_chapters(chapter_id, extraction_id, source_id, t0, t1, title, lo_ids_json, state, "
        "judgment_ref, suggested_at) VALUES ('vc_1', 'ext_v', 'src_v', 10, 70, 'softmax, step by step', '[\"lo_1\"]', "
        "'suggested', 'vch_1', 't')")


def test_the_table_has_its_role():
    assert {table: TABLE_ROLES[table].value for table in TABLES} == TABLES


def test_the_head_fixture_holds_it_empty_in_rollback_mode():
    assert HEAD.read_bytes()[18:20] == b"\x01\x01"
    assert MIGRATION.version in applied_versions(HEAD)
    with closing(sqlite3.connect(f"file:{HEAD}?mode=ro", uri=True)) as connection:
        assert connection.execute("SELECT COUNT(*) FROM video_chapters").fetchone()[0] == 0


def _head_copy(tmp_path: Path) -> Path:
    database = tmp_path / "state.sqlite"
    with closing(sqlite3.connect(HEAD)) as source, closing(sqlite3.connect(database)) as target:
        source.backup(target)
    return database


def test_it_adds_its_objects_and_changes_nothing_else(tmp_path):
    database = _head_copy(tmp_path)
    with closing(sqlite3.connect(database)) as connection:
        undo_268(connection)
        connection.execute("DELETE FROM schema_migrations WHERE version = ?", (MIGRATION.version,))
        connection.commit()
        before = {row[0]: row[1] for row in connection.execute("SELECT name, sql FROM sqlite_master")}
    with upgrade_allowance(UPGRADE_TEST_HELPER):
        assert [m.version for m in apply_migrations(database)] == [MIGRATION.version]
    with closing(sqlite3.connect(database)) as connection:
        after = {row[0]: row[1] for row in connection.execute("SELECT name, sql FROM sqlite_master")}
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
    assert set(after) - set(before) == RD10_ADDED_OBJECTS
    assert set(before) - set(after) == set()
    assert {name for name in before if before[name] != after[name]} == set()
    # The head as 268 left it: 270 later added a replacement guard on its table.
    as_268 = tmp_path / "as_268.sqlite"
    with closing(sqlite3.connect(HEAD)) as source, closing(sqlite3.connect(as_268)) as target:
        source.backup(target)
    with closing(sqlite3.connect(as_268)) as head:
        head.execute("DROP TRIGGER IF EXISTS video_chapters_no_replace_decided")
        expected = {row[0]: row[1] for row in head.execute("SELECT name, sql FROM sqlite_master")}
    assert after == expected


def test_a_chapter_is_decided_once_and_a_decided_chapter_is_kept(tmp_path):
    with closing(sqlite3.connect(_head_copy(tmp_path), isolation_level=None)) as connection:
        connection.execute(_ROW)
        connection.execute(_ROW.replace("'vc_1'", "'vc_2'"))
        # A suggestion still undecided may be replaced by a new run.
        connection.execute("DELETE FROM video_chapters WHERE chapter_id = 'vc_2'")
        connection.execute("UPDATE video_chapters SET state = 'accepted', decided_at = 't2' WHERE chapter_id = 'vc_1'")
        for statement in ("UPDATE video_chapters SET state = 'dismissed' WHERE chapter_id = 'vc_1'",
                          "UPDATE video_chapters SET title = 'x' WHERE chapter_id = 'vc_1'"):
            with pytest.raises(sqlite3.IntegrityError, match="decided once"):
                connection.execute(statement)
        with pytest.raises(sqlite3.IntegrityError, match="kept"):
            connection.execute("DELETE FROM video_chapters WHERE chapter_id = 'vc_1'")
        connection.execute(_ROW.replace("'vc_1'", "'vc_3'"))
        with pytest.raises(sqlite3.IntegrityError, match="decided once"):
            # A suggestion's own facts never change, only its decision.
            connection.execute("UPDATE video_chapters SET t1 = 90 WHERE chapter_id = 'vc_3'")


def test_the_constraints_hold(tmp_path):
    with closing(sqlite3.connect(_head_copy(tmp_path), isolation_level=None)) as connection:
        for bad in (_ROW.replace("'suggested', 'vch_1'", "'maybe', 'vch_1'"), _ROW.replace("10, 70", "70, 10"),
                    _ROW.replace("10, 70", "-1, 70"), _ROW.replace("'softmax, step by step'", "''"),
                    _ROW.replace("'suggested', 'vch_1', 't')", "'accepted', 'vch_1', 't')")):
            with pytest.raises(sqlite3.IntegrityError, match="CHECK"):
                connection.execute(bad)
