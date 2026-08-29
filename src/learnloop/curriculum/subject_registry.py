"""Registry review (spec_source_ingestion_v2 §5.7; spec_knowledge_model §3.4, §12.2).

The facet-contract registry for one subject, as review cards: claim, kind,
conditions, examples, non-goals, error signatures, repairs, a status chip, and
the lock state that decides whether pre-lock merge/coarsen actions are offered.
Plus the identifiability warnings raised at synthesis (``coarsen_distinction`` /
``generate_discriminator`` generation-needs).

Pre-lock actions are legal-with-review (§3.4): ``propose_facet_merge`` creates a
review proposal item through the existing proposal machinery — it NEVER
auto-merges. Coarsening accepts an existing ``coarsen_distinction`` review item
by proposing the merge of its confusable pair and resolving the need.
"""

from __future__ import annotations

from typing import Any

from learnloop.clock import Clock, utc_now_iso
from learnloop.ids import new_ulid
from learnloop.curriculum.curriculum_locks import Operation, can_apply


class RegistryReviewError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def _facet_ids_for_subject(vault, subject_id: str) -> list[str]:
    """Canonical facet ids exercised by the subject's practice items, plus any
    facet whose provenance/contract lists the subject — deterministic, sorted."""

    ids: set[str] = set()
    for item in vault.practice_items.values():
        if subject_id in vault.subjects_for_item(item):
            for facet in item.evidence_facets:
                ids.add(vault.canonical_facet_id(str(facet)))
    return sorted(ids)


def _facet_card(vault, repository, facet, *, lock_result) -> dict[str, Any]:
    locked = not lock_result.legal
    lock_reasons = [
        {
            "source": reason.source,
            "entity_type": reason.entity_type,
            "entity_id": reason.entity_id,
            "detail": reason.detail,
        }
        for reason in lock_result.lock_reasons
    ]
    return {
        "facet_id": facet.id,
        "title": facet.title,
        "concept_id": facet.concept_id,
        "kind": facet.kind,
        "claim": facet.claim,
        "conditions": {
            "preconditions": list(facet.preconditions),
            "postconditions": list(facet.postconditions),
            "applicability": list(facet.applicability),
        },
        "examples": {
            "positive": list(facet.positive_examples),
            "negative": list(facet.negative_examples),
        },
        "non_goals": list(facet.non_goals),
        "error_signatures": list(facet.error_signatures),
        "instructional_repairs": list(facet.instructional_repairs),
        "status": facet.status,
        "version": facet.version,
        # Lock chip: locked facets disable pre-lock actions with the reason;
        # unlocked facets allow merge/coarsen (legal-with-review).
        "locked": locked,
        "lock_reasons": lock_reasons,
        "can_merge": not locked,
        "requires_review": bool(lock_result.requires_review),
    }


def build_subject_registry(vault, repository, subject_id: str) -> dict[str, Any]:
    """Facet-contract cards + identifiability warnings + lock state (§5.7)."""

    if subject_id not in vault.subjects:
        raise RegistryReviewError("unknown_subject", f"Subject '{subject_id}' does not exist.")

    cards: list[dict[str, Any]] = []
    for facet_id in _facet_ids_for_subject(vault, subject_id):
        facet = vault.evidence_facets.get(facet_id)
        if facet is None:
            continue
        lock_result = can_apply(
            vault,
            repository,
            Operation(
                op_type="facet_merge",
                entity_type="facet",
                entity_id=facet_id,
                facet_ids=(facet_id,),
            ),
        )
        cards.append(_facet_card(vault, repository, facet, lock_result=lock_result))

    needs = repository.synthesis_generation_needs(subject_id=subject_id, status="pending")
    warnings = [
        {
            "id": need.get("id"),
            "kind": need.get("need_kind"),
            "target_key": need.get("target_key"),
            "missing_capability": need.get("missing_capability"),
            "facet_ids": need.get("facet_ids") or [],
            "detail": need.get("detail"),
            "status": need.get("status"),
        }
        for need in needs
    ]

    # Meas §D1 (plan 3.4): publish measurement_rank on the surface where the
    # identifiability findings already land, so a reviewer sees what the pool can
    # actually resolve next to the merge proposals. Read-only analysis — it
    # neither creates a need nor proposes a merge; ``propose_facet_merge`` stays
    # the only path, and it still goes through review (§12.2).
    from learnloop.learner.identifiability import build_registry_view, measurement_rank

    rank = measurement_rank(build_registry_view(vault, subject_id))

    return {
        "subject_id": subject_id,
        "facets": cards,
        "identifiability_warnings": warnings,
        "facet_count": len(cards),
        "locked_count": sum(1 for card in cards if card["locked"]),
        "measurement_rank": rank.as_dict(),
    }


