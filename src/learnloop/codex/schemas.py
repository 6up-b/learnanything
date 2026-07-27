from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import (
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    ValidationError,
    WithJsonSchema,
    model_validator,
)

from learnloop.attempt_types import AttemptType

EntityType = Literal["learning_object", "practice_item", "concept", "concept_edge", "rubric", "error_type"]
ProposalOperation = Literal["create", "update", "deactivate"]
ReviewRoute = Literal["auto_apply", "review_required", "reject"]


# --- the wire contract's runtime half ---------------------------------------
#
# ``codex/client._strict_json_schema`` stamps ``additionalProperties: false``
# onto every object in the schema handed to the provider. That is one half of a
# contract; ``WireModel`` is the other. Before it existed every model here ran
# pydantic's default ``extra="ignore"``, so the two halves disagreed in the one
# direction that is invisible: the provider was *forbidden* to emit an
# undeclared field on the strict path, and if it emitted one anyway (chat/JSON
# mode, a non-strict profile, a hand-written fixture, a stored payload from a
# newer revision) validation **dropped it without a word**.
#
# ``spec_measurement_efficiency_v1.md`` §2 F2 is the measured cost of that
# silence: ``RubricCriterionPayload`` had no ``targets`` field, models that
# emitted one had it deleted at validation, and the resulting "an item can only
# ever fill one column" defect read as a design decision for 43 attempts.
# Implementation-plan item 6.1 added the field; this class removes the class of
# defect, by making an undeclared field an error at the boundary that saw it.
#
# Every model in this module inherits it. There is deliberately no opt-out: a
# model that legitimately carries open content declares a ``dict`` FIELD (whose
# contents are unconstrained), never an open model. See
# ``client.map_typed_schema_paths`` for why even that is not free.


class WireModel(BaseModel):
    """Base for every payload that crosses the provider boundary.

    ``extra="forbid"`` mirrors the ``additionalProperties: false`` that
    ``_codex_output_schema`` sends to the provider, so a field the schema does
    not declare is rejected by name instead of being silently discarded.

    Distinct on purpose from :class:`~learnloop.vault.models.VaultModel`, which
    is ``extra="allow"``: a vault row is *our own* persisted state, read back by
    a possibly-older binary, and dropping a field a newer writer added would
    lose the learner's data. A wire payload is the opposite situation — it is
    untrusted input arriving against a schema we just published, so an
    unrecognized key means the contract and the sender have diverged and the
    only safe report is a loud one.
    """

    model_config = ConfigDict(extra="forbid")


#: Pydantic's error ``type`` for a field rejected by ``extra="forbid"``.
EXTRA_FORBIDDEN_ERROR_TYPE = "extra_forbidden"


class UndeclaredWireFieldError(ValueError):
    """A payload carried a field the wire contract does not declare.

    Raised at the boundary that parsed the payload, naming the model and every
    offending path, because "which field" is the entire actionable content of
    the failure — for the human reading the log, and for the bounded repair
    turn that is asked to drop it.
    """

    def __init__(self, model: type[BaseModel], fields: list[str]) -> None:
        self.model_name = model.__name__
        self.fields = list(fields)
        super().__init__(
            f"{self.model_name} does not declare "
            + ", ".join(self.fields)
            + "; the wire contract forbids undeclared fields "
            "(add the field to codex/schemas.py or stop emitting it)."
        )


def undeclared_wire_fields(exc: ValidationError) -> list[str]:
    """Dotted paths of every ``extra="forbid"`` rejection inside ``exc``.

    Returns ``[]`` for an ordinary validation failure, so a caller can tell an
    undeclared field (a contract divergence someone must resolve) apart from a
    malformed value (which the repair turn can usually fix on its own).
    """

    paths: list[str] = []
    for error in exc.errors():
        if error.get("type") != EXTRA_FORBIDDEN_ERROR_TYPE:
            continue
        location = ".".join(str(part) for part in error.get("loc", ()))
        if location and location not in paths:
            paths.append(location)
    return paths


def describe_wire_validation_error(model: type[BaseModel], exc: BaseException) -> str:
    """One actionable line for a failed wire parse, naming model and fields."""

    if isinstance(exc, ValidationError):
        undeclared = undeclared_wire_fields(exc)
        if undeclared:
            return str(UndeclaredWireFieldError(model, undeclared))
    return f"{model.__name__} validation failed: {exc}"


# --- open-keyed maps on the wire -------------------------------------------
#
# Strict structured output requires ``additionalProperties: false`` on every
# object and cannot express an open-keyed map, so a `dict[str, X]` field
# sanitizes into an object the provider is forbidden to put keys into: the
# field silently arrives empty every time, with no error from either side.
#
# These fields therefore travel as a list of explicit key/value pairs, which
# strict output *can* express, while keeping their map representation in
# memory so every consumer, fixture, and stored payload is unaffected. The
# before-validator also still accepts the map form, so hand-written fixtures
# and older providers keep validating.


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
    points: float = Field(gt=0.0, le=4.0)
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
    max_grade: int = Field(ge=0, le=4)
    # spec §1.2: authored link from a fatal error to the registry belief it catches.
    misconception_id: str | None = None


class RubricPatchPayload(WireModel):
    target_practice_item_id: str | None = None
    max_points: int = Field(default=4, ge=1, le=4)
    criteria: list[RubricCriterionPayload]
    fatal_errors: list[RubricFatalErrorPayload] = Field(default_factory=list)


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
    misconception_consistent_answer: str | None = None
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


class AuthoringProposal(WireModel):
    summary: str
    source_refs: list[SourceRef] = Field(default_factory=list)
    items: list[AuthoringProposalItem] = Field(default_factory=list)


class CriterionEvidence(WireModel):
    criterion_id: str
    points_awarded: float
    evidence: str
    notes: str | None = None
    learner_confidence: Literal["confident", "hedged", "absent", "unknown"] | None = None


class FacetCapabilityTargetRef(WireModel):
    kind: Literal["facet_capability"]
    facet_id: str
    capability: str | None = None


