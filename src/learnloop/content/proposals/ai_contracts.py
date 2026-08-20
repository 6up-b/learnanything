"""Feature-owned authoring-proposal AI contract."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Annotated, Any, Literal

from pydantic import (
    BaseModel,
    BeforeValidator,
    Field,
    ValidationError,
    WithJsonSchema,
    model_validator,
)

from learnloop.ai.schemas import WireModel, describe_wire_validation_error
from learnloop.ai.transport import render_structured_prompt
from learnloop.attempt_types import AttemptType

EntityType = Literal[
    "learning_object",
    "practice_item",
    "concept",
    "concept_edge",
    "rubric",
    "error_type",
]
ProposalOperation = Literal["create", "update", "deactivate"]
ReviewRoute = Literal["auto_apply", "review_required", "reject"]

class FacetWeightPayload(WireModel):
    """One facet-weight pair (strict-schema-safe map entry)."""

    facet_id: str = ""
    weight: float = 0.0


class CriterionFacetWeightsPayload(WireModel):
    """Facet weights for one rubric criterion (strict-schema-safe map entry)."""

    criterion_id: str = ""
    weights: list[FacetWeightPayload] = Field(default_factory=list)


class CheckpointDependencyPayload(WireModel):
    """One checkpoint's prerequisites (strict-schema-safe map entry)."""

    checkpoint_id: str = ""
    depends_on: list[str] = Field(default_factory=list)


def _inlined_json_schema(model: type[BaseModel]) -> dict[str, Any]:
    """Return ``model``'s schema with every ``$ref`` resolved in place.

    ``WithJsonSchema`` splices its value in verbatim, so a surviving
    ``#/$defs/...`` pointer would dangle against the enclosing document.
    """

    schema = model.model_json_schema()
    defs = schema.pop("$defs", {})

    def inline(node: Any) -> Any:
        if isinstance(node, list):
            return [inline(item) for item in node]
        if not isinstance(node, dict):
            return node
        ref = node.get("$ref")
        if isinstance(ref, str) and ref.startswith("#/$defs/"):
            return inline(defs[ref.removeprefix("#/$defs/")])
        return {key: inline(child) for key, child in node.items()}

    return inline(schema)


def _pair_list_schema(model: type[BaseModel]) -> WithJsonSchema:
    return WithJsonSchema({"type": "array", "items": _inlined_json_schema(model)})


def _facet_weight_map(value: Any) -> Any:
    """Accept ``[{facet_id, weight}, ...]`` as well as ``{facet_id: weight}``."""

    if not isinstance(value, list):
        return value
    weights: dict[str, float] = {}
    for entry in value:
        if isinstance(entry, FacetWeightPayload):
            entry = entry.model_dump()
        if not isinstance(entry, dict):
            continue
        facet_id = str(entry.get("facet_id") or "")
        if facet_id:
            weights[facet_id] = entry.get("weight", 0.0)
    return weights


def _criterion_facet_weight_map(value: Any) -> Any:
    """Accept ``[{criterion_id, weights}, ...]`` as well as the nested map."""

    if not isinstance(value, list):
        return value
    mapped: dict[str, Any] = {}
    for entry in value:
        if isinstance(entry, CriterionFacetWeightsPayload):
            entry = entry.model_dump()
        if not isinstance(entry, dict):
            continue
        criterion_id = str(entry.get("criterion_id") or "")
        if criterion_id:
            mapped[criterion_id] = _facet_weight_map(entry.get("weights") or [])
    return mapped


def _checkpoint_dependency_map(value: Any) -> Any:
    """Accept ``[{checkpoint_id, depends_on}, ...]`` as well as the map form."""

    if not isinstance(value, list):
        return value
    mapped: dict[str, Any] = {}
    for entry in value:
        if isinstance(entry, CheckpointDependencyPayload):
            entry = entry.model_dump()
        if not isinstance(entry, dict):
            continue
        checkpoint_id = str(entry.get("checkpoint_id") or "")
        if checkpoint_id:
            mapped[checkpoint_id] = entry.get("depends_on") or []
    return mapped


