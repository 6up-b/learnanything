"""Goal attainment metrics in the simulation harness (Phase 2 of the goal redesign).

The runner snapshots the synthetic student's *true* facet mastery on each
goal's due day and projects retention 30 no-practice days later, so sweeps can
measure the cram-vs-space tradeoff a goal quota makes.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from learnloop.sim.profiles import profile_from_mapping
from learnloop.sim.runner import prepare_run_vault, run_simulation
from learnloop.sim.student import SyntheticStudent

from tests.simulation_helpers import build_sim_vault

GOAL_ID = "goal_algebra"


@pytest.fixture()
def sim_vault(tmp_path: Path) -> Path:
    return build_sim_vault(tmp_path / "source_vault")


def _profile():
    return profile_from_mapping(
        {
            "name": "test_goal_metrics",
            "true_mastery": 0.6,
            "learning_rate": 0.15,
            "forgetting_halflife_days": 20,
            "slip": 0.03,
            "guess": 0.05,
            "hint_propensity": 0.1,
            "confidence_calibration": 0.9,
        }
    )


def test_goal_metrics_reported_with_due_day(sim_vault: Path, tmp_path: Path) -> None:
    run_root = prepare_run_vault(sim_vault, tmp_path / "run")
    report = run_simulation(
        run_root, _profile(), days=8, items_per_day=3, seed=7, goal_due_day=6
    )

    per_goal = report.metrics["goals"]["per_goal"]
    assert len(per_goal) == 1
    entry = per_goal[0]
    assert entry["goal_id"] == GOAL_ID
    assert entry["due_day"] == 6
    assert entry["snapshot_day"] == 6
    assert entry["target_recall"] == pytest.approx(0.8)
    assert entry["scope_facet_count"] > 0
    for key in (
        "truth_at_target_fraction_at_due",
        "truth_at_target_fraction_due_plus_30",
        "belief_on_track_fraction_at_due",
    ):
        assert 0.0 <= entry[key] <= 1.0
    # 30 no-practice days can only lose mastery, never gain it.
    assert entry["truth_mean_recall_due_plus_30"] <= entry["truth_mean_recall_at_due"]
    # Per-day belief-side frontier sizes are tracked for the goal.
    assert all(GOAL_ID in record.goal_at_risk_facets for record in report.day_records)
    assert report.goal_due_day == 6
    assert report.as_dict()["goal_due_day"] == 6


def test_goal_metrics_without_due_day_snapshot_at_run_end(
    sim_vault: Path, tmp_path: Path
) -> None:
    run_root = prepare_run_vault(sim_vault, tmp_path / "run")
    report = run_simulation(run_root, _profile(), days=5, items_per_day=3, seed=7)

    entry = report.metrics["goals"]["per_goal"][0]
    assert entry["due_day"] is None
    assert entry["snapshot_day"] == 4  # final day: "as of run end"


def test_goal_metrics_deterministic_across_same_seed(
    sim_vault: Path, tmp_path: Path
) -> None:
    reports = []
    for name in ("run_a", "run_b"):
        run_root = prepare_run_vault(sim_vault, tmp_path / name)
        reports.append(
            run_simulation(
                run_root, _profile(), days=6, items_per_day=3, seed=11, goal_due_day=4
            )
        )
    assert (
        reports[0].metrics["goals"] == reports[1].metrics["goals"]
    )
    assert reports[0].deterministic_dict() == reports[1].deterministic_dict()


def test_projected_mastery_matches_forgetting_model() -> None:
    profile = _profile()
    student = SyntheticStudent(profile, seed=3)
    student.learn({"recall": 1.0}, day=0.0)
    at_due = student.mastery_at("recall", 10.0)

    assert student.projected_mastery("recall", 10.0, 0.0) == pytest.approx(at_due)
    projected = student.projected_mastery("recall", 10.0, 30.0)
    floor = min(profile.forgetting_floor, at_due)
    expected = floor + (at_due - floor) * 2.0 ** (-30.0 / profile.forgetting_halflife_days)
    assert projected == pytest.approx(expected)
    assert projected < at_due
    # Analytic projection must not disturb the lazy-decay state.
    assert student.mastery_at("recall", 10.0) == pytest.approx(at_due)
