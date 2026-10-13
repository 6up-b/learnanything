"""Canonical-sources service RPCs (spec_source_practice_and_probes_v1).

Desktop only (pinned in tests/test_mobile_allowlist.py). Tools propose and
existing serving paths serve (SC1): nothing here writes attempts, evidence,
mastery, FSRS, scheduler state or plan items.
"""
from __future__ import annotations

from typing import Any

from pydantic import Field

from learnloop.instructional.practice import record_proposal_impressions
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.dto import ParamsModel, versioned
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.registry import method

#: Every RPC this module registers (pinned desktop-only).
SOURCE_SERVICE_RPCS: tuple[str, ...] = (
    "record_proposal_impressions",
)


class ImpressionKey(ParamsModel):
    kind: str = "item"
    practice_item_id: str | None = None
    extraction_id: str | None = None
    span_ids: list[str] = Field(default_factory=list)


class RecordImpressionsInput(ParamsModel):
    proposal_id: str
    keys: list[ImpressionKey] = Field(default_factory=list, max_length=200)
    surface: str
    session_id: str | None = None


@method("record_proposal_impressions", RecordImpressionsInput)
def record_proposal_impressions_rpc(ctx: SidecarContext, params: RecordImpressionsInput) -> dict[str, Any]:
    """Fire-and-forget after render: which proposals a surface showed (§6.5)."""

    vault, repository = ctx.require_vault()
    try:
        result = record_proposal_impressions(
            vault, repository, proposal_id=params.proposal_id,
            keys=[key.model_dump() for key in params.keys], surface=params.surface,
            session_id=params.session_id,
        )
    except ValueError as exc:
        raise SidecarError("validation_error", str(exc)) from exc
    return versioned(result)


__all__ = ["SOURCE_SERVICE_RPCS"]
