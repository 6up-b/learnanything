"""Migration 241: FG1's additive tables, the head fixture holding them, and their roles.

Earlier migrations' additivity tests downgrade the head, so they read ``FOLLOWUP_ADDED_OBJECTS``.
"""

from __future__ import annotations

from contextlib import closing
import sqlite3

import pytest

from learnloop.db.migrate import applied_versions, discover_migrations
from learnloop.db.table_roles import TABLE_ROLES
from tests.helpers import MIGRATION_HEAD_FIXTURE
from tests.followup_migration_helpers import FOLLOWUP_ADDED_OBJECTS, ROLES

HEAD = MIGRATION_HEAD_FIXTURE / "state.sqlite"


def test_241_is_applied_and_its_tables_have_their_roles():
    names = {migration.version: migration.path.name for migration in discover_migrations()}
    assert names[241] == "241_followup_generate_serve.sql" and max(names) >= 241
    for table, role in ROLES.items():
        assert TABLE_ROLES[table] is role


def test_the_head_fixture_holds_241_in_rollback_mode_with_empty_tables():
    assert HEAD.read_bytes()[18:20] == b"\x01\x01"
    assert max(applied_versions(HEAD)) >= 241
    with closing(sqlite3.connect(HEAD)) as connection:
        names = {row[0] for row in connection.execute("SELECT name FROM sqlite_master")}
        assert FOLLOWUP_ADDED_OBJECTS <= names
        for table in ROLES:
            assert connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] == 0


@pytest.mark.parametrize("table", ["followup_workflow_events", "generated_probe_burns", "router_decision_bindings"])
def test_the_ledgers_are_append_only(table):
    with closing(sqlite3.connect(HEAD)) as connection:
        triggers = {row[0] for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'trigger' AND tbl_name = ?", (table,))}
    assert {f"{table}_no_update", f"{table}_no_delete"} <= triggers