class CriterionTargetRef(WireModel):
    kind: Literal["criterion"]
    criterion_id: str


class ItemStepTargetRef(WireModel):
    kind: Literal["item_step"]
    checkpoint_id: str
    recipe_id: str | None = None


class AnswerSpanTargetRef(WireModel):
    kind: Literal["answer_span"]
    quote: str
    char_start: int | None = Field(default=None, ge=0)
    char_end: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def validate_offsets(self) -> "AnswerSpanTargetRef":
        if (self.char_start is None) != (self.char_end is None):
            raise ValueError("answer-span offsets must be supplied together")
        if (
            self.char_start is not None
            and self.char_end is not None
            and self.char_end < self.char_start
        ):
            raise ValueError("answer-span char_end must be >= char_start")
        return self


class NoTargetRef(WireModel):
    kind: Literal["none"]


AttributionTargetRef = (
    FacetCapabilityTargetRef
    | CriterionTargetRef
    | ItemStepTargetRef
    | AnswerSpanTargetRef
    | NoTargetRef
)


class FirstDivergence(WireModel):
    anchor_kind: Literal["span", "between_spans", "missing_required_step", "whole_answer"]
    criterion_id: str
    checkpoint_id: str | None = None
    quote: str | None = None
    quote_hash: str | None = None
    char_start: int | None = Field(default=None, ge=0)
    char_end: int | None = Field(default=None, ge=0)
    normalized_quote: str | None = None

    @model_validator(mode="after")
    def validate_offsets(self) -> "FirstDivergence":
        if self.anchor_kind == "missing_required_step" and not self.checkpoint_id:
            raise ValueError(
                "missing_required_step first divergence requires checkpoint_id"
            )
        if (self.char_start is None) != (self.char_end is None):
            raise ValueError("first-divergence offsets must be supplied together")
        if (
            self.char_start is not None
            and self.char_end is not None
            and self.char_end < self.char_start
        ):
            raise ValueError("first-divergence char_end must be >= char_start")
        return self


class FacetContrast(WireModel):
    target_facet: str
    confused_with_facet: str
    justification: str

    @model_validator(mode="after")
    def validate_contrast(self) -> "FacetContrast":
        if self.target_facet == self.confused_with_facet:
            raise ValueError("facet contrast requires two distinct facets")
        if not self.justification.strip():
            raise ValueError("facet contrast justification must cite the trace")
        return self


class CandidateCause(WireModel):
    statement: str
    cause_scope: Literal[
        "learner_state",
        "transient_execution",
        "interaction_context",
        "item_contract",
        "grader_interpretation",
        "unknown",
    ]
    target_ref: AttributionTargetRef | None = Field(default=None, discriminator="kind")

    @model_validator(mode="after")
    def validate_statement(self) -> "CandidateCause":
        if not self.statement.strip():
            raise ValueError("candidate cause statement cannot be empty")
        return self


class PostdictiveClaim(WireModel):
    criterion_id: str
    must: Literal["fail", "not_full_credit"]


class RepairedTrace(WireModel):
    """A minimal, auditable edit of the learner's displayed reasoning."""

    learner_work_prefix: str = ""
    repair_insertion_point: FirstDivergence | None = None
    minimal_edit: str
    regenerated_work: str = ""
    repaired_answer_md: str
    changed_latent_claims: list[str] = Field(default_factory=list)
    changed_checkpoint_ids: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_minimal_edit(self) -> "RepairedTrace":
        if not self.minimal_edit.strip():
            raise ValueError("repaired trace requires a non-empty minimal_edit")
        if not self.repaired_answer_md.strip():
            raise ValueError("repaired trace requires repaired_answer_md")
        return self


class RepairVerificationRequest(WireModel):
    """A request for a backend verifier, never a model-supplied verdict.

    ``test_execution`` is requestable but carries no result field: the outcome
    reaches ``validate_repair_candidate`` through its ``execution_result``
    parameter, from a trusted caller. A model that could attach its own
    ``returncode`` would be issuing itself a deterministic verdict.
    """

    kind: Literal["symbolic_equality", "exact_match", "test_execution"]
    assumptions: list[str] = Field(default_factory=list)
    required_assumptions: list[str] = Field(default_factory=list)


class ErrorAttribution(WireModel):
    # Aug C1: checkable artifact before causal structure.  The top-level
    # GradingProposal also places repair_suggestions immediately after prose;
    # within the suggestion this field therefore precedes every causal label.
    # (ErrorAttribution itself contains no repair artifact.)
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
    resolution_status: Literal["resolved", "unresolved", "abstained"] | None = None
    abstention_reason: str | None = None
    cause_scope: Literal[
        "learner_state",
        "transient_execution",
        "interaction_context",
        "item_contract",
        "grader_interpretation",
        "unknown",
    ] | None = None
    target_ref: AttributionTargetRef | None = Field(default=None, discriminator="kind")
    operation: str | None = Field(default=None, pattern=r"^[a-z][a-z0-9_]*$")
    first_divergence: FirstDivergence | None = None
    localization_confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    causal_confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    facet_contrast: FacetContrast | None = None
    candidate_causes: list[CandidateCause] = Field(default_factory=list)
    postdictive_claims: list[PostdictiveClaim] = Field(default_factory=list)
    soft_postdictive_claims: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_abstention(self) -> "ErrorAttribution":
        if self.resolution_status == "abstained" and not (self.abstention_reason or "").strip():
            raise ValueError("abstention_reason is required when resolution_status is abstained")
        return self


