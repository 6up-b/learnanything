"""Concept neighbourhoods of facets: the groups one judge call partitions.

Two facets share a neighbourhood when any of these links them (union-find, so
the neighbourhood is a connected component):

* the same concept (after the run's concept consolidation);
* adjacent concepts (any concept-graph relation between them);
* the lexical near-duplicate gate's pairs (Jaccard over title and claim
  tokens at or above the gate's threshold);
* an embedding shortlist: each facet's top-k nearest facets by mean-centred
  cosine, when stored or run vectors exist (the study: every duplicate was
  within rank 4).

Embeddings only shortlist; nothing here decides identity (spec R1, R4). A
neighbourhood larger than ``max_group_size`` is split: by average-link
agglomeration over the same vectors when every member has one, otherwise by
packing whole concepts in concept-graph order. Every facet lands in exactly
one group, so two groups can never fuse a chain of facets.
"""

from __future__ import annotations

from collections import defaultdict, deque
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from learnloop.content.synthesis.synthesis_gates import facet_tokens, jaccard

DEFAULT_LEXICAL_THRESHOLD = 0.85


@dataclass(frozen=True)
class FacetNode:
    """One facet in scope: a registered facet or a run candidate."""

    key: str
    payload: Mapping[str, Any]
    concept: str | None = None
    existing: bool = True


@dataclass
class Grouping:
    groups: list[list[str]] = field(default_factory=list)
    #: Why facets were linked: counts per link kind.
    links: dict[str, int] = field(default_factory=dict)
    split_components: int = 0
    shortlist: str = "none"  # none | embedding

    def summary(self) -> dict[str, Any]:
        return {
            "groups": len(self.groups),
            "grouped_facets": sum(len(group) for group in self.groups),
            "largest_group": max((len(group) for group in self.groups), default=0),
            "links": dict(sorted(self.links.items())),
            "split_components": self.split_components,
            "shortlist": self.shortlist,
        }


class _Union:
    def __init__(self, keys: Iterable[str]) -> None:
        self.parent = {key: key for key in keys}

    def find(self, key: str) -> str:
        while self.parent[key] != key:
            self.parent[key] = self.parent[self.parent[key]]
            key = self.parent[key]
        return key

    def union(self, left: str, right: str) -> bool:
        a, b = self.find(left), self.find(right)
        if a == b:
            return False
        if b < a:
            a, b = b, a
        self.parent[b] = a
        return True


def centred_unit(vectors: Mapping[str, np.ndarray]) -> dict[str, np.ndarray]:
    """Mean-centred unit rows over the given set (Slice 1 §9.2 maths).

    Reuse point: Slice 2 T1's ``matching.shortlist.centred_unit`` is the same
    function; switch to it when T1 merges.
    """

    if not vectors:
        return {}
    keys = sorted(vectors)
    widths = {np.asarray(vectors[key]).size for key in keys}
    if len(widths) != 1:
        return {}
    matrix = np.stack([np.asarray(vectors[key], dtype=np.float64) for key in keys])
    centred = matrix - matrix.mean(axis=0)
    norms = np.linalg.norm(centred, axis=1, keepdims=True)
    unit = np.divide(centred, norms, out=np.zeros_like(centred), where=norms != 0)
    return {key: unit[index] for index, key in enumerate(keys)}


def shortlist_pairs(
    unit: Mapping[str, np.ndarray], *, top_k: int, eligible: set[str] | None = None,
) -> list[tuple[str, str, float, int]]:
    """Each facet's top-k neighbours: (query, neighbour, cosine, rank)."""

    keys = sorted(key for key in unit if eligible is None or key in eligible)
    out: list[tuple[str, str, float, int]] = []
    for key in keys:
        scored = sorted(
            ((float(unit[key] @ unit[other]), other) for other in keys if other != key),
            key=lambda row: (-row[0], row[1]),
        )[:top_k]
        out.extend((key, other, score, rank) for rank, (score, other) in enumerate(scored, start=1))
    return out


