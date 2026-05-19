from __future__ import annotations

import asyncio

import pytest

from learnloop.db.repositories import Repository
from learnloop.services.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
from learnloop.tui.app import LearnLoopApp
from learnloop.tui.screens.feedback import FeedbackScreen
from learnloop.vault.loader import load_vault

from tests.helpers import create_basic_vault, seed_due_item


def _direct_attempt(tmp_path):
    """Run the same attempt through the service directly for parity comparison."""
    vault_root = tmp_path / "direct"
    paths = create_basic_vault(vault_root)
    seed_due_item(paths)
    loaded = load_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    return complete_self_graded_attempt(
        loaded,
        repository,
        AttemptDraft(practice_item_id="pi_svd_define_001", learner_answer_md="An answer."),
        SelfGradeInput(criterion_points={"correctness": 3}, confidence=4),
    )


def test_feedback_submit_matches_cli_attempt_and_updates_state(tmp_path):
    async def scenario() -> None:
        vault_root = tmp_path / "vault"
        paths = create_basic_vault(vault_root)
        seed_due_item(paths)

        app = LearnLoopApp(vault_root)
        async with app.run_test() as pilot:
            await pilot.pause()
            today = app.screen
            await today.open_practice()
            await pilot.pause()
            practice = app.screen
            practice.set_answer("An answer.")
            feedback = await practice.open_feedback()
            await pilot.pause()

            assert isinstance(app.screen, FeedbackScreen)
            feedback.set_points("correctness", 3)
            feedback.set_confidence(4)
            result = feedback.submit()

        expected = _direct_attempt(tmp_path)

        assert result.rubric_score == expected.rubric_score
        assert result.correctness == expected.correctness
        assert result.fsrs_rating == expected.fsrs_rating
        assert result.mastery_mean == pytest.approx(expected.mastery_mean, rel=1e-6)

        # State transitions persisted: attempt + grading evidence written.
        repository = Repository(paths.sqlite_path)
        attempt = repository.fetch_practice_attempt(result.attempt_id)
        assert attempt is not None
        assert attempt["rubric_score"] == result.rubric_score
        assert repository.fetch_grading_evidence(result.attempt_id)

    asyncio.run(scenario())
