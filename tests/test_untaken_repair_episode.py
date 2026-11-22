"""A repair episode whose primed attempt is never taken: what the sweep does with it, and what the routine queue
withholds while it is open."""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from learnloop.algorithm_versions import SECTION_END_ALGORITHM_VERSION
from learnloop.attempts.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
from learnloop.clock import FrozenClock, parse_utc
from learnloop.db.repositories import Repository
from learnloop.diagnosis.machine_checks import sweep_machine_checks
from learnloop.diagnosis.remediation import (
    prescribe_remediation,
    start_remediation_episode,
    start_remediation_treatment,
)
from learnloop.scheduling.scheduler import build_due_queue
from learnloop.vault.loader import load_vault
from tests.helpers import NOW, add_followup_item, create_basic_vault, seed_due_item, set_algorithm_version

LO_ID = "lo_svd_definition"
MISSED_ITEM = "pi_svd_define_001"
#: The episode opens a minute after the miss its diagnosis came from.
OPENED = NOW + timedelta(minutes=1)
#: The tag below which an untaken episode has no end.
BEFORE = SECTION_END_ALGORITHM_VERSION


def _world(tmp_path, version: str):
    root = tmp_path / "vault"
    paths = create_basic_vault(root)
    seed_due_item(paths, version=version)
    add_followup_item(root)
    add_followup_item(root, "pi_svd_define_003")
    set_algorithm_version(paths, version)
    vault = load_vault(root)
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
    miss = complete_self_graded_attempt(
        vault,
        repository,
        AttemptDraft(practice_item_id=MISSED_ITEM, learner_answer_md="A diagonal matrix.",
                     attempt_type="independent_attempt"),
        SelfGradeInput(criterion_points={"correctness": 0}, fatal_errors=[], confidence=2),
        clock=FrozenClock(NOW),
    )
    return vault, repository, misconception_id, miss.attempt_id


def _diagnose(repository: Repository, misconception_id: str, attempt_id: str) -> None:
    """The error event that ties the miss to the misconception the episode repairs."""

    repository.insert_error_event({
        "attempt_id": attempt_id, "learning_object_id": LO_ID, "error_type": "misconception", "severity": 0.8,
        "is_misconception": True, "created_at": NOW.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "misconception_id": misconception_id,
    })


def _open_episode(vault, repository, misconception_id: str, attempt_id: str, state: str) -> dict:
    episode = start_remediation_episode(repository, misconception_id, clock=FrozenClock(OPENED))
    prescribe_remediation(vault, repository, episode["id"], clock=FrozenClock(OPENED))
    if state == "treatment":
        start_remediation_treatment(vault, repository, episode["id"], clock=FrozenClock(OPENED))
    _diagnose(repository, misconception_id, attempt_id)
    stored = repository.remediation_episode(episode["id"])
    assert stored["state"] == state and stored["primed_attempt_id"] is None
    return stored


def _missed_item_due(repository: Repository) -> datetime:
    """The missed item's next ordinary review, as its own miss scheduled it."""

    due = parse_utc(repository.practice_item_state(MISSED_ITEM).due_at)
    assert due is not None and due > OPENED
    return due


def _sweep(vault, repository, at: datetime) -> None:
    sweep_machine_checks(vault, repository, LO_ID, clock=FrozenClock(at))


def _queued(vault, repository, item_id: str, at: datetime) -> bool:
    return item_id in [item.practice_item_id for item in build_due_queue(vault, repository, clock=FrozenClock(at))]


# -- below the tag: the episode has no end ------------------------------------------------------------------------


@pytest.mark.parametrize("state", ["prescribed", "treatment"])
def test_below_the_tag_an_untaken_episode_stays_open_past_its_items_review(tmp_path, state):
    vault, repository, misconception_id, attempt_id = _world(tmp_path, BEFORE)
    episode = _open_episode(vault, repository, misconception_id, attempt_id, state)
    due = _missed_item_due(repository)
    for at in (due + timedelta(minutes=1), due + timedelta(days=60)):
        _sweep(vault, repository, at)
        stored = repository.remediation_episode(episode["id"])
        assert stored["state"] == state and stored["primed_attempt_id"] is None


def test_below_the_tag_the_routine_queue_serves_an_untaken_episodes_cold_item(tmp_path):
    """Only an open cold retry withholds the cold item from Today's queue; an untaken episode does not, at any
    time, while the learner-initiated selectors' wider set holds it."""

    vault, repository, misconception_id, attempt_id = _world(tmp_path, BEFORE)
    episode = _open_episode(vault, repository, misconception_id, attempt_id, "treatment")
    cold_item = str(episode["cold_item_id"])
    assert cold_item and cold_item != MISSED_ITEM
    due = _missed_item_due(repository)
    assert cold_item in repository.open_remediation_cold_item_ids()
    assert cold_item not in repository.pending_remediation_cold_item_ids()
    for at in (OPENED, due + timedelta(minutes=1)):
        _sweep(vault, repository, at)
        assert _queued(vault, repository, cold_item, at)
    assert cold_item in repository.open_remediation_cold_item_ids()
