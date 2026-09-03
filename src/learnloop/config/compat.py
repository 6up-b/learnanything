"""One-way normalization and runtime aliases for legacy configuration."""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

from pydantic import BaseModel, ConfigDict

from learnloop.config.schema import (
    DEFAULT_CODEX_MODEL,
    DEFAULT_CODEX_REASONING_EFFORT,
    DEFAULT_CODEX_TASK_ROUTES,
    LEGACY_CODEX_MODEL,
    OPENROUTER_TRANSCRIPTION_PROVIDER,
    AIProviderConfig,
    AudioIngestConfig,
    CodexHTTPProviderConfig,
    CodexSDKProviderConfig,
    openrouter_provider,
)

if TYPE_CHECKING:
    from learnloop.config.schema import LearnLoopConfig


_PROVIDER_TYPE_ALIASES = {
    "codex_http": "http",
    "http_adapter": "http",
    "openai_compatible": "openai_chat",
}


class CodexConfig(BaseModel):
    """Deprecated runtime view over the canonical ``ai.providers.codex`` profile."""

    model_config = ConfigDict(extra="ignore")

    provider: str = "sdk"
    checkout_path: str = ""
    revision: str = "<pinned-commit>"
    startup_command: str = ""
    startup_timeout_seconds: int = 20
    healthcheck_timeout_seconds: int = 5
    timeout_seconds: float = 180
    model: str = DEFAULT_CODEX_MODEL
    reasoning_effort: str = DEFAULT_CODEX_REASONING_EFFORT
    reasoning_summary: str = "none"
    sdk_python_path: str = "sdk/python/src"
    sdk_codex_bin: str = ""
    sdk_launch_command: str = ""
    base_url: str = "http://127.0.0.1:8765"
    healthcheck_path: str = "/health"
    authoring_path: str = "/authoring-proposal"
    canonical_ingest_path: str = "/canonical-ingest"
    grading_path: str = "/grading-proposal"
    tutor_qa_path: str = "/tutor-qa"
    teach_back_path: str = "/teach-back"
    teach_back_authoring_path: str = "/teach-back-authoring"
    misconception_match_path: str = "/misconception-match"


def discard_retired_provider_settings(data: Any) -> Any:
    """Drop provider keys that were parsed historically but never consumed."""

    if not isinstance(data, dict) or "auth_mode" not in data:
        return data
    normalized = dict(data)
    normalized.pop("auth_mode", None)
    return normalized


def normalize_provider_profile(value: Any) -> Any:
    """Canonicalize provider type aliases before union discrimination."""

    if isinstance(value, AIProviderConfig):
        value = value.model_dump(mode="python")
    if not isinstance(value, dict):
        return value
    normalized = discard_retired_provider_settings(value)
    raw_type = str(normalized.get("type") or "codex_sdk").strip().lower()
    normalized["type"] = _PROVIDER_TYPE_ALIASES.get(raw_type, raw_type)
    return normalized


def normalize_ai_input(data: Any) -> Any:
    """Normalize every named provider while preserving non-mapping inputs."""

    if not isinstance(data, dict):
        return data
    normalized = dict(data)
    providers = normalized.get("providers")
    if isinstance(providers, dict):
        normalized["providers"] = {
            name: normalize_provider_profile(profile)
            for name, profile in providers.items()
        }
    return normalized


