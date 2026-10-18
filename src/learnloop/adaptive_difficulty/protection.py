"""Exam protection for AD's model inputs (spec A8, G-AD1-6).

Held-out exam and problem-set units are never quoted to any AD prompt (the
feature audit, the outside forecasters), never written into an AD receipt or
payload, and never read as an AD input. AD asks the one held-out predicate
(``content.sources.exam_material``): an item made from held-out material, or
reserved for a goal's held-out exam, is *protected*. A protected item is not
audited, not forecast by any model, gets no serve inputs, and never appears in
another item's history card.
"""

from __future__ import annotations

import logging
from typing import Any

LOG = logging.getLogger(__name__)


def protected_items(vault: Any, repository: Any) -> frozenset[str]:
    """Items made from held-out material, or reserved for a held-out exam.

    Fails closed: if the predicate cannot be evaluated, every item is
    protected (the caller then sends nothing)."""

    from learnloop.content.sources.exam_material import held_out_items

    try:
        held = set(held_out_items(vault, repository))
        held.update(str(item_id) for item_id in repository.reserved_exam_pool_item_ids())
    except Exception:  # noqa: BLE001 - an unreadable predicate protects everything
        LOG.warning("held-out predicate unavailable: every item treated as protected", exc_info=True)
        return frozenset(getattr(vault, "practice_items", {}) or {})
    return frozenset(held)


def is_protected(vault: Any, repository: Any, practice_item_id: str) -> bool:
    return str(practice_item_id) in protected_items(vault, repository)


__all__ = ["is_protected", "protected_items"]
