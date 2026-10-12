"""Items routine serving never offers, shared by Today's queue and the quick check.

Three exclusions keep an item out of every routine selection, whatever ranks it:

- **exam reservations**: an item reserved for a goal's held-out exam stays
  unseen so the exam remains an honest, uncontaminated test;
- **pending-variant holds**: the learner asked for an easier or harder sibling
  of this exact card and it is still being authored;
- **staged-controller ownership**: during the dual-controller cutover the
  staged policy owns these commitments' items (design §A.2 rule 3).

``build_due_queue`` and the optional quick check (learner field F2) read the
same set, so a selector cannot forget one of them.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from learnloop.db.repositories import Repository
from learnloop.goals.exam_pool import reserved_item_ids
from learnloop.scheduling import controller_ownership


@dataclass(frozen=True)
class ServingExclusions:
    reserved_exam_item_ids: frozenset[str]
    rung_variant_hold_ids: frozenset[str]
    staged_owned_item_ids: frozenset[str]

    @property
    def item_ids(self) -> frozenset[str]:
        return self.reserved_exam_item_ids | self.rung_variant_hold_ids | self.staged_owned_item_ids


def routine_serving_exclusions(vault: Any, repository: Repository) -> ServingExclusions:
    """The shared exclusion sets, each read once."""

    return ServingExclusions(
        reserved_exam_item_ids=frozenset(reserved_item_ids(repository)),
        rung_variant_hold_ids=frozenset(repository.rung_variant_pending_source_ids()),
        staged_owned_item_ids=frozenset(controller_ownership.staged_owned_practice_item_ids(vault, repository)),
    )
