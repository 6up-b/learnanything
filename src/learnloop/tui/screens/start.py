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

from learnloop.scheduling.scheduler import SchedulerSession
from learnloop.scheduling.session_minutes import minute_choices, remembered_session_minutes
from learnloop.tui.state import TuiState
from learnloop.tui.widgets import KeyBar, TextStatic

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


class MinutesPicker(Static):
    """Focusable one-tap minute chips; ←/→ cycle (daily-loop §6.6).

    The chips are the presets plus the remembered value when it isn't one, so
    the minutes Begin uses are always the selected, visible chip.
    """

    can_focus = True
    BINDINGS = [("left", "step(-1)", "Less"), ("right", "step(1)", "More")]

    index: reactive[int] = reactive(0)
    _SEPARATOR = " "

    class Changed(Message):
        def __init__(self, minutes: int) -> None:
            self.minutes = minutes
            super().__init__()

    def __init__(self, minutes: int, **kwargs) -> None:
        super().__init__("", **kwargs)
        self._choices = minute_choices(minutes)
        self.set_reactive(MinutesPicker.index, self._choices.index(minutes))

    def on_mount(self) -> None:
        self.update(self._render())

    @property
    def choices(self) -> tuple[int, ...]:
        return self._choices

    @property
    def minutes(self) -> int:
        return self._choices[self.index]

    def action_step(self, delta: int) -> None:
        self.index = max(0, min(len(self._choices) - 1, self.index + delta))

    def on_click(self, event) -> None:
        # One tap: map the click column onto the chip under it.
        self.focus()
        column = 0
        for i, preset in enumerate(self._choices):
            width = len(f" {preset}m ")
            if column <= event.x < column + width:
                self.index = i
                return
            column += width + len(self._SEPARATOR)

    def watch_index(self, _index: int) -> None:
        if self.is_mounted:
            self.update(self._render())
            self.post_message(self.Changed(self.minutes))

    def _render(self) -> Content:
        parts: list = []
        for i, preset in enumerate(self._choices):
            if i:
                parts.append(self._SEPARATOR)
            label = f" {preset}m "
            if i == self.index:
                parts.append((label, "$text-primary on $primary-muted"))
            else:
                parts.append((label, "$text-muted"))
        return Content.assemble(*parts)


class StartScreen(Screen):
    """Session warm-up: minutes only, a queue preview, then begin.

    Daily-loop DL0 (§6.6): no readiness form. The minutes default to the last
    session's (25 on a fresh vault) and change with one tap.
    """

    CSS_PATH = "start.tcss"

    BINDINGS = [
        ("enter", "begin", "Begin session"),
        ("s", "begin", "Skip warm-up"),
        ("q", "quit", "Quit"),
    ]

    def __init__(self, state: TuiState):
        super().__init__()
        self.state = state
        self.remembered_minutes = remembered_session_minutes(state.repository)

    def compose(self) -> ComposeResult:
        with Horizontal(id="warmup-body"):
            with Vertical(id="warmup-left"):
                yield TextStatic(self._left_head(), id="warmup-left-head")
                yield Torus(id="torus")
                yield TextStatic(self._scope_text(), id="warmup-scope")
            with VerticalScroll(id="warmup-right"):
                yield TextStatic(self._intro_text(), id="warmup-intro")
                yield TextStatic("Time today", classes="section-header")
                with Horizontal(id="minutes-row"):
                    yield TextStatic("available time", id="minutes-label")
                    yield MinutesPicker(self.remembered_minutes.minutes, id="minutes")
                yield TextStatic(self._mode_text(), id="scheduler-mode")
                yield TextStatic("Today's queue · preview", classes="section-header")
                yield TextStatic(self._queue_preview(), id="queue-preview")
                yield TextStatic(self._recap_text(), id="last-session")
                # No "postpone": nothing can defer a session (no reminder or
                # deferred start), so the control would only claim one.
                with Horizontal(id="begin-row"):
                    yield Button("begin session ↵", id="begin-button", variant="primary")
        yield KeyBar(
            keys=[
                ("↵", "Begin session"),
                ("←/→", "Minutes"),
                ("s", "Skip warm-up"),
            ],
        )

    def on_mount(self) -> None:
        self.query_one("#minutes", MinutesPicker).focus()

    # ── session minutes ────────────────────────────────────────────────────
    def on_minutes_picker_changed(self, _event: MinutesPicker.Changed) -> None:
        self._refresh_mode()

    def _refresh_mode(self) -> None:
        self.query_one("#scheduler-mode", TextStatic).update(self._mode_text())

    def _minutes(self) -> int:
        if self.is_mounted:
            return self.query_one("#minutes", MinutesPicker).minutes
        return self.remembered_minutes.minutes

    def _session(self) -> SchedulerSession:
        # Minutes only: no energy is asked for or sent (the scheduler logs None).
        return SchedulerSession(available_minutes=self._minutes())

    # ── navigation ───────────────────────────────────────────────────────────
    async def begin_session(self):
        from learnloop.tui.screens.today import TodayScreen

        session = self._session()
        self.state.available_minutes = session.available_minutes
        self.state.refresh(session=session)
        today = TodayScreen(self.state)
        await self.app.push_screen(today)
        return today

    def action_begin(self) -> None:
        self.run_worker(self.begin_session(), exclusive=True)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "begin-button":
            self.action_begin()

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
        if self.remembered_minutes.source == "last_session":
            note = "minutes from your last session; one tap changes them"
        else:
            note = "pick today's minutes; they are remembered next time"
        return Content.assemble(
            ("ready to practice?\n", "$foreground bold"),
            (note, "$text-muted italic"),
        )

    def _mode_text(self) -> Content:
        # Mirrors the scheduler's actual rule: probe_eig is suppressed when
        # available_minutes <= scheduler.short_session_minutes.
        minutes = self._minutes()
        short_minutes = self.state.vault.config.scheduler.short_session_minutes
        if minutes <= short_minutes:
            mode = f"short_session — probe_eig suppressed (≤{short_minutes} min)"
        elif minutes >= 45:
            mode = "full_loop — probe_eig active"
        else:
            mode = "standard_loop — probe_eig active"
        return Content.assemble(
            ("scheduler mode  ", "$accent bold"),
            (mode, "$text-muted"),
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
