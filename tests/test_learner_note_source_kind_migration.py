"""Curriculum C5's migration 231 (spec_deliverable_curriculum_v1 §10.2, §12 C5).

``learner_text_gaps.source_kind`` and ``learner_text_gap_jobs.source_kind``
gain ``learner_note`` (a linked note's snapshot, read for gaps by opt-in) in a
temp-then-rename rebuild under ``PRAGMA foreign_keys = OFF``, following 208 and
212 exactly (the FK-safe rebuild precedent). Every existing row survives with
its id and every column, the three tables that reference ``learner_text_gaps``
still resolve (``foreign_key_check`` is clean before and after), the
append-only triggers and indexes are back, and nothing else about the tables
changes. No table is new, so nothing new is classified; the head fixture holds
231 and no note text. The durability lane runs it with production pragmas
(WAL, ``synchronous=FULL``).
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
from tests.helpers import MIGRATION_HEAD_FIXTURE, migration_head

NOW = "2026-10-18T10:00:00Z"
KINDS_229 = ("tutor_question", "stuck_answer", "diagnosis", "workbench_text", "reader_formative", "hint_feedback")
TABLES = ("learner_text_gaps", "learner_text_gap_jobs", "learner_text_gap_reversals",
          "learner_gap_check_advances", "learner_gap_commitments")


def _database_at_229(tmp_path: Path) -> Path:
    through = tmp_path / "through_229"
    through.mkdir()
    for migration in discover_migrations():
        if migration.version <= 229:
            (through / migration.path.name).write_text(migration.path.read_text(encoding="utf-8"), encoding="utf-8")
    database = tmp_path / "state.sqlite"
    apply_migrations(database, migrations_dir=through)
    assert max(applied_versions(database)) == 229
    return database


def _seed(database: Path) -> None:
    with closing(connect(database)) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        for index, kind in enumerate(KINDS_229):
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
    database = _database_at_229(tmp_path)
    _seed(database)
    with closing(sqlite3.connect(database)) as connection:
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
    before = {table: _rows(database, table) for table in TABLES}
    columns = {table: _columns(database, table) for table in TABLES[:2]}
    objects = {table: _objects(database, table) for table in TABLES[:2]}
    with upgrade_allowance(UPGRADE_TEST_HELPER):
        applied = apply_migrations(database)
    # Learner data-relax 2's 230 (help_assists.work_md, not a table read here) lands first;
    # RW5d P3's 232 (help_assists and figure_predictions), curriculum C2b's 233 (learner_notes) and
    # teacher TE1's 234 (its own tables and source_tool_calls) follow; none is read here.
    # Follow-ups Nov 2's 235 (learner_text_gap_reversals) and teacher TE1b's 236 (router tables), not read here, follow too.
    assert [migration.version for migration in applied] == list(range(230, migration_head() + 1))
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
        for kind in (*KINDS_229, "learner_note"):
            connection.execute(
                "INSERT INTO learner_text_gap_jobs (id, source_kind, source_id, created_at, updated_at) "
                "VALUES (?, ?, 'ha_new', ?, ?)", (f"job_{kind}", kind, NOW, NOW))
        connection.execute(
            "INSERT INTO learner_text_gaps (id, source_kind, source_id, learner_text, chooser, context_judge, "
            "kind, action, algorithm_version, pipeline_version, created_at) VALUES "
            "('gap_hf', 'learner_note', 'ln_new', 'my note on eigenvalues', 'context_model', 'gap_reader', "
            "'none', 'none', 'mvp-0.27', 'v1', ?)", (NOW,))
        for bad in ("note", "learner_notes"):
            with pytest.raises(sqlite3.IntegrityError):
                connection.execute(
                    "INSERT INTO learner_text_gap_jobs (id, source_kind, source_id, created_at, updated_at) "
                    "VALUES (?, ?, 'q_2', ?, ?)", (f"job_bad_{bad}", bad, NOW, NOW))
        # One job and one gap per source, as before.
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                "INSERT INTO learner_text_gap_jobs (id, source_kind, source_id, created_at, updated_at) "
                "VALUES ('job_dup', 'learner_note', 'ha_new', ?, ?)", (NOW, NOW))
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


def test_231_widens_both_source_kinds_with_learner_note_and_keeps_every_row(tmp_path):
    _check_widened(_upgrade(tmp_path))


@pytest.mark.durability
def test_231_on_the_durability_lane(tmp_path):
    """Production pragmas: the rebuild is WAL-safe and FK-checked before commit."""

    database = _upgrade(tmp_path)
    with closing(sqlite3.connect(database)) as connection:
        assert connection.execute("PRAGMA journal_mode").fetchone()[0] == "wal"
    _check_widened(database)


def test_231_classifies_nothing_new():
    assert role_for_table("learner_text_gaps") is TableRole.RAW_LEDGER
    assert role_for_table("learner_text_gap_jobs") is TableRole.WORKFLOW
    sql = next(m for m in discover_migrations() if m.version == 231).path.read_text()
    created = {line.split()[2] for line in sql.splitlines() if line.startswith("CREATE TABLE")}
    assert created == {"learner_text_gaps__231", "learner_text_gap_jobs__231"}  # renamed onto the old names
    # AD's guard (spec §9.4): no AD operation reaches the gap jobs (unclassified there, so an AD read
    # of one is refused as unclassified); router objective RO2 registered the gaps themselves for its
    # card's rung H3 (PROTECTED: read only by the rules), and the notes' own tables stay PROTECTED.
    from learnloop.adaptive_difficulty import protected_tables as PT

    assert PT.role("learner_text_gaps") == PT.PROTECTED
    assert PT.read_verdict("learner_text_gaps", rules=None) is not None
    for table in ("learner_text_gap_jobs",):
        assert PT.role(table) is None, table
        assert PT.read_verdict(table, rules=None) == "an unclassified table"
    for table in ("learner_notes", "learner_note_links"):
        assert PT.role(table) == PT.PROTECTED, table


def test_231_adds_learner_note_and_nothing_else():
    sql = next(m for m in discover_migrations() if m.version == 231).path.read_text()
    assert sql.count("'reader_formative', 'hint_feedback', 'learner_note'") == 2
    assert "PRAGMA foreign_keys = OFF" in sql and sql.rstrip().endswith("PRAGMA foreign_keys = ON;")
    previous = next(m for m in discover_migrations() if m.version == 212).path.read_text()
    body = previous[previous.index("PRAGMA foreign_keys = OFF;"):previous.rindex("PRAGMA foreign_keys = ON;")]
    ours = sql[sql.index("PRAGMA foreign_keys = OFF;"):sql.rindex("PRAGMA foreign_keys = ON;")]
    # 212's rebuild, exactly, with the one kind more (and its source comment).
    normalized = ours.replace("__231", "__212").replace(", 'learner_note'", "").replace(
        " | learner_notes.id (learner_note: a linked note's snapshot)", "")
    assert normalized.strip() == body.strip()


def test_the_head_fixture_holds_231_in_rollback_mode_with_no_note_gap():
    head = MIGRATION_HEAD_FIXTURE / "state.sqlite"
    assert head.read_bytes()[18:20] == b"\x01\x01"
    assert 231 in applied_versions(head)
    with closing(sqlite3.connect(f"file:{head}?mode=ro", uri=True)) as connection:
        assert connection.execute("PRAGMA journal_mode").fetchone()[0] == "delete"
        for table in ("learner_text_gaps", "learner_text_gap_jobs"):
            sql = connection.execute("SELECT sql FROM sqlite_master WHERE name = ?", (table,)).fetchone()[0]
            assert "'learner_note'" in sql, table
            assert connection.execute(f"SELECT COUNT(*) FROM {table} WHERE source_kind = 'learner_note'"
                                      ).fetchone()[0] == 0
