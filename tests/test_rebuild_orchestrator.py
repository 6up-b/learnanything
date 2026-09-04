"""R2/R3: one lossless umbrella over every rebuildable projection family."""

from __future__ import annotations

import json
import shutil
from datetime import UTC, datetime
from pathlib import Path

from learnloop.clock import FrozenClock
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.db.table_roles import TableRole, tables_for_role
from learnloop.substrate.rebuild_orchestrator import (
    DERIVED_STATE_REPLAYERS,
    derived_table_owners,
    rebuild_all_derived_state,
    validate_replayer_registry,
)
from learnloop.substrate.replay import rebuild_derived_state
from learnloop.vault.loader import load_vault

FIXTURE_VAULT = (
    Path(__file__).resolve().parents[1] / "fixtures" / "migration_head_158"
)
CLOCK = FrozenClock(datetime(2026, 5, 19, 12, 0, tzinfo=UTC))


def _copy_fixture(tmp_path: Path, name: str) -> Path:
    destination = tmp_path / name
    shutil.copytree(FIXTURE_VAULT, destination)
    return destination


def _projection_snapshot(repository: Repository, tables: set[str]) -> dict[str, list[dict]]:
    """An exact row snapshot; no id, timestamp, or value column is ignored."""

    snapshot: dict[str, list[dict]] = {}
    with connect(repository.sqlite_path, read_only=True) as connection:
        for table in sorted(tables):
            rows = [
                dict(row)
                for row in connection.execute(f'SELECT * FROM "{table}"')
            ]
            snapshot[table] = sorted(
                rows,
                key=lambda value: json.dumps(
                    value, sort_keys=True, separators=(",", ":"), default=str
                ),
            )
    return snapshot


def _insert_row(connection, table: str, row: dict) -> None:
    columns = tuple(row)
    placeholders = ", ".join("?" for _ in columns)
    connection.execute(
        f'INSERT INTO "{table}" ({", ".join(columns)}) VALUES ({placeholders})',
        tuple(row[column] for column in columns),
    )


def _inject_one_stale_row_per_derived_table(repository: Repository) -> None:
    """Plant a schema-valid orphan in every declared projection table."""

    at = "1900-01-01T00:00:00Z"
    rows = {
        "ability_transition_events": {
            "attempt_id": "stale_attempt",
            "learning_object_id": "stale_lo",
            "practice_item_id": "stale_item",
            "transition_type": "stale",
            "expected_skill_gain": 0.0,
            "target_facets_json": "[]",
            "reason": "stale",
            "applied_to_belief_counts": 0,
            "applied_to_mastery": 0,
            "applied_to_facet_recall": 0,
            "algorithm_version": "stale",
            "created_at": at,
        },
        "attempt_surprise": {
            "attempt_id": "stale_attempt",
            "observed_joint_bucket_json": "{}",
            "algorithm_version": "stale",
            "created_at": at,
        },
        "capability_residual_state": {
            "id": "stale_residual",
            "facet_id": "stale_facet",
            "capability": "retrieval",
            "active": 1,
            "residual_alpha": 1.0,
            "residual_beta": 1.0,
            "residual_mean": 0.5,
            "parent_alpha": 1.0,
            "parent_beta": 1.0,
            "parent_mean": 0.5,
            "algorithm_version": "stale",
            "created_at": at,
            "updated_at": at,
        },
        "facet_capability_evidence": {
            "facet_id": "stale_facet",
            "capability": "retrieval",
            "algorithm_version": "stale",
            "created_at": at,
            "updated_at": at,
        },
        "facet_recall_state": {
            "id": "stale_recall",
            "facet_id": "stale_facet",
            "capability_key": "retrieval",
            "recall_alpha": 1.0,
            "recall_beta": 1.0,
            "recall_mean": 0.5,
            "recall_variance": 0.1,
            "algorithm_version": "stale",
            "created_at": at,
            "updated_at": at,
        },
        "item_parameter_state": {
            "practice_item_id": "stale_item",
            "b_mean": 0.0,
            "b_var": 1.0,
            "algorithm_version": "stale",
            "updated_at": at,
        },
        "learning_object_mastery": {
            "learning_object_id": "stale_lo",
            "algorithm_version": "stale",
            "updated_at": at,
        },
        "learning_outcome_labels": {
            "id": "stale_label",
            "source_attempt_id": "stale_source",
            "outcome_attempt_id": "stale_outcome",
            "label_type": "same_item_retention",
            "practice_item_id": "stale_item",
            "learning_object_id": "stale_lo",
            "intervening_attempt_count": 0,
            "metadata_json": "{}",
            "algorithm_version": "stale",
            "created_at": at,
        },
        "practice_item_quality_state": {
            "practice_item_id": "stale_item",
            "algorithm_version": "stale",
            "updated_at": at,
        },
        "subject_identifiability_watermarks": {
            "subject_id": "stale_subject",
            "registry_hash": "stale",
            "finding_count": 1,
            "checked_at": at,
        },
    }
    assert set(rows) == set(tables_for_role(TableRole.DERIVED))
    with connect(repository.sqlite_path) as connection:
        # The test deliberately plants orphan projection rows.  Production
        # connections keep FK enforcement enabled; disabling it here lets the
        # cleanup oracle cover attempt-keyed caches too.
        connection.execute("PRAGMA foreign_keys = OFF")
        for table, row in rows.items():
            _insert_row(connection, table, row)
        connection.commit()


