from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Button, Input, Label

from learnloop.services.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
from learnloop.services.scheduler import ScheduledItem
from learnloop.tui.state import TuiState
from learnloop.tui.widgets import TextStatic


class PracticeScreen(Screen):
    """Collects a learner answer, then hands off to the feedback/self-grade screen.

    The screen owns no scheduling, grading, or mastery logic; it only gathers
    input and calls the attempt service.
    """

    BINDINGS = [
        ("escape", "back", "Back"),
        ("ctrl+s", "submit", "Submit"),
    ]

    def __init__(self, state: TuiState, item: ScheduledItem):
        super().__init__()
        self.state = state
        self.item = item
        self.practice_item = state.vault.practice_items[item.practice_item_id]
        self.learning_object = state.vault.learning_objects[item.learning_object_id]
        self.attempt_type = "independent_attempt"
        self.hints_used = 0

    def compose(self) -> ComposeResult:
        with Vertical(id="practice-layout"):
            yield Label("Practice", id="practice-title")
            yield TextStatic(self.learning_object.title, id="practice-lo")
            yield TextStatic(self.practice_item.prompt, id="practice-prompt")
            yield Input(placeholder="Type your answer", id="answer-input")
            yield TextStatic("", id="practice-hints")
            yield Button("Reveal hint", id="hint-button")
            yield Button("Submit answer", id="submit-button")
            yield Button("I don't know", id="dontknow-button")

    @property
    def answer(self) -> str:
        return self.query_one("#answer-input", Input).value

    def set_answer(self, text: str) -> None:
        self.query_one("#answer-input", Input).value = text

    def reveal_hint(self) -> None:
        hints = self.practice_item.hints
        if self.hints_used < len(hints):
            self.hints_used += 1
        shown = "\n".join(f"- {hint}" for hint in hints[: self.hints_used]) or "No hints revealed."
        self.query_one("#practice-hints", TextStatic).update(shown)

    def _draft(self, attempt_type: str | None = None) -> AttemptDraft:
        return AttemptDraft(
            practice_item_id=self.practice_item.id,
            learner_answer_md=self.answer,
            attempt_type=attempt_type or self.attempt_type,
            hints_used=self.hints_used,
        )

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

    async def action_submit(self) -> None:
        await self.open_feedback()

    def action_back(self) -> None:
        self.app.pop_screen()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "hint-button":
            self.reveal_hint()
        elif event.button.id == "submit-button":
            self.app.push_screen(self.open_feedback_screen())
        elif event.button.id == "dontknow-button":
            self.dont_know()

    def open_feedback_screen(self):
        from learnloop.tui.screens.feedback import FeedbackScreen

        return FeedbackScreen(self.state, self.item, self._draft())
