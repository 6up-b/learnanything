"""Reader workbench v2 RPCs: scratchpads (spec §3.4, §10). ``pad.get``, ``pad.list`` and
``pad.apply`` (no submission: ``pad.submit_block`` is not built yet).

Desktop only (pinned in tests/test_mobile_allowlist.py). No model call; a pad is the learner's own
writing, never evidence. ``pad.apply`` follows the write protocol (``learnloop.desks.protocol``), sharing
one batch numbering per client with ``desk.apply``.
"""
from __future__ import annotations

from typing import Any

from pydantic import Field

from learnloop.desks.protocol import ProtocolError
from learnloop.pads.blocks import PadNotFound, PadOp, apply_pad_ops, pad_list, pad_view
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.dto import ParamsModel, Verbatim, versioned
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.handlers.desks import protocol_error
from learnloop_sidecar.registry import method

#: Every RPC this module registers (pinned desktop-only).
PAD_RPCS: tuple[str, ...] = ("pad.get", "pad.list", "pad.apply")


class PadGetInput(ParamsModel):
    pad_id: str = Field(min_length=1)


class PadListInput(ParamsModel):
    desk_id: str | None = None
    query: str | None = None
    kept: bool | None = None
    cursor: str | None = None


class PadApplyInput(ParamsModel):
    client_id: str = Field(min_length=1)
    seq: int = Field(ge=1)
    pad_id: str = Field(min_length=1)
    ops: list[PadOp]


@method("pad.get", PadGetInput)
def pad_get_handler(ctx: SidecarContext, params: PadGetInput) -> dict[str, Any]:
    """One pad: its metadata, its standing blocks in order (each with its head version) and their links."""

    _vault, repository = ctx.require_vault()
    try:
        view = pad_view(repository, params.pad_id)
    except PadNotFound as exc:
        raise SidecarError("pad_not_found", f"No pad {params.pad_id!r}.") from exc
    # A block's payload and an anchor's JSON are the client's, returned with their keys as stored.
    for block in view["blocks"]:
        block["payload"] = Verbatim(block["payload"])
    for anchor in view["anchors"]:
        anchor["anchor"] = Verbatim(anchor["anchor"])
    return versioned(view)


@method("pad.list", PadListInput)
def pad_list_handler(ctx: SidecarContext, params: PadListInput) -> dict[str, Any]:
    """Pads, most recently changed first, a page at a time: for the library, search and the drain."""

    _vault, repository = ctx.require_vault()
    return versioned(pad_list(repository, desk_id=params.desk_id, query=params.query, kept=params.kept,
                              cursor=params.cursor))


@method("pad.apply", PadApplyInput)
def pad_apply_handler(ctx: SidecarContext, params: PadApplyInput) -> dict[str, Any]:
    """One batch of ops on one pad: ``{applied_seq, results, heads, pads}``."""

    _vault, repository = ctx.require_vault()
    try:
        reply = apply_pad_ops(repository, client_id=params.client_id, seq=params.seq, pad_id=params.pad_id,
                              ops=list(params.ops))
    except ProtocolError as exc:
        raise protocol_error(exc) from exc
    return versioned(reply)
