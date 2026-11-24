"""The Reader workbench v2 inline checks migration: ``check_administrations`` (WORKFLOW) holding the one open
administration, ``check_veil_sets`` (RECEIPT, append-only), both empty; and the video chapters' replacement guard
(a decided chapter is never replaced). Nothing else changes. The number is the file name alone (``MIGRATION``)."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path

import pytest

from learnloop.db.migrate import UPGRADE_TEST_HELPER, applied_versions, apply_migrations, discover_migrations, upgrade_allowance
from learnloop.db.table_roles import TABLE_ROLES
from tests.helpers import MIGRATION_HEAD_FIXTURE
from tests.reader_rd7a_migration_helpers import RD7A_ADDED_OBJECTS, TABLES, undo_270

HEAD = MIGRATION_HEAD_FIXTURE / "state.sqlite"
MIGRATION = next(m for m in discover_migrations() if m.name == "reader_workbench_inline_checks")


def _admin(token: str, state: str = "open", **over: str) -> str:
    closed = "NULL" if state == "open" else "'t2'"
    values = {"submission_id": "NULL", "attempt_id": "NULL", **over}
    return ("INSERT INTO check_administrations(administration_token, request_id, commitment_id, surface, session_id, "
            "practice_item_id, contract_hash, cold, state, protection_method, submission_id, attempt_id, opened_at, "
            f"closed_at) VALUES ('{token}', 'req_{token}', 'cm_1', 'reader_inline', 's_1', 'pi_1', 'h', 1, '{state}', "
            f"'structural+notes_by_default', {values['submission_id']}, {values['attempt_id']}, 't', {closed})")


def _veil(veil_id: str, seq: int, token: str = "ad_1") -> str:
    return ("INSERT INTO check_veil_sets(veil_set_id, administration_token, commitment_id, seq, kind, method, veiled_json, "
            f"opened_json, created_at) VALUES ('{veil_id}', '{token}', 'cm_1', {seq}, 'begin', 'm', '[]', '[]', 't')")


def _head_copy(tmp_path: Path) -> Path:
    database = tmp_path / "state.sqlite"
    with closing(sqlite3.connect(HEAD)) as source, closing(sqlite3.connect(database)) as target:
        source.backup(target)
    return database


def test_the_tables_have_their_roles():
    assert {table: TABLE_ROLES[table].value for table in TABLES} == TABLES


def test_the_head_fixture_holds_it_empty_in_rollback_mode():
    assert HEAD.read_bytes()[18:20] == b"\x01\x01"
    assert MIGRATION.version in applied_versions(HEAD)
    with closing(sqlite3.connect(f"file:{HEAD}?mode=ro", uri=True)) as connection:
        for table in TABLES:
            assert connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] == 0


def test_it_adds_its_objects_and_changes_nothing_else(tmp_path):
    database = _head_copy(tmp_path)
    with closing(sqlite3.connect(database)) as connection:
        undo_270(connection)
        connection.execute("DELETE FROM schema_migrations WHERE version = ?", (MIGRATION.version,))
        connection.commit()
        before = {row[0]: row[1] for row in connection.execute("SELECT name, sql FROM sqlite_master")}
    with upgrade_allowance(UPGRADE_TEST_HELPER):
        assert [m.version for m in apply_migrations(database)] == [MIGRATION.version]
    with closing(sqlite3.connect(database)) as connection:
        after = {row[0]: row[1] for row in connection.execute("SELECT name, sql FROM sqlite_master")}
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
    assert set(after) - set(before) == RD7A_ADDED_OBJECTS
    assert set(before) - set(after) == set()
    assert {name for name in before if before[name] != after[name]} == set()
    with closing(sqlite3.connect(f"file:{HEAD}?mode=ro", uri=True)) as head:
        expected = {row[0]: row[1] for row in head.execute("SELECT name, sql FROM sqlite_master")}
    assert after == expected


def test_one_administration_is_open_at_a_time_and_a_closed_one_is_final(tmp_path):
    with closing(sqlite3.connect(_head_copy(tmp_path), isolation_level=None)) as connection:
        connection.execute(_admin("ad_1"))
        with pytest.raises(sqlite3.IntegrityError, match="UNIQUE"):
            connection.execute(_admin("ad_2"))
        connection.execute("UPDATE check_administrations SET exposure_json = '[1]' WHERE administration_token = 'ad_1'")
        connection.execute("UPDATE check_administrations SET state = 'abandoned', closed_at = 't2' "
                           "WHERE administration_token = 'ad_1'")
        connection.execute(_admin("ad_2"))  # the lock is free again
        for statement in ("UPDATE check_administrations SET state = 'open', closed_at = NULL WHERE administration_token = 'ad_1'",
                          "UPDATE check_administrations SET exposure_json = '[]' WHERE administration_token = 'ad_1'"):
            with pytest.raises(sqlite3.IntegrityError, match="final"):
                connection.execute(statement)
        with pytest.raises(sqlite3.IntegrityError, match="kept"):
            connection.execute("DELETE FROM check_administrations WHERE administration_token = 'ad_2'")


def test_the_constraints_hold(tmp_path):
    with closing(sqlite3.connect(_head_copy(tmp_path), isolation_level=None)) as connection:
        for bad in (_admin("ad_x").replace("'reader_inline'", "'today'"),
                    _admin("ad_x").replace("'open', 'structural", "'maybe', 'structural"),
                    _admin("ad_x", state="abandoned").replace("'t2')", "NULL)"),
                    _admin("ad_x", state="submitted")):
            with pytest.raises(sqlite3.IntegrityError, match="CHECK"):
                connection.execute(bad)
        connection.execute(_admin("ad_y", state="submitted", submission_id="'sub_1'", attempt_id="'at_1'"))


def test_the_veil_sets_are_append_only(tmp_path):
    with closing(sqlite3.connect(_head_copy(tmp_path), isolation_level=None)) as connection:
        connection.execute(_admin("ad_1"))
        connection.execute(_veil("vs_1", 1))
        for statement in ("UPDATE check_veil_sets SET method = 'x'", "DELETE FROM check_veil_sets",
                          _veil("vs_1", 2).replace("INSERT INTO", "INSERT OR REPLACE INTO"),
                          _veil("vs_2", 1).replace("INSERT INTO", "INSERT OR REPLACE INTO")):
            with pytest.raises(sqlite3.IntegrityError, match="append-only"):
                connection.execute(statement)
        assert connection.execute("SELECT veil_set_id FROM check_veil_sets").fetchall() == [("vs_1",)]


def test_a_decided_video_chapter_is_never_replaced(tmp_path):
    row = ("INSERT OR REPLACE INTO video_chapters(chapter_id, extraction_id, source_id, t0, t1, title, lo_ids_json, state, "
           "judgment_ref, suggested_at) VALUES ('vc_1', 'ext_v', 'src_v', 10, 70, '{title}', '[]', 'suggested', 'j', 't')")
    with closing(sqlite3.connect(_head_copy(tmp_path), isolation_level=None)) as connection:
        connection.execute(row.format(title="first"))
        connection.execute(row.format(title="second"))  # a suggestion is still replaced
        assert connection.execute("SELECT title FROM video_chapters").fetchall() == [("second",)]
        connection.execute("UPDATE video_chapters SET state = 'accepted', decided_at = 't2'")
        connection.execute(row.format(title="third"))  # a decided one is not: the insert is skipped
        assert connection.execute("SELECT title, state FROM video_chapters").fetchall() == [("second", "accepted")]
