from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Protocol

from learnloop.ai.providers.codex import check_codex_runtime, codex_config_from_ai_profile
from learnloop.config import AIProviderConfig, LearnLoopConfig

AIRuntimeState = Literal[
    "provider_missing_config",
    "provider_auth_required",
    "provider_unavailable",
    "provider_revision_mismatch",
    "ready",
]

_CODEX_COMPAT_STATUS: dict[str, str] = {
    "provider_missing_config": "codex_missing",
    "provider_auth_required": "codex_auth_required",
    "provider_unavailable": "codex_unavailable",
    "provider_revision_mismatch": "codex_revision_mismatch",
}


def legacy_codex_status(status: str) -> str:
    """Translate a neutral runtime state at a legacy Codex-facing boundary.

    Internal routing and new provider-generic APIs use ``provider_*`` states.
    Existing CLI result/error fields predate that vocabulary and remain stable
    unless a separately versioned protocol change is declared.
    """

    return _CODEX_COMPAT_STATUS.get(status, status)


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
    if provider_type in {"openai_chat", "openrouter", "openai_embedding"}:
        if provider_type == "openai_embedding":
            profile = profile.model_copy(update={"model": config.embedding.model})
        default_env = "OPENROUTER_API_KEY" if provider_type in {"openrouter", "openai_embedding"} else "OPENAI_API_KEY"
        api_key_env = profile.api_key_env or default_env
        if not os.environ.get(api_key_env):
            return AIRuntimeReport(
                status="provider_auth_required",
                active_provider=selected,
                provider_type=provider_type,
                model=profile.model,
                message=f"Environment variable {api_key_env} is required.",
            )
        if openai_chat_healthcheck is not None and provider_type != "openai_embedding":
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
    if provider_type == "decider":
        # Key presence only: readiness never sends learner text or pays. The
        # model's reachability is a separate, explicit network probe
        # (ai.providers.decider.probe_decider_endpoint).
        from learnloop.ai.providers.decider import resolved_decider_settings

        settings = resolved_decider_settings(profile)
        if not os.environ.get(settings.api_key_env):
            return AIRuntimeReport(
                status="provider_auth_required",
                active_provider=selected,
                provider_type=provider_type,
                model=settings.model,
                message=f"Environment variable {settings.api_key_env} is required.",
            )
        return AIRuntimeReport(
            status="ready",
            active_provider=selected,
            provider_type=provider_type,
            model=settings.model,
            message="Decision model key is present.",
        )
    if provider_type == "chatgpt_plan":
        return _chatgpt_plan_runtime(selected, profile)
    return AIRuntimeReport(
        status="provider_unavailable",
        active_provider=selected,
        provider_type=provider_type,
        model=profile.model,
        message=f"Unsupported AI provider type {profile.type!r}.",
    )


_CHATGPT_PLAN_STATES: dict[str, AIRuntimeState] = {
    "ready": "ready",
    "signed_out": "provider_auth_required",
    "plan_usage_disabled": "provider_auth_required",
    "store_error": "provider_auth_required",
    "not_eligible": "provider_unavailable",
    "usage_exhausted": "provider_unavailable",
}


def _chatgpt_plan_runtime(selected: str, profile: AIProviderConfig) -> AIRuntimeReport:
    """Local files only: the profile, the machine's sign-in and its pause state.

    Readiness never refreshes a token or sends a request. An expired access
    token with a refresh token is ready (the call refreshes it).
    """

    from learnloop.ai.chatgpt_plan.session import PlanSession

    def report(status: AIRuntimeState, message: str) -> AIRuntimeReport:
        return AIRuntimeReport(status=status, active_provider=selected, provider_type="chatgpt_plan",
                               model=profile.model, message=message)

    if not profile.model:
        return report("provider_missing_config",
                      f"AI provider {selected!r} needs a model; pick one from `learnloop ai models chatgpt`.")
    if getattr(profile, "enabled", True) is False:
        return report("provider_unavailable", f"AI provider {selected!r} is disabled (enabled = false).")
    pause = int(getattr(profile, "usage_limit_pause_minutes", None) or 15)
    state, message = PlanSession().status().readiness(pause_minutes=pause)
    return report(_CHATGPT_PLAN_STATES.get(state, "provider_unavailable"), message)
