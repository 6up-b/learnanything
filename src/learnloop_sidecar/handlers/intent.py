"""Daily-loop DL2 RPCs: the single intent control (spec §5.2) and deadlines (§5.4).

``get_intent`` returns a scope's current setting and, for every choice, the
plain-language consequence ("replaces your earlier setting on …") and the
projected cost ("about N min/day of reviews"), both computed by the very
resolution serving uses. ``set_intent`` applies one choice through the
commitments API. ``set_intent_deadline`` adds or moves a deadline (a learner
goal linked by the commitment version's ``goal_id``) and reloads the vault.

Desktop only (never on the phone allowlist). Below the successor
``mvp-0.29``, or with ``intent.enabled`` off, ``get_intent`` answers
``{"enabled": false}`` and the two writes refuse.
"""

from __future__ import annotations

from typing import Any

from learnloop.daily_plan.intent_cost import cost_function
from learnloop.intent.control import IntentControlError, Scope, apply_choice, describe
from learnloop.intent.deadline import set_deadline
from learnloop.scheduling.intent.model import SCOPE_KINDS
from learnloop.scheduling.intent.serving import intent_enabled
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.dto import ParamsModel, versioned
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.registry import method

INTENT_RPCS = ("get_intent", "set_intent", "set_intent_deadline")


class IntentScopeInput(ParamsModel):
    scope_kind: str
    scope_id: str


class SetIntentInput(IntentScopeInput):
    choice: str


class SetIntentDeadlineInput(IntentScopeInput):
    due_at: str


def _scope(params: IntentScopeInput) -> Scope:
    if params.scope_kind not in SCOPE_KINDS:
        raise SidecarError("intent_scope_invalid", f"Unknown scope kind: {params.scope_kind}.")
    return Scope(params.scope_kind, params.scope_id)


def _describe(vault: Any, repository: Any, scope: Scope) -> dict[str, Any]:
    return describe(vault, repository, scope, cost=cost_function(vault, repository))


def _require_enabled(vault: Any) -> None:
    if not intent_enabled(vault.config):
        raise SidecarError(
            "intent_disabled",
            "Intent settings are off for this vault (they need algorithm version mvp-0.29 or later "
            "and intent.enabled = true).",
        )


@method("get_intent", IntentScopeInput)
def get_intent(ctx: SidecarContext, params: IntentScopeInput) -> dict[str, Any]:
    vault, repository = ctx.require_vault()
    if not intent_enabled(vault.config):
        return versioned({"enabled": False})
    try:
        view = _describe(vault, repository, _scope(params))
    except IntentControlError as error:
        return versioned({"enabled": True, "available": False, "reason": str(error)})
    return versioned({"enabled": True, "available": True, **view})


@method("set_intent", SetIntentInput)
def set_intent(ctx: SidecarContext, params: SetIntentInput) -> dict[str, Any]:
    vault, repository = ctx.require_vault()
    _require_enabled(vault)
    scope = _scope(params)
    try:
        applied = apply_choice(vault, repository, scope, params.choice)
        view = _describe(vault, repository, scope)
    except IntentControlError as error:
        raise SidecarError("intent_choice_invalid", str(error)) from error
    return versioned({"enabled": True, "available": True, "applied": applied.as_dict(), **view})


@method("set_intent_deadline", SetIntentDeadlineInput)
def set_intent_deadline(ctx: SidecarContext, params: SetIntentDeadlineInput) -> dict[str, Any]:
    vault, repository = ctx.require_vault()
    _require_enabled(vault)
    scope = _scope(params)
    try:
        result = set_deadline(vault, repository, scope, params.due_at)
    except IntentControlError as error:
        raise SidecarError("intent_deadline_invalid", str(error)) from error
    ctx.reload(maintenance=False)
    vault, repository = ctx.require_vault()
    view = _describe(vault, repository, scope)
    return versioned({"enabled": True, "available": True, "deadline_set": result, **view})


__all__ = ["INTENT_RPCS"]
