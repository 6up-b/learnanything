from __future__ import annotations

import asyncio

from learnloop.db.repositories import Repository
from learnloop.services.scheduler import build_due_queue
from learnloop.tui.app import LearnLoopApp
from learnloop.tui.screens.practice import PracticeScreen
from learnloop.tui.screens.today import TodayScreen
from learnloop.vault.loader import load_vault

from tests.helpers import begin_session, create_basic_vault, seed_due_item


def test_today_queue_matches_scheduler_and_opens_practice(tmp_path):
    async def scenario() -> None:
        vault_root = tmp_path / "vault"
        paths = create_basic_vault(vault_root)
        seed_due_item(paths)

        loaded = load_vault(vault_root)
        repository = Repository(paths.sqlite_path)
        expected = [item.practice_item_id for item in build_due_queue(loaded, repository, persist_explanations=False)]

        app = LearnLoopApp(vault_root)
        async with app.run_test() as pilot:
            await pilot.pause()
            today = await begin_session(app, pilot)
            assert isinstance(app.screen, TodayScreen)
            assert [item.practice_item_id for item in app.state.queue] == expected

            await today.open_practice()
            await pilot.pause()

            assert isinstance(app.screen, PracticeScreen)
            from learnloop.tui.widgets import TextStatic

            assert "Define SVD." in str(app.screen.query_one("#practice-prompt", TextStatic).renderable)

    asyncio.run(scenario())