EvidenceWeightMap = Annotated[
    dict[str, float],
    BeforeValidator(_facet_weight_map),
    _pair_list_schema(FacetWeightPayload),
]
CriterionFacetWeightMap = Annotated[
    dict[str, dict[str, float]],
    BeforeValidator(_criterion_facet_weight_map),
    _pair_list_schema(CriterionFacetWeightsPayload),
]
CheckpointDependencyMap = Annotated[
    dict[str, list[str]],
    BeforeValidator(_checkpoint_dependency_map),
    _pair_list_schema(CheckpointDependencyPayload),
]


class SourceRef(WireModel):
    ref_type: Literal["note", "canonical_source", "existing_entity", "session", "manual_context"]
    ref_id: str
    path: str | None = None
    locator: str | None = None
    quote: str | None = None
    quote_hash: str | None = None
    # Reader/source-library citations carry immutable source-layer identity in
    # addition to the proposal-local ``ref_id``.  Older note-backed authoring
    # refs omit these fields and retain their existing behavior.
    source_id: str | None = None
    revision_id: str | None = None
    extraction_id: str | None = None
    span_ids: list[str] = Field(default_factory=list)
    span_hash: str | None = None
    section_id: str | None = None
    learning_object_ids: list[str] = Field(default_factory=list)


class TargetEntity(WireModel):
    entity_type: EntityType
    entity_id: str


class ProposalItemAudit(WireModel):
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


class LearningObjectPatchPayload(WireModel):
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


class CriterionTargetPayload(WireModel):
    """One ``(facet, capability, role)`` observation a criterion makes.

    Mirrors :class:`SynthCriterionTarget` (the synthesis lane's equivalent) and
    the vault-side ``CriterionTarget``, closing the asymmetry
    ``spec_measurement_efficiency_v1.md`` F2 measured: the practice-generation
    lane could not author targets at all, so ``compile_criterion_targets`` fell
    back to every criterion -> ``primary`` at the item's single declared
    capability, and the ``supporting`` role (weight 0.3, banked as *embedded*
    credit) was structurally unreachable from generated practice.

    ``role`` here is the **observation** role and has nothing to do with the
    ``role`` on a blueprint component (``required`` / ``alternative`` /
    ``integration``); the two vocabularies are disjoint and the prompt rules say
    so, because conflating them is the obvious authoring failure mode.

    * ``primary`` — the step this criterion owns; full weight.
    * ``supporting`` — a facet that step *consumes*. Per §3.A1 guard 1 it earns
      credit only where the graded trace shows the facet actually exercised;
      absent that observation it is recorded as an
      ``unexercised_supporting_target`` and confers nothing.
    """

    facet: str = ""
    capability: Literal[
        "retrieval",
        "schema_interpretation",
        "procedure_execution",
        "method_selection",
        "coordination",
    ] = "retrieval"
    role: Literal["primary", "supporting"] = "primary"


class RubricCriterionPayload(WireModel):
    id: str
    points: float = Field(gt=0.0)
    description: str
    # Teach-back rubrics are two-tiered: "core" probes one evidence facet,
    # "transfer" stress-tests solid knowledge (discounted evidence mass).
    tier: Literal["core", "transfer"] = "core"
    # Causal-attribution P0b: an empty facet map is honest only when the
    # criterion declares what kind of measurement it actually is.
    measurement_status: Literal[
        "direct", "supporting", "composite", "item_local", "no_canonical_facet"
    ] | None = None
    # Meas §3.A1: the conjunctive-item channel. Authored targets win verbatim in
    # ``compile_criterion_targets``; an empty list keeps the legacy compile
    # (every mapped facet -> primary at the item's declared capability), so this
    # field is strictly additive for every item authored before it existed.
    targets: list[CriterionTargetPayload] = Field(default_factory=list)
    # Criterion dependency DAG: first-error localization (§5.3) treats a
    # criterion whose dependency failed as unassessable rather than failed. A
    # conjunctive item is exactly where this matters — without it, one early
    # divergence reads as failure on every later step of the same task.
    depends_on: list[str] = Field(default_factory=list)