class RepairSuggestion(WireModel):
    # Aug C1 field order is causal under autoregressive decoding: emit the
    # checkable edit before inventing the causal story that explains it.
    repaired_trace: RepairedTrace | None = None
    verification_request: RepairVerificationRequest | None = None
    practice_mode: str
    learning_object_id: str | None = None
    rationale: str
    target_evidence_families: list[str] = Field(default_factory=list)
    target_criterion_ids: list[str] = Field(default_factory=list)
    # P1 structural repair fields. They remain nullable so older/self grading
    # can keep producing the P0 shape without fabricating structure.
    operator: str | None = Field(default=None, pattern=r"^[a-z][a-z0-9_]*$")
    target_refs: list[AttributionTargetRef] = Field(default_factory=list)
    preserve_refs: list[AttributionTargetRef] = Field(default_factory=list)
    expected_minutes: float | None = Field(default=None, ge=0.0)
    answer_reveal_budget: float = Field(default=0.0, ge=0.0, le=1.0)


class ExercisedFacetObservation(WireModel):
    """One facet the grader saw *exercised* in the trace (Meas §3.A6).

    The most bitter-lesson-aligned field in the grading contract: the model
    observes, the harness decides what the observation is worth. Three bounds,
    and none of them is expressible as a field the model fills in — they are
    enforced by what this schema omits.

    * **Positive only.** There is no polarity. Opportunistic evidence may credit
      a facet; it may never indict one. Indicting a facet the item did not
      intend to measure is exactly the smearing causal §1 principle 5 forbids,
      and there is no criterion to appeal to.
    * **Supporting at most.** There is no ``role``. Everything from this channel
      lands as embedded credit under A1's cap.
    * **No capability.** Standing constraint 8: the rung an observation counts
      at is a deterministic property of the criterion's authored target, never a
      model-reported one.

    ``evidence`` is required. An observation with no citation from the trace is
    an assertion, and this channel exists precisely because the model is
    reporting rather than deciding.
    """

    facet: str
    evidence: str
    criterion_id: str | None = None


class ClarificationRequest(WireModel):
    """One question to the learner that would resolve a hedged grade (Meas §3.A8).

    Bounded below by the schema and above by the validator. The schema forbids
    the shapes that would make it an interrogation:

    * there is no ``answer`` and no ``expected_answer`` — the grader is asking,
      not proposing what it expects to hear, which is the difference between a
      question and a leading one;
    * there is no ``points`` or ``grade`` — an answer never grades itself, it
      triggers a re-grade through the ordinary regrade path;
    * ``reason`` is closed to the three uncertainty shapes §3.A8 names plus a
      method-ambiguity arm and an explicit ``other``.

    The validator then drops any request against a *confident* grade
    (``grading._validated_clarification``): the whole channel is licensed by the
    grader having already said it is unsure.
    """

    question_md: str
    reason: Literal[
        "ambiguous_notation",
        "skipped_step",
        "correct_answer_possibly_invalid_reasoning",
        "method_ambiguity",
        "other",
    ] = "other"
    criterion_id: str | None = None


class DiscriminationProfileMatch(WireModel):
    """Which authored candidate profile the trace matches -- or none (Meas §3.A5).

    THE REJECTION ARM IS THE POINT. §3.A5: a profile is "a candidate set the
    diagnostician may match against and **must be free to reject**, with
    ``no_profile_applies`` a first-class outcome carrying the same weight as any
    named match." So the two arms are siblings in one closed vocabulary rather
    than a nullable ``profile_id`` -- a null would make rejection
    indistinguishable from a model that simply did not answer, and the revert
    criterion ("``no_profile_applies`` rate collapses toward zero") would be
    computed over a denominator that silently absorbed both.

    There is no confidence and no ranking. A profile is a PRIOR over causes
    (causal §1 principle 4), and a scored match would be a posterior the item's
    author wrote before the learner arrived.
    """

    outcome: Literal["matched", "no_profile_applies"]
    profile_id: str | None = Field(
        default=None,
        description="REQUIRED on `matched`; must be one of the item's authored profile ids.",
    )
    evidence: str = Field(
        default="",
        description=(
            "The part of the learner's trace that shows the match. Required on "
            "`matched`: a match with no citation is an assertion."
        ),
    )

    @model_validator(mode="after")
    def validate_match(self) -> "DiscriminationProfileMatch":
        if self.outcome == "matched" and not (self.profile_id or "").strip():
            raise ValueError("a matched discrimination profile requires a profile_id")
        return self


class ReportedError(WireModel):
    """One error the learner claims to have found in an A3 worked solution.

    ``repair_md`` is separate from ``claim_md`` because §3.A3 requires the
    REPAIR, not the flag: "Flagging is recognition; repairing is construction."
    A report with a claim and no repair is recorded as flagged-not-repaired and
    earns no facet credit, which is what keeps A3 on the right side of §11's
    no-recognition-items non-goal.
    """

    location: str = Field(
        default="",
        description="Where in the worked solution the learner says the error is.",
    )
    claim_md: str = Field(description="What the learner says is wrong there.")
    repair_md: str = Field(
        default="",
        description=(
            "The corrected work the learner produced. EMPTY when they only flagged "
            "the error without repairing it."
        ),
    )
    matches_planted_error_id: str | None = Field(
        default=None,
        description=(
            "The item's planted-error id this report corresponds to, or null when "
            "it corresponds to none. Null on a CLEAN solution is the informative "
            "case, not an error."
        ),
    )


class ErrorHuntReport(WireModel):
    """What the learner found and repaired in an A3 item (Meas §3.A3).

    Reported as observations, never as a score. The harness decides what each
    report is worth -- in particular whether a report matching no plant is noise
    (on a seeded solution) or a misconception handed over directly (on a clean
    one), which is a fact about the ITEM the grader is not told and cannot infer.
    """

    reported_errors: list[ReportedError] = Field(default_factory=list)


