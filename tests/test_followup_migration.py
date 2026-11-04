"""Migration 241: FG1's additive tables, the head fixture holding them, and their roles.

Earlier migrations' additivity tests downgrade the head, so they read ``FOLLOWUP_ADDED_OBJECTS``.
"""

from __future__ import annotations

from contextlib import closing
from pathlib import Path
import sqlite3

import pytest

from learnloop.db.migrate import applied_versions, discover_migrations
from learnloop.db.table_roles import TABLE_ROLES, TableRole

HEAD = Path(__file__).resolve().parents[1] / "fixtures" / "migration_head_242" / "state.sqlite"
ROLES = {
    "followup_workflows": TableRole.WORKFLOW,
    "followup_generation_jobs": TableRole.WORKFLOW,
    "followup_workflow_events": TableRole.RECEIPT,
    "generated_probe_items": TableRole.RAW_LEDGER,
    "generated_probe_burns": TableRole.RAW_LEDGER,
    "router_decision_bindings": TableRole.RECEIPT,
}
FOLLOWUP_ADDED_OBJECTS = frozenset({
    *ROLES,
    "followup_workflows_state", "followup_workflows_session", "followup_workflows_item",
    "followup_workflow_events_workflow", "followup_workflow_events_no_update", "followup_workflow_events_no_delete",
    "followup_generation_jobs_order", "generated_probe_items_workflow", "generated_probe_items_no_delete",
    "generated_probe_items_no_update", "generated_probe_burns_no_update", "generated_probe_burns_no_delete",
    "router_decision_bindings_item", "router_decision_bindings_no_update", "router_decision_bindings_no_delete",
    # Autoindexes of the UNIQUE constraints.
    "sqlite_autoindex_followup_workflows_1", "sqlite_autoindex_followup_workflows_2",
    "sqlite_autoindex_followup_workflow_events_1", "sqlite_autoindex_followup_generation_jobs_1",
    "sqlite_autoindex_followup_generation_jobs_2", "sqlite_autoindex_generated_probe_items_1",
    "sqlite_autoindex_generated_probe_burns_1", "sqlite_autoindex_generated_probe_burns_2",
    "sqlite_autoindex_router_decision_bindings_1", "sqlite_autoindex_router_decision_bindings_2",
})


def test_241_is_the_head_and_its_tables_have_their_roles():
    names = {migration.version: migration.path.name for migration in discover_migrations()}
    assert names[241] == "241_followup_generate_serve.sql" and max(names) >= 241
    for table, role in ROLES.items():
        assert TABLE_ROLES[table] is role


def test_the_head_fixture_is_at_241_in_rollback_mode_with_empty_tables():
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
