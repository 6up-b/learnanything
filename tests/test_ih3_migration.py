"""Instruct hand-off IH3, migration 251 (docs/specs/spec_instruct_handoff_v1.md §6): ``router_learner_preferences``.

One new RAW_LEDGER table, append-only by two triggers; no existing object changes. A vault at 250 gains exactly the table, its
three indexes and its two triggers, and every row it already held is as it was. The number is the migration's file name alone:
this file reads it from the migration (``MIGRATION``) so a renumbering at landing moves one line.
"""

from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path

import pytest

from learnloop.db.migrate import UPGRADE_TEST_HELPER, applied_versions, apply_migrations, discover_migrations, upgrade_allowance
from learnloop.db.table_roles import TABLE_ROLES, TableRole

HEAD = Path(__file__).resolve().parents[1] / "fixtures" / "migration_head_252" / "state.sqlite"
TABLE = "router_learner_preferences"
MIGRATION = next(m for m in discover_migrations() if m.name == "router_learner_preferences")
OBJECTS = frozenset({TABLE, "router_learner_preferences_decision", "router_learner_preferences_session",
                     "router_learner_preferences_served", "router_learner_preferences_no_update",
                     "router_learner_preferences_no_delete"})
#: What 251 adds (with the table's own autoindex): earlier migrations' "nothing else changed" diffs on the way to head read this.
IH3_ADDED_OBJECTS = OBJECTS | {f"sqlite_autoindex_{TABLE}_1"}
COLUMNS = ["id", "decision_id", "attempt_id", "session_id", "surface", "offered_json", "chosen_kind", "chosen_ref", "note_md",
           "served_decision_id", "algorithm_version", "created_at"]


def test_the_migration_is_the_head_and_the_table_is_a_raw_ledger():
    # RE0's 252 (practice_attempts.active_seconds) is the head since its landing.
    assert MIGRATION.version == 251 and max(m.version for m in discover_migrations()) == 252
    assert TABLE_ROLES[TABLE] is TableRole.RAW_LEDGER


def test_the_head_fixture_holds_it_in_rollback_mode():
    assert HEAD.read_bytes()[18:20] == b"\x01\x01"
    assert MIGRATION.version in applied_versions(HEAD) and max(applied_versions(HEAD)) == 252
    with closing(sqlite3.connect(f"file:{HEAD}?mode=ro", uri=True)) as connection:
        assert [row[1] for row in connection.execute(f"PRAGMA table_info({TABLE})")] == COLUMNS
        assert connection.execute(f"SELECT COUNT(*) FROM {TABLE}").fetchone()[0] == 0


def _downgraded(database: Path) -> None:
    with closing(sqlite3.connect(HEAD)) as source, closing(sqlite3.connect(database)) as target:
        source.backup(target)
    with closing(sqlite3.connect(database)) as connection:
        connection.execute(f"DROP TABLE {TABLE}")  # its indexes and triggers go with it
        connection.execute("DELETE FROM schema_migrations WHERE version = ?", (MIGRATION.version,))
        connection.commit()


def test_it_adds_the_table_its_indexes_and_triggers_and_nothing_else(tmp_path):
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
    assert set(after) - set(before) == IH3_ADDED_OBJECTS
    assert {name for name in before if before[name] != after[name]} == set()


def _row(connection: sqlite3.Connection, ident: str = "p1", **overrides) -> None:
    row = {"id": ident, "decision_id": None, "attempt_id": None, "session_id": "s1", "surface": "feedback",
           "offered_json": "{}", "chosen_kind": "new", "chosen_ref": "cand", "note_md": None, "served_decision_id": None,
           "algorithm_version": "mvp-0.55", "created_at": "2026-11-08T12:00:00Z", **overrides}
    connection.execute(f"INSERT INTO {TABLE} ({','.join(row)}) VALUES ({','.join('?' for _ in row)})", tuple(row.values()))


def test_the_ledger_refuses_update_delete_bad_json_and_a_missing_decision(tmp_path):
    database = tmp_path / "state.sqlite"
    with closing(sqlite3.connect(HEAD)) as source, closing(sqlite3.connect(database)) as target:
        source.backup(target)
    with closing(sqlite3.connect(database)) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        _row(connection)  # no decision: a preference with no draw is a null decision_id
        connection.commit()
        with pytest.raises(sqlite3.DatabaseError, match="append-only"):
            connection.execute(f"UPDATE {TABLE} SET note_md = 'edited'")
        with pytest.raises(sqlite3.DatabaseError, match="append-only"):
            connection.execute(f"DELETE FROM {TABLE}")
        with pytest.raises(sqlite3.IntegrityError):
            _row(connection, "p2", offered_json="not json")
        with pytest.raises(sqlite3.IntegrityError):
            _row(connection, "p3", decision_id="no_such_decision")
        with pytest.raises(sqlite3.IntegrityError):
            _row(connection, "p1")  # the id is the act's own key
        assert connection.execute(f"SELECT COUNT(*) FROM {TABLE}").fetchone()[0] == 1


@pytest.mark.durability
def test_it_applies_under_production_pragmas(tmp_path):
    database = tmp_path / "state.sqlite"
    _downgraded(database)
    with upgrade_allowance(UPGRADE_TEST_HELPER):
        assert [m.version for m in apply_migrations(database)] == [MIGRATION.version]
    assert MIGRATION.version in applied_versions(database) and max(applied_versions(database)) == 252
