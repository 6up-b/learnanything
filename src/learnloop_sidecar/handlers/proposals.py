from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from learnloop.services.proposals import (
    accept_items,
    delete_proposal_item as service_delete_proposal_item,
    edit_proposal_item as service_edit_proposal_item,
    refresh_proposal_item_validation as service_refresh_proposal_item_validation,
    reject_items,
    reset_items,
)
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.dto import ParamsModel, versioned
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.registry import method

# Item types eligible for the low-risk auto-apply route under the spec §7 policy.
# Used only to derive the display "route" pill — the durable decision lives on the row.
_AUTO_APPLY_TYPES = {"learning_object", "practice_item", "concept_edge"}


def _duration_s(started_at: str | None, completed_at: str | None) -> float | None:
    if not started_at or not completed_at:
        return None
    try:
        start = datetime.fromisoformat(started_at.replace("Z", "+00:00"))
        end = datetime.fromisoformat(completed_at.replace("Z", "+00:00"))
    except ValueError:
        return None
    return round((end - start).total_seconds(), 1)


def _review_route(item: dict[str, Any]) -> str:
    """Display route for an item: how the review policy would treat it.

    A label, not the decision — ``decision`` (pending/accepted/rejected) is the
    source of truth for state. Mirrors the shape of ``evaluate_review_policy``:
    invalid items can't be applied (reject); plain source-grounded creations of
    Learning Objects / Practice Items / edges are the auto-apply lane; everything
    else (updates, misconceptions, transfers) needs review.
    """

    if item["validation_status"] == "invalid":
        return "reject"
    if item["operation"] == "create" and item["item_type"] in _AUTO_APPLY_TYPES:
        return "auto_apply"
    return "review_required"


def _render_value(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, separators=(", ", ": "))
    if value is None:
        return "null"
    return str(value)


def _payload_lines(payload: dict[str, Any]) -> list[list[str]]:
    """Flatten a payload into ordered [key, rendered-value] rows for the preview.

    Keys are emitted as string values (not dict keys) so they survive
    camel-casing untouched — the preview shows the real on-disk field names.
    """

    return [[str(key), _render_value(value)] for key, value in payload.items()]


def _source_refs(item: dict[str, Any], batch: dict[str, Any]) -> list[dict[str, Any]]:
    payload = item.get("edited_payload") or item.get("payload") or {}
    provenance = payload.get("provenance") if isinstance(payload, dict) else None
    refs = provenance.get("source_refs") if isinstance(provenance, dict) else None
    if not refs:
        refs = batch.get("source_refs") or []
    out: list[dict[str, Any]] = []
    for ref in refs:
        if not isinstance(ref, dict):
            continue
        label = ref.get("locator") or ref.get("ref_id") or ref.get("ref_type") or "source"
        out.append(
            {
                "label": str(label),
                "kind": ref.get("ref_type") or "derived",
                "ref_id": ref.get("ref_id"),
            }
        )
    return out


def _item_dto(item: dict[str, Any], batch: dict[str, Any]) -> dict[str, Any]:
    payload = item.get("edited_payload") if item.get("edited_payload") is not None else item.get("payload")
    payload = payload if isinstance(payload, dict) else {}
    proposed_entity_id = (
        item.get("target_entity_id") or payload.get("id") or item.get("client_item_id")
    )
    return {
        "id": item["id"],
        "client_item_id": item.get("client_item_id"),
        "item_type": item["item_type"],
        "operation": item["operation"],
        "decision": item["decision"],
        "proposed_entity_id": proposed_entity_id,
        "target_entity_type": item.get("target_entity_type"),
        "target_entity_id": item.get("target_entity_id"),
        "review_route": _review_route(item),
        "validation_status": item["validation_status"],
        "validation_errors": item.get("validation_errors") or [],
        "edited": item.get("edited_payload") is not None,
        "applied": item.get("applied_change_batch_id") is not None,
        # Items don't persist a per-item rationale; the batch summary is the
        # Codex-authored narrative for why these changes were proposed.
        "rationale": batch.get("summary") or "",
        "source_refs": _source_refs(item, batch),
        "payload_lines": _payload_lines(payload),
        # The raw payload as a JSON *string* (not a dict): dto.to_camel would
        # camelCase dict keys and corrupt on-disk field names like
        # ``learning_object_id``. As a string it round-trips untouched and is what
        # the Library payload editor reads/writes.
        "payload_json": json.dumps(payload, indent=2, ensure_ascii=False),
    }


def _count_decisions(items: list[dict[str, Any]]) -> dict[str, int]:
    counts = {"pending": 0, "accepted": 0, "rejected": 0}
    for item in items:
        decision = item["decision"]
        counts[decision] = counts.get(decision, 0) + 1
    return counts


