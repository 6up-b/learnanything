from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from learnloop.attempt_types import AttemptType
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
    source_id: str | None = None
    revision_id: str | None = None
    extraction_id: str | None = None
    span_ids: list[str] = Field(default_factory=list)
    span_hash: str | None = None
    section_id: str | None = None
    learning_object_ids: list[str] = Field(default_factory=list)


class Provenance(VaultModel):
    origin: Literal["human", "codex_proposal", "canonical_extract", "import"] = "human"
    source_refs: list[SourceRef] = Field(default_factory=list)


class GoalFacetScope(VaultModel):
    # Concepts expand to every evidence facet required by LOs on that concept;
    # facets add explicit facet ids (matched wherever an LO requires them).
    concepts: list[str] = Field(default_factory=list)
    facets: list[str] = Field(default_factory=list)

    def is_empty(self) -> bool:
        return not self.concepts and not self.facets


class GoalExamConfig(VaultModel):
    enabled: bool = False
    item_count: int = 20


class Goal(VaultModel):
    """A measurable commitment: target recall over a facet set by a due date.

    Schema v2. Legacy v1 goals (concept_anchors) convert at load:
    anchors become facet_scope.concepts and target_recall defaults.
    """

    id: str
    title: str
    status: Literal["active", "paused", "completed", "expired"] = "active"
    # Tiebreaker between overlapping goals, not a scheduling weight.
    priority: float = Field(default=0.5, ge=0.0, le=1.0)
    # A facet counts toward the goal when its projected recall at due_at
    # (or the default horizon for open-ended goals) meets this threshold.
    target_recall: float = Field(default=0.8, ge=0.0, le=1.0)
    facet_scope: GoalFacetScope = Field(default_factory=GoalFacetScope)
    due_at: str | None = None
    exam: GoalExamConfig = Field(default_factory=GoalExamConfig)
    # Controlled-writer mirror of the confirmed terminal-contract head (P0.4 §3.4).
    # Written ONLY by goal_contracts.confirm/append_* -- direct YAML draft edits
    # never touch these. None on unconfirmed goals + all legacy vaults.
    confirmed_contract_head_id: str | None = None
    confirmed_contract_hash: str | None = None
    created_at: str
    updated_at: str

    @model_validator(mode="before")
    @classmethod
    def _convert_legacy_concept_anchors(cls, data):
        if not isinstance(data, dict):
            return data
        anchors = data.get("concept_anchors")
        scope = data.get("facet_scope")
        if anchors and not scope:
            converted = dict(data)
            converted.pop("concept_anchors")
            converted["facet_scope"] = {"concepts": list(anchors)}
            return converted
        return data


class GoalsFile(VaultModel):
    schema_version: int = 2
    goals: list[Goal] = Field(default_factory=list)


class SourceSetScope(VaultModel):
    """One unit in a member's scope, with an optional per-unit role override
    (spec_source_ingestion_v2 §4.3 — a textbook chapter's exercise section can
    act as a problem set)."""

    unit_id: str
    role_override: str | None = None


class SourceSetMember(VaultModel):
    """A pinned source in a set. Authoritative role/scope/priority live HERE, not
    on the source note — one source of truth (§4.3). ``revision_id`` is required
    and pinned; ``source_id`` lets the system discover later revisions without
    silently changing the collection. Empty scope = whole artifact."""

    source_id: str
    revision_id: str
    default_role: str = "reference"
    scope: list[SourceSetScope] = Field(default_factory=list)
    priority: int = 1


class SourceSet(VaultModel):
    """A source collection with pinned revisions (§4.3). Scheduling-neutral: goals
    may reference sets via ``source_set_ids``, but a set never references a goal
    and carries no scheduling semantics."""

    id: str
    subject_id: str
    title: str
    members: list[SourceSetMember] = Field(default_factory=list)
    priority: int = 1
    created_at: str | None = None
    updated_at: str | None = None


class SourceSetsFile(VaultModel):
    schema_version: int = 1
    source_sets: list[SourceSet] = Field(default_factory=list)


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


