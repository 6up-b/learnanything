"""Adaptive hints H1's migration 211: ``approach_maps`` (spec_adaptive_hints_v1 §9, G-H13).

The 210 -> 211 upgrade adds the table, its two indexes and its two triggers
and nothing else; rows are immutable (a new version is a new row) and never
deleted; one row per item revision and seeds and per item version; the table
is WORKFLOW (paid output, no replayer); the head fixture is at 211 in
rollback mode; the durability lane runs the same upgrade under WAL.
"""
from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path

import pytest

from learnloop.db.connection import connect
from learnloop.db.migrate import UPGRADE_TEST_HELPER, apply_migrations, applied_versions, discover_migrations, \
    upgrade_allowance
from learnloop.db.stores import approach_maps as store
from learnloop.db.table_roles import TableRole, role_for_table
from tests.test_ad1_migration import AD1_ADDED_OBJECTS, AD1_ALTERED_TABLES
from tests.test_ad23_migration import AD23_ADDED_OBJECTS
from tests.test_figures_migration import RW5A_ADDED_OBJECTS
from tests.test_reader_rw3b_migration import RW3B_ADDED_OBJECTS
from tests.test_reader_rw7a_migration import RW7A_ADDED_OBJECTS
from tests.test_t1_batch_origin_migration import T1_ALTERED_TABLES
from tests.test_rw2d_receipts_migration import RW2D_ADDED_OBJECTS, RW2D_ALTERED_TABLES
from tests.test_retrieval_spaces_migration import P1_ADDED_OBJECTS
from tests.test_section_coverage_migration import C0A_ADDED_OBJECTS

HEAD = Path(__file__).resolve().parents[1] / "fixtures" / "migration_head_222" / "state.sqlite"
NOW = "2026-10-18T09:00:00Z"
#: §9's columns, plus the revision keys and the trigger H1 adds.
SPEC_COLUMNS = {"id", "practice_item_id", "practice_item_hash", "family_id", "version", "map_json", "seeds_json",
                "validation_json", "verified_goal", "model", "prompt_version", "input_hash", "created_at",
                "supersedes_id"}
H1_COLUMNS = {"seeds_hash", "structure_hash", "trigger"}


def _database_at_210(tmp_path: Path) -> Path:
    through = tmp_path / "through_210"
    through.mkdir()
    for migration in discover_migrations():
        if migration.version <= 210:
            (through / migration.path.name).write_text(migration.path.read_text(encoding="utf-8"), encoding="utf-8")
    database = tmp_path / "state.sqlite"
    apply_migrations(database, migrations_dir=through)
    assert max(applied_versions(database)) == 210
    return database


def _schema(database: Path) -> dict[str, str]:
    with closing(sqlite3.connect(database)) as connection:
        return {name: sql for name, sql in connection.execute(
            "SELECT name, sql FROM sqlite_master WHERE sql IS NOT NULL AND name NOT LIKE 'sqlite_%'")}


def _upgrade(tmp_path: Path) -> Path:
    database = _database_at_210(tmp_path)
    before = _schema(database)
    with upgrade_allowance(UPGRADE_TEST_HELPER):
        applied = apply_migrations(database)
    # Later migrations (adaptive hints H2b's 212) follow 211 on the way to head.
    assert [migration.version for migration in applied][0] == 211
    after = _schema(database)
    # Adaptive difficulty AD1's 213 (its receipts) follows on the way to head.
    # ... and adaptive difficulty's 214, Reader RW3b's 215, RW5a's 216 and RW7a's 217 (their two tables each), RW2d's 219 and local retrieval P1's 220.
    assert set(after) - set(before) - AD1_ADDED_OBJECTS - AD23_ADDED_OBJECTS - RW3B_ADDED_OBJECTS - RW5A_ADDED_OBJECTS - RW7A_ADDED_OBJECTS - RW2D_ADDED_OBJECTS - P1_ADDED_OBJECTS - C0A_ADDED_OBJECTS == {"approach_maps", "idx_approach_maps_item", "idx_approach_maps_family",
                                        "approach_maps_no_update", "approach_maps_no_delete"}
    # 212 rebuilds the two learner-text tables (their source_kind CHECK only).
    # Adaptive difficulty AD1's 213 adds two practice_attempts columns on the way.
    assert {name: sql for name, sql in after.items()
            if name in before and not name.startswith("learner_text_gap") and name not in AD1_ALTERED_TABLES | T1_ALTERED_TABLES | RW2D_ALTERED_TABLES} \
        == {name: sql for name, sql in before.items()
            if not name.startswith("learner_text_gap") and name not in AD1_ALTERED_TABLES | T1_ALTERED_TABLES | RW2D_ALTERED_TABLES}  # nothing else changed
    return database


