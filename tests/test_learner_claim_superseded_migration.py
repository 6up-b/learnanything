"""Successor mvp-0.36: migration 225 (``learner_claims.superseded_by``).

The claim that replaced this one, written by the replace seam
(``Repository.replace_learner_claim``) from the successor on; NULL while the
claim is in force, and on every row from before the column (the predecessor's
seam deleted a replaced claim). One nullable column, nothing else.
"""
from __future__ import annotations

from contextlib import closing
from pathlib import Path
import sqlite3

import pytest

from learnloop.db.migrate import (
    UPGRADE_TEST_HELPER,
    applied_versions,
    apply_migrations,
    discover_migrations,
    upgrade_allowance,
)

from tests.test_session_ownership_migration import PR4_ADDED_OBJECTS, PR4_ALTERED_TABLES
from tests.test_deliverable_curriculum_migration import C0B_ADDED_OBJECTS

HEAD = Path(__file__).resolve().parents[1] / "fixtures" / "migration_head_228" / "state.sqlite"
#: What 225 alters: the earlier migrations' "nothing else changed" diffs on the way to head read this.
SUPERSEDED_ALTERED_TABLES = frozenset({"learner_claims"})


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


def _old_claim(connection) -> None:
    connection.execute(
        "INSERT INTO learner_claims (id, claim_type, scope_type, scope_id, claimed_level, prior_pseudo_count, "
        "source, created_at) VALUES ('c_old', 'self_rating', 'learning_object', 'lo', 0.8, 2.0, "
        "'learner_report', '2026-10-27T00:00:00Z')"
    )
    connection.commit()


def test_225_adds_the_superseded_by_column_and_nothing_else(tmp_path):
    database = _database_at(tmp_path, 224)
    before = _schema(database)
    with closing(sqlite3.connect(database)) as connection:
        _old_claim(connection)
    with upgrade_allowance(UPGRADE_TEST_HELPER):
        applied = apply_migrations(database)
    # Mobile PR-4's 226 (session ownership) follows it on the way to head.
    assert [migration.version for migration in applied] == [225, 226, 228]
    after = _schema(database)
    assert set(after) - PR4_ADDED_OBJECTS - C0B_ADDED_OBJECTS == set(before)
    assert {name for name in before if before[name] != after[name]} == SUPERSEDED_ALTERED_TABLES | PR4_ALTERED_TABLES
    with closing(sqlite3.connect(database)) as connection:
        assert [row[1] for row in connection.execute("PRAGMA table_info(learner_claims)")][-1] == "superseded_by"
        # A claim from before 225 is in force.
        assert connection.execute("SELECT superseded_by FROM learner_claims WHERE id = 'c_old'").fetchone() == (None,)
        # A claim never replaces itself.
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute("UPDATE learner_claims SET superseded_by = 'c_old' WHERE id = 'c_old'")


def test_the_head_fixture_holds_225_in_rollback_mode():
    # Mobile PR-4's 226 is the head now.
    assert 225 in applied_versions(HEAD)
    assert max(applied_versions(HEAD)) == max(m.version for m in discover_migrations()) == 228
    assert HEAD.read_bytes()[18:20] == b"\x01\x01"
    with closing(sqlite3.connect(f"file:{HEAD}?mode=ro", uri=True)) as connection:
        assert "superseded_by" in [row[1] for row in connection.execute("PRAGMA table_info(learner_claims)")]
        assert connection.execute("PRAGMA journal_mode").fetchone()[0] == "delete"


@pytest.mark.durability
def test_225_on_the_durability_lane(tmp_path):
    database = _database_at(tmp_path, 224)
    with closing(sqlite3.connect(database)) as connection:
        _old_claim(connection)
    with upgrade_allowance(UPGRADE_TEST_HELPER):
        assert [migration.version for migration in apply_migrations(database)] == [225, 226, 228]
    with closing(sqlite3.connect(database)) as connection:
        assert connection.execute("PRAGMA integrity_check").fetchone() == ("ok",)
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
