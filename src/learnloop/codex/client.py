from __future__ import annotations

import json
import logging
import os
import shlex
import shutil
import sys
import threading
import urllib.error
import urllib.request
from dataclasses import asdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from typing import Iterator, Literal, Mapping, Protocol

from pydantic import BaseModel, ValidationError

from learnloop.config import CodexConfig
from learnloop.token_usage import (
    TokenUsage,
    TokenUsageAccounting,
    usage_from_chat_response,
    usage_from_codex_turn,
)
from learnloop.codex.prompts import (
    AUTHORING_PROMPT_VERSION,
    CANONICAL_INGEST_PROMPT_VERSION,
    DIAGNOSTIC_TRIALS_PROMPT_VERSION,
    GRADING_PROMPT_VERSION,
    MISCONCEPTION_MATCH_PROMPT_VERSION,
    PROBE_DIALOGUE_TURN_PROMPT,
    PROBE_DIALOGUE_TURN_PROMPT_VERSION,
    PROBE_FAMILY_TRIALS_PROMPT,
    PROBE_FAMILY_TRIALS_PROMPT_VERSION,
    PROBE_INSTANCE_PROMPT,
    PROBE_INSTANCE_PROMPT_VERSION,
    PROMOTION_ANALYSIS_PROMPT,
    PROMOTION_ANALYSIS_PROMPT_VERSION,
    DEPTH_EDGE_INSTANCE_PROMPT,
    DEPTH_EDGE_INSTANCE_PROMPT_VERSION,
    RUNG_BACKFILL_PROMPT,
    RUNG_BACKFILL_PROMPT_VERSION,
    EXERCISE_AUTHORING_PROMPT,
    EXERCISE_AUTHORING_PROMPT_VERSION,
    READER_PRESET_SYNTHESIS_PROMPT,
    READER_PRESET_SYNTHESIS_PROMPT_VERSION,
    READING_QUICK_CHECK_PROMPT,
    READING_QUICK_CHECK_PROMPT_VERSION,
    APPEND_RECONCILIATION_PROMPT,
    APPEND_RECONCILIATION_PROMPT_VERSION,
    CONCEPT_ANIMATION_PROMPT,
    CONCEPT_ANIMATION_PROMPT_VERSION,
    CONCEPT_GRAPH_STRUCTURING_PROMPT,
    CONCEPT_GRAPH_STRUCTURING_PROMPT_VERSION,
    SOURCE_SET_SYNTHESIS_PROMPT,
    SOURCE_SET_SYNTHESIS_PROMPT_VERSION,
    SOURCE_UNIT_INVENTORY_PROMPT,
    SOURCE_UNIT_INVENTORY_PROMPT_VERSION,
    TEACH_BACK_AUTHORING_PROMPT_VERSION,
    TEACH_BACK_PROMPT_VERSION,
    TUTOR_QA_PROMPT_VERSION,
)
from learnloop.codex.schemas import (
    AuthoringProposal,
    DiagnosticTrials,
    GradingProposal,
    MisconceptionMatch,
    ProbeDialogueTurn,
    ProbeFamilyTrials,
    ProbeInstanceSurfaces,
    PromotionAnalysis,
    DepthEdgeInstanceBatch,
    ExerciseAuthoring,
    RungBackfillClassification,
    ReaderPresetSynthesis,
    ReadingQuickCheck,
    AppendReconciliation,
    ConceptGraphStructuring,
    ManimAnimation,
    SourceSetSynthesis,
    SourceUnitInventory,
    TeachBackAuthoring,
    TeachBackQuestion,
    TutorAnswer,
    WireModel,
    describe_wire_validation_error,
)

LOG = logging.getLogger(__name__)
EVENT_FIELDS_ATTR = "event_fields"

SourceKind = Literal["website_page", "youtube_video", "arxiv_html", "textbook_chapter"]
ChunkKind = Literal["prose", "heading", "code", "math", "caption"]


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


@dataclass(frozen=True)
class SourceChunk:
    """A bounded slice of normalized source Markdown with a stable locator.

    ``locator`` is content-derived and stable across re-fetches (see the spec's
    locator-stability rules); Codex echoes it back in ``SourceRef.locator`` so
    extracted items resolve to a specific span of the registered source.
    """

    locator: str
    text: str
    chunk_kind: ChunkKind = "prose"
    heading_path: list[str] = field(default_factory=list)
    label: str | None = None
    ordinal: int = 0


@dataclass(frozen=True)
class ExtractionPlan:
    """Ordered plan handed to the canonical-ingestor role.

    Learning Objects are created first, then Practice Items, concept edges, and
    rubric drafts attach to them. ``learning_object_required`` is ``False`` only
    in textbook-anchored mode, where retrieving practice for the supplied LOs is
    the primary output and new LOs are gap proposals.
    """

    create_learning_objects_first: bool = True
    attach_practice_items: bool = True
    attach_concept_edges: bool = True
    attach_rubric_drafts: bool = True
    allow_generative_practice_items: bool = True
    require_source_ref_per_item: bool = True
    learning_object_required: bool = True


@dataclass(frozen=True)
class CanonicalIngestContext:
    """Bounded, deterministic input for ``run_canonical_ingest``.

    LearnLoop fetches, normalizes, hashes, and registers the source before
    building this context; Codex only performs semantic extraction over the
    supplied chunks and never fetches URLs or writes files. ``canonical_source``
    is a descriptor of the already-registered canonical-source note: ``id``,
    ``path``, ``canonical_uri``, ``original_uri``, ``title``, ``authors``,
    ``content_hash``, ``retrieved_at``, and ``license_hint``.
    """

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


@dataclass(frozen=True)
class GradingContext:
    attempt_id: str
    practice_item_id: str
    prompt: str
    expected_answer: str
    learner_answer_md: str
    rubric: dict
    evidence_facets: list[str] = field(default_factory=list)
    evidence_weights: dict[str, float] = field(default_factory=dict)
    criterion_facet_weights: dict[str, dict[str, float]] = field(default_factory=dict)
    trace_contract: dict[str, Any] | None = None
    error_taxonomy: dict[str, Any] = field(default_factory=dict)
    # Meas §3.A6: the vocabulary the grader may report trace observations
    # against. Scoped to the item's own learning object rather than the whole
    # vault, for two reasons: a vault-wide list is unbounded token cost on every
    # grading call, and a grader offered every facet in the subject is being
    # invited to pattern-match the vocabulary rather than read the work, which
    # is A6's own revert criterion.
    facet_registry: list[dict[str, str]] = field(default_factory=list)
    # Meas §3.A5: the item's authored candidate hypotheses and what a holder of
    # each visibly produces. A PRIOR over causes the grader may match the trace
    # against and must be free to reject — never a posterior, never a constraint
    # (causal §1 principle 4). Empty on every item that authors none, and the
    # prompt says nothing about profiles when it is empty, so a grader is never
    # shown a candidate set that does not exist.
    discrimination_profiles: list[dict[str, Any]] = field(default_factory=list)
    # Meas §3.A8: the clarification question and the learner's answer, present
    # only on the re-grade that resolves it. Carried in the context (and so in
    # `grading_context_hash`) rather than spliced into `learner_answer_md`,
    # because the answer is a different artifact from the attempt: it arrived
    # later, under a question, and a resolved grade must be able to say so.
    clarification_exchange: dict[str, str] | None = None
    # Meas §3.A3: the worked solution the learner was asked to repair. The
    # planted errors themselves are deliberately NOT included — the grader
    # reports what the learner claimed and repaired, and the harness (which knows
    # where the plants are) decides what each report is worth. Handing the grader
    # the answer key would make every report a confirmation.
    error_hunt_solution: str | None = None
    # Aug C2: deterministic observations available DURING diagnosis.  Every
    # outcome is typed, and parse_failed/unsupported explicitly confer nothing.
    verifier_observations: list[dict[str, Any]] = field(default_factory=list)
    # Aug C4: bounded raw prior traces on the same facet and surface family.
    # Prior diagnoses are omitted so history supplies evidence, not an answer to
    # copy.  The cause-change control in B1 watches the resulting anchoring risk.
    diagnostic_history: list[dict[str, Any]] = field(default_factory=list)


@dataclass(frozen=True)
class TutorQAContext:
    """Bounded input for one tutor Q&A turn.

    ``context`` selects the guardrail profile (practice = Socratic, no answer
    reveal or verification; feedback = full explanation grounded in the graded
    attempt; library = explanatory, grounded in the note body).
    ``candidate_facets`` is the closed facet vocabulary the classification may
    map the question onto. ``thread`` is the prior Q&A turns in this context,
    oldest first, as {question_md, answer_md, question_type} dicts.
    """

    context: str  # "library" | "practice" | "feedback" | "reader"
    question_md: str
    candidate_facets: list[str] = field(default_factory=list)
    thread: list[dict] = field(default_factory=list)
    practice_item_prompt: str | None = None
    expected_answer: str | None = None
    rubric: dict | None = None
    learner_answer_md: str | None = None
    grading_feedback: dict | None = None
    note_title: str | None = None
    note_body: str | None = None
    learning_object_summaries: list[dict] = field(default_factory=list)
    # §12.1 typed transition: when a diagnostic episode on this LO just ended
    # in tutoring, the persisted decision (diagnosed_gap, tutor_move,
    # scaffold_level, answer_reveal_budget, target_facets, …) steers the tutor
    # prose instead of being re-derived from scratch.
    diagnostic_decision: dict | None = None
    # ING M8 (§9.2): bounded semantic-authority source spans for the LO/facets in
    # context ({extraction_id, span_id, label, relation, semantic_authority, text}).
    # The tutor may cite ONLY these; held-out exam spans are excluded upstream.
    source_spans: list[dict] = field(default_factory=list)
    # U-033 (§7.6): per-ask reader answer mode -- answer_directly / help_me_reason
    # / ask_me_first. Selects how the `reader` profile answers; None for the
    # library/practice/feedback profiles. NEVER carries the learner ability
    # estimate or any assessment-reserved statement/rubric (manifest invariant).
    answer_mode: str | None = None


@dataclass(frozen=True)
class TeachBackQuestionContext:
    """Bounded input for one teach-back naive-student question.

    The learner is teaching the practice item's concept; the AI plays a
    curious naive student. ``criterion_id``/``criterion_description``/
    ``facet_targets`` name the rubric criterion the next question must probe
    (selected by the uncertainty-ranked follow-up plan). ``transcript`` is the
    conversation so far, oldest first, as {role, content_md} dicts with role
    "learner" or "ai" — the question must not re-ask what it already covers.
    """

    practice_item_id: str
    practice_item_prompt: str
    criterion_id: str
    criterion_description: str
    criterion_tier: str  # "core" | "transfer"
    facet_targets: list[str] = field(default_factory=list)
    transcript: list[dict] = field(default_factory=list)
    question_number: int = 1
    max_followups: int = 4
    learning_object_title: str | None = None
    learning_object_summary: str | None = None


@dataclass(frozen=True)
class TeachBackAuthoringContext:
    """Bounded source contract for authoring one teach-back transformation.

    ``quest_sentence`` is resolved from the highest-priority relevant active
    goal: explicit learner intent first, then an operational exam/practice
    fallback. It may shape only the transfer scenario; the original item and
    criterion contract remain the authority for the core explanation.
    """

    source_practice_item_id: str
    source_prompt: str
    source_expected_answer: Any
    source_criteria: list[dict] = field(default_factory=list)
    source_trace_contract: dict | None = None
    allowed_facets: list[dict] = field(default_factory=list)
    learning_object_title: str = ""
    learning_object_summary: str = ""
    quest_sentence: str | None = None
    max_core_criteria: int = 3


