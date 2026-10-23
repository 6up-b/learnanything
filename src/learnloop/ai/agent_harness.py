"""The Codex agent harness is refused for serving unless the owner opts in.

Plan-first transport T1 (owner decision 2026-10-21, after four security
verifies of the Codex lockdown kept finding agent-harness features): every
serving route uses LearnLoop's own tool-free ChatGPT-plan client. A
``codex_sdk`` profile (the Codex app-server) or a legacy ``http`` adapter
profile in front of it is refused, for every task, unless
``ai.agent_harness_opt_in = true``, and it is never a fallback
(:func:`learnloop.ai.routing.fallback_provider_for`). The refusal happens
before any client is built or any Codex process (health check, app-server,
bubblewrap) starts: in the client factory, in readiness and in routing.

The frozen Codex modules (``providers/codex.py``, ``codex_lockdown.py``,
``codex_http.py``) stay reachable only through the opt-in until T2 retires
them.
"""
from __future__ import annotations

from typing import Any

from learnloop.ai.errors import AIProviderUnavailable
from learnloop.config.schema import AGENT_HARNESS_PROFILE_TYPES

OPT_IN_SETTING = "ai.agent_harness_opt_in"


class AgentHarnessRefused(AIProviderUnavailable):
    """A Codex (agent-harness) profile was selected without the owner's opt-in."""


def is_agent_harness_type(profile_type: str | None) -> bool:
    return (profile_type or "").strip().lower() in AGENT_HARNESS_PROFILE_TYPES


def is_agent_harness_profile(profile: Any) -> bool:
    return profile is not None and is_agent_harness_type(getattr(profile, "type", None))


def refusal_message(provider_name: str) -> str:
    return (
        f"AI provider {provider_name!r} is the Codex agent harness, which LearnLoop no longer uses for "
        "serving (plan-first transport, owner decision 2026-10-21). Use the ChatGPT plan "
        "(`learnloop ai signin chatgpt`; `learnloop doctor --fix` moves pinned Codex routes to it), or set "
        f"{OPT_IN_SETTING} = true to opt in to Codex explicitly."
    )


def harness_refusal(provider_name: str, profile: Any, *, opt_in: bool) -> str | None:
    """Why ``profile`` may not serve, or ``None`` when it may (not Codex, or opted in)."""

    if opt_in or not is_agent_harness_profile(profile):
        return None
    return refusal_message(provider_name)


def require_harness_opt_in(provider_name: str, profile: Any, *, opt_in: bool) -> None:
    """Raise :class:`AgentHarnessRefused` for a Codex profile without the opt-in."""

    message = harness_refusal(provider_name, profile, opt_in=opt_in)
    if message is not None:
        raise AgentHarnessRefused(message)


__all__ = [
    "AgentHarnessRefused",
    "OPT_IN_SETTING",
    "harness_refusal",
    "is_agent_harness_profile",
    "is_agent_harness_type",
    "refusal_message",
    "require_harness_opt_in",
]
