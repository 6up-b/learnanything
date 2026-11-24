"""Migration 271 (RD7's fix round, the adversarial review of 2026-11-24): five columns on ``check_administrations``
that an administration writes while it is open (what begin froze, what the close promised), and guards so no RD7 row
can be replaced: a replacing insert meeting any unique key, the one-open index or an explicit rowid is refused (or, for
a decided video chapter, skipped). The number is the file name alone (``MIGRATION``)."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path

import pytest

from learnloop.db.migrate import UPGRADE_TEST_HELPER, apply_migrations, discover_migrations, upgrade_allowance
from tests.helpers import MIGRATION_HEAD_FIXTURE

HEAD = MIGRATION_HEAD_FIXTURE / "state.sqlite"
MIGRATION = next(m for m in discover_migrations() if m.name == "reader_workbench_inline_checks_fix")
COLUMNS = ("candidates_json", "presentation_json", "pending_before", "outcome_json", "exposure_ids_json")
GUARD_270_VEILS = ("WHEN EXISTS (SELECT 1 FROM check_veil_sets WHERE veil_set_id = NEW.veil_set_id\n"
                   "             OR (administration_token = NEW.administration_token AND seq = NEW.seq))")
GUARD_270_CHAPTERS = "WHEN EXISTS (SELECT 1 FROM video_chapters WHERE chapter_id = NEW.chapter_id AND state != 'suggested')"


def _copy(tmp_path: Path) -> Path:
    database = tmp_path / "state.sqlite"
    with closing(sqlite3.connect(HEAD)) as source, closing(sqlite3.connect(database)) as target:
        source.backup(target)
    return database


def _undo_271(connection: sqlite3.Connection) -> None:
    """The head as 270 left it: the new columns and guard gone, the two guards as 270 wrote them."""

    connection.execute("DROP TRIGGER check_administrations_no_replace")
    for column in COLUMNS:
        connection.execute(f"ALTER TABLE check_administrations DROP COLUMN {column}")
    connection.execute("DROP TRIGGER check_veil_sets_no_replace")
    connection.execute("CREATE TRIGGER check_veil_sets_no_replace\nBEFORE INSERT ON check_veil_sets\n" + GUARD_270_VEILS
                       + "\nBEGIN\n  SELECT RAISE(ABORT, 'check_veil_sets is append-only');\nEND")
    connection.execute("DROP TRIGGER video_chapters_no_replace_decided")
    connection.execute("CREATE TRIGGER video_chapters_no_replace_decided\nBEFORE INSERT ON video_chapters\n"
                       + GUARD_270_CHAPTERS + "\nBEGIN\n  SELECT RAISE(IGNORE);\nEND")
    connection.execute("DELETE FROM schema_migrations WHERE version = ?", (MIGRATION.version,))


def _admin(token: str, *, state: str = "open", rowid: int | None = None, submission: str | None = None) -> str:
    closed = "NULL" if state == "open" else "'t2'"
    sub = f"'{submission}'" if submission else "NULL"
    attempt = "'at_1'" if state == "submitted" else "NULL"
    rowid_col, rowid_val = ("rowid, ", f"{rowid}, ") if rowid is not None else ("", "")
    return ("INSERT OR REPLACE INTO check_administrations(" + rowid_col + "administration_token, request_id, commitment_id, "
            "surface, session_id, practice_item_id, contract_hash, cold, state, protection_method, submission_id, attempt_id, "
            f"opened_at, closed_at) VALUES ({rowid_val}'{token}', 'req_{token}', 'cm_1', 'reader_inline', 's_1', 'pi_1', 'h', 1, "
            f"'{state}', 'm', {sub}, {attempt}, 't', {closed})")


def test_it_adds_its_columns_and_guard_redefines_two_guards_and_keeps_every_row(tmp_path):
    database = _copy(tmp_path)
    with closing(sqlite3.connect(database)) as connection:
        _undo_271(connection)
        connection.execute(_admin("ad_kept", state="abandoned").replace("INSERT OR REPLACE", "INSERT"))
        connection.commit()
        before = {row[0]: row[1] for row in connection.execute("SELECT name, sql FROM sqlite_master")}
    with upgrade_allowance(UPGRADE_TEST_HELPER):
        assert [m.version for m in apply_migrations(database)] == [MIGRATION.version]
    with closing(sqlite3.connect(database)) as connection:
        after = {row[0]: row[1] for row in connection.execute("SELECT name, sql FROM sqlite_master")}
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        kept = connection.execute(f"SELECT administration_token, {', '.join(COLUMNS)} FROM check_administrations").fetchall()
    assert kept == [("ad_kept", "[]", None, None, None, "[]")]
    assert set(after) - set(before) == {"check_administrations_no_replace"}
    assert set(before) - set(after) == set()
    assert {name for name in before if before[name] != after[name]} == {
        "check_administrations", "check_veil_sets_no_replace", "video_chapters_no_replace_decided"}
    with closing(sqlite3.connect(f"file:{HEAD}?mode=ro", uri=True)) as head:
        assert after == {row[0]: row[1] for row in head.execute("SELECT name, sql FROM sqlite_master")}


def test_an_administration_is_never_replaced(tmp_path):
    with closing(sqlite3.connect(_copy(tmp_path), isolation_level=None)) as connection:
        connection.execute(_admin("ad_1", state="submitted", submission="sub_1"))
        connection.execute(_admin("ad_2"))
        for statement in (_admin("ad_1"),  # its token, reused to reopen it
                          _admin("ad_3"),  # a second open row: REPLACE on the one-open index would delete ad_2
                          _admin("ad_4", state="submitted", submission="sub_1"),  # its submission id
                          _admin("ad_5", state="abandoned", rowid=1)):  # its rowid
            with pytest.raises(sqlite3.IntegrityError, match="never replaced"):
                connection.execute(statement)
        rows = connection.execute("SELECT administration_token, state FROM check_administrations ORDER BY rowid").fetchall()
        assert rows == [("ad_1", "submitted"), ("ad_2", "open")]


def test_a_veil_set_and_a_decided_chapter_are_never_replaced_through_their_rowid(tmp_path):
    with closing(sqlite3.connect(_copy(tmp_path), isolation_level=None)) as connection:
        connection.execute(_admin("ad_1").replace("INSERT OR REPLACE", "INSERT"))
        connection.execute("INSERT INTO check_veil_sets(veil_set_id, administration_token, commitment_id, seq, kind, method, "
                           "created_at) VALUES ('vs_1', 'ad_1', 'cm_1', 1, 'begin', 'm', 't')")
        with pytest.raises(sqlite3.IntegrityError, match="append-only"):
            connection.execute("INSERT OR REPLACE INTO check_veil_sets(rowid, veil_set_id, administration_token, commitment_id, seq, "
                               "kind, method, created_at) VALUES (1, 'vs_2', 'ad_1', 'cm_1', 2, 'more', 'm', 't')")
        connection.execute("INSERT INTO video_chapters(chapter_id, extraction_id, source_id, t0, t1, title, lo_ids_json, state, "
                           "judgment_ref, suggested_at) VALUES ('vc_1', 'ext_v', 'src_v', 10, 70, 'kept', '[]', 'suggested', 'j', 't')")
        connection.execute("UPDATE video_chapters SET state = 'accepted', decided_at = 't2'")
        connection.execute("INSERT OR REPLACE INTO video_chapters(rowid, chapter_id, extraction_id, source_id, t0, t1, title, "
                           "lo_ids_json, state, judgment_ref, suggested_at) VALUES (1, 'vc_2', 'ext_v', 'src_v', 0, 5, 'forged', '[]', "
                           "'suggested', 'j', 't')")
        assert connection.execute("SELECT chapter_id, title, state FROM video_chapters").fetchall() == [("vc_1", "kept", "accepted")]
        assert connection.execute("SELECT veil_set_id FROM check_veil_sets").fetchall() == [("vs_1",)]