@dataclass(frozen=True)
class PromotionAnalysisContext:
    """Bounded input for the Step-0 promotion analysis (spec_tutor_promotion.md §3).

    ``thread`` is the reconstructed Q&A conversation (oldest first, as
    {question_md, answer_md, question_type} dicts); the LAST turn is the one being
    promoted and its ``answer_md`` carries the tutor's socratic question. The
    origin LO's ``facet_vocabulary`` is the closed set of existing evidence facet
    ids to reuse; ``concept_neighbors`` are the concepts reachable from the LO's
    concept via concept edges ({id, title, relation}) for the existing-concepts
    context. ``existing_items`` lists the origin LO's practice items as {id,
    prompt, surface_family, evidence_facets} for the dedup decision. ``intent`` is
    ``"practice"`` or ``"gap"``.
    """

    intent: str
    thread: list[dict] = field(default_factory=list)
    learning_object_id: str | None = None
    learning_object_title: str | None = None
    facet_vocabulary: list[str] = field(default_factory=list)
    concept_neighbors: list[dict] = field(default_factory=list)
    existing_items: list[dict] = field(default_factory=list)


@dataclass(frozen=True)
class ProbeInstanceContext:
    """Bounded input for LLM-backed Item Instance surfaces (probe redesign §9.2).

    One call generates ``count`` surface-varied instances for one admitted
    family/card binding. ``measurement_intent`` states the family's measurement
    pattern in prose; ``existing_prompts``/``existing_surface_families`` are the
    LO's current items for the §5.4 duplication constraint. The structural
    instance gate re-validates every returned surface before persistence.
    """

    family_template_id: str
    family_template_version: int
    instrument_kind: str
    measurement_intent: str
    learning_object_id: str
    learning_object_title: str
    learning_object_concept: str
    learning_object_summary: str
    target_facets: list[str] = field(default_factory=list)
    confusable_concept: str | None = None
    observation_alphabet: list[str] = field(default_factory=list)
    count: int = 2
    existing_prompts: list[str] = field(default_factory=list)
    existing_surface_families: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ProbeDialogueTurnContext:
    """Bounded input for one adaptive dialogue microprobe turn (§8.1).

    ``prior_turns`` is the block so far, oldest first, as
    {kind, prompt_md, learner_answer_md} dicts — the generated turn conditions
    on the learner's actual committed answers, which is what makes the dialogue
    adaptive rather than a slot-filled script.
    """

    turn_kind: str  # commit | reason | counterfactual | counterexample
    turn_number: int
    planned_turns: int
    learning_object_id: str
    learning_object_title: str
    learning_object_concept: str
    learning_object_summary: str
    target_facets: list[str] = field(default_factory=list)
    confusable_concept: str | None = None
    prior_turns: list[dict] = field(default_factory=list)


@dataclass(frozen=True)
class ProbeFamilyTrialsContext:
    """Bounded input for LLM planted trials feeding the family admission gate
    (probe redesign §9.6).

    ``surfaces`` are the concrete instance surfaces under test as
    {surface_suffix, prompt_md, expected_answer_md} dicts; ``hypothesis_slots``
    are the card-bound planted states; ``observation_alphabet`` is the closed
    outcome vocabulary ``matched_outcome`` must come from. The deterministic
    gate (reverse matching, pair separation, controls) runs in LearnLoop code
    on the returned trials.
    """

    family_template_id: str
    family_template_version: int
    instrument_kind: str
    measurement_intent: str
    learning_object_title: str
    learning_object_summary: str
    target_facets: list[str] = field(default_factory=list)
    confusable_concept: str | None = None
    hypothesis_slots: list[str] = field(default_factory=list)
    observation_alphabet: list[str] = field(default_factory=list)
    non_applicable_controls: list[str] = field(default_factory=list)
    surfaces: list[dict] = field(default_factory=list)
    trials_per_hypothesis: int = 3


@dataclass(frozen=True)
class ReaderPresetSynthesisContext:
    """Bounded input for one demand-paged reader preset request (spec §6.3).

    ``blocks`` is the merged smallest-sufficient window as [{span_id, text}];
    ``selected_span_ids`` identifies learner-selected blocks within that window;
    ``selected_text`` is the exact learner-selected surface inside that window
    (or the learner's OCR correction when ``selection_edited`` is true);
    ``learner_text`` is the learner's optional note/question. Both are
    untrusted — the prompt delimits them and instructs the model to ignore
    embedded instructions.
    """

    preset: str
    selected_text: str = ""
    selection_edited: bool = False
    selected_span_ids: list = field(default_factory=list)
    learner_text: str = ""
    section_path: list = field(default_factory=list)
    section_paths: list = field(default_factory=list)
    blocks: list = field(default_factory=list)


@dataclass(frozen=True)
class ReadingQuickCheckContext:
    """Bounded input for one section-boundary quick check (reader producer).

    ``section`` is {section_id, label, blocks:[{span_id, kind, text}]} — the
    readable blocks of ONE guide section. The source text is untrusted — the
    prompt delimits it and instructs the model to ignore embedded instructions.
    """

    extraction_id: str
    section: dict = field(default_factory=dict)


@dataclass(frozen=True)
class RungBackfillContext:
    """Bounded input for legacy-item rung classification (depth backfill).

    ``items`` are {practice_item_id, practice_mode, prompt_excerpt,
    expected_answer_excerpt, retrieval_demand, transfer_distance,
    scaffold_level}. Item text is untrusted source-derived material — the
    prompt instructs the model to treat embedded directives as inert.
    """

    items: list[dict] = field(default_factory=list)
    task_feature_schema: dict = field(default_factory=dict)


@dataclass(frozen=True)
class ExerciseAuthoringContext:
    """Bounded input for reader exercise import (exact-exercise slice).

    ``exercise_text`` is the learner's verbatim selection (one or several
    consecutive textbook exercises); ``segments`` are its resolved source
    anchors [{span_id, exact_quote}]; ``context_blocks`` is the bounded
    surrounding material [{span_id, kind, text}] (shared preambles,
    definitions in scope). ``learning_objects`` is the curriculum catalog
    [{id, title, summary, facets:[{id, title}]}] the item must map into;
    ``task_feature_schema`` is the p1_launch dimension table. Source text is
    untrusted — the prompt instructs the model to treat embedded directives
    as inert.
    """

    extraction_id: str
    exercise_text: str = ""
    segments: list = field(default_factory=list)
    section_path: list = field(default_factory=list)
    context_blocks: list = field(default_factory=list)
    learning_objects: list = field(default_factory=list)
    learning_object_hint: str = ""
    task_feature_schema: dict = field(default_factory=dict)


@dataclass(frozen=True)
class DepthEdgeInstanceContext:
    """Bounded input for LLM depth-edge-instance authoring (spec v2 depth).

    ``templates`` are reviewed edge-template bodies; ``envelope_bounds`` /
    ``current_milestones`` describe the commitment's authorized region and DAG;
    ``pattern_slugs`` lists admitted activity patterns; ``task_feature_schema``
    is the p1_launch dimension table. Instances are candidates only —
    deterministic gates admit them.
    """

    commitment_id: str
    templates: list[dict] = field(default_factory=list)
    envelope_bounds: dict = field(default_factory=dict)
    current_milestones: list[dict] = field(default_factory=list)
    pattern_slugs: list[str] = field(default_factory=list)
    task_feature_schema: dict = field(default_factory=dict)
    count: int = 1


@dataclass(frozen=True)
class SourceUnitInventoryContext:
    """Bounded input for one role-aware unit inventory (source-ingestion §7).

    ``unit_view`` is the deterministic M3-style inventory view of ONE unit (or
    one oversize-unit window): {unit_id, semantic_hash, label, section_heading,
    blocks:[{span_id, kind, text}], window_ordinal, window_count}. ``role`` is
    the confirmed membership/unit role (§4.2) and ``inventory_profile`` is the
    requested profile. The source text is untrusted — the prompt delimits it and
    instructs the model to ignore embedded instructions.
    """

    unit_id: str
    semantic_hash: str
    role: str
    inventory_profile: str  # semantic | practice | assessment | combined
    unit_view: dict = field(default_factory=dict)


@dataclass(frozen=True)
class SourceSetSynthesisContext:
    """Bounded input for one bootstrap synthesis pass/shard (§8.5).

    Carries role-specific unit inventories (NOT raw documents), the synthesis
    brief, a compact existing-registry index, and the exam assessment-alignment
    view (aggregate profile + cited task metadata only — held-out wording is
    NEVER included). ``resolved_spans`` holds the one bounded span-request round's
    resolved evidence (empty on pass 1). All text is untrusted; the prompt
    delimits it and cites provided span ids only.
    """

    source_set_id: str
    subject_id: str
    mode: str  # bootstrap
    brief: dict = field(default_factory=dict)
    unit_inventories: list = field(default_factory=list)
    exam_profile: dict = field(default_factory=dict)
    registry_index: dict = field(default_factory=dict)
    resolved_spans: list = field(default_factory=list)
    shard_ordinal: int = 0
    shard_count: int = 1


@dataclass(frozen=True)
class ConceptGraphContext:
    """Bounded input for the post-merge concept graph-structuring pass (§8.5).

    Carries the merged candidate's compact concept list, per-source outline
    skeletons built from already-paid-for artifacts (the deterministic unit
    tree + cached unit-inventory summaries and prerequisite hints), and the
    existing registry (concepts + edges) so new structure attaches into the
    current graph — never raw source text. The service validates the returned
    merge groups and relations and applies them deterministically; an invalid
    group or edge is a no-op, never an error."""

    source_set_id: str
    subject_id: str
    concepts: list = field(default_factory=list)
    source_skeletons: list = field(default_factory=list)
    registry_concepts: list = field(default_factory=list)
    registry_edges: list = field(default_factory=list)


@dataclass(frozen=True)
class ConceptAnimationContext:
    """Bounded input for one Manim explainer-scene authoring call.

    Carries the concept's title/description plus a few learning-object
    excerpts — never raw source text. ``repair`` (when present) holds the
    previous scene code and either validator violations or renderer stderr for
    the one bounded repair round-trip. The returned scene code is candidate
    only: an AST allowlist validates it and a constrained subprocess renders
    it, with per-run learner consent as the actual boundary."""

    concept_id: str
    concept_title: str
    concept_description: str = ""
    learning_objects: list = field(default_factory=list)
    max_duration_seconds: int = 45
    latex_available: bool = False
    repair: dict | None = None


@dataclass
class AppendReconciliationContext:
    """Bounded input for one append reconciliation pass/shard (§10.1).

    Carries the NEW/changed role-specific unit inventories, the brief, the bounded
    affected-map neighborhood (NEVER the full map — the scaling gate proves it), and
    the exam assessment-alignment view. ``change_kind`` is ``source_added`` or
    ``source_revision_changed``; for the latter, ``revision_diff`` holds the
    deterministic old/new span diff. All text is untrusted; the prompt delimits it
    and cites provided span ids only."""

    source_set_id: str
    subject_id: str
    change_kind: str  # source_added | source_revision_changed
    brief: dict = field(default_factory=dict)
    new_inventories: list = field(default_factory=list)
    neighborhood: dict = field(default_factory=dict)
    exam_profile: dict = field(default_factory=dict)
    revision_diff: dict = field(default_factory=dict)
    resolved_spans: list = field(default_factory=list)
    shard_ordinal: int = 0
    shard_count: int = 1


class CodexClient(Protocol):
    def consume_usage(self) -> TokenUsage:
        """Read-and-reset provider-reported token usage (A7; see token_usage)."""
        ...

    def run_authoring_proposal(self, context: AuthoringContext) -> AuthoringProposal:
        ...

    def run_canonical_ingest(self, context: CanonicalIngestContext) -> AuthoringProposal:
        ...

    def run_grading_proposal(self, context: GradingContext) -> GradingProposal:
        ...

    def run_tutor_qa(self, context: TutorQAContext) -> TutorAnswer:
        ...

    def run_teach_back_question(self, context: TeachBackQuestionContext) -> TeachBackQuestion:
        ...

    def run_teach_back_authoring(self, context: TeachBackAuthoringContext) -> TeachBackAuthoring:
        ...

    def run_misconception_match(self, context: Any) -> MisconceptionMatch:
        ...

    def run_promotion_analysis(self, context: Any) -> PromotionAnalysis:
        ...


