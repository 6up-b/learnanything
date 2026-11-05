"""Reader RW5d P3: migration 232 rebuilds help_assists for figures as a help kind (spec §13.2),
and figure_predictions for predictions made inside an attempt (Codex review F7, F9).

``help_assists`` (RAW_LEDGER, migration 210; ``work_md`` 230) is rebuilt
temp-then-rename with every row and id kept: ``assist_kind`` gains
``figure``, ``hint_kind`` gains ``explore_figure``, ``request`` gains
``take_step`` and a nullable ``figure_id`` (set once) is added, with an index.
No table's foreign key names help_assists, so the rebuild is FK-safe; the
append-only and identity triggers are recreated (the identity trigger also
fixes ``figure_id`` once set). No new table, so no role or replayer;
``help_assists`` is not an AD-readable table, so no column class.
"""

from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path

import pytest

from learnloop.adaptive_difficulty import protected_tables as PT
from learnloop.db.migrate import applied_versions, discover_migrations
from learnloop.db.stores import help_assists as store
from learnloop.db.table_roles import TableRole, role_for_table
from tests.test_ro1_availability import RO1_ALTERED_TABLES
from tests.test_learner_gap_unlinked_migration import UNLINKED_ALTERED_TABLES
from tests.test_learner_notes_vault_origin_migration import C2B_ALTERED_TABLES

# TE1's 234 and TE1b's 236 follow on the way to head (composed in tests/test_teacher_te1b_migration.py).
from tests.test_teacher_te1b_migration import TE1_AND_TE1B_ADDED_OBJECTS as TE1_ADDED_OBJECTS
from tests.test_teacher_te1b_migration import TE1_AND_TE1B_ALTERED_TABLES as TE1_ALTERED_TABLES
from tests.test_figure_prefetch_migration import P5_ADDED_OBJECTS
from tests.test_data_capture_migration import DATA_CAPTURE_ADDED_OBJECTS
from tests.test_followup_migration import FOLLOWUP_ADDED_OBJECTS
from tests.test_hypothesis_marks_migration import MARKS_ADDED_OBJECTS
from tests.test_router_objective_migration import RO0_ADDED_OBJECTS
from tests.test_mobile_jobs_migration import M2A_ADDED_OBJECTS
from tests.test_rw5c_migration import RW5C_ADDED_OBJECTS

HEAD = Path(__file__).resolve().parents[1] / "fixtures" / "migration_head_244" / "state.sqlite"
#: What 232 alters and adds: the earlier migrations' "nothing else changed"
#: diffs on the way to head read these.
#: Codex review F7/F9: figure_predictions is rebuilt too (nullable
#: extraction_id, assist_id, explained_at; the explanation trigger fixes assist_id).
P3_ALTERED_TABLES = frozenset({"help_assists", "help_assists_identity_fixed", "figure_predictions",
                               "figure_predictions_explanation_once"})
P3_ADDED_OBJECTS = frozenset({"idx_help_assists_figure", "idx_figure_predictions_assist"})


def test_232_is_the_figures_migration_and_help_assists_stays_a_raw_ledger():
    names = {migration.version: migration.path.name for migration in discover_migrations()}
    assert names[232] == "232_help_assist_figures.sql"
    assert names[230] == "230_help_assist_work_md.sql"
    assert role_for_table("help_assists") == TableRole.RAW_LEDGER
    assert "help_assists" not in PT.ROLES


def _at_231(tmp_path: Path) -> Path:
    # Curriculum C5's 231 landed first (232 kept its number at P3's landing).
    from learnloop.db.migrate import apply_migrations

    through = tmp_path / "through_231"
    through.mkdir()
    for migration in discover_migrations():
        if migration.version <= 231:
            (through / migration.path.name).write_text(migration.path.read_text(encoding="utf-8"), encoding="utf-8")
    database = tmp_path / "state.sqlite"
    apply_migrations(database, migrations_dir=through)
    assert max(applied_versions(database)) == 231
    return database


def _schema(database: Path) -> dict[str, str]:
    with closing(sqlite3.connect(database)) as connection:
        return {name: sql for name, sql in connection.execute(
            "SELECT name, sql FROM sqlite_master WHERE sql IS NOT NULL")}


