"""Which configured routes use a ChatGPT-plan profile (config only, no network)."""
from __future__ import annotations

from typing import Any

from learnloop.config import LearnLoopConfig
from learnloop.config.schema import CHATGPT_PLAN_PROFILE_TYPE


def plan_profiles(config: LearnLoopConfig) -> list[dict[str, Any]]:
    """Every ``chatgpt_plan`` profile and the routes that name it.

    ``routes`` lists ``ai.routing`` tasks (a list route counts when any of its
    entries names the profile); ``active_provider`` and ``fallback_provider``
    say whether the unrouted tasks, or the readiness fallback, reach it.
    """

    from learnloop.ai.routing import route_names

    routing = config.ai.routing
    profiles = []
    for name, profile in sorted(config.ai.providers.items()):
        if profile.type != CHATGPT_PLAN_PROFILE_TYPE:
            continue
        routes = [task for task in type(routing).model_fields if name in route_names(getattr(routing, task))]
        active = config.ai.active_provider == name
        fallback = (config.ai.fallback_provider or "") == name
        profiles.append({
            "name": name,
            "model": profile.model,
            "enabled": bool(getattr(profile, "enabled", True)),
            "response_format": getattr(profile, "response_format", None),
            "reasoning_effort": profile.reasoning_effort,
            "usage_limit_pause_minutes": int(getattr(profile, "usage_limit_pause_minutes", 15) or 15),
            "routes": routes,
            "active_provider": active,
            "fallback_provider": fallback,
            "in_use": bool(routes or active or fallback),
        })
    return profiles


__all__ = ["plan_profiles"]