class CodexUnavailable(RuntimeError):
    pass


class CodexInterrupted(CodexUnavailable):
    """Raised when a LearnLoop-owned Codex turn is explicitly interrupted."""


class CodexTurnTimeout(CodexUnavailable, TimeoutError):
    """Raised after a Codex SDK turn exceeds its wall-clock deadline."""


def make_codex_client(config: CodexConfig, vault_root: Path) -> CodexClient:
    provider = config.provider.lower()
    if provider == "http":
        return HttpCodexClient(config)
    if provider == "sdk":
        return SdkCodexClient(config, vault_root)
    raise CodexUnavailable(f"Unsupported Codex provider {config.provider!r}")


#: Transport-level keys an app-server may report beside a flat proposal body.
#: They belong to the response envelope, never to the wire contract.
_HTTP_ENVELOPE_KEYS = frozenset({"usage"})


class HttpCodexClient(TokenUsageAccounting):
    """Minimal local Codex app-server client.

    The MVP transport is intentionally small: JSON POSTs to a local app-server.
    The server may return the proposal directly or under a top-level
    ``proposal`` key.
    """

    def __init__(self, config: CodexConfig):
        self.config = config
        self.provider_name = "codex"
        self.provider_type = "http_adapter"
        self.model = config.model

    def run_authoring_proposal(self, context: AuthoringContext) -> AuthoringProposal:
        payload = self._post(self.config.authoring_path, {"context": asdict(context)}, purpose="authoring")
        return self._validated(AuthoringProposal, payload, purpose="authoring")

    def run_canonical_ingest(self, context: CanonicalIngestContext) -> AuthoringProposal:
        payload = self._post(
            self.config.canonical_ingest_path,
            {"context": asdict(context)},
            purpose="canonical_ingest",
        )
        return self._validated(AuthoringProposal, payload, purpose="canonical_ingest")

    def run_grading_proposal(self, context: GradingContext) -> GradingProposal:
        payload = self._post(self.config.grading_path, {"context": asdict(context)}, purpose="grading")
        return self._validated(GradingProposal, payload, purpose="grading")

    def run_tutor_qa(self, context: TutorQAContext) -> TutorAnswer:
        payload = self._post(self.config.tutor_qa_path, {"context": asdict(context)}, purpose="tutor_qa")
        return self._validated(TutorAnswer, payload, purpose="tutor_qa")

    def run_teach_back_question(self, context: TeachBackQuestionContext) -> TeachBackQuestion:
        payload = self._post(self.config.teach_back_path, {"context": asdict(context)}, purpose="teach_back")
        return self._validated(TeachBackQuestion, payload, purpose="teach_back")

    def run_teach_back_authoring(self, context: TeachBackAuthoringContext) -> TeachBackAuthoring:
        payload = self._post(
            self.config.teach_back_authoring_path,
            {"context": asdict(context)},
            purpose="teach_back_authoring",
        )
        return self._validated(TeachBackAuthoring, payload, purpose="teach_back_authoring")

    def run_misconception_match(self, context: Any) -> MisconceptionMatch:
        context_payload = context if isinstance(context, dict) else asdict(context)
        payload = self._post(
            self.config.misconception_match_path,
            {"context": context_payload},
            purpose="misconception_match",
        )
        return self._validated(MisconceptionMatch, payload, purpose="misconception_match")

    def run_promotion_analysis(self, context: Any) -> PromotionAnalysis:
        context_payload = context if isinstance(context, dict) else asdict(context)
        payload = self._post(
            getattr(self.config, "promotion_analysis_path", "/promotion-analysis"),
            {"context": context_payload},
            purpose="promotion_analysis",
        )
        return self._validated(PromotionAnalysis, payload, purpose="promotion_analysis")

    def _validated(self, model_type: type[BaseModel], payload: dict, *, purpose: str) -> Any:
        """Validate one app-server response body against its wire contract.

        The transport envelope is stripped first. The adapter contract says the
        server "may return the proposal directly or under a top-level
        ``proposal`` key", and separately that it may report ``usage`` beside it
        (see ``_post``) — so on the flat shape the metering object is part of
        the envelope, not of the proposal, and stripping it is what keeps
        ``WireModel``'s ban aimed at genuine contract divergence. Before that
        ban, a flat-shaped body simply had its ``usage`` deleted here in
        silence, which is the same failure mode from the other side: the model
        was never wrong, it just never learned it was being ignored.
        """

        if "proposal" in payload:
            body: Any = payload["proposal"]
        else:
            body = {key: value for key, value in payload.items() if key not in _HTTP_ENVELOPE_KEYS}
        try:
            return model_type.model_validate(body)
        except ValidationError as exc:
            raise CodexUnavailable(
                f"Codex app-server returned an invalid {purpose} response: "
                f"{describe_wire_validation_error(model_type, exc)}"
            ) from exc

    def _post(self, path: str, payload: dict, *, purpose: str) -> dict:
        url = _url(self.config.base_url, path)
        _log_codex_debug(
            "codex.http.request",
            provider="codex",
            provider_type=self.provider_type,
            purpose=purpose,
            model=self.config.model,
            url=url,
            path=path,
            request_payload=payload,
        )
        request = urllib.request.Request(
            url,
            data=json.dumps(payload, sort_keys=True).encode("utf-8"),
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.config.healthcheck_timeout_seconds) as response:
                raw = response.read()
        except urllib.error.HTTPError as exc:
            _log_codex_debug(
                "codex.error",
                provider="codex",
                provider_type=self.provider_type,
                purpose=purpose,
                model=self.config.model,
                url=url,
                path=path,
                error=f"HTTP {exc.code}",
            )
            raise CodexUnavailable(f"Codex app-server HTTP {exc.code}") from exc
        except urllib.error.URLError as exc:
            _log_codex_debug(
                "codex.error",
                provider="codex",
                provider_type=self.provider_type,
                purpose=purpose,
                model=self.config.model,
                url=url,
                path=path,
                error=str(exc.reason),
            )
            raise CodexUnavailable(str(exc.reason)) from exc
        try:
            decoded = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            _log_codex_debug(
                "codex.error",
                provider="codex",
                provider_type=self.provider_type,
                purpose=purpose,
                model=self.config.model,
                url=url,
                path=path,
                response_text=_decode_lossy(raw),
                error="invalid_json",
            )
            raise CodexUnavailable("Codex app-server returned invalid JSON") from exc
        if not isinstance(decoded, dict):
            _log_codex_debug(
                "codex.error",
                provider="codex",
                provider_type=self.provider_type,
                purpose=purpose,
                model=self.config.model,
                url=url,
                path=path,
                response=decoded,
                error="non_object_response",
            )
            raise CodexUnavailable("Codex app-server response must be a JSON object")
        # A7: the adapter contract does not require a `usage` object, so this is
        # opportunistic — an app-server that reports one in the OpenAI shape gets
        # metered, one that does not leaves the run's actual_* columns at 0.
        self.record_token_usage(*usage_from_chat_response(decoded))
        _log_codex_debug(
            "codex.http.response",
            provider="codex",
            provider_type=self.provider_type,
            purpose=purpose,
            model=self.config.model,
            url=url,
            path=path,
            response=decoded,
        )
        return decoded


def _url(base_url: str, path: str) -> str:
    return base_url.rstrip("/") + "/" + path.lstrip("/")


def _decode_lossy(raw: bytes) -> str:
    return raw.decode("utf-8", errors="replace")


