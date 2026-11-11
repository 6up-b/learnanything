"""What other test files use from ``tests/test_causal_cold_outcomes.py``, kept here because a test file never
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


def _setup(tmp_path, *, extra_items=True):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    seed_due_item(paths)
    if extra_items:
        add_followup_item(vault_root)
    vault = load_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    misconception_id = repository.insert_misconception(
        learning_object_id=LO_ID,
        statement="Confuses SVD with eigendecomposition.",
        correction_statement="SVD applies to any matrix.",
        facet_ids=["recall"],
        target_facet="recall",
        confused_with_facet="application",
        severity=0.8,
        clock=FrozenClock(NOW),
    )
    return vault_root, vault, repository, misconception_id


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
        SelfGradeInput(
            criterion_points={"correctness": 4}, fatal_errors=[], confidence=4
        ),
        clock=clock,
    )


def _to_treatment(vault, repository, misconception_id):
    episode = start_remediation_episode(
        repository, misconception_id, clock=FrozenClock(NOW)
    )
    prescribe_remediation(vault, repository, episode["id"], clock=FrozenClock(NOW))
    return start_remediation_treatment(
        vault, repository, episode["id"], clock=FrozenClock(NOW)
    )
