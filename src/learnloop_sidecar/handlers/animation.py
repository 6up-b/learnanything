"""Concept explainer-animation RPCs (spec_fork_features §2).

Flow: the inspector calls ``get_animation_runtime`` to gate the button (manim
installed? feature enabled? which model?), ``request_concept_animation`` with
an explicit consent flag (fail-fast on a missing manim BEFORE any model
spend), then polls ``get_concept_animation_status`` while the durable job
generates/validates/renders. Video bytes never cross the RPC channel — the
completed row names a content-addressed mp4 served over llmedia://.
"""

from __future__ import annotations

from typing import Any

from learnloop.ai.routing import provider_for_task
from learnloop.services.concept_animation import (
    ConceptAnimationError,
    manim_runtime,
    request_concept_animation as run_request,
    resolve_manim_command,
)
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.dto import EmptyParams, ParamsModel, versioned
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.registry import method


def _animation_row_payload(row: dict[str, Any]) -> dict[str, Any]:
    payload = {
        "animation_id": row["id"],
        "concept_id": row["concept_id"],
        "learning_object_id": row.get("learning_object_id"),
        "status": row["status"],
        "title": row.get("title"),
        "narration_md": row.get("narration_md"),
        "video_file_name": row.get("video_file_name"),
        "duration_seconds": row.get("duration_seconds"),
        "provider": row.get("provider"),
        "model": row.get("model"),
        "failure_stage": row.get("failure_stage"),
        "failure_reason": row.get("failure_reason"),
        "created_at": row.get("created_at"),
        "completed_at": row.get("completed_at"),
    }
    if row["status"] == "failed":
        # Debug payload only on failure: the scene code + stderr tail let the
        # learner (or a bug report) see exactly what was attempted.
        payload["scene_code"] = row.get("scene_code")
        payload["render_stderr"] = row.get("render_stderr")
    return payload


@method("get_animation_runtime", EmptyParams)
def get_animation_runtime(ctx: SidecarContext, _params: EmptyParams) -> dict[str, Any]:
    vault, _repository = ctx.require_vault()
    config = vault.config
    probe = manim_runtime(
        manim_command=resolve_manim_command(config.animation, vault.root)
    )
    selection = provider_for_task(config, "animation")
    profile = config.ai.providers.get(selection.provider_name)
    return versioned(
        {
            "enabled": config.animation.enabled,
            "manim_available": probe["available"],
            "manim_version": probe["version"],
            "manim_reason": probe["reason"],
            "provider": selection.provider_name,
            "model": profile.model if profile is not None else None,
            "timeout_seconds": config.animation.timeout_seconds,
        }
    )


class RequestConceptAnimationInput(ParamsModel):
    concept_id: str
    learning_object_id: str | None = None
    consent: bool = False


@method("request_concept_animation", RequestConceptAnimationInput)
def request_concept_animation(ctx: SidecarContext, params: RequestConceptAnimationInput) -> dict[str, Any]:
    vault, repository = ctx.require_vault()
    config = vault.config
    if not params.consent:
        raise SidecarError(
            "consent_required",
            "Generating an animation runs AI-written code locally; tick the consent box first.",
        )
    if not config.animation.enabled:
        raise SidecarError("animation_disabled", "[animation] enabled is false in learnloop.toml.")
    probe = manim_runtime(
        manim_command=resolve_manim_command(config.animation, vault.root)
    )
    if not probe["available"]:
        raise SidecarError(
            "manim_missing",
            "manim is not installed: "
            f"{probe['reason']}. Install with: pip install 'learnloop[animation]' "
            "(verify with: python -m manim --version).",
        )
    try:
        summary = run_request(
            vault,
            repository,
            concept_id=params.concept_id,
            learning_object_id=params.learning_object_id,
            consent=params.consent,
        )
    except ConceptAnimationError as exc:
        raise SidecarError(exc.code, str(exc))
    batch_id = ctx.ingest_jobs.enqueue_concept_animation(animation_id=summary["animation_id"])
    repository.update_concept_animation(summary["animation_id"], batch_id=batch_id)
    return versioned({**summary, "batch_id": batch_id})


class ConceptAnimationStatusInput(ParamsModel):
    animation_id: str


@method("get_concept_animation_status", ConceptAnimationStatusInput)
def get_concept_animation_status(ctx: SidecarContext, params: ConceptAnimationStatusInput) -> dict[str, Any]:
    _vault, repository = ctx.require_vault()
    row = repository.concept_animation(params.animation_id)
    if row is None:
        raise SidecarError("animation_not_found", f"Animation '{params.animation_id}' was not found.")
    return versioned(_animation_row_payload(row))


class ConceptAnimationsForConceptInput(ParamsModel):
    concept_id: str
    limit: int = 10


@method("list_concept_animations", ConceptAnimationsForConceptInput)
def list_concept_animations(ctx: SidecarContext, params: ConceptAnimationsForConceptInput) -> dict[str, Any]:
    _vault, repository = ctx.require_vault()
    rows = repository.concept_animations_for_concept(params.concept_id, limit=params.limit)
    return versioned({"animations": [_animation_row_payload(row) for row in rows]})
