from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Protocol

from learnloop.ai.codex_sdk import codex_config_from_ai_profile
from learnloop.config import AIProviderConfig, LearnLoopConfig
from learnloop.codex.runtime import check_codex_runtime

AIRuntimeState = Literal[
    "provider_missing_config",
    "provider_auth_required",
    "provider_unavailable",
    "provider_revision_mismatch",
    "ready",
]


class OpenAIChatHealthcheck(Protocol):
    def __call__(self, profile: AIProviderConfig) -> None:
        ...


@dataclass(frozen=True)
class AIRuntimeReport:
    status: AIRuntimeState
    active_provider: str
    provider_type: str | None = None
    model: str | None = None
    provider_revision: str | None = None
    message: str | None = None

    @property
    def ready(self) -> bool:
        return self.status == "ready"

    @property
    def actual_revision(self) -> str | None:
        return self.provider_revision

    def as_dict(self) -> dict[str, str | bool | None]:
        return {
            "status": self.status,
            "ready": self.ready,
            "active_provider": self.active_provider,
            "provider_type": self.provider_type,
            "model": self.model,
            "provider_revision": self.provider_revision,
            "message": self.message,
        }


def check_ai_runtime(
    vault_root: Path,
    config: LearnLoopConfig,
    *,
    provider_name: str | None = None,
    openai_chat_healthcheck: OpenAIChatHealthcheck | None = None,
) -> AIRuntimeReport:
    selected = provider_name or os.environ.get("LEARNLOOP_AI_PROVIDER") or config.ai.active_provider
    profile = config.ai.providers.get(selected)
    if profile is None:
        return AIRuntimeReport(
            status="provider_missing_config",
            active_provider=selected,
            message=f"AI provider {selected!r} is not configured.",
        )
    provider_type = profile.type.lower()
    if provider_type in {"codex_sdk", "http", "http_adapter"}:
        report = check_codex_runtime(vault_root, codex_config_from_ai_profile(profile))
        status_map: dict[str, AIRuntimeState] = {
            "codex_missing": "provider_missing_config",
            "codex_auth_required": "provider_auth_required",
            "codex_unavailable": "provider_unavailable",
            "codex_revision_mismatch": "provider_revision_mismatch",
            "ready": "ready",
        }
        return AIRuntimeReport(
            status=status_map.get(report.status, "provider_unavailable"),
            active_provider=selected,
            provider_type=provider_type,
            model=profile.model,
            provider_revision=report.actual_revision,
            message=report.message,
        )
    if provider_type == "openai_chat":
        api_key_env = profile.api_key_env or "OPENAI_API_KEY"
        if not os.environ.get(api_key_env):
            return AIRuntimeReport(
                status="provider_auth_required",
                active_provider=selected,
                provider_type=provider_type,
                model=profile.model,
                message=f"Environment variable {api_key_env} is required.",
            )
        if openai_chat_healthcheck is not None:
            try:
                openai_chat_healthcheck(profile)
            except Exception as exc:
                return AIRuntimeReport(
                    status="provider_unavailable",
                    active_provider=selected,
                    provider_type=provider_type,
                    model=profile.model,
                    message=str(exc),
                )
        return AIRuntimeReport(
            status="ready",
            active_provider=selected,
            provider_type=provider_type,
            model=profile.model,
            message="AI provider is ready.",
        )
    return AIRuntimeReport(
        status="provider_unavailable",
        active_provider=selected,
        provider_type=provider_type,
        model=profile.model,
        message=f"Unsupported AI provider type {profile.type!r}.",
    )
