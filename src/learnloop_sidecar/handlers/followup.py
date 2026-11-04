"""FG1's RPCs: what the feedback screen's Next and its held feedback read (spec §6).

Absent a workflow, nothing here changes any reply: ``followup_status`` answers
``{"enabled": false}`` and the feedback bundle carries no ``followup`` key.
"""

from __future__ import annotations

from typing import Any

from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.dto import ParamsModel, to_camel, versioned
from learnloop_sidecar.registry import method


class FollowupInput(ParamsModel):
    attempt_id: str


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

    current = view(vault, repository, params.attempt_id) if generate_and_serve_on(vault.config) else None
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
def followup_continue_without(ctx: SidecarContext, params: FollowupInput) -> dict[str, Any]:
    from learnloop.followup_run.serving import continue_without

    _vault, repository = ctx.require_vault()
    return versioned({"continued": continue_without(repository, params.attempt_id)})


@method("followup_show_anyway", FollowupInput)
def followup_show_anyway(ctx: SidecarContext, params: FollowupInput) -> dict[str, Any]:
    from learnloop.followup_run.serving import show_anyway

    _vault, repository = ctx.require_vault()
    return versioned({"released": show_anyway(repository, params.attempt_id)})
