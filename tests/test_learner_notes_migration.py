"""Curriculum C2: migration 229 (spec_deliverable_curriculum_v1 §10, §12 C2, §12.2).

Two new tables, append-only by trigger and both RAW_LEDGER: ``learner_notes``
(snapshots of the learner's notes, only once linked) and ``learner_note_links`` (the
model's proposals, the learner's links and hides). No DERIVED table, so no replayer;
both classified for AD (§9.4; the links are a READING table). 229 alters nothing.
"""

from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path

import pytest

from learnloop.adaptive_difficulty import protected_tables as PT
from learnloop.db.migrate import applied_versions, discover_migrations
from learnloop.db.table_roles import TableRole, role_for_table

MIGRATIONS = Path(__file__).resolve().parents[1] / "migrations"
HEAD = Path(__file__).resolve().parents[1] / "fixtures" / "migration_head_242" / "state.sqlite"
#: Every schema object 229 adds (it alters nothing): the earlier migrations' "nothing
#: else changed" diffs on the way to head read these.
C2_ADDED_OBJECTS = frozenset({
    "learner_notes", "sqlite_autoindex_learner_notes_1", "sqlite_autoindex_learner_notes_2",
    "idx_learner_notes_key", "learner_notes_no_update", "learner_notes_no_delete",
    "learner_note_links", "sqlite_autoindex_learner_note_links_1", "idx_learner_note_links_note",
    "idx_learner_note_links_lo", "idx_learner_note_links_reading", "learner_note_links_no_update",
    "learner_note_links_no_delete",
})
TABLES = ("learner_notes", "learner_note_links")


def test_229_is_c2s_migration_classified_with_no_derived_table():
    names = {migration.version: migration.path.name for migration in discover_migrations()}
    assert names[229] == "229_learner_notes.sql"
    for table in TABLES:
        assert role_for_table(table) == TableRole.RAW_LEDGER, table
        assert PT.role(table) == PT.PROTECTED, table
    assert "learner_note_links" in PT.READING
    assert "learner_notes" not in PT.READING  # a snapshot names no reading


