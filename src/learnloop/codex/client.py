from __future__ import annotations

import json
import logging
import os
import shlex
import shutil
import sys
import urllib.error
import urllib.request
from dataclasses import asdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from typing import Literal, Mapping, Protocol

from pydantic import BaseModel

from learnloop.config import CodexConfig
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
    APPEND_RECONCILIATION_PROMPT,
    APPEND_RECONCILIATION_PROMPT_VERSION,
    SOURCE_SET_SYNTHESIS_PROMPT,
    SOURCE_SET_SYNTHESIS_PROMPT_VERSION,
    SOURCE_UNIT_INVENTORY_PROMPT,
    SOURCE_UNIT_INVENTORY_PROMPT_VERSION,
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
    AppendReconciliation,
    SourceSetSynthesis,
    SourceUnitInventory,
    TeachBackQuestion,
    TutorAnswer,
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
    error_taxonomy: dict[str, Any] = field(default_factory=dict)


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

    context: str  # "library" | "practice" | "feedback"
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
    max_followups: int = 3
    learning_object_title: str | None = None
    learning_object_summary: str | None = None


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

    def run_misconception_match(self, context: Any) -> MisconceptionMatch:
        ...

    def run_promotion_analysis(self, context: Any) -> PromotionAnalysis:
        ...


class CodexUnavailable(RuntimeError):
    pass


def make_codex_client(config: CodexConfig, vault_root: Path) -> CodexClient:
    provider = config.provider.lower()
    if provider == "http":
        return HttpCodexClient(config)
    if provider == "sdk":
        return SdkCodexClient(config, vault_root)
    raise CodexUnavailable(f"Unsupported Codex provider {config.provider!r}")


class HttpCodexClient:
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
        return AuthoringProposal.model_validate(payload.get("proposal", payload))

    def run_canonical_ingest(self, context: CanonicalIngestContext) -> AuthoringProposal:
        payload = self._post(
            self.config.canonical_ingest_path,
            {"context": asdict(context)},
            purpose="canonical_ingest",
        )
        return AuthoringProposal.model_validate(payload.get("proposal", payload))

    def run_grading_proposal(self, context: GradingContext) -> GradingProposal:
        payload = self._post(self.config.grading_path, {"context": asdict(context)}, purpose="grading")
        return GradingProposal.model_validate(payload.get("proposal", payload))

    def run_tutor_qa(self, context: TutorQAContext) -> TutorAnswer:
        payload = self._post(self.config.tutor_qa_path, {"context": asdict(context)}, purpose="tutor_qa")
        return TutorAnswer.model_validate(payload.get("proposal", payload))

    def run_teach_back_question(self, context: TeachBackQuestionContext) -> TeachBackQuestion:
        payload = self._post(self.config.teach_back_path, {"context": asdict(context)}, purpose="teach_back")
        return TeachBackQuestion.model_validate(payload.get("proposal", payload))

    def run_misconception_match(self, context: Any) -> MisconceptionMatch:
        context_payload = context if isinstance(context, dict) else asdict(context)
        payload = self._post(
            self.config.misconception_match_path,
            {"context": context_payload},
            purpose="misconception_match",
        )
        return MisconceptionMatch.model_validate(payload.get("proposal", payload))

    def run_promotion_analysis(self, context: Any) -> PromotionAnalysis:
        context_payload = context if isinstance(context, dict) else asdict(context)
        payload = self._post(
            getattr(self.config, "promotion_analysis_path", "/promotion-analysis"),
            {"context": context_payload},
            purpose="promotion_analysis",
        )
        return PromotionAnalysis.model_validate(payload.get("proposal", payload))

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


