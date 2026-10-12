"""R2/R3: one lossless umbrella over every rebuildable projection family."""

from __future__ import annotations

import json
import shutil
import pytest
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
    Path(__file__).resolve().parents[1] / "fixtures" / "migration_head_175"
)
CLOCK = FrozenClock(datetime(2026, 5, 19, 12, 0, tzinfo=UTC))


def test_live_rebuild_failure_preserves_all_published_state(tmp_path, monkeypatch):
    import learnloop.substrate.rebuild_orchestrator as orchestrator

    root = _copy_fixture(tmp_path, "interrupted")
    repository = Repository(root / "state.sqlite")
    tables = set(tables_for_role(TableRole.DERIVED)) | {"derived_state_rebuilds"}
    before = _projection_snapshot(repository, tables)
    original = orchestrator._RUNNERS["learning_state"]

    def interrupted(spec, context):
        original(spec, context)
        assert _projection_snapshot(repository, tables) == before
        raise RuntimeError("replay interrupted after family writes")

    monkeypatch.setitem(orchestrator._RUNNERS, "learning_state", interrupted)
    with pytest.raises(RuntimeError, match="replay interrupted"):
        rebuild_all_derived_state(load_vault(root), repository, clock=CLOCK)
    assert _projection_snapshot(repository, tables) == before




def test_live_rebuild_completeness_failure_publishes_nothing(tmp_path, monkeypatch):
    import dataclasses

    import learnloop.substrate.rebuild_orchestrator as orchestrator

    root = _copy_fixture(tmp_path, "incomplete")
    repository = Repository(root / "state.sqlite")
    tables = set(tables_for_role(TableRole.DERIVED)) | {"derived_state_rebuilds"}
    before = _projection_snapshot(repository, tables)
    runners = dict(orchestrator._RUNNERS)

    def accounts_for_nothing(name):
        def runner(spec, context):
            result = runners[name](spec, context)
            return dataclasses.replace(result, accounted_attempt_ids=())
        return runner

    for name in runners:
        monkeypatch.setitem(orchestrator._RUNNERS, name, accounts_for_nothing(name))
    with pytest.raises(orchestrator.ReplayCompletenessError):
        rebuild_all_derived_state(load_vault(root), repository, clock=CLOCK)
    assert _projection_snapshot(repository, tables) == before

def test_content_recalibration_replay_cannot_lose_its_ingest_lease_midway(tmp_path, monkeypatch):
    """The per-LO replay behind a content apply publishes all of it or none.

    It runs inside an ingest job's write fence. A replacement worker taking the
    lease between the replay's reset and its re-fold would otherwise make the
    next write raise ``JobOwnershipLost`` and leave the LO's derived state
    cleared. Holding one write transaction keeps the takeover out until the
    replay has committed.
    """

    import sqlite3

    import learnloop.substrate.replay as replay
    from learnloop.clock import utc_now_iso
    from learnloop.db.scopes import guard_ingest_writes

    reference_root = _copy_fixture(tmp_path, "reference")
    reference = Repository(reference_root / "state.sqlite")
    learning_object_id = reference.learning_object_ids_with_attempts()[0]
    replay.record_content_recalibration(
        load_vault(reference_root), reference,
        affected_learning_object_ids=[learning_object_id], clock=CLOCK,
    )

    root = _copy_fixture(tmp_path, "fenced")
    repository = Repository(root / "state.sqlite")
    repository.insert_ingest_batch(id="batch", workflow_type="import", clock=CLOCK)
    repository.insert_ingest_job(id="job", batch_id="batch", ordinal=0, job_type="fake", clock=CLOCK)
    claimed = repository.claim_next_ingest_job(
        worker_id="w1", now_iso=utc_now_iso(CLOCK), lease_cutoff_iso=utc_now_iso(CLOCK)
    )
    assert claimed["id"] == "job"

    takeover_outcomes: list[str] = []
    original_replay_attempt = replay.replay_existing_attempt

    def replacement_worker_claims_the_job_first(*args, **kwargs):
        if not takeover_outcomes:
            replacement = sqlite3.connect(repository.sqlite_path, timeout=0)
            try:
                with replacement:
                    replacement.execute(
                        "UPDATE ingest_jobs SET worker_id = 'w2', attempt_count = attempt_count + 1 WHERE id = 'job'"
                    )
                takeover_outcomes.append("claimed")
            except sqlite3.OperationalError as error:
                takeover_outcomes.append(str(error))
            finally:
                replacement.close()
        return original_replay_attempt(*args, **kwargs)

    monkeypatch.setattr(replay, "replay_existing_attempt", replacement_worker_claims_the_job_first)
    with guard_ingest_writes(repository.sqlite_path, "job", "w1", claimed["attempt_count"]):
        replay.record_content_recalibration(
            load_vault(root), repository,
            affected_learning_object_ids=[learning_object_id], clock=CLOCK,
        )

    assert takeover_outcomes == ["database is locked"]

    def mastery(repository_: Repository) -> dict:
        with connect(repository_.sqlite_path, read_only=True) as connection:
            row = connection.execute(
                "SELECT * FROM learning_object_mastery WHERE learning_object_id = ?",
                (learning_object_id,),
            ).fetchone()
        assert row is not None
        return {key: row[key] for key in row.keys() if key != "updated_at"}

    assert mastery(repository) == mastery(reference)

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
        "facet_outcome_observations": {
            "attempt_id": "stale_attempt",
            "facet_id": "stale_facet",
            "practice_item_id": "stale_item",
            "revision_status": "excluded",
            "observed_at": at,
            "outcome": 0.0,
            "facet_share": 1.0,
            "effective_mass": 0.0,
            "cold": 0,
            "assisted": 0,
            "primed": 0,
            "serving_origin": "unknown",
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
        "family_memory_state": {
            "family_id": "stale_family",
            "difficulty": 1.0,
            "stability": 1.0,
            "retrievability": 0.5,
            "last_review_at": at,
            "review_count": 1,
            "weights_hash": "stale",
            "projection_version": "stale",
        },
        "item_fingerprints": {
            "practice_item_id": "stale_item",
            "namespace": "surface_hash",
            "component": "stem",
            "value_hash": "stale",
            "item_content_hash": "stale",
            "fingerprint_version": "stale",
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
    # The field is an independent, read-only projection, not part of the
    # learning-state writer. Produce its golden cache through its direct API.
    from learnloop.field.outcomes import rebuild_outcome_view

    with repository.connection() as connection:
        rebuild_outcome_view(connection, vault)
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
