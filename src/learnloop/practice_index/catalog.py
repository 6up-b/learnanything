"""The vault's item-facet hypergraph as the practice index reads it."""
from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable

from learnloop.vault.models import EvidenceFacet, LoadedVault, PracticeItem


#: Practice modes that never become ordinary practice and never ground a dossier.
DIAGNOSTIC_MODES = frozenset({"diagnostic_probe", "diagnostic_microprobe"})


def registered_facets(vault: LoadedVault) -> dict[str, EvidenceFacet]:
    """Registered, non-retired facets by canonical id."""
    return {
        facet_id: facet for facet_id, facet in sorted(vault.evidence_facets.items())
        if facet.status != "retired" and vault.canonical_facet_id(facet_id) == facet_id
    }


def item_facets(vault: LoadedVault, item: PracticeItem) -> set[str]:
    """Canonical facet ids an item declares (registered or not)."""
    return {vault.canonical_facet_id(str(facet)) for facet in item.evidence_facets}


def facet_items(vault: LoadedVault,
                items: Iterable[PracticeItem] | None = None) -> dict[str, list[str]]:
    """Item ids per canonical facet id, sorted."""
    grouped: dict[str, list[str]] = defaultdict(list)
    for item in (vault.practice_items.values() if items is None else items):
        for facet_id in item_facets(vault, item):
            grouped[facet_id].append(item.id)
    return {facet_id: sorted(ids) for facet_id, ids in sorted(grouped.items())}


def facet_label(facet: EvidenceFacet) -> str:
    return (facet.title or facet.claim or facet.description or facet.id).strip()


__all__ = ["DIAGNOSTIC_MODES", "facet_items", "facet_label", "item_facets", "registered_facets"]
