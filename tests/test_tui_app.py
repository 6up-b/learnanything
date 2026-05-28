from __future__ import annotations

import asyncio

from textual.widgets import Static

from learnloop.db.repositories import MasteryState, Repository
from learnloop.tui.app import ErrorScreen, LearnLoopApp
from learnloop.tui.screens.start import StartScreen
from learnloop.tui.screens.today import PracticeCard, TodayScreen

from tests.helpers import NOW_ISO, begin_session, create_basic_vault


def test_tui_app_launches_start_screen_and_syncs_state(tmp_path):
    async def scenario() -> None:
        vault_root = tmp_path / "vault"
        create_basic_vault(vault_root)
        app = LearnLoopApp(vault_root)

        async with app.run_test() as pilot:
            await pilot.pause()

            assert isinstance(app.screen, StartScreen)
            assert app.state is not None
            assert app.state.repository.practice_item_state("pi_svd_define_001") is not None
            assert app.state.repository.mastery_state("lo_svd_definition") is not None

            today = await begin_session(app, pilot)
            assert isinstance(today, TodayScreen)
            assert isinstance(app.screen, TodayScreen)

    asyncio.run(scenario())


def test_tui_app_shows_error_screen_for_missing_vault(tmp_path):
    async def scenario() -> None:
        app = LearnLoopApp(tmp_path / "missing")

        async with app.run_test() as pilot:
            await pilot.pause()

            assert isinstance(app.screen, ErrorScreen)
            assert "learnloop.toml" in str(app.query_one("#error-message", Static).renderable)

    asyncio.run(scenario())


def test_tui_today_screen_renders_queue_details_and_refreshes(tmp_path):
    async def scenario() -> None:
        vault_root = tmp_path / "vault"
        paths = create_basic_vault(vault_root)
        repository = Repository(paths.sqlite_path)
        repository.upsert_mastery_state(
            MasteryState(
                learning_object_id="lo_svd_definition",
                logit_mean=0.0,
                logit_variance=1.0,
                evidence_count=1,
                last_evidence_at="2026-05-18T12:00:00Z",
                algorithm_version="mvp-0.1",
                updated_at=NOW_ISO,
            )
        )
        repository.upsert_practice_item_state(
            "pi_svd_define_001",
            difficulty=5.0,
            stability=2.0,
            due_at="2026-05-18T12:00:00Z",
            last_attempt_at="2026-05-16T12:00:00Z",
            active=True,
        )
        app = LearnLoopApp(vault_root)

        async with app.run_test() as pilot:
            await pilot.pause()
            await begin_session(app, pilot)
            await pilot.press("r")
            await pilot.pause()

            assert isinstance(app.screen, TodayScreen)
            assert [item.practice_item_id for item in app.state.queue] == ["pi_svd_define_001"]
            focused = str(app.screen.query_one("PracticeCard.-focused", PracticeCard).renderable)
            assert "SVD definition" in focused
            assert "Define SVD." in focused
            assert "forgetting_risk" in str(app.screen.query_one("#why-order", Static).renderable)

    asyncio.run(scenario())
