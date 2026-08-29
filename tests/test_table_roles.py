from __future__ import annotations

import pytest

from learnloop.db.connection import connect
from learnloop.db.migrate import apply_migrations
from learnloop.db.table_roles import (
    TABLE_ROLES,
    TableRole,
    assert_complete_registry,
    registry_mismatch,
    role_for_table,
    tables_for_role,
    user_table_names,
)


def test_migration_head_user_tables_match_role_registry_exactly(tmp_path):
    sqlite_path = tmp_path / "state.sqlite"
    apply_migrations(sqlite_path)

    with connect(sqlite_path, read_only=True) as connection:
        actual_tables = user_table_names(connection)

    assert len(actual_tables) == 251
    assert actual_tables == frozenset(TABLE_ROLES)
    assert registry_mismatch(actual_tables).is_complete
    assert_complete_registry(actual_tables)


def test_synthetic_unclassified_table_fails_registry_check(tmp_path):
    sqlite_path = tmp_path / "state.sqlite"
    apply_migrations(sqlite_path)
    with connect(sqlite_path) as connection:
        connection.execute("CREATE TABLE synthetic_unclassified (id TEXT PRIMARY KEY)")
        connection.commit()
        actual_tables = user_table_names(connection)

    mismatch = registry_mismatch(actual_tables)
    assert mismatch.unclassified == frozenset({"synthetic_unclassified"})
    assert mismatch.unknown == frozenset()
    with pytest.raises(ValueError, match=r"unclassified: synthetic_unclassified"):
        assert_complete_registry(actual_tables)


def test_public_role_helpers_partition_registry():
    partition = set().union(*(tables_for_role(role) for role in TableRole))

    assert partition == set(TABLE_ROLES)
    assert sum(len(tables_for_role(role)) for role in TableRole) == len(TABLE_ROLES)
    assert role_for_table("practice_attempts") is TableRole.RAW_LEDGER
    assert role_for_table("learning_object_mastery") is TableRole.DERIVED
    assert role_for_table("derived_state_rebuilds") is TableRole.RECEIPT
    assert role_for_table("ingest_jobs") is TableRole.WORKFLOW
    assert role_for_table("learner_theta") is TableRole.COMPAT


def test_mixed_authoritative_artifacts_are_not_claimed_as_rebuildable():
    assert role_for_table("activity_card_state") is TableRole.RAW_LEDGER
    assert role_for_table("attempt_debug_payloads") is TableRole.RAW_LEDGER
    assert role_for_table("error_events") is TableRole.RAW_LEDGER
    assert role_for_table("item_misconception_discrimination") is TableRole.RAW_LEDGER
    assert role_for_table("parameter_registry") is TableRole.RAW_LEDGER
    assert role_for_table("probe_family_calibrations") is TableRole.RAW_LEDGER
    assert role_for_table("probe_item_calibrations") is TableRole.RAW_LEDGER
    assert role_for_table("soft_kinship_features") is TableRole.RAW_LEDGER
    assert role_for_table("source_block_health") is TableRole.RAW_LEDGER
    assert role_for_table("practice_item_state") is TableRole.COMPAT
