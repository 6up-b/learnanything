"""P2 DIAGNOSTIC track sidecar RPC (spec_p2_narrow_golden_path §5, §6, §9; design B.4-B.5).

The five-layer recipe's Python layer for the pre-authored diagnostic pack + the two-tier
failure-reason triage. Handlers compose the landed P2 services (``diagnostic_pack``,
``failure_triage``) and never touch SQL directly. Method names are dotted
(``diagnostic.*``) so the Tauri client maps them 1:1. This module owns its own handler
file per the P2 work partition -- it shares only the one-line registration in
``handlers/__init__``.
"""

from __future__ import annotations

from typing import Any

from learnloop.services import diagnostic_pack as DP
from learnloop.services import failure_triage as FT
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.dto import ParamsModel, versioned
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.registry import method


# ---------------------------------------------------------------------------
# diagnostic.pack_*
# ---------------------------------------------------------------------------

class PackAssembleInput(ParamsModel):
    pack_slug: str
    blueprint_version_id: str
    cards: list[dict[str, Any]]


@method("diagnostic.pack_assemble", PackAssembleInput)
def diagnostic_pack_assemble(ctx: SidecarContext, params: PackAssembleInput) -> dict[str, Any]:
    _vault, repository = ctx.require_vault()
    try:
        pack = DP.assemble_pack(
            repository,
            pack_slug=params.pack_slug,
            blueprint_version_id=params.blueprint_version_id,
            cards=params.cards,
        )
    except DP.InvalidPack as exc:
        raise SidecarError("invalid_pack", str(exc)) from exc
    return versioned(pack.as_dict())


class PackAdmitInput(ParamsModel):
    pack_id: str
    card_slug: str
    checks: dict[str, Any] | None = None


@method("diagnostic.pack_admit", PackAdmitInput)
def diagnostic_pack_admit(ctx: SidecarContext, params: PackAdmitInput) -> dict[str, Any]:
    _vault, repository = ctx.require_vault()
    pack = DP.admit_pack_card(
        repository, pack_id=params.pack_id, card_slug=params.card_slug, checks=params.checks
    )
    return versioned(pack.as_dict())


class PackReviewInput(ParamsModel):
    pack_id: str
    checks: dict[str, Any] | None = None


@method("diagnostic.pack_review", PackReviewInput)
def diagnostic_pack_review(ctx: SidecarContext, params: PackReviewInput) -> dict[str, Any]:
    _vault, repository = ctx.require_vault()
    try:
        pack = DP.review_pack(repository, pack_id=params.pack_id, checks=params.checks)
    except DP.InvalidPack as exc:
        raise SidecarError("invalid_pack", str(exc)) from exc
    return versioned(pack.as_dict())


class PackListInput(ParamsModel):
    blueprint_version_id: str


@method("diagnostic.pack_list", PackListInput)
def diagnostic_pack_list(ctx: SidecarContext, params: PackListInput) -> dict[str, Any]:
    _vault, repository = ctx.require_vault()
    packs = repository.diagnostic_packs_for_blueprint(params.blueprint_version_id)
    out: list[dict[str, Any]] = []
    for pack in packs:
        record = DP._load_pack(repository, pack["id"])
        out.append(record.as_dict())
    return versioned({"packs": out})


class BaselineEnterInput(ParamsModel):
    run_id: str
    learning_object_id: str
    pack_id: str
    visible_cap: int | None = None


@method("diagnostic.baseline_enter", BaselineEnterInput)
def diagnostic_baseline_enter(ctx: SidecarContext, params: BaselineEnterInput) -> dict[str, Any]:
    vault, repository = ctx.require_vault()
    try:
        result = DP.enter_baseline(
            vault,
            repository,
            run_id=params.run_id,
            learning_object_id=params.learning_object_id,
            pack_id=params.pack_id,
            visible_cap=params.visible_cap,
        )
    except DP.InvalidPack as exc:
        raise SidecarError("invalid_pack", str(exc)) from exc
    return versioned(result)


class BoundaryViewInput(ParamsModel):
    run_id: str


@method("diagnostic.boundary_view", BoundaryViewInput)
def diagnostic_boundary_view(ctx: SidecarContext, params: BoundaryViewInput) -> dict[str, Any]:
    _vault, repository = ctx.require_vault()
    try:
        view = DP.boundary_view(repository, run_id=params.run_id)
    except DP.InvalidPack as exc:
        raise SidecarError("run_not_found", str(exc)) from exc
    return versioned(view)


# ---------------------------------------------------------------------------
# diagnostic.triage_*
# ---------------------------------------------------------------------------

class TriageInput(ParamsModel):
    run_id: str
    attempt: dict[str, Any]
    routing_prior: dict[str, Any] | None = None


@method("diagnostic.triage", TriageInput)
def diagnostic_triage(ctx: SidecarContext, params: TriageInput) -> dict[str, Any]:
    _vault, repository = ctx.require_vault()
    try:
        result = FT.triage(
            repository, params.run_id, attempt=params.attempt, routing_prior=params.routing_prior
        )
    except FT.TriageError as exc:
        raise SidecarError("triage_error", str(exc)) from exc
    return versioned(result.as_dict())


class TriageStatusInput(ParamsModel):
    run_id: str


@method("diagnostic.triage_status", TriageStatusInput)
def diagnostic_triage_status(ctx: SidecarContext, params: TriageStatusInput) -> dict[str, Any]:
    _vault, repository = ctx.require_vault()
    try:
        status = FT.triage_status(repository, params.run_id)
    except FT.TriageError as exc:
        raise SidecarError("run_not_found", str(exc)) from exc
    return versioned(status)


class TriageDecideInput(ParamsModel):
    run_id: str
    triage_event_id: str
    chosen_reason: str
    actor: str = "learner"


@method("diagnostic.triage_decide", TriageDecideInput)
def diagnostic_triage_decide(ctx: SidecarContext, params: TriageDecideInput) -> dict[str, Any]:
    _vault, repository = ctx.require_vault()
    try:
        result = FT.decide(
            repository,
            params.run_id,
            triage_event_id=params.triage_event_id,
            chosen_reason=params.chosen_reason,
            actor=params.actor,
        )
    except FT.TriageError as exc:
        raise SidecarError("triage_error", str(exc)) from exc
    return versioned(result.as_dict())


class TriageOverrideInput(ParamsModel):
    run_id: str
    triage_event_id: str
    chosen_reason: str
    actor: str = "owner"


@method("diagnostic.triage_override", TriageOverrideInput)
def diagnostic_triage_override(ctx: SidecarContext, params: TriageOverrideInput) -> dict[str, Any]:
    _vault, repository = ctx.require_vault()
    try:
        result = FT.override(
            repository,
            params.run_id,
            triage_event_id=params.triage_event_id,
            chosen_reason=params.chosen_reason,
            actor=params.actor,
        )
    except FT.TriageError as exc:
        raise SidecarError("triage_error", str(exc)) from exc
    return versioned(result.as_dict())
