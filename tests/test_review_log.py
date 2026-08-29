"""Review-log reconstruction fidelity: chaining the reconstructed
(rating, elapsed) sequences through apply_review must reproduce the live
practice_item_state exactly."""

from __future__ import annotations

from datetime import timedelta

import pytest

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.attempts.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
from learnloop.scheduling.fsrs import MemoryState, Rating, apply_review
from learnloop.scheduling.review_log import reconstruct_review_log
from learnloop.substrate.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault

from tests.helpers import NOW, create_basic_vault


def _record(vault, repository, *, at, attempt_type="independent_attempt", points=4, hints=0, answer="U Sigma V^T."):
    return complete_self_graded_attempt(
        vault,
        repository,
        AttemptDraft(
            practice_item_id="pi_svd_define_001",
            learner_answer_md=answer,
            attempt_type=attempt_type,
            hints_used=hints,
        ),
        SelfGradeInput(criterion_points={"correctness": points}, confidence=3),
        clock=FrozenClock(at),
    )


def _seeded_vault(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    vault = load_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    sync_vault_state(vault, repository, clock=FrozenClock(NOW))
    return vault, repository


def test_reconstruction_reproduces_live_practice_item_state(tmp_path):
    vault, repository = _seeded_vault(tmp_path)
    # Varied scores, a hinted attempt (rating cap), a dont_know, multi-day gaps.
    _record(vault, repository, at=NOW, points=4)
    _record(vault, repository, at=NOW + timedelta(days=2), points=2)
    _record(vault, repository, at=NOW + timedelta(days=3, hours=6), attempt_type="hinted_attempt", points=4, hints=1)
    _record(vault, repository, at=NOW + timedelta(days=7), attempt_type="dont_know", points=0, answer="")
    _record(vault, repository, at=NOW + timedelta(days=9), points=3)

    log = reconstruct_review_log(vault, repository)
    assert log.total_reviews == 5
    assert log.skipped_attempts == 0
    sequence = log.sequences["pi_svd_define_001"]
    assert [obs.first_review for obs in sequence] == [True, False, False, False, False]

    state: MemoryState | None = None
    for observation in sequence:
        state = apply_review(state, observation.rating, observation.elapsed_days)

    live = repository.practice_item_state("pi_svd_define_001")
    assert state is not None
    assert state.difficulty == pytest.approx(live.difficulty, abs=1e-9)
    assert state.stability == pytest.approx(live.stability, abs=1e-9)


def test_hint_cap_and_score_binning_match_live_semantics(tmp_path):
    vault, repository = _seeded_vault(tmp_path)
    # Full marks with one hint: raw rating EASY, capped to GOOD by the item's
    # fsrs_rating_cap_by_hint policy (helpers.py fixture).
    result = _record(vault, repository, at=NOW, attempt_type="hinted_attempt", points=4, hints=1)
    assert result.fsrs_rating == "good"

    log = reconstruct_review_log(vault, repository)
    observation = log.sequences["pi_svd_define_001"][0]
    assert observation.rating == Rating.GOOD
    assert observation.weight == pytest.approx(1.0)  # hinted evidence_mass


def test_dont_know_rating_and_weight(tmp_path):
    vault, repository = _seeded_vault(tmp_path)
    _record(vault, repository, at=NOW, attempt_type="dont_know", points=0, answer="")
    log = reconstruct_review_log(vault, repository)
    observation = log.sequences["pi_svd_define_001"][0]
    assert observation.rating == Rating.AGAIN
    assert observation.weight == pytest.approx(0.7)  # dont_know evidence_mass


def test_elapsed_days_between_successive_attempts(tmp_path):
    vault, repository = _seeded_vault(tmp_path)
    _record(vault, repository, at=NOW)
    _record(vault, repository, at=NOW + timedelta(days=1, hours=12))
    log = reconstruct_review_log(vault, repository)
    sequence = log.sequences["pi_svd_define_001"]
    assert sequence[0].elapsed_days == 0.0
    assert sequence[1].elapsed_days == pytest.approx(1.5)
    assert log.data_through == sequence[1].observed_at.isoformat().replace("+00:00", "Z")
