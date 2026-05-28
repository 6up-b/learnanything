from __future__ import annotations

import pytest

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.services.mastery import logit
from learnloop.services.scheduler import build_due_queue
from learnloop.services.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault
from learnloop.vault.writer import upsert_learning_object, upsert_practice_item
from learnloop.vault.yaml_io import write_yaml

from tests.helpers import NOW, create_basic_vault


def test_state_sync_initializes_and_deactivates_missing_yaml(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    clock = FrozenClock(NOW)

    result = sync_vault_state(load_vault(vault_root), repository, clock=clock)

    assert result.practice_item_states_created == 1
    assert result.mastery_states_created == 1
    assert repository.practice_item_state("pi_svd_define_001").active is True
    assert repository.mastery_state("lo_svd_definition").evidence_count == 0

    second = sync_vault_state(load_vault(vault_root), repository, clock=clock)

    assert second.as_dict() == {
        "practice_item_states_created": 0,
        "practice_item_states_updated": 0,
        "practice_item_states_deactivated": 0,
        "mastery_states_created": 0,
    }

    paths.practice_item_path("linear-algebra", "pi_svd_define_001").unlink()
    deactivated = sync_vault_state(load_vault(vault_root), repository, clock=clock)

    assert deactivated.practice_item_states_deactivated == 1
    assert repository.practice_item_state("pi_svd_define_001").active is False


def test_state_sync_enters_probe_for_new_active_goal_learning_object(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    clock = FrozenClock(NOW)

    sync_vault_state(load_vault(vault_root), repository, clock=clock)

    probe_state = repository.probe_state("lo_svd_definition")
    queue = build_due_queue(load_vault(vault_root), repository, clock=clock, persist_explanations=False)

    assert probe_state is not None
    assert probe_state.status == "in_progress"
    assert "pi_svd_define_001" in [item.practice_item_id for item in queue]


def test_state_sync_enters_probe_for_new_active_learning_object_without_goal(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    write_yaml(paths.goals_path, {"schema_version": 1, "goals": []})
    repository = Repository(paths.sqlite_path)
    clock = FrozenClock(NOW)

    sync_vault_state(load_vault(vault_root), repository, clock=clock)

    probe_state = repository.probe_state("lo_svd_definition")
    queue = build_due_queue(load_vault(vault_root), repository, clock=clock, persist_explanations=False)

    assert probe_state is not None
    assert probe_state.status == "in_progress"
    assert [item.practice_item_id for item in queue] == ["pi_svd_define_001"]
    assert queue[0].components["probe_eig"] > 0.0


def test_state_sync_enters_probe_when_practice_item_arrives_after_learning_object(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    paths.practice_item_path("linear-algebra", "pi_svd_define_001").unlink()
    write_yaml(paths.goals_path, {"schema_version": 1, "goals": []})
    repository = Repository(paths.sqlite_path)
    clock = FrozenClock(NOW)

    sync_vault_state(load_vault(vault_root), repository, clock=clock)
    assert repository.probe_state("lo_svd_definition") is None

    upsert_practice_item(
        vault_root,
        {
            "id": "pi_svd_define_001",
            "learning_object_id": "lo_svd_definition",
            "practice_mode": "short_answer",
            "attempt_types_allowed": ["independent_attempt"],
            "evidence_facets": ["recall"],
            "evidence_weights": {"recall": 1.0},
            "prompt": "Define SVD.",
            "expected_answer": "A matrix factorization into U, Sigma, and V transpose.",
            "difficulty": 0.55,
            "grading_rubric": {
                "max_points": 4,
                "criteria": [{"id": "correctness", "points": 4, "description": "Correct definition."}],
                "fatal_errors": [],
            },
        },
        clock=clock,
    )

    sync_vault_state(load_vault(vault_root), repository, clock=clock)
    queue = build_due_queue(load_vault(vault_root), repository, clock=clock, persist_explanations=False)

    assert repository.probe_state("lo_svd_definition").status == "in_progress"
    assert [item.practice_item_id for item in queue] == ["pi_svd_define_001"]


def test_state_sync_uses_strong_learner_claim_for_initial_mastery(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    repository.insert_learner_claim(
        {
            "id": "claim_svd_known",
            "claim_type": "self_rating",
            "scope_type": "learning_object",
            "scope_id": "lo_svd_definition",
            "evidence_family": "recall",
            "claimed_level": 0.9,
            "prior_pseudo_count": 4.0,
            "source": "manual_cli",
        },
        clock=FrozenClock(NOW),
    )

    sync_vault_state(load_vault(vault_root), repository, clock=FrozenClock(NOW))

    mastery = repository.mastery_state("lo_svd_definition")
    assert mastery.logit_mean == pytest.approx(logit(0.9))
    assert mastery.logit_variance == pytest.approx(0.25)
    assert mastery.evidence_count == 0
    assert mastery.last_evidence_at is None
    assert repository.probe_state("lo_svd_definition").probe_attempts_target == 1


def test_state_sync_ignores_weak_learner_claim_for_initial_mastery(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    repository.insert_learner_claim(
        {
            "id": "claim_svd_weak",
            "claim_type": "self_rating",
            "scope_type": "learning_object",
            "scope_id": "lo_svd_definition",
            "evidence_family": "recall",
            "claimed_level": 0.7,
            "prior_pseudo_count": 4.0,
            "source": "manual_cli",
        },
        clock=FrozenClock(NOW),
    )

    sync_vault_state(load_vault(vault_root), repository, clock=FrozenClock(NOW))

    mastery = repository.mastery_state("lo_svd_definition")
    assert mastery.logit_mean == 0.0
    assert mastery.logit_variance == 1.0


def test_state_sync_logs_probe_gap_when_active_goal_lo_has_no_items(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    paths.practice_item_path("linear-algebra", "pi_svd_define_001").unlink()
    upsert_learning_object(
        vault_root,
        {
            "id": "lo_svd_gap",
            "title": "SVD gap",
            "subjects": ["linear-algebra"],
            "concept": "singular_value_decomposition",
            "knowledge_type": "definition",
            "summary": "No Practice Item exists yet.",
        },
        clock=FrozenClock(NOW),
    )
    repository = Repository(paths.sqlite_path)

    sync_vault_state(load_vault(vault_root), repository, clock=FrozenClock(NOW))

    events = repository.elicitation_events()
    assert any(event["trigger"] == "probe_phase_local_pi_inadequate" for event in events)
