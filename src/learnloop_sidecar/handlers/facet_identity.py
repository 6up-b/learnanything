"""Facet identity (handoff §4): list a run's merges and absorbs, undo one."""

from __future__ import annotations

from typing import Any

from learnloop.content.facet_identity.actions import (
    FacetIdentityActionError,
    action_by_id,
    describe,
    list_actions,
    undo_action,
)
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.dto import ParamsModel, versioned
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.registry import method


class ListFacetIdentityActionsInput(ParamsModel):
    run_id: str | None = None
    limit: int = 100


class FacetIdentityActionInput(ParamsModel):
    action_id: str


@method("list_facet_identity_actions", ListFacetIdentityActionsInput)
def list_facet_identity_actions(ctx: SidecarContext, params: ListFacetIdentityActionsInput) -> dict[str, Any]:
    """Merges and absorbs (newest first), each with whether it can be undone now."""

    vault, repository = ctx.require_vault()
    limit = max(1, min(int(params.limit), 1000))
    records = list_actions(repository, run_id=params.run_id, limit=limit)
    return versioned({"actions": [describe(record, vault) for record in records]})


@method("undo_facet_identity_action", FacetIdentityActionInput)
def undo_facet_identity_action(ctx: SidecarContext, params: FacetIdentityActionInput) -> dict[str, Any]:
    """One-tap undo: restore the facets one action replaced, and re-fold their evidence.

    Rows graded while the merge stood stay with the survivor (``not_restored``).
    """

    vault, repository = ctx.require_vault()
    try:
        result = undo_action(vault.root, repository, params.action_id)
    except FacetIdentityActionError as exc:
        raise SidecarError(exc.code, str(exc)) from exc
    ctx.reload(maintenance=False)
    vault, repository = ctx.require_vault()
    record = action_by_id(repository, params.action_id)
    return versioned({**result, "action": describe(record, vault) if record is not None else None})
