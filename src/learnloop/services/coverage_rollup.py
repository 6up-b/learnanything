"""Three mutually-exclusive source-set facet coverage buckets."""

from __future__ import annotations

from typing import Any

from learnloop.db.repositories import Repository
from learnloop.vault.models import LoadedVault, SourceSet


def coverage_rollup(
    vault: LoadedVault, repository: Repository, source_set: SourceSet
) -> dict[str, Any]:
    facet_ids: set[str] = set()
    for item in vault.practice_items.values():
        if source_set.subject_id in vault.subjects_for_item(item):
            facet_ids.update(vault.canonical_facet_id(str(facet)) for facet in item.evidence_facets)
    member_revisions = {member.revision_id for member in source_set.members}
    for revision_id in member_revisions:
        for link in repository.entity_source_links_for_revision(revision_id):
            if link.get("entity_type") == "facet" and link.get("entity_id"):
                facet_ids.add(vault.canonical_facet_id(str(link["entity_id"])))

    supplied: set[str] = set()
    for item in vault.practice_items.values():
        state = repository.practice_item_state(item.id)
        if state is not None and not state.active:
            continue
        supplied.update(vault.canonical_facet_id(str(facet)) for facet in item.evidence_facets)
    demonstrated = {
        vault.canonical_facet_id(cell.facet_id)
        for cell in repository.facet_capability_evidence_all()
        if cell.certification_credit > 0
    }

    buckets = {"demonstrated": [], "assessed": [], "no_practice_supply": []}
    for facet_id in sorted(facet_ids):
        # Explicit precedence prevents pooled demonstration + no local supply
        # from being double-counted as system debt.
        if facet_id in demonstrated:
            buckets["demonstrated"].append(facet_id)
        elif facet_id in supplied:
            buckets["assessed"].append(facet_id)
        else:
            buckets["no_practice_supply"].append(facet_id)
    return {
        "total": len(facet_ids),
        "buckets": {
            name: {"count": len(ids), "facet_ids": ids}
            for name, ids in buckets.items()
        },
    }
