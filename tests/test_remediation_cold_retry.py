"""B6 remediation episodes: FrozenClock cold-retry delay, consume-once,
unassisted+unprimed enforcement, and the prescription→primed→cold linkage
(spec §4.10 / §7.2)."""

from __future__ import annotations

from datetime import timedelta

import pytest

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.services.attempts import (
    AttemptDraft,
    AttemptValidationError,
    SelfGradeInput,
    complete_self_graded_attempt,
)
from learnloop.services.remediation import (
    prescribe_remediation,
    start_remediation_episode,
    start_remediation_treatment,
)
from learnloop.vault.loader import load_vault

from tests.helpers import NOW, add_followup_item, create_basic_vault, seed_due_item

LO_ID = "lo_svd_definition"


def _setup(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    seed_due_item(paths)
    add_followup_item(vault_root)  # a second item so primed and cold items differ
    vault = load_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    misconception_id = repository.insert_misconception(
        learning_object_id=LO_ID,
        statement="Confuses SVD with eigendecomposition.",
        correction_statement="SVD applies to any matrix; eigendecomposition needs a square one.",
        facet_ids=["recall"],
        target_facet="recall",
        confused_with_facet="application",
        severity=0.8,
        clock=FrozenClock(NOW),
    )
    return vault, repository, misconception_id


def _attempt(vault, repository, item_id, *, clock, primed=False, hints_used=0):
    return complete_self_graded_attempt(
        vault,
        repository,
        AttemptDraft(
            practice_item_id=item_id,
            learner_answer_md="U Sigma V transpose.",
            attempt_type="independent_attempt",
            hints_used=hints_used,
            primed=primed,
        ),
        SelfGradeInput(criterion_points={"correctness": 4}, fatal_errors=[], confidence=4),
        clock=clock,
    )


def _drive_to_cold_scheduled(vault, repository, misconception_id):
    """diagnosis → prescribed → treatment → primed attempt → cold_scheduled."""

    episode = start_remediation_episode(repository, misconception_id, clock=FrozenClock(NOW))
    assert episode["state"] == "diagnosis"
    prescribed = prescribe_remediation(vault, repository, episode["id"], clock=FrozenClock(NOW))
    assert prescribed["state"] == "prescribed"
    treatment = start_remediation_treatment(vault, repository, episode["id"], clock=FrozenClock(NOW))
    assert treatment["episode"]["state"] == "treatment"
    primed_item = treatment["primed_item_id"]
    cold_item = treatment["cold_item_id"]
    assert primed_item != cold_item

    primed_result = _attempt(vault, repository, primed_item, clock=FrozenClock(NOW), primed=True)
    episode = repository.remediation_episode(episode["id"])
    assert episode["state"] == "cold_scheduled"
    assert episode["primed_attempt_id"] == primed_result.attempt_id
    return episode, primed_result, cold_item


def test_cold_retry_is_not_schedulable_until_not_before(tmp_path):
    vault, repository, misconception_id = _setup(tmp_path)
    _, _, cold_item = _drive_to_cold_scheduled(vault, repository, misconception_id)

    task = repository.active_followup_task_for_item(
        cold_item, at=(NOW + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
    )
    assert task is not None and task["kind"] == "cold_retry"
    assert task["not_before"] == (NOW + timedelta(days=1)).isoformat().replace("+00:00", "Z")

    # Scheduled today, not schedulable today: the delayed structured task is
    # invisible to the scheduler until not_before (>= 1 day later).
    assert cold_item not in repository.pending_followup_practice_item_ids(clock=FrozenClock(NOW))
    assert cold_item not in repository.pending_followup_practice_item_ids(
        clock=FrozenClock(NOW + timedelta(hours=23))
    )
    assert cold_item in repository.pending_followup_practice_item_ids(
        clock=FrozenClock(NOW + timedelta(days=1))
    )


def test_served_cold_attempt_is_enforced_unassisted_and_unprimed(tmp_path):
    vault, repository, misconception_id = _setup(tmp_path)
    _, _, cold_item = _drive_to_cold_scheduled(vault, repository, misconception_id)
    due = FrozenClock(NOW + timedelta(days=1))

    with pytest.raises(AttemptValidationError):
        _attempt(vault, repository, cold_item, clock=due, primed=True)
    with pytest.raises(AttemptValidationError):
        _attempt(vault, repository, cold_item, clock=due, hints_used=1)

    # A clean unassisted, unprimed retry is accepted.
    result = _attempt(vault, repository, cold_item, clock=due)
    task = next(
        task for task in _all_tasks(repository) if task["kind"] == "cold_retry"
    )
    assert task["status"] == "consumed"
    assert task["consumed_attempt_id"] == result.attempt_id


def test_cold_retry_is_consumed_exactly_once(tmp_path):
    vault, repository, misconception_id = _setup(tmp_path)
    episode, _, cold_item = _drive_to_cold_scheduled(vault, repository, misconception_id)
    due = FrozenClock(NOW + timedelta(days=1))

    first = _attempt(vault, repository, cold_item, clock=due)
    task = next(task for task in _all_tasks(repository) if task["kind"] == "cold_retry")
    assert task["status"] == "consumed"
    assert task["consumed_attempt_id"] == first.attempt_id

    # A later attempt on the same item finds no active task and links nothing.
    second = _attempt(vault, repository, cold_item, clock=FrozenClock(NOW + timedelta(days=2)))
    refreshed = repository.followup_task(task["id"])
    assert refreshed["consumed_attempt_id"] == first.attempt_id
    assert refreshed["status"] == "consumed"

    # Even a direct second consume cannot re-bind the task.
    repository.consume_followup_task(task["id"], second.attempt_id, clock=due)
    assert repository.followup_task(task["id"])["consumed_attempt_id"] == first.attempt_id

    updated = repository.remediation_episode(episode["id"])
    assert updated["cold_attempt_id"] == first.attempt_id


def test_episode_links_prescription_primed_and_cold_end_to_end(tmp_path):
    vault, repository, misconception_id = _setup(tmp_path)
    episode, primed_result, cold_item = _drive_to_cold_scheduled(vault, repository, misconception_id)

    cold_result = _attempt(vault, repository, cold_item, clock=FrozenClock(NOW + timedelta(days=1)))
    final = repository.remediation_episode(episode["id"])
    # The four recorded stage boundaries (§7.2 telemetry) survive on one row.
    assert final["state"] == "completed"
    assert final["case_kind"] == "misconception"
    assert final["case_ref"] == misconception_id
    assert final["passages_shown"] is not None  # prescription happened (may be empty)
    assert final["primed_attempt_id"] == primed_result.attempt_id
    assert final["cold_attempt_id"] == cold_result.attempt_id
    assert final["completed_at"]

    task = next(task for task in _all_tasks(repository) if task["kind"] == "cold_retry")
    assert task["remediation_episode_id"] == episode["id"]
    assert task["source_attempt_id"] == primed_result.attempt_id
    assert task["selected_item_id"] == cold_item
    assert task["consumed_attempt_id"] == cold_result.attempt_id


def _all_tasks(repository):
    with repository.connection() as connection:
        rows = connection.execute("SELECT * FROM followup_tasks ORDER BY created_at, id").fetchall()
    return [dict(row) for row in rows]
