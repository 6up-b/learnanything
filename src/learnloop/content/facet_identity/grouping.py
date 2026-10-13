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
import heapq
from typing import Any

import numpy as np

from learnloop.content.synthesis.synthesis_gates import facet_tokens, jaccard
from learnloop.matching import shortlist as matching_shortlist

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
    #: Pairs a shortlist put forward: lexical near-duplicates, nominated
    #: (``extra_pairs``) and each facet's embedding top-k (recorded even when
    #: the vectors only split). The ledger keeps a kept-apart pair only when it
    #: is shortlisted (owner decision 2026-10-12).
    shortlisted: set[frozenset[str]] = field(default_factory=set)

    def summary(self) -> dict[str, Any]:
        return {
            "groups": len(self.groups),
            "grouped_facets": sum(len(group) for group in self.groups),
            "largest_group": max((len(group) for group in self.groups), default=0),
            "links": dict(sorted(self.links.items())),
            "split_components": self.split_components,
            "shortlist": self.shortlist,
            "shortlisted_pairs": len(self.shortlisted),
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

    Slice 2 T1's ``matching.shortlist.centred_unit`` does the maths. Facet
    identity keeps its own rule for vectors of mixed widths (two embedding
    models): no shortlist at all, rather than an error that would fail ingest.
    """

    if not vectors:
        return {}
    rows = {key: np.asarray(vector, dtype=np.float64) for key, vector in vectors.items()}
    try:
        return matching_shortlist.centred_unit(rows)
    except ValueError:
        return {}


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
    shortlisted: set[frozenset[str]] = set()
    for index, left in enumerate(ordered):
        for right in ordered[index + 1:]:
            if jaccard(tokens[left], tokens[right]) >= lexical_threshold:
                shortlisted.add(frozenset((left, right)))
                if union.union(left, right):
                    links["lexical"] += 1
    for left, right in extra_pairs:
        if left in by_key and right in by_key and left != right:
            shortlisted.add(frozenset((left, right)))
            if union.union(left, right):
                links["nominated"] += 1
    unit: dict[str, np.ndarray] = {}
    shortlist = "none"
    if vectors:
        unit = centred_unit({key: vectors[key] for key in by_key if key in vectors})
        if unit:
            for left, right, _score, _rank in shortlist_pairs(unit, top_k=top_k):
                shortlisted.add(frozenset((left, right)))
                if shortlist_edges and union.union(left, right):
                    links["embedding"] += 1
            if shortlist_edges:
                shortlist = "embedding"

    components: dict[str, list[str]] = defaultdict(list)
    for key in ordered:
        components[union.find(key)].append(key)
    grouping = Grouping(links=dict(links), shortlist=shortlist, shortlisted=shortlisted)
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
    """Average-link clustering under a size cap (deterministic), heap-based.

    Each step merges the two clusters with the highest average similarity
    whose joint size stays within ``cap``; ties go to the clusters whose first
    keys sort first. Cluster similarity totals update in place (the sum over
    the merged pair's rows), and a lazy max-heap keeps the next best pair, so
    a neighbourhood of n facets costs O(n² log n) rather than recomputing
    every pair's link each step (review F11). Pairs over the cap never come
    back (clusters only grow).
    """

    keys = sorted(members)
    count = len(keys)
    if count < 2:
        return [keys] if keys else []
    matrix = np.stack([np.asarray(unit[key], dtype=np.float64) for key in keys])
    totals = matrix @ matrix.T  # sum of pairwise similarity between clusters
    size = [1] * count
    alive = [True] * count
    version = [0] * count
    clusters: dict[int, list[str]] = {index: [key] for index, key in enumerate(keys)}
    heap: list[tuple[float, int, int, int, int]] = []
    if cap >= 2:
        heap = [(-float(totals[i, j]), i, j, 0, 0) for i in range(count) for j in range(i + 1, count)]
        heapq.heapify(heap)
    while heap:
        _negative, i, j, version_i, version_j = heapq.heappop(heap)
        if not (alive[i] and alive[j]) or version[i] != version_i or version[j] != version_j:
            continue
        if size[i] + size[j] > cap:
            continue
        # Merge j into i (i < j, so the merged cluster keeps the first key's slot).
        totals[i, :] += totals[j, :]
        totals[:, i] = totals[i, :]
        size[i] += size[j]
        alive[j] = False
        clusters[i].extend(clusters.pop(j))
        version[i] += 1
        for other in range(count):
            if other == i or not alive[other] or size[i] + size[other] > cap:
                continue
            first, second = (i, other) if i < other else (other, i)
            average = float(totals[i, other]) / (size[i] * size[other])
            heapq.heappush(heap, (-average, first, second, version[first], version[second]))
    return sorted(sorted(cluster) for cluster in clusters.values())


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
