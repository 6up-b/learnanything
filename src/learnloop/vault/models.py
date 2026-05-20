from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from learnloop.config import LearnLoopConfig


class VaultModel(BaseModel):
    model_config = ConfigDict(extra="allow")


class SourceRef(VaultModel):
    ref_type: Literal["note", "canonical_source", "existing_entity", "session", "manual_context"]
    ref_id: str
    path: str | None = None
    locator: str | None = None
    quote: str | None = None
    quote_hash: str | None = None


class Provenance(VaultModel):
    origin: Literal["human", "codex_proposal", "canonical_extract", "import"] = "human"
    source_refs: list[SourceRef] = Field(default_factory=list)


class Goal(VaultModel):
    id: str
    title: str
    status: Literal["active", "paused", "completed"] = "active"
    priority: float = Field(default=0.5, ge=0.0, le=1.0)
    concept_anchors: list[str] = Field(default_factory=list)
    due_at: str | None = None
    created_at: str
    updated_at: str


class GoalsFile(VaultModel):
    schema_version: int = 1
    goals: list[Goal] = Field(default_factory=list)


class Concept(VaultModel):
    title: str
    type: Literal["concept", "procedure", "skill", "misconception"] = "concept"
    aliases: list[str] = Field(default_factory=list)
    description: str | None = None
    tags: list[str] = Field(default_factory=list)
    created_at: str
    updated_at: str
    id: str | None = None


class ConceptsFile(VaultModel):
    schema_version: int = 1
    concepts: dict[str, Concept] = Field(default_factory=dict)


class ConceptEdge(VaultModel):
    id: str
    relation_type: Literal["prerequisite", "confusable_with", "part_of", "related"]
    source: str
    target: str
    strength: float = 1.0
    rationale: str | None = None
    created_at: str
    updated_at: str


class RelationsFile(VaultModel):
    schema_version: int = 1
    edges: list[ConceptEdge] = Field(default_factory=list)


class SubjectMetadata(VaultModel):
    schema_version: int = 1
    id: str
    title: str
    status: Literal["active", "paused", "completed"] = "active"
    created_at: str
    updated_at: str


class ConceptGraph(VaultModel):
    schema_version: int = 1
    subject: str
    additional_concepts_in_scope: list[str] = Field(default_factory=list)
    exclude_concepts: list[str] = Field(default_factory=list)
    subject_ordering_hints: list[str] = Field(default_factory=list)


class RubricCriterion(VaultModel):
    id: str
    points: float
    description: str


class RubricFatalError(VaultModel):
    id: str
    description: str
    max_grade: int


class Rubric(VaultModel):
    max_points: int = 4
    criteria: list[RubricCriterion] = Field(default_factory=list)
    fatal_errors: list[RubricFatalError] = Field(default_factory=list)


class RubricAppliesTo(VaultModel):
    practice_mode: str


class DefaultRubric(VaultModel):
    schema_version: int = 1
    id: str
    applies_to: RubricAppliesTo
    rubric: Rubric


class LearningObject(VaultModel):
    schema_version: int = 1
    id: str
    title: str
    subjects: list[str]
    concept: str
    knowledge_type: str
    status: Literal["active", "dormant", "resolved"] = "active"
    contradicts: str | None = None
    summary: str
    prerequisites: list[str] = Field(default_factory=list)
    confusables: list[str] = Field(default_factory=list)
    difficulty_prior: float | None = Field(default=None, ge=0.0, le=1.0)
    tags: list[str] = Field(default_factory=list)
    provenance: Provenance = Field(default_factory=Provenance)
    created_at: str
    updated_at: str


class HintPolicy(VaultModel):
    max_useful_hints: int = 0
    fsrs_rating_cap_by_hint: dict[int | str, str] = Field(default_factory=dict)
    mastery_alpha_dampening_by_hint: dict[int | str, float] = Field(default_factory=dict)


class PracticeItem(VaultModel):
    schema_version: int = 1
    id: str
    learning_object_id: str
    subjects: list[str] | None = None
    practice_mode: str
    attempt_types_allowed: list[str] = Field(default_factory=list)
    evidence_facets: list[str] = Field(default_factory=list)
    evidence_weights: dict[str, float] = Field(default_factory=dict)
    prompt: str
    expected_answer: str | dict[str, Any]
    difficulty: float | None = Field(default=None, ge=0.0, le=1.0)
    tags: list[str] = Field(default_factory=list)
    hints: list[str] = Field(default_factory=list)
    hint_policy: HintPolicy = Field(default_factory=HintPolicy)
    grading_rubric: Rubric | None = None
    provenance: Provenance = Field(default_factory=Provenance)
    created_at: str
    updated_at: str


class ErrorType(VaultModel):
    id: str
    title: str
    description: str | None = None
    related_concepts: list[str] = Field(default_factory=list)
    severity_default: float = Field(default=0.5, ge=0.0, le=1.0)
    is_misconception: bool = False
    tags: list[str] = Field(default_factory=list)
    created_at: str
    updated_at: str


class ErrorTypesFile(VaultModel):
    schema_version: int = 1
    error_types: list[ErrorType] = Field(default_factory=list)


class Note(VaultModel):
    schema_version: int | None = None
    id: str
    subjects: list[str] = Field(default_factory=list)
    related_los: list[str] = Field(default_factory=list)
    related_concepts: list[str] = Field(default_factory=list)
    source_type: Literal["learner_note", "canonical_source", "imported"] = "learner_note"
    created_at: str | None = None
    updated_at: str | None = None
    path: str | None = None
    body: str = ""


@dataclass(frozen=True)
class Subject:
    metadata: SubjectMetadata
    body: str
    graph: ConceptGraph
    path: Path


@dataclass(frozen=True)
class DoctorIssue:
    code: str
    message: str
    path: Path | None = None


@dataclass
class LoadedVault:
    root: Path
    config: LearnLoopConfig
    concepts: dict[str, Concept] = field(default_factory=dict)
    edges: list[ConceptEdge] = field(default_factory=list)
    goals: list[Goal] = field(default_factory=list)
    subjects: dict[str, Subject] = field(default_factory=dict)
    learning_objects: dict[str, LearningObject] = field(default_factory=dict)
    practice_items: dict[str, PracticeItem] = field(default_factory=dict)
    default_rubrics: dict[str, Rubric] = field(default_factory=dict)
    error_types: dict[str, ErrorType] = field(default_factory=dict)
    notes: dict[str, Note] = field(default_factory=dict)
    issues: list[DoctorIssue] = field(default_factory=list)

    def learning_object_for_item(self, item: PracticeItem) -> LearningObject | None:
        return self.learning_objects.get(item.learning_object_id)

    def subjects_for_item(self, item: PracticeItem) -> list[str]:
        if item.subjects is not None:
            return item.subjects
        lo = self.learning_object_for_item(item)
        return lo.subjects if lo else []

    def rubric_for_item(self, item: PracticeItem) -> Rubric | None:
        return item.grading_rubric or self.default_rubrics.get(item.practice_mode)
