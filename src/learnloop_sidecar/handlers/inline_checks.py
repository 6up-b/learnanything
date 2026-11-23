"""Reader workbench v2 RD0 RPC: ``checks.due_for`` (spec §3.4, §12.6.1), the due delayed checks by goal,
learning object, reading or passage, each with its host passage. Read only; it shows nothing of the
item. The administration protocol (``check.begin_inline`` and the rest) is RD7's.

Desktop only (pinned in tests/test_mobile_allowlist.py). No model call.
"""
from __future__ import annotations

from typing import Any

from learnloop.intent.inline_checks import due_checks
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.dto import ParamsModel, versioned
from learnloop_sidecar.registry import method

#: Every RPC this module registers (pinned desktop-only).
INLINE_CHECK_RPCS: tuple[str, ...] = ("checks.due_for",)


class ChecksDueForInput(ParamsModel):
    goal_id: str | None = None
    learning_object_ids: list[str] | None = None
    extraction_id: str | None = None
    span_id: str | None = None


@method("checks.due_for", ChecksDueForInput)
def checks_due_for_handler(ctx: SidecarContext, params: ChecksDueForInput) -> dict[str, Any]:
    """``{checks: [{commitment_id, lo_id, due, host?, provenance}]}``."""

    vault, repository = ctx.require_vault()
    return versioned({"checks": due_checks(
        vault, repository, goal_id=params.goal_id, learning_object_ids=params.learning_object_ids,
        extraction_id=params.extraction_id, span_id=params.span_id)})
