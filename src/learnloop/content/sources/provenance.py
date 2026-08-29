"""Entity provenance and coverage reads (source-ingestion §9.2/§9.3).

``get_entity_provenance`` answers, for any facet / LO / blueprint / practice item:
which sources support it (with exact span locators), which are *semantic* authority
vs *assessment-alignment* only (kept separate so a learner never reads "appeared on
an exam" as "defines the concept"), known conflicts and notation mappings,
staleness, and the synthesis run that introduced it (patch -> agent run ->
manifest). ``entity_source_links`` is authoritative; the YAML ``provenance``
snapshot is a compatible embedded copy.
"""

from __future__ import annotations

from typing import Any

from learnloop.db.repositories import Repository

# Relations that assert (or support) semantic authority vs those that only carry
# task/assessment alignment (§4.2 / §9.3).
_SEMANTIC_RELATIONS = frozenset({"primary", "support", "alternate"})
_ASSESSMENT_RELATIONS = frozenset({"assessment_alignment", "exercise"})


def _link_dto(link: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": link["id"],
        "source_id": link.get("source_id"),
        "revision_id": link.get("revision_id"),
        "locator": link.get("locator"),
        "locator_scheme": link.get("locator_scheme"),
        "relation": link.get("relation"),
        "extraction_id": link.get("extraction_id"),
        "asset_hash": link.get("asset_hash"),
        "span_hash": link.get("span_hash"),
        "status": link.get("status"),
        "stale": link.get("status") not in (None, "current"),
    }


def get_entity_provenance(
    repository: Repository, entity_type: str, entity_id: str
) -> dict[str, Any]:
    """Assemble the entity provenance view (§9.2).

    Semantic authority and assessment-alignment provenance are returned as
    separate lists; staleness and the introducing synthesis-run lineage are
    included when known.
    """

    links = repository.entity_source_links(entity_type, entity_id)
    semantic: list[dict[str, Any]] = []
    assessment: list[dict[str, Any]] = []
    stale: list[dict[str, Any]] = []
    for link in links:
        dto = _link_dto(link)
        relation = link.get("relation")
        if relation in _ASSESSMENT_RELATIONS:
            assessment.append(dto)
        elif relation in _SEMANTIC_RELATIONS:
            semantic.append(dto)
        if dto["stale"]:
            stale.append(dto)

    # Semantic authority is the highest-priority current semantic link: prefer a
    # `primary` relation, else the first current `support`/`alternate`.
    semantic_authority = None
    for preference in ("primary", "support", "alternate"):
        for dto in semantic:
            if dto["relation"] == preference and not dto["stale"]:
                semantic_authority = dto
                break
        if semantic_authority is not None:
            break

    conflicts = [
        {
            "id": conflict["id"],
            "statement": conflict.get("statement"),
            "status": conflict.get("status"),
            "left_source_id": conflict.get("left_source_id"),
            "left_locator": conflict.get("left_locator"),
            "right_source_id": conflict.get("right_source_id"),
            "right_locator": conflict.get("right_locator"),
        }
        for conflict in repository.source_conflicts_for_entity(entity_type, entity_id)
    ]
    notation = [
        {
            "id": mapping["id"],
            "canonical_notation": mapping.get("canonical_notation"),
            "alternate_notation": mapping.get("alternate_notation"),
            "context": mapping.get("context"),
            "status": mapping.get("status"),
        }
        for mapping in repository.notation_mappings_for_entity(entity_type, entity_id)
    ]

    introducing_run = repository.synthesis_run_introducing_entity(entity_type, entity_id)
    introduced_by = None
    if introducing_run is not None:
        manifest = repository.synthesis_manifest(introducing_run["manifest_id"])
        introduced_by = {
            "synthesis_run_id": introducing_run["id"],
            "mode": introducing_run.get("mode"),
            "agent_run_id": introducing_run.get("agent_run_id"),
            "proposal_id": introducing_run.get("proposal_id"),
            "manifest_id": introducing_run.get("manifest_id"),
            "manifest_hash": (manifest or {}).get("manifest_hash"),
        }

    return {
        "entity_type": entity_type,
        "entity_id": entity_id,
        "semantic_sources": semantic,
        "assessment_alignment_sources": assessment,
        "semantic_authority": semantic_authority,
        "stale_links": stale,
        "conflicts": conflicts,
        "notation_mappings": notation,
        "introduced_by": introduced_by,
        "has_provenance": bool(links or conflicts or notation),
    }
