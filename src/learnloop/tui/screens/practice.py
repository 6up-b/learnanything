from __future__ import annotations

from datetime import UTC, datetime

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.content import Content
from textual.reactive import reactive, var
from textual.screen import Screen
from textual.widgets import Button, Rule, TextArea

from learnloop.attempt_types import default_attempt_type
from learnloop.services.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
from learnloop.services.probe_episodes import (
    commit_item_presentation,
    episode_contract,
    episode_hypothesis_set,
    probe_serving_block_reason,
    stop_diagnosing_and_teach,
)
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

_RATING_CAPS = ["easy", "good", "hard", "again"]
_RATING_CAP_VARIANTS = ["success", "primary", "error", "error"]


class PracticeScreen(Screen):
    """Focused practice card for a single Practice Item.

    Recreates the `LearnLoop Practice Items.html` design: breadcrumb, the
    focused practice card (prompt, answer editor, hints, mastery strip), and a
    "Why this item" scheduler-explanation card. The screen owns no scheduling,
    grading, or mastery logic; it only gathers input and calls the attempt
    service. Appearance lives in `practice.tcss`; state changes flip reactive
    classes rather than rebuilding styling by hand.
    """

    CSS_PATH = "practice.tcss"

    BINDINGS = [
        Binding("ctrl+enter", "submit", "Submit", priority=True),
        Binding("ctrl+j", "submit", "Submit", priority=True),
        Binding("f10", "submit", "Submit", priority=True),
        Binding("ctrl+h", "hint", "Hint", priority=True),
        Binding("ctrl+d", "dont_know", "Don't know", priority=True),
        Binding("ctrl+t", "stop_diagnosing", "Stop diagnosing", priority=True),
        Binding("ctrl+s", "skip", "Skip", priority=True),
        Binding("escape", "back", "Back", priority=True),
    ]

    probe: var[bool] = var(False, toggle_class="-probe")
    submitting: var[bool] = var(False, toggle_class="-submitting")
    hints_used: reactive[int] = reactive(0)

    def __init__(self, state: TuiState, item: ScheduledItem):
        super().__init__()
        self.state = state
        self.item = item
        self.practice_item = state.vault.practice_items[item.practice_item_id]
        self.learning_object = state.vault.learning_objects[item.learning_object_id]
        self.attempt_type = default_attempt_type(self.practice_item.attempt_types_allowed)
        # Probe redesign §12: the same measurement contract the Tauri surface
        # enforces. Committing the presentation is the serve event (§5.1).
        self.probe_contract: dict | None = None
        self.probe_presentation_id: str | None = None
        self._resolve_probe_contract()

    def _resolve_probe_contract(self) -> None:
        repository = self.state.repository
        vault = self.state.vault
        episode = repository.open_probe_episode(self.learning_object.id)
        if episode is None or episode.status != "in_progress":
            return
        # §5.9 orchestration gate (shared with the sidecar): the fresh-vault
        # onboarding ceiling applies here too. The TUI has no session concept,
        # so the per-session cap arm is inert (session_id=None).
        if probe_serving_block_reason(vault, repository) is not None:
            return
        # §5.8 parity with the sidecar: the SAME grading-task routing (with
        # fallback provider) decides whether an approved diagnostic grading
        # provider exists — without one no qualifying observation may be
        # served; the episode parks and the item runs as belief-only practice.
        from learnloop_sidecar.handlers.ai_providers import ready_grading_provider

        _provider, runtime, client = ready_grading_provider(vault)
        if not runtime.ready or client is None:
            repository.update_probe_episode_status(episode.id, status="pending_items")
            return
        hypothesis_set = episode_hypothesis_set(repository, episode)
        if hypothesis_set is None:
            return
        # Shared slate-preferring commit: the presentation carries the same
        # §7.3 selection components and §13.3 shadow rankings as the sidecar.
        presentation = commit_item_presentation(
            vault, repository, episode, self.practice_item, hypothesis_set
        )
        if presentation is None:
            return
        self.probe_presentation_id = presentation.id
        self.probe_contract = episode_contract(vault, repository, self.learning_object.id)

    # ── composition ──────────────────────────────────────────────────────
    def compose(self) -> ComposeResult:
        with VerticalScroll(id="practice-scroll"):
            with Horizontal(id="breadcrumb-row"):
                yield TextStatic(self._breadcrumb_content(), id="breadcrumb-left")
                yield TextStatic(self._breadcrumb_meta_content(), id="breadcrumb-right")

            yield TextStatic("Practice item", id="sec-practice", classes="section-header")

            with Vertical(id="main-card"):
                with Horizontal(id="card-head"):
                    yield TextStatic(self._card_title_content(), id="card-title")
                    yield TextStatic(self._card_pills_content(), id="card-pills")
                yield Rule()
                yield TextStatic(self.practice_item.prompt, id="practice-prompt")
                yield TextStatic(self._probe_content(), id="probe-panel")
                with Horizontal(id="answer-row"):
                    yield TextStatic("❯", id="answer-prompt-char")
                yield TextArea(id="answer-input")
                yield TextStatic("0 chars · 0 words", id="answer-meta")
                yield TextStatic("grading…", id="grading-indicator")
                yield Button("Submit Answer", id="submit-answer")
                yield TextStatic("", id="practice-hints")
                yield Rule()
                yield TextStatic(self._mastery_content(), id="mastery-strip")
                yield TextStatic(self._attempt_row_content(), id="attempt-row")

            yield TextStatic("Why this item", id="sec-why", classes="section-header")
            with Vertical(id="why-card"):
                yield TextStatic(self._why_text_content(), id="why-text")
                yield TextStatic(self._why_metrics_content(), id="why-metrics")

        yield KeyBar(
            keys=[
                ("^enter/^j/F10", "Submit"),
                ("^h", "Hint"),
                ("^d", "Don't know"),
                ("^s", "Skip"),
                ("esc", "Back"),
            ],
        )

    def on_mount(self) -> None:
        self.probe = self._is_probe()
        self.query_one("#answer-input", TextArea).focus()

    def on_screen_resume(self) -> None:
        self.submitting = False

    # ── reactive watchers ──────────────────────────────────────────────────
    def watch_hints_used(self, value: int) -> None:
        self.set_class(value > 0, "-hinted")
        if self.is_mounted:
            self.query_one("#practice-hints", TextStatic).update(self._hints_content())
            self.query_one("#attempt-row", TextStatic).update(self._attempt_row_content())

    # ── tested API ───────────────────────────────────────────────────────
    @property
    def answer(self) -> str:
        return self.query_one("#answer-input", TextArea).text

    def set_answer(self, text: str) -> None:
        self.query_one("#answer-input", TextArea).text = text
        self._refresh_answer_meta(text)

    def reveal_hint(self) -> None:
        if self.probe_presentation_id is not None:
            # §5.5: authored hints are disabled during a diagnostic block.
            self.notify(
                "Hints are disabled during a diagnostic check — answer with what you know, "
                "or press ^t to stop diagnosing and start tutoring.",
                severity="warning",
            )
            return
        if self.hints_used < len(self.practice_item.hints):
            self.hints_used += 1

    async def open_feedback(self):
        from learnloop.tui.screens.feedback import FeedbackScreen

        feedback = FeedbackScreen(self.state, self.item, self._draft())
        await self.app.push_screen(feedback)
        return feedback

    def dont_know(self):
        result = complete_self_graded_attempt(
            self.state.vault,
            self.state.repository,
            self._draft("dont_know"),
            SelfGradeInput(criterion_points={}, confidence=3),
        )
        self.app.last_attempt_result = result
        self.state.refresh()
        self.app.pop_screen()
        return result

    def _draft(self, attempt_type: str | None = None) -> AttemptDraft:
        # §12: an active diagnostic block forces the recording attempt type
        # while declared_dont_know preserves the outcome separately (§5.4).
        declared_dont_know = attempt_type == "dont_know"
        resolved_type = attempt_type or self.attempt_type
        if self.probe_presentation_id is not None:
            resolved_type = "diagnostic_probe"
        return AttemptDraft(
            practice_item_id=self.practice_item.id,
            learner_answer_md=self.answer,
            attempt_type=resolved_type,
            hints_used=self.hints_used,
            probe_presentation_id=self.probe_presentation_id,
            declared_dont_know=declared_dont_know,
        )

    # ── actions ──────────────────────────────────────────────────────────
    async def action_submit(self) -> None:
        self.submitting = True
        await self.open_feedback()

    def action_hint(self) -> None:
        self.reveal_hint()

    def action_stop_diagnosing(self) -> None:
        """`Stop diagnosing and teach me` (§3): end measurement, start tutoring."""

        if self.probe_presentation_id is None:
            return
        stop_diagnosing_and_teach(self.state.vault, self.state.repository, self.learning_object.id)
        self.probe_presentation_id = None
        self.probe_contract = None
        self.probe = False
        if self.is_mounted:
            self.query_one("#probe-panel", TextStatic).update(self._probe_content())
        self.notify("Diagnostic ended — this item now runs as ordinary tutoring/practice.")

    def action_dont_know(self) -> None:
        self.dont_know()

    def action_skip(self) -> None:
        self.app.pop_screen()

    def action_back(self) -> None:
        self.app.pop_screen()

    # ── events ───────────────────────────────────────────────────────────
    def on_text_area_changed(self, event: TextArea.Changed) -> None:
        self._refresh_answer_meta(event.text_area.text)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "submit-answer":
            event.stop()
            self.run_worker(self.action_submit(), exclusive=True)

    def _refresh_answer_meta(self, text: str) -> None:
        if not self.is_mounted:
            return
        words = len([w for w in text.split() if w])
        self.query_one("#answer-meta", TextStatic).update(f"{len(text)} chars · {words} words")

    # ── Content builders ───────────────────────────────────────────────────
    def _breadcrumb_content(self) -> Content:
        return Content.assemble(
            ("today", "$primary underline"),
            (" › ", "$text-disabled"),
            ("practice", "$text-muted"),
            (" › ", "$text-disabled"),
            (self.practice_item.id, "$text"),
        )

    def _breadcrumb_meta_content(self) -> Content:
        index, total = self._queue_position()
        attempt_no = self._attempt_number()
        return Content(
            f"item {index} of {total}  ·  attempt {attempt_no}"
        ).stylize("$text-muted italic")

    def _card_title_content(self) -> Content:
        subject = self._primary_subject()
        return Content.assemble(
            (self.learning_object.title, "$text bold"),
            "\n",
            (f"{self.learning_object.id} · {subject}", "$text-muted italic"),
        )

    def _card_pills_content(self) -> Content:
        mode = self.practice_item.practice_mode
        pills: list[Content] = []
        if self._is_probe():
            pills.append(pill("probe", "probe"))
        pills.append(pill(mode, mode_pill_color(mode)))
        return _join(pills)

    def _probe_content(self) -> Content:
        if self.probe_contract is not None:
            observation = self.probe_contract.get("observation_number", 1)
            maximum = self.probe_contract.get("maximum_observations", 4)
            return Content.assemble(
                (f"Diagnostic · observation {observation} of up to {maximum}", "$probe bold"),
                "\n",
                (
                    "feedback is delayed for measurement integrity · hints and ask-tutor are "
                    "unavailable · ^t stops diagnosing and starts tutoring",
                    "$text-muted italic",
                ),
            )
        eig = self.item.components.get("probe_eig", 0.0)
        return Content.assemble(
            ("Probe phase · hypothesis set locked", "$probe bold"),
            "\n",
            (
                f"item selected by probe-EIG · information gain {eig:.2f}",
                "$text-muted italic",
            ),
        )

    def _hints_content(self) -> Content:
        hints = self.practice_item.hints
        if self.hints_used == 0:
            return Content("")
        total = len(hints)
        items: list = []
        for i, hint in enumerate(hints[: self.hints_used]):
            if i:
                items.append("\n")
            items.append(pill(f"hint {i + 1}/{total}", "primary"))
            items.append(" ")
            items.append((hint, "$text"))
        return Content.assemble(*items)

    def _mastery_content(self) -> Content:
        difficulty = self._difficulty()
        mean, sd = self._mastery_mean_sd()
        facets = self.practice_item.evidence_facets or []
        if facets:
            facets_part = (" · ".join(facets), "$accent")
        else:
            facets_part = ("—", "$text-disabled")
        return Content.assemble(
            ("difficulty  ", "$text-disabled"),
            block_bar(difficulty, 6, "$primary"),
            (f" {difficulty:.2f}", "$text-muted"),
            ("     mastery  ", "$text-disabled"),
            block_bar(mean, 6, mastery_token(mean)),
            (f" {mean:.2f} ", "$text-muted"),
            (f"±{sd:.2f}", "$text-disabled"),
            ("     facets  ", "$text-disabled"),
            facets_part,
        )

    def _attempt_row_content(self) -> Content:
        allowed = self.practice_item.attempt_types_allowed or ["independent_attempt"]
        type_pills = _join(
            [pill(name, "primary" if name == self.attempt_type else "slate") for name in allowed]
        )
        total_hints = len(self.practice_item.hints)
        cap_idx = min(3, self.hints_used)
        cap_pill = pill(_RATING_CAPS[cap_idx], _RATING_CAP_VARIANTS[cap_idx])
        return Content.assemble(
            ("attempt type  ", "$text-disabled"),
            type_pills,
            ("     hints used ", "$text-disabled"),
            (f"{self.hints_used} / {total_hints}", "$text-muted"),
            ("     rating cap ", "$text-disabled"),
            cap_pill,
        )

    def _why_text_content(self) -> Content:
        reasons = "; ".join(self.item.plain_english) if self.item.plain_english else "scheduled for review"
        now_hhmm = datetime.now().strftime("%H:%M")
        return Content.assemble(
            ("Highest priority in the queue at ", "$text"),
            (now_hhmm, "$text-muted"),
            (". ", "$text"),
            (reasons, "$primary"),
        )

    def _why_metrics_content(self) -> Content:
        state = self.state.repository.practice_item_states().get(self.practice_item.id)
        now = datetime.now(UTC)
        retr = f"{state.retrievability:.2f}" if state and state.retrievability is not None else "—"
        stab = f"{state.stability:.1f}d" if state and state.stability is not None else "—"
        last = _relative(state.last_attempt_at, now) if state and state.last_attempt_at else "never"
        due = _relative(state.due_at, now) if state and state.due_at else "—"
        version = self.state.vault.config.algorithms.algorithm_version
        return Content.assemble(
            ("R(t) ", "$text-disabled"),
            (retr, "$text-muted"),
            ("     stability ", "$text-disabled"),
            (stab, "$text-muted"),
            ("     last attempt ", "$text-disabled"),
            (last, "$text-muted"),
            ("     next due ", "$text-disabled"),
            (due, "$text-muted"),
            ("     FSRS-6 ", "$text-disabled"),
            (f"· alg {version}", "$text-muted"),
        )

    # ── data helpers ─────────────────────────────────────────────────────
    def _is_probe(self) -> bool:
        if self.probe_presentation_id is not None:
            return True
        return self.item.components.get("probe_eig", 0.0) > 0.0

    def _primary_subject(self) -> str:
        subjects = self.state.vault.subjects_for_item(self.practice_item)
        return subjects[0] if subjects else "—"

    def _difficulty(self) -> float:
        if self.practice_item.difficulty is not None:
            return self.practice_item.difficulty
        state = self.state.repository.practice_item_states().get(self.practice_item.id)
        if state and state.difficulty is not None:
            return state.difficulty
        if self.learning_object.difficulty_prior is not None:
            return self.learning_object.difficulty_prior
        return 0.5

    def _mastery_mean_sd(self) -> tuple[float, float]:
        state = self.state.repository.mastery_states().get(self.learning_object.id)
        if state is None:
            return 0.5, 0.25
        mean = sigmoid(state.logit_mean)
        variance = (mean * (1 - mean)) ** 2 * state.logit_variance
        return mean, variance**0.5

    def _queue_position(self) -> tuple[int, int]:
        queue = self.state.queue
        total = len(queue) or 1
        for idx, scheduled in enumerate(queue):
            if scheduled.practice_item_id == self.practice_item.id:
                return idx + 1, total
        return 1, total

    def _attempt_number(self) -> int:
        prior = self.state.repository.list_recent_attempts_by_practice_item(
            self.practice_item.id, limit=1000
        )
        return len(prior) + 1


def _join(parts: list[Content], sep: str = " ") -> Content:
    items: list = []
    for i, part in enumerate(parts):
        if i:
            items.append(sep)
        items.append(part)
    return Content.assemble(*items)


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
