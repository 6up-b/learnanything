from __future__ import annotations

import asyncio

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.content import Content
from textual.reactive import reactive
from textual.screen import Screen
from textual.widgets import Button, Input, Label

from learnloop.ai.client import make_ai_provider_client
from learnloop.ai.routing import fallback_provider_for, provider_for_task
from learnloop.ai.runtime import check_ai_runtime
from learnloop.codex.client import CodexUnavailable, make_codex_client
from learnloop.codex.runtime import check_codex_runtime
from learnloop.config import (
    CODEX_LOW_PROVIDER,
    CODEX_MEDIUM_PROVIDER,
    CODEX_PROVIDER_NAMES,
    DEFAULT_CODEX_MODEL,
)
from learnloop.services.attempts import (
    AttemptDraft,
    AttemptResult,
    SelfGradeInput,
    complete_attempt_with_ai_fallback,
    complete_attempt_with_ai_required,
    complete_attempt_with_codex_fallback,
    complete_attempt_with_codex_required,
)
from learnloop.services.followups import FollowupDecision, evaluate_attempt_intervention_followup
from learnloop.services.mastery import sigmoid
from learnloop.services.scheduler import ScheduledItem
from learnloop.tui.state import TuiState
from learnloop.tui.widgets import KeyBar, TextStatic, block_bar, mode_pill_color, pill

_RATING_PILL = {"easy": "success", "good": "primary", "hard": "warning", "again": "error"}


