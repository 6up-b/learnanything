"""Strict wire contracts for the practice index's paid LLM roles.

Every field is required, so the strict output schema sent to Codex and the
runtime validation agree. Length and count limits are applied after
validation (rendering clips), because strict schemas carry no such keywords.
"""
from __future__ import annotations

from typing import Literal

from learnloop.ai.schemas import WireModel


Relevance = Literal["relevant", "partial", "not_relevant"]
RELEVANCE_SCORE: dict[str, float] = {"relevant": 2.0, "partial": 1.0, "not_relevant": 0.0}


class DossierContrast(WireModel):
    neighbor_ref: str
    difference: str


class FacetDossierDraft(WireModel):
    """scope (covers/excludes), moves, errors and contrast (Slice 2 §5.9)."""

    covers: list[str]
    excludes: list[str]
    moves: list[str]
    errors: list[str]
    contrast: list[DossierContrast]


class CandidateJudgment(WireModel):
    ref: str
    relevance: Relevance
    rationale: str


class PracticeRerank(WireModel):
    """Judge every candidate, then pick and order the best few."""

    judgments: list[CandidateJudgment]
    picks: list[str]


class FacetQuote(WireModel):
    """A facet the exercise exercises, with a verbatim quote from its statement
    that shows it (checked in code; a facet whose quote fails is dropped)."""

    facet_id: str
    quote: str


class ExerciseMetadata(WireModel):
    """Provisional metadata for one unimported textbook exercise (§8.1)."""

    ref: str
    facets: list[FacetQuote]
    practice_mode: str


class MixedPracticeRerank(WireModel):
    """Judge every candidate (practice items and textbook exercises), pick the
    best few, and give each textbook exercise its provisional metadata."""

    judgments: list[CandidateJudgment]
    picks: list[str]
    exercise_metadata: list[ExerciseMetadata]


class RelevanceLabels(WireModel):
    labels: list[CandidateJudgment]


class WrittenQuery(WireModel):
    seed_ref: str
    query: str


class WrittenQueries(WireModel):
    queries: list[WrittenQuery]


__all__ = [
    "RELEVANCE_SCORE",
    "CandidateJudgment",
    "DossierContrast",
    "ExerciseMetadata",
    "FacetDossierDraft",
    "FacetQuote",
    "MixedPracticeRerank",
    "PracticeRerank",
    "Relevance",
    "RelevanceLabels",
    "WrittenQueries",
    "WrittenQuery",
]
