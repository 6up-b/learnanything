from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Button, Label

from learnloop.services.attempts import (
    AttemptDraft,
    AttemptResult,
    SelfGradeInput,
    complete_self_graded_attempt,
)
from learnloop.services.followups import evaluate_negative_surprise_followup
from learnloop.services.scheduler import ScheduledItem
from learnloop.tui.state import TuiState
from learnloop.tui.widgets import TextStatic


class FeedbackScreen(Screen):
    """Self-grade feedback. Collects per-criterion scores, fatal errors, error
    type, and confidence, then calls the attempt service. The screen contains no
    grading or scheduling logic of its own.
    """

    BINDINGS = [
        ("ctrl+s", "submit", "Submit grade"),
        ("escape", "back", "Back"),
    ]

    def __init__(self, state: TuiState, item: ScheduledItem, draft: AttemptDraft):
        super().__init__()
        self.state = state
        self.item = item
        self.draft = draft
        self.practice_item = state.vault.practice_items[item.practice_item_id]
        self.rubric = self.practice_item.grading_rubric
        self.criterion_points: dict[str, float] = (
            {criterion.id: 0.0 for criterion in self.rubric.criteria} if self.rubric else {}
        )
        self.fatal_errors: list[str] = []
        self.error_type: str | None = None
        self.confidence: int = 3
        self.result: AttemptResult | None = None
        self.available_minutes: int | None = None

    def compose(self) -> ComposeResult:
        expected = self.practice_item.expected_answer
        with Vertical(id="feedback-layout"):
            yield Label("Feedback", id="feedback-title")
            yield TextStatic(f"Expected: {expected}", id="expected-answer")
            yield TextStatic(self._rubric_text(), id="rubric")
            yield TextStatic("", id="feedback-summary")
            yield Button("Submit grade", id="grade-button")
            yield Button("Back to today", id="today-button")

    def _rubric_text(self) -> str:
        if self.rubric is None:
            return "No rubric."
        lines = [f"max_points={self.rubric.max_points}"]
        for criterion in self.rubric.criteria:
            lines.append(f"- {criterion.id} (max {criterion.points:g}): {criterion.description}")
        for fatal in self.rubric.fatal_errors:
            lines.append(f"! fatal {fatal.id} caps at {fatal.max_grade}")
        return "\n".join(lines)

    def set_points(self, criterion_id: str, points: float) -> None:
        self.criterion_points[criterion_id] = float(points)

    def set_confidence(self, confidence: int) -> None:
        self.confidence = int(confidence)

    def set_error_type(self, error_type: str | None) -> None:
        self.error_type = error_type

    def toggle_fatal(self, fatal_error_id: str) -> None:
        if fatal_error_id in self.fatal_errors:
            self.fatal_errors.remove(fatal_error_id)
        else:
            self.fatal_errors.append(fatal_error_id)

    def submit(self) -> AttemptResult:
        result = complete_self_graded_attempt(
            self.state.vault,
            self.state.repository,
            self.draft,
            SelfGradeInput(
                criterion_points=self.criterion_points,
                confidence=self.confidence,
                fatal_errors=self.fatal_errors or None,
                error_type=self.error_type,
            ),
        )
        evaluate_negative_surprise_followup(
            self.state.vault,
            self.state.repository,
            attempt_id=result.attempt_id,
            learning_object_id=result.learning_object_id,
            practice_item_id=result.practice_item_id,
            surprise_direction=result.surprise_direction,
            bayesian_surprise=result.bayesian_surprise,
            grader_confidence=result.grader_confidence,
            error_event_written=bool(result.error_event_ids),
            available_minutes=self.available_minutes,
        )
        self.result = result
        self.app.last_attempt_result = result
        self.query_one("#feedback-summary", TextStatic).update(
            f"score={result.rubric_score} rating={result.fsrs_rating} "
            f"due={result.due_at} mastery={result.mastery_mean:.2f}"
        )
        self.state.refresh()
        return result

    def return_to_today(self) -> None:
        from learnloop.tui.screens.today import TodayScreen

        while len(self.app.screen_stack) > 1 and not isinstance(self.app.screen, TodayScreen):
            self.app.pop_screen()

    def action_submit(self) -> None:
        self.submit()

    def action_back(self) -> None:
        self.return_to_today()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "grade-button":
            self.submit()
        elif event.button.id == "today-button":
            self.return_to_today()
