"""Migration 243: RO0's additive columns and tables, the head fixture holding them, and their roles.

Earlier migrations' additivity tests downgrade the head, so they read ``RO0_ADDED_OBJECTS``.
"""

from __future__ import annotations

from contextlib import closing
from pathlib import Path
import sqlite3

import pytest

from learnloop.config.schema import LearnLoopConfig, RouterObjectiveConfig
from learnloop.data_capture.gates import objective_receipts_on
from learnloop.db.migrate import applied_versions, discover_migrations
from learnloop.db.table_roles import TABLE_ROLES, TableRole
from learnloop.params.parameter_registry import REGISTRY, classify_config_path

HEAD = Path(__file__).resolve().parents[1] / "fixtures" / "migration_head_247" / "state.sqlite"
TABLES = ("session_receipts", "decision_state_receipts", "goal_lifecycle_events")
NEW_COLUMNS = {
    "question_events": {"reveal_state_json"},
    "plan_presentations": {"ask_available"},
    "source_exposure_events": {"initiator", "initiator_block_id", "initiator_session_id", "initiator_visit_id"},
    "decision_measurement_events": {"non_service_type", "delay_json"},
    "decision_objectives": {"delay_json"},
}
RO0_ADDED_OBJECTS = frozenset({
    *TABLES,
    "session_receipts_once", "session_receipts_created", "decision_state_receipts_created", "goal_lifecycle_events_goal",
    "sqlite_autoindex_session_receipts_1", "sqlite_autoindex_decision_state_receipts_1",
    "sqlite_autoindex_decision_state_receipts_2", "sqlite_autoindex_goal_lifecycle_events_1",
    *(f"{table}_no_{verb}" for table in TABLES for verb in ("update", "delete")),
})


def test_243_exists_and_its_tables_are_receipts():
    names = {migration.version: migration.path.name for migration in discover_migrations()}
    assert names[243] == "243_router_objective_receipts.sql"
    for table in TABLES:
        assert TABLE_ROLES[table] is TableRole.RECEIPT


def test_the_head_fixture_holds_243_in_rollback_mode_with_empty_tables_and_null_columns():
    assert HEAD.read_bytes()[18:20] == b"\x01\x01"
    assert 243 in applied_versions(HEAD)
    with closing(sqlite3.connect(HEAD)) as connection:
        names = {row[0] for row in connection.execute("SELECT name FROM sqlite_master")}
        assert RO0_ADDED_OBJECTS <= names
        for table in TABLES:
            assert connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] == 0
        for table, columns in NEW_COLUMNS.items():
            present = {row[1] for row in connection.execute(f"PRAGMA table_info({table})")}
            assert columns <= present
            for column in columns:
                assert connection.execute(f"SELECT COUNT({column}) FROM {table}").fetchone()[0] == 0


@pytest.mark.parametrize("table", TABLES)
def test_the_receipts_are_immutable(tmp_path, table):
    copy = tmp_path / "state.sqlite"
    with closing(sqlite3.connect(HEAD)) as source, closing(sqlite3.connect(copy)) as target:
        source.backup(target)
    with closing(sqlite3.connect(copy)) as connection:
        for trigger in (f"{table}_no_update", f"{table}_no_delete"):
            assert connection.execute("SELECT 1 FROM sqlite_master WHERE type='trigger' AND name=?", (trigger,)).fetchone()


def test_the_session_receipt_checks_hold(tmp_path):
    copy = tmp_path / "state.sqlite"
    with closing(sqlite3.connect(HEAD)) as source, closing(sqlite3.connect(copy)) as target:
        source.backup(target)
    base = {"receipt_version": "v", "created_at": "2026-11-04T00:00:00Z", "detail_json": "{}"}

    def insert(connection, **row):
        values = {**base, **row}
        connection.execute(f"INSERT INTO session_receipts ({','.join(values)}) VALUES ({','.join('?' for _ in values)})",
                           list(values.values()))

    with closing(sqlite3.connect(copy)) as connection:
        insert(connection, id="a", session_id="s", kind="availability", minutes_source="missing")
        with pytest.raises(sqlite3.IntegrityError):  # once per session
            insert(connection, id="b", session_id="s", kind="availability", minutes_source="missing")
        with pytest.raises(sqlite3.IntegrityError):  # missing is recorded as missing, never left out
            insert(connection, id="c", session_id="t", kind="availability")
        with pytest.raises(sqlite3.IntegrityError):  # an end says why and how it is known
            insert(connection, id="d", session_id="t", kind="end")
        insert(connection, id="e", session_id="t", kind="end", end_reason="app_closed", end_basis="inferred")
        # An override is no end: there can be several, and a sessionless plan can have one.
        insert(connection, id="f", session_id="t", kind="stop_response", end_reason="offered_stop_overridden", end_basis="explicit")
        insert(connection, id="g", session_id="t", kind="stop_response", end_reason="offered_stop_overridden", end_basis="explicit")
        insert(connection, id="h", session_id=None, kind="stop_response", end_reason="offered_stop_overridden", end_basis="explicit")


def test_the_switch_is_on_by_default_and_classified():
    assert RouterObjectiveConfig().receipts is True
    config = LearnLoopConfig.model_validate({})
    assert objective_receipts_on(config)
    assert not objective_receipts_on(config.model_copy(update={"router_objective": RouterObjectiveConfig(receipts=False)}))
    rule = classify_config_path("router_objective.receipts")
    assert rule is not None and rule.kind == "structural"
    assert "router_objective.receipts" in REGISTRY
