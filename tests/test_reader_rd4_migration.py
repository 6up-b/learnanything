"""The Reader workbench v2 scratchpads migration: the five RD4 tables, ``pad_text`` in both gap tables and the two
pad reversals. Every rebuilt table keeps its rows, indexes and triggers; nothing is backfilled. The number is the
file name alone (``MIGRATION``)."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path

import pytest

from learnloop.db.migrate import UPGRADE_TEST_HELPER, applied_versions, apply_migrations, discover_migrations, upgrade_allowance
from learnloop.db.table_roles import TABLE_ROLES, TableRole
from tests.helpers import MIGRATION_HEAD_FIXTURE
from tests.reader_rd4_migration_helpers import APPEND_ONLY, RD4_ADDED_OBJECTS, RD4_REBUILT, TABLES, undo_266

HEAD = MIGRATION_HEAD_FIXTURE / "state.sqlite"
MIGRATION = next(m for m in discover_migrations() if m.name == "reader_workbench_pads")

_GAP = ("INSERT INTO learner_text_gaps(id, source_kind, source_id, learner_text, chooser, context_judge, kind, action, "
        "algorithm_version, pipeline_version, created_at) VALUES (?, ?, ?, 'words', 'context_model', 'gap_reader', "
        "'none', 'none', 'mvp-0.68', 'learner-text-gaps-v1', '2026-11-23T00:00:00Z')")
_JOB = ("INSERT INTO learner_text_gap_jobs(id, source_kind, source_id, created_at, updated_at) "
        "VALUES (?, ?, ?, '2026-11-23T00:00:00Z', '2026-11-23T00:00:00Z')")
_REVERSAL = ("INSERT INTO learner_text_gap_reversals(id, gap_id, reversal, actor, created_at) "
             "VALUES (?, ?, ?, 'learner', '2026-11-23T00:00:00Z')")


def test_the_tables_have_the_specs_roles():
    assert {table: TABLE_ROLES[table].value for table in TABLES} == TABLES
    for table in RD4_REBUILT:
        assert table in TABLE_ROLES
    assert TABLE_ROLES["pad_proposals"] is TableRole.RECEIPT


def test_the_head_fixture_holds_it_empty_in_rollback_mode():
    assert HEAD.read_bytes()[18:20] == b"\x01\x01"
    assert MIGRATION.version in applied_versions(HEAD)
    with closing(sqlite3.connect(f"file:{HEAD}?mode=ro", uri=True)) as connection:
        sql = {row[0]: row[1] for row in connection.execute("SELECT name, sql FROM sqlite_master")}
        for table in TABLES:
            assert connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] == 0
    assert "'external_chat', 'pad_text'" in sql["learner_text_gaps"]
    assert "'external_chat', 'pad_text'" in sql["learner_text_gap_jobs"]
    assert "'unlinked', 'superseded', 'retracted'" in sql["learner_text_gap_reversals"]


def _downgraded(database: Path) -> None:
    with closing(sqlite3.connect(HEAD)) as source, closing(sqlite3.connect(database)) as target:
        source.backup(target)
    with closing(sqlite3.connect(database)) as connection:
        undo_266(connection)
        connection.execute("DELETE FROM schema_migrations WHERE version = ?", (MIGRATION.version,))
        connection.commit()


def _seeded_before(database: Path) -> None:
    """Rows in each rebuilt table before the migration (with every reference resolving), so the rebuild is seen
    keeping them."""

    with closing(sqlite3.connect(database)) as connection:
        connection.execute(_GAP, ("ltg_1", "tutor_question", "qe_1"))
        connection.execute(_GAP, ("ltg_2", "learner_note", "note_1"))
        connection.execute(_JOB, ("ltj_1", "tutor_question", "qe_1"))
        connection.execute(_REVERSAL, ("ltr_1", "ltg_2", "unlinked"))
        connection.commit()


def _rows(connection: sqlite3.Connection, table: str) -> list[tuple]:
    return sorted(tuple(row) for row in connection.execute(f"SELECT * FROM {table}"))


def test_it_adds_its_objects_rebuilds_three_tables_and_keeps_every_row(tmp_path):
    database = tmp_path / "state.sqlite"
    _downgraded(database)
    _seeded_before(database)
    with closing(sqlite3.connect(database)) as connection:
        before = {row[0]: row[1] for row in connection.execute("SELECT name, sql FROM sqlite_master")}
        kept = {table: _rows(connection, table) for table in RD4_REBUILT}
    with upgrade_allowance(UPGRADE_TEST_HELPER):
        assert [m.version for m in apply_migrations(database)] == [MIGRATION.version]
    with closing(sqlite3.connect(database)) as connection:
        after = {row[0]: row[1] for row in connection.execute("SELECT name, sql FROM sqlite_master")}
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        assert {table: _rows(connection, table) for table in RD4_REBUILT} == kept
        assert all(row[0] == "ltg_2" for row in connection.execute(
            "SELECT r.gap_id FROM learner_text_gap_reversals AS r JOIN learner_text_gaps AS g ON g.id = r.gap_id"))
    assert set(after) - set(before) == RD4_ADDED_OBJECTS
    assert set(before) - set(after) == set()
    assert {name for name in before if before[name] != after[name]} == set(RD4_REBUILT)
    with closing(sqlite3.connect(f"file:{HEAD}?mode=ro", uri=True)) as head:
        expected = {row[0]: row[1] for row in head.execute("SELECT name, sql FROM sqlite_master")}
    assert {name: after[name] for name in after} == expected


def _head_copy(tmp_path: Path) -> sqlite3.Connection:
    database = tmp_path / "state.sqlite"
    with closing(sqlite3.connect(HEAD)) as source, closing(sqlite3.connect(database)) as target:
        source.backup(target)
    connection = sqlite3.connect(database, isolation_level=None)
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def test_pad_text_and_the_two_reversals_are_admitted_and_nothing_else(tmp_path):
    with closing(_head_copy(tmp_path)) as connection:
        connection.execute(_GAP, ("ltg_p", "pad_text", "pbv_1"))
        connection.execute(_JOB, ("ltj_p", "pad_text", "pbv_1"))
        connection.execute(_REVERSAL, ("ltr_s", "ltg_p", "superseded"))
        connection.execute(_REVERSAL, ("ltr_r", "ltg_p", "retracted"))
        with pytest.raises(sqlite3.IntegrityError, match="CHECK"):
            connection.execute(_GAP, ("ltg_x", "pad_sketch", "pbv_2"))
        with pytest.raises(sqlite3.IntegrityError, match="CHECK"):
            connection.execute(_JOB, ("ltj_x", "pad_sketch", "pbv_2"))
        with pytest.raises(sqlite3.IntegrityError, match="CHECK"):
            connection.execute(_REVERSAL, ("ltr_x", "ltg_p", "forgotten"))
        with pytest.raises(sqlite3.IntegrityError, match="UNIQUE"):
            connection.execute(_REVERSAL, ("ltr_y", "ltg_p", "superseded"))
        with pytest.raises(sqlite3.IntegrityError, match="append-only"):
            connection.execute("UPDATE learner_text_gap_reversals SET actor = 'owner'")


def _pad_and_version(connection: sqlite3.Connection) -> None:
    connection.execute("INSERT INTO pads(pad_id, kind, created_at, updated_at) VALUES ('pad_1', 'running', 't', 't')")
    connection.execute("INSERT INTO pad_block_versions(version_id, block_id, pad_id, position_key, kind, body_md, "
                       "provenance, client_id, created_at) VALUES ('pbv_1', 'blk_1', 'pad_1', 'a0', 'text', 'x', "
                       "'learner', 'c', 't')")


_ROWS = {
    "pad_block_submissions": (
        "INSERT INTO pad_block_submissions(submission_id, block_id, version_id, pad_id, submitted_as, practice_item_id, "
        "session_id, attempt_id, request_hash, created_at) VALUES ('sub_1', 'blk_1', 'pbv_1', 'pad_1', 'attempt', "
        "'pi_1', 'ses_1', 'att_1', 'h', 't')"),
    "carried_question_events": (
        "INSERT INTO carried_question_events(event_id, carried_id, event, at) VALUES ('cqe_1', 'cq_1', 'carried', 't')"),
    "pad_proposals": (
        "INSERT INTO pad_proposals(proposal_id, block_version_id, block_id, pad_id, found_by, target_spec_json, "
        "reason_md, created_at) VALUES ('pp_1', 'pbv_1', 'blk_1', 'pad_1', 'passage_link', '{}', 'r', 't')"),
    "proposal_labels": (
        "INSERT INTO proposal_labels(label_id, proposal_kind, proposal_id, label, at) "
        "VALUES ('pl_1', 'pad_proposal', 'pp_1', 'dismiss', 't')"),
}


@pytest.mark.parametrize("table", APPEND_ONLY)
def test_the_append_only_tables_refuse_update_delete_and_a_replacing_insert(tmp_path, table):
    with closing(_head_copy(tmp_path)) as connection:
        _pad_and_version(connection)
        connection.execute("INSERT INTO carried_questions(carried_id, text, origin_kind, since, updated_at) "
                           "VALUES ('cq_1', 'why?', 'typed', 't', 't')")
        connection.execute(_ROWS[table])
        before = _rows(connection, table)
        for statement in (f"UPDATE {table} SET rowid = rowid", f"DELETE FROM {table}",
                          _ROWS[table].replace("INSERT INTO", "INSERT OR REPLACE INTO", 1)):
            with pytest.raises(sqlite3.IntegrityError, match="append-only"):
                connection.execute(statement)
        assert _rows(connection, table) == before


def test_the_constraints_hold(tmp_path):
    with closing(_head_copy(tmp_path)) as connection:
        _pad_and_version(connection)
        with pytest.raises(sqlite3.IntegrityError, match="CHECK"):
            # An attempt submission names its attempt.
            connection.execute(_ROWS["pad_block_submissions"].replace("'att_1'", "NULL"))
        with pytest.raises(sqlite3.IntegrityError, match="FOREIGN KEY"):
            connection.execute(_ROWS["pad_block_submissions"].replace("'pbv_1'", "'pbv_missing'"))
        with pytest.raises(sqlite3.IntegrityError, match="CHECK"):
            connection.execute("INSERT INTO carried_questions(carried_id, text, origin_kind, since, updated_at) "
                               "VALUES ('cq_2', '   ', 'typed', 't', 't')")
        with pytest.raises(sqlite3.IntegrityError, match="FOREIGN KEY"):
            connection.execute(_ROWS["carried_question_events"])
        connection.execute(_ROWS["pad_proposals"])
        with pytest.raises(sqlite3.IntegrityError, match="append-only|UNIQUE"):
            # One proposal per block version.
            connection.execute(_ROWS["pad_proposals"].replace("'pp_1'", "'pp_2'"))
        with pytest.raises(sqlite3.IntegrityError, match="CHECK"):
            connection.execute(_ROWS["proposal_labels"].replace("'dismiss'", "'loved_it'"))