def test_232_widens_three_checks_adds_figure_id_and_keeps_every_row(tmp_path):
    from learnloop.db.migrate import UPGRADE_TEST_HELPER, apply_migrations, upgrade_allowance

    database = _at_231(tmp_path)
    with closing(sqlite3.connect(database)) as connection:
        connection.execute(
            "INSERT INTO help_assists (id, surface, assist_kind, hint_kind, level, chooser, shown, requested_at, "
            "work_hash, work_chars, work_md, counted_by, request) VALUES ('ha_old', 'practice', 'hint', "
            "'next_step', 3, 'decider', 1, '2026-10-01T00:00:00Z', 'h', 12, 'my draft', 'server', 'more')")
        connection.commit()
        before_row = connection.execute("SELECT * FROM help_assists").fetchone()
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute("INSERT INTO help_assists (id, surface, assist_kind, chooser, shown, requested_at) "
                               "VALUES ('ha_bad', 'practice', 'figure', 'none', 1, 't')")
    before = _schema(database)
    with upgrade_allowance(UPGRADE_TEST_HELPER):
        # Curriculum C2b's 233 (learner_notes) and teacher TE1's 234 (its own tables and source_tool_calls)
        # follow on the way to head; neither is read here.
        # Follow-ups Nov 2's 235 (learner_text_gap_reversals) and teacher TE1b's 236 (router tables), not read here, follow too.
        assert [migration.version for migration in apply_migrations(database)] == [232, 233, 234, 235, 236, 237, 238, 239, 240, 241, 242, 243, 244]
    after = _schema(database)
    assert set(after) - set(before) - TE1_ADDED_OBJECTS - P5_ADDED_OBJECTS - RW5C_ADDED_OBJECTS - M2A_ADDED_OBJECTS - DATA_CAPTURE_ADDED_OBJECTS - FOLLOWUP_ADDED_OBJECTS - MARKS_ADDED_OBJECTS - RO0_ADDED_OBJECTS == set(P3_ADDED_OBJECTS)
    assert {name for name in before if before[name] != after.get(name)} == set(P3_ALTERED_TABLES) | set(
        C2B_ALTERED_TABLES) | (TE1_ALTERED_TABLES | RO1_ALTERED_TABLES) | UNLINKED_ALTERED_TABLES
    with closing(sqlite3.connect(database)) as connection:
        columns = [row[1] for row in connection.execute("PRAGMA table_info(help_assists)")]
        assert columns[-1] == "figure_id" and tuple(columns) == store.COLUMNS
        row = connection.execute("SELECT * FROM help_assists").fetchone()
        assert tuple(row)[:-1] == tuple(before_row) and row[-1] is None
        # The widened CHECKs take the figure row, the chooser's kind and the take step.
        connection.execute(
            "INSERT INTO help_assists (id, surface, assist_kind, hint_kind, level, chooser, shown, requested_at, "
            "counted_by, figure_id) VALUES ('ha_fig', 'practice', 'figure', 'explore_figure', 2, 'decider', 1, "
            "'t', 'server', 'fig_1')")
        connection.execute(
            "INSERT INTO help_assists (id, surface, assist_kind, level, chooser, shown, requested_at, counted_by, "
            "request) VALUES ('ha_take', 'practice', 'figure', 2, 'none', 1, 't', 'server', 'take_step')")
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute("INSERT INTO help_assists (id, surface, assist_kind, chooser, shown, requested_at) "
                               "VALUES ('ha_bad', 'practice', 'sketch', 'none', 1, 't')")
        # figure_id is set once: NULL to a value, never moved.
        connection.execute("UPDATE help_assists SET figure_id = 'fig_2' WHERE id = 'ha_take'")
        with pytest.raises(sqlite3.IntegrityError, match="fixed"):
            connection.execute("UPDATE help_assists SET figure_id = 'fig_3' WHERE id = 'ha_take'")
        with pytest.raises(sqlite3.IntegrityError, match="append-only"):
            connection.execute("DELETE FROM help_assists")
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []


