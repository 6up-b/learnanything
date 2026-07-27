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
    ctx.exam_grading.shutdown()
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


#: One SQL round trip per nav badge. Deliberately NOT routed through the screens'
#: own loaders: ``get_proposals`` materializes and DTO-serializes every item,
#: ``maintenance_feed`` *regenerates and writes* the whole feed, and
#: ``get_measurement_health`` runs reachability plus the scoreboard. All three are
#: fine when a screen is open and far too heavy to hang off a nav bar. These are
#: indexed or small-table counts, so the badge stays a count and never becomes a
#: reason to avoid opening the tab.
_BADGE_COUNT_QUERIES: dict[str, str] = {
    # Proposals tab.
    "pending_proposals": """
        SELECT COUNT(*) FROM proposed_patch_items WHERE decision = 'pending'
    """,
    # Maintain tab, four independent queues.
    "unreviewed_probe_candidates": """
        SELECT COUNT(*) FROM causal_probe_candidates
        WHERE status IN ('candidate', 'registered')
    """,
    "open_source_conflicts": """
        SELECT COUNT(*) FROM source_conflicts WHERE status = 'open'
    """,
    "action_needed_notices": """
        SELECT COUNT(*) FROM maintenance_notices
        WHERE status IN ('active', 'snoozed') AND severity = 'action_needed'
    """,
    "pending_clarifications": """
        SELECT COUNT(*) FROM grading_clarifications c
        LEFT JOIN grading_clarification_responses r ON r.clarification_id = c.id
        WHERE r.id IS NULL
    """,
}

#: Which Maintain-tab queues roll up into that tab's single badge. Proposals gets
#: its own count and is excluded here so one pending item is never counted twice.
_MAINTAIN_BADGE_KEYS: tuple[str, ...] = (
    "unreviewed_probe_candidates",
    "open_source_conflicts",
    "action_needed_notices",
    "pending_clarifications",
)


@method("get_review_counts")
def get_review_counts(ctx: SidecarContext, _params) -> dict[str, Any]:
    """Counts behind the nav-tab badges: what is waiting on the learner.

    Kept separate from ``load_vault`` on purpose. The Rust file watcher re-embeds
    a whole ``app_snapshot`` on a full refresh, so a count folded into that
    snapshot would have to be recomputed on every vault file change; as its own
    method the frontend can refresh badges on exactly the events that can change
    them without making unrelated vault edits pay for the queries.
    """

    _vault, repository = ctx.require_vault()
    counts: dict[str, int] = {}
    with repository.connection() as connection:
        for name, query in _BADGE_COUNT_QUERIES.items():
            counts[name] = int(connection.execute(query).fetchone()[0])
    return versioned(
        {
            **counts,
            "proposals_badge": counts["pending_proposals"],
            "maintain_badge": sum(counts[key] for key in _MAINTAIN_BADGE_KEYS),
        }
    )