class RubricFatalErrorPayload(WireModel):
    id: str
    description: str
    max_grade: int = Field(ge=0)
    # spec §1.2: authored link from a fatal error to the registry belief it catches.
    misconception_id: str | None = None


class RubricPatchPayload(WireModel):
    target_practice_item_id: str | None = None
    max_points: int = Field(default=4, ge=1)
    criteria: list[RubricCriterionPayload]
    fatal_errors: list[RubricFatalErrorPayload] = Field(default_factory=list)

    @model_validator(mode="after")
    def derive_max_points_from_criteria(self) -> "RubricPatchPayload":
        if not self.criteria:
            return self
        total = sum(float(criterion.points) for criterion in self.criteria)
        rounded = int(round(total))
        if total <= 0 or abs(total - rounded) > 1e-6:
            raise ValueError("rubric criterion points must sum to a positive integer")
        self.max_points = rounded
        return self


class TaskFeaturesPayload(WireModel):
    """Point TaskFeature vector (p1_launch schema, spec_p1 §3.4). Generated items
    declare where they sit in task-feature space so the deterministic rung gate
    can check them against the target waypoint."""

    complexity: int | None = Field(default=None, ge=0, le=4)
    transfer: Literal["same_context", "near", "far", "novel_combination"] | None = None
    representation: list[Literal["symbolic", "verbal", "diagram", "code", "physical"]] | None = None
    response: (
        Literal["recognize", "short_constructed", "long_constructed", "structured_steps", "performance"] | None
    ) = None
    scaffolding: Literal["none", "cue", "partial", "worked"] | None = None
    span: Literal["atomic", "single_step", "multi_step", "whole_task"] | None = None
    tools: list[Literal["closed_book", "open_book", "calculator", "code", "references", "collaboration"]] | None = None


class TraceRecipePayload(WireModel):
    id: str
    checkpoints: list[str] = Field(default_factory=list)
    dependencies: CheckpointDependencyMap = Field(default_factory=dict)


class TraceContractPayload(WireModel):
    status: Literal["available", "no_reliable_decomposition"] = "available"
    recipes: list[TraceRecipePayload] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_trace_contract(self) -> "TraceContractPayload":
        if self.status == "no_reliable_decomposition" and self.recipes:
            raise ValueError("no_reliable_decomposition trace contract cannot contain recipes")
        if self.status == "available" and not self.recipes:
            raise ValueError("available trace contract requires at least one recipe")
        recipe_ids = [recipe.id for recipe in self.recipes]
        if len(set(recipe_ids)) != len(recipe_ids):
            raise ValueError("trace contract has duplicate recipe ids")
        for recipe in self.recipes:
            checkpoints = set(recipe.checkpoints)
            if len(checkpoints) != len(recipe.checkpoints):
                raise ValueError(f"trace recipe {recipe.id} has duplicate checkpoints")
            unknown = set(recipe.dependencies) - checkpoints
            unknown.update(
                dependency
                for dependencies in recipe.dependencies.values()
                for dependency in dependencies
                if dependency not in checkpoints
            )
            if unknown:
                raise ValueError(
                    f"trace recipe {recipe.id} has unknown dependency checkpoints: "
                    + ", ".join(sorted(unknown))
                )
        return self


