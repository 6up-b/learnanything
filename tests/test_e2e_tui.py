from __future__ import annotations

import asyncio

from learnloop.db.repositories import Repository
from learnloop.tui.app import LearnLoopApp
from learnloop.tui.screens.feedback import FeedbackScreen
from learnloop.tui.screens.practice import PracticeScreen
from learnloop.tui.screens.today import TodayScreen

from tests.helpers import create_basic_vault, seed_due_item


def test_tui_end_to_end_self_graded_practice(tmp_path):
    async def scenario() -> None:
        vault_root = tmp_path / "vault"
        paths = create_basic_vault(vault_root)
        seed_due_item(paths)

        app = LearnLoopApp(vault_root)
        async with app.run_test() as pilot:
            await pilot.pause()
            assert isinstance(app.screen, TodayScreen)

            today = app.screen
            await today.open_practice()
            await pilot.pause()
            practice = app.screen
            assert isinstance(practice, PracticeScreen)
            practice.set_answer("A factorization into U, Sigma, V transpose.")

            feedback = await practice.open_feedback()
            await pilot.pause()
            assert isinstance(app.screen, FeedbackScreen)
            feedback.set_points("correctness", 4)
            feedback.set_confidence(5)
            result = feedback.submit()

            # Returning to Today refreshes the queue from persisted state.
            feedback.return_to_today()
            await pilot.pause()
            assert isinstance(app.screen, TodayScreen)

        # Persistent state survives the app session.
        repository = Repository(paths.sqlite_path)
        attempt = repository.fetch_practice_attempt(result.attempt_id)
        assert attempt is not None
        assert attempt["rubric_score"] == 4
        assert repository.fetch_grading_evidence(result.attempt_id)
        assert repository.mastery_state("lo_svd_definition").evidence_count >= 1
        assert repository.practice_item_state("pi_svd_define_001").due_at is not None

    asyncio.run(scenario())
