"""FG1's RPCs: what the feedback screen's Next and its held feedback read (spec §6).

Absent a workflow, nothing here changes any reply: ``followup_status`` answers
``{"enabled": false}`` and the feedback bundle carries no ``followup`` key.
"""

from __future__ import annotations

from typing import Any

from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.dto import ParamsModel, to_camel, versioned
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.registry import method
from learnloop_sidecar.request_origin import host_mutation


class FollowupInput(ParamsModel):
    attempt_id: str


class HypothesisExposureInput(ParamsModel):
    attempt_id: str
    surface: str
    #: Causal-hypothesis version ids, in the order on screen.
    hypothesis_version_ids: list[str]
    shown_at: str | None = None


class HypothesisMarkInput(ParamsModel):
    attempt_id: str
    mark: str
    hypothesis_version_id: str | None = None
    free_text: str | None = None
    surface: str = "marks_feedback"


def _fresh_vault(ctx: SidecarContext, vault: Any, repository: Any, attempt_id: str) -> Any:
    """The worker wrote the question on its own slot: this process's vault reads it now."""

    from learnloop.followup_serve.workflow import attempt_workflow

    row = attempt_workflow(repository, attempt_id)
    item_id = row.get("practice_item_id") if row else None
    if item_id and str(item_id) not in vault.practice_items:
        ctx.reload(maintenance=False)
        vault, _repository = ctx.require_vault()
    return vault


@method("followup_status", FollowupInput)
def followup_status(ctx: SidecarContext, params: FollowupInput) -> dict[str, Any]:
    from learnloop.followup_run.serving import view

    vault, repository = ctx.require_vault()
    vault = _fresh_vault(ctx, vault, repository, params.attempt_id)
    from learnloop.followup_serve.gates import generate_and_serve_on

    phone = ctx.request_origin is not None  # FG1 §10: its question waits for the desktop until V3
    current = view(vault, repository, params.attempt_id, phone=phone) if generate_and_serve_on(vault.config) else None
    if current is None:
        return versioned({"enabled": False})
    ctx.resume_post_attempt_jobs()
    return versioned({"enabled": True, **to_camel(current)})


@method("followup_next", FollowupInput)
def followup_next(ctx: SidecarContext, params: FollowupInput) -> dict[str, Any]:
    """Next pressed (§6.1): wait, open the probe, or go on with the plan or the queue."""

    from learnloop.followup_run.serving import next_action, plan_will_place

    vault, repository = ctx.require_vault()
    vault = _fresh_vault(ctx, vault, repository, params.attempt_id)
    action = next_action(vault, repository, params.attempt_id,
                         plan_serves=plan_will_place(vault, repository, params.attempt_id))
    ctx.resume_post_attempt_jobs()
    return versioned(to_camel({
        "action": action.action, "line": action.line, "practice_item_id": action.practice_item_id,
        "presentation_id": action.presentation_id,
    }))


@method("followup_continue_without", FollowupInput)
@host_mutation
def followup_continue_without(ctx: SidecarContext, params: FollowupInput) -> dict[str, Any]:
    from learnloop.followup_run.serving import continue_without

    _vault, repository = ctx.require_vault()
    return versioned({"continued": continue_without(repository, params.attempt_id)})


@method("followup_show_anyway", FollowupInput)
def followup_show_anyway(ctx: SidecarContext, params: FollowupInput) -> dict[str, Any]:
    from learnloop.followup_run.serving import show_anyway

    _vault, repository = ctx.require_vault()
    return versioned({"released": show_anyway(repository, params.attempt_id)})


@method("record_hypothesis_exposure", HypothesisExposureInput)
def record_hypothesis_exposure(ctx: SidecarContext, params: HypothesisExposureInput) -> dict[str, Any]:
    """FG1c, spec_router_objective_v1 §4 row 6: the client's display event. A refused receipt rolls
    back alone with a warning, so this never fails."""

    from learnloop.followup_run.marks import record_exposure

    vault, repository = ctx.require_vault()
    exposure_id = record_exposure(vault, repository, attempt_id=params.attempt_id, surface=params.surface,
                                  hypothesis_version_ids=params.hypothesis_version_ids, shown_at=params.shown_at)
    return versioned({"recorded": exposure_id is not None})


@method("record_hypothesis_mark", HypothesisMarkInput)
def record_hypothesis_mark(ctx: SidecarContext, params: HypothesisMarkInput) -> dict[str, Any]:
    """FG1c, spec §7: one optional mark, appended. Returns the panel's new read."""

    from learnloop.followup_run.marks import MarkRefused, record_mark

    vault, repository = ctx.require_vault()
    try:
        current = record_mark(vault, repository, attempt_id=params.attempt_id, mark=params.mark,
                              hypothesis_version_id=params.hypothesis_version_id, free_text=params.free_text,
                              surface=params.surface)
    except MarkRefused as exc:
        raise SidecarError("validation_error", str(exc)) from exc
    return versioned({"recorded": current is not None, "marks": to_camel(current) if current is not None else None})