class DiscriminationProfilePayload(WireModel):
    """A5's authored candidate shape (``spec_measurement_efficiency_v1`` §3.A5).

    Mirrors the vault-side :class:`~learnloop.vault.models.DiscriminationProfile`
    exactly. Today an item can author ONE link from a fatal error to a belief
    (``RubricFatalErrorPayload.misconception_id``): a detector that fires or does
    not. This is the shape behind the detector -- what a holder of the belief
    actually writes -- authored once and reused by §3.0's persona gate, the
    grading prior, and A4's commissioning.

    There is deliberately no probability, weight, or ``expected`` field. A
    profile is a candidate the diagnostician may reject (``no_profile_applies``
    is a first-class outcome); a number here would read as a posterior, which is
    exactly the causal §1 principle 4 violation §3.A5 warns the feature against.
    """

    id: str
    hypothesis: str = Field(
        description=(
            "The belief in learner-model terms -- what the learner thinks is TRUE, "
            "not a description of the wrong answer."
        )
    )
    observable_signature: str = Field(
        description=(
            "What a holder of `hypothesis` would actually write ON THIS ITEM. Must "
            "be categorically different from expected_answer, or the item is blind "
            "to the belief it claims to profile and is rejected by the gate."
        )
    )
    misconception_id: str | None = None
    facet_id: str | None = None
    fails_criteria: list[str] = Field(default_factory=list)
    distinguishing_features: list[str] = Field(default_factory=list)
    source: Literal["misconception_registry", "facet_error_signature", "authored"] = "authored"


class DifferingComponentPayload(WireModel):
    """The one ``(facet, capability)`` requirement an A4 pair differs on (§3.A4)."""

    facet: str
    capability: Literal[
        "retrieval",
        "schema_interpretation",
        "procedure_execution",
        "method_selection",
        "coordination",
    ]
    structural_change: str | None = Field(
        default=None,
        description=(
            "What changes in the STRUCTURE of the correct answer -- does a "
            "precondition hold, is the theorem applicable. Never merely different "
            "values: that is a clone, and kinship refuses to count it twice."
        ),
    )


class PlantedErrorPayload(WireModel):
    """One registry-sourced error planted in an A3 worked solution (§3.A3).

    ``source`` has no ``freehand`` arm on purpose -- "a freehand error is an
    untyped instrument" -- and ``required_repair`` is what keeps the item on the
    construction side of the no-recognition-items gate.
    """

    id: str
    step_ref: str = Field(
        description="Which step of worked_solution_md carries the error."
    )
    source: Literal["misconception_registry", "facet_error_signature"]
    error_signature: str = Field(
        description=(
            "The registry misconception signature or facet error_signature planted, "
            "VERBATIM. The gate compares against this exact string."
        )
    )
    required_repair: str = Field(
        description=(
            "What a correct repair must produce. Never empty: the learner must "
            "REPAIR the error, not flag it."
        )
    )
    misconception_id: str | None = None
    facet_id: str | None = None


class ErrorHuntPayload(WireModel):
    """An A3 worked solution plus its plants, or the clean rotation (§3.A3).

    An empty ``planted_errors`` list is the clean-solution rotation, not an
    error: it is "strictly more informative", because a learner who finds an
    error in correct work has handed the system a misconception directly.
    """

    worked_solution_md: str
    planted_errors: list[PlantedErrorPayload] = Field(default_factory=list)


class LadderedStemPayload(WireModel):
    """One part of an A2 laddered stem (§3.A2).

    Parts are separate items sharing ``stem_id`` (and
    ``evidence_fingerprint.shared_stimulus_id``), each declaring its own
    ``capability`` -- because credit is filed per ``(facet, capability)`` cell
    and one item can only declare one.
    """

    stem_id: str
    part_index: int = Field(ge=0)
    part_count: int = Field(default=1, ge=1)
    stimulus_md: str | None = None


class VariantManipulationPayload(WireModel):
    axis: str
    direction: Literal["increase", "decrease", "hold"]
    rationale: str | None = None


