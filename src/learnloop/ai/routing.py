"""Provider selection and the single AI client composition root."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Iterator, Literal

from learnloop.ai.errors import AIProviderUnavailable
from learnloop.config import LearnLoopConfig

if TYPE_CHECKING:  # pragma: no cover
    from learnloop.ai.runtime import AIRuntimeReport

MANUAL_PROVIDER = "manual"
EMBEDDING_PROFILE_TYPE = "openai_embedding"

AITask = Literal[
    "embedding",
    "field_question_classifier",
    "field_llm_probability",
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
    # Slice 2 T4: the owner-run contamination report's leak/reveal judge.
    "contamination_judge",
    "grading",
    # Slice 1: the history-aware diagnoser (unset -> the resolved grading
    # route, so a vault that never configures it diagnoses with its grader),
    # the offline review's judge, and its planted-case/probe generator.
    "diagnosis",
    "diagnosis_judge",
    "diagnosis_generator",
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
]

# Every structured operation explicitly inherits one configured task route.
# This is documentation as executable data: feature callers no longer invent
# provider-routing policy from the operation's method name.
ROUTE_FOR_OPERATION: dict[str, AITask] = {
    "field_question_classification": "field_question_classifier",
    "field_llm_probability": "field_llm_probability",
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
    # Slice 2 T4 shadow contamination flags (owner-run report only).
    "contamination_leak_judgment": "contamination_judge",
    "contamination_reveal_judgment": "contamination_judge",
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
        return AIProviderSelection(provider_name=config.ai.routing.embedding or "", explicit=True)
    if task in {"field_question_classifier", "field_llm_probability"}:
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
    embedding_profile = profile.type.strip().lower() == EMBEDDING_PROFILE_TYPE
    if task == "embedding" and not embedding_profile:
        return f"Embedding requires an {EMBEDDING_PROFILE_TYPE} profile; {provider_name!r} is {profile.type!r}."
    if task != "embedding" and embedding_profile:
        return (
            f"{provider_name!r} is an embedding-only profile; it cannot serve "
            f"{task or 'generation'} work."
        )
    return None


def is_embedding_profile(config: LearnLoopConfig, provider_name: str) -> bool:
    profile = config.ai.providers.get(provider_name)
    return profile is not None and profile.type.strip().lower() == EMBEDDING_PROFILE_TYPE


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
    provider_timeout = (
        timeout_seconds
        if profile is not None and profile.type.strip().lower() == "codex_sdk"
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
    if primary.runtime.ready or task == "embedding":
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
    "EMBEDDING_PROFILE_TYPE",
    "MANUAL_PROVIDER",
    "LIST_ROUTE_TASKS",
    "ROUTE_FOR_OPERATION",
    "AIProviderSelection",
    "AITask",
    "ResolvedClient",
    "client_for_provider",
    "fallback_provider_for",
    "is_embedding_profile",
    "provider_for_operation",
    "provider_for_task",
    "provider_list_for_task",
    "route_names",
    "ready_client_for_task",
    "route_profile_mismatch",
    "runtime_for_provider",
]
