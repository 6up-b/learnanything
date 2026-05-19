from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Label, ListItem, ListView, Static

from learnloop.services.scheduler import ScheduledItem
from learnloop.tui.state import TuiState
from learnloop.tui.widgets import TextStatic


class TodayScreen(Screen):
    BINDINGS = [
        ("r", "refresh", "Refresh"),
        ("enter", "open_selected", "Practice"),
    ]

    def __init__(self, state: TuiState):
        super().__init__()
        self.state = state
        self.selected_index = 0

    def compose(self) -> ComposeResult:
        yield TextStatic(f"Vault: {self.state.vault_root}", id="vault-path")
        with Horizontal(id="today-layout"):
            with Vertical(id="queue-panel"):
                yield Label("Today Queue", id="queue-title")
                yield ListView(id="queue-list")
                yield Button("Refresh", id="refresh-button")
            with Vertical(id="detail-panel"):
                yield Label("Details", id="detail-title")
                yield TextStatic("", id="item-title")
                yield TextStatic("", id="item-prompt")
                yield TextStatic("", id="item-components")
                yield TextStatic("", id="item-reasons")
                yield Button("Begin Practice", id="practice-button")

    def on_mount(self) -> None:
        self._render_queue()

    def on_screen_resume(self) -> None:
        self.selected_index = 0
        self._render_queue()

    def action_refresh(self) -> None:
        self.state.refresh()
        self.selected_index = 0
        self._render_queue()

    def action_open_selected(self) -> None:
        item = self._selected_item()
        if item is None:
            return
        self.app.push_screen(self._practice_screen(item))

    async def open_practice(self):
        item = self._selected_item()
        if item is None:
            return None
        screen = self._practice_screen(item)
        await self.app.push_screen(screen)
        return screen

    def _practice_screen(self, item):
        from learnloop.tui.screens.practice import PracticeScreen

        return PracticeScreen(self.state, item)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "refresh-button":
            self.action_refresh()
        elif event.button.id == "practice-button":
            self.action_open_selected()

    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        index = event.list_view.index
        if index is not None:
            self.selected_index = max(0, index)
            self._render_details()

    def _render_queue(self) -> None:
        queue = self.query_one("#queue-list", ListView)
        queue.clear()
        if not self.state.queue:
            queue.append(ListItem(Label("No scheduled items.")))
            self._render_empty_details()
            return
        for item in self.state.queue:
            queue.append(ListItem(Label(_queue_label(item))))
        queue.index = min(self.selected_index, len(self.state.queue) - 1)
        self._render_details()

    def _render_details(self) -> None:
        item = self._selected_item()
        if item is None:
            self._render_empty_details()
            return
        practice_item = self.state.vault.practice_items[item.practice_item_id]
        learning_object = self.state.vault.learning_objects[item.learning_object_id]
        self.query_one("#item-title", Static).update(f"{learning_object.title} / {practice_item.id}")
        self.query_one("#item-prompt", Static).update(practice_item.prompt)
        self.query_one("#item-components", Static).update(
            "Components: "
            + ", ".join(f"{key}={value:.3f}" for key, value in sorted(item.components.items()))
        )
        self.query_one("#item-reasons", Static).update("Why: " + "; ".join(item.plain_english))

    def _render_empty_details(self) -> None:
        self.query_one("#item-title", Static).update("No item selected")
        self.query_one("#item-prompt", Static).update("")
        self.query_one("#item-components", Static).update("")
        self.query_one("#item-reasons", Static).update("")

    def _selected_item(self) -> ScheduledItem | None:
        if not self.state.queue:
            return None
        if self.selected_index >= len(self.state.queue):
            self.selected_index = 0
        return self.state.queue[self.selected_index]


def _queue_label(item: ScheduledItem) -> str:
    return f"{item.practice_item_id}  priority={item.priority:.3f}  mode={item.selected_mode}"
