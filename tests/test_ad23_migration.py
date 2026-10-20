"""Adaptive difficulty AD2+AD3's migration 214 (spec_adaptive_difficulty_v1 §11.2; docs/reviews/adaptive-difficulty-ad23.md).

The 213 -> 214 upgrade adds exactly §11.2's AD2/AD3 tables and alters none:
``ad_selections`` and ``ad_dose_offers`` (RAW_LEDGER, append-only by trigger),
``ad_commission_results``, ``ad_relatedness_runs`` and
``ad_coupling_versions`` (RECEIPT, append-only), ``ad_state`` and
``ad_attempt_trace`` (DERIVED, the AD replayer) and ``item_forecast_scores``
(DERIVED, the forecast-score replayer). Every pre-existing row is unchanged.
The head fixture is at 214 in rollback mode; the durability lane runs the same
upgrade under WAL; the FK check is clean.
"""

from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path

import pytest

from learnloop.db.connection import connect
from learnloop.db.migrate import UPGRADE_TEST_HELPER, applied_versions, apply_migrations, discover_migrations, \
    upgrade_allowance
from learnloop.db.table_roles import TableRole, role_for_table

HEAD = Path(__file__).resolve().parents[1] / "fixtures" / "migration_head_214" / "state.sqlite"
NEW_TABLES = {"ad_selections", "ad_commission_results", "ad_dose_offers", "ad_relatedness_runs",
              "ad_coupling_versions", "ad_state", "ad_attempt_trace", "item_forecast_scores"}
#: What 214 adds (the earlier migrations' "nothing else changed" diffs on the way to head read it).
AD23_ADDED_OBJECTS = frozenset(NEW_TABLES | {
    "ad_selections_no_update", "ad_selections_no_delete", "idx_ad_selections_cell", "idx_ad_selections_block",
    "ad_commission_results_no_update", "ad_commission_results_no_delete",
    "ad_dose_offers_no_update", "ad_dose_offers_no_delete", "idx_ad_dose_offers_draw", "idx_ad_dose_offers_created",
    "ad_relatedness_runs_no_update", "ad_relatedness_runs_no_delete", "idx_ad_relatedness_runs_subject",
    "ad_coupling_versions_no_update", "ad_coupling_versions_no_delete",
    "sqlite_autoindex_ad_selections_1", "sqlite_autoindex_ad_selections_2",
    "sqlite_autoindex_ad_commission_results_1", "sqlite_autoindex_ad_commission_results_2",
    "sqlite_autoindex_ad_dose_offers_1", "sqlite_autoindex_ad_dose_offers_2",
    "sqlite_autoindex_ad_relatedness_runs_1", "sqlite_autoindex_ad_relatedness_runs_2",
    "sqlite_autoindex_ad_coupling_versions_1", "sqlite_autoindex_ad_coupling_versions_2",
    "sqlite_autoindex_ad_state_1", "sqlite_autoindex_ad_attempt_trace_1", "sqlite_autoindex_item_forecast_scores_1",
})
ROLES = {
    "ad_selections": TableRole.RAW_LEDGER, "ad_dose_offers": TableRole.RAW_LEDGER,
    "ad_commission_results": TableRole.RECEIPT, "ad_relatedness_runs": TableRole.RECEIPT,
    "ad_coupling_versions": TableRole.RECEIPT, "ad_state": TableRole.DERIVED, "ad_attempt_trace": TableRole.DERIVED,
    "item_forecast_scores": TableRole.DERIVED,
}


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


