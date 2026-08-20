from __future__ import annotations

from typing import Any, Literal

from learnloop.curriculum.graph_edit_proposals import (
    GraphEditError,
    propose_graph_edits,
    queue_restructure_request,
    resolve_edge_direction,
)
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.dto import ParamsModel, to_camel, versioned
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.handlers.proposals import _proposals_payload
from learnloop_sidecar.registry import method


class GraphEditItemInput(ParamsModel):
    item_type: Literal["concept_edge", "learning_object", "task_blueprint", "concept"]
    operation: Literal["create", "update", "delete"]
    payload: dict[str, Any] = {}
    target_entity_id: str | None = None


class ProposeGraphEditsInput(ParamsModel):
    rationale: str
    edits: list[GraphEditItemInput]


@method("propose_graph_edits", ProposeGraphEditsInput)
def propose_graph_edits_handler(ctx: SidecarContext, params: ProposeGraphEditsInput) -> dict[str, Any]:
    """Compile user graph edits into ONE pending proposal batch (design "Write path").

    Provider ``user``, purpose ``graph_editor``, summary = ``rationale``; every
    edit becomes a pending proposal item validated identically to Codex-authored
    items and routed to the Proposals inbox. Returns ``{batchId, items}`` plus the
    refreshed inbox payload."""

    vault, _repository = ctx.require_vault()
    try:
        result = propose_graph_edits(
            vault.root,
            params.rationale,
            [edit.model_dump() for edit in params.edits],
        )
    except GraphEditError as exc:
        raise SidecarError(exc.code, str(exc)) from exc
    payload = _proposals_payload(ctx)
    payload["batchId"] = result["batch_id"]
    payload["items"] = to_camel(result["items"])
    return payload


class QueueRestructureRequestInput(ParamsModel):
    facet_ids: list[str]
    requested_operation: Literal["merge", "split"]
    rationale: str


@method("queue_restructure_request", QueueRestructureRequestInput)
def queue_restructure_request_handler(
    ctx: SidecarContext, params: QueueRestructureRequestInput
) -> dict[str, Any]:
    """Queue durable restructure intent for LOCKED facets (spec §17 not yet built).

    Errors (pointing back at the normal merge flow) when no named facet is locked;
    otherwise records a ``restructure_request`` generation-need that surfaces in the
    maintenance feed."""

    vault, _repository = ctx.require_vault()
    try:
        record = queue_restructure_request(
            vault.root,
            list(params.facet_ids),
            params.requested_operation,
            params.rationale,
        )
    except GraphEditError as exc:
        raise SidecarError(exc.code, str(exc)) from exc
    return versioned({"request": record})


class ResolveEdgeDirectionInput(ParamsModel):
    edge_id: str
    resolution: Literal["keep", "flip", "retype_related", "retire"]
    rationale: str


@method("resolve_edge_direction", ResolveEdgeDirectionInput)
def resolve_edge_direction_handler(ctx: SidecarContext, params: ResolveEdgeDirectionInput) -> dict[str, Any]:
    """Resolve an ``ambiguous_edge_direction`` notice into a concept_edge edit.

    ``keep`` files no edit; ``flip``/``retype_related``/``retire`` compile a
    concept_edge proposal item through the same service as ``propose_graph_edits``.
    Resolves the corresponding maintenance notice; returns the refreshed inbox."""

    vault, _repository = ctx.require_vault()
    try:
        result = resolve_edge_direction(
            vault.root,
            params.edge_id,
            params.resolution,
            params.rationale,
        )
    except GraphEditError as exc:
        raise SidecarError(exc.code, str(exc)) from exc
    payload = _proposals_payload(ctx)
    payload["resolution"] = to_camel(result)
    return payload
