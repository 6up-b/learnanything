"""What other test files use from ``tests/test_remediation_cold_retry.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.attempts.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
from learnloop.diagnosis.remediation import (
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


def _cold_lane_ids(vault, repository, clock):
    """Items the queue is serving AS the cold-retry lane this build.

    Not plain queue membership: the cold item is an ordinary practice card too,
    so it can sit in the queue on its own merits. What the deferral withholds is
    the delayed COLD lane — the max-priority resurrection whose `followup_kind`
    says the serve is the measurement.
    """

    from learnloop.scheduling.scheduler import build_due_queue

    return [
        item.practice_item_id
        for item in build_due_queue(vault, repository, clock=clock)
        if item.followup_kind == "cold_retry"
    ]