def _proposals_payload(ctx: SidecarContext) -> dict[str, Any]:
    _vault, repository = ctx.require_vault()
    batches = repository.proposal_batches()

    batch_dtos: list[dict[str, Any]] = []
    totals = {"pending": 0, "accepted": 0, "rejected": 0}
    for batch in batches:
        raw_items = repository.proposal_items(batch["id"])
        items = [_item_dto(item, batch) for item in raw_items]
        counts = _count_decisions(items)
        for key in totals:
            totals[key] += counts[key]

        run = repository.agent_run(batch["agent_run_id"]) or {}
        agent_run = {
            "id": batch["agent_run_id"],
            "model": run.get("model"),
            "provider": run.get("provider"),
            "purpose": run.get("purpose") or batch.get("purpose"),
            "codex_revision": run.get("codex_revision"),
            "started_at": run.get("started_at"),
            "completed_at": run.get("completed_at"),
            "status": run.get("status"),
            "duration_s": _duration_s(run.get("started_at"), run.get("completed_at")),
        }
        batch_dtos.append(
            {
                "id": batch["id"],
                "summary": batch.get("summary"),
                "purpose": batch.get("purpose"),
                "status": batch.get("status_cache"),
                "created_at": batch.get("created_at"),
                "updated_at": batch.get("updated_at"),
                "agent_run": agent_run,
                "counts": counts,
                "items": items,
            }
        )

    return versioned(
        {
            "batches": batch_dtos,
            "totals": totals,
            "batch_count": len(batch_dtos),
        }
    )


@method("get_proposals")
def get_proposals(ctx: SidecarContext, _params) -> dict[str, Any]:
    """Codex authoring inbox: proposal batches + items + agent-run lineage.

    Pure serialization over persisted proposal state — every change Codex makes
    routes through this inbox; it never writes vault files directly.
    """

    return _proposals_payload(ctx)


class ProposalDecisionInput(ParamsModel):
    patch_id: str
    item_ids: list[str] | None = None


@method("accept_proposal_items", ProposalDecisionInput)
def accept_proposal_items(ctx: SidecarContext, params: ProposalDecisionInput) -> dict[str, Any]:
    """Accept (and apply) pending proposal items, then return the refreshed inbox."""

    vault, _repository = ctx.require_vault()
    accept_items(vault.root, params.patch_id, params.item_ids)
    # Applying writes vault files, so refresh the in-memory vault — but proposal
    # review is fully offline; skip the Codex runtime probe that would block reload.
    ctx.reload(maintenance=False)
    return _proposals_payload(ctx)


@method("reject_proposal_items", ProposalDecisionInput)
def reject_proposal_items(ctx: SidecarContext, params: ProposalDecisionInput) -> dict[str, Any]:
    """Reject proposal items (reverting any already-applied change), then refresh."""

    vault, _repository = ctx.require_vault()
    reject_items(vault.root, params.patch_id, params.item_ids)
    # Reverting an applied item touches vault files; refresh without the Codex probe.
    ctx.reload(maintenance=False)
    return _proposals_payload(ctx)


@method("reset_proposal_items", ProposalDecisionInput)
def reset_proposal_items(ctx: SidecarContext, params: ProposalDecisionInput) -> dict[str, Any]:
    """Undo a rejection (never-applied items back to pending), then refresh."""

    vault, _repository = ctx.require_vault()
    reset_items(vault.root, params.patch_id, params.item_ids)
    # Undo only flips a DB decision (never-applied items); refresh without the Codex probe.
    ctx.reload(maintenance=False)
    return _proposals_payload(ctx)


class EditProposalItemInput(ParamsModel):
    patch_id: str
    item_id: str
    payload_json: str


@method("edit_proposal_item", EditProposalItemInput)
def edit_proposal_item(ctx: SidecarContext, params: EditProposalItemInput) -> dict[str, Any]:
    """Replace a pending proposal item's payload with edited JSON, then refresh.

    Re-runs the edited-payload validation server-side (see
    ``services.proposals.edit_proposal_item``) so the inbox reflects whether the
    hand-edited payload still resolves.
    """

    vault, _repository = ctx.require_vault()
    try:
        payload = json.loads(params.payload_json)
    except json.JSONDecodeError as exc:
        raise SidecarError("invalid_payload", f"Payload is not valid JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise SidecarError("invalid_payload", "Payload must be a JSON object.")
    try:
        service_edit_proposal_item(vault.root, params.patch_id, params.item_id, payload)
    except ValueError as exc:
        raise SidecarError("invalid_request", str(exc)) from exc
    # Editing a payload changes no vault files — the snapshot reads proposal state
    # straight from SQLite, so there's no need to re-parse the vault or probe Codex.
    return _proposals_payload(ctx)


class RefreshProposalItemValidationInput(ParamsModel):
    patch_id: str
    item_id: str


@method("refresh_proposal_item_validation", RefreshProposalItemValidationInput)
def refresh_proposal_item_validation(ctx: SidecarContext, params: RefreshProposalItemValidationInput) -> dict[str, Any]:
    """Re-run validation for the stored pending proposal payload, then refresh."""

    vault, _repository = ctx.require_vault()
    try:
        service_refresh_proposal_item_validation(vault.root, params.patch_id, params.item_id)
    except ValueError as exc:
        raise SidecarError("invalid_request", str(exc)) from exc
    return _proposals_payload(ctx)


class DeleteProposalItemInput(ParamsModel):
    patch_id: str
    item_id: str


@method("delete_proposal_item", DeleteProposalItemInput)
def delete_proposal_item(ctx: SidecarContext, params: DeleteProposalItemInput) -> dict[str, Any]:
    """Permanently remove a proposal item (reverting it first if applied), then refresh."""

    vault, _repository = ctx.require_vault()
    try:
        service_delete_proposal_item(vault.root, params.patch_id, params.item_id)
    except ValueError as exc:
        raise SidecarError("invalid_request", str(exc)) from exc
    # A delete may revert an applied change (touching vault files), so refresh the
    # in-memory vault — but skip the Codex runtime probe that would block on reload.
    ctx.reload(maintenance=False)
    return _proposals_payload(ctx)