class FeedbackScreen(Screen):
    """Grade an attempt, then show the prototype's read-only results display.

    Grading still happens here (AI auto-grade, or the self-grade form as a
    fallback / tested surface). Once a result exists the screen flips to a
    `-graded` state: the form is hidden and the score / rubric evidence / error
    attributions / belief update / next-action sections are revealed. The screen
    owns no grading or scheduling logic of its own; appearance lives in
    `feedback.tcss` and state changes flip reactive classes.
    """

    CSS_PATH = "feedback.tcss"

    BINDINGS = [
        ("ctrl+s", "submit", "Submit grade"),
        ("n", "next", "Next item"),
        ("escape", "back", "Back"),
    ]

    surprise_direction: reactive[str | None] = reactive(None)
    graded: reactive[bool] = reactive(False)
    has_errors: reactive[bool] = reactive(False)

    def __init__(self, state: TuiState, item: ScheduledItem, draft: AttemptDraft):
        super().__init__()
        self.state = state
        self.item = item
        self.draft = draft
        self.practice_item = state.vault.practice_items[item.practice_item_id]
        self.learning_object = state.vault.learning_objects[item.learning_object_id]
        self.rubric = state.vault.rubric_for_item(self.practice_item)
        self.criterion_points: dict[str, float] = (
            {criterion.id: 0.0 for criterion in self.rubric.criteria} if self.rubric else {}
        )
        self.fatal_errors: list[str] = []
        self.error_type: str | None = None
        self.confidence: int = 3
        self.result: AttemptResult | None = None
        self.followup_decision: FollowupDecision | None = None
        self.available_minutes: int | None = None
        # Mastery posterior captured before this attempt is graded.
        self.pre_mastery: tuple[float, float] = self._mastery_mean_sd()

    def compose(self) -> ComposeResult:
        expected = self.practice_item.expected_answer
        with VerticalScroll(id="feedback-layout"):
            yield TextStatic(self._breadcrumb_content(), id="fb-breadcrumb")
            yield TextStatic("Feedback", id="feedback-title", classes="section-header")
            yield TextStatic(
                Content("An intervention follow-up has been scheduled."),
                id="negative-surprise-banner",
            )

            # ── results (revealed once graded) ────────────────────────────
            with Vertical(id="results"):
                yield TextStatic("", id="result-head")
                yield TextStatic("", id="score-block")
                yield TextStatic("Rubric · criterion evidence", classes="section-header")
                yield TextStatic("", id="rubric-evidence")
                yield TextStatic("", id="tutor-note")
                yield TextStatic("Error attribution", classes="section-header", id="error-header")
                yield TextStatic("", id="error-attributions")
                yield TextStatic("Belief update", classes="section-header")
                yield TextStatic("", id="belief-update")
                yield TextStatic("What's next", classes="section-header")
                with Horizontal(id="next-row"):
                    yield TextStatic("", id="next-followup")
                    yield TextStatic("", id="next-schedule")

            # ── self-grade form (hidden once graded) ──────────────────────
            with Vertical(id="grade-form"):
                yield TextStatic(
                    Content.assemble(("Expected: ", "$text-disabled"), (expected, "$foreground")),
                    id="expected-answer",
                )
                yield TextStatic("", id="grading-status")
                yield TextStatic(self._rubric_content(), id="rubric")
                if self.rubric is not None:
                    for criterion in self.rubric.criteria:
                        yield Label(f"{criterion.id} points (0-{criterion.points:g})")
                        yield Input(
                            value=str(self.criterion_points[criterion.id]),
                            id=f"criterion-{criterion.id}",
                        )
                    if self.rubric.fatal_errors:
                        yield Label("Fatal errors")
                        for fatal in self.rubric.fatal_errors:
                            yield Button(fatal.id, id=f"fatal-{fatal.id}", classes="fatal-toggle")
                        yield TextStatic("Fatal errors: none", id="fatal-summary")
                yield Label("Confidence (1-5)")
                yield Input(value=str(self.confidence), id="confidence-input")
                yield Label("Error type")
                yield Input(value="", placeholder="Optional error type", id="error-type-input")
                yield TextStatic("", id="feedback-summary")
                yield Button("Submit grade", id="grade-button")

            yield Button("Back to today", id="today-button")
        yield KeyBar(keys=[("n / enter", "Next item"), ("esc", "Back to queue")])

    def on_mount(self) -> None:
        if self._ai_ready():
            self.query_one("#grading-status", TextStatic).update(
                Content(f"Sending answer to {self._provider_label()} for evaluation...")
            )
            self.run_worker(self.auto_submit_ai(), exclusive=True)
        else:
            self.query_one("#grading-status", TextStatic).update(
                Content("AI grading is unavailable. Enter a self-grade below.")
            )

    # ── reactive watchers ──────────────────────────────────────────────────
    def watch_surprise_direction(self, value: str | None) -> None:
        self.set_class(value == "negative", "-negative-surprise")

    def watch_graded(self, value: bool) -> None:
        self.set_class(value, "-graded")

    def watch_has_errors(self, value: bool) -> None:
        self.set_class(value, "-has-errors")

    def _rubric_content(self) -> Content:
        if self.rubric is None:
            return Content("No rubric.")
        items: list = [(f"max_points={self.rubric.max_points}", "$text-muted")]
        for criterion in self.rubric.criteria:
            items.append("\n")
            items.append(
                (f"- {criterion.id} (max {criterion.points:g}): {criterion.description}", "$text-muted")
            )
        for fatal in self.rubric.fatal_errors:
            items.append("\n")
            items.append((f"! fatal {fatal.id} caps at {fatal.max_grade}", "$text-error"))
        return Content.assemble(*items)

    def set_points(self, criterion_id: str, points: float) -> None:
        self.criterion_points[criterion_id] = float(points)
        if self.is_mounted:
            self.query_one(f"#criterion-{criterion_id}", Input).value = f"{float(points):g}"

    def set_confidence(self, confidence: int) -> None:
        self.confidence = int(confidence)
        if self.is_mounted:
            self.query_one("#confidence-input", Input).value = str(self.confidence)

    def set_error_type(self, error_type: str | None) -> None:
        self.error_type = error_type
        if self.is_mounted:
            self.query_one("#error-type-input", Input).value = error_type or ""

    def toggle_fatal(self, fatal_error_id: str) -> None:
        if fatal_error_id in self.fatal_errors:
            self.fatal_errors.remove(fatal_error_id)
        else:
            self.fatal_errors.append(fatal_error_id)
        if self.is_mounted:
            button = self.query_one(f"#fatal-{fatal_error_id}", Button)
            button.set_class(fatal_error_id in self.fatal_errors, "-on")
            self._render_fatal_summary()

    def submit(self) -> AttemptResult:
        if self.result is not None:
            return self.result
        self._read_form_state()
        provider_name, runtime, client = self._grading_provider()
        self_grade = SelfGradeInput(
            criterion_points=self.criterion_points,
            confidence=self.confidence,
            fatal_errors=self.fatal_errors or None,
            error_type=self.error_type,
        )
        if provider_name in CODEX_PROVIDER_NAMES:
            result = complete_attempt_with_codex_fallback(
                self.state.vault,
                self.state.repository,
                self.draft,
                self_grade,
                runtime=runtime,
                codex_client=client,
            )
        else:
            result = complete_attempt_with_ai_fallback(
                self.state.vault,
                self.state.repository,
                self.draft,
                self_grade,
                runtime=runtime,
                ai_client=client,
            )
        self._complete_result(result)
        return result

    async def auto_submit_ai(self) -> AttemptResult | None:
        if self.result is not None:
            return self.result
        provider_name, runtime, client = self._grading_provider()
        if not runtime.ready or client is None:
            self.query_one("#grading-status", TextStatic).update(
                Content("AI grading is unavailable. Enter a self-grade below.")
            )
            return None
        try:
            if provider_name in CODEX_PROVIDER_NAMES:
                result = await asyncio.to_thread(
                    complete_attempt_with_codex_required,
                    self.state.vault,
                    self.state.repository,
                    self.draft,
                    runtime=runtime,
                    codex_client=client,
                )
            else:
                result = await asyncio.to_thread(
                    complete_attempt_with_ai_required,
                    self.state.vault,
                    self.state.repository,
                    self.draft,
                    runtime=runtime,
                    ai_client=client,
                )
        except Exception as exc:
            self.query_one("#grading-status", TextStatic).update(
                Content(f"AI grading failed: {type(exc).__name__}. Enter a self-grade below.")
            )
            return None
        self._complete_result(result)
        return result

    async def auto_submit_codex(self) -> AttemptResult | None:
        return await self.auto_submit_ai()

    def _grading_provider(self):
        selection = provider_for_task(self.state.vault.config, "grading")
        provider_name = selection.provider_name
        runtime = self._runtime_for_provider(provider_name)
        if runtime.ready:
            return provider_name, runtime, self._client_for_provider(provider_name)
        fallback = fallback_provider_for(self.state.vault.config, selection)
        if fallback:
            fallback_runtime = self._runtime_for_provider(fallback)
            if fallback_runtime.ready:
                return fallback, fallback_runtime, self._client_for_provider(fallback)
        return provider_name, runtime, None

    def _codex_config_for_provider(self, provider_name: str):
        if provider_name not in {CODEX_LOW_PROVIDER, CODEX_MEDIUM_PROVIDER}:
            return self.state.vault.config.codex
        effort = "low" if provider_name == CODEX_LOW_PROVIDER else "medium"
        return self.state.vault.config.codex.model_copy(
            update={"model": DEFAULT_CODEX_MODEL, "reasoning_effort": effort}
        )

    def _runtime_for_provider(self, provider_name: str):
        if provider_name in CODEX_PROVIDER_NAMES:
            if provider_name == "codex":
                runtime = self.state.startup_maintenance.codex_runtime if self.state.startup_maintenance else None
                if runtime is not None:
                    return runtime
            return check_codex_runtime(self.state.vault.root, self._codex_config_for_provider(provider_name))
        runtime = self.state.startup_maintenance.ai_runtime if self.state.startup_maintenance else None
        if runtime is not None and runtime.active_provider == provider_name:
            return runtime
        return check_ai_runtime(self.state.vault.root, self.state.vault.config, provider_name=provider_name)

    def _client_for_provider(self, provider_name: str):
        try:
            if provider_name in CODEX_PROVIDER_NAMES:
                return make_codex_client(self._codex_config_for_provider(provider_name), self.state.vault.root)
            return make_ai_provider_client(self.state.vault.config, self.state.vault.root, provider_name=provider_name)
        except CodexUnavailable:
            return None

    def _ai_ready(self) -> bool:
        _provider_name, runtime, client = self._grading_provider()
        return bool(runtime.ready and client is not None)

    def _provider_label(self) -> str:
        provider_name, _runtime, _client = self._grading_provider()
        return "Codex" if provider_name in CODEX_PROVIDER_NAMES else f"AI provider {provider_name}"

    def _complete_result(self, result: AttemptResult) -> None:
        _provider_name, runtime, client = self._grading_provider()
        self.followup_decision = evaluate_attempt_intervention_followup(
            self.state.vault,
            self.state.repository,
            result=result,
            available_minutes=self.available_minutes,
            ai_client=client if runtime.ready else None,
        )
        self.result = result
        self.app.last_attempt_result = result
        self.surprise_direction = result.surprise_direction
        source = "Codex" if result.grading_source == "codex" else "AI" if result.grading_source == "ai" else "Self-grade"
        self.query_one("#grading-status", TextStatic).update(Content(f"{source} evaluation complete."))
        self.query_one("#feedback-summary", TextStatic).update(
            Content(
                f"score={result.rubric_score} rating={result.fsrs_rating} "
                f"due={result.due_at} mastery={result.mastery_mean:.2f}"
            )
        )
        self._render_results(result)
        self.has_errors = bool(result.error_event_ids)
        self.graded = True
        # §5.6 opt-out accounting: the TUI reveals feedback per attempt, and
        # each reveal is an intervention boundary — if this diagnostic attempt
        # did not already close its block, run the block-end hook now so the
        # state segment closes and later evidence measures the post-reveal
        # learner state. The integrity model does not depend on the UX cost.
        if self.draft.probe_presentation_id is not None and result.probe_block_end is None:
            from learnloop.services.probe_blocks import end_diagnostic_block

            episode = self.state.repository.open_probe_episode(self.learning_object.id)
            if episode is not None and episode.status == "in_progress":
                end_diagnostic_block(
                    self.state.vault,
                    self.state.repository,
                    episode,
                    ai_client=client if runtime.ready else None,
                )
        self.state.refresh()

    # ── results rendering ────────────────────────────────────────────────────
    def _render_results(self, result: AttemptResult) -> None:
        self.query_one("#result-head", TextStatic).update(self._result_head_content(result))
        self.query_one("#score-block", TextStatic).update(self._score_block_content(result))
        self.query_one("#rubric-evidence", TextStatic).update(self._rubric_evidence_content(result))
        self.query_one("#tutor-note", TextStatic).update(self._tutor_note_content(result))
        self.query_one("#error-attributions", TextStatic).update(self._error_content(result))
        self.query_one("#belief-update", TextStatic).update(self._belief_content(result))
        self.query_one("#next-followup", TextStatic).update(self._followup_content())
        self.query_one("#next-schedule", TextStatic).update(self._schedule_content(result))

    def _result_head_content(self, result: AttemptResult) -> Content:
        return Content.assemble(
            (self.learning_object.title, "$text bold"),
            "  ",
            pill(self.practice_item.practice_mode, mode_pill_color(self.practice_item.practice_mode)),
            "\n",
            (f"{self.practice_item.id} · graded by {result.grading_source}", "$text-muted italic"),
        )

    def _score_block_content(self, result: AttemptResult) -> Content:
        max_points = self.rubric.max_points if self.rubric else max(result.rubric_score, 1)
        ratio = result.rubric_score / max_points if max_points else 0.0
        tone = "$success" if ratio >= 0.75 else "$warning" if ratio >= 0.5 else "$error"
        rating = result.fsrs_rating
        return Content.assemble(
            (f"{result.rubric_score} / {max_points}", f"{tone} bold"),
            ("    grader_confidence ", "$text-disabled"),
            block_bar(result.grader_confidence, 6, "$accent"),
            (f" {result.grader_confidence:.2f}", "$text-muted"),
            "\n",
            ("FSRS rating ", "$text-disabled"),
            pill(rating, _RATING_PILL.get(rating, "primary")),
            ("   next due ", "$text-disabled"),
            (result.due_at, "$text-muted"),
        )

    def _rubric_evidence_content(self, result: AttemptResult) -> Content:
        if self.rubric is None:
            return Content("No rubric.")
        evidence_map = {
            record.criterion_id: record
            for record in self.state.repository.fetch_grading_evidence(result.attempt_id)
        }
        parts: list = []
        for i, criterion in enumerate(self.rubric.criteria):
            if i:
                parts.append("\n")
            record = evidence_map.get(criterion.id)
            awarded = record.points_awarded if record else self.criterion_points.get(criterion.id, 0.0)
            mark, tone = self._criterion_mark(awarded, criterion.points)
            parts.append((f"{mark} ", f"{tone} bold"))
            parts.append((criterion.id, "$text"))
            parts.append((f"  {awarded:.1f}/{criterion.points:g}", f"{tone}"))
            evidence = record.evidence if record and record.evidence else criterion.description
            if evidence:
                parts.append("\n")
                parts.append((f"    {evidence}", "$text-muted"))
        return Content.assemble(*parts)

    def _tutor_note_content(self, result: AttemptResult) -> Content:
        direction = result.surprise_direction
        return Content.assemble(
            ("tutor note  ", "$accent bold"),
            (
                f"correctness {result.correctness:.0%} · surprise {direction} "
                f"({result.bayesian_surprise:.2f} nats)",
                "$text",
            ),
        )

    def _error_content(self, result: AttemptResult) -> Content:
        ids = set(result.error_event_ids)
        if not ids:
            return Content("No error attributions.").stylize("$text-muted")
        events = [
            event
            for event in self.state.repository.active_errors_by_learning_object(result.learning_object_id)
            if event.id in ids
        ]
        if not events:
            return Content(f"{len(ids)} error event(s) recorded.").stylize("$text-muted")
        parts: list = []
        for i, event in enumerate(events):
            if i:
                parts.append("\n")
            # spec §7: prefer the normalized belief statement over the coarse
            # error-type label when the event carries a registry misconception.
            label = getattr(event, "misconception_statement", None) or event.error_type
            parts.append((label, "$text-error bold"))
            parts.append(("  severity ", "$text-disabled"))
            parts.append(block_bar(event.severity, 6, "$error"))
            parts.append((f" {event.severity:.2f}", "$text-muted"))
            if event.is_misconception:
                parts.append("  ")
                parts.append(pill("misconception", "error"))
        return Content.assemble(*parts)

    def _belief_content(self, result: AttemptResult) -> Content:
        before_mean, before_sd = self.pre_mastery
        after_mean = result.mastery_mean
        after_sd = result.mastery_variance**0.5
        tau = self.state.vault.config.scheduler.followup.tau_followup_nats
        return Content.assemble(
            ("before ", "$text-disabled"),
            block_bar(before_mean, 10, "$warning"),
            (f" {before_mean:.2f} ± {before_sd:.2f}", "$text-muted"),
            ("   →   after ", "$text-disabled"),
            block_bar(after_mean, 10, "$success"),
            (f" {after_mean:.2f} ± {after_sd:.2f}", "$text-muted"),
            "\n",
            pill(f"surprise · {result.surprise_direction}", "warning"),
            (f"  bayesian {result.bayesian_surprise:.2f} nats vs τ {tau:.2f}", "$text"),
        )

    def _followup_content(self) -> Content:
        decision = self.followup_decision
        if decision and decision.triggered and decision.practice_item_id:
            return Content.assemble(
                ("Diagnostic follow-up  ", "$text bold"),
                pill("queued", "warning"),
                "\n",
                ("auto-inserted by intervention gate", "$text-muted italic"),
                "\n",
                ("next item ", "$text-disabled"),
                (decision.practice_item_id, "$text-muted"),
            )
        reason = decision.reason if decision else "not_evaluated"
        return Content.assemble(
            ("Diagnostic follow-up  ", "$text bold"),
            pill("none", "slate"),
            "\n",
            (f"gate did not fire ({reason})", "$text-muted italic"),
        )

    def _schedule_content(self, result: AttemptResult) -> Content:
        return Content.assemble(
            ("Schedule  ", "$text bold"),
            pill(f"FSRS · {result.fsrs_rating}", "slate"),
            "\n",
            ("next due ", "$text-disabled"),
            (result.due_at, "$text-muted"),
            "\n",
            ("mastery posterior ", "$text-disabled"),
            (f"{result.mastery_mean:.2f} ± {result.mastery_variance**0.5:.2f}", "$text-muted"),
        )

    def _criterion_mark(self, awarded: float, points: float) -> tuple[str, str]:
        if awarded >= points:
            return "✓", "$success"
        if awarded > 0:
            return "◐", "$warning"
        return "✗", "$error"

    def _mastery_mean_sd(self) -> tuple[float, float]:
        state = self.state.repository.mastery_states().get(self.item.learning_object_id)
        if state is None:
            return 0.5, 0.25
        mean = sigmoid(state.logit_mean)
        variance = (mean * (1 - mean)) ** 2 * state.logit_variance
        return mean, variance**0.5

    def _breadcrumb_content(self) -> Content:
        return Content.assemble(
            ("today", "$text-primary underline"),
            (" › ", "$text-disabled"),
            ("practice", "$text-primary underline"),
            (" › ", "$text-disabled"),
            ("feedback", "$text-muted"),
            (" › ", "$text-disabled"),
            (self.practice_item.id, "$text"),
        )

    def _read_form_state(self) -> None:
        if self.rubric is not None and self.is_mounted:
            for criterion in self.rubric.criteria:
                raw = self.query_one(f"#criterion-{criterion.id}", Input).value.strip()
                self.criterion_points[criterion.id] = float(raw or "0")
        if self.is_mounted:
            raw_confidence = self.query_one("#confidence-input", Input).value.strip()
            self.confidence = int(raw_confidence or "3")
            raw_error_type = self.query_one("#error-type-input", Input).value.strip()
            self.error_type = raw_error_type or None

    def _render_fatal_summary(self) -> None:
        if not self.rubric or not self.rubric.fatal_errors:
            return
        selected = ", ".join(self.fatal_errors) if self.fatal_errors else "none"
        self.query_one("#fatal-summary", TextStatic).update(Content(f"Fatal errors: {selected}"))

    def return_to_today(self) -> None:
        from learnloop.tui.screens.today import TodayScreen

        while len(self.app.screen_stack) > 1 and not isinstance(self.app.screen, TodayScreen):
            self.app.pop_screen()

    def action_submit(self) -> None:
        self.submit()

    def action_next(self) -> None:
        self.return_to_today()

    def action_back(self) -> None:
        self.return_to_today()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "grade-button":
            self.submit()
        elif event.button.id == "today-button":
            self.return_to_today()
        elif event.button.id and event.button.id.startswith("fatal-"):
            self.toggle_fatal(event.button.id.removeprefix("fatal-"))
