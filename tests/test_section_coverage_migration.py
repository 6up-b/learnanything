"""Curriculum C0a: migration 222 (section_coverage), its table role and AD classification."""
from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path

import pytest

from learnloop.db.migrate import UPGRADE_TEST_HELPER, applied_versions, apply_migrations, discover_migrations, upgrade_allowance
from learnloop.db.table_roles import TableRole, tables_for_role
from tests.test_figure_requests_migration import RW5D_ADDED_OBJECTS, RW5D_ALTERED_TABLES
from tests.test_session_ownership_migration import PR4_ADDED_OBJECTS, PR4_ALTERED_TABLES
from tests.test_reader_ca2_fix_orchestrator import CA2_ALTERED_TABLES

HEAD = Path(__file__).resolve().parents[1] / "fixtures" / "migration_head_225" / "state.sqlite"
#: Every schema object 222 adds: the earlier migrations' "nothing else" diffs on the way to head read this.
C0A_ADDED_OBJECTS = frozenset({
    "section_coverage", "sqlite_autoindex_section_coverage_1", "idx_section_coverage_judged",
    "idx_section_coverage_section", "idx_section_coverage_lo", "section_coverage_no_update",
    "section_coverage_no_delete",
})
NOW = "2026-10-25T12:00:00Z"


def _database_at(tmp_path: Path, version: int) -> Path:
    through = tmp_path / f"through_{version}"
    through.mkdir()
    for migration in discover_migrations():
        if migration.version <= version:
            (through / migration.path.name).write_text(migration.path.read_text(encoding="utf-8"), encoding="utf-8")
    database = tmp_path / "state.sqlite"
    apply_migrations(database, migrations_dir=through)
    return database


def _schema(database: Path) -> dict[str, str]:
    with closing(sqlite3.connect(database)) as connection:
        return {name: sql or "" for name, sql in connection.execute(
            "SELECT name, sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_stat%'")}


def test_222_adds_one_table_and_alters_nothing(tmp_path):
    # Built on LP-min (a)'s 221 at the landing (the branch had 222 on 220; the runner is set-based).
    database = _database_at(tmp_path, 221)
    before = _schema(database)
    with upgrade_allowance(UPGRADE_TEST_HELPER):
        applied = apply_migrations(database)
    assert [migration.version for migration in applied] == [222, 223, 224, 225]
    after = _schema(database)
    # Reader CA2's 223 (one workbench_sessions column) and RW5d P1's 224 (its table, and
    # interactive_figures rebuilt) follow on the way to head.
    assert {name for name in before if before[name] != after.get(name)} == CA2_ALTERED_TABLES | RW5D_ALTERED_TABLES | PR4_ALTERED_TABLES
    assert set(after) - set(before) - RW5D_ADDED_OBJECTS - PR4_ADDED_OBJECTS == C0A_ADDED_OBJECTS


def test_the_head_fixture_is_at_222_in_rollback_mode():
    versions = applied_versions(HEAD)
    assert max(versions) == max(m.version for m in discover_migrations()) == 225
    assert 221 in versions  # rebuilt at the landing on main's head 221 (LP-min (a)'s claim fixes)
    assert HEAD.read_bytes()[18:20] == b"\x01\x01"
    with closing(sqlite3.connect(f"file:{HEAD}?mode=ro", uri=True)) as connection:
        assert connection.execute("PRAGMA journal_mode").fetchone()[0] == "delete"
        assert connection.execute("SELECT COUNT(*) FROM section_coverage").fetchone()[0] == 0


def test_table_role_and_ad_classification():
    from learnloop.adaptive_difficulty import protected_tables as PT

    assert "section_coverage" in tables_for_role(TableRole.WORKFLOW)
    assert PT.role("section_coverage") == PT.PROTECTED
    assert "section_coverage" in PT.READING


def _ledger(connection, ledger_id: str = "scv_l1") -> None:
    connection.execute(
        "INSERT INTO judgment_ledger (id, created_at, task, left_kind, left_id, right_kind, right_id, judge, "
        "judge_model, prompt_version, input_hash, verdict, score, rationale) VALUES (?, ?, 'section_coverage', "
        "'learning_object', 'lo', 'reader_section', 'ext/u1', 'llm', 'm', 'v', 'h', 'develops', 1.0, '{}')",
        (ledger_id, NOW))


def _row(connection, row_id: str, **columns) -> None:
    row = {"id": row_id, "extraction_id": "ext", "section_id": "u1", "learning_object_id": "lo",
           "treatment": "develops", "roles_json": "[]", "assumes_json": "[]", "notation_md": None,
           "origin": "retrieval", "candidate_rank": 0, "learner_override": None, "learner_text": None,
           "section_hash": "sh", "lo_hash": "lh", "state_key": "k1", "ledger_id": "scv_l1", "model": "m",
           "prompt_version": "v", "created_at": NOW, **columns}
    names = list(row)
    connection.execute(f"INSERT INTO section_coverage ({','.join(names)}) VALUES ({','.join('?' for _ in names)})",
                       tuple(row[name] for name in names))


def test_the_constraints(tmp_path):
    database = _database_at(tmp_path, 222)
    with closing(sqlite3.connect(database)) as connection:
        _ledger(connection)
        _row(connection, "a")
        with pytest.raises(sqlite3.IntegrityError):  # one judge row per (LO, state, reading, section)
            _row(connection, "b")
        _row(connection, "c", learner_override="not_about", treatment=None, origin="learner")
        _row(connection, "d", learner_override="not_about", treatment=None, origin="learner")  # learner rows repeat
        with pytest.raises(sqlite3.IntegrityError):  # a judge row has a treatment
            _row(connection, "e", treatment=None, state_key="k2")
        with pytest.raises(sqlite3.IntegrityError):
            _row(connection, "f", treatment="maybe", state_key="k3")
        with pytest.raises(sqlite3.IntegrityError):
            _row(connection, "g", origin="guess", state_key="k4")
        connection.commit()
        with pytest.raises(sqlite3.DatabaseError, match="append-only"):
            connection.execute("UPDATE section_coverage SET treatment = 'mentions'")
        with pytest.raises(sqlite3.DatabaseError, match="append-only"):
            connection.execute("DELETE FROM section_coverage")


@pytest.mark.durability
def test_222_on_the_durability_lane(tmp_path):
    from learnloop.db.connection import connect

    database = _database_at(tmp_path, 221)
    with upgrade_allowance(UPGRADE_TEST_HELPER):
        assert [migration.version for migration in apply_migrations(database)] == [222, 223, 224, 225]
    with closing(sqlite3.connect(database)) as connection:
        assert connection.execute("PRAGMA journal_mode").fetchone()[0] == "wal"
    with closing(connect(database)) as connection:
        _ledger(connection)
        _row(connection, "a")
        connection.commit()
        with pytest.raises(sqlite3.DatabaseError, match="append-only"):
            connection.execute("DELETE FROM section_coverage")
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