def _row(map_id: str, **columns) -> dict:
    return {"id": map_id, "practice_item_id": "pi_1", "practice_item_hash": "h1", "family_id": None, "version": 1,
            "map_json": "{}", "seeds_json": "{}", "seeds_hash": "s1", "structure_hash": "t1",
            "validation_json": "{}", "verified_goal": 0, "trigger": "cli", "model": "m", "prompt_version": "v",
            "input_hash": "i", "created_at": NOW, "supersedes_id": None, **columns}


def _check(database: Path) -> None:
    with closing(connect(database)) as connection:
        columns = [row[1] for row in connection.execute("PRAGMA table_info(approach_maps)")]
        assert tuple(columns) == store.COLUMNS and set(columns) == SPEC_COLUMNS | H1_COLUMNS
        store.insert_map(connection, _row("am_1"))
        store.insert_map(connection, _row("am_2", version=2, seeds_hash="s2", supersedes_id="am_1"))
        assert store.next_version(connection, "pi_1") == (3, "am_2")
        for bad in (_row("am_x", version=2, seeds_hash="s9"),  # the version is taken
                    _row("am_y", version=3, seeds_hash="s1"),  # this revision and seeds are stored
                    _row("am_z", version=3, seeds_hash="s3", trigger="replay"),
                    _row("am_w", version=3, seeds_hash="s4", verified_goal=2),
                    _row("am_v", version=0, seeds_hash="s5"),
                    _row("am_u", version=3, seeds_hash="s6", supersedes_id="am_u"),
                    _row("am_t", version=3, seeds_hash="s7", supersedes_id="am_missing")):
            with pytest.raises(sqlite3.IntegrityError):
                store.insert_map(connection, bad)
        for statement in ("UPDATE approach_maps SET map_json = '{\"x\": 1}' WHERE id = 'am_1'",
                          "UPDATE approach_maps SET supersedes_id = NULL WHERE id = 'am_2'",
                          "DELETE FROM approach_maps WHERE id = 'am_1'"):
            with pytest.raises(sqlite3.IntegrityError):
                connection.execute(statement)
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        connection.commit()
        assert store.latest_map(connection, "pi_1")["id"] == "am_2"
        assert store.current_map(connection, "pi_1", practice_item_hash="h1", structure_hash="t1")["id"] == "am_2"
        assert store.map_exists(connection, "am_1") and not store.map_exists(connection, "am_9")


def test_211_adds_approach_maps_and_nothing_else(tmp_path):
    _check(_upgrade(tmp_path))


@pytest.mark.durability
def test_211_on_the_durability_lane(tmp_path):
    database = _upgrade(tmp_path)
    with closing(sqlite3.connect(database)) as connection:
        assert connection.execute("PRAGMA journal_mode").fetchone()[0] == "wal"
    _check(database)


def test_the_head_fixture_carries_the_empty_table(tmp_path):
    from learnloop.db.copies import backup_database

    database = tmp_path / "head.sqlite"
    backup_database(HEAD, database)
    with closing(sqlite3.connect(database)) as connection:
        assert connection.execute("SELECT COUNT(*) FROM approach_maps").fetchone()[0] == 0
    _check(database)


def test_approach_maps_is_workflow():
    assert role_for_table("approach_maps") is TableRole.WORKFLOW


def test_the_store_refuses_unknown_columns(tmp_path):
    from learnloop.db.copies import backup_database

    database = tmp_path / "head.sqlite"
    backup_database(HEAD, database)
    with closing(connect(database)) as connection:
        with pytest.raises(ValueError, match="routes"):
            store.insert_map(connection, {**_row("am_1"), "routes": "[]"})


def test_the_head_fixture_is_at_head_in_rollback_mode():
    assert HEAD.read_bytes()[18:20] == b"\x01\x01"
    assert max(applied_versions(HEAD)) == max(m.version for m in discover_migrations()) == 222
    for suffix in ("-wal", "-shm", "-journal"):
        assert not HEAD.with_name(HEAD.name + suffix).exists()
