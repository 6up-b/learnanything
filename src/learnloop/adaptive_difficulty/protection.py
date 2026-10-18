"""Exam protection for AD's model inputs (spec A8, G-AD1-6).

Held-out exam and problem-set units are never quoted to any AD prompt (the
feature audit, the outside forecasters), never written into an AD receipt or
payload, and never read as an AD input. AD asks the one held-out predicate
(``content.sources.exam_material``): an item made from held-out material, or
reserved for a goal's held-out exam, is *protected*. A protected item is not
audited, not forecast by any model, gets no serve inputs, and never appears in
another item's history card.

The predicate is asked of each **revision**, not only of the vault's current
items (Codex review F1): a revision held in ``practice_item_snapshots`` whose
item was deleted, or whose own source references differ from the current
revision's, is protected when its own canonical exercise or provenance lies
in held-out material (:meth:`Protection.covers`). Inputs frozen at a serve are
revalidated when they are sent, by the identity and source references of
each revision they quote (:meth:`Protection.covers_identity`; Codex re-review
F11).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

LOG = logging.getLogger(__name__)


@dataclass(frozen=True)
class Protection:
    """The held-out predicate, evaluated once per pass.

    ``ids``: the current items made from held-out material and the items a
    goal's held-out exam reserves. ``material``: the held-out material itself,
    so a revision that is not a current item is judged by its own source
    references; None when the predicate could not be evaluated, and then
    everything is protected (fail closed: the caller sends nothing)."""

    ids: frozenset[str]
    material: Any | None

    def __contains__(self, practice_item_id: object) -> bool:
        return self.material is None or str(practice_item_id) in self.ids

    def covers(self, item: Any) -> bool:
        """Whether this revision (a current item or a snapshot) is protected."""

        from learnloop.content.sources.exam_material import held_out_item_ids

        if self.material is None or str(getattr(item, "id", "")) in self.ids:
            return True
        try:
            return bool(held_out_item_ids([item], self.material))
        except Exception:  # noqa: BLE001 - an unreadable revision is protected
            LOG.warning("held-out check of a revision failed: treated as protected", exc_info=True)
            return True

    def covers_identity(self, identity: Any) -> bool:
        """Whether a frozen revision identity (:func:`~learnloop.adaptive_difficulty.outside.source_identity`)
        is protected now: its item id is, or its own source references as
        frozen lie in held-out material (Codex re-review F11; the same rule
        as ``held_out_item_ids``). An unreadable identity is protected."""

        if self.material is None:
            return True
        try:
            if str(identity["practice_item_id"]) in self.ids:
                return True
            keys = [(str(extraction), str(span)) for extraction, span in identity.get("keys") or ()]
            whole = [str(extraction) for extraction in identity.get("whole") or ()]
            if self.material.empty:
                return False
            return any(self.material.covers(*key) for key in keys) or any(
                self.material.covers(extraction) for extraction in whole)
        except Exception:  # noqa: BLE001 - an unreadable identity is protected
            LOG.warning("held-out check of a frozen revision failed: treated as protected", exc_info=True)
            return True


def protection(vault: Any, repository: Any) -> Protection:
    """The held-out predicate for one pass (fails closed)."""

    from learnloop.content.sources.exam_material import held_out_item_ids, held_out_material

    try:
        material = held_out_material(vault, repository)
        items = list(getattr(vault, "practice_items", {}).values())
        held = set(held_out_item_ids(items, material)) if items else set()
        held.update(str(item_id) for item_id in repository.reserved_exam_pool_item_ids())
    except Exception:  # noqa: BLE001 - an unreadable predicate protects everything
        LOG.warning("held-out predicate unavailable: every item treated as protected", exc_info=True)
        return Protection(frozenset(getattr(vault, "practice_items", {}) or {}), None)
    return Protection(frozenset(held), material)


def guard(vault: Any, repository: Any, protected: Any = None) -> Protection:
    """A caller's :class:`Protection`, or a fresh one (a bare id set adds its ids)."""

    if isinstance(protected, Protection):
        return protected
    fresh = protection(vault, repository)
    if protected:
        return Protection(fresh.ids | frozenset(str(value) for value in protected), fresh.material)
    return fresh


def protected_items(vault: Any, repository: Any) -> frozenset[str]:
    """Items made from held-out material, or reserved for a held-out exam.

    Fails closed: if the predicate cannot be evaluated, every item is
    protected (the caller then sends nothing)."""

    return protection(vault, repository).ids


def is_protected(vault: Any, repository: Any, practice_item_id: str) -> bool:
    return str(practice_item_id) in protection(vault, repository)


__all__ = ["Protection", "guard", "is_protected", "protected_items", "protection"]
