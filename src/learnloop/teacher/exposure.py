"""Teacher TE3a (landing ruling R1): what a lesson exposed, frozen at the moment it was shown.

Each displayed record of a lesson (an accepted ``teacher_turn``, a shown ``visual``, a served probe's
``probe_served``) carries, under :data:`EXPOSURE_KEY`, the protection identity of every vault item it exposed as
the vault held that item then (:func:`exposed_identities`). The lesson's receipt takes the union of them
(``teacher.service._receipt_identities``), so AD's guard judges a lesson by the revisions the learner saw, never only
by the ones current at the close. Ids only, never text.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

#: The payload key of a displayed record holding the frozen identities of the vault items it exposed.
EXPOSURE_KEY = "exposure_identities"


def exposed_identities(vault: Any, item_ids: Sequence[Any]) -> list[dict[str, Any]]:
    """Per exposed item still in the vault, in id order, its revision's protection identity,
    ``{practice_item_id, keys, whole}`` (the block keys and whole extractions its canonical exercise and provenance
    refs cite; ids, no text), the shape of AD's ``outside.source_identity``. An exposed item no longer in the vault
    gets none, so AD cannot judge a receipt naming it and withholds it (fail closed)."""

    from learnloop.content.sources.exam_material import item_source_keys

    out: list[dict[str, Any]] = []
    for item_id in sorted({str(value) for value in item_ids if value}):
        item = (getattr(vault, "practice_items", {}) or {}).get(item_id)
        if item is None:
            continue
        keys, whole = item_source_keys(item)
        out.append({"practice_item_id": item_id,
                    "keys": sorted([str(extraction), str(span)] for extraction, span in keys),
                    "whole": sorted(str(extraction) for extraction in whole)})
    return out


__all__ = ["EXPOSURE_KEY", "exposed_identities"]
