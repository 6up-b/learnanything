"""Adaptive hints H2b's migration 212 (spec_adaptive_hints_v1 §9, G-H17).

``learner_text_gaps.source_kind`` and ``learner_text_gap_jobs.source_kind``
gain ``hint_feedback`` (the practice screen's "doesn't connect" text and
discriminating answers) in a temp-then-rename rebuild under ``PRAGMA
foreign_keys = OFF``, following 208 exactly. Every existing row survives with
its id and every column, the three tables that reference
``learner_text_gaps`` still resolve (``foreign_key_check`` is clean before and
after), the append-only triggers and indexes are back, and nothing else
about the tables changes. G-H17's deviation: this is the second widening
(208 carried the Reader's two kinds), recorded in the spec's §15. The
durability lane runs it with production pragmas (WAL, ``synchronous=FULL``).
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

NOW = "2026-10-18T10:00:00Z"
KINDS_211 = ("tutor_question", "stuck_answer", "diagnosis", "workbench_text", "reader_formative")
TABLES = ("learner_text_gaps", "learner_text_gap_jobs", "learner_text_gap_reversals",
          "learner_gap_check_advances", "learner_gap_commitments")


def _database_at_211(tmp_path: Path) -> Path:
    through = tmp_path / "through_211"
    through.mkdir()
    for migration in discover_migrations():
        if migration.version <= 211:
            (through / migration.path.name).write_text(migration.path.read_text(encoding="utf-8"), encoding="utf-8")
    database = tmp_path / "state.sqlite"
    apply_migrations(database, migrations_dir=through)
    assert max(applied_versions(database)) == 211
    return database


def _seed(database: Path) -> None:
    with closing(connect(database)) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        for index, kind in enumerate(KINDS_211):
            connection.execute(
                "INSERT INTO learner_text_gaps (id, source_kind, source_id, attempt_id, practice_item_id, "
                "anchor_learning_object_id, subject_id, learner_text, chooser, context_judge, context_kind, "
                "decider_kind, decider_json, kind, named_json, action, target_kind, target_id, target_subject_id, "
                "match_basis, edge_id, created_concept_id, created_learning_object_id, seed_practice_item_id, "
                "seed_status, detail_json, algorithm_version, pipeline_version, created_at) VALUES "
                "(?, ?, ?, ?, 'pi_1', 'lo_a', 'math', ?, 'context_model', 'gap_reader', 'misconception', "
                "'misconception', '{\"p\": 1}', 'misconception', '{\"belief_statement\": \"F(0) = 1\"}', "
                "'belief_sighting', 'durable', 'mc_1', 'math', 'judge', NULL, NULL, NULL, NULL, NULL, '{\"k\": [1]}', "
                "'mvp-0.27', 'learner-text-gaps-v1', ?)",
                (f"ltg_{index}", kind, f"src_{index}", f"att_{index}" if index else None,
                 f"why is it {index}?", f"2026-10-1{index}T09:00:00Z"),
            )
            connection.execute(
                "INSERT INTO learner_text_gap_jobs (id, source_kind, source_id, state, attempt_count, lease_owner, "
                "lease_expires_at, lease_epoch, not_before, last_error, payload_json, created_at, updated_at) "
                "VALUES (?, ?, ?, 'done', 2, 'w1', NULL, 3, NULL, 'boom', '{\"decided\": {}}', ?, ?)",
                (f"ltgj_{index}", kind, f"src_{index}", NOW, NOW),
            )
        connection.execute(
            "INSERT INTO learner_text_gap_reversals (id, gap_id, reversal, actor, detail_json, created_at) "
            "VALUES ('rev_1', 'ltg_0', 'undo_edge', 'learner', '{}', ?)", (NOW,))
        connection.execute(
            "INSERT INTO learner_gap_check_advances (id, gap_id, learning_object_id, intent, assumption_id, "
            "original_due, advanced_due, algorithm_version, created_at) VALUES "
            "('adv_1', 'ltg_3', 'lo_b', 'assumed', NULL, NULL, ?, 'mvp-0.27', ?)", (NOW, NOW))
        connection.execute(
            "INSERT INTO learner_gap_commitments (id, gap_id, learning_object_id, practice_item_id, "
            "first_review_due, algorithm_version, created_at) VALUES ('com_1', 'ltg_4', 'lo_b', NULL, ?, "
            "'mvp-0.27', ?)", (NOW, NOW))
        connection.commit()


def _rows(database: Path, table: str) -> list[tuple]:
    with closing(sqlite3.connect(database)) as connection:
        return connection.execute(f"SELECT * FROM {table} ORDER BY id").fetchall()


def _columns(database: Path, table: str) -> list[tuple]:
    with closing(sqlite3.connect(database)) as connection:
        return [tuple(row[1:]) for row in connection.execute(f"PRAGMA table_info({table})")]


def _objects(database: Path, table: str) -> dict[tuple[str, str], str | None]:
    with closing(sqlite3.connect(database)) as connection:
        return {(row[0], row[1]): row[2] for row in connection.execute(
            "SELECT type, name, sql FROM sqlite_master WHERE tbl_name = ? AND type IN ('index', 'trigger')",
            (table,))}


def _upgrade(tmp_path: Path) -> Path:
    database = _database_at_211(tmp_path)
    _seed(database)
    with closing(sqlite3.connect(database)) as connection:
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
    before = {table: _rows(database, table) for table in TABLES}
    columns = {table: _columns(database, table) for table in TABLES[:2]}
    objects = {table: _objects(database, table) for table in TABLES[:2]}
    with upgrade_allowance(UPGRADE_TEST_HELPER):
        applied = apply_migrations(database)
    assert [migration.version for migration in applied][0] == 212
    assert {table: _rows(database, table) for table in TABLES} == before  # every row, id and value survives
    for table, shape in columns.items():
        assert _columns(database, table) == shape  # the same columns, types, defaults and keys
    for table, names in objects.items():
        assert _objects(database, table) == names  # every index and trigger is back, the same definition
    return database


def _check_widened(database: Path) -> None:
    with closing(sqlite3.connect(database)) as connection:
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        connection.execute("PRAGMA foreign_keys = ON")
        for kind in (*KINDS_211, "hint_feedback"):
            connection.execute(
                "INSERT INTO learner_text_gap_jobs (id, source_kind, source_id, created_at, updated_at) "
                "VALUES (?, ?, 'ha_new', ?, ?)", (f"job_{kind}", kind, NOW, NOW))
        connection.execute(
            "INSERT INTO learner_text_gaps (id, source_kind, source_id, learner_text, chooser, context_judge, "
            "kind, action, algorithm_version, pipeline_version, created_at) VALUES "
            "('gap_hf', 'hint_feedback', 'ha_new', 'that +1 is where I am', 'context_model', 'gap_reader', "
            "'none', 'none', 'mvp-0.27', 'v1', ?)", (NOW,))
        for bad in ("workbench_stuck", "hint_reply"):
            with pytest.raises(sqlite3.IntegrityError):
                connection.execute(
                    "INSERT INTO learner_text_gap_jobs (id, source_kind, source_id, created_at, updated_at) "
                    "VALUES (?, ?, 'q_2', ?, ?)", (f"job_bad_{bad}", bad, NOW, NOW))
        # One job and one gap per source, as before.
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                "INSERT INTO learner_text_gap_jobs (id, source_kind, source_id, created_at, updated_at) "
                "VALUES ('job_dup', 'hint_feedback', 'ha_new', ?, ?)", (NOW, NOW))
        with pytest.raises(sqlite3.IntegrityError, match="append-only"):
            connection.execute("UPDATE learner_text_gaps SET kind = 'slip' WHERE id = 'gap_hf'")
        with pytest.raises(sqlite3.IntegrityError, match="append-only"):
            connection.execute("DELETE FROM learner_text_gaps WHERE id = 'ltg_0'")
        # The referencing tables still resolve to the rebuilt table.
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                "INSERT INTO learner_text_gap_reversals (id, gap_id, reversal, actor, created_at) "
                "VALUES ('rev_x', 'ltg_missing', 'undo_edge', 'learner', ?)", (NOW,))
        connection.execute(
            "INSERT INTO learner_text_gap_reversals (id, gap_id, reversal, actor, created_at) "
            "VALUES ('rev_2', 'gap_hf', 'not_this_belief', 'learner', ?)", (NOW,))
        connection.rollback()


def test_212_widens_both_source_kinds_with_hint_feedback_and_keeps_every_row(tmp_path):
    _check_widened(_upgrade(tmp_path))


@pytest.mark.durability
def test_212_on_the_durability_lane(tmp_path):
    """Production pragmas: the rebuild is WAL-safe and FK-checked before commit."""

    database = _upgrade(tmp_path)
    with closing(sqlite3.connect(database)) as connection:
        assert connection.execute("PRAGMA journal_mode").fetchone()[0] == "wal"
    _check_widened(database)


def test_212_classifies_nothing_new():
    assert role_for_table("learner_text_gaps") is TableRole.RAW_LEDGER
    assert role_for_table("learner_text_gap_jobs") is TableRole.WORKFLOW
    sql = next(m for m in discover_migrations() if m.version == 212).path.read_text()
    created = {line.split()[2] for line in sql.splitlines() if line.startswith("CREATE TABLE")}
    assert created == {"learner_text_gaps__212", "learner_text_gap_jobs__212"}  # renamed onto the old names


def test_212_adds_hint_feedback_and_nothing_else():
    sql = next(m for m in discover_migrations() if m.version == 212).path.read_text()
    assert sql.count("'workbench_text', 'reader_formative', 'hint_feedback'") == 2
    assert "PRAGMA foreign_keys = OFF" in sql and sql.rstrip().endswith("PRAGMA foreign_keys = ON;")
    previous = next(m for m in discover_migrations() if m.version == 208).path.read_text()
    body = previous[previous.index("PRAGMA foreign_keys = OFF;"):previous.index("ALTER TABLE reader_authored")]
    ours = sql[sql.index("PRAGMA foreign_keys = OFF;"):sql.rindex("PRAGMA foreign_keys = ON;")]
    # 208's rebuild, exactly, with the one kind more (and its source comment).
    normalized = ours.replace("__212", "__208").replace(", 'hint_feedback'", "").replace(
        " |\n  -- help_assists.id (hint_feedback)", "")
    assert normalized.strip() == body.strip()
