from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Literal

from learnloop.config import LearnLoopConfig

AITask = Literal[
    "grading", "canonical_ingest", "canonical_ingest_retry", "authoring", "tutor_qa", "teach_back",
    # Learner-requested easier/harder sibling authoring: small, instruction-
    # constrained, gate-checked — routed to the fast low-effort profile so the
    # request feels interactive rather than riding the synthesis route.
    "rung_variant",
]


@dataclass(frozen=True)
class AIProviderSelection:
    provider_name: str
    explicit: bool = False
    from_env: bool = False

    @property
    def uses_legacy_codex(self) -> bool:
        return self.provider_name == "codex"


def provider_for_task(
    config: LearnLoopConfig,
    task: AITask,
    *,
    explicit_provider: str | None = None,
    allow_env: bool = True,
) -> AIProviderSelection:
    if explicit_provider:
        return AIProviderSelection(provider_name=explicit_provider, explicit=True)
    env_provider = os.environ.get("LEARNLOOP_AI_PROVIDER") if allow_env else None
    if env_provider:
        return AIProviderSelection(provider_name=env_provider, from_env=True)
    routed = getattr(config.ai.routing, task, None)
    if task == "canonical_ingest_retry" and not routed:
        return AIProviderSelection(provider_name="")
    return AIProviderSelection(provider_name=routed or config.ai.active_provider)


def fallback_provider_for(config: LearnLoopConfig, selection: AIProviderSelection) -> str | None:
    fallback = (config.ai.fallback_provider or "").strip() or None
    if selection.explicit or selection.from_env or fallback == selection.provider_name:
        return None
    return fallback
