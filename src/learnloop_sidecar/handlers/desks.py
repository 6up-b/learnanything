"""Reader workbench v2 RPCs: desks (spec §3.4, §5). ``desk.state`` and ``desk.apply``.

Desktop only (pinned in tests/test_mobile_allowlist.py; the phone's desks are deferred, spec §17). No
model call; workflow data, never evidence. ``desk.apply`` follows the write protocol
(``learnloop.desks.protocol``): one batch per call, applied once and in order, with its stored reply.
"""
from __future__ import annotations

from typing import Any

from pydantic import Field

from learnloop.desks.protocol import ProtocolError
from learnloop.desks.workspace import DeskOp, apply_desk_ops, desk_state
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.dto import EmptyParams, ParamsModel, Verbatim, versioned
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.registry import method

#: Every RPC this module registers (pinned desktop-only).
DESK_RPCS: tuple[str, ...] = ("desk.state", "desk.apply")


def protocol_error(exc: ProtocolError) -> SidecarError:
    return SidecarError(exc.code, str(exc), details=exc.details)


class DeskApplyInput(ParamsModel):
    client_id: str = Field(min_length=1)
    seq: int = Field(ge=1)
    ops: list[DeskOp]


@method("desk.state", EmptyParams)
def desk_state_handler(ctx: SidecarContext, params: EmptyParams) -> dict[str, Any]:
    """Every open desk with its slots (authoritative: a pair is two windows sharing a slot), the running
    pads, and each client's last applied batch. Read at startup and after a conflict."""

    _vault, repository = ctx.require_vault()
    state = desk_state(repository)
    # A window's view is the client's JSON, returned with its keys as stored.
    for desk in state["desks"]:
        for slot in desk["slots"]:
            for window in slot["windows"]:
                window["view"] = Verbatim(window["view"])
    return versioned(state)


@method("desk.apply", DeskApplyInput)
def desk_apply_handler(ctx: SidecarContext, params: DeskApplyInput) -> dict[str, Any]:
    """One batch of desk ops: ``{applied_seq, results: [ok | conflict{current} | refused{code}], versions}``."""

    _vault, repository = ctx.require_vault()
    try:
        reply = apply_desk_ops(repository, client_id=params.client_id, seq=params.seq, ops=list(params.ops))
    except ProtocolError as exc:
        raise protocol_error(exc) from exc
    return versioned(reply)
