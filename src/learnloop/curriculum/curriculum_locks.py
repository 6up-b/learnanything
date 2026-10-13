"""The curriculum-layer legality check for destructive operations (knowledge-model §12.1).

``can_apply(operation)`` answers whether a destructive curriculum operation may
apply, and whether it needs review.

Facet identity locks are gone (owner decision 2026-10-12; handoff §4 "Facet
locks no longer block merges"). A facet merge cannot change what past evidence
means: the retired id becomes an alias of the survivor, evidence resolves to
it through ``facet_merges`` at replay, every merge has an exact undo, and the
one counting hazard (a graded criterion naming both facets at one capability)
is held back by ``facet_identity.actions.hold_back_shared``. Rewording an
existing facet's meaning writes a facet version with the old text and an undo
(``facet_identity.actions.record_reword``) instead of being refused. So no
facet arm (accrued evidence, independent surface groups or mass, an active
goal's certified scope, misconceptions, probes) blocks anything any more; facet
merge and split are legal and review-required.

What remains is the learning-object arm: a destructive operation on a learning
object, or on one of its practice items, while that learning object has
recorded practice attempts (a blueprint or assessment-contract rewrite under
history). It is not a facet lock and the owner's decision did not cover it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from learnloop.db.repositories import Repository
from learnloop.vault.models import LoadedVault

# Destructive-operation vocabulary (source-ingestion §8.2). Each is
# review-required; only the learning-object arm below can make one illegal. A
# semantic-preserving alias rename is NOT destructive and is always sanctioned.
DESTRUCTIVE_OPERATIONS: frozenset[str] = frozenset(
    {
        "facet_merge",
        "facet_split",
        "lo_merge",
        "lo_split",
        "concept_merge",
        "concept_split",
        "blueprint_identity_change",
        "recipe_identity_change",
        "assessment_contract_rewrite",
        "criterion_rekey",
        "criterion_target_change",
        "criterion_dependency_change",
        "deactivate",
    }
)

SANCTIONED_OPERATIONS: frozenset[str] = frozenset({"rename_alias"})

OperationType = str
EntityType = Literal["facet", "learning_object", "practice_item", "concept", "rubric", "criterion"]


@dataclass(frozen=True)
class Operation:
    """A proposed curriculum mutation to be checked."""

    op_type: OperationType
    entity_type: EntityType
    entity_id: str
    # Facet ids the operation touches (facet merge/split). Kept for callers;
    # no facet arm reads them any more.
    facet_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class LockReason:
    source: str  # attempts (the learning-object arm)
    entity_type: str
    entity_id: str
    detail: str


@dataclass
class CanApplyResult:
    legal: bool
    lock_reasons: list[LockReason] = field(default_factory=list)
    # A legal destructive op is review-required, never silently auto-applied
    # by synthesis (§8.2).
    requires_review: bool = False


def _learning_object_for(vault: LoadedVault, operation: Operation) -> str | None:
    if operation.entity_type == "learning_object":
        return operation.entity_id
    if operation.entity_type == "practice_item":
        item = vault.practice_items.get(operation.entity_id)
        return item.learning_object_id if item is not None else None
    return None


def can_apply(vault: LoadedVault, repository: Repository, operation: Operation) -> CanApplyResult:
    """Legality of a destructive curriculum operation (§12.1)."""

    if operation.op_type in SANCTIONED_OPERATIONS:
        # A semantic-preserving alias rename resolves history unchanged (§3.4).
        return CanApplyResult(legal=True, requires_review=False)

    reasons: list[LockReason] = []
    lo_id = _learning_object_for(vault, operation)
    if lo_id is not None and repository.attempt_count_for_learning_objects([lo_id]) > 0:
        reasons.append(
            LockReason(
                source="attempts",
                entity_type="learning_object",
                entity_id=lo_id,
                detail=f"LO {lo_id} has recorded practice attempts",
            )
        )

    legal = not reasons
    return CanApplyResult(
        legal=legal,
        lock_reasons=reasons,
        requires_review=legal and operation.op_type in DESTRUCTIVE_OPERATIONS,
    )
