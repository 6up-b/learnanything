from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from learnloop.clock import FrozenClock
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
from learnloop.vault.loader import add_subject, init_vault, load_vault
from learnloop.vault.paths import VaultPaths
from learnloop.vault.yaml_io import write_yaml

NOW = datetime(2026, 5, 19, 12, 0, tzinfo=UTC)
NOW_ISO = "2026-05-19T12:00:00Z"

PLANTED_ERROR = "sign_error"
PLANTED_FACET = "sign_convention"


def _item(
    item_id: str,
    lo_id: str,
    *,
    facets: dict[str, float],
    criterion_facet_weights: dict[str, dict[str, float]] | None = None,
    criteria: list[dict] | None = None,
) -> dict:
    return {
        "schema_version": 1,
        "id": item_id,
        "learning_object_id": lo_id,
        "subjects": None,
        "practice_mode": "short_answer",
        "attempt_types_allowed": ["independent_attempt", "dont_know"],
        "evidence_facets": sorted(facets),
        "evidence_weights": facets,
        "criterion_facet_weights": criterion_facet_weights or {},
        "prompt": f"Prompt for {item_id}.",
        "expected_answer": f"Expected answer for {item_id}.",
        "difficulty": 0.5,
        "tags": [],
        "hints": ["A hint."],
        "grading_rubric": {
            "max_points": 4,
            "criteria": criteria
            or [{"id": "correctness", "points": 4, "description": "Fully correct."}],
            "fatal_errors": [],
        },
        "provenance": {"origin": "human", "source_refs": []},
        "created_at": NOW_ISO,
        "updated_at": NOW_ISO,
    }


def build_sim_vault(root: Path) -> Path:
    """Small 3-LO / 6-item vault; ``sign_convention`` is testable on 4 items."""

    clock = FrozenClock(NOW)
    init_vault(root, clock=clock)
    # P0.5 cutover: `learnloop init` now defaults new vaults to mvp-0.8, whose
    # robust-composition certainty is recomputed fresh (seeded partly from
    # per-run administration ids) and so is not reproducible across two FRESH sim
    # runs -- production pins a decision-time snapshot instead. This sim
    # characterizes the mvp-0.7 scheduler/learner baseline; pin it there so its
    # seed-determinism and in-band metric contracts hold.
    import re as _re

    _cfg = root / "learnloop.toml"
    _cfg.write_text(
        _re.sub(r'algorithm_version = "[^"]+"', 'algorithm_version = "mvp-0.7"',
                _cfg.read_text(encoding="utf-8"), count=1),
        encoding="utf-8",
    )
    add_subject(root, "algebra", "Algebra", clock=clock)
    vault = load_vault(root)
    paths = VaultPaths(vault.root, vault.config)

    write_yaml(
        paths.concepts_path,
        {
            "schema_version": 1,
            "concepts": {
                "linear_equations": {
                    "title": "Linear equations",
                    "type": "procedure",
                    "aliases": [],
                    "description": "Solving linear equations.",
                    "tags": [],
                    "created_at": NOW_ISO,
                    "updated_at": NOW_ISO,
                }
            },
        },
    )
    write_yaml(
        paths.goals_path,
        {
            "schema_version": 2,
            "goals": [
                {
                    "id": "goal_algebra",
                    "title": "Algebra fluency",
                    "status": "active",
                    "priority": 0.8,
                    "target_recall": 0.8,
                    "facet_scope": {"concepts": ["linear_equations"]},
                    "due_at": None,
                    "created_at": NOW_ISO,
                    "updated_at": NOW_ISO,
                }
            ],
        },
    )
    write_yaml(
        paths.error_types_path,
        {
            "schema_version": 1,
            "error_types": [
                {
                    "id": PLANTED_ERROR,
                    "title": "Sign error",
                    "description": "Flips the sign when moving terms across the equals sign.",
                    "related_concepts": ["linear_equations"],
                    "severity_default": 0.7,
                    "is_misconception": True,
                    "tags": [],
                    "created_at": NOW_ISO,
                    "updated_at": NOW_ISO,
                },
                {
                    "id": "recall_failure",
                    "title": "Recall failure",
                    "description": "Could not recall the needed fact.",
                    "related_concepts": [],
                    "severity_default": 0.5,
                    "is_misconception": False,
                    "tags": [],
                    "created_at": NOW_ISO,
                    "updated_at": NOW_ISO,
                },
            ],
        },
    )
    for lo_id, title in (
        ("lo_isolate_variable", "Isolate a variable"),
        ("lo_move_terms", "Move terms across equality"),
        ("lo_check_solution", "Check a solution"),
    ):
        write_yaml(
            paths.learning_object_path("algebra", lo_id),
            {
                "schema_version": 1,
                "id": lo_id,
                "title": title,
                "subjects": ["algebra"],
                "concept": "linear_equations",
                "knowledge_type": "procedure",
                "status": "active",
                "contradicts": None,
                "summary": f"{title}.",
                "prerequisites": [],
                "confusables": [],
                "difficulty_prior": 0.5,
                "tags": [],
                "provenance": {"origin": "human", "source_refs": []},
                "created_at": NOW_ISO,
                "updated_at": NOW_ISO,
            },
        )

    two_part_criteria = [
        {"id": "setup", "points": 2, "description": "Sets up the manipulation."},
        {"id": "signs", "points": 2, "description": "Signs handled correctly."},
    ]
    two_part_weights = {
        "setup": {"recall": 1.0},
        "signs": {PLANTED_FACET: 1.0},
    }
    items = [
        _item("pi_isolate_recall", "lo_isolate_variable", facets={"recall": 1.0}),
        _item(
            "pi_isolate_signs",
            "lo_isolate_variable",
            facets={"recall": 0.5, PLANTED_FACET: 0.5},
            criterion_facet_weights=two_part_weights,
            criteria=two_part_criteria,
        ),
        _item(
            "pi_move_signs_a",
            "lo_move_terms",
            facets={"recall": 0.4, PLANTED_FACET: 0.6},
            criterion_facet_weights=two_part_weights,
            criteria=two_part_criteria,
        ),
        _item(
            "pi_move_signs_b",
            "lo_move_terms",
            facets={"recall": 0.4, PLANTED_FACET: 0.6},
            criterion_facet_weights=two_part_weights,
            criteria=two_part_criteria,
        ),
        _item("pi_check_recall", "lo_check_solution", facets={"recall": 1.0}),
        _item(
            "pi_check_signs",
            "lo_check_solution",
            facets={"recall": 0.5, PLANTED_FACET: 0.5},
            criterion_facet_weights=two_part_weights,
            criteria=two_part_criteria,
        ),
    ]
    for item in items:
        write_yaml(paths.practice_item_path("algebra", item["id"]), item)
    return root


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
