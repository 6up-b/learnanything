"""Learner field F2 RPCs: self-reports, placement state and the quick check.

Every write here is a placement receipt; nothing writes evidence (spec §5.2).
"""

from __future__ import annotations

from typing import Any, Literal

from learnloop.clock import utc_now_iso
from learnloop.diagnosis.quick_check import QuickCheckError, start_quick_check
from learnloop.placement.decisions import PlacementInactive, record_self_report
from learnloop.placement.state import load_placement_state, placement_active
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.dto import ParamsModel, versioned
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.registry import method


class PlacementSelfReportInput(ParamsModel):
    report: Literal["know_this", "too_easy", "dont_know_this"]
    learning_object_ids: list[str] | None = None
    practice_item_id: str | None = None


class PlacementStateInput(ParamsModel):
    learning_object_ids: list[str] | None = None


class StartQuickCheckInput(ParamsModel):
    session_id: str
    learning_object_ids: list[str]


def placement_lo_state(vault, state, learning_object_id: str, *, now_iso: str) -> dict[str, Any]:
    """One LO's placement label. ``assumed`` is an open assumption; nothing
    here claims demonstrated or untested, which the map derives from evidence."""

    open_ = state.open_by_lo.get(learning_object_id)
    latest = state.latest_by_lo.get(learning_object_id)
    return {
        "learning_object_id": learning_object_id,
        "assumed": open_ is not None,
        "label": "assumed (not tested)" if open_ is not None else None,
        "source": open_.source if open_ is not None else None,
        "first_review_due": open_.first_review_due if open_ is not None else None,
        "first_review_is_due": bool(open_ is not None and open_.first_review_due <= now_iso),
        "last_outcome": latest.status if latest is not None and latest.status != "open" else None,
        "returned_by_learner": learning_object_id in state.returned_learning_object_ids,
    }


def placement_payload(vault, repository, learning_object_ids: list[str] | None = None) -> dict[str, Any]:
    state = load_placement_state(vault, repository)
    now_iso = utc_now_iso()
    wanted = (
        sorted(set(learning_object_ids))
        if learning_object_ids is not None
        else sorted(state.open_by_lo)
    )
    return {
        "active": placement_active(vault),
        "algorithm_version": vault.config.algorithms.algorithm_version,
        "quick_check_k": vault.config.placement.quick_check_k,
        "quick_check_budget_minutes": vault.config.placement.quick_check_budget_minutes,
        "learning_objects": [
            placement_lo_state(vault, state, lo_id, now_iso=now_iso)
            for lo_id in wanted
            if lo_id in vault.learning_objects
        ],
    }


@method("get_placement_state", PlacementStateInput)
def get_placement_state(ctx: SidecarContext, params: PlacementStateInput) -> dict[str, Any]:
    vault, repository = ctx.require_vault()
    return versioned(placement_payload(vault, repository, params.learning_object_ids))


@method("placement_self_report", PlacementSelfReportInput)
def placement_self_report(ctx: SidecarContext, params: PlacementSelfReportInput) -> dict[str, Any]:
    """"I know this", "too easy" or "I don't know this" on LOs or on an item's LO.

    Routing preferences, labelled as such: they act immediately and write only
    a placement receipt (D5)."""

    vault, repository = ctx.require_vault()
    learning_object_ids = list(params.learning_object_ids or [])
    trigger_ref = None
    if params.practice_item_id is not None:
        item = vault.practice_items.get(params.practice_item_id)
        if item is None or not item.learning_object_id:
            raise SidecarError("not_found", f"Unknown practice item {params.practice_item_id}.")
        learning_object_ids.append(str(item.learning_object_id))
        trigger_ref = params.practice_item_id
    elif len(learning_object_ids) > 1:
        trigger_ref = ",".join(sorted(set(learning_object_ids)))
    if not learning_object_ids:
        raise SidecarError("invalid_request", "Name learning objects or a practice item.")
    try:
        result = record_self_report(
            vault,
            repository,
            learning_object_ids=learning_object_ids,
            report=params.report,
            trigger_ref=trigger_ref,
        )
    except PlacementInactive as error:
        raise SidecarError("placement_inactive", str(error)) from error
    return versioned({
        **result,
        "placement": placement_payload(vault, repository, sorted(set(learning_object_ids))),
    })


@method("start_quick_check", StartQuickCheckInput)
def start_quick_check_handler(ctx: SidecarContext, params: StartQuickCheckInput) -> dict[str, Any]:
    """"Check what I already know": a short, never-prompted calibration session."""

    vault, repository = ctx.require_vault()
    try:
        progress = start_quick_check(
            vault,
            repository,
            session_id=params.session_id,
            learning_object_ids=params.learning_object_ids,
        )
    except QuickCheckError as error:
        raise SidecarError("invalid_request", str(error)) from error
    return versioned(progress)