class CriterionTarget(VaultModel):
    """What a rubric criterion observes (knowledge-model §5.1).

    ``capability`` is one of ``CAPABILITY_VOCABULARY`` (stored as TEXT, validated
    in doctor). ``role`` compiles deterministically into certification-credit
    allocations (``primary`` 1.0, ``supporting`` 0.3); it is not causal certainty.
    """

    facet: str
    capability: str
    role: Literal["primary", "supporting"] = "primary"


class RubricCriterion(VaultModel):
    id: str
    points: float
    description: str
    # Two-tier teach-back rubrics: "core" criteria probe one evidence facet
    # each; "transfer" criteria stress-test solid knowledge (edge cases,
    # what-ifs) and carry a reduced, symmetric evidence-mass multiplier.
    # Existing vault files omit the field and default to "core".
    tier: Literal["core", "transfer"] = "core"
    # Knowledge-model §5.1 observation contract (all optional for legacy items;
    # authored ``targets`` always override the mode->capability default mapping).
    targets: list[CriterionTarget] = Field(default_factory=list)
    depends_on: list[str] = Field(default_factory=list)
    correlation_group: str | None = None
    recipe_ids: list[str] = Field(default_factory=list)


class RubricFatalError(VaultModel):
    id: str
    description: str
    max_grade: int
    # Optional link to a registry belief (spec §1.2): when set, this fatal error
    # is the signature a holder of the misconception trips. Absent on legacy items.
    misconception_id: str | None = None


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


# Requirement modality (knowledge-model §8.2): only ``hard`` and exercised
# ``path_specific`` requirements materially affect task likelihood/attribution.
RequirementModality = Literal["hard", "path_specific", "facilitating", "instructional_order"]


class RecipeComponent(VaultModel):
    """One facet-capability requirement inside a recipe (§7.2)."""

    facet: str
    capability: str
    modality: RequirementModality = "hard"


class BlueprintRecipe(VaultModel):
    """A valid method for satisfying a blueprint (§7.2).

    ``all_of`` are conjunctive components (all required for this recipe);
    ``any_of`` are alternative components (at least one). ``integration`` is an
    optional explicit coordination factor authored only when component competence
    can coexist with a repeatable, separately-repairable coordination failure.
    """

    id: str
    composition: Literal["conjunctive"] = "conjunctive"
    all_of: list[RecipeComponent] = Field(default_factory=list)
    any_of: list[RecipeComponent] = Field(default_factory=list)
    integration: RecipeComponent | None = None


class Blueprint(VaultModel):
    """A performance blueprint over one or more requirement recipes (§7.2)."""

    id: str
    weight: float = 1.0
    recipes: list[BlueprintRecipe] = Field(default_factory=list)


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
    # Knowledge-model §7.2 AND/OR requirement recipes. Flat ``evidence_facets``
    # (used for search/legacy compat) is derived from these by the loader, never
    # the source of readiness math. Absent on legacy LOs.
    blueprints: list[Blueprint] = Field(default_factory=list)
    difficulty_prior: float | None = Field(default=None, ge=0.0, le=1.0)
    # Provenance of difficulty_prior; non-hashed metadata (spec §6.1), not item content.
    difficulty_source: Literal["author", "llm_estimate", "empirical", "calibrated"] | None = None
    tags: list[str] = Field(default_factory=list)
    provenance: Provenance = Field(default_factory=Provenance)
    created_at: str
    updated_at: str


def recipe_components(recipe: "BlueprintRecipe") -> list["RecipeComponent"]:
    """Every facet-capability component of a recipe, integration included."""

    components = list(recipe.all_of) + list(recipe.any_of)
    if recipe.integration is not None:
        components.append(recipe.integration)
    return components


def learning_object_facet_union(lo: "LearningObject") -> list[str]:
    """Derived flat union of every facet referenced by an LO's blueprints (§7.2).

    This replaces a hand-authored flat ``evidence_facets`` list: it is used for
    search and legacy compatibility only, never as the source of readiness math.
    Deterministic (first-seen order).
    """

    seen: dict[str, None] = {}
    for blueprint in lo.blueprints:
        for recipe in blueprint.recipes:
            for component in recipe_components(recipe):
                seen.setdefault(component.facet, None)
    return list(seen)