class VariantAuthoringContractPayload(WireModel):
    variant_kind: Literal["easier", "harder", "rung_shift"]
    intended_manipulations: list[VariantManipulationPayload] = Field(default_factory=list)
    incidental_changes: list[str] = Field(default_factory=list)
    held_constant: list[str] = Field(default_factory=list)
    preserves_checkpoints: list[str] = Field(default_factory=list)
    deepens_checkpoints: list[str] = Field(default_factory=list)
    drops_checkpoints: list[str] = Field(default_factory=list)


class PracticeItemPatchPayload(WireModel):
    id: str | None = None
    learning_object_id: str | None = None
    subjects: list[str] | None = None
    practice_mode: str | None = None
    attempt_types_allowed: list[AttemptType] | None = None
    prompt: str | None = None
    expected_answer: str | dict | None = None
    grading_rubric: RubricPatchPayload | None = None
    evidence_facets: list[str] | None = None
    evidence_weights: EvidenceWeightMap | None = Field(
        default=None,
        description=(
            "REQUIRED whenever evidence_facets is set: one entry per listed facet id "
            "with its weight (weights should sum to 1.0). An empty list is invalid."
        ),
    )
    criterion_facet_weights: CriterionFacetWeightMap | None = Field(
        default=None,
        description=(
            "One entry per rubric criterion that genuinely measures a canonical facet. "
            "An empty list is valid when the criterion declares item_local or "
            "no_canonical_facet measurement_status."
        ),
    )
    trace_contract: TraceContractPayload | None = None
    variant_contract: VariantAuthoringContractPayload | None = None
    difficulty: float | None = None
    difficulty_source: Literal["author", "llm_estimate", "empirical", "calibrated"] | None = None
    capability: Literal[
        "retrieval", "schema_interpretation", "procedure_execution", "method_selection", "coordination"
    ] | None = Field(
        default=None,
        description=(
            "REQUIRED on generated items: the closed-vocabulary observation mode this "
            "item exercises. Match the target's waypoint capability exactly."
        ),
    )
    task_features: TaskFeaturesPayload | None = Field(
        default=None,
        description=(
            "REQUIRED on generated items: the item's point in task-feature space. Set "
            "every dimension the target waypoint declares to the target value; the "
            "deterministic rung gate rejects items that overshoot the waypoint."
        ),
    )
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
    misconception_consistent_answer: str | None = Field(
        default=None,
        description=(
            "Leave null for ordinary practice. Populating this makes the item a "
            "misconception DIAGNOSTIC, and a diagnostic owes a detector: the "
            "grading_rubric MUST then carry a fatal error whose misconception_id "
            "names a REGISTERED (canonical) misconception. Never speculate a "
            "misconception that is not in the provided context."
        ),
    )
    # Meas §3.A5. Optional and empty by default: a plain practice item makes no
    # discrimination claim and owes no profiles. Authoring ONE promotes the item
    # to the §3.0 gate's hard tier, which is the intended trade -- a claim about
    # causes has to be checkable.
    discrimination_profiles: list[DiscriminationProfilePayload] | None = Field(
        default=None,
        description=(
            "Meas A5: per plausible candidate hypothesis, what a holder of that "
            "hypothesis visibly produces on THIS item. A prior over causes for the "
            "diagnostician and the oracle for the authoring gate -- never a "
            "constraint on diagnosis."
        ),
    )
    # Meas §3.A4. Both fields are set on BOTH members of a pair; a one-sided
    # `contrast_of` is a dangling reference the gate rejects.
    contrast_of: str | None = Field(
        default=None,
        description=(
            "Meas A4: the practice item id of this item's contrast-pair "
            "counterpart. Two prompts differing in exactly ONE requirement."
        ),
    )
    differing_component: DifferingComponentPayload | None = Field(
        default=None,
        description=(
            "Meas A4: the single (facet, capability) requirement the pair differs "
            "on. REQUIRED whenever contrast_of is set."
        ),
    )
    error_hunt: ErrorHuntPayload | None = Field(
        default=None,
        description=(
            "Meas A3: a fully worked solution the learner must find and REPAIR the "
            "errors in. Plant only from the misconception registry or a facet's "
            "error_signatures; never state how many errors there are; an empty "
            "planted_errors list is the deliberate clean-solution rotation."
        ),
    )
    laddered_stem: LadderedStemPayload | None = Field(
        default=None,
        description=(
            "Meas A2: this item's part of a shared stimulus whose parts climb the "
            "capability ladder. Every part of one stem shares stem_id and declares "
            "its own capability."
        ),
    )
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