def normalize_config_input(data: Any) -> Any:
    """Translate accepted legacy shapes into the canonical schema input.

    The transformation is deliberately one-way: canonical keys win when both
    forms are present, and retired values do not survive model serialization.
    This function is idempotent so the filesystem loader can make the pipeline
    explicit while direct ``LearnLoopConfig.model_validate`` calls retain their
    historical compatibility behavior.
    """

    if not isinstance(data, dict):
        return data
    normalized = dict(data)
    normalized.pop("forecasts", None)
    normalized.pop("cross_lo_propagation", None)

    legacy_codex = normalized.pop("codex", None)
    if isinstance(legacy_codex, dict):
        ai = dict(normalized.get("ai") or {})
        providers = dict(ai.get("providers") or {})
        providers.setdefault("codex", _provider_profile_from_legacy_codex(legacy_codex))
        ai["providers"] = providers
        normalized["ai"] = ai

    ingest = normalized.get("ingest")
    audio = ingest.get("audio") if isinstance(ingest, dict) else None
    if (
        isinstance(audio, dict)
        and str(audio.get("provider") or "").strip().lower() == "openrouter"
    ):
        ai = dict(normalized.get("ai") or {})
        providers = dict(ai.get("providers") or {})
        providers.setdefault(
            OPENROUTER_TRANSCRIPTION_PROVIDER,
            _profile_from_legacy_openrouter_audio(audio, providers),
        )
        routing = dict(ai.get("routing") or {})
        if not str(routing.get("transcription") or "").strip():
            routing["transcription"] = OPENROUTER_TRANSCRIPTION_PROVIDER
        ai["providers"] = providers
        ai["routing"] = routing
        normalized["ai"] = ai

    probe = normalized.get("probe")
    if isinstance(probe, dict):
        probe = dict(probe)
        episode = probe.get("episode")
        if isinstance(episode, dict):
            episode = dict(episode)
            episode.pop("self_graded_evidence_weight", None)
            probe["episode"] = episode
        dialogue = probe.get("dialogue")
        if isinstance(dialogue, dict):
            dialogue = dict(dialogue)
            dialogue.pop("max_turns", None)
            probe["dialogue"] = dialogue
        normalized["probe"] = probe

    coverage = normalized.get("recall_coverage")
    if isinstance(coverage, dict):
        coverage = dict(coverage)
        coverage.pop("facet_recall_prior_pseudo_count", None)
        coverage.pop("coverage_epsilon", None)
        normalized["recall_coverage"] = coverage

    ingest = normalized.get("ingest")
    if isinstance(ingest, dict):
        ingest = dict(ingest)
        budgets = ingest.get("budgets")
        if isinstance(budgets, dict):
            budgets = dict(budgets)
            budgets.pop("evidence_span_input_tokens", None)
            ingest["budgets"] = budgets
        # Retired [ingest.native] gates. The master `enabled` plus the audio
        # flag become `[ingest.audio] mode = "native"` (canonical key wins);
        # the `pdf` flag is dropped because `[ingest.pdf] engine` is the only
        # PDF authority.
        native = ingest.get("native")
        if isinstance(native, dict):
            native = dict(native)
            legacy_enabled = bool(native.pop("enabled", False))
            legacy_audio = bool(native.pop("audio", True))
            native.pop("pdf", None)
            ingest["native"] = native
            audio = ingest.get("audio")
            audio = dict(audio) if isinstance(audio, dict) else {}
            if "mode" not in audio and legacy_enabled and legacy_audio:
                audio["mode"] = "native"
            ingest["audio"] = audio
        normalized["ingest"] = ingest

    impacts = normalized.get("error_impacts")
    if isinstance(impacts, dict) and "max_sharpening" in impacts:
        impacts = dict(impacts)
        max_sharpening = impacts.pop("max_sharpening")
        coverage = dict(normalized.get("recall_coverage") or {})
        coverage.setdefault("max_error_sharpening", max_sharpening)
        normalized["recall_coverage"] = coverage
        normalized["error_impacts"] = impacts

    ai = normalized.get("ai")
    if isinstance(ai, dict):
        ai = _normalize_codex_aliases(ai)
        normalized["ai"] = ai
    return normalized


