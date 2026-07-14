from __future__ import annotations

from typing import Any

from learnloop.services.remediation import (
    RemediationError,
    misconception_status_history,
    prescribe_remediation,
    start_remediation_episode,
    start_remediation_treatment,
)
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.dto import ParamsModel, versioned
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.handlers.serializers import practice_item_detail
from learnloop_sidecar.registry import method


class MisconceptionInput(ParamsModel):
    misconception_id: str


class EpisodeInput(ParamsModel):
    episode_id: str


def _case_payload(repository, misconception_id: str) -> dict[str, Any]:
    record = repository.misconception(misconception_id)
    if record is None:
        raise SidecarError("not_found", "Misconception case was not found.")
    return {
        "id": record.id,
        "statement": record.statement,
        "correction_statement": record.correction_statement,
        "mechanism": record.mechanism,
        "target_facet": record.target_facet,
        "confused_with_facet": record.confused_with_facet,
        "status": record.status,
        "history": misconception_status_history(repository, record.id),
    }


@method("start_remediation", MisconceptionInput)
def start_remediation_handler(ctx: SidecarContext, params: MisconceptionInput) -> dict[str, Any]:
    _vault, repository = ctx.require_vault()
    try:
        episode = start_remediation_episode(repository, params.misconception_id)
    except RemediationError as exc:
        raise SidecarError("invalid_request", str(exc)) from exc
    return versioned({"episode": episode, "case": _case_payload(repository, params.misconception_id)})


@method("prescribe_remediation", EpisodeInput)
def prescribe_remediation_handler(ctx: SidecarContext, params: EpisodeInput) -> dict[str, Any]:
    vault, repository = ctx.require_vault()
    try:
        episode = prescribe_remediation(vault, repository, params.episode_id)
    except RemediationError as exc:
        raise SidecarError("invalid_request", str(exc)) from exc
    return versioned({"episode": episode, "case": _case_payload(repository, episode["case_ref"])})


@method("start_remediation_treatment", EpisodeInput)
def start_remediation_treatment_handler(ctx: SidecarContext, params: EpisodeInput) -> dict[str, Any]:
    vault, repository = ctx.require_vault()
    try:
        result = start_remediation_treatment(vault, repository, params.episode_id)
    except RemediationError as exc:
        raise SidecarError("invalid_request", str(exc)) from exc
    return versioned(
        {
            **result,
            "practice_item": practice_item_detail(vault, repository, result["primed_item_id"]),
        }
    )


@method("get_remediation", EpisodeInput)
def get_remediation_handler(ctx: SidecarContext, params: EpisodeInput) -> dict[str, Any]:
    _vault, repository = ctx.require_vault()
    episode = repository.remediation_episode(params.episode_id)
    if episode is None:
        raise SidecarError("not_found", "Remediation episode was not found.")
    return versioned({"episode": episode, "case": _case_payload(repository, episode["case_ref"])})
