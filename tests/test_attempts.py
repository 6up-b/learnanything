from __future__ import annotations

import pytest

from datetime import timedelta

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.services.attempts import AttemptDraft, AttemptValidationError, SelfGradeInput, complete_self_graded_attempt
from learnloop.services.scheduler import SchedulerSession, build_due_queue
from learnloop.services.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault

from tests.helpers import NOW, create_basic_vault


def test_self_graded_attempt_updates_attempt_evidence_state_and_surprise(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    vault = load_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    clock = FrozenClock(NOW)
    sync_vault_state(vault, repository, clock=clock)

    result = complete_self_graded_attempt(
        vault,
        repository,
        AttemptDraft(
            practice_item_id="pi_svd_define_001",
            learner_answer_md="SVD is U Sigma V^T.",
            attempt_type="independent_attempt",
        ),
        SelfGradeInput(
            criterion_points={"correctness": 2},
            fatal_errors=["conceptual_slip"],
            confidence=4,
        ),
        clock=clock,
    )

    attempt = repository.fetch_practice_attempt(result.attempt_id)
    evidence = repository.fetch_grading_evidence(result.attempt_id)
    item_state = repository.practice_item_state("pi_svd_define_001")
    mastery = repository.mastery_state("lo_svd_definition")
    errors = repository.active_errors_by_learning_object("lo_svd_definition")
    surprise = repository.latest_attempt_surprise(result.attempt_id)

    assert attempt["rubric_score"] == 1
    assert attempt["grader_confidence"] == 0.8
    assert [row.criterion_id for row in evidence] == ["correctness"]
    assert evidence[0].points_awarded == 2
    assert item_state.difficulty is not None
    assert item_state.stability is not None
    assert item_state.due_at == result.due_at
    assert mastery.evidence_count == 1
    assert errors[0].error_type == "conceptual_slip"
    assert errors[0].severity >= 0.7
    assert surprise["observed_joint_bucket"] == {"score_bucket": "low", "error_type": "conceptual_slip"}
    assert surprise["surprise_direction"] == "negative"


def test_hinted_attempt_caps_fsrs_rating(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    vault = load_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    clock = FrozenClock(NOW)
    sync_vault_state(vault, repository, clock=clock)

    result = complete_self_graded_attempt(
        vault,
        repository,
        AttemptDraft(
            practice_item_id="pi_svd_define_001",
            learner_answer_md="SVD is U Sigma V^T.",
            attempt_type="hinted_attempt",
            hints_used=1,
        ),
        SelfGradeInput(
            criterion_points={"correctness": 4},
            confidence=5,
        ),
        clock=clock,
    )

    assert result.fsrs_rating == "good"


def test_unknown_attempt_type_fails_before_sqlite_insert(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    vault = load_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    sync_vault_state(vault, repository, clock=FrozenClock(NOW))

    with pytest.raises(AttemptValidationError, match="Unsupported attempt_type"):
        complete_self_graded_attempt(
            vault,
            repository,
            AttemptDraft(
                practice_item_id="pi_svd_define_001",
                learner_answer_md="SVD is U Sigma V^T.",
                attempt_type="freeform_answer",
            ),
            SelfGradeInput(criterion_points={"correctness": 4}, confidence=5),
            clock=FrozenClock(NOW),
        )


def test_attempt_links_to_scheduler_slate_and_later_retention_label(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    vault = load_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    clock = FrozenClock(NOW)
    sync_vault_state(vault, repository, clock=clock)

    queue = build_due_queue(
        vault,
        repository,
        clock=clock,
        session=SchedulerSession(session_id="session_training"),
        limit=1,
    )
    assert queue[0].practice_item_id == "pi_svd_define_001"

    first = complete_self_graded_attempt(
        vault,
        repository,
        AttemptDraft(
            practice_item_id="pi_svd_define_001",
            learner_answer_md="SVD is U Sigma V^T.",
            attempt_type="independent_attempt",
            session_id="session_training",
        ),
        SelfGradeInput(criterion_points={"correctness": 4}, confidence=5),
        clock=clock,
    )

    attempt = repository.fetch_practice_attempt(first.attempt_id)
    slate = repository.latest_scheduler_slate_by_session("session_training")
    candidates = repository.scheduler_slate_candidates(slate["id"])
    assert attempt["session_id"] == "session_training"
    assert attempt["scheduler_slate_id"] == slate["id"]
    assert attempt["scheduler_candidate_id"] == candidates[0]["id"]
    assert candidates[0]["chosen_attempt_id"] == first.attempt_id

    second = complete_self_graded_attempt(
        vault,
        repository,
        AttemptDraft(
            practice_item_id="pi_svd_define_001",
            learner_answer_md="SVD is U Sigma V^T.",
            attempt_type="independent_attempt",
        ),
        SelfGradeInput(criterion_points={"correctness": 3}, confidence=4),
        clock=FrozenClock(NOW + timedelta(days=3)),
    )

    labels = repository.learning_outcome_labels_for_source(first.attempt_id)
    assert [label["outcome_attempt_id"] for label in labels] == [second.attempt_id]
    assert labels[0]["label_type"] == "same_item_retention"
    assert labels[0]["label_value"] == 0.75
    assert labels[0]["elapsed_seconds"] == 3 * 24 * 60 * 60
    assert labels[0]["metadata"]["source"]["scheduler_slate_id"] == slate["id"]
