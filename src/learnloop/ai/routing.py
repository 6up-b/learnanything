"""Provider selection and the single AI client composition root."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Iterator, Literal

from learnloop.ai.errors import AIProviderUnavailable
from learnloop.config import LearnLoopConfig
from learnloop.config.schema import (
    DECIDER_PROFILE_TYPE, DEFAULT_DECIDER_PROVIDER, DEFAULT_EMBEDDING_PROVIDER,
)

if TYPE_CHECKING:  # pragma: no cover
    from learnloop.ai.runtime import AIRuntimeReport

MANUAL_PROVIDER = "manual"
EMBEDDING_PROFILE_TYPE = "openai_embedding"
#: Profile types whose client serves a read-only workspace (a snapshot
#: diagnosis): Codex reads it in its sandbox; the ChatGPT plan is served it by
#: LearnLoop (``learnloop.ai.chatgpt_plan.workspace``). The client's
#: ``supports(READ_ONLY_WORKSPACE)`` stays authoritative; this answers the
#: same question from configuration alone (a dry run builds no client).
WORKSPACE_PROFILE_TYPES: frozenset[str] = frozenset({"codex_sdk", "chatgpt_plan"})
#: Profile types that take a caller's whole-operation deadline
#: (:func:`client_for_provider`).
TURN_DEADLINE_PROFILE_TYPES: frozenset[str] = frozenset({"codex_sdk", "chatgpt_plan"})

AITask = Literal[
    "embedding",
    "field_question_classifier",
    "pf_generator",
    "pf_proposers",
    "pf_selection_judge",
    "pf_family_judge",
    "pf_isomorph_judge",
    "pf_closed_book",
    "pf_reference_verifier",
    "pf_solver_panel",
    "practice_dossier",
    "practice_rerank",
    "practice_query_writer",
    "practice_relevance_judge",
    # Slice 2 T6 source retrieval: the live rewrite of conceptual questions and
    # the tutor-span verification rerank, and the retrieval evaluation's / B4's
    # question writer and two-pass relevance judge.
    "source_query_rewrite",
    "source_rerank",
    "source_query_writer",
    "source_relevance_judge",
    # Canonical sources (spec_source_practice_and_probes_v1 §13): the book's
    # solution match (S1), the syntopic comparison (S3), the exercise
    # discrimination screen and the worked-example equivalence judge (S2a).
    "source_solution_match",
    "source_compare",
    "exercise_discrimination",
    "worked_example_equivalence",
    # Slice 2 T4: the owner-run contamination report's leak/reveal judge.
    "contamination_judge",
    # Facet identity (handoff §4): the cheap same-skill partition judge.
    "facet_identity_judge",
    "grading",
    # Slice 1: the history-aware diagnoser (unset -> the resolved grading
    # route, so a vault that never configures it diagnoses with its grader),
    # the offline review's judge, and its planted-case/probe generator.
    "diagnosis",
    "diagnosis_judge",
    "diagnosis_generator",
    # Slice 2 T1: the same-cause judge (unset -> the resolved diagnosis route).
    "same_cause_judge",
    # Learner-text gaps: the same/different and needed-for-item judge and the
    # stuck-text reader (unset -> the resolved diagnosis route), and the
    # Decider's second opinion (a decider task).
    "learner_gap_judge",
    "learner_gap_reader",
    "learner_gap_decider",
    "canonical_ingest",
    "canonical_ingest_retry",
    "authoring",
    "tutor_qa",
    "teach_back",
    "rung_variant",
    "animation",
    "transcription",
    "video_generation",
    "project",
    # Action router and the learner field's llm_probability arms (router spec
    # §6.2): the decider routes reach a decision model, the LLM routes a chat
    # transport with structured output.
    "tier1_decider",
    "router_decider",
    "router_llm",
    "llm_probability_decider",
    "llm_probability_llm",
    # Method-explicit items (owner rule 2026-10-13): the judge that reads
    # whether a rubric criterion is phrased by method (a decider or chat
    # profile; `learnloop grading method-phrasing`), and makes the one-time
    # required-method statement judgments at import and PF selection.
    "rubric_phrasing_judge",
    # Reader workbench RW1b: the intent box's router (a decider task).
    "reader_intent",
    # Reader workbench RW4a: the library answer's organizer (a listwise task).
    "library_organizer",
]

#: Routes served only by a ``decider`` profile. They never fall back to a chat
#: provider (the interface differs) and ``LEARNLOOP_AI_PROVIDER`` never
#: overrides them, the same rule as ``ai.routing.embedding``.
DECIDER_TASKS: frozenset[str] = frozenset(
    {"router_decider", "llm_probability_decider", "learner_gap_decider", "tier1_decider", "reader_intent"}
)
#: Routes a chat profile OR a ``decider`` profile may serve: the caller asks a
#: structured question of a chat model, or typed questions of a decision model
#: (facet identity: one choice question per facet pair, owner 2026-10-12).
#: Unlike DECIDER_TASKS they keep the ordinary chat-route resolution (an unset
#: route is the active provider's, and a decider is chosen by naming one).
DECIDER_ACCEPTING_TASKS: frozenset[str] = frozenset({"facet_identity_judge", "rubric_phrasing_judge"})

# Every structured operation explicitly inherits one configured task route.
# This is documentation as executable data: feature callers no longer invent
# provider-routing policy from the operation's method name.
ROUTE_FOR_OPERATION: dict[str, AITask] = {
    "field_question_classification": "field_question_classifier",
    "authoring_proposal": "authoring",
    "canonical_ingest": "canonical_ingest",
    "grading_proposal": "grading",
    "blind_grading_proposal": "grading",
    "diagnosis_proposal": "diagnosis",
    "diagnosis_review_judgment": "diagnosis_judge",
    "diagnosis_link_judgment": "diagnosis_judge",
    "diagnosis_planted_cause_judgment": "diagnosis_judge",
    "diagnosis_planted_scenario": "diagnosis_generator",
    "diagnosis_valid_alternative": "diagnosis_generator",
    "diagnosis_synthetic_error": "diagnosis_generator",
    "diagnosis_paraphrase": "diagnosis_generator",
    # Slice 2 T1: one pairwise same-cause verdict; B1's hypothesis writer is
    # the diagnoser's own route (production hypotheses are diagnoser text).
    "same_cause_judgment": "same_cause_judge",
    "recurrence_b1_hypothesis": "diagnosis",
    # Slice 2 T1 §3.7: a repair with a different operator and representation
    # for a recurrence group's K-th answer (the diagnoser's own route).
    "recurrence_escalation_repair": "diagnosis",
    # Learner-text gaps (implementation_handoffs §4): one pairwise verdict
    # (same prerequisite / same belief), the "needed for this item?" yes/no,
    # the stuck-text reading, and the missing prerequisite's draft (the
    # authoring route, as the owner decided).
    "learner_gap_same_prerequisite": "learner_gap_judge",
    "learner_gap_same_belief": "learner_gap_judge",
    "learner_gap_prerequisite_needed": "learner_gap_judge",
    "learner_gap_reading": "learner_gap_reader",
    "learner_gap_prerequisite_draft": "authoring",
    "tutor_qa": "tutor_qa",
    "teach_back_question": "teach_back",
    "teach_back_authoring": "teach_back",
    "misconception_match": "grading",
    "promotion_analysis": "tutor_qa",
    "diagnostic_trials": "authoring",
    "grade_diagnostic_fire": "grading",
    "probe_instance_surfaces": "authoring",
    "probe_dialogue_turn": "authoring",
    "probe_family_trials": "authoring",
    "reader_preset_synthesis": "tutor_qa",
    "reading_quick_check": "tutor_qa",
    "rung_backfill": "authoring",
    "exercise_authoring": "authoring",
    "depth_edge_instances": "authoring",
    "source_unit_inventory": "canonical_ingest",
    "source_set_synthesis": "canonical_ingest",
    "concept_graph_structuring": "canonical_ingest",
    "concept_animation": "animation",
    "video_storyboard": "animation",
    "video_generation": "video_generation",
    "append_reconciliation": "canonical_ingest",
    "vault_epigraphs": "canonical_ingest",
    "media_transcription": "transcription",
    "media_markdown": "canonical_ingest",
    # Project understanding M1 (spec_project_understanding_v1 §7). Probe
    # grading deliberately uses the grading route, not the project route.
    "project_probe_authoring": "project",
    "project_closed_book_check": "project",
    "project_probe_grading": "grading",
    "practice_dossier": "practice_dossier",
    "practice_rerank": "practice_rerank",
    "practice_query_writer": "practice_query_writer",
    "practice_relevance_judge": "practice_relevance_judge",
    "source_query_rewrite": "source_query_rewrite",
    "source_rerank": "source_rerank",
    "source_query_writer": "source_query_writer",
    "source_relevance_judge": "source_relevance_judge",
    "source_solution_match": "source_solution_match",
    "source_compare": "source_compare",
    "exercise_discrimination": "exercise_discrimination",
    "worked_example_equivalence": "worked_example_equivalence",
    # Reader workbench RW4a: one listwise call noting what each passage of a
    # library answer contributes.
    "library_organizer": "library_organizer",
    # Slice 2 T4 shadow contamination flags (owner-run report only).
    "contamination_leak_judgment": "contamination_judge",
    "contamination_reveal_judgment": "contamination_judge",
    # Router R0: the learner field's llm_probability LLM judge (field §7.2).
    "llm_probability_prediction": "llm_probability_llm",
    # Facet identity at ingest and in `learnloop facets dedupe`.
    "facet_identity_judgment": "facet_identity_judge",
    # Method-explicit items: one item's criteria read for method phrasing, and
    # the one-time judgment of a statement that must not be rewritten.
    "rubric_phrasing_judgment": "rubric_phrasing_judge",
    "required_method_statement": "rubric_phrasing_judge",
}


@dataclass(frozen=True, slots=True)
class AIProviderSelection:
    provider_name: str
    explicit: bool = False
    from_env: bool = False


@dataclass(frozen=True, slots=True)
class ResolvedClient:
    """Typed outcome of provider selection, readiness, fallback, and build.

    ``manual`` is a first-class no-client outcome. ``selection`` always records
    what was requested; ``provider_name`` is the provider actually chosen after
    fallback, and ``fallback_from`` records the original name when applicable.
    Iteration preserves the historical ``(provider, runtime, client)`` tuple at
    the small compatibility wrappers being migrated in this stage.
    """

    selection: AIProviderSelection
    provider_name: str
    runtime: AIRuntimeReport
    client: Any | None
    manual: bool = False
    fallback_from: str | None = None

    @property
    def ready(self) -> bool:
        return not self.manual and self.runtime.ready and self.client is not None

    def __iter__(self) -> Iterator[Any]:
        yield self.provider_name
        yield self.runtime
        yield self.client


def provider_for_task(
    config: LearnLoopConfig,
    task: AITask,
    *,
    explicit_provider: str | None = None,
    allow_env: bool = True,
) -> AIProviderSelection:
    """Select a configured name with explicit > environment > route precedence."""

    if explicit_provider:
        return AIProviderSelection(provider_name=explicit_provider, explicit=True)
    if task == "embedding":
        # A global chat override must never redirect learner text or select Codex.
        # Unset is the code-default embedding profile; embedding.enabled still
        # gates every client (ready_client_for_task).
        return AIProviderSelection(
            provider_name=config.ai.routing.embedding or DEFAULT_EMBEDDING_PROVIDER, explicit=True,
        )
    if task in DECIDER_TASKS:
        # A decision model is not a chat transport: an unset route names the
        # code-default decider profile, never the active provider or the env.
        routed = getattr(config.ai.routing, task, None)
        return AIProviderSelection(provider_name=routed or DEFAULT_DECIDER_PROVIDER, explicit=True)
    if task == "field_question_classifier":
        # Offline experiments must not silently inherit a paid serving route.
        return AIProviderSelection(provider_name=getattr(config.ai.routing, task) or "", explicit=True)
    env_provider = os.environ.get("LEARNLOOP_AI_PROVIDER") if allow_env else None
    if env_provider:
        return AIProviderSelection(provider_name=env_provider, from_env=True)
    routed = getattr(config.ai.routing, task, None)
    if task in LIST_ROUTE_TASKS:
        # A list route's single-provider view is its first entry; callers that
        # need the whole panel use provider_list_for_task.
        routed = _route_list(routed)[0] if _route_list(routed) else None
    if task == "canonical_ingest_retry" and not routed:
        return AIProviderSelection(provider_name="")
    if task == "project" and not routed:
        # spec_project_understanding_v1 §7: the project route defaults to the
        # grading provider before the active provider.
        routed = config.ai.routing.grading
    if task == "diagnosis" and not routed:
        # Slice 1 §9.1: an unset diagnosis route follows the RESOLVED grading
        # route, not the active provider, so the diagnoser can be moved to a
        # stronger model by config alone and otherwise matches the grader.
        return provider_for_task(config, "grading", allow_env=allow_env)
    if task == "same_cause_judge" and not routed:
        # Slice 2 §3.1: the same-cause judge is "routed like diagnosis".
        return provider_for_task(config, "diagnosis", allow_env=allow_env)
    if task in ("learner_gap_judge", "learner_gap_reader") and not routed:
        # Learner-text gaps: judged and read like a diagnosis.
        return provider_for_task(config, "diagnosis", allow_env=allow_env)
    return AIProviderSelection(provider_name=routed or config.ai.active_provider)


# Routes that may name several profiles (Slice 2 §5.8): the ensemble proposers
# and a solver panel at different tiers (P10).
LIST_ROUTE_TASKS: frozenset[str] = frozenset({"pf_proposers", "pf_solver_panel"})


def _route_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value.strip() else []
    return [str(entry) for entry in value if str(entry).strip()]


def route_names(value: Any) -> list[str]:
    """The profile names one route value names: a single profile or a list route."""

    return _route_list(value)


def provider_list_for_task(
    config: LearnLoopConfig,
    task: AITask,
    *,
    allow_env: bool = True,
) -> list[AIProviderSelection]:
    """Every configured profile of a list route, in order, duplicates removed.

    An unset list route falls back like any route: the environment override,
    then the active provider. Receipts still record each resolved model.
    """

    if task not in LIST_ROUTE_TASKS:
        return [provider_for_task(config, task, allow_env=allow_env)]
    env_provider = os.environ.get("LEARNLOOP_AI_PROVIDER") if allow_env else None
    if env_provider:
        return [AIProviderSelection(provider_name=env_provider, from_env=True)]
    names = list(dict.fromkeys(_route_list(getattr(config.ai.routing, task, None))))
    if not names:
        return [AIProviderSelection(provider_name=config.ai.active_provider)]
    return [AIProviderSelection(provider_name=name, explicit=True) for name in names]


def provider_for_operation(
    config: LearnLoopConfig,
    operation: str,
    *,
    explicit_provider: str | None = None,
    allow_env: bool = True,
) -> AIProviderSelection:
    try:
        task = ROUTE_FOR_OPERATION[operation]
    except KeyError as exc:
        raise ValueError(f"No AI task route is declared for operation {operation!r}") from exc
    return provider_for_task(
        config,
        task,
        explicit_provider=explicit_provider,
        allow_env=allow_env,
    )


def fallback_provider_for(config: LearnLoopConfig, selection: AIProviderSelection) -> str | None:
    fallback = (config.ai.fallback_provider or "").strip() or None
    if selection.explicit or selection.from_env or fallback == selection.provider_name:
        return None
    return fallback


def route_profile_mismatch(
    config: LearnLoopConfig,
    provider_name: str,
    task: AITask | None,
) -> str | None:
    """Why ``provider_name`` cannot serve ``task``, or ``None`` when it can.

    Embedding profiles have no completion transport, so they never answer a
    generation task; the embedding task sends learner-derived text only to an
    explicit embedding profile. ``task=None`` is a generation use (grading,
    tutoring, a session override, the active provider).
    """

    profile = config.ai.providers.get(provider_name)
    if profile is None:
        return None
    profile_type = profile.type.strip().lower()
    embedding_profile = profile_type == EMBEDDING_PROFILE_TYPE
    decider_profile = profile_type == DECIDER_PROFILE_TYPE
    if task == "embedding" and not embedding_profile:
        return f"Embedding requires an {EMBEDDING_PROFILE_TYPE} profile; {provider_name!r} is {profile.type!r}."
    if task in DECIDER_TASKS and not decider_profile:
        return (
            f"{task} requires a {DECIDER_PROFILE_TYPE} profile; {provider_name!r} is "
            f"{profile.type!r}. A decision route never falls back to a chat provider."
        )
    if task != "embedding" and embedding_profile:
        return (
            f"{provider_name!r} is an embedding-only profile; it cannot serve "
            f"{task or 'generation'} work."
        )
    if task not in DECIDER_TASKS and task not in DECIDER_ACCEPTING_TASKS and decider_profile:
        return (
            f"{provider_name!r} is a decision-model profile; it answers typed questions "
            f"only and cannot serve {task or 'generation'} work."
        )
    return None


def is_embedding_profile(config: LearnLoopConfig, provider_name: str) -> bool:
    profile = config.ai.providers.get(provider_name)
    return profile is not None and profile.type.strip().lower() == EMBEDDING_PROFILE_TYPE


def is_decider_profile(config: LearnLoopConfig, provider_name: str) -> bool:
    profile = config.ai.providers.get(provider_name)
    return profile is not None and profile.type.strip().lower() == DECIDER_PROFILE_TYPE


def serves_read_only_workspace(config: LearnLoopConfig, provider_name: str | None) -> bool:
    """Whether the profile ``provider_name`` can serve a read-only workspace (by its type)."""

    profile = config.ai.providers.get(provider_name or "")
    return profile is not None and profile.type.strip().lower() in WORKSPACE_PROFILE_TYPES


def is_generation_profile(config: LearnLoopConfig, provider_name: str) -> bool:
    """Whether a configured name can serve a chat/generation route.

    Embedding and decision-model profiles have no completion transport, so
    no generation selector (active provider, grading, use cases) offers them.
    Unknown names are left to the caller's own validation.
    """

    return not (is_embedding_profile(config, provider_name) or is_decider_profile(config, provider_name))


def runtime_for_provider(
    vault_root: Path,
    config: LearnLoopConfig,
    provider_name: str,
    *,
    task: AITask | None = None,
) -> AIRuntimeReport:
    """Return one provider-neutral readiness report for any configured name.

    ``task`` defaults to a generation use; an embedding-only profile is then
    never ready, and the embedding task accepts nothing else.
    """

    from learnloop.ai.runtime import AIRuntimeReport, check_ai_runtime

    if provider_name in {"", MANUAL_PROVIDER}:
        return AIRuntimeReport(
            status="provider_unavailable",
            active_provider=MANUAL_PROVIDER,
            message="Manual mode selected; AI is disabled for this workflow.",
        )
    mismatch = route_profile_mismatch(config, provider_name, task)
    if mismatch is not None:
        return AIRuntimeReport(
            status="provider_unavailable",
            active_provider=provider_name,
            provider_type=config.ai.providers[provider_name].type,
            message=mismatch,
        )
    return check_ai_runtime(vault_root, config, provider_name=provider_name)


def client_for_provider(
    vault_root: Path,
    config: LearnLoopConfig,
    provider_name: str,
    *,
    timeout_seconds: int | None = None,
    task: AITask | None = None,
) -> Any | None:
    """Build a configured provider client, returning no client for manual mode."""

    if provider_name in {"", MANUAL_PROVIDER}:
        return None
    mismatch = route_profile_mismatch(config, provider_name, task)
    if mismatch is not None:
        raise AIProviderUnavailable(mismatch)
    from learnloop.ai.client import make_ai_provider_client

    profile = config.ai.providers.get(provider_name)
    # A turn transport's deadline spans the whole operation (Codex's turn, or
    # a ChatGPT-plan workspace turn's rounds and retries), so it takes the
    # caller's; a chat profile keeps its own per-request timeout.
    provider_timeout = (
        timeout_seconds
        if profile is not None and profile.type.strip().lower() in TURN_DEADLINE_PROFILE_TYPES
        else None
    )
    return make_ai_provider_client(
        config,
        vault_root,
        provider_name=provider_name,
        timeout_seconds=provider_timeout,
    )


def ready_client_for_task(
    vault_root: Path,
    config: LearnLoopConfig,
    task: AITask,
    *,
    explicit: str | None = None,
    allow_env: bool = True,
    timeout_seconds: int | None = None,
) -> ResolvedClient:
    """Resolve selection, readiness, fallback, and construction exactly once."""

    selection = provider_for_task(
        config,
        task,
        explicit_provider=explicit,
        allow_env=allow_env,
    )
    if task == "embedding" and not config.embedding.enabled:
        # The master switch is enforced where the paid client is obtained, so
        # no consumer can send text while embeddings are off.
        return _manual_resolution(
            selection,
            message="Embeddings are disabled; set embedding.enabled = true to use them.",
        )
    if selection.provider_name in {"", MANUAL_PROVIDER}:
        return _manual_resolution(selection)

    primary = _resolve_selected_provider(
        vault_root,
        config,
        selection,
        selection.provider_name,
        task=task,
        timeout_seconds=timeout_seconds,
    )
    if primary.runtime.ready or task == "embedding" or task in DECIDER_TASKS:
        return primary

    fallback = fallback_provider_for(config, selection)
    if fallback in {None, ""}:
        return primary
    if fallback == MANUAL_PROVIDER:
        return _manual_resolution(selection, fallback_from=selection.provider_name)

    candidate = _resolve_selected_provider(
        vault_root,
        config,
        selection,
        fallback,
        task=task,
        timeout_seconds=timeout_seconds,
        fallback_from=selection.provider_name,
    )
    return candidate if candidate.runtime.ready else primary


def _resolve_selected_provider(
    vault_root: Path,
    config: LearnLoopConfig,
    selection: AIProviderSelection,
    provider_name: str,
    *,
    task: AITask,
    timeout_seconds: int | None,
    fallback_from: str | None = None,
) -> ResolvedClient:
    from learnloop.ai.runtime import AIRuntimeReport

    runtime = runtime_for_provider(vault_root, config, provider_name, task=task)
    client: Any | None = None
    if runtime.ready:
        try:
            client = client_for_provider(
                vault_root,
                config,
                provider_name,
                timeout_seconds=timeout_seconds,
                task=task,
            )
        except AIProviderUnavailable as exc:
            runtime = AIRuntimeReport(
                status="provider_unavailable",
                active_provider=provider_name,
                provider_type=runtime.provider_type,
                model=runtime.model,
                provider_revision=runtime.provider_revision,
                message=str(exc),
            )
    return ResolvedClient(
        selection=selection,
        provider_name=provider_name,
        runtime=runtime,
        client=client,
        fallback_from=fallback_from,
    )


def _manual_resolution(
    selection: AIProviderSelection,
    *,
    fallback_from: str | None = None,
    message: str = "Manual mode selected; AI is disabled for this workflow.",
) -> ResolvedClient:
    from learnloop.ai.runtime import AIRuntimeReport

    runtime = AIRuntimeReport(
        status="provider_unavailable",
        active_provider=MANUAL_PROVIDER,
        message=message,
    )
    return ResolvedClient(
        selection=selection,
        provider_name=MANUAL_PROVIDER,
        runtime=runtime,
        client=None,
        manual=True,
        fallback_from=fallback_from,
    )


__all__ = [
    "DECIDER_ACCEPTING_TASKS",
    "DECIDER_TASKS",
    "EMBEDDING_PROFILE_TYPE",
    "MANUAL_PROVIDER",
    "LIST_ROUTE_TASKS",
    "ROUTE_FOR_OPERATION",
    "AIProviderSelection",
    "AITask",
    "ResolvedClient",
    "TURN_DEADLINE_PROFILE_TYPES",
    "WORKSPACE_PROFILE_TYPES",
    "client_for_provider",
    "fallback_provider_for",
    "is_decider_profile",
    "is_embedding_profile",
    "is_generation_profile",
    "provider_for_operation",
    "provider_for_task",
    "provider_list_for_task",
    "route_names",
    "ready_client_for_task",
    "route_profile_mismatch",
    "runtime_for_provider",
    "serves_read_only_workspace",
]
