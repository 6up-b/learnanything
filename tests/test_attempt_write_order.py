"""Characterize the canonical attempt write order required before extraction."""

from __future__ import annotations

from learnloop.attempts import post_attempt
from learnloop.attempts.attempts import (
    AttemptDraft,
    SelfGradeInput,
    complete_self_graded_attempt,
)
from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.substrate.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault

from tests.helpers import NOW, create_basic_vault


def test_canonical_attempt_write_order_is_receipt_grade_evidence_state_then_post(
    tmp_path,
    monkeypatch,
):
    paths = create_basic_vault(tmp_path / "vault")
    vault = load_vault(tmp_path / "vault")
    repository = Repository(paths.sqlite_path)
    clock = FrozenClock(NOW)
    sync_vault_state(vault, repository, clock=clock)

    observed: list[str] = []
    hooks = (
        ("_insert_practice_attempt", "receipt"),
        ("_insert_grading_evidence", "grade"),
        ("_insert_error_event", "evidence"),
        ("_upsert_practice_item_state_record", "state"),
    )
    for method_name, label in hooks:
        original = getattr(Repository, method_name)

        def instrumented(self, *args, _original=original, _label=label, **kwargs):
            observed.append(_label)
            return _original(self, *args, **kwargs)

        monkeypatch.setattr(Repository, method_name, instrumented)

    self_grade = SelfGradeInput(
        criterion_points={"correctness": 2},
        error_type="conceptual_slip",
        confidence=4,
    )
    result = complete_self_graded_attempt(
        vault,
        repository,
        AttemptDraft(
            practice_item_id="pi_svd_define_001",
            learner_answer_md="SVD is a scalar decomposition.",
            attempt_type="independent_attempt",
        ),
        self_grade,
        clock=clock,
    )
    observed.append("post-attempt")
    post_attempt.run_post_attempt_pipeline(
        vault,
        repository,
        result=result,
        session_id=None,
        self_grade=self_grade,
        clock=clock,
    )

    first = {label: observed.index(label) for label in set(observed)}
    assert [
        first[label]
        for label in ("receipt", "grade", "evidence", "state", "post-attempt")
    ] == sorted(first.values())
