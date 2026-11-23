"""The Reader workbench v2 RD0 migration (spec §15.1): ten new tables, each classified, the two DERIVED
ones with one replayer each, the ledgers append-only by trigger; nothing else changes and nothing is
backfilled. The number is the migration's file name alone (``MIGRATION``)."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path

import pytest

from learnloop.adaptive_difficulty.protected_tables import ROLES as AD_ROLES
from learnloop.db.migrate import UPGRADE_TEST_HELPER, applied_versions, apply_migrations, discover_migrations, upgrade_allowance
from learnloop.db.table_roles import TABLE_ROLES
from learnloop.substrate.rebuild_orchestrator import derived_table_owners
from tests.helpers import MIGRATION_HEAD_FIXTURE
from tests.reader_rd0_migration_helpers import RD0_ADDED_OBJECTS, TABLES

HEAD = MIGRATION_HEAD_FIXTURE / "state.sqlite"
MIGRATION = next(m for m in discover_migrations() if m.name == "reader_workbench_foundations")


def test_every_table_has_the_specs_role_and_each_derived_one_a_single_replayer():
    assert {table: TABLE_ROLES[table].value for table in TABLES} == TABLES
    owners = derived_table_owners()
    assert owners["question_event_spans"] == ("question_event_spans",)
    assert owners["learner_text_gap_spans"] == ("learner_text_gap_spans",)
    # Unclassified for adaptive difficulty: an AD operation cannot read them at all.
    assert not set(TABLES) & set(AD_ROLES)


def test_the_head_fixture_holds_them_empty_in_rollback_mode():
    assert HEAD.read_bytes()[18:20] == b"\x01\x01"
    assert MIGRATION.version in applied_versions(HEAD)
    with closing(sqlite3.connect(f"file:{HEAD}?mode=ro", uri=True)) as connection:
        for table in TABLES:
            assert connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] == 0, table


def _downgraded(database: Path) -> None:
    with closing(sqlite3.connect(HEAD)) as source, closing(sqlite3.connect(database)) as target:
        source.backup(target)
    with closing(sqlite3.connect(database)) as connection:
        # Children before parents; a dropped table takes its indexes and triggers with it.
        for table in reversed(list(TABLES)):
            connection.execute(f"DROP TABLE {table}")
        connection.execute("DELETE FROM schema_migrations WHERE version = ?", (MIGRATION.version,))
        connection.commit()


def _rows(connection: sqlite3.Connection, table: str) -> list[tuple]:
    return sorted(tuple(row) for row in connection.execute(f"SELECT * FROM {table}"))


def test_it_adds_the_tables_and_changes_nothing_else(tmp_path):
    database = tmp_path / "state.sqlite"
    _downgraded(database)
    with closing(sqlite3.connect(database)) as connection:
        before = {row[0]: row[1] for row in connection.execute("SELECT name, sql FROM sqlite_master")}
        kept = {table: _rows(connection, table) for table in ("question_events", "learner_text_gaps",
                                                              "interaction_events")}
    with upgrade_allowance(UPGRADE_TEST_HELPER):
        assert [m.version for m in apply_migrations(database)] == [MIGRATION.version]
    with closing(sqlite3.connect(database)) as connection:
        after = {row[0]: row[1] for row in connection.execute("SELECT name, sql FROM sqlite_master")}
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        assert {table: _rows(connection, table) for table in kept} == kept
    assert set(after) - set(before) == RD0_ADDED_OBJECTS
    assert {name for name in before if before[name] != after[name]} == set()


def _upgraded(tmp_path: Path) -> sqlite3.Connection:
    database = tmp_path / "state.sqlite"
    _downgraded(database)
    with upgrade_allowance(UPGRADE_TEST_HELPER):
        apply_migrations(database)
    return sqlite3.connect(database)


@pytest.mark.parametrize("table", ["pad_block_versions", "pad_block_anchors", "companion_exchange_context",
                                   "desk_op_receipts", "pad_op_receipts"])
def test_the_ledgers_and_receipts_refuse_update_and_delete(tmp_path, table):
    with closing(_upgraded(tmp_path)) as connection:
        connection.execute("INSERT INTO pads (pad_id, kind, created_at, updated_at) VALUES ('p', 'named', 't', 't')")
        rows = {
            "pad_block_versions": "INSERT INTO pad_block_versions (version_id, block_id, pad_id, position_key, kind, "
                                  "provenance, created_at) VALUES ('v1', 'b', 'p', 'a0', 'text', 'learner', 't')",
            "pad_block_anchors": "INSERT INTO pad_block_anchors (event_id, block_id, extraction_id, span_id, action, "
                                 "created_at) VALUES ('e', 'b', 'x', 's', 'link', 't')",
            "companion_exchange_context": "INSERT INTO companion_exchange_context (question_event_id, surface, origin, "
                                          "created_at) VALUES ('q', 'reader', 'live', 't')",
            "desk_op_receipts": "INSERT INTO desk_op_receipts (client_id, seq, request_hash, result_json, applied_at) "
                                "VALUES ('c', 1, 'h', '{}', 't')",
            "pad_op_receipts": "INSERT INTO pad_op_receipts (client_id, seq, pad_id, request_hash, result_json, "
                               "applied_at) VALUES ('c', 1, 'p', 'h', '{}', 't')",
        }
        connection.execute(rows[table])
        connection.commit()
        column = {"pad_block_versions": "body_md", "pad_block_anchors": "action", "companion_exchange_context": "surface",
                  "desk_op_receipts": "result_json", "pad_op_receipts": "result_json"}[table]
        with pytest.raises(sqlite3.IntegrityError, match="append-only"):
            connection.execute(f"UPDATE {table} SET {column} = {column}")
        with pytest.raises(sqlite3.IntegrityError, match="append-only"):
            connection.execute(f"DELETE FROM {table}")


def test_a_block_has_one_chain_no_second_child_and_no_second_root(tmp_path):
    with closing(_upgraded(tmp_path)) as connection:
        connection.execute("INSERT INTO pads (pad_id, kind, created_at, updated_at) VALUES ('p', 'named', 't', 't')")
        insert = ("INSERT INTO pad_block_versions (version_id, block_id, supersedes_id, pad_id, position_key, kind, "
                  "provenance, created_at) VALUES (?, ?, ?, 'p', 'a0', 'text', 'learner', 't')")
        connection.execute(insert, ("v1", "b", None))
        connection.execute(insert, ("v2", "b", "v1"))
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(insert, ("v3", "b", "v1"))  # a second child of v1: a branching head
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(insert, ("v4", "b", None))  # a second first version of the same block
        with pytest.raises(sqlite3.IntegrityError, match="another block"):
            connection.execute(insert, ("v5", "other", "v2"))  # continuing another block's chain