def _rows(database: Path) -> dict[str, list[tuple]]:
    with closing(sqlite3.connect(database)) as connection:
        tables = [row[0] for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%' ORDER BY name")]
        return {table: sorted(connection.execute(f"SELECT * FROM {table}").fetchall(), key=repr)
                for table in tables if table != "schema_migrations"}


def _upgrade(tmp_path: Path) -> Path:
    database = _database_at(tmp_path, 213)
    with closing(sqlite3.connect(database)) as connection:
        connection.execute(
            "INSERT INTO practice_attempts(id, practice_item_id, learning_object_id, practice_mode, attempt_type, "
            "created_at) VALUES ('att_old', 'pi', 'lo', 'short_answer', 'independent_attempt', '2026-10-01T00:00:00Z')")
        connection.commit()
    before = _schema(database)
    rows_before = _rows(database)
    with upgrade_allowance(UPGRADE_TEST_HELPER):
        applied = apply_migrations(database)
    assert [migration.version for migration in applied] == [214]
    after = _schema(database)
    assert set(after) - set(before) == AD23_ADDED_OBJECTS
    assert {name for name in before if before[name] != after.get(name)} == set(), "214 alters no existing object"
    rows_after = _rows(database)
    assert {table: rows for table, rows in rows_after.items() if table in rows_before} == rows_before
    assert all(not rows_after[table] for table in NEW_TABLES)
    return database


def _check(database: Path) -> None:
    with closing(connect(database)) as connection:
        connection.execute(
            "INSERT INTO ad_selections(id, decision_key, kind, view, mode, support_json, excluded_json, "
            "constants_json, seed, empty_support, state_hash, versions_json, algorithm_version, created_at) VALUES "
            "('s1', 'serve:b:1', 'serve', 'subject', 'band', '[]', '[]', '{}', 'seed', 0, 'h', '{}', 'mvp-0.28', 't')")
        with pytest.raises(sqlite3.IntegrityError):  # the vocabulary of modes
            connection.execute(
                "INSERT INTO ad_selections(id, decision_key, kind, view, mode, support_json, excluded_json, "
                "constants_json, seed, empty_support, state_hash, versions_json, algorithm_version, created_at) "
                "VALUES ('s2', 'k2', 'serve', 'subject', 'greedy', '[]', '[]', '{}', 's', 0, 'h', '{}', 'v', 't')")
        connection.execute(
            "INSERT INTO ad_commission_results(id, selection_id, practice_item_id, p_bar, status, state_hash, "
            "created_at) VALUES ('c1', 's1', 'pi', 0.7, 'in_band', 'h', 't')")
        with pytest.raises(sqlite3.IntegrityError):  # foreign key to its selection
            connection.execute(
                "INSERT INTO ad_commission_results(id, selection_id, practice_item_id, p_bar, status, state_hash, "
                "created_at) VALUES ('c2', 'missing', 'pi2', 0.7, 'in_band', 'h', 't')")
        connection.execute(
            "INSERT INTO ad_dose_offers(id, row_kind, draw_key, chosen_variant, created_at) VALUES "
            "('d1', 'draw', 'visit:section', 'none', 't')")
        connection.execute("INSERT INTO ad_dose_offers(id, row_kind, draw_id, created_at) VALUES "
                           "('d2', 'dismissed', 'd1', 't')")
        for bad in ("INSERT INTO ad_dose_offers(id, row_kind, created_at) VALUES ('d3', 'draw', 't')",
                    "INSERT INTO ad_dose_offers(id, row_kind, draw_key, created_at) VALUES ('d4', 'taken', 'x', 't')",
                    "INSERT INTO ad_dose_offers(id, row_kind, draw_key, chosen_variant, created_at) VALUES "
                    "('d5', 'draw', 'k5', 'extra_dwell', 't')"):
            with pytest.raises(sqlite3.IntegrityError):
                connection.execute(bad)
        connection.execute(
            "INSERT INTO ad_relatedness_runs(id, run_key, subject_id, input_hash, units_json, judgment_ids_json, "
            "status, prompt_version, created_at) VALUES ('r1', 'subj:h', 'subj', 'h', '[]', '[]', 'ok', 'v', 't')")
        connection.execute(
            "INSERT INTO ad_coupling_versions(id, subject_id, version, coupling_version, run_ids_json, adopted_by, "
            "adopted_at) VALUES ('v1', 'subj', 1, 'subj:v1', '[\"r1\"]', 'owner_backfill', 't')")
        for statement in ("UPDATE ad_selections SET mode = 'calibrate'", "DELETE FROM ad_selections",
                          "UPDATE ad_commission_results SET p_bar = 0.1", "DELETE FROM ad_commission_results",
                          "UPDATE ad_dose_offers SET chosen_variant = 'extra_question'", "DELETE FROM ad_dose_offers",
                          "UPDATE ad_relatedness_runs SET status = 'failed'", "DELETE FROM ad_relatedness_runs",
                          "UPDATE ad_coupling_versions SET version = 2", "DELETE FROM ad_coupling_versions"):
            with pytest.raises(sqlite3.IntegrityError, match="append-only"):
                connection.execute(statement)
        # The DERIVED tables are cleared and rebuilt.
        connection.execute("INSERT INTO ad_state(view, part, payload_json, state_hash, versions_json) VALUES "
                           "('subject', 'summary', '{}', 'h', '{}')")
        connection.execute("DELETE FROM ad_state")
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        connection.rollback()


def test_214_adds_the_ad23_tables_and_nothing_else(tmp_path: Path) -> None:
    _check(_upgrade(tmp_path))


@pytest.mark.durability
def test_214_on_the_durability_lane(tmp_path: Path) -> None:
    _check(_upgrade(tmp_path))


def test_the_tables_are_classified() -> None:
    for table, role in ROLES.items():
        assert role_for_table(table) is role, table


def test_head_fixture_at_214_in_rollback_mode() -> None:
    assert max(applied_versions(HEAD)) == max(m.version for m in discover_migrations()) == 214
    header = HEAD.read_bytes()[:20]
    assert (header[18], header[19]) == (1, 1)  # rollback journal, no WAL companion
    for suffix in ("-wal", "-shm"):
        assert not HEAD.with_name(HEAD.name + suffix).exists()
    with closing(sqlite3.connect(HEAD)) as connection:
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
    assert NEW_TABLES <= tables
