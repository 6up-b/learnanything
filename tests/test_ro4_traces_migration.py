"""Router objective RO4, migration 246: ``router_objective_traces`` (spec_router_objective_v1 §8.8).

One append-only RECEIPT table, empty at the head; it changes nothing else.
"""

from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path

import pytest

from learnloop.db.migrate import UPGRADE_TEST_HELPER, applied_versions, apply_migrations, discover_migrations, upgrade_allowance
from learnloop.db.table_roles import TABLE_ROLES, TableRole

HEAD = Path(__file__).resolve().parents[1] / "fixtures" / "migration_head_252" / "state.sqlite"
TABLE = "router_objective_traces"
#: What 246 adds: earlier migrations' "nothing else changed" diffs on the way to head read this.
RO4_ADDED_OBJECTS = frozenset({
    TABLE, "idx_router_objective_traces_local_date", "idx_router_objective_traces_created", f"{TABLE}_no_update",
    f"{TABLE}_no_delete", f"sqlite_autoindex_{TABLE}_1", f"sqlite_autoindex_{TABLE}_2",
})
#: What 246 rebuilds: the goal contract versions widen their change class by 'use_weight_change'.
RO4_ALTERED_TABLE = "goal_contract_versions"
_ROW = ("INSERT INTO router_objective_traces(id, decision_id, decision_kind, trace_version, objective_version, "
        "algorithm_version, local_date, chosen_ref, stop_in_support, trace_json, content_hash, created_at) "
        "VALUES (?, ?, 'plan_block', 'v', 'o', 'mvp-0.47', '2026-11-05', 'c', 1, '{}', 'h', 't')")


def test_246_is_the_head_and_its_table_a_receipt():
    names = {migration.version: migration.path.name for migration in discover_migrations()}
    assert names[246] == "246_router_objective_traces.sql" and max(names) == 252
    assert TABLE_ROLES[TABLE] is TableRole.RECEIPT


def test_the_head_fixture_holds_246_in_rollback_mode_with_an_empty_table():
    assert HEAD.read_bytes()[18:20] == b"\x01\x01"
    assert max(applied_versions(HEAD)) == 252
    with closing(sqlite3.connect(HEAD)) as connection:
        names = {row[0] for row in connection.execute("SELECT name FROM sqlite_master")}
        assert RO4_ADDED_OBJECTS <= names
        assert connection.execute(f"SELECT COUNT(*) FROM {TABLE}").fetchone()[0] == 0


def _downgraded(database: Path) -> None:
    with closing(sqlite3.connect(HEAD)) as source, closing(sqlite3.connect(database)) as target:
        source.backup(target)
    with closing(sqlite3.connect(database)) as connection:
        connection.execute(f"DROP TABLE {TABLE}")
        # The contract versions' table as 245 left it (the CHECK without the new class).
        sql = connection.execute("SELECT sql FROM sqlite_master WHERE name = ?", (RO4_ALTERED_TABLE,)).fetchone()[0]
        connection.execute("PRAGMA writable_schema = ON")
        connection.execute("UPDATE sqlite_master SET sql = ? WHERE name = ?",
                           (sql.replace("'reweight', 'use_weight_change', 'metadata'", "'reweight', 'metadata'"),
                            RO4_ALTERED_TABLE))
        connection.execute("PRAGMA writable_schema = OFF")
        connection.execute("DELETE FROM schema_migrations WHERE version = 246")
        connection.commit()


def test_246_widens_the_contract_change_class_keeping_every_row(tmp_path):
    database = tmp_path / "state.sqlite"
    _downgraded(database)
    with closing(sqlite3.connect(database)) as connection:
        connection.execute(
            "INSERT INTO goal_contract_versions(id, goal_id, version, contract_json, content_hash, support_hash, "
            "contract_schema_version, change_class, author, created_at) VALUES ('v1', 'g', 1, '{}', 'h', 's', 1, "
            "'confirm', 'learner', 't')")
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                "INSERT INTO goal_contract_versions(id, goal_id, version, contract_json, content_hash, support_hash, "
                "contract_schema_version, change_class, author, created_at) VALUES ('v2', 'g', 2, '{}', 'h2', 's', 1, "
                "'use_weight_change', 'learner', 't')")
        connection.commit()
    with upgrade_allowance(UPGRADE_TEST_HELPER):
        apply_migrations(database)
    with closing(sqlite3.connect(database)) as connection:
        assert connection.execute("SELECT id, change_class FROM goal_contract_versions").fetchall() == [("v1", "confirm")]
        connection.execute(
            "INSERT INTO goal_contract_versions(id, goal_id, version, predecessor_version_id, contract_json, "
            "content_hash, support_hash, contract_schema_version, change_class, author, created_at) VALUES "
            "('v2', 'g', 2, 'v1', '{}', 'h2', 's', 1, 'use_weight_change', 'learner', 't')")
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []


def test_246_adds_exactly_its_objects_and_the_table_is_append_only(tmp_path):
    database = tmp_path / "state.sqlite"
    _downgraded(database)
    with closing(sqlite3.connect(database)) as connection:
        before = {row[0]: row[1] for row in connection.execute("SELECT name, sql FROM sqlite_master")}
    with upgrade_allowance(UPGRADE_TEST_HELPER):
        assert [migration.version for migration in apply_migrations(database)] == [246]
    with closing(sqlite3.connect(database)) as connection:
        after = {row[0]: row[1] for row in connection.execute("SELECT name, sql FROM sqlite_master")}
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert set(after) - set(before) == RO4_ADDED_OBJECTS
        # The contract versions' table is rebuilt (§8.5) with one more change class and nothing else.
        changed = {name for name in before if after.get(name) != before[name]}
        assert changed == {RO4_ALTERED_TABLE}
        assert after[RO4_ALTERED_TABLE] == before[RO4_ALTERED_TABLE].replace(
            "'evaluation_change', 'reweight', 'metadata'", "'evaluation_change', 'reweight', 'use_weight_change', 'metadata'")
        connection.execute(_ROW, ("t1", "d1"))
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(f"UPDATE {TABLE} SET chosen_ref = 'x'")
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(f"DELETE FROM {TABLE}")
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(_ROW, ("t2", "d1"))  # one trace per decision
