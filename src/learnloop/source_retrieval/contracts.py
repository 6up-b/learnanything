"""Strict wire contracts for T6's paid LLM roles.

Every field is required, so the strict output schema and runtime validation
agree; length and count limits are applied after validation.
"""
from __future__ import annotations

from typing import Literal

from learnloop.ai.schemas import WireModel

SpanVerdict = Literal["answers", "related", "unrelated"]
#: Graded gain for nDCG and the ledger score: answers 2, related 1, unrelated 0.
VERDICT_SCORE: dict[str, float] = {"answers": 2.0, "related": 1.0, "unrelated": 0.0}


class QueryRewrite(WireModel):
    """A retrieval rewrite: what a relevant passage would say, and search terms."""

    passage: str
    keywords: list[str]


class SpanJudgment(WireModel):
    ref: str
    verdict: SpanVerdict
    rationale: str


class SpanVerification(WireModel):
    """Judge every candidate passage, then pick and order the best few."""

    judgments: list[SpanJudgment]
    picks: list[str]


class SpanLabels(WireModel):
    labels: list[SpanJudgment]


class WrittenQuestion(WireModel):
    seed_ref: str
    question: str


class WrittenQuestions(WireModel):
    questions: list[WrittenQuestion]


__all__ = [
    "QueryRewrite",
    "SpanJudgment",
    "SpanLabels",
    "SpanVerdict",
    "SpanVerification",
    "VERDICT_SCORE",
    "WrittenQuestion",
    "WrittenQuestions",
]
