"""Reader workbench RW6b part 1: migration 227 (spec_reader_workbench_v1 §9.4).

``reader_session_digests`` is new (WORKFLOW: the valuation receipt records a
paid relevance step and the commitments it created, so a rebuild never
clears or re-runs it). No DERIVED table, so no replayer; nothing is altered.
"""

from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path

import pytest

from learnloop.db.migrate import UPGRADE_TEST_HELPER, apply_migrations, discover_migrations, upgrade_allowance
from learnloop.db.stores import reader_digests as RDG
from learnloop.db.table_roles import TableRole, role_for_table

MIGRATIONS = Path(__file__).resolve().parents[1] / "migrations"
HEAD = Path(__file__).resolve().parents[1] / "fixtures" / "migration_head_230" / "state.sqlite"
#: Every schema object 227 adds: the earlier migrations' "nothing else
#: changed" diffs on the way to head read these.
RW6B_ADDED_OBJECTS = frozenset({
    "reader_session_digests", "sqlite_autoindex_reader_session_digests_1",
    "sqlite_autoindex_reader_session_digests_2", "idx_reader_session_digests_extraction",
    "idx_reader_session_digests_ended",
})


def _schema(path: Path) -> dict[str, str | None]:
    with closing(sqlite3.connect(f"file:{path}?mode=ro", uri=True)) as connection:
        return {row[0]: row[1] for row in connection.execute("SELECT name, sql FROM sqlite_master")}


def test_227_is_the_reader_session_digests_migration_and_the_table_is_workflow():
    names = {migration.version: migration.path.name for migration in discover_migrations()}
    assert names[227] == "227_reader_session_digests.sql"
    assert names[226] == "226_session_ownership.sql"
    assert role_for_table("reader_session_digests") == TableRole.WORKFLOW


def test_the_digest_row_round_trips_and_one_session_has_one_row(tmp_path):
    with closing(sqlite3.connect(tmp_path / "state.sqlite")) as connection:
        connection.row_factory = sqlite3.Row
        connection.executescript((MIGRATIONS / "227_reader_session_digests.sql").read_text(encoding="utf-8"))
        row = {"id": "rsd_1", "extraction_id": "ext1", "session_key": "v1", "visit_ids": ["v1", "v2"],
               "started_at": "2026-10-27T10:00:00Z", "ended_at": "2026-10-27T10:40:00Z", "status": "planned",
               "summary": {"activity": True}, "followup_commitment_ids": ["c1"],
               "valuation": {"chosen": [{"ref": "pi"}]}, "created_at": "2026-10-27T11:20:00Z"}
        RDG.insert_digest(connection, row)
        stored = RDG.digest(connection, "rsd_1")
        assert stored["visit_ids"] == ["v1", "v2"] and stored["followup_commitment_ids"] == ["c1"]
        assert stored["valuation"] == {"chosen": [{"ref": "pi"}]} and stored["revaluation"] is None
        # Part 2's narrative columns are carried and stay empty.
        assert stored["narrative_md"] is None and stored["cited_event_ids"] is None and stored["model"] is None
        assert RDG.digest_for_commitment(connection, "c1")["id"] == "rsd_1"
        with pytest.raises(sqlite3.IntegrityError):
            RDG.insert_digest(connection, {**row, "id": "rsd_2"})  # one row per session
        with pytest.raises(ValueError):
            RDG.insert_digest(connection, {**row, "id": "rsd_3", "session_key": "v9", "status": "draft"})
        with pytest.raises(ValueError):
            RDG.update_digest(connection, "rsd_1", session_key="other")
        RDG.update_digest(connection, "rsd_1", revaluation_json={"lines": []}, revalued_on="2026-10-28")
        assert RDG.digest(connection, "rsd_1")["revaluation"] == {"lines": []}


def test_head_226_upgrades_by_adding_only_227s_objects(tmp_path):
    from learnloop.db.copies import backup_database

    database = tmp_path / "state.sqlite"
    backup_database(HEAD, database)
    with closing(sqlite3.connect(database)) as connection:
        for name in sorted(RW6B_ADDED_OBJECTS - {n for n in RW6B_ADDED_OBJECTS if n.startswith("sqlite_autoindex")}):
            kind = connection.execute("SELECT type FROM sqlite_master WHERE name = ?", (name,)).fetchone()[0]
            connection.execute(f"DROP {kind.upper()} IF EXISTS {name}")
        connection.execute("DELETE FROM schema_migrations WHERE version = 227")
        connection.commit()
    before = _schema(database)
    with upgrade_allowance(UPGRADE_TEST_HELPER):
        applied = apply_migrations(database)
    assert [migration.version for migration in applied] == [227]
    after = _schema(database)
    assert set(after) - set(before) == RW6B_ADDED_OBJECTS
    assert {name for name in before if before[name] != after[name]} == set()  # 227 alters nothing


def test_the_head_fixture_holds_exactly_227s_objects_in_rollback_mode():
    with closing(sqlite3.connect(f"file:{HEAD}?mode=ro", uri=True)) as connection:
        names = {row[0] for row in connection.execute("SELECT name FROM sqlite_master")}
        assert RW6B_ADDED_OBJECTS <= names
        # Curriculum C0b's 228 landed first; the head holds 226 + 227 + 228.
        assert connection.execute("SELECT 1 FROM schema_migrations WHERE version = 227").fetchone()
        assert connection.execute("SELECT MAX(version) FROM schema_migrations").fetchone()[0] == 230
        assert connection.execute("PRAGMA journal_mode").fetchone()[0] == "delete"
        assert connection.execute("SELECT COUNT(*) FROM reader_session_digests").fetchone()[0] == 0
    assert HEAD.read_bytes()[18:20] == b"\x01\x01"


@pytest.mark.durability
def test_227_applies_on_a_fresh_durable_vault(tmp_path):
    from tests.helpers import create_basic_vault

    paths = create_basic_vault(tmp_path / "vault", fresh=True)
    with closing(sqlite3.connect(paths.sqlite_path)) as connection:
        assert connection.execute("SELECT 1 FROM sqlite_master WHERE name = 'reader_session_digests'").fetchone()
        assert connection.execute("SELECT 1 FROM schema_migrations WHERE version = 227").fetchone()
