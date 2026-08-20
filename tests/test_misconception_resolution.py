from __future__ import annotations

from datetime import timedelta

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.attempts.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
from learnloop.substrate.replay import replay_learning_object
from learnloop.substrate.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault

from tests.helpers import NOW, create_basic_vault

LO_ID = "lo_svd_definition"
ITEM_ID = "pi_svd_define_001"


def _setup(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    vault = load_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    sync_vault_state(vault, repository, clock=FrozenClock(NOW))
    return vault, repository


def _misconception_attempt(vault, repository, *, minutes: int = 0):
    return complete_self_graded_attempt(
        vault,
        repository,
        AttemptDraft(
            practice_item_id=ITEM_ID,
            learner_answer_md="SVD is eigendecomposition.",
            attempt_type="independent_attempt",
        ),
        SelfGradeInput(criterion_points={"correctness": 2}, fatal_errors=["conceptual_slip"], confidence=4),
        clock=FrozenClock(NOW + timedelta(minutes=minutes)),
    )


def _clean_attempt(vault, repository, *, minutes: int):
    return complete_self_graded_attempt(
        vault,
        repository,
        AttemptDraft(
            practice_item_id=ITEM_ID,
            learner_answer_md="SVD factorizes into U Sigma V^T.",
            attempt_type="independent_attempt",
        ),
        SelfGradeInput(criterion_points={"correctness": 4}, confidence=5),
        clock=FrozenClock(NOW + timedelta(minutes=minutes)),
    )


def _dont_know_attempt(vault, repository, *, minutes: int):
    return complete_self_graded_attempt(
        vault,
        repository,
        AttemptDraft(
            practice_item_id=ITEM_ID,
            learner_answer_md="",
            attempt_type="dont_know",
        ),
        SelfGradeInput(criterion_points={}, confidence=1),
        clock=FrozenClock(NOW + timedelta(minutes=minutes)),
    )


def _event_statuses(repository, attempt_id):
    return {event["id"]: event["status"] for event in repository.error_events_for_attempt(attempt_id)}


def test_error_event_resolves_after_n_clean_attempts_but_not_early(tmp_path):
    vault, repository = _setup(tmp_path)
    first = _misconception_attempt(vault, repository)
    event_id = first.error_event_ids[0]

    _clean_attempt(vault, repository, minutes=1)
    _clean_attempt(vault, repository, minutes=2)

    # Two clean attempts < auto_resolve_clean_attempts (3): must stay active.
    assert _event_statuses(repository, first.attempt_id)[event_id] == "active"
    assert [error.id for error in repository.active_errors_by_learning_object(LO_ID)] == [event_id]

    _clean_attempt(vault, repository, minutes=3)

    assert _event_statuses(repository, first.attempt_id)[event_id] == "resolved"
    assert repository.active_errors_by_learning_object(LO_ID) == []


def test_dont_know_attempts_do_not_count_as_clean(tmp_path):
    vault, repository = _setup(tmp_path)
    first = _misconception_attempt(vault, repository)
    event_id = first.error_event_ids[0]

    _clean_attempt(vault, repository, minutes=1)
    _clean_attempt(vault, repository, minutes=2)
    _dont_know_attempt(vault, repository, minutes=3)

    # Three attempts since the event, but the dont_know is not clean.
    assert _event_statuses(repository, first.attempt_id)[event_id] == "active"


def test_low_correctness_attempt_does_not_count_as_clean(tmp_path):
    vault, repository = _setup(tmp_path)
    first = _misconception_attempt(vault, repository)
    event_id = first.error_event_ids[0]

    _clean_attempt(vault, repository, minutes=1)
    _clean_attempt(vault, repository, minutes=2)
    # 3/4 = 0.75 < auto_resolve_min_correctness (0.85), and it is also the
    # triggering attempt, which must not fire resolution while below threshold.
    complete_self_graded_attempt(
        vault,
        repository,
        AttemptDraft(
            practice_item_id=ITEM_ID,
            learner_answer_md="SVD factorizes a matrix.",
            attempt_type="independent_attempt",
        ),
        SelfGradeInput(criterion_points={"correctness": 3}, confidence=3),
        clock=FrozenClock(NOW + timedelta(minutes=3)),
    )

    assert _event_statuses(repository, first.attempt_id)[event_id] == "active"


def test_replay_reproduces_auto_resolution(tmp_path):
    vault, repository = _setup(tmp_path)
    first = _misconception_attempt(vault, repository)
    event_id = first.error_event_ids[0]
    for minutes in (1, 2, 3):
        _clean_attempt(vault, repository, minutes=minutes)
    assert _event_statuses(repository, first.attempt_id)[event_id] == "resolved"

    replay_learning_object(vault, repository, LO_ID)

    # Replay resets error events to active and re-applies attempts in order;
    # the resolution rule must re-fire deterministically.
    assert _event_statuses(repository, first.attempt_id)[event_id] == "resolved"
    assert repository.active_errors_by_learning_object(LO_ID) == []


def test_count_clean_attempts_since_bounds_and_criteria(tmp_path):
    vault, repository = _setup(tmp_path)
    first = _misconception_attempt(vault, repository)
    _clean_attempt(vault, repository, minutes=1)
    _dont_know_attempt(vault, repository, minutes=2)
    _clean_attempt(vault, repository, minutes=3)

    event = repository.error_events_for_attempt(first.attempt_id)[0]
    until = "2026-05-19T12:03:00Z"
    assert (
        repository.count_clean_attempts_since(
            LO_ID, since=event["created_at"], until=until, min_correctness=0.85
        )
        == 2
    )
    # Upper bound excludes attempts after `until` (replay reproducibility).
    assert (
        repository.count_clean_attempts_since(
            LO_ID, since=event["created_at"], until="2026-05-19T12:01:00Z", min_correctness=0.85
        )
        == 1
    )
    # The event-creating attempt itself is excluded by the strict lower bound
    # and by its non-null error_type.
    assert (
        repository.count_clean_attempts_since(
            LO_ID, since="2026-05-19T11:00:00Z", until="2026-05-19T12:00:00Z", min_correctness=0.85
        )
        == 0
    )
