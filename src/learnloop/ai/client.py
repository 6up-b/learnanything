from __future__ import annotations

from pathlib import Path
from typing import Protocol

from learnloop.config import AIProviderConfig, LearnLoopConfig
from learnloop.codex.client import (
    AuthoringContext,
    CanonicalIngestContext,
    CodexUnavailable,
    GradingContext,
    TeachBackAuthoringContext,
)
from learnloop.codex.schemas import AuthoringProposal, GradingProposal, TeachBackAuthoring
from learnloop.token_usage import TokenUsage


class AIProviderClient(Protocol):
    provider_name: str
    provider_type: str
    model: str | None

    def consume_usage(self) -> TokenUsage:
        """Read-and-reset this client's accumulated provider-reported usage.

        Part of the seam A7 (spec_diagnostic_augmentation_v1.md §2) needs: one
        agent run is several model calls, so cost is accumulated per client and
        drained once when the run is finalized (see
        `learnloop.services.agent_runs.finish_agent_run`). Every concrete client
        inherits it from `learnloop.token_usage.TokenUsageAccounting`; service
        code that may hold a stub should go through `consume_client_usage`
        rather than calling this directly.
        """
        ...

    def run_authoring_proposal(self, context: AuthoringContext) -> AuthoringProposal:
        ...

    def run_canonical_ingest(self, context: CanonicalIngestContext) -> AuthoringProposal:
        ...

    def run_grading_proposal(self, context: GradingContext) -> GradingProposal:
        ...

    def run_teach_back_authoring(self, context: TeachBackAuthoringContext) -> TeachBackAuthoring:
        ...


class AIProviderUnavailable(CodexUnavailable):
    pass


def make_ai_provider_client(
    config: LearnLoopConfig,
    vault_root: Path,
    *,
    provider_name: str | None = None,
    timeout_seconds: int | None = None,
) -> AIProviderClient:
    selected = provider_name or config.ai.active_provider
    profile = config.ai.providers.get(selected)
    if profile is None:
        raise AIProviderUnavailable(f"AI provider {selected!r} is not configured")
    if timeout_seconds is not None:
        profile = profile.model_copy(update={"timeout_seconds": timeout_seconds})
    elif profile.timeout_seconds is None:
        profile = profile.model_copy(update={"timeout_seconds": config.ai.timeout_seconds})
    return make_ai_provider_client_from_profile(selected, profile, vault_root)


def make_ai_provider_client_from_profile(
    provider_name: str,
    profile: AIProviderConfig,
    vault_root: Path,
) -> AIProviderClient:
    provider_type = profile.type.lower()
    if provider_type == "openai_chat":
        from learnloop.ai.openai_chat import OpenAIChatProviderClient

        return OpenAIChatProviderClient(provider_name, profile)
    if provider_type == "openrouter":
        from learnloop.ai.openrouter import OpenRouterProviderClient

        return OpenRouterProviderClient(provider_name, profile)
    if provider_type == "codex_sdk":
        from learnloop.ai.codex_sdk import CodexSDKProviderClient

        return CodexSDKProviderClient(provider_name, profile, vault_root)
    if provider_type in {"http", "http_adapter"}:
        from learnloop.ai.codex_sdk import HttpAdapterProviderClient

        return HttpAdapterProviderClient(provider_name, profile)
    raise AIProviderUnavailable(f"Unsupported AI provider type {profile.type!r} for {provider_name!r}")