def _fresh(tmp_path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(tmp_path / "state.sqlite")
    connection.execute("PRAGMA foreign_keys = ON")
    connection.executescript("CREATE TABLE judgment_ledger (id TEXT PRIMARY KEY);"
                             "INSERT INTO judgment_ledger VALUES ('jl_1');")
    connection.executescript((MIGRATIONS / "229_learner_notes.sql").read_text(encoding="utf-8"))
    return connection


NOTE = ("n1", "/notes/a.org#Eigen", "/notes/a.org", "Eigen", 3, "h1", "a", "Eigen", "2026-10-03", "tend", "text", 0, "t")
NOTE_INSERT = ("INSERT INTO learner_notes (id, note_key, path, heading_path, line, content_hash, title, heading, "
               "captured_on, origin, text_md, truncated, created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)")
LINK_INSERT = ("INSERT INTO learner_note_links (id, note_id, note_key, target_kind, target_key, learning_object_id, "
               "extraction_id, section_id, span_id, goal_id, authorship, status, how, how_line, state_key, ledger_id, "
               "model, prompt_version, created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)")


def test_the_checks_and_the_append_only_triggers(tmp_path):
    with closing(_fresh(tmp_path)) as connection:
        connection.execute(NOTE_INSERT, NOTE)
        with pytest.raises(sqlite3.IntegrityError):  # one snapshot per (note, content hash)
            connection.execute(NOTE_INSERT, ("n2", *NOTE[1:]))
        connection.execute(NOTE_INSERT, ("n3", *NOTE[1:5], "h2", *NOTE[6:]))  # a refreshed snapshot
        for bad in (("n4", *NOTE[1:9], "phone_photo", *NOTE[10:]), ("n5", *NOTE[1:4], 0, "h3", *NOTE[6:])):
            with pytest.raises(sqlite3.IntegrityError):
                connection.execute(NOTE_INSERT, bad)
        ai = ("l1", "n1", NOTE[1], "passage", "passage:e/s/sp", "lo_1", "e", "s", "sp", "g", "ai", "proposed",
              "restates", "It says the same thing.", "k", "jl_1", "m", "v", "t")
        connection.execute(LINK_INSERT, ai)
        learner = ("l2", "n1", NOTE[1], "passage", "passage:e/s/sp", "lo_1", "e", "s", "sp", "g", "learner",
                   "rejected", None, None, None, None, None, None, "t")
        connection.execute(LINK_INSERT, learner)
        by_hand = ("l3", "n1", NOTE[1], "passage", "passage:e//sp", None, "e", None, "sp", None, "learner",
                   "accepted", None, None, None, None, None, None, "t")
        connection.execute(LINK_INSERT, by_hand)
        topic = ("l4", "n1", NOTE[1], "learning_object", "lo:lo_1", "lo_1", "e", "s", "sp", "g", "ai", "proposed",
                 "questions", "It asks why.", "k", "jl_1", "m", "v", "t")
        connection.execute(LINK_INSERT, topic)
        for bad in (
            ("b1", *ai[1:11], "accepted", *ai[12:]),             # the model only proposes
            ("b2", *ai[1:14], None, *ai[15:]),                   # a proposal names its judgment's state
            ("b3", *learner[1:11], "proposed", *learner[12:]),   # the learner links or hides
            ("b4", *ai[1:6], None, None, None, *ai[9:]),         # a passage names its reading
            ("b5", *topic[1:5], None, *topic[6:]),               # an LO link names the LO
            ("b6", "missing", *ai[2:]),                          # the snapshot exists
            ("b7", *ai[1:12], "summarizes", *ai[13:]),           # the how is one of five
        ):
            with pytest.raises(sqlite3.IntegrityError):
                connection.execute(LINK_INSERT, bad)
        for table in TABLES:
            with pytest.raises(sqlite3.IntegrityError, match="append-only"):
                connection.execute(f"UPDATE {table} SET note_key = 'x'")
            with pytest.raises(sqlite3.IntegrityError, match="append-only"):
                connection.execute(f"DELETE FROM {table}")


def test_the_head_fixture_holds_exactly_229s_objects_in_rollback_mode():
    assert HEAD.read_bytes()[18:20] == b"\x01\x01"
    assert max(applied_versions(HEAD)) == max(m.version for m in discover_migrations()) == 242
    with closing(sqlite3.connect(f"file:{HEAD}?mode=ro", uri=True)) as connection:
        names = {row[0] for row in connection.execute("SELECT name FROM sqlite_master")}
        assert C2_ADDED_OBJECTS <= names
        assert connection.execute("PRAGMA journal_mode").fetchone()[0] == "delete"
        for table in TABLES:
            assert connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] == 0


@pytest.mark.durability
def test_229_on_the_durability_lane(tmp_path):
    from learnloop.db.copies import backup_database
    from learnloop.db.migrate import UPGRADE_TEST_HELPER, apply_migrations, upgrade_allowance

    database = tmp_path / "head.sqlite"
    backup_database(HEAD, database)
    with upgrade_allowance(UPGRADE_TEST_HELPER):
        assert apply_migrations(database) == []  # the head is current
    with closing(sqlite3.connect(database)) as connection:
        connection.execute("INSERT INTO judgment_ledger (id, created_at, task, left_kind, left_id, judge, input_hash, "
                           "verdict, rationale, judge_model, prompt_version) VALUES "
                           "('jl_d', 't', 'note_link', 'learning_object', 'lo', 'llm', 'k', 'discusses', '', 'm', 'v')")
        connection.execute(NOTE_INSERT, NOTE)
        connection.execute(LINK_INSERT, ("l1", "n1", NOTE[1], "learning_object", "lo:lo", "lo", None, None, None, None,
                                         "ai", "proposed", "applies", "x", "k", "jl_d", "m", "v", "t"))
        connection.commit()
        assert connection.execute("SELECT COUNT(*) FROM learner_note_links").fetchone()[0] == 1
