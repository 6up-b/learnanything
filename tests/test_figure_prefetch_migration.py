"""Reader RW5d P5: migration 237 (spec_reader_show_me_figures_v1 §13.2b; numbered 237 at landing, after follow-ups Nov 2's 235 and teacher TE1b's 236).

Two RAW_LEDGER tables: ``figure_prefetch_decisions`` (append-only; ``request_id``, ``input_hash`` and the
outcome set once each) and ``plan_usage_pauses`` (append-only, one row per hit time), plus the index on
``figure_requests.prefetch_decision_id``. Both classified for rebuild (no replayer: posteriors are
recomputed from the ledger) and for AD (DENIED: AD reads neither). The head fixture is at 238 in rollback
mode with empty tables. Earlier migrations' "nothing else changed" diffs on the way to head read
``P5_ADDED_OBJECTS``.
"""

from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path

import pytest

from learnloop.adaptive_difficulty import protected_tables as PT
from learnloop.db.migrate import UPGRADE_TEST_HELPER, apply_migrations, discover_migrations, upgrade_allowance
from learnloop.db.table_roles import TableRole, role_for_table

HEAD = Path(__file__).resolve().parents[1] / "fixtures" / "migration_head_238" / "state.sqlite"
P5_TABLES = {"figure_prefetch_decisions": TableRole.RAW_LEDGER, "plan_usage_pauses": TableRole.RAW_LEDGER}
#: What 237 adds (its tables, their indexes and autoindexes, the triggers, the figure_requests index).
P5_ADDED_OBJECTS = frozenset({
    *P5_TABLES,
    "figure_prefetch_decisions_no_delete", "figure_prefetch_decisions_set_once",
    "idx_figure_prefetch_decisions_created", "idx_figure_prefetch_decisions_key", "idx_figure_prefetch_decisions_open",
    "idx_figure_requests_prefetch_decision", "plan_usage_pauses_no_delete", "plan_usage_pauses_no_update",
    "sqlite_autoindex_figure_prefetch_decisions_1", "sqlite_autoindex_plan_usage_pauses_1",
    "sqlite_autoindex_plan_usage_pauses_2",
})

DECISION = ("INSERT INTO figure_prefetch_decisions (id, trigger_kind, trigger_ref, request_key, anchor_json, "
            "model_version, posterior_digest, sampled_eu, propensity, decision, horizon_kind, created_at) VALUES "
            "(?, 'section', 'ext:s2', 'rk', '{}', 'prefetch_decision_v1', 'd', 0.5, 0.75, 'build', 'section_read', "
            "'2026-11-02T00:00:00Z')")


def test_237_is_p5s_migration_and_every_table_is_classified():
    names = {migration.version: migration.path.name for migration in discover_migrations()}
    assert names[237] == "237_figure_prefetch.sql"
    for table, role in P5_TABLES.items():
        assert role_for_table(table) == role, table
        assert PT.role(table) == PT.DENIED, table


def test_the_head_fixture_is_at_237_in_rollback_mode_with_empty_tables():
    assert HEAD.read_bytes()[18:20] == b"\x01\x01"
    with closing(sqlite3.connect(f"file:{HEAD}?mode=ro", uri=True)) as connection:
        assert connection.execute("SELECT MAX(version) FROM schema_migrations").fetchone()[0] == 238
        names = {row[0] for row in connection.execute("SELECT name FROM sqlite_master")}
        assert P5_ADDED_OBJECTS <= names
        for table in P5_TABLES:
            assert connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] == 0


def _upgrade(tmp_path: Path) -> Path:
    database = tmp_path / "state.sqlite"
    with upgrade_allowance(UPGRADE_TEST_HELPER):
        apply_migrations(database)
    return database


def _check(database: Path) -> None:
    with closing(sqlite3.connect(database)) as connection:
        connection.execute(DECISION, ("fpd_1",))
        # Set once each: request_id, input_hash, then the outcome with its time.
        connection.execute("UPDATE figure_prefetch_decisions SET request_id = 'frq_1', input_hash = 'h' WHERE id = 'fpd_1'")
        with pytest.raises(sqlite3.IntegrityError, match="set once"):
            connection.execute("UPDATE figure_prefetch_decisions SET request_id = 'frq_2' WHERE id = 'fpd_1'")
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute("UPDATE figure_prefetch_decisions SET outcome = 'opened' WHERE id = 'fpd_1'")
        connection.execute("UPDATE figure_prefetch_decisions SET outcome = 'opened', outcome_at = 'x' WHERE id = 'fpd_1'")
        with pytest.raises(sqlite3.IntegrityError, match="set once"):
            connection.execute("UPDATE figure_prefetch_decisions SET outcome = 'neither' WHERE id = 'fpd_1'")
        with pytest.raises(sqlite3.IntegrityError, match="set once"):
            connection.execute("UPDATE figure_prefetch_decisions SET propensity = 0.1 WHERE id = 'fpd_1'")
        with pytest.raises(sqlite3.IntegrityError, match="append-only"):
            connection.execute("DELETE FROM figure_prefetch_decisions WHERE id = 'fpd_1'")
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(DECISION.replace("'section', ", "'chat', "), ("fpd_2",))
        connection.execute("INSERT INTO plan_usage_pauses (id, hit_at, reset_at, observed_at) VALUES "
                           "('pup_1', '2026-11-02T01:00:00+00:00', '2026-11-02T01:15:00+00:00', 'now')")
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute("INSERT INTO plan_usage_pauses (id, hit_at, observed_at) VALUES "
                               "('pup_2', '2026-11-02T01:00:00+00:00', 'now')")
        with pytest.raises(sqlite3.IntegrityError, match="append-only"):
            connection.execute("UPDATE plan_usage_pauses SET reset_at = NULL WHERE id = 'pup_1'")
        with pytest.raises(sqlite3.IntegrityError, match="append-only"):
            connection.execute("DELETE FROM plan_usage_pauses")
        indexes = {row[1] for row in connection.execute("PRAGMA index_list(figure_requests)")}
        assert "idx_figure_requests_prefetch_decision" in indexes


def test_237_keeps_the_ledgers_append_only_and_set_once(tmp_path):
    _check(_upgrade(tmp_path))


def test_237_on_the_head_fixture_copy_adds_only_its_objects(tmp_path):
    from learnloop.db.copies import backup_database

    database = tmp_path / "state.sqlite"
    backup_database(HEAD, database)
    with closing(sqlite3.connect(database)) as connection:
        before = {row[0]: row[1] for row in connection.execute("SELECT name, sql FROM sqlite_master")}
    _check(database)
    with closing(sqlite3.connect(database)) as connection:
        after = {row[0]: row[1] for row in connection.execute("SELECT name, sql FROM sqlite_master")}
    assert before == after  # the head already holds 237: nothing changes but the rows


@pytest.mark.durability
def test_237_on_the_durability_lane(tmp_path):
    database = _upgrade(tmp_path)
    with closing(sqlite3.connect(database)) as connection:
        assert connection.execute("PRAGMA journal_mode").fetchone()[0] in ("wal", "delete")
    _check(database)
