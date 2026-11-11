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

from tests.te3a_migration_helpers import TE3A_ALTERED_TABLES
from tests.retrieval_spaces_migration_helpers import P1_ADDED_OBJECTS
from tests.section_coverage_migration_helpers import C0A_ADDED_OBJECTS
from learnloop.db.migrate import (
    UPGRADE_TEST_HELPER,
    applied_versions,
    apply_migrations,
    discover_migrations,
    upgrade_allowance,
)

from tests.rw2d_receipts_migration_helpers import RW2D_ADDED_OBJECTS, RW2D_ALTERED_TABLES
from tests.learner_claim_application_migration_helpers import CLAIM_POINT_ALTERED_TABLES
from tests.figure_requests_migration_helpers import RW5D_ADDED_OBJECTS, RW5D_ALTERED_TABLES
from tests.session_ownership_migration_helpers import PR4_ADDED_OBJECTS, PR4_ALTERED_TABLES
from tests.learner_note_source_kind_migration_helpers import C5_ALTERED_TABLES
from tests.learner_gap_unlinked_migration_helpers import UNLINKED_ALTERED_TABLES
from tests.help_assist_work_md_migration_helpers import DR2_ALTERED_TABLES
from tests.help_assist_figures_migration_helpers import P3_ADDED_OBJECTS, P3_ALTERED_TABLES
from tests.reader_session_digests_migration_helpers import RW6B_ADDED_OBJECTS
from tests.deliverable_curriculum_migration_helpers import C0B_ADDED_OBJECTS
from tests.learner_notes_migration_helpers import C2_ADDED_OBJECTS
# TE1's 234 and TE1b's 236 follow on the way to head (composed in tests/test_teacher_te1b_migration.py).
from tests.teacher_te1b_migration_helpers import TE1_AND_TE1B_ADDED_OBJECTS as TE1_ADDED_OBJECTS
from tests.teacher_te1b_migration_helpers import TE1_AND_TE1B_ALTERED_TABLES as TE1_ALTERED_TABLES
from tests.figure_prefetch_migration_helpers import P5_ADDED_OBJECTS
from tests.data_capture_migration_helpers import DATA_CAPTURE_ADDED_OBJECTS
from tests.followup_migration_helpers import FOLLOWUP_ADDED_OBJECTS
from tests.hypothesis_marks_migration_helpers import MARKS_ADDED_OBJECTS
from tests.router_objective_migration_helpers import RO0_ADDED_OBJECTS
from tests.ro2_history_migration_helpers import RO2_ADDED_OBJECTS
from tests.ro4_traces_migration_helpers import RO4_ADDED_OBJECTS
from tests.teacher_te2log_migration_helpers import TE2LOG_ADDED_OBJECTS
from tests.ih3_migration_helpers import IH3_ADDED_OBJECTS
from tests.decision_records_migration_helpers import B1_ADDED_OBJECTS, B1_ALTERED_TABLES
from tests.mobile_jobs_migration_helpers import M2A_ADDED_OBJECTS
from tests.rw5c_migration_helpers import RW5C_ADDED_OBJECTS
from tests.helpers import MIGRATION_HEAD_FIXTURE, migration_head
from tests.t1_batch_origin_migration_helpers import T1_ALTERED_TABLES

HEAD = MIGRATION_HEAD_FIXTURE / "state.sqlite"


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
    assert [migration.version for migration in applied] == list(range(218, migration_head() + 1))
    after = _schema(database)
    assert set(after) - RW2D_ADDED_OBJECTS - P1_ADDED_OBJECTS - C0A_ADDED_OBJECTS - RW5D_ADDED_OBJECTS - PR4_ADDED_OBJECTS - RW6B_ADDED_OBJECTS - C0B_ADDED_OBJECTS - C2_ADDED_OBJECTS - P3_ADDED_OBJECTS - TE1_ADDED_OBJECTS - P5_ADDED_OBJECTS - RW5C_ADDED_OBJECTS - M2A_ADDED_OBJECTS - DATA_CAPTURE_ADDED_OBJECTS - FOLLOWUP_ADDED_OBJECTS - MARKS_ADDED_OBJECTS - RO0_ADDED_OBJECTS - RO2_ADDED_OBJECTS - RO4_ADDED_OBJECTS - TE2LOG_ADDED_OBJECTS - IH3_ADDED_OBJECTS - B1_ADDED_OBJECTS == set(before)
    assert {name for name in before if before[name] != after[name]} == T1_ALTERED_TABLES | (RW2D_ALTERED_TABLES | CLAIM_POINT_ALTERED_TABLES | RW5D_ALTERED_TABLES | PR4_ALTERED_TABLES | DR2_ALTERED_TABLES | C5_ALTERED_TABLES | P3_ALTERED_TABLES | UNLINKED_ALTERED_TABLES | TE1_ALTERED_TABLES | B1_ALTERED_TABLES | TE3A_ALTERED_TABLES)
    with closing(sqlite3.connect(database)) as connection:
        columns = [row[1] for row in connection.execute("PRAGMA table_info(ingest_batches)")]
        assert columns[-1] == "origin_method"
        # A batch from before 218 belongs to no action.
        assert connection.execute("SELECT origin_method FROM ingest_batches WHERE id = 'b_old'").fetchone() == (None,)


def test_the_head_fixture_is_at_head_in_rollback_mode():
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
