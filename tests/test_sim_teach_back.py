"""Simulation-harness coverage for the teach_back practice mode.

The synthetic vault is a copy of the standard sim vault plus one
``practice_mode: "teach_back"`` item with a two-tier rubric (one core criterion
per evidence facet + a facet-mapped transfer criterion), built in a temp dir --
``fixtures/`` is never touched.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from learnloop.config import LearnLoopConfig
from learnloop.sim.profiles import profile_from_mapping
from learnloop.sim.runner import apply_config_overrides, prepare_run_vault, run_simulation
from learnloop.sim.student import StudentProfile, SyntheticStudent
from learnloop.sim.sweep import DEFAULT_SWEEP_SPEC_PATH, SweepEntry, load_sweep_spec, run_sweep
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths
from learnloop.vault.yaml_io import write_yaml

from tests.test_simulation import NOW_ISO, PLANTED_FACET, build_sim_vault

TEACH_ITEM_ID = "pi_teach_move_terms"


def _teach_back_item() -> dict:
    return {
        "schema_version": 1,
        "id": TEACH_ITEM_ID,
        "learning_object_id": "lo_move_terms",
        "subjects": None,
        "practice_mode": "teach_back",
        "attempt_types_allowed": ["teach_back"],
        "evidence_facets": [PLANTED_FACET, "recall"],
        "evidence_weights": {"recall": 0.5, PLANTED_FACET: 0.5},
        "criterion_facet_weights": {
            "core_recall": {"recall": 1.0},
            "core_signs": {PLANTED_FACET: 1.0},
            "transfer_edge": {"recall": 0.5, PLANTED_FACET: 0.5},
        },
        "prompt": "Teach me how to move terms across an equality.",
        "expected_answer": "Explains term movement including sign flips.",
        "difficulty": 0.5,
        "tags": [],
        "hints": [],
        "grading_rubric": {
            "max_points": 4,
            "criteria": [
                {
                    "id": "core_recall",
                    "points": 1,
                    "description": "Explains the basic manipulation procedure.",
                    "tier": "core",
                },
                {
                    "id": "core_signs",
                    "points": 1,
                    "description": "Explains why signs flip when terms move.",
                    "tier": "core",
                },
                {
                    "id": "transfer_edge",
                    "points": 2,
                    "description": "Handles an unfamiliar edge case (what-if).",
                    "tier": "transfer",
                },
            ],
            "fatal_errors": [],
        },
        "provenance": {"origin": "human", "source_refs": []},
        "created_at": NOW_ISO,
        "updated_at": NOW_ISO,
    }


def build_teach_back_sim_vault(root: Path) -> Path:
    build_sim_vault(root)
    vault = load_vault(root)
    paths = VaultPaths(vault.root, vault.config)
    write_yaml(paths.practice_item_path("algebra", TEACH_ITEM_ID), _teach_back_item())
    return root


@pytest.fixture(scope="module")
def teach_vault(tmp_path_factory) -> Path:
    return build_teach_back_sim_vault(tmp_path_factory.mktemp("teach-source") / "vault")


@pytest.fixture(scope="module")
def teach_runs(teach_vault, tmp_path_factory):
    directory = tmp_path_factory.mktemp("teach-runs")
    runs = []
    for name in ("first", "second"):
        root = prepare_run_vault(teach_vault, directory / name)
        runs.append((root, run_simulation(root, _profile(), days=8, items_per_day=7, seed=42)))
    return runs


def _profile() -> StudentProfile:
    return profile_from_mapping(
        {
            "name": "teach_back_student",
            "true_mastery": 0.75,
            "learning_rate": 0.15,
            "forgetting_halflife_days": 30,
            "slip": 0.03,
            "guess": 0.05,
            "hint_propensity": 0.1,
            "confidence_calibration": 0.9,
            "transfer_difficulty_delta": 0.3,
        }
    )


# -- student answer model -----------------------------------------------------


def test_teach_back_answer_respects_mastery_and_transfer_delta() -> None:
    profile = StudentProfile(
        name="deterministic",
        true_mastery=1.0,
        slip=0.0,
        guess=0.0,
        transfer_difficulty_delta=1.0,
    )
    student = SyntheticStudent(profile, seed=3)
    weights = {"recall": 1.0}
    for _ in range(25):
        core = student.teach_back_answer(
            day=0.0,
            tier="core",
            criterion_weights=weights,
            item_facet_weights=weights,
            max_points=2.0,
        )
        assert core.p_know_effective == pytest.approx(1.0)
        assert core.points_awarded == 2.0  # mastery 1.0, no slip: always full credit
    saw_full_transfer = False
    for _ in range(50):
        transfer = student.teach_back_answer(
            day=0.0,
            tier="transfer",
            criterion_weights=weights,
            item_facet_weights=weights,
            max_points=2.0,
        )
        assert transfer.p_know_effective == pytest.approx(0.0)  # delta wipes mastery
        saw_full_transfer = saw_full_transfer or transfer.points_awarded == 2.0
        assert transfer.points_awarded in (0.0, 1.0)  # zero or partial credit only
    assert not saw_full_transfer


def test_teach_back_transfer_delta_lowers_success_statistically() -> None:
    profile = StudentProfile(name="stats", true_mastery=0.7, transfer_difficulty_delta=0.4)
    student = SyntheticStudent(profile, seed=11)
    weights = {"recall": 1.0}

    def mean_points(tier: str, n: int = 400) -> float:
        total = 0.0
        for _ in range(n):
            total += student.teach_back_answer(
                day=0.0,
                tier=tier,
                criterion_weights=weights,
                item_facet_weights=weights,
                max_points=1.0,
            ).points_awarded
        return total / n

    assert mean_points("core") > mean_points("transfer") + 0.15


def test_transfer_difficulty_delta_round_trips_through_profile() -> None:
    profile = _profile()
    assert profile.transfer_difficulty_delta == 0.3
    assert profile.as_dict()["transfer_difficulty_delta"] == 0.3


# -- runner ---------------------------------------------------------------


def test_runner_completes_session_with_teach_back_item(
    teach_runs,
) -> None:
    run_root, report = teach_runs[0]

    teach_attempts = [a for a in report.attempts if a.attempt_type == "teach_back"]
    assert teach_attempts, "the teach_back item was never practiced"
    for attempt in teach_attempts:
        assert attempt.practice_item_id == TEACH_ITEM_ID
        assert attempt.hints_used == 0
        assert 0 <= attempt.rubric_score <= 4
        assert 0.0 <= attempt.observed_correctness <= 1.0
    assert report.metrics["counts"]["teach_back_attempts"] == len(teach_attempts)
    # The attempt landed in the DB as ONE teach_back attempt via apply_attempt.
    from learnloop.db.repositories import Repository

    vault = load_vault(run_root)
    repository = Repository(VaultPaths(vault.root, vault.config).sqlite_path)
    with repository.connection() as connection:
        rows = connection.execute(
            "SELECT attempt_type, practice_item_id FROM practice_attempts "
            "WHERE attempt_type = 'teach_back'"
        ).fetchall()
    assert len(rows) == len(teach_attempts)
    assert all(row["practice_item_id"] == TEACH_ITEM_ID for row in rows)
    # Belief-vs-truth metrics include the teach_back item's LO like any other.
    belief_los = {
        entry["learning_object_id"]
        for entry in report.metrics["belief_vs_truth"]["per_learning_object"]
    }
    assert "lo_move_terms" in belief_los


def test_teach_back_runs_are_seed_deterministic(teach_runs) -> None:
    reports = [report for _, report in teach_runs]
    assert reports[0].deterministic_dict() == reports[1].deterministic_dict()
    assert any(a.attempt_type == "teach_back" for a in reports[0].attempts)


# -- sweep knobs ------------------------------------------------------------


def test_teach_back_config_overrides_round_trip() -> None:
    updated = apply_config_overrides(
        LearnLoopConfig(),
        {
            "evidence.attempt_types.teach_back.evidence_mass": 0.4,
            "teach_back.transfer_evidence_multiplier": 0.25,
        },
    )
    assert updated.evidence.attempt_types["teach_back"].evidence_mass == 0.4
    assert updated.teach_back.transfer_evidence_multiplier == 0.25


def test_default_sweep_spec_includes_teach_back_knobs() -> None:
    params = {entry.param_path for entry in load_sweep_spec(DEFAULT_SWEEP_SPEC_PATH)}
    assert "evidence.attempt_types.teach_back.evidence_mass" in params
    assert "teach_back.transfer_evidence_multiplier" in params


def test_sweep_runs_with_teach_back_knobs(teach_vault: Path, tmp_path: Path) -> None:
    report = run_sweep(
        teach_vault,
        _profile(),
        sweep_spec=[
            SweepEntry(
                param_path="evidence.attempt_types.teach_back.evidence_mass",
                values=[0.4],
            ),
            SweepEntry(
                param_path="teach_back.transfer_evidence_multiplier",
                values=[0.25],
            ),
        ],
        days=4,
        items_per_day=7,
        seed=42,
        work_dir=tmp_path / "sweep",
    )
    by_param = {result["param_path"]: result for result in report.results}
    assert set(by_param) == {
        "evidence.attempt_types.teach_back.evidence_mass",
        "teach_back.transfer_evidence_multiplier",
    }
    for result in by_param.values():
        assert result.get("error") is None
        assert result["verdict"] in ("decision-relevant", "inert in this scenario")
    assert report.baseline["metrics"]["counts"]["teach_back_attempts"] >= 1