def propose_facet_merge(
    vault,
    repository,
    *,
    subject_id: str,
    retired_facet_id: str,
    surviving_facet_id: str,
    rationale: str | None = None,
    need_id: str | None = None,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """Create a pre-lock facet-merge review item (never auto-merge, §12.2).

    Emits a proposal batch with a single ``facet`` deactivate item on the retired
    facet, carrying the survivor + rationale in its payload so review/apply routes
    it through the existing proposal machinery. When ``need_id`` is given (a
    coarsening acceptance), the generation-need is resolved."""

    retired = vault.canonical_facet_id(retired_facet_id)
    surviving = vault.canonical_facet_id(surviving_facet_id)
    if retired == surviving:
        raise RegistryReviewError("invalid_merge", "A facet cannot be merged into itself.")
    if retired not in vault.evidence_facets:
        raise RegistryReviewError("facet_not_found", f"Facet '{retired_facet_id}' does not exist.")
    if surviving not in vault.evidence_facets:
        raise RegistryReviewError("facet_not_found", f"Facet '{surviving_facet_id}' does not exist.")

    lock_result = can_apply(
        vault,
        repository,
        Operation(op_type="facet_merge", entity_type="facet", entity_id=retired, facet_ids=(retired,)),
    )
    if not lock_result.legal:
        raise RegistryReviewError(
            "facet_identity_locked",
            "This facet's identity is locked; merge is no longer legal-with-review.",
        )

    now = utc_now_iso(clock)
    # Proposals always tie to an agent_run row (house invariant); a learner-
    # initiated registry action records a lightweight one.
    agent_run_id = repository.insert_agent_run(
        {
            "purpose": "registry_facet_merge",
            "provider": "learner",
            "provider_type": "learner",
            "started_at": now,
            "completed_at": now,
            "status": "completed",
        }
    )
    client_item_id = f"facet_merge_{new_ulid()}"
    item = {
        "client_item_id": client_item_id,
        "item_type": "facet",
        "operation": "deactivate",
        "target_entity_type": "facet",
        "target_entity_id": retired,
        "payload": {
            "merge_into": surviving,
            "rationale": rationale or "",
            "restructure": "facet_merge",
        },
        "source_ref_ids": [],
        "audit": {"origin": "registry_review", "rationale": rationale or ""},
        "decision": "pending",
        "validation_status": "valid",
        "validation_errors": [],
        "depends_on_client_item_ids": [],
        "dependency_status": "pending",
        "created_at": now,
        "updated_at": now,
    }
    batch = {
        "agent_run_id": agent_run_id,
        "purpose": "facet_merge",
        "summary": f"Merge facet {retired} into {surviving}",
        "source_refs": [],
        "status_cache": "pending",
        "created_at": now,
        "updated_at": now,
    }
    proposal_id = repository.persist_proposal_batch(batch, [item])

    if need_id is not None:
        repository.resolve_synthesis_generation_need(need_id, status="resolved", clock=clock)

    return {
        "proposal_id": proposal_id,
        "retired_facet_id": retired,
        "surviving_facet_id": surviving,
        "need_id": need_id,
        "resolved_need": need_id is not None,
    }
