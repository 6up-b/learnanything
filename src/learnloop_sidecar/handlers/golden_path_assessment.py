"""P2 ASSESSMENT + RESTORATION + MILESTONE track -- sidecar RPC
(spec_p2_narrow_golden_path §9; design B.8-B.10).

Own handler module (kept separate from the spine's ``golden_path`` handlers). The
Python layer of the five-layer recipe: cold-assessment enter/submit/status,
restoration + boundary-diff fetch, and the milestone / depth-invitation fetch plus
the EXPLICIT learner accept/decline endpoints. Every handler composes a landed P2
service and never touches SQL directly.

The accept endpoint records intent as a non-pinnable draft and MUST NOT activate a
depth edge or append an authorized successor while U-018 is off (§7.5).
"""

from __future__ import annotations

from typing import Any

from learnloop.services import golden_path_assessment as GA
from learnloop.services import golden_path_restoration as GRstr
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.dto import ParamsModel, versioned
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.registry import method


class RunIdInput(ParamsModel):
    run_id: str


@method("golden_path.assess_open", RunIdInput)
def assess_open(ctx: SidecarContext, params: RunIdInput) -> dict[str, Any]:
    vault, repository = ctx.require_vault()
    try:
        admin = GA.open_assessment(
            repository, run_id=params.run_id, idempotency_key=f"assess_open:{params.run_id}"
        )
    except GA.PracticeOnlyNoAssessment as exc:
        raise SidecarError("practice_only_no_assessment", str(exc)) from exc
    except GA.ReserveInvalid as exc:
        raise SidecarError("assessment_reserve_invalid", str(exc), retryable=True) from exc
    payload = admin.as_dict()
    # The live screen must render the cold question: attach the surface's item
    # prompt (and its id + rubric ceiling for the self-grade) -- never the
    # expected answer, which stays hidden until after submission.
    surface = repository.fetch_surface(admin.surface_id)
    item_id = (surface or {}).get("legacy_practice_item_id")
    item = vault.practice_items.get(item_id) if item_id else None
    if item is not None:
        rubric = item.grading_rubric
        payload.update(
            practice_item_id=item.id,
            prompt=item.prompt,
            max_points=rubric.max_points if rubric is not None else 4,
        )
    return versioned(payload)


class AssessSubmitInput(ParamsModel):
    run_id: str
    administration_id: str
    surface_id: str
    rubric_score: int
    max_points: int
    attempt_id: str
    response_text: str | None = None
    grader_confidence: float | None = None
    has_fatal: bool = False
    feedback_condition: str | None = None
    reveal_feedback: bool = True


@method("golden_path.assess_submit", AssessSubmitInput)
def assess_submit(ctx: SidecarContext, params: AssessSubmitInput) -> dict[str, Any]:
    vault, repository = ctx.require_vault()
    surface = repository.fetch_surface(params.surface_id)
    if surface is None:
        raise SidecarError("surface_not_found", f"surface {params.surface_id} not found")
    item_id = surface.get("legacy_practice_item_id")
    item = vault.practice_items.get(item_id) if item_id else None
    if item is None:
        raise SidecarError("assessment_item_not_found", f"no practice item for surface {params.surface_id}")
    result = GA.submit_assessment(
        vault,
        repository,
        run_id=params.run_id,
        administration_id=params.administration_id,
        item=item,
        surface_id=params.surface_id,
        rubric_score=params.rubric_score,
        max_points=params.max_points,
        attempt_id=params.attempt_id,
        response_text=params.response_text,
        grader_confidence=params.grader_confidence,
        has_fatal=params.has_fatal,
        feedback_condition=params.feedback_condition,
        reveal_feedback=params.reveal_feedback,
    )
    return versioned(result.as_dict())


@method("golden_path.assess_result", RunIdInput)
def assess_result(ctx: SidecarContext, params: RunIdInput) -> dict[str, Any]:
    _vault, repository = ctx.require_vault()
    result = GA.assessment_result(repository, run_id=params.run_id)
    if result is None:
        raise SidecarError("no_assessment_result", f"run {params.run_id} has no assessment result")
    return versioned(result)


@method("golden_path.restore", RunIdInput)
def restore(ctx: SidecarContext, params: RunIdInput) -> dict[str, Any]:
    _vault, repository = ctx.require_vault()
    try:
        receipt = GRstr.restore(
            repository, run_id=params.run_id, idempotency_key=f"restore:{params.run_id}"
        )
    except ValueError as exc:
        raise SidecarError("restore_unavailable", str(exc)) from exc
    return versioned(receipt.as_dict())


@method("golden_path.boundary_diff", RunIdInput)
def boundary_diff(ctx: SidecarContext, params: RunIdInput) -> dict[str, Any]:
    _vault, repository = ctx.require_vault()
    row = repository.latest_golden_path_artifact(params.run_id, kind="boundary_diff")
    if row is None:
        raise SidecarError("no_boundary_diff", f"run {params.run_id} has no boundary diff")
    import json

    return versioned(json.loads(row["payload_json"]))


@method("golden_path.depth_invitation", RunIdInput)
def depth_invitation(ctx: SidecarContext, params: RunIdInput) -> dict[str, Any]:
    _vault, repository = ctx.require_vault()
    row = repository.latest_golden_path_artifact(params.run_id, kind="depth_invitation")
    milestone = repository.latest_golden_path_artifact(params.run_id, kind="milestone")
    import json

    return versioned({
        "invitation": json.loads(row["payload_json"]) if row is not None else None,
        "milestone": json.loads(milestone["payload_json"]) if milestone is not None else None,
    })


@method("golden_path.accept_edge", RunIdInput)
def accept_edge(ctx: SidecarContext, params: RunIdInput) -> dict[str, Any]:
    _vault, repository = ctx.require_vault()
    try:
        payload = GRstr.accept_depth_invitation(
            repository, run_id=params.run_id, idempotency_key=f"accept:{params.run_id}"
        )
    except ValueError as exc:
        raise SidecarError("no_depth_invitation", str(exc)) from exc
    return versioned(payload)


class DeclineInput(ParamsModel):
    run_id: str
    reason: str | None = None


@method("golden_path.decline_edge", DeclineInput)
def decline_edge(ctx: SidecarContext, params: DeclineInput) -> dict[str, Any]:
    _vault, repository = ctx.require_vault()
    payload = GRstr.decline_depth_invitation(
        repository, run_id=params.run_id, idempotency_key=f"decline:{params.run_id}", reason=params.reason
    )
    return versioned(payload)