def neighbourhood_groups(
    nodes: Sequence[FacetNode],
    *,
    concept_edges: Iterable[tuple[str, str]] = (),
    extra_pairs: Iterable[tuple[str, str]] = (),
    vectors: Mapping[str, np.ndarray] | None = None,
    top_k: int = 4,
    max_group_size: int = 40,
    lexical_threshold: float = DEFAULT_LEXICAL_THRESHOLD,
    shortlist_edges: bool = True,
) -> Grouping:
    """Connected concept neighbourhoods, bounded to ``max_group_size``.

    Only groups of two or more facets are returned: a lone facet has nothing
    to be a duplicate of. ``shortlist_edges=False`` uses ``vectors`` only to
    split an oversized neighbourhood (the dedupe command), never to link.
    """

    by_key = {node.key: node for node in nodes}
    union = _Union(by_key)
    links: dict[str, int] = defaultdict(int)

    by_concept: dict[str, list[str]] = defaultdict(list)
    for node in nodes:
        if node.concept:
            by_concept[node.concept].append(node.key)
    for members in by_concept.values():
        for other in members[1:]:
            if union.union(members[0], other):
                links["same_concept"] += 1
    adjacency: dict[str, set[str]] = defaultdict(set)
    for left, right in concept_edges:
        if left == right:
            continue
        adjacency[left].add(right)
        adjacency[right].add(left)
        if by_concept.get(left) and by_concept.get(right):
            if union.union(by_concept[left][0], by_concept[right][0]):
                links["concept_graph"] += 1
    tokens = {node.key: facet_tokens(dict(node.payload)) for node in nodes}
    ordered = sorted(by_key)
    for index, left in enumerate(ordered):
        for right in ordered[index + 1:]:
            if jaccard(tokens[left], tokens[right]) >= lexical_threshold:
                if union.union(left, right):
                    links["lexical"] += 1
    for left, right in extra_pairs:
        if left in by_key and right in by_key and union.union(left, right):
            links["nominated"] += 1
    unit: dict[str, np.ndarray] = {}
    shortlist = "none"
    if vectors:
        unit = centred_unit({key: vectors[key] for key in by_key if key in vectors})
        if unit and shortlist_edges:
            shortlist = "embedding"
            for left, right, _score, _rank in shortlist_pairs(unit, top_k=top_k):
                if union.union(left, right):
                    links["embedding"] += 1

    components: dict[str, list[str]] = defaultdict(list)
    for key in ordered:
        components[union.find(key)].append(key)
    grouping = Grouping(links=dict(links), shortlist=shortlist)
    for root in sorted(components):
        members = components[root]
        if len(members) < 2:
            continue
        if len(members) <= max_group_size:
            grouping.groups.append(members)
            continue
        grouping.split_components += 1
        if unit and all(key in unit for key in members):
            parts = _agglomerate(members, unit, max_group_size)
        else:
            parts = _pack_by_concept(members, by_key, adjacency, max_group_size)
        grouping.groups.extend(part for part in parts if len(part) >= 2)
    grouping.groups.sort(key=lambda group: (group[0], len(group)))
    return grouping


def _agglomerate(members: list[str], unit: Mapping[str, np.ndarray], cap: int) -> list[list[str]]:
    """Average-link clustering under a size cap (deterministic)."""

    clusters: list[list[str]] = [[key] for key in sorted(members)]
    similarity = {(a, b): float(unit[a] @ unit[b]) for a in members for b in members if a < b}

    def link(left: list[str], right: list[str]) -> float:
        total = 0.0
        for a in left:
            for b in right:
                total += similarity[(a, b) if a < b else (b, a)]
        return total / (len(left) * len(right))

    while True:
        best: tuple[float, int, int] | None = None
        for i in range(len(clusters)):
            for j in range(i + 1, len(clusters)):
                if len(clusters[i]) + len(clusters[j]) > cap:
                    continue
                score = link(clusters[i], clusters[j])
                if best is None or score > best[0]:
                    best = (score, i, j)
        if best is None:
            break
        _score, i, j = best
        clusters[i] = sorted(clusters[i] + clusters[j])
        del clusters[j]
    return sorted(clusters)


def _pack_by_concept(
    members: list[str],
    by_key: Mapping[str, FacetNode],
    adjacency: Mapping[str, set[str]],
    cap: int,
) -> list[list[str]]:
    """Whole concepts packed in concept-graph order; huge concepts are chunked."""

    by_concept: dict[str, list[str]] = defaultdict(list)
    for key in members:
        by_concept[by_key[key].concept or f"__none__:{key}"].append(key)
    order: list[str] = []
    seen: set[str] = set()
    for start in sorted(by_concept, key=lambda concept: (-len(by_concept[concept]), concept)):
        if start in seen:
            continue
        queue = deque([start])
        seen.add(start)
        while queue:
            concept = queue.popleft()
            order.append(concept)
            for neighbour in sorted(adjacency.get(concept, ())):
                if neighbour in by_concept and neighbour not in seen:
                    seen.add(neighbour)
                    queue.append(neighbour)
    groups: list[list[str]] = []
    current: list[str] = []
    for concept in order:
        keys = sorted(by_concept[concept])
        while len(keys) > cap:
            groups.append(keys[:cap])
            keys = keys[cap:]
        if len(current) + len(keys) > cap:
            groups.append(current)
            current = []
        current.extend(keys)
    if current:
        groups.append(current)
    return [sorted(group) for group in groups]


__all__ = [
    "DEFAULT_LEXICAL_THRESHOLD",
    "FacetNode",
    "Grouping",
    "centred_unit",
    "neighbourhood_groups",
    "shortlist_pairs",
]
