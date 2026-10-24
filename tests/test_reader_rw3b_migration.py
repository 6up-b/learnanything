"""Reader RW3b's migration 215 (spec_reader_workbench_v1 §6.3, §11): ``passage_links`` and ``reader_cue_impressions``.

The 213 -> 215 upgrade (AD2+AD3 holds 214 on its own branch; the runner has
no contiguity rule) adds the two tables with every column §6.3 names, their
indexes and triggers, and alters nothing else. ``passage_links`` is WORKFLOW
(paid outputs, never re-run on rebuild), append-only; ``reader_cue_impressions``
is RECEIPT, append-only but for the learner's first response, written once.
Foreign keys hold (a link cites its judgment_ledger verdict; an impression its
link). The durability lane runs the upgrade with production pragmas.
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
from tests.test_reader_rw7a_migration import RW7A_ADDED_OBJECTS
from tests.test_t1_batch_origin_migration import T1_ALTERED_TABLES
from tests.test_rw2d_receipts_migration import RW2D_ADDED_OBJECTS, RW2D_ALTERED_TABLES

HEAD = Path(__file__).resolve().parents[1] / "fixtures" / "migration_head_219" / "state.sqlite"
NOW = "2026-10-20T10:00:00Z"
#: What 215 adds: the earlier migrations' "nothing else changed" diffs on the
#: way to head read these.
RW3B_ADDED_OBJECTS = frozenset({
    "passage_links", "idx_passage_links_extraction", "idx_passage_links_target", "passage_links_no_update",
    "passage_links_no_delete", "reader_cue_impressions", "idx_reader_cue_impressions_link",
    "idx_reader_cue_impressions_created", "reader_cue_impressions_response_once", "reader_cue_impressions_no_delete",
    "sqlite_autoindex_passage_links_1", "sqlite_autoindex_passage_links_2",
    "sqlite_autoindex_reader_cue_impressions_1", "sqlite_autoindex_reader_cue_impressions_2",
})
SECTION_6_3_LINKS = {"id", "extraction_id", "span_id", "target_kind", "target_id", "relation", "quote", "ledger_id",
                     "state_key", "model", "prompt_version", "created_at"}
SECTION_6_3_IMPRESSIONS = {"id", "link_id", "learning_object_id", "visit_id", "shown", "suppressed_reason", "propensity", "seed", "p_open",
                           "p_open_source", "density", "response", "response_text_hash", "created_at", "responded_at"}


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
    database = _database_at(tmp_path, 213)
    before = _schema(database)
    with upgrade_allowance(UPGRADE_TEST_HELPER):
        applied = apply_migrations(database)
    # Reader RW5a's 216 and RW7a's 217 (their own two tables each, altering nothing) follow on the way to head.
    assert [migration.version for migration in applied] == [215, 216, 217, 218, 219]  # and T1's 218, RW2d's 219
    after = _schema(database)
    assert set(after) - set(before) - RW5A_ADDED_OBJECTS - RW7A_ADDED_OBJECTS - RW2D_ADDED_OBJECTS == RW3B_ADDED_OBJECTS
    assert {name for name in before if before[name] != after.get(name)} - T1_ALTERED_TABLES - RW2D_ALTERED_TABLES == set(), "215 alters nothing"
    return database


def _ledger(connection, ledger_id: str = "pcj_1") -> None:
    connection.execute(
        "INSERT INTO judgment_ledger (id, created_at, task, left_kind, left_id, right_kind, right_id, judge, "
        "judge_model, prompt_version, input_hash, verdict, score, rationale) VALUES (?, ?, 'passage_cue', "
        "'cue_target', 'ext|misconception:m1|k', 'reader_span', 'ext/s1', 'llm', 'm', 'v', 'h', "
        "'clarifies_distinction', 1.0, '{}')", (ledger_id, NOW))


def _link(connection, link_id: str = "plink_1", *, ledger_id: str = "pcj_1", **columns) -> None:
    row = {"id": link_id, "extraction_id": "ext", "span_id": "s1", "target_kind": "misconception", "target_id": "m1",
           "relation": "clarifies_distinction", "quote": "the quoted words", "pick_rank": 1, "ledger_id": ledger_id,
           "state_key": "k", "model": "m", "prompt_version": "v", "created_at": NOW, **columns}
    names = sorted(row)
    connection.execute(f"INSERT INTO passage_links ({', '.join(names)}) VALUES ({', '.join('?' for _ in names)})",
                       [row[name] for name in names])


def _impression(connection, impression_id: str = "cimp_1", **columns) -> None:
    row = {"id": impression_id, "cue_id": "dcue_1", "link_id": "plink_1", "extraction_id": "ext", "span_id": "s1",
           "kind": "distinction", "visit_id": "v1", "shown": 1, "suppressed_reason": None, "propensity": 0.9,
           "seed": "abc", "p_open": 1.0, "p_open_source": "misconception_lifecycle", "density": "normal",
           "created_at": NOW, **columns}
    names = sorted(row)
    connection.execute(
        f"INSERT INTO reader_cue_impressions ({', '.join(names)}) VALUES ({', '.join('?' for _ in names)})",
        [row[name] for name in names])


def _check(database: Path) -> None:
    with closing(connect(database)) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        assert SECTION_6_3_LINKS <= {row[1] for row in connection.execute("PRAGMA table_info(passage_links)")}
        assert SECTION_6_3_IMPRESSIONS <= {
            row[1] for row in connection.execute("PRAGMA table_info(reader_cue_impressions)")}
        _ledger(connection)
        _link(connection)
        assert tuple(connection.execute("SELECT ranks_json, roles_json FROM passage_links").fetchone()) == ("{}", "[]")
        # A link cites a real verdict; its vocabularies are CHECKed; it never changes.
        for bad in ({"id": "plink_2", "ledger_id": "pcj_missing", "span_id": "s2"},
                    {"id": "plink_3", "relation": "none", "span_id": "s3"},
                    {"id": "plink_4", "target_kind": "learner", "span_id": "s4"},
                    {"id": "plink_5", "pick_rank": 0, "span_id": "s5"}):
            link_id = bad.pop("id")
            with pytest.raises(sqlite3.IntegrityError):
                _link(connection, link_id, **bad)
        with pytest.raises(sqlite3.IntegrityError):  # one row per (extraction, target, state, span)
            _link(connection, "plink_dup")
        for statement in ("UPDATE passage_links SET quote = 'x'", "DELETE FROM passage_links"):
            with pytest.raises(sqlite3.IntegrityError, match="append-only"):
                connection.execute(statement)
        # An impression: shown or not with its reason; a holdout names a link; the
        # learner's first response is written once and nothing else changes.
        _impression(connection)
        _impression(connection, "cimp_g", cue_id="cue_guide", link_id=None, kind="revisit", propensity=None,
                    seed=None)
        _impression(connection, "cimp_h", cue_id="dcue_2", shown=0, suppressed_reason="holdout", propensity=0.1)
        for bad in ({"id": "cimp_b1", "cue_id": "c_b1", "shown": 0, "suppressed_reason": None},
                    {"id": "cimp_b2", "cue_id": "c_b2", "shown": 1, "suppressed_reason": "spacing"},
                    {"id": "cimp_b3", "cue_id": "c_b3", "shown": 0, "suppressed_reason": "holdout", "link_id": None},
                    {"id": "cimp_b4", "cue_id": "c_b4", "shown": 0, "suppressed_reason": "skim"},
                    {"id": "cimp_b5", "cue_id": "c_b5", "density": "lots"},
                    {"id": "cimp_b6", "cue_id": "c_b6", "link_id": "plink_missing"},
                    {"id": "cimp_b7", "cue_id": "c_b7", "propensity": 0.0},
                    {"id": "cimp_b8", "cue_id": "dcue_1"}):  # one per (visit, cue)
            impression_id = bad.pop("id")
            with pytest.raises(sqlite3.IntegrityError):
                _impression(connection, impression_id, **bad)
        connection.execute("UPDATE reader_cue_impressions SET response = 'opened', responded_at = ? "
                           "WHERE id = 'cimp_1'", (NOW,))
        for statement in ("UPDATE reader_cue_impressions SET response = 'check_me' WHERE id = 'cimp_1'",
                          "UPDATE reader_cue_impressions SET shown = 0, suppressed_reason = 'spacing' WHERE id = 'cimp_g'",
                          "UPDATE reader_cue_impressions SET propensity = 0.5 WHERE id = 'cimp_h'",
                          "UPDATE reader_cue_impressions SET learning_object_id = 'lo_x' WHERE id = 'cimp_h'",
                          "DELETE FROM reader_cue_impressions"):
            with pytest.raises(sqlite3.IntegrityError):
                connection.execute(statement)
        with pytest.raises(sqlite3.IntegrityError):  # a response without its time
            connection.execute("UPDATE reader_cue_impressions SET response = 'opened' WHERE id = 'cimp_g'")
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []


def test_215_adds_the_two_rw3b_tables_and_nothing_else(tmp_path):
    _check(_upgrade(tmp_path))


@pytest.mark.durability
def test_215_on_the_durability_lane(tmp_path):
    database = _upgrade(tmp_path)
    with closing(sqlite3.connect(database)) as connection:
        assert connection.execute("PRAGMA journal_mode").fetchone()[0] == "wal"
    _check(database)


def test_the_rw3b_tables_are_classified():
    assert role_for_table("passage_links") is TableRole.WORKFLOW
    assert role_for_table("reader_cue_impressions") is TableRole.RECEIPT


def test_the_head_fixture_is_at_head_in_rollback_mode_with_empty_rw3b_tables(tmp_path):
    from learnloop.db.copies import backup_database

    assert HEAD.read_bytes()[18:20] == b"\x01\x01"
    # RW7a's 217 is the head now (tests/test_reader_rw7a_migration.py).
    assert max(applied_versions(HEAD)) == max(m.version for m in discover_migrations()) == 219
    with closing(sqlite3.connect(f"file:{HEAD}?mode=ro", uri=True)) as connection:
        assert connection.execute("PRAGMA journal_mode").fetchone()[0] == "delete"
        for table in ("passage_links", "reader_cue_impressions"):
            assert connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] == 0
    database = tmp_path / "head.sqlite"
    backup_database(HEAD, database)
    _check(database)
