"""Explicit conflict resolution (source-ingestion §10.2).

Accepting a `source_conflict` item persists an OPEN two-sided conflict; it never
applies either competing side. Resolution is a SEPARATE later explicit action with
its own service and audit history:

- ``prefer_for_context`` — prefer one source's meaning for a defined context;
- ``keep_both_scoped``   — preserve both meanings, each scoped;
- ``notation_mapping``   — the disagreement is only notation; emit a mapping;
- ``dismiss``            — the conflict was not real.

Every resolution preserves both evidence locators on the conflict row and appends
an immutable ``source_conflict_resolutions`` audit row (``resolve_source_conflict``).
A ``notation_mapping`` resolution also inserts the mapping so the equivalence is
usable. Nothing here rewrites a facet's semantic contract.
"""

from __future__ import annotations

from typing import Any

from learnloop.clock import Clock
from learnloop.db.repositories import Repository

RESOLUTION_KINDS = frozenset({"prefer_for_context", "keep_both_scoped", "notation_mapping", "dismiss"})


class ConflictResolutionError(ValueError):
    pass


def resolve_conflict(
    repository: Repository,
    conflict_id: str,
    *,
    resolution_kind: str,
    resolution: dict[str, Any] | None = None,
    actor: str | None = None,
    rationale: str | None = None,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """Resolve an open conflict; return the updated conflict row (§10.2)."""

    if resolution_kind not in RESOLUTION_KINDS:
        raise ConflictResolutionError(f"unknown resolution kind {resolution_kind!r}")
    conflict = repository.source_conflict(conflict_id)
    if conflict is None:
        raise ConflictResolutionError(f"conflict {conflict_id} does not exist")
    if conflict["status"] != "open":
        raise ConflictResolutionError(f"conflict {conflict_id} is already {conflict['status']}")

    payload = dict(resolution or {})
    payload["kind"] = resolution_kind
    status = "dismissed" if resolution_kind == "dismiss" else "resolved"

    # A notation_mapping resolution also materializes the equivalence so it is usable.
    if resolution_kind == "notation_mapping":
        canonical = str(payload.get("canonical_notation") or "")
        alternate = str(payload.get("alternate_notation") or "")
        if not canonical or not alternate:
            raise ConflictResolutionError("notation_mapping resolution requires both notations")
        mapping_id = repository.insert_notation_mapping(
            entity_type=conflict["entity_type"],
            entity_id=conflict["entity_id"],
            canonical_notation=canonical,
            alternate_notation=alternate,
            subject_id=conflict.get("subject_id"),
            context=payload.get("context"),
            source_id=conflict.get("right_source_id"),
            revision_id=conflict.get("right_revision_id"),
            locator=conflict.get("right_locator"),
            status="active",
            clock=clock,
        )
        payload["notation_mapping_id"] = mapping_id

    repository.resolve_source_conflict(
        conflict_id, status=status, resolution=payload, resolution_kind=resolution_kind,
        actor=actor, rationale=rationale, clock=clock,
    )
    return repository.source_conflict(conflict_id)


def conflict_with_audit(repository: Repository, conflict_id: str) -> dict[str, Any] | None:
    conflict = repository.source_conflict(conflict_id)
    if conflict is None:
        return None
    conflict["resolutions"] = repository.source_conflict_resolutions(conflict_id)
    return conflict