class SdkCodexClient:
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

    def run_authoring_proposal(self, context: AuthoringContext) -> AuthoringProposal:
        text = self._run_structured(
            _authoring_prompt(context),
            _codex_output_schema(AuthoringProposal),
            purpose="authoring",
        )
        return AuthoringProposal.model_validate_json(text)

    def run_canonical_ingest(self, context: CanonicalIngestContext) -> AuthoringProposal:
        text = self._run_structured(
            _canonical_ingest_prompt(context),
            _codex_output_schema(AuthoringProposal),
            purpose="canonical_ingest",
        )
        return AuthoringProposal.model_validate_json(text)

    def run_grading_proposal(self, context: GradingContext) -> GradingProposal:
        text = self._run_structured(
            _grading_prompt(context),
            _codex_output_schema(GradingProposal),
            purpose="grading",
        )
        return GradingProposal.model_validate_json(text)

    def run_tutor_qa(self, context: TutorQAContext) -> TutorAnswer:
        text = self._run_structured(
            _tutor_qa_prompt(context),
            _codex_output_schema(TutorAnswer),
            purpose="tutor_qa",
        )
        return TutorAnswer.model_validate_json(text)

    def run_teach_back_question(self, context: TeachBackQuestionContext) -> TeachBackQuestion:
        text = self._run_structured(
            _teach_back_question_prompt(context),
            _codex_output_schema(TeachBackQuestion),
            purpose="teach_back",
        )
        return TeachBackQuestion.model_validate_json(text)

    def run_misconception_match(self, context: Any) -> MisconceptionMatch:
        text = self._run_structured(
            _misconception_match_prompt(context),
            _codex_output_schema(MisconceptionMatch),
            purpose="misconception_match",
        )
        return MisconceptionMatch.model_validate_json(text)

    def run_promotion_analysis(self, context: Any) -> PromotionAnalysis:
        text = self._run_structured(
            _promotion_analysis_prompt(context),
            _codex_output_schema(PromotionAnalysis),
            purpose="promotion_analysis",
        )
        return PromotionAnalysis.model_validate_json(text)

    def run_diagnostic_trials(self, context: Any) -> DiagnosticTrials:
        """Codex answers-under-belief for the sim discrimination gate (spec §6).

        Deliberately NOT on the ``CodexClient`` Protocol / ``HttpCodexClient`` —
        the gate discovers it via ``getattr(client, "run_diagnostic_trials",
        None)`` so providers without it degrade to the deterministic path.
        """

        text = self._run_structured(
            _diagnostic_trials_prompt(context),
            _codex_output_schema(DiagnosticTrials),
            purpose="diagnostic_trials",
        )
        return DiagnosticTrials.model_validate_json(text)

    def run_probe_instance_surfaces(self, context: ProbeInstanceContext) -> ProbeInstanceSurfaces:
        """LLM-backed Item Instance surfaces (probe redesign §9.2/§9.4).

        Deliberately NOT on the ``CodexClient`` Protocol / ``HttpCodexClient`` —
        instance generation discovers it via ``getattr(client,
        "run_probe_instance_surfaces", None)`` and falls back to the parametric
        surface templates when the provider lacks it or is unavailable.
        """

        text = self._run_structured(
            _probe_instance_surfaces_prompt(context),
            _codex_output_schema(ProbeInstanceSurfaces),
            purpose="probe_instance_surfaces",
        )
        return ProbeInstanceSurfaces.model_validate_json(text)

    def run_probe_dialogue_turn(self, context: ProbeDialogueTurnContext) -> ProbeDialogueTurn:
        """One adaptive dialogue microprobe turn (probe redesign §8.1).

        Same getattr-discovery contract as ``run_probe_instance_surfaces``:
        the dialogue service falls back to the parametric turn templates when
        the provider lacks it or is unavailable.
        """

        text = self._run_structured(
            _probe_dialogue_turn_prompt(context),
            _codex_output_schema(ProbeDialogueTurn),
            purpose="probe_dialogue_turn",
        )
        return ProbeDialogueTurn.model_validate_json(text)

    def run_probe_family_trials(self, context: ProbeFamilyTrialsContext) -> ProbeFamilyTrials:
        """LLM planted trials for the family admission gate (probe redesign §9.6).

        Same getattr-discovery contract as ``run_diagnostic_trials``: the gate
        runner degrades to reporting that no trial source is available rather
        than fabricating synthetic admission evidence.
        """

        text = self._run_structured(
            _probe_family_trials_prompt(context),
            _codex_output_schema(ProbeFamilyTrials),
            purpose="probe_family_trials",
        )
        return ProbeFamilyTrials.model_validate_json(text)

    def run_source_unit_inventory(self, context: SourceUnitInventoryContext) -> SourceUnitInventory:
        """Role-aware unit inventory over one unit view (source-ingestion §7).

        Deliberately NOT on the ``CodexClient`` Protocol / ``HttpCodexClient`` —
        the inventory service discovers it via ``getattr(client,
        "run_source_unit_inventory", None)`` and degrades (no inventory produced)
        when the provider lacks it or is unavailable. The returned contract is
        candidate-only; the service reassigns deterministic ids and validates
        span citations before persisting.
        """

        text = self._run_structured(
            _source_unit_inventory_prompt(context),
            _codex_output_schema(SourceUnitInventory),
            purpose="source_unit_inventory",
        )
        return SourceUnitInventory.model_validate_json(text)

    def run_source_set_synthesis(self, context: SourceSetSynthesisContext) -> SourceSetSynthesis:
        """N-way bootstrap synthesis over role-specific inventories (§8.5).

        Deliberately NOT on the ``CodexClient`` Protocol / ``HttpCodexClient`` —
        the synthesis service discovers it via ``getattr(client,
        "run_source_set_synthesis", None)`` and degrades when the provider lacks
        it. Output is candidate-only, span-cited, and dependency-annotated; the
        service validates spans, runs the §8.7 gates, normalizes dependencies,
        and persists through the existing proposal pipeline.
        """

        text = self._run_structured(
            _source_set_synthesis_prompt(context),
            _codex_output_schema(SourceSetSynthesis),
            purpose="source_set_synthesis",
        )
        return SourceSetSynthesis.model_validate_json(text)

    def run_append_reconciliation(self, context: AppendReconciliationContext) -> AppendReconciliation:
        """Reconcile new/changed material into an existing map (§10.1/§10.2).

        Deliberately NOT on the ``CodexClient`` Protocol — the append service
        discovers it via ``getattr(client, "run_append_reconciliation", None)`` and
        degrades when the provider lacks it. Output is candidate-only, span-cited,
        and dependency-annotated; the service verifies additivity from item type +
        payload, runs the §8.7 gates plus the append-vocabulary gate, and persists
        through the existing proposal pipeline."""

        text = self._run_structured(
            _append_reconciliation_prompt(context),
            _codex_output_schema(AppendReconciliation),
            purpose="append_reconciliation",
        )
        return AppendReconciliation.model_validate_json(text)

    def _run_structured(self, prompt: str, output_schema: dict[str, Any], *, purpose: str) -> str:
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
            if launch_args is None and not self.config.sdk_codex_bin:
                launch_args = _default_sdk_launch_args()
            app_config = SdkAppConfig(
                codex_bin=self.config.sdk_codex_bin or None,
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
                result = thread.run(
                    prompt,
                    cwd=str(self.vault_root),
                    model=self.config.model or None,
                    effort=effort,
                    output_schema=output_schema,
                    personality=Personality.pragmatic,
                    summary=summary,
                )
        except Exception as exc:
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
    "`surface_family`, and `repair_targets`. `criterion_facet_weights` must map "
    "EVERY rubric criterion id (core and transfer) to its facet weight map; an "
    "empty object `{}` fails validation whenever the item has a rubric. Generated "
    "grading rubrics must stay on the LearnLoop 0-4 grading scale: set `max_points` "
    "to 4 or less, and make rubric criterion points sum to `max_points`. "
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
                "For each error_attribution's `error_type`, pick the id from "
                "`error_taxonomy.canonical_error_types` whose `use_when` fits the "
                "observed failure and whose `avoid_when` does not — use ONLY those "
                "ids for ordinary errors. Use existing rubric fatal "
                "error ids or vault-specific taxonomy ids only when they apply more "
                "precisely. If the learner explicitly says they do not know, do not "
                "remember, or cannot recall a specific requested part, assign that "
                "part to the taxonomy id describing an inability to retrieve from "
                "memory; do not invent a `missing_*` or `unknown_*` "
                "error type. For each failed rubric line or facet, add an "
                "error_attribution unless another attribution already covers the same "
                "failure. For each error_attribution, fill "
                "`target_criterion_ids` and/or `target_evidence_families` with "
                "the rubric line(s) and item evidence facet(s) most directly affected. "
                "For each repair_suggestion, also fill `target_evidence_families` "
                "with the narrow item evidence facet(s) the learner-facing repair "
                "rationale is meant to diagnose or repair. "
                "When an error_attribution sets `is_misconception=true`, "
                "`misconception_statement` is REQUIRED: state the learner's belief "
                "in learner-model terms (what the learner thinks is true), NOT a "
                "description of the wrong answer — e.g. \"believes Q maps standard "
                "vectors to eigenbasis coefficients (reverses Q / Q^T)\", not "
                "\"used Q instead of Q^T\". Also fill "
                "`misconception_consistent_answer` when you can: the answer a holder "
                "of that belief would give on this specific item. "
                "Use the supplied `error_taxonomy.selection_policy` and "
                "`error_taxonomy.targeting_policy` exactly."
            ),
            "context": asdict(context),
        },
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
    "Write answer_md as concise Markdown (LaTeX math allowed)."
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
}