class SdkCodexClient(TokenUsageAccounting):
    """Codex Python SDK-backed client.

    The SDK speaks the real Codex app-server v2 JSON-RPC protocol over stdio.
    LearnLoop still owns the learning-specific schemas and validates the final
    model output before anything can be persisted.
    """

    def __init__(self, config: CodexConfig, vault_root: Path):
        self.config = config
        self.provider_name = "codex"
        self.provider_type = "codex_sdk"
        self.model = config.model
        self.vault_root = vault_root.resolve()
        self.checkout_path = _resolve_checkout_path(self.vault_root, config.checkout_path)
        self.sdk_python_path = _resolve_sdk_python_path(self.checkout_path, config.sdk_python_path)
        self._turn_lock = threading.RLock()
        self._active_turn: Any = None
        self._active_codex: Any = None
        self._active_deadline_timer: threading.Timer | None = None
        self._active_force_close_timer: threading.Timer | None = None
        self._active_stop_scheduled = False
        self._interrupt_requested = threading.Event()
        self._deadline_expired = threading.Event()

    def interrupt(self) -> bool:
        """Interrupt this client's active SDK turn without killing the sidecar.

        The cancellation flag is set before looking up the turn handle so a
        request racing with turn startup still prevents that call from running.
        Clients are scoped to one ingest job, so the flag intentionally remains
        set for the rest of that job attempt.
        """

        self._interrupt_requested.set()
        with self._turn_lock:
            turn = self._active_turn
            codex = self._active_codex
        if turn is not None:
            self._schedule_turn_stop(turn, codex)
        return True

    def _expire_turn(self, turn: Any, codex: Any) -> None:
        """Deadline callback: request a clean interrupt, then force-close if needed."""

        with self._turn_lock:
            if self._active_turn is not turn:
                return
            self._deadline_expired.set()
        self._schedule_turn_stop(turn, codex)

    def _schedule_turn_stop(self, turn: Any, codex: Any) -> None:
        """Stop an SDK turn without blocking the palette or deadline thread."""

        with self._turn_lock:
            if self._active_turn is not turn or self._active_stop_scheduled:
                return
            self._active_stop_scheduled = True
            close = getattr(codex, "close", None)
            if callable(close):
                force_close = threading.Timer(0.25, close)
                force_close.daemon = True
                self._active_force_close_timer = force_close
                force_close.start()

        def request_interrupt() -> None:
            try:
                turn.interrupt()
            except Exception:  # noqa: BLE001 - force-close is the bounded fallback
                return

        threading.Thread(
            target=request_interrupt,
            name="learnloop-codex-interrupt",
            daemon=True,
        ).start()

    def run_authoring_proposal(self, context: AuthoringContext) -> AuthoringProposal:
        return self._run_validated(
            _authoring_prompt(context), AuthoringProposal, purpose="authoring"
        )

    def run_canonical_ingest(self, context: CanonicalIngestContext) -> AuthoringProposal:
        return self._run_validated(
            _canonical_ingest_prompt(context), AuthoringProposal, purpose="canonical_ingest"
        )

    def run_grading_proposal(self, context: GradingContext) -> GradingProposal:
        return self._run_validated(
            _grading_prompt(context), GradingProposal, purpose="grading"
        )

    def run_tutor_qa(self, context: TutorQAContext) -> TutorAnswer:
        return self._run_validated(_tutor_qa_prompt(context), TutorAnswer, purpose="tutor_qa")

    def run_teach_back_question(self, context: TeachBackQuestionContext) -> TeachBackQuestion:
        return self._run_validated(
            _teach_back_question_prompt(context), TeachBackQuestion, purpose="teach_back"
        )

    def run_teach_back_authoring(self, context: TeachBackAuthoringContext) -> TeachBackAuthoring:
        return self._run_validated(
            _teach_back_authoring_prompt(context),
            TeachBackAuthoring,
            purpose="teach_back_authoring",
        )

    def run_misconception_match(self, context: Any) -> MisconceptionMatch:
        return self._run_validated(
            _misconception_match_prompt(context), MisconceptionMatch, purpose="misconception_match"
        )

    def run_promotion_analysis(self, context: Any) -> PromotionAnalysis:
        return self._run_validated(
            _promotion_analysis_prompt(context), PromotionAnalysis, purpose="promotion_analysis"
        )

    def run_diagnostic_trials(self, context: Any) -> DiagnosticTrials:
        """Codex answers-under-belief for the sim discrimination gate (spec §6).

        Deliberately NOT on the ``CodexClient`` Protocol / ``HttpCodexClient`` —
        the gate discovers it via ``getattr(client, "run_diagnostic_trials",
        None)`` so providers without it degrade to the deterministic path.
        """

        return self._run_validated(
            _diagnostic_trials_prompt(context), DiagnosticTrials, purpose="diagnostic_trials"
        )

    def run_probe_instance_surfaces(self, context: ProbeInstanceContext) -> ProbeInstanceSurfaces:
        """LLM-backed Item Instance surfaces (probe redesign §9.2/§9.4).

        Deliberately NOT on the ``CodexClient`` Protocol / ``HttpCodexClient`` —
        instance generation discovers it via ``getattr(client,
        "run_probe_instance_surfaces", None)`` and falls back to the parametric
        surface templates when the provider lacks it or is unavailable.
        """

        return self._run_validated(
            _probe_instance_surfaces_prompt(context),
            ProbeInstanceSurfaces,
            purpose="probe_instance_surfaces",
        )

    def run_probe_dialogue_turn(self, context: ProbeDialogueTurnContext) -> ProbeDialogueTurn:
        """One adaptive dialogue microprobe turn (probe redesign §8.1).

        Same getattr-discovery contract as ``run_probe_instance_surfaces``:
        the dialogue service falls back to the parametric turn templates when
        the provider lacks it or is unavailable.
        """

        return self._run_validated(
            _probe_dialogue_turn_prompt(context), ProbeDialogueTurn, purpose="probe_dialogue_turn"
        )

    def run_probe_family_trials(self, context: ProbeFamilyTrialsContext) -> ProbeFamilyTrials:
        """LLM planted trials for the family admission gate (probe redesign §9.6).

        Same getattr-discovery contract as ``run_diagnostic_trials``: the gate
        runner degrades to reporting that no trial source is available rather
        than fabricating synthetic admission evidence.
        """

        return self._run_validated(
            _probe_family_trials_prompt(context), ProbeFamilyTrials, purpose="probe_family_trials"
        )

    def run_reader_preset_synthesis(self, context: ReaderPresetSynthesisContext) -> ReaderPresetSynthesis:
        """Fulfil one demand-paged reader preset request (spec §6).

        Deliberately NOT on the ``CodexClient`` Protocol / ``HttpCodexClient`` —
        the reader-request drain discovers it via ``getattr(client,
        "run_reader_preset_synthesis", None)`` and leaves requests queued when
        the provider lacks it. Output is candidate-only; the drain validates
        span citations and lands it as a PROPOSED source object for review.
        """

        return self._run_validated(
            _reader_preset_synthesis_prompt(context),
            ReaderPresetSynthesis,
            purpose="reader_preset_synthesis",
        )

    def run_reading_quick_check(self, context: ReadingQuickCheckContext) -> ReadingQuickCheck:
        """Author one section-boundary quick check (reader producer slice).

        Deliberately NOT on the ``CodexClient`` Protocol / ``HttpCodexClient`` —
        the reader quick-check service discovers it via ``getattr(client,
        "run_reading_quick_check", None)`` and degrades (no question authored)
        when the provider lacks it. Output is candidate-only; the service
        validates span citations against the section's spans before persisting.
        """

        return self._run_validated(
            _reading_quick_check_prompt(context), ReadingQuickCheck, purpose="reading_quick_check"
        )

    def run_rung_backfill(self, context: RungBackfillContext) -> RungBackfillClassification:
        """Classify legacy items into rung metadata (depth backfill).

        Deliberately NOT on the ``CodexClient`` Protocol — the backfill service
        discovers it via ``getattr(client, "run_rung_backfill", None)``. Output
        is candidate-only; deterministic validators admit or skip each entry.
        """

        return self._run_validated(
            _rung_backfill_prompt(context),
            RungBackfillClassification,
            purpose="rung_backfill",
        )

    def run_exercise_authoring(self, context: ExerciseAuthoringContext) -> ExerciseAuthoring:
        """Complete selected textbook exercises into full practice items.

        Deliberately NOT on the ``CodexClient`` Protocol / ``HttpCodexClient`` —
        ``services/exercise_authoring`` discovers it via ``getattr(client,
        "run_exercise_authoring", None)`` and refuses (typed error) when the
        provider lacks it. Output is candidate-only: the service re-anchors
        every statement verbatim against the selection and admits or repairs
        the rest through deterministic validators before writing the item.
        """

        return self._run_validated(
            _exercise_authoring_prompt(context), ExerciseAuthoring, purpose="exercise_authoring"
        )

    def run_depth_edge_instances(self, context: DepthEdgeInstanceContext) -> DepthEdgeInstanceBatch:
        """Author depth-edge instances from reviewed templates (spec v2 depth).

        Deliberately NOT on the ``CodexClient`` Protocol / ``HttpCodexClient`` —
        ``services/depth_edge_authoring`` discovers it via ``getattr(client,
        "run_depth_edge_instances", None)`` and refuses (typed error) when the
        provider lacks it. Output is candidate-only; every instance runs the
        deterministic admission gates before persisting as admitted/rejected.
        """

        return self._run_validated(
            _depth_edge_instance_prompt(context),
            DepthEdgeInstanceBatch,
            purpose="depth_edge_instances",
        )

    def run_source_unit_inventory(self, context: SourceUnitInventoryContext) -> SourceUnitInventory:
        """Role-aware unit inventory over one unit view (source-ingestion §7).

        Deliberately NOT on the ``CodexClient`` Protocol / ``HttpCodexClient`` —
        the inventory service discovers it via ``getattr(client,
        "run_source_unit_inventory", None)`` and degrades (no inventory produced)
        when the provider lacks it or is unavailable. The returned contract is
        candidate-only; the service reassigns deterministic ids and validates
        span citations before persisting.
        """

        return self._run_validated(
            _source_unit_inventory_prompt(context),
            SourceUnitInventory,
            purpose="source_unit_inventory",
        )

    def run_source_set_synthesis(self, context: SourceSetSynthesisContext) -> SourceSetSynthesis:
        """N-way bootstrap synthesis over role-specific inventories (§8.5).

        Deliberately NOT on the ``CodexClient`` Protocol / ``HttpCodexClient`` —
        the synthesis service discovers it via ``getattr(client,
        "run_source_set_synthesis", None)`` and degrades when the provider lacks
        it. Output is candidate-only, span-cited, and dependency-annotated; the
        service validates spans, runs the §8.7 gates, normalizes dependencies,
        and persists through the existing proposal pipeline.
        """

        return self._run_validated(
            _source_set_synthesis_prompt(context), SourceSetSynthesis, purpose="source_set_synthesis"
        )

    def run_concept_graph_structuring(self, context: ConceptGraphContext) -> ConceptGraphStructuring:
        """Duplicate-concept merges + big-picture concept relations (§8.5).

        Deliberately NOT on the ``CodexClient`` Protocol — the synthesis service
        discovers it via ``getattr(client, "run_concept_graph_structuring",
        None)`` and degrades to deterministic same-title merging (no authored
        relations) when the provider lacks it. Output is candidate-only: the
        service validates every id/edge and applies merges itself."""

        return self._run_validated(
            _concept_graph_structuring_prompt(context),
            ConceptGraphStructuring,
            purpose="concept_graph_structuring",
        )

    def run_concept_animation(self, context: ConceptAnimationContext) -> ManimAnimation:
        """Author one Manim CE explainer scene for a concept.

        Deliberately NOT on the ``CodexClient`` Protocol — the animation service
        discovers it via ``getattr(client, "run_concept_animation", None)`` and
        fails typed when the provider lacks it. Output is candidate-only: the
        service AST-validates and renders it in a constrained subprocess."""

        return self._run_validated(
            _concept_animation_prompt(context), ManimAnimation, purpose="concept_animation"
        )

    def run_append_reconciliation(self, context: AppendReconciliationContext) -> AppendReconciliation:
        """Reconcile new/changed material into an existing map (§10.1/§10.2).

        Deliberately NOT on the ``CodexClient`` Protocol — the append service
        discovers it via ``getattr(client, "run_append_reconciliation", None)`` and
        degrades when the provider lacks it. Output is candidate-only, span-cited,
        and dependency-annotated; the service verifies additivity from item type +
        payload, runs the §8.7 gates plus the append-vocabulary gate, and persists
        through the existing proposal pipeline."""

        return self._run_validated(
            _append_reconciliation_prompt(context),
            AppendReconciliation,
            purpose="append_reconciliation",
        )

    def _run_validated(
        self, prompt: str, model_type: type[BaseModel], *, purpose: str
    ) -> Any:
        """Run one structured turn and repair malformed/schema-invalid JSON once.

        The OpenAI-compatible provider already has this bounded repair pass.
        Keeping the same behavior here prevents a transient invalid escape or
        lone Unicode surrogate in model-authored Markdown from failing an
        otherwise retryable background job.
        """

        output_schema = _codex_output_schema(model_type)
        try:
            text = self._run_structured(prompt, output_schema, purpose=purpose)
        except CodexUnavailable as first_exc:
            # Some app-server/model combinations reject malformed structured
            # output before exposing a final_response to the SDK. In that case
            # the ordinary validation repair below never gets a chance to run.
            # Retry only the narrow family of JSON string/escape failures; a
            # genuinely unavailable provider must retain its original error.
            if not _is_structured_json_transport_error(first_exc):
                raise
            _log_codex_debug(
                "codex.structured_output_regenerate",
                provider="codex",
                provider_type=self.provider_type,
                purpose=purpose,
                model=self.config.model,
                error=str(first_exc),
            )
            text = self._run_structured(
                _structured_output_regeneration_prompt(prompt),
                output_schema,
                purpose=f"{purpose}_json_regenerate",
            )
        try:
            return model_type.model_validate_json(text)
        except (ValidationError, ValueError, json.JSONDecodeError) as first_exc:
            reason = describe_wire_validation_error(model_type, first_exc)
            _log_codex_debug(
                "codex.structured_output_repair",
                provider="codex",
                provider_type=self.provider_type,
                purpose=purpose,
                model=self.config.model,
                error=str(first_exc),
                reason=reason,
            )
            repaired = self._run_structured(
                _structured_output_repair_prompt(text, model_type, reason=reason),
                output_schema,
                purpose=f"{purpose}_json_repair",
            )
            try:
                return model_type.model_validate_json(repaired)
            except (ValidationError, ValueError, json.JSONDecodeError) as second_exc:
                # Name the model and the offending field. A forbidden extra is
                # a contract divergence someone has to resolve in
                # ``codex/schemas.py``; a raw pydantic dump buried in a generic
                # "invalid JSON" is what let F2 hide for 43 attempts.
                raise CodexUnavailable(
                    f"Codex returned invalid {model_type.__name__} JSON after one repair "
                    f"attempt: {describe_wire_validation_error(model_type, second_exc)}"
                ) from second_exc

    def _run_structured(self, prompt: str, output_schema: dict[str, Any], *, purpose: str) -> str:
        if self._interrupt_requested.is_set():
            raise CodexInterrupted("Codex turn interrupted by the learner.")
        _ensure_sdk_importable(self.sdk_python_path)
        try:
            from openai_codex import Codex
            from openai_codex import CodexConfig as SdkAppConfig
            from openai_codex.types import Personality, ReasoningEffort, ReasoningSummary
        except ImportError as exc:
            raise CodexUnavailable(
                f"Codex Python SDK is not importable from {self.sdk_python_path}."
            ) from exc

        try:
            effort = _sdk_reasoning_effort(ReasoningEffort, self.config.reasoning_effort)
            summary = _sdk_reasoning_summary(ReasoningSummary, self.config.reasoning_summary)
            launch_args = _sdk_launch_args(self.config.sdk_launch_command)
            app_config = SdkAppConfig(
                codex_bin=_resolved_sdk_codex_bin(self.config.sdk_codex_bin),
                launch_args_override=launch_args,
                cwd=str(self.vault_root),
                client_name="learnloop",
                client_title="LearnLoop",
            )
            _log_codex_debug(
                "codex.prompt",
                provider="codex",
                provider_type=self.provider_type,
                purpose=purpose,
                model=self.config.model,
                cwd=str(self.vault_root),
                service_name=f"learnloop:{purpose}",
                reasoning_effort=self.config.reasoning_effort,
                reasoning_summary=self.config.reasoning_summary,
                prompt=prompt,
                prompt_length=len(prompt),
                output_schema=output_schema,
            )
            with Codex(config=app_config) as codex:
                thread = codex.thread_start(
                    cwd=str(self.vault_root),
                    model=self.config.model or None,
                    service_name=f"learnloop:{purpose}",
                )
                turn = thread.turn(
                    prompt,
                    cwd=str(self.vault_root),
                    model=self.config.model or None,
                    effort=effort,
                    output_schema=output_schema,
                    personality=Personality.pragmatic,
                    summary=summary,
                )
                with self._turn_lock:
                    self._active_turn = turn
                    self._active_codex = codex
                    self._active_stop_scheduled = False
                    self._deadline_expired.clear()
                    deadline_timer = threading.Timer(
                        max(0.001, float(self.config.timeout_seconds)),
                        self._expire_turn,
                        args=(turn, codex),
                    )
                    deadline_timer.daemon = True
                    self._active_deadline_timer = deadline_timer
                    deadline_timer.start()
                try:
                    if self._interrupt_requested.is_set():
                        self._schedule_turn_stop(turn, codex)
                    result = turn.run()
                finally:
                    with self._turn_lock:
                        if self._active_turn is turn:
                            self._active_turn = None
                            self._active_codex = None
                            if self._active_deadline_timer is not None:
                                self._active_deadline_timer.cancel()
                            if self._active_force_close_timer is not None:
                                self._active_force_close_timer.cancel()
                            self._active_deadline_timer = None
                            self._active_force_close_timer = None
                            self._active_stop_scheduled = False
        except CodexInterrupted:
            raise
        except CodexTurnTimeout:
            raise
        except Exception as exc:
            if self._deadline_expired.is_set():
                raise CodexTurnTimeout(
                    f"Codex SDK turn exceeded its {self.config.timeout_seconds:g}-second deadline."
                ) from exc
            if self._interrupt_requested.is_set():
                raise CodexInterrupted("Codex turn interrupted by the learner.") from exc
            _log_codex_debug(
                "codex.error",
                provider="codex",
                provider_type=self.provider_type,
                purpose=purpose,
                model=self.config.model,
                cwd=str(self.vault_root),
                error=str(exc),
            )
            raise CodexUnavailable(str(exc)) from exc

        # A7 (spec_diagnostic_augmentation_v1.md §2): meter before the
        # deadline/interrupt/empty-response checks below. A turn the learner
        # interrupted or that timed out still burned tokens, and a cost meter
        # that only counts clean completions understates every ratio built on it.
        self.record_token_usage(*usage_from_codex_turn(result))

        if self._deadline_expired.is_set():
            raise CodexTurnTimeout(
                f"Codex SDK turn exceeded its {self.config.timeout_seconds:g}-second deadline."
            )
        if self._interrupt_requested.is_set():
            raise CodexInterrupted("Codex turn interrupted by the learner.")

        final_response = result.final_response
        _log_codex_debug(
            "codex.response",
            provider="codex",
            provider_type=self.provider_type,
            purpose=purpose,
            model=self.config.model,
            cwd=str(self.vault_root),
            response=final_response,
            response_length=len(final_response) if final_response is not None else None,
        )
        if final_response is None:
            raise CodexUnavailable("Codex SDK turn completed without a final response.")
        return final_response.strip()


