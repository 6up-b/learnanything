from __future__ import annotations

from pathlib import Path
from typing import Any, TypeAlias

from learnloop.ai import model_use
from learnloop.ai.agent_harness import refuse_agent_harness
from learnloop.ai.errors import AIProviderUnavailable
from learnloop.ai.transport import OperationClient
from learnloop.config import AIProviderConfig, LearnLoopConfig

# Compatibility spelling retained for domain type annotations. OperationClient
# is the common identity/capability surface of every transport; only
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
    if profile.type == "openai_embedding":
        profile = profile.model_copy(update={
            "model": config.embedding.model,
            "dimensions": config.embedding.dimensions,
        })
    idle_timeout = profile.timeout_seconds or config.ai.timeout_seconds
    if timeout_seconds is not None:
        profile = profile.model_copy(update={"timeout_seconds": timeout_seconds})
    elif profile.timeout_seconds is None:
        profile = profile.model_copy(update={"timeout_seconds": config.ai.timeout_seconds})
    return make_ai_provider_client_from_profile(selected, profile, vault_root, idle_timeout_seconds=idle_timeout)


def make_ai_provider_client_from_profile(
    provider_name: str,
    profile: AIProviderConfig,
    vault_root: Path,
    *,
    idle_timeout_seconds: float | None = None,
) -> AIProviderClient:
    """Build one client for ``profile``: the single AI client factory.

    Every client it builds carries the live lookup of the learner's one OK for
    the library at ``vault_root`` (:func:`learnloop.ai.model_use.bind`): none of
    its requests is sent before that OK, whichever thread or job sends it.

    A Codex agent-harness profile (``codex_sdk``, legacy ``http``) an old
    config may still name is refused here with the clear message, not
    reported as an unsupported type.
    """

    refuse_agent_harness(provider_name, profile)
    provider_type = profile.type.lower()
    if provider_type == "openai_embedding":
        from learnloop.ai.providers.openai_embedding import OpenAIEmbeddingProviderClient

        return model_use.bind(OpenAIEmbeddingProviderClient(provider_name, profile), vault_root)
    if provider_type == "voyage_contextual_embedding":
        from learnloop.ai.providers.voyage_contextual import VoyageContextualClient

        return model_use.bind(VoyageContextualClient(provider_name, profile), vault_root)
    if provider_type == "openai_chat":
        from learnloop.ai.providers.openai_chat import OpenAIChatProviderClient

        return model_use.bind(OpenAIChatProviderClient(provider_name, profile), vault_root)
    if provider_type == "openrouter":
        from learnloop.ai.providers.openrouter import OpenRouterProviderClient

        return model_use.bind(OpenRouterProviderClient(provider_name, profile), vault_root)
    if provider_type == "decider":
        from learnloop.ai.providers.decider import DeciderProviderClient

        return model_use.bind(DeciderProviderClient(provider_name, profile), vault_root)
    if provider_type == "chatgpt_plan":
        from learnloop.ai.providers.chatgpt_plan import ChatGPTPlanProviderClient

        client = ChatGPTPlanProviderClient(provider_name, profile, idle_timeout_seconds=idle_timeout_seconds)
        return model_use.bind(client, vault_root)
    raise AIProviderUnavailable(f"Unsupported AI provider type {profile.type!r} for {provider_name!r}")


def make_video_generation_client(
    config: LearnLoopConfig,
    vault_root: Path,
    *,
    provider_name: str,
    http: Any = None,
) -> Any:
    """Build the text-to-video client for an OpenRouter profile.

    Video generation is not a chat completion: it reuses the OpenRouter profile
    (key env, base URL, attribution headers) but talks to the async
    ``/api/v1/videos`` job API. Only ``openrouter``-type profiles qualify; no
    new profile type is introduced, so runtime readiness checks already cover
    the key."""

    profile = config.ai.providers.get(provider_name)
    if profile is None:
        raise AIProviderUnavailable(f"video provider {provider_name!r} is not configured")
    if profile.type.lower() != "openrouter":
        raise AIProviderUnavailable(
            "video generation requires an OpenRouter profile; choose a video model in Settings → Animation"
        )
    from learnloop.ai.providers.openrouter_video import OpenRouterVideoClient

    return model_use.bind(OpenRouterVideoClient(provider_name, profile, http=http), vault_root)
