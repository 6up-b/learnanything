from __future__ import annotations

import asyncio
import re
from pathlib import Path

from learnloop.tui.app import LearnLoopApp

from tests.helpers import begin_session, create_basic_vault, seed_due_item

_TUI_DIR = Path(__file__).resolve().parents[1] / "src" / "learnloop" / "tui"
_HEX = re.compile(r"#[0-9a-fA-F]{6}\b")


def test_app_registers_and_activates_learnloop_theme(tmp_path):
    async def scenario() -> None:
        vault_root = tmp_path / "vault"
        create_basic_vault(vault_root)
        app = LearnLoopApp(vault_root)

        async with app.run_test() as pilot:
            await pilot.pause()

            assert app.theme == "learnloop"
            assert "learnloop" in app.available_themes
            variables = app.get_css_variables()
            # Custom variable resolves; auto-derived semantic tokens resolve.
            assert variables["probe"] == "#dc7fb8"
            assert variables.get("primary-muted")
            assert variables.get("text-primary")

    asyncio.run(scenario())


def test_all_screen_stylesheets_resolve_when_mounted(tmp_path):
    """Mount the app and push every screen so each CSS_PATH is parsed.

    Parsing happens before on_mount registers the theme; without the
    get_theme_variable_defaults override an undefined custom variable like
    $probe (used in practice.tcss) would crash here.
    """

    async def scenario() -> None:
        vault_root = tmp_path / "vault"
        paths = create_basic_vault(vault_root)
        seed_due_item(paths)
        app = LearnLoopApp(vault_root)

        async with app.run_test() as pilot:
            await pilot.pause()  # mounts StartScreen (start.tcss + learnloop.tcss)

            today = await begin_session(app, pilot)  # mounts TodayScreen (today.tcss)
            practice = await today.open_practice()
            await pilot.pause()  # parses practice.tcss
            assert practice is not None

            await practice.open_feedback()
            await pilot.pause()  # parses feedback.tcss

    asyncio.run(scenario())


def test_no_literal_hex_outside_theme_module():
    offenders: list[str] = []
    for path in [*_TUI_DIR.rglob("*.py"), *_TUI_DIR.rglob("*.tcss")]:
        if path.name == "theme.py":
            continue
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if _HEX.search(line):
                offenders.append(f"{path.relative_to(_TUI_DIR)}:{lineno}: {line.strip()}")
    assert not offenders, "literal hex colors must live only in theme.py:\n" + "\n".join(offenders)