class HintPolicy(VaultModel):
    max_useful_hints: int = 0
    fsrs_rating_cap_by_hint: dict[int | str, str] = Field(default_factory=dict)
    mastery_alpha_dampening_by_hint: dict[int | str, float] = Field(default_factory=dict)
    coverage_surface_dampening_by_hint: dict[int | str, float] = Field(default_factory=dict)


class EvidenceFingerprint(VaultModel):
    """Global surface/correlation fingerprint (knowledge-model §6).

    Vault-wide familiarity/correlation lookup keys on these fields so a near-clone
    under another LO cannot mint fresh independent evidence after facet state
    becomes global. All optional and additive; legacy items omit it entirely.
    """

    source_family: str | None = None
    shared_stimulus_id: str | None = None
    representation: str | None = None
    solution_recipe_family: str | None = None
    answer_structure: str | None = None


class PracticeItem(VaultModel):
    schema_version: int = 1
    id: str
    learning_object_id: str
    subjects: list[str] | None = None
    practice_mode: str
    attempt_types_allowed: list[AttemptType] = Field(default_factory=list)
    evidence_facets: list[str] = Field(default_factory=list)
    evidence_weights: dict[str, float] = Field(default_factory=dict)
    criterion_facet_weights: dict[str, dict[str, float]] = Field(default_factory=dict)
    prompt: str
    expected_answer: str | dict[str, Any]
    difficulty: float | None = Field(default=None, ge=0.0, le=1.0)
    # Provenance of difficulty; non-hashed metadata (spec §6.1), not item content.
    difficulty_source: Literal["author", "llm_estimate", "empirical", "calibrated"] | None = None
    tags: list[str] = Field(default_factory=list)
    hints: list[str] = Field(default_factory=list)
    hint_policy: HintPolicy = Field(default_factory=HintPolicy)
    retrieval_demand: float | None = Field(default=None, ge=0.0, le=1.0)
    transfer_distance: float | None = Field(default=None, ge=0.0, le=1.0)
    scaffold_level: float | None = Field(default=None, ge=0.0, le=1.0)
    # Depth-rung metadata (spec v2 §4 / spec_p1 §3.4): the closed-vocab
    # capability + the item's point in task-feature space, stamped by the rung-
    # targeted generation path. Optional so pre-rung vault files load unchanged.
    capability: Literal[
        "retrieval", "schema_interpretation", "procedure_execution", "method_selection", "coordination"
    ] | None = None
    task_features: dict[str, Any] | None = None
    # Schema pin for task_features (e.g. "p1_launch@1"); stamped server-side.
    task_feature_schema: str | None = None
    surface_family: str | None = None
    evidence_fingerprint: EvidenceFingerprint = Field(default_factory=EvidenceFingerprint)
    # spec §5.2.2: for generated diagnostics, the categorically-divergent answer a
    # holder of the targeted belief would give. Round-trips through patches so the
    # sim gate and review policy can read it off the applied item. None otherwise.
    misconception_consistent_answer: str | None = None
    repair_targets: list[str] = Field(default_factory=list)
    grading_rubric: Rubric | None = None
    # Learner-owned lifecycle (Andy: readers control the prompts they collect).
    # `retired` items keep every attempt/evidence row but are never served again;
    # state_sync deactivates their scheduler state on the next sync.
    status: Literal["active", "retired"] = "active"
    status_reason: str | None = None
    provenance: Provenance = Field(default_factory=Provenance)
    created_at: str
    updated_at: str


