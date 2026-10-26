"""Reader RW7a's migration 217 (spec_reader_workbench_v1 §10.1, §11): ``reader_path_sections`` and ``reader_path_depths``.

The 215 -> 217 upgrade (AD2+AD3 holds 214 on its own branch, and RW5a's 216
lands on the way; the runner has no contiguity rule) adds the two tables with every
column §10.1 names, their indexes and append-only triggers, and alters
nothing else. Both are WORKFLOW (paid outputs and the learner's choices,
never re-run on rebuild, read by no replay). A judge row cites its
``judgment_ledger`` verdict and is unique per (reading, depth, state, section);
overrides are rows of their own. The durability lane runs the upgrade with
production pragmas.
"""

from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path

import pytest

from learnloop.db.connection import connect
from learnloop.db.migrate import (
    UPGRADE_TEST_HELPER,
    applied_versions,
    apply_migrations,
    discover_migrations,
    upgrade_allowance,
)
from learnloop.db.table_roles import TableRole, role_for_table
from tests.test_figures_migration import RW5A_ADDED_OBJECTS
from tests.test_t1_batch_origin_migration import T1_ALTERED_TABLES
from tests.test_rw2d_receipts_migration import RW2D_ADDED_OBJECTS, RW2D_ALTERED_TABLES
from tests.test_retrieval_spaces_migration import P1_ADDED_OBJECTS
from tests.test_learner_claim_application_migration import CLAIM_POINT_ALTERED_TABLES
from tests.test_section_coverage_migration import C0A_ADDED_OBJECTS
from tests.test_figure_requests_migration import RW5D_ADDED_OBJECTS, RW5D_ALTERED_TABLES

HEAD = Path(__file__).resolve().parents[1] / "fixtures" / "migration_head_224" / "state.sqlite"
NOW = "2026-10-21T10:00:00Z"
#: What 217 adds: the earlier migrations' "nothing else changed" diffs on the
#: way to head read these.
RW7A_ADDED_OBJECTS = frozenset({
    "reader_path_sections", "idx_reader_path_sections_judged", "idx_reader_path_sections_reading",
    "reader_path_sections_no_update", "reader_path_sections_no_delete", "sqlite_autoindex_reader_path_sections_1",
    "reader_path_depths", "idx_reader_path_depths_source", "reader_path_depths_no_update",
    "reader_path_depths_no_delete", "sqlite_autoindex_reader_path_depths_1",
})
SECTION_10_1 = {"id", "extraction_id", "depth", "section_id", "label", "reason", "exercise_span_id",
                "learner_override", "ledger_id", "state_key", "model", "prompt_version", "created_at"}


def _database_at(tmp_path: Path, version: int) -> Path:
    through = tmp_path / f"through_{version}"
    through.mkdir()
    for migration in discover_migrations():
        if migration.version <= version:
            (through / migration.path.name).write_text(migration.path.read_text(encoding="utf-8"), encoding="utf-8")
    database = tmp_path / "state.sqlite"
    apply_migrations(database, migrations_dir=through)
    assert max(applied_versions(database)) == version
    return database


def _schema(database: Path) -> dict[str, str]:
    with closing(sqlite3.connect(database)) as connection:
        return {name: sql or "" for name, sql in connection.execute(
            "SELECT name, sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_stat%'")}


def _upgrade(tmp_path: Path) -> Path:
    database = _database_at(tmp_path, 215)
    before = _schema(database)
    with upgrade_allowance(UPGRADE_TEST_HELPER):
        applied = apply_migrations(database)
    # Reader RW5a's 216 (its own two tables, altering nothing) lands with 217 on the way to head.
    assert [migration.version for migration in applied] == [216, 217, 218, 219, 220, 221, 222, 224]  # and T1's 218, RW2d's 219, local retrieval P1's 220
    after = _schema(database)
    assert set(after) - set(before) - RW5A_ADDED_OBJECTS - RW2D_ADDED_OBJECTS - P1_ADDED_OBJECTS - C0A_ADDED_OBJECTS - RW5D_ADDED_OBJECTS == RW7A_ADDED_OBJECTS
    assert {name for name in before if before[name] != after.get(name)} - T1_ALTERED_TABLES - (RW2D_ALTERED_TABLES | CLAIM_POINT_ALTERED_TABLES) == set(), "217 alters nothing"
    return database


def _ledger(connection, ledger_id: str = "rpj_1") -> None:
    connection.execute(
        "INSERT INTO judgment_ledger (id, created_at, task, left_kind, left_id, right_kind, right_id, judge, "
        "judge_model, prompt_version, input_hash, verdict, score, rationale) VALUES (?, ?, 'reading_path_role', "
        "'reading_path', 'ext:fluency', 'reader_section', 'u1', 'llm', 'm', 'v', 'h', 'core', NULL, '{}')",
        (ledger_id, NOW))


