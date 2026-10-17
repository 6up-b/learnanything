"""RW1b's migration 208 (spec_reader_workbench_v1 §3.4 item 13, G36).

``learner_text_gaps.source_kind`` and ``learner_text_gap_jobs.source_kind``
are widened with BOTH reader workbench kinds (``workbench_text``,
``reader_formative``) in one temp-then-rename rebuild under ``PRAGMA
foreign_keys = OFF``. Every existing row survives with its id and every
column, the three tables that reference ``learner_text_gaps`` still resolve
(``foreign_key_check`` is clean), the append-only triggers and indexes are
back, and nothing else about the tables changes. The same migration adds
``reader_authored_questions.answer_basis`` (NULL on existing rows) and the
UNIQUE selection reuse key. The durability lane runs it with production
pragmas (WAL, ``synchronous=FULL``).
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

NOW = "2026-10-17T10:00:00Z"


def _database_at_207(tmp_path: Path) -> Path:
    through = tmp_path / "through_207"
    through.mkdir()
    for migration in discover_migrations():
        if migration.version <= 207:
            (through / migration.path.name).write_text(migration.path.read_text(encoding="utf-8"), encoding="utf-8")
    database = tmp_path / "state.sqlite"
    apply_migrations(database, migrations_dir=through)
    assert max(applied_versions(database)) == 207
    return database


def _seed(database: Path) -> None:
    with closing(connect(database)) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        for index, kind in enumerate(("tutor_question", "stuck_answer", "diagnosis")):
            connection.execute(
                "INSERT INTO learner_text_gaps (id, source_kind, source_id, attempt_id, practice_item_id, "
                "anchor_learning_object_id, subject_id, learner_text, chooser, context_judge, context_kind, "
                "decider_kind, decider_json, kind, named_json, action, target_kind, target_id, target_subject_id, "
                "match_basis, edge_id, created_concept_id, created_learning_object_id, seed_practice_item_id, "
                "seed_status, detail_json, algorithm_version, pipeline_version, created_at) VALUES "
                "(?, ?, ?, ?, 'pi_1', 'lo_a', 'math', ?, 'context_model', 'tutor', 'prerequisite', 'prerequisite', "
                "'{\"p\": 1}', 'prerequisite', '{\"prerequisite_name\": \"limits\"}', 'matched_prerequisite', "
                "'learning_object', 'lo_b', 'math', 'judge', 'edge_1', NULL, NULL, NULL, NULL, '{\"k\": [1]}', "
                "'mvp-0.16', 'learner-text-gaps-v1', ?)",
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
            "('adv_1', 'ltg_1', 'lo_b', 'assumed', NULL, NULL, ?, 'mvp-0.16', ?)", (NOW, NOW))
        connection.execute(
            "INSERT INTO learner_gap_commitments (id, gap_id, learning_object_id, practice_item_id, "
            "first_review_due, algorithm_version, created_at) VALUES ('com_1', 'ltg_2', 'lo_b', NULL, ?, "
            "'mvp-0.16', ?)", (NOW, NOW))
        connection.execute(
            "INSERT INTO reader_authored_questions (id, extraction_id, section_id, question_md, expected_answer_md, "
            "prompt_version, created_at, updated_at) VALUES ('raq_1', 'ext1', 'u1', 'Q?', 'A.', 'v1', ?, ?)",
            (NOW, NOW))
        connection.commit()


def _rows(database: Path, table: str) -> list[tuple]:
    with closing(sqlite3.connect(database)) as connection:
        return connection.execute(f"SELECT * FROM {table} ORDER BY id").fetchall()


def _columns(database: Path, table: str) -> list[tuple]:
    with closing(sqlite3.connect(database)) as connection:
        return [tuple(row[1:]) for row in connection.execute(f"PRAGMA table_info({table})")]


def _objects(database: Path, table: str) -> set[tuple[str, str]]:
    with closing(sqlite3.connect(database)) as connection:
        return {(row[0], row[1]) for row in connection.execute(
            "SELECT type, name FROM sqlite_master WHERE tbl_name = ? AND type IN ('index', 'trigger')", (table,))}


def _upgrade(tmp_path: Path) -> tuple[Path, dict[str, list[tuple]], dict[str, list[tuple]]]:
    database = _database_at_207(tmp_path)
    _seed(database)
    tables = ("learner_text_gaps", "learner_text_gap_jobs", "learner_text_gap_reversals",
              "learner_gap_check_advances", "learner_gap_commitments")
    before = {table: _rows(database, table) for table in tables}
    columns = {table: _columns(database, table) for table in ("learner_text_gaps", "learner_text_gap_jobs")}
    objects = {table: _objects(database, table) for table in ("learner_text_gaps", "learner_text_gap_jobs")}
    with upgrade_allowance(UPGRADE_TEST_HELPER):
        applied = apply_migrations(database)
    assert [migration.version for migration in applied] == [208]
    after = {table: _rows(database, table) for table in tables}
    assert after == before  # every row, id and column value survives
    for table, shape in columns.items():
        assert _columns(database, table) == shape  # the same columns, types, defaults and keys
    for table, names in objects.items():
        assert _objects(database, table) == names  # every index and trigger is back
    return database, before, after


def _check_widened(database: Path) -> None:
    with closing(sqlite3.connect(database)) as connection:
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        connection.execute("PRAGMA foreign_keys = ON")
        for kind in ("reader_formative", "workbench_text"):
            connection.execute(
                "INSERT INTO learner_text_gap_jobs (id, source_kind, source_id, created_at, updated_at) "
                "VALUES (?, ?, 'q_1', ?, ?)", (f"job_{kind}", kind, NOW, NOW))
            connection.execute(
                "INSERT INTO learner_text_gaps (id, source_kind, source_id, learner_text, chooser, context_judge, "
                "kind, action, algorithm_version, pipeline_version, created_at) VALUES "
                "(?, ?, 'q_1', 'my next step', 'context_model', 'gap_reader', 'none', 'none', 'mvp-0.27', 'v1', ?)",
                (f"gap_{kind}", kind, NOW))
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                "INSERT INTO learner_text_gap_jobs (id, source_kind, source_id, created_at, updated_at) "
                "VALUES ('job_bad', 'workbench_stuck', 'q_2', ?, ?)", (NOW, NOW))
        with pytest.raises(sqlite3.IntegrityError, match="append-only"):
            connection.execute("UPDATE learner_text_gaps SET kind = 'slip' WHERE id = 'ltg_0'")
        with pytest.raises(sqlite3.IntegrityError, match="append-only"):
            connection.execute("DELETE FROM learner_text_gaps WHERE id = 'ltg_0'")
        # A reversal still needs a real gap: the foreign key resolves to the rebuilt table.
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                "INSERT INTO learner_text_gap_reversals (id, gap_id, reversal, actor, created_at) "
                "VALUES ('rev_x', 'ltg_missing', 'undo_edge', 'learner', ?)", (NOW,))
        connection.execute(
            "INSERT INTO learner_text_gap_reversals (id, gap_id, reversal, actor, created_at) "
            "VALUES ('rev_2', 'gap_reader_formative', 'not_this_belief', 'learner', ?)", (NOW,))
        # answer_basis: NULL on the existing row; only source or model.
        assert connection.execute(
            "SELECT answer_basis FROM reader_authored_questions WHERE id = 'raq_1'").fetchone() == (None,)
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute("UPDATE reader_authored_questions SET answer_basis = 'guess' WHERE id = 'raq_1'")
        # The selection reuse key is unique; section rows are not touched by it.
        insert = ("INSERT INTO reader_authored_questions (id, extraction_id, section_id, question_md, "
                  "expected_answer_md, prompt_version, scope_kind, question_style, anchor_span_ids_json, "
                  "answer_basis, created_at, updated_at) VALUES (?, 'ext1', 'u1', 'Q?', 'A.', 'rw1b-v1', ?, "
                  "'next_step', '[\"s1\"]', 'source', ?, ?)")
        connection.execute(insert, ("raq_sel_1", "selection", NOW, NOW))
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(insert, ("raq_sel_2", "selection", NOW, NOW))
        connection.execute(insert, ("raq_sec_2", "section", NOW, NOW))
        connection.rollback()


def test_208_widens_both_source_kinds_and_keeps_every_row(tmp_path):
    database, _before, _after = _upgrade(tmp_path)
    _check_widened(database)


@pytest.mark.durability
def test_208_on_the_durability_lane(tmp_path):
    """Production pragmas: the rebuild is WAL-safe and FK-checked before commit."""

    database, _before, _after = _upgrade(tmp_path)
    with closing(sqlite3.connect(database)) as connection:
        assert connection.execute("PRAGMA journal_mode").fetchone()[0] == "wal"
    _check_widened(database)


def test_208_keeps_the_table_roles():
    assert role_for_table("learner_text_gaps") is TableRole.RAW_LEDGER
    assert role_for_table("learner_text_gap_jobs") is TableRole.WORKFLOW
    assert role_for_table("reader_authored_questions") is not None


def test_the_migration_names_both_kinds_in_one_rebuild():
    sql = next(m for m in discover_migrations() if m.version == 208).path.read_text()
    assert sql.count("'workbench_text', 'reader_formative'") == 2
    assert "PRAGMA foreign_keys = OFF" in sql
    # No other migration widens these CHECKs again.
    later = [m for m in discover_migrations() if m.version > 208]
    assert not any("learner_text_gaps__" in m.path.read_text() for m in later)
