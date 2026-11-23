"""The Reader workbench v2 guards migration: replacing inserts refused on the append-only tables, the
projections' one-time initialization receipts, and the index that makes one exchange's lookup a probe.
Nothing else changes and nothing is backfilled. The number is the file name alone (``MIGRATION``)."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path

import pytest

from learnloop.db.migrate import UPGRADE_TEST_HELPER, applied_versions, apply_migrations, discover_migrations, upgrade_allowance
from learnloop.db.table_roles import TABLE_ROLES, TableRole
from learnloop.substrate.passage_spans import READER_ANSWER_QUESTION_KEY
from tests.helpers import MIGRATION_HEAD_FIXTURE
from tests.reader_rd0_guards_migration_helpers import GUARDS, INDEX, INITIALIZATIONS, RD0_GUARDS_ADDED_OBJECTS

HEAD = MIGRATION_HEAD_FIXTURE / "state.sqlite"
MIGRATION = next(m for m in discover_migrations() if m.name == "reader_workbench_guards")


def test_the_receipt_table_is_a_receipt_and_the_head_fixture_holds_it_empty():
    assert TABLE_ROLES[INITIALIZATIONS] is TableRole.RECEIPT
    assert HEAD.read_bytes()[18:20] == b"\x01\x01"
    assert MIGRATION.version in applied_versions(HEAD)
    with closing(sqlite3.connect(f"file:{HEAD}?mode=ro", uri=True)) as connection:
        assert connection.execute(f"SELECT COUNT(*) FROM {INITIALIZATIONS}").fetchone()[0] == 0


def _downgraded(database: Path) -> None:
    with closing(sqlite3.connect(HEAD)) as source, closing(sqlite3.connect(database)) as target:
        source.backup(target)
    with closing(sqlite3.connect(database)) as connection:
        for trigger in GUARDS:
            connection.execute(f"DROP TRIGGER {trigger}")
        connection.execute(f"DROP INDEX {INDEX}")
        connection.execute(f"DROP TABLE {INITIALIZATIONS}")
        connection.execute("DELETE FROM schema_migrations WHERE version = ?", (MIGRATION.version,))
        connection.commit()


def _upgraded(tmp_path: Path) -> sqlite3.Connection:
    database = tmp_path / "state.sqlite"
    _downgraded(database)
    with upgrade_allowance(UPGRADE_TEST_HELPER):
        assert [m.version for m in apply_migrations(database)] == [MIGRATION.version]
    return sqlite3.connect(database)


def test_it_adds_its_objects_and_changes_nothing_else(tmp_path):
    database = tmp_path / "state.sqlite"
    _downgraded(database)
    with closing(sqlite3.connect(database)) as connection:
        before = {row[0]: row[1] for row in connection.execute("SELECT name, sql FROM sqlite_master")}
    with upgrade_allowance(UPGRADE_TEST_HELPER):
        assert [m.version for m in apply_migrations(database)] == [MIGRATION.version]
    with closing(sqlite3.connect(database)) as connection:
        after = {row[0]: row[1] for row in connection.execute("SELECT name, sql FROM sqlite_master")}
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
    assert set(after) - set(before) == RD0_GUARDS_ADDED_OBJECTS
    assert {name for name in before if before[name] != after[name]} == set()


REPLACING = {
    "desk_op_receipts": ("INSERT INTO desk_op_receipts VALUES ('c', 1, 'h', '{}', 't')",
                         "INSERT OR REPLACE INTO desk_op_receipts VALUES ('c', 1, 'other', '{}', 't2')"),
    "pad_op_receipts": ("INSERT INTO pad_op_receipts VALUES ('c', 1, 'p', 'h', '{}', 't')",
                        "INSERT OR REPLACE INTO pad_op_receipts VALUES ('c', 1, 'p', 'other', '{}', 't2')"),
    "pad_block_anchors": ("INSERT INTO pad_block_anchors (event_id, block_id, extraction_id, span_id, action, created_at)"
                          " VALUES ('e', 'b', 'x', 's', 'link', 't')",
                          "INSERT OR REPLACE INTO pad_block_anchors (event_id, block_id, extraction_id, span_id, action, "
                          "created_at) VALUES ('e', 'b', 'x', 's', 'unlink', 't2')"),
    "companion_exchange_context": ("INSERT INTO companion_exchange_context (question_event_id, surface, origin, "
                                   "created_at) VALUES ('q', 'reader', 'live', 't')",
                                   "INSERT OR REPLACE INTO companion_exchange_context (question_event_id, surface, "
                                   "origin, created_at) VALUES ('q', 'desk', 'live', 't2')"),
    "projection_initializations": ("INSERT INTO projection_initializations VALUES ('question_event_spans', 1, 1, 't')",
                                   "INSERT OR REPLACE INTO projection_initializations VALUES "
                                   "('question_event_spans', 0, 0, 't2')"),
}


@pytest.mark.parametrize("table", sorted(REPLACING))
def test_a_replacing_insert_is_refused_and_the_row_stays(tmp_path, table):
    first, replacing = REPLACING[table]
    with closing(_upgraded(tmp_path)) as connection:
        connection.execute(first)
        connection.commit()
        before = connection.execute(f"SELECT * FROM {table}").fetchall()
        with pytest.raises(sqlite3.IntegrityError, match="append-only"):
            connection.execute(replacing)
        assert connection.execute(f"SELECT * FROM {table}").fetchall() == before


def test_a_replacing_insert_cannot_rewrite_a_blocks_chain(tmp_path):
    with closing(_upgraded(tmp_path)) as connection:
        connection.execute("INSERT INTO pads (pad_id, kind, created_at, updated_at) VALUES ('p', 'named', 't', 't')")
        insert = ("INSERT OR REPLACE INTO pad_block_versions (version_id, block_id, supersedes_id, pad_id, position_key, "
                  "kind, body_md, provenance, created_at) VALUES (?, 'b', ?, 'p', 'a0', 'text', ?, 'learner', 't')")
        connection.execute(insert, ("v1", None, "first"))
        connection.execute(insert, ("v2", "v1", "second"))
        connection.commit()
        for attempt in (("v1", None, "rewritten"), ("v9", None, "a second root"), ("v8", "v1", "a second child")):
            with pytest.raises(sqlite3.IntegrityError, match="append-only"):
                connection.execute(insert, attempt)
        assert connection.execute("SELECT version_id, body_md FROM pad_block_versions ORDER BY version_id").fetchall() == [
            ("v1", "first"), ("v2", "second")]


def test_one_exchanges_answer_lookup_uses_the_index(tmp_path):
    with closing(_upgraded(tmp_path)) as connection:
        plan = connection.execute(
            "EXPLAIN QUERY PLAN SELECT subject_id, payload_json, created_at, id FROM interaction_events WHERE kind = "
            f"'reader_answer_submitted' AND {READER_ANSWER_QUESTION_KEY} IN (?)", ("q",)).fetchall()
    assert any(INDEX in str(row[-1]) for row in plan), plan
