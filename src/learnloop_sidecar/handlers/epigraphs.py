"""Start-screen epigraphs: read the model-authored quotes/haiku for a vault."""

from __future__ import annotations

from typing import Any

from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.dto import ParamsModel, versioned
from learnloop_sidecar.registry import method

MAX_EPIGRAPH_LIMIT = 50


class ListVaultEpigraphsInput(ParamsModel):
    subject_id: str | None = None
    limit: int = 12


@method("list_vault_epigraphs", ListVaultEpigraphsInput)
def list_vault_epigraphs(ctx: SidecarContext, params: ListVaultEpigraphsInput) -> dict[str, Any]:
    """Newest-first epigraphs for the Start screen's hero text.

    Read-only: rows are written only when a synthesis completes
    (``learnloop.content.synthesis.vault_epigraphs``), never on demand."""

    _vault, repository = ctx.require_vault()
    limit = max(1, min(int(params.limit), MAX_EPIGRAPH_LIMIT))
    rows = repository.recent_vault_epigraphs(subject_id=params.subject_id or None, limit=limit)
    return versioned({"epigraphs": [_epigraph_dto(row) for row in rows]})


def _epigraph_dto(row: dict[str, Any]) -> dict[str, Any]:
    text = str(row.get("text") or "")
    return {
        "id": row["id"],
        "subject_id": row["subject_id"],
        "source_set_id": row.get("source_set_id"),
        "synthesis_run_id": row.get("synthesis_run_id"),
        "mode": row.get("mode"),
        "kind": row["kind"],
        "text": text,
        "lines": text.split("\n"),
        "prompt_version": row.get("prompt_version"),
        "provider": row.get("provider"),
        "model": row.get("model"),
        "created_at": row["created_at"],
    }
