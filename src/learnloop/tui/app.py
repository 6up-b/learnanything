from __future__ import annotations

from pathlib import Path

from textual.app import App, ComposeResult
from textual.screen import Screen
from learnloop.tui.screens.start import StartScreen
from learnloop.tui.state import TuiState
from learnloop.tui.theme import LEARNLOOP_THEME, LEARNLOOP_VARIABLES
from learnloop.tui.widgets import TextStatic


class ErrorScreen(Screen):
    def __init__(self, message: str):
        super().__init__()
        self.message = message

    def compose(self) -> ComposeResult:
        yield TextStatic("LearnLoop could not open this vault.", id="error-title")
        yield TextStatic(self.message, id="error-message")


class LearnLoopApp(App):
    CSS_PATH = "learnloop.tcss"

    BINDINGS = [
        ("q", "quit", "Quit"),
    ]

    def __init__(self, vault_root: Path):
        super().__init__()
        self.vault_root = vault_root
        self.state: TuiState | None = None
        self.last_attempt_result = None

    def get_theme_variable_defaults(self) -> dict[str, str]:
        # Custom theme variables must resolve at CSS-parse time, which happens
        # before on_mount registers the theme. Without this, any sheet using
        # $probe raises "reference to undefined variable" and the app crashes.
        return dict(LEARNLOOP_VARIABLES)

    def on_mount(self) -> None:
        self.register_theme(LEARNLOOP_THEME)
        self.theme = "learnloop"

    def get_default_screen(self) -> Screen:
        try:
            self.state = TuiState.load(self.vault_root)
        except Exception as exc:
            return ErrorScreen(str(exc))
        return StartScreen(self.state)


def run(vault_root: Path) -> None:
    LearnLoopApp(vault_root).run()
