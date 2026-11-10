"""Arc B close fix round, migration 254 (ADR-017, strategy §3.7): ``router.payload_retention_days`` clears an old decision
record's ``alternatives_json`` and ``facts_json`` and keeps the row.

The migration replaces only 253's no-update trigger: it lets an update through when it changes nothing but those two
columns, to their fixed placeholders, on a row over a day old. Every identity column stays immutable and deletes stay
refused. ``db.stores.provenance.prune_old_decision_payloads`` is the maintenance pass (run at startup).
"""

from __future__ import annotations

import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

import pytest

from learnloop.db.copies import backup_database
from learnloop.db.migrate import UPGRADE_TEST_HELPER, applied_versions, apply_migrations, discover_migrations, upgrade_allowance
from learnloop.db.repositories import Repository
from learnloop.db.stores.provenance import PRUNED_ALTERNATIVES, PRUNED_FACTS, prune_decision_payloads, prune_old_decision_payloads
from tests.helpers import MIGRATION_HEAD_FIXTURE

HEAD = MIGRATION_HEAD_FIXTURE / "state.sqlite"
MIGRATION = next(m for m in discover_migrations() if m.name == "decision_records_payload_retention")
# The trigger's day floor reads SQLite's own clock, so "recent" is recent by the wall clock.
NOW = datetime.now(timezone.utc)
OLD, RECENT = "2024-01-02T03:04:05.000001+00:00", NOW.isoformat()  # OLD: past the default 365 days
IDENTITY = ("id", "trace_id", "parent_id", "kind", "status", "subject_kind", "subject_id", "chosen_ref", "decided_by",
            "rule", "versions_json", "detail_table", "detail_id", "error_type", "error_where", "created_at")


@pytest.fixture()
def database(tmp_path: Path) -> Path:
    path = tmp_path / "state.sqlite"
    backup_database(HEAD, path)
    with closing(sqlite3.connect(path)) as connection:
        for record_id, created in (("r_old", OLD), ("r_recent", RECENT)):
            connection.execute(
                "INSERT INTO decision_records (id, trace_id, parent_id, kind, status, subject_kind, subject_id, "
                "chosen_ref, decided_by, rule, alternatives_json, facts_json, versions_json, detail_table, detail_id, "
                "created_at) VALUES (?, 'tr', 'p', 'slate', 'chosen', 'slate', 's1', 'item_a', 'greedy', 'lane_quota', "
                "'[{\"ref\": \"item_b\", \"lost_by\": \"lane_quota\"}]', '{\"waits_n\": 3}', '{\"seed\": \"x\"}', "
                "'slates', 's1', ?)", (record_id, created))
        connection.commit()
    return path


def _row(path: Path, record_id: str) -> dict:
    with closing(sqlite3.connect(path)) as connection:
        connection.row_factory = sqlite3.Row
        return dict(connection.execute("SELECT * FROM decision_records WHERE id = ?", (record_id,)).fetchone())


def test_the_head_holds_254_in_rollback_mode():
    assert MIGRATION.version in applied_versions(HEAD)
    assert HEAD.read_bytes()[18:20] == b"\x01\x01"


def test_pruning_clears_the_payloads_of_old_rows_only_and_keeps_every_identity_column(database: Path):
    before_old, before_recent = _row(database, "r_old"), _row(database, "r_recent")
    assert prune_old_decision_payloads(Repository.attach(database), retention_days=30, now=NOW) == 1
    after_old, after_recent = _row(database, "r_old"), _row(database, "r_recent")
    assert (after_old["alternatives_json"], after_old["facts_json"]) == (PRUNED_ALTERNATIVES, PRUNED_FACTS)
    assert {name: after_old[name] for name in IDENTITY} == {name: before_old[name] for name in IDENTITY}
    assert after_recent == before_recent
    # A second pass finds nothing left to clear.
    assert prune_old_decision_payloads(Repository.attach(database), retention_days=30, now=NOW) == 0


