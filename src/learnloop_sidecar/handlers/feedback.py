from __future__ import annotations

from typing import Any

from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.dto import ParamsModel
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.handlers.serializers import attempt_detail, feedback_bundle
from learnloop_sidecar.logging import log_event
from learnloop_sidecar.registry import method


class AttemptInput(ParamsModel):
    attempt_id: str


class TriggerRegradeInput(ParamsModel):
    attempt_id: str


class AddErrorEventInput(ParamsModel):
    attempt_id: str
    error_type: str
    severity: float = 0.5


@method("get_feedback", AttemptInput)
def get_feedback(ctx: SidecarContext, params: AttemptInput) -> dict[str, Any]:
    vault, repository = ctx.require_vault()
    attempt = repository.fetch_practice_attempt(params.attempt_id)
    session_id = attempt.get("session_id") if attempt is not None else None
    repository.record_feedback_shown(params.attempt_id, session_id=session_id)
    bundle = feedback_bundle(vault, repository, params.attempt_id)
    log_event(
        "feedback_shown",
        session_id=session_id,
        attempt_id=params.attempt_id,
        practice_item_id=bundle.get("practiceItemId"),
        feedback_md=bundle.get("feedbackMd"),
        followup_queued=bundle.get("followupQueued"),
        triggered_actions=(bundle.get("surprise") or {}).get("triggeredActions"),
        suppressed_actions=(bundle.get("surprise") or {}).get("suppressedActions"),
    )
    return bundle


@method("get_attempt", AttemptInput)
def get_attempt(ctx: SidecarContext, params: AttemptInput) -> dict[str, Any]:
    vault, repository = ctx.require_vault()
    return attempt_detail(vault, repository, params.attempt_id)


@method("trigger_regrade", TriggerRegradeInput)
def trigger_regrade(ctx: SidecarContext, params: TriggerRegradeInput) -> dict[str, Any]:
    from learnloop.ai.client import make_ai_provider_client
    from learnloop.ai.routing import fallback_provider_for, provider_for_task
    from learnloop.ai.runtime import check_ai_runtime
    from learnloop.codex.client import make_codex_client
    from learnloop.codex.runtime import check_codex_runtime
    from learnloop.services.regrade import _regrade_attempt

    vault, repository = ctx.require_vault()
    attempt = repository.fetch_practice_attempt(params.attempt_id)
    if attempt is None:
        raise SidecarError("not_found", f"Attempt {params.attempt_id} not found.")
    selection = provider_for_task(vault.config, "grading")
    provider_name = selection.provider_name
    runtime = check_codex_runtime(vault.root, vault.config.codex) if provider_name == "codex" else check_ai_runtime(vault.root, vault.config, provider_name=provider_name)
    if not runtime.ready:
        fallback = fallback_provider_for(vault.config, selection)
        if fallback == "codex":
            fallback_runtime = check_codex_runtime(vault.root, vault.config.codex)
            if fallback_runtime.ready:
                provider_name = "codex"
                runtime = fallback_runtime
    if not runtime.ready:
        label = "Codex" if provider_name == "codex" else f"AI provider {provider_name}"
        raise SidecarError("ai_unavailable", f"{label} is {runtime.status}; regrade requires an AI provider.")
    client = make_codex_client(vault.config.codex, vault.root) if provider_name == "codex" else make_ai_provider_client(vault.config, vault.root, provider_name=provider_name)
    _regrade_attempt(
        vault,
        repository,
        attempt,
        runtime=runtime,
        client=client,
        grading_source="codex" if provider_name == "codex" else "ai",
        clock=None,
    )
    return feedback_bundle(vault, repository, params.attempt_id)


@method("add_error_event", AddErrorEventInput)
def add_error_event(ctx: SidecarContext, params: AddErrorEventInput) -> dict[str, Any]:
    from learnloop.clock import utc_now_iso
    from learnloop.ids import new_ulid

    vault, repository = ctx.require_vault()
    attempt = repository.fetch_practice_attempt(params.attempt_id)
    if attempt is None:
        raise SidecarError("not_found", f"Attempt {params.attempt_id} not found.")
    now = utc_now_iso()
    repository.insert_error_event({
        "id": new_ulid(),
        "attempt_id": params.attempt_id,
        "learning_object_id": attempt["learning_object_id"],
        "error_type": params.error_type,
        "severity": params.severity,
        "is_misconception": False,
        "repair_plan": None,
        "status": "active",
        "created_at": now,
        "updated_at": now,
    })
    return feedback_bundle(vault, repository, params.attempt_id)
