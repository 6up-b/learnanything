"""Curriculum C0b: migration 228 (spec_deliverable_curriculum_v1 §5, §7.4, §12.2).

Three new tables, append-only by trigger: ``deliverable_scope_inputs`` (RAW_LEDGER,
the learner's own words), ``deliverable_scope_resolutions`` and
``deliverable_path_sections`` (WORKFLOW, paid outputs never re-run on rebuild). No
DERIVED table, so no replayer; every table classified for AD (§9.4). 228 alters
nothing; RW6b part 1 holds 227 on its own branch.
"""

from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path

import pytest

from learnloop.adaptive_difficulty import protected_tables as PT
from learnloop.db.migrate import applied_versions, discover_migrations
from learnloop.db.table_roles import TableRole, role_for_table

MIGRATIONS = Path(__file__).resolve().parents[1] / "migrations"
HEAD = Path(__file__).resolve().parents[1] / "fixtures" / "migration_head_228" / "state.sqlite"
#: Every schema object 228 adds (it alters nothing): the earlier migrations' "nothing
#: else changed" diffs on the way to head read these.
C0B_ADDED_OBJECTS = frozenset({
    "deliverable_scope_inputs", "sqlite_autoindex_deliverable_scope_inputs_1", "idx_deliverable_scope_inputs_goal",
    "deliverable_scope_inputs_no_update", "deliverable_scope_inputs_no_delete",
    "deliverable_scope_resolutions", "sqlite_autoindex_deliverable_scope_resolutions_1",
    "idx_deliverable_scope_resolutions_goal", "deliverable_scope_resolutions_no_update",
    "deliverable_scope_resolutions_no_delete",
    "deliverable_path_sections", "sqlite_autoindex_deliverable_path_sections_1",
    "idx_deliverable_path_sections_judged", "idx_deliverable_path_sections_goal",
    "idx_deliverable_path_sections_reading", "deliverable_path_sections_no_update",
    "deliverable_path_sections_no_delete",
})
TABLES = ("deliverable_scope_inputs", "deliverable_scope_resolutions", "deliverable_path_sections")


def test_228_is_c0bs_migration_classified_with_no_derived_table():
    names = {migration.version: migration.path.name for migration in discover_migrations()}
    assert names[228] == "228_deliverable_curriculum.sql"
    assert role_for_table("deliverable_scope_inputs") == TableRole.RAW_LEDGER
    assert role_for_table("deliverable_scope_resolutions") == TableRole.WORKFLOW
    assert role_for_table("deliverable_path_sections") == TableRole.WORKFLOW
    for table in TABLES:
        assert PT.role(table) is not None, table
    assert {"deliverable_path_sections", "deliverable_scope_inputs"} <= PT.READING


def _fresh(tmp_path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(tmp_path / "state.sqlite")
    connection.executescript("CREATE TABLE judgment_ledger (id TEXT PRIMARY KEY);"
                             "INSERT INTO judgment_ledger VALUES ('jl_1');")
    connection.executescript((MIGRATIONS / "228_deliverable_curriculum.sql").read_text(encoding="utf-8"))
    return connection


def test_the_checks_and_the_append_only_triggers(tmp_path):
    with closing(_fresh(tmp_path)) as connection:
        connection.execute("INSERT INTO deliverable_scope_inputs (id, goal_id, kind, text_md, created_at) "
                           "VALUES ('i1', 'g', 'text', 'eigenvalues', 't')")
        for bad in (("i2", "g", "photo", "x"), ("i3", "g", "text", None)):
            with pytest.raises(sqlite3.IntegrityError):
                connection.execute("INSERT INTO deliverable_scope_inputs (id, goal_id, kind, text_md, created_at) "
                                   "VALUES (?, ?, ?, ?, 't')", bad)
        with pytest.raises(sqlite3.IntegrityError):  # a passage names its reading
            connection.execute("INSERT INTO deliverable_scope_inputs (id, goal_id, kind, created_at) "
                               "VALUES ('i4', 'g', 'passage', 't')")
        row = ("p1", "g", "fluency", "lo", "ext", "sec", "core", 0, "why", None, None, None, "k", "jl_1", "m", "v", "t")
        insert = ("INSERT INTO deliverable_path_sections (id, goal_id, depth, learning_object_id, extraction_id, "
                  "section_id, label, ordinal, reason, exercise_span_id, learner_override, commitment_id, state_key, "
                  "ledger_id, model, prompt_version, created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)")
        connection.execute(insert, row)
        with pytest.raises(sqlite3.IntegrityError):  # one judge row per (goal, depth, state, LO, section)
            connection.execute(insert, ("p2", *row[1:]))
        connection.execute(insert, ("p3", *row[1:10], "skip", *row[11:]))  # a learner row beside it
        for bad_label in (("p4", *row[1:6], "enrichment", *row[7:]), ("p5", *row[1:2], "deep", *row[3:])):
            with pytest.raises(sqlite3.IntegrityError):
                connection.execute(insert, bad_label)
        connection.execute("INSERT INTO deliverable_scope_resolutions (id, goal_id, origin, state_key, ledger_id, model, "
                           "prompt_version, created_at) VALUES ('r1', 'g', 'resolver', 'k', 'jl_1', 'm', 'v', 't')")
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute("INSERT INTO deliverable_scope_resolutions (id, goal_id, origin, state_key, ledger_id, "
                               "model, prompt_version, created_at) VALUES ('r2', 'g', 'judge', 'k', 'jl_1', 'm', 'v', 't')")
        for table in TABLES:
            with pytest.raises(sqlite3.IntegrityError, match="append-only"):
                connection.execute(f"UPDATE {table} SET goal_id = 'x'")
            with pytest.raises(sqlite3.IntegrityError, match="append-only"):
                connection.execute(f"DELETE FROM {table}")


def test_the_head_fixture_holds_exactly_228s_objects_in_rollback_mode():
    assert HEAD.read_bytes()[18:20] == b"\x01\x01"
    assert max(applied_versions(HEAD)) == max(m.version for m in discover_migrations()) == 228
    with closing(sqlite3.connect(f"file:{HEAD}?mode=ro", uri=True)) as connection:
        names = {row[0] for row in connection.execute("SELECT name FROM sqlite_master")}
        assert C0B_ADDED_OBJECTS <= names
        assert connection.execute("PRAGMA journal_mode").fetchone()[0] == "delete"
        for table in TABLES:
            assert connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] == 0
