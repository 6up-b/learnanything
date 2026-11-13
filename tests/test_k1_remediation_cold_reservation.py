"""K1-6: a remediation's cold item is reserved from the moment it is chosen, and the cold kinds have one definition."""

from __future__ import annotations

from datetime import timedelta

import pytest

from learnloop import learner_protection, serve_eligibility
from learnloop.db.repositories import Repository
from learnloop.instructional.policy import cold_administration_open
from learnloop.scheduling.serving_exclusions import out_of_timing_serving_exclusions
from learnloop.vault.loader import load_vault
from tests.helpers import create_basic_vault


@pytest.fixture
def world(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    return load_vault(paths.root), Repository(paths.sqlite_path)


def _episode(repository: Repository, cold_item: str, state: str):
    episode = repository.create_remediation_episode(case_kind="diagnosis", case_ref="att_1", state="diagnosis")
    return repository.update_remediation_episode(episode["id"], state=state, cold_item_id=cold_item)


def test_a_cold_item_chosen_for_a_treatment_is_reserved_before_its_task_exists(world):
    vault, repository = world
    cold_item = next(iter(vault.practice_items))
    assert not cold_administration_open(repository, cold_item)
    _episode(repository, cold_item, "treatment")
    assert repository.open_followup_tasks_of_kind("cold_retry") == []
    assert cold_administration_open(repository, cold_item)
    exclusions = out_of_timing_serving_exclusions(
        vault, repository, cold_followup_kinds=sorted(serve_eligibility.COLD_FOLLOWUP_TASK_KINDS),
        reveal_window=timedelta(days=1))
    assert cold_item in exclusions.cold_check_reserved_item_ids


@pytest.mark.parametrize("state", ["completed", "abandoned"])
def test_a_finished_episode_reserves_nothing(world, state):
    vault, repository = world
    cold_item = next(iter(vault.practice_items))
    _episode(repository, cold_item, state)
    assert not cold_administration_open(repository, cold_item)


def test_the_cold_task_kinds_are_defined_once():
    assert learner_protection.COLD_TASK_KINDS is serve_eligibility.COLD_FOLLOWUP_TASK_KINDS


def test_the_routine_due_queue_does_not_serve_a_reserved_cold_item_before_its_check(world):
    """An ordinary due item that a treatment episode has chosen as its cold item leaves Today's queue
    until the episode ends: practising it first would spoil the check."""

    from learnloop.scheduling.scheduler import build_due_queue

    vault, repository = world
    cold_item = next(iter(vault.practice_items))
    assert cold_item in [item.practice_item_id for item in build_due_queue(vault, repository)]
    episode = _episode(repository, cold_item, "treatment")
    assert repository.open_followup_tasks_of_kind("cold_retry") == []
    assert cold_item not in [item.practice_item_id for item in build_due_queue(vault, repository)]
    repository.update_remediation_episode(episode["id"], state="completed")
    assert cold_item in [item.practice_item_id for item in build_due_queue(vault, repository)]


def _scheduled_retry(repository: Repository, cold_item: str, *, not_before: str, expires_at: str):
    episode = _episode(repository, cold_item, "cold_scheduled")
    task = repository.create_followup_task(
        kind="cold_retry", case_kind="diagnosis", case_ref="att_1", source_attempt_id=None,
        remediation_episode_id=episode["id"], not_before=not_before, expires_at=expires_at,
        selected_item_id=cold_item, context={},
    )
    return episode, task


def test_a_cold_retry_that_expires_unanswered_releases_its_reservation(world):
    """The reservation ends with the thing it reserves for: a retry left to expire frees the item for the
    queue and for practice admission, whichever reader looks next."""

    from datetime import UTC, datetime

    from learnloop.clock import FrozenClock
    from learnloop.scheduling.scheduler import build_due_queue

    vault, repository = world
    cold_item = next(iter(vault.practice_items))
    episode, _task = _scheduled_retry(
        repository, cold_item, not_before="2026-01-02T00:00:00Z", expires_at="2026-01-09T00:00:00Z")
    assert cold_administration_open(repository, cold_item)
    during = FrozenClock(datetime(2026, 1, 5, tzinfo=UTC))
    repository.due_followup_tasks(clock=during)
    assert cold_administration_open(repository, cold_item)  # the window is still open
    after = FrozenClock(datetime(2026, 1, 20, tzinfo=UTC))
    repository.due_followup_tasks(clock=after)  # the queue's own expiry
    assert repository.open_followup_tasks_of_kind("cold_retry") == []
    assert not cold_administration_open(repository, cold_item)
    assert repository.remediation_episode(episode["id"])["state"] == "abandoned"
    assert cold_item in [item.practice_item_id for item in build_due_queue(vault, repository, clock=after)]


def test_a_withdrawn_cold_retry_with_no_replacement_releases_its_reservation(world):
    from learnloop.diagnosis.remediation import withdraw_cold_measurement
    from learnloop.serve_eligibility import COLD_CHECK_HELP_TAKEN

    vault, repository = world
    cold_item = next(iter(vault.practice_items))
    episode, task = _scheduled_retry(
        repository, cold_item, not_before="2026-01-02T00:00:00Z", expires_at="2099-01-09T00:00:00Z")
    withdraw_cold_measurement(vault, repository, task["id"], reason=COLD_CHECK_HELP_TAKEN)
    assert not cold_administration_open(repository, cold_item)
    assert repository.remediation_episode(episode["id"])["state"] == "abandoned"
