from __future__ import annotations

from typing import Any

from learnloop.curriculum.subject_registry import (
    RegistryReviewError,
    build_subject_registry,
    propose_facet_merge,
)
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.dto import ParamsModel, versioned
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.registry import method


class SubjectRegistryInput(ParamsModel):
    subject_id: str


class ProposeFacetMergeInput(ParamsModel):
    subject_id: str
    retired_facet_id: str
    surviving_facet_id: str
    rationale: str | None = None
    need_id: str | None = None


@method("get_subject_registry", SubjectRegistryInput)
def get_subject_registry_handler(ctx: SidecarContext, params: SubjectRegistryInput) -> dict[str, Any]:
    """Registry review (§5.7): facet-contract cards (claim/conditions/examples/
    non-goals/error-signatures/repairs/status/version) and identifiability
    warnings from the synthesis generation-needs. Every card can be merged:
    facet identity locks were removed (owner, 2026-10-12)."""

    vault, repository = ctx.require_vault()
    try:
        payload = build_subject_registry(vault, repository, params.subject_id)
    except RegistryReviewError as exc:
        raise SidecarError(exc.code, str(exc)) from exc
    return versioned(payload)


@method("propose_facet_merge", ProposeFacetMergeInput)
def propose_facet_merge_handler(ctx: SidecarContext, params: ProposeFacetMergeInput) -> dict[str, Any]:
    """Merge (or coarsen) two facets now, with a one-tap undo.

    The owner's merge applies live through the facet-identity merge, exactly
    like a judge's: the result carries the action and its undo
    (``undo_facet_identity_action``). A graded criterion naming both facets at
    one capability holds it back (``shared_graded_criterion``). When
    ``need_id`` is set (accepting a coarsening warning) the generation-need is
    resolved. The method keeps its name for the desktop bridge."""

    vault, repository = ctx.require_vault()
    if params.subject_id not in vault.subjects:
        raise SidecarError("unknown_subject", f"Subject '{params.subject_id}' does not exist.")
    try:
        result = propose_facet_merge(
            vault,
            repository,
            subject_id=params.subject_id,
            retired_facet_id=params.retired_facet_id,
            surviving_facet_id=params.surviving_facet_id,
            rationale=params.rationale,
            need_id=params.need_id,
        )
    except RegistryReviewError as exc:
        raise SidecarError(exc.code, str(exc)) from exc
    ctx.reload(maintenance=False)
    return versioned(result)
