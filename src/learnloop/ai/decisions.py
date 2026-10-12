"""The decision-model contract: typed questions in, typed probabilities out.

A decision model (router spec §6, Perplexity's Decider) reads one ``state``
and answers named questions with probabilities instead of prose:

* ``noul``: P(yes);
* ``choice``: a probability for each of 1-255 named options, plus the most
  likely one and a self-reported confidence (no calibration claim);
* ``score``: a probability for each of 1-10 ordered rubric levels, plus the
  expected level and a confidence.

Requests are built only from the typed question classes, so no unknown field
can be sent (the APIs answer 400 to one). Responses are parsed strictly: an
answer must exist for every question and nothing else, carry exactly its
type's documented fields, and hold finite probabilities that cover the asked
options and sum to about one. Anything else fails closed with
``DecisionResponseInvalid``: if the provider changes its API, callers stop
rather than read numbers whose meaning moved. The model explains nothing;
there is no rationale field.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
import math
from typing import Any, Protocol, TypeAlias, runtime_checkable

from learnloop.ai.errors import AIInvalidOutput

MAX_QUESTIONS = 128
MAX_CHOICE_OPTIONS = 255
MAX_SCORE_LEVELS = 10
#: Documented sums are "about 1"; a wider gap means the shape changed.
PROBABILITY_SUM_TOLERANCE = 0.02

DecisionState: TypeAlias = str | Mapping[str, Any] | Sequence[Any]


class DecisionResponseInvalid(AIInvalidOutput):
    """A paid decision response did not match the documented contract."""


def _text(value: str, what: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{what} must be a nonempty string")
    return value


@dataclass(frozen=True)
class NoulQuestion:
    """A yes/no question; ``when_true``/``when_false`` describe each answer."""

    instructions: str
    when_true: str | None = None
    when_false: str | None = None

    def __post_init__(self) -> None:
        _text(self.instructions, "noul instructions")
        # OpenRouter's schema requires both criteria when either is given.
        if (self.when_true is None) != (self.when_false is None):
            raise ValueError("noul criteria need both a true and a false description, or neither")
        for value in (self.when_true, self.when_false):
            if value is not None:
                _text(value, "noul criterion")

    def wire(self) -> dict[str, Any]:
        body: dict[str, Any] = {"type": "noul", "instructions": self.instructions}
        if self.when_true is not None:
            body["criteria"] = {"true": self.when_true, "false": self.when_false}
        return body


@dataclass(frozen=True)
class ChoiceQuestion:
    """Pick one of 1-255 named options; a description may be None."""

    instructions: str
    options: Mapping[str, str | None]

    def __post_init__(self) -> None:
        _text(self.instructions, "choice instructions")
        if not isinstance(self.options, Mapping) or not 1 <= len(self.options) <= MAX_CHOICE_OPTIONS:
            raise ValueError(f"a choice question takes 1 to {MAX_CHOICE_OPTIONS} options")
        for name, description in self.options.items():
            _text(name, "choice option name")
            if description is not None:
                _text(description, "choice option description")
        object.__setattr__(self, "options", dict(self.options))

    def wire(self) -> dict[str, Any]:
        return {"type": "choice", "instructions": self.instructions, "criteria": dict(self.options)}


@dataclass(frozen=True)
class ScoreQuestion:
    """Rate on an ordered rubric of 1-10 levels; index i is score i."""

    instructions: str
    levels: Sequence[str]

    def __post_init__(self) -> None:
        _text(self.instructions, "score instructions")
        if isinstance(self.levels, (str, bytes)) or not 1 <= len(self.levels) <= MAX_SCORE_LEVELS:
            raise ValueError(f"a score question takes 1 to {MAX_SCORE_LEVELS} levels")
        for level in self.levels:
            _text(level, "score level")
        object.__setattr__(self, "levels", tuple(self.levels))

    def wire(self) -> dict[str, Any]:
        return {"type": "score", "instructions": self.instructions, "criteria": list(self.levels)}


Question: TypeAlias = NoulQuestion | ChoiceQuestion | ScoreQuestion


@dataclass(frozen=True)
class NoulAnswer:
    p_yes: float


@dataclass(frozen=True)
class ChoiceAnswer:
    choice: str
    probabilities: Mapping[str, float]
    confidence: float | None = None


@dataclass(frozen=True)
class ScoreAnswer:
    score: float
    probabilities: Mapping[int, float]
    confidence: float | None = None


Answer: TypeAlias = NoulAnswer | ChoiceAnswer | ScoreAnswer


@dataclass(frozen=True)
class DecisionResult:
    """Typed answers plus the provider's own accounting for the receipt."""

    answers: Mapping[str, Answer]
    model: str
    input_tokens: int
    output_tokens: int
    cost: float | None = None
    response_id: str | None = None
    provider: str | None = None
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)