class GradingProposal(WireModel):
    # Intentionally first: autoregressive graders diagnose in prose before the
    # structured attribution contract can pressure them into a nearby label.
    diagnosis_md: str | None = None
    # Aug C1 (plan amendment): prose remains first to preserve causal §5.1;
    # the repaired trace comes next, inside these suggestions, and structured
    # causal fields come later.  RepairSuggestion orders repaired_trace first.
    repair_suggestions: list[RepairSuggestion] = Field(default_factory=list)
    attempt_id: str
    practice_item_id: str
    rubric_score: int = Field(ge=0, le=4)
    criterion_evidence: list[CriterionEvidence] = Field(default_factory=list)
    fatal_errors: list[str] = Field(default_factory=list)
    error_attributions: list[ErrorAttribution] = Field(default_factory=list)
    grader_confidence: float = Field(ge=0.0, le=1.0)
    manual_review_recommended: bool = False
    feedback_md: str | None = None
    # Meas §3.A6: facets the trace shows exercised, whether or not the item
    # declared them. Deliberately last in the field order — it is an observation
    # made *while* grading, and putting it ahead of the attribution contract
    # would invite the model to author coverage before it has finished
    # diagnosing (causal §5.1's field-order argument, applied in reverse).
    exercised_facets: list[ExercisedFacetObservation] = Field(default_factory=list)
    # Meas §3.A8: at most one, and only against a criterion this proposal has
    # already hedged or abstained on. Nullable with no default question, because
    # "I am sure enough" must stay the cheap answer.
    clarification_request: ClarificationRequest | None = None
    # Meas §3.A5: which of the item's authored candidate profiles the trace
    # matches, or the first-class rejection. Placed AFTER the attribution
    # contract for causal §5.1's reason: the profiles are a prior, and a model
    # that reported the match first would be reasoning from the authored
    # candidates back to the diagnosis instead of forward from the trace.
    # Null when the item authored none -- the harness records that arm itself
    # rather than asking the model to say "there was nothing to match".
    discrimination_profile_match: DiscriminationProfileMatch | None = None
    # Meas §3.A3: what the learner found and REPAIRED in a worked solution. Null
    # on every item that is not an error hunt.
    error_hunt_report: ErrorHuntReport | None = None


QuestionType = Literal["clarification", "prerequisite", "mechanism", "strategy", "verification", "other"]


class TeachBackQuestion(WireModel):
    """One naive-student follow-up question in a teach-back conversation.

    The persona never corrects, confirms, or reveals; the service supplies the
    target criterion/facets in the context and stores the question as an AI
    transcript turn.
    """

    question_md: str


class TeachBackCriterionDraft(WireModel):
    """One criterion in an AI-authored, source-item-scoped teach-back.

    The model authors the learner-facing description and proposes an honest
    measurement mapping. The service validates every source criterion and facet
    id against the bounded authoring context before persisting anything.
    """

    description: str = ""
    source_criterion_ids: list[str] = Field(default_factory=list)
    measurement_status: Literal[
        "direct", "supporting", "composite", "item_local", "no_canonical_facet"
    ] = "item_local"
    facet_ids: list[str] = Field(default_factory=list)


class TeachBackAuthoring(WireModel):
    """AI-authored transformation of one completed Practice Item.

    Core criteria remain anchored to the source assessment. The single transfer
    criterion may use the active quest sentence for context, but may not change
    the knowledge target. ``quest_connection`` is an inspectable declaration,
    not evidence that the connection is pedagogically valid.
    """

    prompt_md: str = ""
    expected_answer_md: str = ""
    core_criteria: list[TeachBackCriterionDraft] = Field(default_factory=list)
    transfer_criterion: TeachBackCriterionDraft | None = None
    transfer_scenario: str = ""
    quest_connection: Literal["connected", "not_relevant", "no_quest"] = "no_quest"
    trace_contract: TraceContractPayload | None = None


class ReaderPresetSynthesis(WireModel):
    """One demand-paged reader preset result (spec §6, reader producer).

    Candidate-only: the service validates ``span_ids`` against the request
    window's spans and lands the content as a PROPOSED source object plus a
    reviewable mapping proposal — never auto-admitted into pools or evidence.
    """

    content_md: str = ""
    span_ids: list[str] = Field(default_factory=list)


class ReadingQuickCheck(WireModel):
    """One AI-authored section-boundary quick check (reader producer slice).

    Candidate-only: the service validates ``span_ids`` against the section's
    provided spans (never model-invented) and persists the row itself. The
    question is a formative self-check — it never becomes evidence unless the
    learner escalates it into a practice item.
    """

    question_md: str = ""
    expected_answer_md: str = ""
    span_ids: list[str] = Field(default_factory=list)


class RungBackfillItem(WireModel):
    """One legacy item's rung classification (candidate-only; deterministic
    validators admit or skip each entry)."""

    practice_item_id: str = ""
    capability: str = ""
    task_features: TaskFeaturesPayload | None = None


class RungBackfillClassification(WireModel):
    items: list[RungBackfillItem] = Field(default_factory=list)


class ExerciseAuthoredItem(WireModel):
    """One selected textbook exercise completed into a full PracticeItem
    contract (reader exercise import).

    Candidate-only: ``statement_md`` must echo one exercise statement verbatim
    from the learner's selection — the service re-anchors it against the
    selection text and stores the source-owned slice, so the practice surface
    is never model-rewritten. Every other field is the AI-authored
    interpretation around that fixed surface, admitted or repaired by
    deterministic validators (facet registry, rubric arithmetic, capability
    vocabulary, p1_launch task-feature schema).
    """

    statement_md: str = ""
    title: str = ""
    learning_object_id: str = ""
    practice_mode: str = "short_answer"
    expected_answer_md: str = ""
    grading_rubric: RubricPatchPayload | None = None
    evidence_facets: list[str] = Field(default_factory=list)
    evidence_weights: list[FacetWeightPayload] = Field(default_factory=list)
    criterion_facet_weights: list[CriterionFacetWeightsPayload] = Field(default_factory=list)
    trace_contract: TraceContractPayload | None = None
    hints: list[str] = Field(
        default_factory=list,
        description="2-4 progressive hints: orient first, near-give-away last.",
    )
    capability: str = ""
    task_features: TaskFeaturesPayload | None = None
    difficulty: float | None = Field(default=None, ge=0.0, le=1.0)
    retrieval_demand: float | None = Field(default=None, ge=0.0, le=1.0)
    transfer_distance: float | None = Field(default=None, ge=0.0, le=1.0)
    scaffold_level: float | None = Field(default=None, ge=0.0, le=1.0)
    classification_reason: str = ""


