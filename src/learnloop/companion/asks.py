"""Where a companion question is asked (spec §8.6): the desk, the surface, the focused window, the
selected pad blocks and the desk's goal, read before the question is sent and recorded with the
exchange (``companion_exchange_context``).

Reads only, on a read-only connection; the one write is :func:`learnloop.companion.history.
record_exchange_context`, after the exchange exists. Nothing here reaches the tutor's prompt: the
desk and pad context is recorded, not sent (a structured prompt change is its own step).
"""
from __future__ import annotations

import json
from contextlib import closing
from dataclasses import dataclass
from typing import Any

from learnloop.db.connection import connect
from learnloop.db.stores import desks as desk_store
from learnloop.db.stores import pad_reads

#: The surfaces a passage-grounded companion question is asked from. ``reader`` is the old Reader
#: screen (no desk); ``desk`` a source window on a workbench desk; ``lesson`` a lesson window's
#: passage; ``notebook`` a Teacher notebook frame (named by ``notebook_ref``).
ASK_SURFACES = ("desk", "reader", "lesson", "notebook")
#: How many selected pad blocks one question may name (a request-size guardrail).
MAX_PAD_BLOCKS = 40


class CompanionAskError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class AskContext:
    surface: str
    desk_id: str | None
    goal_id: str | None
    window_spec: dict[str, Any] | None
    pad_block_ids: list[str]

    def record(self) -> dict[str, Any]:
        """The keyword arguments of ``record_exchange_context`` (besides the exchange)."""

        return {"surface": self.surface, "desk_id": self.desk_id, "goal_id": self.goal_id,
                "window_spec": self.window_spec, "pad_block_ids": self.pad_block_ids or None}


def _focused_window(connection: Any, desk: dict[str, Any]) -> dict[str, Any] | None:
    window_id = desk.get("focus_window_id")
    if not window_id:
        return None
    window = desk_store.window(connection, str(window_id))
    if window is None or window.get("closed_at") or window.get("desk_id") != desk["desk_id"]:
        return None
    try:
        spec = json.loads(window.get("spec_json") or "{}")
    except (TypeError, ValueError):
        spec = {}
    return {"window_id": window["window_id"], "kind": window["kind"], **(spec if isinstance(spec, dict) else {})}


def ask_context(repository: Any, *, surface: str, desk_id: str | None, pad_block_ids: list[str] | None,
                notebook_ref: str | None) -> AskContext:
    """Read and check where the question is asked; refusals raise :class:`CompanionAskError`.

    A desk must exist and be open; its goal and focused window are read from it, never taken from the
    client. Every named pad block must exist and not be removed (its head is not a tombstone)."""

    if surface not in ASK_SURFACES:
        raise CompanionAskError("validation_error", f"Unknown surface {surface!r}.")
    if surface == "desk" and not desk_id:
        raise CompanionAskError("validation_error", "A question asked on a desk names the desk.")
    if surface == "notebook" and not notebook_ref:
        raise CompanionAskError("validation_error", "A question asked in a notebook names the notebook.")
    blocks = list(dict.fromkeys(pad_block_ids or ()))
    if len(blocks) > MAX_PAD_BLOCKS:
        raise CompanionAskError("validation_error", f"At most {MAX_PAD_BLOCKS} pad blocks go with one question.")
    goal_id: str | None = None
    window_spec: dict[str, Any] | None = None
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        if desk_id:
            desk = desk_store.desk(connection, desk_id)
            if desk is None or desk.get("archived_at"):
                raise CompanionAskError("desk_not_found", f"No open desk {desk_id!r}.")
            goal_id = desk.get("goal_id")
            window_spec = _focused_window(connection, desk)
        for block_id in blocks:
            head = pad_reads.head(connection, block_id)
            if head is None or head["tombstone"]:
                raise CompanionAskError("block_not_found", f"No pad block {block_id!r}.")
    if notebook_ref:
        window_spec = {**(window_spec or {}), "notebook_ref": notebook_ref}
    return AskContext(surface=surface, desk_id=desk_id, goal_id=goal_id, window_spec=window_spec,
                      pad_block_ids=blocks)


__all__ = ["ASK_SURFACES", "MAX_PAD_BLOCKS", "AskContext", "CompanionAskError", "ask_context"]