# Naive-student persona for teach-back. The load-bearing guardrails: the
# student must never correct, confirm, deny, or reveal — otherwise the graded
# transcript stops being independent learner evidence.
_TEACH_BACK_TASK = (
    "You are a curious NAIVE STUDENT being taught by the learner. The learner "
    "just explained the concept to you (see context.transcript, oldest first). "
    "Return a TeachBackQuestion as schema-valid JSON only. Ask exactly ONE "
    "short follow-up question, in character, that probes the rubric criterion "
    "described by context.criterion_description and its target facets "
    "(context.facet_targets). You do not know the answer: you may feign "
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
    "Markdown (LaTeX math allowed)."
)


def _tutor_qa_prompt(context: TutorQAContext) -> str:
    opening = not context.question_md.strip() and context.diagnostic_decision is not None
    task = _TUTOR_QA_CONTEXT_TASKS.get(context.context, _TUTOR_QA_CONTEXT_TASKS["library"])
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
    """Return a schema accepted by Codex's strict Responses API wrapper."""

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
        normalized[key] = _strict_json_schema(child)

    if _is_object_schema(normalized):
        properties = normalized.get("properties")
        if isinstance(properties, dict):
            normalized["required"] = list(properties.keys())
        else:
            normalized.setdefault("required", [])
        normalized["additionalProperties"] = False

    return normalized


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


def _default_sdk_launch_args() -> tuple[str, ...]:
    executable = shutil.which("codex.cmd" if os.name == "nt" else "codex") or "codex"
    return (executable, "app-server", "--listen", "stdio://")


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
