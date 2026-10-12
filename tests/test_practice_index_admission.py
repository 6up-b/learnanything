"""find_practice admission reuses the scheduler's eligibility rules, read-only."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from learnloop.clock import FrozenClock
from learnloop.practice_index.admission import EXCLUSION_REASONS, PracticeAdmission
from learnloop.scheduling.scheduler import build_due_queue
from learnloop.vault.loader import load_vault
from learnloop.vault.repository import open_vault_repository
from learnloop.vault.yaml_io import read_yaml, write_yaml
from tests.practice_index_fakes import build_practice_vault

NOW = datetime(2026, 10, 12, 12, 0, tzinfo=UTC)


def _iso(value: datetime) -> str:
    return value.replace(microsecond=0).isoformat().replace("+00:00", "Z")


@pytest.fixture
def practice(tmp_path):
    paths = build_practice_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    repository = open_vault_repository(vault.root, paths.sqlite_path)
    return paths, vault, repository


def _reason(vault, repository, item_id):
    admission = PracticeAdmission.load(vault, repository, clock=FrozenClock(NOW))
    return admission.exclusion_reason(vault, vault.practice_items[item_id])


def test_everything_the_scheduler_would_serve_is_admitted(practice):
    _paths, vault, repository = practice
    queue = build_due_queue(vault, repository, persist_explanations=False, clock=FrozenClock(NOW))
    admission = PracticeAdmission.load(vault, repository, clock=FrozenClock(NOW))
    admitted, excluded = admission.admit(vault, sorted(vault.practice_items))
    assert {entry.practice_item_id for entry in queue} <= set(admitted)
    assert not excluded


def test_admission_never_writes(practice):
    paths, vault, repository = practice
    before = paths.sqlite_path.read_bytes()
    admission = PracticeAdmission.load(vault, repository, clock=FrozenClock(NOW))
    admission.admit(vault, sorted(vault.practice_items))
    assert paths.sqlite_path.read_bytes() == before


def test_retired_and_deactivated_items_are_excluded(practice):
    _paths, vault, repository = practice
    vault.practice_items["pi_eigen_1"].status = "retired"
    repository.upsert_practice_item_state("pi_eigen_2", active=False)
    assert _reason(vault, repository, "pi_eigen_1") == "retired"
    assert _reason(vault, repository, "pi_eigen_2") == "inactive_state"
    assert _reason(vault, repository, "pi_eigen_3") is None


def test_exam_reserves_and_diagnostic_surfaces_are_excluded(practice):
    _paths, vault, repository = practice
    repository.insert_exam_pool_items([{
        "id": "epi_1", "goal_id": "goal_linear_algebra_ml", "practice_item_id": "pi_span_1",
        "reserved_at": _iso(NOW),
    }])
    vault.practice_items["pi_span_2"].practice_mode = "diagnostic_probe"
    vault.practice_items["pi_span_3"].practice_mode = "diagnostic_microprobe"
    assert _reason(vault, repository, "pi_span_1") == "exam_reserved"
    assert _reason(vault, repository, "pi_span_2") == "diagnostic_reserve"
    assert _reason(vault, repository, "pi_span_3") == "dialogue_instance"


def test_parked_learning_objects_are_excluded(practice):
    paths, _vault, repository = practice
    lo_path = paths.learning_object_path("linear-algebra", "lo_inner")
    data = read_yaml(lo_path)
    data["status"] = "dormant"
    write_yaml(lo_path, data)
    vault = load_vault(paths.root)
    assert _reason(vault, repository, "pi_orthogonal_1") == "lo_not_servable"
    assert _reason(vault, repository, "pi_span_1") is None


def test_reserved_cold_checks_and_recent_reveals_are_excluded(practice):
    _paths, vault, repository = practice
    repository.create_followup_task(
        kind="cold_retry", case_kind="diagnosis", case_ref="case-1",
        not_before=_iso(NOW + timedelta(days=2)), selected_item_id="pi_matmul_1",
        clock=FrozenClock(NOW),
    )
    repository.insert_reveal_event({
        "practice_item_id": "pi_matmul_2", "source_kind": "tutor_answer", "amount": 1.0,
        "created_at": _iso(NOW - timedelta(hours=2)),
    })
    repository.insert_reveal_event({
        "practice_item_id": "pi_matmul_3", "source_kind": "tutor_answer", "amount": 1.0,
        "created_at": _iso(NOW - timedelta(days=3)),
    })
    assert _reason(vault, repository, "pi_matmul_1") == "cold_check_reserved"
    assert _reason(vault, repository, "pi_matmul_2") == "revealed_recently"
    # Outside the cold retrieval delay the item is ordinary practice again.
    assert _reason(vault, repository, "pi_matmul_3") is None


def test_exclusion_reasons_are_declared():
    assert len(EXCLUSION_REASONS) == len(set(EXCLUSION_REASONS))
    assert {"exam_reserved", "lo_not_servable", "cold_check_reserved", "revealed_recently",
            "diagnostic_reserve"} <= set(EXCLUSION_REASONS)


def test_shared_rules_exclude_exactly_what_the_scheduler_drops(practice):
    """The rules both doors apply agree item for item (the parity pin)."""
    paths, _vault, repository = practice
    for item_id, change in (("pi_eigen_1", {"status": "retired"}),
                            ("pi_span_2", {"practice_mode": "diagnostic_probe"})):
        item_path = paths.practice_item_path("linear-algebra", item_id)
        write_yaml(item_path, {**read_yaml(item_path), **change})
    lo_path = paths.learning_object_path("linear-algebra", "lo_inner")
    write_yaml(lo_path, {**read_yaml(lo_path), "status": "resolved"})
    repository.insert_exam_pool_items([{
        "id": "epi_1", "goal_id": "goal_linear_algebra_ml", "practice_item_id": "pi_span_1",
        "reserved_at": _iso(NOW),
    }])
    vault = load_vault(paths.root)
    queue = build_due_queue(vault, repository, persist_explanations=False, clock=FrozenClock(NOW))
    admission = PracticeAdmission.load(vault, repository, clock=FrozenClock(NOW))
    admitted, excluded = admission.admit(vault, sorted(vault.practice_items))
    assert {entry.practice_item_id for entry in queue} == set(admitted)
    assert excluded == {
        "pi_eigen_1": "retired", "pi_span_1": "exam_reserved", "pi_span_2": "diagnostic_reserve",
        "pi_orthogonal_1": "lo_not_servable", "pi_orthogonal_2": "lo_not_servable",
        "pi_orthogonal_3": "lo_not_servable",
    }
