"""B8 duel storage: pre-reveal answer_confidence only, and a duel read model
that compares learner vs model exclusively on matched cold attempts (spec §4.6)."""

from __future__ import annotations

import sqlite3

import pytest

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.services.attempts import (
    AttemptDraft,
    AttemptValidationError,
    SelfGradeInput,
    complete_self_graded_attempt,
)
from learnloop.services.exam_calibration import calibration_report
from learnloop.vault.loader import load_vault

from tests.helpers import NOW, NOW_ISO, create_basic_vault

LO_ID = "lo_svd_definition"
ITEM_ID = "pi_svd_define_001"


def _setup(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    vault = load_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    return vault, repository


def _insert_slate(repository, slate_id="slate1"):
    with repository.connection() as connection:
        connection.execute(
            """
            INSERT INTO scheduler_slates(
              id, session_id, generated_at, selection_policy, session_context_json,
              config_snapshot_json, algorithm_version, created_at, updated_at
            ) VALUES (?, 'sess1', ?, 'policy', '{}', '{}', 'mvp-0.7', ?, ?)
            """,
            (slate_id, NOW_ISO, NOW_ISO, NOW_ISO),
        )
        connection.commit()


def _insert_candidate(repository, candidate_id, *, predicted, slate_id="slate1", item_id=ITEM_ID):
    with repository.connection() as connection:
        connection.execute(
            """
            INSERT INTO scheduler_slate_candidates(
              id, slate_id, practice_item_id, rank, selected_mode, priority,
              predicted_correctness, components_json, algorithm_version, created_at
            ) VALUES (?, ?, ?, 1, 'review', 1.0, ?, '{}', 'mvp-0.7', ?)
            """,
            (candidate_id, slate_id, f"{item_id}_{candidate_id}", predicted, NOW_ISO),
        )
        connection.commit()


def _insert_attempt(
    repository,
    attempt_id,
    *,
    candidate_id=None,
    answer_confidence=None,
    correctness=1.0,
    attempt_type="independent_attempt",
    hints_used=0,
    primed=0,
):
    with repository.connection() as connection:
        connection.execute(
            """
            INSERT INTO practice_attempts(
              id, practice_item_id, learning_object_id, practice_mode, attempt_type,
              rubric_score, correctness, hints_used, primed, answer_confidence,
              scheduler_candidate_id, created_at
            ) VALUES (?, ?, ?, 'short_answer', ?, 4, ?, ?, ?, ?, ?, ?)
            """,
            (
                attempt_id,
                f"{ITEM_ID}_{attempt_id}",
                LO_ID,
                attempt_type,
                correctness,
                hints_used,
                primed,
                answer_confidence,
                candidate_id,
                NOW_ISO,
            ),
        )
        connection.commit()


# -- Pre-reveal capture ---------------------------------------------------------


def test_answer_confidence_must_be_a_1_to_5_committed_tap(tmp_path):
    vault, repository = _setup(tmp_path)
    for invalid in (0, 6):
        with pytest.raises(AttemptValidationError):
            complete_self_graded_attempt(
                vault,
                repository,
                AttemptDraft(
                    practice_item_id=ITEM_ID,
                    learner_answer_md="U Sigma V transpose.",
                    attempt_type="independent_attempt",
                    answer_confidence=invalid,
                ),
                SelfGradeInput(criterion_points={"correctness": 4}, confidence=4),
                clock=FrozenClock(NOW),
            )


def test_post_reveal_confidence_tap_cannot_land_on_a_graded_attempt(tmp_path):
    """answer_confidence rides only the pre-reveal draft. Once the submission is
    graded, a replayed submission carrying a late tap is rejected by the
    submission-identity unique index and the stored value stays untouched."""

    vault, repository = _setup(tmp_path)

    def submit(confidence):
        return complete_self_graded_attempt(
            vault,
            repository,
            AttemptDraft(
                practice_item_id=ITEM_ID,
                learner_answer_md="U Sigma V transpose.",
                attempt_type="independent_attempt",
                answer_confidence=confidence,
                submission_id="submission-1",
            ),
            SelfGradeInput(criterion_points={"correctness": 4}, confidence=4),
            clock=FrozenClock(NOW),
        )

    result = submit(None)  # the learner skipped the pre-reveal tap
    with pytest.raises(sqlite3.IntegrityError):
        submit(5)  # post-reveal: the outcome is known, the tap is refused

    stored = repository.fetch_practice_attempt(result.attempt_id)
    assert stored["answer_confidence"] is None
    assert repository.calibration_duel_pairs() == []


# -- Duel read model -------------------------------------------------------------


def test_duel_excludes_assisted_primed_and_unmatched_attempts(tmp_path):
    vault, repository = _setup(tmp_path)
    _insert_slate(repository)
    for index, predicted in enumerate((0.9, 0.9, 0.9, 0.9, None), start=1):
        _insert_candidate(repository, f"cand{index}", predicted=predicted)

    # The one matched attempt: unassisted, unprimed, both predictions present.
    _insert_attempt(repository, "att_ok", candidate_id="cand1", answer_confidence=4, correctness=1.0)
    # Excluded: assisted (hints), primed, missing learner tap, missing model side.
    _insert_attempt(repository, "att_hint", candidate_id="cand2", answer_confidence=4, hints_used=1)
    _insert_attempt(repository, "att_primed", candidate_id="cand3", answer_confidence=4, primed=1)
    _insert_attempt(repository, "att_notap", candidate_id="cand4", answer_confidence=None)
    _insert_attempt(repository, "att_nomodel", candidate_id="cand5", answer_confidence=4)
    _insert_attempt(repository, "att_nocand", candidate_id=None, answer_confidence=4)
    _insert_attempt(
        repository, "att_dontknow", candidate_id="cand1", answer_confidence=4,
        attempt_type="dont_know", correctness=0.0,
    )

    pairs = repository.calibration_duel_pairs()
    assert [pair["attempt_id"] for pair in pairs] == ["att_ok"]

    report = calibration_report(vault, repository)
    duel = report["duel"]
    assert duel["n"] == 1
    # Learner tap 4 maps to 0.70 at consumption time; stored values stay 1-5.
    assert duel["learner_brier"] == pytest.approx((0.70 - 1.0) ** 2)
    assert duel["model_brier"] == pytest.approx((0.90 - 1.0) ** 2)


def test_duel_is_empty_when_no_matched_attempt_exists(tmp_path):
    vault, repository = _setup(tmp_path)
    _insert_slate(repository)
    _insert_candidate(repository, "cand1", predicted=0.9)
    _insert_attempt(repository, "att_hint", candidate_id="cand1", answer_confidence=4, hints_used=1)

    report = calibration_report(vault, repository)
    assert report["duel"] == {"n": 0, "learner_brier": None, "model_brier": None}
    # The minimum-N gate keeps the reliability curve honest at this volume.
    assert report["items"]["curve_available"] is False
