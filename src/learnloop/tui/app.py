from __future__ import annotations

from pathlib import Path

from textual.app import App, ComposeResult
from textual.screen import Screen
from learnloop.tui.screens.today import TodayScreen
from learnloop.tui.state import TuiState
from learnloop.tui.widgets import TextStatic


class ErrorScreen(Screen):
    def __init__(self, message: str):
        super().__init__()
        self.message = message

    def compose(self) -> ComposeResult:
        yield TextStatic("LearnLoop could not open this vault.", id="error-title")
        yield TextStatic(self.message, id="error-message")


class LearnLoopApp(App):
    CSS = """
    Screen {
        padding: 1 2;
    }

    #today-layout {
        height: 1fr;
    }

    #queue-panel {
        width: 42%;
        padding-right: 2;
    }

    #detail-panel {
        width: 58%;
    }

    #queue-title,
    #detail-title {
        text-style: bold;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("r", "refresh", "Refresh"),
        ("enter", "open_selected", "Practice"),
    ]

    def __init__(self, vault_root: Path):
        super().__init__()
        self.vault_root = vault_root
        self.state: TuiState | None = None
        self.last_attempt_result = None

    def get_default_screen(self) -> Screen:
        try:
            self.state = TuiState.load(self.vault_root)
        except Exception as exc:
            return ErrorScreen(str(exc))
        return TodayScreen(self.state)

    def action_refresh(self) -> None:
        screen = self.screen
        if isinstance(screen, TodayScreen):
            screen.action_refresh()

    def action_open_selected(self) -> None:
        screen = self.screen
        if isinstance(screen, TodayScreen):
            screen.action_open_selected()


def run(vault_root: Path) -> None:
    LearnLoopApp(vault_root).run()
