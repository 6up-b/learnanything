from __future__ import annotations

from datetime import UTC, datetime

from textual.app import ComposeResult
from textual.containers import Grid, VerticalScroll
from textual.content import Content
from textual.message import Message
from textual.reactive import var
from textual.screen import Screen

from learnloop.services.mastery import sigmoid
from learnloop.services.scheduler import ScheduledItem
from learnloop.tui.state import TuiState
from learnloop.tui.widgets import (
    KeyBar,
    TextStatic,
    block_bar,
    mastery_token,
    mode_pill_color,
    pill,
)


def _is_followup(components: dict[str, float]) -> bool:
    return (
        components.get("negative_surprise_followup", 0.0) > 0.0
        or components.get("intervention_followup", 0.0) > 0.0
    )


class PracticeCard(TextStatic):
    """A single queue item rendered as a bordered card (one Content block).

    The card carries its flat-queue index so the screen can map clicks and
    keyboard focus back to the underlying ScheduledItem.
    """

    class Selected(Message):
        def __init__(self, index: int, *, open_item: bool) -> None:
            self.index = index
            self.open_item = open_item
            super().__init__()

    def __init__(self, content: Content, index: int, **kwargs) -> None:
        super().__init__(content, **kwargs)
        self.index = index

    def on_click(self) -> None:
        self.post_message(self.Selected(self.index, open_item=True))