def ai_provider_from_codex(config: CodexConfig) -> AIProviderConfig:
    """Translate the deprecated Codex runtime object to a typed profile."""

    provider_class: type[CodexSDKProviderConfig] | type[CodexHTTPProviderConfig]
    if config.provider.lower() in {"http", "http_adapter"}:
        provider_class = CodexHTTPProviderConfig
    else:
        provider_class = CodexSDKProviderConfig
    return provider_class(
        model=config.model,
        checkout_path=config.checkout_path,
        revision=config.revision,
        startup_command=config.startup_command,
        startup_timeout_seconds=config.startup_timeout_seconds,
        healthcheck_timeout_seconds=config.healthcheck_timeout_seconds,
        reasoning_effort=config.reasoning_effort,
        reasoning_summary=config.reasoning_summary,
        sdk_python_path=config.sdk_python_path,
        sdk_codex_bin=config.sdk_codex_bin,
        sdk_launch_command=config.sdk_launch_command,
        base_url=config.base_url,
        healthcheck_path=config.healthcheck_path,
        authoring_path=config.authoring_path,
        canonical_ingest_path=config.canonical_ingest_path,
        grading_path=config.grading_path,
        tutor_qa_path=config.tutor_qa_path,
        teach_back_path=config.teach_back_path,
        teach_back_authoring_path=config.teach_back_authoring_path,
        misconception_match_path=config.misconception_match_path,
    )


def codex_config_view(config: LearnLoopConfig) -> CodexConfig:
    """Build the non-serialized ``config.codex`` compatibility alias."""

    profile = config.ai.providers.get("codex")
    if profile is None:
        return CodexConfig()
    payload = profile.model_dump(mode="python", exclude={"type"}, exclude_none=True)
    payload["provider"] = "http" if profile.type == "http" else "sdk"
    return CodexConfig.model_validate(payload)


def _provider_profile_from_legacy_codex(value: dict[str, Any]) -> dict[str, Any]:
    legacy = CodexConfig.model_validate(value)
    payload = legacy.model_dump(mode="python")
    provider = str(payload.pop("provider", "sdk")).strip().lower()
    payload["type"] = "http" if provider in {"http", "http_adapter"} else "codex_sdk"
    return payload


def _profile_from_legacy_openrouter_audio(
    audio: dict[str, Any], providers: dict[str, Any]
) -> dict[str, Any]:
    base: Any = providers.get("openrouter")
    if isinstance(base, AIProviderConfig):
        profile = base.model_dump(mode="python", exclude_none=True)
    elif isinstance(base, dict):
        profile = dict(base)
    else:
        profile = openrouter_provider().model_dump(mode="python", exclude_none=True)

    profile["type"] = "openrouter"
    defaults = AudioIngestConfig()
    profile["model"] = str(audio.get("transcription_model", defaults.transcription_model))
    timeout = audio.get("timeout_seconds", defaults.timeout_seconds)
    profile["timeout_seconds"] = None if timeout is None else int(timeout)
    modalities = [str(value) for value in profile.get("input_modalities") or []]
    if "audio" not in modalities:
        modalities.append("audio")
    profile["input_modalities"] = modalities
    return profile


def _normalize_codex_aliases(ai: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(ai)
    raw_providers = normalized.get("providers")
    if raw_providers is None:
        providers: dict[str, Any] = {}
    elif isinstance(raw_providers, dict):
        providers = dict(raw_providers)
    else:
        return normalized
    codex = providers.get("codex")
    if isinstance(codex, AIProviderConfig):
        codex = codex.model_dump(mode="python")
    if isinstance(codex, dict) and codex.get("model") == LEGACY_CODEX_MODEL:
        codex = dict(codex)
        codex["model"] = DEFAULT_CODEX_MODEL
        codex["reasoning_effort"] = DEFAULT_CODEX_REASONING_EFFORT
        providers["codex"] = codex
    if providers:
        normalized["providers"] = providers

    routing = normalized.get("routing")
    if isinstance(routing, dict):
        routing = dict(routing)
        for task, default_provider in DEFAULT_CODEX_TASK_ROUTES.items():
            if routing.get(task) == "codex":
                routing[task] = default_provider
        normalized["routing"] = routing
    return normalized


__all__ = [
    "CodexConfig",
    "ai_provider_from_codex",
    "codex_config_view",
    "discard_retired_provider_settings",
    "normalize_ai_input",
    "normalize_config_input",
    "normalize_provider_profile",
]
