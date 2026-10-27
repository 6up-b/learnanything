"""Plan-first transport T1, redesign D round 5: migration 218 (``ingest_batches.origin_method``).

The action (RPC method) whose request created an ingest batch, so a batch
resumed after a sidecar restart asks again as its action (Codex verify of
ad6dad0c4, Medium 2). One nullable column, nothing else; the queue store's
batch decoder leaves it out of every payload.
"""
from __future__ import annotations

from contextlib import closing
from pathlib import Path
import sqlite3

from tests.test_retrieval_spaces_migration import P1_ADDED_OBJECTS
from tests.test_section_coverage_migration import C0A_ADDED_OBJECTS
from learnloop.db.migrate import (
    UPGRADE_TEST_HELPER,
    applied_versions,
    apply_migrations,
    discover_migrations,
    upgrade_allowance,
)

from tests.test_rw2d_receipts_migration import RW2D_ADDED_OBJECTS, RW2D_ALTERED_TABLES
from tests.test_learner_claim_application_migration import CLAIM_POINT_ALTERED_TABLES
from tests.test_figure_requests_migration import RW5D_ADDED_OBJECTS, RW5D_ALTERED_TABLES

HEAD = Path(__file__).resolve().parents[1] / "fixtures" / "migration_head_225" / "state.sqlite"
#: What 218 alters: the earlier migrations' "nothing else changed" diffs on the way to head read this.
T1_ALTERED_TABLES = frozenset({"ingest_batches"})


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


def test_218_adds_the_batch_origin_column_and_nothing_else(tmp_path):
    database = _database_at(tmp_path, 217)
    before = _schema(database)
    with closing(sqlite3.connect(database)) as connection:
        connection.execute("INSERT INTO ingest_batches (id, workflow_type, created_at) VALUES ('b_old', 'w', 't')")
        connection.commit()
    with upgrade_allowance(UPGRADE_TEST_HELPER):
        applied = apply_migrations(database)
    # RW2d's 219 (its receipt table, and a workbench_sessions column) and local retrieval P1's 220 (its three tables) follow on the way to head.
    assert [migration.version for migration in applied] == [218, 219, 220, 221, 222, 223, 224]
    after = _schema(database)
    assert set(after) - RW2D_ADDED_OBJECTS - P1_ADDED_OBJECTS - C0A_ADDED_OBJECTS - RW5D_ADDED_OBJECTS == set(before)
    assert {name for name in before if before[name] != after[name]} == T1_ALTERED_TABLES | (RW2D_ALTERED_TABLES | CLAIM_POINT_ALTERED_TABLES | RW5D_ALTERED_TABLES)
    with closing(sqlite3.connect(database)) as connection:
        columns = [row[1] for row in connection.execute("PRAGMA table_info(ingest_batches)")]
        assert columns[-1] == "origin_method"
        # A batch from before 218 belongs to no action.
        assert connection.execute("SELECT origin_method FROM ingest_batches WHERE id = 'b_old'").fetchone() == (None,)


def test_the_head_fixture_is_at_head_in_rollback_mode():
    # Curriculum C0a's 222 is the head now (tests/test_section_coverage_migration.py).
    assert max(applied_versions(HEAD)) == max(m.version for m in discover_migrations()) == 224
    assert HEAD.read_bytes()[18:20] == b"\x01\x01"
    with closing(sqlite3.connect(f"file:{HEAD}?mode=ro", uri=True)) as connection:
        assert "origin_method" in [row[1] for row in connection.execute("PRAGMA table_info(ingest_batches)")]
        assert connection.execute("PRAGMA journal_mode").fetchone()[0] == "delete"


def test_the_batch_origin_never_reaches_a_payload(tmp_path):
    from learnloop.db.repositories import Repository
    from tests.helpers import create_basic_vault

    paths = create_basic_vault(tmp_path / "vault")
    repository = Repository.attach(paths.sqlite_path)
    repository.insert_ingest_batch(id="b1", workflow_type="w", origin_method="build_study_map")
    assert repository.ingest_batch_origin("b1") == "build_study_map"
    assert "origin_method" not in repository.get_ingest_batch("b1")
    assert all("origin_method" not in batch for batch in repository.list_ingest_batches())
