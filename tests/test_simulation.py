from __future__ import annotations

from pathlib import Path

import pytest

from learnloop.sim.profiles import load_profile, profile_from_mapping
from learnloop.sim.runner import (
    apply_config_overrides,
    prepare_run_vault,
    run_simulation,
    SimulationError,
)
from learnloop.sim.student import SyntheticStudent
from learnloop.sim.sweep import SweepEntry, run_sweep
from learnloop.config import LearnLoopConfig
from tests.simulation_helpers import PLANTED_ERROR, PLANTED_FACET, build_sim_vault

@pytest.fixture()
def sim_vault(tmp_path: Path) -> Path:
    return build_sim_vault(tmp_path / "source_vault")


def _misconception_profile():
    return profile_from_mapping(
        {
            "name": "test_misconception",
            "true_mastery": 0.85,
            "learning_rate": 0.15,
            "forgetting_halflife_days": 30,
            "slip": 0.03,
            "guess": 0.05,
            "hint_propensity": 0.1,
            "confidence_calibration": 0.9,
            "misconceptions": [
                {"facet_id": PLANTED_FACET, "error_type": PLANTED_ERROR, "strength": 0.9}
            ],
        }
    )


def test_same_seed_produces_identical_reports(sim_vault: Path, tmp_path: Path) -> None:
    profile = _misconception_profile()
    reports = []
    for name in ("run_a", "run_b"):
        run_root = prepare_run_vault(sim_vault, tmp_path / name)
        reports.append(
            run_simulation(run_root, profile, days=8, items_per_day=4, seed=7)
        )
    assert reports[0].deterministic_dict() == reports[1].deterministic_dict()
    # And a different seed actually changes outcomes.
    run_root = prepare_run_vault(sim_vault, tmp_path / "run_c")
    other = run_simulation(run_root, _misconception_profile(), days=8, items_per_day=4, seed=8)
    assert other.deterministic_dict() != reports[0].deterministic_dict()


def test_planted_misconception_is_identified(sim_vault: Path, tmp_path: Path) -> None:
    run_root = prepare_run_vault(sim_vault, tmp_path / "run")
    report = run_simulation(
        run_root, _misconception_profile(), days=15, items_per_day=4, seed=42
    )
    planted = report.metrics["misconceptions"]["planted"]
    assert len(planted) == 1
    entry = planted[0]
    assert entry["error_type"] == PLANTED_ERROR
    assert entry["detected"] is True
    assert entry["first_error_event_day"] is not None
    assert entry["first_error_event_day"] <= 5
    assert entry["error_events"] >= 3  # the signal accumulates
    # Belief accuracy improves over the run vs day 1.
    belief = report.metrics["belief_vs_truth"]
    assert belief["daily_mae_first"] is not None and belief["daily_mae_last"] is not None
    assert belief["daily_mae_last"] < belief["daily_mae_first"]
    # Calibration numbers exist and are finite.
    assert report.metrics["calibration"]["n"] > 0
    assert report.metrics["calibration"]["log_loss"] is not None


def test_sweep_flags_decision_relevant_and_inert_params(
    sim_vault: Path, tmp_path: Path
) -> None:
    report = run_sweep(
        sim_vault,
        _misconception_profile(),
        sweep_spec=[
            # An extreme follow-up gate threshold fires interventions that
            # reorder the daily queues and change resolution counts.
            SweepEntry(param_path="scheduler.followup.gate_score_threshold", values=[0.05]),
            # An ingest knob can never touch scheduling in this scenario.
            SweepEntry(param_path="ingest.window_char_cap", values=[999999]),
        ],
        days=12,
        items_per_day=2,
        seed=42,
        work_dir=tmp_path / "sweep",
    )
    by_param = {result["param_path"]: result for result in report.results}
    relevant = by_param["scheduler.followup.gate_score_threshold"]
    inert = by_param["ingest.window_char_cap"]
    assert relevant["verdict"] == "decision-relevant"
    # Queue order actually moved (Kendall tau on daily queues dropped) or the
    # follow-up/resolution machinery changed the run.
    assert (
        (relevant["mean_kendall_tau"] is not None and relevant["mean_kendall_tau"] < 1.0)
        or any(delta != 0 for delta in relevant["count_deltas"].values())
    )
    assert inert["verdict"] == "inert in this scenario"
    assert inert["mean_topk_overlap"] == 1.0
    assert all(delta == 0 for delta in inert["count_deltas"].values())


def test_config_overrides_apply_in_memory_only(sim_vault: Path) -> None:
    config = LearnLoopConfig()
    updated = apply_config_overrides(
        config,
        {
            "scheduler.goal_frontier_weight": 0.9,
            "misconceptions.auto_resolve_clean_attempts": 5,
            "evidence.attempt_types.independent_attempt.evidence_mass": 0.6,
        },
    )
    assert updated.scheduler.goal_frontier_weight == 0.9
    assert updated.misconceptions.auto_resolve_clean_attempts == 5
    assert updated.evidence.attempt_types["independent_attempt"].evidence_mass == 0.6
    # Original untouched; bad paths fail loudly.
    assert config.scheduler.goal_frontier_weight != 0.9
    with pytest.raises(SimulationError):
        apply_config_overrides(config, {"scheduler.no_such_knob": 1.0})
    # The source vault's TOML is never edited by a simulation run.
    toml_before = (sim_vault / "learnloop.toml").read_text(encoding="utf-8")
    assert "goal_frontier_weight = 0.9" not in toml_before


def test_builtin_profiles_and_student_model() -> None:
    for name in ("novice", "intermediate_with_misconception", "strong_forgetter", "overconfident"):
        profile = load_profile(name)
        assert profile.name == name
    forgetter = load_profile("strong_forgetter")
    student = SyntheticStudent(forgetter, seed=1)
    m0 = student.mastery_at("recall", 0.0)
    m_later = student.mastery_at("recall", 20.0)
    assert m_later < m0  # forgetting decays mastery
    student.learn({"recall": 1.0}, 20.0)
    assert student.mastery_at("recall", 20.0) > m_later  # practice restores it
