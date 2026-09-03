"""Settings tab RPCs: read and persist AI model routing, the OpenRouter API
key, and (in later slices) ingestion preferences.

Persistence rules:
- Model/provider choices go into the per-vault ``learnloop.toml`` through
  ``learnloop.ops.settings_store`` (comment-preserving, atomic), then
  ``ctx.reload(maintenance=False)`` re-reads config.
- Secrets go into the machine-global ``settings.env`` — never the committed
  vault config — and are ALSO written straight into ``os.environ`` because
  ``load_dotenv`` never overwrites an existing key, so a reload alone would
  keep a stale value alive until process restart.
- Responses never echo a saved key; only presence plus a last-4 hint.
"""

from __future__ import annotations

import logging
import os
from typing import Any

from learnloop.ai.runtime import check_ai_runtime
from learnloop.content.authoring.concept_animation import video_generation_readiness
from learnloop.config import CODEX_PROVIDER_NAMES, global_ai_defaults_path, global_settings_path
from learnloop.ops.settings_store import (
    USE_CASE_ROUTES,
    SettingsStoreError,
    apply_config_updates,
    openrouter_profile_name,
    openrouter_task_profile_values,
    save_ai_settings_to,
    upsert_env_var,
)

logger = logging.getLogger(__name__)
from learnloop_sidecar.context import SidecarContext, runtime_health
from learnloop_sidecar.dto import EmptyParams, ParamsModel, versioned
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.handlers.ingest import (
    BUDGET_BOUNDS,
    PLAN_BUDGET_FIELDS,
    validated_budget_overrides,
)
from learnloop_sidecar.registry import method

OPENROUTER_KEY_ENV = "OPENROUTER_API_KEY"

# [animation] render settings the Settings tab edits.
ANIMATION_QUALITY_OPTIONS = ("ql", "qm", "qh")
ANIMATION_RENDERER_OPTIONS = ("manim", "video_model")
ANIMATION_SHOT_BOUNDS = (1, 6)
ANIMATION_DURATION_BOUNDS = (15, 180)
ANIMATION_TIMEOUT_BOUNDS = (60, 3600)

_ROUTING_TASKS = (
    "grading",
    "canonical_ingest",
    "canonical_ingest_retry",
    "authoring",
    "tutor_qa",
    "teach_back",
    "rung_variant",
    "animation",
    "transcription",
    "video_generation",
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
    # Providers are a LIST of {name, ...} objects: versioned()/to_camel
    # camelizes every dict key, which would mangle names like
    # "openrouter_grading" if they were used as keys.
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
        "ingest": {
            # Transitional: true when either modality is routed natively.
            "native_multimodal": (
                config.ingest.audio.mode == "native" or config.ingest.pdf.engine == "native"
            ),
            "transcription_provider": config.ingest.audio.provider,
            "transcription_model": config.ingest.audio.transcription_model,
            "transcription_base_url": config.ingest.audio.transcription_base_url,
            "transcription_key": _key_state(config.ingest.audio.transcription_api_key_env),
            "budgets": {
                field: getattr(config.ingest.budgets, field) for field in PLAN_BUDGET_FIELDS
            },
            # Accepted range per ceiling, so the UI validates with the same
            # numbers the handler enforces instead of its own copies.
            "budget_bounds": {
                field: {"min": BUDGET_BOUNDS[field][0], "max": BUDGET_BOUNDS[field][1]}
                for field in PLAN_BUDGET_FIELDS
            },
            "provider_limits": _provider_limits(config),
        },
        "animation": {
            "enabled": config.animation.enabled,
            "renderer": config.animation.renderer,
            "renderer_options": list(ANIMATION_RENDERER_OPTIONS),
            # Readiness of the video-model renderer (route + key), no network.
            "video": {
                **video_generation_readiness(config, vault.root),
                "max_shots": config.animation.video_max_shots,
                "timeout_seconds": config.animation.video_timeout_seconds,
                "resolution": config.animation.video_resolution,
            },
            "quality": config.animation.quality,
            "quality_options": list(ANIMATION_QUALITY_OPTIONS),
            "min_duration_seconds": config.animation.min_duration_seconds,
            "max_duration_seconds": config.animation.max_duration_seconds,
            "timeout_seconds": config.animation.timeout_seconds,
            # Accepted ranges, so the UI validates with the handler's numbers.
            "duration_bounds": {"min": ANIMATION_DURATION_BOUNDS[0], "max": ANIMATION_DURATION_BOUNDS[1]},
            "timeout_bounds": {"min": ANIMATION_TIMEOUT_BOUNDS[0], "max": ANIMATION_TIMEOUT_BOUNDS[1]},
        },
    }


