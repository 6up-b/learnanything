"""Source-object layer + relations + canonical mapping proposals (spec §7, design
B step 7).

A source object is a PER-SOURCE reviewed/proposed semantic object, never a
cross-source truth claim (§7.1). Inventory / demand-paged-synthesis output begins
``proposed``; authoring, review, and linking are append-only. The reader cannot
create a transcript-shaped graph merely because content was visible or highlighted
(§7.3) -- new canonical objects flow only through the proposal/gate/review path, and
accepting a mapping never overwrites the source object nor deletes the annotation.
"""

from __future__ import annotations

from typing import Any, Mapping

from learnloop.clock import Clock
from learnloop.db.repositories import Repository

OBJECT_TYPES = (
    "claim", "definition", "procedure", "worked_example",
    "problem", "proof_move", "motif_or_passage", "artifact",
)
RELATION_TYPES = (
    "supports", "contradicts", "refines", "alternate_definition",
    "unresolved", "learner_connects",
)
MAPPING_TARGET_KINDS = ("facet", "lo", "blueprint", "commitment", "new_object")

# §5.2/§A.3.6: connect_it's birth relation is learner_connects -- never a canonical
# edge; it stays a proposal unless reviewed into another relation (§7.2).
CONNECT_IT_RELATION = "learner_connects"


class SourceObjectError(ValueError):
    """Domain error for the source-object service."""


def author_source_object(
    repository: Repository,
    *,
    source_id: str,
    revision_id: str,
    object_type: str,
    exact_text: str = "",
    content: Mapping[str, Any] | None = None,
    citations: list[Mapping[str, Any]] | None = None,
    authorship: str = "ai",
    status: str = "proposed",
    authorial_role: str | None = None,
    salience_proposal: float | None = None,
    model_provenance: Mapping[str, Any] | None = None,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """Author a new source object (version 1). Inventory/reader output begins
    ``proposed`` (§7.1); a source object is not a cross-source truth claim."""

    if object_type not in OBJECT_TYPES:
        raise SourceObjectError(f"unknown object_type: {object_type!r}")
    source_object_id = repository.create_source_object(source_id=source_id, clock=clock)
    written = repository.append_source_object_version(
        source_object_id=source_object_id,
        version={
            "revision_id": revision_id,
            "object_type": object_type,
            "authorial_role": authorial_role,
            "salience_proposal": salience_proposal,
            "exact_text": exact_text,
            "content": dict(content or {}),
            "authorship": authorship,
            "status": status,
            "model_provenance": dict(model_provenance) if model_provenance is not None else None,
        },
        citations=list(citations or []),
        clock=clock,
    )
    return {"source_object_id": source_object_id, "status": status, **written}


def review_source_object(
    repository: Repository, *, source_object_id: str, status: str, clock: Clock | None = None
) -> dict[str, Any]:
    """Append a review status successor (``reviewed`` / ``rejected`` / ``superseded``).
    Accepting/reviewing never overwrites prior versions -- they remain for audit."""

    if status not in ("proposed", "reviewed", "rejected", "superseded"):
        raise SourceObjectError(f"unknown status: {status!r}")
    try:
        return repository.set_source_object_status(
            source_object_id=source_object_id, status=status, clock=clock
        )
    except ValueError as exc:
        raise SourceObjectError(str(exc)) from exc


def link_relation(
    repository: Repository,
    *,
    source_object_id: str,
    related_object_id: str | None = None,
    relation_type: str = CONNECT_IT_RELATION,
    learner_text: str | None = None,
    authorship: str = "learner",
    clock: Clock | None = None,
) -> dict[str, Any]:
    """Create a versioned relation between source objects. ``learner_connects``
    preserves the learner's wording and remains ``proposed`` until reviewed (§7.2)."""

    if relation_type not in RELATION_TYPES:
        raise SourceObjectError(f"unknown relation_type: {relation_type!r}")
    relation_id = repository.create_source_object_relation(
        source_object_id=source_object_id, related_object_id=related_object_id,
        relation_type=relation_type, learner_text=learner_text, authorship=authorship,
        review_status="proposed", clock=clock,
    )
    return {"relation_id": relation_id, "relation_type": relation_type, "review_status": "proposed"}


def propose_mapping(
    repository: Repository,
    *,
    target_kind: str,
    source_object_id: str | None = None,
    annotation_id: str | None = None,
    target_ref: str | None = None,
    confidence: float | None = None,
    rationale: str | None = None,
    provenance: Mapping[str, Any] | None = None,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """Append a canonical mapping proposal (§7.3). Append-only; accepting does not
    overwrite the source object and rejecting does not delete the annotation."""

    if target_kind not in MAPPING_TARGET_KINDS:
        raise SourceObjectError(f"unknown target_kind: {target_kind!r}")
    proposal_id = repository.create_mapping_proposal(
        source_object_id=source_object_id, annotation_id=annotation_id,
        target_kind=target_kind, target_ref=target_ref, confidence=confidence,
        rationale=rationale, provenance=provenance, clock=clock,
    )
    return {"proposal_id": proposal_id, "status": "proposed"}


def accept_mapping(repository: Repository, *, proposal_id: str, clock: Clock | None = None) -> dict[str, Any]:
    row = repository.decide_mapping_proposal(proposal_id=proposal_id, status="accepted", clock=clock)
    if row is None:
        raise SourceObjectError(f"unknown mapping proposal: {proposal_id!r}")
    return row


def reject_mapping(repository: Repository, *, proposal_id: str, clock: Clock | None = None) -> dict[str, Any]:
    """Rejecting a mapping never deletes the annotation or suppresses alternatives (§7.3)."""

    row = repository.decide_mapping_proposal(proposal_id=proposal_id, status="rejected", clock=clock)
    if row is None:
        raise SourceObjectError(f"unknown mapping proposal: {proposal_id!r}")
    return row


def source_objects_for_source(repository: Repository, *, source_id: str) -> list[dict[str, Any]]:
    return repository.source_objects_for_source(source_id)


def proposal_inbox(
    repository: Repository, *, status: str = "proposed", source_object_id: str | None = None
) -> dict[str, Any]:
    """Non-modal review inbox (§6.4): accumulated proposals reviewed without losing
    reading position. Nothing here is auto-applied."""

    return {"proposals": repository.mapping_proposals(status=status, source_object_id=source_object_id)}
