from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from learnloop.attempt_types import AttemptType

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


class ProposalItemAudit(BaseModel):
    audit_type: Literal[
        "deterministic_validator",
        "lean",
        "symbolic_solver",
        "numeric_check",
        "step_by_step_trace",
    ]
    status: Literal["passed", "failed", "not_applicable_with_trace"]
    summary: str
    trace: str | None = Field(
        default=None,
        description=(
            "REQUIRED (non-null, non-empty) when status is 'not_applicable_with_trace': "
            "explain why no deterministic check applies and walk through how the "
            "expected answer was verified by hand."
        ),
    )
    validator_name: str | None = None
    validator_version: str | None = None


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
    difficulty_source: Literal["author", "llm_estimate", "empirical", "calibrated"] | None = None
    tags: list[str] | None = None


class RubricCriterionPayload(BaseModel):
    id: str
    points: float = Field(gt=0.0, le=4.0)
    description: str
    # Teach-back rubrics are two-tiered: "core" probes one evidence facet,
    # "transfer" stress-tests solid knowledge (discounted evidence mass).
    tier: Literal["core", "transfer"] = "core"


class RubricFatalErrorPayload(BaseModel):
    id: str
    description: str
    max_grade: int = Field(ge=0, le=4)
    # spec §1.2: authored link from a fatal error to the registry belief it catches.
    misconception_id: str | None = None


class RubricPatchPayload(BaseModel):
    target_practice_item_id: str | None = None
    max_points: int = Field(default=4, ge=1, le=4)
    criteria: list[RubricCriterionPayload]
    fatal_errors: list[RubricFatalErrorPayload] = Field(default_factory=list)


class PracticeItemPatchPayload(BaseModel):
    id: str | None = None
    learning_object_id: str | None = None
    subjects: list[str] | None = None
    practice_mode: str | None = None
    attempt_types_allowed: list[AttemptType] | None = None
    prompt: str | None = None
    expected_answer: str | dict | None = None
    grading_rubric: RubricPatchPayload | None = None
    evidence_facets: list[str] | None = None
    evidence_weights: dict[str, float] | None = Field(
        default=None,
        description=(
            "REQUIRED whenever evidence_facets is set: map EVERY listed facet id to "
            "its weight (weights should sum to 1.0). An empty object is invalid."
        ),
    )
    criterion_facet_weights: dict[str, dict[str, float]] | None = Field(
        default=None,
        description=(
            "REQUIRED whenever grading_rubric is present: map EVERY rubric criterion "
            "id to {facet_id: weight}. An empty object is invalid — cover each "
            "criterion, reusing ids from evidence_facets."
        ),
    )
    difficulty: float | None = None
    difficulty_source: Literal["author", "llm_estimate", "empirical", "calibrated"] | None = None
    retrieval_demand: float | None = Field(
        default=None,
        description=(
            "REQUIRED on generated items, in [0,1]: how much unaided recall the item "
            "demands (0=fully cued recognition, 1=free recall with no cues)."
        ),
    )
    transfer_distance: float | None = Field(
        default=None,
        description=(
            "REQUIRED on generated items, in [0,1]: how far the item sits from the "
            "source material's surface form (0=near/verbatim, 1=far transfer to a "
            "novel situation)."
        ),
    )
    scaffold_level: float | None = Field(
        default=None,
        description=(
            "REQUIRED on generated items, in [0,1]: how much support the prompt "
            "provides (0=no scaffolding, 1=heavily scaffolded/step-by-step)."
        ),
    )
    surface_family: str | None = Field(
        default=None,
        description=(
            "REQUIRED on generated items: short snake_case id for the item's surface "
            "form (e.g. 'numeric_compute', 'concept_explain'). Reuse the Learning "
            "Object's existing surface_families from context when the form matches; "
            "mint a new id only for a genuinely new surface."
        ),
    )
    # spec §5.2.2: the categorically-divergent answer a holder of the targeted
    # belief would give on a diagnostic item. Feeds the sim gate (§6) and the
    # §5.3 review check; None on ordinary (non-diagnostic) items.
    misconception_consistent_answer: str | None = None
    repair_targets: list[str] | None = Field(
        default=None,
        description=(
            "REQUIRED (non-empty) on generated items: the evidence facet ids and/or "
            "rubric fatal error ids this item can diagnose or repair. Every entry "
            "must exactly match an id in evidence_facets or grading_rubric.fatal_errors."
        ),
    )
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
    audit: ProposalItemAudit | None = None
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
        if self.operation == "create" and self.item_type not in {"concept_edge", "rubric"}:
            payload_id = getattr(self.payload, "id", None)
            if self.proposed_entity_id is None and payload_id is None:
                raise ValueError("proposed_entity_id is required for create unless payload owns id")
        return self


class AuthoringProposal(BaseModel):
    summary: str
    source_refs: list[SourceRef] = Field(default_factory=list)
    items: list[AuthoringProposalItem] = Field(default_factory=list)


class CriterionEvidence(BaseModel):
    criterion_id: str
    points_awarded: float
    evidence: str
    notes: str | None = None
    learner_confidence: Literal["confident", "hedged", "absent", "unknown"] | None = None


class ErrorAttribution(BaseModel):
    error_type: str
    severity: float | None = Field(default=None, ge=0.0, le=1.0)
    evidence: str
    is_misconception: bool = False
    # spec §2.1 (G1): required when is_misconception=True, but not enforced here so
    # legacy providers that omit it still validate — the belief in learner-model
    # terms, and what a holder of the belief would answer on this item.
    misconception_statement: str | None = None
    misconception_consistent_answer: str | None = None
    target_evidence_families: list[str] = Field(default_factory=list)
    target_criterion_ids: list[str] = Field(default_factory=list)


