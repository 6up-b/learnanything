"""Local contextual retrieval P1a: migration 220 (embedding_spaces, retrieval_feedback,
retrieval_fusion_posteriors) and its table roles."""
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
from learnloop.db.stores.retrieval_spaces import (
    append_feedback,
    feedback_rows,
    has_tables,
    register_space,
    set_space_status,
    spaces,
)
from learnloop.db.table_roles import TableRole, tables_for_role
from learnloop.substrate.rebuild_orchestrator import derived_table_owners
from tests.test_learner_claim_application_migration import CLAIM_POINT_ALTERED_TABLES
from tests.test_section_coverage_migration import C0A_ADDED_OBJECTS
from tests.test_figure_requests_migration import RW5D_ADDED_OBJECTS, RW5D_ALTERED_TABLES
from tests.test_reader_ca2_fix_orchestrator import CA2_ALTERED_TABLES

HEAD = Path(__file__).resolve().parents[1] / "fixtures" / "migration_head_225" / "state.sqlite"
NEW_TABLES = {"embedding_spaces", "retrieval_feedback", "retrieval_fusion_posteriors"}
#: Every schema object 220 adds: the earlier migrations' "nothing else" diffs on the way to head read this.
P1_ADDED_OBJECTS = frozenset({
    "embedding_spaces", "sqlite_autoindex_embedding_spaces_1",
    "retrieval_feedback", "sqlite_autoindex_retrieval_feedback_1", "retrieval_feedback_receipt",
    "retrieval_feedback_owner", "retrieval_feedback_no_update", "retrieval_feedback_no_delete",
    "retrieval_fusion_posteriors", "sqlite_autoindex_retrieval_fusion_posteriors_1",
})


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


def test_220_adds_three_tables_and_alters_nothing(tmp_path):
    database = _database_at(tmp_path, 219)
    before = _schema(database)
    with upgrade_allowance(UPGRADE_TEST_HELPER):
        applied = apply_migrations(database)
    assert [migration.version for migration in applied] == [220, 221, 222, 223, 224]
    after = _schema(database)
    assert {name for name in before if before[name] != after.get(name)} == CLAIM_POINT_ALTERED_TABLES | CA2_ALTERED_TABLES | RW5D_ALTERED_TABLES
    # LP-min (a)'s 221 (one learner_claims column) and curriculum C0a's 222 (its one table, altering nothing)
    # follow on the way to head.
    assert set(after) - set(before) - C0A_ADDED_OBJECTS - RW5D_ADDED_OBJECTS == P1_ADDED_OBJECTS


def test_the_head_fixture_holds_220_in_rollback_mode():
    # Curriculum C0a's 222 is the head now (tests/test_section_coverage_migration.py).
    assert max(applied_versions(HEAD)) == max(m.version for m in discover_migrations()) == 224
    assert HEAD.read_bytes()[18:20] == b"\x01\x01"
    with closing(sqlite3.connect(f"file:{HEAD}?mode=ro", uri=True)) as connection:
        assert has_tables(connection)
        assert connection.execute("PRAGMA journal_mode").fetchone()[0] == "delete"
        for table in NEW_TABLES:
            assert connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] == 0


def test_table_roles_and_the_one_replayer():
    assert "embedding_spaces" in tables_for_role(TableRole.WORKFLOW)
    assert "retrieval_feedback" in tables_for_role(TableRole.RECEIPT)
    assert "retrieval_fusion_posteriors" in tables_for_role(TableRole.DERIVED)
    assert derived_table_owners()["retrieval_fusion_posteriors"] == ("retrieval_fusion_posteriors",)


def test_feedback_is_append_only_and_spaces_are_mutable(tmp_path):
    database = _database_at(tmp_path, 220)
    with closing(sqlite3.connect(database)) as connection:
        append_feedback(connection, [{"receipt_id": "rq_1", "event": "query", "consumer": "tutor",
                                      "query_kind": "lookup", "payload": {"a": 1}},
                                     {"receipt_id": "rq_1", "event": "delivered", "consumer": "tutor",
                                      "query_kind": "lookup", "extraction_id": "e", "span_id": "s", "position": 1}])
        connection.commit()
        with pytest.raises(sqlite3.DatabaseError, match="append-only"):
            connection.execute("UPDATE retrieval_feedback SET consumer = 'x'")
        with pytest.raises(sqlite3.DatabaseError, match="append-only"):
            connection.execute("DELETE FROM retrieval_feedback")
        with pytest.raises(sqlite3.IntegrityError):  # a query row names no span; a span row is never a query
            connection.execute("INSERT INTO retrieval_feedback (id, receipt_id, event, consumer, query_kind, span_id, "
                               "created_at) VALUES ('x', 'r', 'query', 'c', 'k', 's', 't')")
        assert [row["event"] for row in feedback_rows(connection)] == ["query", "delivered"]
        register_space(connection, space_id="ls_x", name="local:grouped", kind="local", pins={"a": 1},
                       status="active")
        register_space(connection, space_id="ls_x", name="ignored", kind="local", pins={}, status="active")
        set_space_status(connection, "ls_x", "epoch_drift", reason="a canary moved")
        row = spaces(connection)["ls_x"]
        assert row["name"] == "local:grouped" and row["status"] == "epoch_drift" and row["pins"] == {"a": 1}


def test_a_database_before_220_reads_as_empty(tmp_path):
    database = _database_at(tmp_path, 219)
    with closing(sqlite3.connect(database)) as connection:
        assert not has_tables(connection)
        assert spaces(connection) == {} and feedback_rows(connection) == []


@pytest.mark.durability
def test_220_on_the_durability_lane(tmp_path):
    from learnloop.db.connection import connect

    database = _database_at(tmp_path, 219)
    with upgrade_allowance(UPGRADE_TEST_HELPER):
        assert [migration.version for migration in apply_migrations(database)] == [220, 221, 222, 223, 224]
    with closing(sqlite3.connect(database)) as connection:
        assert connection.execute("PRAGMA journal_mode").fetchone()[0] == "wal"
    with closing(connect(database)) as connection:
        append_feedback(connection, [{"receipt_id": "rq_d", "event": "query", "consumer": "c", "query_kind": "k"}])
        connection.commit()
        with pytest.raises(sqlite3.DatabaseError, match="append-only"):
            connection.execute("DELETE FROM retrieval_feedback")
        assert len(feedback_rows(connection)) == 1
