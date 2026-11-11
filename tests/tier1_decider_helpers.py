"""What other test files use from ``tests/test_tier1_decider.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from types import SimpleNamespace

from learnloop.ai.decisions import ChoiceAnswer, ChoiceQuestion, DecisionResult
from learnloop.ai.errors import AIProviderUnavailable


class Decider:
    """A Decider double whose choice field disagrees with its probability argmax."""

    model = "fake/decider"
    provider_name = "fake"
    provider_type = "decider"
    settings = SimpleNamespace(price_per_million_input=0.02)

    def __init__(self, error: Exception | None = None):
        self.error = error
        self.calls: list = []

    def decide(self, state, questions, *, purpose):
        self.calls.append((state, questions, purpose))
        if self.error:
            raise self.error
        answers = {}
        for name, question in questions.items():
            assert isinstance(question, ChoiceQuestion)
            options = list(question.options)
            probabilities = {k: (0.8 if i == len(options) - 1 else 0.2 / (len(options) - 1))
                             for i, k in enumerate(options)}
            # Deliberately disagree with the probability argmax.
            answers[name] = ChoiceAnswer(options[0], probabilities)
        return DecisionResult(answers, self.model, 100, 0, 0.000002)


class FixedDecider(Decider):
    """Answers each question with ``choices[purpose]`` (or ``choices[name]``) at 0.9."""

    def __init__(self, choices):
        super().__init__()
        self.choices = choices

    def decide(self, state, questions, *, purpose):
        self.calls.append((purpose, state))
        answers = {}
        for name, question in questions.items():
            choice = self.choices.get(purpose, self.choices.get(name, next(iter(question.options))))
            assert choice in question.options
            n = len(question.options)
            answers[name] = ChoiceAnswer(choice, {k: (1.0 if n == 1 else 0.9) if k == choice else 0.1 / (n - 1)
                                                  for k in question.options})
        return DecisionResult(answers, self.model, 100, 0, 0.000002)


def _no_decider(*_args):
    raise AIProviderUnavailable("Decider unavailable")


def _rows(repository, task=None):
    with repository.connection() as connection:
        query = "SELECT * FROM judgment_ledger" + (" WHERE task = ?" if task else "") + " ORDER BY rowid"
        return [dict(row) for row in connection.execute(query, (task,) if task else ())]


class TiedDecider(Decider):
    """Its two first options share the top probability (and its choice field names the first)."""

    def decide(self, state, questions, *, purpose):
        self.calls.append((state, questions, purpose))
        answers = {}
        for name, question in questions.items():
            options = list(question.options)
            probabilities = {k: (0.5 if i < 2 else 0.0) for i, k in enumerate(options)}
            answers[name] = ChoiceAnswer(options[0], probabilities)
        return DecisionResult(answers, self.model, 100, 0, 0.000002)
