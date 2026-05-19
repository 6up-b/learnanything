from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from learnloop.clock import FrozenClock
from learnloop.db.repositories import MasteryState, Repository
from learnloop.vault.loader import add_subject, init_vault, load_vault
from learnloop.vault.paths import VaultPaths
from learnloop.vault.yaml_io import write_yaml


NOW = datetime(2026, 5, 19, 12, 0, tzinfo=UTC)
NOW_ISO = "2026-05-19T12:00:00Z"


def seed_due_item(paths: VaultPaths) -> Repository:
    """Seed mastery + a past-due Practice Item so the basic vault item schedules."""
    repository = Repository(paths.sqlite_path)
    repository.upsert_mastery_state(
        MasteryState(
            learning_object_id="lo_svd_definition",
            logit_mean=0.0,
            logit_variance=1.0,
            evidence_count=1,
            last_evidence_at="2026-05-18T12:00:00Z",
            algorithm_version="mvp-0.1",
            updated_at=NOW_ISO,
        )
    )
    repository.upsert_practice_item_state(
        "pi_svd_define_001",
        difficulty=5.0,
        stability=2.0,
        due_at="2026-05-18T12:00:00Z",
        last_attempt_at="2026-05-16T12:00:00Z",
        active=True,
    )
    return repository


def create_basic_vault(root: Path) -> VaultPaths:
    clock = FrozenClock(NOW)
    init_vault(root, clock=clock)
    add_subject(root, "linear-algebra", "Linear Algebra", clock=clock)
    vault = load_vault(root)
    paths = VaultPaths(vault.root, vault.config)

    write_yaml(
        paths.concepts_path,
        {
            "schema_version": 1,
            "concepts": {
                "singular_value_decomposition": {
                    "title": "Singular Value Decomposition",
                    "type": "procedure",
                    "aliases": ["SVD"],
                    "description": "Matrix factorization.",
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
            "schema_version": 1,
            "goals": [
                {
                    "id": "goal_linear_algebra_ml",
                    "title": "Linear algebra for ML",
                    "status": "active",
                    "priority": 0.8,
                    "concept_anchors": ["singular_value_decomposition"],
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
                    "id": "conceptual_slip",
                    "title": "Conceptual slip",
                    "description": "The answer confuses the core definition.",
                    "related_concepts": ["singular_value_decomposition"],
                    "severity_default": 0.7,
                    "is_misconception": True,
                    "tags": [],
                    "created_at": NOW_ISO,
                    "updated_at": NOW_ISO,
                }
            ],
        },
    )
    write_yaml(
        paths.learning_object_path("linear-algebra", "lo_svd_definition"),
        {
            "schema_version": 1,
            "id": "lo_svd_definition",
            "title": "SVD definition",
            "subjects": ["linear-algebra"],
            "concept": "singular_value_decomposition",
            "knowledge_type": "definition",
            "status": "active",
            "contradicts": None,
            "summary": "SVD factorizes a matrix into orthogonal factors and singular values.",
            "prerequisites": [],
            "confusables": [],
            "difficulty_prior": 0.55,
            "tags": [],
            "provenance": {"origin": "human", "source_refs": []},
            "created_at": NOW_ISO,
            "updated_at": NOW_ISO,
        },
    )
    write_yaml(
        paths.practice_item_path("linear-algebra", "pi_svd_define_001"),
        {
            "schema_version": 1,
            "id": "pi_svd_define_001",
            "learning_object_id": "lo_svd_definition",
            "subjects": None,
            "practice_mode": "short_answer",
            "attempt_types_allowed": ["independent_attempt", "hinted_attempt", "dont_know"],
            "evidence_facets": ["recall"],
            "evidence_weights": {"recall": 1.0},
            "prompt": "Define SVD.",
            "expected_answer": "A matrix factorization into U, Sigma, and V transpose.",
            "difficulty": 0.55,
            "tags": [],
            "hints": ["Name the three factors."],
            "hint_policy": {
                "max_useful_hints": 1,
                "fsrs_rating_cap_by_hint": {"1": "good"},
                "mastery_alpha_dampening_by_hint": {"1": 0.5},
            },
            "grading_rubric": {
                "max_points": 4,
                "criteria": [{"id": "correctness", "points": 4, "description": "Correct definition."}],
                "fatal_errors": [
                    {
                        "id": "conceptual_slip",
                        "description": "Confuses SVD with a different decomposition.",
                        "max_grade": 1,
                    }
                ],
            },
            "provenance": {"origin": "human", "source_refs": []},
            "created_at": NOW_ISO,
            "updated_at": NOW_ISO,
        },
    )
    return paths