@runtime_checkable
class DecisionClient(Protocol):
    """One request per call: the same ``state`` answers every named question."""

    provider_name: str
    provider_type: str
    model: str | None

    def decide(
        self, state: DecisionState, questions: Mapping[str, Question], *, purpose: str,
    ) -> DecisionResult:
        ...


def validate_questions(questions: Mapping[str, Question]) -> dict[str, Question]:
    if not isinstance(questions, Mapping) or not 1 <= len(questions) <= MAX_QUESTIONS:
        raise ValueError(f"a decision request takes 1 to {MAX_QUESTIONS} questions")
    checked: dict[str, Question] = {}
    for name, question in questions.items():
        _text(name, "question name")
        if not isinstance(question, (NoulQuestion, ChoiceQuestion, ScoreQuestion)):
            # Typed classes only: an untyped dict could carry unknown fields.
            raise TypeError(f"question {name!r} must be a NoulQuestion, ChoiceQuestion or ScoreQuestion")
        checked[name] = question
    return checked


def validate_state(state: DecisionState) -> DecisionState:
    if state is None or isinstance(state, (bytes, bytearray)) or not isinstance(state, (str, Mapping, Sequence)):
        raise ValueError("decision state must be a string, an object or an array")
    if isinstance(state, str) and not state.strip():
        raise ValueError("decision state must not be empty")
    return state


def request_body(model: str, state: DecisionState, questions: Mapping[str, Question]) -> dict[str, Any]:
    """The complete wire body: ``model``, ``state`` and ``questions``, nothing else.

    Perplexity's API answers 400 to any other top-level field, and nothing
    else is needed on OpenRouter, so the same body serves both dialects.
    """

    _text(model, "model")
    checked = validate_questions(questions)
    return {
        "model": model,
        "state": validate_state(state),
        "questions": {name: question.wire() for name, question in checked.items()},
    }


_RESPONSE_FIELDS = frozenset({"model", "answers", "usage", "id", "provider"})
_USAGE_FIELDS = frozenset({"input_tokens", "output_tokens", "cost"})
_ANSWER_FIELDS = {
    "noul": frozenset({"type", "noul"}),
    "choice": frozenset({"type", "choice", "probabilities", "confidence"}),
    "score": frozenset({"type", "score", "probabilities", "confidence", "legend"}),
}