def test_replayer_registry_owns_each_derived_table_exactly_once():
    validate_replayer_registry()

    owners = derived_table_owners()
    derived = tables_for_role(TableRole.DERIVED)

    assert set(owners) == set(derived)
    assert all(len(owner_names) == 1 for owner_names in owners.values())
    assert [spec.name for spec in DERIVED_STATE_REPLAYERS].index(
        "activity_substrate"
    ) < [spec.name for spec in DERIVED_STATE_REPLAYERS].index("learning_state")
    assert [spec.name for spec in DERIVED_STATE_REPLAYERS].index(
        "learning_state"
    ) < [spec.name for spec in DERIVED_STATE_REPLAYERS].index(
        "canonical_projection"
    )


def test_umbrella_accounts_for_every_raw_attempt_and_records_one_receipt(tmp_path):
    root = _copy_fixture(tmp_path, "complete")
    vault = load_vault(root)
    repository = Repository(root / "state.sqlite")
    raw_attempt_ids = {
        str(attempt["id"]) for attempt in repository.list_all_attempts()
    }
    with connect(repository.sqlite_path, read_only=True) as connection:
        receipts_before = connection.execute(
            "SELECT COUNT(*) FROM derived_state_rebuilds"
        ).fetchone()[0]

    result = rebuild_all_derived_state(vault, repository, clock=CLOCK)

    assert set(result.accounted_attempt_ids) == raw_attempt_ids
    assert result.unaccounted_attempt_ids == []
    assert result.raw_attempts == len(raw_attempt_ids)
    assert result.replayed_attempts == len(raw_attempt_ids)
    assert result.marker_id is not None
    with connect(repository.sqlite_path, read_only=True) as connection:
        receipts_after = connection.execute(
            "SELECT COUNT(*) FROM derived_state_rebuilds"
        ).fetchone()[0]
        missing_activity_rows = connection.execute(
            """
            SELECT a.id
              FROM practice_attempts AS a
              LEFT JOIN activity_observations AS o ON o.attempt_id = a.id
             WHERE o.id IS NULL
            """
        ).fetchall()
    assert receipts_after == receipts_before + 1
    assert missing_activity_rows == []


def test_golden_projection_survives_one_umbrella_rebuild_exactly_and_stale_rows_clear(
    tmp_path,
):
    root = _copy_fixture(tmp_path, "golden")
    vault = load_vault(root)
    repository = Repository(root / "state.sqlite")
    derived = set(tables_for_role(TableRole.DERIVED))

    # The established direct replay is the independent golden producer.  It
    # runs once before the umbrella-under-test and writes no rebuild receipt.
    rebuild_derived_state(
        vault,
        repository,
        clock=CLOCK,
        record_receipt=False,
    )
    expected = _projection_snapshot(repository, derived)
    with connect(repository.sqlite_path, read_only=True) as connection:
        receipts_before = int(
            connection.execute(
                "SELECT COUNT(*) FROM derived_state_rebuilds"
            ).fetchone()[0]
        )

    _inject_one_stale_row_per_derived_table(repository)
    dirty = _projection_snapshot(repository, derived)
    assert all(len(dirty[table]) == len(expected[table]) + 1 for table in derived)

    rebuild_all_derived_state(vault, repository, clock=CLOCK)

    # Every byte-bearing column participates, including ids and all timestamps.
    # The sole excluded mutation is the append-only rebuild receipt, which is
    # intentionally outside DERIVED and asserted independently below.
    assert _projection_snapshot(repository, derived) == expected
    with connect(repository.sqlite_path, read_only=True) as connection:
        receipts_after = int(
            connection.execute(
                "SELECT COUNT(*) FROM derived_state_rebuilds"
            ).fetchone()[0]
        )
    assert receipts_after == receipts_before + 1


def test_same_version_full_rebuild_is_semantically_idempotent_on_golden_fixture(
    tmp_path,
):
    root = _copy_fixture(tmp_path, "golden")
    vault = load_vault(root)
    repository = Repository(root / "state.sqlite")
    derived = set(tables_for_role(TableRole.DERIVED))

    rebuild_all_derived_state(vault, repository, clock=CLOCK)
    first = _projection_snapshot(repository, derived)
    rebuild_all_derived_state(vault, repository, clock=CLOCK)
    second = _projection_snapshot(repository, derived)

    assert second == first