# Difficulty estimation guidance threaded into both authoring prompts so the 2PL
# difficulty `b` (spec_irt_difficulty.md §4.3, §6.3) is populated on ship.
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

# Every source-linked generated Practice Item is post-validated against the
# ProposalItemAudit contract (services/proposals.py); a trace-less
# not_applicable_with_trace audit is rejected as `missing_generated_audit_trace`.
_AUDIT_GUIDANCE = (
    "Every generated Practice Item must carry an `audit`. Use status `passed` or "
    "`failed` when a deterministic check (numeric check, symbolic solver, "
    "step-by-step trace) ran. For conceptual/constructed-response items with no "
    "deterministic check, use status `not_applicable_with_trace` and you MUST fill "
    "`trace` with a short manual verification walkthrough of the expected answer; "
    "a null or empty trace fails validation."
)


def _authoring_prompt(context: AuthoringContext) -> str:
    return _json_prompt(
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


def _canonical_ingest_prompt(context: CanonicalIngestContext) -> str:
    return _json_prompt(
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


def _grading_prompt(context: GradingContext) -> str:
    return _json_prompt(
        "learnloop grading proposal",
        GRADING_PROMPT_VERSION,
        {
            "task": (
                "Grade the learner answer against the prompt, expected answer, and "
                "rubric. Return a LearnLoop GradingProposal as schema-valid JSON only. "
                "Write `diagnosis_md` FIRST, before filling any structured field. "
                "Next construct the smallest `repaired_trace` that preserves the "
                "learner's valid prefix. Only AFTER that checkable repair, fill the "
                "structured causal fields as explanations of the edit. Diagnose the "
                "displayed work in ordinary prose without trying to fit it to the "
                "supplied facet vocabulary; structure only claims that the prose and "
                "repair actually establish. Treat `verifier_observations` as typed "
                "instruments: verified/contradicted may localize a failure, while "
                "parse_failed/unsupported/assumption_missing confer NO support and "
                "must not attract the anchor merely because another part parsed. "
                "`diagnostic_history` contains raw prior traces only. Use it to test "
                "recurrence, but re-diagnose the current trace independently; a prior "
                "cause may have changed. A first_divergence span quote must "
                "be copied VERBATIM from the learner answer — character-for-character, "
                "including whitespace and notation. Leave char_start/char_end null: "
                "offsets are recomputed server-side from the quote, so never count "
                "characters yourself. Locate the EARLIEST incorrect or unsupported "
                "claim, not merely the learner's later admission of uncertainty; do "
                "not preserve an earlier false count, equation, or premise in the "
                "repair prefix. Every named facet must also "
                "appear in diagnosis_md. A missing_required_step divergence must name "
                "a checkpoint_id from the item's trace contract. "
                "For each error_attribution's `error_type`, pick the id from "
                "`error_taxonomy.canonical_error_types` whose `use_when` fits the "
                "observed failure and whose `avoid_when` does not — use ONLY those "
                "ids for ordinary errors. Use existing rubric fatal "
                "error ids or vault-specific taxonomy ids only when they apply more "
                "precisely. Use the retrieval-failure taxonomy id only when the trace "
                "locally supports a failure to access previously learned, "
                "task-relevant knowledge. An expression such as 'I don't know how' "
                "or 'I'm not sure,' or an inability to continue, does not by itself "
                "establish failed retrieval. If the evidence instead identifies a "
                "misunderstanding, unsuitable selection or organization, incorrect "
                "execution or application, transfer or context mismatch, "
                "representation difficulty, or a local omission or slip, classify "
                "that more specific observed mechanism. For each failed rubric "
                "line or facet, add an "
                "error_attribution unless another attribution already covers the same "
                "failure. Set the orthogonal `resolution_status`, `cause_scope`, and "
                "typed `target_ref` axes independently. A facet may be named only "
                "when the failed step exercises that facet's claim; prefer a failed "
                "criterion, item step, answer span, or a reasoned abstention over the "
                "nearest listed facet. `target_evidence_families` may be empty. "
                "Passing evidence for a facet is evidence FOR it, never a repair "
                "target. Set facet_contrast only when the trace explicitly demonstrates "
                "a contract swap, with a trace-citing justification. "
                "When resolution_status is abstained, give a concrete abstention_reason. "
                "When unresolved, draft `candidate_causes` as a SET in ONE pass, "
                "not one at a time: generate the roughly 3-5 genuinely distinct "
                "explanations of this trace TOGETHER, and give each a "
                "`prior_weight` — your verbalized relative plausibility across "
                "that set, any non-negative scale, higher means more likely. "
                "Weights are a prior you are stating out loud, not a "
                "measurement; the system normalizes them and never reads them "
                "as calibrated probabilities. Write each `statement` as plain "
                "prose about what the learner did or believed. There is no "
                "vocabulary to fit, no category to span, and no label you must "
                "produce: a candidate is never wrong for its wording. For each "
                "candidate give `discriminating_predictions` — free-text "
                "falsifiable expectations of the form \"if this cause is true, "
                "we'd observe X on Y\". Those predictions are what make two "
                "candidates DIFFERENT: if two candidates predict the same "
                "observations, they are the same candidate said twice, so MERGE "
                "them. Returning fewer than three candidates is the correct "
                "answer when the trace genuinely underdetermines less; padding "
                "the set with restatements is worse than a short list. "
                "`mechanism` is optional — fill it only when an obvious "
                "mechanism label applies, and leave it null rather than "
                "reaching for the nearest one. The system adds the open-set "
                "H_OTHER arm itself. `localization_confidence` and "
                "`causal_confidence` are separate model-reported proposals, not outcome "
                "confidence or posteriors. `operation` is nullable free snake_case. "
                "For each repair_suggestion, target only failed criterion ids and/or "
                "genuinely implicated evidence facets; both target lists may be empty. "
                "When a safe local repair is supported, structure it with a snake_case "
                "`operator`, typed `target_refs`, `preserve_refs` for demonstrated "
                "work, `expected_minutes`, and the fraction-like "
                "`answer_reveal_budget`. "
                "Choose the repair SHAPE from what went wrong. When the "
                "mechanism is a durable wrong belief — a conceptual or schema "
                "error, a representation/notation confusion, a wrong selection "
                "or plan, a missed condition or assumption, a transfer or "
                "context mismatch — DEFAULT to an ELICITING repair rather than "
                "a spliced solution: use an `operator` beginning `elicit_`, "
                "name the divergence anchor in `target_refs`, ask exactly ONE "
                "targeted `eliciting_question` the learner can answer unaided, "
                "state in `expected_response_contract` what a correct unaided "
                "response would demonstrate, and keep `answer_reveal_budget` "
                "near zero. Showing a believer the corrected work teaches them "
                "to recognize it, not to stop believing what they believe; the "
                "question is what makes their belief speak again. When the "
                "mechanism is instead a slip, a local execution error, or a "
                "retrieval lapse, keep the spliced `repaired_trace` — there is "
                "no belief to elicit and the edit is the whole lesson. This is "
                "a default, not a rule: override it when the trace warrants, "
                "and nothing rejects your choice. "
                "Emit `repaired_trace` only when you can keep "
                "the learner's displayed work verbatim through a supported insertion "
                "point: copy `learner_work_prefix`, state one `minimal_edit`, regenerate "
                "only downstream work in the learner's notation, and enumerate changed "
                "latent claims and authored checkpoint ids. Do not fabricate trace "
                "structure when the item has no reliable decomposition. Request "
                "`symbolic_equality` verification only when the full repaired answer "
                "and authored expected answer are parseable mathematical expressions; "
                "request `exact_match` only when exact text equality is the authored "
                "contract. Never propose a verification verdict. "
                "When an error_attribution sets `is_misconception=true`, "
                "`misconception_statement` is REQUIRED: state the learner's belief "
                "in learner-model terms (what the learner thinks is true), NOT a "
                "description of the wrong answer — e.g. \"believes Q maps standard "
                "vectors to eigenbasis coefficients (reverses Q / Q^T)\", not "
                "\"used Q instead of Q^T\". Also fill "
                "`misconception_consistent_answer` when you can: the answer a holder "
                "of that belief would give on this specific item. "
                "Postdictive claims are deterministic implications only: if the "
                "cause were true, the named criterion must fail or lose full credit. "
                "Use the supplied `error_taxonomy.selection_policy` and "
                "`error_taxonomy.targeting_policy` exactly. Set `rubric_score` to "
                "the rounded sum of awarded criterion points after any fatal-error "
                "cap. The rubric criterion total is the maximum; never normalize or "
                "clamp the score to four. "
                "LAST, fill `exercised_facets`: facets from "
                "`context.facet_registry` that the learner's written work "
                "actually EXERCISES, whether or not this item declares them. "
                "Quote the part of the trace that shows it in `evidence` — an "
                "observation with no citation is not one. This channel is "
                "positive only: it says a facet was used, never that it was "
                "used wrongly, and a facet that appears only in the item's "
                "prompt rather than in the learner's own work was not "
                "exercised. Report at most a handful, and leave it empty when "
                "the work shows nothing beyond the criteria you already "
                "graded; an empty list is the common and correct answer on a "
                "short response. "
                "`clarification_request`: leave it null unless you are "
                "genuinely unsure what the LEARNER did and one question would "
                "settle it - ambiguous notation, a skipped step that is either "
                "fluency or a gap, a correct answer possibly reached by invalid "
                "reasoning, or which of two methods they believed they were "
                "using. Ask at most one, only against a criterion you marked "
                "`learner_confidence='hedged'` or an attribution you marked "
                "`abstained`. NEVER ask about something you could settle "
                "yourself from the item, the expected answer, or the trace - "
                "that is the system's debt, not the learner's. If "
                "`context.clarification_exchange` is present, the learner has "
                "already answered a question about this attempt: grade with "
                "their answer in hand, do not ask again, and if it still does "
                "not settle the matter, abstain rather than guess. "
                "`discrimination_profile_match`: when "
                "`context.discrimination_profiles` is non-empty, the item's "
                "author has written down, per candidate hypothesis, what a "
                "holder of it visibly produces. Treat that list as a PRIOR - a "
                "set of candidates to check the trace against - never as a menu "
                "you must choose from. Set outcome='matched' with the profile_id "
                "and a quote from the learner's work ONLY when the work really "
                "shows that hypothesis; otherwise set "
                "outcome='no_profile_applies', which is a full answer and not a "
                "failure to answer. Picking the closest profile when none fits "
                "is worse than rejecting them all: it replaces what the learner "
                "did with what the author guessed. Leave the field null when "
                "the item lists no profiles. "
                "`error_hunt_report`: when `context.error_hunt_solution` is "
                "present the learner was shown that worked solution and asked "
                "to find and REPAIR whatever is wrong with it. Report each "
                "error they claimed, with where they say it is, what they say "
                "is wrong, and the corrected work they produced - `repair_md` "
                "empty when they only pointed at it without fixing it. You are "
                "NOT told how many errors were planted or where; do not guess "
                "at `matches_planted_error_id` unless the item names the plant "
                "to you. The solution may contain no errors at all, and "
                "reporting that the learner found one in correct work is the "
                "informative outcome, not a mistake to smooth over."
            ),
            "context": asdict(context),
        },
    )


# Two extraction fields, and one boundary that makes them safe.
#
# The learner's own question is a production: it was written BEFORE anything the
# tutor is about to say, so an expectation it asserts is uncontaminated evidence
# about the learner's model. Reading that expectation out of the question text
# is transcription, and it stays admissible even when the answer that follows
# reveals the solution.
#
# What is NOT safe is the tutor inventing beliefs. Once an answer has been given
# — and every answer on this surface reveals something — the model's picture of
# "what the learner must think" is a picture of what the model just explained.
# So `new_candidate_cause` is admissible only when it is grounded in the
# learner's own words, and never in the tutor's.
_TUTOR_QA_LEARNER_EXTRACTION = (
    "Two fields report on the LEARNER'S QUESTION rather than on your answer. "
    "`embedded_prediction`: if the learner's question itself asserts a "
    "falsifiable expectation — something they evidently expect to be true, "
    "e.g. \"learner expects replacing (x+y)e2 with ((x+y)/2)e2 to change the "
    "sum\" — state that expectation in one sentence. Take it from the question "
    "TEXT; do not infer what they probably think, and set it to null when the "
    "question asserts nothing (that is the common case). "
    "`new_candidate_cause`: set it ONLY when this exchange surfaced a possible "
    "cause of the learner's difficulty that their written attempt could not "
    "have shown — something they said or asked that reveals it. Write "
    "`statement` as plain prose in learner-model terms; there is no vocabulary "
    "to fit. Ground it in the learner's words, NEVER in what you just "
    "explained: after you have answered, anything you would say about their "
    "beliefs describes your own explanation, not them. Null is the correct and "
    "usual answer."
)

# Per-context tutor behavior. Practice guardrails are the load-bearing part:
# mid-attempt the tutor must never hand over or verify the answer, or hint
# dampening on the eventual attempt becomes meaningless.
_TUTOR_QA_SHARED = (
    "You are a LearnLoop tutor answering one learner question. Return a "
    "TutorAnswer as schema-valid JSON only. Classify the question as exactly one "
    "question_type: `clarification` (what the prompt/wording means), "
    "`prerequisite` (background knowledge needed), `mechanism` (why/how "
    "something works), `strategy` (how to approach the task), `verification` "
    "(is my answer/approach right?), or `other`. Also classify question_channel: "
    "`epistemic` when the question signals missing or uncertain knowledge about "
    "the content, `interaction_preference` when the learner is instead asking "
    "for a different explanation style, pace, scaffold level, more or less "
    "detail, or a direct answer (a request about HOW to be tutored, not WHAT is "
    "true). Fill `facets` with the subset "
    "of context.candidate_facets the question is genuinely about (empty when "
    "none apply); never invent facet ids outside that list. Use "
    "context.thread as prior conversation turns and stay consistent with them. "
    "Write answer_md as concise Markdown (LaTeX math allowed). "
    "When context.source_spans is non-empty and a span grounds a claim you make, "
    "add it to `citations` as {extraction_id, span_id, label} using ONLY the "
    "extraction_id/span_id pairs present in context.source_spans — never invent a "
    "span, and cite only spans your answer actually relies on. Leave citations "
    "empty when no provided span is relevant."
    " " + _TUTOR_QA_LEARNER_EXTRACTION
)

_TUTOR_QA_CONTEXT_TASKS = {
    "practice": (
        "Context: the learner is MID-ATTEMPT on the given practice item. Act as "
        "a Socratic tutor. You MUST NOT state the answer, complete the "
        "derivation, reveal the expected answer, or confirm or deny whether the "
        "learner's current approach or partial answer is correct. If the "
        "question asks for verification, deflect with a guiding question that "
        "helps the learner check it themselves. Clarify wording, surface "
        "prerequisites, and nudge strategy without giving away the solution."
    ),
    "feedback": (
        "Context: the learner's attempt has already been graded. Full "
        "explanation is allowed and encouraged: ground your answer in the "
        "practice item, its rubric, the learner's answer, and the grading "
        "feedback provided, explaining what went wrong or right and why."
    ),
    "library": (
        "Context: the learner is reading a note. Answer explanatorily, "
        "grounded in the note body and the related learning objects; connect "
        "the answer back to the note's content."
    ),
    "reader": (
        "Context: the learner is reading a source span in the reader (U-033). "
        "There is NO attempt to protect here, so you are NOT Socratic-by-default: "
        "you MAY state facts, complete a derivation, give a worked example, and "
        "confirm or deny an interpretation. Ground every claim in the provided "
        "source spans and cite them. Support comprehension, inquiry, "
        "self-explanation, and goal connection. You are NOT given the learner's "
        "ability estimate and MUST NOT tune the answer to a supposed deficit."
    ),
}

# U-033 (§7.6): per-ask answer-mode overlays for the `reader` profile. Appended to
# the reader task so the learner's chosen mode shapes the answer's shape.
_TUTOR_QA_READER_MODE_TASKS = {
    "answer_directly": (
        " Answer mode: ANSWER DIRECTLY -- give the complete answer up front, "
        "then a brief why."
    ),
    "help_me_reason": (
        " Answer mode: HELP ME REASON -- do not hand over the final answer first; "
        "walk the learner through the reasoning steps so they reach it."
    ),
    "ask_me_first": (
        " Answer mode: ASK ME FIRST -- open with one focused question that checks "
        "the learner's current understanding before you explain."
    ),
}


# Naive-student persona for teach-back. The load-bearing guardrails: the
# student must never correct, confirm, deny, or reveal — otherwise the graded
# transcript stops being independent learner evidence.
_TEACH_BACK_TASK = (
    "You are a curious NAIVE STUDENT being taught by the learner. The learner "
    "just explained the concept to you (see context.transcript, oldest first). "
    "Return a TeachBackQuestion as schema-valid JSON only. Ask exactly ONE "
    "short follow-up question, in character, that probes the rubric criterion "
    "described by context.criterion_description and, when present, its target "
    "facets (context.facet_targets). An item-local criterion can honestly have "
    "no facet target; in that case use the criterion description and practice "
    "item prompt. You do not know the answer: you may feign "
    "confusion, ask for a simpler explanation, an example, an edge case, or a "
    "what-if — but you MUST NOT correct the learner, confirm or deny whether "
    "anything they said is right, reveal any part of the answer, or introduce "
    "facts they have not taught you. Condition on the transcript: do not ask "
    "about something the learner's explanation or earlier answers already "
    "clearly covered; probe the part of the criterion that is still untaught "
    "or fuzzy. If context.criterion_tier is \"transfer\", push toward edge "
    "cases, unusual applications, or transfer scenarios for the criterion. "
    "Write question_md as one concise Markdown question (LaTeX math allowed)."
)


_TEACH_BACK_AUTHORING_TASK = (
    "Transform the ONE completed source Practice Item into a focused teach-back "
    "conversation contract. Return TeachBackAuthoring as schema-valid JSON only. "
    "The opening prompt must name the source problem or task specifically and ask "
    "the learner to explain the reasoning or method; NEVER replace it with the "
    "broad Learning Object title, and do not reveal the expected answer, solution "
    "steps, or hints in that opening prompt. Author 1..context.max_core_criteria core criteria "
    "that together cover EVERY id in context.source_criteria exactly as a teachable "
    "explanation. List the covered ids in source_criterion_ids. You may combine "
    "adjacent source criteria, but may not omit one or invent an id. For every "
    "criterion, link only facet ids from context.allowed_facets that it genuinely "
    "measures. Use item_local or no_canonical_facet with an empty facet_ids list "
    "when the source procedure is more specific than the facet vocabulary; do not "
    "copy a uniform whole-item facet smear. Author exactly one transfer criterion. "
    "If context.quest_sentence is relevant, create a modest, concrete scenario "
    "connected to that sentence which still exercises the SAME reasoning as the "
    "source item, set quest_connection=connected, and place the scenario in "
    "transfer_scenario. The quest may shape ONLY this transfer criterion, never "
    "the core criteria or their facet mappings. If the quest is absent, set "
    "quest_connection=no_quest and use a nearby edge case. If it is unrelated, "
    "set quest_connection=not_relevant and use a nearby edge case rather than "
    "forcing a superficial analogy. The transfer criterion must name what reasoning "
    "the learner should transfer and include the relevant source_criterion_ids. "
    "A transfer criterion that names facets must use measurement_status=supporting; "
    "otherwise use item_local or no_canonical_facet with no facet ids. "
    "Write expected_answer_md as an explanation standard, not merely the final "
    "answer. Preserve context.source_trace_contract when it is reliable; otherwise "
    "compile a small checkpoint trace from the expected reasoning, or return null "
    "when no reliable decomposition exists."
)


def _teach_back_authoring_prompt(context: TeachBackAuthoringContext) -> str:
    return _json_prompt(
        "learnloop source-item teach-back authoring",
        TEACH_BACK_AUTHORING_PROMPT_VERSION,
        {
            "task": _TEACH_BACK_AUTHORING_TASK,
            "context": asdict(context),
        },
    )


def _teach_back_question_prompt(context: TeachBackQuestionContext) -> str:
    return _json_prompt(
        "learnloop teach-back question",
        TEACH_BACK_PROMPT_VERSION,
        {
            "task": _TEACH_BACK_TASK,
            "context": asdict(context),
        },
    )


# §12.1: appended when a diagnostic episode transitioned to tutoring. The
# typed decision was persisted BEFORE prose generation, so the tutor executes
# it rather than re-diagnosing; measurement has ended, so the mid-attempt
# no-reveal guardrail yields to the decision's answer_reveal_budget.
_TUTOR_QA_DIAGNOSTIC_DECISION_TASK = (
    "A diagnostic episode on this Learning Object has ENDED and transitioned to "
    "tutoring. context.diagnostic_decision is the persisted typed decision: "
    "ground your tutoring in it. Open with the named `tutor_move` (e.g. "
    "contrast_cases = contrast the target with the confusable; counterexample = "
    "present a case where the diagnosed belief fails; explanation = teach the "
    "mechanism; transfer_question = pose a shifted-surface question; "
    "state_subgoal = name the next subgoal; localize_error = walk to the first "
    "divergent step; elicit_reasoning = ask for their reasoning first). Target "
    "the `target_facets` and the `diagnosed_gap`; match depth to "
    "`scaffold_level` (0 = minimal support, 1 = heavy scaffolding). "
    "`answer_reveal_budget` overrides the mid-attempt guardrail: 0 means never "
    "reveal, 1 means partial worked steps are allowed, 2 means full explanation "
    "including the answer is allowed — measurement is over, so teaching to the "
    "diagnosed gap is the goal."
)


# Proactive handoff (§12.1 "stop diagnosing & teach me" / block-end tutoring
# route): the learner hasn't spoken yet, so the ordinary "answering one
# question" framing doesn't apply. Reuses run_tutor_qa/TutorAnswer wholesale —
# an empty question_md paired with a diagnostic_decision selects this framing
# instead of a new provider method.
_TUTOR_QA_OPENING_SHARED = (
    "You are a LearnLoop tutor OPENING a tutoring conversation. There is no "
    "learner question yet — do not ask what they would like to know or wait "
    "for one; proactively execute the move below. Return a TutorAnswer as "
    "schema-valid JSON only. Set question_type to `strategy` and "
    "question_channel to `epistemic`. Fill `facets` with the subset of "
    "context.candidate_facets your opening targets (empty when none apply); "
    "never invent facet ids outside that list. Write answer_md as concise "
    "Markdown (LaTeX math allowed). There is no learner question here, so "
    "`embedded_prediction` and `new_candidate_cause` MUST both be null: with "
    "nothing the learner has said, any cause you named would be your own."
)


def _tutor_qa_prompt(context: TutorQAContext) -> str:
    opening = not context.question_md.strip() and context.diagnostic_decision is not None
    task = _TUTOR_QA_CONTEXT_TASKS.get(context.context, _TUTOR_QA_CONTEXT_TASKS["library"])
    if context.context == "reader" and context.answer_mode:
        task = task + _TUTOR_QA_READER_MODE_TASKS.get(context.answer_mode, "")
    if context.diagnostic_decision is not None:
        task = task + " " + _TUTOR_QA_DIAGNOSTIC_DECISION_TASK
    shared = _TUTOR_QA_OPENING_SHARED if opening else _TUTOR_QA_SHARED
    return _json_prompt(
        "learnloop tutor qa",
        TUTOR_QA_PROMPT_VERSION,
        {
            "task": shared + " " + task,
            "context": asdict(context),
        },
    )


def _misconception_match_prompt(context: Any) -> str:
    """Registry belief-match prompt (spec §2.2.2).

    Asks whether a freshly graded belief is the same as any existing registry row
    for the learning object; the model returns ``same:<id>`` or ``new`` and errs
    toward ``new`` when unsure (spec §9, avoid over-merging distinct beliefs).
    """

    return _json_prompt(
        "learnloop misconception match",
        MISCONCEPTION_MATCH_PROMPT_VERSION,
        {
            "task": (
                "Decide whether the learner belief in `statement` is the SAME "
                "underlying misconception as one of the `candidates` (return "
                "decision 'same' with that candidate's misconception_id) or a "
                "genuinely DISTINCT belief (return decision 'new'). Compare the "
                "beliefs themselves, never their error-type labels. When unsure, "
                "prefer 'new'."
            ),
            "statement": getattr(context, "statement", ""),
            "learning_object_id": getattr(context, "learning_object_id", ""),
            "candidates": getattr(context, "candidates", []),
        },
    )


def _promotion_analysis_prompt(context: Any) -> str:
    """Step-0 promotion-analysis prompt (spec_tutor_promotion.md §3 Step 0)."""

    context_payload = context if isinstance(context, dict) else asdict(context)
    return _json_prompt(
        "learnloop promotion analysis",
        PROMOTION_ANALYSIS_PROMPT_VERSION,
        {
            "task": PROMOTION_ANALYSIS_PROMPT,
            "context": context_payload,
        },
    )


def _diagnostic_trials_prompt(context: Any) -> str:
    """Answers-under-belief prompt for the sim discrimination gate (spec §6).

    Asks codex to ROLE-PLAY ``n_trials`` planted students (who genuinely hold the
    stated belief) and ``n_trials`` clean students on one item, then judge whether
    the misconception-keyed fatal error would fire on each. One call, all trials.
    """

    def _get(key: str, default: Any = None) -> Any:
        if isinstance(context, Mapping):
            return context.get(key, default)
        return getattr(context, key, default)

    n_trials = int(_get("n_trials", 0) or 0)
    max_words = int(_get("max_answer_words", 40) or 40)
    return _json_prompt(
        "learnloop diagnostic trials",
        DIAGNOSTIC_TRIALS_PROMPT_VERSION,
        {
            "task": (
                f"Role-play {n_trials} DISTINCT `planted` students who GENUINELY "
                "HOLD the belief in `misconception_statement` and answer "
                "`item_prompt` accordingly (natural, varied phrasing — NEVER copy "
                "`misconception_consistent_answer` verbatim), and "
                f"{n_trials} DISTINCT `clean` students who are competent (correct "
                "substance; wording may vary or carry minor slips). For EACH "
                "answer set `fires` = true iff a grader would attribute the "
                "misconception-keyed fatal error described in `keyed_fatal_errors` "
                "— i.e. the answer is substantively consistent with the belief AND "
                f"categorically wrong. Keep every `answer` <= {max_words} words."
            ),
            "n_trials": n_trials,
            "max_answer_words": max_words,
            "item_prompt": _get("item_prompt", ""),
            "expected_answer": _get("expected_answer", ""),
            "misconception_statement": _get("misconception_statement", ""),
            "misconception_consistent_answer": _get("misconception_consistent_answer", ""),
            "keyed_fatal_errors": _get("keyed_fatal_errors", []),
        },
    )


def _probe_instance_surfaces_prompt(context: ProbeInstanceContext) -> str:
    """LLM instance-surface prompt (probe redesign §9.2/§9.4)."""

    return _json_prompt(
        "learnloop probe instance surfaces",
        PROBE_INSTANCE_PROMPT_VERSION,
        {
            "task": PROBE_INSTANCE_PROMPT,
            "context": asdict(context),
        },
    )


def _probe_dialogue_turn_prompt(context: ProbeDialogueTurnContext) -> str:
    """Adaptive dialogue-turn prompt (probe redesign §8.1)."""

    return _json_prompt(
        "learnloop probe dialogue turn",
        PROBE_DIALOGUE_TURN_PROMPT_VERSION,
        {
            "task": PROBE_DIALOGUE_TURN_PROMPT,
            "context": asdict(context),
        },
    )


def _probe_family_trials_prompt(context: ProbeFamilyTrialsContext) -> str:
    """Planted-trial prompt for the family admission gate (probe redesign §9.6)."""

    return _json_prompt(
        "learnloop probe family trials",
        PROBE_FAMILY_TRIALS_PROMPT_VERSION,
        {
            "task": PROBE_FAMILY_TRIALS_PROMPT,
            "context": asdict(context),
        },
    )


def _reader_preset_synthesis_prompt(context: ReaderPresetSynthesisContext) -> str:
    """Demand-paged reader preset synthesis prompt (spec §6)."""

    return _json_prompt(
        "learnloop reader preset synthesis",
        READER_PRESET_SYNTHESIS_PROMPT_VERSION,
        {
            "task": READER_PRESET_SYNTHESIS_PROMPT,
            "context": asdict(context),
        },
    )


def _reading_quick_check_prompt(context: ReadingQuickCheckContext) -> str:
    """Section-boundary quick-check authoring prompt (reader producer)."""

    return _json_prompt(
        "learnloop reading quick check",
        READING_QUICK_CHECK_PROMPT_VERSION,
        {
            "task": READING_QUICK_CHECK_PROMPT,
            "context": asdict(context),
        },
    )


def _rung_backfill_prompt(context: RungBackfillContext) -> str:
    """Legacy-item rung classification prompt (depth backfill)."""

    return _json_prompt(
        "learnloop rung backfill",
        RUNG_BACKFILL_PROMPT_VERSION,
        {
            "task": RUNG_BACKFILL_PROMPT,
            "context": asdict(context),
        },
    )


def _exercise_authoring_prompt(context: ExerciseAuthoringContext) -> str:
    """Reader exercise-import authoring prompt (exact-exercise slice)."""

    return _json_prompt(
        "learnloop exercise import",
        EXERCISE_AUTHORING_PROMPT_VERSION,
        {
            "task": EXERCISE_AUTHORING_PROMPT,
            "context": asdict(context),
        },
    )


def _depth_edge_instance_prompt(context: DepthEdgeInstanceContext) -> str:
    """Depth-edge-instance authoring prompt (spec v2 depth-milestone graph)."""

    return _json_prompt(
        "learnloop depth edge instances",
        DEPTH_EDGE_INSTANCE_PROMPT_VERSION,
        {
            "task": DEPTH_EDGE_INSTANCE_PROMPT,
            "context": asdict(context),
        },
    )


def _source_unit_inventory_prompt(context: SourceUnitInventoryContext) -> str:
    """Role-aware unit inventory prompt (source-ingestion §7)."""

    return _json_prompt(
        "learnloop source unit inventory",
        SOURCE_UNIT_INVENTORY_PROMPT_VERSION,
        {
            "task": SOURCE_UNIT_INVENTORY_PROMPT,
            "context": asdict(context),
        },
    )


def _source_set_synthesis_prompt(context: SourceSetSynthesisContext) -> str:
    """Bootstrap synthesis prompt (source-ingestion §8.5)."""

    return _json_prompt(
        "learnloop source set synthesis",
        SOURCE_SET_SYNTHESIS_PROMPT_VERSION,
        {
            "task": SOURCE_SET_SYNTHESIS_PROMPT,
            "context": asdict(context),
        },
    )


def _concept_graph_structuring_prompt(context: ConceptGraphContext) -> str:
    """Post-merge concept graph-structuring prompt (source-ingestion §8.5)."""

    return _json_prompt(
        "learnloop concept graph structuring",
        CONCEPT_GRAPH_STRUCTURING_PROMPT_VERSION,
        {
            "task": CONCEPT_GRAPH_STRUCTURING_PROMPT,
            "context": asdict(context),
        },
    )


def _concept_animation_prompt(context: ConceptAnimationContext) -> str:
    """Manim explainer-scene authoring prompt (spec_fork_features §2)."""

    return _json_prompt(
        "learnloop concept animation",
        CONCEPT_ANIMATION_PROMPT_VERSION,
        {
            "task": CONCEPT_ANIMATION_PROMPT,
            "context": asdict(context),
        },
    )


def _append_reconciliation_prompt(context: AppendReconciliationContext) -> str:
    """Append reconciliation prompt (source-ingestion §10.2)."""

    return _json_prompt(
        "learnloop append reconciliation",
        APPEND_RECONCILIATION_PROMPT_VERSION,
        {
            "task": APPEND_RECONCILIATION_PROMPT,
            "context": asdict(context),
        },
    )


def _json_prompt(title: str, prompt_version: str, payload: dict[str, Any]) -> str:
    return (
        f"{title}\n"
        f"prompt_version: {prompt_version}\n\n"
        "Return only JSON that matches the provided output schema. Do not include "
        "Markdown fences or explanatory prose.\n\n"
        f"{json.dumps(payload, sort_keys=True, ensure_ascii=False)}"
    )


def _structured_output_repair_prompt(
    text: str, model_type: type[BaseModel], *, reason: str = ""
) -> str:
    """Bounded second pass for malformed or schema-invalid structured output.

    ``reason`` carries the validator's own diagnosis. It matters most for an
    undeclared field: the repair turn is the mechanism that keeps one bad key
    from costing a whole batch, and it can only drop a field it is told about.
    """

    schema = json.dumps(_codex_output_schema(model_type), sort_keys=True, ensure_ascii=False)
    # JSON-encode the prior output as data so its backslashes, control
    # characters, and any invalid-looking LaTeX escapes cannot become prompt
    # structure on the repair turn.
    encoded_output = json.dumps(text, ensure_ascii=True)
    diagnosis = f"Validator diagnosis of the prior output:\n{reason}\n\n" if reason else ""
    return (
        "Repair the prior model output into one JSON object that validates against "
        "the schema below. Preserve its meaning. Return only JSON. In every JSON "
        "string, escape backslashes (including LaTeX commands) correctly, and replace "
        "any lone Unicode surrogate with the intended Unicode scalar or U+FFFD. Emit "
        "only the fields the schema declares: drop any key it does not list rather "
        "than renaming or inventing one.\n\n"
        f"{diagnosis}"
        f"Schema:\n{schema}\n\nPrior output as a JSON string:\n{encoded_output}"
    )


def _structured_output_regeneration_prompt(prompt: str) -> str:
    """Retry a turn whose malformed JSON was rejected inside app-server."""

    return (
        f"{prompt}\n\n"
        "The prior attempt was rejected because its structured output was not valid "
        "JSON. Generate the answer again. In every JSON string, double every literal "
        "backslash used by LaTeX or other prose (for example, emit `\\\\in`, not "
        "`\\in`) and never emit a lone Unicode surrogate."
    )


def _is_structured_json_transport_error(exc: BaseException) -> bool:
    """Whether app-server failed before returning malformed structured output."""

    message = str(exc).lower()
    return any(
        marker in message
        for marker in (
            "hex escape",
            "invalid escape",
            "unicode escape",
            "invalid json",
            "json parse",
            "json syntax",
        )
    )


def _sdk_reasoning_effort(reasoning_effort_type: Any, value: str | None) -> Any:
    normalized = (value or "").strip().lower()
    if not normalized:
        return None
    try:
        return reasoning_effort_type(normalized)
    except ValueError as exc:
        valid = ", ".join(item.value for item in reasoning_effort_type)
        raise CodexUnavailable(f"Invalid codex.reasoning_effort {value!r}; expected one of: {valid}") from exc


def _sdk_reasoning_summary(reasoning_summary_type: Any, value: str | None) -> Any:
    normalized = (value or "").strip().lower()
    if not normalized:
        return None
    try:
        return reasoning_summary_type.model_validate(normalized)
    except Exception as exc:
        raise CodexUnavailable(
            f"Invalid codex.reasoning_summary {value!r}; expected none, auto, concise, or detailed"
        ) from exc


_UNSUPPORTED_STRICT_SCHEMA_KEYS = {
    "default",
    # Tagged unions (`Field(discriminator=...)`) emit `discriminator` + `oneOf`.
    # Strict structured output permits neither; Pydantic still routes on the
    # `kind` literal when the response is validated, so dropping the hint is
    # free. `oneOf` is renamed rather than dropped -- see _strict_json_schema.
    "discriminator",
    "exclusiveMaximum",
    "exclusiveMinimum",
    "format",
    "maxItems",
    "maxLength",
    "maximum",
    "minItems",
    "minLength",
    "minimum",
    "multipleOf",
    "pattern",
    "title",
    "uniqueItems",
}


def _codex_output_schema(model: type[BaseModel]) -> dict[str, Any]:
    """Return a schema accepted by Codex's strict Responses API wrapper.

    The gate is the point. ``_strict_json_schema`` forbids undeclared fields on
    the wire; :class:`~learnloop.codex.schemas.WireModel` forbids them at
    validation. Those are two halves of one contract, and for most of this
    module's life they agreed only by luck — a model outside the ``WireModel``
    hierarchy runs ``extra="ignore"``, so the provider would be barred from
    emitting a field that, had it arrived by any non-strict route, would have
    been discarded in silence (``spec_measurement_efficiency_v1.md`` §2 F2).
    Refusing to build a schema for such a model makes the two halves derive
    from a single declaration instead.
    """

    if not (isinstance(model, type) and issubclass(model, WireModel)):
        raise TypeError(
            f"{model.__name__} is not a WireModel, so its strict output schema would "
            "forbid extra fields that its validator silently drops. Inherit "
            "learnloop.codex.schemas.WireModel."
        )
    return _strict_json_schema(model.model_json_schema())


def _strict_json_schema(value: Any) -> Any:
    if isinstance(value, list):
        return [_strict_json_schema(item) for item in value]
    if not isinstance(value, dict):
        return value

    normalized: dict[str, Any] = {}
    for key, child in value.items():
        if key in {"$defs", "properties"} and isinstance(child, dict):
            normalized[key] = {name: _strict_json_schema(schema) for name, schema in child.items()}
            continue
        if key in _UNSUPPORTED_STRICT_SCHEMA_KEYS:
            continue
        if key == "additionalProperties":
            continue
        if key == "oneOf":
            # Tagged unions are `anyOf` for our purposes: the variants are
            # mutually exclusive on their `kind` literal anyway, so nothing
            # ambiguous can match twice.
            key = "anyOf"
            if "anyOf" in value:  # pragma: no cover - Pydantic never emits both
                raise ValueError("cannot normalize a schema carrying both anyOf and oneOf")
        if key == "const":
            # `const` is outside the strict-output keyword allowlist; a
            # single-member `enum` is inside it and validates identically.
            normalized["enum"] = [child]
            continue
        normalized[key] = _strict_json_schema(child)

    _flatten_nested_any_of(normalized)

    if _is_object_schema(normalized):
        # The Responses API's strict-schema validator requires the complete
        # object triplet even for a bare ``dict`` that has no declared keys.
        # Omitting ``properties`` here made a parent field disappear during
        # provider validation while its name remained in the parent's
        # ``required`` list (for example ``AppendRestructure.payload``), which
        # surfaced as the misleading "Extra required key 'payload'" 400.
        properties = normalized.get("properties")
        if not isinstance(properties, dict):
            properties = {}
            normalized["properties"] = properties
        normalized["required"] = list(properties.keys())
        normalized["additionalProperties"] = False

    return normalized


def _flatten_nested_any_of(schema: dict[str, Any]) -> None:
    """Splice ``anyOf`` members that are themselves a bare ``anyOf`` wrapper.

    An optional tagged union arrives as ``anyOf: [{oneOf: [...]}, {null}]``;
    once the inner ``oneOf`` is renamed that leaves a pointless nesting level.
    """

    members = schema.get("anyOf")
    if not isinstance(members, list):
        return
    flattened: list[Any] = []
    for member in members:
        if isinstance(member, dict) and set(member) == {"anyOf"} and isinstance(member["anyOf"], list):
            flattened.extend(member["anyOf"])
            continue
        flattened.append(member)
    schema["anyOf"] = flattened


def map_typed_schema_paths(model: type[BaseModel]) -> list[str]:
    """Locate open-keyed object fields, which strict output cannot express.

    Strict structured output requires ``additionalProperties: false`` on every
    object and has no open-keyed map form, so sanitizing one yields an object
    the provider is forbidden to populate: the field always arrives empty
    instead of erroring. The fields that already ship this way are pinned by a
    test so a new one cannot be added without noticing the limitation. Modeling
    such a field as a list of key/value objects is the way to make it fillable.

    Two shapes qualify, and only the first was detected originally:

    * ``dict[str, X]`` -> ``additionalProperties: {<schema of X>}``;
    * a bare ``dict`` / ``dict[str, Any]`` -> ``additionalProperties: true``.

    The second is the same defect wearing a different keyword — it sanitizes to
    ``{"type": "object", "properties": {}, "required": [],
    "additionalProperties": false}``, an object with no declared properties and
    no permitted extras, so the only value the provider can legally emit is
    ``{}``. ``WireModel``'s
    ``extra="forbid"`` cannot help here: the ban lives on the *model*, and
    these are untyped ``dict`` fields with no model behind them.
    """

    def walk(node: Any, path: str) -> Iterator[str]:
        if isinstance(node, list):
            for index, item in enumerate(node):
                yield from walk(item, f"{path}[{index}]")
            return
        if not isinstance(node, dict):
            return
        extra = node.get("additionalProperties")
        if "properties" not in node and (extra is True or (isinstance(extra, dict) and extra)):
            yield path
        for key, child in node.items():
            if key in {"$defs", "properties"} and isinstance(child, dict):
                for name, schema in child.items():
                    yield from walk(schema, f"{path}/{key}/{name}")
                continue
            yield from walk(child, f"{path}/{key}")

    return sorted(set(walk(model.model_json_schema(), "")))


def _is_object_schema(schema: dict[str, Any]) -> bool:
    schema_type = schema.get("type")
    if schema_type == "object":
        return True
    if isinstance(schema_type, list) and "object" in schema_type:
        return True
    return "properties" in schema


def _ensure_sdk_importable(sdk_python_path: Path) -> None:
    if sdk_python_path.exists():
        value = str(sdk_python_path)
        if value not in sys.path:
            sys.path.insert(0, value)


def _sdk_launch_args(command: str) -> tuple[str, ...] | None:
    if not command.strip():
        return None
    return tuple(shlex.split(command, posix=os.name != "nt"))


def _resolved_sdk_codex_bin(configured: str | None) -> str | None:
    """Prefer an explicit/pinned SDK runtime, with a source-checkout fallback.

    LearnLoop can import the SDK straight from a Codex source checkout. Such a
    checkout does not necessarily install the SDK's optional
    ``openai-codex-cli-bin`` package, so leaving ``codex_bin`` unset would make
    every tutor/authoring call fail before launch. When the pinned package is
    present the SDK resolves it itself; otherwise use the installed CLI.
    """

    if (configured or "").strip():
        return str(configured).strip()
    try:
        from codex_cli_bin import bundled_codex_path

        bundled_codex_path()
        return None
    except (ImportError, FileNotFoundError):
        return shutil.which("codex.cmd" if os.name == "nt" else "codex")


def _resolve_checkout_path(vault_root: Path, checkout_path: str) -> Path:
    raw = Path(checkout_path)
    if raw.is_absolute():
        return raw.resolve()
    return (vault_root / raw).resolve()


def _resolve_sdk_python_path(checkout_path: Path, sdk_python_path: str) -> Path:
    raw = Path(sdk_python_path)
    if raw.is_absolute():
        return raw.resolve()
    return (checkout_path / raw).resolve()


def _log_codex_debug(event: str, **fields: Any) -> None:
    """Emit full Codex request/response data into sidecar debug logs.

    The sidecar JSONL formatter treats ``event_fields`` specially. Keeping this
    helper in the core client avoids coupling Codex transport code back to the
    Tauri sidecar package while still making debug logs capture each prompt and
    response when sidecar debug logging is enabled.
    """

    if not LOG.isEnabledFor(logging.DEBUG):
        return
    LOG.debug(event, extra={EVENT_FIELDS_ATTR: {k: v for k, v in fields.items() if v is not None}})