def _ingest_provider_name(config) -> str:
    """The provider the build plan measures its ceilings against (§3.1)."""

    return config.ai.routing.canonical_ingest or config.ai.active_provider


def _provider_limits(config) -> dict[str, Any]:
    """`[ingest.providers.<routed>]` context/output limits.

    These are commented out in the default config, which leaves the build plan
    with no context number and silently disables its overflow checks — so the
    payload always names the provider whose block needs filling in."""

    provider = _ingest_provider_name(config)
    limits = config.ingest.providers.get(provider)
    return {
        "provider": provider,
        "context_tokens": limits.context_tokens if limits else None,
        "max_output_tokens": limits.max_output_tokens if limits else None,
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
    """Persist provider/model choices to learnloop.toml and reload.

    A use-case choosing provider "openrouter" with a model slug materializes a
    per-use-case profile (openrouter_<usecase>) cloned from the seeded
    openrouter profile so different tasks can run different OpenRouter models.
    """

    vault, _repository = ctx.require_vault()
    config = vault.config
    known_providers = set(config.ai.providers) | CODEX_PROVIDER_NAMES
    updates: dict[tuple[str, ...], Any] = {}

    if params.active_provider is not None:
        if params.active_provider not in known_providers:
            raise SidecarError(
                "invalid_provider",
                f"Unknown provider {params.active_provider!r}. Configured: {', '.join(sorted(known_providers))}.",
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
        if use_case == "video" and choice.provider != "openrouter":
            raise SidecarError(
                "invalid_provider",
                "Video generation runs only through an OpenRouter video model (provider \"openrouter\").",
            )
        if choice.provider == "openrouter":
            model = _validate_model_slug(choice.openrouter_model or "")
            if use_case == "video" and "/" not in model:
                raise SidecarError("invalid_model", 'Video models are OpenRouter slugs like "google/veo-3.1".')
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
        config_path = vault.root / "learnloop.toml"
        try:
            apply_config_updates(config_path, updates)
        except SettingsStoreError as exc:
            raise SidecarError(exc.code, str(exc))
        ctx.reload(maintenance=False)
        # Mirror the persisted [ai] selection into the machine-global defaults so
        # a later new vault (created with none open) inherits this backend
        # instead of falling back to the codex template. Best-effort.
        try:
            save_ai_settings_to(config_path, global_ai_defaults_path())
        except SettingsStoreError as exc:
            logger.warning("could not persist global AI defaults: %s", exc)
        if grading_changed:
            # The session-only override survives reloads and would silently
            # shadow the freshly persisted grading route.
            ctx.grading_provider_override = None

    vault, repository = ctx.require_vault()
    payload = _settings_payload(ctx)
    payload["health"] = runtime_health(
        vault, repository, grading_override=ctx.grading_provider_override
    )
    return versioned(payload)


class UpdateIngestSettingsParams(ParamsModel):
    native_multimodal: bool | None = None
    transcription_provider: str | None = None
    transcription_model: str | None = None
    transcription_base_url: str | None = None
    # Durable `[ingest.budgets]` defaults. Omitted fields are left untouched, so
    # the UI can apply one row at a time.
    budgets: dict[str, int] | None = None
    # `[ingest.providers.<routed>]` limits. Omit a field to leave it as-is; there
    # is no clear (the config writer sets keys, it cannot remove them).
    provider_context_tokens: int | None = None
    provider_max_output_tokens: int | None = None


TRANSCRIPTION_PROVIDERS = ("openai_compatible", "openrouter")


@method("update_ingest_settings", UpdateIngestSettingsParams)
def update_ingest_settings(ctx: SidecarContext, params: UpdateIngestSettingsParams) -> dict[str, Any]:
    vault, _repository = ctx.require_vault()
    updates: dict[tuple[str, ...], Any] = {}
    if params.native_multimodal is not None:
        # Transitional shim over the per-modality authorities: on routes both
        # PDF and audio natively; off restores local PDF extraction only when
        # native was the selected engine (an explicit marker/pypdf choice stays).
        updates[("ingest", "audio", "mode")] = "native" if params.native_multimodal else "transcription"
        if params.native_multimodal:
            updates[("ingest", "pdf", "engine")] = "native"
        elif vault.config.ingest.pdf.engine == "native":
            updates[("ingest", "pdf", "engine")] = "auto"
    provider: str | None = None
    if params.transcription_provider is not None:
        provider = params.transcription_provider.strip().lower()
        if provider not in TRANSCRIPTION_PROVIDERS:
            raise SidecarError(
                "invalid_provider",
                f"Transcription provider must be one of: {', '.join(TRANSCRIPTION_PROVIDERS)}.",
            )
        updates[("ingest", "audio", "provider")] = provider
    model: str | None = None
    if params.transcription_model is not None:
        model = params.transcription_model.strip()
        if not model:
            raise SidecarError("invalid_model", "Transcription model must not be empty.")
        updates[("ingest", "audio", "transcription_model")] = model
    if params.transcription_base_url is not None:
        base_url = params.transcription_base_url.strip()
        if not base_url.lower().startswith(("http://", "https://")):
            raise SidecarError("invalid_base_url", "Transcription base URL must be http(s).")
        updates[("ingest", "audio", "transcription_base_url")] = base_url
    # OpenRouter transcription runs as chat input_audio against a model slug;
    # catch an endpoint model (e.g. whisper-1) left behind on a provider
    # switch. Only when the request touches provider/model — an unrelated
    # update (e.g. the native toggle) must not fail on a pre-existing mismatch.
    if provider is not None or model is not None:
        effective_provider = (
            provider
            if provider is not None
            else vault.config.ingest.audio.provider.strip().lower()
        )
        effective_model = (
            model if model is not None else vault.config.ingest.audio.transcription_model
        )
        if effective_provider == "openrouter" and "/" not in effective_model:
            raise SidecarError(
                "invalid_model",
                'OpenRouter transcription models are slugs like "vendor/model" and must accept audio input.',
            )
    for field, value in validated_budget_overrides(params.budgets).items():
        updates[("ingest", "budgets", field)] = value
    provider = _ingest_provider_name(vault.config)
    for param, key in (
        (params.provider_context_tokens, "context_tokens"),
        (params.provider_max_output_tokens, "max_output_tokens"),
    ):
        if param is None:
            continue
        # apply_config_updates can set but not delete, so there is no "clear"
        # here — an unset limit stays unset by simply not sending the field.
        if param < 1:
            raise SidecarError(
                "invalid_provider_limit",
                f"{provider} {key} must be a positive number of tokens.",
            )
        updates[("ingest", "providers", provider, key)] = param
    if updates:
        try:
            apply_config_updates(vault.root / "learnloop.toml", updates)
        except SettingsStoreError as exc:
            raise SidecarError(exc.code, str(exc))
        ctx.reload(maintenance=False)
    return versioned(_settings_payload(ctx))


class SetTranscriptionApiKeyParams(ParamsModel):
    api_key: str


@method("set_transcription_api_key", SetTranscriptionApiKeyParams)
def set_transcription_api_key(ctx: SidecarContext, params: SetTranscriptionApiKeyParams) -> dict[str, Any]:
    """Save the [ingest.audio] endpoint's API key — same machinery and rules as
    the OpenRouter key (global settings.env + direct os.environ write)."""

    vault, _repository = ctx.require_vault()
    env_name = vault.config.ingest.audio.transcription_api_key_env
    value = params.api_key.strip()
    if len(value) > 512 or any(ord(ch) < 32 for ch in value):
        raise SidecarError("invalid_api_key", "API key contains control characters or is too long.")
    path = global_settings_path()
    try:
        upsert_env_var(path, env_name, value or None)
    except SettingsStoreError as exc:
        raise SidecarError(exc.code, str(exc))
    if value:
        os.environ[env_name] = value
    else:
        os.environ.pop(env_name, None)
    return versioned(
        {
            **_key_state(env_name),
            "env_name": env_name,
            "settings_env_path": str(path),
        }
    )


class SetOpenrouterApiKeyParams(ParamsModel):
    api_key: str


@method("set_openrouter_api_key", SetOpenrouterApiKeyParams)
def set_openrouter_api_key(ctx: SidecarContext, params: SetOpenrouterApiKeyParams) -> dict[str, Any]:
    vault, _repository = ctx.require_vault()
    value = params.api_key.strip()
    if len(value) > 512 or any(ord(ch) < 32 for ch in value):
        raise SidecarError("invalid_api_key", "API key contains control characters or is too long.")

    path = global_settings_path()
    try:
        upsert_env_var(path, OPENROUTER_KEY_ENV, value or None)
    except SettingsStoreError as exc:
        raise SidecarError(exc.code, str(exc))
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


class UpdateAnimationSettingsParams(ParamsModel):
    renderer: str | None = None
    quality: str | None = None
    max_duration_seconds: int | None = None
    timeout_seconds: int | None = None
    video_max_shots: int | None = None


@method("update_animation_settings", UpdateAnimationSettingsParams)
def update_animation_settings(
    ctx: SidecarContext, params: UpdateAnimationSettingsParams
) -> dict[str, Any]:
    """Persist [animation] render quality / pacing cap / timeout and reload."""

    vault, _repository = ctx.require_vault()
    updates: dict[tuple[str, ...], Any] = {}
    if params.renderer is not None:
        renderer = params.renderer.strip().lower()
        if renderer not in ANIMATION_RENDERER_OPTIONS:
            raise SidecarError(
                "invalid_renderer",
                f"Animation renderer must be one of: {', '.join(ANIMATION_RENDERER_OPTIONS)}.",
            )
        updates[("animation", "renderer")] = renderer
    if params.video_max_shots is not None:
        low, high = ANIMATION_SHOT_BOUNDS
        if not low <= params.video_max_shots <= high:
            raise SidecarError("invalid_shot_count", f"Storyboard shots must be between {low} and {high}.")
        updates[("animation", "video_max_shots")] = params.video_max_shots
    if params.quality is not None:
        quality = params.quality.strip().lower()
        if quality not in ANIMATION_QUALITY_OPTIONS:
            raise SidecarError(
                "invalid_quality",
                f"Animation quality must be one of: {', '.join(ANIMATION_QUALITY_OPTIONS)}.",
            )
        updates[("animation", "quality")] = quality
    if params.max_duration_seconds is not None:
        low, high = ANIMATION_DURATION_BOUNDS
        floor = max(low, vault.config.animation.min_duration_seconds)
        if not floor <= params.max_duration_seconds <= high:
            raise SidecarError(
                "invalid_duration",
                f"Animation length must be between {floor} and {high} seconds.",
            )
        updates[("animation", "max_duration_seconds")] = params.max_duration_seconds
    if params.timeout_seconds is not None:
        low, high = ANIMATION_TIMEOUT_BOUNDS
        if not low <= params.timeout_seconds <= high:
            raise SidecarError(
                "invalid_timeout", f"Render timeout must be between {low} and {high} seconds."
            )
        updates[("animation", "timeout_seconds")] = params.timeout_seconds
    if updates:
        try:
            apply_config_updates(vault.root / "learnloop.toml", updates)
        except SettingsStoreError as exc:
            raise SidecarError(exc.code, str(exc))
        ctx.reload(maintenance=False)
    return versioned(_settings_payload(ctx))
