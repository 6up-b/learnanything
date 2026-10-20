"""Adaptive difficulty AD1's migration 213 (spec_adaptive_difficulty_v1 §11.2; docs/reviews/adaptive-difficulty-ad1.md).

The 212 -> 213 upgrade adds the two nullable ``practice_attempts`` columns
(``difficulty_rating``, ``first_hint_progress``, CHECKed vocabularies), the
nullable ``question_events.answered_at`` (Codex review F4) and
``question_events.answer_mode`` (CHECKed; fix round 4, V5),
``item_serve_inputs`` and ``ad_reading_opportunities`` (RECEIPT, append-only
by trigger) and ``item_forecast_payloads`` (WORKFLOW), and nothing else; no
``item_forecasts`` table (item forecasts are ``forecast_receipts`` rows of
kind ``item_unassisted_success``). Every row an earlier version wrote reads
null in the new columns. The head fixture is at 213 in rollback mode; the
durability lane runs the same upgrade under WAL; the FK check is clean.
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
from tests.test_reader_rw3b_migration import RW3B_ADDED_OBJECTS

HEAD = Path(__file__).resolve().parents[1] / "fixtures" / "migration_head_215" / "state.sqlite"
#: What 213 adds and alters: the earlier migrations' "nothing else changed"
#: diffs on the way to head read these (tests/test_approach_maps_schema.py,
#: test_help_assists_schema.py, test_library_asks_migration.py).
AD1_ADDED_OBJECTS = frozenset({
    "item_serve_inputs", "ad_reading_opportunities", "item_forecast_payloads",
    "idx_item_serve_inputs_item", "idx_item_serve_inputs_plan", "item_serve_inputs_no_update",
    "item_serve_inputs_no_delete", "idx_ad_reading_opportunities_lo", "idx_ad_reading_opportunities_written",
    "ad_reading_opportunities_no_update", "ad_reading_opportunities_no_delete", "idx_item_forecast_payloads_created",
})
#: ``question_events`` gains ``answered_at`` (Codex review F4) and ``answer_mode`` (fix round 4, V5).
AD1_ALTERED_TABLES = frozenset({"practice_attempts", "question_events"})
NEW_TABLES = {"item_serve_inputs", "ad_reading_opportunities", "item_forecast_payloads"}
NEW_OBJECTS = NEW_TABLES | {
    "idx_item_serve_inputs_item", "idx_item_serve_inputs_plan", "item_serve_inputs_no_update",
    "item_serve_inputs_no_delete", "idx_ad_reading_opportunities_lo", "idx_ad_reading_opportunities_written",
    "ad_reading_opportunities_no_update", "ad_reading_opportunities_no_delete", "idx_item_forecast_payloads_created",
    "sqlite_autoindex_item_serve_inputs_2", "sqlite_autoindex_ad_reading_opportunities_2",
    "sqlite_autoindex_ad_reading_opportunities_3", "sqlite_autoindex_item_forecast_payloads_2",
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


def _upgrade(tmp_path: Path) -> Path:
    database = _database_at(tmp_path, 212)
    with closing(sqlite3.connect(database)) as connection:
        connection.execute(
            "INSERT INTO practice_attempts(id, practice_item_id, learning_object_id, practice_mode, attempt_type, "
            "created_at) VALUES ('att_old', 'pi', 'lo', 'short_answer', 'independent_attempt', '2026-10-01T00:00:00Z')")
        connection.commit()
    before = _schema(database)
    with upgrade_allowance(UPGRADE_TEST_HELPER):
        applied = apply_migrations(database)
    # Reader RW3b's 215 (its own two tables, altering nothing) follows on the way to head.
    assert [migration.version for migration in applied] == [213, 215]
    after = _schema(database)
    assert set(after) - set(before) - RW3B_ADDED_OBJECTS == {name for name in NEW_OBJECTS if not name.startswith("sqlite_autoindex")} | {
        name for name in after if name.startswith("sqlite_autoindex") and name.split("_autoindex_")[1].rsplit("_", 1)[0]
        in NEW_TABLES}
    changed = {name for name in before if before[name] != after.get(name)}
    assert changed == AD1_ALTERED_TABLES, (
        "213 alters practice_attempts (two columns) and question_events (answered_at, answer_mode) and nothing else")
    assert "item_forecasts" not in after
    return database


def _check(database: Path) -> None:
    with closing(connect(database)) as connection:
        columns = {row[1]: row for row in connection.execute("PRAGMA table_info(practice_attempts)")}
        assert columns["difficulty_rating"][3] == 0 and columns["first_hint_progress"][3] == 0  # nullable
        questions = {row[1]: row for row in connection.execute("PRAGMA table_info(question_events)")}
        assert questions["answered_at"][3] == 0 and questions["answered_at"][4] is None  # nullable, no default
        assert questions["answer_mode"][3] == 0 and questions["answer_mode"][4] is None  # nullable, no default
        ask = ("INSERT INTO question_events(id, context, question_md, answer_status, created_at, answer_mode) "
               "VALUES (?, 'reader', 'why?', 'answered', '2026-10-18T00:00:00Z', ?)")
        for index, mode in enumerate(("answer_directly", "help_me_reason", "ask_me_first", None)):
            connection.execute(ask, (f"q_ok_{index}", mode))
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(ask, ("q_bad", "reader"))
        old = connection.execute("SELECT difficulty_rating, first_hint_progress FROM practice_attempts "
                                 "WHERE id = 'att_old'").fetchone()
        assert old is None or tuple(old) == (None, None)
        insert = ("INSERT INTO practice_attempts(id, practice_item_id, learning_object_id, practice_mode, attempt_type, "
                  "created_at, difficulty_rating, first_hint_progress) VALUES (?, 'pi', 'lo', 'short_answer', "
                  "'independent_attempt', '2026-10-18T00:00:00Z', ?, ?)")
        for index, (rating, marker) in enumerate((("easy", "no_draft"), ("about_right", "draft_started"),
                                                  ("hard", None), (None, None))):
            connection.execute(insert, (f"att_ok_{index}", rating, marker))
        for index, (rating, marker) in enumerate((("very_hard", None), (None, "typing"))):
            with pytest.raises(sqlite3.IntegrityError):
                connection.execute(insert, (f"att_bad_{index}", rating, marker))
        connection.execute(
            "INSERT INTO item_serve_inputs(id, receipt_key, presentation_kind, plan_presentation_id, practice_item_id, "
            "content_hash, served_at, audit_json, signals_json, pre_exposed, resolution_version, created_at) "
            "VALUES ('sin_1', 'plan_presentation:pp1', 'plan_presentation', 'pp1', 'pi', 'h', '2026-10-18T00:00:00Z', "
            "'{}', '{}', 0, 'ad_feature_resolution_v1', '2026-10-18T00:00:00Z')")
        with pytest.raises(sqlite3.IntegrityError):  # a plan presentation row names its presentation
            connection.execute(
                "INSERT INTO item_serve_inputs(id, receipt_key, presentation_kind, practice_item_id, content_hash, "
                "served_at, audit_json, signals_json, pre_exposed, resolution_version, created_at) VALUES ('sin_2', "
                "'k2', 'plan_presentation', 'pi', 'h', 't', '{}', '{}', 0, 'v', 't')")
        reading = ("INSERT INTO ad_reading_opportunities(id, opportunity_key, kind, subkind, source_table, source_id, "
                   "source_written_at, learning_object_id, facet_doses_json, mapping_version, sweep, swept_at, "
                   "authority_class) VALUES (?, ?, ?, 'section_read', 'reader_section_progress', ?, 't', 'lo', '{}', "
                   "'v', 'serve', 't', ?)")
        connection.execute(reading, ("ro_1", "k1", "reading", "s1", "salience_only"))
        for row in (("ro_2", "k2", "dwell", "s2", "salience_only"), ("ro_3", "k3", "reading", "s3", "evidence"),
                    ("ro_4", "k1", "reading", "s4", "salience_only")):
            with pytest.raises(sqlite3.IntegrityError):
                connection.execute(reading, row)
        for statement in ("UPDATE item_serve_inputs SET pre_exposed = 1", "DELETE FROM item_serve_inputs",
                          "UPDATE ad_reading_opportunities SET learning_object_id = 'x'",
                          "DELETE FROM ad_reading_opportunities"):
            with pytest.raises(sqlite3.IntegrityError, match="append-only"):
                connection.execute(statement)
        connection.execute("INSERT INTO item_forecast_payloads(id, owner_key, forecaster, kind, content_hash, "
                           "content_json, created_at) VALUES ('p1', 'k', 'llm_v1:item', 'request', 'h', '{}', 't')")
        connection.execute("DELETE FROM item_forecast_payloads")  # WORKFLOW: pruned
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        connection.commit()


def test_213_adds_the_ad1_receipts_and_nothing_else(tmp_path):
    _check(_upgrade(tmp_path))


@pytest.mark.durability
def test_213_on_the_durability_lane(tmp_path):
    database = _upgrade(tmp_path)
    with closing(sqlite3.connect(database)) as connection:
        assert connection.execute("PRAGMA journal_mode").fetchone()[0] == "wal"
    _check(database)


def test_the_head_fixture_is_at_head_with_empty_ad1_tables(tmp_path):
    from learnloop.db.copies import backup_database

    with closing(sqlite3.connect(f"file:{HEAD}?mode=ro", uri=True)) as connection:
        assert connection.execute("PRAGMA journal_mode").fetchone()[0] == "delete"
        # Reader RW3b's 215 is the head now (tests/test_reader_rw3b_migration.py).
        assert connection.execute("SELECT MAX(version) FROM schema_migrations").fetchone()[0] == 215
        assert all(connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] == 0 for table in NEW_TABLES)
    database = tmp_path / "head.sqlite"
    backup_database(HEAD, database)
    _check(database)


def test_the_ad1_tables_are_classified():
    assert role_for_table("item_serve_inputs") is TableRole.RECEIPT
    assert role_for_table("ad_reading_opportunities") is TableRole.RECEIPT
    assert role_for_table("item_forecast_payloads") is TableRole.WORKFLOW


def test_a_served_revision_hashes_as_the_scheduler_snapshots_it(tmp_path):
    from learnloop.adaptive_difficulty.feature_audit import item_revision
    from learnloop.scheduling.scheduler import _practice_item_snapshot
    from learnloop.vault.loader import load_vault
    from tests.helpers import create_basic_vault

    item = load_vault(create_basic_vault(tmp_path / "vault").root).practice_items["pi_svd_define_001"]
    assert item_revision(item) == _practice_item_snapshot(item)
