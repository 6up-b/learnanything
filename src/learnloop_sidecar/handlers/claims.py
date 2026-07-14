from __future__ import annotations

from typing import Any

from learnloop.services.hypothesis_claims import (
    HypothesisClaimError,
    dismiss_claim,
    export_claim_events,
    present_claims,
    purge_claim_events,
    record_response,
)
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.dto import ParamsModel, versioned
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.registry import method


class ClaimCandidateInput(ParamsModel):
    claim_class: str
    claim_type: str
    claim_ref: Any
    claim_version: str
    producer_version: str
    surface: str
    temperature: str
    visible_at: str | None = None
    cold_reask: bool = False
    claim_text: str | None = None
    provenance: str | None = None
    receipt_ref: str | None = None


class PresentClaimsInput(ParamsModel):
    claims: list[ClaimCandidateInput]
    session_id: str | None = None
    visit_id: str | None = None


class RespondClaimInput(ParamsModel):
    presentation_id: str
    response_payload: dict[str, Any]


class DismissClaimInput(ParamsModel):
    presentation_id: str


@method("present_claims", PresentClaimsInput)
def present_claims_handler(ctx: SidecarContext, params: PresentClaimsInput) -> dict[str, Any]:
    vault, repository = ctx.require_vault()
    try:
        presentations = present_claims(
            repository,
            [claim.model_dump() for claim in params.claims],
            session_id=params.session_id,
            visit_id=params.visit_id,
            session_card_budget=vault.config.hypothesis.session_card_budget,
            claim_cooldown_days=vault.config.hypothesis.claim_cooldown_days,
        )
    except HypothesisClaimError as exc:
        raise SidecarError("invalid_request", str(exc)) from exc
    return versioned({"claims": presentations})


@method("respond_claim", RespondClaimInput)
def respond_claim_handler(ctx: SidecarContext, params: RespondClaimInput) -> dict[str, Any]:
    _vault, repository = ctx.require_vault()
    try:
        event = record_response(repository, params.presentation_id, params.response_payload)
    except HypothesisClaimError as exc:
        raise SidecarError("invalid_request", str(exc)) from exc
    return versioned({"event": event})


@method("dismiss_claim", DismissClaimInput)
def dismiss_claim_handler(ctx: SidecarContext, params: DismissClaimInput) -> dict[str, Any]:
    _vault, repository = ctx.require_vault()
    try:
        event = dismiss_claim(repository, params.presentation_id)
    except HypothesisClaimError as exc:
        raise SidecarError("invalid_request", str(exc)) from exc
    return versioned({"event": event})


@method("export_claims")
def export_claims_handler(ctx: SidecarContext, _params: ParamsModel) -> dict[str, Any]:
    _vault, repository = ctx.require_vault()
    return versioned({"events": export_claim_events(repository)})


@method("purge_claims")
def purge_claims_handler(ctx: SidecarContext, _params: ParamsModel) -> dict[str, Any]:
    _vault, repository = ctx.require_vault()
    return versioned({"purged": purge_claim_events(repository)})