class ExerciseAuthoring(WireModel):
    """The full exercise-import response: one entry per distinct exercise
    found in the learner's selection (a selection sweeping exercises 3-5
    yields three items)."""

    items: list[ExerciseAuthoredItem] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class DepthEdgeInstancePayload(WireModel):
    """One LLM-authored depth-edge instance (candidate-only; spec v2 §depth).

    Instantiates an owner-reviewed edge TEMPLATE for one commitment. Every
    instance is admitted or rejected by deterministic gates in
    ``services/depth_edge_authoring`` — model judgment never authorizes an edge.
    """

    edge_id: str = ""
    predecessor_milestone: str = ""
    successor_milestone_slug: str = ""
    # Successor task contract: capability (closed vocab) + task_features point
    # vector and/or task_feature_bounds ({dim: {target?, max?}}).
    successor_task_contract: dict = Field(default_factory=dict)
    # Observable entry/exit evidence: {"kind": one of n_of_m_success |
    # fresh_surface_pass | certified_attempt, "threshold": {...}}.
    entry_evidence: dict | None = None
    exit_evidence: dict = Field(default_factory=dict)
    # {"kind": "fresh_surface" | "reserved_family_mint", "family": ...}
    fresh_proof: dict = Field(default_factory=dict)
    expected_burden: dict = Field(default_factory=dict)
    # {"pattern_slug": ..., "purpose": ...} — must resolve to an admitted
    # activity pattern whose allowed purposes include the edge's purpose.
    activity_path: dict = Field(default_factory=dict)
    rationale: str = ""


class DepthEdgeInstanceBatch(WireModel):
    instances: list[DepthEdgeInstancePayload] = Field(default_factory=list)


class TutorCitation(WireModel):
    """One source-span citation on a tutor answer (ING M8, §9.2).

    The model may cite ONLY spans supplied in ``context.source_spans``; the
    service drops any citation whose ``(extraction_id, span_id)`` was not
    provided (never model-invented). The chip opens the Open-in-source viewer.
    """

    extraction_id: str
    span_id: str
    label: str | None = None


class TutorAnswer(WireModel):
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
    # ING M8 (§9.2): optional source-span citations, validated against the spans
    # supplied in the context. Empty when no links exist (degrades to unchanged
    # behavior).
    citations: list[TutorCitation] = Field(default_factory=list)


class MisconceptionMatch(WireModel):
    """LLM verdict for registry normalization (spec §2.2.2).

    ``decision == "same"`` means the graded belief is the same as the registry
    row named by ``misconception_id``; ``"new"`` means it is a distinct belief
    and a fresh row should be inserted. When unsure the model should prefer
    ``"new"`` (spec §9: avoid over-merging distinct beliefs).
    """

    decision: Literal["same", "new"]
    misconception_id: str | None = None


class PromotionAnalysis(WireModel):
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


class ProbeInstanceSurface(WireModel):
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


class ProbeInstanceSurfaces(WireModel):
    """Batch of surface-varied instances for one family/card binding."""

    surfaces: list[ProbeInstanceSurface] = Field(default_factory=list)


class ProbeDialogueTurn(WireModel):
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


class ProbeFamilyTrial(WireModel):
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


class ProbeFamilyTrials(WireModel):
    """All planted trials for one family admission gate run (one call)."""

    trials: list[ProbeFamilyTrial] = Field(default_factory=list)


class DiagnosticTrialResult(WireModel):
    """One simulated student's answer + whether the keyed fatal error fires.

    ``answer`` is the student's natural-language response (never verbatim the
    canned misconception-consistent string); ``fires`` is the model's judgment of
    whether a grader would attribute the misconception-keyed fatal error to it.
    """

    answer: str
    fires: bool


class DiagnosticTrials(WireModel):
    """Codex answers-under-belief for the sim discrimination gate (spec §6).

    ``planted`` are learners who genuinely HOLD the targeted belief; ``clean``
    are competent learners. One structured call returns all trials at once so the
    gate spends a single provider request regardless of trial count.
    """

    planted: list[DiagnosticTrialResult] = Field(default_factory=list)
    clean: list[DiagnosticTrialResult] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Role-specific unit inventory (spec_source_ingestion_v2 §7, ING M4)
#
# The SourceUnitInventory contract, verbatim. Every assertion cites provided
# span ids; the model never invents a locator. Ids the model returns are
# placeholders — the inventory service reassigns deterministic ids from
# (unit_id, window_ordinal, item_ordinal, normalized-content-hash), so an
# unchanged semantic view yields stable ids. Inventory rows are CANDIDATES, not
# canonical facets/recipes/learner evidence.
# ---------------------------------------------------------------------------


class InventoryConceptMention(WireModel):
    mention_id: str = ""
    name: str = ""
    aliases: list[str] = Field(default_factory=list)
    notation: list[str] = Field(default_factory=list)
    span_ids: list[str] = Field(default_factory=list)


class InventoryClaim(WireModel):
    claim_id: str = ""
    kind: Literal["definition", "theorem", "procedure", "assumption", "example"] = "definition"
    statement: str = ""
    preconditions: list[str] = Field(default_factory=list)
    postconditions: list[str] = Field(default_factory=list)
    applicability: list[str] = Field(default_factory=list)
    examples: list[str] = Field(default_factory=list)
    counterexamples: list[str] = Field(default_factory=list)
    non_goals: list[str] = Field(default_factory=list)
    concept_mention_ids: list[str] = Field(default_factory=list)
    prerequisite_hints: list[str] = Field(default_factory=list)
    span_ids: list[str] = Field(default_factory=list)


