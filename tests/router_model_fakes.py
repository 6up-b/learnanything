"""Fakes for router R2b/R2c: a Decider, a router LLM and an embedding client.

No network, no key: the router's model source is replaced by
:class:`FakeModels`, which says which fakes are "set up" and hands them to the
runtime. Each fake records what it was asked, can block on an event (a slow
model, G7) and can fail on demand.

Each fake's request is one physical request, as a real provider's is
(``ai.execution.model_call`` with its usage reported): the router's daily
guard admits it in its start receipt, so a refused request never reaches
the fake (Codex review F3-F5), and its receipt is written like a real one.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
import json
import re
import threading
from typing import Any

from learnloop.ai.decisions import (
    ChoiceAnswer,
    ChoiceQuestion,
    DecisionResult,
    NoulAnswer,
    NoulQuestion,
)
from learnloop.ai.transport import ISOLATED_TURN, STRUCTURED_COMPLETION
from learnloop.daily_plan.router_runtime import RouterRuntime

DECIDER_MODEL = "perplexity/pplx-decider-v1.1-27b"
LLM_MODEL = "fake-router-llm"
_OPTION = re.compile(r"^- \[([^\]]+)\] ", re.MULTILINE)


def options_in(text: str) -> list[str]:
    """The option ids a router request lists under "# The options"."""

    section = text.split("# The options", 1)[-1]
    section = section.split("\n# ", 1)[0]
    return _OPTION.findall(section)


def uniform(refs: list[str]) -> dict[str, float]:
    return {ref: 1.0 / len(refs) for ref in refs}


def first_option(refs: list[str]) -> dict[str, float]:
    """All mass on the first option (the staged rule's pick leads the options)."""

    return {ref: (1.0 if index == 0 else 0.0) for index, ref in enumerate(refs)}


class FakeDecider:
    provider_name = "fake_decider"
    provider_type = "decider"
    model = DECIDER_MODEL

    def __init__(
        self,
        *,
        choice: Callable[[list[str]], Mapping[str, float]] | None = None,
        p_yes: float = 0.5,
        cost: float = 0.0004,
        gate: threading.Event | None = None,
        error: Exception | None = None,
    ) -> None:
        self.choice = choice or uniform
        self.p_yes = p_yes
        self.cost = cost
        self.gate = gate
        self.error = error
        self.calls: list[dict[str, Any]] = []

    def estimated_cost(self, input_tokens: int) -> float:
        return input_tokens * 0.02 / 1_000_000

    def decide(self, state, questions, *, purpose: str, timeout_seconds: float | None = None) -> DecisionResult:
        from learnloop.ai.decisions import request_body
        from learnloop.ai.execution import model_call

        body = json.dumps(request_body(self.model, state, questions), sort_keys=True, default=str)
        with model_call(self, purpose=purpose, prompt=body):
            return self._decide(state, questions, purpose=purpose, timeout_seconds=timeout_seconds)

    def _decide(self, state, questions, *, purpose: str, timeout_seconds: float | None) -> DecisionResult:
        from learnloop.ai.execution import report_call_usage

        self.calls.append({"state": state, "questions": dict(questions), "purpose": purpose,
                           "timeout_seconds": timeout_seconds})
        if self.gate is not None:
            self.gate.wait(30)
        if self.error is not None:
            raise self.error
        report_call_usage({"input_tokens": 1200, "output_tokens": 16, "cost": self.cost})
        answers: dict[str, Any] = {}
        for name, question in questions.items():
            if isinstance(question, ChoiceQuestion):
                refs = list(question.options)
                weights = dict(self.choice(refs))
                total = sum(weights.values()) or 1.0
                probabilities = {ref: float(weights.get(ref, 0.0)) / total for ref in refs}
                best = max(refs, key=lambda ref: probabilities[ref])
                answers[name] = ChoiceAnswer(choice=best, probabilities=probabilities, confidence=0.5)
            elif isinstance(question, NoulQuestion):
                answers[name] = NoulAnswer(p_yes=self.p_yes)
        return DecisionResult(answers=answers, model=self.model, input_tokens=1200, output_tokens=16, cost=self.cost,
                              response_id="dec_1", provider="Perplexity",
                              raw={"model": self.model, "answers": {name: repr(value) for name, value in answers.items()}})


class FakeLLM:
    provider_name = "fake_llm"
    provider_type = "fake"
    model = LLM_MODEL

    def __init__(
        self,
        *,
        answer: Callable[[Any], Mapping[str, Any]] | None = None,
        gate: threading.Event | None = None,
        error: Exception | None = None,
    ) -> None:
        self.answer = answer or self.default_answer
        self.gate = gate
        self.error = error
        self.requests: list[Any] = []

    def supports(self, capability: str) -> bool:
        return capability in {STRUCTURED_COMPLETION, ISOLATED_TURN}

    @staticmethod
    def default_answer(request: Any) -> dict[str, Any]:
        fields = request.result_model.model_fields
        if "intervene_now" in fields:
            return {"intervene_now": 0.5, "rationale": "Finish this first."}
        refs = options_in(request.prompt)
        out: dict[str, Any] = {
            "choose_block": [{"id": ref, "probability": 1.0 / len(refs)} for ref in refs],
            "rationale": "This keeps your recent work fresh.",
            "evidence_ids": [],
        }
        if "teach_first" in fields:
            topics = re.findall(r"^   - ([^:]+): ", request.prompt, re.MULTILINE)
            out["teach_first"] = [{"topic_id": topic, "probability": 0.2} for topic in topics]
            out["will_pass_next"] = [{"topic_id": topic, "probability": 0.7} for topic in topics]
        return out

    def complete(self, request: Any) -> Any:
        # Every real structured transport sends the result model's strict
        # schema, which only a WireModel has (the live R2bc session's finding).
        from learnloop.ai.execution import model_call, report_call_usage
        from learnloop.ai.strict_schema import strict_output_schema

        strict_output_schema(request.result_model)
        with model_call(self, purpose="chat_request", prompt=request.prompt, budget=request.output_budget_tokens):
            self.requests.append(request)
            if self.gate is not None:
                self.gate.wait(30)
            if self.error is not None:
                raise self.error
            report_call_usage({"input_tokens": max(1, len(request.prompt) // 4), "output_tokens": 200})
            return request.result_model.model_validate(dict(self.answer(request)))


class FakeEmbedding:
    model_id = model = "fake-embed"
    provider_name = "fake_embedding"
    dims = 8
    modalities = frozenset({"text"})
    max_input_tokens = 32_768

    def __init__(self) -> None:
        self.calls: list[list[str]] = []

    def embed(self, inputs: list[str], task_prefix: str) -> list[list[float]]:
        from learnloop.ai.execution import model_call, report_call_usage

        with model_call(self, purpose="embedding", prompt=list(inputs)):
            self.calls.append(list(inputs))
            report_call_usage({"input_tokens": sum(len(text) // 4 + 1 for text in inputs), "output_tokens": 0})
            out = []
            for text in inputs:
                seed = sum(ord(char) for char in text)
                out.append([((seed * (index + 3)) % 97) / 97.0 + (0.01 * index) for index in range(self.dims)])
            return out


class FakeModels:
    """The router's model source with fakes; a missing fake is "not set up"."""

    def __init__(self, *, decider: Any = None, llm: Any = None, embedding: Any = None) -> None:
        self.decider = decider
        self.llm = llm
        self.embedding = embedding

    def readiness(self, vault: Any) -> dict[str, str | None]:
        return {"decider": None if self.decider is not None else "unset",
                "llm": None if self.llm is not None else "unset"}

    def client(self, vault: Any, name: str, *, timeout_seconds: float) -> Any:
        client = self.decider if name == "decider" else self.llm
        if client is None:
            from learnloop.daily_plan.router_runtime import _NotReady

            raise _NotReady("unset")
        return client

    def decider_reachable(self, client: Any) -> tuple[bool, str]:
        return True, "fake"

    def embedding_client(self, vault: Any) -> Any:
        return self.embedding if bool(vault.config.embedding.enabled) else None


def fake_runtime(*, decider: Any = None, llm: Any = None, embedding: Any = None, inline: bool = True,
                 seed: Callable[[str, str], str] | None = None) -> RouterRuntime:
    return RouterRuntime(models=FakeModels(decider=decider, llm=llm, embedding=embedding), inline=inline, seed=seed)


def seed_with_first_uniform(at_least: float = 0.0, below: float = 1.0) -> Callable[[str, str], str]:
    """A seed function whose draws' first uniform lies in ``[at_least, below)``."""

    from learnloop.router.mixture import uniform as mixture_uniform

    for index in range(10_000):
        seed = f"pinned-{index}"
        value = mixture_uniform(seed, "component")
        if at_least <= value < below:
            return lambda _key, _decision_id, seed=seed: seed
    raise AssertionError("no seed found")
