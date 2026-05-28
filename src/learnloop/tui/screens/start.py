from __future__ import annotations

import math
from datetime import UTC, datetime

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.content import Content
from textual.message import Message
from textual.reactive import reactive
from textual.screen import Screen
from textual.widgets import Button, Static

from learnloop.services.scheduler import SchedulerSession
from learnloop.tui.state import TuiState
from learnloop.tui.widgets import KeyBar, TextStatic, block_bar

# Density ramp (dim → bright). ASCII only; the warm tint comes from theme
# tokens, bucketed by luminance (no literal hex — see theme.py).
_RAMP = ".,-~:;=!*#$@"
# luminance bucket → theme token (faint purple → amber → yellow highlight)
_RAMP_TOKENS = ("$text-disabled", "$secondary", "$primary", "$warning")

_TORUS_W = 42
_TORUS_H = 20


class Torus(Static):
    """Rotating shaded ASCII torus (Andy Sloane's donut.c), tinted with theme
    tokens. Re-renders on a timer while the Start screen is visible.
    """

    def __init__(self, **kwargs) -> None:
        super().__init__("", **kwargs)
        self._a = 0.0
        self._b = 0.0

    def on_mount(self) -> None:
        self.set_interval(1 / 12, self._tick)
        self._tick()

    def _tick(self) -> None:
        if not self.is_mounted:
            return
        self.update(self._frame())
        self._a += 0.07
        self._b += 0.03

    def _frame(self) -> Content:
        w, h = _TORUS_W, _TORUS_H
        buffer = [-1] * (w * h)
        zbuffer = [0.0] * (w * h)
        cos_a, sin_a = math.cos(self._a), math.sin(self._a)
        cos_b, sin_b = math.cos(self._b), math.sin(self._b)

        theta = 0.0
        while theta < math.tau:
            cos_t, sin_t = math.cos(theta), math.sin(theta)
            theta += 0.20
            circle_x = 2 + cos_t
            circle_y = sin_t
            phi = 0.0
            while phi < math.tau:
                cos_p, sin_p = math.cos(phi), math.sin(phi)
                phi += 0.07
                x = circle_x * (cos_b * cos_p + sin_a * sin_b * sin_p) - circle_y * cos_a * sin_b
                y = circle_x * (sin_b * cos_p - sin_a * cos_b * sin_p) + circle_y * cos_a * cos_b
                z = 5 + cos_a * circle_x * sin_p + circle_y * sin_a
                ooz = 1 / z
                xp = int(w / 2 + 21 * ooz * x)
                yp = int(h / 2 - 10 * ooz * y)
                if xp < 0 or xp >= w or yp < 0 or yp >= h:
                    continue
                lum = (
                    cos_p * cos_t * sin_b
                    - cos_a * cos_t * sin_p
                    - sin_a * sin_t
                    + cos_b * (cos_a * sin_t - cos_t * sin_a * sin_p)
                )
                if lum <= 0:
                    continue
                idx = xp + w * yp
                if ooz > zbuffer[idx]:
                    zbuffer[idx] = ooz
                    buffer[idx] = min(len(_RAMP) - 1, max(0, int(lum * 8)))

        # Group consecutive same-token runs into styled spans for efficiency.
        spans: list = []
        for row in range(h):
            run_token: str | None = None
            run_chars = ""
            for col in range(w):
                lum_idx = buffer[col + w * row]
                if lum_idx < 0:
                    char, token = " ", None
                else:
                    char = _RAMP[lum_idx]
                    bucket = min(len(_RAMP_TOKENS) - 1, lum_idx * len(_RAMP_TOKENS) // len(_RAMP))
                    token = _RAMP_TOKENS[bucket]
                if token != run_token:
                    if run_chars:
                        spans.append((run_chars, run_token) if run_token else run_chars)
                    run_chars, run_token = "", token
                run_chars += char
            if run_chars:
                spans.append((run_chars, run_token) if run_token else run_chars)
            spans.append("\n")
        return Content.assemble(*spans)


class Slider(Static):
    """Focusable block-fill slider in [0, 1]; ←/→ adjust by 0.1, click to set."""

    can_focus = True
    BINDINGS = [("left", "step(-0.1)", "Lower"), ("right", "step(0.1)", "Raise")]

    _LABEL_W = 14
    _BAR_W = 14

    value: reactive[float] = reactive(0.5)

    class Changed(Message):
        def __init__(self, slider: "Slider") -> None:
            self.slider = slider
            super().__init__()

    def __init__(self, label: str, value: float = 0.5, **kwargs) -> None:
        super().__init__("", **kwargs)
        self._label = label
        self.set_reactive(Slider.value, value)

    def on_mount(self) -> None:
        self.update(self._render())

    def action_step(self, delta: float) -> None:
        self.value = max(0.0, min(1.0, round(self.value + delta, 2)))

    def on_click(self, event) -> None:
        self.focus()
        col = event.x - self._LABEL_W
        value = col / (self._BAR_W - 1) if self._BAR_W > 1 else 0.0
        self.value = max(0.0, min(1.0, round(value, 1)))

    def watch_value(self, _value: float) -> None:
        if self.is_mounted:
            self.update(self._render())
            self.post_message(self.Changed(self))

    def _render(self) -> Content:
        return Content.assemble(
            (f"{self._label:<{self._LABEL_W}}", "$text-disabled"),
            block_bar(self.value, self._BAR_W, "$primary"),
            (f"  {self.value * 10:.1f}", "$text-muted"),
        )


class MinutesPicker(Static):
    """Focusable preset chips for available session minutes; ←/→ cycle."""

    can_focus = True
    BINDINGS = [("left", "step(-1)", "Less"), ("right", "step(1)", "More")]

    _PRESETS = (10, 20, 30, 45, 60)
    index: reactive[int] = reactive(2)

    class Changed(Message):
        def __init__(self, minutes: int) -> None:
            self.minutes = minutes
            super().__init__()

    def __init__(self, minutes: int = 30, **kwargs) -> None:
        super().__init__("", **kwargs)
        start = self._PRESETS.index(minutes) if minutes in self._PRESETS else 2
        self.set_reactive(MinutesPicker.index, start)

    def on_mount(self) -> None:
        self.update(self._render())

    @property
    def minutes(self) -> int:
        return self._PRESETS[self.index]

    def action_step(self, delta: int) -> None:
        self.index = max(0, min(len(self._PRESETS) - 1, self.index + delta))

    def watch_index(self, _index: int) -> None:
        if self.is_mounted:
            self.update(self._render())
            self.post_message(self.Changed(self.minutes))

    def _render(self) -> Content:
        parts: list = []
        for i, preset in enumerate(self._PRESETS):
            if i:
                parts.append("  ")
            label = f" {preset}m "
            if i == self.index:
                parts.append((label, "$text-primary on $primary-muted"))
            else:
                parts.append((label, "$text-muted"))
        return Content.assemble(*parts)


class StartScreen(Screen):
    """Session warm-up: readiness inputs + queue preview, then begin."""

    CSS_PATH = "start.tcss"

    BINDINGS = [
        ("enter", "begin", "Begin session"),
        ("s", "begin", "Skip warm-up"),
        ("p", "postpone", "Postpone 1h"),
        ("q", "quit", "Quit"),
    ]

    def __init__(self, state: TuiState):
        super().__init__()
        self.state = state

    def compose(self) -> ComposeResult:
        with Horizontal(id="warmup-body"):
            with Vertical(id="warmup-left"):
                yield TextStatic(self._left_head(), id="warmup-left-head")
                yield Torus(id="torus")
                yield TextStatic(self._scope_text(), id="warmup-scope")
            with VerticalScroll(id="warmup-right"):
                yield TextStatic(self._intro_text(), id="warmup-intro")
                yield TextStatic("Readiness", classes="section-header")
                yield Slider("energy", 0.7, id="energy")
                yield Slider("sleep quality", 0.5, id="sleep")
                with Horizontal(id="minutes-row"):
                    yield TextStatic("available time", id="minutes-label")
                    yield MinutesPicker(30, id="minutes")
                yield TextStatic(self._mode_text(), id="scheduler-mode")
                yield TextStatic("Today's queue · preview", classes="section-header")
                yield TextStatic(self._queue_preview(), id="queue-preview")
                yield TextStatic(self._recap_text(), id="last-session")
                with Horizontal(id="begin-row"):
                    yield Button("postpone", id="postpone-button")
                    yield Button("begin session ↵", id="begin-button", variant="primary")
        yield KeyBar(
            keys=[
                ("↵", "Begin session"),
                ("←/→", "Adjust"),
                ("p", "Postpone 1h"),
                ("s", "Skip warm-up"),
            ],
        )

    def on_mount(self) -> None:
        self.query_one("#energy", Slider).focus()

    # ── session readiness ──────────────────────────────────────────────────
    def on_slider_changed(self, _event: Slider.Changed) -> None:
        self._refresh_mode()

    def on_minutes_picker_changed(self, _event: MinutesPicker.Changed) -> None:
        self._refresh_mode()

    def _refresh_mode(self) -> None:
        self.query_one("#scheduler-mode", TextStatic).update(self._mode_text())

    def _energy(self) -> float:
        return self.query_one("#energy", Slider).value if self.is_mounted else 0.7

    def _sleep(self) -> float:
        return self.query_one("#sleep", Slider).value if self.is_mounted else 0.5

    def _minutes(self) -> int:
        return self.query_one("#minutes", MinutesPicker).minutes if self.is_mounted else 30

    def _energy_bucket(self) -> str:
        energy = self._energy()
        return "low" if energy < 0.4 else "high" if energy >= 0.75 else "medium"

    def _session(self) -> SchedulerSession:
        return SchedulerSession(available_minutes=self._minutes(), energy=self._energy_bucket())

    # ── navigation ───────────────────────────────────────────────────────────
    async def begin_session(self):
        from learnloop.tui.screens.today import TodayScreen

        self.state.refresh(session=self._session())
        today = TodayScreen(self.state)
        await self.app.push_screen(today)
        return today

    def action_begin(self) -> None:
        self.run_worker(self.begin_session(), exclusive=True)

    def action_postpone(self) -> None:
        self.notify("Session postponed 1h.", severity="information")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "begin-button":
            self.action_begin()
        elif event.button.id == "postpone-button":
            self.action_postpone()

    # ── content builders ───────────────────────────────────────────────────
    def _left_head(self) -> Content:
        now = datetime.now()
        return Content.assemble(
            ("session warm-up\n", "$text-primary underline"),
            (now.strftime("%A · %H:%M"), "$text-muted italic"),
        )

    def _scope_text(self) -> Content:
        goal = self._primary_goal_title()
        concepts = len(self.state.vault.concepts)
        objects = len(self.state.vault.learning_objects)
        return Content.assemble(
            (goal, "$foreground"),
            "\n",
            (f"{concepts} concepts in scope · {objects} active learning_objects", "$text-muted italic"),
        )

    def _intro_text(self) -> Content:
        return Content.assemble(
            ("ready to practice?\n", "$foreground bold"),
            ("tell the scheduler about today; it adjusts the queue, not your goals", "$text-muted italic"),
        )

    def _mode_text(self) -> Content:
        energy = self._energy()
        minutes = self._minutes()
        if energy < 0.4:
            mode = "short_session — probe_eig suppressed"
        elif minutes >= 45:
            mode = "full_loop — probe_eig active"
        else:
            mode = "standard_loop"
        factor = 0.5 * energy + 0.3 * self._sleep() + 0.2 * min(1.0, minutes / 60)
        return Content.assemble(
            ("scheduler mode  ", "$accent bold"),
            (mode, "$text-muted"),
            ("   readiness_factor ", "$text-disabled"),
            (f"{factor:.2f}", "$primary"),
        )

    def _queue_preview(self) -> Content:
        due, probe, later, overdue = self._queue_counts()
        return Content.assemble(
            (f"{due:>2} ", "$primary bold"),
            ("due now    ", "$text-disabled"),
            (f"{probe:>2} ", "$probe bold"),
            ("probe queue\n", "$text-disabled"),
            (f"{later:>2} ", "$text-muted bold"),
            ("later today", "$text-disabled"),
            ("   ", "$text-disabled"),
            (f"{overdue:>2} ", "$success bold"),
            ("overdue >2d", "$text-disabled"),
        )

    def _recap_text(self) -> Content:
        pending = self.state.repository.pending_followup_practice_item_ids()
        if pending:
            return Content.assemble(
                ("last session  ", "$primary"),
                (f"· diagnostic follow-up still queued ({len(pending)})", "$text-muted"),
            )
        return Content.assemble(
            ("last session  ", "$primary"),
            ("· no open follow-ups", "$text-muted"),
        )

    # ── data helpers ─────────────────────────────────────────────────────────
    def _queue_counts(self) -> tuple[int, int, int, int]:
        due = probe = later = 0
        for item in self.state.queue:
            components = item.components
            if components.get("probe_eig", 0.0) > 0.0:
                probe += 1
            elif (
                components.get("forgetting_risk", 0.0) > 0.0
                or components.get("negative_surprise_followup", 0.0) > 0.0
                or components.get("intervention_followup", 0.0) > 0.0
            ):
                due += 1
            else:
                later += 1
        overdue = self._overdue_count()
        return due, probe, later, overdue

    def _overdue_count(self) -> int:
        now = datetime.now(UTC)
        count = 0
        for state in self.state.repository.practice_item_states().values():
            if not state.due_at:
                continue
            try:
                due = datetime.fromisoformat(state.due_at.replace("Z", "+00:00"))
            except ValueError:
                continue
            if due.tzinfo is None:
                due = due.replace(tzinfo=UTC)
            if (now - due).total_seconds() > 2 * 86400:
                count += 1
        return count

    def _primary_goal_title(self) -> str:
        active = [goal for goal in self.state.vault.goals if goal.status == "active"]
        if not active:
            return "—"
        return max(active, key=lambda goal: goal.priority).title
