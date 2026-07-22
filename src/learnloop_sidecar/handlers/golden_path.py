"""P2 golden-path spine sidecar RPC (spec_p2_narrow_golden_path §9; design B.1-B.3).

The five-layer recipe's Python layer: blueprint register/review/get + the atomic
confirmation and run-state/advance endpoints. Handlers compose the landed P2 services
and never touch SQL directly. Method names are dotted (``golden_path.*`` / ``blueprint.*``)
per the design so the Tauri client maps them 1:1.
"""

from __future__ import annotations

from typing import Any

from learnloop.services import golden_path_compose as GPX
from learnloop.services import golden_path_confirm as GPC
from learnloop.services import golden_path_run as GPR
from learnloop.services import task_blueprints as TB
from learnloop.services.activities import resolve_legacy_item
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.dto import ParamsModel, versioned
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.registry import method


# ---------------------------------------------------------------------------
# blueprint.*
# ---------------------------------------------------------------------------

class RegisterBlueprintInput(ParamsModel):
    blueprint_slug: str
    spec: dict[str, Any]
    authoring_version: str = "stub-1"


@method("blueprint.register", RegisterBlueprintInput)
def blueprint_register(ctx: SidecarContext, params: RegisterBlueprintInput) -> dict[str, Any]:
    _vault, repository = ctx.require_vault()
    try:
        version = TB.register_blueprint_version(
            repository,
            blueprint_slug=params.blueprint_slug,
            spec=params.spec,
            authoring_version=params.authoring_version,
        )
    except TB.InvalidBlueprint as exc:
        raise SidecarError("invalid_blueprint", str(exc)) from exc
    return versioned(_blueprint_dto(version))


class ReviewBlueprintInput(ParamsModel):
    blueprint_version_id: str
    checks: dict[str, Any] | None = None


@method("blueprint.review", ReviewBlueprintInput)
def blueprint_review(ctx: SidecarContext, params: ReviewBlueprintInput) -> dict[str, Any]:
    _vault, repository = ctx.require_vault()
    version = TB.review_blueprint_version(
        repository, blueprint_version_id=params.blueprint_version_id, checks=params.checks
    )
    return versioned(_blueprint_dto(version))


class BlueprintVersionInput(ParamsModel):
    blueprint_version_id: str


@method("blueprint.get_version", BlueprintVersionInput)
def blueprint_get_version(ctx: SidecarContext, params: BlueprintVersionInput) -> dict[str, Any]:
    _vault, repository = ctx.require_vault()
    row = repository.task_blueprint_version(params.blueprint_version_id)
    if row is None:
        raise SidecarError("blueprint_not_found", f"blueprint version {params.blueprint_version_id} not found")
    version = TB._load_version(repository, params.blueprint_version_id)
    return versioned(_blueprint_dto(version))


class DiscoverCandidatesInput(ParamsModel):
    learning_object_id: str | None = None


@method("blueprint.discover_candidates", DiscoverCandidatesInput)
def blueprint_discover_candidates(
    ctx: SidecarContext, params: DiscoverCandidatesInput
) -> dict[str, Any]:
    """The library exemplar pool (§3.1 discovery, previously deferred): active
    practice items grouped by learning object, with freshness for the held-out
    pick."""

    vault, repository = ctx.require_vault()
    pool = GPX.discover_exemplar_pool(
        vault, repository, learning_object_id=params.learning_object_id
    )
    return versioned({"pool": pool})


class ComposeBlueprintDraftInput(ParamsModel):
    learning_object_id: str
    anchor_item_ids: list[str]
    held_out_item_id: str
    title: str | None = None
    blueprint_slug: str | None = None


@method("blueprint.compose_draft", ComposeBlueprintDraftInput)
def blueprint_compose_draft(
    ctx: SidecarContext, params: ComposeBlueprintDraftInput
) -> dict[str, Any]:
    """Compose a picker selection into a registered DRAFT blueprint version plus
    the matching confirm ingredients. The draft still goes through the existing
    owner review (`blueprint.review`) before confirmation can succeed."""

    vault, repository = ctx.require_vault()
    try:
        composed = GPX.compose_blueprint_draft(
            vault,
            repository,
            learning_object_id=params.learning_object_id,
            anchor_item_ids=params.anchor_item_ids,
            held_out_item_id=params.held_out_item_id,
            title=params.title,
        )
        version = TB.register_blueprint_version(
            repository,
            blueprint_slug=params.blueprint_slug or f"bp_{params.learning_object_id}",
            spec=composed["spec"],
            authoring_version="picker-template-1",
        )
    except GPX.ComposeError as exc:
        raise SidecarError("validation_error", str(exc)) from exc
    except TB.InvalidBlueprint as exc:
        raise SidecarError("invalid_blueprint", str(exc)) from exc
    import json as _jsonlib

    return versioned(
        {
            "blueprint": _blueprint_dto(version),
            # As a STRING so the camelizing DTO layer cannot rewrite the body's
            # snake_case keys -- it round-trips verbatim into golden_path.confirm.
            "contractBodyJson": _jsonlib.dumps(composed["contract_body"]),
            "sourceRev": composed["source_rev"],
            "unitId": composed["unit_id"],
            "heldOutItemId": composed["held_out_item_id"],
            "warnings": composed["warnings"],
        }
    )