class InventoryProcedureSignal(WireModel):
    procedure_id: str = ""
    contract: str = ""
    ordered_steps: list[str] = Field(default_factory=list)
    preconditions: list[str] = Field(default_factory=list)
    common_invalid_steps: list[str] = Field(default_factory=list)
    observable_step_span_ids: list[str] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def coerce_span_ids(cls, data: Any) -> Any:
        """Accept ``span_ids``, the name every other inventory row uses.

        This is a deliberate alias, not an undeclared field: the §7 contract
        calls the procedure row's citations ``observable_step_span_ids`` and
        every sibling row calls its own ``span_ids``, so models transpose them
        constantly. It is *consumed* here (popped, not merely copied) because
        ``WireModel`` forbids extras — leaving the key behind would turn a
        supported spelling into a rejection.
        """

        if not isinstance(data, dict) or "span_ids" not in data:
            return data
        coerced = dict(data)
        span_ids = coerced.pop("span_ids")
        if not coerced.get("observable_step_span_ids") and span_ids:
            coerced["observable_step_span_ids"] = list(span_ids)
        return coerced



class InventoryPracticeSignal(WireModel):
    signal_id: str = ""
    kind: Literal["exercise", "worked_example", "solution"] = "exercise"
    task_family: str = ""
    valid_method_hints: list[str] = Field(default_factory=list)
    response_structure: str = ""
    capability_demands: list[str] = Field(default_factory=list)
    representation: str = ""
    difficulty_signal: str = ""
    concept_mention_ids: list[str] = Field(default_factory=list)
    span_ids: list[str] = Field(default_factory=list)


class InventoryAssessmentSignal(WireModel):
    assessment_item_id: str = ""
    held_out: bool = False
    topic_mentions: list[str] = Field(default_factory=list)
    task_family: str = ""
    capability_demands: list[str] = Field(default_factory=list)
    representation: str = ""
    response_format: str = ""
    point_or_time_emphasis: str = ""
    method_visibility: str = ""
    span_ids: list[str] = Field(default_factory=list)


class InventoryMisconceptionSignal(WireModel):
    statement: str = ""
    confused_concept_mentions: list[str] = Field(default_factory=list)
    trigger_conditions: list[str] = Field(default_factory=list)
    invalid_step: str = ""
    repair_hint: str = ""
    span_ids: list[str] = Field(default_factory=list)


class InventoryCoverageClaim(WireModel):
    concept_mention_id: str = ""
    depth: str = ""
    pedagogical_forms: list[str] = Field(default_factory=list)
    span_ids: list[str] = Field(default_factory=list)


class InventoryWarning(WireModel):
    kind: str = ""
    detail: str = ""
    span_ids: list[str] = Field(default_factory=list)


class SourceUnitInventory(WireModel):
    """The §7 unit-inventory contract. One envelope, role-aware profiles: a
    narrower profile may leave irrelevant sections empty (they are never forced
    through the most expensive prompt)."""

    unit_id: str = ""
    semantic_hash: str = ""
    outline_summary: str = ""
    concept_mentions: list[InventoryConceptMention] = Field(default_factory=list)
    claims: list[InventoryClaim] = Field(default_factory=list)
    procedure_signals: list[InventoryProcedureSignal] = Field(default_factory=list)
    practice_signals: list[InventoryPracticeSignal] = Field(default_factory=list)
    assessment_signals: list[InventoryAssessmentSignal] = Field(default_factory=list)
    misconception_signals: list[InventoryMisconceptionSignal] = Field(default_factory=list)
    coverage_claims: list[InventoryCoverageClaim] = Field(default_factory=list)
    inventory_warnings: list[InventoryWarning] = Field(default_factory=list)


# --- Source-set synthesis (ING M6, spec §8.5) -------------------------------
#
# The bootstrap synthesis output contract. It emits DEPENDENCY-ANNOTATED
# proposal items (facets, concepts, LOs with blueprints/recipes, task
# blueprints, practice items with rubric criteria) plus a single bounded
# round of `span_requests`. All ids are CLIENT ids; the service reassigns
# deterministic entity ids and normalizes `depends_on` into the dependency
# table. Provenance cites ONLY span ids supplied in the synthesis context.


class SynthSpanRef(WireModel):
    """One span citation (§8.5). Cites provided extraction/unit/span ids only."""

    extraction_id: str = ""
    revision_id: str = ""
    unit_id: str = ""
    span_id: str = ""
    source_id: str = ""
    locator: str = ""
    relation: Literal["primary", "support", "alternate", "exercise", "assessment_alignment"] = "support"
    role: str = "reference"


class SynthSpanRequest(WireModel):
    """A pass-1 evidence-view request (§8.5). Resolved for selected units only."""

    extraction_id: str = ""
    unit_id: str = ""
    span_id: str = ""
    purpose: str = ""


class SynthConcept(WireModel):
    client_item_id: str = ""
    id: str = ""
    title: str = ""
    type: Literal["concept", "procedure", "skill", "misconception"] = "concept"
    description: str = ""
    aliases: list[str] = Field(default_factory=list)


class SynthFacet(WireModel):
    """A canonical facet registry entry (knowledge-model §3.2), span-cited."""

    client_item_id: str = ""
    id: str = ""
    concept_client_id: str = ""
    concept_id: str = ""
    kind: Literal["definition", "proposition", "procedure_contract", "applicability_condition", "interpretation"] = "definition"
    claim: str = ""
    preconditions: list[str] = Field(default_factory=list)
    postconditions: list[str] = Field(default_factory=list)
    applicability: list[str] = Field(default_factory=list)
    positive_examples: list[str] = Field(default_factory=list)
    negative_examples: list[str] = Field(default_factory=list)
    non_goals: list[str] = Field(default_factory=list)
    error_signatures: list[str] = Field(default_factory=list)
    instructional_repairs: list[str] = Field(default_factory=list)
    aliases: list[str] = Field(default_factory=list)
    provenance: list[SynthSpanRef] = Field(default_factory=list)


class SynthRecipeComponent(WireModel):
    facet_client_id: str = ""
    facet: str = ""
    capability: Literal[
        "retrieval",
        "schema_interpretation",
        "procedure_execution",
        "method_selection",
        "coordination",
    ] = "retrieval"
    modality: Literal["hard", "path_specific", "facilitating", "instructional_order"] = "hard"