def discriminates(item: "PracticeItem", rubric: "Rubric | None" = None) -> dict[str, list[str]]:
    """Item-level view of which misconceptions this item's fatal errors catch.

    Derived (not authored): maps ``misconception_id`` -> [fatal_error_id] from the
    ``misconception_id`` links on the resolved rubric's fatal errors (spec §1.2).
    ``rubric`` defaults to the item's own ``grading_rubric``; pass the resolved
    rubric when the item inherits fatal errors from a default rubric.
    """

    resolved = rubric if rubric is not None else item.grading_rubric
    mapping: dict[str, list[str]] = {}
    if resolved is None:
        return mapping
    for fatal_error in resolved.fatal_errors:
        misconception_id = getattr(fatal_error, "misconception_id", None)
        if not misconception_id:
            continue
        mapping.setdefault(misconception_id, []).append(fatal_error.id)
    return mapping


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


# Closed, domain-general capability vocabulary (knowledge-model §4.1). Stored
# as TEXT everywhere and validated in app code (doctor), never as a DB/pydantic
# enum, so extension stays additive.
CAPABILITY_VOCABULARY: tuple[str, ...] = (
    "retrieval",
    "schema_interpretation",
    "procedure_execution",
    "method_selection",
    "coordination",
)

FacetKind = Literal[
    "definition",
    "proposition",
    "procedure_contract",
    "applicability_condition",
    "interpretation",
]


class FacetProvenance(VaultModel):
    """Synthesis-time embedded provenance snapshot for a facet (§3.2).

    ``entity_source_links`` is authoritative for current multi-source facet
    provenance; this YAML field is the snapshot legacy readers use.
    """

    origin: Literal["sourceset_synthesis", "manual", "facet_normalization"] = "manual"
    source_refs: list[SourceRef] = Field(default_factory=list)


class EvidenceFacet(VaultModel):
    """A registry entry for an assessable semantic atom (schema_version 2, §3.2).

    Schema v1 registries keep loading unchanged: every v2 field is optional and
    defaulted, so a legacy ``{id, title, aliases, ...}`` facet parses as before.
    """

    id: str
    title: str | None = None
    aliases: list[str] = Field(default_factory=list)
    description: str | None = None
    tags: list[str] = Field(default_factory=list)
    # Schema v2 semantic contract (all optional; absent on legacy v1 entries).
    concept_id: str | None = None
    kind: FacetKind | None = None
    claim: str | None = None
    preconditions: list[str] = Field(default_factory=list)
    postconditions: list[str] = Field(default_factory=list)
    applicability: list[str] = Field(default_factory=list)
    positive_examples: list[str] = Field(default_factory=list)
    negative_examples: list[str] = Field(default_factory=list)
    non_goals: list[str] = Field(default_factory=list)
    error_signatures: list[str] = Field(default_factory=list)
    instructional_repairs: list[str] = Field(default_factory=list)
    status: Literal["proposed", "reviewed", "retired"] = "reviewed"
    version: int = 1
    # Deterministic hash of the normalized semantic contract; proposes cross-vault
    # reuse, never asserts equivalence. Computed at load when omitted.
    semantic_fingerprint: str | None = None
    provenance: FacetProvenance = Field(default_factory=FacetProvenance)


class EvidenceFacetsFile(VaultModel):
    schema_version: int = 1
    facets: list[EvidenceFacet] = Field(default_factory=list)


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
    evidence_facets: dict[str, EvidenceFacet] = field(default_factory=dict)
    facet_aliases: dict[str, str] = field(default_factory=dict)
    notes: dict[str, Note] = field(default_factory=dict)
    source_sets: list[SourceSet] = field(default_factory=list)
    issues: list[DoctorIssue] = field(default_factory=list)

    def learning_object_for_item(self, item: PracticeItem) -> LearningObject | None:
        return self.learning_objects.get(item.learning_object_id)

    def subjects_for_item(self, item: PracticeItem) -> list[str]:
        if item.subjects is not None:
            return item.subjects
        lo = self.learning_object_for_item(item)
        return lo.subjects if lo else []

    def canonical_facet_id(self, facet_id: str) -> str:
        return self.facet_aliases.get(facet_id, facet_id)

    def rubric_for_item(self, item: PracticeItem) -> Rubric | None:
        return item.grading_rubric or self.default_rubrics.get(item.practice_mode)
