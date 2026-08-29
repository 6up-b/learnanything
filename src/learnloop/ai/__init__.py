"""Provider-neutral AI contracts and composition helpers.

Exports are resolved lazily so low-level modules such as ``ai.usage`` do not
bootstrap provider/configuration code merely because a repository imports the
token-usage value object.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

_EXPORTS = {
    "AIProviderClient": ("learnloop.ai.client", "AIProviderClient"),
    "AIProviderSelection": ("learnloop.ai.routing", "AIProviderSelection"),
    "AIRuntimeReport": ("learnloop.ai.runtime", "AIRuntimeReport"),
    "ResolvedClient": ("learnloop.ai.routing", "ResolvedClient"),
    "check_ai_runtime": ("learnloop.ai.runtime", "check_ai_runtime"),
    "fallback_provider_for": ("learnloop.ai.routing", "fallback_provider_for"),
    "make_ai_provider_client": ("learnloop.ai.client", "make_ai_provider_client"),
    "provider_for_task": ("learnloop.ai.routing", "provider_for_task"),
    "ready_client_for_task": ("learnloop.ai.routing", "ready_client_for_task"),
}

__all__ = list(_EXPORTS)


def __getattr__(name: str) -> Any:
    try:
        module_name, attribute = _EXPORTS[name]
    except KeyError as exc:  # pragma: no cover - standard module protocol
        raise AttributeError(name) from exc
    value = getattr(import_module(module_name), attribute)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))