def test_232_rebuilds_figure_predictions_with_every_row_and_the_attempt_link(tmp_path):
    """Codex review F7, F9: extraction_id nullable (an attempt host's
    illustration has no home), assist_id (the attempt's figure row, fixed)
    and explained_at (set once with the explanation); every row and id kept."""

    from learnloop.db.migrate import UPGRADE_TEST_HELPER, apply_migrations, upgrade_allowance
    from learnloop.db.stores import figures as figure_store

    database = _at_231(tmp_path)
    with closing(sqlite3.connect(database)) as connection:
        for figure_id in ("fig_old", "fig_new"):
            connection.execute(
                "INSERT INTO interactive_figures (id, extraction_id, origin, spec_version, verification, "
                "prompt_version, input_hash, created_at) VALUES (?, 'ext', 'selection', 'ifs-v1', 'failed', 'p', "
                "'h', 't')", (figure_id,))
        connection.execute(
            "INSERT INTO figure_predictions (id, figure_id, extraction_id, prediction_index, learner_answer, "
            "observed_json, matched, explanation_text, created_at) VALUES ('fp_old', 'fig_old', 'ext', 0, 'up', "
            "'{}', 0, 'it grew', '2026-10-01T00:00:00Z')")
        connection.commit()
        before = tuple(connection.execute("SELECT * FROM figure_predictions").fetchone())
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                "INSERT INTO figure_predictions (id, figure_id, extraction_id, prediction_index, learner_answer, "
                "observed_json, matched, created_at) VALUES ('fp_x', 'fig_old', NULL, 1, 'up', '{}', 1, 't')")
    with upgrade_allowance(UPGRADE_TEST_HELPER):
        apply_migrations(database)
    with closing(sqlite3.connect(database)) as connection:
        columns = tuple(row[1] for row in connection.execute("PRAGMA table_info(figure_predictions)"))
        assert columns == figure_store.PREDICTION_COLUMNS
        assert tuple(connection.execute("SELECT * FROM figure_predictions").fetchone()) == (*before, None, None)
        connection.execute(
            "INSERT INTO figure_predictions (id, figure_id, extraction_id, prediction_index, learner_answer, "
            "observed_json, matched, created_at, assist_id) VALUES ('fp_new', 'fig_new', NULL, 0, 'up', '{}', 0, "
            "'t', 'ha_1')")
        assert figure_store.set_explanation(connection, "fp_new", "it fell", at="t2")
        assert connection.execute("SELECT explanation_text, explained_at FROM figure_predictions WHERE id = 'fp_new'"
                                  ).fetchone() == ("it fell", "t2")
        with pytest.raises(sqlite3.IntegrityError, match="append-only"):
            connection.execute("UPDATE figure_predictions SET explained_at = 't3' WHERE id = 'fp_new'")
        with pytest.raises(sqlite3.IntegrityError, match="append-only"):
            connection.execute("UPDATE figure_predictions SET assist_id = 'ha_2' WHERE id = 'fp_old'")
        with pytest.raises(sqlite3.IntegrityError, match="append-only"):
            connection.execute("DELETE FROM figure_predictions")
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"


def test_the_check_values_are_the_kinds_the_code_writes():
    from learnloop.hints.kinds import KIND_NAMES

    sql = (Path(__file__).resolve().parents[1] / "migrations" / "232_help_assist_figures.sql").read_text()
    for kind in KIND_NAMES:
        assert f"'{kind}'" in sql
    assert "'explore_figure'" in sql and "'take_step'" in sql and "'figure'" in sql


def test_the_head_fixture_holds_232_in_rollback_mode():
    # The head is teacher TE1b's 236 now (rebuilt from follow-ups Nov 2's 235 head with only 236 applied); it holds 232.
    assert HEAD.read_bytes()[18:20] == b"\x01\x01"
    assert 232 in applied_versions(HEAD)
    assert max(applied_versions(HEAD)) == max(m.version for m in discover_migrations()) == 244
    with closing(sqlite3.connect(f"file:{HEAD}?mode=ro", uri=True)) as connection:
        columns = [row[1] for row in connection.execute("PRAGMA table_info(help_assists)")]
        assert columns[-1] == "figure_id"
        assert connection.execute("PRAGMA journal_mode").fetchone()[0] == "delete"
        assert connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'index' AND name = 'idx_help_assists_figure'").fetchone()
        assert [row[1] for row in connection.execute("PRAGMA table_info(figure_predictions)")][-2:] == [
            "assist_id", "explained_at"]


@pytest.mark.durability
def test_232_on_the_durability_lane(tmp_path):
    from learnloop.db.migrate import UPGRADE_TEST_HELPER, apply_migrations, upgrade_allowance

    database = _at_231(tmp_path)
    with upgrade_allowance(UPGRADE_TEST_HELPER):
        assert [migration.version for migration in apply_migrations(database)] == [232, 233, 234, 235, 236, 237, 238, 239, 240, 241, 242, 243, 244]
    with closing(sqlite3.connect(database)) as connection:
        assert connection.execute("PRAGMA journal_mode").fetchone()[0] == "wal"
        store.insert_assist(connection, {"id": "ha_d", "surface": "practice", "assist_kind": "figure",
                                         "chooser": "none", "shown": 1, "requested_at": "t", "level": 2,
                                         "counted_by": "server", "figure_id": "fig_d"})
        connection.commit()
        assert connection.execute("SELECT figure_id FROM help_assists").fetchone()[0] == "fig_d"
