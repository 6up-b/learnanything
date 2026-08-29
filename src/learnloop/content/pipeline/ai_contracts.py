"""Feature-owned canonical-ingest AI input and prompt."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Literal

from learnloop.ai.transport import render_structured_prompt
from learnloop.content.proposals.ai_contracts import (
    _AUDIT_GUIDANCE,
    _DIFFICULTY_GUIDANCE,
    _PRACTICE_METADATA_GUIDANCE,
)

SourceKind = Literal["website_page", "youtube_video", "arxiv_html", "textbook_chapter"]
ChunkKind = Literal["prose", "heading", "code", "math", "caption"]


@dataclass(frozen=True)
class SourceChunk:
    locator: str
    text: str
    chunk_kind: ChunkKind = "prose"
    heading_path: list[str] = field(default_factory=list)
    label: str | None = None
    ordinal: int = 0


@dataclass(frozen=True)
class ExtractionPlan:
    create_learning_objects_first: bool = True
    attach_practice_items: bool = True
    attach_concept_edges: bool = True
    attach_rubric_drafts: bool = True
    allow_generative_practice_items: bool = True
    require_source_ref_per_item: bool = True
    learning_object_required: bool = True


@dataclass(frozen=True)
class CanonicalIngestContext:
    vault_root: str
    source_kind: SourceKind
    canonical_source: dict
    chunks: list[SourceChunk]
    target_subject: str | None = None
    target_learning_object_ids: list[str] = field(default_factory=list)
    concepts: list[dict] = field(default_factory=list)
    learning_objects: list[dict] = field(default_factory=list)
    extraction_plan: ExtractionPlan = field(default_factory=ExtractionPlan)
    instructions: str | None = None


CANONICAL_INGEST_PROMPT_VERSION = "mvp-0.6-criterion-total-scoring"


def canonical_ingest_prompt(context: CanonicalIngestContext) -> str:
    return render_structured_prompt(
        "learnloop canonical source ingestion",
        CANONICAL_INGEST_PROMPT_VERSION,
        {
            "task": (
                "Extract source-grounded LearnLoop authoring proposal items from the "
                "provided canonical-source chunks. Use the supplied source locators "
                "for source refs. Return only schema-valid JSON. "
                + _DIFFICULTY_GUIDANCE
                + " "
                + _PRACTICE_METADATA_GUIDANCE
                + " "
                + _AUDIT_GUIDANCE
            ),
            "context": asdict(context),
        },
    )


__all__ = [
    "CANONICAL_INGEST_PROMPT_VERSION",
    "CanonicalIngestContext",
    "ChunkKind",
    "ExtractionPlan",
    "SourceChunk",
    "SourceKind",
    "canonical_ingest_prompt",
]