@pytest.mark.parametrize("column", IDENTITY)
def test_an_identity_column_is_still_refused_even_beside_a_placeholder(database: Path, column: str):
    value = "2025-01-01T00:00:00+00:00" if column == "created_at" else "x"
    with closing(sqlite3.connect(database)) as connection, pytest.raises(sqlite3.IntegrityError, match="append-only"):
        connection.execute(f"UPDATE decision_records SET {column} = ?, alternatives_json = ?, facts_json = ? "
                           "WHERE id = 'r_old'", (value, PRUNED_ALTERNATIVES, PRUNED_FACTS))


def test_anything_but_the_placeholders_a_young_row_and_a_delete_are_still_refused(database: Path):
    with closing(sqlite3.connect(database)) as connection:
        for statement, args in (
            ("UPDATE decision_records SET facts_json = '{}' WHERE id = 'r_old'", ()),
            ("UPDATE decision_records SET alternatives_json = '[]' WHERE id = 'r_old'", ()),
            ("UPDATE decision_records SET alternatives_json = ?, facts_json = ? WHERE id = 'r_recent'",
             (PRUNED_ALTERNATIVES, PRUNED_FACTS)),
            ("DELETE FROM decision_records WHERE id = 'r_old'", ()),
        ):
            with pytest.raises(sqlite3.IntegrityError, match="append-only"):
                connection.execute(statement, args)


def test_below_254_pruning_clears_nothing_and_never_raises(tmp_path: Path):
    path = tmp_path / "state.sqlite"
    backup_database(HEAD, path)
    with closing(sqlite3.connect(path)) as connection:
        connection.execute("DROP TRIGGER decision_records_no_update")
        connection.execute("CREATE TRIGGER decision_records_no_update BEFORE UPDATE ON decision_records "
                           "BEGIN SELECT RAISE(ABORT, 'decision_records is append-only'); END")
        connection.execute("INSERT INTO decision_records (id, trace_id, kind, status, created_at) "
                           "VALUES ('r', 't', 'slate', 'chosen', ?)", (OLD,))
        connection.commit()
        assert prune_decision_payloads(connection, before="2026-06-01T00:00:00") == 0


def test_the_migration_replaces_only_the_no_update_trigger(tmp_path: Path):
    path = tmp_path / "state.sqlite"
    backup_database(HEAD, path)
    with closing(sqlite3.connect(path)) as connection:
        connection.execute("DROP TRIGGER decision_records_no_update")
        connection.execute("CREATE TRIGGER decision_records_no_update BEFORE UPDATE ON decision_records "
                           "BEGIN SELECT RAISE(ABORT, 'decision_records is append-only'); END")
        connection.execute("DELETE FROM schema_migrations WHERE version = ?", (MIGRATION.version,))
        connection.commit()
        before = dict(connection.execute("SELECT name, sql FROM sqlite_master"))
    with upgrade_allowance(UPGRADE_TEST_HELPER):
        assert [m.version for m in apply_migrations(path)] == [MIGRATION.version]
    with closing(sqlite3.connect(path)) as connection:
        after = dict(connection.execute("SELECT name, sql FROM sqlite_master"))
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    assert set(after) == set(before)
    assert {name for name in before if before[name] != after[name]} == {"decision_records_no_update"}


def test_startup_maintenance_runs_the_retention_pass(tmp_path: Path):
    from learnloop.ops.startup import run_startup_maintenance
    from learnloop.vault.loader import load_vault
    from tests.helpers import create_basic_vault

    paths = create_basic_vault(tmp_path / "vault")
    with closing(sqlite3.connect(paths.sqlite_path)) as connection:
        connection.execute("INSERT INTO decision_records (id, trace_id, kind, status, facts_json, created_at) "
                           "VALUES ('r_startup', 't', 'slate', 'chosen', '{\"waits_n\": 1}', ?)", (OLD,))
        connection.commit()
    run_startup_maintenance(load_vault(paths.root), Repository(paths.sqlite_path))
    assert _row(paths.sqlite_path, "r_startup")["facts_json"] == PRUNED_FACTS
