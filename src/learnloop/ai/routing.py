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

AITask = Literal[
    "grading",
    "canonical_ingest",
    "canonical_ingest_retry",
    "authoring",
    "tutor_qa",
    "teach_back",
    "rung_variant",
    "animation",
    "transcription",
]

# Every structured operation explicitly inherits one configured task route.
# This is documentation as executable data: feature callers no longer invent
# provider-routing policy from the operation's method name.
ROUTE_FOR_OPERATION: dict[str, AITask] = {
    "authoring_proposal": "authoring",
    "canonical_ingest": "canonical_ingest",
    "grading_proposal": "grading",
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
    "append_reconciliation": "canonical_ingest",
    "media_transcription": "transcription",
    "media_markdown": "canonical_ingest",
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
    env_provider = os.environ.get("LEARNLOOP_AI_PROVIDER") if allow_env else None
    if env_provider:
        return AIProviderSelection(provider_name=env_provider, from_env=True)
    routed = getattr(config.ai.routing, task, None)
    if task == "canonical_ingest_retry" and not routed:
        return AIProviderSelection(provider_name="")
    return AIProviderSelection(provider_name=routed or config.ai.active_provider)


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


def runtime_for_provider(
    vault_root: Path,
    config: LearnLoopConfig,
    provider_name: str,
) -> AIRuntimeReport:
    """Return one provider-neutral readiness report for any configured name."""

    from learnloop.ai.runtime import AIRuntimeReport, check_ai_runtime

    if provider_name in {"", MANUAL_PROVIDER}:
        return AIRuntimeReport(
            status="provider_unavailable",
            active_provider=MANUAL_PROVIDER,
            message="Manual mode selected; AI is disabled for this workflow.",
        )
    return check_ai_runtime(vault_root, config, provider_name=provider_name)


def client_for_provider(
    vault_root: Path,
    config: LearnLoopConfig,
    provider_name: str,
    *,
    timeout_seconds: int | None = None,
) -> Any | None:
    """Build a configured provider client, returning no client for manual mode."""

    if provider_name in {"", MANUAL_PROVIDER}:
        return None
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
    if selection.provider_name in {"", MANUAL_PROVIDER}:
        return _manual_resolution(selection)

    primary = _resolve_selected_provider(
        vault_root,
        config,
        selection,
        selection.provider_name,
        timeout_seconds=timeout_seconds,
    )
    if primary.runtime.ready:
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
    timeout_seconds: int | None,
    fallback_from: str | None = None,
) -> ResolvedClient:
    from learnloop.ai.runtime import AIRuntimeReport

    runtime = runtime_for_provider(vault_root, config, provider_name)
    client: Any | None = None
    if runtime.ready:
        try:
            client = client_for_provider(
                vault_root,
                config,
                provider_name,
                timeout_seconds=timeout_seconds,
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
) -> ResolvedClient:
    from learnloop.ai.runtime import AIRuntimeReport

    runtime = AIRuntimeReport(
        status="provider_unavailable",
        active_provider=MANUAL_PROVIDER,
        message="Manual mode selected; AI is disabled for this workflow.",
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
    "MANUAL_PROVIDER",
    "ROUTE_FOR_OPERATION",
    "AIProviderSelection",
    "AITask",
    "ResolvedClient",
    "client_for_provider",
    "fallback_provider_for",
    "provider_for_operation",
    "provider_for_task",
    "ready_client_for_task",
    "runtime_for_provider",
]
