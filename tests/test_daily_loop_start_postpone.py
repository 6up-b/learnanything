"""Daily-loop audit 2026-10-11: the Start screen's "postpone" control.

The desktop Start screen showed a "postpone" button with no handler, and the TUI
Start screen's "Postpone 1h" only flashed "Session postponed 1h." while doing
nothing. LearnLoop has no backing behaviour for postponing a session (no reminder,
no deferred start, no sidecar method), so neither surface may offer the control.
The desktop half is covered by ``apps/learnloop-tauri/src/screens/StartScreen.test.tsx``.
"""

from __future__ import annotations

import asyncio

from learnloop.tui.app import LearnLoopApp
from learnloop.tui.screens.start import StartScreen

from tests.helpers import create_basic_vault


def test_tui_start_screen_offers_no_postpone_it_cannot_honour(tmp_path):
    async def scenario() -> None:
        vault_root = tmp_path / "vault"
        create_basic_vault(vault_root)
        app = LearnLoopApp(vault_root)

        async with app.run_test() as pilot:
            await pilot.pause()
            assert isinstance(app.screen, StartScreen)
            assert not app.screen.query("#postpone-button")
            await pilot.press("p")
            await pilot.pause()
            # No "Session postponed" claim for a postponement that never happens.
            assert not any("postponed" in str(note.message).lower() for note in app._notifications)

    asyncio.run(scenario())
    assert all(binding[1] != "postpone" for binding in StartScreen.BINDINGS)