def _blueprint_dto(version: TB.BlueprintVersion) -> dict[str, Any]:
    return {
        "blueprint_version_id": version.id,
        "blueprint_id": version.blueprint_id,
        "version": version.version,
        "status": version.status,
        "content_hash": version.content_hash,
        "minted": version.minted,
        "exemplars": [dict(e) for e in version.exemplars],
    }


# ---------------------------------------------------------------------------
# golden_path.*
# ---------------------------------------------------------------------------

class ConfirmInput(ParamsModel):
    goal_id: str
    blueprint_version_id: str
    contract_body: dict[str, Any]
    depth_preset: str
    source_rev: str
    unit_id: str
    action: str = "select_exemplar"
    assessment_surface_id: str | None = None
    assessment_practice_item_id: str | None = None


@method("golden_path.confirm", ConfirmInput)
def golden_path_confirm(ctx: SidecarContext, params: ConfirmInput) -> dict[str, Any]:
    vault, repository = ctx.require_vault()

    surface_id = params.assessment_surface_id
    if surface_id is None and params.assessment_practice_item_id is not None:
        item = vault.practice_items.get(params.assessment_practice_item_id)
        if item is None:
            raise SidecarError(
                "assessment_item_not_found",
                f"practice item {params.assessment_practice_item_id} not in vault",
            )
        resolved = resolve_legacy_item(vault, repository, item, purpose="assessment")
        surface_id = resolved.surface_id

    try:
        receipt = GPC.confirm_exemplar_and_start(
            repository,
            goal_id=params.goal_id,
            blueprint_version_id=params.blueprint_version_id,
            contract_body=params.contract_body,
            depth_preset=params.depth_preset,
            source_rev=params.source_rev,
            unit_id=params.unit_id,
            action=params.action,
            assessment_surface_id=surface_id,
        )
    except GPC.NotConfirmable as exc:
        raise SidecarError("not_confirmable", exc.reason) from exc
    except Exception as exc:  # BlueprintNotReviewed / GoalAlreadyConfirmed
        raise SidecarError("confirmation_refused", str(exc)) from exc
    return versioned(receipt.as_dict())


class RunStatusInput(ParamsModel):
    run_id: str


@method("golden_path.run_status", RunStatusInput)
def golden_path_run_status(ctx: SidecarContext, params: RunStatusInput) -> dict[str, Any]:
    _vault, repository = ctx.require_vault()
    try:
        state = GPR.project_run(repository, params.run_id)
    except ValueError as exc:
        raise SidecarError("run_not_found", str(exc)) from exc
    return versioned(_run_state_dto(state))


class ListRunsInput(ParamsModel):
    pass


@method("golden_path.list_runs", ListRunsInput)
def golden_path_list_runs(ctx: SidecarContext, params: ListRunsInput) -> dict[str, Any]:
    """Every confirmed run with its cached state — the desktop's re-entry point.
    A run spans days; without this list an in-flight run would be unreachable
    after an app restart (the screen only holds the run id in memory)."""

    _vault, repository = ctx.require_vault()
    runs = [
        {
            "run_id": run["id"],
            "goal_id": run["goal_id"],
            "current_state": run["current_state"],
            "mode": run["mode"],
            "milestone": run.get("initial_milestone"),
            "blueprint_version_id": run["blueprint_version_id"],
            "created_at": run["created_at"],
        }
        for run in repository.golden_path_runs_all()
    ]
    return versioned({"runs": runs})


class AdvanceInput(ParamsModel):
    run_id: str
    to_state: str
    reason: str
    idempotency_key: str
    expected_head_event_id: str | None = None
    successor_milestone: str | None = None


@method("golden_path.advance", AdvanceInput)
def golden_path_advance(ctx: SidecarContext, params: AdvanceInput) -> dict[str, Any]:
    _vault, repository = ctx.require_vault()
    try:
        result = GPR.advance(
            repository,
            params.run_id,
            to_state=params.to_state,
            reason=params.reason,
            idempotency_key=params.idempotency_key,
            expected_head_event_id=params.expected_head_event_id,
            successor_milestone=params.successor_milestone,
        )
    except GPR.IllegalTransition as exc:
        raise SidecarError("illegal_transition", str(exc)) from exc
    except GPR.StaleRunHead as exc:
        raise SidecarError("stale_run_head", str(exc), retryable=True) from exc
    state = GPR.project_run(repository, params.run_id)
    return versioned({"result": result.as_dict(), "state": _run_state_dto(state)})


def _run_state_dto(state: GPR.RunState) -> dict[str, Any]:
    return {
        "run_id": state.run_id,
        "current_state": state.current_state,
        "head_event_id": state.head_event_id,
        "head_seq": state.head_seq,
        "mode": state.mode,
        "milestone": state.milestone,
        "goal_contract_head_version_id": state.goal_contract_head_version_id,
        "event_count": state.event_count,
        "next_action": state.next_action.as_dict(),
        "history": [dict(h) for h in state.history],
    }
