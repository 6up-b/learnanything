from __future__ import annotations

from typing import Any

from learnloop.ai.client import make_ai_provider_client
from learnloop.ai.routing import fallback_provider_for, provider_for_task
from learnloop.ai.runtime import AIRuntimeReport, check_ai_runtime
from learnloop.codex.client import CodexUnavailable, make_codex_client
from learnloop.codex.runtime import check_codex_runtime
from learnloop.config import CODEX_PROVIDER_NAMES
from learnloop_sidecar.context import SidecarContext, available_grading_providers
from learnloop_sidecar.dto import ParamsModel, versioned
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.registry import method

MANUAL_PROVIDER = "manual"


def ready_grading_provider(vault, override: str | None = None) -> tuple[str, Any, Any | None]:
    """Resolve the grading backend, honoring the runtime override.

    ``override`` is the sidecar-session override set via ``set_grading_provider``:
    ``"manual"`` short-circuits to a never-ready runtime (no client), so callers
    take their self-grade fallback path; a provider key is treated as an explicit
    selection (no silent fallback provider).
    """

    if override == MANUAL_PROVIDER:
        runtime = AIRuntimeReport(
            status="provider_unavailable",
            active_provider=MANUAL_PROVIDER,
            message="Manual grading selected; AI grading is disabled.",
        )
        return MANUAL_PROVIDER, runtime, None
    selection = provider_for_task(vault.config, "grading", explicit_provider=override)
    provider_name = selection.provider_name
    runtime = runtime_for_provider(vault, provider_name)
    if runtime.ready:
        return provider_name, runtime, client_for_provider(vault, provider_name)
    fallback = fallback_provider_for(vault.config, selection)
    if fallback:
        fallback_runtime = runtime_for_provider(vault, fallback)
        if fallback_runtime.ready:
            return fallback, fallback_runtime, client_for_provider(vault, fallback)
    return provider_name, runtime, None


def ready_tutor_qa_provider(vault) -> tuple[str, Any, Any | None]:
    """Resolve the tutor Q&A backend via the ``tutor_qa`` routing entry.

    Defaults to ai.active_provider when unrouted (provider_for_task fallback
    chain); honors the shared fallback provider when the routed one is down.
    """

    return _ready_routed_provider(vault, "tutor_qa")


def ready_teach_back_provider(vault) -> tuple[str, Any, Any | None]:
    """Resolve the teach-back (naive student) backend via ``teach_back`` routing.

    Same fallback chain as tutor Q&A: ai.active_provider when unrouted, the
    shared fallback provider when the routed one is down.
    """

    return _ready_routed_provider(vault, "teach_back")


def ready_canonical_ingest_provider(vault) -> tuple[str, Any, Any | None]:
    """Resolve the medium-effort canonical-ingest/synthesis route."""

    return _ready_routed_provider(vault, "canonical_ingest")


def _ready_routed_provider(vault, task: str) -> tuple[str, Any, Any | None]:
    selection = provider_for_task(vault.config, task)
    provider_name = selection.provider_name
    runtime = runtime_for_provider(vault, provider_name)
    if runtime.ready:
        return provider_name, runtime, client_for_provider(vault, provider_name)
    fallback = fallback_provider_for(vault.config, selection)
    if fallback:
        fallback_runtime = runtime_for_provider(vault, fallback)
        if fallback_runtime.ready:
            return fallback, fallback_runtime, client_for_provider(vault, fallback)
    return provider_name, runtime, None


def runtime_for_provider(vault, provider_name: str):
    if provider_name in vault.config.ai.providers:
        return check_ai_runtime(vault.root, vault.config, provider_name=provider_name)
    if provider_name == "codex":
        return check_codex_runtime(vault.root, vault.config.codex)
    return check_ai_runtime(vault.root, vault.config, provider_name=provider_name)


def client_for_provider(vault, provider_name: str):
    if provider_name in vault.config.ai.providers:
        return _ai_client(vault, provider_name)
    if provider_name == "codex":
        return _codex_client(vault)
    return _ai_client(vault, provider_name)


def grading_source_for_provider(provider_name: str) -> str:
    return (
        "codex"
        if provider_name in CODEX_PROVIDER_NAMES
        else "ai"
    )


def provider_label(provider_name: str) -> str:
    return (
        "Codex"
        if provider_name in CODEX_PROVIDER_NAMES
        else f"AI provider {provider_name}"
    )


def _codex_client(vault):
    try:
        return make_codex_client(vault.config.codex, vault.root)
    except CodexUnavailable:
        return None


def _ai_client(vault, provider_name: str):
    try:
        return make_ai_provider_client(vault.config, vault.root, provider_name=provider_name)
    except CodexUnavailable:
        return None


class SetGradingProviderParams(ParamsModel):
    provider: str


@method("set_grading_provider", SetGradingProviderParams)
def set_grading_provider(ctx: SidecarContext, params: SetGradingProviderParams) -> dict[str, Any]:
    """Switch the AI grading backend at runtime (not persisted to learnloop.toml).

    ``provider`` must be a configured provider key (e.g. "codex",
    "deepseek_flash") or the literal "manual". "manual" disables AI grading so
    attempts fall back to self-grading; health.ai then reports
    activeProvider="manual" with manualGrading=true.
    """

    vault, _repository = ctx.require_vault()
    options = available_grading_providers(vault)
    if params.provider not in options:
        raise SidecarError(
            "invalid_provider",
            f"Unknown grading provider {params.provider!r}. Valid options: {', '.join(options)}.",
            details={"available_providers": options},
        )
    ctx.grading_provider_override = params.provider
    if params.provider == MANUAL_PROVIDER:
        ready = True
    else:
        ready = bool(runtime_for_provider(vault, params.provider).ready)
    return versioned(
        {
            "active_provider": params.provider,
            "manual_grading": params.provider == MANUAL_PROVIDER,
            "ready": ready,
            "available_providers": options,
        }
    )
