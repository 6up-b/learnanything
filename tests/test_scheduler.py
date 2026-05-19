from __future__ import annotations

from datetime import UTC, datetime

from learnloop.clock import FrozenClock
from learnloop.db.repositories import MasteryState, Repository
from learnloop.services.scheduler import build_due_queue
from learnloop.vault.loader import add_subject, init_vault, load_vault
from learnloop.vault.paths import VaultPaths
from learnloop.vault.yaml_io import write_yaml


NOW = datetime(2026, 5, 19, 12, 0, tzinfo=UTC)
NOW_ISO = "2026-05-19T12:00:00Z"


def test_scheduler_scores_due_goal_item(tmp_path):
    vault_root = tmp_path / "vault"
    clock = FrozenClock(NOW)
    init_vault(vault_root, clock=clock)
    add_subject(vault_root, "linear-algebra", "Linear Algebra", clock=clock)
    vault = load_vault(vault_root)
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
            "attempt_types_allowed": ["independent_attempt"],
            "evidence_facets": ["recall"],
            "evidence_weights": {"recall": 1.0},
            "prompt": "Define SVD.",
            "expected_answer": "A matrix factorization.",
            "difficulty": 0.55,
            "tags": [],
            "hints": [],
            "hint_policy": {"max_useful_hints": 0, "fsrs_rating_cap_by_hint": {}, "mastery_alpha_dampening_by_hint": {}},
            "grading_rubric": {
                "max_points": 4,
                "criteria": [{"id": "correctness", "points": 4, "description": "Correct definition."}],
                "fatal_errors": [],
            },
            "provenance": {"origin": "human", "source_refs": []},
            "created_at": NOW_ISO,
            "updated_at": NOW_ISO,
        },
    )

    loaded = load_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    repository.upsert_practice_item_state(
        "pi_svd_define_001",
        difficulty=5.0,
        stability=2.0,
        due_at="2026-05-18T12:00:00Z",
        last_attempt_at="2026-05-16T12:00:00Z",
        active=True,
        clock=clock,
    )
    repository.upsert_mastery_state(
        MasteryState(
            learning_object_id="lo_svd_definition",
            logit_mean=0.0,
            logit_variance=1.0,
            evidence_count=1,
            last_evidence_at="2026-05-16T12:00:00Z",
            algorithm_version="mvp-0.1",
            updated_at=NOW_ISO,
        )
    )

    queue = build_due_queue(loaded, repository, clock=clock, persist_explanations=False)

    assert [item.practice_item_id for item in queue] == ["pi_svd_define_001"]
    assert queue[0].components["forgetting_risk"] > 0
    assert queue[0].components["active_goal"] == 0.8
