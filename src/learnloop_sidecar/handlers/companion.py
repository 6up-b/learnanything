"""Reader workbench v2 RD0 RPC: ``companion.history`` (spec §3.4, §8.5), every tutor exchange by day and
desk, newest first, a page at a time.

Desktop only (pinned in tests/test_mobile_allowlist.py). Read only; no model call (the search by
meaning is the companion's job, RD3).
"""
from __future__ import annotations

from datetime import date
from typing import Any

from pydantic import Field

from learnloop.companion.history import companion_history
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.dto import ParamsModel, versioned
from learnloop_sidecar.registry import method

#: Every RPC this module registers (pinned desktop-only).
COMPANION_RPCS: tuple[str, ...] = ("companion.history",)


class CompanionHistoryInput(ParamsModel):
    # ``from`` is a Python keyword; the wire name stays the spec's.
    date_from: date | None = Field(default=None, alias="from")
    date_to: date | None = Field(default=None, alias="to")
    desk_id: str | None = None
    query: str | None = None
    cursor: str | None = None


@method("companion.history", CompanionHistoryInput)
def companion_history_handler(ctx: SidecarContext, params: CompanionHistoryInput) -> dict[str, Any]:
    """``{days: [{date, desks: [{desk_id, exchanges}]}], cursor}``."""

    _vault, repository = ctx.require_vault()
    return versioned(companion_history(
        repository, date_from=params.date_from.isoformat() if params.date_from else None,
        date_to=params.date_to.isoformat() if params.date_to else None, desk_id=params.desk_id, query=params.query,
        cursor=params.cursor))
