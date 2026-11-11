"""What other test files use from ``tests/test_reader_ca3_compare_anywhere.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

from learnloop.ai.decisions import ChoiceAnswer, ChoiceQuestion, DecisionResult, NoulAnswer, NoulQuestion
from learnloop.source_retrieval import compare_scope as CS

from tests.router_model_fakes import FakeDecider


class ScopeDecider(FakeDecider):
    """The Decider at its listed price, answering each question by name:
    ``choices`` maps a question to the option it prefers (a spanned option
    may be named by its text), ``named`` the books' titles it says yes to."""

    settings = SimpleNamespace(price_per_million_input=0.02)

    def __init__(self, *, choices: dict[str, str] | None = None, named: tuple[str, ...] = (),
                 error: Exception | None = None, tie: str | None = None) -> None:
        super().__init__(error=error)
        self.prefer = dict(choices or {})
        self.named = set(named)
        self.tie = tie

    def _decide(self, state, questions, *, purpose, timeout_seconds):
        from learnloop.ai.execution import report_call_usage

        self.calls.append({"state": state, "questions": dict(questions), "purpose": purpose,
                           "timeout_seconds": timeout_seconds})
        if self.error is not None:
            raise self.error
        report_call_usage({"input_tokens": 1200, "output_tokens": 16, "cost": 0.0004})
        answers: dict[str, Any] = {}
        for name, question in questions.items():
            if isinstance(question, ChoiceQuestion):
                options = list(question.options)
                wanted = self.prefer.get(name)
                pick = next((option for option in options if option == wanted
                             or (question.options[option] or "").strip('"') == wanted), None)
                if name == self.tie:
                    probabilities = {option: 1.0 / len(options) for option in options}
                else:
                    pick = pick or options[0]
                    rest = 0.1 / max(1, len(options) - 1)
                    probabilities = {option: (0.9 if option == pick else rest) for option in options}
                    if len(options) == 1:
                        probabilities = {pick: 1.0}
                answers[name] = ChoiceAnswer(choice=pick or options[0], probabilities=probabilities, confidence=0.5)
            elif isinstance(question, NoulQuestion):
                said = any(title in question.instructions for title in self.named)
                answers[name] = NoulAnswer(p_yes=0.8 if said else 0.1)
        return DecisionResult(answers=answers, model=self.model, input_tokens=1200, output_tokens=16, cost=0.0004,
                              response_id="dec_1", provider="Perplexity", raw={"model": self.model})


BOOKS = [CS.Book("b1", "src_axler", "Linear Algebra Done Right", "axler-ladr"),
         CS.Book("b2", "src_strang", "Introduction to Linear Algebra", "strang"),
         CS.Book("b3", "src_lay", "Linear Algebra and Its Applications", "lay")]