class RepairSuggestion(BaseModel):
    practice_mode: str
    learning_object_id: str | None = None
    rationale: str
    target_evidence_families: list[str] = Field(default_factory=list)


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


QuestionType = Literal["clarification", "prerequisite", "mechanism", "strategy", "verification", "other"]


class TeachBackQuestion(BaseModel):
    """One naive-student follow-up question in a teach-back conversation.

    The persona never corrects, confirms, or reveals; the service supplies the
    target criterion/facets in the context and stores the question as an AI
    transcript turn.
    """

    question_md: str


class TutorAnswer(BaseModel):
    """Structured tutor Q&A output: the answer plus the question classification.

    ``facets`` must be a subset of the candidate facets supplied in the
    context; the service drops anything else before persisting.
    """

    answer_md: str
    question_type: QuestionType = "other"
    facets: list[str] = Field(default_factory=list)
    # §13.4 (probe redesign): `epistemic` = the question signals missing or
    # uncertain knowledge; `interaction_preference` = the learner is asking for
    # a different explanation style, pace, scaffold level, or a direct answer.
    # Preference questions change tutor policy, not mastery belief.
    question_channel: Literal["epistemic", "interaction_preference"] = "epistemic"


class MisconceptionMatch(BaseModel):
    """LLM verdict for registry normalization (spec §2.2.2).

    ``decision == "same"`` means the graded belief is the same as the registry
    row named by ``misconception_id``; ``"new"`` means it is a distinct belief
    and a fresh row should be inserted. When unsure the model should prefer
    ``"new"`` (spec §9: avoid over-merging distinct beliefs).
    """

    decision: Literal["same", "new"]
    misconception_id: str | None = None


class PromotionAnalysis(BaseModel):
    """Step-0 extraction for tutor-question promotion (spec_tutor_promotion.md §3).

    ``attributed_facets`` are the evidence facet ids the tutor's socratic question
    exercises — existing ids from the origin LO vocabulary are strongly preferred;
    a new id is minted only when nothing covers the probe. ``question_nature``
    classifies the probe's cognitive demand and keys the gap-route frontier
    interpretation (§3 G2). ``attempted_in_thread`` records whether the learner
    tried the socratic question in-thread and failed, vs never engaged — a
    calibration feature, never an algorithmic input. ``covered_by_practice_item_id``
    (nullable) names an existing item that already exercises the same probe (same
    facets + substantially the same demand); when set, the dedup short-circuit
    fires and nothing is authored (§3 Step 0).
    """

    attributed_facets: list[str] = Field(default_factory=list)
    question_nature: Literal[
        "core_recall", "mechanism", "transfer", "edge_case", "what_if"
    ] = "core_recall"
    attempted_in_thread: bool = False
    covered_by_practice_item_id: str | None = None


class ProbeInstanceSurface(BaseModel):
    """One LLM-generated Item Instance surface for an admitted family/card
    binding (probe redesign §9.2/§9.4).

    The family template owns the measurement pattern, rubric structure, and
    signature fatal errors; the model supplies only surface wording. Every
    surface still passes the instance-level structural gate
    (``instance_gate_errors``) before it can be persisted, so a leaky or
    ungrounded surface is dropped, never served.
    """

    surface_suffix: str
    prompt_md: str
    expected_answer_md: str


class ProbeInstanceSurfaces(BaseModel):
    """Batch of surface-varied instances for one family/card binding."""

    surfaces: list[ProbeInstanceSurface] = Field(default_factory=list)


class ProbeDialogueTurn(BaseModel):
    """One adaptive dialogue microprobe turn surface (probe redesign §8.1).

    Generated conditioned on the learner's prior committed answers in the
    block, so a `reason` turn asks about THEIR answer and a `counterfactual`
    turn minimally perturbs THEIR committed case. The turn must stay a pure
    measurement: no teaching, hinting, correcting, or revealing whether any
    prior answer was right. Falls back to the parametric turn templates when
    the provider is unavailable.
    """

    prompt_md: str
    expected_answer_md: str


class ProbeFamilyTrial(BaseModel):
    """One simulated planted-state response for the family admission gate
    (probe redesign §9.6).

    ``matched_outcome`` is the outcome class (from the family's observation
    alphabet) the model judges a careful grader would assign to ``answer`` —
    the deterministic gate then checks whether the planted slot is recovered
    as the likelihood argmax of that outcome. ``non_applicable_control``
    trials present a scenario where the family's trigger conditions do not
    hold; a sound family must not fire a signature outcome there.
    """

    hypothesis_slot: str
    answer: str
    matched_outcome: str
    non_applicable_control: bool = False


class ProbeFamilyTrials(BaseModel):
    """All planted trials for one family admission gate run (one call)."""

    trials: list[ProbeFamilyTrial] = Field(default_factory=list)


class DiagnosticTrialResult(BaseModel):
    """One simulated student's answer + whether the keyed fatal error fires.

    ``answer`` is the student's natural-language response (never verbatim the
    canned misconception-consistent string); ``fires`` is the model's judgment of
    whether a grader would attribute the misconception-keyed fatal error to it.
    """

    answer: str
    fires: bool


class DiagnosticTrials(BaseModel):
    """Codex answers-under-belief for the sim discrimination gate (spec §6).

    ``planted`` are learners who genuinely HOLD the targeted belief; ``clean``
    are competent learners. One structured call returns all trials at once so the
    gate spends a single provider request regardless of trial count.
    """

    planted: list[DiagnosticTrialResult] = Field(default_factory=list)
    clean: list[DiagnosticTrialResult] = Field(default_factory=list)
