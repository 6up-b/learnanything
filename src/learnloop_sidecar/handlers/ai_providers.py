from __future__ import annotations

from typing import Any

from learnloop.ai.errors import AIProviderUnavailable
from learnloop.ai.routing import (
    MANUAL_PROVIDER,
    client_for_provider as resolve_client_for_provider,
    ready_client_for_task,
    runtime_for_provider as resolve_runtime_for_provider,
)
from learnloop.config import CODEX_PROVIDER_NAMES
from learnloop_sidecar.context import SidecarContext, available_grading_providers
from learnloop_sidecar.dto import ParamsModel, versioned
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.registry import method

def ready_grading_provider(vault, override: str | None = None) -> tuple[str, Any, Any | None]:
    """Resolve the grading backend, honoring the runtime override.

    ``override`` is the sidecar-session override set via ``set_grading_provider``:
    ``"manual"`` short-circuits to a never-ready runtime (no client), so callers
    take their self-grade fallback path; a provider key is treated as an explicit
    selection (no silent fallback provider).
    """

    return tuple(
        ready_client_for_task(
            vault.root,
            vault.config,
            "grading",
            explicit=override,
        )
    )


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
    return tuple(ready_client_for_task(vault.root, vault.config, task))


def runtime_for_provider(vault, provider_name: str):
    return resolve_runtime_for_provider(vault.root, vault.config, provider_name)


def client_for_provider(vault, provider_name: str):
    try:
        return resolve_client_for_provider(vault.root, vault.config, provider_name)
    except AIProviderUnavailable:
        return None


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
