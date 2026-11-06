"""Router objective RO2, migration 245: ``ad_history_forecast_draws`` (spec_router_objective_v1 §6.3).

One append-only RECEIPT table, empty at the head; it changes nothing else. AD's guard classifies it
(PROTECTED, with its epoch rule) and AD may write it.
"""

from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path

import pytest

from learnloop.adaptive_difficulty import column_classes as C
from learnloop.adaptive_difficulty import protected_tables as T
from learnloop.db.migrate import UPGRADE_TEST_HELPER, applied_versions, apply_migrations, discover_migrations, upgrade_allowance
from learnloop.db.table_roles import TABLE_ROLES, TableRole

HEAD = Path(__file__).resolve().parents[1] / "fixtures" / "migration_head_248" / "state.sqlite"
TABLE = "ad_history_forecast_draws"
#: What 245 adds: earlier migrations' "nothing else changed" diffs on the way to head read this.
RO2_ADDED_OBJECTS = frozenset({
    TABLE, "idx_ad_history_forecast_draws_presentation", f"{TABLE}_no_update", f"{TABLE}_no_delete",
    f"sqlite_autoindex_{TABLE}_1", f"sqlite_autoindex_{TABLE}_2",
})


def test_245_is_the_head_and_its_table_a_receipt_ad_classifies():
    names = {migration.version: migration.path.name for migration in discover_migrations()}
    assert names[245] == "245_history_forecaster.sql" and max(names) == 248
    assert TABLE_ROLES[TABLE] is TableRole.RECEIPT
    assert T.ROLES[TABLE] == T.PROTECTED and TABLE in T.AD_WRITABLE and TABLE in T.EPOCH
    assert T.ROLES["help_assists"] == T.PROTECTED and "help_assists" in C.CLASSES


def test_the_head_fixture_holds_245_in_rollback_mode_with_an_empty_table():
    assert HEAD.read_bytes()[18:20] == b"\x01\x01"
    assert max(applied_versions(HEAD)) == 248
    with closing(sqlite3.connect(HEAD)) as connection:
        names = {row[0] for row in connection.execute("SELECT name FROM sqlite_master")}
        assert RO2_ADDED_OBJECTS <= names
        assert connection.execute(f"SELECT COUNT(*) FROM {TABLE}").fetchone()[0] == 0


def _downgraded(database: Path) -> None:
    with closing(sqlite3.connect(HEAD)) as source, closing(sqlite3.connect(database)) as target:
        source.backup(target)
    with closing(sqlite3.connect(database)) as connection:
        connection.execute(f"DROP TABLE {TABLE}")
        connection.execute("DELETE FROM schema_migrations WHERE version = 245")
        connection.commit()


def test_245_adds_exactly_its_objects_and_the_table_is_append_only(tmp_path):
    database = tmp_path / "state.sqlite"
    _downgraded(database)
    with closing(sqlite3.connect(database)) as connection:
        before = {row[0]: row[1] for row in connection.execute("SELECT name, sql FROM sqlite_master")}
    with upgrade_allowance(UPGRADE_TEST_HELPER):
        assert [migration.version for migration in apply_migrations(database)] == [245]
    with closing(sqlite3.connect(database)) as connection:
        after = {row[0]: row[1] for row in connection.execute("SELECT name, sql FROM sqlite_master")}
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert set(after) - set(before) == RO2_ADDED_OBJECTS
        assert {name: sql for name, sql in after.items() if name in before} == before
        connection.execute(
            f"INSERT INTO {TABLE}(id, draw_key, plan_presentation_id, practice_item_id, draw_version, seed, u, "
            "anchor_rung, drawn_rung, propensity, propensities_json, card_version, frozen_json, served_at, created_at) "
            "VALUES ('d1', 'k', 'pp', 'pi', 'v', 's', 0.5, 'H3', 'H1', 0.3333, '{}', 'c', '{}', 't', 't')")
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(f"UPDATE {TABLE} SET u = 0.1")
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(f"DELETE FROM {TABLE}")
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                f"INSERT INTO {TABLE}(id, draw_key, plan_presentation_id, practice_item_id, draw_version, seed, u, "
                "anchor_rung, drawn_rung, propensity, propensities_json, card_version, frozen_json, served_at, "
                "created_at) VALUES ('d2', 'k2', 'pp', 'pi', 'v', 's', 0.5, 'H3', 'H3', 0.3, '{}', 'c', '{}', 't', 't')")


@pytest.mark.durability
def test_245_on_the_durability_lane(tmp_path):
    database = tmp_path / "state.sqlite"
    _downgraded(database)
    with upgrade_allowance(UPGRADE_TEST_HELPER):
        assert [migration.version for migration in apply_migrations(database)] == [245]
    with closing(sqlite3.connect(database)) as connection:
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