def _section(connection, row_id: str = "rps_1", **columns) -> None:
    row = {"id": row_id, "extraction_id": "ext", "depth": "fluency", "section_id": "u1", "label": "core",
           "reason": "needed", "exercise_span_id": None, "learner_override": None, "ledger_id": "rpj_1",
           "state_key": "k", "model": "m", "prompt_version": "v", "created_at": NOW, **columns}
    names = sorted(row)
    connection.execute(
        f"INSERT INTO reader_path_sections ({', '.join(names)}) VALUES ({', '.join('?' for _ in names)})",
        [row[name] for name in names])


def _check(database: Path) -> None:
    with closing(connect(database)) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        assert {row[1] for row in connection.execute("PRAGMA table_info(reader_path_sections)")} == SECTION_10_1
        assert {row[1] for row in connection.execute("PRAGMA table_info(reader_path_depths)")} == {
            "id", "source_id", "depth", "created_at"}
        _ledger(connection)
        _section(connection)
        # Every label and override the spec names, each a row of its own.
        for index, label in enumerate(("prerequisite", "enrichment", "already_shown", "assumed")):
            _section(connection, f"rps_l{index}", section_id=f"u{index + 2}", label=label)
        for index, choice in enumerate(("read_anyway", "skip", "none")):
            _section(connection, f"rps_o{index}", learner_override=choice)
        for bad in ({"id": "rps_b1", "section_id": "b1", "ledger_id": "rpj_missing"},
                    {"id": "rps_b2", "section_id": "b2", "label": "essential"},
                    {"id": "rps_b3", "section_id": "b3", "depth": "mastery"},
                    {"id": "rps_b4", "section_id": "b4", "learner_override": "mark_known"},
                    {"id": "rps_b5"}):  # one judge row per (reading, depth, state, section)
            row_id = bad.pop("id")
            with pytest.raises(sqlite3.IntegrityError):
                _section(connection, row_id, **bad)
        for statement in ("UPDATE reader_path_sections SET label = 'enrichment'", "DELETE FROM reader_path_sections"):
            with pytest.raises(sqlite3.IntegrityError, match="append-only"):
                connection.execute(statement)
        connection.execute("INSERT INTO reader_path_depths (id, source_id, depth, created_at) VALUES "
                           "('rpd_1', 'src', 'get_the_idea', ?)", (NOW,))
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute("INSERT INTO reader_path_depths (id, source_id, depth, created_at) VALUES "
                               "('rpd_2', 'src', 'deep', ?)", (NOW,))
        for statement in ("UPDATE reader_path_depths SET depth = 'fluency'", "DELETE FROM reader_path_depths"):
            with pytest.raises(sqlite3.IntegrityError, match="append-only"):
                connection.execute(statement)
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []


def test_217_adds_the_two_rw7a_tables_and_nothing_else(tmp_path):
    _check(_upgrade(tmp_path))


@pytest.mark.durability
def test_217_on_the_durability_lane(tmp_path):
    database = _upgrade(tmp_path)
    with closing(sqlite3.connect(database)) as connection:
        assert connection.execute("PRAGMA journal_mode").fetchone()[0] == "wal"
    _check(database)


def test_the_rw7a_tables_are_workflow():
    assert role_for_table("reader_path_sections") is TableRole.WORKFLOW
    assert role_for_table("reader_path_depths") is TableRole.WORKFLOW


def test_the_head_fixture_is_at_217_in_rollback_mode_with_empty_rw7a_tables(tmp_path):
    from learnloop.db.copies import backup_database

    assert HEAD.read_bytes()[18:20] == b"\x01\x01"
    assert max(applied_versions(HEAD)) == max(m.version for m in discover_migrations()) == 224
    # RW5a's 216 landed after RW7a; AD2+AD3's 214 joined them at its compose round, T1's 218, RW2d's 219 and local retrieval P1's 220 after.
    assert {214, 215, 216, 217, 218, 219, 220, 221} <= set(applied_versions(HEAD))
    with closing(sqlite3.connect(f"file:{HEAD}?mode=ro", uri=True)) as connection:
        assert connection.execute("PRAGMA journal_mode").fetchone()[0] == "delete"
        for table in ("reader_path_sections", "reader_path_depths"):
            assert connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] == 0
    database = tmp_path / "head.sqlite"
    backup_database(HEAD, database)
    _check(database)