def _probability(value: Any, what: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise DecisionResponseInvalid(f"{what} is not a finite number")
    if not 0.0 <= float(value) <= 1.0:
        raise DecisionResponseInvalid(f"{what} is outside [0, 1]")
    return float(value)


def _count(value: Any, what: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise DecisionResponseInvalid(f"{what} is not a nonnegative integer")
    return value


def _distribution(values: Any, expected: Sequence[str], what: str) -> dict[str, float]:
    if not isinstance(values, Mapping) or set(values) != set(expected):
        raise DecisionResponseInvalid(f"{what} probabilities do not cover exactly the asked options")
    result = {key: _probability(values[key], f"{what} probability {key!r}") for key in expected}
    if abs(sum(result.values()) - 1.0) > PROBABILITY_SUM_TOLERANCE:
        raise DecisionResponseInvalid(f"{what} probabilities do not sum to one")
    return result


def _answer(name: str, question: Question, raw: Any) -> Answer:
    if not isinstance(raw, Mapping):
        raise DecisionResponseInvalid(f"answer {name!r} is not an object")
    expected_type = question.wire()["type"]
    if raw.get("type") != expected_type:
        raise DecisionResponseInvalid(f"answer {name!r} has type {raw.get('type')!r}, asked {expected_type!r}")
    unknown = set(raw) - _ANSWER_FIELDS[expected_type]
    if unknown:
        raise DecisionResponseInvalid(f"answer {name!r} has unknown fields: {', '.join(sorted(unknown))}")
    confidence = raw.get("confidence")
    if confidence is not None:
        confidence = _probability(confidence, f"answer {name!r} confidence")
    if isinstance(question, NoulQuestion):
        return NoulAnswer(p_yes=_probability(raw.get("noul"), f"answer {name!r} noul"))
    if isinstance(question, ChoiceQuestion):
        options = list(question.options)
        probabilities = _distribution(raw.get("probabilities"), options, f"answer {name!r}")
        choice = raw.get("choice")
        if choice not in question.options:
            raise DecisionResponseInvalid(f"answer {name!r} chose an option that was not asked")
        return ChoiceAnswer(choice=choice, probabilities=probabilities, confidence=confidence)
    levels = [str(index) for index in range(len(question.levels))]
    probabilities = _distribution(raw.get("probabilities"), levels, f"answer {name!r}")
    legend = raw.get("legend")
    if legend is not None and (not isinstance(legend, Mapping) or set(legend) != set(levels)):
        raise DecisionResponseInvalid(f"answer {name!r} legend does not match the asked levels")
    score = raw.get("score")
    if isinstance(score, bool) or not isinstance(score, (int, float)) or not math.isfinite(score):
        raise DecisionResponseInvalid(f"answer {name!r} score is not a finite number")
    if not 0.0 <= float(score) <= len(levels) - 1:
        raise DecisionResponseInvalid(f"answer {name!r} score is outside the rubric")
    return ScoreAnswer(
        score=float(score),
        probabilities={int(key): value for key, value in probabilities.items()},
        confidence=confidence,
    )


def parse_response(payload: Any, questions: Mapping[str, Question]) -> DecisionResult:
    """Parse a 200 body against the questions that were asked; fail closed."""

    if not isinstance(payload, Mapping):
        raise DecisionResponseInvalid("decision response is not a JSON object")
    unknown = set(payload) - _RESPONSE_FIELDS
    if unknown:
        raise DecisionResponseInvalid(f"decision response has unknown fields: {', '.join(sorted(unknown))}")
    model = payload.get("model")
    if not isinstance(model, str) or not model:
        raise DecisionResponseInvalid("decision response names no model")
    answers = payload.get("answers")
    if not isinstance(answers, Mapping) or set(answers) != set(questions):
        raise DecisionResponseInvalid("decision answers do not match the asked questions")
    usage = payload.get("usage")
    if not isinstance(usage, Mapping) or set(usage) - _USAGE_FIELDS:
        raise DecisionResponseInvalid("decision usage is missing or has unknown fields")
    cost = usage.get("cost")
    if cost is not None and (
        isinstance(cost, bool) or not isinstance(cost, (int, float)) or not math.isfinite(cost) or cost < 0
    ):
        raise DecisionResponseInvalid("decision usage cost is not a finite nonnegative number")
    for key in ("id", "provider"):
        if payload.get(key) is not None and not isinstance(payload[key], str):
            raise DecisionResponseInvalid(f"decision response {key} is not a string")
    return DecisionResult(
        answers={name: _answer(name, question, answers[name]) for name, question in questions.items()},
        model=model,
        input_tokens=_count(usage.get("input_tokens"), "usage input_tokens"),
        output_tokens=_count(usage.get("output_tokens"), "usage output_tokens"),
        cost=float(cost) if cost is not None else None,
        response_id=payload.get("id"),
        provider=payload.get("provider"),
        raw=dict(payload),
    )


__all__ = [
    "Answer",
    "ChoiceAnswer",
    "ChoiceQuestion",
    "DecisionClient",
    "DecisionResponseInvalid",
    "DecisionResult",
    "DecisionState",
    "MAX_CHOICE_OPTIONS",
    "MAX_QUESTIONS",
    "MAX_SCORE_LEVELS",
    "NoulAnswer",
    "NoulQuestion",
    "Question",
    "ScoreAnswer",
    "ScoreQuestion",
    "parse_response",
    "request_body",
    "validate_questions",
    "validate_state",
]
