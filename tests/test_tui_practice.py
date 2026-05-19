from __future__ import annotations

import asyncio

from learnloop.tui.app import LearnLoopApp
from learnloop.tui.screens.feedback import FeedbackScreen
from learnloop.tui.screens.practice import PracticeScreen
from learnloop.tui.widgets import TextStatic

from tests.helpers import create_basic_vault, seed_due_item


def test_practice_screen_collects_answer_and_opens_feedback(tmp_path):
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
            assert isinstance(practice, PracticeScreen)
            practice.set_answer("A factorization into U, Sigma, V transpose.")
            practice.reveal_hint()
            assert "Name the three factors." in str(
                practice.query_one("#practice-hints", TextStatic).renderable
            )

            feedback = await practice.open_feedback()
            await pilot.pause()
            assert isinstance(app.screen, FeedbackScreen)
            assert feedback.draft.learner_answer_md == "A factorization into U, Sigma, V transpose."
            assert "Expected" in str(app.screen.query_one("#expected-answer", TextStatic).renderable)

    asyncio.run(scenario())
