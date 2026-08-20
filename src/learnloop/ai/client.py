from __future__ import annotations

from pathlib import Path
from typing import TypeAlias

from learnloop.ai.errors import AIProviderUnavailable
from learnloop.ai.transport import OperationClient
from learnloop.config import AIProviderConfig, LearnLoopConfig

# Compatibility spelling retained for domain type annotations. OperationClient
# is the honest common identity/capability surface shared by structured
# transports and the retained endpoint-bound HTTP adapter; only
# StructuredTransport declares complete().
AIProviderClient: TypeAlias = OperationClient


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
        from learnloop.ai.providers.openai_chat import OpenAIChatProviderClient

        return OpenAIChatProviderClient(provider_name, profile)
    if provider_type == "openrouter":
        from learnloop.ai.providers.openrouter import OpenRouterProviderClient

        return OpenRouterProviderClient(provider_name, profile)
    if provider_type == "codex_sdk":
        from learnloop.ai.providers.codex import CodexSDKProviderClient

        return CodexSDKProviderClient(provider_name, profile, vault_root)
    if provider_type in {"http", "http_adapter"}:
        from learnloop.ai.providers.codex_http import HttpAdapterProviderClient

        return HttpAdapterProviderClient(provider_name, profile)
    raise AIProviderUnavailable(f"Unsupported AI provider type {profile.type!r} for {provider_name!r}")
