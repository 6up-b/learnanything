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

from tests.test_section_coverage_migration import C0A_ADDED_OBJECTS
from tests.test_figure_requests_migration import RW5D_ADDED_OBJECTS, RW5D_ALTERED_TABLES
from tests.test_session_ownership_migration import PR4_ADDED_OBJECTS, PR4_ALTERED_TABLES
from tests.test_learner_note_source_kind_migration import C5_ALTERED_TABLES
from tests.test_learner_gap_unlinked_migration import UNLINKED_ALTERED_TABLES
from tests.test_help_assist_work_md_migration import DR2_ALTERED_TABLES
from tests.test_help_assist_figures_migration import P3_ADDED_OBJECTS, P3_ALTERED_TABLES
from tests.test_reader_session_digests_migration import RW6B_ADDED_OBJECTS
from tests.test_deliverable_curriculum_migration import C0B_ADDED_OBJECTS
from tests.test_learner_notes_migration import C2_ADDED_OBJECTS
# TE1's 234 and TE1b's 236 follow on the way to head (composed in tests/test_teacher_te1b_migration.py).
from tests.test_teacher_te1b_migration import TE1_AND_TE1B_ADDED_OBJECTS as TE1_ADDED_OBJECTS
from tests.test_teacher_te1b_migration import TE1_AND_TE1B_ALTERED_TABLES as TE1_ALTERED_TABLES
from tests.test_reader_ca2_fix_orchestrator import CA2_ALTERED_TABLES
from tests.test_figure_prefetch_migration import P5_ADDED_OBJECTS
from tests.test_data_capture_migration import DATA_CAPTURE_ADDED_OBJECTS
from tests.test_followup_migration import FOLLOWUP_ADDED_OBJECTS
from tests.test_hypothesis_marks_migration import MARKS_ADDED_OBJECTS
from tests.test_router_objective_migration import RO0_ADDED_OBJECTS
from tests.test_mobile_jobs_migration import M2A_ADDED_OBJECTS
from tests.test_rw5c_migration import RW5C_ADDED_OBJECTS

HEAD = Path(__file__).resolve().parents[1] / "fixtures" / "migration_head_243" / "state.sqlite"
#: What 221 alters: the earlier migrations' "nothing else changed" diffs on the way to head read this.
CLAIM_POINT_ALTERED_TABLES = frozenset({"learner_claims"})


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
    assert [migration.version for migration in applied] == [221, 222, 223, 224, 225, 226, 227, 228, 229, 230, 231, 232, 233, 234, 235, 236, 237, 238, 239, 240, 241, 242, 243]
    after = _schema(database)
    assert set(after) - C0A_ADDED_OBJECTS - RW5D_ADDED_OBJECTS - PR4_ADDED_OBJECTS - RW6B_ADDED_OBJECTS - C0B_ADDED_OBJECTS - C2_ADDED_OBJECTS - P3_ADDED_OBJECTS - TE1_ADDED_OBJECTS - P5_ADDED_OBJECTS - RW5C_ADDED_OBJECTS - M2A_ADDED_OBJECTS - DATA_CAPTURE_ADDED_OBJECTS - FOLLOWUP_ADDED_OBJECTS - MARKS_ADDED_OBJECTS - RO0_ADDED_OBJECTS == set(before)
    assert {name for name in before if before[name] != after[name]} == CLAIM_POINT_ALTERED_TABLES | CA2_ALTERED_TABLES | RW5D_ALTERED_TABLES | PR4_ALTERED_TABLES | DR2_ALTERED_TABLES | C5_ALTERED_TABLES | P3_ALTERED_TABLES | UNLINKED_ALTERED_TABLES | TE1_ALTERED_TABLES
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
    # Curriculum C0a's 222 is the head now (tests/test_section_coverage_migration.py).
    assert 221 in applied_versions(HEAD)
    assert max(applied_versions(HEAD)) == max(m.version for m in discover_migrations()) == 243
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
        assert [migration.version for migration in apply_migrations(database)] == [221, 222, 223, 224, 225, 226, 227, 228, 229, 230, 231, 232, 233, 234, 235, 236, 237, 238, 239, 240, 241, 242, 243]
    with closing(sqlite3.connect(database)) as connection:
        assert connection.execute("PRAGMA journal_mode").fetchone()[0] == "wal"
        connection.execute("UPDATE learner_claims SET applied_after_attempts = 2 WHERE id = 'c_old'")
        connection.commit()
        assert connection.execute("SELECT applied_after_attempts FROM learner_claims").fetchone() == (2,)
