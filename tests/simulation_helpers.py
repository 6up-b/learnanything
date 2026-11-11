"""What other test files use from ``tests/test_simulation.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from learnloop.clock import FrozenClock
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
