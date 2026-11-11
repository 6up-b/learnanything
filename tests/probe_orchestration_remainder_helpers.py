"""What other test files use from ``tests/test_probe_orchestration_remainder.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.ids import new_ulid
from learnloop.attempts.attempts import ApplyAttemptInput, AttemptDraft, ResolvedGrade, apply_attempt
from learnloop.vault.loader import load_vault

from tests.helpers import NOW, admit_probe_instrument_card, create_basic_vault


LO_ID = "lo_svd_definition"
ITEM_ID = "pi_svd_define_001"
CLOCK = FrozenClock(NOW)


def _setup(tmp_path, *, with_card: bool = True):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    loaded = load_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    if with_card:
        admit_probe_instrument_card(repository)
    return vault_root, loaded, repository


def _grade(score: int) -> ResolvedGrade:
    return ResolvedGrade(
        rubric_score=score,
        criterion_points={"correctness": float(score)},
        evidence_rows=[],
        error_attributions=[],
        grader_confidence=1.0,
        confidence=4,
        manual_review_reason=None,
    )


def _submit(loaded, repository, *, score=4, attempt_type="independent_attempt",
            presentation_id=None, answer_confidence=None, session_id=None, clock=CLOCK,
            item_id=ITEM_ID):
    attempt_id = new_ulid()
    result = apply_attempt(
        loaded,
        repository,
        ApplyAttemptInput(
            draft=AttemptDraft(
                practice_item_id=item_id,
                learner_answer_md="answer",
                attempt_type=attempt_type,
                session_id=session_id,
                probe_presentation_id=presentation_id,
                answer_confidence=answer_confidence,
            ),
            attempt_id=attempt_id,
            grade=_grade(score),
            grading_source="ai",
        ),
        clock=clock,
    )
    return attempt_id, result
