"""LP-min (a) claim fixes, Codex re-review F7: migration 221 (``learner_claims.applied_after_attempts``).

Where a re-anchoring claim was applied among its learning object's attempts,
recorded by the claim-fixes successor's re-anchor in the claim's own
transaction. One nullable column, nothing else; a claim from before it reads
NULL (replay places it by ``(created_at, id)``, as before).
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

from tests.te3a_migration_helpers import TE3A_ALTERED_TABLES
from tests.section_coverage_migration_helpers import C0A_ADDED_OBJECTS
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
from tests.reader_ca2_fix_orchestrator_helpers import CA2_ALTERED_TABLES
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
from tests.apply_intents_conflicted_migration_helpers import K35_ALTERED_TABLES
from tests.mobile_jobs_migration_helpers import M2A_ADDED_OBJECTS
from tests.rw5c_migration_helpers import RW5C_ADDED_OBJECTS
from tests.helpers import MIGRATION_HEAD_FIXTURE, migration_head
from tests.learner_claim_application_migration_helpers import CLAIM_POINT_ALTERED_TABLES

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


def _old_claim(connection) -> None:
    connection.execute(
        "INSERT INTO learner_claims (id, claim_type, scope_type, scope_id, claimed_level, prior_pseudo_count, "
        "source, created_at) VALUES ('c_old', 'self_rating', 'learning_object', 'lo', 0.3, 2.0, "
        "'tutor_gap_declaration', '2026-10-25T00:00:00Z')"
    )
    connection.commit()


def test_221_adds_the_claim_point_column_and_nothing_else(tmp_path):
    database = _database_at(tmp_path, 220)
    before = _schema(database)
    with closing(sqlite3.connect(database)) as connection:
        _old_claim(connection)
    with upgrade_allowance(UPGRADE_TEST_HELPER):
        applied = apply_migrations(database)
    # Curriculum C0a's 222 (its one table, altering nothing) follows on the way to head.
    assert [migration.version for migration in applied] == list(range(221, migration_head() + 1))
    after = _schema(database)
    assert set(after) - C0A_ADDED_OBJECTS - RW5D_ADDED_OBJECTS - PR4_ADDED_OBJECTS - RW6B_ADDED_OBJECTS - C0B_ADDED_OBJECTS - C2_ADDED_OBJECTS - P3_ADDED_OBJECTS - TE1_ADDED_OBJECTS - P5_ADDED_OBJECTS - RW5C_ADDED_OBJECTS - M2A_ADDED_OBJECTS - DATA_CAPTURE_ADDED_OBJECTS - FOLLOWUP_ADDED_OBJECTS - MARKS_ADDED_OBJECTS - RO0_ADDED_OBJECTS - RO2_ADDED_OBJECTS - RO4_ADDED_OBJECTS - TE2LOG_ADDED_OBJECTS - IH3_ADDED_OBJECTS - B1_ADDED_OBJECTS == set(before)
    assert {name for name in before if before[name] != after[name]} == CLAIM_POINT_ALTERED_TABLES | CA2_ALTERED_TABLES | RW5D_ALTERED_TABLES | PR4_ALTERED_TABLES | DR2_ALTERED_TABLES | C5_ALTERED_TABLES | P3_ALTERED_TABLES | UNLINKED_ALTERED_TABLES | TE1_ALTERED_TABLES | (B1_ALTERED_TABLES | K35_ALTERED_TABLES) | TE3A_ALTERED_TABLES
    with closing(sqlite3.connect(database)) as connection:
        # The successor mvp-0.36's 225 adds superseded_by after it on the way to head.
        assert [row[1] for row in connection.execute("PRAGMA table_info(learner_claims)")][-2:] == [
            "applied_after_attempts", "superseded_by",
        ]
        # A claim from before 221 has no recorded point.
        assert connection.execute(
            "SELECT applied_after_attempts FROM learner_claims WHERE id = 'c_old'"
        ).fetchone() == (None,)
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute("UPDATE learner_claims SET applied_after_attempts = -1 WHERE id = 'c_old'")


def test_the_head_fixture_holds_221_in_rollback_mode():
    assert 221 in applied_versions(HEAD)
    assert HEAD.read_bytes()[18:20] == b"\x01\x01"
    with closing(sqlite3.connect(f"file:{HEAD}?mode=ro", uri=True)) as connection:
        assert "applied_after_attempts" in [row[1] for row in connection.execute("PRAGMA table_info(learner_claims)")]
        assert connection.execute("PRAGMA journal_mode").fetchone()[0] == "delete"


@pytest.mark.durability
def test_221_on_the_durability_lane(tmp_path):
    database = _database_at(tmp_path, 220)
    with closing(sqlite3.connect(database)) as connection:
        _old_claim(connection)
    with upgrade_allowance(UPGRADE_TEST_HELPER):
        assert [migration.version for migration in apply_migrations(database)] == list(range(221, migration_head() + 1))
    with closing(sqlite3.connect(database)) as connection:
        assert connection.execute("PRAGMA journal_mode").fetchone()[0] == "wal"
        connection.execute("UPDATE learner_claims SET applied_after_attempts = 2 WHERE id = 'c_old'")
        connection.commit()
        assert connection.execute("SELECT applied_after_attempts FROM learner_claims").fetchone() == (2,)