class ConceptPatchPayload(WireModel):
    id: str | None = None
    title: str | None = None
    type: Literal["concept", "procedure", "skill", "misconception"] | None = None
    aliases: list[str] | None = None
    description: str | None = None
    tags: list[str] | None = None


class ConceptEdgePatchPayload(WireModel):
    source_concept_id: str
    target_concept_id: str
    relation_type: Literal["prerequisite", "confusable_with", "part_of", "related"]
    strength: float | None = None
    rationale: str | None = None


class ErrorTypePatchPayload(WireModel):
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


class AuthoringProposalItem(WireModel):
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
        try:
            coerced["payload"] = model.model_validate(data["payload"])
        except ValidationError as exc:
            # Without this, a forbidden extra inside the payload is reported
            # against the ``AuthoringPayload`` *union*: pydantic retries the
            # payload against all six members and emits six failures, none of
            # which names the model the item_type actually selected. Re-raising
            # here pins the diagnosis to the one model that was supposed to
            # accept it, which is the only form a repair turn can act on.
            raise ValueError(describe_wire_validation_error(model, exc)) from exc
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


@dataclass(frozen=True)
class AuthoringContext:
    vault_root: str
    source_ids: list[str]
    instructions: str | None = None
    subjects: list[str] = field(default_factory=list)
    source_refs: list[dict] = field(default_factory=list)
    concepts: list[dict] = field(default_factory=list)
    notes: list[dict] = field(default_factory=list)
    learning_objects: list[dict] = field(default_factory=list)
    practice_items: list[dict] = field(default_factory=list)
    goals: list[dict] = field(default_factory=list)
    focus_concepts: list[str] = field(default_factory=list)
    focus_facets: list[str] = field(default_factory=list)


class AuthoringProposal(WireModel):
    summary: str
    source_refs: list[SourceRef] = Field(default_factory=list)
    items: list[AuthoringProposalItem] = Field(default_factory=list)


AUTHORING_PROMPT_VERSION = "mvp-0.9-criterion-total-scoring"
DIAGNOSTIC_AUTHORING_PROMPT_VERSION = "mvp-0.5-diagnostic-authoring"
PRACTICE_GENERATION_PROMPT_VERSION = "mvp-1.2-criterion-total-scoring"

DIAGNOSTIC_AUTHORING_PROMPT = """\
Author ONE diagnostic Practice Item that discriminates the target misconception \
below. The item must satisfy ALL of these constraints (spec §5.2):

1. Forced application to a concrete instance: the learner must APPLY their model \
to a specific case and commit to an output (compute a value or choose between \
operators; commit to a holding on a novel fact pattern; predict a mechanism's \
behaviour under a stated change) — not restate or re-derive the rule.
2. Documented categorical contrast: provide BOTH `expected_answer` and \
`misconception_consistent_answer`; they must differ CATEGORICALLY (different \
value, holding, choice, or predicted behaviour), never merely in emphasis or \
completeness.
3. Misconception-keyed fatal error: the grading rubric must carry at least one \
fatal error with `misconception_id` set to the target misconception id, \
describing its signature.
4. Surface shift: `surface_family` MUST differ from the source item's \
surface_family.
5. Minimal footprint: `evidence_facets` must be a subset of the implicated \
facets; do NOT re-test criteria the learner already demonstrated.
"""

