from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

EntityType = Literal["learning_object", "practice_item", "concept", "concept_edge", "rubric", "error_type"]
ProposalOperation = Literal["create", "update", "deactivate"]
ReviewRoute = Literal["auto_apply", "review_required", "reject"]


class SourceRef(BaseModel):
    ref_type: Literal["note", "canonical_source", "existing_entity", "session", "manual_context"]
    ref_id: str
    path: str | None = None
    locator: str | None = None
    quote: str | None = None
    quote_hash: str | None = None


class TargetEntity(BaseModel):
    entity_type: EntityType
    entity_id: str


class LearningObjectPatchPayload(BaseModel):
    id: str | None = None
    title: str | None = None
    concept_id: str | None = None
    subjects: list[str] | None = None
    knowledge_type: str | None = None
    status: Literal["active", "dormant", "resolved"] | None = None
    contradicts: str | None = None
    summary: str | None = None
    prerequisites: list[str] | None = None
    confusables: list[str] | None = None
    difficulty_prior: float | None = None
    tags: list[str] | None = None


class RubricCriterionPayload(BaseModel):
    id: str
    points: float
    description: str


class RubricFatalErrorPayload(BaseModel):
    id: str
    description: str
    max_grade: int


class RubricPatchPayload(BaseModel):
    target_practice_item_id: str | None = None
    max_points: int = 4
    criteria: list[RubricCriterionPayload]
    fatal_errors: list[RubricFatalErrorPayload] = Field(default_factory=list)


class PracticeItemPatchPayload(BaseModel):
    id: str | None = None
    learning_object_id: str | None = None
    subjects: list[str] | None = None
    practice_mode: str | None = None
    attempt_types_allowed: list[str] | None = None
    prompt: str | None = None
    expected_answer: str | dict | None = None
    grading_rubric: RubricPatchPayload | None = None
    evidence_facets: list[str] | None = None
    evidence_weights: dict[str, float] | None = None
    difficulty: float | None = None
    hints: list[str] | None = None
    hint_policy: dict | None = None
    tags: list[str] | None = None


class ConceptPatchPayload(BaseModel):
    id: str | None = None
    title: str | None = None
    type: Literal["concept", "procedure", "skill", "misconception"] | None = None
    aliases: list[str] | None = None
    description: str | None = None
    tags: list[str] | None = None


class ConceptEdgePatchPayload(BaseModel):
    source_concept_id: str
    target_concept_id: str
    relation_type: Literal["prerequisite", "confusable_with", "part_of", "related"]
    strength: float | None = None
    rationale: str | None = None


class ErrorTypePatchPayload(BaseModel):
    id: str | None = None
    title: str | None = None
    description: str | None = None
    related_concepts: list[str] | None = None
    severity_default: float | None = None
    is_misconception: bool | None = None
    tags: list[str] | None = None


AuthoringPayload = (
    LearningObjectPatchPayload
    | PracticeItemPatchPayload
    | ConceptPatchPayload
    | ConceptEdgePatchPayload
    | RubricPatchPayload
    | ErrorTypePatchPayload
)


class AuthoringProposalItem(BaseModel):
    client_item_id: str
    item_type: EntityType
    operation: ProposalOperation
    target: TargetEntity | None = None
    proposed_entity_id: str | None = None
    source_ref_ids: list[str] = Field(default_factory=list)
    rationale: str
    review_route: ReviewRoute
    payload: AuthoringPayload

    @model_validator(mode="before")
    @classmethod
    def coerce_payload_by_item_type(cls, data: Any) -> Any:
        if not isinstance(data, dict) or not isinstance(data.get("payload"), dict):
            return data
        payload_models = {
            "learning_object": LearningObjectPatchPayload,
            "practice_item": PracticeItemPatchPayload,
            "concept": ConceptPatchPayload,
            "concept_edge": ConceptEdgePatchPayload,
            "rubric": RubricPatchPayload,
            "error_type": ErrorTypePatchPayload,
        }
        model = payload_models.get(data.get("item_type"))
        if model is None:
            return data
        coerced = dict(data)
        coerced["payload"] = model.model_validate(data["payload"])
        return coerced

    @model_validator(mode="after")
    def validate_target_rules(self) -> "AuthoringProposalItem":
        if self.operation in {"update", "deactivate"} and self.target is None:
            raise ValueError("target is required for update/deactivate")
        if self.operation == "create" and self.target is not None and self.item_type != "concept_edge":
            raise ValueError("target is forbidden for create except concept_edge endpoint references")
        return self


class AuthoringProposal(BaseModel):
    summary: str
    source_refs: list[SourceRef] = Field(default_factory=list)
    items: list[AuthoringProposalItem] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_source_refs(self) -> "AuthoringProposal":
        known = {source.ref_id for source in self.source_refs}
        for item in self.items:
            unknown = set(item.source_ref_ids) - known
            if unknown:
                raise ValueError(f"unknown source_ref_ids for {item.client_item_id}: {sorted(unknown)}")
        return self


class CriterionEvidence(BaseModel):
    criterion_id: str
    points_awarded: float
    evidence: str
    notes: str | None = None


class ErrorAttribution(BaseModel):
    error_type: str
    severity: float = Field(ge=0.0, le=1.0)
    evidence: str
    is_misconception: bool = False
    target_evidence_families: list[str] = Field(default_factory=list)


class RepairSuggestion(BaseModel):
    practice_mode: str
    learning_object_id: str | None = None
    rationale: str


class GradingProposal(BaseModel):
    attempt_id: str
    practice_item_id: str
    rubric_score: int = Field(ge=0, le=4)
    criterion_evidence: list[CriterionEvidence] = Field(default_factory=list)
    fatal_errors: list[str] = Field(default_factory=list)
    error_attributions: list[ErrorAttribution] = Field(default_factory=list)
    grader_confidence: float = Field(ge=0.0, le=1.0)
    manual_review_recommended: bool = False
    feedback_md: str | None = None
    repair_suggestions: list[RepairSuggestion] = Field(default_factory=list)
