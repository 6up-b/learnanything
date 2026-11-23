"""A pad's marimo cells (spec §10.4 ``cell``, §11.5): the standing ``cell`` blocks of one pad, in pad order.

The pad is the source of truth. The notebook the runtime runs is generated from these cells on every open (the
sidecar's notebook handler), never edited in its own right, so a cell is written, edited, moved and removed with the
pad ops every block uses (versions append-only, provenance kept). A cell's code is never learner text for the gap
pipeline: ``pads.emission`` emits text, notes and ink transcriptions only.
"""
from __future__ import annotations

from typing import Any

from learnloop.db.stores import pad_reads as reads

CELL = "cell"


def pad_cells(repository: Any, pad_id: str) -> list[dict[str, Any]] | None:
    """``[{block_id, version_id, code, provenance}]`` for the pad's standing cells in pad order; None for no pad."""

    with repository.connection() as connection:
        if reads.pad(connection, pad_id) is None:
            return None
        heads = reads.heads(connection, pad_id)
    return [{"block_id": str(head["block_id"]), "version_id": str(head["version_id"]), "code": str(head["body_md"] or ""),
             "provenance": str(head["provenance"])}
            for head in heads if head["kind"] == CELL and not head["tombstone"]]


__all__ = ["CELL", "pad_cells"]