class SynthIntegrationComponent(WireModel):
    """The optional `integration` component of a recipe (knowledge-model §7.2).

    Distinct from :class:`SynthRecipeComponent` in exactly one way: `capability`
    is nullable with no default. An `all_of`/`any_of` component always observes
    *something*, so a default is harmless there; the integration slot is optional
    and its capability decides whether the LO is certifiable at all, so "the
    model did not choose" must be representable rather than silently becoming a
    requirement nobody authored. Absence is dropped with a review diagnostic at
    normalization, never defaulted.
    """

    facet_client_id: str = ""
    facet: str = ""
    capability: Literal[
        "retrieval",
        "schema_interpretation",
        "procedure_execution",
        "method_selection",
        "coordination",
    ] | None = None
    modality: Literal["hard", "path_specific", "facilitating", "instructional_order"] = "hard"


class SynthRecipe(WireModel):
    id: str = ""
    composition: Literal["conjunctive"] = "conjunctive"
    all_of: list[SynthRecipeComponent] = Field(default_factory=list)
    any_of: list[SynthRecipeComponent] = Field(default_factory=list)
    integration: SynthIntegrationComponent | None = None


class SynthBlueprint(WireModel):
    """A performance blueprint (knowledge-model §7.2). Merged onto its LO."""

    client_item_id: str = ""
    id: str = ""
    learning_object_client_id: str = ""
    learning_object_id: str = ""
    weight: float = 1.0
    # A blueprint with no recipe is meaningless (nothing to build tasks from) and
    # is a hard-fail at the recipe_validity gate. Requiring >=1 here rejects that
    # degenerate output at parse time on both client paths; on the chat path it
    # triggers the one-shot JSON repair round (whose schema now shows minItems:1).
    # Note: minItems is stripped from the strict Codex/OpenAI output schema, so
    # this does not change that structured-output API contract.
    recipes: list[SynthRecipe] = Field(default_factory=list, min_length=1)


class SynthLearningObject(WireModel):
    client_item_id: str = ""
    id: str = ""
    concept_client_id: str = ""
    concept_id: str = ""
    title: str = ""
    summary: str = ""
    knowledge_type: str = ""
    prerequisite_concept_client_ids: list[str] = Field(default_factory=list)
    prerequisites: list[str] = Field(default_factory=list)
    confusable_concept_client_ids: list[str] = Field(default_factory=list)
    confusables: list[str] = Field(default_factory=list)
    provenance: list[SynthSpanRef] = Field(default_factory=list)


class SynthCriterionTarget(WireModel):
    facet_client_id: str = ""
    facet: str = ""
    capability: Literal[
        "retrieval",
        "schema_interpretation",
        "procedure_execution",
        "method_selection",
        "coordination",
    ] = "retrieval"
    role: Literal["primary", "supporting"] = "primary"


class SynthCriterion(WireModel):
    id: str = ""
    points: float = 1.0
    description: str = ""
    tier: Literal["core", "transfer"] = "core"
    targets: list[SynthCriterionTarget] = Field(default_factory=list)
    depends_on: list[str] = Field(default_factory=list)
    recipe_ids: list[str] = Field(default_factory=list)
    correlation_group: str = ""


class SynthEvidenceFingerprint(WireModel):
    source_family: str = ""
    shared_stimulus_id: str = ""
    representation: str = ""
    solution_recipe_family: str = ""
    answer_structure: str = ""


class SynthPracticeItem(WireModel):
    client_item_id: str = ""
    id: str = ""
    learning_object_client_id: str = ""
    learning_object_id: str = ""
    practice_mode: str = "retrieval"
    prompt: str = ""
    expected_answer: str = ""
    evidence_facet_client_ids: list[str] = Field(default_factory=list)
    evidence_facets: list[str] = Field(default_factory=list)
    criteria: list[SynthCriterion] = Field(default_factory=list)
    fatal_error_ids: list[str] = Field(default_factory=list)
    evidence_fingerprint: SynthEvidenceFingerprint = Field(default_factory=SynthEvidenceFingerprint)
    retrieval_demand: float = 0.5
    transfer_distance: float = 0.0
    scaffold_level: float = 0.0
    surface_family: str = "source_form"
    depends_on_client_item_ids: list[str] = Field(default_factory=list)
    provenance: list[SynthSpanRef] = Field(default_factory=list)


class SynthConflict(WireModel):
    entity_client_id: str = ""
    statement: str = ""
    left: SynthSpanRef = Field(default_factory=SynthSpanRef)
    right: SynthSpanRef = Field(default_factory=SynthSpanRef)


class ConceptRelation(WireModel):
    """One typed concept-graph edge (knowledge-model concept graph).

    ``source``/``target`` are concept ``client_item_id``s from this candidate OR
    already-registered concept ids. Direction: source --prerequisite--> target
    means source is a prerequisite of target; source --part_of--> target means
    source is a sub-concept of target. The service resolves ids, drops invalid
    or cycle-forming edges with review diagnostics, and compiles the survivors
    into ``concept_edge`` proposal items."""

    source: str = ""
    target: str = ""
    relation_type: Literal["prerequisite", "part_of", "confusable_with", "related"] = "related"
    rationale: str = ""
    strength: float = 1.0


