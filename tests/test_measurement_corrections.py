from __future__ import annotations

import sqlite3

import pytest

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.services.canonical_projection import CANONICAL_PROJECTION_VERSION
from learnloop.services.measurement_corrections import (
    MeasurementCorrectionError,
    create_measurement_correction,
)
from learnloop.services.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault

from tests.helpers import NOW
from tests.test_km2_write_path import SHARED, _attempt, build_mvp07_vault


def test_attempted_item_correction_is_append_only_and_projection_versioned(tmp_path):
    paths = build_mvp07_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    sync_vault_state(vault, repository, clock=FrozenClock(NOW))
    _attempt(
        vault,
        repository,
        "pi_svd_define_001",
        {"correctness": 4},
        FrozenClock(NOW),
    )
    source_path = paths.practice_item_path("linear-algebra", "pi_svd_define_001")
    source_bytes = source_path.read_bytes()
    source_contract_id = repository.assessment_contract_versions_for_practice_item(
        "pi_svd_define_001"
    )[0]["id"]
    assert repository.canonical_facet_recall_state(SHARED, "retrieval", None) is not None

    corrected_rubric = {
        "max_points": 4,
        "criteria": [
            {
                "id": "correctness",
                "points": 4,
                "description": "Correct response, but not a canonical-facet measure.",
                "measurement_status": "no_canonical_facet",
                "targets": [],
            }
        ],
        "fatal_errors": [],
    }
    result = create_measurement_correction(
        paths.root,
        repository,
        source_practice_item_id="pi_svd_define_001",
        corrected_practice_item_id="pi_svd_define_001_measurement_v2",
        corrected_fields={
            "grading_rubric": corrected_rubric,
            "criterion_facet_weights": {},
        },
        reason="The criterion measured an item-local response, not SVD recall.",
        consuming_projection_version="mvp-0.7",
        reinterpret_historical_evidence=True,
        clock=FrozenClock(NOW),
    )

    assert source_path.read_bytes() == source_bytes
    assert result.source_contract_version_ids == [source_contract_id]
    corrections = repository.measurement_contract_corrections(
        correction_set_id=result.correction_set_id
    )
    assert len(corrections) == 1
    assert corrections[0]["consuming_projection_version"] == "mvp-0.7"
    assert corrections[0]["historical_evidence_policy"] == "reinterpret_measurement"
    assert corrections[0]["corrected_contract_version_id"] == result.corrected_contract_version_id
    assert result.projection_rebuild_id is not None
    marker = repository.latest_derived_state_rebuild()
    assert marker is not None
    assert marker["canonical_projection_version"] == CANONICAL_PROJECTION_VERSION
    assert marker["coverage_denominator_version"] is not None

    original = repository.fetch_assessment_contract_version(source_contract_id)
    effective_v07 = repository.effective_assessment_contract_version(
        source_contract_id, projection_version="mvp-0.7"
    )
    effective_v08 = repository.effective_assessment_contract_version(
        source_contract_id, projection_version="mvp-0.8"
    )
    assert effective_v07 is not None and effective_v07["id"] == result.corrected_contract_version_id
    assert effective_v08 is not None and original is not None
    assert effective_v08["id"] == original["id"]

    assert repository.canonical_facet_recall_state(SHARED, "retrieval", None) is None
    assert repository.practice_item_state("pi_svd_define_001").active is False
    assert repository.practice_item_state(result.corrected_practice_item_id).active is True

    with repository.connection() as connection:
        with pytest.raises(sqlite3.IntegrityError, match="append-only"):
            connection.execute(
                "UPDATE measurement_contract_corrections SET reason = 'rewritten' WHERE id = ?",
                (result.correction_ids[0],),
            )


def test_historical_reinterpretation_rejects_a_changed_task(tmp_path):
    paths = build_mvp07_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    sync_vault_state(vault, repository, clock=FrozenClock(NOW))
    _attempt(
        vault,
        repository,
        "pi_svd_define_001",
        {"correctness": 4},
        FrozenClock(NOW),
    )

    with pytest.raises(MeasurementCorrectionError, match="cannot change prompt"):
        create_measurement_correction(
            paths.root,
            repository,
            source_practice_item_id="pi_svd_define_001",
            corrected_practice_item_id="pi_illegal_changed_task",
            corrected_fields={"prompt": "A different question."},
            reason="This should be a new assessment, not a reinterpretation.",
            consuming_projection_version="mvp-0.7",
            reinterpret_historical_evidence=True,
            clock=FrozenClock(NOW),
        )

    assert "pi_illegal_changed_task" not in load_vault(paths.root).practice_items
    assert repository.measurement_contract_corrections(
        source_practice_item_id="pi_svd_define_001"
    ) == []
