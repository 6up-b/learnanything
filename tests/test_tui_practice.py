from __future__ import annotations

import asyncio

from learnloop.tui.app import LearnLoopApp
from learnloop.tui.screens.feedback import FeedbackScreen
from learnloop.tui.screens.practice import PracticeScreen
from learnloop.tui.widgets import TextStatic
from learnloop.vault.loader import load_vault
from learnloop.vault.writer import upsert_practice_item

from tests.helpers import begin_session, create_basic_vault, seed_due_item


def test_practice_screen_collects_answer_and_opens_feedback(tmp_path):
    async def scenario() -> None:
        vault_root = tmp_path / "vault"
        paths = create_basic_vault(vault_root)
        seed_due_item(paths)

        app = LearnLoopApp(vault_root)
        async with app.run_test() as pilot:
            await pilot.pause()
            today = await begin_session(app, pilot)
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


def test_practice_screen_submit_shortcut_opens_feedback(tmp_path):
    async def scenario() -> None:
        vault_root = tmp_path / "vault"
        paths = create_basic_vault(vault_root)
        seed_due_item(paths)

        app = LearnLoopApp(vault_root)
        async with app.run_test() as pilot:
            await pilot.pause()
            today = await begin_session(app, pilot)
            await today.open_practice()
            await pilot.pause()

            practice = app.screen
            assert isinstance(practice, PracticeScreen)
            practice.set_answer("A factorization into U, Sigma, V transpose.")
            await pilot.press("ctrl+j")
            await pilot.pause()

            assert isinstance(app.screen, FeedbackScreen)
            assert app.screen.draft.learner_answer_md == "A factorization into U, Sigma, V transpose."

    asyncio.run(scenario())


def test_practice_screen_submit_button_opens_feedback(tmp_path):
    async def scenario() -> None:
        vault_root = tmp_path / "vault"
        paths = create_basic_vault(vault_root)
        seed_due_item(paths)

        app = LearnLoopApp(vault_root)
        async with app.run_test() as pilot:
            await pilot.pause()
            today = await begin_session(app, pilot)
            await today.open_practice()
            await pilot.pause()

            practice = app.screen
            assert isinstance(practice, PracticeScreen)
            practice.set_answer("A factorization into U, Sigma, V transpose.")
            await pilot.click("#submit-answer")
            await pilot.pause()

            assert isinstance(app.screen, FeedbackScreen)
            assert app.screen.draft.learner_answer_md == "A factorization into U, Sigma, V transpose."

    asyncio.run(scenario())


def test_practice_screen_uses_item_allowed_attempt_type(tmp_path):
    async def scenario() -> None:
        vault_root = tmp_path / "vault"
        paths = create_basic_vault(vault_root)
        upsert_practice_item(
            vault_root,
            {
                **load_vault(vault_root).practice_items["pi_svd_define_001"].model_dump(mode="json"),
                "attempt_types_allowed": ["open_text"],
            },
        )
        seed_due_item(paths)

        app = LearnLoopApp(vault_root)
        async with app.run_test() as pilot:
            await pilot.pause()
            today = await begin_session(app, pilot)
            await today.open_practice()
            await pilot.pause()

            practice = app.screen
            assert isinstance(practice, PracticeScreen)
            assert practice.attempt_type == "open_text"
            practice.set_answer("A factorization into U, Sigma, V transpose.")
            feedback = await practice.open_feedback()
            await pilot.pause()

            assert isinstance(app.screen, FeedbackScreen)
            assert feedback.draft.attempt_type == "open_text"

    asyncio.run(scenario())
