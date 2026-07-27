from __future__ import annotations

from typing import Any

from pydantic import Field

from learnloop_sidecar import __version__
from learnloop_sidecar.context import SidecarContext, config_dto, runtime_health, vault_summary
from learnloop_sidecar.dto import ParamsModel, versioned
from learnloop_sidecar.registry import METHOD_REGISTRY, method


class InitializeParams(ParamsModel):
    vault_path: str
    client_version: str | None = None


class RefreshVaultFilesInput(ParamsModel):
    vault_root: str
    paths: list[str] = Field(default_factory=list)


@method("initialize", InitializeParams)
def initialize(ctx: SidecarContext, params: InitializeParams) -> dict[str, Any]:
    ctx.load(params.vault_path)
    vault, repository = ctx.require_vault()
    return versioned(
        {
            "sidecar_version": __version__,
            "protocol": {"jsonrpc": "2.0", "framing": "ndjson"},
            "capabilities": {
                "methods": sorted(METHOD_REGISTRY),
                "jobs": ["ingest"],
                "streaming": "coarse",
            },
            "vault": vault_summary(vault),
            "health": runtime_health(vault, repository, grading_override=ctx.grading_provider_override),
        }
    )


@method("shutdown")
def shutdown(ctx: SidecarContext, _params) -> dict[str, Any]:
    ctx.ingest_jobs.shutdown()
    ctx.shutdown_requested = True
    return {"ok": True}


@method("rpc.health")
def rpc_health(ctx: SidecarContext, _params) -> dict[str, Any]:
    vault, repository = ctx.require_vault()
    return runtime_health(vault, repository, grading_override=ctx.grading_provider_override)


@method("load_vault")
def load_vault_handler(ctx: SidecarContext, _params) -> dict[str, Any]:
    return ctx.app_snapshot()


@method("reload_vault")
def reload_vault_handler(ctx: SidecarContext, _params) -> dict[str, Any]:
    ctx.reload()
    return ctx.app_snapshot()


@method("refresh_vault_files", RefreshVaultFilesInput)
def refresh_vault_files(ctx: SidecarContext, params: RefreshVaultFilesInput) -> dict[str, Any]:
    """Rust watcher handoff: incrementally refresh supported changed files."""

    return versioned(
        ctx.refresh_vault_files(params.paths, expected_root=params.vault_root)
    )


@method("get_runtime_health")
def get_runtime_health(ctx: SidecarContext, _params) -> dict[str, Any]:
    vault, repository = ctx.require_vault()
    return runtime_health(vault, repository, grading_override=ctx.grading_provider_override)


@method("get_config")
def get_config(ctx: SidecarContext, _params) -> dict[str, Any]:
    vault, _repository = ctx.require_vault()
    return config_dto(vault)