_DIFFICULTY_GUIDANCE = (
    "Estimate `difficulty` for every Practice Item and `difficulty_prior` for every "
    "Learning Object on this [0,1] anchor scale: 0.0-0.2 trivial/recognition, "
    "0.2-0.4 easy recall, 0.4-0.5 basic application, 0.5 normal target-level, "
    "0.6-0.8 transfer/multi-step, 0.8-1.0 difficult synthesis/adversarial. "
    "Set `difficulty_source = \"llm_estimate\"` on every item you estimate."
)

_PRACTICE_METADATA_GUIDANCE = (
    "For every generated Practice Item, include reward-facing metadata: "
    "`evidence_facets`, `evidence_weights`, `criterion_facet_weights` when a rubric "
    "exists, `retrieval_demand`, `transfer_distance`, `scaffold_level`, "
    "`surface_family`, and `repair_targets`. Link a rubric criterion to a facet "
    "only when the criterion genuinely measures that facet's claim. Set each "
    "criterion's `measurement_status`; `item_local` and `no_canonical_facet` "
    "criteria intentionally have no criterion_facet_weights entry. When the "
    "expected answer has a reliable step structure, include a nullable "
    "`trace_contract` with named checkpoint recipes and dependencies; otherwise "
    "declare `no_reliable_decomposition` rather than inventing steps. Generated "
    "Set each grading rubric's `max_points` to the positive integral sum of its "
    "criterion points. Criterion points are the scoring authority; there is no "
    "global four-point ceiling. "
    "`repair_targets` must name evidence facets or rubric fatal error ids."
)

_FACET_VOCABULARY_GUIDANCE = (
    "Facet and surface vocabulary: each Learning Object in context lists "
    "existing_evidence_facets (facet ids already established for it) and "
    "existing_surface_families. When an item probes knowledge an existing facet "
    "names, reuse that exact facet id in "
    "evidence_facets/evidence_weights/criterion_facet_weights; mint a new facet id "
    "only when the item probes knowledge no existing facet covers — never restate "
    "an existing facet under a new name. Likewise reuse existing surface_family "
    "ids when the item's surface form matches one."
)

_AUDIT_GUIDANCE = (
    "Every generated Practice Item must carry an `audit`. Use status `passed` or "
    "`failed` when a deterministic check (numeric check, symbolic solver, "
    "step-by-step trace) ran. For conceptual/constructed-response items with no "
    "deterministic check, use status `not_applicable_with_trace` and you MUST fill "
    "`trace` with a short manual verification walkthrough of the expected answer; "
    "a null or empty trace fails validation."
)


def authoring_prompt(context: AuthoringContext) -> str:
    return render_structured_prompt(
        "learnloop authoring proposal",
        AUTHORING_PROMPT_VERSION,
        {
            "task": (
                "Create a LearnLoop AuthoringProposal for useful Learning Objects, "
                "Practice Items, concept edges, or rubric updates. Persist nothing; "
                "return only schema-valid JSON. "
                "When context.focus_concepts is non-empty, concentrate the proposal "
                "on those concept ids: prefer Learning Objects and Practice Items "
                "that teach or assess them. When context.focus_facets is non-empty, "
                "target those evidence facets in generated Practice Items "
                "(evidence_facets/evidence_weights). "
                + _DIFFICULTY_GUIDANCE
                + " "
                + _PRACTICE_METADATA_GUIDANCE
                + " "
                + _FACET_VOCABULARY_GUIDANCE
                + " "
                + _AUDIT_GUIDANCE
            ),
            "context": asdict(context),
        },
    )


__all__ = [
    "AUTHORING_PROMPT_VERSION",
    "DIAGNOSTIC_AUTHORING_PROMPT",
    "DIAGNOSTIC_AUTHORING_PROMPT_VERSION",
    "PRACTICE_GENERATION_PROMPT_VERSION",
    "AuthoringContext",
    "AuthoringProposal",
    "authoring_prompt",
]
