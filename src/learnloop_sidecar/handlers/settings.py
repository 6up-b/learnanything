"""Settings RPCs for AI routing and the machine-global OpenRouter API key."""

from __future__ import annotations

import os
from typing import Any

from learnloop.ai.runtime import check_ai_runtime
from learnloop.config import CODEX_PROVIDER_NAMES, global_settings_path
from learnloop.services.settings_store import (
    USE_CASE_ROUTES,
    SettingsStoreError,
    apply_config_updates,
    openrouter_profile_name,
    openrouter_task_profile_values,
    upsert_env_var,
)
from learnloop_sidecar.context import SidecarContext, runtime_health
from learnloop_sidecar.dto import EmptyParams, ParamsModel, versioned
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.registry import method

OPENROUTER_KEY_ENV = "OPENROUTER_API_KEY"

_ROUTING_TASKS = (
    "grading",
    "canonical_ingest",
    "canonical_ingest_retry",
    "authoring",
    "tutor_qa",
    "teach_back",
    "rung_variant",
)


def _key_state(env_name: str) -> dict[str, Any]:
    value = os.environ.get(env_name) or ""
    return {
        "key_present": bool(value),
        "key_hint": value[-4:] if len(value) >= 8 else ("set" if value else None),
    }


def _settings_payload(ctx: SidecarContext) -> dict[str, Any]:
    vault, _repository = ctx.require_vault()
    config = vault.config
    # Keep provider names as values in a list: ``versioned`` camelizes mapping
    # keys and would otherwise rewrite names such as openrouter_grading.
    providers = [
        {
            "name": name,
            "type": profile.type,
            "model": profile.model,
            "base_url": profile.base_url,
            "api_key_env": profile.api_key_env,
        }
        for name, profile in sorted(config.ai.providers.items())
    ]
    return {
        "ai": {
            "active_provider": config.ai.active_provider,
            "fallback_provider": config.ai.fallback_provider,
            "routing": {task: getattr(config.ai.routing, task) for task in _ROUTING_TASKS},
            "use_cases": sorted(USE_CASE_ROUTES),
            "providers": providers,
            "env_provider_override": os.environ.get("LEARNLOOP_AI_PROVIDER") or None,
        },
        "openrouter": {
            **_key_state(OPENROUTER_KEY_ENV),
            "settings_env_path": str(global_settings_path()),
        },
    }


@method("get_settings", EmptyParams)
def get_settings(ctx: SidecarContext, _params: EmptyParams) -> dict[str, Any]:
    return versioned(_settings_payload(ctx))


class UseCaseChoice(ParamsModel):
    provider: str
    openrouter_model: str | None = None


class UpdateAiSettingsParams(ParamsModel):
    active_provider: str | None = None
    use_cases: dict[str, UseCaseChoice] | None = None


def _validate_model_slug(slug: str) -> str:
    cleaned = slug.strip()
    if not cleaned or any(ch.isspace() for ch in cleaned) or any(ord(ch) < 32 for ch in cleaned):
        raise SidecarError("invalid_model", f"invalid OpenRouter model slug {slug!r}")
    return cleaned


@method("update_ai_settings", UpdateAiSettingsParams)
def update_ai_settings(ctx: SidecarContext, params: UpdateAiSettingsParams) -> dict[str, Any]:
    """Persist provider/model choices and return refreshed runtime health."""

    vault, _repository = ctx.require_vault()
    config = vault.config
    known_providers = set(config.ai.providers) | CODEX_PROVIDER_NAMES
    updates: dict[tuple[str, ...], Any] = {}

    if params.active_provider is not None:
        if params.active_provider not in known_providers:
            raise SidecarError(
                "invalid_provider",
                (
                    f"Unknown provider {params.active_provider!r}. "
                    f"Configured: {', '.join(sorted(known_providers))}."
                ),
            )
        updates[("ai", "active_provider")] = params.active_provider

    grading_changed = False
    for use_case, choice in (params.use_cases or {}).items():
        routes = USE_CASE_ROUTES.get(use_case)
        if routes is None:
            raise SidecarError(
                "invalid_use_case",
                f"Unknown use case {use_case!r}. Valid: {', '.join(sorted(USE_CASE_ROUTES))}.",
            )
        if choice.provider == "openrouter":
            model = _validate_model_slug(choice.openrouter_model or "")
            profile_name = openrouter_profile_name(use_case)
            base = config.ai.providers.get("openrouter")
            if base is None:
                raise SidecarError("invalid_provider", "No openrouter profile is configured.")
            for key, value in openrouter_task_profile_values(base, model).items():
                updates[("ai", "providers", profile_name, key)] = value
            target = profile_name
        else:
            if choice.provider not in known_providers:
                raise SidecarError(
                    "invalid_provider",
                    f"Unknown provider {choice.provider!r} for use case {use_case!r}.",
                )
            target = choice.provider
        for task in routes:
            updates[("ai", "routing", task)] = target
        if use_case == "grading":
            grading_changed = True

    if updates:
        try:
            apply_config_updates(vault.root / "learnloop.toml", updates)
        except SettingsStoreError as exc:
            raise SidecarError(exc.code, str(exc)) from exc
        ctx.reload(maintenance=False)
        if grading_changed:
            # A runtime-only grading choice would otherwise shadow the newly
            # persisted route.
            ctx.grading_provider_override = None

    vault, repository = ctx.require_vault()
    payload = _settings_payload(ctx)
    payload["health"] = runtime_health(
        vault,
        repository,
        grading_override=ctx.grading_provider_override,
    )
    return versioned(payload)


class SetOpenrouterApiKeyParams(ParamsModel):
    api_key: str


@method("set_openrouter_api_key", SetOpenrouterApiKeyParams)
def set_openrouter_api_key(
    ctx: SidecarContext,
    params: SetOpenrouterApiKeyParams,
) -> dict[str, Any]:
    vault, _repository = ctx.require_vault()
    value = params.api_key.strip()
    if len(value) > 512 or any(ord(ch) < 32 for ch in value):
        raise SidecarError(
            "invalid_api_key",
            "API key contains control characters or is too long.",
        )

    path = global_settings_path()
    try:
        upsert_env_var(path, OPENROUTER_KEY_ENV, value or None)
    except SettingsStoreError as exc:
        raise SidecarError(exc.code, str(exc)) from exc
    if value:
        os.environ[OPENROUTER_KEY_ENV] = value
    else:
        os.environ.pop(OPENROUTER_KEY_ENV, None)

    report = check_ai_runtime(vault.root, vault.config, provider_name="openrouter")
    return versioned(
        {
            **_key_state(OPENROUTER_KEY_ENV),
            "settings_env_path": str(path),
            "ready": report.ready,
            "status": report.status,
        }
    )