class TodayScreen(Screen):
    CSS_PATH = "today.tcss"

    BINDINGS = [
        ("j", "move(1)", "Move down"),
        ("down", "move(1)", "Move down"),
        ("k", "move(-1)", "Move up"),
        ("up", "move(-1)", "Move up"),
        ("enter", "open_selected", "Practice"),
        ("l", "open_selected", "Practice"),
        ("right", "open_selected", "Practice"),
        ("r", "refresh", "Refresh"),
        *[(str(n), f"quick_open({n})", "Quick open") for n in range(1, 10)],
    ]

    empty: var[bool] = var(False, toggle_class="-empty")
    inserted_followup: var[bool] = var(False, toggle_class="-inserted")

    def __init__(self, state: TuiState):
        super().__init__()
        self.state = state
        self.selected_index = 0
        # Flat, priority-ordered list of items parallel to the rendered cards.
        self._items: list[ScheduledItem] = []
        self._cards: list[PracticeCard] = []

    def compose(self) -> ComposeResult:
        with VerticalScroll(id="today-scroll"):
            yield TextStatic(self._header_content(), id="today-header")
            yield TextStatic(self._status_content(), id="today-status")
            yield TextStatic(self._banner_content(), id="surprise-banner")
            yield TextStatic(self._summary_content(), id="today-summary")
            yield Grid(id="card-grid")
            yield TextStatic(self._why_order_content(), id="why-order")
        yield KeyBar(
            keys=[
                ("j/k", "Move"),
                ("enter", "Practice"),
                ("1-9", "Quick open"),
                ("r", "Refresh"),
            ],
        )

    def on_mount(self) -> None:
        self._render_queue()

    def on_screen_resume(self) -> None:
        self.selected_index = 0
        self.state.refresh()
        self._render_queue()

    # ── actions ──────────────────────────────────────────────────────────────
    def action_refresh(self) -> None:
        self.state.refresh()
        self.selected_index = 0
        self._render_queue()

    def action_move(self, delta: int) -> None:
        if not self._items:
            return
        self.selected_index = max(0, min(len(self._items) - 1, self.selected_index + delta))
        self._mark_focused()

    def action_open_selected(self) -> None:
        item = self._selected_item()
        if item is None:
            return
        self.app.push_screen(self._practice_screen(item))

    def action_quick_open(self, n: int) -> None:
        index = n - 1
        if 0 <= index < len(self._items):
            self.selected_index = index
            self._mark_focused()
            self.action_open_selected()

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

    def on_practice_card_selected(self, event: PracticeCard.Selected) -> None:
        self.selected_index = event.index
        self._mark_focused()
        if event.open_item:
            self.action_open_selected()

    # ── rendering ──────────────────────────────────────────────────────────
    def _render_queue(self) -> None:
        grid = self.query_one("#card-grid", Grid)
        grid.remove_children()
        self._items = []
        self._cards = []

        if not self.state.queue:
            self.empty = True
            self.inserted_followup = False
            grid.mount(TextStatic("No scheduled items.", id="empty-state"))
            self._refresh_static_panels()
            return

        self.empty = False
        index = 0
        followup_present = False
        widgets: list = []
        for title, items in self._grouped():
            widgets.append(TextStatic(title, classes="section-header card-grid-header"))
            for item in items:
                inserted = _is_followup(item.components)
                followup_present = followup_present or inserted
                card = PracticeCard(
                    self._card_content(item, index, inserted),
                    index,
                    classes="practice-card",
                )
                if inserted:
                    card.add_class("-inserted-card")
                widgets.append(card)
                self._cards.append(card)
                self._items.append(item)
                index += 1
        grid.mount(*widgets)

        self.inserted_followup = followup_present
        self.selected_index = min(self.selected_index, len(self._items) - 1)
        self._mark_focused()
        self._refresh_static_panels()

    def _refresh_static_panels(self) -> None:
        self.query_one("#today-summary", TextStatic).update(self._summary_content())
        self.query_one("#surprise-banner", TextStatic).update(self._banner_content())
        self.query_one("#why-order", TextStatic).update(self._why_order_content())
        self.query_one("#today-status", TextStatic).update(self._status_content())

    def _grouped(self) -> list[tuple[str, list[ScheduledItem]]]:
        """Presentation grouping over the flat priority queue (scheduler order
        is unchanged). Precedence: probe → due-now → later.
        """
        probe: list[ScheduledItem] = []
        due: list[ScheduledItem] = []
        later: list[ScheduledItem] = []
        for item in self.state.queue:
            components = item.components
            if components.get("probe_eig", 0.0) > 0.0:
                probe.append(item)
            elif (
                components.get("forgetting_risk", 0.0) > 0.0
                or _is_followup(components)
            ):
                due.append(item)
            else:
                later.append(item)
        sections: list[tuple[str, list[ScheduledItem]]] = []
        if due:
            sections.append(("Due now", due))
        if probe:
            sections.append(("Probe queue", probe))
        if later:
            sections.append(("Later today", later))
        return sections

    def _mark_focused(self) -> None:
        for card in self._cards:
            card.set_class(card.index == self.selected_index, "-focused")

    def _selected_item(self) -> ScheduledItem | None:
        if 0 <= self.selected_index < len(self._items):
            return self._items[self.selected_index]
        return self._items[0] if self._items else None

    # ── content builders ───────────────────────────────────────────────────
    def _header_content(self) -> Content:
        version = self.state.vault.config.algorithms.algorithm_version
        return Content.assemble(
            ("🌀 LearnLoop ", "$foreground bold"),
            pill(f"alg {version}", "secondary"),
            "\n",
            ("A local learning vault for goal-tied practice in the terminal", "$success"),
        )

    def _status_content(self) -> Content:
        goal = self._primary_goal_title()
        provider_name, ai_ready = self._ai_status()
        return Content.assemble(
            ("Goal ", "$text-muted"),
            (goal, "$text-primary underline"),
            ("    Vault ", "$text-muted"),
            (str(self.state.vault_root), "$success"),
            ("    AI ", "$text-muted"),
            (provider_name, "$text-muted"),
            " ",
            ("● ready" if ai_ready else "○ unavailable", "$success" if ai_ready else "$text-disabled"),
        )

    def _summary_content(self) -> Content:
        due, probe, later = self._section_counts()
        total = due + probe + later
        return Content(
            f"{total} items, {probe} probe, {self._budget()} min budget — your queue:"
        ).stylize("$text-muted italic")

    def _banner_content(self) -> Content:
        followup = self._followup_item()
        if followup is None:
            return Content("")
        item, scheduled = followup
        return Content.assemble(
            ("+1  diagnostic follow-up inserted at position 1  ", "$primary bold"),
            pill("intervention gate", "warning"),
            "\n",
            ("A diagnostic follow-up on ", "$text-muted"),
            (item.learning_object_id, "$text"),
            (" was queued after an intervention trigger  ·  follow-up ", "$text-muted"),
            (scheduled.practice_item_id, "$text-primary"),
        )

    def _why_order_content(self) -> Content:
        item = self._selected_item()
        if item is None:
            return Content("")
        parts: list = [("why this order  ", "$primary")]
        terms = [(key, value) for key, value in sorted(item.components.items()) if value]
        if not terms:
            parts.append(("scheduled for review", "$text-muted"))
        else:
            for i, (key, value) in enumerate(terms):
                if i:
                    parts.append((" + ", "$text-disabled"))
                parts.append((f"{key} × {value:.2f}", "$text-muted"))
        parts.append(("  ·  press ", "$text-disabled"))
        parts.append(("?", "$primary"))
        parts.append((" for the per-item breakdown", "$text-disabled"))
        return Content.assemble(*parts)

    def _card_content(self, item: ScheduledItem, index: int, inserted: bool) -> Content:
        practice_item = self.state.vault.practice_items[item.practice_item_id]
        learning_object = self.state.vault.learning_objects[item.learning_object_id]
        subject = self._subject(practice_item)
        mode = practice_item.practice_mode
        mastery = self._mastery(item.learning_object_id)
        due = self._due_offset(item.practice_item_id)
        hotkey = str(index + 1) if index < 9 else "·"

        title_row: list = [(learning_object.title, "$text bold")]
        if item.components.get("probe_eig", 0.0) > 0.0:
            title_row.append(" ")
            title_row.append(pill("probe", "probe"))
        if inserted:
            title_row.append(" ")
            title_row.append(pill("intervention", "warning"))
        title_row.append("  ")
        title_row.append(pill(mode, mode_pill_color(mode)))

        prompt_preview = _clip(practice_item.prompt, 200)
        return Content.assemble(
            Content.assemble(*title_row),
            "\n",
            (f"{practice_item.id} · {subject}", "$text-muted italic"),
            "\n\n",
            (prompt_preview, "$text"),
            "\n\n",
            ("mastery ", "$text-disabled"),
            block_bar(mastery, 8, mastery_token(mastery)),
            (f" {mastery:.2f}", "$text-muted"),
            ("     due ", "$text-disabled"),
            (due, "$primary" if "ago" in due else "$text-muted"),
            (f"     [{hotkey}]", "$text-disabled"),
        )

    # ── data helpers ─────────────────────────────────────────────────────────
    def _section_counts(self) -> tuple[int, int, int]:
        due = probe = later = 0
        for item in self.state.queue:
            components = item.components
            if components.get("probe_eig", 0.0) > 0.0:
                probe += 1
            elif (
                components.get("forgetting_risk", 0.0) > 0.0
                or _is_followup(components)
            ):
                due += 1
            else:
                later += 1
        return due, probe, later

    def _followup_item(self) -> tuple[object, ScheduledItem] | None:
        for scheduled in self.state.queue:
            if _is_followup(scheduled.components):
                return scheduled, scheduled
        return None

    def _budget(self) -> int:
        for item in self.state.queue:
            if item.readiness_factor is not None:
                short = self.state.vault.config.scheduler.short_session_minutes
                return max(short, round(item.readiness_factor * 30))
        return self.state.vault.config.scheduler.short_session_minutes

    def _subject(self, practice_item) -> str:
        subjects = self.state.vault.subjects_for_item(practice_item)
        return subjects[0] if subjects else "—"

    def _mastery(self, learning_object_id: str) -> float:
        state = self.state.repository.mastery_states().get(learning_object_id)
        if state is None:
            return 0.5
        return sigmoid(state.logit_mean)

    def _due_offset(self, practice_item_id: str) -> str:
        state = self.state.repository.practice_item_states().get(practice_item_id)
        if state is None or not state.due_at:
            return "—"
        return _relative(state.due_at, datetime.now(UTC))

    def _primary_goal_title(self) -> str:
        active = [goal for goal in self.state.vault.goals if goal.status == "active"]
        if not active:
            return "—"
        return max(active, key=lambda goal: goal.priority).title

    def _ai_status(self) -> tuple[str, bool]:
        maintenance = self.state.startup_maintenance
        if maintenance and maintenance.ai_runtime is not None:
            return maintenance.ai_runtime.active_provider, maintenance.ai_runtime.ready
        runtime = maintenance.codex_runtime if maintenance else None
        return "codex", bool(runtime and runtime.ready)


def _clip(text: str, limit: int) -> str:
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def _relative(iso: str, now: datetime) -> str:
    try:
        moment = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return iso
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=UTC)
    delta = (moment - now).total_seconds()
    future = delta >= 0
    seconds = abs(delta)
    if seconds < 60:
        return "now"
    if seconds < 3600:
        magnitude = f"{int(seconds // 60)}m"
    elif seconds < 86400:
        magnitude = f"{int(seconds // 3600)}h"
    else:
        magnitude = f"{int(seconds // 86400)}d"
    return f"in {magnitude}" if future else f"{magnitude} ago"
