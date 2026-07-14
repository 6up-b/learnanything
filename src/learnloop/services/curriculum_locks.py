"""The single curriculum-layer lock API (knowledge-model §12.1, §3.4).

``can_apply(operation)`` computes direct and transitive lock reasons for a
destructive curriculum operation from EXISTING evidence sources: practice
attempts (accrued facet recall), active goal certified scope, probe episodes,
misconceptions, and exam pools. ``identity_locks()`` is a read adapter over the
same closure — never a second enumerated implementation (source-ingestion §8.2
is its enforcement view; on divergence this contract wins).

Independence-gated facet identity locking (§3.4: >= N distinct surface groups,
``[locks].facet_lock_mass`` independent mass, or active-goal certified scope)
is only partly computable at KM1 — the surface-group and mass ledgers arrive
with KM2. ``_facet_independence_locked`` is the clearly-named seam for that
trigger; at KM1 it evaluates the goal-scope arm and leaves the mass/surface arms
to KM2.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from learnloop.db.repositories import Repository
from learnloop.vault.models import LearningObject, LoadedVault, learning_object_facet_union

# Destructive-operation vocabulary (source-ingestion §8.2): every op here breaks
# a protected identity closure and is legal only where no lock exists. A
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

# Facet merge/split are legal-with-review pre-lock (independence-gated, §3.4).
FACET_RESTRUCTURE_OPERATIONS: frozenset[str] = frozenset({"facet_merge", "facet_split"})

SANCTIONED_OPERATIONS: frozenset[str] = frozenset({"rename_alias"})

OperationType = str
EntityType = Literal["facet", "learning_object", "practice_item", "concept", "rubric", "criterion"]


@dataclass(frozen=True)
class Operation:
    """A proposed curriculum mutation to be checked against the lock closure."""

    op_type: OperationType
    entity_type: EntityType
    entity_id: str
    # Facet ids the operation touches (for facet merge/split/rekey). For an
    # LO/concept operation, the caller may leave this empty; can_apply expands
    # the entity's facet closure itself.
    facet_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class LockReason:
    source: str  # attempts | goal_certified_scope | misconception | probe | exam_pool
    entity_type: str
    entity_id: str
    detail: str


@dataclass
class CanApplyResult:
    legal: bool
    lock_reasons: list[LockReason] = field(default_factory=list)
    # A destructive op with no locks is legal-but-review-required, never silently
    # auto-applied (§8.2). Facet merge/split are the canonical review case.
    requires_review: bool = False


def _learning_objects_for_facet(vault: LoadedVault, facet_id: str) -> list[LearningObject]:
    los: list[LearningObject] = []
    for lo in vault.learning_objects.values():
        if facet_id in learning_object_facet_union(lo):
            los.append(lo)
            continue
        for item in vault.practice_items.values():
            if item.learning_object_id == lo.id and facet_id in item.evidence_facets:
                los.append(lo)
                break
    return los


def _goal_scoped_facets(vault: LoadedVault) -> set[str]:
    """Facet ids in any active goal's certified scope (§3.4 lock arm).

    Concepts expand to the facets required by LOs on that concept; explicit
    facet scope adds those ids directly (alias-resolved).
    """

    scoped: set[str] = set()
    concept_facets: dict[str, set[str]] = {}
    for lo in vault.learning_objects.values():
        facets = set(learning_object_facet_union(lo))
        for item in vault.practice_items.values():
            if item.learning_object_id == lo.id:
                facets.update(item.evidence_facets)
        concept_facets.setdefault(lo.concept, set()).update(facets)
    for goal in vault.goals:
        if goal.status != "active":
            continue
        for facet in goal.facet_scope.facets:
            scoped.add(vault.canonical_facet_id(facet))
        for concept in goal.facet_scope.concepts:
            scoped.update(concept_facets.get(concept, set()))
    return scoped


def _facet_independence_locked(
    vault: LoadedVault,
    repository: Repository,
    facet_id: str,
    *,
    goal_scoped: set[str],
) -> LockReason | None:
    """Independence-gated facet lock trigger (§3.4).

    KM1 evaluates the active-goal certified-scope arm (computable now). The
    surface-group count and independent-mass arms depend on KM2's capability
    ledgers; this is the named seam where they attach.
    """

    if facet_id in goal_scoped:
        return LockReason(
            source="goal_certified_scope",
            entity_type="facet",
            entity_id=facet_id,
            detail="facet is in an active goal's certified scope",
        )
    # KM2: the surface-group and independent-mass arms, read from the capability
    # ledger and canonical belief state (§3.4). Direct evidence spanning >=
    # facet_surface_groups distinct surface/correlation groups, or independent
    # mass >= facet_lock_mass, makes history load-bearing enough to lock.
    locks = vault.config.locks
    surface_groups, independent_mass = repository.facet_independence_evidence(facet_id)
    if surface_groups >= locks.facet_surface_groups:
        return LockReason(
            source="independent_surface_groups",
            entity_type="facet",
            entity_id=facet_id,
            detail=(
                f"direct evidence spans {surface_groups} distinct surface/correlation "
                f"groups (>= {locks.facet_surface_groups})"
            ),
        )
    if independent_mass >= locks.facet_lock_mass:
        return LockReason(
            source="independent_mass",
            entity_type="facet",
            entity_id=facet_id,
            detail=(
                f"independent evidence mass {independent_mass:.3f} "
                f"(>= {locks.facet_lock_mass})"
            ),
        )
    return None


def _facet_lock_reasons(
    vault: LoadedVault,
    repository: Repository,
    facet_id: str,
    *,
    evidence_facets: set[str],
    misconception_facets: set[str],
    goal_scoped: set[str],
) -> list[LockReason]:
    reasons: list[LockReason] = []
    if facet_id in evidence_facets:
        reasons.append(
            LockReason(
                source="attempts",
                entity_type="facet",
                entity_id=facet_id,
                detail="facet carries accrued attempt evidence",
            )
        )
    independence = _facet_independence_locked(vault, repository, facet_id, goal_scoped=goal_scoped)
    if independence is not None:
        reasons.append(independence)
    if facet_id in misconception_facets:
        reasons.append(
            LockReason(
                source="misconception",
                entity_type="facet",
                entity_id=facet_id,
                detail="facet is referenced by an active misconception",
            )
        )
    # Transitive: a facet exercised by an LO with probe episodes or exam-pool
    # membership inherits those locks.
    for lo in _learning_objects_for_facet(vault, facet_id):
        if repository.probe_episodes_for_learning_object(lo.id):
            reasons.append(
                LockReason(
                    source="probe",
                    entity_type="learning_object",
                    entity_id=lo.id,
                    detail=f"facet is exercised by LO {lo.id} with probe episodes",
                )
            )
            break
    return reasons


def _entity_facet_closure(vault: LoadedVault, operation: Operation) -> set[str]:
    if operation.facet_ids:
        return {vault.canonical_facet_id(facet) for facet in operation.facet_ids}
    if operation.entity_type == "facet":
        return {vault.canonical_facet_id(operation.entity_id)}
    if operation.entity_type == "learning_object":
        lo = vault.learning_objects.get(operation.entity_id)
        if lo is None:
            return set()
        facets = set(learning_object_facet_union(lo))
        for item in vault.practice_items.values():
            if item.learning_object_id == lo.id:
                facets.update(item.evidence_facets)
        return facets
    if operation.entity_type == "practice_item":
        item = vault.practice_items.get(operation.entity_id)
        return set(item.evidence_facets) if item is not None else set()
    return set()


def can_apply(vault: LoadedVault, repository: Repository, operation: Operation) -> CanApplyResult:
    """Compute lock legality for a destructive curriculum operation (§12.1)."""

    if operation.op_type in SANCTIONED_OPERATIONS:
        # A semantic-preserving alias rename resolves history unchanged (§3.4).
        return CanApplyResult(legal=True, requires_review=False)

    evidence_facets = repository.facet_ids_with_recall_evidence()
    misconception_facets = repository.active_misconception_facet_ids()
    goal_scoped = _goal_scoped_facets(vault)

    reasons: list[LockReason] = []
    for facet_id in sorted(_entity_facet_closure(vault, operation)):
        reasons.extend(
            _facet_lock_reasons(
                vault,
                repository,
                facet_id,
                evidence_facets=evidence_facets,
                misconception_facets=misconception_facets,
                goal_scoped=goal_scoped,
            )
        )

    # LO/concept-level locks: attempts on the LO's items, probe episodes.
    if operation.entity_type in ("learning_object", "practice_item"):
        lo_id = (
            operation.entity_id
            if operation.entity_type == "learning_object"
            else getattr(vault.practice_items.get(operation.entity_id), "learning_object_id", None)
        )
        if lo_id is not None and repository.attempt_count_for_learning_objects([lo_id]) > 0:
            reasons.append(
                LockReason(
                    source="attempts",
                    entity_type="learning_object",
                    entity_id=lo_id,
                    detail=f"LO {lo_id} has recorded practice attempts",
                )
            )

    locked = bool(reasons)
    is_facet_restructure = operation.op_type in FACET_RESTRUCTURE_OPERATIONS
    # Destructive ops are legal only where no lock exists; facet merge/split are
    # additionally legal-with-review pre-lock. Locked facet merge/split is
    # invalid (restructure-with-history required).
    legal = not locked
    requires_review = legal and operation.op_type in DESTRUCTIVE_OPERATIONS
    return CanApplyResult(
        legal=legal,
        lock_reasons=_dedupe_reasons(reasons),
        requires_review=requires_review or (is_facet_restructure and legal),
    )


def _dedupe_reasons(reasons: list[LockReason]) -> list[LockReason]:
    seen: dict[tuple[str, str, str, str], LockReason] = {}
    for reason in reasons:
        key = (reason.source, reason.entity_type, reason.entity_id, reason.detail)
        seen.setdefault(key, reason)
    return list(seen.values())


def identity_locks(
    vault: LoadedVault,
    repository: Repository,
    subject_id: str | None = None,
) -> dict[str, list[LockReason]]:
    """Read adapter over ``can_apply``: locked facet ids -> their lock reasons.

    Enumerates every registered facet and reports those a facet merge/split
    could not be applied to. Not a second lock implementation — it drives the
    same ``can_apply`` closure (§8.2).
    """

    locks: dict[str, list[LockReason]] = {}
    for facet_id in vault.evidence_facets:
        result = can_apply(
            vault,
            repository,
            Operation(op_type="facet_merge", entity_type="facet", entity_id=facet_id),
        )
        if not result.legal:
            locks[facet_id] = result.lock_reasons
    return locks