class SourceSetSynthesis(WireModel):
    """The §8.5 bootstrap synthesis contract (candidate-only, span-cited).

    Deliberately NOT on the CodexClient Protocol — discovered via getattr like
    run_source_unit_inventory. The service validates span citations, runs the
    §8.7 gates, normalizes dependencies, and persists through the existing
    proposal pipeline. Every declared conflict candidate must appear here or be
    explicitly dispositioned as a non-conflict."""

    summary: str = ""
    span_requests: list[SynthSpanRequest] = Field(default_factory=list)
    concepts: list[SynthConcept] = Field(default_factory=list)
    facets: list[SynthFacet] = Field(default_factory=list)
    learning_objects: list[SynthLearningObject] = Field(default_factory=list)
    blueprints: list[SynthBlueprint] = Field(default_factory=list)
    practice_items: list[SynthPracticeItem] = Field(default_factory=list)
    conflicts: list[SynthConflict] = Field(default_factory=list)
    non_conflict_dispositions: list[str] = Field(default_factory=list)
    # Within-shard concept relations (optional): the post-merge graph
    # structuring pass authors the cross-shard / cross-source structure.
    concept_relations: list[ConceptRelation] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class ConceptMergeGroup(WireModel):
    """One set of semantically-duplicate concepts to fold into a canonical one.

    ``canonical_client_id`` is the concept that survives; every concept in
    ``duplicate_client_ids`` is folded into it (its title and aliases become
    aliases of the canonical) and all references are rewritten. Ids must be
    concept ``client_item_id`` values from the provided candidate list."""

    canonical_client_id: str = ""
    duplicate_client_ids: list[str] = Field(default_factory=list)
    rationale: str = ""


class ConceptGraphStructuring(WireModel):
    """The post-merge concept graph-structuring contract (§8.5).

    One bounded pass over the WHOLE merged candidate plus compact source
    skeletons (outline trees + cached inventory summaries) — the only stage
    that sees every concept across every shard and source, so it both folds
    semantic duplicates (``merge_groups``) and authors the big-picture
    structure (``relations``: part_of hierarchy, prerequisites, confusables).

    Deliberately NOT on the CodexClient Protocol — discovered via getattr like
    run_source_set_synthesis. The service validates every referenced id,
    rejects chains/cycles, applies merges deterministically, and treats any
    invalid group or edge as a droppable no-op, never an error."""

    merge_groups: list[ConceptMergeGroup] = Field(default_factory=list)
    relations: list[ConceptRelation] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


# --- Append reconciliation (§10.2) ------------------------------------------


class AppendProvenanceLink(WireModel):
    """A `provenance_link` additive item (span_attach / alternate_explanation /
    assessment_alignment, §10.2). Purely attaches an existing entity to a new span
    — it never mutates the target. The intent label is untrusted; the apply handler
    only ever writes an entity_source_links row."""

    client_item_id: str = ""
    reconciliation_intent: Literal[
        "span_attach", "alternate_explanation", "assessment_alignment"
    ] = "span_attach"
    target_entity_type: Literal[
        "facet", "learning_object", "task_blueprint", "practice_item", "concept"
    ] = "facet"
    target_entity_id: str = ""
    expected_target_hash: str = ""
    relation: Literal["support", "alternate", "assessment_alignment"] = "support"
    span: SynthSpanRef = Field(default_factory=SynthSpanRef)


class AppendNotationMapping(WireModel):
    """A contextual notation equivalence (`notation_mapping`, review-required)."""

    client_item_id: str = ""
    target_entity_type: Literal["facet", "learning_object", "concept"] = "facet"
    target_entity_id: str = ""
    canonical_notation: str = ""
    alternate_notation: str = ""
    context: str = ""
    span: SynthSpanRef = Field(default_factory=SynthSpanRef)


class AppendConflict(WireModel):
    """A two-sided conflict (`source_conflict`, always reviewed). Accepting persists
    an OPEN conflict; it never applies either competing side."""

    client_item_id: str = ""
    entity_type: Literal["facet", "learning_object", "concept"] = "facet"
    entity_id: str = ""
    statement: str = ""
    left: SynthSpanRef = Field(default_factory=SynthSpanRef)
    right: SynthSpanRef = Field(default_factory=SynthSpanRef)


class AppendRestructure(WireModel):
    """A semantic replacement/removal (`restructure_unlocked`; update/deactivate).

    Legal only when the touched identity is unlocked and the target hash matches;
    always review-required, invalid (not merely reviewed) on a locked entity."""

    client_item_id: str = ""
    target_entity_type: Literal["learning_object", "concept", "practice_item"] = "learning_object"
    target_entity_id: str = ""
    operation: Literal["update", "deactivate"] = "update"
    expected_target_hash: str = ""
    payload: dict = Field(default_factory=dict)


class AppendReconciliation(WireModel):
    """The §10.2 append reconciliation contract (candidate-only, span-cited).

    Context = new/changed inventories + brief + the bounded affected neighborhood
    (NEVER the full map). Additive intents use specialized append-only item types;
    pure additivity is verified from item type + payload by the gate/handlers, never
    trusted from these intent labels. Discovered via getattr like
    run_source_set_synthesis."""

    summary: str = ""
    span_requests: list[SynthSpanRequest] = Field(default_factory=list)
    # new_coverage reuses the bootstrap curriculum vocabulary (operation=create).
    concepts: list[SynthConcept] = Field(default_factory=list)
    facets: list[SynthFacet] = Field(default_factory=list)
    learning_objects: list[SynthLearningObject] = Field(default_factory=list)
    blueprints: list[SynthBlueprint] = Field(default_factory=list)
    practice_items: list[SynthPracticeItem] = Field(default_factory=list)
    # specialized additive item types.
    provenance_links: list[AppendProvenanceLink] = Field(default_factory=list)
    notation_mappings: list[AppendNotationMapping] = Field(default_factory=list)
    conflicts: list[AppendConflict] = Field(default_factory=list)
    restructures: list[AppendRestructure] = Field(default_factory=list)
    conflict_candidates: list[str] = Field(default_factory=list)
    non_conflict_dispositions: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class ManimAnimation(WireModel):
    """One LLM-authored Manim CE explainer scene (spec_fork_features §2).

    Candidate-only: the animation service AST-validates ``scene_code`` against
    an import/builtin allowlist and renders it in a constrained subprocess with
    a timeout — nothing here is trusted or auto-executed, and per-run learner
    consent is the actual security boundary."""

    scene_code: str = ""
    scene_class: str = ""
    title: str = ""
    narration_md: str = ""
