"""A Codex (agent-harness) profile is refused for every task.

LearnLoop serves through its own tool-free ChatGPT-plan client and OpenRouter
(owner decisions 2026-10-21: plan-first transport, then retire the Codex code).
The Codex provider is gone, but an old ``learnloop.toml`` may still name a
``codex_sdk`` profile (the Codex app-server) or a legacy ``http`` adapter in
front of it. Such a config must still load and read as a clear refusal rather
than "not configured" or an unsupported type, so the profile types stay in the
schema and every entry that could serve a profile asks this module first: the
client factory, readiness, routing (where a Codex profile is never a
fallback) and the desktop's offered-provider list. `learnloop doctor --fix`
moves a route that pins a Codex profile to the plan profile of the same tier.
"""
from __future__ import annotations

from typing import Any

from learnloop.ai.errors import AIProviderUnavailable
from learnloop.config.schema import AGENT_HARNESS_PROFILE_TYPES


class AgentHarnessRefused(AIProviderUnavailable):
    """A Codex (agent-harness) profile was selected; it serves nothing."""


def is_agent_harness_type(profile_type: str | None) -> bool:
    return (profile_type or "").strip().lower() in AGENT_HARNESS_PROFILE_TYPES


def is_agent_harness_profile(profile: Any) -> bool:
    return profile is not None and is_agent_harness_type(getattr(profile, "type", None))


def refusal_message(provider_name: str) -> str:
    return (
        f"AI provider {provider_name!r} is the Codex agent harness, which LearnLoop no longer uses for "
        "serving (plan-first transport, owner decision 2026-10-21). Use the ChatGPT plan "
        "(`learnloop ai signin chatgpt`; `learnloop doctor --fix` moves pinned Codex routes to it)."
    )


def harness_refusal(provider_name: str, profile: Any) -> str | None:
    """Why ``profile`` may not serve, or ``None`` when it is not a Codex profile."""

    if not is_agent_harness_profile(profile):
        return None
    return refusal_message(provider_name)


def refuse_agent_harness(provider_name: str, profile: Any) -> None:
    """Raise :class:`AgentHarnessRefused` for a Codex profile."""

    message = harness_refusal(provider_name, profile)
    if message is not None:
        raise AgentHarnessRefused(message)


__all__ = [
    "AgentHarnessRefused",
    "harness_refusal",
    "is_agent_harness_profile",
    "is_agent_harness_type",
    "refusal_message",
    "refuse_agent_harness",
]
