"""Tier 1, the Decider migration (owner decision 2026-10-13): fakes only, no network.

Each moved judgment: the Decider decides (the argmax of its distribution, not
its separate choice field), the LLM runs only when the Decider is unavailable,
refused for spend or failing, and the judgment's switch restores the LLM path.
The facet span-support check is in ``test_facet_span_support``, the agreement
report in ``test_decider_agreement``; both use the doubles below.
"""

from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from learnloop.ai.decisions import ChoiceAnswer, ChoiceQuestion, DecisionResult
from learnloop.ai.errors import AIProviderUnavailable
from learnloop.config.schema import LearnLoopConfig
from learnloop.db.repositories import Repository


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


def _config(**switches) -> LearnLoopConfig:
    config = LearnLoopConfig()
    config.algorithms.algorithm_version = "mvp-0.20"
    for name, value in switches.items():
        setattr(config.decider_routes, name, value)
    return config


def _rows(repository, task=None):
    with repository.connection() as connection:
        query = "SELECT * FROM judgment_ledger" + (" WHERE task = ?" if task else "") + " ORDER BY rowid"
        return [dict(row) for row in connection.execute(query, (task,) if task else ())]


# -- the shared decision ----------------------------------------------------------------------------


SERVING = ["learner_gap_judge", "learner_gap_kind", "misconception_match", "diagnosis_link_judgment",
           "field_question_classification", "contamination_leak_judgment", "contamination_reveal_judgment"]


@pytest.mark.parametrize("task", [*SERVING, "facet_span_support"])
@pytest.mark.parametrize("mode", ["decider", "unavailable", "failed", "refused", "disabled"])
def test_route_decision_fallback_and_switch(tmp_path, task, mode):
    from learnloop.ai.review_spend import ReviewSpend
    from learnloop.ai.spend import SpendCaps
    from learnloop.decider_judgments import decide, log_llm

    config = _config(**{task: mode != "disabled"})
    repo = Repository(tmp_path / "state.sqlite3")
    client = Decider(RuntimeError("failed") if mode == "failed" else None)
    calls = []

    def factory():
        calls.append(True)
        return None if mode == "unavailable" else client

    spend = ReviewSpend(SpendCaps(max_calls=0)) if mode == "refused" else None
    result = decide(root=tmp_path, config=config, repository=repo, task=task,
                    state={"input": "text"}, question=ChoiceQuestion("Choose", {"yes": None, "no": None}),
                    client_factory=factory, spend=spend)
    if mode == "decider":
        # The argmax decides, not the response's choice field.
        assert (result.status, result.choice, result.probabilities) == ("ok", "no", {"yes": 0.2, "no": 0.8})
    else:
        assert result.choice is None and result.status == mode
        log_llm(repo, result, choice="yes", model="fake/llm")
    rows = _rows(repo)
    if mode == "refused":
        assert not client.calls  # refused before anything is sent
    if mode == "disabled":
        assert not calls and [row["judge"] for row in rows] == ["llm"]
    else:
        assert rows[0]["judge"] == "decider"
        assert rows[0]["verdict"] == ("no" if mode == "decider" else mode)
        assert json.loads(rows[0]["rationale"])["status"] == result.status
    assert all(row["input_hash"] == result.input_hash for row in rows)


def test_serving_judgments_wait_for_the_successor_and_the_router_is_never_tier1():
    from learnloop.decider_judgments import enabled

    config = LearnLoopConfig()
    config.algorithms.algorithm_version = "mvp-0.19"
    assert not any(enabled(config, task) for task in SERVING)
    # The span-support check is a content path: its switch acts at every version.
    assert enabled(config, "facet_span_support")
    config.algorithms.algorithm_version = "mvp-0.20"
    assert all(enabled(config, task) for task in SERVING)
    assert not enabled(config, "router_decider") and not enabled(config, "llm_probability_decider")


def test_a_cancellation_is_never_a_fallback(tmp_path):
    from learnloop.ai.errors import AIInterrupted
    from learnloop.decider_judgments import decide

    repo = Repository(tmp_path / "state.sqlite3")
    with pytest.raises(AIInterrupted):
        decide(root=tmp_path, config=_config(), repository=repo, task="misconception_match", state="s",
               question=ChoiceQuestion("Choose", {"yes": None, "no": None}),
               client_factory=lambda: Decider(AIInterrupted("stop")))


def test_decider_receipt_and_spend_ignore_llm_output_budget(tmp_path):
    from learnloop.ai.execution import model_call, output_limit, report_call_usage
    from learnloop.ai.review_spend import ReviewSpend
    from learnloop.ai.spend import SpendCaps
    from learnloop.decider_judgments import decide

    config = _config()
    config.ai.output_tokens = 1234
    repo = Repository(tmp_path / "state.sqlite")

    class Receipted(FixedDecider):
        def decide(self, state, questions, *, purpose):
            assert output_limit() is None
            with model_call(self, purpose=purpose, prompt=state):
                result = super().decide(state, questions, purpose=purpose)
                report_call_usage({"input_tokens": 100, "output_tokens": 0, "cost": 0.000002,
                                   "resolved_model": self.model})
                return result

    client = Receipted({"misconception_match": "new"})
    spend = ReviewSpend(SpendCaps(), config=config)
    result = decide(root=tmp_path, config=config, repository=repo, task="misconception_match", state="belief",
                    question=ChoiceQuestion("Same or new?", {"same": None, "new": None}),
                    client_factory=lambda: client, spend=spend)
    assert result.choice == "new"
    assert spend.budget.used.calls == 1
    assert 100 <= spend.budget.used.total_tokens < config.ai.output_tokens
    assert spend.totals["tier1_decider"].input_tokens == 100
    with repo.connection() as c:
        row = c.execute("SELECT judge, output_budget_tokens, status, cost FROM model_call_receipts").fetchone()
    assert tuple(row) == ("decider", None, "completed", 0.000002)
