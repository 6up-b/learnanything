from __future__ import annotations

from pathlib import Path
from typing import Protocol

from learnloop.config import AIProviderConfig, LearnLoopConfig
from learnloop.codex.client import AuthoringContext, CanonicalIngestContext, CodexUnavailable, GradingContext
from learnloop.codex.schemas import AuthoringProposal, GradingProposal


class AIProviderClient(Protocol):
    provider_name: str
    provider_type: str
    model: str | None

    def run_authoring_proposal(self, context: AuthoringContext) -> AuthoringProposal:
        ...

    def run_canonical_ingest(self, context: CanonicalIngestContext) -> AuthoringProposal:
        ...

    def run_grading_proposal(self, context: GradingContext) -> GradingProposal:
        ...


class AIProviderUnavailable(CodexUnavailable):
    pass


def make_ai_provider_client(
    config: LearnLoopConfig,
    vault_root: Path,
    *,
    provider_name: str | None = None,
) -> AIProviderClient:
    selected = provider_name or config.ai.active_provider
    profile = config.ai.providers.get(selected)
    if profile is None:
        raise AIProviderUnavailable(f"AI provider {selected!r} is not configured")
    if profile.timeout_seconds is None:
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
    if provider_type == "codex_sdk":
        from learnloop.ai.codex_sdk import CodexSDKProviderClient

        return CodexSDKProviderClient(provider_name, profile, vault_root)
    if provider_type in {"http", "http_adapter"}:
        from learnloop.ai.codex_sdk import HttpAdapterProviderClient

        return HttpAdapterProviderClient(provider_name, profile)
    raise AIProviderUnavailable(f"Unsupported AI provider type {profile.type!r} for {provider_name!r}")
