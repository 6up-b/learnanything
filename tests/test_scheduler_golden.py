from __future__ import annotations

from datetime import UTC, datetime, timedelta
from math import exp

import pytest

from learnloop.clock import FrozenClock
from learnloop.db.repositories import MasteryState, Repository
from learnloop.services.scheduler import build_due_queue
from learnloop.vault.loader import load_vault
from learnloop.vault.writer import upsert_concept, upsert_concept_edge, upsert_learning_object, upsert_practice_item
from learnloop.vault.yaml_io import write_yaml

from tests.helpers import NOW, NOW_ISO, create_basic_vault


def test_scheduler_forgetting_risk_zero_before_due_date(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    write_yaml(paths.goals_path, {"schema_version": 1, "goals": []})
    loaded = load_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    repository.upsert_mastery_state(_mastery("lo_svd_definition"))
    repository.upsert_practice_item_state(
        "pi_svd_define_001",
        difficulty=5.0,
        stability=2.0,
        due_at="2026-05-20T12:00:00Z",
        last_attempt_at="2026-05-18T12:00:00Z",
        active=True,
        clock=FrozenClock(NOW),
    )

    queue = build_due_queue(loaded, repository, clock=FrozenClock(NOW), persist_explanations=False)

    assert queue == []


def test_scheduler_ties_by_lowest_practice_item_id_and_filters_inactive(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    _add_practice_item(vault_root, "pi_svd_define_000")
    loaded = load_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    repository.upsert_mastery_state(_mastery("lo_svd_definition"))
    for item_id in ["pi_svd_define_000", "pi_svd_define_001"]:
        repository.upsert_practice_item_state(
            item_id,
            difficulty=5.0,
            stability=2.0,
            due_at="2026-05-18T12:00:00Z",
            last_attempt_at="2026-05-16T12:00:00Z",
            active=True,
            clock=FrozenClock(NOW),
        )

    queue = build_due_queue(loaded, repository, clock=FrozenClock(NOW), persist_explanations=False)

    assert [item.practice_item_id for item in queue] == ["pi_svd_define_000", "pi_svd_define_001"]

    repository.upsert_practice_item_state(
        "pi_svd_define_000",
        difficulty=5.0,
        stability=2.0,
        due_at="2026-05-18T12:00:00Z",
        last_attempt_at="2026-05-16T12:00:00Z",
        active=False,
        clock=FrozenClock(NOW),
    )
    queue = build_due_queue(loaded, repository, clock=FrozenClock(NOW), persist_explanations=False)

    assert [item.practice_item_id for item in queue] == ["pi_svd_define_001"]


def test_scheduler_active_goal_follows_allowed_edges_only(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    _add_related_concept_lo_and_item(vault_root, relation_type="related")
    loaded = load_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    repository.upsert_mastery_state(_mastery("lo_related"))
    repository.upsert_practice_item_state("pi_related_001", active=True, clock=FrozenClock(NOW))

    queue = build_due_queue(loaded, repository, clock=FrozenClock(NOW), persist_explanations=False)

    assert "pi_related_001" not in [item.practice_item_id for item in queue]

    upsert_concept_edge(
        vault_root,
        {
            "id": "edge_goal_related",
            "relation_type": "prerequisite",
            "source": "singular_value_decomposition",
            "target": "related_concept",
            "strength": 1.0,
        },
        clock=FrozenClock(NOW),
    )
    loaded = load_vault(vault_root)
    queue = build_due_queue(loaded, repository, clock=FrozenClock(NOW), persist_explanations=False)
    related = [item for item in queue if item.practice_item_id == "pi_related_001"][0]

    assert related.components["active_goal"] == 0.8


def test_scheduler_recent_error_decays_by_exp_days_over_seven(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    write_yaml(paths.goals_path, {"schema_version": 1, "goals": []})
    loaded = load_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    repository.upsert_mastery_state(_mastery("lo_svd_definition"))
    repository.upsert_practice_item_state(
        "pi_svd_define_001",
        due_at="2026-05-20T12:00:00Z",
        active=True,
        clock=FrozenClock(NOW),
    )
    repository.insert_error_event(
        {
            "id": "err_recent",
            "learning_object_id": "lo_svd_definition",
            "error_type": "conceptual_slip",
            "severity": 0.7,
            "is_misconception": True,
            "status": "active",
            "created_at": (NOW - timedelta(days=7)).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            "updated_at": NOW_ISO,
        }
    )

    queue = build_due_queue(loaded, repository, clock=FrozenClock(NOW), persist_explanations=False)

    assert len(queue) == 1
    assert queue[0].components["recent_error"] == pytest.approx(0.7 * exp(-1))


def _mastery(learning_object_id: str) -> MasteryState:
    return MasteryState(
        learning_object_id=learning_object_id,
        logit_mean=0.0,
        logit_variance=1.0,
        evidence_count=1,
        last_evidence_at="2026-05-18T12:00:00Z",
        algorithm_version="mvp-0.1",
        updated_at=NOW_ISO,
    )


def _add_practice_item(vault_root, item_id: str) -> None:
    upsert_practice_item(
        vault_root,
        {
            "id": item_id,
            "learning_object_id": "lo_svd_definition",
            "subjects": None,
            "practice_mode": "short_answer",
            "attempt_types_allowed": ["independent_attempt"],
            "evidence_facets": ["recall"],
            "evidence_weights": {"recall": 1.0},
            "prompt": f"Define SVD for {item_id}.",
            "expected_answer": "A matrix factorization into U, Sigma, and V transpose.",
            "grading_rubric": {
                "max_points": 4,
                "criteria": [{"id": "correctness", "points": 4, "description": "Correct definition."}],
                "fatal_errors": [],
            },
        },
        clock=FrozenClock(NOW),
    )


def _add_related_concept_lo_and_item(vault_root, *, relation_type: str) -> None:
    upsert_concept(vault_root, "related_concept", {"title": "Related concept", "type": "concept"}, clock=FrozenClock(NOW))
    upsert_concept_edge(
        vault_root,
        {
            "id": "edge_goal_related",
            "relation_type": relation_type,
            "source": "singular_value_decomposition",
            "target": "related_concept",
            "strength": 1.0,
        },
        clock=FrozenClock(NOW),
    )
    upsert_learning_object(
        vault_root,
        {
            "id": "lo_related",
            "title": "Related LO",
            "subjects": ["linear-algebra"],
            "concept": "related_concept",
            "knowledge_type": "fact",
            "summary": "A related concept.",
        },
        clock=FrozenClock(NOW),
    )
    upsert_practice_item(
        vault_root,
        {
            "id": "pi_related_001",
            "learning_object_id": "lo_related",
            "subjects": None,
            "practice_mode": "short_answer",
            "attempt_types_allowed": ["independent_attempt"],
            "evidence_facets": ["recall"],
            "evidence_weights": {"recall": 1.0},
            "prompt": "Explain the related concept.",
            "expected_answer": "A related concept.",
            "grading_rubric": {
                "max_points": 4,
                "criteria": [{"id": "correctness", "points": 4, "description": "Correct answer."}],
                "fatal_errors": [],
            },
        },
        clock=FrozenClock(NOW),
    )
