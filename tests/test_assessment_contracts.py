from __future__ import annotations

import pytest

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.services.assessment_contracts import (
    compile_assessment_contract,
    contract_hash,
    snapshot_for_presentation,
)
from learnloop.services.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
from learnloop.services.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault
from learnloop.vault.yaml_io import read_yaml, write_yaml

from tests.helpers import NOW, create_basic_vault, set_algorithm_version


def test_snapshot_authoritative_after_live_rubric_change(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    set_algorithm_version(paths, "mvp-0.7")
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    item = vault.practice_items["pi_svd_define_001"]

    version_id = snapshot_for_presentation(repository, vault, item)
    stored = repository.fetch_assessment_contract_version(version_id)
    original_total = stored["contract"]["rubric_total"]

    # Mutate the live rubric on disk after the snapshot was taken.
    item_path = paths.practice_item_path("linear-algebra", "pi_svd_define_001")
    data = read_yaml(item_path)
    data["grading_rubric"]["criteria"] = [
        {"id": "correctness", "points": 2, "description": "Correct definition."},
        {"id": "extra", "points": 2, "description": "Extra rigor."},
    ]
    write_yaml(item_path, data)

    # The stored snapshot is unchanged: grading/replay resolve against it.
    reread = repository.fetch_assessment_contract_version(version_id)
    assert reread["contract"]["rubric_total"] == original_total
    assert [c["id"] for c in reread["contract"]["criteria"]] == ["correctness"]


def test_identical_item_versions_reuse_one_snapshot(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    set_algorithm_version(paths, "mvp-0.7")
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    item = vault.practice_items["pi_svd_define_001"]

    first = snapshot_for_presentation(repository, vault, item)
    second = snapshot_for_presentation(repository, vault, item)
    assert first == second  # content-addressed, idempotent


def test_contract_hash_changes_when_targets_change(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    set_algorithm_version(paths, "mvp-0.7")
    vault = load_vault(paths.root)
    item = vault.practice_items["pi_svd_define_001"]
    baseline = contract_hash(compile_assessment_contract(vault, item))

    # An authored capability target changes attribution -> a new contract hash.
    item_path = paths.practice_item_path("linear-algebra", "pi_svd_define_001")
    data = read_yaml(item_path)
    data["grading_rubric"]["criteria"][0]["targets"] = [
        {"facet": "recall", "capability": "coordination", "role": "primary"}
    ]
    write_yaml(item_path, data)
    reloaded = load_vault(paths.root)
    changed = contract_hash(
        compile_assessment_contract(reloaded, reloaded.practice_items["pi_svd_define_001"])
    )
    assert changed != baseline


def test_observation_id_attaches_once(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    repository = Repository(paths.sqlite_path)
    from tests.test_migrations import _insert_attempt
    from learnloop.db.connection import connect

    with connect(paths.sqlite_path) as connection:
        _insert_attempt(connection, attempt_id="att1", attempt_type="independent_attempt")
        connection.commit()

    row = {
        "criterion_id": "c1",
        "points_awarded": 1.0,
        "grader_tier": 1,
        "created_at": "2026-01-01T00:00:00Z",
        "observation_id": "att1:c1:0",
    }
    repository.insert_grading_evidence("att1", [row])
    # A second row with the same observation_id violates the unique index.
    with pytest.raises(Exception):
        repository.insert_grading_evidence(
            "att1",
            [{**row, "id": "different_id"}],
        )


def test_mvp07_attempt_stamps_observation_lineage(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    set_algorithm_version(paths, "mvp-0.7")
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    clock = FrozenClock(NOW)
    sync_vault_state(vault, repository, clock=clock)

    result = complete_self_graded_attempt(
        vault,
        repository,
        AttemptDraft(
            practice_item_id="pi_svd_define_001",
            learner_answer_md="SVD is U Sigma V^T.",
            attempt_type="independent_attempt",
        ),
        SelfGradeInput(criterion_points={"correctness": 4}, fatal_errors=[], confidence=4),
        clock=clock,
    )
    evidence = repository.fetch_grading_evidence(result.attempt_id)
    assert evidence
    row = evidence[0]
    assert row.observation_id == f"{result.attempt_id}:correctness:0"
    assert row.grading_revision == 0
    assert row.assessment_contract_version_id is not None


def test_legacy_attempt_records_no_observation_lineage(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")  # mvp-0.6 default
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    clock = FrozenClock(NOW)
    sync_vault_state(vault, repository, clock=clock)

    result = complete_self_graded_attempt(
        vault,
        repository,
        AttemptDraft(
            practice_item_id="pi_svd_define_001",
            learner_answer_md="SVD is U Sigma V^T.",
            attempt_type="independent_attempt",
        ),
        SelfGradeInput(criterion_points={"correctness": 4}, fatal_errors=[], confidence=4),
        clock=clock,
    )
    evidence = repository.fetch_grading_evidence(result.attempt_id)
    assert evidence
    # Legacy path leaves the KM1 lineage columns NULL (replay stays identical).
    assert evidence[0].observation_id is None
    assert evidence[0].assessment_contract_version_id is None
    contracts = repository.fetch_assessment_contract_version("nonexistent")
    assert contracts is None
