"""Fake facet-identity judges (no network): a structured judge and a Decider."""

from __future__ import annotations

import json
import re
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest

from learnloop.ai.errors import AIProviderUnavailable
from learnloop.ai.transport import BOUNDED_STRUCTURED_COMPLETION, STRUCTURED_COMPLETION, StructuredRequest
from learnloop.ai.usage import TokenUsage
from learnloop.content.facet_identity.judge import FacetPartitionVerdict, FacetSetVerdict

REGRESSION = Path(__file__).resolve().parent / "facet_identity_regression.json"


def regression_data() -> dict[str, Any]:
    return json.loads(REGRESSION.read_text(encoding="utf-8"))


def clusters_from_pairs(pairs: Iterable[Sequence[str]]) -> list[list[str]]:
    """Connected components of the merge-worthy pairs (the study's 5 clusters)."""

    parent: dict[str, str] = {}

    def find(key: str) -> str:
        parent.setdefault(key, key)
        while parent[key] != key:
            key = parent[key]
        return key

    for left, right in pairs:
        a, b = find(left), find(right)
        if a != b:
            parent[max(a, b)] = min(a, b)
    groups: dict[str, list[str]] = {}
    for key in list(parent):
        groups.setdefault(find(key), []).append(key)
    return sorted(sorted(group) for group in groups.values())


def _context(prompt: str) -> dict[str, Any]:
    for candidate in reversed(prompt.split("\n\n")):
        try:
            payload = json.loads(candidate)
        except ValueError:
            continue
        if isinstance(payload, dict) and isinstance(payload.get("context"), dict):
            return payload["context"]
    raise AssertionError("judge prompt carried no JSON context")


@dataclass
class FakeFacetJudge:
    """A structured judge that merges the facets of each known cluster.

    ``clusters`` name facets by claim text (``by="claim"``) or by any key a
    caller derives from the judge view (``key``). Each cluster's members that
    are in the group become one set: ``action`` (merge by default), the first
    listed member canonical. ``fail`` makes the next N calls raise.
    """

    clusters: Sequence[Sequence[str]] = ()
    key: Callable[[Mapping[str, Any]], str] = lambda view: str(view.get("claim") or "")
    action: str = "merge"
    fail: int = 0
    provider_name: str = "codex_luna"
    provider_type: str = "codex_sdk"
    model: str = "fake-judge-1"
    requests: list[dict[str, Any]] = field(default_factory=list)

    def supports(self, capability: str) -> bool:
        return capability in {STRUCTURED_COMPLETION, BOUNDED_STRUCTURED_COMPLETION}

    def complete(self, request: StructuredRequest[Any]) -> Any:
        context = _context(request.prompt)
        self.requests.append({"purpose": request.purpose, "prompt": request.prompt, "context": context})
        if self.fail > 0:
            self.fail -= 1
            raise AIProviderUnavailable("fake judge unavailable")
        facets = context["facets"]
        by_key: dict[str, list[str]] = {}
        for view in facets:
            by_key.setdefault(self.key(view), []).append(view["label"])
        sets: list[FacetSetVerdict] = []
        used: set[str] = set()
        for cluster in self.clusters:
            labels = [label for member in cluster for label in by_key.get(member, []) if label not in used]
            if len(labels) < 2:
                continue
            existing = [label for label in labels if label.startswith("E")]
            canonical = existing[0] if existing else labels[0]
            used.update(labels)
            sets.append(FacetSetVerdict(
                members=labels, action=self.action, canonical=canonical,
                absorb_as="example" if self.action == "absorb" else None,
                rationale="fake: the same skill",
            ))
        return FacetPartitionVerdict(sets=sets)

    def consume_usage(self) -> TokenUsage:
        return TokenUsage()


@dataclass
class _Answer:
    choice: str
    probabilities: Mapping[str, float]


@dataclass
class _Result:
    answers: Mapping[str, _Answer]
    model: str = "perplexity/pplx-decider-v1.1-27b"
    input_tokens: int = 100
    output_tokens: int = 0
    cost: float | None = 0.0001


@dataclass
class FakeDecider:
    """A decision client: answers each pair question from ``choose(first, second)``."""

    choose: Callable[[Mapping[str, Any], Mapping[str, Any]], str]
    provider_name: str = "fake_decider"
    provider_type: str = "decider"
    model: str = "perplexity/pplx-decider-v1.1-27b"
    calls: list[dict[str, Any]] = field(default_factory=list)

    def decide(self, state: Mapping[str, Any], questions: Mapping[str, Any], *, purpose: str) -> _Result:
        self.calls.append({"state": state, "questions": questions, "purpose": purpose})
        by_label = {facet["label"]: facet for facet in state["facets"]}
        answers: dict[str, _Answer] = {}
        for name, question in questions.items():
            wire = question.wire()
            assert wire["type"] == "choice" and set(wire["criteria"]) >= {"same_skill", "distinct"}
            match = re.search(r"Compare facet (\S+) with facet (\S+?)\.", wire["instructions"])
            assert match is not None, wire["instructions"]
            first, second = match.group(1), match.group(2)
            choice = self.choose(by_label[first], by_label[second])
            probabilities = {option: (0.85 if option == choice else 0.05) for option in wire["criteria"]}
            answers[name] = _Answer(choice=choice, probabilities=probabilities)
        return _Result(answers=answers)


@pytest.fixture(autouse=True)
def supporting_span_decider(monkeypatch):
    """The span-support check's Decider, answering ``supports`` (no network).

    A test module that applies cited model rewords imports this fixture: its
    rewords apply as before the check existed. The check's other outcomes,
    its card and its labels have their own tests (``test_tier1_decider``).
    """

    from types import SimpleNamespace

    from learnloop import decider_judgments
    from learnloop.ai.decisions import ChoiceAnswer, DecisionResult

    class Supporting:
        provider_name = "fake_span_decider"
        provider_type = "decider"
        model = "fake/span-decider"
        settings = SimpleNamespace(price_per_million_input=0.02)

        def decide(self, state, questions, *, purpose):
            assert purpose == "facet_span_support"
            assert len(questions) == 1
            assert state["spans"]
            return DecisionResult(
                {name: ChoiceAnswer("supports", {option: 0.85 if option == "supports" else 0.05
                                                 for option in question.options})
                 for name, question in questions.items()}, self.model, 100, 0, 0.000002)

    monkeypatch.setattr(decider_judgments, "client_for", lambda *args: Supporting())
