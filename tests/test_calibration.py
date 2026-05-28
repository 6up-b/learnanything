"""Tests for the difficulty-miscalibration monitor (spec_irt_difficulty.md §7.4)."""

from __future__ import annotations

import json

from learnloop.clock import FrozenClock
from learnloop.db.repositories import MasteryState, Repository
from learnloop.services.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
from learnloop.services.calibration import difficulty_miscalibration_flags
from learnloop.services.doctor import run_doctor
from learnloop.vault.loader import load_vault
from learnloop.vault.writer import upsert_practice_item

from tests.helpers import NOW, NOW_ISO, create_basic_vault


class _StubRepo:
    """Minimal repository exposing only attempt_innovation_samples."""

    def __init__(self, samples):
        self._samples = samples

    def attempt_innovation_samples(self):
        return self._samples


def _sample(item_id: str, score: int, expected: float | None, lo: str = "lo_svd_definition") -> dict:
    dist = {"mu_z": 0.0, "sigma_z": 1.0, "b": 0.0, "a": 1.0}
    if expected is not None:
        dist["expected_correctness"] = expected
    return {
        "practice_item_id": item_id,
        "learning_object_id": lo,
        "rubric_score": score,
        "predicted_score_dist_json": json.dumps(dist),
    }


def _vault(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    return load_vault(vault_root)


# --- unit: aggregation logic -------------------------------------------------


def test_persistent_overperformance_flags_too_hard(tmp_path):
    vault = _vault(tmp_path)
    # 5 aces (y=1) against a predicted correctness of 0.15 -> innovation +0.85.
    samples = [_sample("pi_svd_define_001", 4, 0.15) for _ in range(5)]
    flags = difficulty_miscalibration_flags(vault, _StubRepo(samples))
    assert len(flags) == 1
    assert flags[0].practice_item_id == "pi_svd_define_001"
    assert flags[0].direction == "too_hard"
    assert flags[0].attempts == 5
    assert flags[0].mean_innovation > 0.5
    assert "b too hard" in flags[0].message


def test_persistent_underperformance_flags_too_easy(tmp_path):
    vault = _vault(tmp_path)
    samples = [_sample("pi_svd_define_001", 0, 0.9) for _ in range(5)]  # innovation -0.9
    flags = difficulty_miscalibration_flags(vault, _StubRepo(samples))
    assert len(flags) == 1
    assert flags[0].direction == "too_easy"
    assert flags[0].mean_innovation < -0.5
    assert "b too easy" in flags[0].message


def test_below_min_attempts_is_not_flagged(tmp_path):
    vault = _vault(tmp_path)
    samples = [_sample("pi_svd_define_001", 4, 0.1) for _ in range(4)]
    assert difficulty_miscalibration_flags(vault, _StubRepo(samples)) == []


def test_balanced_innovation_is_not_flagged(tmp_path):
    vault = _vault(tmp_path)
    # innovation +0.1, well within the +/-0.5 band.
    samples = [_sample("pi_svd_define_001", 2, 0.4) for _ in range(8)]
    assert difficulty_miscalibration_flags(vault, _StubRepo(samples)) == []


def test_samples_without_expected_correctness_are_skipped(tmp_path):
    vault = _vault(tmp_path)
    # Pre-IRT surprise rows carry no expected_correctness; they cannot be scored.
    samples = [_sample("pi_svd_define_001", 4, None) for _ in range(10)]
    assert difficulty_miscalibration_flags(vault, _StubRepo(samples)) == []


def test_unknown_items_are_ignored(tmp_path):
    vault = _vault(tmp_path)
    samples = [_sample("pi_does_not_exist", 4, 0.1) for _ in range(6)]
    assert difficulty_miscalibration_flags(vault, _StubRepo(samples)) == []


def test_threshold_and_min_attempts_are_configurable(tmp_path):
    vault = _vault(tmp_path)
    samples = [_sample("pi_svd_define_001", 4, 0.6) for _ in range(3)]  # innovation +0.4
    assert difficulty_miscalibration_flags(vault, _StubRepo(samples)) == []
    flags = difficulty_miscalibration_flags(vault, _StubRepo(samples), min_attempts=3, threshold=0.3)
    assert len(flags) == 1
    assert flags[0].direction == "too_hard"


# --- integration: through the real attempt pipeline + doctor -----------------


def _ace_repeatedly(tmp_path, difficulty: float, count: int):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    upsert_practice_item(
        vault_root,
        {
            "id": "pi_mislabeled",
            "learning_object_id": "lo_svd_definition",
            "subjects": None,
            "practice_mode": "short_answer",
            "attempt_types_allowed": ["independent_attempt"],
            "evidence_facets": ["recall"],
            "evidence_weights": {"recall": 1.0},
            "prompt": "p",
            "expected_answer": "x",
            "difficulty": difficulty,
            "grading_rubric": {
                "max_points": 4,
                "criteria": [{"id": "correctness", "points": 4, "description": "c"}],
                "fatal_errors": [],
            },
        },
        clock=FrozenClock(NOW),
    )
    repository = Repository(paths.sqlite_path)
    repository.upsert_mastery_state(
        MasteryState("lo_svd_definition", 0.0, 1.0, 1, NOW_ISO, "mvp-0.1", NOW_ISO)
    )
    loaded = load_vault(vault_root)
    for _ in range(count):
        complete_self_graded_attempt(
            loaded,
            repository,
            AttemptDraft(practice_item_id="pi_mislabeled", learner_answer_md="x"),
            # Low confidence keeps the latent mu pinned so the innovation stays one-sided.
            SelfGradeInput(criterion_points={"correctness": 4}, confidence=1),
            clock=FrozenClock(NOW),
        )
    return vault_root, loaded, repository


def test_pipeline_flags_an_item_rated_too_hard(tmp_path):
    _root, loaded, repository = _ace_repeatedly(tmp_path, difficulty=0.95, count=6)
    flags = difficulty_miscalibration_flags(loaded, repository)
    item_flags = {flag.practice_item_id: flag for flag in flags}
    assert "pi_mislabeled" in item_flags
    assert item_flags["pi_mislabeled"].direction == "too_hard"


def test_doctor_surfaces_miscalibration_warning(tmp_path):
    root, _loaded, _repository = _ace_repeatedly(tmp_path, difficulty=0.95, count=6)
    report = run_doctor(root)
    codes = {(issue.code, issue.entity_id) for issue in report.issues}
    assert ("difficulty:miscalibrated", "pi_mislabeled") in codes


def test_doctor_does_not_flag_a_well_calibrated_item(tmp_path):
    # Acing a genuinely easy item (b ~ -2.25) matches the prediction -> no flag.
    root, _loaded, _repository = _ace_repeatedly(tmp_path, difficulty=0.05, count=6)
    report = run_doctor(root)
    codes = {issue.code for issue in report.issues}
    assert "difficulty:miscalibrated" not in codes
