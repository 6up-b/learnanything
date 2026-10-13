"""Registry review (spec_source_ingestion_v2 §5.7; spec_knowledge_model §3.4, §12.2).

The facet-contract registry for one subject, as review cards: claim, kind,
conditions, examples, non-goals, error signatures, repairs, a status chip and
the facet's version. Plus the identifiability warnings raised at synthesis
(``coarsen_distinction`` / ``generate_discriminator`` generation-needs).

Facet identity locks were removed (owner, 2026-10-12), so every card can be
merged. ``propose_facet_merge`` applies the owner's merge live through the
facet-identity merge (``merge_registered_facets``), with the same one-tap
undo a judge's merge has; coarsening accepts a ``coarsen_distinction``
warning by merging its confusable pair and resolving the need.
"""

from __future__ import annotations

import json
from typing import Any

from learnloop.ai.execution import content_key
from learnloop.clock import Clock, utc_now_iso
from learnloop.content.facet_identity.actions import (
    HELD_BACK_NOTE,
    action_by_id,
    describe,
    merge_registered_facets,
)
from learnloop.content.facet_identity.judge import TASK
from learnloop.db.stores.judgments import append_judgment
from learnloop.ids import new_ulid
from learnloop.vault.loader import load_vault


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


def _facet_card(facet) -> dict[str, Any]:
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
    }


def build_subject_registry(vault, repository, subject_id: str) -> dict[str, Any]:
    """Facet-contract cards + identifiability warnings (§5.7)."""

    if subject_id not in vault.subjects:
        raise RegistryReviewError("unknown_subject", f"Subject '{subject_id}' does not exist.")

    cards: list[dict[str, Any]] = []
    for facet_id in _facet_ids_for_subject(vault, subject_id):
        facet = vault.evidence_facets.get(facet_id)
        if facet is None:
            continue
        cards.append(_facet_card(facet))

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
    """Merge ``retired_facet_id`` into ``surviving_facet_id`` now, with a one-tap undo.

    The owner asked for it (registry review, the facet inspector, or accepting
    a coarsening warning), so it applies live through the facet-identity merge,
    exactly like a judge's merge: the retired id becomes the survivor's alias,
    evidence re-keys through ``facet_merges``, and ``learnloop facets undo``
    (or the desktop undo) restores both. Until 2026-10-12 this filed a facet
    ``deactivate`` review item that proposal apply could not compile, and
    refused a locked facet; facet locks were removed (owner decision). A graded
    criterion that names both facets at one capability still holds the merge
    back (it would count one facet twice). The owner's verdict is appended to
    ``judgment_ledger`` (task ``same_facet``, judge ``owner``). When
    ``need_id`` is given (a coarsening acceptance) the generation-need is
    resolved once the merge applies.
    """

    retired = vault.canonical_facet_id(retired_facet_id)
    surviving = vault.canonical_facet_id(surviving_facet_id)
    if retired == surviving:
        raise RegistryReviewError("invalid_merge", "A facet cannot be merged into itself.")
    if retired not in vault.evidence_facets:
        raise RegistryReviewError("facet_not_found", f"Facet '{retired_facet_id}' does not exist.")
    if surviving not in vault.evidence_facets:
        raise RegistryReviewError("facet_not_found", f"Facet '{surviving_facet_id}' does not exist.")

    run_id = new_ulid()
    left, right = sorted((retired, surviving))
    with repository.atomic():
        judgment_id = append_judgment(
            repository.connection(), task=TASK, left_kind="facet", left_id=left,
            right_kind="facet", right_id=right, judge="owner",
            input_hash=content_key({"owner_merge": run_id, "pair": [left, right]}), verdict="same",
            rationale=json.dumps(
                {"origin": "registry", "survivor": surviving, "subject_id": subject_id,
                 "rationale": rationale or ""},
                sort_keys=True,
            ),
            created_at=utc_now_iso(clock),
        )
    result = merge_registered_facets(
        vault.root, repository,
        survivor=surviving, retired=[retired], action="merge", absorb_as=None,
        origin="registry", run_id=run_id, judge="owner", judge_model=None, prompt_version=None,
        judgment_ids=[judgment_id],
        detail={"rationale": rationale or "", "subject_id": subject_id, "need_id": need_id},
        clock=clock,
    )
    if result.get("status") != "applied":
        reason = str(result.get("reason") or "merge_refused")
        message = HELD_BACK_NOTE if reason == "shared_graded_criterion" else f"The merge was not applied ({reason})."
        raise RegistryReviewError(reason, message)

    if need_id is not None:
        repository.resolve_synthesis_generation_need(need_id, status="resolved", clock=clock)

    action_id = str(result["action_id"])
    record = action_by_id(repository, action_id)
    return {
        "status": "applied",
        "action_id": action_id,
        "undo": f"learnloop facets undo {action_id}",
        "action": describe(record, load_vault(vault.root)) if record is not None else None,
        "retired_facet_id": retired,
        "surviving_facet_id": surviving,
        "need_id": need_id,
        "resolved_need": need_id is not None,
    }
