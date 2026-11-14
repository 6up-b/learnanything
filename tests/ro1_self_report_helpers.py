"""What other test files use from ``tests/test_ro1_self_report.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

import pytest

from learnloop.attempts.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.diagnosis.causal_attribution import record_unresolved_cause_self_report
from learnloop.substrate.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault

from tests.helpers import NOW
from tests.km2_write_path_helpers import build_shared_facet_vault


@pytest.fixture(scope="module")
def picked(tmp_path_factory):
    """A miss with an unresolved factor, resolved by the learner's pick (written at mvp-0.7)."""

    root = tmp_path_factory.mktemp("picked") / "vault"
    paths = build_shared_facet_vault(root)
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    clock = FrozenClock(NOW)
    sync_vault_state(vault, repository, clock=clock)
    result = complete_self_graded_attempt(
        vault, repository,
        AttemptDraft(practice_item_id="pi_svd_ambiguous_001", learner_answer_md="An answer."),
        SelfGradeInput(criterion_points={"whole_item": 0}, fatal_errors=[], confidence=4),
        clock=clock,
    )
    factor = repository.unresolved_cause_factors_for_attempt(result.attempt_id)[0]
    report = record_unresolved_cause_self_report(
        vault, repository, factor_id=factor["id"], response="believed_candidate", candidate_index=0, clock=clock)
    assert report["resolved"] is True
    return paths, factor["id"], result.attempt_id
